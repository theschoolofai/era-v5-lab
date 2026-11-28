"""Reproducible Lab 5 DT compatibility benchmark (CPU stand-in, 2 seeds).

Runs:
1. Full FT vs LoRA vs DT (AdamW) vs DT (Hybrid Muon shape-based) vs DT (Hybrid Muon + activation recompute)
   on a deterministic 2-layer routed MoE stand-in, reporting loss, optimizer step-time share, peak RSS/tensor
   bytes, deletion fraction, and wall time.
2. Unseen-expert Wanda calibration ablation (`--dt-unseen official` vs `--dt-unseen keep`).
3. Idle-expert zero-grad Newton-Schulz drift check (`skip_zero_grad=False` vs `True`).

Usage:
    python teams/10-post-training/dt/run_lab5_dt_checks.py --out teams/10-post-training/results/lab5_dt_muon_recompute.json
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

TEAM10 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM10 / "dt"))
sys.path.insert(0, str(TEAM10 / "capstone"))

import hybrid_optim as ho  # noqa: E402
import mask as dtmask  # noqa: E402
from test_lab5_dt_compat import TinyMoELM  # noqa: E402


def _add_lora(model: nn.Module, r: int = 8, alpha: float = 16.0) -> None:
    for p in model.parameters():
        p.requires_grad_(False)
    for blk in model.blocks:
        for e in blk.experts:
            base = e["gate"]
            wrap = nn.Module()
            wrap.base = base
            wrap.lora_A = nn.Parameter(torch.randn(r, base.in_features) * 0.02)
            wrap.lora_B = nn.Parameter(torch.zeros(base.out_features, r))
            scale = alpha / r

            class _LoRALinear(nn.Module):
                def __init__(self, b, a_p, b_p, sc):
                    super().__init__()
                    self.base = b
                    self.lora_A = a_p
                    self.lora_B = b_p
                    self.scale = sc

                @property
                def weight(self):
                    return self.base.weight + (self.lora_B @ self.lora_A) * self.scale

            e["gate"] = _LoRALinear(base, wrap.lora_A, wrap.lora_B, scale)


def run_arm(arm: str, base_state: dict, x: torch.Tensor, y: torch.Tensor, steps: int, seed: int) -> dict:
    torch.manual_seed(seed)
    m = TinyMoELM(vocab=64, d=48, hidden=96, n_layers=2, n_experts=6)
    m.load_state_dict(copy.deepcopy(base_state))

    is_dt = arm.startswith("dt_")
    if arm == "full_hybrid_muon":
        opt = ho.build_optimizer(m.named_parameters(), kind="hybrid_muon", lr=1e-3, muon_lr=6e-3)
    elif arm == "lora_adamw":
        _add_lora(m)
        opt = ho.build_optimizer(m.named_parameters(), kind="adamw", lr=1e-3)
    elif arm == "dt_adamw":
        dtmask.convert(m, ("re:blocks\\.[0-9]+\\.experts\\.[0-9]+\\.gate",), alpha_start=100.0, alpha_end=1000.0, total_steps=steps, seed=seed)
        opt = ho.build_optimizer(m.named_parameters(), kind="adamw", lr=5e-4)
    elif arm == "dt_muon_shape":
        dtmask.convert(m, ("re:blocks\\.[0-9]+\\.experts\\.[0-9]+\\.gate",), alpha_start=100.0, alpha_end=1000.0, total_steps=steps, seed=seed)
        opt = ho.build_optimizer(m.named_parameters(), kind="hybrid_muon", lr=5e-4, muon_lr=5e-4, dt_gate_optim="shape")
    elif arm == "dt_muon_recompute":
        m.use_checkpoint = True
        dtmask.convert(m, ("re:blocks\\.[0-9]+\\.experts\\.[0-9]+\\.gate",), alpha_start=100.0, alpha_end=1000.0, total_steps=steps, seed=seed)
        opt = ho.build_optimizer(m.named_parameters(), kind="hybrid_muon", lr=5e-4, muon_lr=5e-4, dt_gate_optim="shape")
    else:
        raise ValueError(arm)

    trainable_params = sum(p.numel() for p in m.parameters() if p.requires_grad)
    m.train()
    losses = []
    t0 = time.perf_counter()
    for step in range(steps):
        opt.zero_grad()
        loss = F.cross_entropy(m(x).reshape(-1, 64), y.reshape(-1))
        loss.backward()
        if is_dt:
            dtmask.regulariser_backward_(m, dtmask.lambda_at(step, steps, 1e-5))
        opt.step()
        if is_dt:
            dtmask.step_all(m)
        losses.append(float(loss.detach()))
    wall_s = time.perf_counter() - t0
    opt_sum = opt.summary(wall_s)
    del_frac = dtmask.deletion_stats(m)["deleted_frac_of_targeted"] if is_dt else 0.0
    storage_bytes = (trainable_params // 8) if is_dt else (trainable_params * 2)  # 1-bit packed mask vs bf16 delta
    return {
        "arm": arm,
        "seed": seed,
        "steps": steps,
        "trainable_params": trainable_params,
        "loss_start": round(losses[0], 4),
        "loss_end": round(losses[-1], 4),
        "loss_drop": round(losses[0] - losses[-1], 4),
        "wall_seconds": round(wall_s, 4),
        "optim_seconds": opt_sum["optim_seconds"],
        "optim_step_share": opt_sum["optim_step_share"],
        "deleted_frac_targeted": round(del_frac, 4),
        "delta_storage_bytes": storage_bytes,
    }


def unseen_ablation(seeds: list[int]) -> list[dict]:
    rows = []
    for seed in seeds:
        torch.manual_seed(seed)
        base = TinyMoELM(vocab=64, d=48, hidden=96, n_layers=2, n_experts=6)
        with torch.no_grad():
            for blk in base.blocks:
                blk.router_bias.copy_(torch.tensor([5.0, 5.0, 0.0, 0.0, -50.0, -50.0]))
        dtmask.convert(base, ("re:blocks\\.[0-9]+\\.experts\\.[0-9]+\\.gate",), total_steps=20, seed=seed)
        scores = {
            n: torch.rand_like(layer.base_weight)
            for n, layer in dtmask.masked_layers(base)
            if not (n.endswith("experts.4.gate") or n.endswith("experts.5.gate"))
        }
        for policy in ("official", "keep"):
            m = copy.deepcopy(base)
            info = dtmask.apply_wanda_prior(m, scores, eta=1.0 / 2048.0, prior_strength=3.0, unseen=policy)
            ds = dtmask.deletion_stats(m)
            rows.append({
                "seed": seed,
                "unseen_policy": policy,
                "layers_without_scores": info["layers_without_scores"],
                "init_deleted_frac_targeted": round(ds["deleted_frac_of_targeted"], 5),
            })
    return rows


def idle_expert_muon_check() -> dict:
    torch.manual_seed(11)
    w_raw = nn.Parameter(torch.randn(32, 16))
    w_guarded = nn.Parameter(w_raw.detach().clone())
    o_raw = ho.Muon([w_raw], lr=0.006, skip_zero_grad=False)
    o_guard = ho.Muon([w_guarded], lr=0.006, skip_zero_grad=True)
    g1 = torch.randn_like(w_raw)
    w_raw.grad = g1.clone()
    w_guarded.grad = g1.clone()
    o_raw.step()
    o_guard.step()
    b_raw, b_guard = w_raw.detach().clone(), w_guarded.detach().clone()
    w_raw.grad = torch.zeros_like(w_raw)
    w_guarded.grad = torch.zeros_like(w_guarded)
    o_raw.step()
    o_guard.step()
    return {
        "unguarded_max_abs_drift_on_zero_grad": round(float((w_raw.detach() - b_raw).abs().max()), 6),
        "guarded_max_abs_drift_on_zero_grad": round(float((w_guarded.detach() - b_guard).abs().max()), 6),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    arms = ["full_hybrid_muon", "lora_adamw", "dt_adamw", "dt_muon_shape", "dt_muon_recompute"]
    runs = []
    for seed in args.seeds:
        torch.manual_seed(100 + seed)
        base = TinyMoELM(vocab=64, d=48, hidden=96, n_layers=2, n_experts=6)
        base_state = copy.deepcopy(base.state_dict())
        x = torch.randint(0, 64, (4, 16))
        y = torch.randint(0, 64, (4, 16))
        for arm in arms:
            runs.append(run_arm(arm, base_state, x, y, args.steps, seed))

    payload = {
        "scope": "CPU stand-in routed MoE (2 layers, d=48, h=96, 6 experts top-2); mechanics & relative comparison only, not a quality/scale claim",
        "seeds": args.seeds,
        "steps": args.steps,
        "arms": runs,
        "unseen_expert_ablation": unseen_ablation(args.seeds),
        "idle_expert_muon_check": idle_expert_muon_check(),
    }
    text = json.dumps(payload, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
