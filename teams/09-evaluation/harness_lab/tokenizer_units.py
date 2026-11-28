"""Compare how tokenizers cut the same held-out bytes (Lab 5 design 4, metric_v1.md).

    python teams/09-evaluation/harness_lab/tokenizer_units.py \
        --tokenizer p1536=<p1536>/tokenizer.json --tokenizer C3=<c3>/tokenizer.json \
        --out teams/09-evaluation/results/metric_v1/tokenizer_units.json

Reads Team 5's heldout_v1 (text + sources) and prints, per slice and per tokenizer: documents, original UTF-8 bytes,
bytes after the tokenizer's normalizer, tokens, bytes per token, documents longer than one window, and window
starts after the first (context resets under token-count windows). It also checks that decode(encode(text)) gives
the normalized text. It prints counts only, never document text. Needs `tokenizers`.
"""

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

from tokenizers import Tokenizer

HERE = Path(__file__).resolve().parent
HELDOUT = HERE.parents[1] / "05-architecture" / "heldout_v1" / "data"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def measure(texts, slices, tokenizers, window):
    rows = collections.defaultdict(collections.Counter)
    for text, name in zip(texts, slices):
        raw = len(text.encode("utf-8"))
        for label, tok in tokenizers.items():
            r = rows[(name, label)]
            norm = tok.normalizer.normalize_str(text) if tok.normalizer else text
            ids = tok.encode(text, add_special_tokens=False).ids
            starts = -(-len(ids) // window)
            r.update(docs=1, raw_bytes=raw, normalized_bytes=len(norm.encode("utf-8")),
                     docs_changed_by_normalizer=int(norm != text), tokens=len(ids),
                     docs_over_window=int(len(ids) > window), context_resets=max(starts - 1, 0),
                     round_trip_failures=int(tok.decode(ids) != norm))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer", action="append", required=True, metavar="NAME=PATH")
    ap.add_argument("--heldout", type=Path, default=HELDOUT / "heldout_v1.jsonl")
    ap.add_argument("--sources", type=Path, default=HELDOUT / "heldout_v1_sources.jsonl")
    ap.add_argument("--window", type=int, default=2048, help="token window (dry run 2 block_size)")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)

    tokenizers, tok_sha = {}, {}
    for spec in a.tokenizer:
        name, path = spec.split("=", 1)
        tokenizers[name], tok_sha[name] = Tokenizer.from_file(path), sha256(path)
    slice_of = {r["id"]: r["slice"] for r in map(json.loads, a.sources.read_text("utf-8").splitlines())}
    docs = [json.loads(line) for line in a.heldout.read_text("utf-8").splitlines()]
    rows = measure([d["text"] for d in docs], [slice_of[d["id"]] for d in docs], tokenizers, a.window)

    out = {"heldout_sha256": sha256(a.heldout), "sources_sha256": sha256(a.sources), "window": a.window,
           "tokenizer_sha256": tok_sha, "rows": []}
    for (name, label), r in sorted(rows.items()):
        out["rows"].append({"slice": name, "tokenizer": label, **r,
                            "bytes_per_token": round(r["raw_bytes"] / r["tokens"], 4)})
    totals = collections.defaultdict(collections.Counter)
    for (_, label), r in rows.items():
        totals[label].update(r)
    out["totals"] = {k: dict(v) for k, v in totals.items()}

    names = list(tokenizers)
    print(f"{'slice':6}{'docs':>6}{'raw bytes':>11}{'norm Δ':>8}" + "".join(f"{n + ' B/tok':>12}" for n in names)
          + "".join(f"{n + ' resets':>13}" for n in names))
    for name in sorted({k[0] for k in rows}):
        first = rows[(name, names[0])]
        print(f"{name:6}{first['docs']:>6}{first['raw_bytes']:>11}{first['normalized_bytes'] - first['raw_bytes']:>8}"
              + "".join(f"{rows[(name, n)]['raw_bytes'] / rows[(name, n)]['tokens']:>12.3f}" for n in names)
              + "".join(f"{rows[(name, n)]['context_resets']:>13}" for n in names))
    for n in names:
        t = totals[n]
        print(f"{n}: {t['docs']} docs, {t['raw_bytes']} raw bytes, {t['normalized_bytes']} normalized, {t['tokens']} tokens, "
              f"{t['context_resets']} context resets, {t['round_trip_failures']} round-trip failures", file=sys.stderr)
    if a.out:
        a.out.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
