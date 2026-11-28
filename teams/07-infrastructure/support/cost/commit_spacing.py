"""Why commits of a run are further apart than INTERVAL_S, from its commits.jsonl and metrics.jsonl.

In simple words: for every pair of commits it splits the wall time between them into time inside training
steps (perf/step_ms), and the rest: evaluations, the save stall and per-step overhead. Intervals with one more
evaluation than the others are longer by about one evaluation, so the script also fits

    other_s = evals * eval_s + base_s        (least squares over the full intervals; the final one is left out)

    python support/cost/commit_spacing.py --commits <run>/commits.jsonl --metrics <run>/metrics.jsonl
"""
import argparse
import json


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def spacing(commits, metrics, interval_s):
    by_step = {}
    for r in metrics:
        by_step.setdefault(r["step"], {}).update(r)
    evals = {s for s, r in by_step.items() if any(k.startswith("val/") for k in r)}
    rows = []
    for a, b in zip(commits, commits[1:]):
        steps = range(a["step"] + 1, b["step"] + 1)
        step_s = sum(by_step.get(s, {}).get("perf/step_ms", 0.0) for s in steps) / 1000
        wall = b["time"] - a["time"]
        rows.append({"from": a["step"], "to": b["step"], "reason": b["reason"], "wall_s": wall,
                     "over_interval_s": wall - interval_s, "step_s": step_s, "other_s": wall - step_s,
                     "evals": sum(1 for s in steps if s in evals), "eval_at_commit": b["step"] in evals})
    full = [r for r in rows if r["reason"] == "interval"]
    n = len(full)
    mx, my = sum(r["evals"] for r in full) / n, sum(r["other_s"] for r in full) / n
    var = sum((r["evals"] - mx) ** 2 for r in full)
    eval_s = sum((r["evals"] - mx) * (r["other_s"] - my) for r in full) / var if var else None
    base_s = my - eval_s * mx if eval_s is not None else None
    return rows, eval_s, base_s


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--commits", required=True)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--interval-s", type=float, default=600.0)
    a = ap.parse_args(argv)
    rows, eval_s, base_s = spacing(read_jsonl(a.commits), read_jsonl(a.metrics), a.interval_s)
    print("| From step | To step | Wall s | Over interval s | In steps s | Other s | Evals | Eval at commit step |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['from']} | {r['to']} ({r['reason']}) | {r['wall_s']:.1f} | {r['over_interval_s']:.1f} | "
              f"{r['step_s']:.1f} | {r['other_s']:.1f} | {r['evals']} | {'yes' if r['eval_at_commit'] else 'no'} |")
    full = [r for r in rows if r["reason"] == "interval"]
    mean = sum(r["wall_s"] for r in full) / len(full)
    print(f"\nmean spacing of interval commits: {mean:.1f} s ({mean - a.interval_s:+.1f} s over {a.interval_s:.0f})")
    if eval_s is not None:
        print(f"fit over interval commits: one evaluation {eval_s:.1f} s, rest per interval {base_s:.1f} s")


if __name__ == "__main__":
    main()
