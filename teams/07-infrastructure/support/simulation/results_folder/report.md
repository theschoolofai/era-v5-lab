# Simulation metrics report: run `v5main`

Cluster price used: 2 × gpu-node-8 = **$227.86/h** (assumed price, see metrics/prices.yaml). Interval: 8 s (one interval = $0.51).

> In the simulation a fault is injected about once a minute, while a real run sees one every few hours or days. So goodput and cost-waste numbers here are far worse than production will be. The simulation proves the *mechanism* and measures each step's *duration*; `support/cost/cost_model.py --measured` projects those durations onto real failure rates.

Metrics in catalog: 74; computed from simulation events: 40.

## Alerts

| Severity | ID | Metric | Value | Caused by the test? | Action |
|---|---|---|---|---|---|
| HIGH | CK-07 | NaN guard trips | 1 count | yes | Rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | Q-02 | Main run held (exit 78 / crash loop) | 3 count | yes | Read the job.held cause; rollback or fix, then release. |
| HIGH | Q-05 | Main-run interruptions per day | 927.1357 count/day | fault rate | Group incidents by node and cause_class; drain repeat offenders. |
| HIGH | Q-19 | Goodput of the main run | 11.3053 % | fault rate | See the largest non-productive bucket in the report. |
| HIGH | H-01 | Fatal Xid on a node | 1 count | no | Automatic drain + save; open a hardware ticket; replace the instance. |
| HIGH | H-21 | Spot interruption notice | 1 count | yes | Automatic: drain + save + requeue. Page only if no commit within 90 s. |
| HIGH | H-24 | Loss-spike guard trips | 1 count | yes | Look at the batches before the spike; rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | C-02 | Cost per productive GPU-hour vs list price | 8.8454 ratio | fault rate | Fix the largest waste bucket (C-03). |
| HIGH | C-03 | Wasted share of main-run spend | 88.6947 % | fault rate | The report lists each bucket in USD. |
| HIGH | C-04 | Cost of one incident | 21.4587 x interval cost | yes | Large values: missing emergency save, slow restore, or no spare. |
| MEDIUM | CK-03 | Consecutive failed saves | 1 count | no | Read the failure cause (nvme_full, IntegrityError, upload timeout) and fix it now. |
| MEDIUM | Q-04 | Crash-loop holds | 1 count | yes | Read the logs of the 3 crashes; for the main run this is also Q-02 (high). |
| MEDIUM | Q-09 | Drained nodes | 2 count | yes | Re-test with --full; repair, replace or stop the instance. |
| MEDIUM | Q-10 | Node replacement time (drain to spare running the job) | 422.224 s | yes | Keep the hot spare up; check preemption grace time on the spare's team job. |
| MEDIUM | Q-21 | Human interventions | 4 count/week | yes | Automate the step that needed a person. |
| MEDIUM | H-14 | Step watchdog fired (hang) | 1.8396 count/h | fault rate | Read the stack dump in the job log and the NCCL flight-recorder trace; drain the rank that stopped. |
| MEDIUM | H-15 | Straggler ratio (rank step time / median) | 1.1546 ratio | no | Medium for 3 windows: drain at the next checkpoint. |
| LOW | CK-14 | Work lost per incident | 0.9337 x interval | no | Check that SIGUSR1/SIGTERM reached the trainer and the emergency save committed. |
| LOW | CK-19 | Resharded resumes | 2 count | yes | Note it in the run log and the paper's failure table. |
| LOW | Q-16 | Jobs rejected for no valid account | 1 count | yes | Check the submit system's account mapping. |

## Where the main run's wall-clock time (and money) went

| Bucket | Seconds | Share | USD |
|---|---|---|---|
| checkpoint_stall | 1.26 | 0.1% | $0.08 |
| lost_work | 33.08 | 1.9% | $2.09 |
| detection | 307.62 | 18.1% | $19.47 |
| reschedule | 1050.86 | 61.7% | $66.51 |
| restore | 117.42 | 6.9% | $7.43 |
| productive | 192.5 | 11.3% | $12.18 |
| wall_clock | 1702.74 | 100.0% | $107.77 |

## Recovery time by fault type (MTTR, seconds)

| Fault | n | p50 | p95 | max |
|---|---|---|---|---|
| hang | 1 | 87.35 | 87.35 | 87.35 |
| health_fail | 1 | 118.03 | 118.03 | 118.03 |
| kill | 3 | 81.15 | 88.64 | 88.64 |
| kill_during_restore | 1 | 170.78 | 170.78 | 170.78 |
| kill_during_save | 1 | 81.26 | 81.26 | 81.26 |
| node_loss | 1 | 118.07 | 118.07 | 118.07 |
| resume_after_fence | 1 | 4.21 | 4.21 | 4.21 |
| rollback | 2 | 3.67 | 3.92 | 3.92 |
| sigusr1 | 3 | 87.01 | 89.14 | 89.14 |
| spot_notice | 1 | 88.18 | 88.18 | 88.18 |
| two_nodes_down | 1 | 118.85 | 118.85 | 118.85 |

## Incidents

| Fault | Cause class | Detect s | Reschedule s | Restore s | MTTR s | Lost steps | Restored step | Human |
|---|---|---|---|---|---|---|---|---|
| nvlink_down | gpu | None | None | None | None | None | None | no |
| time_limit | planned | 153.62 | 0.0 | None | None | None | None | no |
| kill | software | 0.12 | 87.06 | 1.46 | 88.64 | 98 | 2732 | no |
| kill | software | 0.16 | 77.89 | 1.4 | 79.45 | 30 | 2860 | no |
| kill | software | 0.11 | 78.94 | 2.1 | 81.15 | 28 | 2992 | no |
| sigusr1 | preemption | 0.32 | 85.42 | 1.26 | 87.01 | 0 | 3022 | no |
| sigusr1 | preemption | 0.33 | 86.57 | 2.25 | 89.14 | 0 | 3066 | no |
| sigusr1 | preemption | 0.35 | 85.28 | 1.3 | 86.94 | 0 | 3092 | no |
| kill_during_save | software | 7.66 | 71.6 | 2.0 | 81.26 | 27 | 3223 | no |
| kill_during_restore | software | 0.11 | 78.07 | 92.6 | 170.78 | 15 | 3355 | no |
| spot_notice | host | 2.99 | 83.91 | 1.29 | 88.18 | 0 | 3413 | no |
| health_fail | gpu | 26.61 | 90.18 | 1.24 | 118.03 | 0 | 3872 | no |
| two_nodes_down | gpu | 26.61 | 90.17 | 2.07 | 118.85 | 0 | 4339 | no |
| hang | software | 21.27 | 64.79 | 1.29 | 87.35 | 31 | 4339 | no |
| node_loss | host | 45.13 | 70.98 | 1.96 | 118.07 | 41 | 4339 | no |
| split_brain | software | 1.43 | None | None | None | None | None | no |
| resume_after_fence | operator | 2.37 | 0.0 | 1.85 | 4.21 | 126 | 6594 | no |
| nan | software | 1.28 | None | None | None | None | None | yes |
| rollback | operator | 2.75 | 0.0 | 1.17 | 3.92 | 36 | 6594 | yes |
| loss_spike | software | 7.12 | None | None | None | None | None | yes |
| rollback | operator | 7.28 | 0.0 | 2.18 | 3.43 | 126 | 6594 | yes |

## Checkpoint

- committed: 55, failed: 1, restores: 16
- stall per save: mean 0.023 s, p95 0.0287 s; commit latency mean 0.0249 s; size 1152096 bytes (tiny model)

## All computed metrics

| ID | Metric | Value | Unit | Severity |
|---|---|---|---|---|
| CK-01 | Time since last committed checkpoint | 1.1874 | x interval | OK |
| CK-02 | Compute dollars at risk (since last commit) | 0.6012 | USD | OK |
| CK-03 | Consecutive failed saves | 1 | count | MEDIUM |
| CK-04 | Checksum mismatches (commit or restore) | 0 | count | OK |
| CK-05 | Restore check failures (digest, probe, next batch, frozen) | 0 | count | OK |
| CK-06 | Strict-load or environment refusals | 0 | count | OK |
| CK-07 | NaN guard trips | 1 | count | HIGH |
| CK-08 | Save stall as share of interval | 0.2872 | % | OK |
| CK-09 | Commit latency (stall end to committed) | 0.0635 | s | OK |
| CK-10 | Save backpressure (previous save still running) | 0 | count/day | OK |
| CK-13 | Restore time (job start to first productive step) | 92.6 | s | OK |
| CK-14 | Work lost per incident | 0.9337 | x interval | LOW |
| CK-15 | Protected checkpoint missing or deleted | 0 | count | OK |
| CK-16 | Orphan uncommitted objects in S3 | 0.0 | GB | OK |
| CK-18 | Export parity failures (safetensors) | 0 | count | OK |
| CK-19 | Resharded resumes | 2 | count | LOW |
| CK-20 | Probe value missing for this device class | 0 | count | OK |
| Q-01 | Main run not running (pending time) | 90.18 | s | OK |
| Q-02 | Main run held (exit 78 / crash loop) | 3 | count | HIGH |
| Q-03 | Reschedule latency (job end to running again) | 90.18 | s | OK |
| Q-04 | Crash-loop holds | 1 | count | MEDIUM |
| Q-05 | Main-run interruptions per day | 927.1357 | count/day | HIGH |
| Q-07 | Allocated but not stepping | 92.599 | s | OK |
| Q-09 | Drained nodes | 2 | count | MEDIUM |
| Q-10 | Node replacement time (drain to spare running the job) | 422.224 | s | MEDIUM |
| Q-14 | Team GPU-hours lost to preemption | 0.0922 | node-h/week | OK |
| Q-16 | Jobs rejected for no valid account | 1 | count | LOW |
| Q-19 | Goodput of the main run | 11.3053 | % | HIGH |
| Q-20 | MTTR (fault to first productive step) | 81.6506 | s | OK |
| Q-21 | Human interventions | 4 | count/week | MEDIUM |
| H-01 | Fatal Xid on a node | 1 | count | HIGH |
| H-14 | Step watchdog fired (hang) | 1.8396 | count/h | MEDIUM |
| H-15 | Straggler ratio (rank step time / median) | 1.1546 | ratio | MEDIUM |
| H-17 | Health check runtime (prolog) | 0.048 | s | OK |
| H-18 | Required check skipped | 0 | count | OK |
| H-21 | Spot interruption notice | 1 | count | HIGH |
| H-24 | Loss-spike guard trips | 1 | count | HIGH |
| C-02 | Cost per productive GPU-hour vs list price | 8.8454 | ratio | HIGH |
| C-03 | Wasted share of main-run spend | 88.6947 | % | HIGH |
| C-04 | Cost of one incident | 21.4587 | x interval cost | HIGH |
