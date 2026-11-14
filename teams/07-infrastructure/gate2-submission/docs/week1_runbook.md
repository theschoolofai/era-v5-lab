# Team 7 Week 1 launch and validation runbook (historical)

**Historical record, not the current portable Gate 2 procedure.**
Prefer [`docs/runbook.md`](runbook.md) for current CPU Gate 2 commands.
Original developer-specific absolute paths have been replaced with environment
variables. To adapt these older commands set `TEAM7_INFRA_DIR` to the absolute
path of `teams/07-infrastructure` and `SLURM_DEMO_DIR` to your separately
installed Docker Slurm demo checkout. Both resources must actually exist.

```bash
export TEAM7_INFRA_DIR="$(pwd)/teams/07-infrastructure"  # from shared repo root
export SLURM_DEMO_DIR=/path/to/local/slurm-docker-cluster
```

## 1. Verified local project locations

The existing host Git checkout is:

```text
$TEAM7_INFRA_DIR
origin: https://github.com/murthyap63-a11y/Team7-infrastructure
base commit: 7beee4005f0b5fed3df4b993f2ded7f6f37ab6a6
```

The existing container is `intelligent_proskuriakova`, created from `ghcr.io/murthyap63-a11y/team7-h100-env:latest`, with the project at `/workspace/infrastructure`. Docker inspection found **no host bind mounts**. Its repository matched the host checkout's base commit; its only original working-tree changes were executable permissions. The host checkout already had partial fixes from an earlier session; those changes were preserved and completed. Updated project files are also copied into that stopped container's writable layer. This does not rebuild or publish the image.

Use the host checkout as the editable source of truth. Changing files in a container does not update a host checkout or the registry image. On the GPU cluster the corrected infrastructure is explicitly bind-mounted at `/opt/team7-infra`, so the image's older embedded launch script is not used.

## 2. Local shell and CPU checks

From the host checkout:

```bash
cd "$TEAM7_INFRA_DIR"
for script in ./*.sh; do bash -n "$script"; done
python3 -m unittest discover -s tests -p 'test_*.py' -v
TEAM7_MODE=preflight bash submit.sh --dry-run
# Expected error until the model/data/checkpoint paths and real files are supplied:
bash submit.sh --dry-run
```

Regression tests stub GPU/Docker commands only at the orchestration boundary. They test topology rejection, GPU mapping, runtime arguments, resource caps, exit codes, ECC failures, and TERM cleanup. These results are not GPU validation.

CPU tests use the cached linux/amd64 Team 7 image under emulation. No GPU flag or Slurm executable is required:

```bash
open -a Docker
# Wait until docker info succeeds.
docker info >/dev/null
INFRA_PATH="$PWD"
docker run --rm --platform linux/amd64   --hostname team7-cpu-smoke --add-host team7-cpu-smoke:127.0.0.1   --user "$(id -u):$(id -g)"   --mount "type=bind,src=$INFRA_PATH,dst=/opt/team7-infra,readonly"   -e PYTHONDONTWRITEBYTECODE=1 -e HOME=/tmp   --entrypoint bash ghcr.io/murthyap63-a11y/team7-h100-env:latest   -c 'python3 /opt/team7-infra/tests/cpu_smoke.py && torchrun --standalone --nnodes=1 --nproc-per-node=2 /opt/team7-infra/collective_smoke.py --backend gloo'
```

Expect CUDA unavailable, zero GPUs, restored CPU training losses exactly equal for five utility-test steps, and Gloo ranks 0/1 with sum 3.0. Those small steps exercise the checkpoint utility, not the missing MoE trainer. An explicit hostname mapping prevents the older PyTorch rendezvous code from advertising an unresolvable container hostname. Do not use `--network none` without such a mapping.

## 3. Separate local Slurm CPU queue: user1 and user2

The inspected cluster's actual Compose directory is the **nested** checkout:

```text
$SLURM_DEMO_DIR
```

Do not run a second copy of the parent checkout: both define fixed container names. Do not mount the Docker socket into the training image or add Slurm daemons to it. This queue exercise uses independent controller/database/CPU-worker containers and never calls the GPU launcher.

Start the existing containers without rebuilding, recreating, or deleting volumes:

```bash
docker start mysql slurmdbd slurmctld   slurm-docker-cluster-cpu-worker-1 slurm-docker-cluster-cpu-worker-2
docker exec slurmctld scontrol ping
docker exec slurmctld sinfo -Nel
docker exec slurmctld squeue
```

Wait for the controller to respond and c1/c2 to register. After a Docker VM restart, nodes may be DOWN with reason `Node unexpectedly rebooted`. Inspect the reason and slurmd health first:

```bash
docker exec slurmctld scontrol show nodes c1,c2
docker ps --format '{{.Names}} {{.Status}}'
# Only in this local demo, for that reboot reason, with healthy workers/no jobs:
docker exec slurmctld scontrol update NodeName=c1,c2 State=RESUME
```

The existing cluster has user1 UID/GID 1002 and user2 UID/GID 1003 on the controller and both workers. Verify them before submitting:

```bash
for service in slurmctld slurm-docker-cluster-cpu-worker-1 slurm-docker-cluster-cpu-worker-2; do
  docker exec "$service" getent passwd user1 user2
  docker exec "$service" getent group user1 user2
done
```

If recreating this demo on a fresh machine, use the nested checkout with `GPU_ENABLE=false` and two CPU workers:

```bash
cd "$SLURM_DEMO_DIR"
GPU_ENABLE=false CPU_WORKER_COUNT=2 docker compose build slurmdbd
GPU_ENABLE=false CPU_WORKER_COUNT=2 docker compose up -d mysql slurmdbd slurmctld cpu-worker
```

Only for fresh demo containers lacking these identities, create the same identities in all three containers. First check `getent passwd 1002 1003` and `getent group 1002 1003`; resolve collisions rather than overwriting an existing user. Then, for each of the three service names, run:

```bash
# Replace SERVICE with one container name from the verification loop.
docker exec SERVICE groupadd -g 1002 user1
docker exec SERVICE useradd -m -u 1002 -g 1002 -s /bin/bash user1
docker exec SERVICE groupadd -g 1003 user2
docker exec SERVICE useradd -m -u 1003 -g 1003 -s /bin/bash user2
```

Skip identities already present and matching. These manual demo identities live in container writable layers; recreation requires repeating them or adding them to a demo image. The inspected cluster has AccountingStorageEnforce=none, so no account association was needed for the queue test. If you enable association enforcement, create authorized test associations with the cluster administrator before testing; this runbook does not change accounting policy.

Run the included test from the infrastructure checkout, with exactly two idle CPU nodes and no other jobs:

```bash
cd "$TEAM7_INFRA_DIR"
python3 tests/slurm_queue_smoke.py
```

The test creates its own timestamped directories under the shared `/data` volume, submits a short exclusive two-node CPU job as user1, then submits a one-node job as user2. Expect user1 RUNNING, user2 PENDING(Resources), then both COMPLETED with ExitCode=0:0 and the correct user identities in output. It cancels only the job IDs it created during cleanup. No job, volume, or output directory is deleted. This checks resource queueing, not fair-share or per-account limits.

Successful runs on 30 October 2026: jobs **23/24**, followed by final-script verification jobs **25 (user1)** and **26 (user2)**. The queue script prints exact output locations for future runs.

## 4. Real GPU cluster prerequisites

Before submitting, the cluster operator must confirm:

- An accessible Slurm login host and one Linux x86_64 compute node with eight physical H100 GPUs (MIG disabled for this launcher), a suitable partition, account/QoS, and shared storage.
- Slurm `sbatch` on the submit host, `srun` on compute, and `python3` on both. The PyTorch image does not need Slurm clients.
- A driver compatible with the image's CUDA stack, NVIDIA Container Toolkit configured for the local Docker daemon, permission to run Docker, and approved use of Docker within Slurm jobs. Verify runtime with the actual image; do not assume installing Docker alone is enough.
- The Docker daemon is on the allocated compute node, reached through a local Unix socket, and sees the same absolute bind-source paths as the Slurm task. Remote daemons, Docker-in-Docker, and a Docker socket forwarded from another host are unsupported.
- Slurm publishes eight global physical device indices/full UUIDs through `SLURM_STEP_GPUS` or `SLURM_JOB_GPUS`. The launcher resolves these with host `nvidia-smi`. It refuses missing, duplicate, partial, unknown, non-H100, or nonphysical devices; it never guesses using cgroup-remapped CUDA indices.
- The site's device-ID mapping agrees with host NVIDIA indices/UUIDs. Slurm GRES IDs may depend on site configuration; the operator must verify the eight resolved UUIDs match the allocated devices. Provide a site-specific resolver before use if these conventions differ.
- The corrected infrastructure, real training checkout, dataset and checkpoint directory exist at identical shared paths on login and compute nodes. UID/GID permissions must allow a numeric-UID container to read inputs and write checkpoints.
- Default resource request: exclusive node, 32 CPUs, 128 GiB RAM, one hour. Adjust finite per-node `--mem` and CPU count for the workload. `--mem=0` and per-CPU memory requests are unsupported here. Docker receives CPU quota, inherited Slurm CPU affinity, and a memory/swap cap matching the allocation.

The Docker daemon owns its processes outside the normal Slurm task process tree. Explicit GPU/CPU/memory limits and shell cleanup help, but they are not a substitute for site integration: accounting may not include container usage, and SIGKILL/node failure can bypass traps. Before production, the operator must provide a job epilog/container cleanup mechanism and approved cgroup/accounting integration (or port the launcher to the site's supported container runtime). Container names begin with `team7-JOBID-STEPID-` and have a unique suffix. Never prune unrelated containers. This task does not change cluster policy.

## 5. Mount and environment contract

| Host source | Container path | Access |
| --- | --- | --- |
| `INFRA_DIR` (set by submit.sh) | `/opt/team7-infra` | read only |
| `TRAIN_DIR` | `/workspace/training` (working directory) | read only |
| `DATA_DIR` | `/workspace/datasets` | read only |
| `CHECKPOINT_DIR` | `/workspace/checkpoints` | read/write |

Training paths `TRAIN_ENTRY` and `TRAIN_CONFIG` are relative to TRAIN_DIR; files must be nonempty and remain inside the training tree, including symlink resolution. The container checks Python syntax and nonempty YAML mapping, but cannot validate the missing model's schema/dependencies. Configs must refer to the **container** dataset/checkpoint paths. `DATA_DIR` and `CHECKPOINT_DIR` are also supplied as container environment variables, but the real model must actually honor them. Relative training inputs resolve from `/workspace/training`. Put outputs/caches in a writable location; HOME is ephemeral `/tmp`, code/data are read only, and supplemental group membership is not forwarded.

One container contains every worker, with its own 16 GiB shared-memory segment, unlimited memlock and a 64 MiB stack limit (the site must permit those limits). Default Docker networking suffices for the single-node rendezvous. Host networking, host IPC, privileged mode, Docker socket mounts, dmesg privileges, and blanket `--gpus all` are unnecessary here. CUDA sees the eight selected devices as local indices 0..7. OMP threads default to allocated CPUs / 8. Model-specific environment (tokens, offline caches, NCCL tuning, etc.) is not forwarded automatically: configure it deliberately for the real trainer.

## 6. GPU deployment and acceptance sequence

Copy this infrastructure checkout to an approved shared path and cd there. Pre-pull the actual image on every eligible compute node using the site-approved process. Authenticate to GHCR beforehand if required. For repeatable runs, record and use the pulled digest:

```bash
# On each eligible compute node or through the site's image provisioning process:
docker pull ghcr.io/murthyap63-a11y/team7-h100-env:latest
docker image inspect ghcr.io/murthyap63-a11y/team7-h100-env:latest   --format '{{json .RepoDigests}}'
# On the login host, use the real RepoDigest value (replace <verified-sha256>):
export DOCKER_IMAGE='ghcr.io/murthyap63-a11y/team7-h100-env@sha256:<verified-sha256>'
```

The launcher uses `--pull=never` to avoid network/auth surprises during an allocation, resolves the cached image to its immutable local image ID, and logs that ID/digests. It mounts updated helpers, so rebuilding the image is required only when changing baked dependencies. Dockerfile retains NVIDIA PyTorch `24.03-py3`; its requirements are broad lower bounds, not a reproducible dependency lock. A new dependency build needs separate compatibility validation and a new tag/digest.

First submit infrastructure-only preflight from the login host:

```bash
export TEAM7_MODE=preflight
bash submit.sh --dry-run --partition=train
# Add --account=YOUR_ACCOUNT, --qos=YOUR_QOS or --constraint=YOUR_H100_FEATURE if required.
jobid=$(bash submit.sh --partition=train)
jobid=${jobid%%;*}
squeue -j "$jobid" -o '%.18i %.12u %.12T %.30R'
# After completion:
sacct -j "$jobid" --format=JobID,State,ExitCode,AllocTRES
cat "${LOG_DIR:-$PWD/logs}/train_${jobid}.log"
cat "${LOG_DIR:-$PWD/logs}/train_${jobid}.err"
```

Accept only if there is one compute step/container, eight distinct H100s, known zero uncorrected ECC counters, CUDA operations on all eight devices, eight NCCL ranks with world=8 and reduced sum=36.0, and COMPLETED/0:0. NCCL success exercises communication but does not certify NVLink bandwidth or topology. GPU health failure must stop before training.

Then get the actual training checkout/config/data from the model owner; do not create empty substitute files:

```bash
export TEAM7_MODE=train
export TRAIN_DIR=/shared/team7/model
export DATA_DIR=/shared/team7/datasets
export CHECKPOINT_DIR=/shared/team7/checkpoints
export TRAIN_ENTRY=train_moe.py
export TRAIN_CONFIG=configs/config_v1.yaml
# Replace the example paths with real ones; create only the intended output directory.
mkdir -p "$CHECKPOINT_DIR"
bash submit.sh --dry-run --partition=train
jobid=$(bash submit.sh --partition=train)
jobid=${jobid%%;*}
squeue -j "$jobid"
```

The real model config must set a short smoke workload using its documented schema. Check eight worker ranks, real data access, output/checkpoint permissions, expected loss behavior, checkpoint restart, and final exit status. Schema, tokenizer, dataset, model packages, and distributed training correctness remain the model owner's responsibilities.

During a controlled infrastructure-only run, test cancellation as well:

```bash
scancel "$jobid"
sacct -j "$jobid" --format=JobID,State,ExitCode
# On its allocated compute node, inspect only this job's containers:
docker ps -a --filter "name=team7-${jobid}-"
```

TERM/INT propagate through the batch shell/srun to the compute wrapper; the wrapper stops its uniquely named container (10-second grace, then forced removal fallback). Nonzero srun/training exit codes remain nonzero; success is printed only after success. `#SBATCH --signal=B:TERM@60` requests early batch termination before the time limit, leaving cleanup time. SIGKILL, daemon failure, or node loss require operator epilog recovery. Before training relies on pre-timeout checkpointing, implement and test signal handling in the actual trainer; this infrastructure does not promise graceful model checkpointing.

Optional host-only hardware log audit:

```bash
python3 xid_scan.py
```

Run with existing operator-approved kernel-log access, outside the unprivileged container. Exit 0 means no listed critical-policy XID in the readable log snapshot, 1 means a listed code was found, 2 means the scan is unknown/unreadable. Historical XIDs need operator interpretation; this is not an in-training monitor. Do not add privileged mode solely to read dmesg.

## 7. Current blockers

No real trainer/config/data access or GPU Slurm endpoint/credentials were supplied. H100 allocation, NVIDIA runtime, NCCL, model training, GPU cancellation, and site cgroup/epilog integration have not been validated here. Local queue success does not remove any of these blockers. See the delivered validation report for commands/results and the separately preserved multi-node plan.

## Primary references

- [Slurm sbatch](https://slurm.schedmd.com/sbatch.html): task/resource directives, shared-file assumptions and batch signal semantics.
- [Slurm srun](https://slurm.schedmd.com/srun.html) and [GRES](https://slurm.schedmd.com/gres.html): step resources and global vs cgroup-visible GPU IDs.
- [PyTorch torchrun](https://docs.pytorch.org/docs/main/elastic/run.html): standalone rendezvous, ranks and nproc-per-node.
- [NVIDIA GPU enumeration](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html): UUID selection and Docker GPU quoting.
- [Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/): CPU and memory limits for daemon-owned containers.
