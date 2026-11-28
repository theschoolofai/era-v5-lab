#!/usr/bin/env python3
"""Add per-batch composition and data position to dry run 2's metrics.jsonl (Week 5, Team 08 task 1).

dryrun2-1234 (#869) did not log what each batch was made of. Its record says how it was fed: "Training text of this
run was one English web shard of 25M tokens, not the sample-v0 mix" (teams/05-architecture/results/dryrun2-1234/
README.md). So every training batch is 100% `english` and the native Indic share is 0, by the record, not measured per
batch. The data position comes from the counts the run did log for each step:

- `data_tokens_seen`: running sum of `train/input_positions` (token positions fed to the model);
- `data_bytes_seen`:  running sum of `train/utf8_bytes` (UTF-8 bytes of the scored text);
- `data_epoch`:       `data_tokens_seen` / the shard's 25,000,000 tokens (the README's round figure).

Words are not in the record (no text), so `lane_share_words` and `data_words_seen` are left out, not guessed.

The output is the run's own rows with these fields added, in the same order, so the alarms and the ClickHouse loader
read one file for the run (reloading a run_id replaces all its rows). Rows with no training counts (step 0, the
evaluation-only row) are passed through unchanged.

    python -I teams/08-monitoring/metrics_logger/dryrun2_composition.py \\
        teams/05-architecture/results/dryrun2-1234/metrics.jsonl --out ./out/dryrun2-1234/metrics.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from composition import DataPosition  # noqa: E402

SHARD_TOKENS = 25_000_000  # README: "one English web shard of 25M tokens"
LANE = "english"           # README: one English web shard


def add_composition(lines, shard_tokens: float = SHARD_TOKENS, lane: str = LANE):
    """Yield the run's rows (dicts) with composition and data position added to every training row."""
    position = DataPosition(corpus_tokens=shard_tokens)
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue  # a torn last line from a killed run
        tokens, nbytes = row.get("train/input_positions"), row.get("train/utf8_bytes")
        if isinstance(tokens, (int, float)) and not isinstance(tokens, bool) and tokens > 0:
            row["indic_share"] = 1.0 if lane == "indic" else 0.0
            row["lane_share_tokens"] = {lane: 1.0}
            if isinstance(nbytes, (int, float)) and not isinstance(nbytes, bool) and nbytes > 0:
                row["lane_share_bytes"] = {lane: 1.0}
            row.update(position.update(tokens=tokens, bytes=nbytes or 0, words=None))
        yield row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Add composition and data position to dry run 2's metrics.jsonl.")
    ap.add_argument("metrics", type=Path, help="dryrun2-1234 metrics.jsonl (#869)")
    ap.add_argument("--out", type=Path, required=True, help="where to write the merged metrics.jsonl")
    ap.add_argument("--shard-tokens", type=float, default=SHARD_TOKENS)
    args = ap.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    n = with_comp = 0
    with open(args.metrics, encoding="utf-8") as src, open(args.out, "w", encoding="utf-8") as dst:
        for row in add_composition(src, shard_tokens=args.shard_tokens):
            n += 1
            with_comp += "indic_share" in row
            dst.write(json.dumps(row) + "\n")
    print(f"wrote {n} rows to {args.out}: {with_comp} with composition and data position", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
