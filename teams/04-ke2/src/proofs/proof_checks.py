"""Numerical checks for proof.md on a real tokenizer.json (byte-level BPE, e.g. BrahmicTokenizer-131K). See proof.md section 4.

usage: python proof_checks.py <dir with tokenizer.json and special_tokens_map.json> [out.json]
       (out.json defaults to teams/04-ke2/results/proof_checks.json)

Builds two tables and runs the codec on both, for P = 32 and 64 in fp32 and bf16:
  raw     the real vocabulary bytes (GPT-2 byte-to-unicode map inverted)
  decode  what the repository's token_id_to_bytes feeds (decode([id]), real `tokenizers` decoder)
For each: distinct codes, whether the groups by code equal the groups by cut string (Theorem 1),
unreachable tokens, tokens longer than P or cut to nothing (Lemma 2), and the cause of every colliding pair.
Also the smallest gap between the two code values after rounding to bf16 (Lemma 1 remark).
Needs torch, tokenizers and kronecker-embeddings. The tokenizer files are never part of this repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

if __package__ in (None, ""):  # run as a script: make ke2 and the upstream codec importable
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from ke2.upstream import ensure_kronecker_embeddings

    ensure_kronecker_embeddings()

import torch
from tokenizers import Tokenizer

from forward import code_digest, codes, pair_cause, truncate
from ke2.config import RESULTS_DIR
from ke2.tokenizer import BYTE_TO_UNI

DEFAULT_OUT = RESULTS_DIR / "proof_checks.json"


def bytes_to_unicode() -> dict[int, str]:
    """The GPT-2 byte -> character map (shared with the table builder)."""
    return dict(BYTE_TO_UNI)


def is_utf8(b: bytes) -> bool:
    try:
        b.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def load_tables(tok_dir: Path) -> tuple[list[bytes], list[bytes], dict]:
    """Return (raw, fed, info). fed comes from the repository's token_id_to_bytes."""
    from kronecker_embeddings.tokenizer_utils import token_id_to_bytes

    tk = Tokenizer.from_file(str(tok_dir / "tokenizer.json"))
    vocab = tk.get_vocab(with_added_tokens=True)
    n = max(vocab.values()) + 1
    inv = {c: b for b, c in bytes_to_unicode().items()}
    raw: list[bytes | None] = [None] * n
    for s, i in vocab.items():
        raw[i] = bytes(inv[c] for c in s) if all(c in inv for c in s) else s.encode("utf-8")
    assert all(r is not None for r in raw), "gaps in the id range"

    smap = json.loads((tok_dir / "special_tokens_map.json").read_text(encoding="utf-8"))

    class Adapter:  # the members of a transformers tokenizer that token_id_to_bytes uses
        all_special_ids = [vocab[t] for t in smap.values() if isinstance(t, str)]  # noqa: RUF012

        def convert_ids_to_tokens(self, i):
            return tk.id_to_token(i)

        def decode(self, ids, skip_special_tokens=False, clean_up_tokenization_spaces=False):
            return tk.decode(ids, skip_special_tokens=skip_special_tokens)

    ad = Adapter()
    fed = [token_id_to_bytes(ad, i) for i in range(n)]
    h = hashlib.sha256()
    for i, r in enumerate(raw):
        h.update(i.to_bytes(4, "big") + len(r).to_bytes(2, "big") + r)
    special = {i for i, t in tk.get_added_tokens_decoder().items() if t.special}
    bad = [r for i, r in enumerate(raw) if i not in special and not is_utf8(r)]
    info = {
        "vocab": n,
        "tokenizer_json_sha256": hashlib.sha256((tok_dir / "tokenizer.json").read_bytes()).hexdigest(),
        "raw_table_sha256": h.hexdigest(),
        "special_tokens": len(special),
        "max_bytes": max(len(r) for r in raw),
        "max_bytes_ordinary": max(len(r) for i, r in enumerate(raw) if i not in special),
        "max_bytes_special": max(len(raw[i]) for i in special),
        "not_valid_utf8": len(bad),
        "not_valid_utf8_start_with_continuation": sum(1 for r in bad if r[0] & 0xC0 == 0x80),
        "not_valid_utf8_with_kannada_lead": sum(1 for r in bad if b"\xe0\xb2" in r or b"\xe0\xb3" in r),
        "fffd_token_ids": [i for i, r in enumerate(raw) if r == "�".encode()],
    }
    return raw, fed, info


def check_table(raw: list[bytes], fed: list[bytes], P: int) -> dict:
    cuts = [truncate(f, P) for f in fed]
    out: dict = {
        "longer_than_P": sum(1 for f in fed if len(f) > P),
        "cut_to_empty": sum(1 for f, c in zip(fed, cuts, strict=True) if f and not c),
    }
    for dtype in (torch.float32, torch.bfloat16):
        by_code = defaultdict(list)
        for s in range(0, len(cuts), 1000):
            for k, z in enumerate(codes(cuts[s : s + 1000], P, dtype)):
                by_code[code_digest(z)].append(s + k)
        by_cut = defaultdict(list)
        for i, c in enumerate(cuts):
            by_cut[c].append(i)
        out[str(dtype).split(".")[-1]] = {
            "distinct_codes": len(by_code),
            "distinct_cut_strings": len(by_cut),
            "partitions_equal": {frozenset(g) for g in by_code.values()} == {frozenset(g) for g in by_cut.values()},
        }
        if dtype is torch.float32:
            groups = [g for g in by_code.values() if len(g) > 1]
    causes: Counter = Counter()
    for g in groups:
        for a, b in combinations(g, 2):
            causes[pair_cause(raw[a], raw[b], fed[a], fed[b], P)] += 1
    out.update(
        groups=len(groups),
        unreachable=sum(len(g) - 1 for g in groups),
        largest=sorted((len(g) for g in groups), reverse=True)[:5],
        pair_causes=dict(causes),
    )
    return out


def bf16_min_gap(P: int) -> float:
    """The smallest high - low gap of a bf16 code over every length L from 1 to P (Lemma 1 remark)."""
    zs = codes([b"a" * L for L in range(1, P + 1)], P, torch.bfloat16).float()
    return float((zs.max(dim=1).values - zs.min(dim=1).values).min())


def run(tok_dir: Path) -> dict:
    raw, fed, info = load_tables(tok_dir)
    info["fed_equals_raw"] = sum(1 for r, f in zip(raw, fed, strict=True) if r == f)
    for P in (32, 64):
        info[f"P{P}_bf16_min_gap"] = bf16_min_gap(P)
        info[f"P{P}_raw"] = check_table(raw, raw, P)
        info[f"P{P}_decode"] = check_table(raw, fed, P)
    return info


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tokenizer_dir", type=Path, help="folder with tokenizer.json and special_tokens_map.json")
    ap.add_argument("out", type=Path, nargs="?", default=DEFAULT_OUT, help="output JSON file")
    a = ap.parse_args(argv)

    import kronecker_embeddings
    import tokenizers

    res = run(a.tokenizer_dir)
    res["env"] = {
        "torch": torch.__version__,
        "tokenizers": tokenizers.__version__,
        "kronecker_embeddings": kronecker_embeddings.__version__,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(res, indent=2)
    a.out.write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text)
    print(f"written to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
