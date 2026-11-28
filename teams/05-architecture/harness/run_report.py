"""Report on a G5 training run from its metrics.jsonl (train_week2.py output).

Reads only the metrics file. Prints a markdown report: training loss, held-out bits per byte
(overall and per slice), learning rate, real-token throughput and row fill, and MoE expert
load per layer when the run recorded it (--expert-load-every).

    python teams/05-architecture/harness/run_report.py out/dryrun2-1234/metrics.jsonl
    python teams/05-architecture/harness/run_report.py metrics.jsonl --out report.md
    python teams/05-architecture/harness/run_report.py metrics.jsonl --charts charts/

--charts DIR also writes the expert-load charts (Lab 5, design task 4, #892): busiest_share.svg (the
busiest expert's share per layer over the run, with TSAI's 5x failure line and the balanced
reference), busiest_share_heatmap.svg (the same numbers as a layer-by-step grid) and expert_load.md
(the table, plus every expert with zero choices and for how many logged steps in a row).
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

# TSAI's router comparison with balancing on (05 Architecture, 24 Nov 2026), router on Muon,
# bias_gamma 0.001, 1,221 steps at T2: the reference the dry run 2 expert load is read against.
REFERENCE = {"busiest_low": 0.073, "busiest_high": 0.090, "max_over_mean": 1.44, "cv": 0.105}


def read_rows(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{n}: not JSON ({e})")
    if not rows:
        raise SystemExit(f"{path}: no rows")
    return rows


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def layer_load(counts):
    """Share of the busiest expert, max/mean, coefficient of variation and dead experts, for one layer."""
    total = sum(counts)
    if total <= 0:
        return None
    m = total / len(counts)
    return {
        "busiest": max(counts) / total,
        "max_over_mean": max(counts) / m,
        "cv": statistics.pstdev(counts) / m,
        "dead": sum(1 for c in counts if c == 0),
        "experts": len(counts),
    }


def report(rows, name, summary=None):
    """summary: the run's summary.json (optional), for the wall time."""
    out = [f"# Run report: {name}", ""]
    train = [r for r in rows if "loss" in r and r.get("step", 0) > 0]
    evals = [r for r in rows if "val/bpb" in r]
    loads = [r for r in rows if "expert_load" in r]

    # Health: every loss and gradient norm finite.
    bad = [r["step"] for r in train if not finite(r.get("loss")) or not finite(r.get("gradient_norm", 0.0))]
    steps = max((r.get("step", 0) for r in rows), default=0)
    out += ["## Health", "",
            f"- Steps recorded: {len(train)} training rows, last step {steps}.",
            f"- Non-finite loss or gradient norm: {'none' if not bad else f'{len(bad)} rows, first at step {bad[0]}'}.",
            ""]

    if train:
        k = max(1, min(50, len(train) // 10))
        first, last = [r["loss"] for r in train[:k]], [r["loss"] for r in train[-k:]]
        clipped = sum(1 for r in train if r.get("gradient_clipping_applied"))
        norms = [r["gradient_norm"] for r in train if finite(r.get("gradient_norm"))]
        out += ["## Training loss", "",
                f"- Mean of the first {k} steps: {mean(first):.4f}; mean of the last {k}: {mean(last):.4f}; "
                f"lowest single step: {min(r['loss'] for r in train):.4f}.",
                f"- Gradient norm before clipping: median {statistics.median(norms):.3f}, max {max(norms):.3f}; "
                f"clipped on {clipped} of {len(train)} steps ({clipped / len(train):.1%})." if norms else "- No gradient norms.",
                ""]
        lrs = [r["lr"] for r in train if finite(r.get("lr"))]
        if lrs:
            out += ["## Learning rate", "",
                    f"- First {lrs[0]:.3g}, peak {max(lrs):.3g} (first reached at step "
                    f"{next(r['step'] for r in train if r.get('lr') == max(lrs))}), last {lrs[-1]:.3g}.", ""]
        scored = sum(r.get("train/scored_tokens", 0) for r in train)
        positions = sum(r.get("train/input_positions", 0) for r in train)
        ms = sum(r.get("perf/step_ms", 0.0) for r in train)
        if scored and ms:
            out += ["## Throughput", "",
                    f"- Real (scored) tokens per second: {scored / (ms / 1000):,.0f} over {ms / 3.6e6:.2f} h of step time.",
                    f"- Row fill: {scored:,} scored tokens in {positions:,} input positions ({scored / positions:.1%}).",
                    "- The trainer's tokens_per_second counts padded positions; the line above does not."]
            peaks = [r["gpu_peak_gb"] for r in train if finite(r.get("gpu_peak_gb")) and r["gpu_peak_gb"] > 0]
            if peaks:
                out.append(f"- Peak GPU memory: {max(peaks):.2f} GiB.")
            wall = summary.get("wall_seconds") if summary else None
            if finite(wall) and wall > 0:
                outside = wall - ms / 1000
                out.append(f"- Wall time {wall / 60:.1f} min, of which {outside / 60:.1f} min ({outside / wall:.0%}) outside "
                           "training steps (start-up, evaluations, checkpoints): the run's idle time for training.")
            out.append("")

    if evals:
        out += ["## Held-out bits per byte", "", "| Step | val/bpb |", "|---:|---:|"]
        out += [f"| {r['step']} | {r['val/bpb']:.4f} |" for r in evals]
        a, b = evals[0], evals[-1]
        slices = sorted({k.split("/")[2] for k in b if k.startswith("val/slices/") and k.endswith("/bpb")})
        if slices:
            out += ["", f"Per slice, step {a['step']} to step {b['step']}:", "",
                    "| Slice | First | Last | Change |", "|---|---:|---:|---:|"]
            for s in slices:
                x, y = a.get(f"val/slices/{s}/bpb"), b.get(f"val/slices/{s}/bpb")
                if finite(x) and finite(y):
                    out.append(f"| {s} | {x:.4f} | {y:.4f} | {y - x:+.4f} |")
        out.append("")

    out += ["## Expert load", ""]
    if not loads:
        out += ["- None recorded (the run did not pass --expert-load-every).", ""]
    else:
        out += [f"- Recorded at {len(loads)} steps (first {loads[0]['step']}, last {loads[-1]['step']}).",
                f"- Reference, TSAI 24 Nov (balanced, router on Muon): busiest expert "
                f"{REFERENCE['busiest_low']:.1%} to {REFERENCE['busiest_high']:.1%} per layer, max/mean "
                f"{REFERENCE['max_over_mean']}, CV {REFERENCE['cv']}.", ""]
        last = loads[-1]
        stats = [layer_load(c) for c in last["expert_load"]]
        n = stats[0]["experts"] if stats and stats[0] else 0
        out += [f"At step {last['step']} (fair share {1 / n:.2%} with {n} experts):" if n else "", "",
                "| Layer | Busiest expert | Max/mean | CV | Dead experts |", "|---:|---:|---:|---:|---:|"]
        for i, st in enumerate(stats):
            out.append(f"| {i} | {st['busiest']:.1%} | {st['max_over_mean']:.2f} | {st['cv']:.3f} | {st['dead']} |"
                       if st else f"| {i} | no tokens | | | |")
        out += ["", "Busiest expert over the run (worst layer at each recorded step):", "",
                "| Step | Worst busiest share | Layers with a dead expert |", "|---:|---:|---:|"]
        for r in loads:
            s = [layer_load(c) for c in r["expert_load"]]
            s = [x for x in s if x]
            out.append(f"| {r['step']} | {max(x['busiest'] for x in s):.1%} | {sum(1 for x in s if x['dead'])} |")
        out.append("")
    return "\n".join(out)


FAIL_MULTIPLE = 5  # TSAI: "A chart where one expert takes 5 times the even share is a failed router."


def busiest_table(rows):
    """[(step, [busiest share per layer], [(layer, expert) with zero choices])] for every logged step."""
    out = []
    for r in rows:
        if "expert_load" not in r:
            continue
        shares, zeros = [], []
        for li, counts in enumerate(r["expert_load"]):
            total = sum(counts)
            shares.append(max(counts) / total if total else float("nan"))
            zeros += [(li, e) for e, c in enumerate(counts) if c == 0]
        out.append((r["step"], shares, zeros))
    return out


def idle_streaks(table):
    """Every expert with zero choices, as runs of consecutive logged steps: [(layer, expert, first, last, n)]."""
    runs, open_ = [], {}
    for step, _, zeros in table:
        now = set(zeros)
        for key in list(open_):
            if key not in now:
                runs.append((*key, *open_.pop(key)))
        for key in now:
            first, _, n = open_.get(key, (step, step, 0))
            open_[key] = (first, step, n + 1)
    runs += [(*key, *v) for key, v in open_.items()]
    return sorted(runs, key=lambda r: (-r[4], r[0], r[1]))


def _svg_line_chart(table, experts):
    W, H, L, R, T, B = 760, 320, 56, 150, 20, 44
    steps = [s for s, _, _ in table]
    smax = max(steps) or 1
    top = max(0.55, max(max(v for v in sh if v == v) for _, sh, _ in table) + 0.05)
    x = lambda s: L + s / smax * (W - L - R)
    y = lambda v: T + (1 - v / top) * (H - T - B)
    even, fail = 1 / experts, FAIL_MULTIPLE / experts
    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
              "#9c755f", "#bab0ac"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="sans-serif" font-size="11">',
         f'<rect width="{W}" height="{H}" fill="white"/>']
    for v in [i / 10 for i in range(0, int(top * 10) + 1)]:
        o.append(f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#ddd"/>'
                 f'<text x="{L - 6}" y="{y(v) + 4:.1f}" text-anchor="end" fill="#666">{v:.0%}</text>')
    for s in steps[:: max(1, len(steps) // 6)] + [steps[-1]]:
        o.append(f'<text x="{x(s):.1f}" y="{H - B + 16}" text-anchor="middle" fill="#666">{s}</text>')
    o.append(f'<text x="{(L + W - R) / 2:.0f}" y="{H - 8}" text-anchor="middle" fill="#666">training step</text>')
    o.append(f'<rect x="{L}" y="{y(REFERENCE["busiest_high"]):.1f}" width="{W - L - R}" '
             f'height="{y(REFERENCE["busiest_low"]) - y(REFERENCE["busiest_high"]):.1f}" fill="#2e8b57" fill-opacity="0.18"/>')
    o.append(f'<line x1="{L}" x2="{W - R}" y1="{y(fail):.1f}" y2="{y(fail):.1f}" stroke="#c0392b" stroke-width="1.5" stroke-dasharray="6 4"/>')
    o.append(f'<line x1="{L}" x2="{W - R}" y1="{y(even):.1f}" y2="{y(even):.1f}" stroke="#666" stroke-dasharray="2 3"/>')
    for li in range(len(table[0][1])):
        pts = " ".join(f"{x(s):.1f},{y(sh[li]):.1f}" for s, sh, _ in table if sh[li] == sh[li])
        c = colors[li % len(colors)]
        o.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="1.5"/>')
        o.append(f'<text x="{W - R + 8}" y="{T + 14 * li + 10}" fill="{c}">layer {li}</text>')
    worst = " ".join(f"{x(s):.1f},{y(max(v for v in sh if v == v)):.1f}" for s, sh, _ in table)
    o.append(f'<polyline points="{worst}" fill="none" stroke="#222" stroke-width="2.5" stroke-dasharray="1 0"/>')
    n = len(table[0][1])
    o.append(f'<text x="{W - R + 8}" y="{T + 14 * n + 14}" fill="#222" font-weight="bold">worst layer</text>')
    o.append(f'<text x="{W - R + 8}" y="{T + 14 * n + 32}" fill="#c0392b">failed: {fail:.2%} (5x)</text>')
    o.append(f'<text x="{W - R + 8}" y="{T + 14 * n + 46}" fill="#2e8b57">TSAI reference</text>')
    o.append(f'<text x="{W - R + 8}" y="{T + 14 * n + 60}" fill="#666">even: {even:.2%}</text>')
    o.append("</svg>")
    return "\n".join(o)


def _svg_heatmap(table, experts):
    n = len(table[0][1])
    cw, ch, L, T = 26, 22, 70, 24
    W, H = L + cw * len(table) + 10, T + ch * n + 30
    fail = FAIL_MULTIPLE / experts

    def color(v):
        if v != v:
            return "#eee"
        if v >= fail:
            return "#c0392b"
        if v >= 0.20:
            return "#e67e22"
        if v >= 2 / experts:
            return "#f1c40f"
        return "#7fbf8f"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="sans-serif" font-size="9">',
         f'<rect width="{W}" height="{H}" fill="white"/>']
    for j, (s, sh, _) in enumerate(table):
        o.append(f'<text x="{L + cw * j + cw / 2}" y="{T - 6}" text-anchor="middle" fill="#666">{s}</text>')
        for li, v in enumerate(sh):
            o.append(f'<rect x="{L + cw * j}" y="{T + ch * li}" width="{cw - 1}" height="{ch - 1}" fill="{color(v)}">'
                     f'<title>step {s}, layer {li}: {v:.1%}</title></rect>'
                     f'<text x="{L + cw * j + cw / 2}" y="{T + ch * li + 14}" text-anchor="middle" fill="#111">{v * 100:.0f}</text>')
    for li in range(n):
        o.append(f'<text x="{L - 6}" y="{T + ch * li + 14}" text-anchor="end" fill="#444">layer {li}</text>')
    o.append(f'<text x="{L}" y="{H - 8}" fill="#666">busiest expert share (%) per layer and logged step; red at or above {fail:.2%}</text>')
    o.append("</svg>")
    return "\n".join(o)


def charts(rows, outdir):
    """Write busiest_share.svg, busiest_share_heatmap.svg and expert_load.md; return the paths written."""
    table = busiest_table(rows)
    if not table:
        raise SystemExit("No expert_load rows: run the trainer with --expert-load-every N")
    experts = len(next(r for r in rows if "expert_load" in r)["expert_load"][0])
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    fail = FAIL_MULTIPLE / experts
    md = ["# Expert load", "",
          f"Busiest expert's share of each layer's choices; even share {1 / experts:.2%} with {experts} experts; "
          f"TSAI's failure line (5 times even) {fail:.2%}.", "",
          "| Step | " + " | ".join(f"L{i}" for i in range(len(table[0][1]))) + " | Worst | Failed |",
          "|---:|" + "---:|" * (len(table[0][1]) + 1) + "---|"]
    for s, sh, _ in table:
        w = max(v for v in sh if v == v)
        md.append(f"| {s} | " + " | ".join(f"{v:.1%}" for v in sh) + f" | {w:.1%} | {'yes' if w >= fail else ''} |")
    failed = [s for s, sh, _ in table if max(v for v in sh if v == v) >= fail]
    md += ["", f"Logged steps at or above the failure line: {len(failed)} of {len(table)}"
           + (f" (first {failed[0]}, last {failed[-1]})." if failed else "."), "",
           "## Experts with zero choices", "",
           "Each row is one expert at zero choices for one or more logged steps in a row.", ""]
    streaks = idle_streaks(table)
    if streaks:
        md += ["| Layer | Expert | First logged step | Last logged step | Logged steps in a row |", "|---:|---:|---:|---:|---:|"]
        md += [f"| {l} | {e} | {a} | {b} | {n} |" for l, e, a, b, n in streaks]
    else:
        md.append("None.")
    files = {"busiest_share.svg": _svg_line_chart(table, experts),
             "busiest_share_heatmap.svg": _svg_heatmap(table, experts),
             "expert_load.md": "\n".join(md) + "\n"}
    for name, text in files.items():
        (outdir / name).write_text(text, encoding="utf-8")
    return [outdir / n for n in files]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("metrics", type=Path)
    ap.add_argument("--out", type=Path, help="also write the report here")
    ap.add_argument("--charts", type=Path, metavar="DIR", help="also write the expert-load charts and table here")
    args = ap.parse_args()
    rows = read_rows(args.metrics)
    side = args.metrics.parent / "summary.json"
    summary = json.loads(side.read_text(encoding="utf-8")) if side.exists() else None
    text = report(rows, args.metrics.parent.name or args.metrics.name, summary)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    if args.charts:
        for p in charts(rows, args.charts):
            print(f"wrote {p}")


if __name__ == "__main__":
    main()
