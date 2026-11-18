# G7 week 3 rotation: dry run 1, steps 916-1,221 (smitasasindran)

Work order tasks R1 (review dry run 1 from the returned logs) and R2 (log each failure and each restart).
There was no live shift: dry run 1 finished on 16 Nov (#475), so R1 is an offline review of the logs for the step
range, **steps 916 to 1,221**.

**Status (18 Nov):** R2 done. **The per-step logs of dry run 1 were not
available**, so R1 is not verified from per-step data. See "Logs in the repo".

## The run

| Item | Value | Source |
|---|---|---|
| Job request | `teams/05-architecture/jobs/2026-11-15-dryrun1.md` | #475, merged 16 Nov |
| Run ID / output | `dryrun1-1234`, `./out/dryrun1-1234/` | job request |
| Trainer | `teams/05-architecture/harness/train_week2.py`, Team 5's trainer | #475 |
| Arm and size | exp2_muon at T2, muon_lr 0.01, seed 1234 | TSAI result on #475 |
| Tokenizer | p1536, sha256 `e6b93a93...a64b` (the job request names frozen C3, `15468e66...`) | TSAI result on #475 |
| Steps / status | 1,221 of 1,221, COMPLETED | TSAI result on #475 |
| Final train cross-entropy / gradient norm | 4.8906 / 0.7037 (step 1,221, inside my range) | TSAI result on #475 |
| Held-out val/bpb | 1.5159 (English 1.9844, code 1.8901, Indic mean 1.3289, three-group 1.7345); same arm with tokenizer v0: 1.6443 | TSAI result on #475 |
| NaN / inf in loss record | none | TSAI result on #475 |
| Checkpoint | one `checkpoint.pt` at the last step (about 2.2 GB), kept by TSAI | TSAI result on #475 |

## R1: steps 916-1,221

### Logs in the repo

`teams/05-architecture/jobs/evidence/2026-11-15-dryrun1/` on main (checked 18 Nov)
holds the **3-step smoke run**, not dry run 1: `summary.json` has `"status": "SMOKE"`, `"steps": 3`;
`metrics.jsonl` has 4 rows (steps 0 to 3); `smoke.md` says it is "a test log" run on a CPU laptop. None of it covers
steps 916-1,221.

### What can be said without the logs

| Check | Finding |
|---|---|
| Step continuity (916-1,221 each once) | **Not verified.** TSAI reports 1,221 of 1,221 steps completed, which implies the range was run, but I could not check each step. |
| Finite loss and gradient norm | **Not verified per step.** TSAI reports no NaN or inf in the loss record. |
| Loss spikes | **Not verified.** Only the end point is known: final cross-entropy 4.8906 at step 1,221. |
| Gradient norm | **Not verified.** Final gradient norm 0.7037 at step 1,221. |
| Throughput | **Not verified.** No step times or tokens per second were returned. |
| Held-out evals in range | The final val/bpb 1.5159 is reported; the other eval steps are unknown. |
| Team 8 alarms offline | **Not run** on the real data (no data). |

I make no PASS claim for steps 916-1,221 from TSAI's summary alone.

### Plan once the logs land

When the full-run `metrics.jsonl`, `losses.txt` and `summary.json` are published, for steps 916-1,221:

- check that every step appears exactly once and that `summary.json` says COMPLETED with 1,221 steps;
- check that `train/ce_loss` and `gradient_norm` are finite and look for loss and gradient-norm spikes;
- check `perf/step_ms` and `tokens_per_second` for slow steps and drops;
- list the held-out evals (`val/bpb`) in the range;
- compare `losses.txt` (hex floats, one line per step) with `train/ce_loss` in `metrics.jsonl`;
- run Team 8's alarms offline, over the whole file so the 1,000-step trailing windows are warm, and keep the alarms
  in the range:

```bash
python -I teams/08-monitoring/alarms/alarms.py --jsonl <path>/metrics.jsonl
```

## R2: failures and restarts

### Dry run 1

| # | Time / step | Event | Cause | Action | Restored from | Steps lost |
|---|---|---|---|---|---|---|
| none | | | | | | |

- Failures: **0**. Restarts: **0**. 1,221 of 1,221 steps, COMPLETED, no NaN or inf (TSAI result on #475).
- Dry run 1 did not run under `ckpt/supervisor.py` and did not use the Checkpointer. It saved one checkpoint at
  the last step. So it gives **no evidence** for "only COMPLETE checkpoint restarts".

### Restore drill on the final checkpoint (#491; results in #573), run by TSAI on 17 Nov

Numbers are from TSAI's result note as written in `restore_dryrun1.md`, section 5. The job outputs were not added
to the repository.

| Check | Job A: restore final checkpoint | Job B: stop at 610, restore, continue |
|---|---|---|
| Exit code, no identity error (C1) | 0 | resume run 0 |
| `steps` / `status` (C2) | 1,221 / COMPLETED | stop run 610 / INCOMPLETE_NOT_A_RESULT; resume run 1,221 / COMPLETED |
| `final_model_sha256` equals dry run 1 (C3) | yes | yes |
| `losses.txt` equals dry run 1, bit for bit (C4) | yes, 1,221 of 1,221 lines | yes, 1,221 of 1,221 lines |
| Every step present (C5) | n/a | yes, steps 1 to 1,221 |
| Stop run equals dry run 1 up to step 610 (C6) | n/a | yes, no run-to-run noise |
| Job start to exit | about 6 min 8 s | about 30 min 39 s (includes 611 training steps) |
| Result | PASS | PASS |

What it shows: the saved checkpoint loads and gives back the same model, and a run stopped at step 610 and
restored finishes bit-for-bit like the run that was never stopped. What it does not show: both jobs restored from
a checkpoint saved after a clean stop, not after a kill, and `train_week2.py` writes `checkpoint.pt` directly with
no COMPLETE marker. The COMPLETE-only restart after a kill is shown by the Team 07 restart test
([restart_cpu.txt](restart_cpu.txt), [restart_node.txt](restart_node.txt)). TSAI agrees that the week-5 main run
should save through the `Checkpointer`.

## Open items

- [ ] Get the full-run `metrics.jsonl`, `losses.txt`, `summary.json` from TSAI (asked on #475 on 17 Nov).
- [ ] Review steps 916-1,221 from the real logs and replace the "What can be said" table with the findings.
- [ ] Run `alarms.py` offline and record the alarms in my range.
- [x] R2: no failures, no restarts; restore drill (#491, #573) recorded.

## References

- Dry run 1: #475. Restore drill: #491 (plan and job requests), #573 (results).
- Team 8 alarms: `teams/08-monitoring/alarms/alarms.py`.
