# Handoff to Team 08-monitoring — H200 GPU validation run

**From:** Team 06-performance
**Date:** 2026-10-28
**What:** All 6 GPU validation tasks executed on Modal (NVIDIA H200 single-GPU + 2×H200 torchrun), commit `19221759f9d820ce0563d5d2f44e22eac0de53d2`, branch `g6/dev`.
**Where:** everything in this folder (`teams/06-performance/results/modal_gpu/`); full console log in `h200_v1_full_console.log`.

---

## 1. The monitoring interface: what every run JSON exposes

Each benchmark run produces a JSON (`results/runs/<tag>.json`) that is the primary machine-readable interface for monitoring. Top-level sections:

| Section | Contents | Monitoring use |
|---|---|---|
| `meta` | GPU name/spec, torch/cuda/driver versions, device, commit, python, compute capability, SM count, GPU mem GB | Environment fingerprint — attach to every metric series |
| `system` | **1 Hz nvidia-smi sampling during measured steps** (66 samples in this run): `gpu_util_pct`, `mem_util_pct`, `mem_used_mib`, `sm_clock_mhz`, `mem_clock_mhz`, `power_w`, `temp_c` — each with min/median/max/mean. Plus `slowdown_samples` / `slowdown_reasons` (thermal-throttle detection) | Core GPU telemetry, already aggregated |
| `memory` | `peak_allocated_gb`, `peak_reserved_gb` (PyTorch allocator) | Memory-headroom alerts |
| `trace` | `gpu_busy_pct` (kernel trace, not nvidia-smi), `host_syncs_per_step`, `sync_sites` (file:line histogram!), `kernels_per_step`, `top_ops` | Distinguishes "GPU slow" from "GPU idle waiting on host" |
| `clean` | `step_ms`, `data_ms`, `events_created_during_steps` (should be 0 — timer health) | Step-time dashboards |
| `metrics` | `tokens_per_s`, `model_flops_per_token`, `params_total/active`, `peak_tflops`, `mfu`, `hfu` | Throughput + efficiency KPIs |
| `goodput` | `badput_s` (time lost to non-productive work) | Waste tracking |
| `checkpoint` | `save_ms`, `to_cpu_ms` vs `write_ms`, `size_mb`, `write_mb_per_s` | I/O monitoring |
| `comm` | `moe_a2a` (all-to-all timing on multi-GPU runs) | Distributed comm monitoring |
| `warnings` | Machine-generated list (e.g. gated parts with p10–p90 spread >10%) | Pre-computed data-quality flags |

## 2. Key numbers from this H200 run (`h200_v1`)

- Step (clean): median **401.98 ms**, p10–p90 311–575 ms, **40,758 tokens/s**, MFU 1.3% / HFU 1.7%
- nvidia-smi during clean steps: **util 28% median**, mem 31.5 GiB, SM 1980 MHz, 179 W, 37 °C, **0 thermal slowdowns**
- Trace view: **GPU busy only 22.6%**, **433 host syncs/step**, 18,355 kernels/step
  - Sync sites: `models/moe.py:76` (216/step) and `models/moe.py:78` (216/step) — the per-expert loop dispatch; `__init__.py:1270` (1)
- Memory: peak allocated 25.15 GB on 141 GB card (ample headroom)
- The gap between 28% (nvidia-smi) and 22.6% (busy) confirms the step is **host/CPU-bound** — the GPU idles waiting on Python-side MoE dispatch and optimizer work

## 3. Monitoring-relevant findings (please factor into thresholds/alerts)

1. **Step-time variance is high**: the 5% repeatability gate **failed** — 24/33 gated parts outside 5% between two identical runs (`opt.muon` 72↔82 ms, several `bwd:block*` 14–21%). The report flags p10–p90 spread >10% on 28 parts. **Implication: don't set alert thresholds tighter than ~±10–15% on per-part step times until this is fixed**; whole-step median is more stable than parts.
2. **`opt.muon.ns` is the #1 hot part** (69.4 ms, 17.3% of step) and also the noisiest — if you monitor per-part time, expect this one to swing.
3. **A/B switches change the profile dramatically**: `moe.dispatch=sorted` halves step time (206.8 vs 417.6 ms); `muon_impl=batched` cuts optimizer time 10×. After these land, **baseline dashboards need re-baselining**.
4. **Throttle/slowdown detection works and showed zero events** at 179 W / 37 °C on H200 — safe template for other GPUs.

## 4. How to run / reproduce (Modal, H200)

```powershell
# full suite (tests + bench + A/B + 2-GPU)  — see repo root modal_bench.py
modal run modal_bench.py --stage all --tag <tag>
modal run modal_bench.py --stage bench      # 2-run repeatability benchmark only
modal run modal_bench.py --stage multigpu   # 2-GPU torchrun comm timing
modal run modal_bench.py --stage fetch      # re-download all artifacts from the Modal volume
```

- FineWeb-131K data is cached on Modal volume `era-perf-cache` (data prep runs once, then reused)
- All run artifacts are auto-stashed to that volume after every stage (network-drop safe)
- Console logs: `h200_v1_full_console.log` (successful run), `h200_v1_first_attempt_partial.log` (includes full 274-test correctness output)

## 5. Artifact inventory in this folder

| File | What it is | Gist |
|---|---|---|
| `h200_v1.json` / `-run2.json` | Baseline run JSONs (schema in §1) — the two repeatability runs | — |
| `h200_v1.md` / `-run2.md` | Human-readable reports: full per-part timing tables, slowest-5, warnings | [gist](https://gist.github.com/varshith2000/e394873e87f79d224815b6996a7e3fe1) |
| `h200_v1_comparison.md` | Run-1 vs run-2 gate comparison (the 24/33 FAIL detail) | [gist](https://gist.github.com/varshith2000/5eeebb4cb0ec3e7810782a4cf905d01d) (incl. slowest-5) |
| `h200_v1_slowest.md` | Five slowest parts with week-2 ideas | [gist](https://gist.github.com/varshith2000/5eeebb4cb0ec3e7810782a4cf905d01d) (same gist) |
| `h200_v1_moe_{loop,sorted}.json/.md` | MoE dispatch A/B | [gist](https://gist.github.com/varshith2000/3a491b0af2c21978a35399c0e2dd0717) (incl. Muon A/B) |
| `h200_v1_muon_{loop,batched}.json/.md` | Muon implementation A/B | [gist](https://gist.github.com/varshith2000/3a491b0af2c21978a35399c0e2dd0717) (same gist) |
| `h200_v1_2gpu_comm.json/.md` | 2×H200 torchrun comm benchmark (MoE all-to-all 5.9 ms/step) | [gist](https://gist.github.com/varshith2000/866f394f855ca00dce1a933c7d45d55d) |
| `h200_v1_parts/*.json` | Per-part kernel traces of the 5 slowest parts | — |
| `h200_v1_full_console.log` | Complete console output of the successful run | [gist](https://gist.github.com/varshith2000/63ac8f7d5dae8049597432c94c203a0a) |

## 6. Open items Team 8 should track

- Repeatability variance investigation (Team 06, Week 2) — until resolved, gate/alert thresholds stay loose
- `perfkit/roofline.py` not yet run — will add roofline context to metrics
- Team 5's final architecture config will trigger a re-baseline of everything above
- If Team 8 wants extra telemetry fields in `system`/`trace`, the interface is `perfkit/bench.py` (sampling) + `perfkit/schema.py` (JSON contract) — coordinate changes with Team 06

## Shared gist links (unlisted — anyone with the link can view)

- **Baseline reports (run 1 + run 2):** https://gist.github.com/varshith2000/e394873e87f79d224815b6996a7e3fe1
- **Repeatability gate comparison + slowest-5:** https://gist.github.com/varshith2000/5eeebb4cb0ec3e7810782a4cf905d01d
- **A/B reports (MoE loop vs sorted, Muon loop vs batched):** https://gist.github.com/varshith2000/3a491b0af2c21978a35399c0e2dd0717
- **2×H200 comm benchmark:** https://gist.github.com/varshith2000/866f394f855ca00dce1a933c7d45d55d
- **Full console log:** https://gist.github.com/varshith2000/63ac8f7d5dae8049597432c94c203a0a
