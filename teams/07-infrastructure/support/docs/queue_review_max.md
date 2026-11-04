# Queue deep review: uz9ai's repo next to ours and millermuttu's

> **Superseded for decisions by [team07_merge_plan.md](team07_merge_plan.md)** (pradeep-kumar-gs + millermuttu + uz9ai in one
> page). This file stays as the detailed review behind it.

Reviewed: `uz9ai/queue` (branch `main`, last push 28 Oct 2026), the "X" source (`max_queue-main`) in the G7
review. Compared with this repo (`fd0f59b`/`38538cb`, "P") and millermuttu's `millermuttu/era-v5-lab`
(`07-infrastructure`, "M"). Written 30 Oct 2026. Target, as agreed: **the TSAI shared GPU node(s)**.
Companion to [merge_plan.md](merge_plan.md); this file goes deeper on the queue
only and updates that plan's queue section.

> **In simple words.** uz9ai built the most careful *real-machine* Slurm setup of the three: one config file
> (`cluster.toml`) that is checked before anything is installed, an installer that can run twice safely, exact
> user/account/QOS limits, and tests that save evidence an admin can read. It ran on real cloud GPU nodes. Its
> gaps are what happens *after* something goes wrong: a crash is never retried, a NaN is not held, and health
> checks are not wired in yet. Ours is strongest exactly there. The best queue takes **uz9ai's installer, config,
> limits and evidence**, **our failure handling** (exit codes, crash loop, holds, auto-drain, launch order), and
> **millermuttu's single-node config** for the shared node.

## How this was checked

- Every text file of uz9ai's repo was read (31 files: `queue_design.md`, `cluster/` installer, `team7config`,
  tests, `train.py`, `eval.py`). Two screenshots were looked at as evidence.
- **Nothing of uz9ai's was run here** (no cloud, and running downloaded code is blocked on this machine). His
  evidence: the screenshot `imgs/train_test1.png` shows `test_requeue.py` on `train-01`, 28 Oct 07:26 UTC:
  **T12 and T12b PASS**, each job `COMPLETED`, `Restarts=3`, 3 `REQUEUED` records in `sacct`. The README links
  videos of the install and of training/eval jobs. The `test_limits.py` (T01–T11) result is not in the repo.
- Note: `cluster/README.md` §10 still says "Not yet run on cloud nodes". The screenshot shows it has been; that line is
  out of date.

## Size and shape

| | uz9ai (X) | pradeep-kumar-gs (P) | millermuttu (M) |
|---|---|---|---|
| Queue code | ~4,260 lines: installer (stdlib only), `team7config` loader/validator, tests | `job_queue.py` + `slurm/` scripts + `launch.sh` (~1,400 lines) | `slurm.conf` + site files + `test.sh` (~250 lines) |
| Design doc | `queue_design.md`: 15 sections, **10 ADRs**, 18-item test plan, admin sign-off box | ADR 0002 + `queue/README.md` | README |
| Where it runs | real Cloud nodes: `ctl-01` (CPU) + `train-01` + `eval-01` (one GPU each) | Docker Slurm (CPU, fake GPUs); cloud files written, not run | Docker Slurm (fake GPUs); `node/` files for the shared node, not run |
| Real-hardware evidence | **yes**: T12/T12b on cloud nodes, training on a 1-GPU node (screenshots) | none yet (Kaggle pending) | none yet |
| Docker / CI | **no** (ADR-08: real nodes only) | yes, 33 drills | yes, `test.sh` ~90 s |

## What uz9ai does better than both of us

1. **One validated config for everything.** `cluster.toml` describes hosts, Slurm, partitions, QOS, accounts,
   users, storage, checkpoints and job templates. `team7config` validates it (≈460 lines of checks with clear
   messages) before anything is touched, and the **same file is installed on every host** so training code
   reads the same requeue code, signal lead and paths Slurm was configured with (`team7-config get …`). Ours
   spreads these over `slurm.conf`, `node.env`, `setup_accounts.sh` and job scripts.
2. **Installer that is safe to rerun and can be previewed.** `install.sh validate | render | --dry-run |
   --only/--skip`, every step checks state first; `apply` reconciles QOS/accounts/users and **never deletes**,
   only reports extras; it refuses to run on the wrong host (IP, GPU count, GPU model) and stops if node sizes
   differ from `slurmd -C`. Ours has `launch.sh` (start order, checks) but no installer.
3. **Configless Slurm** (`SlurmctldParameters=enable_configless`): nodes fetch `slurm.conf` from the controller,
   so a node can never run a stale config. Ours copies the files to each node (and `launch.sh` only compares a
   code fingerprint).
4. **Tight, tested limits.** Per-QOS `MaxWall`, `MaxTRESPerJob=gres/gpu=G`, `MaxJobsPA=1` (one training run
   per team), `MaxJobsPU`, `MaxSubmitJobsPU`; a `debug` QOS (30 min, 1 GPU, higher priority) instead of a debug
   partition; `CR_Core_Memory`. Tests T01–T11 check each one, including the exact pending reason
   (`AssocGrpGRES`, `QOSMaxGRESPerJob`, `QOSMaxWallDurationPerJobLimit`, MaxJobs) and that a user cannot cancel
   another's job. Ours has accounts, a node cap, GPU-hour budgets and fair share, but **no MaxWall, MaxJobs or
   MaxSubmit limits** and no debug QOS.
5. **The `limits-test` partition trick.** A partition kept `INACTIVE`, switched on only to prove GPU limits
   across two 1-GPU nodes, then restored from the TOML even if a test fails. A clean way to test a limit the
   normal layout never reaches.
6. **Evidence an admin can check.** Every test writes `evidence/<timestamp>/`: each command, the user who ran
   it, its output, `scontrol`/`sacct` snapshots and a `summary.md`; expected reason strings come from the Slurm
   docs and a different string is recorded, not hidden. This is exactly what the G7 review asks for ("fresh
   per-test evidence, not printed PASS strings").
7. **The DeepSpeed launcher analysis (ADR-10).** Checked in DeepSpeed's source: `launch.py`/`runner.py` do not
   handle `SIGUSR1`, so a signalled launcher dies and kills ranks mid-save; and `launch.py` kills all ranks
   when one exits non-zero, so ranks must **barrier before exiting 75**. Hence `--signal=B:USR1@<lead>`
   (batch shell only) and forwarding to rank PIDs. Neither of us had looked at this.
8. **Time limits with self-requeue.** `--signal=B:USR1@300` before `MaxWall`, save, exit 75, requeue with the
   same job ID; `lead ≥ 2 × save time + 60 s`. Ours gives the main run `MaxTime=INFINITE` and uses SIGUSR1 only
   for preemption, spot and drains.
9. **Pinned training environment.** `pyenv/pyproject.toml` + `uv.lock` (torch 2.14.1+cu126, DeepSpeed 0.19.8),
   built before `slurmd` starts so no job lands on a node without it; notes on CUDA 13 node image vs cu126 wheels and
   on not building DeepSpeed ops across a CUDA major mismatch. Ours pins versions only in the Docker image.
10. **Secrets handled properly.** Munge key from a file copied by hand or from **the cloud parameter store**
    (SecureString), DB password generated on the controller and never leaving it, `cluster.toml` holds no
    secrets and is committed.
11. **Real checkpoint hygiene in `train.py`.** sha256 manifest, `fsync`, atomic rename, `COMPLETE` last, and on
    resume **skips a corrupt checkpoint and uses the previous valid one** (millermuttu's does not).

## Problems found in uz9ai's work

| # | Problem | Why it matters | Fix (where it comes from) |
|---|---|---|---|
| X1 | **A crash is never retried.** Any exit other than 0 or 75 ends `FAILED` (§8, §11) | An NCCL error, a CUDA fault or an OOM kill at 3 a.m. stops the run until a person resubmits; GPU hours idle all night | P's wrapper: one-off crash → 75 (requeue), **3 crashes in 30 min → hold** (78) |
| X2 | **No "hold for a person" path.** NaN, loss spike, failed restore checks or a changed environment all end as plain `FAILED`, or would be retried by hand | The person has to read logs to know if a retry is safe | P's exit 78 + `RequeueExitHold` + job comment saying what happened and what to do |
| X3 | **Health not wired in.** `[health].enabled = false`; the prolog and timer call `health/launch.sh --quick`, which does not exist (millermuttu's `launch.sh` is an sbatch job with no `--quick`) | No node is checked before jobs today | P's `health_check.py --mode prolog/periodic/full` already has this interface; point uz9ai's `[health]` at it |
| X4 | **SIGUSR1 can be lost** if it arrives before the ranks wrote their PID files (start of a segment); the job is then killed at the limit after `KillWait` | Work since the last periodic save is lost, silently | Log a warning when no PID file exists, and send the signal again 30 s later; or use P's launch shape (below), which needs no PID files |
| X5 | Barrier-before-exit and `CUDA_VISIBLE_DEVICES` through the launcher are untested on more than one GPU (uz9ai says so) | The multi-GPU node is the real target | Run T12b on the shared node with 8 GPUs (week 2) |
| X6 | **Layout assumes separate train and eval nodes** and a separate controller host (ADR-01, ADR-04) | On the shared node there is one host: partitions per node collapse, and the controller shares the node's fate | Single-node layout from M's `node/`; uz9ai's GPU limits (`GrpTRES`, `MaxTRESPerJob`) become the real limits, as his own ADR-01 note predicts |
| X7 | No preemption (ADR-07); P preempts team jobs for the main run | Mutually exclusive; the G7 review flagged it | Team decision (question 2 in the merge plan). On a shared node with team jobs next to the main run, P's QoS preemption is the safer default |
| X8 | Retention inside the training job (`keep` deletes old folders) | On S3 the training role should not be able to delete | P's separate retention job/role |
| X9 | Tests need root on real hosts; nothing runs in CI | Every change needs cloud time to check | Port T01–T11 to run against the Docker cluster too (same `sacctmgr`/`sbatch` calls) |
| X10 | `DenyOnLimit` not set: an over-limit job pends instead of being refused at submit | Users wait for a job that can never start (T09 records which one happens, good) | Decide per QOS; set `Flags=DenyOnLimit` where a pending job is useless (MaxWall, MaxTRESPerJob) |

## Launch shape: the three options

| | Shape | SIGUSR1 reaches | Exit code reaches Slurm | Tested |
|---|---|---|---|---|
| uz9ai | batch shell runs `deepspeed` launcher; shell forwards SIGUSR1 to rank PIDs from files | ranks only (by PID files) | launcher passes the rank's 75 through | the cloud, 1 GPU (T12b) |
| millermuttu | `srun` 1 task/node → `torchrun` (c10d rendezvous, new id per restart) | torchrun agent (forwards SIGTERM/SIGINT; SIGUSR1 handling depends on version) | agent exit code | Docker, 2 nodes × 2 CPU ranks |
| pradeep-kumar-gs | `srun` one task per GPU running the trainer directly (uz9ai's ADR-10 **alternative b**); `job_queue.py` wraps `srun` | every rank directly (Slurm signals the step) | wrapper maps to 0/75/78 | Docker, 2 nodes × 2 ranks, the DeepSpeed trainer starts the same way (`deepspeed.initialize` from Slurm's variables, no launcher) |

**Keep P's shape** as the default: it has no launcher to protect, and our DeepSpeed simulation already proves
uz9ai's fallback (b) works. Keep **uz9ai's ADR-10 text** in the ADR as the reason, and his PID-file template as the
documented alternative if Team 05 insists on the `deepspeed` launcher.

## Queue verdict, area by area (supersedes §2 of the merge plan)

| Area | Keep | From |
|---|---|---|
| Config source of truth | `cluster.toml` + `team7config` validation, installed on every host | **X** |
| Installing a host | `install.sh controller/node/apply/verify`, `--dry-run`, never-delete `apply` | **X**, with a single-host mode for the shared node (controller + node on one host; today the IP checks assume separate hosts) |
| Starting / checking the stack | `launch.sh` order and checks (munge key, DB backup + restore, controllers, health, store probe, submit) | **P**, calling X's installer for anything missing |
| Slurm config distribution | configless (`enable_configless`) | **X** |
| Single-node layout | `node/` site/gres/cgroup files | **M**, rendered from `cluster.toml` |
| Accounts and users | per-team accounts with GPU shares (`GrpTRES=gres/gpu`), real users with fixed UIDs and SSH keys | **X**'s reconcile code, **M**'s GPU shares and team list |
| QOS limits | `MaxWall`, `MaxTRESPerJob`, `MaxJobsPA=1`, `MaxSubmitJobsPU`, `debug` QOS | **X** |
| Main-run protection | `mainrun` QoS with requeue preemption and grace | **P** (if teams share the node; else park) |
| Budgets and fair share | `GrpTRESMins` GPU-hour budgets, fair share, accounting per team | **P** (+ X's priority weights) |
| Exit-code contract | 0 / 75 / 78, crash loop → hold, job comment in plain words | **P** |
| Time limits | `--signal=B:USR1@<lead>` before `MaxWall`, self-requeue, `lead ≥ 2 × save + 60 s` | **X**, added to P's job scripts |
| Launch shape | `srun` per rank (no launcher) | **P**; X's ADR-10 analysis kept as the reason |
| Health hooks | prolog + timer + full at bring-up; drain by `scontrol` from the script | **P's** `health_check.py` (X's design and P agree on every rule); M's checks inside it |
| Pinned environment | `uv.lock` for the node venv | **X** |
| Secrets | munge key via the cloud session manager or hand copy; DB password generated on host | **X** |
| Tests | X's T01–T18 as the acceptance list with **evidence folders**; P's drills for failures; M's `test.sh` as 90-second smoke | **all three** |
| Design doc | X's `queue_design.md` structure (ADRs with alternatives, test plan, sign-off) merged into ADR 0002 | **X** layout, P/M content |

## Additions to the merge plan's work list

| # | Task | From | Size |
|---|---|---|---|
| Q1 | Bring `team7config` + `cluster.toml` in; render `slurm.conf`, `node/` files and `accounts` from it | X | M |
| Q2 | Single-host mode in the installer (controller and node on the shared node) | X + M | M |
| Q3 | QOS limits (`MaxWall`, `MaxJobsPA`, `MaxSubmitJobsPU`, `MaxTRESPerJob`, `debug`) and `--signal=B:USR1@<lead>` in our job scripts | X → P | S |
| Q4 | `job_queue.py` keeps the 0/75/78 contract inside X's templates (fixes X1, X2) | P → X | S |
| Q5 | `[health]` points at `health_check.py --mode prolog/periodic` (fixes X3) | P → X | S |
| Q6 | Evidence folders for drills and smoke tests (`evidence/<test>/commands, outputs, summary.md`) | X → P | M |
| Q7 | Port T01–T11 to the Docker cluster so they run without the cloud (fixes X9) | X → P | M |
| Q8 | `uv.lock` for the node venv; Docker image installs from the same lock | X | S |

## Questions for uz9ai

1. Can `install.sh` run controller and node on **one host**? (IP checks, configless with `SlurmctldHost` =
   the node itself.)
2. Was `test_limits.py` (T01–T11) run on cloud nodes, and is the evidence folder available?
3. Would you accept crash → requeue with a crash-loop hold (X1) instead of crash → `FAILED`?
4. Should Team 05's trainer use the `deepspeed` launcher at all, given that `srun` per rank works with DeepSpeed
   in our simulation?
