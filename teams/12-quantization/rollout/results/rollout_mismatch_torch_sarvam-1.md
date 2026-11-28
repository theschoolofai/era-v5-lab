# Quantized rollouts against a PyTorch bf16 reference: sarvam-1 (G12 design task 3, with Team 10)

**Status:** 28 Nov 2026, Kaggle T4 x2, notebook `rollout_mismatch.ipynb` version `1d623bbcc0a6` (in `environment.json`, run by SomaKorada07).
Follow-up to #894: the same 384 sampled rollouts per format, now also scored by PyTorch, the setup of Team 10's trainer
(`rl-loop/policy.py`: bf16 weights, fp32 logits), with 95% intervals that resample the 48 prompts. One model, one seed.
Every number below is read from the JSON files in `torch_reference_sarvam-1/`.

## Setup

| Item | Value |
|---|---|
| Model | `sarvamai/sarvam-1` @ `e9607337286ddf496d4a2562b194e489dcf3feea`, dense |
| Sampler | quantized llama.cpp b11669 GGUF (llama-cpp-python 0.3.36, CUDA), output layer Q8_0 below 8 bits, temperature 1, top-k, top-p and min-p off |
| References | (1) llama.cpp bf16 GGUF, as #894; (2) the Hugging Face model in PyTorch bfloat16 on cuda, torch 2.11.0+cu126, fp32 logits |
| Prompts | the first 48 of `prompts/fixed_100.jsonl`: **40 English, 8 Indic, no code** (this notebook version did not record the selection) |
| Rollouts | 8 per prompt (384 per format), at most 256 new tokens |
| eps | 0.2 (`grpo.TR_EPSILON`) |
| Intervals | 95% percentile intervals, resampling the 48 prompts (2,000 resamples) |

## Result

| Format | Outside, llama.cpp ref | Outside, PyTorch ref (95% interval) | Difference (pts) | k3, llama.cpp ref | k3, PyTorch ref (95% interval) | Difference | Top-1, llama.cpp ref | Top-1, PyTorch ref (95% interval) | Rollout tok/s |
|---|---:|---|---:|---:|---|---:|---:|---|---:|
| Q8_0 | 9.18% | **11.55%** [9.84%, 13.24%] | +2.37 | 0.0065 | **0.0079** [0.0069, 0.0089] | +0.0014 | 94.34% | 93.45% [92.27%, 94.60%] | 77.39 |
| Q6_K | 16.75% | **18.23%** [15.98%, 20.18%] | +1.48 | 0.0127 | **0.0141** [0.0125, 0.0157] | +0.0014 | 93.19% | 92.96% [91.99%, 93.93%] | 84.14 |
| Q5_K_M | 27.51% | **28.37%** [26.43%, 30.21%] | +0.86 | 0.0264 | **0.0276** [0.0255, 0.0298] | +0.0013 | 90.35% | 89.83% [88.96%, 90.70%] | 95.97 |
| Q4_K_M | 40.99% | **40.95%** [38.19%, 43.52%] | -0.04 | 0.0739 | **0.0751** [0.0693, 0.0823] | +0.0011 | 84.73% | 84.64% [83.24%, 86.05%] | 105.47 |

## What it says

- **The ranking and the size of the effect hold against the PyTorch reference.** Outside the trust region: Q8_0 11.55%, Q6_K 18.23%, Q5_K_M 28.37%, Q4_K_M 40.95%.
- **PyTorch shows a little more mismatch than llama.cpp's bf16 for the three higher bit-widths** (+2.37, +1.48 and +0.86 points of tokens outside) and the same at Q4_K_M (-0.04). The k3 difference is nearly constant at +0.0011 to +0.0014, which is consistent with a fixed llama.cpp-versus-PyTorch term on top of the quantization gap. This run has no bf16 sampler row, so that term is not measured directly.
- **Team 10's stop rule (k3 at or below 0.05):** Q8_0, Q6_K and Q5_K_M have interval upper bounds under it (0.0089, 0.0157, 0.0298); Q4_K_M's lower bound (0.0693) is above it. Q5_K_M passes the rule but masks 28.37% of tokens; whether that is acceptable is Team 10's call.
- The llama.cpp columns equal #894's (outside, top-1 and k3 to the digits shown; only tok/s differs), so the sampling is reproducible across sessions.

## Limits

- **Mostly English prompts:** 40 of 48 are English and 8 Indic; nothing here says anything about code. A balanced prompt set, a code model (Qwen2.5-Coder-1.5B) and a bf16 sampler row (for the engine floor and a speed ratio) are the next runs.
- **One model, one seed, base model, raw prompts** (not chat-formatted RL prompts). Intervals resample prompts, not seeds.
- **Mean KL is not available** in PyTorch mode (it needs the sampler's full distribution); the llama.cpp-reference columns of #894 have it.
- **Speed** is llama-cpp-python decode on T4s with `logits_all`, one stream at a time. No bf16 speed was measured here, so no speed ratio is claimed.
- The dump of sampled token ids (model-generated completions) is not committed.
