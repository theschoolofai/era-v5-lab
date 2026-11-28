# Lab 5: periodic check of the rollout copy on Team 9's mini-benchmark

28 November 2026. Team 10. Laptop CPU. Step 3 of [`../rl/fast_rollouts_v1.md`](../rl/fast_rollouts_v1.md): every N RL updates,
score the rollout copy on Team 9's mini-benchmark (lab PR 929, open on 28 November) and stop if it falls behind.

The wiring is built and tested with made-up score files and made-up questions. **No benchmark item was read, and nothing here
measures model quality.**

## How it works

The evaluation firewall keeps benchmark items out of training jobs: such a job names no benchmark dataset, and a Team 9
job reads the items. So the trainer exports weights and reads scores back.

| Step | Who | What |
|---|---|---|
| 1 | trainer | Every `every` updates and at the last one: `learner.safetensors` (not with `control`), `rollout.safetensors`, `model.json`, then `request.json` with the sha256 of each |
| 2 | Team 9's evaluation job | `minibench_lab.py --weights-safetensors ...` writes one score file per weights file into the same folder |
| 3 | trainer, at its next update | Judges any step whose scores have arrived, writes `verdict.json`, logs it in `metrics.jsonl`, removes the weights |
| after the run | anyone on Team 10 | `rollout_check.py judge --check-dir <dir>` for scores that came late, with the run's own `control` and `min_bpb` (`check.json`) |

```yaml
# train config (model.kind team5 or team5_adapter)
sampler: quant
quant: {scheme: bf16}
rollout_check: {dir: out/checks, every: 10, action: report}   # control: <check folder of the bf16 run>
```

The scoring command for one exported file, for the evaluation job (not run on real items here). Without `control`, run it
for `rollout` and again for `learner`. `<N>` and `<sha256>` come from `request.json`:

```bash
python teams/09-evaluation/harness_lab/minibench_lab.py --profile quick --device cuda \
  --model-config <dir>/step_<N>/model.json --weights-safetensors <dir>/step_<N>/rollout.safetensors \
  --weights-sha256 <sha256> --step <N> --out <dir>/step_<N>/rollout.score.json \
  --tokenizer <tokenizer.json> --tokenizer-sha256 <sha256> --byte-table <raw table .npz> --cache <eval cache>
```

## The rule

- Tasks that decide: MMLU, the MILU languages and the arithmetic sets, as Team 9's card says. Diagnostic tasks are neither
  judged nor copied into Team 10's files.
- Comparison: Team 9's `minibench_compare.py`, paired on items. **Worse** means the 95% interval of a task's gold
  bits-per-byte change lies above zero and the rise is at least `min_bpb` (0.01), or the interval of its accuracy change lies
  below zero.
- Baseline: the bf16 control run's rollout copy at the same step (`control`), or, without it, the learner at the same step.
- A score file counts only if its `model_revision` and `step` match the exported weights, both files of a comparison come
  from the same device, dtype and hardware, and neither is a smoke-profile score.
- `action: report` (default) only logs. `action: stop` ends the run after a worse verdict (exit code 4; it stays stopped
  after a restart).

This reads the plan's "drops by more than 2 standard errors" as the paired 95% interval, and adds the floor.

### Disk, restarts and the control run

- A weights file is removed once its score has gone into a verdict (with `control`: once its score arrives). While
  `max_pending` (3) steps still hold weights, further steps are skipped and the row says `rollout_check_skipped`; the last
  step and a stopping step are always written. At dry run 2's size that bounds a run without a scorer to about 4 to 6 GB.
- A resumed run (`state_dir`) redoes the exports after its restored step. A check folder of any other run is refused.
- Run the control with the same `every`. A step the control run never exported or never had scored stays pending.

### Why the floor

On Team 9's published score files for one set of (untrained) weights, with the same comparison:

| Compared | Largest rise in a deciding task (bpb) | Worse tasks, no floor | Worse tasks, floor 0.01 |
|---|---:|---:|---:|
| quick, CPU fp32 against GPU bf16 | 0.0037 | 4 | 0 |
| quick, native fp32 against GGUF bf16, CPU | 0.0032 | 1 | 0 |

The largest change in either direction was 0.0086. Numerical differences alone produce shifts of this size, and the
paired interval flags them. 0.01 sits just above the largest; it is chosen from these files only. It is not calibrated on trained checkpoints.

```bash
# from the repository root, with lab PR 929's files; --min-bpb 0 gives the third column
python teams/10-post-training/rl-loop/rollout_check.py files \
  teams/09-evaluation/results/minibench_v1/quick-cpu.json teams/09-evaluation/results/minibench_v1/quick-cuda.json
```

## Checked

- The exported files load with Team 9's `load_model_config` and `build_model`, strict `load_state_dict`, and give the same
  probe loss as the model in memory for `copy`, `bf16` and `w4a16_sim` on a tiny Team 5 model. For `w8a8_sim` the loaded
  rollout copy differs, because the file does not carry the activation rounding.
- Through `team5_adapter`, on a 2-layer stand-in run folder (width 256, vocabulary 131,072, the real tokenizer and KE2
  table): 2 steps with the check on, and every exported file loads strictly into a model built the way Team 9's scorer
  builds it (`Artifacts`, then `build_model`), with the tokenizer sha256 in `model.json`. The score files there were made up.
- Team 9's own `minibench_lab.py` (smoke profile, CPU) scores both exported files of that stand-in and writes the fields the
  check reads; their `minibench_compare.py` compares the two files, and the trainer's judging refuses them as smoke scores.
  The item loader was replaced by made-up questions, so no benchmark data was opened; the held-out part used Team 5's
  held-out files.
- A run with the check on logs the same training rewards, losses and k3 as one without it (tiny model, 4 steps).
- `rl-loop/test_rollout_check.py`: 23 tests. One needs `minibench_compare.py` and is skipped until lab PR 929 is merged.

## Cost to the trainer

Model shape of dry run 2 (176.4M parameters, untrained, random byte table), 8 threads, 3 runs each, local NVMe disk
(writes are not forced to disk, so this is the time into the page cache), medians. With `control` only the rollout file is
written, so a check costs less than the table's two files:

| Scheme | Build the copy | Write and hash both files | Files per check |
|---|---:|---:|---:|
| `bf16` | 0.17 s | 1.05 s | 1,069 MB |
| `w4a16_sim` | 0.34 s | 1.42 s | 1,422 MB |

```bash
# from teams/10-post-training/ (12 s wall, peak 2.4 GB resident, torch 2.7.1+cpu; load average 5.3 at the start)
python rl-loop/bench_quant_rollout.py export --threads 8 --out results/lab5_rollout_check_export.json
```

Scoring itself runs elsewhere: Team 9's card gives 6.7 s per model on a laptop GPU and 129 s on a CPU for the quick
profile.

## Limits

- **Team 5's model only.** Team 9's weights path builds Team 5's `LanguageModel`, so Hugging Face policies are refused.
- Verdicts come late by design: a stop takes effect at the first update after the scores arrive.
- The quick profile has 20 items per MILU language and per arithmetic set. Team 9's card says to leave decisions with the
  Tier A guard until the suite is calibrated on real checkpoints, so keep `action: report` until then.
- Ten tasks are tested at every check with no multiple-testing correction. Between two separately trained runs
  (`control`), the interval covers item sampling only, not the difference between two training runs.
- Held-out bits per byte has no interval in the comparison, so it is logged and never decides.
- Not run: benchmark items, a GPU, a Team 5 checkpoint, a real bf16 control run.
