# Week 3 harness

## G8 live metrics

Pass the job package's run ID as `--run-id "$RUN_ID"` to use the same identity in G5 and G8. IDs begin with a letter or digit and may also contain dots, dashes, and underscores. A fresh invocation without the flag generates an ID. The trainer records it in `manifest.json`, `summary.json`, and the native checkpoint. Resume uses a fresh output directory and recovers the checkpoint ID if the flag is omitted. If supplied, the ID must match the checkpoint. For a compatible legacy checkpoint without an ID, the checkpoint file's SHA-256 is its ID. The resume identity check still applies.

To enable the G8 adapter, put `teams/08-monitoring/metrics_logger` on `PYTHONPATH` and pass `--logger-factory g5_adapter:make_writer`. The trainer writes the manifest before calling the factory once with the output directory. The returned writer receives `write(row)` in step order, including the initial evaluation at step 0 and the saved history on resume. The trainer calls `flush()` before writing final artifacts and `close()` on exit. A logger error fails the invocation.

The adapter writes `g8/metrics.jsonl` with `run_id`, `step`, `time`, and the existing G8 metrics. It flushes at step 0, every 10 steps, on a nonfinite metric, and on close. Replayed rows retain their step and run ID and receive timestamps when written. Use the newest segment's G8 file for ingestion because it includes the checkpoint's history. The ClickHouse loader reads the embedded run ID. The trainer also writes its native `metrics.jsonl`.

## Validate run evidence

Run this against the output directory after the trainer has exited.

```bash
python teams/05-architecture/harness/validate_week2_run.py /path/to/run
python teams/05-architecture/harness/validate_week2_run.py /path/to/run --expected-steps 1000 --json > run-evidence.json
python teams/05-architecture/harness/validate_week2_run.py /path/to/copied-run --verify-inventory run-evidence.json
```

The validator uses the resolved step budget in the manifest. Supply `--expected-steps` when you have the budget from the job request. It checks the summary status and completed steps, the evaluation row at step 0, one metrics row per completed step, and one row per completed step in each loss trace. It recomputes the manifest identity and reports SHA-256 hashes for the evidence files, including the required checkpoint for non-smoke runs. Archive the JSON report with the run to check the hashes after copying.

Exit code 0 means the directory passed the evidence checks for a completed quality run. Exit code 1 covers smoke runs, incomplete runs, and evidence failures. The JSON report records the classification, row counts, checkpoint inspection status, and any errors. For a checkpoint you trust, add `--trusted-checkpoint` to verify its step and run identity against the summary and manifest. This option uses PyTorch's full checkpoint loader on CPU. Without it, the checkpoint is checked for presence and included in the hash inventory.
