# Metrics catalog

Generated from `metrics/catalog.yaml` by `python metrics/evaluate.py --render-md`. Do not edit by hand.

| Severity | Response | Who |
|---|---|---|
| **HIGH** | page now, 24x7, ack <= 15 min | Team 07 on-call (Team 08 delivers the page) |
| **MEDIUM** | fix the same working day (<= 4 h) | Team 07 |
| **LOW** | weekly ops review | Team 07 + lead |

## Checkpoint (20 metrics)

| ID | Metric | Unit | Alert when | LOW | MEDIUM | HIGH | Why it matters (simple words) | Action | Sim |
|---|---|---|---|---|---|---|---|---|---|
| CK-01 | Time since last committed checkpoint | x interval | above | 1.2 | 1.5 | 2.0 | Everything trained since the last commit is lost if a node dies now. | Check checkpoint.failed events; if saves fail, fix storage before the next failure costs a full interval. | yes |
| CK-02 | Compute dollars at risk (since last commit) | USD | above | 1.2 × interval cost | 1.5 × interval cost | 2.0 × interval cost | The same risk in money: cluster price x time since the last commit. | Same as CK-01. Thresholds are multiples of the cost of one interval. | yes |
| CK-03 | Consecutive failed saves | count | above | — | 1 | 2 | One failed save doubles the work at risk; two in a row triples it. | Read the failure cause (nvme_full, IntegrityError, upload timeout) and fix it now. | yes |
| CK-04 | Checksum mismatches (commit or restore) | count | above | — | — | 1 | A damaged checkpoint file. The restore skips it, but the cause (disk, network, S3) can damage the next one. | Find the hop that corrupts data (NVMe, network, S3). Pin the last good checkpoint. | yes |
| CK-05 | Restore check failures (digest, probe, next batch, frozen) | count | above | — | — | 1 | The loaded state is not the saved state: a silent misload like V4's (loss 2.95 vs 2.55). | Stop the run; compare the printed saved/restored values; do not continue on that checkpoint. | yes |
| CK-06 | Strict-load or environment refusals | count | above | — | — | 1 | The code or software changed under the run; every restart fails the same way. | Fix the key mismatch, or restart with --allow-env-change after a person approves the change. | yes |
| CK-07 | NaN guard trips | count | above | — | — | 1 | Training produced NaN. The run is held, nothing bad was saved, but GPUs are idle until a rollback. | Rollback: --from-step <last good> --skip N --branch <new>. | yes |
| CK-08 | Save stall as share of interval | % | above | 1.0 | 2.0 | 5.0 | While a save stalls training, all GPUs wait. 2% stall = 2% of the GPU bill wasted. | Raise the interval or speed up GPU-to-host staging (Team 06). | yes |
| CK-09 | Commit latency (stall end to committed) | s | above | 300 | 600 | 1200 | Until the commit, the new checkpoint does not protect anything; eval also waits for it. | Check upload throughput (CK-11) and S3 errors. | yes |
| CK-10 | Save backpressure (previous save still running) | count/day | above | 1 | 3 | — | The interval is shorter than the upload time: saves queue up and the wait becomes stall. | Increase the interval or upload bandwidth. | yes |
| CK-11 | Upload throughput vs baseline | ratio | below | 0.8 | 0.5 | — | Slow uploads stretch commit latency and the work at risk. | Check NIC, S3 prefix throttling (503 SlowDown), multipart size. | no |
| CK-12 | NVMe headroom (free / per-node checkpoint share) | ratio | below | 3.0 | 2.0 | 1.2 | Below 1.2x the next save is skipped (nvme_full). | Clean the node's NVMe, lower keep_local, or replace the node. | no |
| CK-13 | Restore time (job start to first productive step) | s | above | 600 | 900 | 1800 | Every restore minute is a full-cluster minute paid for with no training. | Use the node-local copy when valid; prefetch from S3 in parallel; check S3 throughput. | yes |
| CK-14 | Work lost per incident | x interval | above | 0.6 | 1.0 | 2.0 | Expected loss is half an interval; more means saves failed or the emergency save did not happen. | Check that SIGUSR1/SIGTERM reached the trainer and the emergency save committed. | yes |
| CK-15 | Protected checkpoint missing or deleted | count | above | — | — | 1 | Protected checkpoints (every N-th, final, pinned) are the money we can never re-buy. | Restore from S3 versioning; check the retention job's cloud role. | yes |
| CK-16 | Orphan uncommitted objects in S3 | GB | above | 1 | 100 | — | Half-uploaded checkpoints are never used but are billed every month. | Run the retention job; add an S3 lifecycle rule to abort incomplete multipart uploads after 1 day. | yes |
| CK-17 | Checkpoint storage cost per day vs plan | ratio | above | 1.0 | 1.5 | — | S3 cost grows with every kept checkpoint. | Move protected checkpoints older than X days to the archive tier; check keep counts. | no |
| CK-18 | Export parity failures (safetensors) | count | above | — | 1 | — | Teams 09/11/12 would evaluate or ship weights that are not the trained ones. | Block the export; compare keys and probe bits. | yes |
| CK-19 | Resharded resumes | count | above | 1 | — | — | Resume on a different world size is safe but not bit-equal: the branch is marked. | Note it in the run log and the paper's failure table. | yes |
| CK-20 | Probe value missing for this device class | count | above | 1 | — | — | First restore on new hardware cannot compare probe bits yet. | Record the probe on the new class at the next save. | yes |

## Queue (21 metrics)

| ID | Metric | Unit | Alert when | LOW | MEDIUM | HIGH | Why it matters (simple words) | Action | Sim |
|---|---|---|---|---|---|---|---|---|---|
| Q-01 | Main run not running (pending time) | s | above | — | 120 | 600 | The main run's nodes are paid for whether it runs or not. | squeue reason: no nodes (drained > spares?), held, or controller issue. | yes |
| Q-02 | Main run held (exit 78 / crash loop) | count | above | — | — | 1 | Held means a person must act; until then the cluster burns money with no training. | Read the job.held cause; rollback or fix, then release. | yes |
| Q-03 | Reschedule latency (job end to running again) | s | above | 120 | 300 | 600 | Time between the crash and the restart is pure loss. Floor: cred_expire=60 + 1 s, so a normal restart is 85-95 s; LOW starts at 2x that floor. | Check the spare is up and idle (Q-08), and slurmctld load. | yes |
| Q-04 | Crash-loop holds | count | above | — | 1 | — | A job crashed 3 times in 30 min and was stopped so it does not burn GPU hours in a loop. | Read the logs of the 3 crashes; for the main run this is also Q-02 (high). | yes |
| Q-05 | Main-run interruptions per day | count/day | above | 2 | 5 | 10 | A rising rate means a bad node or bad code; each one costs ~interval/2 + MTTR. | Group incidents by node and cause_class; drain repeat offenders. | yes |
| Q-06 | Idle GPU node-hours (up, no job) | node-h/day | above | 0.5 | 2 | 4 | An idle running GPU node costs the full hourly price for nothing. | Check SuspendTime / power saving; stop forgotten instances. | no |
| Q-07 | Allocated but not stepping | s | above | — | 300 | 900 | Slurm says the job runs, but no training step completes: a hang or a slow restore. | Check the watchdog fired; dump stacks; if not, cancel with USR1. | yes |
| Q-08 | Healthy idle spare nodes | count | below | — | 0 | — | Without a spare, the next node failure waits for a new instance (minutes to hours). | Undrain a repaired node or start a new one. | no |
| Q-09 | Drained nodes | count | above | 1 | 2 | 3 | Drained nodes are paid for (unless stopped) and reduce spares. | Re-test with --full; repair, replace or stop the instance. | yes |
| Q-10 | Node replacement time (drain to spare running the job) | s | above | 120 | 300 | 900 | How long the main run is down when a node is taken out. | Keep the hot spare up; check preemption grace time on the spare's team job. | yes |
| Q-11 | slurmctld not responding | s | above | — | — | 60 | No scheduling, no requeue, no restarts. | Fail over to the backup controller; check the head node. | no |
| Q-12 | slurmdbd not responding | s | above | — | 300 | — | Accounting and budgets stop updating; limits are enforced on stale data. | Restart slurmdbd; check MariaDB disk. | no |
| Q-13 | Team queue wait p95 | h | above | 1 | 4 | — | Teams blocked waiting cannot use the capacity calendar they were given. | Check fair-share and caps; move work to off-peak. | no |
| Q-14 | Team GPU-hours lost to preemption | node-h/week | above | 1 | 5 | — | Preempted team jobs lose work since their last save. | Ask the team to checkpoint more often, or schedule them away from main-run restarts. | yes |
| Q-15 | Account budget used (GrpTRESMins) | % | above | 50 | 75 | 90 | At 100% the account's jobs stop. | Warn the team at 50/75; at 90 the lead decides to top up or stop. | no |
| Q-16 | Jobs rejected for no valid account | count | above | 1 | — | — | Someone tried to submit outside the accounting rules. | Check the submit system's account mapping. | yes |
| Q-17 | Clock offset between nodes | ms | above | 50 | 100 | 500 | Wrong clocks break event ordering, MTTR numbers and incident timelines. | Restart chrony; check the cloud's time service. | no |
| Q-18 | Container image pull time | s | above | 300 | 900 | — | A slow first pull adds to every restart on a new node. | Pre-pull the image into the Enroot cache on NVMe at boot. | no |
| Q-19 | Goodput of the main run | % | below | 92 | 90 | 80 | The share of paid wall-clock time that trained the model. Frontier runs: 89-90%. | See the largest non-productive bucket in the report. | yes |
| Q-20 | MTTR (fault to first productive step) | s | above | 900 | 1800 | 3600 | Mean time the whole cluster is down per incident. | Break it down: detection, reschedule, restore (report shows each). | yes |
| Q-21 | Human interventions | count/week | above | 1 | 3 | — | Every manual step is a delay at 4 a.m. and a chance of mistakes. Llama 3: 3 of 466. | Automate the step that needed a person. | yes |

## Health (24 metrics)

| ID | Metric | Unit | Alert when | LOW | MEDIUM | HIGH | Why it matters (simple words) | Action | Sim |
|---|---|---|---|---|---|---|---|---|---|
| H-01 | Fatal Xid on a node | count | above | — | — | 1 | The GPU is broken (79 fallen off bus, 94/95 ECC, 48 DBE...). The job will crash or produce garbage. | Automatic drain + save; open a hardware ticket; replace the instance. | yes |
| H-02 | Warn/unknown Xid | count/day | above | 1 | 3 | — | Often software (13, 31, 43) but repeats point to hardware. | Correlate with job crashes; drain at the next checkpoint if repeating. | no |
| H-03 | ECC uncorrectable errors | count | above | — | — | 1 | Memory returned wrong data: the step result cannot be trusted. | Drain now; roll back to the checkpoint before the first error if loss looks wrong. | no |
| H-04 | Correctable ECC 24 h vs fleet median | ratio | above | 2 | 3 | — | A rising correctable count often comes before an uncorrectable one. | Schedule the node for --full re-test at the next checkpoint. | no |
| H-05 | Row remap pending | count | above | — | 1 | — | The GPU needs a reset to finish repairing its memory. | Drain at the next checkpoint and reset the GPU. | no |
| H-06 | Row remap failure | count | above | — | — | 1 | The GPU ran out of spare memory rows: it must be replaced. | Drain now; replace the instance. | no |
| H-07 | GPU count lower than expected | count | above | — | — | 1 | A GPU disappeared: jobs fail to start or run slower. | Drain; reboot or replace. | no |
| H-08 | GPU temperature vs slowdown limit | C below limit | below | 10 | 5 | 0 | A hot GPU slows down and then the whole job runs at its speed. | Check the instance; provider support ticket for cooling. | no |
| H-09 | Hardware slowdown / power brake active | count | above | — | 1 | — | One throttled GPU slows every GPU in the job. | Drain at the next checkpoint. | no |
| H-10 | PCIe link narrower than max | count | above | — | 1 | — | Slow host-GPU copies: slower checkpoints and data loading. | Reboot; replace if it persists. | no |
| H-11 | NVLink / fast network link down | count | above | — | — | 1 | Collectives fall back to slow paths or fail. | Drain now. | no |
| H-12 | All-reduce busbw vs baseline | ratio | below | 0.95 | 0.9 | 0.7 | A slow link slows every step of the main run. | Below 0.9 the node fails --full; find the slow NIC or GPU. | no |
| H-13 | All-reduce wrong result | count | above | — | — | 1 | Wrong sums mean wrong gradients: silent damage to the model. | Drain now; check for silent data corruption on that node. | no |
| H-14 | Step watchdog fired (hang) | count/h | above | — | 1 | 2 | A hang was turned into a restart; repeated hangs point to a bad node or a deadlock. | Read the stack dump in the job log and the NCCL flight-recorder trace; drain the rank that stopped. | yes |
| H-15 | Straggler ratio (rank step time / median) | ratio | above | 1.05 | 1.1 | 1.25 | The slowest rank sets the speed of all ranks: a 10% straggler wastes 10% of the bill. | Medium for 3 windows: drain at the next checkpoint. | yes |
| H-16 | NCCL timeouts | count/h | above | — | 1 | 2 | Network or a stuck rank; each costs a restart. | Flight-recorder dump shows which rank; drain that node. | no |
| H-17 | Health check runtime (prolog) | s | above | 30 | 60 | — | Every prolog second delays every job start. | Move slow checks to --full. | yes |
| H-18 | Required check skipped | count | above | — | 1 | — | We are blind on that node: a GPU check could not run. | Install the missing tool (nvidia-smi, dcgmi) or fix permissions. | yes |
| H-19 | False drains (passes --full after drain) | count/week | above | 1 | 3 | — | Each false drain costs a restart and a spare for nothing. | Loosen the threshold that caused it. | no |
| H-20 | Missed incidents (no prior warn/fail) | count/dry run | above | 1 | — | — | A failure our checks did not see coming. | Add a check or tighten a threshold; update the coverage map. | no |
| H-21 | Spot interruption notice | count | above | — | — | 1 | 2 minutes until the node is gone. The automatic save must finish in time. | Automatic: drain + save + requeue. Page only if no commit within 90 s. | yes |
| H-22 | DCGM diag failure | count | above | — | — | 1 | NVIDIA's own test says the GPU is faulty. | Drain; replace the instance. | no |
| H-24 | Loss-spike guard trips | count | above | — | — | 1 | The loss jumped far above its recent median for several steps without a NaN: the model is diverging. The run is held, nothing bad was saved. | Look at the batches before the spike; rollback: --from-step <last good> --skip N --branch <new>. | yes |
| H-23 | Host memory available for staging | ratio of need | below | 2.0 | 1.2 | 1.0 | Async staging needs pinned host RAM; without it saves fail or the node swaps. | Find the memory leak (data loader workers); restart at next checkpoint. | no |

## Cost (9 metrics)

| ID | Metric | Unit | Alert when | LOW | MEDIUM | HIGH | Why it matters (simple words) | Action | Sim |
|---|---|---|---|---|---|---|---|---|---|
| C-01 | Burn rate vs plan | ratio | above | 1.05 | 1.1 | 1.25 | Spending faster than the plan ends the budget before training ends. | Find what is running outside the capacity calendar; stop it. | no |
| C-02 | Cost per productive GPU-hour vs list price | ratio | above | 1.08 | 1.11 | 1.25 | price / goodput: what one useful GPU-hour really costs. 1.11 = goodput 90%. | Fix the largest waste bucket (C-03). | yes |
| C-03 | Wasted share of main-run spend | % | above | 8 | 10 | 20 | Stall + lost work + detection + reschedule + restore, in money. | The report lists each bucket in USD. | yes |
| C-04 | Cost of one incident | x interval cost | above | 0.75 | 1.5 | 3.0 | (lost work + detect + reschedule + restore) x cluster price. | Large values: missing emergency save, slow restore, or no spare. | yes |
| C-05 | Instances running that Slurm does not know | count | above | — | — | 1 | A forgotten GPU instance can cost thousands of dollars a day (V4: a cluster idle for 3 days). | Stop it now; find who started it. | no |
| C-06 | Budget days left vs training days left | ratio | below | 1.2 | 1.0 | 0.8 | Below 1.0 the money runs out before training finishes. | Cut team allocations or the run length; decide early. | no |
| C-07 | Cross-zone / internet egress | USD/day | above | 1 | 20 | — | Data transfer out of the region or across AZs is billed per GB; it should be near 0. | Keep nodes, bucket and eval in one region and zone; use a private storage endpoint. | no |
| C-08 | Unattached block volumes / old snapshots | USD/month | above | 10 | 100 | — | Storage left behind keeps billing. | Delete or snapshot-and-delete. | no |
| C-09 | Spare node cost share | % | above | 15 | 25 | — | One hot spare on a 2-node run is 33% extra; on 8 nodes 11%. Worth it only if it saves more restart time. | Let the spare run preemptible team work; revisit spare count vs MTBF. | no |
