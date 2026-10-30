# Results

- `runs/<tag>.json` + `<tag>.md`: one bench run each (committed as evidence).
- `runs/<tag>_parts/`: one small Chrome trace per slowest part (committed), written by `perfkit.bench` when a run
  has both `layer` and `trace` modes; listed in the run JSON under `trace.parts`. Open them in
  https://ui.perfetto.dev or `chrome://tracing`.
- Full profiler traces go to `~/.cache/era-perf/traces/`, outside the repo (too big for git; pr-guard
  rejects files over 5 MB). Never write them under `results/`.
- `baseline_v0.md`, `slowest5_v0.md`: the Gate 1 baseline and the five slowest parts, from the two runs
  `runs/baseline_v0.json` and `runs/baseline_v0-run2.json` (A100-SXM4-40GB, commit `f1f4986`). The part traces
  are from the first run (`runs/baseline_v0_parts/`); the second run's are not committed (same parts).

Every result names its GPU and commit. A number without both does not count.
