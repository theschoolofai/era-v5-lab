# Quantized rollouts against a PyTorch bf16 reference, balanced prompts: sarvam-1 and Qwen2.5-Coder-1.5B (G12 task 3, with Team 10)

**Status:** 28 Nov 2026, Kaggle T4 x2 (llama.cpp b11669 samplers, llama-cpp-python 0.3.36; PyTorch reference torch 2.11.0+cu126, bf16 weights, fp32 logits). Follow-up to #894 and #908.
Every number below is read from the JSON files in `torch_reference_sarvam-1_balanced/` and `torch_reference_qwen2.5-coder-1.5b_balanced/`. One model each, one seed.

## Setup

| Item | sarvam-1 | Qwen2.5-Coder-1.5B |
|---|---|---|
| Model | `sarvamai/sarvam-1 @ e9607337286ddf496d4a2562b194e489dcf3feea` | `Qwen/Qwen2.5-Coder-1.5B @ df3ce67c0e24480f20468b6ef2894622d69eb73b` |
| Notebook version | `3d49ae3f859e` (recorded) | `1edb192ad957` (recorded) |
| Prompts | 50 of `prompts/fixed_100.jsonl`, balanced: 10 each of english, indic, code, tool_call, reasoning | the same 50 |
| Rollouts | 8 per prompt (400 per format), at most 256 new tokens, temperature 1, top-k, top-p and min-p off | the same |
| Samplers | llama.cpp GGUF, output layer Q8_0 below 8 bits; `bf16` is also run as a sampler | the same |
| eps | 0.2 (`grpo.TR_EPSILON`) | 0.2 |
| Intervals | 95% percentile, resampling prompts (2,000 resamples); per category, resampling that category's 10 prompts | the same |
| Per-category rows and the spread (sarvam-1) | recomputed on Apple MPS from the same dump, because that run's notebook did not yet record categories | per-category rows from the Kaggle run; the spread recomputed on Apple MPS |

## sarvam-1

**Pooled, PyTorch reference** (llama.cpp reference and speed beside it):

| Format | Outside [0.8, 1.2] (95% interval) | k3 (95% interval) | Top-1 (95% interval) | Outside, llama.cpp ref | k3, llama.cpp ref | Decode speed vs bf16 sampler |
|---|---|---|---|---:|---:|---:|
| bf16 | 0.35% [0.22%, 0.49%] | 0.00124 [0.00103, 0.00145] | 97.25% [96.66%, 97.82%] | 0.00% | 0.00000 | 1.00x (47.59 tok/s) |
| Q8_0 | 9.91% [8.45%, 11.25%] | 0.00709 [0.00617, 0.00793] | 95.06% [94.28%, 95.95%] | 8.47% | 0.00592 | 1.61x (76.43 tok/s) |
| Q6_K | 16.16% [14.21%, 17.93%] | 0.01308 [0.01160, 0.01446] | 93.61% [92.56%, 94.69%] | 14.79% | 0.01188 | 1.73x (82.47 tok/s) |
| Q5_K_M | 22.61% [20.31%, 24.86%] | 0.02410 [0.02189, 0.02626] | 92.11% [91.07%, 93.09%] | 22.22% | 0.02283 | 1.99x (94.81 tok/s) |
| Q4_K_M | 36.70% [33.10%, 39.83%] | 0.07344 [0.06638, 0.08017] | 86.44% [84.99%, 87.96%] | 36.49% | 0.07254 | 2.17x (103.26 tok/s) |

The `bf16` row has no quantization in it: it is the llama.cpp-versus-PyTorch engine floor (k3 0.00124, 0.35% outside). A quantized row's excess over it is the quantization part.

**By category, PyTorch reference** (k3 with its 95% interval; share of tokens outside in brackets):

| Format | code | english | indic | reasoning | tool_call |
|---|---|---|---|---|---|
| Q8_0 | 0.0057 [0.0035, 0.0076] (8.0%) | 0.0071 [0.0052, 0.0093] (10.5%) | 0.0077 [0.0056, 0.0096] (10.9%) | 0.0056 [0.0041, 0.0068] (7.6%) | 0.0088 [0.0072, 0.0103] (12.3%) |
| Q6_K | 0.0083 [0.0054, 0.0115] (9.6%) | 0.0142 [0.0122, 0.0163] (17.8%) | 0.0151 [0.0124, 0.0179] (20.1%) | 0.0115 [0.0080, 0.0143] (12.4%) | 0.0137 [0.0115, 0.0161] (17.7%) |
| Q5_K_M | 0.0238 [0.0197, 0.0284] (18.5%) | 0.0252 [0.0200, 0.0290] (26.6%) | 0.0293 [0.0251, 0.0342] (30.7%) | 0.0207 [0.0164, 0.0241] (18.6%) | 0.0222 [0.0179, 0.0265] (20.0%) |
| Q4_K_M | 0.0518 [0.0372, 0.0665] (24.7%) | 0.0842 [0.0672, 0.1060] (39.9%) | 0.0720 [0.0661, 0.0780] (45.8%) | 0.0774 [0.0648, 0.0902] (31.6%) | 0.0834 [0.0687, 0.0985] (40.2%) |

**Per prompt and per simulated step against Team 10's k3 limit of 0.05** (steps: 16 prompts drawn from the 50, 20,000 draws):

| Format | Prompts above 0.05 | Rollouts above 0.05 | Steps above 0.05 | Step k3 median / p95 | Largest prompt |
|---|---:|---:|---:|---|---:|
| Q8_0 | 0% | 0.0% | 0.0% | 0.0071 / 0.0082 | 0.023 |
| Q6_K | 0% | 0.0% | 0.0% | 0.0129 / 0.0145 | 0.029 |
| Q5_K_M | 2% | 2.0% | 0.0% | 0.0241 / 0.0268 | 0.067 |
| Q4_K_M | 90% | 90.0% | 100.0% | 0.0740 / 0.0832 | 0.211 |

## Qwen2.5-Coder-1.5B

**Pooled, PyTorch reference** (llama.cpp reference and speed beside it):

| Format | Outside [0.8, 1.2] (95% interval) | k3 (95% interval) | Top-1 (95% interval) | Outside, llama.cpp ref | k3, llama.cpp ref | Decode speed vs bf16 sampler |
|---|---|---|---|---:|---:|---:|
| bf16 | 0.31% [0.17%, 0.49%] | 0.00066 [0.00051, 0.00084] | 98.30% [97.93%, 98.67%] | 0.00% | 0.00000 | 1.00x (58.67 tok/s) |
| Q8_0 | 1.58% [1.10%, 2.11%] | 0.00184 [0.00145, 0.00228] | 97.69% [97.21%, 98.18%] | 0.69% | 0.00114 | 1.39x (81.38 tok/s) |
| Q6_K | 6.20% [5.06%, 7.34%] | 0.00533 [0.00434, 0.00643] | 96.26% [95.45%, 97.01%] | 5.32% | 0.00445 | 1.45x (84.82 tok/s) |
| Q5_K_M | 13.75% [11.95%, 15.55%] | 0.01239 [0.01042, 0.01447] | 94.07% [93.09%, 95.11%] | 13.20% | 0.01176 | 1.54x (90.37 tok/s) |
| Q4_K_M | 25.45% [22.47%, 28.16%] | 0.04678 [0.03641, 0.06211] | 90.28% [88.70%, 91.80%] | 25.04% | 0.04693 | 1.57x (92.29 tok/s) |

The `bf16` row has no quantization in it: it is the llama.cpp-versus-PyTorch engine floor (k3 0.00066, 0.31% outside). A quantized row's excess over it is the quantization part.

**By category, PyTorch reference** (k3 with its 95% interval; share of tokens outside in brackets):

| Format | code | english | indic | reasoning | tool_call |
|---|---|---|---|---|---|
| Q8_0 | 0.0009 [0.0007, 0.0011] (0.5%) | 0.0020 [0.0017, 0.0023] (1.5%) | 0.0036 [0.0030, 0.0042] (3.6%) | 0.0006 [0.0005, 0.0007] (0.4%) | 0.0015 [0.0012, 0.0019] (1.1%) |
| Q6_K | 0.0026 [0.0021, 0.0029] (2.9%) | 0.0056 [0.0036, 0.0076] (7.3%) | 0.0091 [0.0077, 0.0107] (10.3%) | 0.0027 [0.0022, 0.0033] (3.3%) | 0.0068 [0.0043, 0.0098] (7.7%) |
| Q5_K_M | 0.0092 [0.0064, 0.0125] (9.3%) | 0.0136 [0.0110, 0.0163] (17.6%) | 0.0190 [0.0161, 0.0218] (19.1%) | 0.0064 [0.0040, 0.0090] (7.8%) | 0.0129 [0.0092, 0.0180] (14.4%) |
| Q4_K_M | 0.0261 [0.0211, 0.0321] (19.9%) | 0.0441 [0.0338, 0.0552] (31.7%) | 0.0910 [0.0581, 0.1435] (35.3%) | 0.0260 [0.0177, 0.0345] (14.2%) | 0.0406 [0.0339, 0.0516] (26.3%) |

**Per prompt and per simulated step against Team 10's k3 limit of 0.05** (steps: 16 prompts drawn from the 50, 20,000 draws):

| Format | Prompts above 0.05 | Rollouts above 0.05 | Steps above 0.05 | Step k3 median / p95 | Largest prompt |
|---|---:|---:|---:|---|---:|
| Q8_0 | 0% | 0.0% | 0.0% | 0.0018 / 0.0023 | 0.006 |
| Q6_K | 0% | 0.0% | 0.0% | 0.0052 / 0.0066 | 0.014 |
| Q5_K_M | 0% | 0.0% | 0.0% | 0.0124 / 0.0148 | 0.028 |
| Q4_K_M | 26% | 26.0% | 35.7% | 0.0449 / 0.0660 | 0.327 |

## What it says

- **Q8_0 and Q6_K stay under Team 10's k3 limit of 0.05, with their intervals, on both models:** pooled k3 0.0071 and 0.0131 on sarvam-1, 0.0018 and 0.0053 on Qwen. Q5_K_M too (0.0241 and 0.0124). No simulated 16-prompt step reaches 0.05 for these three formats on either model (largest simulated step: sarvam-1 0.030, Qwen 0.018). Individual prompts stay under 0.05 for Q8_0 and Q6_K on both models and for Q5_K_M on Qwen; for Q5_K_M on sarvam-1 2% of prompts (one prompt) exceed it, the largest at 0.067.
- **Q4_K_M depends on the model.** On sarvam-1 its pooled k3 is 0.0734 (0.066 to 0.080), above the limit, and 100% of simulated steps exceed it. On Qwen it is 0.0468 (0.036 to 0.062), which straddles the limit, yet 35.7% of simulated steps exceed it: the pooled mean hides a heavy tail, so a per-step limit would stop a Q4_K_M run on either model. In both it masks a quarter or more of the sampled tokens under objective_v1 (36.70% and 25.45% outside).
- **Qwen is much less sensitive than sarvam-1** at every format (Q8_0 k3 0.0018 against 0.0071), and quantizing buys less speed on it (decode 1.39x to 1.57x against 1.61x to 2.17x on sarvam-1).
- **The engine floor is small:** llama.cpp bf16 against PyTorch bf16 gives k3 0.00124 on sarvam-1 and 0.00066 on Qwen. The PyTorch k3 of the quantized rows exceeds the llama.cpp-reference k3 by a similar small amount (sarvam-1 +0.0009 to +0.0013; Qwen -0.0001 to +0.0009).
- **By category,** Indic is the most sensitive and code the least on Qwen (Q4_K_M k3 0.091 on Indic with its interval above 0.05, 0.026 on code with its interval below it); on sarvam-1 the categories differ less. Each category has 10 prompts, so these cells are noisy.

## Limits

- **The sampler is a llama.cpp GGUF.** The numbers say nothing about int8_dynamic, the simulated schemes of Team 10's #185, or vLLM; a vLLM W4A16 run is separate.
- **One seed, one model each, 10 prompts per category, a static base model:** k3 can move as a policy trains.
- **The steps are drawn from 50 prompts** and use completions of at most 256 tokens (Team 10's are 1,536 or more): they vary somewhat less than steps with fresh prompts, and a real step averages over more tokens. The two effects work against each other; read the step shares as indicative.
- **Speed** is llama-cpp-python decode on T4s with `logits_all`, one stream at a time, against the llama.cpp bf16 sampler of the same run. It is not a speed against PyTorch bf16 decoding, and not a rollout engine's throughput.
- **Mean KL** is available only against the llama.cpp reference (the per-format files), not against PyTorch.
- The dumps (model-generated token ids) are not committed.
