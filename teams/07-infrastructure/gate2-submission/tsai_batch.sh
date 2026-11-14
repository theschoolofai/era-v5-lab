#!/usr/bin/env bash
set -Eeuo pipefail
[[ ${SLURM_JOB_ID:-} && ${SLURM_NNODES:-} == 1 && ${SLURM_NTASKS:-} == 1 ]] || { echo 'TSAI CPU batch requires one Slurm node/task' >&2; exit 2; }
[[ $# == 4 ]] || exit 2
py=$1; repo=$2; package=$3; run_dir=$4
step_pid=
stop() {
    trap '' TERM INT
    if [[ -n $step_pid ]]; then
        kill -TERM "$step_pid" 2>/dev/null || true
        wait "$step_pid" || true
    fi
    exit "$1"
}
trap 'stop 143' TERM
trap 'stop 130' INT
export SLURM_EXPORT_ENV=ALL
# One srun task contains the supervisor; the supervisor starts one CPU worker.
srun --nodes=1 --ntasks=1 --kill-on-bad-exit=1 "$py" "$repo/tsai_runner.py" "$package" --run-dir "$run_dir" &
step_pid=$!
wait "$step_pid"
