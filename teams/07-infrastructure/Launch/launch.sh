#!/bin/bash
#SBATCH --job-name=team7_docker_train
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --gres=gpu:8
#SBATCH --partition=train
#SBATCH --output=logs/train_%j.log
#SBATCH --error=logs/train_%j.err

echo "=================================================="
echo " Slurm Job Started on Host: $(hostname)"
echo " Job ID: $SLURM_JOB_ID"
echo "=================================================="

# Define your Docker image name
DOCKER_IMAGE="team7_infra:latest"

# Gather Master Node address for NCCL/PyTorch distributed communication
export MASTER_ADDR=$(scontrol show hostnames $SLURM_JOB_NODELOG | head -n 1)
export MASTER_PORT=29500
export WORLD_SIZE=$SLURM_NTASKS

echo "Master Address: $MASTER_ADDR"
echo "World Size (Total GPUs): $WORLD_SIZE"

# Run the workload inside the Docker container with full GPU (NVLink/NCCL) passthrough
srun docker run --rm \
    --gpus all \
    --net=host \
    --ipc=host \
    -v /shared/storage/datasets:/workspace/datasets \
    -v /shared/storage/checkpoints:/workspace/checkpoints \
    -e MASTER_ADDR=$MASTER_ADDR \
    -e MASTER_PORT=$MASTER_PORT \
    -e WORLD_SIZE=$WORLD_SIZE \
    -e SLURM_NODEID=$SLURM_NODEID \
    $DOCKER_IMAGE \
    bash -c "./gpu_health.sh && torchrun \
        --nproc_per_node=8 \
        --nnodes=$SLURM_NNODES \
        --node_rank=$SLURM_NODEID \
        --master_addr=$MASTER_ADDR \
        --master_port=$MASTER_PORT \
        train_moe.py --config configs/config_v1.yaml"

echo "=================================================="
echo " Docker containerized training job completed."
echo "=================================================="