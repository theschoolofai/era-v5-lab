#!/usr/bin/env python3
"""Paired comparison of each quantized format with bf16 on eval_mini, item by item.

    python paired.py runs/ --base bf16 [--out paired.md]

Reads runs/<format>/<task>_<k>shot.samples.jsonl (written by run_mini_gguf.py) and compares every format with
the base on the SAME items. Comparing two accuracies with their own standard errors (as compare_v0.md does for
models) needs gaps of ~2 points per 400 items; pairing removes the item-to-item variation both runs share, so a
much smaller real change becomes measurable.

Per task, on its primary metric (G9's choice: acc_norm for ARC-C and HellaSwag, acc for MMLU and TruthfulQA-mc2,
exact_match with the flexible-extract filter for GSM8K):
  0/1 metrics:      b = items right in base but wrong in the format, c = the reverse; difference = (c - b) / n,
                    95% CI from the paired variance; p from McNemar's exact test on b and c.
  TruthfulQA-mc2:   acc is a probability share per item; mean of the per-item differences, 95% CI, no p-value.
MMLU's 57 subjects are pooled into one row.
"""
from __future__ import annotations

import argparse, json, math
from collections import defaultdict
from pathlib import Path

PRIMARY = {"arc_challenge": ("acc_norm", "none"), "arc_easy": ("acc_norm", "none"), "hellaswag": ("acc_norm", "none"),
           "mmlu": ("acc", "none"), "gsm8k": ("exact_match", "flexible-extract"), "truthfulqa_mc2": ("acc", "none")}
BINARY = {"arc_challenge", "arc_easy", "hellaswag", "mmlu", "gsm8k"}


def group(task: str) -> str:
    return "mmlu" if task.startswith("mmlu") else task


def load(fmt_dir: Path) -> dict[str, dict[tuple, float]]:
    """{group task: {(leaf task, doc_id): primary metric value}}"""
    out = defaultdict(dict)
    for f in sorted(fmt_dir.glob("*.samples.jsonl")):
        for line in open(f):
            r = json.loads(line)
            g = group(r["task"])
            if g not in PRIMARY:
                continue
            metric, filt = PRIMARY[g]
            if r.get("filter", "none") == filt and metric in r:
                out[g][(r["task"], r["doc_id"])] = float(r[metric])
    return out


def mcnemar_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def compare(base: dict[tuple, float], other: dict[tuple, float], binary: bool) -> dict:
    keys = sorted(base.keys() & other.keys())
    n = len(keys)
    if n == 0:
        return {"n": 0}
    x, y = [base[k] for k in keys], [other[k] for k in keys]
    res = {"n": n, "base": sum(x) / n, "fmt": sum(y) / n, "missing": len(base.keys() ^ other.keys())}
    if binary:
        b = sum(1 for p, q in zip(x, y) if p == 1 and q == 0)
        c = sum(1 for p, q in zip(x, y) if p == 0 and q == 1)
        diff = (c - b) / n
        se = math.sqrt(max((b + c) - (c - b) ** 2 / n, 0)) / n
        res.update(diff=diff, lo=diff - 1.96 * se, hi=diff + 1.96 * se, b=b, c=c, p=mcnemar_p(b, c))
    else:
        d = [q - p for p, q in zip(x, y)]
        mean = sum(d) / n
        sd = math.sqrt(sum((v - mean) ** 2 for v in d) / (n - 1)) if n > 1 else 0.0
        res.update(diff=mean, lo=mean - 1.96 * sd / math.sqrt(n), hi=mean + 1.96 * sd / math.sqrt(n))
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", type=Path)
    ap.add_argument("--base", default="bf16")
    ap.add_argument("--out", type=Path, help="also write the markdown table here")
    args = ap.parse_args()

    base = load(args.runs / args.base)
    lines = [f"Paired against **{args.base}** on the same items. Differences in points (format minus base); "
             "b = right in base, wrong in format; c = the reverse.", "",
             "| Format | Task | n | Base | Format | Difference (95% CI) | b / c | McNemar p |",
             "|---|---|---|---|---|---|---|---|"]
    for fmt_dir in sorted(p for p in args.runs.iterdir() if p.is_dir() and p.name != args.base):
        other = load(fmt_dir)
        for task in PRIMARY:
            if task not in base or task not in other:
                continue
            r = compare(base[task], other[task], task in BINARY)
            if not r["n"]:
                continue
            pts = lambda v: f"{100 * v:+.1f}"
            bc = f"{r['b']} / {r['c']}" if "b" in r else "-"
            p = f"{r['p']:.3f}" if "p" in r else "-"
            warn = f" ({r['missing']} items unmatched)" if r["missing"] else ""
            lines.append(f"| {fmt_dir.name} | {task}{warn} | {r['n']} | {100 * r['base']:.1f} | {100 * r['fmt']:.1f} | "
                         f"{pts(r['diff'])} ({pts(r['lo'])} to {pts(r['hi'])}) | {bc} | {p} |")
    text = "\n".join(lines)
    print(text)
    if args.out:
        args.out.write_text(text + "\n")


if __name__ == "__main__":
    main()
