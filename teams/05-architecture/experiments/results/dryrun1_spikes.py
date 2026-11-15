"""Find every loss spike in a training log with the lab's two spike rules, and print the tables for dryrun1_loss.md.

Usage (from the repository root):
    python -I teams/05-architecture/experiments/results/dryrun1_spikes.py --jsonl <metrics.jsonl> [--rows 20] [--out tables.md] [--svg chart.svg]

Reads a metrics.jsonl (one JSON object per step, with step, loss_ntp, loss_mtp, gradient_norm, lr,
tokens_per_second, and val/bpb on evaluation steps) and applies:

  Team 8, spike_score (page a person): loss_ntp, loss_mtp or gradient_norm at or above the mean + 7 standard
    deviations of the trailing 1,000 clean steps, active after 100 steps; also non_finite (NaN or infinity, stop).
    Applied by importing Team 8's own AlarmMonitor from teams/08-monitoring/alarms/alarms.py, unchanged.
  Team 7, loss guard (stop the run): loss_ntp above 1.5 x the median of the last 100 clean losses (active once
    50 are in the window); spike steps are not added to the window; 3 spike steps in a row stop the run
    (exit 78, no save, the job is held for a rollback). Copied from Team 7's trainer,
    teams/07-infrastructure/support/simulation/trainer/train.py (the "loss-spike guard", ADR 0001 section 6),
    with its defaults: --spike-ratio 1.5, --spike-window 100, --spike-steps 3.

Prints (or writes with --out) three Markdown tables: the loss curve (about --rows rows, plus every spike step),
every spike with the rule that caught it and what the log shows next, and a summary with the numbers the
stability paragraph needs. With --svg it also draws the loss chart (raw loss_ntp, its 50-step moving average,
spike steps marked). Standard library only; it changes no file it reads.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # importing Team 8's alarms.py must leave no __pycache__ in their folder

CURVE_FIELDS = ("loss_ntp", "loss_mtp", "gradient_norm", "lr", "tokens_per_second")
T7_RATIO, T7_WINDOW, T7_STEPS = 1.5, 100, 3
MA = 50  # moving-average window for the chart and the summary


def moving_average(xs, n=MA):
    out, s, q = [], 0.0, collections.deque()
    for x in xs:
        q.append(x)
        s += x
        if len(q) > n:
            s -= q.popleft()
        out.append(s / len(q))
    return out


def write_svg(path, train_rows, spike_steps, title):
    """A plain SVG line chart: raw loss_ntp (light), its moving average (dark), spike steps (red marks)."""
    W, H, L, R, T, B = 900, 360, 60, 20, 30, 45
    xs = [r["step"] for r in train_rows]
    ys = [float(r["loss_ntp"]) for r in train_rows]
    ma = moving_average(ys)
    x0, x1 = min(xs), max(xs)
    y0, y1 = math.floor(min(ys)), math.ceil(max(ys))
    sx = lambda x: L + (x - x0) / max(1, x1 - x0) * (W - L - R)
    sy = lambda y: T + (y1 - y) / max(1e-9, y1 - y0) * (H - T - B)
    line = lambda vs: " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(xs, vs))
    g = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="sans-serif" font-size="12">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<text x="{L}" y="18" font-size="14" font-weight="bold">{title}</text>']
    for k in range(6):
        yv = y0 + (y1 - y0) * k / 5
        g.append(f'<line x1="{L}" x2="{W - R}" y1="{sy(yv):.1f}" y2="{sy(yv):.1f}" stroke="#e5e5e5"/>'
                 f'<text x="{L - 8}" y="{sy(yv) + 4:.1f}" text-anchor="end" fill="#555">{yv:.1f}</text>')
    for k in range(6):
        xv = round(x0 + (x1 - x0) * k / 5)
        g.append(f'<text x="{sx(xv):.1f}" y="{H - B + 18}" text-anchor="middle" fill="#555">{xv}</text>')
    g.append(f'<text x="{(L + W - R) / 2}" y="{H - 8}" text-anchor="middle" fill="#333">step</text>')
    g.append(f'<text x="14" y="{(T + H - B) / 2}" transform="rotate(-90 14 {(T + H - B) / 2})" text-anchor="middle" fill="#333">loss_ntp</text>')
    g.append(f'<polyline fill="none" stroke="#9db7d5" stroke-width="1" points="{line(ys)}"/>')
    g.append(f'<polyline fill="none" stroke="#1f4e8c" stroke-width="2.2" points="{line(ma)}"/>')
    for r in train_rows:
        if r["step"] in spike_steps:
            g.append(f'<line x1="{sx(r["step"]):.1f}" x2="{sx(r["step"]):.1f}" y1="{T}" y2="{H - B}" stroke="#c0392b" stroke-dasharray="4 3"/>'
                     f'<text x="{sx(r["step"]) + 4:.1f}" y="{T + 12}" fill="#c0392b">spike, step {r["step"]}</text>')
    g.append(f'<g transform="translate({W - R - 250},{T + 8})"><line x1="0" x2="22" y1="0" y2="0" stroke="#9db7d5"/><text x="28" y="4">loss_ntp, every step</text>'
             f'<line x1="0" x2="22" y1="18" y2="18" stroke="#1f4e8c" stroke-width="2.2"/><text x="28" y="22">{MA}-step moving average</text></g>')
    g.append("</svg>")
    Path(path).write_text("\n".join(g) + "\n", encoding="utf-8")


def load_alarms(repo_root):
    path = Path(repo_root) / "teams" / "08-monitoring" / "alarms" / "alarms.py"
    if not path.exists():
        raise SystemExit(f"Team 8's alarms.py not found at {path}; pass --repo-root")
    spec = importlib.util.spec_from_file_location("team8_alarms", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, path


def read_rows(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise SystemExit(f"{path}:{n}: not JSON ({e})")
    return rows


def team7_guard(train_rows):
    """Team 7's loss-spike guard on loss_ntp, step by step. Returns the spike events and the first stop, if any."""
    window = collections.deque(maxlen=T7_WINDOW)
    run, events, stop = 0, [], None
    for r in train_rows:
        lv = r.get("loss_ntp", r.get("loss"))
        if lv is None or not math.isfinite(float(lv)):
            events.append({"step": r["step"], "value": lv, "median": None, "run": None, "kind": "non-finite"})
            stop = stop or r["step"]
            continue
        lv = float(lv)
        if len(window) >= T7_WINDOW // 2 and lv > T7_RATIO * statistics.median(window):
            run += 1
            events.append({"step": r["step"], "value": lv, "median": statistics.median(window), "run": run, "kind": "spike"})
            if run >= T7_STEPS and stop is None:
                stop = r["step"]
        else:
            run = 0
            window.append(lv)
    return events, stop


def team8_alarms(mod, train_rows):
    monitor = mod.AlarmMonitor()
    out = []
    for r in train_rows:
        kw = {k: r[k] for k in mod.SCALAR_METRICS if k in r}
        for al in monitor.step(r["step"], **kw) or []:
            out.append(al)
    return out


def fmt(v, nd=4):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.2e}" if (abs(v) < 1e-3 and v != 0) or abs(v) >= 1e5 else f"{v:.{nd}f}"
    return str(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jsonl", required=True, help="the run's metrics.jsonl")
    ap.add_argument("--rows", type=int, default=20, help="about this many rows in the curve table (decision A3)")
    ap.add_argument("--repo-root", default=".", help="where teams/08-monitoring/ is (default: the current folder)")
    ap.add_argument("--out", help="write the tables to this Markdown file instead of printing them")
    ap.add_argument("--svg", help="also draw the loss chart to this SVG file")
    a = ap.parse_args()

    mod, alarms_path = load_alarms(a.repo_root)
    rows = read_rows(a.jsonl)
    # training rows only: the week-2 harness writes an evaluation-only step 0 without train/ce_loss
    train_rows = [r for r in rows if "loss_ntp" in r and not (r.get("step") == 0 and "train/ce_loss" not in r)]
    if not train_rows:
        raise SystemExit("no training rows with loss_ntp in the file")
    t7, t7_stop = team7_guard(train_rows)
    t8 = team8_alarms(mod, train_rows)
    t8_spikes = [x for x in t8 if x.get("rule") in ("spike_score", "non_finite")]

    steps = [r["step"] for r in train_rows]
    gaps = [(p, q) for p, q in zip(steps, steps[1:]) if q != p + 1]
    val = {r["step"]: r["val/bpb"] for r in rows if "val/bpb" in r}
    lv = [float(r["loss_ntp"]) for r in train_rows]
    ma = moving_average(lv)
    ma_at = {r["step"]: m for r, m in zip(train_rows, ma)}
    every = max(1, len(train_rows) // a.rows)
    vsteps = sorted(k for k in val if k > 0)
    if len(vsteps) > 1:  # land the rows on held-out evaluation steps, so every row has a held-out score
        d = vsteps[1] - vsteps[0]
        every = max(d, round(every / d) * d)
    spike_steps = {e["step"] for e in t7} | {x["step"] for x in t8_spikes}
    curve = [r for i, r in enumerate(train_rows) if i == 0 or r["step"] % every == 0 or i == len(train_rows) - 1 or r["step"] in spike_steps]

    sha = hashlib.sha256(Path(a.jsonl).read_bytes()).hexdigest()
    out = [f"<!-- generated by dryrun1_spikes.py from {Path(a.jsonl).name} (sha256 {sha}): {len(train_rows)} training steps -->", ""]
    out += ["### The loss curve", "",
            f"The first step, every {every} steps, the last step, and every spike step (marked *). loss_ntp is one batch, so it is noisy;"
            f" the {MA}-step moving average shows the trend.", "",
            f"| step | loss_ntp | {MA}-step average | loss_mtp | gradient_norm | lr | tokens/s | held-out bpb |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in curve:
        mark = "*" if r["step"] in spike_steps else ""
        out.append(f"| {r['step']}{mark} | {fmt(r.get('loss_ntp'))} | {fmt(ma_at[r['step']])} | " + " | ".join(fmt(r.get(k)) for k in CURVE_FIELDS[1:3]) +
                   f" | {fmt(r.get('lr'))} | {fmt(r.get('tokens_per_second'), 0)} | {fmt(val.get(r['step']))} |")
    out += ["", "### Every spike", ""]
    if not t7 and not t8_spikes:
        out.append("No spike by either rule.")
    else:
        out += ["| step | metric | value | Team 7 guard (1.5 × median of last 100, 3 in a row stops) | Team 8 spike_score (mean + 7σ of last 1,000) | what happened next |",
                "|---:|---|---:|---|---|---|"]
        by_step = collections.defaultdict(lambda: {"t7": None, "t8": []})
        for e in t7:
            by_step[e["step"]]["t7"] = e
        for x in t8_spikes:
            by_step[x["step"]]["t8"].append(x)
        for s in sorted(by_step):
            e, xs = by_step[s]["t7"], by_step[s]["t8"]
            t7txt = (f"spike {e['run']} in a row (median {fmt(e['median'])})" + (" → **stop, exit 78**" if s == t7_stop else "")) if e and e["kind"] == "spike" else ("non-finite → stop" if e else "—")
            t8txt = "; ".join(f"{x['rule']} on {x.get('metric', '')}: {x.get('detail', '')}" for x in xs) or "—"
            metric = xs[0].get("metric", "loss_ntp") if xs and not e else "loss_ntp"
            value = e["value"] if e else (xs[0].get("value") if xs else None)
            nxt = [r for r in train_rows if r["step"] > s][:1]
            nexttxt = (f"next step {nxt[0]['step']}: {metric} {fmt(nxt[0].get(metric))}; " if nxt else "last step; ") + \
                      (f"run continued to step {steps[-1]}" if t7_stop is None or t7_stop > s else "run stopped")
            out.append(f"| {s} | {metric} | {fmt(value)} | {t7txt} | {t8txt} | {nexttxt} (paging and any action: from the job log) |")
    out += ["", "### Summary", "",
            f"- Training steps read: {len(train_rows)} (steps {steps[0]} to {steps[-1]}){'; gaps: ' + ', '.join(f'{p}→{q}' for p, q in gaps) if gaps else '; no gaps'}.",
            f"- Team 7 guard: {sum(1 for e in t7 if e['kind'] == 'spike')} spike step(s); " + (f"it would have **stopped the run at step {t7_stop}**." if t7_stop is not None else "it would not have stopped the run."),
            f"- Team 8: {sum(1 for x in t8_spikes if x['rule'] == 'spike_score')} spike_score alarm(s), {sum(1 for x in t8_spikes if x['rule'] == 'non_finite')} non_finite; other Team 8 warnings: {len(t8) - len(t8_spikes)}.",
            f"- Team 8's code: {alarms_path.as_posix()}.",
            f"- loss_ntp: first step {fmt(float(train_rows[0]['loss_ntp']))}, last step {fmt(float(train_rows[-1]['loss_ntp']))}, lowest {fmt(min(lv))} (step {train_rows[lv.index(min(lv))]['step']}).",
            f"- {MA}-step moving average of loss_ntp: {fmt(ma[MA - 1])} at step {steps[MA - 1]}, {fmt(ma[len(ma) // 2])} at step {steps[len(ma) // 2]}, {fmt(ma[-1])} at step {steps[-1]}." if len(ma) >= MA else f"- fewer than {MA} steps: no moving average.",
            "- Held-out bpb: " + (f"{fmt(val[min(val)])} at step {min(val)} → {fmt(val[max(val)])} at step {max(val)} ({len(val)} evaluations; lowest {fmt(min(val.values()))} at step {min(val, key=val.get)})" if val else "not in the log") + "."]
    if a.svg:
        write_svg(a.svg, train_rows, spike_steps, f"Loss curve, {Path(a.jsonl).parent.name or Path(a.jsonl).name}")
        out.append(f"- Chart: {Path(a.svg).name}.")
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        sys.stdout.buffer.write(text.encode("utf-8"))  # UTF-8 on every console (Windows cp1252 cannot print the sigma sign)


if __name__ == "__main__":
    main()
