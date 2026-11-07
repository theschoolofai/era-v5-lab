# Future multi-node plan (not an executable launch mode)

The original launcher mixed an apparent multi-node rendezvous plan with eight Slurm tasks per node and eight torchrun workers per task. Preserve the intention to scale across nodes, but do not retain that executable topology. The current launch path explicitly rejects more than one node/task.

A future implementation should request N nodes, **one Slurm task per node**, eight GPUs per node, and launch exactly one container/torchrun agent per node with `srun --nodes=N --ntasks=N --ntasks-per-node=1`. Each agent creates eight workers; global world size is N*8. torchrun should provide worker rank/world variables rather than manually setting WORLD_SIZE to the Slurm task count.

Use a fixed-size shared rendezvous with a job-unique ID and a routable endpoint on node zero (derived on the Slurm host using the correct `SLURM_JOB_NODELIST`, not the old `SLURM_JOB_NODELOG` typo). All agents must receive identical rendezvous backend/endpoint/ID and node count; use a unique node rank from SLURM_NODEID for a static-rendezvous design, or let a properly configured c10d rendezvous assign group ranks. Do not use `--standalone` independently on each node; that creates separate jobs.

Each agent must resolve **its step's local allocated global devices** to UUIDs. A multi-node SLURM_JOB_GPUS string must not be interpreted as one global device list for all nodes. The site's GRES ID conventions need explicit validation.

Prerequisites include operator-approved host networking or equivalent routed ports, node-to-node rendezvous reachability, NCCL network/RDMA/InfiniBand device passthrough where needed, matching driver/image/dependencies, shared training/config/data/checkpoint access, adequate CPU/memory limits per node, and rank-safe checkpoint ownership. Single-node private shared memory remains useful inside each container; it does not solve inter-node communication.

Before enabling this path, build a separate submission/compute wrapper with topology checks and coordinated cleanup across nodes. Validate a two-node, sixteen-rank NCCL all-reduce, failure of one worker/node, rendezvous timeout, cancellation, image/mount identity, and model checkpoint restart before attempting real training. No multi-node GPU test was run on this Mac.
