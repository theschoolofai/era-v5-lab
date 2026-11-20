# Week 3 harness

## G8 live metrics

Pass the job package's run ID as `--run-id "$RUN_ID"` to use the same identity in G5 and G8. IDs begin with a letter or digit and may also contain dots, dashes, and underscores. A fresh invocation without the flag generates an ID. The trainer records it in `manifest.json`, `summary.json`, and the native checkpoint. Resume uses a fresh output directory and recovers the checkpoint ID if the flag is omitted. If supplied, the ID must match the checkpoint. For a compatible legacy checkpoint without an ID, the checkpoint file's SHA-256 is its ID. The resume identity check still applies.

To enable the G8 adapter, put `teams/08-monitoring/metrics_logger` on `PYTHONPATH` and pass `--logger-factory g5_adapter:make_writer`. The trainer writes the manifest before calling the factory once with the output directory. The returned writer receives `write(row)` in step order, including the initial evaluation at step 0 and the saved history on resume. The trainer calls `flush()` before writing final artifacts and `close()` on exit. A logger error fails the invocation.

The adapter writes `g8/metrics.jsonl` with `run_id`, `step`, `time`, and the existing G8 metrics. It flushes at step 0, every 10 steps, on a nonfinite metric, and on close. Replayed rows retain their step and run ID and receive timestamps when written. Use the newest segment's G8 file for ingestion because it includes the checkpoint's history. The ClickHouse loader reads the embedded run ID. The trainer also writes its native `metrics.jsonl`.

## Validate run evidence

Run this against the output directory after the trainer has exited.

```bash
python teams/05-architecture/harness/validate_week2_run.py /path/to/run --trusted-checkpoint
python teams/05-architecture/harness/validate_week2_run.py /path/to/run --trusted-checkpoint --expected-steps 1000 --json > run-evidence.json
python teams/05-architecture/harness/validate_week2_run.py /path/to/copied-run --trusted-checkpoint --verify-inventory run-evidence.json
```

The validator uses the resolved step budget in the manifest. Supply `--expected-steps` when you have the budget from the job request. It checks the summary status and completed steps, the evaluation row at step 0, one metrics row per completed step, and one row per completed step in each loss trace. It recomputes the manifest identity and reports SHA-256 hashes for the evidence files, including the required checkpoint for non-smoke runs. Archive the JSON report with the run to check the hashes after copying.

A quality PASS requires `smoke=false`, a `COMPLETED` summary, the exact configured or expected step count, all six evidence files, and matching checkpoint identity and step. Run with `--trusted-checkpoint` only on trusted outputs because PyTorch uses its full checkpoint loader. The validator reports a failure for a quality candidate when checkpoint inspection cannot be performed.

Exit code 0 means the run completed with internally consistent evidence. This validation provides neither a BPB result nor a winning configuration. Exit code 1 covers smoke runs, incomplete runs, and evidence failures. The JSON report includes the verdict, evidence scope, row counts, checkpoint inspection status, and errors.
