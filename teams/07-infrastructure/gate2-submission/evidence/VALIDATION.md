# Gate 2 validation — 2 November 2026

Gate 2 deadline: **Saturday, 14 November 2026**. All results below were executed locally, not inferred from code or historical logs.

## Results

| Check | Actual result | Evidence |
|---|---|---|
| Fresh-process CPU restore at step 100 | PASS: all 100 raw FP32 losses and ordered ID batches equal for steps 101..200 | `host/summary.json`, `host/restore_comparison.jsonl`, reference/restored traces |
| SIGKILL after completed step 125 | PASS: supervisor observes -9, starts attempt 2 from COMPLETE step 100; loss/IDs and final state equal | `host/killed/events.jsonl`, `host/restart_comparison.jsonl` |
| Invalid checkpoints / crash debris | PASS: missing marker at 150, modified payload at 160, modified manifest at 170, self-consistent hashes but invalid serialization at 200 excluded. Step-200 corruption and stale lock quarantined; valid step 200 republished | `host/kill_supervisor.log`, `host/killed/checkpoints/.rejected/` |
| Concurrent runner and cancellation | PASS: second writer rejected; supervisor TERM exits 143 and starts no replacement | `host/lock_rejection.log`, `host/cancel_supervisor.log` |
| Final training state | PASS: model/AdamW/scheduler/sampler/RNG all bit equal for fresh restore and SIGKILL recovery | Both summaries and `final.pt` files |
| Linux CPU restore/SIGKILL suite inside actual Slurm allocation | PASS with same step/ID/state criteria; user1 job **32**, c1, COMPLETED/0:0 | `slurm/gate2/summary.json`, `slurm/validation_32.out`, `slurm/slurm_accounting.txt` |
| Actual TSAI package adapter submission | PASS: user1 job **31**, c1, COMPLETED/0:0; one CPU node/task | `slurm/package-run/slurm_31.out`, `slurm/package-run/events.jsonl` |
| Real local two-user resource queue | PASS: job **33** user1 occupied c1/c2; job **34** user2 PENDING(Resources), then both COMPLETED/0:0 | `slurm-queue.log`; shared outputs `/data/team7-smoke-20261102T084004Z` |
| Unit/regression checks | PASS: **27 tests** on macOS and **27 tests** in Linux Docker | `all-regression.log`, `linux-regression.log` |
| Week 1 legacy checkpoint utility | PASS: five restored CPU losses and model state equal | `legacy-cpu.log` |
| Week 1 Gloo collective | PASS: two Linux CPU ranks, world=2, all-reduce sum=3.0 | `linux-gloo.log` |
| Shell syntax / existing launcher behavior | PASS in regression suite; GPU/Docker orchestration boundary uses stubs | `all-regression.log`; not GPU validation |

Earlier smoke jobs 29/30 also passed before final hardening; **31/32 are the final acceptance runs**. An initial attempt ran before nodes finished transitioning to idle and correctly refused to submit. No production scheduler was contacted or altered.

## Environments

- Host: macOS ARM64, Python 3.14.0, Torch 2.14.1, NumPy 2.5.4, CPU only. Exact installed requirements in `host-requirements.txt`.
- Docker Slurm: existing `slurm-docker-cluster:26.05.5`, Linux ARM64, Slurm 26.05.5, Python 3.12.15, Torch 2.5.1, NumPy 2.1.3. Shared venv `/data/team7-gate2-py312`. Exact dependency freeze in `slurm/linux-requirements.txt`.
- CPU equality is checked separately within each environment; no cross-platform or cross-version bit equality is claimed.
- Final Slurm source snapshot: `/data/team7-gate2-20261102T083952Z/infra`; full working-tree handoff is included in the delivered archive.

## Reproduction

From the existing infrastructure checkout:

```bash
export PYTHON=/Users/shashanks/Documents/Codex/2026-10-25/referenced-chatgpt-conversation-this-is-an-2/work/venv/bin/python
"$PYTHON" -m unittest discover -s tests -p 'test_*.py' -v
"$PYTHON" tests/gate2_validate.py --output /tmp/team7-gate2-host-NEW
python3 tests/slurm_gate2.py --output /tmp/team7-gate2-slurm-NEW
python3 tests/slurm_queue_smoke.py
```

The last two require the existing Docker Slurm demo to be up, the shared venv installed and two CPU nodes idle; setup/inspection commands are in `docs/runbook.md`. Use new empty output directories. To repeat the Gloo check against the saved shared snapshot:

```bash
docker exec slurmctld env OMP_NUM_THREADS=1 /data/team7-gate2-py312/bin/python -m torch.distributed.run --standalone --nnodes=1 --nproc-per-node=2 /data/team7-gate2-20261102T083952Z/infra/collective_smoke.py --backend gloo
```

The Gate 2 suite compares bytes and ordered lists, without tolerance. A trace must contain exactly steps 1..200 once each. Both comparison files must contain exactly 100 successful rows; summaries must state PASS. Failed runs retain logs and do not silently create a success summary.

## What remains unvalidated

No H100/CUDA/NCCL hardware, genuine MoE trainer/config/dataset, distributed/sharded/AMP checkpoint, production shared-filesystem semantics, GPU scheduler identity/quotas or site cgroup/epilog integration were available. The cached original H100 training image was absent, so it was not rebuilt or treated as tested. Gloo is a CPU collective only.

Automatic recovery demonstrated here is a killed worker in a **live** local/Slurm allocation. Automated recovery after whole-node, supervisor or allocation loss is not implemented by an external service; `--no-requeue` is deliberate. The runbook describes operator recovery with the same persisted identity/checkpoint and remaining attempt budget. No external TSAI runner/schema was supplied, so the new v1 contract needs TSAI review before external integration.

The source remains in the user's existing Git working tree; no commit, push, image publication or production deployment was performed. Week 1 changes already present were retained; merge provenance is in `docs/week1_merge.md`.
