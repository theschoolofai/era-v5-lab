# Lab 5 Gradient-Coverage Check (TSAI 28 Nov Rule #6)

Verifies TSAI's 28 Nov Rule #6 across Team 10's fast paths on **NVIDIA GeForce RTX 5070 Ti (CUDA)**: after one forward and backward pass, lists every trainable parameter whose gradient is `None` or all zero, records why each entry is allowed, and compares fast path ON vs OFF on identical weights.

**Exact reproduction commands:**
```bash
uv run --no-project --with torch --with numpy \
  python teams/10-post-training/dt/check_grad_coverage.py --device cuda \
  --out teams/10-post-training/results/lab5_grad_coverage.json
uv run --no-project --with pytest --with torch --with numpy \
  python -m pytest teams/10-post-training/dt/test_grad_coverage.py -v -p no:cacheprovider
```
Raw output: [`lab5_grad_coverage.json`](lab5_grad_coverage.json).

**Scope & limits:** Routed MoE stand-in (`2` layers, `d=48`, `h=96`, `6` experts top-2) on RTX 5070 Ti CUDA; verifies gradient coverage and fast-path ON vs OFF parity, not production model throughput.

## Measured Fast-Path ON vs OFF Comparison (RTX 5070 Ti CUDA)

| Check | Fast Path ON vs OFF | Trainable Tensors | `None` Grads | All-Zero Grads | Lists Identical? | Max `\|grad_fast - grad_ref\|` | Verdict |
|---|---|---:|---:|---:|---|---:|---|
| `dt_regulariser_backward_vs_autograd` | `dtmask.regulariser_backward_()` vs autograd `regulariser().backward()` | 12 | `0` vs `0` | `0` vs `0` | **Yes** | `0.0` | **PASS** |
| `dt_activation_recompute_use_reentrant_false` | `checkpoint(..., use_reentrant=False)` ON vs OFF | 12 | `0` vs `0` | `0` vs `0` | **Yes** | `0.0` | **PASS** |
| `full_moe_cuda_bf16_autocast_vs_fp32_with_idle_expert` | CUDA `bfloat16` autocast ON vs `float32` OFF (expert 5 held at 0 tokens via `router_bias`) | 43 | `0` vs `0` | `6` vs `6` | **Yes** | `0.0003002` | **PASS** |

## Listed `None` / All-Zero Parameters & Allowed Reasons

- **`dt_regulariser_backward_vs_autograd`:** `none_grads = []`, `zero_grads = []` (all 12 DT `.gate` tensors receive exact gradients).
- **`dt_activation_recompute_use_reentrant_false`:** `none_grads = []`, `zero_grads = []` (all 12 DT `.gate` tensors receive exact gradients).
- **`full_moe_cuda_bf16_autocast_vs_fp32_with_idle_expert`:** `none_grads = []`; the 6 all-zero gradients are identically `blocks.{0,1}.experts.5.{gate,up,down}.weight` on both `bf16` autocast ON and `fp32` OFF. **Why allowed:** expert 5 was routed 0 tokens (`router_bias[5] = -50.0`), and `capstone/hybrid_optim.py` (`skip_zero_grad=True`) skips these all-zero tensors so stale Muon momentum does not move idle experts. All 37 remaining trainable tensors have non-zero gradients in both paths.
