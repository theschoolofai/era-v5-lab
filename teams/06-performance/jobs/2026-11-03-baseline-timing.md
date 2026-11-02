# G6 baseline timing (Gate 2 job request)

```
Team:            06-performance
Owner:           Raj H (raj-harit-v2)
Lead approval:   raj-harit-v2
Question:        What are step_ms (median), tokens/s, MFU, HFU, and peak memory for configs/base.yaml on one GPU with --repeat 2 at level 3?
Script:          teams/06-performance/jobs/run_baseline_timing.py
Command:         python teams/06-performance/jobs/run_baseline_timing.py --out out
Config:          teams/06-performance/configs/base.yaml
Inputs:          synthetic if FineWeb shards absent; prefer FineWeb Brahmic-131K sample under data.dir when present
Hardware:        1 GPU
Max time:        45
Precision:       bf16
Measures:        clean.step_ms.median, tokens_per_s, mfu, hfu, peak_allocated_gb, gated parts within 5% across --repeat 2, GPU name, commit SHA
Expected result: step_ms near prior A100 baseline (~40–50 ms at B=16 T=256) or documented host delta; repeat exit 0
Outputs:         out/result.json, out/baseline_v1_job.json, out/baseline_v1_job.md, out/baseline_v1_job-run2.json (under 50 MB)
Test log:        teams/06-performance/jobs/2026-11-03-baseline-timing.log (own machine, --smoke-cpu synthetic, PASS)
```

## Pins

| Item | Value |
| :--- | :--- |
| Intended G6 tip (day-to-day) | `vaibh27/era-v5-lab` `g6/dev` @ `cf47f58` (PR #43 landed) |
| Class PR commit | the merge commit of this job-request PR on `theschoolofai/era-v5-lab` |
| Packages | `torch>=2.3`, `numpy`, `pyyaml`, `tokenizers>=0.15` (see `teams/06-performance/perfkit/requirements.txt`) |

## Notes

- Default (no `--smoke-cpu`) runs `perfkit.bench` on `base.yaml` with `--modes clean,layer --level 3 --repeat 2`.
- The attached test log is the same script with `--smoke-cpu` (tiny synthetic CPU) to prove the wrapper; TSAI GPU run should omit `--smoke-cpu`.
- Writes only under `./out/`.
