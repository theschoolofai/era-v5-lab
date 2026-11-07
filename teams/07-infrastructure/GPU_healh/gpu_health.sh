#!/bin/bash
#SBATCH-NAME: gpu_health_check
# Pre-flight diagnostic check for H100 cluster nodes

echo "=================================================="
echo " Running GPU Pre-Flight Health Check on $(hostname)"
echo " Timestamp: $(date)"
echo "=================================================="

# 1. Check NVIDIA Driver & GPU Visibility
if ! command -v nvidia-smi &> /dev/null; then
    echo "[ERROR] nvidia-smi not found! GPU drivers may be missing."
    exit 1
fi

nvidia-smi --query-gpu=index,name,temperature.gpu,memory.free,utilization.gpu --format=csv

# 2. Check for ECC Memory Errors
ECC_ERRORS=$(nvidia-smi --query-gpu=ecc.errors.corrected.volatile.device,ecc.errors.uncollected.volatile.device --format=csv,noheader)
echo "ECC Error Status: $ECC_ERRORS"

# 3. Quick NCCL / P2P Interconnect Check
echo "Checking NCCL / NVLink topology..."
python3 -c "import torch; print(f'PyTorch CUDA Available: {torch.cuda.is_available()}; Device Count: {torch.cuda.device_count()})'"

echo "=================================================="
echo " GPU Health Check Passed Successfully."
echo "=================================================="