# Main-run command checklist: Team 5 review and Team 7 launch gate

Status: **DRAFT for Team 5 review. No Team 5 approval is claimed.** Checked against lab main at `d0e556b3`.

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
| **D3: claim before first commit** | Decide how `train_week2.py` should recover when `latest.json` contains a fencing claim but no checkpoint has committed. Preferred change: treat this state as fresh using the same committed-candidate rule as `Checkpointer.candidates()`. Until then, accept that Team 7 holds the job with exit 78. | The trainer currently rejects fresh mode whenever `latest.json` exists and rejects resume mode when no committed candidate exists. No Team 7 flag can make that state progress safely. |
| **D4: rollback** | Decide whether `train_week2.py` will implement `--from-step`, `--skip`, `--branch`, and any required `--allow-env-change` behavior. If not, approve removing the automated rollback procedure for this trainer and document the manual alternative. | The current Team 7 runbook describes these flags, but Team 5's trainer does not accept or apply them. The implementation holds instead of crash-looping when they are supplied. |
| **D5: local checkpoint cache** | Confirm that `<out>/checkpoint-cache` may live under `V5_OUT_ROOT`, including capacity for two local checkpoints, or add a Team 5 option that places it on `/nvme/ckpt`. Tell Team 8 whether its log shipper must exclude this directory. | `train_week2.py` fixes the cache below `--out`. Team 7 can move all of `V5_OUT_ROOT`, but cannot independently move only the checkpoint cache. |
| **D6: deployed paths and optional metrics** | Provide the node path to `train_week2.py` and its `week2/` package. Confirm whether the main command must include `--logger-factory g5_adapter:make_writer` and the Team 8 package on `PYTHONPATH`. | Team 7 validates the trainer path and supplies its own `ckpt/` and `common/` packages, but Team 5 owns the harness installation and metrics adapter decision. |

Suggested Team 5 response:

```text
D1: accept / changes: ... ; mainrun.args owner/path: ...
D2: accept one GPU / distributed plan: ...
D3: trainer change / accept temporary hold: ...
D4: implement flags / approved manual alternative: ...
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
| C7 | `--checkpoint-interval-s 600 --watchdog-s 600` | Team 7; Team 5 confirms performance suitability | Sbatch pins both to 600 seconds in production; inherited simulation values are ignored. A different approved value requires a reviewed code/checklist change. |
| C8 | `PYTHONPATH` containing Team 7, plus `OMP_NUM_THREADS=1`, `RUN_ID`, `V5_EVENTS_DIR`, and `V5_RUNS_DIR` | Team 7 | Set explicitly. Team 5 answers the optional metrics path in D6. |
| C9 | `TORCH_NCCL_ASYNC_ERROR_HANDLING=1`, trace buffer `2000`, dump-on-timeout `1`, and an absolute `TORCH_NCCL_DEBUG_INFO_TEMP_FILE` whose directory exists outside `--out` | Team 7 | Trace prefix is `<attempt>/nccl_trace/rank_`; trainer output is `<attempt>/train`. Dumps cannot make `--out` non-empty and cannot mix between attempts. This closes the command-side runbook §14 item. |
| C10 | None of `--steps`, `--interval-s`, `--remote-root`, `--local-root`, `--step-sleep`, or `--drill-dir`; no test crash hooks | Team 7 | Simulation flags remain only in explicit simulation mode. `V5_DRILL_DIR` and `V5_TEST_CRASH_BEFORE_SEAL` are unset before Team 5 starts. |
| C11 | One node and one task bound to one GPU; the exclusive partition reserves all eight node GPUs | Team 5 accepts D2 cost/scope; Team 7 allocation/guard | Sbatch requests 1 node × 1 task × 8 allocated GPUs and passes `srun --gpus-per-task=1`, so Team 5 sees one GPU without starting multiple writers. It validates `SLURM_JOB_NUM_NODES=1`, `SLURM_NTASKS=1`, and `SLURM_GPUS_ON_NODE=8`. D2 remains open. |
| C12 | A defined recovery rule for a claim with no commit | Team 5 | The helper reports `claimed_only`; sbatch holds with exit 78. D3 remains open. |
| C13 | A rollback procedure accepted by both teams | Team 5 trainer; Team 7 operations docs | Unsupported rollback flags hold rather than crash-loop. D4 remains open. |
| C14 | Sufficient local checkpoint-cache space and a log-shipping rule | Team 5 and Team 8, with Team 7 placement | D5 remains open. |

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
2. C1–C14 are satisfied, or both teams record a named, time-bounded exception for an open row.
3. The exact production command runs once on the target environment.
4. That run commits a checkpoint, receives one SIGKILL, requeues automatically, passes `--resume-committed`, and
   restores the committed step with the same checks as `jobs/2026-11-23-dryrun2-kill-drill.md`.
5. The evidence records the command, environment names without secrets, job/restart IDs, committed and restored
   steps, exit codes, `--out`, and NCCL trace path.

**No-go today.** D1–D6 have no recorded Team 5 answers, C12–C14 are open, and the exact command has not completed
the required kill-and-restore drill.

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
