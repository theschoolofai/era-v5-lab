#!/usr/bin/env python3
"""How much does k3 move from prompt to prompt and from step to step? (G12, for Team 10's per-step max_k3 rule)

    python step_k3_spread.py torch_reference_perrollout.json [--out spread.json] [--threshold 0.05] [--prompts-per-step 16]

Input: the output of `score_with_torch.py --per-rollout`. k3 is reported pooled over a whole run in the other tables
(mean of r - log r - 1 over every sampled token). Team 10's loop checks it per step, on a small batch, so the pooled mean
says little about how often a per-step limit trips. Here, per format:
  per prompt    k3 of one prompt (its rollouts pooled): median, p90, max, and the share of prompts above the threshold
  per step      steps simulated by drawing `prompts-per-step` prompts without replacement (Team 10's step is 16 prompts),
                k3 of the step = token-weighted mean over the rollouts of those prompts; the share of steps above the
                threshold, and the median and p95 of the step k3
Limit: a step here has the run's completions (at most 256 new tokens), Team 10's has 1,536 or more per completion, so a
real step averages over more tokens and varies less than the simulated one: the shares are an upper bound for the same
per-token mismatch. The drawing is seeded; the pool is the run's prompts, so a step shares prompts with other steps.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

import numpy as np


def per_prompt(rows: list[dict]) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for r in rows:
        d = out.setdefault(r["prompt_idx"], {"tokens": 0, "k3_sum": 0.0, "category": r["category"], "rollouts": 0})
        d["tokens"] += r["tokens"]; d["k3_sum"] += r["k3_sum"]; d["rollouts"] += 1
    return out


def quantiles(x: np.ndarray) -> dict:
    return {"median": float(np.median(x)), "p90": float(np.quantile(x, 0.9)), "max": float(x.max())}


def simulate_steps(prompts: dict[int, dict], per_step: int, n_steps: int, seed: int) -> np.ndarray:
    ids = np.array(sorted(prompts))
    tokens = np.array([prompts[i]["tokens"] for i in ids], dtype=float)
    ksum = np.array([prompts[i]["k3_sum"] for i in ids], dtype=float)
    rng = np.random.default_rng(seed)
    pick = np.argsort(rng.random((n_steps, len(ids))), axis=1)[:, :per_step]     # draw per_step prompts without replacement
    return ksum[pick].sum(1) / tokens[pick].sum(1)


def analyse(fmt: dict, threshold: float, per_step: int, n_steps: int = 20000, seed: int = 0) -> dict:
    prompts = per_prompt(fmt["per_rollout"])
    pk = np.array([d["k3_sum"] / d["tokens"] for d in prompts.values()])
    rk = np.array([r["k3_sum"] / r["tokens"] for r in fmt["per_rollout"]])
    steps = simulate_steps(prompts, min(per_step, len(prompts)), n_steps, seed)
    by_cat = {}
    for c in sorted({d["category"] for d in prompts.values()}):
        v = np.array([d["k3_sum"] / d["tokens"] for d in prompts.values() if d["category"] == c])
        by_cat[c] = {"prompts": int(len(v)), "share_above": float((v > threshold).mean()), **quantiles(v)}
    return {"format": fmt["format"], "pooled_k3": float(sum(r["k3_sum"] for r in fmt["per_rollout"]) / sum(r["tokens"] for r in fmt["per_rollout"])),
            "prompts": int(len(pk)), "per_prompt": {"share_above": float((pk > threshold).mean()), **quantiles(pk)},
            "per_rollout": {"share_above": float((rk > threshold).mean()), **quantiles(rk)},
            "per_step": {"prompts_per_step": min(per_step, len(prompts)), "simulated_steps": n_steps, "share_above": float((steps > threshold).mean()),
                         "median": float(np.median(steps)), "p95": float(np.quantile(steps, 0.95)), "max": float(steps.max())},
            "by_category_per_prompt": by_cat}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("torch_json", type=Path)
    ap.add_argument("--threshold", type=float, default=0.05)
    ap.add_argument("--prompts-per-step", type=int, default=16)
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    d = json.loads(a.torch_json.read_text())
    res = {"threshold": a.threshold, "reference": d.get("reference"), "formats": [analyse(f, a.threshold, a.prompts_per_step, a.steps) for f in d["formats"] if "per_rollout" in f]}
    for r in res["formats"]:
        s = r["per_step"]
        print(f"{r['format']:7s} pooled k3 {r['pooled_k3']:.4f} | prompts above {a.threshold}: {100 * r['per_prompt']['share_above']:5.1f}% (median {r['per_prompt']['median']:.4f}, "
              f"max {r['per_prompt']['max']:.3f}) | simulated {s['prompts_per_step']}-prompt steps above: {100 * s['share_above']:5.1f}% (median {s['median']:.4f}, p95 {s['p95']:.4f})")
    if a.out:
        a.out.write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
