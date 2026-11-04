"""Forward-encode helpers for the proofs in proof.md (Lemma 1, Lemma 2, Theorem 1).

The codec is the upstream one (``kronecker_embeddings.codec.kronecker_codec``). This module adds
what the proof needs on top of it:

  truncate        the cut rule from Lemma 2: the repository rule by default, the proposed variant with rule="proposed"
  codes           codes for a list of byte strings, using the repository codec
  read_support    reads the bytes back from a code (the argument of Lemma 1)
  expected_values closed-form high and low value of a code (Lemma 1)
  pair_cause      names why two tokens share a code (corollary of Theorem 1)

Needs the ``ke2`` package (teams/04-ke2/src) and ``kronecker_embeddings`` on the import path; the
entry points and tests/conftest.py arrange both (see ``ke2.upstream``).
"""

from __future__ import annotations

import hashlib

import torch
from kronecker_embeddings.codec import kronecker_codec

from ke2.codec import code_values
from ke2.codec import read_support as _read_support
from ke2.truncation import proposed_truncate, repo_truncate

EPS = 1e-6  # the repository default for the z-norm denominator
CAUSES = ("empty", "cut_to_empty", "same_raw", "bad_bytes_in", "truncation")
RULES = {"repo": repo_truncate, "proposed": proposed_truncate}

__all__ = [
    "CAUSES", "EPS", "RULES", "code_digest", "codes", "decode_style_bytes", "expected_values", "pair_cause",
    "proposed_truncate", "read_support", "repo_truncate", "truncate",
]  # fmt: skip


def truncate(raw: bytes, P: int, rule: str = "repo") -> bytes:
    """The cut used by the proof. The default is the repository rule; rule="proposed" is the variant."""
    return RULES[rule](raw, P)


def codes(strings: list[bytes], P: int, dtype: torch.dtype = torch.float32) -> torch.Tensor:
    """Codes for byte strings that are already at most P bytes. Shape (len(strings), 256 * P)."""
    buf = torch.zeros(len(strings), P, dtype=torch.uint8)
    lens = torch.zeros(len(strings), dtype=torch.long)
    for i, s in enumerate(strings):
        if len(s) > P:
            raise ValueError(f"string {i} has {len(s)} bytes, more than P={P}")
        if s:
            buf[i, : len(s)] = torch.frombuffer(bytearray(s), dtype=torch.uint8)
        lens[i] = len(s)
    return kronecker_codec(buf, lens, pos_dim=P, out_dtype=dtype)


def code_digest(code: torch.Tensor) -> bytes:
    """A hash of one code vector, to compare many codes without keeping them all."""
    return hashlib.sha1(code.float().contiguous().numpy().tobytes()).digest()


def read_support(code: torch.Tensor, P: int) -> bytes:
    """Read the byte string back from a code: the high cells are the lit cells.

    Cell i of the flattened (256, P) grid is byte i // P at position i % P.
    Raises ValueError if the lit cells are not exactly one per position 0..L-1.
    """
    return _read_support(code, P)


def expected_values(L: int, P: int, eps: float = EPS) -> tuple[float, float]:
    """(high, low): the two values of the code of a string with L bytes (1 <= L <= P)."""
    high, low = code_values(L, P, eps=eps)
    return float(high), float(low)


def decode_style_bytes(raw: bytes) -> bytes:
    """A model of tokenizer.decode([id]).encode(): invalid bytes become U+FFFD.

    A stand-in for tests. On BrahmicTokenizer-131K it equals the real `tokenizers` decoder for every id
    (proof.md section 4); other tokenizers may differ.
    """
    return raw.decode("utf-8", errors="replace").encode("utf-8")


def pair_cause(raw_a: bytes, raw_b: bytes, fed_a: bytes, fed_b: bytes, P: int, rule: str = "repo") -> str | None:
    """Why do two tokens share a code? None if they do not.

    raw_*  the token's real vocabulary bytes
    fed_*  the bytes the table feeds to the codec (equal to raw_* for the raw byte table)
    rule   the cut rule, "repo" or "proposed"
    """
    cut_a, cut_b = truncate(fed_a, P, rule), truncate(fed_b, P, rule)
    if cut_a != cut_b:
        return None
    if not cut_a:
        return "empty" if not fed_a and not fed_b else "cut_to_empty"
    if raw_a == raw_b:
        return "same_raw"
    if fed_a == fed_b:
        return "bad_bytes_in"
    return "truncation"
