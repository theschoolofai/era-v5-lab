"""Load a GPT-2 ByteLevel BPE tokenizer and recover the exact bytes of every token.

The vocabulary strings of a ByteLevel tokenizer are written in a fixed 256-symbol alphabet that is
a bijection with byte values. Inverting it symbol by symbol recovers each token's exact bytes,
whether or not they form valid UTF-8. ``tokenizer.decode([id])`` cannot: a token holding part of a
multi-byte character decodes to U+FFFD.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import HF_ID, HF_REVISION, TOKENIZER_ENV_VARS
from .hashing import sha256_file

log = logging.getLogger(__name__)

U_FFFD = "�".encode()
"""UTF-8 of the replacement character, ``EF BF BD``."""


class VocabHoleError(ValueError):
    """A token ID has no vocabulary entry, or an empty byte string.

    Every such ID would be encoded as the empty string, whose code is the zero vector, so all holes
    collide with each other (see proof.md, Lemma 2 remark). Strict table builds refuse them.
    """


class TokenizerIdentityError(ValueError):
    """The tokenizer file is not the artifact the caller asked for."""


# --------------------------------------------------------------------------- #
# GPT-2 ByteLevel alphabet
# --------------------------------------------------------------------------- #
def gpt2_bytes_to_unicode() -> dict[int, str]:
    """The canonical GPT-2 byte -> printable-character map (identical to HF ``bytes_to_unicode``)."""
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return {b: chr(c) for b, c in zip(bs, cs, strict=True)}


BYTE_TO_UNI: dict[int, str] = gpt2_bytes_to_unicode()
UNI_TO_BYTE: dict[str, int] = {u: b for b, u in BYTE_TO_UNI.items()}
if len(UNI_TO_BYTE) != 256:  # pragma: no cover - guards the constant above
    raise RuntimeError("ByteLevel alphabet must be a bijection on 256 symbols")


def piece_to_raw_bytes(piece: str) -> bytes:
    """Invert the ByteLevel alphabet symbol by symbol. Never lossy."""
    try:
        return bytes(UNI_TO_BYTE[ch] for ch in piece)
    except KeyError as e:
        raise ValueError(f"piece {piece!r} contains non-ByteLevel symbol {e}") from e


# --------------------------------------------------------------------------- #
# Resolution and loading
# --------------------------------------------------------------------------- #
def _as_tokenizer_file(candidate: str | os.PathLike[str]) -> Path | None:
    p = Path(candidate).expanduser()
    if p.is_dir():
        p = p / "tokenizer.json"
    return p if p.is_file() else None


def resolve_tokenizer_path(arg: str | None = None, *, allow_download: bool = False) -> Path:
    """Return a local ``tokenizer.json``.

    Order: ``arg`` (a file or folder), ``$KE2_TOKENIZER``, ``$BRAHMIC_TOKENIZER_DIR``, then the
    Hugging Face cache at the pinned revision. Downloading happens only with ``allow_download=True``.
    """
    candidates = [arg] if arg else []
    candidates += [os.environ[v] for v in TOKENIZER_ENV_VARS if os.environ.get(v)]
    for c in candidates:
        found = _as_tokenizer_file(c)
        if found is not None:
            return found

    repo_id = arg if (arg and "/" in arg and not Path(arg).exists()) else HF_ID
    revision = HF_REVISION if repo_id == HF_ID else None
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as e:  # pragma: no cover
        raise FileNotFoundError(f"tokenizer.json not found in {candidates} and huggingface_hub is missing") from e
    try:
        return Path(hf_hub_download(repo_id, "tokenizer.json", revision=revision, local_files_only=True))
    except Exception as e:
        if not allow_download:
            raise FileNotFoundError(
                f"tokenizer.json not found locally (tried {candidates} and the HF cache for {repo_id}); "
                "pass a path, set KE2_TOKENIZER, or allow downloading"
            ) from e
    log.info("downloading tokenizer.json from %s@%s", repo_id, revision or "main")
    return Path(hf_hub_download(repo_id, "tokenizer.json", revision=revision))


@dataclass
class TokenizerBundle:
    """Everything the tables need from one ``tokenizer.json``."""

    path: Path
    tok: Any  # tokenizers.Tokenizer
    json: dict
    vocab_size: int
    id_to_piece: dict[int, str]  # model vocabulary, in ByteLevel symbols
    added: dict[int, dict]  # added_tokens by ID
    special_ids: set[int] = field(default_factory=set)
    _sha256: str = field(default="", repr=False)

    @property
    def sha256(self) -> str:
        """SHA-256 of the ``tokenizer.json`` file: the identity every table is bound to."""
        if not self._sha256:
            self._sha256 = sha256_file(self.path)
        return self._sha256


def load_tokenizer(
    path_or_id: str | None = None, *, expected_sha256: str | None = None, allow_download: bool = False
) -> TokenizerBundle:
    """Load a tokenizer; with ``expected_sha256``, refuse any other artifact."""
    from tokenizers import Tokenizer  # local import keeps the numpy-only helpers importable

    path = resolve_tokenizer_path(path_or_id, allow_download=allow_download)
    tok = Tokenizer.from_file(str(path))
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    vocab = d["model"]["vocab"]
    added = {a["id"]: a for a in d.get("added_tokens", [])}
    vocab_size = max(max(vocab.values()), *(added.keys() or [0])) + 1
    hf_size = tok.get_vocab_size(with_added_tokens=True)
    if hf_size != vocab_size:
        raise ValueError(f"vocab size mismatch: json={vocab_size} tokenizers={hf_size}")
    bundle = TokenizerBundle(
        path=path,
        tok=tok,
        json=d,
        vocab_size=vocab_size,
        id_to_piece={v: k for k, v in vocab.items()},
        added=added,
        special_ids={i for i, a in added.items() if a.get("special", False)},
    )
    if expected_sha256 and bundle.sha256 != expected_sha256:
        raise TokenizerIdentityError(f"{path} has SHA-256 {bundle.sha256[:12]}…, expected {expected_sha256[:12]}…")
    return bundle


# --------------------------------------------------------------------------- #
# Per-token byte sources
# --------------------------------------------------------------------------- #
def raw_bytes_for_id(tb: TokenizerBundle, tid: int, *, missing_ok: bool = False) -> bytes:
    """Exact bytes of token ``tid``: the inverted ByteLevel piece, or literal UTF-8 for added tokens.

    Raises :class:`VocabHoleError` for an ID with no vocabulary entry unless ``missing_ok``
    (then returns ``b""``).
    """
    if tid in tb.added:
        return tb.added[tid]["content"].encode("utf-8")
    piece = tb.id_to_piece.get(tid)
    if piece is None:
        if missing_ok:
            return b""
        raise VocabHoleError(f"token id {tid} has no vocabulary entry (hole in id space)")
    return piece_to_raw_bytes(piece)


def decode_bytes_for_id(tb: TokenizerBundle, tid: int) -> bytes:
    """Upstream behaviour: ``tokenizer.decode([id]).encode('utf-8')``; specials as literal content.

    Mirrors ``kronecker_embeddings.tokenizer_utils.token_id_to_bytes`` for a ByteLevel tokenizer
    without ``<0xNN>`` byte-fallback pieces.
    """
    if tid in tb.special_ids:
        return tb.added[tid]["content"].encode("utf-8")
    text = tb.tok.decode([tid], skip_special_tokens=False)
    return (text or "").encode("utf-8")
