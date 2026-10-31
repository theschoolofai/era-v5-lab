# Job queue (`queue/job_queue.py` and `slurm/`): who runs where, and how the main run restarts by itself

Decision record: [ADR 0002](../adr/0002-job-queue-slurm.md). Checkpoint side:
[../ckpt/README.md](../ckpt/README.md). Health side: [../health/README.md](../health/README.md).
Simulation results: [sim_results.md](../support/docs/sim_results.md).

> **In one paragraph.** A scheduler is the "front desk" of the cluster. Teams hand in jobs; it decides who runs
> where and when; it keeps the main run first; and when something breaks it puts the main run back in the queue
> so it restarts from the last checkpoint **without anyone typing a command**. We use **Slurm**, the standard for
> training clusters. The instructor asked us to prove it in a **Docker copy of the cluster** first, so we do
> not pay for GPUs while we debug the queue. The Docker copy uses **the same `slurm.conf`** as the cloud.

---

## How it works, step by step

Plain-words overview and the reasons behind each choice: [team briefing §3.2–3.3](../TEAM_BRIEFING.md#32-the-job-queue-slurm-and-three-exit-codes-adr-0002).
The wrapper is `queue/job_queue.py`; the Slurm files are in `slurm/`.

**A. The life of one job** (the main run or a team job)

```text
sbatch slurm/mainrun.sbatch            (team jobs: slurm/team_job.sbatch, with --time and a warning signal)
  │  Slurm checks the account, QOS, GPU share, per-job limits and budget
  │     over a per-job limit or budget → refused at once with the reason
  │     share in use / no free node     → waits (PENDING, with the reason)
  ▼
prolog (slurm/prolog.sh → health_check.py --mode prolog, ≤ 30 s)
  │     node fails → node drained, job back in the queue (not held), starts on a healthy node
  ▼
job script → job_queue.py run   (the wrapper; status comment "RUNNING (start #n)")
  │  srun starts one trainer per GPU; the wrapper waits, and passes a time-limit warning (SIGUSR1) on to them
  ▼
trainer exits → the wrapper turns the result into ONE of three codes:
  0   done                                     → Slurm: COMPLETED
  75  saved and stopped, or a one-off crash    → Slurm requeues (RequeueExit=75); back to "prolog"
  78  stop: NaN, loss spike, failed restore check, changed environment, other copy owns the run,
      or 3 crashes in 30 min (crash ledger)    → Slurm holds the job (RequeueExitHold=78)
  └─ in every case: a plain-words job comment ("what happened · already done · what you do") and events
     (job.started / ended / requeued / held)
```

**B. The crash-loop cap** (`crash_loop()`): every crash adds a line to `crashes.json` in the run's folder of the
shared store (not on a node, because the next attempt may start on another node). Three crashes within 30 minutes
turn the next 75 into 78. If the store cannot be reached the crash is still retried and an event says the cap is
not counting.

**C. Who gets the GPUs** (`slurm/setup_accounts.sh`, `slurm/slurm.conf`)

```text
QOS mainrun  (priority 1000, may preempt normal and debug)  ← the main run
QOS normal   (priority 10, 24 h max, GPUs per job ≤ share, ≤ 50 queued per team, refused at submit if over)
QOS debug    (priority 100, 30 min, 1 GPU, 1 running + 2 queued per user)
account per team: GPU share (GrpTRES gres/gpu), node cap, GPU-hour budget (GrpTRESMins; a job starts only if it fits)
preemption: team job gets SIGTERM → 60 s to save → exit 75 → back in the queue
```

**D. Background helpers**

| Helper | Where it runs | What it does |
|---|---|---|
| `job_queue.py spot-watch` (`v5-spot-watch.service`) | every GPU node | asks for a spot warning every 5 s (`V5_SPOT_NOTICE_CMD`); on a warning drains the node and tells its jobs to save |
| `job_queue.py keep-spare` (`v5-keep-spare.timer`) | controller, every minute | keeps one free GPU node powered up as the hot spare |
| `job_queue.py drain "<reason>"` | anywhere | takes a node out of service; its jobs save and move |
| `job_queue.py status` | anywhere | every job and drained node, in plain words |
| `slurm/backup_db.sh` | database host, daily | dumps the accounting database and proves the dump restores |

---


## 1. Why Slurm, and why on our own cloud instances

V4 had **no scheduler**: GPUs from many student accounts, jobs started by hand, a cluster idle for 3 days, and
restarts typed by hand.

| Option | Why not / why |
|---|---|
| No scheduler (V4) | no queue, no fairness, no automatic restart |
| managed Kubernetes | multi-node GPU training needs add-ons; many extra layers |
| the provider's managed Slurm service | its own config layer between us and Slurm; harder to copy in Docker. **Our fallback** if running Slurm ourselves is too much work |
| A managed cloud batch service | weak for multi-node jobs, no fair-share |
| **Self-managed Slurm on cloud nodes** ✅ | full control; the norm for LLM training; **the Docker test runs the same file** |

---

## 2. The cluster at a glance

```text
                     ┌──────────────── head (small CPU instances) ────────────────┐
  teams ── sbatch ─► │ slurmctld (primary)   slurmctld2 (backup)   slurmdbd + MariaDB │
  (via svc user)     └───────────────┬────────────────────────────────────────────┘
                                     │ schedules
          ┌──────────────────────────┼───────────────────────────┐
          ▼                          ▼                           ▼
   gpu-1  gpu-2  … (main run)     gpu-N (hot spare:        eval / cpu nodes
   8 GPUs each, fast network      runs team jobs that       (evaluation, data,
                                  the main run can take)    retention, export)
                                     │
                          checkpoints, logs, events ──► S3
```

- **Main run** on on-demand or a reserved capacity booking, **never spot**, plus **one hot spare** node.
- The **hot spare is not idle**: it runs team jobs that the main run preempts when it needs the node.
- **Idle nodes are stopped** (`State=CLOUD`, `SuspendTime=600`), except exactly one spare, which
  `job_queue.py keep-spare` names every minute (and boots, if none is free). This replaces V4's "idle alarm".
- **GPUs are a counted resource (gres)**. A job that asks `--gpus-per-node=8` gets exactly 8, sees only those
  (`CUDA_VISIBLE_DEVICES`), and its GPU-hours are recorded against its account.

### Partitions (queues)

| Partition | For |
|---|---|
| `gpu` | training, whole nodes only |
| `eval` | cheaper GPU nodes for evaluation (never the training nodes) |
| `debug` | 30-minute limit |
| `cpu` | data, tokenizer, retention and export jobs |

---

## 3. Who gets the GPUs: accounts, priority, budgets

```text
root
├── mainrun   QOS=mainrun  Priority 1000, can preempt "normal", no time limit
└── teams     QOS=normal   Priority 10, preemptible (60 s grace to save, then requeued)
    ├── data  tokenizer  ke2  arch  perf  infra  monitoring  eval  posttrain  release  quant
```

In simple words:

1. **Every job is charged to an account.** A job with no valid account is **rejected**.
2. **The main run outranks everyone.** If it needs a node, a team job on that node gets SIGTERM, has 60 s to
   save, and goes back into the queue.
3. **Teams share the rest fairly** (fair-share): a team that used a lot recently waits behind one that used little.
4. **No team can hold more than 2 nodes** (`GrpTRES=node=2`).
5. **Each team has a GPU-hour budget** (`GrpTRESMins`). Alerts at 50 / 75 / 90%, hard stop at 100%.

Students never get SSH or cloud keys. The submit system calls `sbatch` with a team account through one service
user (`svc`).

```bash
# a team job (scaling ladder, benchmark, eval)
sbatch --account=arch --export=ALL,RUN_ID=ladder-1 slurm/team_job.sbatch
# the main run (one script for the first start and every restart)
sbatch slurm/mainrun.sbatch
```

---

## 4. The restart contract (the most important part)

```text
 trainer exits ──► job_queue.py (wrapper) ──► exit code ──► Slurm
     0  done                                  0  ─────────► COMPLETED
     75 saved, run me again                   75 ─────────► requeue (RequeueExit=75) ─► restarts from latest.json
     78 NaN / spike / failed checks           78 ─────────► HOLD    (RequeueExitHold=78) ─► page a person
     1, 137, 139… (crash)                     75, unless 3 crashes in 30 min → 78
```

- **One script** (`mainrun.sbatch`) for every start. It always resumes from `latest.json`, so a restart needs no
  human input.
- **The wrapper** (`job_queue.py run`) maps every trainer outcome to 0, 75 or 78, applies the **crash-loop cap**
  (3 crashes in 30 min → hold: retrying a broken job just burns money), and writes `job.started / ended /
  requeued / held` events. The crash times are one object, `crashes.json`, in the run's S3 folder: a requeued
  job starts on any node, so the count cannot live on a node's disk, and S3 cannot append to a file.
- **Every job says why it stopped, in plain words**, where people look: the Slurm job comment
  (`squeue -o "%.10i %.12T %.20r %k"`), a banner at the end of the job log, and the events. For example
  `V5 HELD (78): loss spike: held at step 5880. Explain: python metrics/explain.py loss_spike. Do: roll back …`.
  The trainer leaves a short exit note (`common.reasons.write_exit_note`); the words come from
  `common/reasons.py`. Monitoring guide: [../metrics/README.md](../metrics/README.md).
- **Signals.** The trainer treats SIGUSR1 and SIGTERM the same: save, wait for the commit, exit 75.

| Who sends it | When | What the job loses |
|---|---|---|
| Slurm (SIGTERM) | a team job is preempted by the main run | ~0 (it saves in its 60 s grace) |
| `job_queue.py spot-watch` (SIGUSR1) | cloud's 2-minute spot warning | ~0 |
| health check (SIGUSR1) | the node is sick | ~0 |
| nobody (no warning) | process killed, node lost | the work since the last checkpoint |

- A node that stops answering for **30 s** (`SlurmdTimeout`) is marked DOWN and its job is requeued.

### Why a restart takes ~90 s

Slurm will not restart a requeued job until the old job's launch credential has expired (`cred_expire` + 1 s;
the default is ~121 s). We set **`AuthInfo=cred_expire=60`**: measured ~90 s from exit to running (run 11),
every requeue succeeded. Week 1 used 30 s (~52 s), but the credential must also outlive the prolog (budget 30 s),
so the review asked for margin: 60 s is twice the prolog budget.

> **Lesson from simulation run 7.** We first forced an immediate restart (~4 s). Sometimes the job started
> while the old credential was still valid; Slurm killed it ("Job credential revoked") and marked it
> **FAILED**: the main run was lost. We removed that trick. ~90 s per restart (~$23 on 8 nodes at assumed
> prices) is the price of never losing the run.

### When there are not enough nodes

If more nodes fail than there are spares, the main run **waits** (pending), and alert Q-01 pages after 10 min.
It does **not** shrink by itself: fewer GPUs change speed and are not bit-equal, so a person decides. The
operator can restart it on fewer nodes (`sbatch --nodes=1 …`); the rollback drill tests this.

---

## 5. Keeping the control plane alive

| Risk | Protection | Tested |
|---|---|---|
| controller (`slurmctld`) dies | backup `slurmctld2` takes over (shared state on a shared file system); running jobs keep training | yes: takeover in 82 s, training never stopped |
| accounting database lost | `backup_db.sh` dumps it daily to S3; a backup **counts only after a test restore** with the same tables | yes: 31 of 31 tables restored |
| software upgrade mid-run | only at a checkpoint: emergency save → roll nodes → requeue with `--allow-env-change` (logged). Slurm order: `slurmdbd` → `slurmctld` → `slurmd` | written down (ADR 0002 §11) |

---

## 6. Files

### `queue/job_queue.py`: the queue logic, in one Python file

| Command | What it does |
|---|---|
| `job_queue.py run -- <srun args> -- <trainer args>` | **the job wrapper** every sbatch script calls: starts the trainer (`V5_TRAIN_SCRIPT`), maps its outcome to 0 / 75 / 78, applies the crash-loop cap, writes the plain-words job comment, log banner and `job.*` events |
| `job_queue.py spot-watch` | runs on every node: polls the spot warning (the instance metadata service) every 5 s; drains the node and asks its jobs to save |
| `job_queue.py drain <reason> [--node N]` | takes a node out of service; its jobs save and move (also used by the health check) |
| `job_queue.py status` | every job and every drained node, each explained in plain words |
| `job_queue.py keep-spare` | controller, every minute (`slurm/v5-keep-spare.timer`): sets `SuspendExcNodes` to the spare node by name; powers one up if no GPU node is free |

It is not called `queue.py` on purpose: that name would hide Python's own `queue` module, which boto3 and
threads use.

### `slurm/`: Slurm configuration and job scripts (the Docker test uses the same files where they match)

| File | What it does |
|---|---|
| `slurm.conf` | **shared** by Docker and Cloud nodes: controllers, accounting, priorities, preemption, requeue codes, health hooks, gres |
| `nodes.cloud.conf` | the cloud node and partition lines (`State=CLOUD`, the spare named by `keep-spare`) |
| `v5-keep-spare.service`, `.timer` | systemd units on the controller: run `job_queue.py keep-spare` every minute |
| `site.cloud.conf`, `cgroup.cloud.conf`, `gres.cloud.conf` | the cloud only: cgroup enforcement (a job uses only its own cores, memory, GPUs), GPU discovery through NVML |
| `mainrun.sbatch` | the main-run job: account `mainrun`, 2 nodes × 8 GPUs, `--requeue`, sets the deterministic env (`OMP_NUM_THREADS=1`) and the NCCL flight recorder |
| `team_job.sbatch` | a preemptible team job |
| `prolog.sh` | quick health check before a job starts on a node (see health README) |
| `epilog.sh` | cleans temporary restore files on NVMe after a job |
| `healthcheck.sh` | Slurm's `HealthCheckProgram`, every 30 s |
| `setup_accounts.sh` | creates accounts, QOS, limits and the `svc` user |
| `backup_db.sh` | dump and `--verify-latest` the accounting database |

### `support/simulation/slurm-docker/` (optional: the test cluster on a laptop)

| File | What it does |
|---|---|
| `docker-compose.yml` | MariaDB, `slurmdbd`, `slurmctld` + `slurmctld2`, S3 emulator (`s3emu`, moto), nodes `c1–c3` ("GPU") and `c4` (eval/CPU) |
| `Dockerfile` | Ubuntu 24.04, Slurm 23.11, torch 2.5.1 CPU, boto3, moto |
| `entrypoint.sh` | starts each role; creates placeholder GPU device files `/dev/v5gpu0-1` |
| `nodes.conf`, `gres.conf`, `site.conf`, `cgroup.conf` | the Docker versions of the four files that differ from the cloud |
| `slurmdbd.conf` | accounting daemon config (test-only password) |

**Docker vs the cloud, the only differences:** CPU instead of GPU (gloo instead of NCCL); 2 placeholder GPUs per node
(allocation and accounting only, no computation); no cgroup enforcement; no Pyxis containers; no power saving;
no the fast network. Everything else (requeue, preemption, accounts, budgets, health drain, failover, S3 code path) is the
real thing.

---

## 7. Run it yourself

From `teams/07-infrastructure`, with Docker Desktop running:

```bash
docker compose -f support/simulation/slurm-docker/docker-compose.yml build slurmdbd   # once, ~5 min
python3 support/simulation/run_sim.py                    # every drill, ~25 min; ends with "N/N drills passed"
python3 support/simulation/run_sim.py --keep-up          # same, but leave the cluster running to poke at it
```

On a live cluster, `python /opt/v5/queue/job_queue.py status` shows every job and drained node in
plain words. With the test cluster up, open a shell on the controller
(`docker compose -f support/simulation/slurm-docker/docker-compose.yml exec slurmctld bash`) and try:

```bash
sinfo                                  # nodes and their state (idle / alloc / drain / down)
squeue                                 # what is running and pending, and why pending
scontrol show job <id>                 # one job: restarts, reason, allocated GPUs (AllocTRES)
sacct -a -X -D -o jobid,account,state,elapsed,alloctres   # history incl. every requeue (-D)
sshare -a                              # fair-share per account
sacctmgr show assoc format=account,user,qos,grptres,grptresmins
scontrol ping                          # which controller is in charge
```

---

## 8. What the simulation proved (run 9, 31 of 31 drills)

| Drill | What happened | Recovery time (MTTR p50) | Work lost |
|---|---|---|---|
| kill a training process | wrapper → 75 → requeued → restored | 50 s (3 runs) | 24–45 steps |
| preemption signal | emergency save, 75, requeued | 58 s (3 runs) | 0 |
| spot notice | node drained, save, moved to the spare | 57 s | 0 |
| health fail | drained within one interval, save, moved | 88 s | 0 |
| frozen process (hang) | watchdog at 20 s → 75 → restart | 56 s | 44 steps |
| node unplugged | DOWN after ~30 s, requeued on remaining nodes | 88 s | 24 steps |
| two nodes down, one spare | main run waits (no crash loop), recovers on repair | 58 s after repair | — |
| controller stopped | backup in control in 82 s | — | 0 |
| team jobs vs main run | team jobs saved and requeued; main run started | — | — |
| no account | rejected | — | — |
| GPU allocation | `gres/gpu=4` allocated; over-asking refused | — | — |
| crash loop | requeued twice, then held | — | — |
| budget exceeded | next job pending with the budget reason | — | — |
| fair share | heavy account gets a lower factor | — | — |
| DB backup | 31 of 31 tables restored | — | — |

Low "goodput" in the simulation report is **by design**: we inject a fault every ~30 s, while a real run sees
one every few hours. What matters is the time of each step (detect, reschedule, restore), which
`support/cost/cost_model.py --measured` projects onto real failure rates.

---

## 9. Metrics to watch

Full list: Q-01 … Q-21 in [metrics_catalog.md](../support/docs/metrics_catalog.md). These page someone now (HIGH):

| ID | Metric | HIGH when | What to do |
|---|---|---|---|
| Q-01 | main run not running | pending ≥ 10 min | `squeue` reason: no nodes? budget? repair or add a node |
| Q-02 | main run held | any | read the 78 cause (NaN, spike, crash loop); roll back or fix |
| Q-03 | reschedule time | ≥ 10 min | spare missing or prolog failing |
| Q-05 | interruptions | ≥ 10 per day | find the common cause in the incident records |
| Q-06 | idle GPU node-hours | ≥ 4 per day | power saving not working; nodes paid for nothing |
| Q-07 | allocated but not stepping | ≥ 15 min | stuck in restore or data wait |
| Q-09 | drained nodes | ≥ 3 | hardware wave: replace nodes |
| Q-10 | node replacement time | ≥ 15 min | cloud capacity, node image start |
| Q-11 | slurmctld down | ≥ 60 s | check the backup took over |
| Q-15 | account budget used | ≥ 90% | talk to the team and the lead |
| Q-17 | clock offset | ≥ 500 ms | chrony on the node |
| Q-19 | goodput | ≤ 80% | look at the waste buckets |
| Q-20 | MTTR | ≥ 60 min | which restart step is slow |

---

## 10. Still open

- GPU type and count; reserved capacity booking or on-demand; real prices.
- cloud account: cloud roles, bucket names, the fast network, Pyxis/Enroot, power-saving scripts (`node_suspend.sh` /
  `node_resume.sh` are week-2 work).
- The submit system's contract (does it call `sbatch` with an account?).
- On-call rota: who acts on a HIGH alert at 4 a.m.
- Capacity calendar for weeks 2–4.

---

## 11. Words used here

| Word | Meaning |
|---|---|
| `slurmctld` | the controller: the brain that schedules |
| `slurmd` | the agent on each node that runs jobs |
| `slurmdbd` | accounting: accounts, budgets, job history |
| partition | a queue of nodes |
| QOS | quality of service: priority and preemption rules |
| preempt | take a node from a lower-priority job (it saves first) |
| requeue | put a job back in the queue to start again |
| hold | keep a job in the queue but do not start it until a person releases it |
| drain | "no new jobs on this node" |
| gres | a counted resource such as GPUs |
| fair-share | priority goes down the more an account used recently |
| MTTR | mean time to recover: fault → training again |
| goodput | share of paid time that trained the model |
