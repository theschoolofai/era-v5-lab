"""Team 8's RL feed from train.py's metrics.jsonl: one JSON line per step, flat names.

    python rl-loop/metrics_feed.py --metrics out/metrics.jsonl --out out/rl_feed.jsonl [--summary out/summary.json]

Team 8's names (teams/08-monitoring/metrics/metric_list_v1.yaml): train_reward, reward_per_env, entropy, mismatch_k3,
mismatch_abs_logratio, gradient_norm. Team 10's additions (docs/post_training_plan_v1.md section 3): heldout_reward,
heldout_reward_quant, mixed_group_frac, rollout_tok_s, idle_s, optim_step_s, optim_step_share, step_s, kl, peak_vram_gb,
quant_scheme, quant_refresh_s, and router_checksum_ok on the last row when --summary is given.

A field is written only when the run measured it: a missing mismatch_k3 means the sampler had no log-probabilities of its
own, not that the gap was zero.

A resumable run (train.state_dir) writes each step's row before it evaluates, so held-out rewards are also read from
evals.jsonl beside the metrics file (or --evals). On CUDA the optimizer time and share are written only when the run
synchronised its clocks (train.time_sync); otherwise the number is only the time to launch the update.

idle_s is the host reward-scoring time of the step, during which the accelerator has no work. It is a lower bound: gaps
between the other phases are not measured.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SAME_NAME = ("train_reward", "mismatch_k3", "mismatch_abs_logratio", "entropy", "heldout_reward", "heldout_reward_quant",
             "optim_step_s", "step_s", "quant_scheme", "quant_refresh_s")


def feed_row(rec: dict) -> dict:
    row = {"step": rec["step"], **{k: rec[k] for k in SAME_NAME if rec.get(k) is not None}}
    if rec.get("grad_norm") is not None:
        row["gradient_norm"] = rec["grad_norm"]
    kinds = rec.get("group_kinds")  # objective_v1
    used, dropped = rec.get("groups_used"), rec.get("groups_dropped")
    if kinds and sum(kinds.values()):
        row["mixed_group_frac"] = round(kinds.get("mixed", 0) / sum(kinds.values()), 6)
    elif used is not None and dropped is not None and used + dropped:
        row["mixed_group_frac"] = round(used / (used + dropped), 6)  # a kept group is one whose rewards differ
    if rec.get("rollout_tokens_per_s") is not None:
        row["rollout_tok_s"] = rec["rollout_tokens_per_s"]
    if (rec.get("times_s") or {}).get("reward") is not None:
        row["idle_s"] = rec["times_s"]["reward"]
    if "peak_torch_gb" in rec and not rec.get("times_synced"):
        row.pop("optim_step_s", None)
    elif rec.get("optim_step_s") is not None and rec.get("step_s"):
        row["optim_step_share"] = round(rec["optim_step_s"] / rec["step_s"], 6)
    if rec.get("peak_torch_gb") is not None:
        row["peak_vram_gb"] = rec["peak_torch_gb"]
    kl = rec.get("kl_to_start")
    if kl is not None:
        row["kl"] = kl
    envs = {name: round(v["passes"] / v["rollouts"], 6) for name, v in (rec.get("subgroups") or {}).items() if v.get("rollouts")}
    if envs:
        row["reward_per_env"] = envs
    return row


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def convert(metrics: Path, out: Path, summary: Path | None = None, evals: Path | None = None) -> list[dict]:
    rows = [feed_row(rec) for rec in _jsonl(metrics)]
    evals = evals or metrics.parent / "evals.jsonl"
    if evals.exists():
        names = {"heldout": "heldout_reward", "heldout_quant": "heldout_reward_quant"}
        by_step = {(e["step"], names[e["name"]]): e["pass"] for e in _jsonl(evals) if e.get("name") in names}
        for row in rows:
            for key in names.values():
                if key not in row and (row["step"], key) in by_step:
                    row[key] = by_step[row["step"], key]
    if summary is not None and rows:
        ok = json.loads(summary.read_text(encoding="utf-8")).get("router_unchanged")
        if ok is not None:
            rows[-1]["router_checksum_ok"] = bool(ok)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, allow_nan=False) + "\n" for r in rows), encoding="utf-8")
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--metrics", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--summary", type=Path)
    ap.add_argument("--evals", type=Path, help="default: evals.jsonl beside --metrics, when present")
    a = ap.parse_args(argv)
    print(json.dumps({"rows": len(convert(a.metrics, a.out, a.summary, a.evals)), "out": str(a.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
