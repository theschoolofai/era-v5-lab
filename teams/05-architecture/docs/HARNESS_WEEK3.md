# Week 3 harness

## G8 live metrics

A fresh invocation assigns a run ID and records it in `manifest.json`, `summary.json`, and the checkpoint when one is written. A resume keeps the checkpoint's run ID and uses a fresh output directory. For a compatible checkpoint without an ID, the trainer uses the checkpoint file's SHA-256 as the run ID. The existing resume identity check still applies.

To enable the G8 adapter, put `teams/08-monitoring/metrics_logger` on `PYTHONPATH` and pass `--logger-factory g5_adapter:make_writer`. The trainer writes the manifest before calling the factory once with the output directory. The returned writer receives `write(row)` in step order, including the initial evaluation at step 0 and the saved history on resume. The trainer calls `flush()` before writing final artifacts and `close()` on exit. A logger error fails the invocation.

The adapter writes `g8/metrics.jsonl` with `run_id`, `step`, `time`, and the existing G8 metrics. It flushes at step 0, every 10 steps, on a nonfinite metric, and on close. Replayed rows retain their step and run ID and receive timestamps when written. Use the newest segment's G8 file for ingestion because it includes the checkpoint's history. The ClickHouse loader reads the embedded run ID. The trainer also writes its native `metrics.jsonl`.
