# Team 7 parallel layout v0 — Gate 2

Date: 2 November 2026. Gate 2: Saturday 14 November 2026.

## Executable layouts

| Path | Nodes | Slurm tasks | Containers | Worker processes | Validation |
|---|---:|---:|---:|---:|---|
| `tsai_runner.py` local CPU | 1 host | none | none | 1 CPU worker | Tested on macOS ARM64 |
| `tsai_submit.py` CPU | 1 | 1 | worker already runs in local Docker Slurm demo | 1 CPU worker plus supervisor | Tested on Linux ARM64 through Slurm |
| Existing `submit.sh` H100 path | 1 | 1 | 1 Docker container | torchrun creates 8 GPU ranks | Shell/argument regressions only; hardware test pending |

CPU fixture: FP32 model and losses, AdamW, StepLR, dropout; one Torch compute thread, deterministic algorithms, batch 8, dataset 257 IDs, epoch permutation with private Torch generator. The sampler checkpoint stores permutation, generator state, epoch, in-epoch cursor and total consumed count. Save at completed optimizer-step boundaries every 100 steps, after scheduler advance. No DataLoader worker prefetch, gradient accumulation, mixed precision, or distributed optimizer state is exercised.

The CPU Slurm demo has c1 and c2; acceptance uses one node/task and one CPU. A separate user1/user2 queue test occupies both nodes temporarily. Docker hosts the Slurm controller and workers; no nested Docker socket is passed to jobs.

## Existing eight-H100 contract

`submit.sh -> launch.sh -> one srun task -> run_container.sh -> container_entry.sh -> torchrun --standalone --nnodes=1 --nproc-per-node=8`.

Slurm requests one node, one task, eight physical H100 GPUs, 32 CPUs and 128 GiB RAM by default. The wrapper resolves eight distinct allocated global GPU devices to UUIDs and passes only those UUIDs to Docker. Local worker rank 0..7 selects CUDA device 0..7. torchrun owns rank/world variables. Do not combine eight Slurm tasks with eight workers per task. GPU preflight and eight-rank NCCL smoke precede the real trainer. Default OMP threads are allocated CPUs divided by eight. See `docs/week1_runbook.md` for mounts, numeric user ownership, runtime assumptions and cleanup limitations.

The infrastructure fixes launch topology; it does not choose the absent model's DP/TP/EP/PP/FSDP strategy. The model owner must supply that mapping and prove checkpoint ownership. `ckpt.save` explicitly refuses an initialized distributed world larger than one. TSAI v1 CPU packages reject GPU resource requests rather than applying the CPU checkpoint writer to distributed training.

## Checkpoint ownership and consistency

One supervisor lock per run, inherited by its worker, prevents concurrent writers on the same shared run directory. One checkpoint writer serializes model, optimizer, scheduler, global Python/NumPy/Torch RNG states, training mode and sampler state. Files and directories are fsynced before same-filesystem publication by rename. Readers require directory name, COMPLETE marker, manifest hash, state size/hash, serialization/schema and config identity to agree. This relies on filesystem support for atomic rename, durable fsync and advisory flock; validate the actual shared filesystem before deployment.

For distributed work, every participating rank needs correct RNG/sampler/shard state, a coordinated safe-step barrier, rank-local payloads, and one coordinator publishing COMPLETE only after all rank manifests are durable. A rank-zero weights-only save is insufficient. GPU kernels, CUDA RNG, AMP scaler, distributed reductions, topology changes and partial rank failure remain untested here.

## Future multi-node work

Follow `docs/MULTINODE_PLAN.md`: N Slurm tasks across N nodes, one container and torchrun agent per node, eight workers per agent, global world size 8N, shared job-unique rendezvous. This is a design, not an enabled launch path. Validate two-node collectives, site networking, device mapping, rank-safe checkpoints and loss/data-ID recovery before enabling it.
