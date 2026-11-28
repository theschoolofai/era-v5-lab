# vLLM W4A16 rollouts against a PyTorch bf16 reference: Qwen2.5-Coder-1.5B (G12 task 3, with Team 10)

**Status:** 28 Nov 2026, Kaggle T4 x2, notebook `rollout_vllm.ipynb` version `1f0a071bc0f2` (recorded in `environment.json`, run by SomaKorada07). One model, one seed, one quantization recipe.
Every number below is read from the JSON files in `torch_reference_qwen2.5-coder-1.5b_vllm/`.

Team 10 asked for the path they would run on a GPU: vLLM sampling a W4A16 (GPTQ) copy of the policy, scored against the PyTorch bf16 model that trains it. The llama.cpp Q8_0 row of the same model and prompts (from `rollout_mismatch.ipynb`) is given for comparison.

## Setup

| Item | Value |
|---|---|
| Model | `Qwen/Qwen2.5-Coder-1.5B@df3ce67c0e24480f20468b6ef2894622d69eb73b` |
| Sampler | vLLM 0.33.0 on a T4, dtype `half` (a T4 has no bf16 compute, so fp16): the unquantized model (`vllm_fp16`) and the W4A16 copy (`vllm_W4A16`), temperature 1, top-k, top-p and min-p off |
| Quantization | llm-compressor 0.15.0 GPTQ, scheme W4A16, group size 128, `lm_head` kept in bf16 (the model ties it to the embedding, which stays bf16); calibration 256 documents x 1024 tokens of `HuggingFaceFW/fineweb-edu/sample-10BT` (web text, not code); 1278 s |
| Quantized folder | 196 of 196 decoder linears packed, 1.14 GB (0.37 of the base), 8 files; sha256 of every file in `W4A16_manifest.json` (the exported zip was checked against it) |
| W4A16 kernel on the T4 | `MarlinLinearKernel` for CompressedTensorsWNA16 (from the vLLM log of the sampling process) |
| Prompts | 50 of `prompts/fixed_100.jsonl`, balanced: 10 each of english, indic, code, tool_call, reasoning; 8 rollouts each (400 per format), at most 256 new tokens |
| Reference | the Hugging Face model in PyTorch bf16 on CUDA, fp32 logits (`rl-loop/policy.py`'s setup); intervals resample prompts (2,000 resamples) |

## Result

| Format | Outside [0.8, 1.2] (95% interval) | k3 (95% interval) | Top-1 (95% interval) | vLLM batched tok/s | vs the vLLM baseline |
|---|---|---|---|---:|---:|
| vllm_fp16 | 0.32% [0.18%, 0.48%] | 0.0008 [0.0006, 0.0010] | 98.16% [97.83%, 98.49%] | 2682.63 | 1.00x |
| vllm_W4A16 | 39.68% [36.37%, 43.06%] | 0.1186 [0.1007, 0.1375] | 83.28% [81.14%, 85.37%] | 2808.55 | 1.05x |

For comparison, the llama.cpp Q8_0 row of the same model and prompts (single-stream decode, a different engine and speed measure): outside 1.58%, k3 0.0018 [0.0015, 0.0023], top-1 97.69%.

## By category (PyTorch reference; k3 with its 95% interval, share of tokens outside in brackets)

| Format | code | english | indic | reasoning | tool_call |
|---|---|---|---|---|---|
| vllm_fp16 | 0.0004 [0.0003, 0.0004] (0.0%) | 0.0006 [0.0005, 0.0006] (0.0%) | 0.0018 [0.0015, 0.0021] (1.0%) | 0.0003 [0.0002, 0.0004] (0.0%) | 0.0007 [0.0005, 0.0008] (0.2%) |
| vllm_W4A16 | 0.0860 [0.0789, 0.0940] (34.1%) | 0.0683 [0.0592, 0.0815] (39.5%) | 0.2223 [0.2023, 0.2413] (57.4%) | 0.0930 [0.0757, 0.1146] (26.8%) | 0.0971 [0.0800, 0.1161] (37.6%) |

## Per prompt and per simulated step against Team 10's k3 limit of 0.05 (steps: 16 prompts drawn from the 50, 20,000 draws)

| Format | Prompts above 0.05 | Rollouts above 0.05 | Steps above 0.05 | Step k3 median / p95 | Largest prompt |
|---|---:|---:|---:|---|---:|
| vllm_fp16 | 0% | 0.0% | 0.0% | 0.0008 / 0.0011 | 0.003 |
| vllm_W4A16 | 96% | 87.5% | 100.0% | 0.1183 / 0.1421 | 0.273 |

## What it says

- **The vLLM sampler is sound:** the unquantized model in vLLM matches the PyTorch reference as closely as llama.cpp's bf16 does (k3 0.0008 here, 0.00066 for llama.cpp bf16 on the same model). Running fp16 on a T4 against a bf16 reference costs nothing visible.
- **This W4A16 copy does not meet Team 10's k3 limit.** Pooled k3 is 0.1186 (0.1007 to 0.1375), above 0.05 with the whole interval; 39.68% of sampled tokens are outside the trust region. It is 2.5 times the k3 of this model's llama.cpp Q4_K_M (0.0468) and 64 times that of Q8_0 (0.0018).
- **It fails in every category** (every interval above 0.05); Indic is the worst (k3 0.222, top-1 71.5%). 96% of prompts and 100% of simulated steps exceed 0.05, so a per-step limit would stop a run at its first steps.
- **It buys almost no speed here:** 1.05x the vLLM baseline in batched throughput on a T4, against 1.39x to 1.57x for the llama.cpp formats of this model (single-stream, a different measure).
- **The quantized model behaves like a degraded one:** 156 of 400 rollouts end at an end-of-text token, against 193 for the baseline, and it writes 10% more tokens.

## Limits

- **One recipe, one calibration set, one seed.** The recipe is the week-2 one: symmetric 4-bit, group size 128, every decoder linear, calibrated on web text (fineweb-edu), not code. A code-calibrated W4A16, another group size, or an 8-bit scheme (W8A16, the counterpart of Q8_0) may do better; none was run, so this is not a result about 4-bit weights in general.
- **A T4 computes in fp16,** the reference is bf16; the baseline row shows the gap is small, but the exact bf16 GPU path was not run (it needs an L4 or A100).
- **vLLM's tokens/s is batched throughput** (all 400 sequences at once), not the single-stream decode speed of the llama.cpp rows; compare it only with the vLLM baseline.
- **The step shares** are drawn from 50 prompts with completions of at most 256 tokens (Team 10's are 1,536 or more); read them as indicative. With k3 this far above 0.05 the conclusion does not depend on them.
- **The kernel line** comes from the vLLM log of the sampling process; the log is appended to across runs, and both loads in it (the smoke and this run) used the same kernel.
- The quantized folder (a zip of about 1.15 GB) is not committed; releasing any model file is TSAI's decision (Qwen2.5-Coder-1.5B is Apache-2.0). The token-id dumps are not committed either.
