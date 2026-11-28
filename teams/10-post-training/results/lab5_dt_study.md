# Lab 5: Deletion Tuning on a small model of Team 5's classes

28 November 2026. Team 10. Laptop CPU. Follow-up to [`lab5_dt_muon_recompute.md`](lab5_dt_muon_recompute.md): longer runs,
exact answers on unseen strings, a Muon learning-rate sweep on the gate logits and recompute on Team 5's model.

CPU stand-in, mechanics and relative comparison only, not a scale claim.

## Setup

- Model: `week2.LanguageModel` from the T2 config, cut to 4 layers, width 64, 16 routed + 1 shared expert, top 2
  (1.01M parameters). DT targets `g5_gate`: 68 gate matrices of 32 x 64.
- Per seed (1, 2): 800 pre-training steps on bytes of this repository's Markdown at `1ee65d5c` (500,000 bytes, the last
  tenth held out; sha256 in the JSON). Every arm starts from that state and takes 600 steps, batch 16.
- Task: `R:` + 6 random letters + `=` + the first letter six times. 2,048 training strings, 512 unseen ones for scoring.
  `exact` means every answer position right with teacher forcing. Before training: task loss 6.66 / 6.42, exact 0.
- Settings: full FT AdamW 1e-4 (hybrid Muon 1e-3); LoRA r=8, 1e-3; DT AdamW 5e-4, alpha 100 to 1000, lambda 1e-5,
  eta 1/2048. None of these is tuned.
- **How the task was chosen:** a first task (reverse the string, 200 steps) was learned by no arm. I tried other tasks and
  kept one that full FT and LoRA learn completely in 600 steps. Read the comparison with that choice in mind.

```bash
# from teams/10-post-training/ (885 s wall, peak 666 MB resident, 4 threads, torch 2.7.1+cpu)
OMP_NUM_THREADS=4 python dt/run_lab5_dt_study.py --seeds 1 2 --out results/lab5_dt_study.json
OMP_NUM_THREADS=4 python dt/run_lab5_dt_study.py --seeds 1 2 --coverage --out results/lab5_dt_study_coverage.json   # 4 s
```

## Results (means of 2 seeds; step time per seed)

| Arm | Trainable | Task loss | Exact | Held-out bits/byte change | Optimizer state KB | To ship KB | Saved activations KB | Step ms (seed 1 / 2) | Optimizer share (seed 1) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `full` | 1,012,288 | 0.013 | 1.000 | +1.94 | 7,909 | 1,923.1 | 17,713 | 23.8 / 24.6 | 22% |
| `full_muon` | 1,012,288 | 0.000 | 1.000 | +4.84 | 3,849 | 1,923.1 | 17,713 | 198.9 / 213.2 | 91% |
| `lora` | 171,008 | 0.000 | 1.000 | +8.19 | 1,338 | 310.8 | 17,158 | 32.1 / 36.5 | 23% |
| `dt_official_64` | 139,264 | 1.426 | 0.003 | +0.50 | 1,088 | 12.3 | 12,642 | 18.1 / 21.1 | 8% |
| `dt_official_256` | 139,264 | 1.426 | 0.003 | +0.50 | 1,088 | 12.2 | 12,642 | 18.1 / 21.3 | 8% |
| `dt_keep_64` | 139,264 | 1.426 | 0.003 | +0.50 | 1,088 | 11.9 | 12,642 | 18.2 / 21.9 | 8% |
| `dt_keep_256` | 139,264 | 1.426 | 0.003 | +0.50 | 1,088 | 11.9 | 12,642 | 18.2 / 23.0 | 8% |
| `dt_muon_gates_0.001` | 139,264 | 3.473 | 0.000 | +0.12 | 544 | 8.1 | 12,642 | 42.4 / 47.9 | 59% |
| `dt_muon_gates_0.003` | 139,264 | 2.340 | 0.000 | +0.29 | 544 | 11.3 | 12,642 | 44.8 / 51.7 | 59% |
| `dt_muon_gates_0.006` | 139,264 | 1.893 | 0.000 | +0.41 | 544 | 13.0 | 12,642 | 48.5 / 47.9 | 57% |
| `full_recompute` | 1,012,288 | 0.013 | 1.000 | +1.94 | 7,909 | 1,923.1 | 636 | 33.7 / 34.2 | 16% |
| `lora_recompute` | 171,008 | 0.000 | 1.000 | +8.19 | 1,338 | 310.8 | 434 | 53.2 / 51.9 | 14% |
| `dt_keep_64_recompute` | 139,264 | 1.426 | 0.003 | +0.50 | 1,088 | 11.9 | 434 | 30.4 / 28.4 | 5% |

Step times are from a shared laptop. Part of seed 2 ran while a test suite was also running, so compare arms within seed 1.
"Saved activations" is the size of the tensors autograd holds after one forward pass, not a measured memory peak.

## Findings

1. **Negative result: DT did not learn this task.** Full FT and LoRA answer every unseen string; DT with AdamW ends at
   task loss 1.31 to 1.54 with exact at most 0.006. Its smaller change in held-out bits per byte is therefore **not** a
   forgetting comparison: the arms did not reach the same fit.
2. **Deletion went far above eta.** Every AdamW DT arm ends with about 20% of the gate weights deleted (one layer up to
   38%), against eta = 0.049%. At lambda 1e-5 the regulariser did not hold it in this setup.
3. **`--dt-unseen`:** 5 to 9 of 68 layers got no calibration token. Under `official` they start about 50% deleted (3.8%
   to 6.7% of all gate weights); under `keep` 0.13% to 0.14% of all gate weights start deleted. During training the official
   layers recover to 1.8% to 7.8% deleted (`keep`: 0% to 0.47%). Final task loss is the same within 0.001.
4. **Calibration size was not tested here.** A layer has 2,048 logits, so eta marks `floor(2048 / 2048) = 1` entry and
   "strictly below that score" marks none. The prior deletes nothing at this size; only which layers calibration reaches
   matters, and under `keep` 64 and 256 rows give the same run.
5. **Muon on the gate logits** gets closer to AdamW as its rate rises, but at 0.006 (12 times AdamW's rate) its task loss
   is still higher (1.89 against 1.43, same step count). It halves the optimizer state and its step takes 2.2 to 2.7 times
   as long on this CPU.
6. **Full FT with hybrid Muon** reaches a lower task loss than AdamW, changes held-out bits per byte more, and takes
   8.4 to 8.7 times as long per step on this CPU. This says nothing about GPU optimizer time.
7. **Recompute** cuts saved activations by 96% to 98% and costs 30% to 66% more step time. LoRA and DT report the same
   losses with it on; full FT's last training loss differs by at most 0.000006.

## Gradient coverage, recompute off and on

TSAI's rule for speed claims: one forward and backward of the task loss, every trainable parameter whose gradient is
`None` or all zero, with the fast path off and on. Run on the untrained model of each seed. Optimizer choice does not
enter: the gradients are the same before either optimizer's step.

| Method | Seed | Trainable tensors | `None` | All zero, off and on | Lists identical | Largest gradient difference |
|---|---:|---:|---:|---|---|---:|
| full | 1 / 2 | 235 | 0 | 18 / 24 | yes | below 5e-7 (varies between runs) |
| LoRA | 1 / 2 | 440 | 0 | 238 / 244 | yes | 0 |
| DT (task loss only) | 1 / 2 | 68 | 0 | 6 / 8 | yes | 0 |

Allowed reasons, each name listed with its own in
[`lab5_dt_study_coverage.json`](lab5_dt_study_coverage.json):

- A routed expert that gets no token the loss depends on (6 experts for seed 1, 8 for seed 2; in the last layer only the
  answer positions count).
- LoRA only: `lora_B` starts at zero, so the first backward gives `lora_A` no gradient (202 / 196 tensors).

DT's regulariser is left out on purpose: it gives every logit a gradient and would hide an idle expert.

## Not measured

- No GPU, no 7B+ model, no matched-fit forgetting comparison, no tuning of DT's rate, lambda or sharpness.
- Whether finding 1 holds with more steps or other DT settings is open.
