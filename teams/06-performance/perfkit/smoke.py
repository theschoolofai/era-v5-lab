"""Smoke test: does a config build, train and run at a sane speed on this machine?  [implemented]

    cd teams/06-performance
    python -m perfkit.smoke                                         # configs/lab_small.yaml
    python -m perfkit.smoke --config configs/base.yaml            # plain NanoGPT
    python -m perfkit.smoke --batch 16 model.ce_impl=chunked        # key=value overrides as in bench

Prints: GPU, params, reversible reconstruction error, loss at the start and end, median step time
with p10 / p90, tokens/s, peak memory. Precision and batch are picked from the GPU: bf16 and B=32 where
bf16 is native (A100, L4, H100), else fp16 + GradScaler and B=8 (T4, P100, V100); run.dtype and
run.batch_size of the config are ignored.

Not the baseline: plain wall-clock step times with one CUDA event pair, no per-part regions, no run JSON.
Gate 1 numbers come from perfkit.bench on committed code.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dataio.loader import Loader  # noqa: E402
from models.config import load_config, model_config  # noqa: E402
from models.gpt import GPT  # noqa: E402
from models.optim import _native_bf16, build_optimizer  # noqa: E402
from models.reversible import reconstruction_error  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(ROOT / "configs/lab_small.yaml"))
    ap.add_argument("--batch", type=int, default=None, help="default: 32 with native bf16, else 8")
    ap.add_argument("--steps", type=int, default=30, help="timed steps")
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("overrides", nargs="*", help="key=value, e.g. model.reversible=false")
    a = ap.parse_args(argv)

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bf16 = dev.type == "cuda" and _native_bf16()          # emulated bf16 (T4 etc.) counts as no
    dtype = torch.bfloat16 if (bf16 or dev.type == "cpu") else torch.float16
    B = a.batch or (32 if bf16 else 8)
    cfg = load_config(a.config, a.overrides)
    m = model_config(cfg)
    print("GPU:", torch.cuda.get_device_name() if dev.type == "cuda" else "cpu", "| torch", torch.__version__,
          "| dtype", dtype, "| B", B, "| T", m.block_size, "| config", Path(a.config).name, *a.overrides)

    ld = Loader(cfg["data"]["source"], B, m.block_size, dev, data_dir=cfg["data"]["dir"], vocab_size=m.vocab_size,
                tokenizer_path=cfg["data"].get("tokenizer_path"))
    print(f"tokenizer: BrahmicTokenizer-131K | vocab {ld.vocab_size} | artifact {ld.tokenizer.path}")
    torch.manual_seed(cfg["run"]["seed"])
    model = GPT(m, ld.token_bytes(m.ke_max_pos) if m.embedding == "ke1" else None).to(dev)
    opt = build_optimizer(model, cfg["optim"])
    scaler = torch.amp.GradScaler("cuda") if dtype == torch.float16 else None
    total, active = model.param_counts()
    print(f"params total {total / 1e6:.1f}M, active {active / 1e6:.1f}M")

    if m.reversible:
        x, _ = ld.next_batch()
        with torch.autocast(dev.type, dtype=dtype):
            err = reconstruction_error(model.tok(x) + model.pos(torch.arange(m.block_size, device=dev)), model.blocks)
        print(f"reversible reconstruction error: {err:.1e}  ({'OK' if err < 1e-3 else 'TOO HIGH'})")

    def step(step_index):
        x, y = ld.next_batch()
        with torch.autocast(dev.type, dtype=dtype):
            loss = model(x, y)[1]
        if scaler:
            scaler.scale(loss).backward()
            opt.unscale(scaler)
        else:
            loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), cfg["run"]["grad_clip"])
        opt.set_lr(step_index, a.warmup + a.steps,
                   schedule=cfg["optim"].get("schedule", "constant"),
                   warmup_steps=cfg["optim"].get("warmup_steps", 0),
                   min_lr_ratio=cfg["optim"].get("min_lr_ratio", 0.1))
        opt.step(scaler)
        if scaler:
            scaler.update()
        for moe in model.moe_layers():
            moe.update_bias()
        opt.zero_grad()
        return loss

    if dev.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    times, losses = [], []
    for i in range(a.warmup + a.steps):
        if dev.type == "cuda":
            start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            start.record()
        t0 = time.perf_counter()
        loss = step(i)
        if dev.type == "cuda":
            end.record()
            end.synchronize()
            ms = start.elapsed_time(end)
        else:
            ms = (time.perf_counter() - t0) * 1e3
        losses.append(loss.item())
        if i >= a.warmup:
            times.append(ms)
        if i % 10 == 0:
            print(f"step {i:3d}  loss {losses[-1]:.3f}  {ms:.0f} ms")

    times.sort()
    med = times[len(times) // 2]
    print(f"\nloss {losses[0]:.3f} -> {losses[-1]:.3f}  (start should be ~ln({m.vocab_size}) = "
          f"{torch.log(torch.tensor(float(m.vocab_size))):.2f})")
    print(f"step median {med:.1f} ms  p10 {times[len(times) // 10]:.1f}  p90 {times[9 * len(times) // 10]:.1f}"
          f"  -> {B * m.block_size / med * 1e3:,.0f} tokens/s")
    if dev.type == "cuda":
        print(f"peak memory {torch.cuda.max_memory_allocated() / 2 ** 30:.1f} GB")
    print("all weights finite:", all(torch.isfinite(p).all().item() for p in model.parameters()))


if __name__ == "__main__":
    main()
