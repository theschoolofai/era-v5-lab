# Dry run 2 (dryrun2-1234): run record

TSAI posts the small files of the finished run so that teams can check their work. The step 1,221 weights are not in Git; TSAI shares them by link.

| File | What it is |
|---|---|
| `manifest.json` | the run manifest (config.model has head_mode kas_v2; tokenizer sha256 e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b) |
| `metrics.jsonl` | per-step metrics of the run |
| `summary.json` | status COMPLETED, 1,221 steps, final_model_sha256 8d1600b278a3d8e15c3d7af408a86e7c47acd987a899bf5eeee6b2c72192eb47 |
| `commits.jsonl` | the Team 7 checkpoint commit log |
| `latest.json` | the checkpoint pointer (step 1,221) |

Redacted by TSAI: in `manifest.json` the GPU name and the checkpoint store path, in `latest.json` the host name. Nothing else was changed. The original manifest.json has sha256 b9a9baa4 (first 8 characters).

Use: replay for Team 8 (alarms), scoring for Team 9, step time for Team 6, report for Team 5, commit log for Team 7. Training text of this run was one English web shard of 25M tokens, not the sample-v0 mix.
