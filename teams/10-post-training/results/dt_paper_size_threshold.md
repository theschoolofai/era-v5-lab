# Where the paper's Deletion Tuning claims start to hold, by model size (28 Nov 2026)

**Evidence level: a reading of the paper (arXiv 2611.10866v1), plus a check against its released masks. Nothing was
trained.** This note is input for design task 2 ("the model size where the paper's claims start to hold") and for
`lab5_dt_muon_recompute.md` §4. The paper's table numbers are copied into `../dt/paper_size_table.py`, which prints
every derived number below. Section and table numbers refer to the paper's v1 HTML (arxiv.org/html/2611.10866v1).
The command outputs are in `dt_paper_size_threshold_evidence/`. It is a companion to `dt_mask_anatomy.md`.

## Summary

1. **Accuracy under GRPO.** Deletion Tuning (DT) is level with or above full fine-tuning (FFT) at every size from 7B
   up: Llama 8B (83.55 vs 83.24 on GSM8K), Qwen 7B (52.32 vs 51.89 on the SimpleRL-Zoo mean), Qwen 14B and
   Qwen3-30B-A3B. It is below FFT at every size up to 3B: by 6.06 points at Llama 1B, 1.00 at Llama 3B, 1.37 at Qwen
   0.5B and 2.37 at Qwen 3B. The paper has no size between 3B and 7B, so the crossover lies somewhere in that range.
   Gaps of about a point (Llama 3B −1.00, Llama 8B +0.31) are within the paper's own hyperparameter spread (§1).
2. **The accuracy ratio hides part of the gap.** Up to 3B, DT reaches 90% to 99% of FFT's accuracy (the paper's own
   figure, §5.2). Measured as the share of FFT's gain over the base model, it reaches 64% to 97%: Qwen 3B 64.2%, Qwen
   0.5B 84.0%, Llama 1B 89.8%, Llama 3B 96.5%. From 7B up it reaches 101% to 105%.
3. **Up to 3B, the other cheap methods mostly do better.** At every size up to 3B, at least three of the four LoRA
   and random-sparse (MTH) settings score above DT. The one exception is MTH 99% at Llama 3B (80.53 against DT's
   81.49). At Qwen 0.5B, LoRA r=1 (20.30) and MTH 99% (21.84) beat both FFT (19.01) and DT (17.64). DT has the
   smallest adapter at every Table 1 size; the FFT checkpoints are about 3,600 to 4,900 times larger.
4. **Under SFT** (Table 5: Llama-3.2 1B and 3B Instruct), DT matches or beats FFT at 3B on both suites. At 1B it does so
   on MMLU-Pro (18.62 vs 16.97) but not on BBEH (5.65 vs 8.35, 56% of FFT's gain). The paper has no SFT result above
   3B, and both SFT models start as Instruct models.
5. **Forgetting** was tested at the three Llama sizes only (1B, 3B, 8B; GRPO on GSM8K), and DT stays low at all three.
   Its forward KL stays at or below 0.05 and its prior-task accuracy within one point of base. FFT ends 1.3 to 3.1
   points below base, and LoRA and MTH up to 5.4 (§5.4, Figure 2). Nothing smaller than 1B was tested. At 1B DT
   reaches only 89.8% of FFT's gain, so the comparison there is not at equal task gain.

So, from the paper alone: under GRPO, "matches FFT" holds from 7B up and not up to 3B. Under SFT it holds at 3B from
an Instruct start. "Forgets less" holds at all three Llama sizes tested.

## 1. Per-size comparison

```bash
python dt/paper_size_table.py
```
```
setting                       model           base    FFT  best LoRA/MTH    DT  DT-FFT  DT/FFT  DT share of FFT gain  FFT MB / DT MB
GRPO, GSM8K (Table 1)         Llama 1B         1.21  60.50          60.73  54.44   -6.06   90.0%                 89.8%           4,714x
GRPO, GSM8K (Table 1)         Llama 3B        53.53  82.49          82.44  81.49   -1.00   98.8%                 96.5%           3,954x
GRPO, GSM8K (Table 1)         Llama 8B        60.27  83.24          83.38  83.55   +0.31  100.4%                101.3%           3,647x
GRPO, SimpleRL-Zoo (Table 1)  Qwen 0.5B       10.44  19.01          21.84  17.64   -1.37   92.8%                 84.0%           3,770x
GRPO, SimpleRL-Zoo (Table 1)  Qwen 3B         37.73  44.35          44.16  41.98   -2.37   94.7%                 64.2%           4,360x
GRPO, SimpleRL-Zoo (Table 1)  Qwen 7B         40.18  51.89          52.13  52.32   +0.43  100.8%                103.7%           4,210x
GRPO, SimpleRL-Zoo (Table 2)  Qwen 14B        44.37  54.87              -  55.43   +0.56  101.0%                105.3%           4,942x
GRPO, SimpleRL-Zoo (Table 2)  Qwen3 30B-A3B   49.41  58.43              -  58.54   +0.11  100.2%                101.2%           3,935x
SFT, MMLU-Pro (Table 5)       Llama 1B        10.37  16.97              -  18.62   +1.65  109.7%                125.0%           4,714x
SFT, MMLU-Pro (Table 5)       Llama 3B        12.63  21.19              -  22.28   +1.09  105.1%                112.7%           3,954x
SFT, BBEH (Table 5)           Llama 1B         2.17   8.35              -   5.65   -2.70   67.7%                 56.3%           4,714x
SFT, BBEH (Table 5)           Llama 3B         8.87  11.39              -  11.39   +0.00  100.0%                100.0%           3,954x

SimpleRL-Zoo per benchmark (Table 8): DT minus FFT, points (problems, for the two small sets)
model                 GSM8K         MATH500         Minerva   OlympiadBench          AIME24           AMC23   mean
Qwen 0.5B             -3.95           -2.60           +0.73           -0.75      +3.33 (+1)      -5.00 (-2)  -1.37
Qwen 3B               +0.16           +0.00           -0.37           -0.67      -3.34 (-1)     -10.00 (-4)  -2.37
Qwen 7B               -0.15           +0.60           -0.74           +0.37     +10.00 (+3)      -7.50 (-3)  +0.43

Hyperparameter sweeps (Tables 13-15): spread = best - worst setting, points
Llama 8B  DT 12 settings 82.03 to 83.55 (spread 1.52); FFT 4 settings 81.89 to 83.24 (spread 1.35); DT settings at or above the main FFT number 83.24: 3
Qwen 7B   DT 12 settings 49.60 to 52.80 (spread 3.20); FFT 4 settings 50.55 to 51.93 (spread 1.38); DT settings at or above the main FFT number 51.89: 7
```

- **How the numbers are chosen.** All numbers are the paper's best-checkpoint accuracies (%). For GRPO, the paper
  reports the best validation accuracy across saved checkpoints, so the same set picks and reports the number. For
  SFT, it validates at the end of training. This favours every method, by an amount the paper does not report.
- **Columns.** "best LoRA/MTH" is the best of LoRA r=1, LoRA r=4, MTH 99% and MTH 99.95%; Tables 2 and 5 have no
  such rows. "DT share of FFT gain" is (DT − base) / (FFT − base). The DT sizes are rounded (0.5 MB at Qwen 0.5B), so
  the size ratios are approximate.
- **Model names** follow the paper's §5.1: Llama-3.2-1B/3B-Instruct, Llama-3-8B-Instruct, the Qwen2.5 base models,
  and Qwen3-30B-A3B.
- **Per benchmark.** The Table 8 means reproduce Table 1's DT − FFT (−1.37, −2.37, +0.43).
  - At Qwen 3B, most of the gap is AMC23 (−10.00, 4 problems) and AIME24 (−3.34, 1 problem); the four larger
    benchmarks are within 0.67 points.
  - At Qwen 7B, the lead also comes down to these two small sets (+3 problems on AIME24, −3 on AMC23).
  - At Qwen 0.5B the gap is broad (GSM8K −3.95, MATH500 −2.60).
  - The problem counts assume the usual set sizes (30 AIME24 and 40 AMC23 problems). The paper does not state them,
    but the table's values are whole multiples of 1/30 and 1/40.
- **Sweeps.** The paper swept DT's settings only at Llama 8B and Qwen 7B (§5.7), and FFT's learning rate and KL
  coefficient at the same two sizes (Table 15). The spread of DT's settings there (1.52 and 3.20 points) is as large
  as the per-size gaps above. Only 3 of the 12 DT settings at Llama 8B reach FFT's 83.24.

## 2. What the paper's sizes do not settle for us

- **GRPO settings** (§5.1). The paper ramps the sharpness α from 10³ to 10⁴ over the run, with lr 3e-4 (constant),
  η 1/2048 and λ 1e-5, and no tuning per size. Rollouts per step are 64 × 4 = 256 (GSM8K, 3 epochs) and 256 × 8 =
  2,048 (SimpleRL-Zoo, 150 steps). G10's E4 GRPO DT run used the same α values, ramped over 100 steps, with
  16 × 8 = 128 rollouts per step and 60 updates (`dt_rl_e4_20261115.md`).
- **SFT settings.** Our dry run 2 DT arm matches the paper's SFT lr (5e-4) and α (10² → 10³). It differs in other
  ways:
  - 243 steps × 16 rows, against the paper's 400 steps at effective batch 4 (§5.1);
  - a warmup-plus-cosine learning rate (`sft/bench/train.py::lr_at`), where the paper's is constant;
  - the targets are MoE expert gates.
- **Instruct starts.** The paper's SFT models are Instruct models. On our bench task, pure DT gave 0 of 110 valid
  replies from SmolLM2-1.7B base, and also 0 of 110 from SmolLM2-1.7B-Instruct, whose untrained score was 107 of 110
  (`dt_sft_surrogate.md`). So an Instruct start alone did not fix pure DT on our format. The paper's Instruct starts
  are one difference from our setting, not a shown cause.
- **Seeds.** The paper does not say how many seeds it ran; each table cell is one number with no error bar. Together
  with the sweep spreads in §1, gaps of about a point in either direction may be within run-to-run variation.
- **Our dry run 2 model** (8 layers, width 512; an MoE of about 176M parameters) is far below the paper's smallest
  model (0.5B), and the paper has no MoE below 30B. The dry run 2 comparison is SFT. Under SFT the paper's smallest
  size (Llama 1B) is mixed: DT +1.65 on MMLU-Pro, −2.70 on BBEH. So the paper predicts nothing definite for this
  model, and a gap there would not contradict it.

## 3. Check of the released masks against the paper's Table 7

Table 7 gives the share of all model parameters that DT deletes in the six Table 1 runs. Applied to the released
Qwen masks (parameter counts are the safetensors totals of the base models on the Hub, tied embeddings counted once):

```bash
python dt/mask_anatomy.py masks <masks>/grpo/qwen2.5-3b-simplerl-zoo --total-params 3085938688
```

| Released mask | share of all parameters | Table 7, earliest / final saved | file size (`config.json`) / paper's adapter size, MB |
|---|---:|---|---|
| Qwen2.5-0.5B | 0.0404% | 0.0393% / 0.0405% | 0.457 / 0.5 |
| Qwen2.5-3B | 0.0380% | 0.0379% / 0.0418% | 2.724 / 2.7 |
| Qwen2.5-7B | 0.0415% | 0.0381% / 0.0415% | 7.479 / 6.9 |
| Qwen2.5-14B | 0.0325% | not in Table 7 | 11.444 / 11.4 |
| Qwen3-30B-A3B-Base | 0.0752% (0.0373% without the 18 heavy experts) | not in Table 7 | 31.675 / 29.6 |

- **0.5B and 7B** are within 0.0001 points of Table 7's final checkpoints. The 3B mask is close to the earliest
  saved checkpoint instead; its file size agrees with the paper's 2.7 MB. So the released 3B file may be an earlier
  checkpoint, for example the best one.
- **7B and 30B.** These files are larger than the paper's adapter sizes (7.479 against 6.9 MB, 31.675 against
  29.6), so they may not be the exact checkpoints in Tables 1 and 2 either.
- **The released 30B file** deletes 0.0752% of all weights, above the abstract's "fewer than 0.05%". Table 7 covers
  only the six runs up to 8B. About half of this file's deletions sit in 18 experts. On our replay of the official
  calibration on a 4-bit copy, 15 of them got 0 calibration tokens and 3 got 1 to 4 (`dt_mask_anatomy.md`). Without
  those 18 experts it would be 0.0373%.

## Limits

- A reading of the published numbers; no run was repeated. Figure 2's curves are read from the paper's text (§5.4),
  not from the plot.
- The sizes compared are the paper's models and tasks (Llama on GSM8K, Qwen on SimpleRL-Zoo, Llama on MMLU-Pro and
  BBEH), not our data or our model.
