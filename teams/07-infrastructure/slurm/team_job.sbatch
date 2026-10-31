#!/bin/bash
# A team job (scaling-ladder run, benchmark, eval). Submit with the team's account:
#   sbatch --account=arch --export=ALL,RUN_ID=ladder-1 team_job.sbatch
# It can be preempted by the main run at any time; it saves on SIGTERM and is requeued, so the team
# loses at most the work since its last save.
# Time limit: Slurm sends SIGUSR1 to this script 300 s before --time runs out (B: only the batch shell). The
# wrapper passes it to the trainers, they save and exit 75, and Slurm requeues the job with the same id, so a
# long job runs in segments and loses nothing (Max's self-requeue, team 07). Set the lead to at least
# 2 x the save time + 60 s. A longer --time than the QOS MaxWall is refused at submit.
#SBATCH --job-name=v5-team
#SBATCH --qos=normal
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --gpus-per-node=8
#SBATCH --requeue
#SBATCH --time=04:00:00
#SBATCH --signal=B:USR1@300
#SBATCH --open-mode=append
#SBATCH --output=/var/log/v5/logs/%x-%j.out
set -u
source /etc/v5/node.env 2>/dev/null || true
export RUN_ID="${RUN_ID:-team-$SLURM_JOB_ID}"
export V5_EVENTS_DIR="${V5_EVENTS_DIR:-/var/log/v5/events}"
export OMP_NUM_THREADS=1                       # part of the bit-equal environment (ADR 0001 §1)
export V5_DEVICE="${V5_DEVICE:-cuda}"           # node.env sets cpu in the Docker test
export V5_DRILL_DIR="/s3/drills/$RUN_ID"           # test-only hooks; the folder does not exist in production
export MASTER_ADDR="$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -1)"
export MASTER_PORT=$((20000 + SLURM_JOB_ID % 20000))
export GLOO_SOCKET_IFNAME="${GLOO_SOCKET_IFNAME:-eth0}"
# The trainer: V5_TRAIN_SCRIPT (Team 05's real one on EC2); default is the test trainer in support/simulation/trainer/.
exec /opt/venv/bin/python /opt/v5/queue/job_queue.py run -- --ntasks-per-node="$SLURM_NTASKS_PER_NODE" -- \
  --run-id "$RUN_ID" --remote-root "${V5_REMOTE_ROOT:-/s3/ckpt}" --local-root /nvme/ckpt \
  --steps "${STEPS:-1000}" --interval-s "${INTERVAL_S:-600}" --step-sleep "${STEP_SLEEP:-0}" \
  ${TRAIN_EXTRA:-}
