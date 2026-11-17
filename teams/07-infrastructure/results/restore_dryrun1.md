# Restore drill on dry run 1

Week 3, core task 5: **do one restore drill in dry run 1: stop, restore, continue. Compare the loss.**

Gate 3 evidence for Team 07: *dry run 1 ends with no lost steps and only COMPLETE checkpoint restarts.*

**Status: plan and job requests.** The results tables in section 5 are filled in from the logs that TSAI returns.

## 1. What dry run 1 was

TSAI ran dry run 1 on 16 Nov (#475): Team 05's `train_week2.py`, `exp2_muon.yaml` at T2 size, seed 1234,
tokenizer p1536, 1,221 of 1,221 steps, status COMPLETED, no NaN or inf in the loss record.

- It ran as **one process**, **without** the Team 07 supervisor (`ckpt/supervisor.py`) and **without** the
  `Checkpointer` (`ckpt/ckpt.py`).
- It had **zero restarts**.
- It saved **one checkpoint**, `checkpoint.pt` (about 2.2 GB), at the last step. TSAI keeps it.

So the restore drill cannot be a stop in the middle of dry run 1 itself. It is done on the saved checkpoint, as TSAI
asked in the Team 07 group on 16 Nov.

## 2. The drill: two jobs

`train_week2.py` already has the two options needed: `--stop-after N` (stop after step N and save `checkpoint.pt`)
and `--resume PATH` (load a checkpoint and carry on). On resume it refuses a checkpoint whose identity hash (code,
config, data, device, software) differs from the current run, so a passing resume also proves that nothing changed.

| Job | What it does | Request |
|---|---|---|
| **A. Restore** (required) | Load dry run 1's final checkpoint (step 1,221) into a fresh output folder with the same command. | [2026-11-17-restore-final-ckpt.md](../jobs/2026-11-17-restore-final-ckpt.md) |
| **B. Stop, restore, continue** (optional, if TSAI agrees) | Run the same command to step 610 and stop. Resume from that checkpoint to step 1,221. Compare with dry run 1. | [2026-11-17-stop-resume.md](../jobs/2026-11-17-stop-resume.md) |

**A** proves the saved checkpoint loads and gives back the same model. It does not train any step again, because
training cannot go past the last step without changing the step count, and that fails the identity check.

**B** is the full "stop, restore, continue" of the work order. It costs about one more dry run of compute, so TSAI
decides whether to run it.

## 3. Checks

| # | Check | Job | Pass if | Read from |
|---|---|---|---|---|
| C1 | The checkpoint loads | A, B | Exit code 0, no identity error | job log |
| C2 | Right step | A, B | `summary.json` `steps` = 1,221 and `status` = COMPLETED | `summary.json` |
| C3 | Same model | A, B | `final_model_sha256` equals dry run 1's | `summary.json` vs #475 |
| C4 | Same loss | A, B | `losses.txt` equals dry run 1's, line for line (bit for bit, hex floats) | `losses.txt` vs #475 |
| C5 | No lost steps | B | `losses.txt` has 1,221 lines; `metrics.jsonl` has every step from 0 to 1,221 once | `losses.txt`, `metrics.jsonl` |
| C6 | Stop run matches before the stop | B | Lines 1 to 610 of the stop run's `losses.txt` equal lines 1 to 610 of dry run 1's | stop run `losses.txt` |

**How to read B if C4 fails.** C6 tells the two causes apart. If C6 also fails, two runs of the same command already
differ on the GPU before any restore, so the difference is run-to-run noise, not the restore. If C6 passes and C4
fails, the restore changed something. Either way the largest difference is recorded.

## 4. What this gives Gate 3

| Gate 3 line | Evidence |
|---|---|
| No lost steps | Dry run 1: 1,221 of 1,221 steps, COMPLETED (#475). Job B, check C5, if run. |
| Only COMPLETE checkpoint restarts | Dry run 1 had no restart, so it shows nothing here. The COMPLETE-only restart evidence stays the Team 07 restart test: [restart_cpu.txt](restart_cpu.txt) and [restart_node.txt](restart_node.txt) (SIGKILL after step 140, restart from the COMPLETE checkpoint at step 125, 200/200 steps bit-equal). |

**Risk for the main run (week 5).** `train_week2.py` writes `checkpoint.pt` once, at the end, straight to its final
name with `torch.save`. It has no COMPLETE marker and no write-then-rename, so a kill during that save leaves a
broken file under the real name. The Team 07 `Checkpointer` exists for this. Before the main run, the trainer should
save through the `Checkpointer` and run under the supervisor.

A related finding from Team 08 (#512): metrics are written to disk every 10 steps, so after a kill and restore the
rows between the last flush and a newer checkpoint are never written again. Flushing `metrics.jsonl` at each
checkpoint save fixes it.

## 5. Results

*Filled in from the returned logs.*

| Number | Job A | Job B |
|---|---|---|
| Exit code | | |
| `steps` / `status` | | |
| `final_model_sha256` equal to dry run 1 (C3) | | |
| `losses.txt` equal to dry run 1 (C4) | | |
| Largest loss difference, if not equal | | |
| Every step present (C5) | n/a | |
| Stop run equal to dry run 1 up to step 610 (C6) | n/a | |
| Restore time (job start to first step, or to exit for A) | | |
| Result (PASS / FAIL) | | |
