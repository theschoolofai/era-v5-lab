# Runbook: restoring a run from its last checkpoint

Second version. It covers restore (the steps and the restore time) and restart after a killed trainer
(`ckpt/supervisor.py`, `results/restart_cpu.txt`). The restart on the lab node, the 2-GPU restore and the queue
rules (not yet merged) are marked **pending** below.

> **In simple words.** Machines break and runs stop. Every few hundred steps the run saves a *checkpoint*: a
> copy of everything the next step needs. To restore, the new copy of the run reads the newest good checkpoint,
> **proves** it is exactly what was saved, and carries on as if nothing had happened. Most of the time Slurm does
> this by itself (exit code 75) and nobody has to act. You act only when a job is **held (exit 78)**, when an
> alert says a restore check failed (**CK-05**) or the restore is slow (**CK-13**), or when you roll back on purpose.

Commands run from `teams/07-infrastructure/` and use the paths of the production layout (`/opt/v5/...` in
the [user guide](../USER_GUIDE.md)). `<run>` is the run's checkpoint folder: `<remote_root>/<run_id>`, a folder
on the shared file system or `s3://bucket/prefix/run_id`.

Every number in this file is marked **measured** (run by us, with the command and machine named),
**computed** (arithmetic on measured numbers or on an input) or **reference** (taken from another document).

---

## 1. When to restore

| You see | What it means | Do |
|---|---|---|
| exit **75**, job back in the queue (`REQUEUED`, `BeginTime`) | a safe stop: preemption, spot notice, health drain, time limit, one crash | **nothing.** The next attempt restores by itself (section 3). |
| the trainer was killed (SIGKILL, out of memory, lost node) and **there is no Slurm** (one machine, the TSAI runner, the CPU tests) | nothing restarts it unless a supervisor is running | start it under `ckpt/supervisor.py`, section 5.1 |
| exit **78**, `squeue` shows `SPECIAL_EXIT` or `JobHeldUser` | stopped on purpose; retrying alone would not help | read the cause (section 2), then use the table in section 6 |
| alert **CK-05** (a restore check failed) | the loaded state was not the saved state; the job fell back to the previous commit | section 6, `RestoreCheckError`; do not continue on that checkpoint |
| alert **CK-13** (restore time) | the restart took long | section 7 |
| NaN or loss spike | no checkpoint was written after it; job held | roll back, section 5 |
| you want to prove a restore works (new code, new image, new store) | a rehearsal | section 4 |

## 2. Look before you act

```bash
python queue/job_queue.py status                   # jobs and drained nodes, plain words
scontrol show job <id> | grep Comment              # a held job names its cause here
python ckpt/ckpt.py list --run <run> | tail -3     # the newest committed checkpoints
python ckpt/ckpt.py verify --run <run>             # re-check every file against its sha256
python metrics/explain.py <cause>                  # what a cause means and what to do
```

`ckpt.py list` reads `commits.jsonl`, the ordered list of commits. It never lists folders: a folder with no
`MANIFEST.json` is a half-written save and is not a checkpoint.

## 3. What a restore does, in order

This happens automatically at the start of every attempt (`Checkpointer.restore` in `ckpt/ckpt.py`; the main
run's script is `slurm/mainrun.sbatch`, which always resumes from `latest.json`). You only read it, to know what
a log line means.

| # | Step | If it fails |
|---|---|---|
| 1 | **Claim the run.** Write `latest.json` with `epoch + 1`, only if nobody changed it since it was read. From now on an older copy of this run cannot commit (fencing). | another attempt owns the run: `FencedError`, exit 78 |
| 2 | **Pick candidates.** `latest.json` first, then `commits.jsonl` newest to oldest. | none committed: a fresh start at step 0 |
| 3 | **Checksums.** Every file listed in `MANIFEST.json` against its sha256. | `IntegrityError`: use the previous commit |
| 4 | **Environment.** image, torch/CUDA/NCCL, config sha, tokenizer, embedding policy, `OMP_NUM_THREADS` against the manifest. | `EnvMismatchError`, exit 78 |
| 5 | **Download** to the node's local NVMe, each copy checked again. | use the previous commit |
| 6 | **Strict keys.** Every tensor name, shape and dtype matches the model. | `StrictLoadError`, exit 78 |
| 7 | **Load** weights, optimizer, random generators and the data position (resharded if the GPU count changed). | `DataManifestError` or `ReshardError`, exit 78 |
| 8 | **The four proofs** (below). | `RestoreCheckError`: use the previous commit |

The four proofs. **All must pass**, or the checkpoint is not used:

| Proof | Rule |
|---|---|
| State digest | a fingerprint of every logical tensor equals the saved one (same at any number of GPUs) |
| Probe loss | the loss on one fixed batch is **bit-equal** to the saved value for this device class |
| Next batch | the hash of the next data batch equals the saved one |
| Frozen tensors | each frozen tensor (for example the KE2 tables) has its saved fingerprint |

If every candidate fails, restore stops with `CheckpointError` (exit 78): nothing usable is left.

### How to tell it worked

- Rank 0 writes one `restore.done` event (the events folder is `V5_EVENTS_DIR`; the main run uses
  `/var/log/v5/events`). Check `step` is the step you expect, `resharded` is `false` unless the GPU count
  changed on purpose, and `branch` is the branch you expect.
- There is **no** `restore.failed` event for the same attempt. If there is one, the run fell back to an older
  checkpoint: see `RestoreCheckError` and `IntegrityError` in section 6.
- `restore.done` also carries the time of each phase: `verify_s`, `download_s`, `load_s`, `checks_s`, `restore_s`
  (section 7 uses them).

## 4. Rehearse a restore (no GPU, no network, about 15 s)

`jobs/restore_test/restore_test.py` trains Team 05's tiny MoE twice (run A without a stop, run B stopped at
step 150), restores B from its step-100 checkpoint with our `Checkpointer`, and compares steps 101 to 200.

```bash
pip install -r teams/04-ke2/src/requirements.txt          # torch 2.14.1 or newer
python jobs/restore_test/restore_test.py                  # 1 CPU process
python jobs/restore_test/restore_test.py --nproc 2        # 2 CPU processes (gloo)
python jobs/restore_test/restore_test.py --nproc 2 --device cuda    # 2 GPUs: needs a node with 2 GPUs
```

It passes when the last line is

```
PASS restore_test nproc=1 cpu: steps 101-200: loss_ntp and loss_mtp bit-equal, data ids equal
```

Exit codes: `0` PASS, `1` a difference (the line names the first step and field), `78` a run crashed (for
example a checkpoint failed its restore checks). A difference at step 101 means the data position, weights or
random state did not come back; a difference at step 102 or later with step 101 equal means something the next
step uses (usually the optimizer state) did not come back.

Results so far:

| Where | Result | Source |
|---|---|---|
| 1 and 2 CPU processes, Ubuntu, torch 2.14.1 | PASS, steps 101-200 bit-equal, data ids equal (**reference**) | `results/restore_test_cpu.txt` |
| 1 GPU, TSAI job on the lab node | PASS (**reference**) | `results/restore_test_gpu.txt` |
| 1 CPU process, Apple M5, torch 2.14.1, Python 3.13, 9 runs | PASS 9 of 9 (**measured**) | this runbook, section 7 |
| 2 CPU processes, same machine, 9 runs | PASS 9 of 9 (**measured**) | this runbook, section 7 |
| 2 GPUs | **pending**: needs a 2-GPU node, planned after Gate 2 | `results/restore_test_gpu.txt` |

## 5. Restart after a kill, and roll back on purpose

### 5.1 Restart after a kill

**With Slurm** nothing to type: `queue/job_queue.py run` (called by `slurm/mainrun.sbatch` and
`slurm/team_job.sbatch`) turns the trainer's exit into 0, 75 or 78, Slurm requeues on 75, and the next attempt
restores as in section 3.

**Without Slurm** (a single machine, the TSAI runner, the CPU tests) `ckpt/supervisor.py` applies the same rules.
It starts the trainer as a child process and, when the child ends, decides from the exit code. A restart runs the
**same command** again; the trainer calls `Checkpointer.restore()`, which loads the newest COMPLETE checkpoint
(`MANIFEST.json` written, then `latest.json` moved). A half-written checkpoint can never be loaded, and the
supervisor does not need to know anything about the model.

```bash
RUN_ID=r1 V5_REMOTE_ROOT=/shared/ckpt python ckpt/supervisor.py --log out/supervisor.jsonl -- python my_train.py
```

| Child exit | Supervisor does | Supervisor exit |
|---|---|---|
| 0 | stops | 0 |
| 75 (saved, run me again) | restarts, up to `--max-stops` times (default 100) | 78 when the limit is reached |
| 78 | does not restart | 78 |
| anything else (exception, SIGKILL, segfault) | restarts, unless it is a crash loop (3 crashes in 30 minutes, `CRASHLOOP_N` and `CRASHLOOP_WINDOW_S`) or `--max-restarts` (default 10) crashes are used up | 78 |

It waits `--backoff` seconds (default 5) before a restart. SIGTERM and SIGUSR1 are passed on to the trainer;
Ctrl-C is passed on as SIGTERM, because the trainer saves on SIGTERM and would crash on SIGINT. After a stop
signal no new trainer starts and the supervisor exits 75 for the outer scheduler to decide. If the supervisor
itself is killed with SIGKILL its child keeps running; that is safe, because the next attempt claims
`latest.json` and the old child's next commit is refused (`FencedError`, section 6).

**Read the log.** `--log` gets one JSON line per attempt, and `supervisor.*` events go to the events folder.
`pointer_step` is the step `latest.json` points to when the restart is decided. It is **not proof** of what the
trainer loaded: if that checkpoint fails its checks, `restore()` falls back to an older commit. The trainer's own
`restore.done` event (section 3) has the step it really restored.

**Prove it works.** `jobs/restart_test/restart_test.py` trains Team 05's tiny MoE twice. Run A goes from step 1 to
200 without a stop, with a checkpoint every 25 steps. Run B is the same command under the supervisor and is killed
with SIGKILL once it is past step 140. The supervisor restarts it, and for **every step 1 to 200** the losses must
be bit-equal to run A and the batch data id (position and sha256 of the batch tokens) the same. The supervisor log
must show exactly one restart (exit -9) and then exit 0.

```bash
CUDA_VISIBLE_DEVICES="" python jobs/restart_test/restart_test.py --out <scratch folder>          # about 10 s
```

PASS looks like this (last line; exit 0; exit 1 is a difference, 78 a crashed run, 75 the time limit):

```
PASS restart_test cpu: SIGKILL after step 140, restarted from COMPLETE checkpoint step 125, steps 1-200: loss_ntp and loss_mtp bit-equal, data ids equal
```

Numbers. The committed result names macOS arm64, Python 3.13.14, torch 2.14.1 (CPU); my runs are on an Apple M5, Python 3.13, torch 2.14.1 (CPU):

| | killed after step | restarted from (last COMPLETE checkpoint) | steps done twice | bit-equal steps | wall time A / B |
|---|---|---|---|---|---|
| committed result, `results/restart_cpu.txt` (**reference**) | 140 | 125 | 15 | 200 of 200 | 2.4 s / 3.9 s |
| same, kills after step 32, 100 and 165 (**reference**) | 32, 100, 165 | 25, 75, 150 | not listed | PASS on each | not listed |
| my runs, 3 repetitions, same command (**measured**) | 140, 141, 141 | 125 each | 15, 16, 16 | 200 of 200 each | 1.3 to 1.5 s / 2.0 s |

The supervisor log in all of them: attempt 0 exit -9 (crash: killed by SIGKILL), restart with `latest.json` at
step 125; attempt 1 exit 0 (done), stop. Work lost per kill = the steps since the last checkpoint: 15 or 16 steps
here, with a checkpoint every 25 (**computed**: killed-after step minus restarted-from step). Also **measured**:
`ckpt/test_supervisor.py`, 19 passed in 2 s on the same machine.

**What this does not cover.**
- The kill always lands after step 140, when the step-125 checkpoint is already committed, so it never kills a
  trainer in the middle of a save. That case is covered by the checkpoint drills (`kill_during_save`,
  `kill_during_restore`; `support/docs/sim_results.md`) and tests T3, T4 and T19 in `support/tests/test_ckpt.py`.
- One CPU process only. Not run on a GPU yet.
- The run as a TSAI job under queue rules v1 (`--run-id`, output in `./out/<run_id>/`, checked by
  `queue/queue_rules.py`): the rules file and the checker are in PR #245, not on main yet. The restart on the lab
  node (`results/restart_node.txt`) is **pending**.

### 5.2 Roll back on purpose (after a NaN or a loss spike)

```bash
python ckpt/ckpt.py list --run <run>               # pick the last good step K
scancel <held job id>
sbatch --export=ALL,TRAIN_EXTRA="--from-step K --skip 5 --branch b1" slurm/mainrun.sbatch
```

The run restores step K, skips the next 5 batches (the bad data) and continues on a **new branch** `b1`.
The old branch stays readable, so the run can be replayed. Restoring on fewer nodes works too
(`sbatch --nodes=1 ...`); the branch is then marked `<branch>-resharded-w<N>` and the loss is not bit-equal
going forward, because the sum order changes.

To check a branch afterwards: `python ckpt/ckpt.py list --run <run>`, then `restore.done` as in section 3.

## 6. When a restore fails: cause and action

Read the cause with `scontrol show job <id> | grep Comment`, then find it here. The full list, with the alert
ids, is `support/docs/codes_and_actions.md` (generated from `common/reasons.py`); `python metrics/explain.py
<cause>` prints any row. Causes not listed here are not about restore.

| Cause | Exit | Already done | You do |
|---|---|---|---|
| `IntegrityError` | falls back | a file did not match its sha256; the damaged checkpoint is never used and the previous commit is tried | pin the last good checkpoint (`ckpt.py pin --run <run> --step N`); find which hop corrupts data (disk, network, S3). Alert CK-04 |
| `RestoreCheckError` | falls back | digest, probe loss, next batch or frozen hashes differ; the previous commit is tried | compare the two printed values in the job log; **do not continue on that checkpoint**. Alert CK-05 |
| `CheckpointError` | 78 | every committed checkpoint failed, or the requested step does not exist | `ckpt.py list` and `verify --run <run>`; check the store (alerts CK-04 and CK-05 say where). Alert CK-06 |
| `StrictLoadError` | 78 | restore refused; every key that differs is in the job log | fix the model code or the key mapping; never resume by ignoring keys. Alert CK-06 |
| `EnvMismatchError` | 78 | restore refused; the differences are in the job log | if intended and approved, resubmit with `TRAIN_EXTRA=--allow-env-change` (it is logged); otherwise go back to the old image. Alert CK-06 |
| `DataManifestError` | 78 | restore refused before any step | point the loader back at the run's shard list, or start a new branch on purpose and tell Teams 01/02. Alert CK-06 |
| `ReshardError` | 78 | restore refused before any step | resubmit at the saved world size (the log names it), or fix the loader to keep one global ledger offset (`ckpt/loader_contract.py`). Alert CK-06 |
| `FencedError` | 78 | this attempt's commit was refused; the pointer and the newer attempt are untouched | nothing for the run; find why the old attempt was still alive (node network, slurmd), and drain that node if it repeats. No alert |
| `FrozenChangedError` | 78 | nothing saved; the previous checkpoint is still good | find which code trains the named tensor, fix it, then roll back (section 5.2). Alert CK-06 |
| `nonfinite`, `loss_spike` | 78 | nothing saved after the bad step | roll back (section 5.2); tell Team 05. Alerts CK-07 (`nonfinite`), H-24 (`loss_spike`) |
| `crash_loop` | 78 | 3 crashes in 30 minutes; held so it stops burning GPU hours | read the last job log for the real error, fix it, then `scontrol release <id>`. Alert Q-04 |
| `unknown_fatal` | 78 | exit 78 with no exit note | read the end of the job log for the FATAL line, then follow that cause. Alert Q-02 |
| `nvme_full` | save skipped | training continues, but nothing new is protected | free NVMe space or drain the node. Alert CK-03 |

Rule of thumb: a wrong **environment**, **keys** or **data list** stops with 78 because every older checkpoint
would fail the same way. A **damaged** checkpoint falls back to the previous commit by itself.

## 7. Restore time

### What is measured, and what it is not

The committed evidence gives only whole-script wall time: CPU 13.2 s (1 process) and 15.0 s (2 processes),
GPU 45 s (**reference**: `results/restore_test_cpu.txt`, `results/restore_test_gpu.txt`). That time contains
run A, both launches of run B and the comparison, so it is **not** the restore time.

`Checkpointer.restore` reports its own phases in the `restore.done` event. The numbers below come from that
event and from timing `restore()` end to end. They are a **lower bound**, not the production time:

- **tiny model, CPU.** The tiny MoE checkpoint is 1.5 MB.
- **no remote store.** The store is a folder on the local disk, and the page cache is warm. A shared file
  system or S3 adds the network (see the inputs below).
- **one thread per process, no GPU.** The state-digest check is compute-bound.
- `restore()` is not the same as CK-13. CK-13 runs from **job start to the first productive step**; that also
  holds Python start-up, imports, building the model, process-group start-up and the first step. These are
  **not measured here**.

### Measured: the restore test's own restore (tiny MoE, step 100)

Machine: Apple M5, 10 cores, 16 GB, macOS, Python 3.13, torch 2.14.1 (CPU), local folder store.
Method: `restore_test.py --out <scratch>` run 9 times each; rank 0's `restore.done` read from the events folder.
Median (min to max), seconds. **measured**

| Phase | 1 process | 2 processes |
|---|---|---|
| checksums (`verify_s`) | 0.0006 (0.0006 to 0.0007) | 0.0008 (0.0008 to 0.0009) |
| download (`download_s`) | 0.0013 (0.0013 to 0.0013) | 0.0067 (0.0065 to 0.0069) |
| load (`load_s`) | 0.0145 (0.0142 to 0.0149) | 0.0180 (0.0176 to 0.0181) |
| four proofs (`checks_s`) | 0.0065 (0.0064 to 0.0067) | 0.0070 (0.0069 to 0.0072) |
| **restore (`restore_s`)** | **0.031 (0.030 to 0.031)** | **0.034 (0.034 to 0.035)** |
| checkpoint size | 1.5 MB | 1.5 MB |
| whole script (for comparison) | 4.0 (4.0 to 4.2) | 4.9 (4.9 to 5.1) |

So for the tiny model the restore is about **30 ms**, under 1% of the script. The claim (step 1 of section 3) is
not inside `restore_s`; timing `restore()` as a whole shows it costs about **1 ms** more on a local folder
store (**computed**: total minus `restore_s`, 4 sizes below).

### Measured: how restore time grows with checkpoint size

A scratch script (not in this repo) saves a synthetic model with AdamW state (8 square linear layers) and times
`Checkpointer.restore` from a cold node-local folder, 9 repetitions per size, 1 process, same machine and store.
Total = claim + restore. Median seconds (min to max). **measured**

| Checkpoint | checksums | download | load | four proofs | **restore total** |
|---|---|---|---|---|---|
| 25 MB | 0.009 | 0.012 | 0.008 | 0.040 | **0.070** (0.069 to 0.071) |
| 101 MB | 0.034 | 0.044 | 0.013 | 0.153 | **0.244** (0.243 to 0.245) |
| 403 MB | 0.137 | 0.175 | 0.037 | 0.605 | **0.957** (0.947 to 0.997) |
| 1,611 MB | 0.590 | 0.933 | 0.304 | 2.501 | **4.371** (4.102 to 4.588) |

Reading it: restore time is linear in size over this range, about **2.4 to 2.7 s per GB**, **computed**
from the table (total divided by size). The four proofs are the largest share (about 55%) and are compute-bound
here, one CPU thread per process; on GPUs they run faster, which was not measured. This is local disk with a warm
cache: it says nothing about S3 or network throughput.

### To scale it to the real model: the inputs

| Input | Where to get it | Status |
|---|---|---|
| checkpoint size per rank (weights + AdamW state, about 3 times the fp32 weights) | `ckpt.py list`, or `du` on a step folder | **pending**: config v1 arrives Sat 14 Nov |
| download throughput from the store, per node | the store's own benchmark; `download_s` in `restore.done` | **not measured**: no GPU node with the real store yet |
| number of ranks, and whether the node-local copy is still valid (then there is no download) | the job | per run |
| speed of the four proofs on GPU | `checks_s` in `restore.done` | **not measured** |

How to use them: the checksums, load and four proofs scale with size at the rates in the table (the proofs
faster on GPU); the download is `size / store throughput` instead of the local-disk copy above. Do not
multiply the table past 1.6 GB: at real size the download is the part most likely to change. When a GPU run
gives `restore.done`, replace the table's rows with those values.

### The alarm

CK-13 (restore time, job start to the first productive step): **LOW 600 s, MEDIUM 900 s, HIGH 1800 s**
(**reference**: `metrics/catalog.yaml`). HIGH pages someone. What to do: use the node-local copy when valid,
prefetch from S3 in parallel, check S3 throughput. `restore_s` and `download_s` in `restore.done` show whether
the time went into the network or into the checks.

### Reference: recovery time in the Docker Slurm simulation

A killed trainer was back and training in about 50 s (median of 3 runs), a preemption in 58 s (**reference**:
`queue/README.md` section 8). That is the whole recovery: Slurm requeue, the credential wait (`BeginTime`, about
50 s), start-up and restore. It is not comparable to `restore_s`.

## 8. Not covered yet

| Item | Owner | Status |
|---|---|---|
| Restart job on the lab node (`results/restart_node.txt`) | Lead | **pending**, due Sat 14 Nov |
| Restore on 2 GPUs | TSAI, after Gate 2 | **pending** |
| Restore time on a GPU node with the real store and config v1 | G7 | **pending** |
| Queue rules (`docs/queue_rules_v1.md`, `queue/queue_rules.py`) and the parallel layout (`docs/parallel_layout_v0.md`) | G7 | **pending**: PR #245 and PR #246, not on main; not part of this file |
| Restart test on a GPU, as a TSAI job | G7 | **pending** |

## 9. Sources

`USER_GUIDE.md` (sections 1.3 to 1.6, 5.2, 5.4), `ckpt/README.md`, `ckpt/ckpt.py` (`restore`, `_restore_one`),
`ckpt/supervisor.py`, `ckpt/test_supervisor.py`, `jobs/restore_test/README.md`, `jobs/restart_test/README.md`,
`results/restart_cpu.txt`, `results/restore_test_cpu.txt`, `results/restore_test_gpu.txt`,
`support/docs/codes_and_actions.md`, `common/reasons.py`, `metrics/catalog.yaml`, `queue/README.md`.
