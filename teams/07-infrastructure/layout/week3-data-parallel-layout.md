## Week 3: Parallel layout and dry run 1:
With a 2-GPU node, this dry run involves testing our orchestration pipeline, distributed backend (NCCL), and parallel execution topologies (such as Tensor Parallelism TP=2 vs. Fully Sharded Data Parallel FSDP / Distributed Data Parallel DDP) using either a scaled-down surrogate model or a synthetic workload. The goal is to measure hardware utilization and Tokens Per Second (TPS) to establish baseline performance before cluster scaling.
### Implementation & Measurement Script
#### Run a benchmark script or Slurm job request to evaluate throughput across layouts:
~~~
#!/bin/bash
#SBATCH --job-name=week3_dryrun
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=2
#SBATCH --gres=gpu:2
#SBATCH --time=00:30:00

export NCCL_DEBUG=INFO
export PYTHONUNBUFFERED=1

echo "=== Testing Layout: FSDP / DDP (2 GPUs) ==/="
torchrun --nproc_per_node=2 train_benchmark.py --parallel_mode=fsdp --batch_size=4 --seq_len=4096

echo "=== Testing Layout: Tensor Parallel (TP=2) ==="
torchrun --nproc_per_node=2 train_benchmark.py --parallel_mode=tp --batch_size=4 --seq_len=4096
~~~
#### Recording Metrics:

Track Global Tokens/sec = $\frac{\text{World Size} \times \text{Batch Size} \times \text{Sequence Length}}{\text{Step Time (seconds)}}$.Log GPU memory footprint (nvidia-smi --query-gpu=memory.used --format=csv) to identify memory bandwidth bottlenecks.

## Operations Runbook (docs/runbook.md): Infrastructure Runbook: 2-Node Lab / 2-GPU Failures

### 1. Node Failures & Slurm Requeue
- **Symptom:** Slurm job enters `NODE_FAIL` or `TIMEOUT` state; node stops responding to heartbeat.
- **Diagnosis:** 
  ```bash
  scontrol show node <node_name>
  dmesg -T | grep -iE "oom|killed|nvrm|hardware"
  
Recovery:

Drain faulty node: scontrol update NodeName=<node_name> State=DRAIN Reason="Hardware fault"

Resubmit job pointing to the latest valid atomic checkpoint:

sbatch --requeue job_script.sh

## NCCL Hangs & Communication Deadlocks
Symptom: Training freezes mid-iteration without throwing exceptions; GPU utilization drops to 0% while CPU sits high or waiting.

Diagnosis:
Enable verbose NCCL logging and inspect distributed process states:	
~~~
export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=INIT,COLL
ps aux | grep python
~~~
Recovery:

#### Force-terminate all orphaned Python/MPI/NCCL processes across nodes:
pkill -9 -f python 
 
Reset InfiniBand/Ethernet socket interfaces if required (sudo systemctl restart networking).

Rerun job with watchdog timeout enabled (TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC=60).

## Bad / Corrupted Checkpoints
Symptom: RuntimeError: Error deserializing torch object or NaN loss spikes immediately after resuming from a checkpoint.



Prevention (Atomic Writes): Never write directly to ckpt.pt. Always write to ckpt.pt.tmp and use os.replace("ckpt.pt.tmp", "ckpt.pt") to guarantee atomic replacement.
#### Recovery:

Verify checkpoint integrity via SHA256 sum or PyTorch archive check:

~~~
import torch
try:
    torch.load("checkpoints/latest_checkpoint.pt", map_location="cpu")
    print("Checkpoint valid.")
except Exception as e:
    print(f"Corrupted checkpoint detected: {e}")
~~~
If corrupted, roll back the symlink/pointer to the previous rolling backup (checkpoint_step_N-1.pt).
	