#!/bin/bash
# The V5 main run (ADR 0002 §5). The same script chooses fresh start or committed resume on every attempt.
#
# V5_TRAINER modes:
#   week2 (default) Team 05's single-GPU harness/train_week2.py. Required settings:
#       V5_TRAIN_SCRIPT=/path/to/train_week2.py
#       V5_TRAIN_ARGS_FILE=/path/to/mainrun.args   # one --option=value argument per line
#   sim             Team 07's test trainer. Requires V5_SIMULATION=1; run_sim.py sets both test values explicitly.
#
# train_week2.py does not support the documented rollback flags (--from-step, --skip, --branch) yet. The
# main-run command therefore refuses them rather than entering a crash loop; see the main-run checklist (PR #819, draft, not merged).
#
# Team 05's current trainer is one process using one GPU. The gpu partition is node-exclusive, so this job
# reserves all 8 GPUs on one node and binds its one task to one GPU. Team 5 must accept that temporary cost or
# provide a distributed plan; see the main-run checklist (PR #819, draft) D2.
#SBATCH --job-name=v5-mainrun
#SBATCH --account=mainrun
#SBATCH --qos=mainrun
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=/var/log/v5/logs/%x-%j.out
set -u
source /etc/v5/node.env 2>/dev/null || true
export RUN_ID="${RUN_ID:-v5main}"
export V5_EVENTS_DIR="${V5_EVENTS_DIR:-/var/log/v5/events}"
export V5_RUNS_DIR="${V5_RUNS_DIR:-/var/log/v5/runs}"
export V5_REMOTE_ROOT="${V5_REMOTE_ROOT:-/shared/ckpt}"
export OMP_NUM_THREADS=1                       # part of the bit-equal environment (ADR 0001 §1)
export V5_DEVICE="${V5_DEVICE:-cuda}"          # node.env sets cpu in the Docker test
export MASTER_ADDR="$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -1)"
export MASTER_PORT=$((20000 + SLURM_JOB_ID % 20000))
export GLOO_SOCKET_IFNAME="${GLOO_SOCKET_IFNAME:-eth0}"
export TORCH_NCCL_ASYNC_ERROR_HANDLING=1 TORCH_NCCL_TRACE_BUFFER_SIZE=2000 TORCH_NCCL_DUMP_ON_TIMEOUT=1
V5_TRAINER="${V5_TRAINER:-week2}"
PY=/opt/venv/bin/python
QUEUE=/opt/v5/queue/job_queue.py

# Exit 78 maps to a held Slurm job. Record the reason in the log, the job comment and a job.held event (the Q-02
# monitoring counter). The event is best effort: it must never change the exit code.
hold() {
  local msg="V5 HELD (78): $*"
  echo "$msg" >&2
  scontrol update JobId="${SLURM_JOB_ID:-}" Comment="${msg//\"/\'}" >/dev/null 2>&1 || true
  "$PY" "$QUEUE" hold-event --reason "$*" >/dev/null 2>&1 || true
  exit 78
}

[[ "$RUN_ID" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] \
  || hold "RUN_ID must begin with a letter or digit and contain only letters, digits, dots, dashes and underscores"

if [[ "$V5_TRAINER" == sim ]]; then
  [[ "${V5_SIMULATION:-}" == 1 ]] \
    || hold "V5_TRAINER=sim is test-only and also requires V5_SIMULATION=1"
  # Never let an inherited production trainer receive simulation-only flags.
  unset V5_TRAIN_SCRIPT
  export V5_DRILL_DIR="${V5_DRILL_DIR:-/s3/drills/$RUN_ID}"
  exec "$PY" "$QUEUE" run -- --ntasks-per-node="$SLURM_NTASKS_PER_NODE" -- \
    --run-id "$RUN_ID" --remote-root "$V5_REMOTE_ROOT" --local-root /nvme/ckpt \
    --steps "${STEPS:-100000}" --interval-s "${INTERVAL_S:-1800}" \
    --watchdog-s "${WATCHDOG_S:-600}" --step-sleep "${STEP_SLEEP:-0}" --drill-dir "$V5_DRILL_DIR" \
    ${TRAIN_EXTRA:-}
fi

[[ "$V5_TRAINER" == week2 ]] || hold "V5_TRAINER must be week2 or sim, not '$V5_TRAINER'"
unset V5_DRILL_DIR V5_TEST_CRASH_BEFORE_SEAL
export V5_DEVICE=cuda
[[ -z "${TRAIN_EXTRA:-}" ]] \
  || hold "TRAIN_EXTRA is simulation-only; put every reviewed Team 05 option in V5_TRAIN_ARGS_FILE"
[[ "${SLURM_NTASKS:-}" == 1 ]] \
  || hold "train_week2.py requires exactly one task (this job has ${SLURM_NTASKS:-unset})"
[[ "${SLURM_JOB_NUM_NODES:-}" == 1 ]] \
  || hold "train_week2.py requires exactly one node (this job has ${SLURM_JOB_NUM_NODES:-unset})"
[[ "${SLURM_GPUS_ON_NODE:-}" == 8 ]] \
  || hold "the exclusive gpu partition must allocate all 8 GPUs (this job has ${SLURM_GPUS_ON_NODE:-unset})"
[[ "$(basename -- "${V5_TRAIN_SCRIPT:-}")" == train_week2.py && -f "${V5_TRAIN_SCRIPT:-}" ]] \
  || hold "V5_TRAIN_SCRIPT must name Team 05's train_week2.py (now '${V5_TRAIN_SCRIPT:-}')"
[[ -r "${V5_TRAIN_ARGS_FILE:-}" ]] \
  || hold "V5_TRAIN_ARGS_FILE must name Team 05's readable main-run argument file (now '${V5_TRAIN_ARGS_FILE:-}')"

out_root="${V5_OUT_ROOT:-/var/log/v5/out}"
[[ "$out_root" == /* ]] || hold "V5_OUT_ROOT must be absolute, not '$out_root'"

# One argument per non-comment line. Keeping each line as one array element supports spaces without eval.
inputs=()
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line#"${line%%[![:space:]]*}"}"
  line="${line%"${line##*[![:space:]]}"}"
  [[ -z "$line" || "$line" == \#* ]] && continue
  [[ "$line" == --* ]] || hold "V5_TRAIN_ARGS_FILE line is not a --option argument: '$line'"
  inputs+=("$line")
done < "$V5_TRAIN_ARGS_FILE"

# These are Team 05's decisions and inputs. Requiring explicit values makes an incomplete command hold before
# allocating training work instead of crashing three times in argparse. Team 05 reviews this list in the checklist.
required=(--config --runtime --resolution --tokenizer-release --tokenizer --byte-table --train-data --heldout-data
          --heldout-sources --heldout-sha256 --heldout-report --seed)
missing=()
for flag in "${required[@]}"; do
  occurrences=0
  valued=0
  for arg in "${inputs[@]}"; do
    if [[ "${arg%%=*}" == "$flag" ]]; then
      occurrences=$((occurrences + 1))
      [[ "$arg" == *=?* ]] && valued=$((valued + 1))
    fi
  done
  (( occurrences == 0 || valued == 0 )) && missing+=("$flag")
  (( occurrences <= 1 )) || hold "V5_TRAIN_ARGS_FILE sets $flag more than once"
done
(( ${#missing[@]} == 0 )) || hold "V5_TRAIN_ARGS_FILE needs explicit values for: ${missing[*]}"

# mainrun.sbatch owns these invariants. The argument file is a reviewed allowlist: every accepted Team 05 option
# must use its full argparse name, so unique-prefix abbreviations cannot silently change the command.
owned=(--out --run-id --checkpoint-store --checkpoint-interval-s --checkpoint-at-start --resume --resume-committed
       --watchdog-s --device --smoke --no-checkpoint)
unsupported=(--from-step --skip --branch --allow-env-change --stop-after --smoke-steps --smoke-seq-len
             --smoke-batch-size)
value_optional=(--lr --logger-factory --expert-load-every)
boolean_optional=(--consolidate-step-checks --no-consolidate-step-checks)
optional=("${value_optional[@]}" "${boolean_optional[@]}")
allowed=("${required[@]}" "${optional[@]}")
for flag in "${optional[@]}"; do
  occurrences=0
  for arg in "${inputs[@]}"; do
    [[ "${arg%%=*}" == "$flag" ]] && occurrences=$((occurrences + 1))
  done
  (( occurrences <= 1 )) || hold "V5_TRAIN_ARGS_FILE sets $flag more than once"
done
boolean_count=0
for arg in "${inputs[@]}"; do
  for flag in "${boolean_optional[@]}"; do
    [[ "${arg%%=*}" == "$flag" ]] && boolean_count=$((boolean_count + 1))
  done
done
(( boolean_count <= 1 )) || hold "choose only one of --consolidate-step-checks and --no-consolidate-step-checks"
for arg in "${inputs[@]}"; do
  name="${arg%%=*}"
  for flag in "${owned[@]}"; do
    [[ "$flag" == "$name"* ]] && hold "'$arg' may not override mainrun.sbatch's $flag"
  done
  for flag in "${unsupported[@]}"; do
    [[ "$flag" == "$name"* ]] && hold "train_week2.py main runs do not support $flag"
  done
  exact=0
  for flag in "${allowed[@]}"; do
    [[ "$name" == "$flag" ]] && exact=1
  done
  if (( exact == 0 )); then
    for flag in "${allowed[@]}"; do
      [[ "$flag" == "$name"* ]] && hold "'$arg' abbreviates reviewed option $flag; spell every option in full"
    done
    hold "'$arg' is not an approved train_week2.py main-run option; Team 05 must review the allowlist"
  fi
  for flag in "${value_optional[@]}"; do
    [[ "$name" == "$flag" && "$arg" != *=?* ]] && hold "$flag requires a non-empty --option=value argument"
  done
  for flag in "${boolean_optional[@]}"; do
    [[ "$name" == "$flag" && "$arg" != "$flag" ]] && hold "$flag is a bare switch and does not take a value"
  done
done

export V5_TRAIN_SCRIPT                         # job_queue.py reads this when its process starts
export PYTHONPATH="/opt/v5${PYTHONPATH:+:$PYTHONPATH}"

# Read the shared store before choosing a start mode. Any read error holds; it never guesses "fresh".
mode="$("$PY" "$QUEUE" start-mode --remote-root "$V5_REMOTE_ROOT" --run-id "$RUN_ID")" \
  || hold "cannot determine the start mode from $V5_REMOTE_ROOT; check the store, then release the job"
case "$mode" in
  fresh) start=(--checkpoint-at-start) ;;
  resume) start=(--resume-committed) ;;
  claimed_only) hold "$V5_REMOTE_ROOT/$RUN_ID has a claim but no committed checkpoint; confirm in sacct that the" \
    "earlier job for this run ID has ended, then resubmit with a new RUN_ID; nothing was committed" ;;
  *) hold "job_queue.py start-mode returned '$mode'" ;;
esac

# Keep the trainer's fresh --out separate from the per-attempt NCCL trace directory.
attempt="$out_root/$RUN_ID/$SLURM_JOB_ID.${SLURM_RESTART_COUNT:-0}"
mkdir -p "$attempt/nccl_trace" || hold "cannot create $attempt/nccl_trace"
export TORCH_NCCL_DEBUG_INFO_TEMP_FILE="$attempt/nccl_trace/rank_"
echo "V5 main run: Team 05 trainer, start mode $mode, out $attempt/train" >&2

# 600 s is pinned for the interval and the watchdog. Retention (--keep 9) is sized for it, so changing it means
# editing docs/checkpoint_interval.md §5 (still provisional) and the retention step (C15 in the PR #819 checklist) as well.
exec "$PY" "$QUEUE" run -- --ntasks-per-node="$SLURM_NTASKS_PER_NODE" --gpus-per-task=1 -- \
  "${inputs[@]}" \
  --device cuda --run-id "$RUN_ID" --checkpoint-store "$V5_REMOTE_ROOT" \
  --checkpoint-interval-s 600 --watchdog-s 600 \
  --out "$attempt/train" "${start[@]}"
