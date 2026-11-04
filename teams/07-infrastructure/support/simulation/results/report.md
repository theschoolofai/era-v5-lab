# Simulation metrics report: run `v5main`

Cluster: 2 × gpu-node-8. Waste is counted in **node-hours** (cost = node-hours × the price of one node-hour, an input with no value in the repo). Interval: 8 s (one interval = 0.0044 node-hours).

> In the simulation a fault is injected about once a minute, while a real run sees one every few hours or days. So goodput and cost-waste numbers here are far worse than production will be. The simulation proves the *mechanism* and measures each step's *duration*; `support/cost/cost_model.py --measured` projects those durations onto real failure rates.

Metrics in catalog: 74; computed from simulation events: 40.

## Alerts

| Severity | ID | Metric | Value | Caused by the test? | Action |
|---|---|---|---|---|---|
| HIGH | CK-07 | NaN guard trips | 1 count | yes | Rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | Q-02 | Main run held (exit 78 / crash loop) | 3 count | yes | Read the job.held cause; rollback or fix, then release. |
| HIGH | Q-05 | Main-run interruptions per day | 932.3674 count/day | fault rate | Group incidents by node and cause_class; drain repeat offenders. |
| HIGH | Q-19 | Goodput of the main run | 12.0399 % | fault rate | See the largest non-productive bucket in the report. |
| HIGH | H-01 | Fatal Xid on a node | 1 count | no | Automatic drain + save; open a hardware ticket; replace the instance. |
| HIGH | H-21 | Spot interruption notice | 1 count | yes | Automatic: drain + save + requeue. Page only if no commit within 90 s. |
| HIGH | H-24 | Loss-spike guard trips | 1 count | yes | Look at the batches before the spike; rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | C-02 | Node-hours per productive node-hour | 8.3057 ratio | fault rate | Fix the largest waste bucket (C-03). |
| HIGH | C-03 | Wasted share of main-run spend | 87.9601 % | fault rate | The report lists each bucket in node-hours. |
| HIGH | C-04 | Cost of one incident | 21.45 x interval node-hours | yes | Large values: missing emergency save, slow restore, or no spare. |
| MEDIUM | CK-03 | Consecutive failed saves | 1 count | no | Read the failure cause (nvme_full, IntegrityError, upload timeout) and fix it now. |
| MEDIUM | CK-14 | Work lost per incident | 1.0012 x interval | no | Check that SIGUSR1/SIGTERM reached the trainer and the emergency save committed. |
| MEDIUM | Q-04 | Crash-loop holds | 1 count | yes | Read the logs of the 3 crashes; for the main run this is also Q-02 (high). |
| MEDIUM | Q-09 | Drained nodes | 2 count | yes | Re-test with --full; repair, replace or stop the instance. |
| MEDIUM | Q-10 | Node replacement time (drain to spare running the job) | 422.031 s | yes | Keep the hot spare up; check preemption grace time on the spare's team job. |
| MEDIUM | Q-21 | Human interventions | 4 count/week | yes | Automate the step that needed a person. |
| MEDIUM | H-14 | Step watchdog fired (hang) | 1.8499 count/h | fault rate | Read the stack dump in the job log and the NCCL flight-recorder trace; drain the rank that stopped. |
| MEDIUM | H-15 | Straggler ratio (rank step time / median) | 1.1307 ratio | no | Medium for 3 windows: drain at the next checkpoint. |
| LOW | CK-01 | Time since last committed checkpoint | 1.2648 x interval | no | Check checkpoint.failed events; if saves fail, fix storage before the next failure costs a full interval. |
| LOW | CK-02 | Node-hours at risk (since last commit) | 0.0056 node-h | no | Same as CK-01. Thresholds are multiples of the node-hours in one interval. |
| LOW | CK-19 | Resharded resumes | 2 count | yes | Note it in the run log and the paper's failure table. |
| LOW | Q-16 | Jobs rejected for no valid account | 1 count | yes | Check the submit system's account mapping. |

## Where the main run's wall-clock time (and node-hours) went

| Bucket | Seconds | Share | Node-hours |
|---|---|---|---|
| checkpoint_stall | 1.27 | 0.1% | 0.0007 |
| lost_work | 29.07 | 1.7% | 0.0162 |
| detection | 314.05 | 18.6% | 0.1745 |
| reschedule | 1021.34 | 60.4% | 0.5674 |
| restore | 120.89 | 7.1% | 0.0672 |
| productive | 203.49 | 12.0% | 0.113 |
| wall_clock | 1690.11 | 100.0% | 0.9389 |

## Recovery time by fault type (MTTR, seconds)

| Fault | n | p50 | p95 | max |
|---|---|---|---|---|
| hang | 1 | 88.1 | 88.1 | 88.1 |
| health_fail | 1 | 88.33 | 88.33 | 88.33 |
| kill | 3 | 82.19 | 89.13 | 89.13 |
| kill_during_restore | 1 | 169.41 | 169.41 | 169.41 |
| kill_during_save | 1 | 81.17 | 81.17 | 81.17 |
| node_loss | 1 | 118.33 | 118.33 | 118.33 |
| resume_after_fence | 1 | 4.47 | 4.47 | 4.47 |
| rollback | 2 | 3.62 | 4.55 | 4.55 |
| sigusr1 | 3 | 88.18 | 89.97 | 89.97 |
| spot_notice | 1 | 88.81 | 88.81 | 88.81 |
| two_nodes_down | 1 | 117.12 | 117.12 | 117.12 |

## Incidents

| Fault | Cause class | Detect s | Reschedule s | Restore s | MTTR s | Lost steps | Restored step | Human |
|---|---|---|---|---|---|---|---|---|
| nvlink_down | gpu | None | None | None | None | None | None | no |
| time_limit | planned | 154.61 | 0.0 | None | None | None | None | no |
| kill | software | 0.25 | 87.3 | 1.58 | 89.13 | 78 | 2762 | no |
| kill | software | 0.25 | 79.27 | 1.57 | 81.09 | 7 | 2893 | no |
| kill | software | 0.25 | 79.71 | 2.23 | 82.19 | 5 | 3025 | no |
| sigusr1 | preemption | 0.38 | 84.55 | 1.6 | 86.54 | 0 | 3071 | no |
| sigusr1 | preemption | 0.37 | 87.42 | 2.18 | 89.97 | 0 | 3088 | no |
| sigusr1 | preemption | 0.41 | 85.46 | 2.31 | 88.18 | 0 | 3120 | no |
| kill_during_save | software | 10.02 | 69.07 | 2.08 | 81.17 | 8 | 3252 | no |
| kill_during_restore | software | 0.24 | 76.98 | 92.19 | 169.41 | 37 | 3383 | no |
| spot_notice | host | 2.12 | 84.34 | 2.35 | 88.81 | 0 | 3439 | no |
| health_fail | gpu | 25.63 | 61.12 | 1.58 | 88.33 | 0 | 3887 | no |
| two_nodes_down | gpu | 25.15 | 90.26 | 1.72 | 117.12 | 0 | 4330 | no |
| hang | software | 20.67 | 65.51 | 1.92 | 88.1 | 30 | 4330 | no |
| node_loss | host | 45.58 | 70.35 | 2.4 | 118.33 | 30 | 4330 | no |
| split_brain | software | 7.5 | None | None | None | None | None | no |
| resume_after_fence | operator | 2.26 | 0.0 | 2.21 | 4.47 | 135 | 6825 | no |
| nan | software | 1.13 | None | None | None | None | None | yes |
| rollback | operator | 3.07 | 0.0 | 1.48 | 4.55 | 35 | 6825 | yes |
| loss_spike | software | 7.5 | None | None | None | None | None | yes |
| rollback | operator | 6.66 | 0.0 | 1.49 | 2.7 | 125 | 6825 | yes |

## Checkpoint

- committed: 57, failed: 1, restores: 16
- stall per save: mean 0.0223 s, p95 0.0254 s; commit latency mean 0.1044 s; size 1152044 bytes (tiny model)

## All computed metrics

| ID | Metric | Value | Unit | Severity |
|---|---|---|---|---|
| CK-01 | Time since last committed checkpoint | 1.2648 | x interval | LOW |
| CK-02 | Node-hours at risk (since last commit) | 0.0056 | node-h | LOW |
| CK-03 | Consecutive failed saves | 1 | count | MEDIUM |
| CK-04 | Checksum mismatches (commit or restore) | 0 | count | OK |
| CK-05 | Restore check failures (digest, probe, next batch, frozen) | 0 | count | OK |
| CK-06 | Strict-load or environment refusals | 0 | count | OK |
| CK-07 | NaN guard trips | 1 | count | HIGH |
| CK-08 | Save stall as share of interval | 0.2783 | % | OK |
| CK-09 | Commit latency (stall end to committed) | 0.1597 | s | OK |
| CK-10 | Save backpressure (previous save still running) | 0 | count/day | OK |
| CK-13 | Restore time (job start to first productive step) | 92.19 | s | OK |
| CK-14 | Work lost per incident | 1.0012 | x interval | MEDIUM |
| CK-15 | Protected checkpoint missing or deleted | 0 | count | OK |
| CK-16 | Orphan uncommitted objects in S3 | 0.0 | GB | OK |
| CK-18 | Export parity failures (safetensors) | 0 | count | OK |
| CK-19 | Resharded resumes | 2 | count | LOW |
| CK-20 | Probe value missing for this device class | 0 | count | OK |
| Q-01 | Main run not running (pending time) | 90.26 | s | OK |
| Q-02 | Main run held (exit 78 / crash loop) | 3 | count | HIGH |
| Q-03 | Reschedule latency (job end to running again) | 90.26 | s | OK |
| Q-04 | Crash-loop holds | 1 | count | MEDIUM |
| Q-05 | Main-run interruptions per day | 932.3674 | count/day | HIGH |
| Q-07 | Allocated but not stepping | 92.19 | s | OK |
| Q-09 | Drained nodes | 2 | count | MEDIUM |
| Q-10 | Node replacement time (drain to spare running the job) | 422.031 | s | MEDIUM |
| Q-14 | Team GPU-hours lost to preemption | 0.0 | node-h/week | OK |
| Q-16 | Jobs rejected for no valid account | 1 | count | LOW |
| Q-19 | Goodput of the main run | 12.0399 | % | HIGH |
| Q-20 | MTTR (fault to first productive step) | 80.0056 | s | OK |
| Q-21 | Human interventions | 4 | count/week | MEDIUM |
| H-01 | Fatal Xid on a node | 1 | count | HIGH |
| H-14 | Step watchdog fired (hang) | 1.8499 | count/h | MEDIUM |
| H-15 | Straggler ratio (rank step time / median) | 1.1307 | ratio | MEDIUM |
| H-17 | Health check runtime (prolog) | 0.043 | s | OK |
| H-18 | Required check skipped | 0 | count | OK |
| H-21 | Spot interruption notice | 1 | count | HIGH |
| H-24 | Loss-spike guard trips | 1 | count | HIGH |
| C-02 | Node-hours per productive node-hour | 8.3057 | ratio | HIGH |
| C-03 | Wasted share of main-run spend | 87.9601 | % | HIGH |
| C-04 | Cost of one incident | 21.45 | x interval node-hours | HIGH |
