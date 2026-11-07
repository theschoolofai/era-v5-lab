# TSAI job package v1 (Team 7 repository contract)

This is the implemented Team 7 CPU handoff format. No external TSAI runner implementation or approved schema was provided; confirm this contract with TSAI before integrating an external service. The actual parser is `tsai_runner.admit`, used by both runner and submitter. `examples/gate2_job.json` is a runnable package, not a GPU model substitute.

## Contents and fields

Deliver the existing repository at an immutable revision (or archive plus file hashes), package JSON, its config and code inventory, data manifest/references, an installed Python environment, and a new shared writable run directory. No credentials belong in the package. External dataset manifests must reference immutable shard/tokenizer versions and hashes; the runner hashes the manifest, not each remote data byte. This example uses a fully specified synthetic dataset with no downloads.

The package has exactly these top-level fields:

| Field | Required format / meaning |
|---|---|
| `schema_version` | Integer 1 |
| `job_id` | 1..64 letters/digits/underscores/hyphens, starting with letter/digit |
| `owner` | Nonempty audit string; not an authorization mechanism |
| `command` | Nonempty argv string array; executed directly without shell expansion |
| `config` | Existing repository-relative JSON file containing a nonempty mapping |
| `code` | Nonempty unique list of existing repository-relative code files; list all trainer/imported local dependencies |
| `data` | Exactly `{ "id": "immutable-data-version", "manifest": "relative/path.json" }` |
| `resources` | Exactly `nodes`, `tasks`, `gpus`, `cpus`, `memory_mb`, `time_minutes`, `partition` |
| `restart` | Exactly `max_restarts`, `backoff_seconds`, `exit_codes` |

Input paths are resolved under the existing repository; absolute paths, traversal and symlinks escaping the repository fail admission. No cwd guessing is used. Command placeholders: `{python}` is the running interpreter, `{repo}` the source root, `{config}` the absolute config path, `{run_dir}` the absolute output root, `{resume}` an absolute verified checkpoint directory or the literal `none`. Config/run_dir/resume placeholders are mandatory; unknown placeholders fail. Packages and commands are trusted executable code, not a sandbox or an untrusted upload interface.

Resources require `nodes=1`, `tasks=1`, `gpus=0`, positive integer CPU/memory/time, and a partition containing only letters/digits/underscore/hyphen. Slurm's site policy still governs admission. GPU packages are intentionally rejected by this v1 CPU adapter. Restart constraints and behavior are in `../queue_rules_v1.md`.

## Worker interface

The worker must accept the substituted arguments, restore BEFORE its next data draw, and return 0 only after completion. For the supplied fixture:

```text
python tests/gate2_worker.py --config ABS_CONFIG --run-dir ABS_RUN --resume none|ABS_CHECKPOINT
```

`identity.json` contains normalized package/config, SHA256 of declared code and data manifest, and Python/Torch/NumPy/system/machine identity. Runner revalidates input identity before every attempt. The worker checks config content again. Inputs must stay immutable during a run; runtime dependency freeze and source archive are part of the handoff, and undeclared dependencies cannot be detected automatically.

Checkpoint v2 layout:

```text
RUN/
  identity.json
  .runner.lock
  events.jsonl
  attempt-01.log
  trace.jsonl
  checkpoints/
    step-00000100/
      state.pt
      manifest.json
      COMPLETE
    .rejected/     # preserved corrupt/partial files and stale step locks
```

`manifest.json` records version, step, config identity hash, state filename, byte count and SHA256. `COMPLETE` contains SHA256 of the manifest. `state.pt` saves model, optimizer, scheduler, sampler state, consumed count, RNG states and model training mode. Single-writer lock, fsync and same-filesystem rename precede publication. Readers validate marker, hashes, schema and identity; they never use a partial directory. The model owner must extend this for AMP, gradient accumulation, workers/prefetch or distributed shards. Only trusted lab checkpoints are supported; hashes detect accidental corruption, not a malicious writer.

The legacy `save_checkpoint/load_checkpoint` API is retained for Week 1 callers, but is not a v2 COMPLETE checkpoint and is not selected by the restart runner. Week 1 bootstrap directory format v1 is not silently migrated; create a new v2 run. Existing saved checkpoints are left untouched.

## Commands

From this repository using a Python environment with Torch and NumPy:

```bash
python tsai_runner.py examples/gate2_job.json --validate
python tsai_runner.py examples/gate2_job.json --run-dir /shared/team7/runs/unique-cpu-run
python tsai_submit.py examples/gate2_job.json --run-dir /shared/team7/runs/unique-slurm-run --dry-run
python tsai_submit.py examples/gate2_job.json --run-dir /shared/team7/runs/unique-slurm-run
```

The final two commands require a CPU Slurm partition named in the package, shared source/environment/outputs, and authorized Unix identity. `--dry-run` creates the run directory and prints exact submission argv; it does not contact Slurm. `tsai_batch.sh` forwards cancellation through its single srun task to the supervisor.
