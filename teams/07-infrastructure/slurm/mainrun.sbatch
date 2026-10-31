#!/bin/bash
# The V5 main run (ADR 0002 §5). The same script for every restart: it always resumes from latest.json.
# Rollback: sbatch --export=ALL,TRAIN_EXTRA="--from-step K --skip N --branch B" mainrun.sbatch
#
# EC2 defaults: 8 GPUs and 8 ranks per node. The Docker test overrides on the command line
# (sbatch --ntasks-per-node=2 --gpus-per-node=2 ...), which takes precedence over these lines.
# In simple words: top priority (qos mainrun), whole nodes, and "requeue me" if anything goes wrong,
# so nobody has to type a restart command at 4 a.m.
#SBATCH --job-name=v5-mainrun
#SBATCH --account=mainrun
#SBATCH --qos=mainrun
#SBATCH --partition=gpu
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=/var/log/v5/logs/%x-%j.out
set -u
source /etc/v5/node.env 2>/dev/null || true
export RUN_ID="${RUN_ID:-v5main}"
export V5_EVENTS_DIR="${V5_EVENTS_DIR:-/var/log/v5/events}"
export OMP_NUM_THREADS=1                       # part of the bit-equal environment (ADR 0001 §1)
export V5_DEVICE="${V5_DEVICE:-cuda}"           # node.env sets cpu in the Docker test
export V5_DRILL_DIR="/s3/drills/$RUN_ID"           # test-only hooks; the folder does not exist in production
export MASTER_ADDR="$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -1)"
export MASTER_PORT=$((20000 + SLURM_JOB_ID % 20000))
export GLOO_SOCKET_IFNAME="${GLOO_SOCKET_IFNAME:-eth0}"
export TORCH_NCCL_ASYNC_ERROR_HANDLING=1 TORCH_NCCL_TRACE_BUFFER_SIZE=2000 TORCH_NCCL_DUMP_ON_TIMEOUT=1
# The trainer: V5_TRAIN_SCRIPT (Team 05's real one on EC2); default is the test trainer in support/simulation/trainer/.
exec /opt/venv/bin/python /opt/v5/queue/job_queue.py run -- --ntasks-per-node="$SLURM_NTASKS_PER_NODE" -- \
  --run-id "$RUN_ID" --remote-root "${V5_REMOTE_ROOT:-/s3/ckpt}" --local-root /nvme/ckpt \
  --steps "${STEPS:-100000}" --interval-s "${INTERVAL_S:-1800}" \
  --watchdog-s "${WATCHDOG_S:-600}" --step-sleep "${STEP_SLEEP:-0}" --drill-dir "/s3/drills/$RUN_ID" \
  ${TRAIN_EXTRA:-}
