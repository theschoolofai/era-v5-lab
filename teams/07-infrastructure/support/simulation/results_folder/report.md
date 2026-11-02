# Simulation metrics report: run `v5main`

Cluster: 2 × gpu-node-8. Waste is counted in **node-hours** (cost = node-hours × the price of one node-hour, an input with no value in the repo). Interval: 8 s (one interval = 0.0044 node-hours).

> In the simulation a fault is injected about once a minute, while a real run sees one every few hours or days. So goodput and cost-waste numbers here are far worse than production will be. The simulation proves the *mechanism* and measures each step's *duration*; `support/cost/cost_model.py --measured` projects those durations onto real failure rates.

Metrics in catalog: 74; computed from simulation events: 40.

## Alerts

| Severity | ID | Metric | Value | Caused by the test? | Action |
|---|---|---|---|---|---|
| HIGH | CK-07 | NaN guard trips | 1 count | yes | Rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | Q-02 | Main run held (exit 78 / crash loop) | 3 count | yes | Read the job.held cause; rollback or fix, then release. |
| HIGH | Q-05 | Main-run interruptions per day | 924.4969 count/day | fault rate | Group incidents by node and cause_class; drain repeat offenders. |
| HIGH | Q-19 | Goodput of the main run | 11.6275 % | fault rate | See the largest non-productive bucket in the report. |
| HIGH | H-01 | Fatal Xid on a node | 1 count | no | Automatic drain + save; open a hardware ticket; replace the instance. |
| HIGH | H-21 | Spot interruption notice | 1 count | yes | Automatic: drain + save + requeue. Page only if no commit within 90 s. |
| HIGH | H-24 | Loss-spike guard trips | 1 count | yes | Look at the batches before the spike; rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | C-02 | Node-hours per productive node-hour | 8.6003 ratio | fault rate | Fix the largest waste bucket (C-03). |
| HIGH | C-03 | Wasted share of main-run spend | 88.3725 % | fault rate | The report lists each bucket in node-hours. |
| HIGH | C-04 | Cost of one incident | 21.435 x interval node-hours | yes | Large values: missing emergency save, slow restore, or no spare. |
| MEDIUM | CK-03 | Consecutive failed saves | 1 count | no | Read the failure cause (nvme_full, IntegrityError, upload timeout) and fix it now. |
| MEDIUM | Q-04 | Crash-loop holds | 1 count | yes | Read the logs of the 3 crashes; for the main run this is also Q-02 (high). |
| MEDIUM | Q-09 | Drained nodes | 2 count | yes | Re-test with --full; repair, replace or stop the instance. |
| MEDIUM | Q-10 | Node replacement time (drain to spare running the job) | 422.174 s | yes | Keep the hot spare up; check preemption grace time on the spare's team job. |
| MEDIUM | Q-21 | Human interventions | 4 count/week | yes | Automate the step that needed a person. |
| MEDIUM | H-14 | Step watchdog fired (hang) | 1.8343 count/h | fault rate | Read the stack dump in the job log and the NCCL flight-recorder trace; drain the rank that stopped. |
| LOW | CK-01 | Time since last committed checkpoint | 1.3359 x interval | no | Check checkpoint.failed events; if saves fail, fix storage before the next failure costs a full interval. |
| LOW | CK-02 | Node-hours at risk (since last commit) | 0.0059 node-h | no | Same as CK-01. Thresholds are multiples of the node-hours in one interval. |
| LOW | CK-14 | Work lost per incident | 0.9712 x interval | no | Check that SIGUSR1/SIGTERM reached the trainer and the emergency save committed. |
| LOW | CK-19 | Resharded resumes | 1 count | yes | Note it in the run log and the paper's failure table. |
| LOW | Q-16 | Jobs rejected for no valid account | 1 count | yes | Check the submit system's account mapping. |
| LOW | H-15 | Straggler ratio (rank step time / median) | 1.0917 ratio | no | Medium for 3 windows: drain at the next checkpoint. |

## Where the main run's wall-clock time (and node-hours) went

| Bucket | Seconds | Share | Node-hours |
|---|---|---|---|
| checkpoint_stall | 1.35 | 0.1% | 0.0007 |
| lost_work | 26.21 | 1.5% | 0.0146 |
| detection | 339.46 | 19.9% | 0.1886 |
| reschedule | 1029.28 | 60.2% | 0.5718 |
| restore | 113.86 | 6.7% | 0.0633 |
| productive | 198.7 | 11.6% | 0.1104 |
| wall_clock | 1708.85 | 100.0% | 0.9494 |

## Recovery time by fault type (MTTR, seconds)

| Fault | n | p50 | p95 | max |
|---|---|---|---|---|
| hang | 1 | 88.32 | 88.32 | 88.32 |
| health_fail | 1 | 91.14 | 91.14 | 91.14 |
| kill | 3 | 80.8 | 87.2 | 87.2 |
| kill_during_restore | 1 | 170.64 | 170.64 | 170.64 |
| kill_during_save | 1 | 80.09 | 80.09 | 80.09 |
| node_loss | 1 | 118.15 | 118.15 | 118.15 |
| resume_after_fence | 1 | 37.65 | 37.65 | 37.65 |
| rollback | 2 | 2.84 | 2.93 | 2.93 |
| sigusr1 | 3 | 89.07 | 90.15 | 90.15 |
| spot_notice | 1 | 89.1 | 89.1 | 89.1 |
| two_nodes_down | 1 | 115.95 | 115.95 | 115.95 |

## Incidents

| Fault | Cause class | Detect s | Reschedule s | Restore s | MTTR s | Lost steps | Restored step | Human |
|---|---|---|---|---|---|---|---|---|
| nvlink_down | gpu | None | None | None | None | None | None | no |
| time_limit | planned | 155.11 | 0.0 | None | None | None | None | no |
| kill | software | 0.12 | 85.22 | 1.87 | 87.2 | 104 | 2736 | no |
| kill | software | 0.12 | 79.21 | 1.3 | 80.64 | 12 | 2868 | no |
| kill | software | 0.12 | 78.83 | 1.84 | 80.8 | 21 | 2999 | no |
| sigusr1 | preemption | 0.31 | 85.8 | 1.29 | 87.4 | 0 | 3043 | no |
| sigusr1 | preemption | 0.32 | 87.45 | 1.3 | 89.07 | 0 | 3055 | no |
| sigusr1 | preemption | 0.34 | 87.98 | 1.82 | 90.15 | 0 | 3072 | no |
| kill_during_save | software | 9.91 | 68.42 | 1.75 | 80.09 | 16 | 3204 | no |
| kill_during_restore | software | 0.12 | 79.25 | 91.27 | 170.64 | 14 | 3336 | no |
| spot_notice | host | 3.13 | 84.72 | 1.25 | 89.1 | 0 | 3402 | no |
| health_fail | gpu | 26.78 | 63.12 | 1.25 | 91.14 | 0 | 3860 | no |
| two_nodes_down | gpu | 23.83 | 90.15 | 1.97 | 115.95 | 0 | 4276 | no |
| hang | software | 20.96 | 66.1 | 1.26 | 88.32 | 24 | 4276 | no |
| node_loss | host | 43.19 | 73.03 | 1.93 | 118.15 | 34 | 4276 | no |
| split_brain | software | 2.13 | None | None | None | None | None | no |
| resume_after_fence | operator | 36.35 | 0.0 | 1.3 | 37.65 | 130 | 6400 | no |
| nan | software | 0.98 | None | None | None | None | None | yes |
| rollback | operator | 1.53 | 0.0 | 1.23 | 2.76 | 60 | 6400 | yes |
| loss_spike | software | 7.34 | None | None | None | None | None | yes |
| rollback | operator | 6.77 | 0.0 | 1.23 | 2.93 | 23 | 6527 | yes |

## Checkpoint

- committed: 56, failed: 1, restores: 16
- stall per save: mean 0.0241 s, p95 0.0305 s; commit latency mean 0.0267 s; size 1152112 bytes (tiny model)

## All computed metrics

| ID | Metric | Value | Unit | Severity |
|---|---|---|---|---|
| CK-01 | Time since last committed checkpoint | 1.3359 | x interval | LOW |
| CK-02 | Node-hours at risk (since last commit) | 0.0059 | node-h | LOW |
| CK-03 | Consecutive failed saves | 1 | count | MEDIUM |
| CK-04 | Checksum mismatches (commit or restore) | 0 | count | OK |
| CK-05 | Restore check failures (digest, probe, next batch, frozen) | 0 | count | OK |
| CK-06 | Strict-load or environment refusals | 0 | count | OK |
| CK-07 | NaN guard trips | 1 | count | HIGH |
| CK-08 | Save stall as share of interval | 0.3008 | % | OK |
| CK-09 | Commit latency (stall end to committed) | 0.0662 | s | OK |
| CK-10 | Save backpressure (previous save still running) | 0 | count/day | OK |
| CK-13 | Restore time (job start to first productive step) | 91.27 | s | OK |
| CK-14 | Work lost per incident | 0.9712 | x interval | LOW |
| CK-15 | Protected checkpoint missing or deleted | 0 | count | OK |
| CK-16 | Orphan uncommitted objects in S3 | 0.0 | GB | OK |
| CK-18 | Export parity failures (safetensors) | 0 | count | OK |
| CK-19 | Resharded resumes | 1 | count | LOW |
| CK-20 | Probe value missing for this device class | 0 | count | OK |
| Q-01 | Main run not running (pending time) | 90.15 | s | OK |
| Q-02 | Main run held (exit 78 / crash loop) | 3 | count | HIGH |
| Q-03 | Reschedule latency (job end to running again) | 90.15 | s | OK |
| Q-04 | Crash-loop holds | 1 | count | MEDIUM |
| Q-05 | Main-run interruptions per day | 924.4969 | count/day | HIGH |
| Q-07 | Allocated but not stepping | 91.267 | s | OK |
| Q-09 | Drained nodes | 2 | count | MEDIUM |
| Q-10 | Node replacement time (drain to spare running the job) | 422.174 | s | MEDIUM |
| Q-14 | Team GPU-hours lost to preemption | 0.0 | node-h/week | OK |
| Q-16 | Jobs rejected for no valid account | 1 | count | LOW |
| Q-19 | Goodput of the main run | 11.6275 | % | HIGH |
| Q-20 | MTTR (fault to first productive step) | 81.9994 | s | OK |
| Q-21 | Human interventions | 4 | count/week | MEDIUM |
| H-01 | Fatal Xid on a node | 1 | count | HIGH |
| H-14 | Step watchdog fired (hang) | 1.8343 | count/h | MEDIUM |
| H-15 | Straggler ratio (rank step time / median) | 1.0917 | ratio | LOW |
| H-17 | Health check runtime (prolog) | 0.058 | s | OK |
| H-18 | Required check skipped | 0 | count | OK |
| H-21 | Spot interruption notice | 1 | count | HIGH |
| H-24 | Loss-spike guard trips | 1 | count | HIGH |
| C-02 | Node-hours per productive node-hour | 8.6003 | ratio | HIGH |
| C-03 | Wasted share of main-run spend | 88.3725 | % | HIGH |
| C-04 | Cost of one incident | 21.435 | x interval node-hours | HIGH |
