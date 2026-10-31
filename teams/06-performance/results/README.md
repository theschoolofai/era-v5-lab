# Results

- `baseline_v0.md`, `slowest5_v0.md`: the Gate 1 baseline and the five slowest parts (A100-SXM4-40GB, commit
  `f1ed7f2`, `configs/base.yaml`), from the pairs `baseline_v0` + `baseline_v0-run2` and `mtp_v0` + `mtp_v0-run2`
  (`model.mtp=true`). Their run JSONs, JSONL sidecars, part traces and logs are in the gist
  https://gist.github.com/vaibh27/574990425455e4a9cb64822f14e3d85b; they are not committed.
- `runs/` (not committed): where bench writes each run, `<tag>.json` + `<tag>.md`, the live `<tag>.jsonl` sidecar
  (`gpu_sample` and `step_timing` events, for G8; `docs/METRICS.md`) and `<tag>_parts/`, one small Chrome trace
  per slowest part (open it in https://ui.perfetto.dev or `chrome://tracing`). Share run files as a gist.
- Full profiler traces go to `~/.cache/era-perf/traces/`, outside the repo (too big for git; pr-guard
  rejects files over 5 MB). Never write them under `results/`.

Every result names its GPU and commit. A number without both does not count.
