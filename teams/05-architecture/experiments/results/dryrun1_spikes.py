"""Find every loss spike in a training log with the lab's two spike rules, and print the tables for dryrun1_loss.md.

Usage (from the repository root):
    python -I teams/05-architecture/experiments/results/dryrun1_spikes.py --jsonl <metrics.jsonl> [--rows 20] [--out tables.md]

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
every spike with the rule that caught it, and a summary. Standard library only; it changes no file it reads.
"""
import argparse
import collections
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path

CURVE_FIELDS = ("loss_ntp", "loss_mtp", "gradient_norm", "lr", "tokens_per_second")
T7_RATIO, T7_WINDOW, T7_STEPS = 1.5, 100, 3


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
    every = max(1, len(train_rows) // a.rows)
    spike_steps = {e["step"] for e in t7} | {x["step"] for x in t8_spikes}
    curve = [r for i, r in enumerate(train_rows) if i % every == 0 or i == len(train_rows) - 1 or r["step"] in spike_steps]
    val = {r["step"]: r["val/bpb"] for r in rows if "val/bpb" in r}

    out = [f"<!-- generated by dryrun1_spikes.py from {Path(a.jsonl).name}: {len(train_rows)} training steps -->", ""]
    out += ["### The loss curve", "",
            f"Every {every} steps, the last step, and every spike step (marked *).", "",
            "| step | loss_ntp | loss_mtp | gradient_norm | lr | tokens/s | held-out bpb |",
            "|---:|---:|---:|---:|---:|---:|---:|"]
    for r in curve:
        mark = "*" if r["step"] in spike_steps else ""
        out.append(f"| {r['step']}{mark} | " + " | ".join(fmt(r.get(k)) for k in CURVE_FIELDS[:3]) +
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
            out.append(f"| {s} | {metric} | {fmt(value)} | {t7txt} | {t8txt} | (from the job log) |")
    out += ["", "### Summary", "",
            f"- Training steps read: {len(train_rows)} (steps {steps[0]} to {steps[-1]}){'; gaps: ' + ', '.join(f'{p}→{q}' for p, q in gaps) if gaps else '; no gaps'}.",
            f"- Team 7 guard: {sum(1 for e in t7 if e['kind'] == 'spike')} spike step(s); " + (f"it would have **stopped the run at step {t7_stop}**." if t7_stop is not None else "it would not have stopped the run."),
            f"- Team 8: {sum(1 for x in t8_spikes if x['rule'] == 'spike_score')} spike_score alarm(s), {sum(1 for x in t8_spikes if x['rule'] == 'non_finite')} non_finite; other Team 8 warnings: {len(t8) - len(t8_spikes)}.",
            f"- Team 8's code: {alarms_path.as_posix()}."]
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
