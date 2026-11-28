"""GPU benchmark of Hybrid Muon vs AdamW, LoRA, Deletion Tuning, and activation recompute on Team 5's MoE.

Measures real CUDA-synced step time, tokens/s, optimizer share (`optim_step_share`), peak VRAM (`max_memory_allocated`),
and runs the TSAI 28 Nov Rule #6 gradient-coverage check (fast path OFF vs ON: activation recompute and bf16 autocast).

Usage:
    python teams/10-post-training/dt/bench_gpu_muon_recompute.py \
      --device cuda --steps 10 --warmup 2 \
      --out teams/10-post-training/results/lab5_gpu_muon_recompute.json
"""
from __future__ import annotations

import argparse
import copy
import json
import statistics
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import torch
import torch.nn.functional as F

HERE = Path(__file__).resolve().parent
TEAM10 = HERE.parent
sys.path[:0] = [
    str(HERE),
    str(TEAM10 / "capstone"),
    str(TEAM10 / "rl-loop"),
    str(TEAM10.parent / "05-architecture" / "harness"),
]

import check_grad_coverage as cgc  # noqa: E402
import hybrid_optim as ho  # noqa: E402
import sft_g5  # noqa: E402
from week2 import config as C  # noqa: E402
from week2.model import LanguageModel  # noqa: E402

dtmask = sft_g5.dtmask


def make_g5_moe(
    *,
    n_layer: int,
    n_embd: int,
    n_head: int,
    n_kv_head: int,
    ffn_hidden: int,
    vocab_size: int,
    block_size: int,
    seed: int,
) -> LanguageModel:
    m = copy.deepcopy(
        C.load_runtime(str(TEAM10.parent / "05-architecture" / "configs" / "arms" / "t2.yaml"))["model"]
    )
    m.update(
        vocab_size=vocab_size,
        block_size=block_size,
        n_layer=n_layer,
        n_head=n_head,
        n_kv_head=n_kv_head,
        n_embd=n_embd,
    )
    m["moe"] = dict(m["moe"], num_experts=16, top_k=2, num_shared=1, ffn_hidden=ffn_hidden, bias_gamma=0.001)
    g1 = torch.Generator().manual_seed(1)
    g2 = torch.Generator().manual_seed(2)
    rows = torch.randint(0, 255, (vocab_size, 32), generator=g1, dtype=torch.uint8)
    lengths = torch.randint(1, 5, (vocab_size,), generator=g2)
    torch.manual_seed(seed)
    return LanguageModel(m, rows, lengths)


def _sync(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def _setup_arm(
    base: LanguageModel,
    arm: str,
    device: torch.device,
    batch_ids: torch.Tensor,
    total_steps: int,
) -> tuple[LanguageModel, object, bool, bool]:
    """Return (model, optimizer, is_dt, use_recompute)."""
    model = copy.deepcopy(base)
    is_dt = arm.startswith("dt_")
    use_recompute = arm.endswith("_recompute")
    method = "lora" if arm.startswith("lora") else ("dt" if is_dt else "full")
    opts = SimpleNamespace(
        seed=1,
        steps=max(total_steps, 1),
        lora_r=16,
        lora_alpha=32.0,
        dt_targets="g5_gate",
        dt_alpha_start=100.0,
        dt_alpha_end=1000.0,
        dt_lambda=1e-5,
        dt_eta=1.0 / 2048.0,
    )
    sft_g5.apply_method(model, method, opts)
    model.to(device)
    if is_dt:
        wrapper = sft_g5.G5ForBench(model)
        cal = [{"input_ids": batch_ids, "attention_mask": torch.ones_like(batch_ids)}]
        scores = dtmask.wanda_scores(wrapper, cal, device)
        dtmask.apply_wanda_prior(wrapper, scores, opts.dt_eta, 3.0, unseen="keep")
        gate_opt = "hybrid_muon" if "muon" in arm else "adamw"
        opt = ho.build_optimizer(
            model.named_parameters(),
            kind=gate_opt,
            lr=5e-4,
            muon_lr=5e-4,
            wd=0.0,
            betas=(0.9, 0.95),
            dt_gate_optim="muon" if "muon" in arm else "adamw",
            skip_zero_grad_muon=True,
        )
    elif method == "lora":
        opt = ho.build_optimizer(model.named_parameters(), kind="adamw", lr=1e-3, wd=0.0, betas=(0.9, 0.95))
    else:
        kind = "hybrid_muon" if "muon" in arm else "adamw"
        opt = ho.build_optimizer(
            model.named_parameters(),
            kind=kind,
            lr=1e-4,
            muon_lr=1e-3,
            wd=0.0,
            betas=(0.9, 0.95),
            skip_zero_grad_muon=True,
        )
    model.train()
    return model, opt, is_dt, use_recompute


def _loss_step(model: LanguageModel, x: torch.Tensor, y: torch.Tensor, *, use_bf16: bool, device: torch.device) -> torch.Tensor:
    ctx = torch.autocast(device_type=device.type, dtype=torch.bfloat16) if use_bf16 else nullcontext()
    valid = torch.ones_like(x, dtype=torch.bool)
    with ctx:
        logits = model(x, valid)
        if isinstance(logits, tuple):
            logits = logits[0]
        return F.cross_entropy(logits.float().reshape(-1, logits.size(-1)), y.reshape(-1))


def benchmark_arm(
    base: LanguageModel,
    arm: str,
    x: torch.Tensor,
    y: torch.Tensor,
    *,
    device: torch.device,
    use_bf16: bool,
    warmup: int,
    steps: int,
) -> dict:
    total_steps = warmup + steps
    model, opt, is_dt, use_recompute = _setup_arm(base, arm, device, x, total_steps)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    tokens_per_step = int(x.numel())
    sync_fn = (lambda: _sync(device)) if device.type == "cuda" else None

    if device.type == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)

    step_times: list[float] = []
    optim_times: list[float] = []
    last_loss = 0.0

    with sft_g5.block_recompute(model, use_recompute):
        for step in range(total_steps):
            if step == warmup and device.type == "cuda":
                torch.cuda.reset_peak_memory_stats(device)
            _sync(device)
            t0 = time.perf_counter()
            opt.zero_grad(set_to_none=True)
            loss = _loss_step(model, x, y, use_bf16=use_bf16, device=device)
            loss.backward()
            if is_dt:
                dtmask.regulariser_backward_(model, dtmask.lambda_at(step, max(total_steps, 1), 1e-5))
            opt_s0 = opt.optim_seconds
            opt.step(sync_fn=sync_fn)
            if is_dt:
                dtmask.step_all(model)
            _sync(device)
            dt_step = time.perf_counter() - t0
            dt_opt = opt.optim_seconds - opt_s0
            last_loss = float(loss.detach())
            if step >= warmup:
                step_times.append(dt_step)
                optim_times.append(dt_opt)

    peak_vram_gb = (
        round(torch.cuda.max_memory_allocated(device) / (1024 ** 3), 4)
        if device.type == "cuda"
        else None
    )
    med_step = statistics.median(step_times)
    med_opt = statistics.median(optim_times)
    total_step = sum(step_times)
    total_opt = sum(optim_times)
    del model, opt
    if device.type == "cuda":
        torch.cuda.empty_cache()

    return {
        "arm": arm,
        "trainable_params": trainable,
        "recompute": use_recompute,
        "bf16_autocast": use_bf16,
        "tokens_per_step": tokens_per_step,
        "median_step_ms": round(med_step * 1000.0, 3),
        "median_optim_ms": round(med_opt * 1000.0, 3),
        "optim_step_share": round(total_opt / max(total_step, 1e-12), 4),
        "tok_s": round(tokens_per_step / max(med_step, 1e-12), 1),
        "peak_vram_gb": peak_vram_gb,
        "last_loss": round(last_loss, 5),
    }


def coverage_pair(
    base: LanguageModel,
    arm_off: str,
    arm_on: str,
    x: torch.Tensor,
    y: torch.Tensor,
    *,
    device: torch.device,
    use_bf16_off: bool,
    use_bf16_on: bool,
) -> dict:
    """TSAI 28 Nov Rule #6: 1 forward+backward with fast path OFF vs ON; compare None/zero grad lists."""
    out = {}
    grads_by_tag = {}
    for tag, arm, bf16 in (("fast_off", arm_off, use_bf16_off), ("fast_on", arm_on, use_bf16_on)):
        model, opt, _, use_recompute = _setup_arm(base, arm, device, x, total_steps=1)
        opt.zero_grad(set_to_none=True)
        with sft_g5.block_recompute(model, use_recompute):
            loss = _loss_step(model, x, y, use_bf16=bf16, device=device)
            loss.backward()
        _sync(device)
        audit = cgc.audit_grads(model)
        out[tag] = {
            "arm": arm,
            "bf16_autocast": bf16,
            "trainable_tensors": audit["trainable_tensors"],
            "none_grads": sorted(r["name"] for r in audit["none_grads"]),
            "zero_grads": sorted(r["name"] for r in audit["zero_grads"]),
        }
        grads_by_tag[tag] = {
            n: p.grad.detach().float().cpu()
            for n, p in model.named_parameters()
            if p.requires_grad and p.grad is not None
        }
        del model, opt
        if device.type == "cuda":
            torch.cuda.empty_cache()

    same_none = out["fast_off"]["none_grads"] == out["fast_on"]["none_grads"]
    same_zero = out["fast_off"]["zero_grads"] == out["fast_on"]["zero_grads"]
    max_diff = 0.0
    for k, g0 in grads_by_tag["fast_off"].items():
        if k in grads_by_tag["fast_on"]:
            d = float((g0 - grads_by_tag["fast_on"][k]).abs().max())
            if d > max_diff:
                max_diff = d
    return {
        "pair": f"{arm_off}_vs_{arm_on}",
        "fast_off": out["fast_off"],
        "fast_on": out["fast_on"],
        "lists_identical": same_none and same_zero,
        "max_abs_grad_diff": round(max_diff, 7),
    }


def run(args) -> dict:
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested but CUDA is unavailable")
    base = make_g5_moe(
        n_layer=args.layers,
        n_embd=args.embd,
        n_head=args.heads,
        n_kv_head=args.kv_heads,
        ffn_hidden=args.ffn_hidden,
        vocab_size=args.vocab,
        block_size=args.seq_len,
        seed=args.seed,
    )
    total_params = sum(p.numel() for p in base.parameters())
    g = torch.Generator().manual_seed(args.seed + 7)
    x = torch.randint(0, args.vocab, (args.batch, args.seq_len), generator=g).to(device)
    y = torch.randint(0, args.vocab, (args.batch, args.seq_len), generator=g).to(device)
    use_bf16 = bool(args.bf16 and device.type == "cuda")

    arms = [
        "full_adamw",
        "full_hybrid_muon",
        "full_hybrid_muon_recompute",
        "lora_adamw",
        "dt_adamw",
        "dt_adamw_recompute",
    ]
    rows = []
    for arm in arms:
        rec = benchmark_arm(
            base, arm, x, y,
            device=device, use_bf16=use_bf16, warmup=args.warmup, steps=args.steps,
        )
        print(json.dumps(rec), flush=True)
        rows.append(rec)

    cov = [
        coverage_pair(base, "full_hybrid_muon", "full_hybrid_muon_recompute", x, y,
                      device=device, use_bf16_off=use_bf16, use_bf16_on=use_bf16),
        coverage_pair(base, "dt_adamw", "dt_adamw_recompute", x, y,
                      device=device, use_bf16_off=use_bf16, use_bf16_on=use_bf16),
    ]
    if device.type == "cuda":
        cov.append(
            coverage_pair(base, "full_hybrid_muon", "full_hybrid_muon", x, y,
                          device=device, use_bf16_off=False, use_bf16_on=True)
        )
        cov[-1]["pair"] = "full_hybrid_muon_fp32_vs_bf16_autocast"

    result = {
        "device": args.device,
        "gpu_name": torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu",
        "torch": torch.__version__,
        "model": {
            "class": "week2.LanguageModel",
            "layers": args.layers,
            "n_embd": args.embd,
            "n_head": args.heads,
            "n_kv_head": args.kv_heads,
            "ffn_hidden": args.ffn_hidden,
            "num_experts": 16,
            "num_shared": 1,
            "top_k": 2,
            "vocab_size": args.vocab,
            "total_params": total_params,
        },
        "batch": args.batch,
        "seq_len": args.seq_len,
        "bf16_autocast": use_bf16,
        "warmup": args.warmup,
        "steps": args.steps,
        "arms": rows,
        "gradient_coverage": cov,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--layers", type=int, default=8)
    ap.add_argument("--embd", type=int, default=512)
    ap.add_argument("--heads", type=int, default=8)
    ap.add_argument("--kv-heads", type=int, default=4)
    ap.add_argument("--ffn-hidden", type=int, default=256)
    ap.add_argument("--vocab", type=int, default=4096)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--seq-len", type=int, default=256)
    ap.add_argument("--bf16", action="store_true", default=True)
    ap.add_argument("--no-bf16", dest="bf16", action="store_false")
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    res = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
