#!/usr/bin/env bash
#SBATCH --job-name=team7_docker_train
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --gres=gpu:8
#SBATCH --exclusive
#SBATCH --partition=train
#SBATCH --time=01:00:00
#SBATCH --signal=B:TERM@60
#SBATCH --output=logs/train_%j.log
#SBATCH --error=logs/train_%j.err

set -Eeuo pipefail
trap 'rc=$?; echo "[ERROR] launch line $LINENO exited $rc" >&2; exit "$rc"' ERR
[[ -n ${SLURM_JOB_ID:-} ]] || { echo 'Submit from a Slurm host with bash submit.sh; do not bash launch.sh inside Docker.' >&2; exit 2; }
[[ ${SLURM_NNODES:-0} == 1 && ${SLURM_NTASKS:-0} == 1 ]] || { echo 'Requires exactly one node and one Slurm task.' >&2; exit 2; }
: "${INFRA_DIR:?Use submit.sh so the original script directory survives sbatch spooling}"
[[ -r $INFRA_DIR/run_container.sh ]] || { echo 'INFRA_DIR must be shared with the compute node.' >&2; exit 2; }
command -v srun >/dev/null || { echo 'srun required on the Slurm compute host.' >&2; exit 2; }
step_pid=
forward_signal() {
    local code=$1
    trap '' TERM INT
    if [[ -n $step_pid ]]; then
        kill -TERM "$step_pid" 2>/dev/null || true
        wait "$step_pid" || true
    fi
    exit "$code"
}
trap 'forward_signal 143' TERM
trap 'forward_signal 130' INT
echo "[START] job=$SLURM_JOB_ID host=$(hostname) time=$(date -u +%FT%TZ)"
# One step, one container; torchrun alone owns the eight worker ranks.
srun --nodes=1 --ntasks=1 --export=ALL --kill-on-bad-exit=1 --cpu-bind=cores --unbuffered bash "$INFRA_DIR/run_container.sh" &
step_pid=$!
wait "$step_pid"
step_pid=
echo "[SUCCESS] job=$SLURM_JOB_ID completed time=$(date -u +%FT%TZ)"
