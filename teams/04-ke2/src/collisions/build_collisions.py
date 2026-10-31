#!/usr/bin/env python3
"""KE2 collisions: per-script collision audit of the byte tables.

Definition: two token IDs *collide* at pos_dim P under an extraction if their
table rows (bytes after truncation to P) are identical. Identical rows give
identical Kronecker codes, so the model cannot tell the tokens apart.

Extractions (tables from src/build_tables.py / the ke2 package):
  decode — upstream kronecker-embeddings behaviour, tokenizer.decode([id])
  raw    — exact bytes via the inverted ByteLevel alphabet (the KE2 fix)

Every collision group gets one cause:
  empty           a member has zero bytes (every empty row is the zero vector)
  duplicate_vocab members' true bytes are identical (two vocab entries, same bytes)
  special_literal as above, but a special token's literal text equals a normal token
  decode_collapse true bytes differ, extraction bytes already equal before
                  truncation, and the shared bytes contain U+FFFD
  truncation      extraction bytes differ before truncation, equal after cutting to P
  other           none of the above  -> gate: must be zero

Outputs (default: teams/04-ke2/results/):
  collisions.csv          one row per group
  collisions_summary.csv  per (extraction, P, script_class) counts and rate
  collisions_meta.json    provenance + totals + gate

Usage:
  python build_collisions.py [--tokenizer PATH_OR_HF_ID] [--out DIR] [--allow-download]
Tokenizer lookup (no flag): $KE2_TOKENIZER, $BRAHMIC_TOKENIZER_DIR, then the HF cache.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent  # teams/04-ke2/src/collisions
SRC = HERE.parent  # teams/04-ke2/src (ke2 package, build_tables.py)
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import build_tables as bt  # noqa: E402
from ke2.config import HF_ID, TOKENIZER_SHA256  # noqa: E402
from ke2.config import RESULTS_DIR as RESULTS  # noqa: E402  (teams/04-ke2/results)

CAUSES = ("empty", "duplicate_vocab", "special_literal", "decode_collapse", "truncation", "other")

GROUP_COLUMNS = [
    "extraction",
    "P",
    "group_id",
    "cause",
    "script_class",
    "member_classes",
    "n_tokens",
    "token_ids",
    "bytes_hex",
    "byte_len",
    "true_bytes_hex_examples",
]
SUMMARY_COLUMNS = [
    "extraction",
    "P",
    "script_class",
    "n_tokens",
    "n_colliding_tokens",
    "n_excess_tokens",
    "rate_colliding",
]
N_EXAMPLES = 5


# --------------------------------------------------------------------------- #
# Cause labelling (pure function: unit-testable without a tokenizer)
# --------------------------------------------------------------------------- #
def label_cause(
    true_bytes: Sequence[bytes], untruncated: Sequence[bytes], truncated: bytes, is_special: Sequence[bool]
) -> str:
    """Cause of one collision group.

    true_bytes  : exact bytes of each member (raw, untruncated)
    untruncated : each member's bytes under the extraction, before truncation
    truncated   : the shared table row (after truncation to P)
    is_special  : per member
    """
    if len(truncated) == 0 or any(len(b) == 0 for b in untruncated):
        return "empty"
    if len(set(true_bytes)) == 1:
        if any(is_special) and not all(is_special):
            return "special_literal"
        return "duplicate_vocab"
    if len(set(untruncated)) == 1:
        return "decode_collapse" if bt.U_FFFD in untruncated[0] else "other"
    return "truncation"


# --------------------------------------------------------------------------- #
# Core computation
# --------------------------------------------------------------------------- #
@dataclass
class Group:
    extraction: str
    P: int
    group_id: int
    cause: str
    ids: list[int]
    row: bytes
    member_classes: dict[str, int]

    @property
    def script_class(self) -> str:
        if len(self.member_classes) == 1:
            return next(iter(self.member_classes))
        return f"multiple({len(self.member_classes)})"


@dataclass
class Audit:
    tokenizer_sha256: str
    vocab_size: int
    classes: list[str]  # per token id (detail=True)
    groups: list[Group] = field(default_factory=list)
    summary: list[dict] = field(default_factory=list)


def untruncated_bytes(tb, kind: str, tid: int) -> bytes:
    if kind == "raw":
        return bt.raw_bytes_for_id(tb, tid)
    if kind == "decode":
        return bt.decode_bytes_for_id(tb, tid)
    raise ValueError(kind)


def classify(tb) -> list[str]:
    return [
        bt.script_class(bt.raw_bytes_for_id(tb, i), is_special=i in tb.special_ids, detail=True)
        for i in range(tb.vocab_size)
    ]


def find_groups(table) -> list[list[int]]:
    """Token-id lists that share an identical row (size >= 2), sorted by first id."""
    by_row = collections.defaultdict(list)
    for i in range(table.vocab_size):
        by_row[table.row(i)].append(i)
    return sorted((ids for ids in by_row.values() if len(ids) > 1), key=lambda g: g[0])


def audit(tb, tables: dict[tuple[str, int], object]) -> Audit:
    classes = classify(tb)
    a = Audit(tokenizer_sha256=tb.sha256, vocab_size=tb.vocab_size, classes=classes)
    true = {}  # cache raw bytes for members only

    for kind, P in sorted(tables, key=lambda k: (k[0], k[1])):
        t = tables[kind, P]
        groups = find_groups(t)
        colliding = set()
        for gid, ids in enumerate(groups):
            for i in ids:
                if i not in true:
                    true[i] = bt.raw_bytes_for_id(tb, i)
            cause = label_cause(
                true_bytes=[true[i] for i in ids],
                untruncated=[untruncated_bytes(tb, kind, i) for i in ids],
                truncated=t.row(ids[0]),
                is_special=[i in tb.special_ids for i in ids],
            )
            mc = collections.Counter(classes[i] for i in ids)
            a.groups.append(Group(kind, P, gid, cause, ids, t.row(ids[0]), dict(mc.most_common())))
            colliding.update(ids)

        # per-class summary (every class appears, even with zero collisions)
        n_tok = collections.Counter(classes)
        n_col = collections.Counter(classes[i] for i in colliding)
        # excess = tokens beyond the first in each group, attributed to members' classes
        n_exc = collections.Counter()
        for ids in groups:
            for i in ids[1:]:
                n_exc[classes[i]] += 1
        for cls in sorted(n_tok):
            a.summary.append(
                {
                    "extraction": kind,
                    "P": P,
                    "script_class": cls,
                    "n_tokens": n_tok[cls],
                    "n_colliding_tokens": n_col[cls],
                    "n_excess_tokens": n_exc[cls],
                    "rate_colliding": round(n_col[cls] / n_tok[cls], 6),
                }
            )
    return a


def totals(a: Audit) -> dict:
    out = {}
    for g in a.groups:
        k = f"{g.extraction}_P{g.P}"
        d = out.setdefault(
            k,
            {
                "n_groups": 0,
                "n_tokens_in_groups": 0,
                "n_excess_tokens": 0,
                "largest_group": 0,
                "causes": collections.Counter(),
            },
        )
        d["n_groups"] += 1
        d["n_tokens_in_groups"] += len(g.ids)
        d["n_excess_tokens"] += len(g.ids) - 1
        d["largest_group"] = max(d["largest_group"], len(g.ids))
        d["causes"][g.cause] += 1
    for row in a.summary:  # make sure zero-collision tables still appear
        out.setdefault(
            f"{row['extraction']}_P{row['P']}",
            {
                "n_groups": 0,
                "n_tokens_in_groups": 0,
                "n_excess_tokens": 0,
                "largest_group": 0,
                "causes": collections.Counter(),
            },
        )
    for d in out.values():
        d["causes"] = dict(d["causes"])
    return dict(sorted(out.items()))


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def group_rows(a: Audit, tb) -> list[dict]:
    rows = []
    for g in a.groups:
        rows.append(
            {
                "extraction": g.extraction,
                "P": g.P,
                "group_id": g.group_id,
                "cause": g.cause,
                "script_class": g.script_class,
                "member_classes": ";".join(f"{c}:{n}" for c, n in g.member_classes.items()),
                "n_tokens": len(g.ids),
                "token_ids": ";".join(map(str, g.ids)),
                "bytes_hex": g.row.hex(),
                "byte_len": len(g.row),
                "true_bytes_hex_examples": ";".join(bt.raw_bytes_for_id(tb, i).hex() for i in g.ids[:N_EXAMPLES]),
            }
        )
    return rows


def tokenizer_name(tb, override: str | None = None) -> str:
    """A portable name for the tokenizer (never a local path): the HF id for the pinned file."""
    if override:
        return override
    if tb.sha256 == TOKENIZER_SHA256:
        return HF_ID
    return f"local {Path(tb.path).name} (identified by tokenizer_sha256)"


def write_outputs(a: Audit, tb, out_dir: Path, name: str | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "collisions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=GROUP_COLUMNS)
        w.writeheader()
        w.writerows(group_rows(a, tb))
    with open(out_dir / "collisions_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_COLUMNS)
        w.writeheader()
        w.writerows(a.summary)
    tot = totals(a)
    meta = {
        "tokenizer": tokenizer_name(tb, name),
        "tokenizer_sha256": a.tokenizer_sha256,
        "vocab_size": a.vocab_size,
        "definition": "collision = identical table row (bytes after truncation to P)",
        "truncation": {"raw": "bytes[:P]", "decode": "utf8_safe_truncate (upstream)"},
        "versions": _versions(),
        "totals": tot,
        "n_other_groups": sum(d["causes"].get("other", 0) for d in tot.values()),
    }
    meta["gate_zero_other"] = meta["n_other_groups"] == 0
    (out_dir / "collisions_meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def _versions() -> dict:
    v = {}
    for m in ("tokenizers", "numpy", "kronecker_embeddings"):
        try:
            v[m] = __import__(m).__version__
        except Exception:
            v[m] = None
    return v


def print_report(a: Audit, meta: dict) -> None:
    print(f"tokenizer  {meta['tokenizer']}")
    print(f"sha256     {a.tokenizer_sha256}")
    print(f"V          {a.vocab_size}\n")
    print(f"{'table':<10} {'groups':>6} {'in_groups':>9} {'excess':>6} {'largest':>7}  causes")
    for k, d in meta["totals"].items():
        print(
            f"{k:<10} {d['n_groups']:>6} {d['n_tokens_in_groups']:>9} {d['n_excess_tokens']:>6} "
            f"{d['largest_group']:>7}  {d['causes']}"
        )
    print("\nper script class (colliding tokens / tokens), P=32")
    rows = [r for r in a.summary if r["P"] == 32]
    by_cls = collections.defaultdict(dict)
    for r in rows:
        by_cls[r["script_class"]][r["extraction"]] = (r["n_colliding_tokens"], r["n_tokens"])
    print(f"  {'script_class':<52} {'raw':>14} {'decode':>14}")
    for cls in sorted(by_cls, key=lambda c: -by_cls[c].get("raw", (0, 0))[1]):
        rw = by_cls[cls].get("raw", (0, 0))
        dc = by_cls[cls].get("decode", (0, 0))
        print(f"  {cls:<52} {rw[0]:>6}/{rw[1]:<7} {dc[0]:>6}/{dc[1]:<7}")
    print(f"\ngate (zero 'other' groups): {'PASS' if meta['gate_zero_other'] else 'FAIL'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer", default=None, help="tokenizer.json / dir / HF id")
    ap.add_argument("--out", default=str(RESULTS))
    ap.add_argument("--tokenizer-name", default=None, help="name recorded in collisions_meta.json (default: HF id)")
    ap.add_argument("--allow-download", action="store_true", help="fetch the tokenizer from the HF Hub if needed")
    args = ap.parse_args(argv)

    tb = bt.load_tokenizer(args.tokenizer, allow_download=args.allow_download)
    tables = {}
    for P in bt.POS_DIMS:
        tables["decode", P] = bt.build_decode_table(tb, P)
        tables["raw", P] = bt.build_raw_table(tb, P)
    a = audit(tb, tables)
    meta = write_outputs(a, tb, Path(args.out), args.tokenizer_name)
    print_report(a, meta)
    print(f"\nwrote {Path(args.out).resolve()}")
    return 0 if meta["gate_zero_other"] else 1


if __name__ == "__main__":
    sys.exit(main())
