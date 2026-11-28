"""Design 6 (Lab 5): where a training run waits. Two measurements, one JSON each.

within  -- inside one run, per step, on the GPU timeline (CUDA events, no sync inside the steps):
    host_gap_ms   GPU idle from the end of step i-1 to the moment the host enters next_batch for step i
                  (Python and bookkeeping between steps).
    loader_ms     from entering next_batch to the batch being on the GPU: the loader's host work the GPU
                  waited for, plus the host-to-device copy. With data.prefetch the host work was done during
                  the previous step, so this is mostly the copy.
    step_ms       from the batch being on the GPU to the end of step i (forward, backward, optimizer).
  GPU utilisation from perfkit.metrics.GpuSampler (nvidia-smi, 1 s samples) over the same steps.
  On CPU there is no GPU timeline: the gaps are reported as null and only host times are kept.

between -- across a finished run, from its record files: wall time not inside measured steps.
    Reads summary.json (wall_seconds) and metrics.jsonl (perf/step_ms) as written by the G5 trainer
    (dry run 2, class #869).

  python -B perfkit/waste.py within --config configs/base.yaml --steps 100 --warmup 10 data.prefetch=false
  python -B perfkit/waste.py between --run-dir <dir with summary.json and metrics.jsonl>
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models.config import load_config  # noqa: E402
from perfkit import bench as B  # noqa: E402
from perfkit import metrics as M  # noqa: E402
from perfkit import timer as T  # noqa: E402


def _stats(xs):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    if not xs:
        return None
    st = T.stats(xs)
    return {k: round(st[k], 4) for k in ("median", "p10", "p90", "mean", "min", "max", "n")} | {
        "sum": round(sum(xs), 4)}


def within(config: str, overrides: list, steps: int, warmup: int, gap_floor_ms: float) -> dict:
    """Run warmup + steps training steps and time the gaps between them on the GPU timeline."""
    cfg = load_config(config, overrides)
    device = B.pick_device(cfg["run"]["device"])
    s = B.build(cfg, device)
    cuda = device.type == "cuda"

    marks = {}                                   # per step: CUDA events (or host times on CPU)
    orig_next = s.loader.next_batch

    def stamp():
        if cuda:
            e = torch.cuda.Event(enable_timing=True)
            e.record()
            return e
        return time.perf_counter()

    def next_batch_marked():
        marks["enter"] = stamp()
        out = orig_next()
        marks["ready"] = stamp()
        return out

    s.loader.next_batch = next_batch_marked
    for _ in range(warmup):
        B.train_step(s)
    if cuda:
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)

    rows, prev_end = [], None
    t_start = time.perf_counter()
    with M.GpuSampler(device) as sampler:
        prev_end = stamp()
        for i in range(steps):
            if hasattr(sampler, "set_step"):
                sampler.set_step(i + 1)
            data_ms, _ = B.train_step(s)
            end = stamp()
            rows.append({"step": i + 1, "data_host_ms": data_ms, "prev_end": prev_end,
                         "enter": marks["enter"], "ready": marks["ready"], "end": end})
            prev_end = end
        if cuda:
            torch.cuda.synchronize(device)
    wall_s = time.perf_counter() - t_start
    s.loader.next_batch = orig_next

    def ms(a, b):
        if cuda:
            return a.elapsed_time(b)
        return (b - a) * 1e3

    per_step = []
    for r in rows:
        host_gap, loader, step = ms(r["prev_end"], r["enter"]), ms(r["enter"], r["ready"]), ms(r["ready"], r["end"])
        per_step.append({"step": r["step"], "host_gap_ms": round(host_gap, 4) if cuda else None,
                         "loader_ms": round(loader, 4) if cuda else None, "step_ms": round(step, 4),
                         "data_host_ms": round(r["data_host_ms"], 4)})
    total = sum(p["step_ms"] + (p["host_gap_ms"] or 0) + (p["loader_ms"] or 0) for p in per_step)
    gap_total = sum((p["host_gap_ms"] or 0) + (p["loader_ms"] or 0) for p in per_step)
    stalled = sum(1 for p in per_step if (p["loader_ms"] or 0) > gap_floor_ms) if cuda else None

    tokens = s.loader.B * s.loader.T
    med_cycle = _stats([p["step_ms"] + (p["host_gap_ms"] or 0) + (p["loader_ms"] or 0) for p in per_step])
    rates = B.throughput_rates(med_cycle["median"], positions_per_step=tokens, scored_tokens_per_step=tokens,
                               scored_bytes_per_step=float(tokens)) if med_cycle else {}
    commit, dirty = M.git_state()
    return {
        "measure": "design6_within",
        "command": "python -B perfkit/waste.py within " + " ".join(
            ["--config", config, "--steps", str(steps), "--warmup", str(warmup)] + list(overrides)),
        "gpu": M.device_name(device), "device": device.type, "dtype": s.dtype, "commit": commit, "dirty": dirty,
        "torch": torch.__version__,
        "shape": {"B": s.loader.B, "T": s.loader.T, "positions_per_step": tokens},
        "data": {"source": cfg["data"]["source"], "prefetch": bool(cfg["data"]["prefetch"])},
        "steps": steps, "warmup": warmup, "wall_s": round(wall_s, 3),
        "host_gap_ms": _stats([p["host_gap_ms"] for p in per_step]),
        "loader_ms": _stats([p["loader_ms"] for p in per_step]),
        "step_ms": _stats([p["step_ms"] for p in per_step]),
        "cycle_ms": med_cycle,
        "data_host_ms": _stats([p["data_host_ms"] for p in per_step]),
        "gpu_wait_share_pct": round(100.0 * gap_total / total, 3) if cuda and total > 0 else None,
        "steps_with_loader_over_floor": stalled, "gap_floor_ms": gap_floor_ms,
        "positions_per_s_from_cycle": round(rates.get("positions_per_s", float("nan")), 2) if rates else None,
        "peak_memory": M.memory(device),
        "gpu_sampler": sampler.summary(),
        "per_step": per_step,
        "notes": ["loader_ms includes the host-to-device copy of one [B, T+1] int64 batch and the two device-side slice copies",
                  "positions_per_s_from_cycle uses the full cycle (gap + loader + step), not perfkit's step time",
                  "scored tokens = positions: this loader has no document mask"],
    }


def between(run_dir: str) -> dict:
    """Wall time a finished run spent outside its measured steps (G5 trainer record files)."""
    d = Path(run_dir)
    summary = json.loads((d / "summary.json").read_text())
    step_ms, positions, scored, by_step, eval_steps = [], [], [], {}, []
    for line in (d / "metrics.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if any(k.startswith("val/") for k in r) and "step" in r:
            eval_steps.append(r["step"])        # the trainer evaluates after this step, outside perf/step_ms
        if "perf/step_ms" in r:
            step_ms.append(r["perf/step_ms"])
            positions.append(r.get("train/input_positions"))
            scored.append(r.get("train/scored_tokens"))
            if "step" in r:
                by_step[r["step"]] = r["perf/step_ms"]
    wall = summary["wall_seconds"]
    in_steps = sum(step_ms) / 1e3
    fill = [s / p for s, p in zip(scored, positions) if s is not None and p]
    out = {
        "measure": "design6_between", "run_dir": str(d), "run_id": summary.get("run_id"),
        "status": summary.get("status"), "steps": len(step_ms),
        "wall_s": round(wall, 3), "in_steps_s": round(in_steps, 3),
        "outside_steps_s": round(wall - in_steps, 3),
        "outside_steps_pct": round(100.0 * (wall - in_steps) / wall, 3) if wall else None,
        "step_ms": _stats(step_ms),
        "fill_scored_over_positions": {k: v for k, v in (_stats(fill) or {}).items() if k != "sum"},
        "notes": ["outside_steps covers startup, evaluation, checkpoint saves and anything else not in perf/step_ms"],
    }
    commits = d / "commits.jsonl"
    if commits.exists() and by_step:
        # checkpoint commit times split the run into intervals: wall between two commits vs the step time inside
        cs = [json.loads(x) for x in commits.read_text().splitlines() if x.strip()]
        cs = sorted((c for c in cs if "time" in c and "step" in c), key=lambda c: c["step"])
        rows = []
        for a, b in zip(cs, cs[1:]):
            iv_wall = b["time"] - a["time"]
            iv_steps = sum(v for k, v in by_step.items() if a["step"] < k <= b["step"]) / 1e3
            rows.append({"from_step": a["step"], "to_step": b["step"], "wall_s": round(iv_wall, 3),
                         "in_steps_s": round(iv_steps, 3), "outside_steps_s": round(iv_wall - iv_steps, 3),
                         "evals": sum(1 for e in eval_steps if a["step"] < e <= b["step"])})
        span = cs[-1]["time"] - cs[0]["time"] if len(cs) > 1 else None
        out["commit_intervals"] = rows
        out["eval_steps"] = len(eval_steps)
        full = rows[:-1] if len(rows) > 2 else rows            # the last interval ends early (run end)
        xs, ys = [r["evals"] for r in full], [r["outside_steps_s"] for r in full]
        if len(set(xs)) > 1:                     # outside = fixed + per_eval * evals, least squares
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            per_eval = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
            out["fit_outside_vs_evals"] = {"per_eval_s": round(per_eval, 2),
                                           "fixed_per_interval_s": round(my - per_eval * mx, 2),
                                           "intervals_used": len(full),
                                           "note": "fit over checkpoint intervals except the last (shorter)"}
        out["first_to_last_commit_s"] = round(span, 3) if span is not None else None
        out["outside_commit_span_s"] = round(wall - span, 3) if span is not None else None
        out["notes"].append("commit_intervals: wall between checkpoint commits (commits.jsonl time) minus the "
                            "perf/step_ms of the steps inside; outside_commit_span_s = wall before the step-0 "
                            "commit plus after the last commit (startup, final save, teardown)")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("within")
    w.add_argument("--config", default=str(ROOT / "configs" / "base.yaml"))
    w.add_argument("--steps", type=int, default=100)
    w.add_argument("--warmup", type=int, default=10)
    w.add_argument("--gap-floor-ms", type=float, default=0.5,
                   help="a step counts as loader-stalled when loader_ms is above this")
    w.add_argument("--out", default=None, help="write the JSON here (default: print)")
    w.add_argument("overrides", nargs="*")
    b = sub.add_parser("between")
    b.add_argument("--run-dir", required=True)
    b.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    res = within(a.config, a.overrides, a.steps, a.warmup, a.gap_floor_ms) if a.cmd == "within" else between(a.run_dir)
    text = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).write_text(text)
        brief = {k: v for k, v in res.items() if k != "per_step"}
        print(json.dumps(brief, indent=1))
    else:
        print(text)


if __name__ == "__main__":
    main()
