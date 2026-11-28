"""Lab 5 task 1(a) GPU checks for model.head_mode=kas_v2 (frozen p1536 byte table), before PR-B leaves draft.

  1. parity: KASHead on CUDA vs CPU, same weights and input (logits + all 5 parameter grads).
  2. determinism: two identical CUDA forward+backward passes; bit-equal or not, and the max difference
     (F.embedding_bag backward accumulates with atomics on CUDA); also whether deterministic mode allows it.
  3. bf16 autocast: GPT loss under bf16 autocast vs fp32 (KASHead runs its maths in fp32 by design).
  4. torch.compile: compiled GPT loss and grads vs eager.
  5. bench: dense vs kas_v2 head, peak memory and step time (bf16 autocast, AdamW, synthetic tokens).

  PYTHONPATH=. python correctness/kas_gpu_check.py --out kas_gpu_check.json
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time

import torch

from models.config import ModelConfig
from models.gpt import GPT
from models.kas_v2 import KASCodec, KASHead, load_kas_table

V = 131072
HEAD_PARAMS = ("W_out", "beta", "unigram", "tok_u", "tok_c")


def git(*args):
    try:
        return subprocess.check_output(["git", *args], text=True).strip()
    except Exception:
        return "unknown"


def rel(a, b):
    return float((a.double() - b.double()).abs().max() / b.double().abs().max().clamp_min(1e-30))


def head_pass(head, x, grad):
    head.zero_grad(set_to_none=True)
    out = head(x)
    out.backward(grad)
    return out.detach(), {n: getattr(head, n).grad.detach().clone() for n in HEAD_PARAMS}


def check_parity_and_determinism(rows, lengths, d=256, n=256):
    torch.manual_seed(0)
    cpu = KASHead(rows, lengths, d, KASCodec()).eval()
    codec = KASCodec().cuda()                       # GPT registers its codec as a submodule; here move it by hand
    gpu = KASHead(rows, lengths, d, codec).cuda().eval()
    gpu.load_state_dict(cpu.state_dict())
    with torch.no_grad():
        for p in (cpu.unigram, gpu.unigram):
            p.copy_(torch.randn(V, generator=torch.Generator().manual_seed(1)).to(p.device) * 0.1)
    x = torch.randn(n, d, generator=torch.Generator().manual_seed(2))
    grad = torch.randn(n, V, generator=torch.Generator().manual_seed(3))
    lc, gc = head_pass(cpu, x, grad)
    l1, g1 = head_pass(gpu, x.cuda(), grad.cuda())
    l2, g2 = head_pass(gpu, x.cuda(), grad.cuda())
    parity = {"logits_rel_max": rel(l1.cpu(), lc), **{f"grad_{k}_rel_max": rel(g1[k].cpu(), gc[k]) for k in HEAD_PARAMS}}
    determinism = {
        "logits_bit_equal": bool(torch.equal(l1, l2)),
        **{f"grad_{k}_bit_equal": bool(torch.equal(g1[k], g2[k])) for k in HEAD_PARAMS},
        **{f"grad_{k}_max_abs_diff": float((g1[k] - g2[k]).abs().max()) for k in HEAD_PARAMS},
    }
    torch.use_deterministic_algorithms(True)
    try:
        head_pass(gpu, x.cuda(), grad.cuda())
        determinism["deterministic_mode"] = "runs"
    except RuntimeError as e:
        determinism["deterministic_mode"] = "raises: " + str(e).splitlines()[0][:200]
    finally:
        torch.use_deterministic_algorithms(False)
    return parity, determinism


def gpt(head, d, layers, seq):
    torch.manual_seed(0)
    cfg = ModelConfig(vocab_size=V, block_size=seq, n_layer=layers, n_head=max(1, d // 64), n_embd=d,
                      attn_impl="sdpa", head_mode=head, tie_embeddings=False, reversible=False)
    return GPT(cfg).cuda().train()


def batch(b, t, seed):
    g = torch.Generator().manual_seed(seed)
    ids = torch.randint(0, V, (b, t + 1), generator=g).cuda()
    return ids[:, :-1], ids[:, 1:]


def check_bf16_and_compile(d=256, layers=2, b=4, t=256):
    x, y = batch(b, t, 5)
    model = gpt("kas_v2", d, layers, t)
    model.eval()                                    # no token-row dropout, so passes are comparable
    with torch.no_grad():
        logits, l32 = model(x, y)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits_bf, l16 = model(x, y)
    bf16 = {"loss_fp32": float(l32), "loss_bf16_autocast": float(l16),
            "abs_diff": abs(float(l32) - float(l16)), "logits_dtype_bf16_run": str(logits_bf.dtype),
            "logits_finite": bool(torch.isfinite(logits_bf).all())}

    def loss_and_grads(m):
        m.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            _, loss = m(x, y)
        loss.backward()
        return float(loss), {n: model.head.get_parameter(n).grad.clone() for n in HEAD_PARAMS}

    eager_loss, eager_grads = loss_and_grads(model)
    t0 = time.perf_counter()
    try:
        compiled = torch.compile(model)
        comp_loss, comp_grads = loss_and_grads(compiled)
    except Exception as e:                          # e.g. Triton cannot build its C helper without Python headers
        return bf16, {"status": "skipped", "error": f"{type(e).__name__}: {str(e).splitlines()[0][:300]}"}
    first = time.perf_counter() - t0
    comp = {"status": "ran", "loss_eager": eager_loss, "loss_compiled": comp_loss, "abs_diff": abs(eager_loss - comp_loss),
            "first_call_seconds": round(first, 1),
            **{f"grad_{k}_rel_max": rel(comp_grads[k], eager_grads[k]) for k in HEAD_PARAMS}}
    return bf16, comp


def bench(head, d, layers, b, t, steps=20, warmup=5):
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    model = gpt(head, d, layers, t)
    total, active = model.param_counts()
    opt = torch.optim.AdamW(model.parameters(), lr=1e-4, betas=(0.9, 0.95), weight_decay=0.0, fused=True)
    x, y = batch(b, t, 7)
    times = []
    for i in range(warmup + steps):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.autocast("cuda", dtype=torch.bfloat16):
            _, loss = model(x, y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        torch.cuda.synchronize()
        if i >= warmup:
            times.append(time.perf_counter() - t0)
    times.sort()
    med = times[len(times) // 2]
    out = {"head": head, "n_embd": d, "n_layer": layers, "batch": b, "seq": t, "params_total": total,
           "params_active": active, "step_ms_median": round(med * 1e3, 2), "step_ms_min": round(times[0] * 1e3, 2),
           "tokens_per_s_median": round(b * t / med), "peak_mem_GiB": round(torch.cuda.max_memory_allocated() / 2**30, 3),
           "loss_last": float(loss)}
    del model, opt
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--bench-widths", default="512,1024")
    ap.add_argument("--bench-layers", type=int, default=2)
    ap.add_argument("--bench-batch", type=int, default=4)
    ap.add_argument("--bench-seq", type=int, default=512)
    a = ap.parse_args()
    assert torch.cuda.is_available(), "needs CUDA"

    rows, lengths = load_kas_table(V)
    parity, determinism = check_parity_and_determinism(rows, lengths)
    bf16, comp = check_bf16_and_compile()
    runs = [bench(h, int(d), a.bench_layers, a.bench_batch, a.bench_seq)
            for d in a.bench_widths.split(",") for h in ("dense", "kas_v2")]

    result = {
        "check": "kas_gpu_check", "parity_cuda_vs_cpu": parity, "determinism_cuda": determinism,
        "bf16_autocast": bf16, "torch_compile": comp, "bench": runs,
        "bench_note": "2-layer model, synthetic random tokens, bf16 autocast, fused AdamW: compares the heads, "
                      "not V4. Median of 20 steps after 5 warmup.",
        "device": torch.cuda.get_device_name(0), "capability": list(torch.cuda.get_device_capability(0)),
        "torch": torch.__version__, "cuda": torch.version.cuda, "python": platform.python_version(),
        "git_sha": git("rev-parse", "HEAD"), "git_dirty": bool(git("status", "--porcelain", "--", ".")),
        "command": " ".join([sys.executable] + sys.argv),
    }
    text = json.dumps(result, indent=2)
    print(text)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
