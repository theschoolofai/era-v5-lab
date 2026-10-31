# Monitoring guide (`metrics/`): how to read what the cluster reports, and what to do about it

For **Team 08 (Monitoring)** and **whoever is on call**. Decision record: [ADR 0004](../adr/0004-cost-model-and-alerting.md).
All 74 metrics: [metrics_catalog.md](../support/docs/metrics_catalog.md). Every code and cause on one page:
[codes_and_actions.md](../support/docs/codes_and_actions.md).

> **In one paragraph.** Everything the cluster says (an exit code, a held job, a drained node, an alert)
> answers three questions in the same words everywhere: **what happened**, **what the system already did by
> itself**, and **what a person does now**. Most faults fix themselves (the job saves, Slurm restarts it, a sick
> node is taken out). A person is only needed when the system deliberately stopped, because retrying would
> burn money: those are the **HIGH** alerts. If you see a code you do not know, run
> `python metrics/explain.py <code>`.

---

## 1. The 30-second version

| You see | It means | You do |
|---|---|---|
| exit **0** | finished | nothing |
| exit **75**, state `REQUEUED` / `BeginTime` | it saved (or crashed once) and restarts by itself in ~50 s | nothing |
| exit **78**, state `SPECIAL_EXIT` / `JobHeldUser` | **held on purpose**: retrying would waste GPU hours | read the job **Comment**; it says what to do |
| node `drain` with reason `v5:<name>` | the health check took a sick node out; its jobs saved and moved | fix or replace the node, then resume it |
| a **HIGH** page | money is being wasted now, or a checkpoint is at risk | act within 15 min (§5) |
| **MEDIUM** | fix today | §5 |
| **LOW** | weekly review | — |

```bash
python metrics/explain.py 78          # or 137, loss_spike, CK-05, v5:xid, JobHeldUser ...
```

---

## 2. Where the signals come from

```text
 trainer ─┐                                       ┌─► Slurm job Comment + job log banner   (people)
 ckpt  ───┤  one JSON line per event              │
 health ──┼──► /var/log/v5/events/<host>-<pid>.jsonl ─────┼─► metrics/watch.py  (every 30 s) ──► alert.fired event
 wrapper ─┤   (common/events.py)                  │                                  └─► webhook: Team 08 pager / chat
 spot   ──┘                                       └─► metrics/evaluate.py (after a run) ─► report.md, metrics.json, alerts.json
                                                       Slurm itself: squeue, sinfo -R, sacct, sshare
```

| Source | What it gives | How to consume it |
|---|---|---|
| **Events** (`/var/log/v5/events/*.jsonl`, node-local) | every fact, with UTC time, host, run, job | ship the files (Team 08's agent → S3 / log store); one JSON per line, no free-text parsing |
| **Live alerts** (`metrics/watch.py`) | `alert.fired` events + a webhook post when a metric reaches a new severity | set `V5_ALERT_WEBHOOK`; page on `severity: high` |
| **Report** (`metrics/evaluate.py`) | goodput, incidents (MTTR per fault), dollars wasted, every metric with its level | after each dry run / daily; `metrics.json` for dashboards |
| **Slurm job Comment** | plain-words status of each job (`V5 HELD (78): loss spike at step 5880 …`) | `squeue -o "%.10i %.12T %.20r %k"` or `scontrol show job <id>` |
| **Job log banner** | the same, longer: what happened / already done / what you do / detail | end of `/var/log/v5/logs/<job>-<id>.out` |
| **Health report** | one JSON per check run, `verdict` + `drain_reason` | the `health.report` event; `/var/log/slurm/health-last.json` on the node |

### Event format

```json
{"schema": "v5-event/1", "time": "2026-10-28T04:12:09.512Z", "host": "gpu-3", "run_id": "v5main",
 "job_id": "8812", "event": "job.held", "cause": "loss_spike", "step": 5880, "restart_count": 4,
 "title": "V5 HELD (78): loss spike: held at step 5880", "severity": "high",
 "you_do": "roll back: sbatch --export=ALL,TRAIN_EXTRA=\"--from-step <last good step> ...\" slurm/mainrun.sbatch"}
```

The events you will use most:

| Event | Key fields | Means |
|---|---|---|
| `job.started` | `restart_count`, `nodes` | a start or restart |
| `job.ended` | `exit` (0/75/78), `trainer_exit` (raw), `cause`, `title`, `you_do` | why the job stopped |
| `job.requeued` / `job.held` | `cause`, `title`, `you_do` | restarting by itself / waiting for a person |
| `checkpoint.committed` | `step`, `stall_s`, `commit_latency_s`, `bytes` | money is protected up to this step |
| `checkpoint.failed` | `cause` (`nvme_full`, `IntegrityError`, `UploadTimeout`, …) | a save did not protect anything |
| `restore.done` / `restore.failed` / `restore.fatal` | `step`, `cause`, `resharded` | how the restart went |
| `train.step` | `step`, `loss`, `step_s` | training is moving |
| `train.watchdog`, `train.loss_spike`, `train.nonfinite` | `step` | a hang / divergence / NaN |
| `node.drained` | `node`, `reason` | a node was taken out |
| `node.spot_notice` | `node` | AWS takes the instance back in 2 min |
| `health.report` | `verdict`, `failed`, `warned`, `skipped_required` | node health |
| `alert.fired` | `id`, `severity`, `value`, `why`, `action`, `respond`, `who`, `page` | an alert |

### Alert payload (webhook body)

```json
{"text": "[HIGH] Q-02 Main run held (exit 78 / crash loop): 1 count\nWhy it matters: ...\nWhat to do: Read the job.held cause; rollback or fix, then release.\nRespond: page now, 24x7, ack <= 15 min (Team 07 on-call (Team 08 delivers the page)). More: python metrics/explain.py Q-02",
 "alert": {"id": "Q-02", "severity": "high", "name": "Main run held (exit 78 / crash loop)", "value": 1,
           "unit": "count", "area": "queue", "why": "...", "action": "...", "respond": "page now, 24x7, ack <= 15 min",
           "who": "Team 07 on-call (Team 08 delivers the page)", "explain": "python metrics/explain.py Q-02"}}
```

`text` (and `content`) is ready for Slack or Discord; `alert` is for a pager or a dashboard. An alert fires
**once per new severity** for a metric, so a flapping value does not page every 30 s.

---

## 3. Severity: how fast, and who

| Level | Response | Who |
|---|---|---|
| **HIGH** | page now, 24×7, acknowledge within 15 min. GPU money is being wasted now, or a checkpoint (money already spent) is at risk | Team 07 on-call; Team 08 delivers the page |
| **MEDIUM** | the same working day (≤ 4 h). Still running, but cost grows if nobody acts | Team 07 |
| **LOW** | weekly ops review: a trend or small inefficiency | Team 07 + lead |

Division of work: **Team 08** collects, stores, shows and delivers. **Team 07** owns the action on the node,
the job or the checkpoint.

---

## 4. "I see X. What now?"

### 4.1 A job's state in `squeue`

```bash
squeue -o "%.10i %.14j %.12T %.22r %k"      # id, name, state, reason, comment (our plain-words status)
```

| State / reason | Means | You do |
|---|---|---|
| `RUNNING`, comment `V5 RUNNING (start #N)` | training (N−1 restarts so far) | nothing |
| `PENDING` / `BeginTime` | just requeued; Slurm waits ~50 s for the old credential to expire | nothing |
| `PENDING` / `Resources` (main run) | not enough healthy nodes | Q-01 pages after 10 min: check `sinfo -R`, repair or add a node |
| `PENDING` / `Priority` | others are ahead | nothing (team jobs) |
| `PENDING` / `AssocGrp…Minutes` | the account's budget is used up | lead decides (Q-15) |
| `PENDING` / `AssocGrpNodeLimit` | the team already holds its 2 nodes | wait |
| `SPECIAL_EXIT` / `JobHeldUser` | **held after exit 78** | read the comment, then §4.2 |
| `PREEMPTED` → `PENDING` | a team job gave its node to the main run (it saved first) | nothing |
| `NODE_FAIL` → requeued | its node died | nothing for the job; look at the node |

### 4.2 Exit codes

| Exit | Name | What the system did | You do |
|---|---|---|---|
| 0 | DONE | job completed | nothing |
| 75 | RETRY | requeued; restarts from `latest.json` | nothing (unless Q-05: too many) |
| 78 | HELD | held, nothing bad saved | follow the cause (table below), then `scontrol release <id>` or resubmit |

The **cause** of a 78, from the job comment or `job.held.cause`:

| Cause | Means | You do |
|---|---|---|
| `nonfinite` | NaN/Inf in loss or state | **roll back** (below), skipping the bad batches |
| `loss_spike` | loss > 1.5 × median for 3 steps | **roll back**; tell Team 05 |
| `crash_loop` | 3 crashes in 30 min | read the job log for the real error; fix; release |
| `StrictLoadError` | model code and checkpoint disagree on tensor names/shapes | fix the code; never resume by ignoring keys |
| `EnvMismatchError` | image / library / config changed | if approved: resubmit with `TRAIN_EXTRA=--allow-env-change` (logged) |
| `CheckpointError` | no committed checkpoint passes its checks | `python ckpt/ckpt.py list` / `verify`; look at CK-04/05 |
| `unknown_fatal` | trainer gave no reason | read the `FATAL` line at the end of the job log |

**Roll back** (keeps the old branch, so nothing is lost):

```bash
python ckpt/ckpt.py list --run s3://<bucket>/ckpt/v5main          # pick the last good step
sbatch --export=ALL,TRAIN_EXTRA="--from-step <step> --skip <N> --branch <new>" slurm/mainrun.sbatch
scancel <held job id>
```

**Raw trainer exit codes** (`job.ended.trainer_exit`; the wrapper already turned them into 75):
`1` Python error (often NCCL), `134` abort, `137` killed (OOM / kill -9), `139` segfault, `143` unhandled
SIGTERM. One is noise; three in 30 min become `crash_loop`.

### 4.3 A drained node (`sinfo -R`)

```bash
sinfo -R            # REASON shows v5:<check names>, e.g. v5:ecc_uncorrectable,xid
python metrics/explain.py v5:ecc_uncorrectable,xid
```

| Reason | You do |
|---|---|
| `xid` (fatal code, or Xid 94 twice in 24 h on one GPU), `ecc_uncorrectable`, `remapped_rows` (failure), `dcgm_diag`, `gpu` | replace the instance (stop/start moves it to new hardware); open a hardware ticket |
| `gpu_count` | reboot; replace if still missing |
| `gpu_temperature` | check cooling; replace if repeated |
| `nvme_free` | clean `/nvme` |
| `clock_offset` | fix chrony |
| `nccl_<op>` (all_reduce, reduce_scatter, all_gather, all_to_all), `nccl_collectives` | `health_check.py --mode full` on it; replace if it fails again |
| `nvlink` | reset the GPUs or reboot; replace if the link stays down |
| `spot_notice` | nothing: the instance goes away |
| `drill_force_fail` | test only: remove `/var/lib/v5-health/force_fail` |

Then put it back: `scontrol update nodename=<node> state=resume`. Its jobs already saved and moved: the
main run is not waiting for you unless Q-01 also fires.

### 4.4 Health check exit codes

`0` pass, `3` warn, `4` fail. In prolog mode a warn also exits 0 (otherwise Slurm would drain healthy
nodes). The JSON report says which check; `explain.py <check name>` says what to do.

---

## 5. Every HIGH alert and its first action

(From `metrics/catalog.yaml`; MEDIUM and LOW levels and the "why" for each are in
[metrics_catalog.md](../support/docs/metrics_catalog.md).)

### Checkpoint: protect money already spent

| ID | Alert | HIGH when | First action |
|---|---|---|---|
| CK-01 | time since last commit | ≥ 2 × interval | check `checkpoint.failed`; fix storage before the next failure costs a full interval |
| CK-02 | dollars at risk since last commit | ≥ 2 × interval cost | same as CK-01 |
| CK-03 | failed saves in a row | ≥ 2 | read the cause (`nvme_full`, `IntegrityError`, `UploadTimeout`) and fix it now |
| CK-04 | checksum mismatch | any | find the hop that corrupts data (NVMe, network, S3); pin the last good checkpoint |
| CK-05 | restore check failure | any | stop; compare the printed saved/restored values; do not continue on that checkpoint |
| CK-06 | strict-load / environment refusal | any | fix the key mismatch, or `--allow-env-change` after approval |
| CK-07 | NaN guard | any | roll back |
| CK-08 | save stall | ≥ 5% of interval | raise the interval or speed up GPU-to-host staging (Team 06) |
| CK-09 | commit latency | ≥ 1200 s | check upload throughput and S3 errors |
| CK-12 | NVMe headroom | ≤ 1.2 × checkpoint share | clean NVMe, lower `keep_local`, or replace the node |
| CK-13 | restore time | ≥ 30 min | use the node-local copy; check S3 throughput |
| CK-14 | work lost per incident | ≥ 2 × interval | check the stop signal reached the trainer and the emergency save committed |
| CK-15 | protected checkpoint missing | any | restore from S3 versioning; check the retention role |

### Queue: keep the main run running

| ID | Alert | HIGH when | First action |
|---|---|---|---|
| Q-01 | main run not running | pending ≥ 10 min | `squeue` reason: not enough nodes? held? controller? |
| Q-02 | main run held | any | read the cause (§4.2); roll back or fix; release |
| Q-03 | reschedule latency | ≥ 10 min | is the spare up and idle (Q-08)? controller load? |
| Q-05 | interruptions | ≥ 10 per day | group incidents by node and cause; drain repeat offenders |
| Q-06 | idle GPU node-hours | ≥ 4 per day | power saving working? stop forgotten instances |
| Q-07 | allocated but not stepping | ≥ 15 min | did the watchdog fire? if not, `scancel --signal=USR1 <job>` |
| Q-09 | drained nodes | ≥ 3 | re-test with `--mode full`; repair, replace or stop |
| Q-10 | node replacement time | ≥ 15 min | keep the spare up; check the grace time of the spare's team job |
| Q-11 | controller down | ≥ 60 s | the backup should be in control (`scontrol ping`); fix the head node |
| Q-15 | account budget | ≥ 90% | lead decides: top up or stop |
| Q-17 | clock offset | ≥ 500 ms | restart chrony |
| Q-19 | goodput | ≤ 80% | look at the largest waste bucket in the report |
| Q-20 | MTTR | ≥ 60 min | which part is slow: detection, reschedule or restore |

### Health: broken hardware

| ID | Alert | HIGH when | First action |
|---|---|---|---|
| H-01 | fatal Xid | any | already drained and saved; replace the instance |
| H-03 | ECC uncorrectable | any | drained; if the loss looks wrong, roll back to before the first error |
| H-06 | row-remap failure | any | replace |
| H-07 | GPU missing | any | reboot or replace |
| H-08 | at slowdown temperature | 0 °C margin | AWS ticket for cooling |
| H-11 | NVLink / EFA link down | any | drain now |
| H-12 | all-reduce bandwidth | ≤ 0.7 × baseline | find the slow NIC or GPU |
| H-13 | all-reduce wrong sum | any | drain; suspect silent data corruption |
| H-14 | watchdog (hang) | ≥ 2 per hour | read the stack dump and flight-recorder trace; drain the rank that stopped |
| H-15 | straggler | ≥ 1.25 × median | drain at the next checkpoint |
| H-16 | NCCL timeouts | ≥ 2 per hour | the flight-recorder trace names the rank; drain its node |
| H-21 | spot notice | any | automatic; page only if no commit within 90 s |
| H-22 | DCGM diag failure | any | replace |
| H-23 | host memory for staging | ≤ 1.0 × need | find the leak (data-loader workers); restart at the next checkpoint |
| H-24 | loss-spike guard | any | roll back; look at the batches before the spike |

### Cost

| ID | Alert | HIGH when | First action |
|---|---|---|---|
| C-01 | burn rate vs plan | ≥ 1.25 × | find what runs outside the capacity calendar; stop it |
| C-02 | cost per productive GPU-hour | ≥ 1.25 × list price | fix the largest waste bucket (C-03) |
| C-03 | wasted share of main-run spend | ≥ 20% | the report lists each bucket in dollars |
| C-04 | cost of one incident | ≥ 3 × interval cost | missing emergency save, slow restore, or no spare |
| C-05 | instance outside Slurm | any | stop it now; find who started it (`support/cost/find_unmanaged.py`) |
| C-06 | budget days left vs training days left | ≤ 0.8 | cut allocations or run length; decide early |

---

## 6. Three walk-throughs

**4 a.m., page "[HIGH] Q-02 Main run held".**
`squeue` shows `SPECIAL_EXIT`, comment `V5 HELD (78): loss spike: held at step 5880. … Do: roll back …`. Nothing
bad was saved, so `latest.json` is from before the spike. Run `ckpt.py list`, pick the last step before 5880,
submit the rollback with `--skip 5 --branch b2`, cancel the held job. Time: ~5 min. Tell Team 05 in the morning.

**Page "[HIGH] H-01 fatal Xid on gpu-3".**
Nothing to do for the run: the node is drained, the main run saved and restarted on the spare (~1 min,
~0 steps lost). For the node: `sinfo -R` shows `v5:xid`; stop/start or replace the instance, then
`state=resume`. The pool now has no spare until it is back: do it the same day.

**Page "[HIGH] CK-03 2 failed saves in a row".**
Training still runs, but the last commit is getting old (CK-01 will follow). `checkpoint.failed` says
`cause: nvme_full` on gpu-2: clean `/nvme` there (or drain the node so the run moves). If the cause is
`UploadTimeout` or `IntegrityError`, look at S3 errors and network: this is money at risk, act now.

---

## 7. Dashboard suggestions (Team 08)

| Panel | From |
|---|---|
| Main run: state + comment, step, last commit age (CK-01), dollars at risk (CK-02) | `squeue`, `train.step`, `checkpoint.committed` |
| Goodput and waste buckets in dollars (Q-19, C-03) | `metrics.json` |
| Incidents table: kind, cause, detect / reschedule / restore seconds, steps lost | `report.md` incidents |
| Nodes: up / drained (with reason) / down / spare | `sinfo -R`, `node.drained` |
| Alerts open by severity | `alert.fired` |
| Budget used per account (Q-15) | `sshare`, `sacct` |

---

## 8. Files

| File | What it does |
|---|---|
| `catalog.yaml` | **the single source**: every metric with LOW / MEDIUM / HIGH thresholds, why it matters, the action, owner |
| `evaluate.py` | events → incidents, goodput, dollars, metric levels (`report.md`, `metrics.json`, `alerts.json`); `--render-md` writes the catalog page |
| `watch.py` | live: recomputes every 30 s, emits `alert.fired`, posts to `V5_ALERT_WEBHOOK` |
| `explain.py` | any code / cause / alert / reason → plain words + what to do; `--all` writes [codes_and_actions.md](../support/docs/codes_and_actions.md) |
| `../common/reasons.py` | the table behind `explain.py`, the Slurm job comment and the job-log banner |
| `../common/events.py` | the event format |
| `prices.yaml` | instance prices (assumptions, `checked: null`) for the dollar metrics |

In `support/`: `tests/test_monitoring.py` fails if the code can report something that has no explanation.

From `teams/07-infrastructure/`. Events are written on each node's own disk (`/var/log/v5/events`) and the log agent ships
them to `s3://<bucket>/events/`; `watch.py` reads a folder, so on EC2 point it at a synced copy
(`aws s3 sync s3://<bucket>/events /var/lib/v5-watch/events`). In Docker the folder is the shared `/s3/events`.

```bash
python metrics/watch.py --events /s3/events --run v5main --nodes 2 --interval-s 1800 --every 30
python metrics/evaluate.py --events /s3/events --out /s3/report --run v5main --nodes 2 --interval-s 1800
python metrics/evaluate.py --render-md ../support/docs/metrics_catalog.md   # after editing catalog.yaml
python metrics/explain.py --all ../support/docs/codes_and_actions.md        # after editing common/reasons.py
```

**Contract for a real trainer** (Team 05): exit 0 / 75 / 78 as in ADR 0001 §6, and call
`common.reasons.write_exit_note(code, cause, step, detail)` just before exiting, with a cause listed in
`common/reasons.py`. Without the note everything still works, but a held job can only say "no reason given".

---

## 9. Still open

- The on-call rota and the alert channel (lead + Team 08).
- Real thresholds for GPU metrics after the week-2 baseline.
- Which metrics Team 08 stores long-term, and for how long (proposal: events 90 days, then Glacier).
