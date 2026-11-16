# Deletion Tuning, LoRA, and full fine-tuning

**Status (TSAI / Instructor guideline, 15 Nov 2026):** Deletion Tuning (`arXiv 2611.10866`) is evaluated here as a **potential candidate** for final training, **not yet a decision**. TSAI decides at Gate 3 after reviewing these findings.

Port of `arXiv 2611.10866`, read from `agentic-learning-ai-lab/deleting-weights` (`src/learnable_sparsity`, MIT). Portable CPU reference code is in `sft/deletion_tuning.py` (equal-step synthetic check `sft/dt_vs_fft.py`), and PyTorch/GPU training modules are in `dt/mask.py` (`dt/run_triple.sh`).

## 1. Surrogate open-model comparison (`SmolLM2-135M` and `SmolLM2-1.7B`, equal 400 steps)

**Evidence level: surrogate, exploratory (one seed per arm except 135M full FT with 3 seeds).** Full setup, CIs, McNemar tests, untied-head probes, and caveats are in `results/dt_sft_surrogate.md`.

- **Slice:** OCR-2 `slice-v1` (train `2,509` rows / `531` clusters, dev `300`, test `300` rows / `110` clusters, `<= 2,048` tokens, no overlap with held-out families).
- **Equal steps:** 400 optimizer steps × 8 rows across all methods (`AdamW`, BF16 autocast, FP32 master weights).
- **Arms:** Full FT (`lr 1e-4`), LoRA (`r=4, alpha=8`, `q/k/v/o/gate/up/down`, `lr 1e-3`), pure DT (`gate_proj` masks only, `alpha 100->1000`, Wanda prior `eta=1/2048`, `lambda 1e-5->0`, `lr 2e-3`), and **DT+m hybrid** (DT plus the 5 chat-marker embedding/head rows trainable at `lr 1e-4`).

| Model | Start | Method | Test target bpb ↓ | Format valid (/110) ↑ | Exec pass@1 (/100, validated /69) | Held-out v1 bpb Δ vs base ↓ | Deleted (gate / all weights) |
| --- | --- | --- | ---: | ---: | --- | ---: | --- |
| `SmolLM2-135M` | base | untrained | 0.8148 | 0 | 0 / 0 | 1.0981 (base) | — |
| `SmolLM2-135M` | base | Full fine-tuning (3 seeds) | **0.4836** | **81–87** (mean 76.7%) | 1–2 / — | +0.0508 | — |
| `SmolLM2-135M` | base | LoRA (`r=4`) | 0.5283 | 0 | 0 / — | +0.0384 | — |
| `SmolLM2-135M` | base | Deletion Tuning (pure) | 0.5321 | 0 | 0 / — | **+0.0279** | 3.22% / 0.63% |
| `SmolLM2-135M` | base | DT + marker rows (hybrid) | 0.5287 | 63 | 1 / 1 | +0.0295 | 3.21% / 0.63% |
| `SmolLM2-1.7B` | base | untrained | 1.0490 | 0 | 0 / 0 | 0.8434 (base) | — |
| `SmolLM2-1.7B` | base | Full fine-tuning | **0.3332** | **93** | **21 / 20** | +0.0746 | — |
| `SmolLM2-1.7B` | base | LoRA (`r=4`) | 0.3500 | 84 | 18 / 17 | +0.0687 | — |
| `SmolLM2-1.7B` | base | Deletion Tuning (pure) | 0.3698 | 0 | 0 / — | +0.0163 | 1.32% / 0.31% |
| `SmolLM2-1.7B` | base | DT + marker rows (hybrid) | 0.3633 | 76 | 13 / 13 | **+0.0091** | 1.25% / 0.29% |
| `SmolLM2-1.7B` | instruct | untrained | 0.5815 | 107 | 13 / 13 | 0.9061 (base) | — |
| `SmolLM2-1.7B` | instruct | Full fine-tuning | **0.3284** | **91** | **22 / 22** | +0.0402 | — |
| `SmolLM2-1.7B` | instruct | LoRA (`r=4`) | 0.3409 | 8 | 0 / — | +0.0190 | — |
| `SmolLM2-1.7B` | instruct | Deletion Tuning (pure) | 0.3556 | 0 | 0 / — | **+0.0054** | 1.22% / 0.29% |

*Additional `1.7B` base run (`dt_sft_surrogate.md` R7): LoRA + marker rows gave `0.3483` test bpb, `81/110` valid replies, `15/100` (`14/69`) exec, `+0.0381` held-out drift.*

## 2. Deletion-fraction and target-layer sweep (`SmolLM2-135M`, DT + marker rows)

From `results/dt_sft_surrogate.md` §R10 (tied head, 5 marker rows trainable in every arm, base held-out v1 bpb `1.0981`, one seed):

| Target layers | Init quantile (`eta`) | Deleted at init (targeted) | Deleted at end (targeted / all) | Test target bpb ↓ | Format valid (/110) ↑ | Supplement valid (/22) | Held-out v1 bpb Δ ↓ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MLP gate (`gate_proj`) | `1/8192` | 0.15% | 3.17% / 0.63% | 0.5288 | 62 | 13 | +0.0295 |
| MLP gate (`gate_proj`, ref) | `1/2048` | 0.18% | 3.21% / 0.63% | 0.5287 | 63 | 9 | +0.0295 |
| MLP gate (`gate_proj`) | `1/256` | 0.52% | 3.50% / 0.69% | 0.5286 | 59 | 12 | **+0.0276** |
| All MLP (`gate, up, down`) | `1/2048` | 0.18% | 1.55% / 0.92% | **0.5048** | **71** | 12 | +0.0426 |
| Attention (`q, k, v, o`) | `1/2048` | 0.18% | 2.65% / 0.52% | 0.5303 | **71** | 11 | +0.0471 |

## 3. Findings (what held and what failed)

1. **Forgetting vs capability trade-off:** Pure Deletion Tuning keeps held-out forgetting far lower than Full FT (`+0.0163` vs `+0.0746` at 1.7B base, `0.22×`), and reaches `0.949` of Full FT's target-bpb gain at 1.7B base.
2. **Pure DT fails new special-token format (`0/110`):** When chat markers (`<|im_start|>`, `<|im_end|>`, `<|think|>`, `<|/think|>`) are untrained embeddings, pure DT leaves embedding/output weights frozen and produces **0/110** valid formatted replies across 135M base, 1.7B base, and 1.7B instruct.
3. **Hybrid DT + output marker rows recovers most format (`76/110` at 1.7B):** Allowing the 5 marker rows on the output head to train (`dt_sft_surrogate.md` §R8) recovers `76/110` valid replies and `13/100` exec pass@1 at 1.7B while keeping forgetting at `+0.0091` (`0.12×` Full FT), though still behind Full FT (`93/110`, `21/100`) and LoRA (`84/110`, `18/100`).
4. **Init deletion fraction vs target layers:** A 32× sweep in initial Wanda quantile (`1/8192` to `1/256`) barely changes final deletion (`3.17% -> 3.50%`) or metrics; training determines sparsity. Expanding target layers from `gate_proj` to all MLP lowers test bpb (`0.5287 -> 0.5048`) at the cost of ~45% more forgetting (`+0.0295 -> +0.0426`).
5. **Capstone caveat:** All runs above are on dense `SmolLM2` with `AdamW`, not the capstone MoE with `Muon` / `KE2`. See `jobs/2026-11-19-dt-vs-fft-1.7b.md` for the TSAI reproduction request (`1.7B` base row).

## 4. Local CPU update-rule smoke check

`sft/dt_vs_fft.py --steps 30 --seed 0` (32 synthetic rows, 4×4 gate, no benchmark text; log `jobs/2026-11-14-dt-vs-fft.log`, job `jobs/2026-11-14-dt-vs-fft.md`):

| Method | Steps | Loss at step 0 | Loss at step 30 | Base weight changed | Hard-mask deleted fraction |
| --- | ---: | ---: | ---: | --- | ---: |
| Deletion Tuning | 30 | 0.020717 | 0.020717 | no | 0 |
| LoRA, rank 1, gate only | 30 | 0.020719 | 0.020687 | no | — |
| Full fine-tuning | 30 | 0.020719 | 0.002844 | yes | — |
