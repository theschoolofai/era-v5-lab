#!/usr/bin/env python3
"""Go / no-go gates for the main run (Lab 5, lead addition 12).

Reads one run record (the folder with metrics.jsonl, as #869 commits it) plus the evidence the other teams produce, and
prints PASS, FAIL or PENDING for each gate in gates_v1.yaml. PENDING means an input does not exist yet; it is a no-go.

    python3 teams/05-architecture/lab5/go_no_go/check_gates.py --run teams/05-architecture/results/dryrun2-1234 \
        [--restart <Team 7 result.json or detail.json>] [--eval <eval_mini_v1.json>] [--eval-model lab:<run>] \
        [--fit <fit.json>] [--team9 <holds.json>] [--token-budget <tokens> --wall-hours <hours>] [--md out.md]

fit.json (lead addition 9): {"E": .., "A": .., "alpha": .., "B": .., "beta": .., "n_active": .., "holdout_error": ..}
holds.json (Team 9, #931): {"early_quality": "go" | "hold", "watcher": "go" | "hold", "evidence": "<PR or file>"}
The token budget has no default: it stays empty until the corpus-v1 token count is posted. Nothing here changes config v1.
Exit code: 0 every gate passes, 1 a gate fails, 2 no gate fails but at least one is pending.
"""
import argparse
import json
import math
import statistics
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PASS, FAIL, PENDING = "PASS", "FAIL", "PENDING"


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def read_metrics(run):
    rows = []
    for line in (Path(run) / "metrics.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def with_tokens(rows):
    """Attach the cumulative real (scored) training tokens seen up to each row's step."""
    seen, out = 0, []
    for r in sorted(rows, key=lambda r: r.get("step", 0)):
        seen += r.get("train/scored_tokens", 0) or 0
        out.append((seen, r))
    return out


# ---- gates -------------------------------------------------------------------------------------------------

def gate_health(rows, cfg):
    train = [r for r in rows if "loss" in r and r.get("step", 0) > 0]
    if not train:
        return PENDING, "no training rows"
    bad = [r["step"] for r in train if not finite(r.get("loss")) or not finite(r.get("gradient_norm", 0.0))]
    if bad:
        return FAIL, f"{len(bad)} steps with a non-finite loss or gradient norm, first at step {bad[0]}"
    return PASS, f"{len(train)} training steps, all finite"


def predict(fit, n_active, tokens):
    return fit["E"] + fit["A"] / n_active ** fit["alpha"] + fit["B"] / tokens ** fit["beta"]


def gate_loss_vs_fit(rows, cfg, fit):
    lo, hi = cfg["window"]
    evals = [(t, r["val/bpb"]) for t, r in with_tokens(rows) if "val/bpb" in r and lo <= t <= hi]
    seen = with_tokens(rows)[-1][0] if rows else 0
    if fit is None:
        return PENDING, f"no scaling-law fit yet (lead addition 9); the run has seen {seen:,} real tokens"
    if len(evals) < cfg["min_evals"]:
        return PENDING, (f"{len(evals)} evals between {lo:.3g} and {hi:.3g} tokens (need {cfg['min_evals']}); "
                         f"the run has seen {seen:,} real tokens")
    vals = [v for _, v in evals]
    measured, sd = statistics.mean(vals), statistics.stdev(vals)
    predicted = predict(fit, fit["n_active"], cfg["tokens"])
    tol = max(2 * fit["holdout_error"], 2 * sd)
    gap = measured - predicted
    msg = (f"measured {measured:.4f} bpb (mean of {len(vals)} evals, sd {sd:.4f}) vs predicted {predicted:.4f} "
           f"at {cfg['tokens']:.3g} tokens; gap {gap:+.4f}, tolerance {tol:.4f}")
    return (PASS if gap <= tol else FAIL), msg


def gate_resume(path, cfg):
    if path is None:
        return PENDING, "no Team 7 restart or restore result on the main-run config yet"
    r = json.loads(Path(path).read_text(encoding="utf-8"))
    if "schema" in r:                                    # restart_test result.json (g7-job-result/1)
        ok, optim = r.get("status") == "pass", (r.get("numbers") or {}).get("optim")
        what = f"restart_test {r.get('run_id')}: status {r.get('status')}"
    else:                                                # restore_test / restart_test detail.json
        ok, optim = r.get("pass") is True, r.get("optim")
        what = f"pass {r.get('pass')}, first_diff {json.dumps(r.get('first_diff'))[:120]}"
    if not ok:
        return FAIL, what
    if optim is not None and optim != cfg["optimizer"]:
        return FAIL, f"{what}, but the optimizer was {optim}, not {cfg['optimizer']}"
    return PASS, what + (f", optimizer {optim}" if optim else ", optimizer not recorded")


def layer_shares(counts):
    total = sum(counts)
    return [c / total for c in counts] if total else None


def gate_router(rows, cfg):
    loads = [r for r in rows if "expert_load" in r]
    if not loads:
        return PENDING, "no expert_load rows in metrics.jsonl"
    limit, after = cfg["max_busiest_over_even"], cfg["no_idle_after_step"]
    over, idle, worst = [], [], (0.0, None, None)
    for r in loads:
        for layer, counts in enumerate(r["expert_load"]):
            s = layer_shares(counts)
            if s is None:
                continue
            ratio = max(s) * len(s)                      # busiest share / even share
            if ratio > worst[0]:
                worst = (ratio, r["step"], layer)
            if ratio >= limit:
                over.append((r["step"], layer, max(s)))
            if r["step"] > after and min(counts) == 0:
                idle.append((r["step"], layer))
    n_exp = len(loads[0]["expert_load"][0])
    head = (f"worst busiest expert {worst[0]:.2f}x the even share (step {worst[1]}, layer {worst[2]}); "
            f"line {limit:g}x = {limit / n_exp:.2%} at {n_exp} experts")
    if over or idle:
        parts = [head]
        if over:
            steps = sorted({s for s, _, _ in over})
            parts.append(f"over the line at {len(over)} layer-steps, steps {steps[0]} to {steps[-1]}")
        if idle:
            parts.append(f"an expert with zero tokens after step {after} at {len(idle)} layer-steps "
                         f"(first: step {idle[0][0]}, layer {idle[0][1]})")
        return FAIL, "; ".join(parts)
    return PASS, head


def gate_eval(path, model, cfg):
    if path is None:
        return PENDING, "no eval_mini_v1 scores for the main run's step-0 checkpoint yet"
    recs = json.loads(Path(path).read_text(encoding="utf-8"))["records"]
    step0 = [r for r in recs if r.get("primary") and (model is None or r["model"] == model)
             and (r.get("checkpoint") or {}).get("step") == 0]
    if not step0:
        return PENDING, f"no primary step-0 records for {model or 'any lab model'}"
    by = {r["task"]: r for r in step0}
    bad, ok = [], []
    for task, t in cfg["tasks"].items():
        r = by.get(task)
        if r is None:
            bad.append(f"{task}: no score")
            continue
        if r["n_items"] != t["items"]:
            bad.append(f"{task}: {r['n_items']} of {t['items']} items")
            continue
        v = r["value"]
        inside = t["band"][0] <= v <= t["band"][1] or t["one_letter"][0] <= v <= t["one_letter"][1]
        (ok if inside else bad).append(f"{task} {v:.1f}")
    if bad:
        return FAIL, "outside the step-0 band or incomplete: " + ", ".join(bad)
    return PASS, "inside the step-0 band: " + ", ".join(ok)


def measured_tps(rows):
    train = [r for r in rows if r.get("step", 0) > 0 and "perf/step_ms" in r]
    tok = sum(r.get("train/scored_tokens", 0) for r in train)
    secs = sum(r["perf/step_ms"] for r in train) / 1000
    pos = sum(r.get("train/input_positions", 0) for r in train)
    return (tok / secs if secs else None), (tok / pos if pos else None)


def gate_throughput(rows, cfg, token_budget, wall_hours):
    tps, fill = measured_tps(rows)
    if tps is None:
        return PENDING, "no step times in metrics.jsonl"
    have = f"measured {tps:,.0f} real tokens/s (row fill {fill:.1%})"
    token_budget = token_budget or cfg.get("token_budget")
    wall_hours = wall_hours or cfg.get("wall_hours")
    if not (token_budget and wall_hours):
        return PENDING, have + "; the token budget and the time budget are not set, so there is no floor yet"
    need = token_budget / (wall_hours * 3600 * (1 - cfg["idle_allowance"]))
    msg = f"{have}; floor {need:,.0f} tokens/s ({token_budget:.3g} tokens in {wall_hours:g} h, {cfg['idle_allowance']:.0%} idle)"
    return (PASS if tps >= need else FAIL), msg


def gate_team9(path, cfg):
    if path is None:
        return PENDING, "no Team 9 verdict yet on early quality and watcher lag (#931)"
    r = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [c for c in cfg["checks"] if r.get(c) not in ("go", "hold")]
    if missing:
        return PENDING, "no Team 9 verdict for " + ", ".join(missing)
    held = [c for c in cfg["checks"] if r[c] == "hold"]
    ev = f" (evidence: {r['evidence']})" if r.get("evidence") else ""
    if held:
        return FAIL, "Team 9 holds on " + ", ".join(held) + ev
    return PASS, "Team 9: go on " + ", ".join(cfg["checks"]) + ev


# ---- report ------------------------------------------------------------------------------------------------

def run_gates(a, cfg):
    rows = read_metrics(a.run)
    fit = json.loads(Path(a.fit).read_text(encoding="utf-8")) if a.fit else None
    return [
        ("Run health", *gate_health(rows, cfg["run_health"])),
        ("Loss vs scaling-law prediction at 1B tokens", *gate_loss_vs_fit(rows, cfg["loss_vs_fit"], fit)),
        ("Resume test (Team 7)", *gate_resume(a.restart, cfg["resume"])),
        ("Router evenness", *gate_router(rows, cfg["router_evenness"])),
        ("Evaluation pass at step 0 (Team 9)", *gate_eval(a.eval, a.eval_model, cfg["eval_pass"])),
        ("Tokens per second", *gate_throughput(rows, cfg["throughput"], a.token_budget, a.wall_hours)),
        ("Team 9 holds: early quality, watcher lag (#931)", *gate_team9(a.team9, cfg["team9_holds"])),
    ]


def render(run, results):
    verdict = "GO" if all(s == PASS for _, s, _ in results) else "NO-GO"
    lines = [f"Gates for `{run}`: **{verdict}**", "", "| Gate | Result | Detail |", "|---|---|---|"]
    lines += [f"| {g} | {s} | {d} |" for g, s, d in results]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, help="run folder with metrics.jsonl")
    ap.add_argument("--gates", default=str(HERE / "gates_v1.yaml"))
    ap.add_argument("--restart", help="Team 7 restart_test result.json or detail.json")
    ap.add_argument("--eval", help="Team 9 eval_mini_v1.json")
    ap.add_argument("--eval-model", help="model name of the run in eval_mini, e.g. lab:<run>")
    ap.add_argument("--fit", help="scaling-law fit json (lead addition 9)")
    ap.add_argument("--team9", help="Team 9 verdicts on its two holds (#931)")
    ap.add_argument("--token-budget", type=float, help="no default; posted with the corpus-v1 token count")
    ap.add_argument("--wall-hours", type=float)
    ap.add_argument("--md", help="also write the table here")
    a = ap.parse_args(argv)
    cfg = yaml.safe_load(Path(a.gates).read_text(encoding="utf-8"))
    results = run_gates(a, cfg)
    text = render(a.run, results)
    print(text)
    if a.md:
        Path(a.md).write_text(text, encoding="utf-8")
    states = {s for _, s, _ in results}
    return 1 if FAIL in states else 2 if PENDING in states else 0


if __name__ == "__main__":
    sys.exit(main())
