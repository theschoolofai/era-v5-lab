# Restart cost, commit spacing and job time caps (Lab 5, design task 5, restart side)

Owner: Pradeep (Team 07). Due Wed 2 Dec 2026, 7:00 AM IST. The other half of design task 5 (cost per million
tokens, storage streaming, CPU capacity) is Smita's; this file gives that cost table its restart number.

Inputs, all measured unless marked:

| Input | Value | Source |
|---|---|---|
| Commit log and per-step metrics | dry run 2, `dryrun2-1234`, 1,221 steps, `INTERVAL_S=600`, `eval_every_steps=50` | TSAI, PR #869 (`teams/05-architecture/results/dryrun2-1234/`) |
| Checkpoint size and save | 2,081 MiB; stall 0.09 s, whole save 1.43 s (1 A100) | Team 6 #688, [checkpoint_interval.md](checkpoint_interval.md) §1 |
| Restore read and load | 2.5 to 2.8 s per GB; slow hosted CPU 72 s per GB | [checkpoint_interval.md](checkpoint_interval.md) §1 |
| MTTR (fault to first productive step) | 80.0 s (simulation, tiny model, no download) | `support/simulation/results/metrics.json`, Q-20 |
| Node | 1 node, 8 GPUs (planning assumption in the Lab 5 brief) | brief |
| Price | an input: cost = node-hours x your price per node-hour (TSAI review on #150: no price in the repo) | |

## 1. Why commits came 660 to 697 s apart, not 600 s

```
python support/cost/commit_spacing.py --commits <dryrun2-1234>/commits.jsonl --metrics <dryrun2-1234>/metrics.jsonl
```

| From step | To step | Wall s | Over interval s | In steps s | Other s | Evals | Eval at commit step |
|---|---|---|---|---|---|---|---|
| 0 | 195 (interval) | 664.6 | 64.6 | 494.1 | 170.6 | 3 | no |
| 195 | 350 (interval) | 693.2 | 93.2 | 473.9 | 219.3 | 4 | yes |
| 350 | 513 (interval) | 660.5 | 60.5 | 490.4 | 170.1 | 3 | no |
| 513 | 672 (interval) | 659.5 | 59.5 | 488.4 | 171.1 | 3 | no |
| 672 | 836 (interval) | 663.8 | 63.8 | 491.5 | 172.3 | 3 | no |
| 836 | 993 (interval) | 660.2 | 60.2 | 487.4 | 172.8 | 3 | no |
| 993 | 1150 (interval) | 697.3 | 97.3 | 483.0 | 214.3 | 4 | yes |
| 1150 | 1221 (final) | 339.5 | -260.5 | 229.5 | 110.0 | 2 | yes |

Mean spacing of the interval commits: **671.3 s** (+71.3 s). Fit over them: one evaluation **45.4 s**, the rest
per interval 35.0 s.

What the code does (`teams/05-architecture/harness/train_week2.py:843-846`):

1. The deadline is checked only after a step ends, and after that step's evaluation. The two long gaps (693 s,
   697 s) are exactly the two whose commit step is an eval step (350, 1150): the deadline passed during the step,
   then the 45 s evaluation ran, then the save.
2. The next deadline is set after `save_committed()` returns (`checkpoint_clock() + interval`), so the time in
   the save is added to every interval, not taken from it.
3. The commit time in `commits.jsonl` is when the commit lands, after the background upload, so each gap also
   holds the difference of two commit latencies.

Not explained: about 60 s on every gap without an eval at the commit step. Team 6 measured the save at 1.43 s
and a step is at most 6.1 s, so neither the stall nor the step boundary accounts for it. The dry run did not set
`V5_EVENTS_DIR`, and `common/events.py:35` drops events when it is unset, so `checkpoint.committed` (`stall_s`,
`commit_latency_s`, `backpressure_s`) was never written. **Finding:** the run command must set `V5_EVENTS_DIR`
(`slurm/mainrun.sbatch` does, the dry-run command did not). Then the split is one `jq` away, and Team 8's dashboard
gets checkpoint duration (design task 3).

Decision: no code change. Making the cadence fixed (`deadline += interval`) would save at most the save time per
interval and still overshoot by an evaluation; the cost model below uses the measured 671 s instead of 600 s.

Idle time (brief rule "report idle time"): the evaluations take 3 x 45.4 = 136 s of every 671 s interval, **20%
of the wall clock**, with every GPU waiting on one evaluation pass. That is the largest waste in the dry run, larger
than any checkpoint cost here. For Team 5 and Team 9: evaluate less often, or on fewer bytes, in the main run.

## 2. What a restart costs

An unplanned restart (node loss, crash, SIGKILL) loses the work since the last commit, on average half an interval,
then the time to restart and to restore. A planned stop (time cap, spot notice, operator) saves first, so it loses
no steps.

```
unplanned  = nodes x (interval / 2 + MTTR + restore) / 3600            node-hours
planned    = nodes x (finish step + eval if due + save + MTTR + restore) / 3600
```

```
python -c "
I, M, R, Rs = 671.3, 80.0, 2081*2**20/1e9*2.8, 2081*2**20/1e9*72
for name, s in [('unplanned, measured spacing 671 s', I/2+M+R), ('unplanned, slow restore', I/2+M+Rs),
                ('unplanned, if commits were 600 s apart', 600/2+M+R),
                ('planned (step 6.1 s + save 1.43 s)', 6.1+1.43+M+R), ('planned, eval due (+45.4 s)', 6.1+45.4+1.43+M+R)]:
    print(f'{name:40s} {s:7.1f} s  {s/3600:.3f} node-h')"
```

| Restart | Seconds | Node-hours (1 node) | Steps done again |
|---|---|---|---|
| Unplanned, measured spacing 671 s | 421.8 | **0.117** | about 80 (half of 160 steps per interval) |
| Unplanned, slow restore (72 s per GB) | 572.8 | 0.159 | about 80 |
| Unplanned, if commits were 600 s apart | 386.1 | 0.107 | about 73 |
| Planned (time cap, spot notice), save 1.43 s | 93.6 | **0.026** | 0 |
| Planned, an evaluation was due | 139.0 | 0.039 | 0 |

Cost = node-hours x price per node-hour. Per day, unplanned: failures per day x 0.117. With the published priors
(9,921 to 50,677 GPU-hours per interruption, `MTBF_PRIORS` in `cost_model.py`) one 8-GPU node fails every 1,240 to
6,335 hours, so hardware restarts cost 0.0004 to 0.0023 node-hours per day. Spot reclaims and time caps decide
the real number. Each costs 0.026 node-hours if the save finishes within the notice. Section 3 says how to
make sure it does.

What these numbers do not hold: the requeue wait in Slurm (time on no node is not node-hours, but it is calendar
time), and the restore of a larger model. Restore grows with checkpoint size (2.8 s per GB fast path); the interval
and MTTR do not.

## 3. Running across job time caps without losing steps

The chain exists and was tested in parts:

| Link | Where | Evidence |
|---|---|---|
| Slurm warns the batch shell before the time limit | `#SBATCH --signal=B:USR1@<lead>` | Slurm simulation drill `time_limit_self_requeue` PASS, 1 Nov: saved 770, restored 770, lost 0 ([evidence](../support/simulation/results/evidence/time_limit.log)) |
| The wrapper passes SIGUSR1 to the trainers | `queue/job_queue.py:191-200` | same drill |
| The trainer finishes the step, saves (`reason=signal`), waits for the commit, exits 75 | `train_week2.py:664-676, 853-863` | Team 05 `tests/test_week2_team7_checkpoints.py`: signal after batch 1, exit 75, commit at step 1 with reason `signal`; 5 passed on 28 Nov |
| Exit 75 requeues the job | `slurm/slurm.conf` `RequeueExit=75` | same drill |
| The new job restores latest.json and continues at the next step, bit-equal | `ckpt.py` restore | `jobs/restart_test`, `jobs/restore_test` (PR #899) |

Our own cluster sets no cap on the main run: the `gpu` partition has `MaxTime=INFINITE` and the `mainrun` QOS no
`MaxWall` (`slurm/nodes.cloud.conf`, `slurm/setup_accounts.sh`). A cap comes from a site or a provider (a `--time`
on the job). Then:

**Gap:** `slurm/mainrun.sbatch` has no `--signal` line, on main and in #820. Without it, the time limit
sends SIGTERM and then, after `KillWait=30` (`slurm.conf:62`), SIGKILL. The trainer also saves on SIGTERM, but in
30 s it must finish the step (up to 6.1 s), an evaluation if one is due (45.4 s), the save, and the commit. A save
that does not commit in time is lost, and **the job ends TIMEOUT, which Slurm does not requeue: the run stops until
a person restarts it.**

**Drill, 28 Nov (Docker Slurm, `mainrun.sbatch` from main, 1 node x 2 ranks, `--time=00:07:00`, upload slowed to
20 s per file with the `upload_delay_s` hook so a save takes about a minute):**

```
python3 support/simulation/run_sim.py --only mainrun_time_cap_signal mainrun_time_cap_nosignal
```

| Arm | Signal save committed | Lost steps | Job after the cap | Result |
|---|---|---|---|---|
| `--signal=B:USR1@120` | yes, step 4044 | **0** | requeued (Restarts 1), restored step 4044 | PASS |
| no `--signal` (as on main and in #820) | **no**: SIGKILL 30 s after SIGTERM | **2,891** (stopped at 6,585, latest.json at 3,694) | **TIMEOUT**, Restarts 0, not requeued | PASS (the failure as predicted) |

Evidence: `support/simulation/results/evidence/mainrun_time_cap_signal.log`, `mainrun_time_cap_nosignal.log`
(every command, exit code and output). 2 of 2 selected drills passed in 943 s.

**Found by the first run of this drill:** with the slow upload and a 30 s interval, every save waited on the previous
upload (`checkpoint.backpressure`), no step finished for `WATCHDOG_S` (20 s), and the step watchdog restarted a
healthy run three times, each time from step 447 (about 900 steps lost per restart). `train_week2.py` arms its
watchdog after each step (`:802`), and the evaluation and the save then run while it is armed (`:828-846`).
**Rule for the main run:** `WATCHDOG_S` > evaluation + save stall + backpressure (60 s > 45.4 + 1.4 today; the
main-run default 600 s is fine). The interval must stay longer than the upload, which `checkpoint_interval.md`
already requires (1.2 x save pipeline).

**Fix (for #820, Max):** add

```
#SBATCH --signal=B:USR1@300
```

Lead = step 6.1 s + evaluation 45.4 s + save 1.43 s + commit (not measured, see section 1) + Slurm's signal timing
(up to 60 s early). 300 s covers that with room for a commit that takes minutes; the drill above passed with
120 s and a 60 s save. A warning 300 s early costs at
most 300 s of node time per cap, which is less than one unplanned restart. Raising `KillWait` instead would not
help with a save that is still running when the step does not end. Keep `KillWait=30`.

**After #820 merges:** rerun the two drills above on the new `mainrun.sbatch`; the signal arm must still give 0 lost
steps with the `--signal` line in the script instead of on the `sbatch` command line.
