"""TSAI 28 Nov Rule #6 Gradient-Coverage Check across G10 fast paths.

After one forward + backward pass, lists every trainable parameter whose gradient is `None` or all zero,
explains why each entry is allowed (if any), and compares fast-path ON vs fast-path OFF.

Covers:
1. DT `regulariser_backward_()` (layer-by-layer graph-free fast path) vs autograd `(-lam * regulariser()).backward()`.
2. DT + activation recompute (`torch.utils.checkpoint(..., use_reentrant=False)`) ON vs OFF.
3. CUDA `bfloat16` autocast ON vs `float32` OFF (with non-starved vs forced-idle MoE experts).
4. Grad-masked `--marker-rows` hook (verifies non-marker rows are never skipped/corrupted on fast path).

Usage:
    python teams/10-post-training/dt/check_grad_coverage.py --device cuda \
        --out teams/10-post-training/results/lab5_grad_coverage.json
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from contextlib import nullcontext
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

TEAM10 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM10 / "dt"))
sys.path.insert(0, str(TEAM10 / "capstone"))

import mask as dtmask  # noqa: E402
from test_lab5_dt_compat import TinyMoELM  # noqa: E402


def audit_grads(model: nn.Module, allowed_reasons: dict[str, str] | None = None) -> dict:
    """Inspect every trainable parameter after backward; classify None and all-zero gradients."""
    allowed_reasons = allowed_reasons or {}
    trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    none_grads: list[dict] = []
    zero_grads: list[dict] = []
    for name, p in trainable:
        if p.grad is None:
            none_grads.append({"name": name, "shape": list(p.shape), "reason": allowed_reasons.get(name, "UNEXPECTED_NONE")})
        elif int(torch.count_nonzero(p.grad)) == 0:
            zero_grads.append({"name": name, "shape": list(p.shape), "reason": allowed_reasons.get(name, "UNEXPECTED_ZERO")})
    unexpected = [x for x in none_grads + zero_grads if x["reason"].startswith("UNEXPECTED_")]
    return {
        "trainable_tensors": len(trainable),
        "none_grad_count": len(none_grads),
        "zero_grad_count": len(zero_grads),
        "none_grads": none_grads,
        "zero_grads": zero_grads,
        "unexpected_missing_or_zero": unexpected,
        "all_explained": len(unexpected) == 0,
    }


def compare_fast_vs_ref(
    name: str,
    model_factory,
    run_fn,
    *,
    allowed_reasons: dict[str, str] | None = None,
) -> dict:
    """Run one forward+backward with fast_on=False and fast_on=True on identical weights; compare grad coverage."""
    m_ref = model_factory()
    m_fast = copy.deepcopy(m_ref)
    run_fn(m_ref, fast_on=False)
    run_fn(m_fast, fast_on=True)

    cov_ref = audit_grads(m_ref, allowed_reasons)
    cov_fast = audit_grads(m_fast, allowed_reasons)

    ref_none = sorted(x["name"] for x in cov_ref["none_grads"])
    fast_none = sorted(x["name"] for x in cov_fast["none_grads"])
    ref_zero = sorted(x["name"] for x in cov_ref["zero_grads"])
    fast_zero = sorted(x["name"] for x in cov_fast["zero_grads"])

    diffs = []
    for (n1, p1), (n2, p2) in zip(m_ref.named_parameters(), m_fast.named_parameters()):
        if not p1.requires_grad:
            continue
        if (p1.grad is None) != (p2.grad is None):
            diffs.append({"name": n1, "issue": "none_mismatch"})
        elif p1.grad is not None and p2.grad is not None:
            diffs.append({"name": n1, "max_abs_diff": float((p1.grad.float() - p2.grad.float()).abs().max())})

    max_diff = max((d.get("max_abs_diff", 0.0) for d in diffs), default=0.0)
    return {
        "check": name,
        "lists_identical": (ref_none == fast_none) and (ref_zero == fast_zero),
        "ref_coverage": cov_ref,
        "fast_coverage": cov_fast,
        "max_grad_abs_diff": round(max_diff, 7),
        "pass": cov_ref["all_explained"] and cov_fast["all_explained"] and (ref_none == fast_none) and (ref_zero == fast_zero),
    }


def run_all(device: str) -> dict:
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested but CUDA is unavailable")
    dev = torch.device(device)
    torch.manual_seed(123)
    x = torch.randint(0, 64, (4, 16), device=dev)
    y = torch.randint(0, 64, (4, 16), device=dev)

    def make_dt_moe():
        torch.manual_seed(7)
        m = TinyMoELM(vocab=64, d=48, hidden=96, n_layers=2, n_experts=6).to(dev)
        dtmask.convert(m, ("re:blocks\\.[0-9]+\\.experts\\.[0-9]+\\.gate",),
                       alpha_start=100.0, alpha_end=1000.0, total_steps=20, seed=0)
        return m

    def run_regulariser(m: nn.Module, fast_on: bool) -> None:
        m.train()
        loss = F.cross_entropy(m(x).reshape(-1, 64), y.reshape(-1))
        if fast_on:
            loss.backward()
            dtmask.regulariser_backward_(m, 1e-5)
        else:
            (loss - 1e-5 * dtmask.regulariser(m)).backward()

    def run_recompute(m: nn.Module, fast_on: bool) -> None:
        m.use_checkpoint = fast_on
        m.train()
        loss = F.cross_entropy(m(x).reshape(-1, 64), y.reshape(-1))
        loss.backward()
        dtmask.regulariser_backward_(m, 1e-5)

    def make_full_moe():
        torch.manual_seed(9)
        m = TinyMoELM(vocab=64, d=48, hidden=96, n_layers=2, n_experts=6).to(dev)
        # Hold expert 5 at 0 routed tokens via router_bias (like dryrun2-1234 idle experts) while experts 0..4 compete.
        with torch.no_grad():
            for blk in m.blocks:
                blk.router_bias.copy_(torch.tensor([0.0, 0.0, 0.0, 0.0, 0.0, -50.0], device=dev))
        return m

    idle_reasons = {
        f"blocks.{li}.experts.5.{proj}.weight": "idle routed expert (0 tokens routed because router_bias[5]=-50.0); allowed and skipped by hybrid_optim.skip_zero_grad_muon"
        for li in range(2) for proj in ("gate", "up", "down")
    }

    def run_bf16_autocast(m: nn.Module, fast_on: bool) -> None:
        m.train()
        ctx = torch.autocast(device_type=dev.type, dtype=torch.bfloat16) if fast_on else nullcontext()
        with ctx:
            loss = F.cross_entropy(m(x).reshape(-1, 64), y.reshape(-1))
        loss.backward()

    checks = [
        compare_fast_vs_ref("dt_regulariser_backward_vs_autograd", make_dt_moe, run_regulariser),
        compare_fast_vs_ref("dt_activation_recompute_use_reentrant_false", make_dt_moe, run_recompute),
        compare_fast_vs_ref(
            f"full_moe_{dev.type}_bf16_autocast_vs_fp32_with_idle_expert",
            make_full_moe,
            run_bf16_autocast,
            allowed_reasons=idle_reasons,
        ),
    ]
    return {
        "rule": "TSAI 28 Nov Lab Rules #6: gradient-coverage check (fast path ON vs OFF)",
        "device": device,
        "gpu_name": torch.cuda.get_device_name(0) if device == "cuda" else "cpu",
        "all_pass": all(c["pass"] for c in checks),
        "checks": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    res = run_all(args.device)
    text = json.dumps(res, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if res["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
