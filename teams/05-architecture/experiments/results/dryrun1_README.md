# Dry run 1 loss record: how it is made

**Owner:** Deepjyoti Saha (G5, week-3 task 4). **Written:** 15 Nov 2026, before dry run 1 ran.

This folder holds G5's evidence for Gate 3's "dry run 1 ends with a stable loss curve":

| File | What it is |
|---|---|
| [`dryrun1_loss.md`](dryrun1_loss.md) | The record: what ran, the loss curve, every spike, stops and restarts, and whether the curve is stable. |
| [`dryrun1_spikes.py`](dryrun1_spikes.py) | The script that finds the spikes with both lab rules and prints the record's tables. Standard library only. |
| [`dryrun1_loss_sample_attn0.md`](dryrun1_loss_sample_attn0.md) | A **sample**: the same record filled in end to end from a week-2 log (the T2 reference run of 10 Nov), showing exactly what the real record will look like. |
| [`dryrun1_loss_sample_attn0.svg`](dryrun1_loss_sample_attn0.svg) | The sample's loss chart, drawn by the script. |
| `dryrun1_README.md` | This file: the method, the decisions behind it, and how the sample was made. |

## 1. What a spike is in this lab: two rules

The lab has two definitions, owned by two teams, with different consequences. They can disagree (see section 4),
so the record reports both, one column each.

| Rule | Owner and code | Watches | Condition | What it does |
|---|---|---|---|---|
| `spike_score` | Team 8, [`teams/08-monitoring/alarms/alarms.py`](../../../08-monitoring/alarms/alarms.py) | `loss_ntp`, `loss_mtp`, `gradient_norm` | at or above the mean + 7 standard deviations of the last 1,000 clean steps (active after 100 steps); a spike step is not added to the window | pages a person; the run continues |
| `non_finite` | Team 8, same file | any metric | NaN or infinity | stop |
| loss guard | Team 7, [`teams/07-infrastructure/support/simulation/trainer/train.py`](../../../07-infrastructure/support/simulation/trainer/train.py) ("loss-spike guard", ADR 0001 §6) | `loss_ntp` | above 1.5 × the median of the last 100 clean losses (active once 50 are in the window); a spike step is not added; 3 in a row | stops the run: no save, exit 78, the job is held until a person rolls back ([`USER_GUIDE.md`](../../../07-infrastructure/USER_GUIDE.md) §1.5, §5.4) |

The script imports Team 8's `AlarmMonitor` unchanged and copies Team 7's guard with its defaults
(`--spike-ratio 1.5`, `--spike-window 100`, `--spike-steps 3`), so both rules are exactly the ones the lab runs.

## 2. How to run it

From the repository root:

```bash
python -I teams/05-architecture/experiments/results/dryrun1_spikes.py --jsonl <path to metrics.jsonl>
python -I teams/05-architecture/experiments/results/dryrun1_spikes.py --jsonl <path> --rows 20 --out tables.md --svg chart.svg
```

It reads one `metrics.jsonl` (one JSON object per step: `step`, `loss_ntp`, `loss_mtp`, `gradient_norm`, `lr`,
`tokens_per_second`, and `val/bpb` on evaluation steps), skips the week-2 harness's evaluation-only step 0, and
prints three Markdown tables, headed by the log's sha256:

- **the loss curve:** the first step, about `--rows` rows (placed on the held-out evaluation steps when the log has
  them, so every row has a held-out score), the last step and every spike step; `loss_ntp` is one batch and noisy, so
  a 50-step moving average column shows the trend;
- **every spike:** both rules side by side, and what the log shows at the next step (the value and whether the run
  continued); who was paged and what they did is added by hand from the job log;
- **a summary:** steps read and gaps, spikes per rule, whether Team 7's guard would have stopped the run, and the
  numbers the stability paragraph quotes (first, last and lowest loss, the moving average at the start, middle and
  end, held-out bits per byte first to last).

With `--svg` it also draws the chart: `loss_ntp` every step, its 50-step moving average, spike steps marked.
It changes no file it reads, and writes no `__pycache__` into Team 8's folder.

## 3. Decisions behind the record

| # | Decision | Chosen | Why |
|---|---|---|---|
| A0 | The Muon rate to cite | `muon_lr` 0.01 | TSAI in the G5 group, 15 Nov; config v1 leaves it unset on purpose |
| A1 | Which spike rule leads | both, one column each | Team 7's guard decides whether the run stops; Team 8's rule is the lab's spike definition |
| A2 | Commit the script | yes | anyone can rerun the record on the same logs |
| A3 | Curve detail | about 20 rows plus every spike step, and a chart | readable, and no spike is left out |
| A4 | Held-out bits per byte | included as a column when the logs have it | a falling held-out score supports "stable" |
| A5 | Late logs or a held run | file what exists by Friday and say what is missing | a record of a held run is still evidence |

## 4. The sample: the record filled from a week-2 log

[`dryrun1_loss_sample_attn0.md`](dryrun1_loss_sample_attn0.md) is `dryrun1_loss.md` filled in completely from the
T2 reference run of the 10 Nov attention screen,
[`jobs/evidence/2026-11-10-attention-screen/attn-0/`](../../jobs/evidence/2026-11-10-attention-screen/attn-0/)
(1,221 training steps, the same `metrics.jsonl` field names dry run 1 is expected to write). It does two jobs:
it shows reviewers exactly what the real record will look like, and it tests the method before dry run 1's logs
arrive.

How it was made:

| Section | Filled from |
|---|---|
| 1. What ran | by hand, from `command.json`, `manifest.json`, `summary.json`, `environment.json`, the job request and the screen's README |
| 2. The loss curve, 3. Every spike, the summary in 5 | the script, unchanged output: `python -I teams/05-architecture/experiments/results/dryrun1_spikes.py --jsonl teams/05-architecture/jobs/evidence/2026-11-10-attention-screen/attn-0/metrics.jsonl --svg teams/05-architecture/experiments/results/dryrun1_loss_sample_attn0.svg` |
| 4. Stops and restarts | by hand, from `summary.json` (one launch, 1,221 of 1,221 steps, not timed out) |
| 5. The paragraph | by hand, quoting only numbers in the script's summary |
| 6. Sources | by hand |

What the sample found:

- **Team 8:** one `spike_score` alarm, at step 1085 on `gradient_norm`: 4.873, 14.3 standard deviations above the
  trailing mean of 0.865; back to 0.586 at the next step. Team 8's own `alarms.py --jsonl` on the same file reports
  the same single alarm.
- **Team 7:** no spike step; its guard would not have stopped the run (it watches the loss, which did not jump).
- **So the two rules can disagree.** A gradient spike that the loss absorbs pages a person under Team 8's rule but
  never stops the run under Team 7's. That is why the record keeps both columns.
- The loss falls (50-step average 9.17 at step 50, 6.02 at step 1221); held-out bits per byte 2.99 before training,
  1.78 at the end; no gaps, no stops.

For dry run 1 the same steps are repeated on its own logs; the only parts added by hand beyond the sample are
"who was paged and what they did" (from Team 8's alarm output and Dharshan's shift log) and any restarts.

## 5. What is still open

- Where dry run 1's returned logs are kept: proposed `teams/05-architecture/jobs/evidence/<date>-dryrun1/`, laid out
  like the attention screen, with the record linking to them (to agree in G5).
- The dry run 1 job request (Shivanshu, Mon 16 Nov): the shards, steps, where the logs come back, and whether
  Team 7's trainer writes the same `metrics.jsonl` fields. The script may need a field-name mapping if not.
- The logs themselves (TSAI and Team 7, Tue 17 to Thu 19 Nov).
- Team 8's alarm output for dry run 1 and Dharshan's shift log, to fill "what happened next" and the restarts.
