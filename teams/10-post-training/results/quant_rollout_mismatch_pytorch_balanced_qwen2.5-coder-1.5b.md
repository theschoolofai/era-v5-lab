# Quantized-rollout mismatch against a PyTorch bf16 reference: Qwen2.5-Coder-1.5B (Team 12 follow-up to #894)

**Scope and limits:** Qwen2.5-Coder-1.5B, Kaggle T4 x2, 8 rollouts per prompt, at most 256 new tokens, eps = 0.2, temperature = 1.0 (Team 10's defaults). Prompts: 50 from the fixed prompt file, selection `balanced` (10 english, 10 indic, 10 code, 10 tool_call, 10 reasoning). The sampler is a quantized llama.cpp GGUF; the reference scores the same token ids in PyTorch (bfloat16 weights, fp32 logits, cuda, torch 2.11.0+cu126), the setup of `rl-loop/policy.py`. Intervals are 95% percentile intervals that resample prompts (the rollouts of a prompt are not independent). One seed, one model. Mean KL is not available in PyTorch mode (it needs the sampler's full distribution). Rollout tok/s is llama-cpp-python decode on that GPU, one stream at a time, not a rollout engine's throughput.

Reference model: `Qwen/Qwen2.5-Coder-1.5B@df3ce67c0e24480f20468b6ef2894622d69eb73b`. Notebook version `1edb192ad957` (G12 `rollout_mismatch.ipynb`). Source PRs: this work https://github.com/theschoolofai/era-v5-lab/pull/965; the llama.cpp-reference baseline https://github.com/theschoolofai/era-v5-lab/pull/894.

| Format | Tokens outside [0.8, 1.2] (below / above) | 95% interval | abs log-ratio p50 / p90 / p99 | k3 | k3 95% interval | Top-1 agreement | Rollout tok/s | Speed vs llama.cpp bf16 (same harness) |
|---|---:|---|---|---:|---|---:|---:|---:|
| `bf16` | **0.31%** (0.13% / 0.18%) | [0.17%, 0.49%] | 0.00707 / 0.0548 / 0.132 | **0.0007** | [0.0005, 0.0008] | 98.30% [97.93%, 98.67%] | 58.7 | 1.00x |
| `Q8_0` | **1.58%** (0.59% / 0.99%) | [1.10%, 2.11%] | 0.01 / 0.0943 / 0.228 | **0.0018** | [0.0015, 0.0023] | 97.69% [97.21%, 98.18%] | 81.4 | 1.39x |
| `Q6_K` | **6.20%** (2.87% / 3.33%) | [5.06%, 7.34%] | 0.0167 / 0.155 / 0.384 | **0.0053** | [0.0043, 0.0064] | 96.26% [95.45%, 97.01%] | 84.8 | 1.45x |
| `Q5_K_M` | **13.75%** (7.05% / 6.70%) | [11.95%, 15.55%] | 0.0294 / 0.249 / 0.614 | **0.0124** | [0.0104, 0.0145] | 94.07% [93.09%, 95.11%] | 90.4 | 1.54x |
| `Q4_K_M` | **25.45%** (14.35% / 11.09%) | [22.47%, 28.16%] | 0.0573 / 0.441 / 1.17 | **0.0468** | [0.0364, 0.0621] | 90.28% [88.70%, 91.80%] | 92.3 | 1.57x |

## By prompt category (PyTorch reference; prompts per category in the header; intervals resample the prompts of that category)

| Format | code: outside / k3 / top-1 | english: outside / k3 / top-1 | indic: outside / k3 / top-1 | reasoning: outside / k3 / top-1 | tool_call: outside / k3 / top-1 |
|---|---|---|---|---|---|
| `bf16` | 0.00% / 0.0003 / 98.74% | 0.11% / 0.0006 / 97.94% | 1.01% / 0.0014 / 97.15% | 0.05% / 0.0002 / 99.66% | 0.23% / 0.0006 / 97.95% |
| `Q8_0` | 0.55% / 0.0009 / 98.73% | 1.46% / 0.0020 / 96.79% | 3.59% / 0.0036 / 96.09% | 0.43% / 0.0006 / 99.35% | 1.06% / 0.0015 / 97.70% |
| `Q6_K` | 2.86% / 0.0026 / 97.96% | 7.27% / 0.0056 / 94.21% | 10.29% / 0.0091 / 94.19% | 3.29% / 0.0027 / 98.28% | 7.70% / 0.0068 / 96.15% |
| `Q5_K_M` | 9.32% / 0.0092 / 96.10% | 17.60% / 0.0136 / 92.22% | 19.11% / 0.0190 / 90.73% | 7.83% / 0.0064 / 97.22% | 14.37% / 0.0129 / 94.89% |
| `Q4_K_M` | 19.90% / 0.0261 / 92.98% | 31.75% / 0.0441 / 88.92% | 35.29% / 0.0910 / 85.02% | 14.25% / 0.0260 / 95.22% | 26.26% / 0.0406 / 89.45% |

Each category has few prompts (10 at a balanced 50), so these cells are noisier than the pooled table; the intervals are in `torch_reference.json` (`by_category`).

**Reading the table**
- The `bf16` row has no quantization in it: llama.cpp's bf16 sampler against the PyTorch reference. It is the engine-to-engine floor (0.31% of tokens outside, k3 0.0007); a quantized row's excess over it is the quantization part.
- The speed column divides a format's rollout tok/s by the `bf16` sampler's tok/s from the same run and session. It is not a speedup against PyTorch bf16 decoding, which was not measured.
- Team 10's stop rule (`k3 <= 0.05`), on the pooled k3 with its interval: under the limit: `bf16`, `Q8_0`, `Q6_K`, `Q5_K_M`; interval contains the limit: `Q4_K_M` (0.0468, interval 0.0364 to 0.0621); above the limit: none.
