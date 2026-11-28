# Quantized policy for GRPO rollouts: sarvam-1, per bit-width (G12 design task 3, with Team 10)

**Status:** first real run, 28 Nov 2026, Kaggle T4 x2, notebook `rollout_mismatch.ipynb` version `1cc3dfcfb454`
(recorded in `results/environment.json`, run by SomaKorada07; every number below is read from the per-format JSON files).
One model, one seed, llama.cpp reference. Findings below hold for this setup only.

## Question

objective_v1 (Team 10, `rl-loop/grpo.py`) keeps a token only when `ratio = trainer / sampler` is inside `[1 - eps, 1 + eps]`.
If the rollout sampler is a quantized copy, quantization alone moves the ratio. How much, per bit-width?

## Setup

| Item | Value |
|---|---|
| Model | `sarvamai/sarvam-1` @ `e9607337286ddf496d4a2562b194e489dcf3feea`, dense |
| Reference | bf16 GGUF, llama.cpp b11669 via llama-cpp-python 0.3.36 (CUDA) |
| Samplers | Q8_0, Q6_K, Q5_K_M, Q4_K_M; output layer Q8_0 below 8 bits (`--output-tensor-type q8_0`), as `quantize_eval.py` |
| Prompts | first 48 of `prompts/fixed_100.jsonl`, raw text, BOS added by llama.cpp: **40 English, 8 Indic, no code, tool-call or reasoning prompts** (the file lists its categories one after another) |
| Rollouts | 8 per prompt (384), at most 256 new tokens, temperature 1, top-k, top-p and min-p off |
| Scoring | both models score the same sampled token ids, teacher-forced, full logits |
| eps | 0.2 (`grpo.TR_EPSILON`, as `mismatch_probe.py`) |
| Seed | reference 1234; sampler 1235 in every format run (the notebook starts one process per format) |

## Result

| Format | New tokens | Rollout tok/s | Outside [0.8, 1.2] | Below | Above | Mean abs log-ratio | k3 | KL(bf16 to quant) | Top-1 agreement |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Q8_0 | 50,568 | 77.38 | 9.18% | 4.51% | 4.67% | 0.0746 | 0.00654 | 0.00684 | 94.34% |
| Q6_K | 59,080 | 84.12 | 16.75% | 8.19% | 8.56% | 0.1017 | 0.01274 | 0.01281 | 93.19% |
| Q5_K_M | 58,592 | 97.02 | 27.51% | 14.17% | 13.34% | 0.1502 | 0.02638 | 0.02654 | 90.35% |
| Q4_K_M | 56,888 | 105.59 | 40.99% | 23.47% | 17.52% | 0.2519 | 0.07393 | 0.07335 | 84.73% |

Per-format JSON files (with the breakdown by the sampler's probability and by position in the completion) are in `results/`.

## What it says

- Every column moves in the same direction as the bit-width drops: more tokens outside the trust region, larger log-ratios,
  higher KL, lower top-1 agreement. Q8_0 puts 9.2% of sampled tokens outside [0.8, 1.2]; Q4_K_M puts 41.0% outside.
- k3 and KL agree to within about 10% in every row (for example Q8_0 0.00654 and 0.00684). They estimate the KL in the
  two directions, so close values mean the ratio estimate and the full-vocabulary KL tell the same story.
- Decode speed rises as the bit-width falls (77 to 106 tok/s, 1.36 times from Q8_0 to Q4_K_M). Token counts differ by format
  (50,568 to 59,080) because each format samples its own completions, which end at different lengths.
- For GRPO this means: with a Q8_0 sampler about one token in eleven would be masked out by objective_v1 from quantization
  alone; with Q4_K_M, about two in five.

## Limits (do not drop them when quoting)

- **llama.cpp bf16 is the reference, not Team 10's torch trainer.** The engine-to-engine gap of `mismatch_probe.py` is not in
  these numbers; only the quantization gap, with llama.cpp's own arithmetic as the floor. A PyTorch bf16 reference is the
  next stage.
- **No intervals.** The run saves aggregates, not per-rollout values, so no confidence interval was computed. The steps
  between formats are large, but this is unproven until intervals exist.
- **Mostly English prompts.** 40 of the 48 prompts are English and 8 are Indic, so the numbers say little about Indic text, and nothing about code. A balanced prompt set (`--balanced`: 10 per category) is the next run.
- **One model, one seed, one prompt set.** sarvam-1 is a dense base model; an MoE (Granite) is not run yet, and on a random
  MoE stand-in the mismatch was far larger (not a result, the weights were random).
- **Speed** is llama-cpp-python decode on T4s with `logits_all`, one stream at a time. It is not a rollout engine's
  throughput, and no bf16 speed was measured, so no speed-up against bf16 is claimed.
- Prompts are raw text with a base model, not chat-formatted RL prompts.

## Reproduce

Kaggle: import `teams/12-quantization/rollout/rollout_mismatch.ipynb`, GPU T4 x2, Internet on; set `N = 48`, `K = 8`,
`MAX_NEW = 256`, `FORMATS = ["Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M"]`, Save & Run All. Locally:
`python teams/12-quantization/rollout/quant_rollout_mismatch.py --ref model-bf16.gguf --quant Q8_0=model-Q8_0.gguf
--prompts teams/12-quantization/prompts/fixed_100.jsonl --out q8.json --n 48 --k 8 --max-new 256`.
