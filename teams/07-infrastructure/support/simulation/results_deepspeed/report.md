# Simulation metrics report: run `v5main`

Cluster price used: 2 × p6-b200.48xlarge = **$227.86/h** (assumed price, see metrics/prices.yaml). Interval: 8 s (one interval = $0.51).

> In the simulation a fault is injected about once a minute, while a real run sees one every few hours or days. So goodput and cost-waste numbers here are far worse than production will be. The simulation proves the *mechanism* and measures each step's *duration*; `support/cost/cost_model.py --measured` projects those durations onto real failure rates.

Metrics in catalog: 74; computed from simulation events: 40.

## Alerts

| Severity | ID | Metric | Value | Caused by the test? | Action |
|---|---|---|---|---|---|
| HIGH | CK-06 | Strict-load or environment refusals | 1 count | yes | Fix the key mismatch, or restart with --allow-env-change after a person approves the change. |
| HIGH | CK-07 | NaN guard trips | 1 count | yes | Rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | Q-02 | Main run held (exit 78 / crash loop) | 3 count | yes | Read the job.held cause; rollback or fix, then release. |
| HIGH | Q-05 | Main-run interruptions per day | 891.4477 count/day | fault rate | Group incidents by node and cause_class; drain repeat offenders. |
| HIGH | Q-19 | Goodput of the main run | 27.0244 % | fault rate | See the largest non-productive bucket in the report. |
| HIGH | H-14 | Step watchdog fired (hang) | 2.0635 count/h | fault rate | Read the stack dump in the job log and the NCCL flight-recorder trace; drain the rank that stopped. |
| HIGH | H-21 | Spot interruption notice | 1 count | yes | Automatic: drain + save + requeue. Page only if no commit within 90 s. |
| HIGH | H-24 | Loss-spike guard trips | 1 count | yes | Look at the batches before the spike; rollback: --from-step <last good> --skip N --branch <new>. |
| HIGH | C-02 | Cost per productive GPU-hour vs list price | 3.7004 ratio | fault rate | Fix the largest waste bucket (C-03). |
| HIGH | C-03 | Wasted share of main-run spend | 72.9756 % | fault rate | The report lists each bucket in USD. |
| HIGH | C-04 | Cost of one incident | 14.9775 x interval cost | yes | Large values: missing emergency save, slow restore, or no spare. |
| MEDIUM | Q-04 | Crash-loop holds | 1 count | yes | Read the logs of the 3 crashes; for the main run this is also Q-02 (high). |
| MEDIUM | Q-09 | Drained nodes | 2 count | yes | Re-test with --full; repair, replace or stop the instance. |
| MEDIUM | Q-21 | Human interventions | 5 count/week | yes | Automate the step that needed a person. |
| MEDIUM | H-15 | Straggler ratio (rank step time / median) | 1.1234 ratio | no | Medium for 3 windows: drain at the next checkpoint. |
| LOW | CK-01 | Time since last committed checkpoint | 1.385 x interval | no | Check checkpoint.failed events; if saves fail, fix storage before the next failure costs a full interval. |
| LOW | CK-02 | Compute dollars at risk (since last commit) | 0.7013 USD | no | Same as CK-01. Thresholds are multiples of the cost of one interval. |
| LOW | CK-14 | Work lost per incident | 0.7238 x interval | no | Check that SIGUSR1/SIGTERM reached the trainer and the emergency save committed. |
| LOW | Q-16 | Jobs rejected for no valid account | 1 count | yes | Check the submit system's account mapping. |

## Where the main run's wall-clock time (and money) went

| Bucket | Seconds | Share | USD |
|---|---|---|---|
| checkpoint_stall | 1.11 | 0.1% | $0.07 |
| lost_work | 16.07 | 1.0% | $1.02 |
| detection | 147.87 | 8.8% | $9.36 |
| reschedule | 1019.73 | 60.8% | $64.54 |
| restore | 40.04 | 2.4% | $2.53 |
| productive | 453.58 | 27.0% | $28.71 |
| wall_clock | 1678.39 | 100.0% | $106.23 |

## Recovery time by fault type (MTTR, seconds)

| Fault | n | p50 | p95 | max |
|---|---|---|---|---|
| hang | 1 | 89.71 | 89.71 | 89.71 |
| health_fail | 1 | 91.55 | 91.55 | 91.55 |
| kill | 3 | 81.46 | 89.2 | 89.2 |
| kill_during_restore | 1 | 79.49 | 79.49 | 79.49 |
| kill_during_save | 1 | 80.25 | 80.25 | 80.25 |
| node_loss | 1 | 117.67 | 117.67 | 117.67 |
| rollback | 2 | 4.78 | 5.41 | 5.41 |
| sigusr1 | 3 | 89.28 | 89.81 | 89.81 |
| spot_notice | 1 | 88.94 | 88.94 | 88.94 |
| two_nodes_down | 1 | 113.51 | 113.51 | 113.51 |

## Incidents

| Fault | Cause class | Detect s | Reschedule s | Restore s | MTTR s | Lost steps | Restored step | Human |
|---|---|---|---|---|---|---|---|---|
| kill | software | 0.27 | 85.93 | 3.0 | 89.2 | 65 | 2905 | no |
| kill | software | 0.24 | 78.58 | 2.24 | 81.06 | 3 | 3037 | no |
| kill | software | 0.25 | 78.95 | 2.26 | 81.46 | 1 | 3169 | no |
| sigusr1 | preemption | 0.39 | 86.51 | 2.92 | 89.81 | 0 | 3190 | no |
| sigusr1 | preemption | 0.38 | 84.64 | 2.3 | 87.31 | 0 | 3224 | no |
| sigusr1 | preemption | 0.33 | 85.97 | 2.98 | 89.28 | 0 | 3253 | no |
| kill_during_save | software | 9.96 | 67.44 | 2.85 | 80.25 | 14 | 3386 | no |
| kill_during_restore | software | 0.24 | 76.67 | 2.58 | 79.49 | 32 | 3518 | no |
| spot_notice | host | 1.84 | 84.83 | 2.28 | 88.94 | 0 | 3558 | no |
| health_fail | gpu | 25.56 | 63.13 | 2.87 | 91.55 | 0 | 3998 | no |
| two_nodes_down | gpu | 21.0 | 90.13 | 2.38 | 113.51 | 0 | 4384 | no |
| hang | software | 20.81 | 66.22 | 2.69 | 89.71 | 6 | 4384 | no |
| node_loss | host | 44.05 | 70.73 | 2.89 | 117.67 | 36 | 4384 | no |
| nan | software | 1.12 | None | None | None | None | None | yes |
| rollback | operator | 3.64 | 0.0 | None | None | None | None | yes |
| rollback | operator | 2.43 | 0.0 | 2.98 | 5.41 | 97 | 6623 | yes |
| loss_spike | software | 7.38 | None | None | None | None | None | yes |
| rollback | operator | 7.98 | 0.0 | 2.82 | 4.15 | 15 | 6755 | yes |

## Checkpoint

- committed: 56, failed: 0, restores: 16
- stall per save: mean 0.0197 s, p95 0.0222 s; commit latency mean 0.0853 s; size 1466776 bytes (tiny model)

## All computed metrics

| ID | Metric | Value | Unit | Severity |
|---|---|---|---|---|
| CK-01 | Time since last committed checkpoint | 1.385 | x interval | LOW |
| CK-02 | Compute dollars at risk (since last commit) | 0.7013 | USD | LOW |
| CK-03 | Consecutive failed saves | 0 | count | OK |
| CK-04 | Checksum mismatches (commit or restore) | 0 | count | OK |
| CK-05 | Restore check failures (digest, probe, next batch, frozen) | 0 | count | OK |
| CK-06 | Strict-load or environment refusals | 1 | count | HIGH |
| CK-07 | NaN guard trips | 1 | count | HIGH |
| CK-08 | Save stall as share of interval | 0.2467 | % | OK |
| CK-09 | Commit latency (stall end to committed) | 0.1025 | s | OK |
| CK-10 | Save backpressure (previous save still running) | 0 | count/day | OK |
| CK-13 | Restore time (job start to first productive step) | 3.0 | s | OK |
| CK-14 | Work lost per incident | 0.7238 | x interval | LOW |
| CK-15 | Protected checkpoint missing or deleted | 0 | count | OK |
| CK-16 | Orphan uncommitted objects in S3 | 0.0 | GB | OK |
| CK-18 | Export parity failures (safetensors) | 0 | count | OK |
| CK-19 | Resharded resumes | 0 | count | OK |
| CK-20 | Probe value missing for this device class | 0 | count | OK |
| Q-01 | Main run not running (pending time) | 90.13 | s | OK |
| Q-02 | Main run held (exit 78 / crash loop) | 3 | count | HIGH |
| Q-03 | Reschedule latency (job end to running again) | 90.13 | s | OK |
| Q-04 | Crash-loop holds | 1 | count | MEDIUM |
| Q-05 | Main-run interruptions per day | 891.4477 | count/day | HIGH |
| Q-07 | Allocated but not stepping | 20.19 | s | OK |
| Q-09 | Drained nodes | 2 | count | MEDIUM |
| Q-10 | Node replacement time (drain to spare running the job) | 92.774 | s | OK |
| Q-14 | Team GPU-hours lost to preemption | 0.0 | node-h/week | OK |
| Q-16 | Jobs rejected for no valid account | 1 | count | LOW |
| Q-19 | Goodput of the main run | 27.0244 | % | HIGH |
| Q-20 | MTTR (fault to first productive step) | 79.2533 | s | OK |
| Q-21 | Human interventions | 5 | count/week | MEDIUM |
| H-01 | Fatal Xid on a node | 0 | count | OK |
| H-14 | Step watchdog fired (hang) | 2.0635 | count/h | HIGH |
| H-15 | Straggler ratio (rank step time / median) | 1.1234 | ratio | MEDIUM |
| H-17 | Health check runtime (prolog) | 0.012 | s | OK |
| H-18 | Required check skipped | 0 | count | OK |
| H-21 | Spot interruption notice | 1 | count | HIGH |
| H-24 | Loss-spike guard trips | 1 | count | HIGH |
| C-02 | Cost per productive GPU-hour vs list price | 3.7004 | ratio | HIGH |
| C-03 | Wasted share of main-run spend | 72.9756 | % | HIGH |
| C-04 | Cost of one incident | 14.9775 | x interval cost | HIGH |
