# Main-run command checklist: Team 5 review and Team 7 launch gate

Status: **DRAFT for Team 5 review. No Team 5 approval is claimed.** Checked against lab main at `821c82ad` (teams 05 and 07 are unchanged since `d0e556b3`). Status of each open row and the date it was last checked: see the table after “No-go today”.

This checklist decides whether `teams/07-infrastructure/slurm/mainrun.sbatch` can start Team 5's
`teams/05-architecture/harness/train_week2.py` safely. Today main launches the simulation trainer and its flags.
The separate Team 7 implementation changes production to Team 5's one-GPU trainer and keeps simulation opt-in.

## Team 5: decisions and inputs requested

Please review every row in this table. Reply with **accept**, a replacement decision, or an owner and due date.
The main run remains **no-go** until Team 5 answers D1–D6 and the command passes the drill below.

| Decision | Team 5 needs to review or provide | Why Team 7 cannot decide it |
|---|---|---|
| **D1: exact main-run inputs** | Provide the reviewed `mainrun.args` values for `--config`, `--runtime`, `--resolution`, `--tokenizer-release`, `--tokenizer`, `--byte-table`, `--train-data`, `--heldout-data`, `--heldout-sources`, `--heldout-sha256`, `--heldout-report`, and `--seed`. Confirm the config has `approval.status: agreed`, a reference, `evaluation.approved`, and bf16. State whether the reviewed file also needs any allowed optional flag: `--lr`, `--logger-factory`, or `--expert-load-every` with a value, or the bare switch `--consolidate-step-checks` / `--no-consolidate-step-checks`. | These select Team 5's model, data, tokenizer, evaluation contract and reproducibility seed. The sbatch checks that each required value is explicit but must not choose it. If any listed option should not be mandatory or allowed, Team 5 must say which one and why. |
| **D2: one-GPU trainer on an exclusive node** | Confirm that the first main run is intentionally one process bound to one GPU while the `gpu` partition reserves the whole eight-GPU node. Accept the temporary seven-GPU idle cost, request a suitable shareable/one-GPU node class, or provide the distributed-training plan and date. | `train_week2.py` has no process-group initialization, rank-aware loader or distributed model wrapper. Several Slurm tasks would start independent writers on one run ID. The existing partition is `OverSubscribe=EXCLUSIVE`, so requesting one nominal GPU does not make the other seven schedulable. A distributed version also needs the runbook's 10-minute collective timeout and rank-aware checkpoint behavior. |
| **D3: claim before first commit** | Review the recovery that Team 7 proposes for Team 5's draft #826 (target week 5, not this week; neither Team 5's lead nor this checklist has approved it): `train_week2.py` calls the public `checkpointer.claim()` and then `checkpointer.candidates()`. No candidates: a fresh start; commit step 0 and wait for it before the first optimizer update (exit 75 if the save fails or is unconfirmed). Candidates exist: exit 78 with "use `--resume-committed`". No new trainer flag, no `claim_initial()` and no new fields in `latest.json`. Until then, accept that Team 7 holds the job with exit 78. This week the fresh-start path is unchanged. | The trainer currently rejects fresh mode whenever `latest.json` exists and rejects resume mode when no committed candidate exists, so no Team 7 flag can make that state progress safely. Team 7 prefers this order because claiming before reading closes the race with an old attempt that commits in between: `claim()` bumps the epoch with a conditional write, so that attempt is fenced at its commit (ADR 0001 §3), as in every committed resume. A check of `candidates()` alone would leave that race open. Team 7's launcher does the other half: before resubmitting a `claimed_only` run it checks in `sacct` that the earlier job for this run ID has ended (queue rule R1). In week 5 it will do that check itself and pass `--checkpoint-at-start` for both `fresh` and `claimed_only`. Team 7's `start-mode` check uses the same shared rule as `Checkpointer.candidates()`, so the launcher and the trainer cannot disagree. A draft must not start a second fresh run over a live claim. |
| **D4: rollback** | Decide whether `train_week2.py` will implement `--from-step`, `--skip`, `--branch`, and any required `--allow-env-change` behavior. Team 7 recommends starting with `--from-step` only, passed through to `Checkpointer.restore(from_step=…)`, which already exists in Team 7's `ckpt/ckpt.py`; the other flags can wait if Team 5 agrees. Team 5 may choose differently. If it adds none of them, the manual alternative must be written down and agreed by both teams. Team 7 does not remove the rollback procedure from its runbook without Team 5's approval. | Today a loss spike holds the run (exit 78) and there is no automated way back. The Team 7 runbook describes these flags, but Team 5's trainer does not accept or apply them. The implementation holds instead of crash-looping when they are supplied. When a flag lands, Team 7 moves it from the sbatch's unsupported list to its allowlist in a follow-up change. |
| **D5: local checkpoint cache** | Preferred: add a Team 5 option that places the cache on the node-local checkpoint disk (suggestion below). Otherwise confirm that `<out>/checkpoint-cache` may live under `V5_OUT_ROOT` and state who removes the caches of earlier attempts and when. Tell Team 8 whether its log shipper must exclude this directory. Each attempt also writes its own `<run>/<job>.<restart>/train/metrics.jsonl` (new `--out` per attempt), so Team 8's ingestion must read all of them. | `train_week2.py` fixes the cache below `--out`, and every attempt gets a new `--out`. `keep_local=2` prunes only inside one attempt, and restore staging (`restore/`) is not pruned at all. One attempt can hold up to 3 saved checkpoints during an upload plus 1 restore copy, and nothing removes the caches of earlier attempts: a restore always downloads from the shared store, so those caches are never reused. `V5_OUT_ROOT` (default set in `slurm/mainrun.sbatch`) is the disk that also holds job logs and events. Team 7 can move all of `V5_OUT_ROOT`, but cannot independently move only the checkpoint cache. |
| **D6: deployed paths and optional metrics** | Provide the node path to `train_week2.py` and its `week2/` package (the node path and the logger stay with TSAI; the dry run 2 paths are in the job on main). Confirm whether the main command must include `--logger-factory g5_adapter:make_writer` and the Team 8 package on `PYTHONPATH`. | Team 7 validates the trainer path and supplies its own `ckpt/` and `common/` packages, but Team 5 and TSAI own the harness installation and the metrics adapter decision. |

Suggested Team 5 response:

```text
D1: accept / changes: ... ; mainrun.args owner/path: ...
D2: accept one GPU / distributed plan: ...
D3: accept claim() then candidates() (#826 proposal) / other design / accept temporary hold: ...
D4: implement flags (which ones) / approved manual alternative: ...
D5: capacity and log-shipping decision: ...
D6: trainer path and logger decision: ...
Reviewer and date: ...
```

## Command checklist

The “implementation” column describes the separate Team 7 sbatch/code change. It is not evidence that the change
has merged or run on a cloud node.

| # | The production command must contain | Owner | Implementation or open result |
|---|---|---|---|
| C1 | Team 5's actual `train_week2.py`, not the simulation trainer | Team 7 path check; Team 5 supplies path | `V5_TRAINER=week2` is the default and is explicit in the production submission. `V5_TRAIN_SCRIPT` must exist and have basename `train_week2.py`. Simulation requires both `V5_TRAINER=sim` and `V5_SIMULATION=1` and clears any inherited production trainer path. |
| C2 | The complete D1 argument set, with no simulation-only flags | Team 5 | One full argument per line in `V5_TRAIN_ARGS_FILE`: value-taking options use `--option=value`; boolean switches are bare. Missing values, abbreviations, unknown options and wrong arity hold before training starts. Team 5 must provide and review the file. |
| C3 | `--device cuda`, an approved bf16 config, and the reviewed seed | Team 7 device; Team 5 config/seed | Sbatch supplies `--device`; D1 remains open. The trainer itself rejects non-CUDA/non-bf16 quality runs. |
| C4 | One validated identity and store: `--run-id "$RUN_ID" --checkpoint-store "$V5_REMOTE_ROOT"` | Team 7 | Sbatch validates the run ID, owns both flags and exports `V5_REMOTE_ROOT`, so paths cannot escape the run folder and the trainer and crash-loop ledger use the same store. Caller arguments cannot override them. |
| C5 | Exactly one automatic start mode: fresh gets `--checkpoint-at-start`; a committed run gets `--resume-committed` | Team 7 | `job_queue.py start-mode` validates and reads `latest.json` and every `commits.jsonl` candidate. Missing, unreadable or malformed stores hold rather than guessing fresh or fencing the run. |
| C6 | A new absolute `--out` for every attempt | Team 7 | `<V5_OUT_ROOT>/<run_id>/<job_id>.<restart>/train`; relative `V5_OUT_ROOT` is refused. |
| C7 | `--checkpoint-interval-s 600 --watchdog-s 600` | Team 7; Team 5 confirms performance suitability | Sbatch pins both to 600 seconds in production; inherited simulation values are ignored. A different approved value requires a reviewed code/checklist change. Retention (`--keep 9`, C15) is sized for 600 s in `checkpoint_interval.md` §5, which is still provisional, so changing one means editing both. A comment at the pin says so. |
| C8 | `PYTHONPATH` containing Team 7, plus `OMP_NUM_THREADS=1`, `RUN_ID`, `V5_EVENTS_DIR`, and `V5_RUNS_DIR` | Team 7 | Set explicitly. Team 5 answers the optional metrics path in D6. |
| C9 | `TORCH_NCCL_ASYNC_ERROR_HANDLING=1`, trace buffer `2000`, dump-on-timeout `1`, and an absolute `TORCH_NCCL_DEBUG_INFO_TEMP_FILE` whose directory exists outside `--out` | Team 7 | Trace prefix is `<attempt>/nccl_trace/rank_`; trainer output is `<attempt>/train`. Dumps cannot make `--out` non-empty and cannot mix between attempts. This closes the command-side runbook §14 item. |
| C10 | None of `--steps`, `--interval-s`, `--remote-root`, `--local-root`, `--step-sleep`, or `--drill-dir`; no test crash hooks | Team 7 | Simulation flags remain only in explicit simulation mode. `V5_DRILL_DIR` and `V5_TEST_CRASH_BEFORE_SEAL` are unset before Team 5 starts. |
| C11 | One node and one task bound to one GPU; the exclusive partition reserves all eight node GPUs | Team 5 accepts D2 cost/scope; Team 7 allocation/guard | Sbatch requests 1 node × 1 task × 8 allocated GPUs and passes `srun --gpus-per-task=1`, so Team 5 sees one GPU without starting multiple writers. It validates `SLURM_JOB_NUM_NODES=1`, `SLURM_NTASKS=1`, and `SLURM_GPUS_ON_NODE=8`. D2 remains open. |
| C12 | A defined recovery rule for a claim with no commit | Team 5 (trainer, #826); Team 7 (launcher) | The helper reports `claimed_only`; sbatch holds with exit 78 and says: confirm in `sacct` that the earlier job for this run ID has ended, then resubmit with a new `RUN_ID`; nothing was committed. This is the accepted interim hold. Week 5: the launcher does the `sacct` check and passes `--checkpoint-at-start`, and the trainer calls `claim()` then `candidates()`. D3 remains open. |
| C13 | A rollback procedure accepted by both teams | Team 5 trainer; Team 7 operations docs | Unsupported rollback flags hold rather than crash-loop. Until `--from-step` exists a loss spike holds the run with no automated way back. D4 remains open. |
| C14 | Sufficient local checkpoint-cache space, a cleanup owner for earlier attempts' caches, and a log-shipping rule | Team 5 (cache option), Team 8 (shipping), Team 7 (placement and interim cleanup) | **Space risk: nobody cleans earlier attempts' caches today.** Each attempt keeps up to 3 saved checkpoints during an upload plus 1 restore copy (`restore/` is never pruned), in a new `--out` folder. A restore always downloads from the shared store, so earlier caches are never reused. Repeated restarts therefore fill the `V5_OUT_ROOT` disk, which also holds job logs and events. D5 remains open. Interim, until Team 5 provides the cache option: the Team 7 operator removes `checkpoint-cache` under finished attempts of this run (never the running job's) after each restart or release, and checks free space on `V5_OUT_ROOT` before releasing a held job. Everything else in the attempt folder stays. |

## Run operations (outside the command)

| # | Operation | Owner | Implementation or open result |
|---|---|---|---|
| C15 | Pin step 0 after the first commit, and run retention with `--keep 9 --protect-every 10` | Team 7 operator | Open until the drill evidence includes it. (1) After the first commit (step 0, reason `start`, written by `--checkpoint-at-start`) appears in `python teams/07-infrastructure/ckpt/ckpt.py list --run "$V5_REMOTE_ROOT/$RUN_ID"`, run `python teams/07-infrastructure/ckpt/ckpt.py pin --run "$V5_REMOTE_ROOT/$RUN_ID" --step 0` and check that `pins.json` contains 0. `--run` needs the full store path; the run ID alone fails (#743), and `pin` does not check that the step exists. (2) Run retention as its own job (the training job never deletes, ADR 0002 §7) with `--keep 9 --protect-every 10`, dry run first, and check that step 0 is listed under `protected`. At the 600 s interval (C7), `checkpoint_interval.md` §5 sets `--keep 9` for a 90-minute reach; `--protect-every 10` is Team 9's cadence (#739). `--protect-every` counts commit position, and step 0 is commit 1, so without the pin retention deletes step 0 once it is older than the newest 9 commits. |

## Suggestion for Team 5 on D5: cache on the node-local checkpoint disk

Add a `--checkpoint-cache-dir` option (a path, default `<out>/checkpoint-cache`) and pass it to
`Checkpointer(run_id, str(cache_dir), ...)` at `train_week2.py:540`. Team 7 would then pass the node-local checkpoint
root, `V5_CKPT_CACHE_ROOT`. That name is a proposal: the sbatch does not define it yet, and it would default to the
root the node already uses for checkpoints. Give the root, not a run subfolder, because `Checkpointer` appends the
run ID. The cache lives at `<root>/<run>/`, shared across attempts. The existing `keep_local=2` then covers the
whole run on that node, and `slurm/epilog.sh` already removes the `restore/` folders under that root. `--out` stays empty at start, as the check at `train_week2.py:306` requires. Once the
option exists, `mainrun.sbatch` adds it to its owned flags. Team 7 does not implement this change.

## Protected command ownership

Team 5's argument file may not override `--out`, `--run-id`, `--checkpoint-store`,
`--checkpoint-interval-s`, start/resume flags, `--watchdog-s`, `--device`, `--smoke`, or `--no-checkpoint`.
Each required D1 input must occur exactly once with a non-empty value. Optional flags may occur at most once,
and the two consolidate switches are mutually exclusive. The file accepts only the required D1 names and the
optional names listed in D1; every option must use its full argparse name and correct value/bare-switch form.
Production rejects `TRAIN_EXTRA` entirely, along with smoke/stop controls and unsupported rollback flags. Any
additional Team 5 option therefore needs an explicit checklist and allowlist review, so inherited operator or
simulation settings cannot change or truncate the run.

## Go / no-go rule

**Go** only when all of the following are true:

1. Team 5 records decisions D1–D6, including the exact reviewed argument file and trainer path.
2. C1–C15 are satisfied, or both teams record a named, time-bounded exception for an open row.
3. The exact production command runs once on the target environment.
4. That run commits a checkpoint, receives one SIGKILL, requeues automatically, passes `--resume-committed`, and
   restores the committed step with the same checks as `jobs/2026-11-23-dryrun2-kill-drill.md`.
5. The evidence records the command, environment names without secrets, job/restart IDs, committed and restored
   steps, exit codes, `--out`, and NCCL trace path.
6. The evidence also records `pins.json` (containing step 0) and the retention dry-run output from C15.

**No-go today.** D1–D6 have no recorded Team 5 answers, C12–C15 are open, and the exact command has not completed
the required kill-and-restore drill. Team 5 has said the main run stays no-go and this checklist stays a draft. Team 5's
position on each open item: D1 open (no model size, context length or reviewed `mainrun.args`); D2 open, and an
exclusive eight-GPU node is not a decision for this week (7 of 8 GPUs sit idle for the whole run until it is
decided); D3 open, with the exit 78 hold accepted until a recovery draft (#826) is agreed; D4 open, and the removal
of the rollback flags is not approved (a loss spike holds the run, with no automated way back); D5 and D6 open,
with the node path and the logger staying with TSAI.

To re-verify “No-go today” without reading the threads, use this table. Update the date whenever a row is rechecked.

| Row | Status | Last checked | Source |
|---|---|---|---|
| D1 | Open: no model size or context length in config v1, no reviewed `mainrun.args` | 2026-11-28 | Team 5 lead review of #819 (26 Nov, reproduced in the #819 thread) |
| D2 | Open: an exclusive eight-GPU node is not a decision for this week | 2026-11-28 | same |
| D3 | Open: exit 78 hold accepted; recovery proposed in draft #826 (`83632902`), not approved | 2026-11-28 | same; #826 and #820 threads through 27 Nov |
| D4 | Open: removal of the rollback flags not approved; the trainer does not take them | 2026-11-28 | same |
| D5, D6 | Open: dry run 2 paths are in the job on main; node path and logger stay with TSAI | 2026-11-28 | same |
| C12–C14 | Open (follow D3, D4, D5) | 2026-11-28 | this file |
| C15 | Open until the drill evidence includes the pin and the retention dry run | 2026-11-28 | this file |
| C1–C11 | Not rechecked in this update | none | the Team 7 change in #820 |

## Proposed submission after Team 5 supplies D1 and D6

```bash
sbatch --export=ALL,RUN_ID=v5main,V5_TRAINER=week2,\
V5_TRAIN_SCRIPT=/approved/path/train_week2.py,\
V5_TRAIN_ARGS_FILE=/approved/path/mainrun.args \
  teams/07-infrastructure/slurm/mainrun.sbatch
```

The sbatch defaults to one node and one task, reserves all eight GPUs required by the exclusive `gpu` partition,
and binds the task to one GPU. It selects fresh or committed resume from the shared store; an operator must not
add a resume flag manually.

## Related docs not yet updated

These Team 7 files still show the `TRAIN_EXTRA` rollback or `--allow-env-change`, which `mainrun.sbatch` rejects
for Team 5's trainer: `USER_GUIDE.md` (lines 182, 379, 410, 424), `ckpt/README.md` (lines 64, 245),
`queue/README.md` (line 207), `metrics/README.md` (lines 86, 169, 177) and `adr/0002-job-queue-slurm.md` (lines 193,
318). `queue/README.md` (lines 160, 234) describes the earlier two-node, always-resume script, and `USER_GUIDE.md`
(line 68) shows the submit command without the new required variables. The correct text depends on the D4 decision, so Team 7 updates them once D4 is decided. The
runbook (`docs/runbook.md`, §5 and §6) is updated in the Team 7 code change.
