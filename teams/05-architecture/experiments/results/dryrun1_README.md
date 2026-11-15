# Dry run 1 loss record: how it is made

**Owner:** Deepjyoti Saha (G5, week-3 task 4). **Written:** 15 Nov 2026, before dry run 1 ran.

This folder holds G5's evidence for Gate 3's "dry run 1 ends with a stable loss curve":

| File | What it is |
|---|---|
| [`dryrun1_loss.md`](dryrun1_loss.md) | The record: what ran, the loss curve, every spike, stops and restarts, and whether the curve is stable. |
| [`dryrun1_spikes.py`](dryrun1_spikes.py) | The script that finds the spikes with both lab rules and prints the record's tables. Standard library only. |
| `dryrun1_README.md` | This file: the method, the decisions behind it, and a test on a week-2 log. |

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
python -I teams/05-architecture/experiments/results/dryrun1_spikes.py --jsonl <path> --rows 20 --out tables.md
```

It reads one `metrics.jsonl` (one JSON object per step: `step`, `loss_ntp`, `loss_mtp`, `gradient_norm`, `lr`,
`tokens_per_second`, and `val/bpb` on evaluation steps), skips the week-2 harness's evaluation-only step 0, and
prints three Markdown tables: the loss curve (about `--rows` rows, the last step and every spike step), every spike
with both rules side by side, and a summary (steps read, gaps, spikes per rule, whether Team 7's guard would have
stopped the run). It changes no file it reads.

## 3. Decisions behind the record

| # | Decision | Chosen | Why |
|---|---|---|---|
| A0 | The Muon rate to cite | `muon_lr` 0.01 | TSAI in the G5 group, 15 Nov; config v1 leaves it unset on purpose |
| A1 | Which spike rule leads | both, one column each | Team 7's guard decides whether the run stops; Team 8's rule is the lab's spike definition |
| A2 | Commit the script | yes | anyone can rerun the record on the same logs |
| A3 | Curve detail | about 20 rows plus every spike step, and a chart | readable, and no spike is left out |
| A4 | Held-out bits per byte | included as a column when the logs have it | a falling held-out score supports "stable" |
| A5 | Late logs or a held run | file what exists by Friday and say what is missing | a record of a held run is still evidence |

## 4. Test on a week-2 log

Run on the T2 reference run of the 10 Nov attention screen,
[`jobs/evidence/2026-11-10-attention-screen/attn-0/metrics.jsonl`](../../jobs/evidence/2026-11-10-attention-screen/attn-0/metrics.jsonl)
(1,221 training steps, the same field names dry run 1 is expected to write):

- **Team 8:** one `spike_score` alarm, at step 1085 on `gradient_norm`: 4.873, 14.3 standard deviations above the
  trailing mean of 0.865. Team 8's own `alarms.py --jsonl` on the same file reports the same single alarm.
- **Team 7:** no spike step; its guard would not have stopped the run (it watches the loss, which did not jump).
- **What it shows:** the two rules can disagree. A gradient spike that the loss absorbs pages a person under
  Team 8's rule but never stops the run under Team 7's. That is why the record keeps both columns.
- No gaps in the steps; held-out bits per byte 1.8993 at step 550 and 1.7770 at step 1221.

## 5. What is still open

- The dry run 1 job request (Shivanshu, Mon 16 Nov): the shards, steps, where the logs come back, and whether
  Team 7's trainer writes the same `metrics.jsonl` fields. The script may need a field-name mapping if not.
- The logs themselves (TSAI and Team 7, Tue 17 to Thu 19 Nov).
- Team 8's alarm output for dry run 1 and Dharshan's shift log, to fill "what happened next" and the restarts.
