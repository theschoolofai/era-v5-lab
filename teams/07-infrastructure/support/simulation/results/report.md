# Simulation metrics report: run `v5main`

Cluster price used: 2 × gpu-node-8 = **$227.86/h** (assumed price, see metrics/prices.yaml). Interval: 8 s (one interval = $0.51).

> In the simulation a fault is injected about once a minute, while a real run sees one every few hours or days. So goodput and cost-waste numbers here are far worse than production will be. The simulation proves the *mechanism* and measures each step's *duration*; `support/cost/cost_model.py --measured` projects those durations onto real failure rates.

Metrics in catalog: 74; computed from simulation events: 40.

## Alerts

| Severity | ID | Metric | Value | Caused by the test? | Action |
|---|---|---|---|---|---|
| HIGH | CK-07 | NaN guard trips | 1 count | yes | Rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | Q-02 | Main run held (exit 78 / crash loop) | 3 count | yes | Read the job.held cause; rollback or fix, then release. |
| HIGH | Q-05 | Main-run interruptions per day | 919.2649 count/day | fault rate | Group incidents by node and cause_class; drain repeat offenders. |
| HIGH | Q-19 | Goodput of the main run | 11.4316 % | fault rate | See the largest non-productive bucket in the report. |
| HIGH | H-01 | Fatal Xid on a node | 1 count | no | Automatic drain + save; open a hardware ticket; replace the instance. |
| HIGH | H-21 | Spot interruption notice | 1 count | yes | Automatic: drain + save + requeue. Page only if no commit within 90 s. |
| HIGH | H-24 | Loss-spike guard trips | 1 count | yes | Look at the batches before the spike; rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | C-02 | Cost per productive GPU-hour vs list price | 8.7476 ratio | fault rate | Fix the largest waste bucket (C-03). |
| HIGH | C-03 | Wasted share of main-run spend | 88.5684 % | fault rate | The report lists each bucket in USD. |
| HIGH | C-04 | Cost of one incident | 21.4012 x interval cost | yes | Large values: missing emergency save, slow restore, or no spare. |
| MEDIUM | CK-03 | Consecutive failed saves | 1 count | no | Read the failure cause (nvme_full, IntegrityError, upload timeout) and fix it now. |
| MEDIUM | Q-04 | Crash-loop holds | 1 count | yes | Read the logs of the 3 crashes; for the main run this is also Q-02 (high). |
| MEDIUM | Q-09 | Drained nodes | 2 count | yes | Re-test with --full; repair, replace or stop the instance. |
| MEDIUM | Q-10 | Node replacement time (drain to spare running the job) | 422.303 s | yes | Keep the hot spare up; check preemption grace time on the spare's team job. |
| MEDIUM | Q-21 | Human interventions | 4 count/week | yes | Automate the step that needed a person. |
| MEDIUM | H-14 | Step watchdog fired (hang) | 1.8239 count/h | fault rate | Read the stack dump in the job log and the NCCL flight-recorder trace; drain the rank that stopped. |
| LOW | CK-01 | Time since last committed checkpoint | 1.3576 x interval | no | Check checkpoint.failed events; if saves fail, fix storage before the next failure costs a full interval. |
| LOW | CK-02 | Compute dollars at risk (since last commit) | 0.6874 USD | no | Same as CK-01. Thresholds are multiples of the cost of one interval. |
| LOW | CK-14 | Work lost per incident | 0.9738 x interval | no | Check that SIGUSR1/SIGTERM reached the trainer and the emergency save committed. |
| LOW | CK-19 | Resharded resumes | 1 count | yes | Note it in the run log and the paper's failure table. |
| LOW | Q-16 | Jobs rejected for no valid account | 1 count | yes | Check the submit system's account mapping. |
| LOW | H-15 | Straggler ratio (rank step time / median) | 1.0895 ratio | no | Medium for 3 windows: drain at the next checkpoint. |

## Where the main run's wall-clock time (and money) went

| Bucket | Seconds | Share | USD |
|---|---|---|---|
| checkpoint_stall | 1.44 | 0.1% | $0.09 |
| lost_work | 22.19 | 1.3% | $1.40 |
| detection | 345.74 | 20.2% | $21.88 |
| reschedule | 1025.49 | 59.8% | $64.91 |
| restore | 125.12 | 7.3% | $7.92 |
| productive | 196.19 | 11.4% | $12.42 |
| wall_clock | 1716.17 | 100.0% | $108.62 |

## Recovery time by fault type (MTTR, seconds)

| Fault | n | p50 | p95 | max |
|---|---|---|---|---|
| hang | 1 | 89.02 | 89.02 | 89.02 |
| health_fail | 1 | 88.92 | 88.92 | 88.92 |
| kill | 3 | 80.12 | 88.6 | 88.6 |
| kill_during_restore | 1 | 169.47 | 169.47 | 169.47 |
| kill_during_save | 1 | 78.08 | 78.08 | 78.08 |
| node_loss | 1 | 120.46 | 120.46 | 120.46 |
| resume_after_fence | 1 | 39.78 | 39.78 | 39.78 |
| rollback | 2 | 3.9 | 3.9 | 3.9 |
| sigusr1 | 3 | 89.06 | 89.09 | 89.09 |
| spot_notice | 1 | 88.51 | 88.51 | 88.51 |
| two_nodes_down | 1 | 116.67 | 116.67 | 116.67 |

## Incidents

| Fault | Cause class | Detect s | Reschedule s | Restore s | MTTR s | Lost steps | Restored step | Human |
|---|---|---|---|---|---|---|---|---|
| nvlink_down | gpu | None | None | None | None | None | None | no |
| time_limit | planned | 158.86 | 0.0 | None | None | None | None | no |
| kill | software | 0.31 | 86.41 | 1.88 | 88.6 | 33 | 2747 | no |
| kill | software | 0.27 | 78.05 | 1.8 | 80.12 | 33 | 2877 | no |
| kill | software | 0.3 | 77.29 | 2.12 | 79.7 | 34 | 3006 | no |
| sigusr1 | preemption | 0.44 | 86.42 | 2.2 | 89.06 | 0 | 3033 | no |
| sigusr1 | preemption | 0.46 | 85.66 | 2.06 | 88.18 | 0 | 3057 | no |
| sigusr1 | preemption | 0.45 | 86.06 | 2.58 | 89.09 | 0 | 3092 | no |
| kill_during_save | software | 8.21 | 67.46 | 2.41 | 78.08 | 49 | 3211 | no |
| kill_during_restore | software | 0.28 | 77.92 | 91.27 | 169.47 | 29 | 3341 | no |
| spot_notice | host | 1.45 | 84.68 | 2.37 | 88.51 | 0 | 3404 | no |
| health_fail | gpu | 24.13 | 63.06 | 1.72 | 88.92 | 0 | 3836 | no |
| two_nodes_down | gpu | 24.02 | 90.12 | 2.53 | 116.67 | 0 | 4226 | no |
| hang | software | 20.96 | 66.24 | 1.82 | 89.02 | 4 | 4226 | no |
| node_loss | host | 41.21 | 76.12 | 3.13 | 120.46 | 14 | 4226 | no |
| split_brain | software | 8.92 | None | None | None | None | None | no |
| resume_after_fence | operator | 37.25 | 0.0 | 2.53 | 39.78 | 130 | 6470 | no |
| nan | software | 1.38 | None | None | None | None | None | yes |
| rollback | operator | 1.63 | 0.0 | 2.26 | 3.89 | 40 | 6470 | yes |
| loss_spike | software | 7.31 | None | None | None | None | None | yes |
| rollback | operator | 7.9 | 0.0 | 2.44 | 3.9 | 4 | 6596 | yes |

## Checkpoint

- committed: 57, failed: 1, restores: 16
- stall per save: mean 0.0253 s, p95 0.0326 s; commit latency mean 0.1197 s; size 1152152 bytes (tiny model)

## All computed metrics

| ID | Metric | Value | Unit | Severity |
|---|---|---|---|---|
| CK-01 | Time since last committed checkpoint | 1.3576 | x interval | LOW |
| CK-02 | Compute dollars at risk (since last commit) | 0.6874 | USD | LOW |
| CK-03 | Consecutive failed saves | 1 | count | MEDIUM |
| CK-04 | Checksum mismatches (commit or restore) | 0 | count | OK |
| CK-05 | Restore check failures (digest, probe, next batch, frozen) | 0 | count | OK |
| CK-06 | Strict-load or environment refusals | 0 | count | OK |
| CK-07 | NaN guard trips | 1 | count | HIGH |
| CK-08 | Save stall as share of interval | 0.3158 | % | OK |
| CK-09 | Commit latency (stall end to committed) | 0.2317 | s | OK |
| CK-10 | Save backpressure (previous save still running) | 0 | count/day | OK |
| CK-13 | Restore time (job start to first productive step) | 91.27 | s | OK |
| CK-14 | Work lost per incident | 0.9738 | x interval | LOW |
| CK-15 | Protected checkpoint missing or deleted | 0 | count | OK |
| CK-16 | Orphan uncommitted objects in S3 | 0.0 | GB | OK |
| CK-18 | Export parity failures (safetensors) | 0 | count | OK |
| CK-19 | Resharded resumes | 1 | count | LOW |
| CK-20 | Probe value missing for this device class | 0 | count | OK |
| Q-01 | Main run not running (pending time) | 90.12 | s | OK |
| Q-02 | Main run held (exit 78 / crash loop) | 3 | count | HIGH |
| Q-03 | Reschedule latency (job end to running again) | 90.12 | s | OK |
| Q-04 | Crash-loop holds | 1 | count | MEDIUM |
| Q-05 | Main-run interruptions per day | 919.2649 | count/day | HIGH |
| Q-07 | Allocated but not stepping | 91.269 | s | OK |
| Q-09 | Drained nodes | 2 | count | MEDIUM |
| Q-10 | Node replacement time (drain to spare running the job) | 422.303 | s | MEDIUM |
| Q-14 | Team GPU-hours lost to preemption | 0.0 | node-h/week | OK |
| Q-16 | Jobs rejected for no valid account | 1 | count | LOW |
| Q-19 | Goodput of the main run | 11.4316 | % | HIGH |
| Q-20 | MTTR (fault to first productive step) | 82.0906 | s | OK |
| Q-21 | Human interventions | 4 | count/week | MEDIUM |
| H-01 | Fatal Xid on a node | 1 | count | HIGH |
| H-14 | Step watchdog fired (hang) | 1.8239 | count/h | MEDIUM |
| H-15 | Straggler ratio (rank step time / median) | 1.0895 | ratio | LOW |
| H-17 | Health check runtime (prolog) | 0.091 | s | OK |
| H-18 | Required check skipped | 0 | count | OK |
| H-21 | Spot interruption notice | 1 | count | HIGH |
| H-24 | Loss-spike guard trips | 1 | count | HIGH |
| C-02 | Cost per productive GPU-hour vs list price | 8.7476 | ratio | HIGH |
| C-03 | Wasted share of main-run spend | 88.5684 | % | HIGH |
| C-04 | Cost of one incident | 21.4012 | x interval cost | HIGH |
