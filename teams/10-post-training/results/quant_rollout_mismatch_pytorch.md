# Quantized-rollout mismatch against a PyTorch bf16 reference: sarvam-1 (Team 12 follow-up to #894)

**Scope and limits:** sarvam-1, Kaggle T4 x2, 8 rollouts per prompt, at most 256 new tokens, eps = 0.2, temperature = 1.0 (Team 10's defaults). Prompts: 48 from the fixed prompt file, selection `first (not recorded)` (composition not recorded by the script version of this run; the first 48 of the fixed prompts: 40 English, 8 Indic, no code). The sampler is a quantized llama.cpp GGUF; the reference scores the same token ids in PyTorch (bfloat16 weights, fp32 logits, cuda, torch 2.11.0+cu126), the setup of `rl-loop/policy.py`. Intervals are 95% percentile intervals that resample prompts (the rollouts of a prompt are not independent). One seed, one model. Mean KL is not available in PyTorch mode (it needs the sampler's full distribution). Rollout tok/s is llama-cpp-python decode on that GPU, one stream at a time, not a rollout engine's throughput.

Reference model: `sarvamai/sarvam-1@e9607337286ddf496d4a2562b194e489dcf3feea`. Notebook version `1d623bbcc0a6` (G12 `rollout_mismatch.ipynb`). Source PRs: this work https://github.com/theschoolofai/era-v5-lab/pull/908; the llama.cpp-reference baseline https://github.com/theschoolofai/era-v5-lab/pull/894.

| Format | Tokens outside [0.8, 1.2] (below / above) | 95% interval | abs log-ratio p50 / p90 / p99 | k3 | k3 95% interval | Top-1 agreement | Rollout tok/s | Speed vs llama.cpp bf16 (same harness) |
|---|---:|---|---|---:|---|---:|---:|---:|
| `Q8_0` | **11.55%** (5.66% / 5.89%) | [9.84%, 13.24%] | 0.0493 / 0.215 / 0.41 | **0.0079** | [0.0069, 0.0089] | 93.45% [92.27%, 94.60%] | 77.4 | - |
| `Q6_K` | **18.23%** (9.21% / 9.02%) | [15.98%, 20.18%] | 0.0589 / 0.285 / 0.572 | **0.0141** | [0.0125, 0.0157] | 92.96% [91.99%, 93.93%] | 84.1 | - |
| `Q5_K_M` | **28.37%** (14.64% / 13.74%) | [26.43%, 30.21%] | 0.0903 / 0.392 / 0.805 | **0.0276** | [0.0255, 0.0298] | 89.83% [88.96%, 90.70%] | 96.0 | - |
| `Q4_K_M` | **40.95%** (23.34% / 17.61%) | [38.19%, 43.52%] | 0.146 / 0.654 / 1.39 | **0.0751** | [0.0693, 0.0823] | 84.64% [83.24%, 86.05%] | 105.5 | - |

**Reading the table**
- No `bf16` sampler row was run, so no speed ratio is given.
- Team 10's stop rule (`k3 <= 0.05`) holds on the formats whose k3 and interval upper bound are at or below 0.05: `Q8_0`, `Q6_K`, `Q5_K_M`.
