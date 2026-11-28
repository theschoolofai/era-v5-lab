# Test log: router-balance arms (jobs/2026-11-29-router-balance.md)

The same script (`teams/05-architecture/harness/train_week2.py`) and arm files, run before the request: on a Colab T4 (dry run 2's arm at full shape) and on a laptop CPU (every arm, small shape). Smoke mode marks these "not a quality result"; they check that the setup is right and every arm runs.

## 1. Colab T4, dry run 2's arm, full shape (28 Nov)

Training text: the first 10,000 documents of sample-v0 shard `en-fineweb-edu-train-000000` (9,999,399 tokens), decoded with the frozen p1536 tokenizer (sha256 e6b93a93...); decoding and re-encoding gives the same tokens on the 50 documents checked. Held-out: `teams/05-architecture/heldout_v1/data/heldout_v1.jsonl` (sha256 21c6e4b2...). Arm: dry run 2's arm with `run.dtype: fp32` (the T4 has no fast bf16).

```
python teams/05-architecture/harness/train_week2.py --config <dry run 2's arm, fp32> --runtime teams/05-architecture/configs/runtime.yaml --tokenizer-release frozen-p1536 --tokenizer p1536_tokenizer.json --byte-table teams/04-ke2/results/tables/p1536-s0/raw_table_P32.npz --train-data train.jsonl --heldout-data teams/05-architecture/heldout_v1/data/heldout_v1.jsonl --heldout-sources teams/05-architecture/heldout_v1/data/heldout_v1_sources.jsonl --device cuda --seed 1234 --out out/sizing --smoke --smoke-steps 1221 --stop-after 20 --expert-load-every 10 --no-checkpoint
```

```
T3 SIZING RESULT
GPU: Tesla T4
exit code 0, wall 415s, 20 training steps logged
step time (median, steps 4+): 9.22 s
real tokens/s: 692
GPU memory allocated (max logged): 2.14 GiB
start-up + step-0 evaluation (wall minus steps): 224s
expert_load rows: [10, 20]
step-10 busiest share per layer: [44.8, 49.7, 49.5, 47.2, 49.5, 48.0, 49.7, 48.7]
val/bpb at step 0: 2.160660032078147
estimate for one 600-step run without evaluations: 92 min
```

Held-out bits per byte at step 0, 2.1607, is dry run 2's step-0 value (#869), and every layer's busiest expert is at 45% to 50% by step 10, as in dry run 2: the setup reproduces dry run 2's start.

Second run, the same with 8, 4 and 2 rows per pass (copied runtime file, evaluation every 600 steps), 10 steps each:

```
T3 SIZING RESULT 2
GPU: Tesla T4
rows per pass 8: exit 1, out of memory True | torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 768.00 MiB. GPU 0 has a total capacity of 14.56 GiB of which 535.81 MiB is free.
rows per pass 4: exit 1, out of memory True | ... Tried to allocate 512.00 MiB ... 147.81 MiB is free.
rows per pass 2: exit 1, out of memory True | ... Tried to allocate 752.00 MiB ... 691.81 MiB is free.
```

So the T4 runs one row per pass at 9.2 s per step: a full 1,221-step run takes about 3 hours, which is why the arms need the team GPU.

## 2. Laptop CPU, every arm, small shape (28 Nov)

200 documents of the same training text, 10 held-out documents, rows of 64 positions, 2 rows per step, 2 steps, expert load every step:

```
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/router_balance/<arm>.yaml --runtime teams/05-architecture/configs/runtime.yaml --tokenizer-release frozen-p1536 --tokenizer p1536_tokenizer.json --byte-table teams/04-ke2/results/tables/p1536-s0/raw_table_P32.npz --train-data train.jsonl --heldout-data heldout.jsonl --device cpu --seed 1234 --out out/<arm> --smoke --smoke-steps 1221 --stop-after 2 --smoke-seq-len 64 --smoke-batch-size 2 --expert-load-every 1 --no-checkpoint
```

| Arm | Exit | val/bpb, step 0 | Loss, steps 1 and 2 | Layer 0, experts 0 to 5, step 2 | bias_gamma |
|---|---|---:|---|---|---:|
| base (A0) | 0 | 3.1902 | 10.476, 10.614 | 95, 0, 0, 0, 1, 0 | 0.001 |
| gamma_low (A1) | 0 | 3.1902 | 10.476, 10.615 | 95, 0, 0, 0, 1, 0 | 0.0001 |
| gamma_high (A2) | 0 | 3.1902 | 10.476, 10.615 | 90, 0, 0, 0, 1, 0 | 0.01 |
| fast_start (A3) | 0 | 3.1902 | 10.476, 10.615 | 90, 0, 0, 0, 1, 0 | 0.001 (0.01 to step 200) |
| sample_window (A4) | 0 | 3.1902 | 10.438, 10.569 | 22, 7, 2, 4, 14, 19 | 0.001 |
| aux_loss (A5) | 0 | 3.1902 | 10.476, 10.613 | 95, 0, 0, 0, 1, 0 | 0.001 |
| zero_guard (A6) | 0 | 3.1902 | 10.476, 10.614 | 95, 0, 0, 0, 1, 0 | 0.001 |
| guard_row_mask (A7) | 0 | 3.1902 | 10.476, 10.614 | 95, 0, 0, 0, 1, 0 | 0.001 |

Every arm runs; the step-0 score is the same for all (same model and data); A2 and A3 move the bias faster (90 instead of 95 at step 2); A4 spreads the choices at once. Two CPU steps cannot show the rest; that is what the runs are for.

## 3. Tests

`python -m pytest teams/05-architecture/tests -q`: all pass, including `tests/test_router_balance_arms.py` (18 tests: each switch does what it says, is off by default, and Udit's two row-mask checks) and `tests/test_run_report.py` (17, including the expert-load charts, peak memory and idle time). The exact count is in the PR's latest commit message.
