# Simulation metrics report: run `v5main`

Cluster price used: 2 × p6-b200.48xlarge = **$227.86/h** (assumed price, see metrics/prices.yaml). Interval: 8 s (one interval = $0.51).

> In the simulation a fault is injected about once a minute, while a real run sees one every few hours or days. So goodput and cost-waste numbers here are far worse than production will be. The simulation proves the *mechanism* and measures each step's *duration*; `support/cost/cost_model.py --measured` projects those durations onto real failure rates.

Metrics in catalog: 74; computed from simulation events: 40.

## Alerts

| Severity | ID | Metric | Value | Caused by the test? | Action |
|---|---|---|---|---|---|
| HIGH | CK-07 | NaN guard trips | 1 count | yes | Rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | Q-02 | Main run held (exit 78 / crash loop) | 3 count | yes | Read the job.held cause; rollback or fix, then release. |
| HIGH | Q-05 | Main-run interruptions per day | 938.0487 count/day | fault rate | Group incidents by node and cause_class; drain repeat offenders. |
| HIGH | Q-19 | Goodput of the main run | 11.7657 % | fault rate | See the largest non-productive bucket in the report. |
| HIGH | H-01 | Fatal Xid on a node | 1 count | no | Automatic drain + save; open a hardware ticket; replace the instance. |
| HIGH | H-15 | Straggler ratio (rank step time / median) | 2.0694 ratio | no | Medium for 3 windows: drain at the next checkpoint. |
| HIGH | H-21 | Spot interruption notice | 1 count | yes | Automatic: drain + save + requeue. Page only if no commit within 90 s. |
| HIGH | H-24 | Loss-spike guard trips | 1 count | yes | Look at the batches before the spike; rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | C-02 | Cost per productive GPU-hour vs list price | 8.4993 ratio | fault rate | Fix the largest waste bucket (C-03). |
| HIGH | C-03 | Wasted share of main-run spend | 88.2343 % | fault rate | The report lists each bucket in USD. |
| HIGH | C-04 | Cost of one incident | 21.5362 x interval cost | yes | Large values: missing emergency save, slow restore, or no spare. |
| MEDIUM | CK-03 | Consecutive failed saves | 1 count | no | Read the failure cause (nvme_full, IntegrityError, upload timeout) and fix it now. |
| MEDIUM | Q-04 | Crash-loop holds | 1 count | yes | Read the logs of the 3 crashes; for the main run this is also Q-02 (high). |
| MEDIUM | Q-09 | Drained nodes | 2 count | yes | Re-test with --full; repair, replace or stop the instance. |
| MEDIUM | Q-10 | Node replacement time (drain to spare running the job) | 422.283 s | yes | Keep the hot spare up; check preemption grace time on the spare's team job. |
| MEDIUM | Q-21 | Human interventions | 4 count/week | yes | Automate the step that needed a person. |
| MEDIUM | H-14 | Step watchdog fired (hang) | 1.8612 count/h | fault rate | Read the stack dump in the job log and the NCCL flight-recorder trace; drain the rank that stopped. |
| LOW | CK-01 | Time since last committed checkpoint | 1.2464 x interval | no | Check checkpoint.failed events; if saves fail, fix storage before the next failure costs a full interval. |
| LOW | CK-02 | Compute dollars at risk (since last commit) | 0.6311 USD | no | Same as CK-01. Thresholds are multiples of the cost of one interval. |
| LOW | CK-14 | Work lost per incident | 0.9912 x interval | no | Check that SIGUSR1/SIGTERM reached the trainer and the emergency save committed. |
| LOW | CK-19 | Resharded resumes | 1 count | yes | Note it in the run log and the paper's failure table. |
| LOW | Q-16 | Jobs rejected for no valid account | 1 count | yes | Check the submit system's account mapping. |

## Where the main run's wall-clock time (and money) went

| Bucket | Seconds | Share | USD |
|---|---|---|---|
| checkpoint_stall | 1.24 | 0.1% | $0.08 |
| lost_work | 26.75 | 1.6% | $1.69 |
| detection | 302.62 | 18.1% | $19.15 |
| reschedule | 1026.26 | 61.3% | $64.96 |
| restore | 121.49 | 7.2% | $7.69 |
| productive | 197.13 | 11.8% | $12.48 |
| wall_clock | 1675.49 | 100.0% | $106.05 |

## Recovery time by fault type (MTTR, seconds)

| Fault | n | p50 | p95 | max |
|---|---|---|---|---|
| hang | 1 | 89.23 | 89.23 | 89.23 |
| health_fail | 1 | 91.73 | 91.73 | 91.73 |
| kill | 3 | 81.91 | 88.84 | 88.84 |
| kill_during_restore | 1 | 170.17 | 170.17 | 170.17 |
| kill_during_save | 1 | 79.0 | 79.0 | 79.0 |
| node_loss | 1 | 115.93 | 115.93 | 115.93 |
| resume_after_fence | 1 | 5.03 | 5.03 | 5.03 |
| rollback | 2 | 3.99 | 4.05 | 4.05 |
| sigusr1 | 3 | 88.58 | 90.18 | 90.18 |
| spot_notice | 1 | 89.26 | 89.26 | 89.26 |
| two_nodes_down | 1 | 113.1 | 113.1 | 113.1 |

## Incidents

| Fault | Cause class | Detect s | Reschedule s | Restore s | MTTR s | Lost steps | Restored step | Human |
|---|---|---|---|---|---|---|---|---|
| nvlink_down | gpu | None | None | None | None | None | None | no |
| time_limit | planned | 154.8 | 0.0 | None | None | None | None | no |
| kill | software | 0.23 | 86.51 | 2.1 | 88.84 | 83 | 2757 | no |
| kill | software | 0.23 | 79.08 | 1.55 | 80.86 | 1 | 2889 | no |
| kill | software | 0.23 | 79.55 | 2.12 | 81.91 | 9 | 3021 | no |
| sigusr1 | preemption | 0.38 | 86.63 | 1.57 | 88.58 | 0 | 3041 | no |
| sigusr1 | preemption | 0.39 | 87.51 | 2.28 | 90.18 | 0 | 3052 | no |
| sigusr1 | preemption | 0.38 | 85.79 | 1.57 | 87.74 | 0 | 3083 | no |
| kill_during_save | software | 7.86 | 69.57 | 1.57 | 79.0 | 46 | 3214 | no |
| kill_during_restore | software | 0.24 | 77.85 | 92.07 | 170.17 | 36 | 3344 | no |
| spot_notice | host | 2.37 | 84.62 | 2.27 | 89.26 | 0 | 3396 | no |
| health_fail | gpu | 27.45 | 62.14 | 2.14 | 91.73 | 0 | 3860 | no |
| two_nodes_down | gpu | 22.4 | 89.09 | 1.61 | 113.1 | 0 | 4273 | no |
| hang | software | 20.89 | 65.55 | 2.78 | 89.23 | 27 | 4273 | no |
| node_loss | host | 41.95 | 72.37 | 1.61 | 115.93 | 47 | 4273 | no |
| split_brain | software | 1.74 | None | None | None | None | None | no |
| resume_after_fence | operator | 2.76 | 0.0 | 2.27 | 5.03 | 134 | 6526 | no |
| nan | software | 0.91 | None | None | None | None | None | yes |
| rollback | operator | 1.93 | 0.0 | 2.12 | 4.05 | 64 | 6526 | yes |
| loss_spike | software | 7.62 | None | None | None | None | None | yes |
| rollback | operator | 7.86 | 0.0 | 1.86 | 3.93 | 5 | 6655 | yes |

## Checkpoint

- committed: 56, failed: 1, restores: 16
- stall per save: mean 0.0221 s, p95 0.0242 s; commit latency mean 0.1069 s; size 1152112 bytes (tiny model)

## All computed metrics

| ID | Metric | Value | Unit | Severity |
|---|---|---|---|---|
| CK-01 | Time since last committed checkpoint | 1.2464 | x interval | LOW |
| CK-02 | Compute dollars at risk (since last commit) | 0.6311 | USD | LOW |
| CK-03 | Consecutive failed saves | 1 | count | MEDIUM |
| CK-04 | Checksum mismatches (commit or restore) | 0 | count | OK |
| CK-05 | Restore check failures (digest, probe, next batch, frozen) | 0 | count | OK |
| CK-06 | Strict-load or environment refusals | 0 | count | OK |
| CK-07 | NaN guard trips | 1 | count | HIGH |
| CK-08 | Save stall as share of interval | 0.2766 | % | OK |
| CK-09 | Commit latency (stall end to committed) | 0.2131 | s | OK |
| CK-10 | Save backpressure (previous save still running) | 0 | count/day | OK |
| CK-13 | Restore time (job start to first productive step) | 92.07 | s | OK |
| CK-14 | Work lost per incident | 0.9912 | x interval | LOW |
| CK-15 | Protected checkpoint missing or deleted | 0 | count | OK |
| CK-16 | Orphan uncommitted objects in S3 | 0.0 | GB | OK |
| CK-18 | Export parity failures (safetensors) | 0 | count | OK |
| CK-19 | Resharded resumes | 1 | count | LOW |
| CK-20 | Probe value missing for this device class | 0 | count | OK |
| Q-01 | Main run not running (pending time) | 89.09 | s | OK |
| Q-02 | Main run held (exit 78 / crash loop) | 3 | count | HIGH |
| Q-03 | Reschedule latency (job end to running again) | 89.09 | s | OK |
| Q-04 | Crash-loop holds | 1 | count | MEDIUM |
| Q-05 | Main-run interruptions per day | 938.0487 | count/day | HIGH |
| Q-07 | Allocated but not stepping | 92.068 | s | OK |
| Q-09 | Drained nodes | 2 | count | MEDIUM |
| Q-10 | Node replacement time (drain to spare running the job) | 422.283 | s | MEDIUM |
| Q-14 | Team GPU-hours lost to preemption | 0.0 | node-h/week | OK |
| Q-16 | Jobs rejected for no valid account | 1 | count | LOW |
| Q-19 | Goodput of the main run | 11.7657 | % | HIGH |
| Q-20 | MTTR (fault to first productive step) | 79.9712 | s | OK |
| Q-21 | Human interventions | 4 | count/week | MEDIUM |
| H-01 | Fatal Xid on a node | 1 | count | HIGH |
| H-14 | Step watchdog fired (hang) | 1.8612 | count/h | MEDIUM |
| H-15 | Straggler ratio (rank step time / median) | 2.0694 | ratio | HIGH |
| H-17 | Health check runtime (prolog) | 0.047 | s | OK |
| H-18 | Required check skipped | 0 | count | OK |
| H-21 | Spot interruption notice | 1 | count | HIGH |
| H-24 | Loss-spike guard trips | 1 | count | HIGH |
| C-02 | Cost per productive GPU-hour vs list price | 8.4993 | ratio | HIGH |
| C-03 | Wasted share of main-run spend | 88.2343 | % | HIGH |
| C-04 | Cost of one incident | 21.5362 | x interval cost | HIGH |
