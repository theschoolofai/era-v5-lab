# G7 runbook: restore a run from its last checkpoint, and how long it takes

Owner: G7 rotation members. Status: **v0 draft for lead review** (week 2, due Sat 14 Nov 2026).
Code: [`ckpt/ckpt.py`](../ckpt/ckpt.py), [`ckpt/supervisor.py`](../ckpt/supervisor.py). Tests:
[`jobs/restore_test/`](../jobs/restore_test/README.md), [`jobs/restart_test/`](../jobs/restart_test/README.md).
Rules: [`docs/queue_rules_v1.md`](queue_rules_v1.md). Causes and actions:
[`support/docs/codes_and_actions.md`](../support/docs/codes_and_actions.md). Design:
[ADR 0001](../adr/0001-checkpoint-format-and-commit.md), [`ckpt/README.md`](../ckpt/README.md).

> **In simple words.** A checkpoint is a saved copy of the training. "Restore" means: a new process reads the
> newest good copy, proves it got back exactly what was saved, and trains on from there. Most of the time this
> happens by itself (exit 75, or a crash under the supervisor). This file says **when a person must act**,
> **what to type**, **how to tell the restore worked**, and **how long a restore takes** (measured, not guessed).

Where this file and the code disagree, the code wins and this file is fixed.

---

## 1. When to act

| You see | It means | Do |
|---|---|---|
| exit **75** | the job saved and stopped (time limit, stop signal, preemption, health drain) | nothing. It runs again and restores itself (section 4) |
| a crash (exit -9, other non-zero) under `ckpt/supervisor.py` | the trainer died without saving | nothing, unless the supervisor stops with 78 (section 4) |
| exit **78**, or the job is held | stopped on purpose; a person must look | read the cause in the job log, then [`codes_and_actions.md`](../support/docs/codes_and_actions.md); section 6 |
| alert **CK-05** (`RestoreCheckError`) | the restored state is not the saved state | do not continue on that checkpoint; section 6 |
| alert **CK-13** | restore is slow (job start to first productive step) | section 7 |
| NaN, or a loss spike | the guards stopped the run (exit 78) | roll back with `--from-step` / `--skip` / `--branch` (section 5) |

`python metrics/explain.py <cause>` explains any cause code.

---

## 2. Look at the checkpoints first

From `teams/07-infrastructure/`. `<run>` is the run's checkpoint folder: `<remote_root>/<run_id>` on a cluster,
`./out/<run_id>/ckpt/<arm>` in a TSAI job ([queue rules R4](queue_rules_v1.md)). The store address and access
come from the cluster settings (`ops/cluster.env`, from `ops/cluster.env.example`), never from this file.

```bash
python ckpt/ckpt.py list   --run <run>              # committed checkpoints, newest last
python ckpt/ckpt.py verify --run <run> --step <N>   # every file of step N against its sha256
python ckpt/ckpt.py pin    --run <run> --step <N>   # keep step N safe from retention while you work
```

A good checkpoint (restore test, step 100):

```text
$ python ckpt/ckpt.py verify --run <run> --step 100
{"step": 100, "path": "main/step_00000100-e1", "files": 3, "bad": []}        exit 0
```

`"bad": []` and exit 0 is good. A damaged file is listed by name in `bad` and the exit code is 1. `verify` without
`--step` checks the latest one only. An explicit `--step` that does not exist fails; it does not fall back.

### Which checkpoint is COMPLETE (the rule as implemented)

A checkpoint is **COMPLETE** when its step folder has `MANIFEST.json` **and** `latest.json` or `commits.jsonl`
names that folder ([queue rules v1.1, R4](queue_rules_v1.md), PR #245). There is **no separate `COMPLETE`
file**: `ckpt.py` writes `MANIFEST.json` last, and moves `latest.json` (with the fencing check) and appends to
`commits.jsonl` only after it. A `MANIFEST.json` that no pointer names is a save cut before its commit (not a
checkpoint, not an error). A pointer to a folder without `MANIFEST.json` is an error.

---

## 3. What a restore does, in order

Every trainer calls `Checkpointer.restore()` at start. Nobody picks a folder by hand.

```text
1. claim       write latest.json with epoch + 1 -> an older copy of this run can no longer commit
2. candidates  latest.json first, then commits.jsonl newest -> oldest (never "list folders")
3. per candidate:
   a. checksums     every file against MANIFEST.json                  fail -> try the previous commit
   b. environment   image, torch / CUDA / NCCL, config, tokenizer,    fail -> stop, exit 78
                    git_sha, OMP_NUM_THREADS
   c. copy          to node-local disk, each copy re-checked          fail -> try the previous commit
   d. strict keys   every name, shape and dtype                       fail -> stop, exit 78
   e. load          weights (resharded if the device count changed), data position, random generators
   f. 4 proofs      state digest, probe-loss bits, next-batch hash,   fail -> try the previous commit
                    frozen hashes
4. no commit yet -> fresh start at step 0;  every candidate failed -> exit 78 (CheckpointError)
```

### How to tell it worked

- The job log has a `restore.done` event with the **expected step** and `"resharded": false` (unless you changed
  the device count on purpose).
- There is **no `restore.failed`** event for the same attempt. A `restore.failed` followed by `restore.done` on an
  older step means it fell back: the job is fine, but `verify` the skipped step.
- `restore.done` carries the time of each phase: `verify_s`, `download_s`, `load_s`, `checks_s` and the total
  `restore_s` (section 7).

---

## 4. Automatic restart (`ckpt/supervisor.py`)

Without a scheduler (one machine, the TSAI runner, the CPU tests), `ckpt/supervisor.py` (PR #257) runs the
trainer as a child process and starts the **same command** again after a 75 or a crash. The trainer's
`restore()` then picks the newest COMPLETE checkpoint (section 3). The supervisor knows nothing about the model.

```bash
RUN_ID=<run_id> V5_REMOTE_ROOT=<remote_root> \
  python ckpt/supervisor.py --log ./out/<run_id>/logs/supervisor.jsonl -- <trainer command>
```

| Child exits with | Supervisor does |
|---|---|
| `0` done | stops, exit 0 |
| `75` saved and stopped | restarts, at most `--max-stops` times (default 100); then stops with 78 |
| `78` a person must look | stops, exit 78, no restart |
| anything else (exception, SIGKILL, segfault) | restarts after `--backoff` (default 5 s); stops with 78 after **3 crashes in 30 min** (`CRASHLOOP_N`, `CRASHLOOP_WINDOW_S`) or after `--max-restarts` crashes (default 10) |
| SIGTERM / Ctrl-C to the supervisor | passes SIGTERM to the trainer, starts no new trainer, exits 75 |

- **Log:** one JSON line per attempt in `--log` (in a job: `./out/<run_id>/logs/supervisor.jsonl`, queue rules
  R3), with `attempt`, `rc`, `meaning`, `action`, `reason`, `seconds`, and `pointer_step` on a restart. The same
  rows go out as `supervisor.*` events. `pointer_step` is what `latest.json` named when the restart was decided;
  the step really restored is in the trainer's `restore.done`.
- **If the supervisor itself is killed**, the child keeps running. That is safe: the next attempt claims
  `latest.json`, and the old child's next commit is refused (fencing).
- On a later Slurm cluster the job wrapper applies the same rules (requeue on 75, crash-loop cap); see
  [ADR 0002](../adr/0002-job-queue-slurm.md).

**Proof on CPU** ([`results/restart_cpu.txt`](../results/restart_cpu.txt), PR #258): run B was killed with SIGKILL
after step 140; the supervisor restarted it once, the trainer restored the COMPLETE checkpoint at step 125, and
all steps 1-200 were bit-equal to the run that never stopped. Kill points 32, 100 and 165 also pass. A rerun
for this file (section 7.1) gave the same PASS three times.

---

## 5. Roll back to a chosen step (after a NaN or loss spike)

```bash
sbatch --export=ALL,TRAIN_EXTRA="--from-step <N> --skip <K> --branch <new_branch>" slurm/mainrun.sbatch
```

It restores step `N` (find the last good one with `ckpt.py list`), skips the next `K` batches, and continues on
a **new branch**, so the old branch can be replayed later. Pin step `N` first (section 2). On fewer devices the
restore reshards; the run is marked `<branch>-resharded-w<N>` and is no longer bit-equal going forward.

---

## 6. When a restore fails

Causes and actions are in [`codes_and_actions.md`](../support/docs/codes_and_actions.md); this is the short form.

| What you see | Alert | What to do |
|---|---|---|
| `restore.failed` `IntegrityError`, then `restore.done` on an older step | CK-04 | nothing urgent; it fell back. Pin the last good step; `verify` the bad one |
| `RestoreCheckError` (restored state differs) | CK-05 | compare the two printed values; do not continue on that checkpoint |
| exit 78 `EnvMismatchError` | CK-06 | fix the stack. `--allow-env-change` only if the lead agrees; it is logged |
| exit 78 `StrictLoadError` (lists keys) | CK-06 | fix the model code; never load around it |
| exit 78 `DataManifestError` | CK-06 | point the loader back at the run's shard list |
| exit 78 `ReshardError` | CK-06 | restart on the saved device count |
| exit 78 `CheckpointError` | CK-06 | every candidate failed: `ckpt.py list` / `verify`; hold the run; tell the checkpoint owner |
| `FencedError` | - | normal after a split: a newer copy of the run owns it and keeps training |
| supervisor exit 78 "crash loop" | - | 3 crashes in 30 min: read the last trainer error in `logs/job.log` before any restart |

Watch out: `git_sha` is one of the fields that must match, and it comes from `GIT_SHA` (`unknown` when it is not
set). Set it the same way on every attempt of a run (issue #298 tracks recording it by default).

---

## 7. Restore time

**Restore time** here = `restore_s` in the `restore.done` event: from reading the manifest to the end of the four
proofs. It does not include the claim, starting Python or importing torch. It is **not CK-13**, which runs from
job start to the first productive step.

### 7.1 CPU (measured, lower bound)

Team 05 tiny MoE, checkpoint about **1.5 MB** (one shard, `extra_rank0.json`, `sums_rank0.json`, plus
`MANIFEST.json`), local folder store, member laptop (macOS arm64, 12 cores), Python 3.13.1, torch 2.14.1,
numpy 2.2.6, one thread per process (the script sets it). `main` at `4332666`, 6 Nov 2026. Three runs each, median.

| Test | Devices | `restore_s` (3 runs) | median | verify | copy to local | load | 4 proofs | whole test |
|---|---|---|---|---|---|---|---|---|
| restore test (step 100) | 1 CPU process | 0.072, 0.068, 0.071 s | **0.071 s** | 0.001 s | 0.015 s | 0.023 s | 0.008 s | 7.2-10.0 s |
| restore test (step 100) | 2 CPU processes (gloo) | 0.083, 0.084, 0.086 s | **0.084 s** | 0.002 s | 0.036 s | 0.028 s | 0.009 s | 8.0-8.2 s |
| restart test (SIGKILL, step 125) | 1 CPU process | 0.121, 0.078, 0.081 s | **0.081 s** | 0.001 s | 0.020 s | 0.026 s | 0.009 s | - |

- All nine runs: **PASS**. Restore test: steps 101-200 bit-equal, data IDs equal, `"resharded": false`.
  Restart test: steps 1-200 bit-equal, one restart from step 125.
- Phase columns are medians, from the one `restore.done` event each run writes. With 2 processes the copy to local disk takes
  about twice as long; the other phases barely change.
- A first run on 2 Nov, same machine, gave 0.088 s and 0.094 s (median of 3, 1 and 2 processes); other members'
  machines give 0.03 to 0.07 s. Matching numbers across machines is not a goal; the order of size is.
- These numbers prove the steps work. **They do not scale to the main run**: at full size `restore_s` is
  dominated by reading the checkpoint from the store and hashing every file.

### 7.2 GPU (pending)

| Devices | `restore_s` | Result | Source |
|---|---|---|---|
| 1 GPU | _pending_ | PASS, whole test 45 s (no `restore_s` recorded) | [`results/restore_test_gpu.txt`](../results/restore_test_gpu.txt), PR #196 |
| 1 GPU | _pending, TSAI job results expected Thu 12 Nov_ | _pending_ | `jobs/results/<YYYY-MM-DD>-<short-name>/` |
| 2 GPUs | _after Gate 2_ | - | needs a node with 2 GPUs; until then the 2-process CPU row is the 2-device evidence |

### 7.3 What to expect on the main run, and the alarm

```text
restore_s  ~  checkpoint size per node / store read speed  +  sha256 of every file  +  load into the devices
```

Alarm **CK-13** ([`metrics/catalog.yaml`](../metrics/catalog.yaml)), job start to first productive step:
**LOW 600 s, MEDIUM 900 s, HIGH 1800 s**. If it fires: use the node-local copy when it is valid, read from the
store in parallel, check the store read speed. `download_s` and `restore_s` in `restore.done` show whether the
store is the slow part. The real number needs the config v1 sizes and the real store (Sat 14 Nov).

---

## 8. Rehearse a restore and a restart (anyone, CPU, about 10 s each)

From the repo root, once, in a fresh virtual environment (no GPU, no keys, no network after the install):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r teams/04-ke2/src/requirements.txt pyyaml     # torch 2.14.1 or newer
```

Then from `teams/07-infrastructure/`:

```bash
CUDA_VISIBLE_DEVICES="" python jobs/restore_test/restore_test.py              # 1 CPU process
CUDA_VISIBLE_DEVICES="" python jobs/restore_test/restore_test.py --nproc 2    # 2 CPU processes
CUDA_VISIBLE_DEVICES="" python jobs/restart_test/restart_test.py              # SIGKILL + supervisor
```

The last lines must be:

```text
PASS restore_test nproc=1 cpu: steps 101-200: loss_ntp and loss_mtp bit-equal, data ids equal
PASS restart_test cpu: SIGKILL after step 140, restarted from COMPLETE checkpoint step 125, steps 1-200: loss_ntp and loss_mtp bit-equal, data ids equal
```

Exit `0` PASS, `1` a difference (the line names the first step and field), `78` a run crashed. Output goes to
`out/` next to each script (git-ignored). Read the restore time:

```bash
python -c "import glob,json; [print({k: d[k] for k in d if k.endswith('_s') or k == 'step'}) for f in glob.glob('jobs/*_test/out/**/*.jsonl', recursive=True) for d in map(json.loads, open(f)) if d.get('event') == 'restore.done']"
```

Check the checkpoint by hand: `python ckpt/ckpt.py verify --run jobs/restore_test/out/ckpt_store/restore-b --step 100`.
The supervisor log of the restart test is `jobs/restart_test/out/logs/supervisor.jsonl` (two lines: exit -9,
restart; exit 0, stop).

**Do not commit `out/`.** It holds checkpoints, and the event files and `latest.json` record the machine name.
Copy only the PASS line and the numbers.

---

## 9. Open items

| Item | Owner | Blocks |
|---|---|---|
| GPU `restore_s`, 1 GPU (section 7.2) | lead sends the request; TSAI results expected Thu 12 Nov | section 7.2 |
| Real restore time at config v1 size and on the real store | checkpoint owner + Team 6, after config v1 (Sat 14 Nov) | section 7.3 |
| Separate `COMPLETE` file after `MANIFEST.json` (#245 discussion) | lead | none today: v1.1 says no file; section 2 changes only if the team reverses it |
| Manifests record `git_sha=unknown` when `GIT_SHA` is unset (issue #298) | checkpoint owner | the warning in section 6 |
| Merge this file with the other rotation runbooks (PRs #277, #291, #294, #308) | lead | one runbook |
| 2-GPU restore | after Gate 2 | section 7.2 |

## 10. Change log

| Version | Date | Change |
|---|---|---|
| v0 | 2026-11-02 | first draft: restore steps, failure table, CPU restore time (1 and 2 processes) |
| v0.1 | 2026-11-06 | "When to act" first; COMPLETE rule of queue rules v1.1; supervisor restart (PR #257, #258); CPU times re-measured on `main` (restore and restart tests); CK-13 alarm; GPU row from PR #196 |
