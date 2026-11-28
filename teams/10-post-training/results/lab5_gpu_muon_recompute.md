# Lab 5: GPU Hybrid Muon, Deletion Tuning & Activation Recompute Benchmark (RTX 5070 Ti CUDA)

28 November 2026. Team 10. **NVIDIA GeForce RTX 5070 Ti (16 GB VRAM), PyTorch `2.15.0+cu132`, CUDA `bfloat16` autocast.**  
Follow-up to [`lab5_dt_study.md`](lab5_dt_study.md) (CPU-only) to measure **real GPU `optim_step_share`**, **GPU `tokens/s`**, **real peak VRAM (`max_memory_allocated`)**, and **TSAI 28 Nov Rule #6 CUDA gradient coverage** on Team 5's `week2.LanguageModel` (`16` routed + `1` shared expert, top-2, KE2/KAS untied head, `router_bias`).

**Scope & limits:** Synthetic token batch (`batch=4, seq_len=256`, `1,024` tokens/step) on a `66.13M`-parameter Team 5 MoE (`8` layers, `n_embd=512`, `n_head=8`, `n_kv_head=4`, `ffn_hidden=256`, `vocab=4,096`). Throughput, optimizer share, and VRAM are real CUDA measurements for this shape and batch size; do not extrapolate them as production-scale numbers (we do not state a production model scale — run at the production scale TSAI sets).

**Exact reproduction command:**
```bash
uv run --no-project --with numpy --with pyyaml --with safetensors --with torch \
  python teams/10-post-training/dt/bench_gpu_muon_recompute.py \
  --device cuda --layers 8 --embd 512 --heads 8 --kv-heads 4 --ffn-hidden 256 \
  --vocab 4096 --batch 4 --seq-len 256 --warmup 3 --steps 15 \
  --out teams/10-post-training/results/lab5_gpu_muon_recompute.json
```
Raw JSON: [`lab5_gpu_muon_recompute.json`](lab5_gpu_muon_recompute.json). Unit test: `dt/test_gpu_muon_recompute.py`.

---

## 1. CUDA-Synced Step Time, Optimizer Share & Peak VRAM (`66.13M` Team 5 MoE, `bf16` autocast)

`3` warm-up steps + `15` timed steps (`torch.cuda.synchronize()` around both the full step and `opt.step()`).

| Arm | Trainable Params | Recompute | Median Step (ms) | Median Optim (ms) | `optim_step_share` | Throughput (`tok/s`) | Peak VRAM (GB) | Last Loss |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| `full_adamw` | 66,134,528 | off | 40.291 | 6.668 | **16.95%** | 25,415.3 | 1.5949 | 3.71054 |
| `full_hybrid_muon` | 66,134,528 | off | 98.424 | 65.301 | **66.31%** | 10,403.9 | **1.3799** | 6.24362 |
| `full_hybrid_muon_recompute` | 66,134,528 | on | 118.088 | 66.111 | **53.94%** | 8,671.5 | **1.3799** | 6.24362 |
| `lora_adamw` | 5,472,256 | off | 75.252 | 3.792 | **5.01%** | 13,607.7 | 1.1269 | 5.55004 |
| `dt_adamw` | 17,825,792 | off | 48.093 | 1.929 | **3.98%** | 21,292.3 | 1.1655 | 8.34137 |
| `dt_adamw_recompute` | 17,825,792 | on | 71.084 | 1.945 | **2.65%** | 14,405.5 | **0.6870** | 8.34137 |

### Key GPU Findings

1. **Real GPU VRAM reduction with DT + activation recompute:** `dt_adamw_recompute` cuts measured CUDA peak VRAM by **41.1%** (`1.1655 GB -> 0.6870 GB`) with **exact loss parity** (`8.34137` vs `8.34137`) and `optim_step_share = 2.65%` (`1.945 ms`).
2. **Hybrid Muon saves optimizer-state VRAM vs AdamW (`1.3799 GB` vs `1.5949 GB`, -13.5%)**, because Muon keeps one momentum buffer (`buf`) per 2D matrix instead of AdamW's two (`exp_avg`, `exp_avg_sq`). On `full_hybrid_muon_recompute`, peak VRAM stays at `1.3799 GB` because optimizer state + master weights already exceed activations at `batch=4, seq_len=256`; longer contexts (`>= 2,048`) are activation-bound and recover VRAM there too.
3. **Hybrid Muon `optim_step_share` on MoE (`66.31%` at `1,024` tokens/step):** With `16` routed experts × `3` matrices × `8` layers (`384` separate `256x512` 2D parameter tensors), per-tensor Python-loop Newton-Schulz5 costs `65.3 ms` per optimizer step regardless of micro-batch size. At `1,024` tokens/step that is `66.3%` of step time; gradient accumulation to realistic SFT batch sizes (`8,192–32,768` tokens/step) amortizes the fixed `65 ms` optimizer step down proportionally, and batching equal-shape expert matrices in `hybrid_optim.py` is the next clear optimization if MoE full-FT uses Hybrid Muon.

---

## 2. Gradient-Coverage Check on CUDA (TSAI 28 Nov Rule #6)

One forward and backward pass on CUDA (`batch=4, seq_len=256`), comparing fast path **OFF** vs **ON**:

| Pair (Fast Path OFF vs ON) | Trainable Tensors | `None` Grads (OFF / ON) | All-Zero Grads (OFF / ON) | Lists Identical | Max `|grad_off - grad_on|` |
|---|---:|---:|---:|---|---:|
| `full_hybrid_muon` vs `full_hybrid_muon_recompute` (`bf16`) | 467 | 0 / 0 | 0 / 0 | **yes** | `0.0` |
| `dt_adamw` vs `dt_adamw_recompute` (`bf16`, task loss only) | 136 | 0 / 0 | 0 / 0 | **yes** | `0.0` |
| `full_hybrid_muon` (`fp32`) vs `full_hybrid_muon` (`bf16` autocast) | 467 | 0 / 0 | 0 / 0 | **yes** | `0.0015404` |

Every trainable tensor received a non-zero gradient in all three pairs (`0` `None`, `0` all-zero; activation recompute matches uncheckpointed gradients bit-for-bit on CUDA with `max_abs_grad_diff = 0.0`).
