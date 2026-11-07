# Team 7 H100 infrastructure

This repository provides infrastructure, not a model trainer. The supported launch is:

```text
Slurm login host: submit.sh -> sbatch
One Linux x86_64 node, eight allocated H100 GPUs
  launch.sh -> one srun task -> run_container.sh -> one Docker container
    GPU inventory/ECC/CUDA check -> eight-rank NCCL collective
    -> torchrun --standalone --nnodes=1 --nproc-per-node=8 <trainer> --config <config>
```

The former eight Slurm tasks, each starting eight PyTorch workers, could start 64 workers on eight GPUs. The launcher now fixes one node and one Slurm task; PyTorch creates all eight ranks. `torchrun` owns rank/world/rendezvous variables. There is no `scontrol` dependency for a single-node rendezvous.

## What is missing

`train_moe.py` and `configs/config_v1.yaml` are absent from this infrastructure repository and the inspected Team 7 container. Supply the actual model checkout, its validated configuration, data/tokenizer/checkpoints, and any additional Python dependencies. The model must support `--config`, `LOCAL_RANK`, distributed initialization, and one GPU per worker. No placeholder trainer is supplied.

macOS Apple Silicon can run CPU checks under Docker's amd64 emulation and a separate CPU Slurm demo. It cannot validate NVIDIA H100, CUDA, NCCL, NVLink, or actual GPU training. Installing Slurm commands in the PyTorch container does not create a cluster.

## Files

| File | Purpose |
| --- | --- |
| `submit.sh`, `settings.sh` | Validate shared paths, create log directory before sbatch, submit/preview fixed topology |
| `launch.sh` | Allocate one node/task and eight GPUs; forward termination to srun |
| `run_container.sh` | Validate host/runtime/allocation; resolve GPUs to UUIDs; pin image ID; mount files; stop its own container on exit |
| `container_entry.sh` | Check training content, run GPU/NCCL preflight, exec training |
| `gpu_allocation.py` | Convert eight distinct Slurm global GPU IDs to physical H100 UUIDs |
| `gpu_health.sh` | Inventory, zero uncorrected ECC policy, GPU count/type and CUDA tensor checks |
| `collective_smoke.py` | Bounded NCCL/Gloo all-reduce check; not training or a performance benchmark |
| `xid_scan.py` | Optional host dmesg scan against a selected XID policy; unreadable logs return 2 |
| `ckpt.py` | Atomic replacement and RNG restore utility; model integration remains external |
| `tests/` | CPU-safe regression, tensor/checkpoint and separate Slurm queue checks |

## Quick preview (Mac or login host)

```bash
TEAM7_MODE=preflight bash submit.sh --dry-run
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The preview checks paths and prints a submission command. It does not contact Slurm, Docker, or a GPU. It creates the log directory. Default training mode fails before submission until genuine training files are provided.

## GPU cluster submission

Use the Slurm **host**, not a shell in the PyTorch container. First follow the node/runtime setup and mount contract in [the runbook](docs/runbook.md). The default image is `ghcr.io/murthyap63-a11y/team7-h100-env:latest`; prefer a verified digest for deployment.

```bash
# First test infrastructure only. Set real partition/account values for your site.
TEAM7_MODE=preflight bash submit.sh --dry-run --partition=train
TEAM7_MODE=preflight bash submit.sh --partition=train

# Training requires all three shared host directories and the real files.
export TRAIN_DIR=/shared/team7/model
export DATA_DIR=/shared/team7/datasets
export CHECKPOINT_DIR=/shared/team7/checkpoints
export TRAIN_ENTRY=train_moe.py
export TRAIN_CONFIG=configs/config_v1.yaml
bash submit.sh --dry-run --partition=train
bash submit.sh --partition=train
```

The `/shared/...` values above are examples: replace them with existing, shared cluster paths. `--account=...`, `--qos=...`, `--constraint=...`, `--time=...`, `--mem=...`, and `--cpus-per-task=...` are accepted by `submit.sh`. Defaults are 32 CPUs, 128 GiB memory, one hour, exclusive node, partition `train`. Memory must be finite and per node; at least eight CPUs are required. Tune these with the training owner.

Full local queue steps, deployment acceptance checks, cancellation, mount/runtime limitations and recovery are in [docs/runbook.md](docs/runbook.md). A future multi-node design is deliberately documented separately in [docs/MULTINODE_PLAN.md](docs/MULTINODE_PLAN.md).


## Week 2 Gate 2 (14 November 2026)

Week 1 checkpoint design is merged into `ckpt.py` as a durable COMPLETE directory
store; the older file API remains available. `tsai_runner.py` validates CPU job
packages and performs bounded restart from verified state. `tsai_submit.py` and
`tsai_batch.sh` submit the same CPU package through Slurm. These run a CPU
acceptance fixture; the missing GPU model is still required for production training.

```bash
python tsai_runner.py examples/gate2_job.json --validate
python tests/gate2_validate.py --output /tmp/team7-gate2-NEW
python -m unittest discover -s tests -p 'test_*.py' -v
```

Use a Python environment with Torch and NumPy. See [Gate 2 evidence](evidence/VALIDATION.md),
[operations](docs/runbook.md), [job packages](docs/job_package_v1.md),
[queue rules](queue_rules_v1.md), [parallel layout](parallel_layout_v0.md) and
[Week 1 merge provenance](docs/week1_merge.md).
