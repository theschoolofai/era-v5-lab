# exp1-lr-1e-3

Arm owner: Mukund Singh (`mukund-23`). EXP-1, size T1. Plan: `experiments/plan_v1.md`.

## What this arm changes

| Field | Value |
|---|---|
| Config | `configs/arms/exp1/lr_1e-3.yaml` (inherits `configs/arms/t1.yaml`) |
| The one change from T1 | `optim.lr` = 0.001 |
| Optimizer | AdamW, betas (0.9, 0.999), weight decay 0, grad clip 1.0, constant schedule, no warmup |
| Budget | batch 8, context 1,024, 245 steps, 30 min cap |

`t1.yaml` also sets `optim.lr: 0.001`, as a timing placeholder that lets the loader take a step.
This arm sets 0.001 on purpose, as one of the five swept rates. The number is the same; the meaning is not.

## Job

| Field | Value |
|---|---|
| Job | TBD (EXP-1 job file and results path) |
| Harness | `harness/train_week2.py` at commit TBD |
| Settings | TBD (agreed settings file / `runtime.yaml` commit) |
| Hardware, dtype | TBD GPU, bf16 |
| Held-out | `heldout_v1/data/heldout_v1.jsonl`, sha256 `21c6e4b2…`, 1,059 docs, named by `results/heldout_v1.sha256` |
| Training data | TBD (train file name and sha256 from the job manifest) |

## Result

bits per byte = sum of next-token loss in nats over every held-out token / ln 2 / UTF-8 bytes of the held-out text.
The winner-rule mean is the three-group mean (English, code, mean of the 11 Indic slices). Code and the Indic mean are the guards.

Made by:

```bash
python teams/05-architecture/experiments/exp1/lr_1e-3/summarize_arm.py TBD/seed1234 TBD/seed1235 TBD/seed1236 \
  --json teams/05-architecture/experiments/exp1/lr_1e-3/arm_summary.json
```

TBD: paste the table and the mean/spread lines that the command prints.

| seed | steps | wall min | three-group bpb | whole-file bpb | English | code | Indic mean | NaN/inf | counted |
|---|---|---|---|---|---|---|---|---|---|
| 1234 | TBD | | | | | | | | |
| 1235 | TBD | | | | | | | | |
| 1236 | TBD | | | | | | | | |

Mean and seed spread (max − min): TBD. Per-slice bpb for each seed: `arm_summary.json`.

NaN check: every number in `metrics.jsonl` and `summary.json` and every line of `losses.txt`, for all three seeds. TBD.

The script also checks each run: `optim.lr` is 0.001, GPU bf16, 245 of 245 steps inside 30 min, the official held-out sha256,
`val/bpb` equal to nats / ln 2 / bytes, and the three seeds differ only in `run.seed` (same config, code, data and artifacts).

## Smoke test before the job (not a result)

CPU fp32 on main `ea7b533` (#190 at `656696c`, #191 at `885a86d`), Tue 3 Nov:
- 61 of 61 week-2 tests pass. `check_week2.py` on this arm: 0 errors, dense untied head.
- Tokenizer v0 `2de039f2…`, raw P32 table content `47d411a9…`.
- Two seed-1234 runs, 20 steps, sequence 128, batch 2: identical `losses.txt` and final model sha `e59a5fcb…`. 0 NaN or inf. First train CE 11.94 (ln 131,072 = 11.78), last 6.43.
- Smoke settings came from `configs/small/smoke_resolution.yaml` (`norm_eps` 1e-6). The job uses the agreed settings. Its bits per byte on a 50-doc held-out slice is not a result.

## Limits

- One constant learning rate, no warmup, about 2.0M training tokens at T1. The arm says which of five rates scores best in this setup, not the best rate for a longer run.
- The training mix is not set. About 73% of held-out bytes are Indic, so the score depends on the training data the job uses.
- The comparison across the five arms is Shivanshu's, in `experiments/results_v1.md`.
