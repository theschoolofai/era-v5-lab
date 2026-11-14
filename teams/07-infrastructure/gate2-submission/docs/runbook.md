# Team 7 Gate 2 operations runbook

Gate: Saturday 14 November 2026. Prepared and locally tested 2 November 2026.

The source of truth is the existing `Team7-infrastructure` checkout; Week 1 launcher and GPU checks remain in that codebase. This runbook covers the new CPU restore/restart path. Historical H100 deployment instructions are preserved in [week1_runbook.md](week1_runbook.md), and the future multi-node plan remains separate.

## 1. Prepare and inspect

Start in the shared repository's team directory. Use a Python environment
with a compatible PyTorch/NumPy installation; on a fresh machine create one:

```bash
cd teams/07-infrastructure     # from the ERA V5 Lab repository root
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export PYTHON="$(command -v python)"
"$PYTHON" -c 'import torch,numpy; print(torch.__version__,numpy.__version__)'
"$PYTHON" tsai_runner.py examples/gate2_job.json --validate
```

If the directory is already open in a terminal, omit the `cd` line. If your
platform requires a specific PyTorch wheel/index, install a supported build
first. The historical tested versions are in
`evidence/host-requirements.txt` and `evidence/slurm/linux-requirements.txt`;
these are environment records, not universally portable lockfiles.
Bitwise equality is checked *within one fixed environment*, not across OS,
hardware or Torch versions. [PyTorch reproducibility guidance](https://docs.pytorch.org/docs/stable/notes/randomness.html).

## 2. Reproduce host CPU Gate 2

Choose a new empty evidence directory for every run:

```bash
"$PYTHON" -m unittest discover -s tests -p 'test_*.py' -v
"$PYTHON" tests/cpu_smoke.py
"$PYTHON" tests/gate2_validate.py --output /tmp/team7-gate2-host-NEW
```

Expect `summary.json` status PASS, exactly 100 records in each comparison JSONL for steps 101..200, all raw FP32 loss bits and ordered ID lists equal, and equal final model/AdamW/scheduler/sampler/RNG state. The validator starts separate reference/restore processes. It pauses a real worker after step 125, introduces four invalid newer checkpoints plus partial-write/stale-lock debris, sends SIGKILL to that worker PID, and checks that its live supervisor starts exactly one replacement at step 100. The invalid step-200 path must be quarantined so the replacement can publish step 200. It also verifies lock rejection and supervisor TERM cancellation without retry. These are synthetic CPU infrastructure tests.

Artifacts: reference/restored/killed traces and final states, checkpoint payloads/manifests, per-attempt logs, runner events, per-step comparisons and a summary. Retain both successful and rejected checkpoints until Gate 2 review; no automatic retention deletion is implemented.

## 3. Reproduce existing Docker/Slurm CPU tests

The tested demo was a separately installed Docker-based Slurm cluster with a `slurmctld` controller, MySQL/slurmdbd, two CPU workers (`c1`, `c2`) and shared `/data`. **This demo is not bundled in this team folder.** Provision or reuse an authorized equivalent before running Slurm tests. On the original local demo, start the existing services and inspect them:

```bash
open -a Docker
docker info
docker start mysql slurmdbd slurmctld slurm-docker-cluster-cpu-worker-1 slurm-docker-cluster-cpu-worker-2
docker exec slurmctld scontrol ping
docker exec slurmctld squeue
docker exec slurmctld sinfo -Nel
docker exec slurmctld scontrol show nodes c1,c2
```

In the original local demo, nodes sometimes showed DOWN after a Docker VM reboot; the workers were checked and resumed only after confirming their processes were healthy and no jobs were present. Inspect the node reason, slurmd health and queue before any state change. Only for this isolated demo after a verified reboot issue, an authorized operator may use `docker exec slurmctld scontrol update NodeName=c1,c2 State=RESUME`, then wait for both nodes to report idle. Do not apply this to production or unknown failures.

The isolated demo environment was created once on the shared volume (no global container Python changes):

```bash
docker exec slurmctld python3 -m venv /data/team7-gate2-py312
docker exec slurmctld /data/team7-gate2-py312/bin/python -m pip install torch==2.5.1 numpy==2.1.3
```

Skip setup if it already exists and imports successfully. The exact transitive installed versions are in the saved Linux requirements file. Users `user1` and `user2` must exist with matching UID/GID on the controller and workers, and the shared Python interpreter at `/data/team7-gate2-py312/bin/python` must be accessible to both jobs. These prerequisites were present in the tested demo; they are **not installed automatically by the source archive**. Check identities and require two idle CPU nodes:

```bash
python3 tests/slurm_gate2.py --output /tmp/team7-gate2-slurm-NEW
python3 tests/slurm_queue_smoke.py
```

The Gate 2 script copies a source snapshot into its own timestamped shared directory, runs an actual package through `tsai_submit.py`, then submits the full kill/restore validator as a second user1 Slurm batch job. It copies source, CPU payloads, logs, requirements and accounting to the requested host output. It cancels only its own job IDs during cleanup. The queue script then verifies user1 RUNNING, user2 PENDING(Resources), followed by both COMPLETED/0:0 as their correct identities. This tests a local Slurm CPU cluster hosted by Docker, not the original CUDA image or a remote GPU site.

## 4. Run or recover a CPU package

Read [job_package_v1.md](job_package_v1.md), [queue_rules_v1.md](../queue_rules_v1.md) and [parallel_layout_v0.md](../parallel_layout_v0.md). Validate the package; use a unique shared writable run directory. For Slurm use `tsai_submit.py` from the intended Unix account. Owner metadata does not switch accounts. Record job ID; monitor `squeue -j JOBID`, then `sacct -j JOBID --format=JobID,User,State,ExitCode,AllocTRES`. Inspect `slurm_JOBID.out/err`, attempt logs and events.

Inside a live allocation, the supervisor automatically retries only permitted worker failures with remaining budget and a valid COMPLETE checkpoint. A step-125 kill rolls back to 100 and replays 101..125; loss/ID comparisons use the final one-record-per-step trace. Concurrent runners fail the lock; never bypass it or remove it to force overlap. The file itself may remain after completion; advisory lock ownership, not existence, indicates activity.

For cancellation use `scancel JOBID` (or TERM the local runner). Cancellation stops the worker and never resubmits. For supervisor/node/allocation loss, there is no automatic external requeue service: inspect accounting, ensure the old worker is gone, verify shared storage and remaining persisted attempt budget, then explicitly resubmit the same package/run directory. An orphan worker retains the run lock until it exits, preventing overlapping replay. Checkpoints without a valid COMPLETE marker/hash/state are excluded, and crash debris is preserved under `.rejected/`. All-corrupt or missing checkpoint sets fail rather than silently restarting from zero. A changed config/code/data/runtime identity requires a new run directory. Never edit identity/events to bypass these protections.

## 5. GPU/cluster handoff still required

Local evidence does not validate H100, CUDA, NCCL, real MoE training, mixed precision, sharded checkpointing, production shared-storage durability, account quotas, cgroup isolation, or automatic allocation/node recovery. Supply the genuine model checkout/config/data/tokenizer and a reachable authorized GPU Slurm environment; confirm site runtime/epilog requirements in `week1_runbook.md`. Implement the model's distributed safe-step checkpoint adapter and loss/ordered-ID trace, then repeat restore/kill/cancellation tests on the actual layout. The CPU writer rejects distributed worlds larger than one.

Gate 2 local evidence and tested job IDs are indexed in [evidence/VALIDATION.md](../evidence/VALIDATION.md). Large binary checkpoints were intentionally excluded from the submission; rerunning the validators reconstructs them. This archive is source/evidence only, not a GitHub commit, push or published image.
