# Lab 5 GRPO 3-Arm Comparison (Full FT vs LoRA vs Deletion Tuning) & Rollout Cache Check (28 Nov 2026)

**Scope & limits:** CPU stand-in, mechanics and relative comparison only, not a scale claim. Routed MoE stand-in (`2` layers, `d=48`, `h=96`, `6` experts top-2, `2` seeds, `12` `objective_v1` GRPO updates, verifiable toy reward). Do not quote wall times or optimizer-share figures as main-run numbers.

**Exact reproduction commands:**
```bash
uv run --no-project --with torch --with numpy \
  python teams/10-post-training/dt/run_lab5_grpo_compare.py --steps 12 --seeds 1 2 \
  --out teams/10-post-training/results/lab5_grpo_dt_vs_fft.json
uv run --no-project --with pytest --with torch --with pyyaml --with safetensors --with numpy \
  python -m pytest teams/10-post-training/dt/test_lab5_grpo_and_cache.py -v -p no:cacheprovider
```
Raw output: [`lab5_grpo_dt_vs_fft.json`](lab5_grpo_dt_vs_fft.json).

---

## 1. Matched-Seed GRPO Comparison (`objective_v1`, shared base weights & step-0 rollout cache)

All three arms per seed load the exact same base weights and reuse cached step-0 rollouts via `rl-loop/rollout_cache.py` (`hits=2, misses=1, hit_rate=66.67%` per seed — `lora_adamw` and `dt_adamw` skip redundant step-0 sampling).

| Arm | Seed | Updates | Trainable Params | Held-Out Reward (`before -> after`, `Δ`) | Held-Out `Δbpb` (Forgetting) | Wall Time (s) | Rollout Time (s) | Optim Time (s) | Optim Share of Step Time | Delta Storage (Bytes) |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `full_hybrid_muon` | 1 | 12 | 172,752 | `0.0469 -> 0.0469` (`+0.0000`) | `+0.0013` | 0.9162 | 0.2081 | 0.1621 | 17.70% | 345,504 (bf16) |
| `lora_adamw` | 1 | 12 | 13,824 | `0.0469 -> 0.0469` (`+0.0000`) | `-0.0010` | 0.4083 | 0.1749 | 0.0084 | 2.06% | 27,648 (bf16) |
| `dt_adamw` | 1 | 12 | 55,296 | `0.0469 -> 0.0469` (`+0.0000`) | `-0.0092` | 0.4139 | 0.1784 | 0.0063 | 1.53% | 6,912 (1-bit mask) |
| `full_hybrid_muon` | 2 | 12 | 172,752 | `0.0938 -> 0.1094` (`+0.0156`) | `+0.0072` | 0.7401 | 0.1937 | 0.0474 | 6.41% | 345,504 (bf16) |
| `lora_adamw` | 2 | 12 | 13,824 | `0.0938 -> 0.0938` (`+0.0000`) | `-0.0002` | 0.4341 | 0.1873 | 0.0105 | 2.43% | 27,648 (bf16) |
| `dt_adamw` | 2 | 12 | 55,296 | `0.0938 -> 0.0938` (`+0.0000`) | `+0.0061` | 0.4179 | 0.1809 | 0.0065 | 1.55% | 6,912 (1-bit mask) |

## 2. Engineering Findings (Design Tasks 2, 3, 6 & Hybrid Muon)

1. **Zero hard-coded AdamW across all G10 trainers:** `capstone/sft_g5.py`, `sft/bench/train.py`, and `rl-loop/train.py` now all support shape-based **Hybrid Muon** (`capstone/hybrid_optim.py`), save/restore Muon momentum buffers (`buf`) in checkpoints, and report `optimizer.optim_step_share`.
2. **DT-then-RL (`keep_zero`) × Hybrid Muon contract (`test_lab5_grpo_and_cache.py`):** Because Muon's Newton-Schulz orthogonalization couples entries across rows/columns, an orthogonalizing update refills element-wise deleted zero entries unless `keep_zero` runs with `enforce: true` (post-step re-zeroing). `rl-loop/train.py` enforces this via `kz.check_optimizer(...)`: AdamW passes with gradient masking alone, whereas `hybrid_muon` with `keep_zero` requires `enforce: true`.
3. **Rollout-cache reuse (`rl-loop/rollout_cache.py`):** Step-0 rollouts keyed by `(checkpoint_sha256, prompts_sha256, sampler_cfg_sha256)` achieved a `66.67%` hit rate across the 3-arm comparison (`hits=2, misses=1` per seed), avoiding duplicate rollout sampling on identical starting weights.
4. **What this stand-in cannot show:** Real code/math/Indic reward climb, 7B+ DT scaling, or GPU/bf16 throughput — those depend on TSAI staging & running `jobs/2026-11-26-g10-dryrun2-dt-vs-fft.md` + `jobs/2026-11-17-dt-then-rl-code.md` and Team 12 / Team 9 quantized-rollout runs.
