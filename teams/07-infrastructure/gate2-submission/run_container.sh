#!/usr/bin/env bash
set -Eeuo pipefail
: "${SLURM_JOB_ID:?Requires Slurm allocation}" "${INFRA_DIR:?Use submit.sh}"
source "$INFRA_DIR/settings.sh"
validate_paths
[[ ${SLURM_NNODES:-0} == 1 && ${SLURM_NTASKS:-0} == 1 && ${SLURM_PROCID:-0} == 0 ]] || fail 'Requires one node and one Slurm task (rank zero)'
[[ $(uname -s) == Linux && $(uname -m) == x86_64 ]] || fail 'This image requires an x86_64 Linux NVIDIA compute node'
for tool in docker nvidia-smi python3; do command -v "$tool" >/dev/null || fail "Missing compute-node command: $tool"; done
# DOCKER_CONTEXT overrides DOCKER_HOST in the Docker CLI. Resolve once and pin it.
if [[ -n ${DOCKER_CONTEXT:-} ]]; then
    endpoint=$(docker context inspect "$DOCKER_CONTEXT" --format '{{.Endpoints.docker.Host}}')
else
    endpoint=${DOCKER_HOST:-$(docker context inspect --format '{{.Endpoints.docker.Host}}')}
fi
[[ $endpoint == unix://* ]] || fail 'Docker must use the local compute-node daemon (unix socket)'
unset DOCKER_CONTEXT DOCKER_HOST
engine=(docker --host "$endpoint")
[[ $("${engine[@]}" info --format '{{.OSType}}') == linux ]] || fail 'Docker daemon unavailable or not Linux'
image_id=$("${engine[@]}" image inspect "$DOCKER_IMAGE" --format '{{.Id}}') || fail "Image not cached: $DOCKER_IMAGE. Pull it on each compute node before submission."
[[ $("${engine[@]}" image inspect "$image_id" --format '{{.Os}}/{{.Architecture}}') == linux/amd64 ]] || fail 'Requires a linux/amd64 image'
# STEP_GPUS/JOB_GPUS use global GPU IDs, unlike remapped CUDA_VISIBLE_DEVICES.
export TEAM7_GPU_IDS=${SLURM_STEP_GPUS:-${SLURM_JOB_GPUS:-}}
gpu_uuids=$(python3 "$INFRA_DIR/gpu_allocation.py")
cpus=${SLURM_CPUS_PER_TASK:-0}
memory=${SLURM_MEM_PER_NODE:-0}
[[ $cpus =~ ^[0-9]+$ && $cpus -ge 8 ]] || fail 'At least eight allocated CPU cores are required'
[[ $memory =~ ^[0-9]+$ && $memory -gt 0 ]] || fail 'Use a finite per-node --mem allocation (not --mem=0 or --mem-per-cpu)'
affinity=$(python3 -c 'import os; print(",".join(map(str, sorted(os.sched_getaffinity(0)))))')
[[ -n $affinity ]] || fail 'Cannot determine Slurm CPU affinity'
# Unique name avoids stopping an unrelated container on a name collision.
state_dir=$(mktemp -d)
name="team7-${SLURM_JOB_ID}-${SLURM_STEP_ID:-batch}-${state_dir##*/}"
started=0
cleanup() {
    local rc=$?
    trap - EXIT TERM INT
    if [[ $started == 1 ]]; then
        # Daemon-owned processes need explicit cleanup; scancel alone is insufficient.
        if ! "${engine[@]}" stop --time 10 "$name" >/dev/null 2>&1; then
            "${engine[@]}" rm --force "$name" >/dev/null 2>&1 || true
        fi
    fi
    rm -rf -- "$state_dir"
    echo "[EXIT] job=$SLURM_JOB_ID status=$rc time=$(date -u +%FT%TZ)" >&2
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
args=(run --rm --init --name "$name" --pull=never
    --gpus "\"device=$gpu_uuids\"" --shm-size=16g
    --ulimit memlock=-1 --ulimit stack=67108864
    --cpus "$cpus" --cpuset-cpus "$affinity" --memory "${memory}m" --memory-swap "${memory}m"
    --user "$(id -u):$(id -g)"
    --mount "type=bind,src=$INFRA_DIR,dst=/opt/team7-infra,readonly"
    -e PYTHONUNBUFFERED=1 -e PYTHONDONTWRITEBYTECODE=1 -e HOME=/tmp
    -e "OMP_NUM_THREADS=$((cpus / 8))" -e TEAM7_EXPECTED_GPUS=8
    -e CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
    -e "NVIDIA_VISIBLE_DEVICES=$gpu_uuids" -e NVIDIA_DRIVER_CAPABILITIES=compute,utility
    -e "TEAM7_MODE=$TEAM7_MODE" -e "TRAIN_ENTRY=$TRAIN_ENTRY" -e "TRAIN_CONFIG=$TRAIN_CONFIG")
if [[ $TEAM7_MODE == train ]]; then
    args+=(--mount "type=bind,src=$TRAIN_DIR,dst=/workspace/training,readonly"
        --mount "type=bind,src=$DATA_DIR,dst=/workspace/datasets,readonly"
        --mount "type=bind,src=$CHECKPOINT_DIR,dst=/workspace/checkpoints"
        -e DATA_DIR=/workspace/datasets -e CHECKPOINT_DIR=/workspace/checkpoints
        --workdir /workspace/training)
else
    args+=(--workdir /tmp)
fi
echo "[CONTAINER] job=$SLURM_JOB_ID image=$DOCKER_IMAGE id=$image_id GPUs=$gpu_uuids cpus=$cpus memory_MiB=$memory mode=$TEAM7_MODE"
"${engine[@]}" image inspect "$image_id" --format 'image-id={{.Id}} digests={{json .RepoDigests}}'
# Pin the resolved image ID so a concurrent retag cannot change this run.
# Background + wait allows shell traps to stop the daemon-owned container.
started=1
"${engine[@]}" "${args[@]}" --entrypoint bash "$image_id" /opt/team7-infra/container_entry.sh &
pid=$!
wait "$pid"
