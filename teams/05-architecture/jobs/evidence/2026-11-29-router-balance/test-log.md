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
| gamma_mid (A2b) | 0 | 3.1902 | 10.476, 10.613 | 94, 0, 0, 0, 1, 0 | 0.003 |
| aux_loss_strong (A5b) | 0 | 3.1902 | 10.476, 10.614 | 96, 0, 0, 0, 1, 0 | 0.001 |
| sample_window_bias (A4b) | 0 | 3.1902 | 10.438, 10.567 | 22, 8, 2, 4, 14, 20 | 0.001 |

Every arm runs; the step-0 score is the same for all (same model and data); A2 and A3 move the bias faster (90 instead of 95 at step 2); A4 spreads the choices at once. Two CPU steps cannot show the rest; that is what the runs are for.

## 3. Colab T4 screen of the early-collapse arms (29 Nov)

Before asking for the team GPU, the arms that target the early collapse were screened on a Colab T4: dry run 2's model, recipe, batch and 1,221-step schedule in fp32, expert load every 5 steps, no held-out evaluation after step 0. An arm fails at the first logged step from step 25 with any layer's busiest expert above 31.25% (TSAI's 5 times line) and is stopped there. Commit 25d0e51b, seed 1234, notebook `t3_screen_a2_a4_a5.ipynb` (Drive checkpoints, resumable).

```
T3 SCREEN RESULT
GPU: Tesla T4 | commit 25d0e51b
rule: fail at the first logged step from 25 with any layer busiest > 31.25%; expert load every 5 steps
A2 (gamma_high): FAIL at step 25: busiest 47.3% in layer 0 | attempts 1 | val/bpb step 0 2.160660032078147
A4 (sample_window): FAIL at step 75: busiest 31.4% in layer 5 | attempts 1 | val/bpb step 0 2.160660032078147
A5 (aux_loss): FAIL at step 25: busiest 47.5% in layer 1 | attempts 1 | val/bpb step 0 2.160660032078147
```

Per layer, from the runs' `metrics.jsonl`:

| Arm | Layers above 31.25% | What the per-layer data shows |
|---|---|---|
| A2 (bias step 0.01) | 5 of 8 at step 5; 6 of 8 at step 25 | The busiest expert changes at almost every logged step (layer 0: expert 9, 4, 14, 10, 4): the larger step overshoots and moves the collapse from expert to expert |
| A4 (sampling, 200 steps) | 0 of 8 to step 70; 1 of 8 at step 75 | Every layer at 10% to 17% for 40 steps, no expert at zero; then layer 5 alone climbs (expert 11: 21%, 26%, 28%, 31.4%) while sampling ignores the bias |
| A5 (loss weight 0.001) | 8 of 8 to step 20; 5 of 8 at step 25 | Like dry run 2's start (44% to 50% in every layer); three layers come down by step 25 (23%, 18%, 29%) |

A1 (bias step 0.0001) is not run: at a tenth of dry run 2's step, the bias cannot fix in 1,221 steps what dry run 2 fixed by about step 350. A3 is the same as A2 for its first 200 steps, so it fails with A2. Limits: fp32 on a T4, one seed, 25 to 75 steps. Second screen of stronger settings: A5b (loss weight 0.01), A2b (bias step 0.003), A4b (sampling from the probabilities plus the bias), notebook `t3_screen2_a5b_a2b_a4b.ipynb`.

## 4. Tests

`python -m pytest teams/05-architecture/tests -q`: all pass, including `tests/test_router_balance_arms.py` (18 tests: each switch does what it says, is off by default, and Udit's two row-mask checks) and `tests/test_run_report.py` (17, including the expert-load charts, peak memory and idle time). The exact count is in the PR's latest commit message.
