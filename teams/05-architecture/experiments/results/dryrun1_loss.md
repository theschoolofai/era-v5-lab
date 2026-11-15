# Dry run 1: the loss record

**Owner:** Deepjyoti Saha (G5, week-3 task 4). **Status:** DRAFT. "What ran" is filled from the job request
([#475](https://github.com/theschoolofai/era-v5-lab/pull/475), not yet run); the rest is filled from the dry run 1
logs when TSAI returns them. **Gate 3 evidence:** "dry run 1 ends with a stable loss curve" (Fri 20 Nov, 23:59 IST).

How the numbers are made, the two spike rules and how to rerun everything: [`dryrun1_README.md`](dryrun1_README.md).
What this record will look like once filled: 🧪 [`dryrun1_loss_sample_attn0.md`](dryrun1_loss_sample_attn0.md), a
SAMPLE for illustration only (a week-2 log with injected spikes and stops; not dry run 1).

## 1. What ran

| Item | Value | Source |
|---|---|---|
| Job request | [`jobs/2026-11-15-dryrun1.md`](../../jobs/2026-11-15-dryrun1.md), one job, one command | [#475](https://github.com/theschoolofai/era-v5-lab/pull/475) (Shivanshu, 15 Nov; TSAI reviews and runs it) |
| Trainer | `teams/05-architecture/harness/train_week2.py` at `71bc0fb`, with TSAI's Gate 2 speed fixes and the C3 scoring patch of [#474](https://github.com/theschoolofai/era-v5-lab/pull/474); run directly, one process | job request, "Script" and "Source and staging" |
| Config | `configs/arms/exp2_muon.yaml`, which carries the Gate 2 choices of `config_v1.yaml` ([#447](https://github.com/theschoolofai/era-v5-lab/pull/447)) at T2 size; the trainer cannot load `config_v1.yaml` itself | job request, "Where each setting comes from" |
| Optimizer | Muon for the block matrices with **`muon_lr` 0.01**; `lr` 0.001 for the other parameters; gradient clip 1.0 | the instructor, 05 Architecture group (dry run 1 uses `muon_lr` 0.01); `config_v1.yaml` |
| Model size | T2: 8 layers, width 512, 8 heads (2 key-value), 16 routed + 1 shared expert, top-2, eager attention, dense untied head, no second head (`mtp: false`) | `exp2_muon.yaml` / `t2.yaml` |
| Steps, batch, context, seed | 1,221 steps, batch 8, context 2,048, seed 1234; 90-minute cap; bf16 on 1 GPU | job request |
| Tokenizer | the frozen C3 tokenizer, sha256 `15468e66…`, with its raw P32 byte table (content sha256 `fc5e5f8f…`) | job request; `teams/03-tokenizer/release/` |
| Training data | the TSAI-staged text bundle of the week-2 jobs (`train.jsonl`, sha256 `267c33bf…`); not shards (shards are for dry run 2) | the instructor, as quoted in the job request |
| Held-out scoring | the original `heldout_v1` (sha256 `21c6e4b2…`, 1,059 documents) and its original byte count, 3,775,551; at step 0, every 50 steps and the last step | job request, "How the run is scored and reported" |
| Spike rules inside the job | **none.** `train_week2.py` has no loss guard and no Team 8 monitor; it stops on a NaN or infinite loss, gradient or parameter with an error, before that step's row is written. This record applies both lab rules to the returned `metrics.jsonl` and reports what each **would** have done. | `train_week2.py` |
| Checkpoints | one, at the end; none during the run, so a stopped run starts again from step 0 (open item 3 of the request) | job request |
| Hardware, run by, start and end | _to fill_ | returned `manifest.json`, `summary.json` |
| Logs used | _to fill: `metrics.jsonl`, `losses.txt`, `summary.json`, `manifest.json`, with sha256_ | returned logs |

## 2. The loss curve

_To fill: the curve table printed by `dryrun1_spikes.py`, and the chart it draws with `--svg`._

## 3. Every spike

_To fill: the close-up chart (`--spike-svg`) and the spike table printed by `dryrun1_spikes.py`, both rules side by
side, then the details of each spike: which rule would have caught it and why, and what the log shows next._

## 4. Stops and restarts

_To fill: the attempts table printed by `dryrun1_spikes.py`, then, from the returned files and the run's console
output:_

| Time | Step | How it ended | Cause | What happened | Source |
|---|---:|---|---|---|---|
| _to fill_ | | | | | `summary.json` (`status`: COMPLETED or INCOMPLETE_NOT_A_RESULT), the console output |

A NaN or infinity stops `train_week2.py` with an error and voids the run (job request); the step is then missing
from `metrics.jsonl` and shows only in the console output. Fewer than 1,221 steps is INCOMPLETE_NOT_A_RESULT.

## 5. Is the curve stable?

_To fill: four to six sentences. Does the loss fall; how many spikes by each rule; did each recover, and how
fast; any stop and why; anything unexplained. This reports what the logs show; the Gate 3 judgement is TSAI's._

## 6. Sources

- The job request: [#475](https://github.com/theschoolofai/era-v5-lab/pull/475), [`jobs/2026-11-15-dryrun1.md`](../../jobs/2026-11-15-dryrun1.md), and its smoke log [`jobs/evidence/2026-11-15-dryrun1/smoke.md`](../../jobs/evidence/2026-11-15-dryrun1/smoke.md).
- _to fill: the returned logs, the console output._
