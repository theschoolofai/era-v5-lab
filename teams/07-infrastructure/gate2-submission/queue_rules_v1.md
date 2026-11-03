# Team 7 queue rules v1

Date: 2 November 2026. Repository implementation contract for Gate 2, due 14 November.
TSAI policy approval and production quotas have not been supplied. This file does not claim those settings are installed on a production scheduler.

## Admission and ownership

1. Submit a JSON v1 package described in `docs/job_package_v1.md`. Validate it before submission with `tsai_runner.py --validate`; `tsai_submit.py` repeats admission. Require owner, job ID, existing config/code/data manifest, positive finite resources and bounded restart policy.
2. Preserve resolved config, package, code SHA256 inventory, data-manifest hash and runtime versions as `identity.json`. Use an absolute, writable, shared run directory. Never reuse it for changed inputs or a completed run. Owner is audit metadata; Unix/Slurm identity supplies authorization, not that string.
3. V1 runner admission allows one node, one CPU task and zero GPUs. Slurm enforces requested CPU/memory/time; local runs have a wall-time deadline but no OS memory/CPU quota. For GPU allocation use the existing eight-H100 launcher and its preflight, pending model-specific restart integration.
4. Create the log/run directory before sbatch. Source, Python environment, config, data references and run/checkpoint paths must be visible at identical absolute paths to every eligible worker. Slurm moves the batch script, not these files.

## Queue policy

- Slurm owns scheduling order, priority, resource availability and accounting. The runner does not bypass PENDING jobs, resubmit them repeatedly, drain nodes or provision cloud resources.
- Production proposal retained from Week 1: one Unix user per student, one account per team, approved associations, consumable CPU/memory/GPU resources, accounting/limit/QoS enforcement and site cgroups. TSAI must assign numeric account quotas, per-user running-job limits, short validation/train QoS, max wall times and fair-share/backfill settings. No fabricated default quota is installed here.
- Request accurate resources and finite time; never use GPU claims to run CPU validation. Hold/reject jobs with unavailable dependencies, incompatible configs, missing data or unknown GPU health.
- Record Slurm job ID, Unix user/account, node, requested/allocated resources, exit state and code alongside package identity, attempt events and checkpoint reference. Cancellation must target only job IDs belonging to the current run.

## Lifecycle and restart rules

`admitted -> PENDING -> RUNNING -> succeeded | failed | cancelled | timed-out`.
Within RUNNING, worker attempts may transition `attempt_started -> attempt_exited -> verified checkpoint selection -> next attempt`.

- Initial execution uses resume=`none`. After failure, select the highest numbered valid COMPLETE checkpoint, checking both checksums and serialized state schema. A valid checkpoint from a different identity fails closed. Newer invalid checkpoints are logged and moved into `.rejected/`; temporary directories and stale step locks are also preserved there after the run lock proves the previous writer has gone.
- Retry only configured exit codes from the allowlist: SIGKILL (-9), SIGSEGV (-11), temporary failure 75, or wrapper code 137. Default example allows -9, 75 and 137. Exit 0 succeeds; ordinary code/config failure 2 stops. Without a valid checkpoint, stop instead of restarting from scratch.
- `max_restarts` is 0..10, with 2 in the example: at most 3 attempts. Attempt count persists in `events.jsonl` across runner invocations. Backoff is bounded 0..60 seconds. Retry budget exhaustion is terminal.
- Supervisor TERM/INT cancels the worker process group, waits up to 5 seconds, then kills it if needed; cancellation never retries. Do not interpret user `scancel`, allocation timeout, OOM or node failure as permission to keep consuming resources. The CPU adapter explicitly submits `--no-requeue`.
- Restart tested here means restarting a killed worker **within its existing live allocation**. No external scheduler watchdog is implemented. If the supervisor/node/allocation dies, preserve the shared run directory and inspect Slurm accounting. An operator may submit the same package/run directory in a new allocation only after confirming no old worker holds its lock and checking remaining attempt budget. Durable checkpoint storage is required. Automated allocation/node recovery is a later integration.
- Keep trace records at or below the restored step; replay speculative records after it. The fixture demonstrates this by discarding steps 101..125 after restoration at 100. Consumers must key metrics by run/step and avoid double-counting replayed steps.

## Evidence and limits

`tests/slurm_queue_smoke.py` proves user1 can occupy both local CPU nodes, user2 waits with Resources, and both complete as the expected identities after release. It does not prove account authorization, fair-share, quotas, GPU isolation or production priority.
`tests/slurm_gate2.py` proves actual package submission and fresh-process restore/SIGKILL recovery inside local Docker Slurm CPU jobs. See `evidence/VALIDATION.md` for exact runs and commands.

References: [Slurm sbatch](https://slurm.schedmd.com/sbatch.html), [Slurm resource limits](https://slurm.schedmd.com/resource_limits.html). Production changes require the site's normal operator policy; no scheduler policy changes are performed by the runner.
