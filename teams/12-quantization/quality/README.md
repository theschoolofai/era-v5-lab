# OLMoE: KL divergence of each quantized format from bf16

A third measurement next to the benchmark scores (`runs/runs.csv`, `eval_mini/`) and WikiText-2 perplexity (`perplexity/`).
Run on 26 Oct 2026 by s9k96. Results: [`kl.csv`](kl.csv).

## Why

Perplexity only looks at the probability each model gives the **true** next token, so errors can cancel: a quantized
model can be more confident on some tokens and less on others and keep almost the same average. KL divergence
compares the **whole** next-token distribution of the quantized model with bf16's at every token; it is never
negative, so nothing cancels, and it needs no correct answer: bf16 is the reference. Two related numbers:

- **Same top-1:** how often the quantized model's most likely next token is bf16's. With greedy decoding, 1 minus this
  is the share of positions where the two models would start to write different text.
- **PPL ratio:** PPL(quantized) / PPL(bf16) on the same tokens, with an uncertainty that accounts for both runs
  seeing the same text. It puts a number on the note in `perplexity/README.md` that the differences between formats
  are more certain than each value's own ±.

## Results

| Format | Size | KL divergence (mean) | KL 99th pct | Same top-1 as bf16 | PPL | PPL ratio vs bf16 | Pass time |
|---|---|---|---|---|---|---|---|
| bf16 | 13.84 GB | (reference) | | | 8.818 ± 0.171 | 1 | not recorded |
| Q8_0 | 7.36 GB | 0.0013 | 0.015 | 98.3% | 8.818 ± 0.171 | 1.0007 ± 0.0005 | 29 s |
| Q6_K | 5.71 GB | 0.0038 | 0.035 | 96.8% | 8.844 ± 0.172 | 1.0036 ± 0.0008 | 26 s |
| Q5_K_M | 4.95 GB | 0.0081 | 0.063 | 95.3% | 8.862 ± 0.172 | 1.0057 ± 0.0012 | 26 s |
| Q4_K_M | 4.24 GB | 0.0233 | 0.183 | 92.1% | 8.970 ± 0.174 | 1.0179 ± 0.0019 | 23 s |
| Q3_K_M | 3.37 GB | 0.0576 | 0.410 | 87.9% | 9.325 ± 0.182 | 1.0582 ± 0.0031 | 24 s |
| Q2_K | 2.59 GB | 0.2336 | 1.523 | 76.2% | 11.322 ± 0.226 | 1.2848 ± 0.0078 | 22 s |

- **Every step down the ladder is measurably worse**, including the steps perplexity alone cannot separate: Q8_0's
  PPL is 8.818 like bf16's, but 1.7% of its top-1 tokens differ and its KL is non-zero. KL grows 2 to 3 times per step
  from Q8_0 to Q3_K_M, then 4 times from Q3_K_M to Q2_K.
- **Same top-1** reads as text drift under greedy decoding: Q4_K_M picks a different next token than bf16 at 1 position
  in 13, Q2_K at 1 in 4.
- **The PPL ratio's ± is 30 to 340 times smaller than each PPL's own ±** (0.0005 to 0.0078 against about 0.17),
  because both runs see the same tokens. So even Q6_K's +0.36% is real, which a comparison of the PPL values with
  their own ± would miss. Q8_0's +0.07% is only 1.4 times its ± (0.0005): not shown to differ from bf16 by perplexity; KL and top-1 do show it.
- **Agrees with `perplexity/`** (full WikiText-2 test, Kaggle T4, CUDA): PPL increase vs bf16 there / here is
  Q8_0 +0.02% / +0.07%, Q6_K +0.24% / +0.36%, Q5_K_M +0.58% / +0.57%, Q4_K_M +2.32% / +1.79%, Q3_K_M +6.55% / +5.82%,
  Q2_K +31.4% / +28.5%. Same ordering and size; the gaps come from the different slice of text (64 chunks here, the
  whole test set there) and backend.
- The absolute PPL (8.82) differs from `perplexity/` (7.99) because this run scores a different part of the text.
  Compare ratios, not absolute values.
- Pass times are for 16k scored tokens on the M5 GPU and say nothing about generation speed. The bf16 pass time
  was not recorded in this run (the script records it from now on).

## Setup

- Model: `allenai/OLMoE-1B-7B-0924`, revision `6d84c48581ec` (same pin as `scripts/quantize_eval.py`)
- Quantization: the GGUFs of `scripts/quantize_eval.py` (output layer Q8_0, router F32), llama.cpp b11669 (Homebrew 0.7.0)
- Text: WikiText-2 raw test (HF `Salesforce/wikitext`, pinned commit), first 64 chunks of 512 tokens; llama.cpp
  scores the second half of each chunk, so **16,384 tokens** are compared
- Machine: Apple M5, 16 GB. The bf16 reference pass runs on the CPU (`--base-ngl 0`), to keep the 13.8 GB bf16 file
  out of GPU memory on a 16 GB Mac (GPU offload of bf16 was not tried). The quantized passes run on the GPU.
- Tool: `llama-perplexity --kl-divergence-base` (saves bf16's log-probabilities, ~100 KB per scored token: 1.6 GB here) and
  `--kl-divergence` (compares a quantized model with them)

## Reproduce

```bash
python teams/12-quantization/quality/kl_eval.py --base-ngl 0          # 16 GB Mac: bf16 pass on CPU
python teams/12-quantization/quality/kl_eval.py --chunks 4            # quick check, ~2 min
```

It reuses the GGUFs in `~/.cache/era-v5-quant` made by `scripts/quantize_eval.py` (same file names) and makes any
missing format with the same rule. It needs the bf16 GGUF there first: run `scripts/quantize_eval.py` once.
Each run appends one row per format to `kl.csv`; logs go to `~/.cache/era-v5-quant/kl-logs/`.
