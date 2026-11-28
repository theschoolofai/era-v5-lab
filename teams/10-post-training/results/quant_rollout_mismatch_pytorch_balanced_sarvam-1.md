# Quantized-rollout mismatch against a PyTorch bf16 reference: sarvam-1 (Team 12 follow-up to #894)

**Scope and limits:** sarvam-1, Kaggle T4 x2, 8 rollouts per prompt, at most 256 new tokens, eps = 0.2, temperature = 1.0 (Team 10's defaults). Prompts: 50 from the fixed prompt file, selection `balanced` (10 english, 10 indic, 10 code, 10 tool_call, 10 reasoning). The sampler is a quantized llama.cpp GGUF; the reference scores the same token ids in PyTorch (bfloat16 weights, fp32 logits, cuda, torch 2.11.0+cu126), the setup of `rl-loop/policy.py`. Intervals are 95% percentile intervals that resample prompts (the rollouts of a prompt are not independent). One seed, one model. Mean KL is not available in PyTorch mode (it needs the sampler's full distribution). Rollout tok/s is llama-cpp-python decode on that GPU, one stream at a time, not a rollout engine's throughput.

Reference model: `sarvamai/sarvam-1@e9607337286ddf496d4a2562b194e489dcf3feea`. Notebook version `3d49ae3f859e` (G12 `rollout_mismatch.ipynb`). Source PRs: this work https://github.com/theschoolofai/era-v5-lab/pull/965; the llama.cpp-reference baseline https://github.com/theschoolofai/era-v5-lab/pull/894.

| Format | Tokens outside [0.8, 1.2] (below / above) | 95% interval | abs log-ratio p50 / p90 / p99 | k3 | k3 95% interval | Top-1 agreement | Rollout tok/s | Speed vs llama.cpp bf16 (same harness) |
|---|---:|---|---|---:|---|---:|---:|---:|
| `bf16` | **0.35%** (0.08% / 0.26%) | [0.22%, 0.49%] | 0.0134 / 0.0854 / 0.171 | **0.0012** | [0.0010, 0.0015] | 97.25% [96.66%, 97.82%] | 47.6 | 1.00x |
| `Q8_0` | **9.91%** (4.57% / 5.34%) | [8.45%, 11.25%] | 0.0307 / 0.202 / 0.432 | **0.0071** | [0.0062, 0.0079] | 95.06% [94.28%, 95.95%] | 76.4 | 1.61x |
| `Q6_K` | **16.16%** (7.96% / 8.20%) | [14.21%, 17.93%] | 0.0432 / 0.27 / 0.592 | **0.0131** | [0.0116, 0.0145] | 93.61% [92.56%, 94.69%] | 82.5 | 1.73x |
| `Q5_K_M` | **22.61%** (11.26% / 11.36%) | [20.31%, 24.86%] | 0.0506 / 0.353 / 0.834 | **0.0241** | [0.0219, 0.0263] | 92.11% [91.07%, 93.09%] | 94.8 | 1.99x |
| `Q4_K_M` | **36.70%** (21.33% / 15.37%) | [33.10%, 39.83%] | 0.107 / 0.635 / 1.51 | **0.0734** | [0.0664, 0.0802] | 86.44% [84.99%, 87.96%] | 103.3 | 2.17x |

## By prompt category (PyTorch reference; prompts per category in the header; intervals resample the prompts of that category)

| Format | code: outside / k3 / top-1 | english: outside / k3 / top-1 | indic: outside / k3 / top-1 | reasoning: outside / k3 / top-1 | tool_call: outside / k3 / top-1 |
|---|---|---|---|---|---|
| `bf16` | 0.53% / 0.0012 / 97.18% | 0.32% / 0.0014 / 96.70% | 0.05% / 0.0007 / 98.14% | 0.31% / 0.0011 / 97.92% | 0.62% / 0.0016 / 96.52% |
| `Q8_0` | 7.96% / 0.0057 / 96.80% | 10.47% / 0.0071 / 93.32% | 10.91% / 0.0077 / 94.74% | 7.57% / 0.0056 / 95.71% | 12.27% / 0.0088 / 94.41% |
| `Q6_K` | 9.55% / 0.0083 / 96.22% | 17.81% / 0.0142 / 92.47% | 20.07% / 0.0151 / 91.10% | 12.36% / 0.0115 / 93.88% | 17.70% / 0.0137 / 93.95% |
| `Q5_K_M` | 18.49% / 0.0238 / 93.86% | 26.56% / 0.0252 / 90.26% | 30.71% / 0.0293 / 88.93% | 18.59% / 0.0207 / 93.21% | 19.96% / 0.0222 / 93.71% |
| `Q4_K_M` | 24.65% / 0.0518 / 91.17% | 39.93% / 0.0842 / 83.37% | 45.78% / 0.0720 / 81.89% | 31.62% / 0.0774 / 88.51% | 40.16% / 0.0834 / 86.29% |

Each category has few prompts (10 at a balanced 50), so these cells are noisier than the pooled table; the intervals are in `torch_reference.json` (`by_category`).

The pooled rows are from the Kaggle run (CUDA). The per-category rows were recomputed on Apple MPS (2.11.0, bfloat16) from the same dump of sampled tokens, because that run's notebook did not yet record categories. The pooled numbers of the two runs agree within 0.23 points of tokens outside and 0.0006 in k3, and every MPS pooled value lies inside Kaggle's 95% interval: True.

**Reading the table**
- The `bf16` row has no quantization in it: llama.cpp's bf16 sampler against the PyTorch reference. It is the engine-to-engine floor (0.35% of tokens outside, k3 0.0012); a quantized row's excess over it is the quantization part.
- The speed column divides a format's rollout tok/s by the `bf16` sampler's tok/s from the same run and session. It is not a speedup against PyTorch bf16 decoding, which was not measured.
- Team 10's stop rule (`k3 <= 0.05`), on the pooled k3 with its interval: under the limit: `bf16`, `Q8_0`, `Q6_K`, `Q5_K_M`; interval contains the limit: none; above the limit: `Q4_K_M`.
