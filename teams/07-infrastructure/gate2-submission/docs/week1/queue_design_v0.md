# Queue design v0 — Team 7, Week 1

Status: proposed for TSAI approval. The Docker implementation is a local CPU scheduling fixture, not the production cluster configuration.

## Goal and ownership

Schedule lab jobs fairly, enforce assigned resources, make failures visible, and keep cloud credentials with TSAI. TSAI decides GPU shares per team/day, provisions nodes, and owns S3 credentials. Students submit scripts through the lab process. No cloud provisioning or spending is included in this design.

## Proposed production policy

Use Slurm with slurmctld, slurmd and slurmdbd accounting; one Unix identity per student and one Slurm account per team. Associate users only with their assigned accounts. Enable accounting association, limit and QoS enforcement. Use consumable CPU/memory/GPU resources, cgroup device isolation on lab Linux, bounded wall times and one agreed GPU quota per account. No numeric production quota is assumed before TSAI supplies it.

Provide short validation and training QoS classes. Validate config hash, data/tokenizer versions, output location and resource request before admission. Backfill can use otherwise idle capacity; fair-share weights and maximum running jobs must be approved by TSAI. Persist scheduler state and accounting database outside ephemeral compute. Queue order alone is not evidence of fair-share correctness.

Lifecycle: submitted → pending → running → completed or failed/cancelled/timed out. Record job ID, run ID, account, commit ID, config hash, requested/allocated resources, start/end time, exit code and checkpoint reference. Team 8 receives these records via the agreed JSON contract.

Before a GPU job, run gpu_health.sh and a small collective test. A failed/unknown check blocks admission for operator review. This reference does not automatically drain nodes or reset GPUs. On termination, the training loop must publish a checkpoint at a safe optimizer-step boundary if time remains. Week 2 adds bounded automatic restart from a verified COMPLETE checkpoint; do not blindly requeue a persistent failing job.

## Two-account Docker acceptance test

The supplied Dockerfile builds one disposable CPU node/controller/database container. Accounts team_a and team_b belong to Unix users alice and bob respectively. The test proves both users run jobs, alice cannot submit against team_b, and a job waits when both configured CPUs are occupied and then runs after resources release.

From this directory:

```bash
docker build -t era-v5-slurm-w1 slurm-docker
docker run --rm --hostname lab era-v5-slurm-w1
```

Capture build output, installed Slurm version, image digest, association table and PASS output for the PR. The image has no exposed ports, bind mounts, cloud access or GPU passthrough. It uses task/none and linuxproc specifically for a disposable Docker smoke test; it does not prove Linux cgroup isolation, GPU isolation, multi-node networking or production accounting persistence. The local database value is intentionally disposable. Do not deploy this container as the production scheduler.

## Required approvals/dependencies

- Team 5: config v0, due 27 October according to the video frame.
- Team 8: health-check JSON format, due 29 October according to the video frame. gpu_health.py currently proposes schema_version 0.
- TSAI: both designs, GPU allocation policy, node/partition/account details and submission interface.
- Team lead: final topic folder name; bootstrap is a proposed shared topic, not a personal folder.

Gate 1 on 31 October: TSAI approves queue and checkpoint designs; Docker Slurm, health and CPU restore tests pass. A CPU fixture cannot substitute for a live NVIDIA health test.
