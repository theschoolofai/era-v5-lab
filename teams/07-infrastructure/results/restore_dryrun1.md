# Restore drill in dry run 1

Week 3, core task 5: **do one restore drill in dry run 1: stop, restore, continue. Compare the loss.**

Gate 3 evidence for Team 07: *dry run 1 ends with no lost steps and only COMPLETE checkpoint restarts.*

**Status: plan.** The results tables below are filled in from the logs that TSAI returns for dry run 1.

## 1. What the drill does

Dry run 1 saves a checkpoint every 10 minutes (`INTERVAL_S=600`, [checkpoint_interval.md](../docs/checkpoint_interval.md)).

1. Dry run 1 runs under `ckpt/supervisor.py`, as in the restart test ([jobs/restart_test/](../jobs/restart_test/README.md)).
2. About **25 minutes** in, after the 20-minute checkpoint is COMPLETE and before the 30-minute save starts, the
   trainer is killed with **SIGKILL**: no warning and no last save, like a lost node.
3. The supervisor sees the crash and starts the same command again.
4. `Checkpointer.restore()` loads the newest COMPLETE checkpoint (the 20-minute one) and training continues.
5. The steps between that checkpoint and the kill (about 5 minutes of training) are trained a second time.
   These **redone steps** are the comparison: the first pass and the second pass must give the same loss and the
   same data.

No second, unstopped run is needed. The run compares with itself on the redone steps.

**Why SIGKILL and not a clean stop.** On a clean stop (exit 75) the trainer saves first, so nothing is redone and
the restore is only half tested. A kill tests the harder case: the restore must skip anything not COMPLETE and go
back to the last COMPLETE checkpoint.

**If full-width dry run 1 is not ready on the day**, TSAI runs the same code at small width, and the same checks apply.

## 2. Checks

| # | Check | Pass if | Where it is read |
|---|---|---|---|
| C1 | One restart | The supervisor log shows one crash (exit -9), one restart, then a normal exit | `logs/supervisor.jsonl` |
| C2 | COMPLETE-only restore | The restore loads a checkpoint with `MANIFEST.json` written and listed in `commits.jsonl`. No partial checkpoint is loaded | `logs/events.jsonl` (`restore.*`), `ckpt/commits.jsonl` |
| C3 | Right restart step | The first step after the restart is the checkpoint step + 1 | per-step rows, attempt 1 |
| C4 | No lost steps | Every step from 1 to the last step appears; after the restart there is no gap | per-step rows |
| C5 | Same loss | On every redone step, `loss_ntp` and `loss_mtp` of the second pass equal the first pass (tolerance in section 4) | per-step rows, attempt 0 vs attempt 1 |
| C6 | Same data | On every redone step, the batch data ID (global batch position + sha256 of the batch tokens) is the same | per-step rows |
| C7 | Alarms carry on (if the alarms are on in dry run 1) | The Team 08 alarm state is restored with the checkpoint (`load_state_dict`), so no alarm warm-up gap after the restart | alarm log after the restart |

## 3. Numbers to record

| Number | Value |
|---|---|
| Run ID | *from the dry run 1 package* |
| Width (full or small) | |
| Killed after step | |
| Restored from checkpoint step | |
| Steps redone | |
| Restore time (crash to first step after restart) | |
| Largest loss difference on redone steps | |
| Steps compared | |
| Result (PASS / FAIL) | |

## 4. Open points

1. **Bit-equal or a tolerance.** The restart test was bit-equal on 1 GPU. Across many GPUs, small rounding
   differences can appear. To be agreed with the Team 07 lead before the run: bit-equal, or a fixed tolerance.
2. **Redone steps in the metrics.** The redone steps write their metrics twice. Team 08 checks "no missing steps"
   on the same run, so Team 08 needs to know which row counts (Team 07 proposes: the row after the restart).
3. **Rotation members** who watch dry run 1 (R1/R2) will see this restart in the logs. It is planned, and it is
   logged here.

## 5. Results

*Filled in from the returned logs.*
