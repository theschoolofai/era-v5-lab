# Lab 5 Deletion Tuning Findings: Hybrid Muon, Activation Recompute, and Unseen MoE Experts (28 Nov 2026)

**Scope & limits:** CPU stand-in routed MoE (2 layers, `d=48`, `h=96`, 6 experts top-2, 2 seeds, 20 steps), paired with prior public-model (`SmolLM2-135M`/`1.7B`, `Phi-mini-MoE-instruct` 7.65B) evidence. The stand-in tests **mechanics, gradient parity, optimizer step-time share, storage, and failure modes** — not capstone model quality or 7B+ scaling behavior.

**Exact reproduction commands:**
```bash
uv run --no-project --with pytest --with torch --with pyyaml --with safetensors --with numpy \
  python -m pytest teams/10-post-training/dt/test_lab5_dt_compat.py teams/10-post-training/capstone/test_dryrun2_dt_compare.py -v -p no:cacheprovider
uv run --no-project --with torch --with numpy \
  python teams/10-post-training/dt/run_lab5_dt_checks.py --steps 20 --seeds 1 2 --out teams/10-post-training/results/lab5_dt_muon_recompute.json
```
Raw output: [`lab5_dt_muon_recompute.json`](lab5_dt_muon_recompute.json).

---

## 1. Does Deletion Tuning Work with Shape-Based Hybrid Muon and Activation Recompute?

**Summary verdict (including negative result):**
- **Activation recompute (`use_reentrant=False`) + DT:** **PASS** (gradient-equivalent, `<= 1e-6`).
- **Muon on DT `.gate` logits (`--dt-gate-optim shape`, matched `lr = 5e-4`):** **REJECTED (negative result).** Training is finite, but AdamW drops loss **~3.3x faster** (`-0.3458` / `-0.3292` vs `-0.1033` / `-0.0992` across 2 seeds) at **< half the optimizer step-time share** (`8.4–8.9%` vs `20.2–21.7%` on CPU). Reason: Newton-Schulz orthogonalizes the 2D gate gradient (`rms ~ lr / sqrt(cols)`), coupling entries of an element-wise binary mask. Under Hybrid Muon, keep DT `.gate` logits on AdamW (`--dt-gate-optim adamw`, default in `capstone/sft_g5.py`) while routing non-gate 2D matrices to Muon. *(Scope caveat: higher `muon_lr` and 7B+ widths were not swept here.)*

Details:
1. **DT + Hybrid Muon (`dt_adamw` vs `dt_muon_shape`):** Under TSAI's 28 Nov shape-based rule (`ndim == 2 -> Muon`, `non-2D -> AdamW`), `MaskedLinear.gate` (`[out, in]`) is 2D and routes to Muon. `capstone/hybrid_optim.py` and `capstone/sft_g5.py` support both `--dt-gate-optim shape` (pure shape rule) and `--dt-gate-optim adamw` (recommended), plus full Muon momentum buffer (`buf`) checkpoint save/restore (`test_hybrid_muon_shape_routing_and_momentum_checkpoint_roundtrip` passes bit-exact).
2. **DT + Activation Recompute (`torch.utils.checkpoint(..., use_reentrant=False)`):** Compatible and gradient-equivalent. `MaskedLinear.weight` recomputes `W * sigmoid(alpha * G)` deterministically within a step (since `dtmask.step_all()` runs after `backward()`), and `regulariser_backward_()` is already graph-free. `test_dt_with_activation_recompute_matches_standard_gradients` matches uncheckpointed `.gate.grad` within `atol=1e-6, rtol=1e-5`, and 20-step runs match to 4 decimal places (`loss_end` `4.2050` vs `4.2051` on seed 1; `4.3416` vs `4.3416` on seed 2).

### Measured 2-Seed Stand-In Comparison (20 steps, identical base weights per seed)

| Arm | Seed | Trainable Params | Loss Start -> End (Drop) | Wall Time (s) | Optim Time (s) | Optim Share of Step Time | Deleted Frac (Targeted) | Delta Storage (Bytes) |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| `full_hybrid_muon` | 1 | 172,752 | `4.3155 -> 3.2432` (`-1.0722`) | 0.4635 | 0.2320 | **50.05%** | 0.0000 | 345,504 (bf16) |
| `lora_adamw` | 1 | 13,824 | `4.3155 -> 4.2753` (`-0.0401`) | 0.0873 | 0.0149 | **17.08%** | 0.0000 | 27,648 (bf16) |
| `dt_adamw` | 1 | 55,296 | `4.3083 -> 3.9625` (`-0.3458`) | 0.0912 | 0.0081 | **8.93%** | 0.5052 | 6,912 (1-bit mask) |
| `dt_muon_shape` | 1 | 55,296 | `4.3083 -> 4.2050` (`-0.1033`) | 0.0940 | 0.0204 | **21.71%** | 0.5006 | 6,912 (1-bit mask) |
| `dt_muon_recompute` | 1 | 55,296 | `4.3083 -> 4.2051` (`-0.1033`) | 0.1481 | 0.0206 | **13.94%** | 0.5006 | 6,912 (1-bit mask) |
| `full_hybrid_muon` | 2 | 172,752 | `4.4401 -> 3.4980` (`-0.9420`) | 0.2117 | 0.0682 | **32.22%** | 0.0000 | 345,504 (bf16) |
| `lora_adamw` | 2 | 13,824 | `4.4401 -> 4.4017` (`-0.0384`) | 0.0840 | 0.0116 | **13.82%** | 0.0000 | 27,648 (bf16) |
| `dt_adamw` | 2 | 55,296 | `4.4408 -> 4.1116` (`-0.3292`) | 0.0990 | 0.0083 | **8.40%** | 0.5015 | 6,912 (1-bit mask) |
| `dt_muon_shape` | 2 | 55,296 | `4.4408 -> 4.3416` (`-0.0992`) | 0.1087 | 0.0219 | **20.16%** | 0.5014 | 6,912 (1-bit mask) |
| `dt_muon_recompute` | 2 | 55,296 | `4.4408 -> 4.3416` (`-0.0992`) | 0.1507 | 0.0209 | **13.86%** | 0.5015 | 6,912 (1-bit mask) |

---

## 2. Finding for TSAI: Idle-Expert Zero-Gradient Momentum Re-Inflation in Fused MoE Muon

In a fused/stacked MoE forward (such as Team 5's `torch.stack` over routed experts), an expert that receives **zero tokens** in a step gets an **all-zero gradient tensor** (`p.grad == 0`), **not** `p.grad is None`.
- In standard `Muon.step()` (`skip_zero_grad=False`, matching `teams/05-architecture/harness/week2/optim.py`), the `if p.grad is None: continue` check does not trigger. `buf` decays by `0.95`, and `zeropower_batched()` divides by `X.norm() + eps`, **re-inflating stale momentum back to unit spectral norm** and applying a full-magnitude update to an idle expert.
- Measured on a `32x16` matrix at `muon_lr = 0.006`:
  - `skip_zero_grad=False`: max abs weight drift on an all-zero gradient step = **`0.003745`**.
  - `skip_zero_grad=True` (`capstone/hybrid_optim.py`): max abs weight drift = **`0.0`** (bit-exact unchanged).
- Note: the same bug is still live in `teams/05-architecture/harness/week2/optim.py:78` on `main`; an independent failing test against Team 5's `optim.py` (`#875`) reproduces `2.78x` weight-norm growth over 50 zero-grad steps and leaves the fix to Team 5 / TSAI.

---

## 3. Finding: Unseen MoE Experts in DT Wanda Calibration (`--dt-unseen official` vs `keep`)

When a routed MoE expert receives zero tokens during Wanda calibration (`layers_without_scores > 0`), `--dt-unseen official` leaves its logits at `N(0, 0.01^2)` — deleting ~50% of its gate weights at step 0 (far above `eta = 1/2048 = 0.049%`). On our 2-seed routed MoE stand-in with 4 of 12 expert layers idle during calibration:

| Seed | `--dt-unseen` Policy | `layers_without_scores` | Initial Deleted Frac (Targeted) |
|---:|---|---:|---:|
| 1 | `official` | 4 / 12 | **16.764%** |
| 1 | `keep` | 4 / 12 | **0.177%** |
| 2 | `official` | 4 / 12 | **16.873%** |
| 2 | `keep` | 4 / 12 | **0.157%** |

`capstone/dryrun2_dt_compare.py` now records both `dt_unseen_policy` and `dt_layers_without_scores` in `compare.json` and `compare.md`. Recommendation: inspect `layers_without_scores` on `dryrun2-1234` and run `--dt-unseen keep` whenever any routed expert receives zero calibration tokens.

---

## 4. Model Size Threshold Where Paper Claims Start to Hold (arXiv 2611.10866)

- **Paper regime (arXiv 2611.10866):** Claims low-forgetting SFT/GRPO gains from ~**7B+ parameters** upward where MLP gate projections have sufficient over-parameterized redundancy (`0.5–1%` binary deletion suffices).
- **Lab empirical checks so far:**
  - `SmolLM2-135M` / `1.7B` (`results/dt_vs_fft.md`): small dense models show higher sensitivity to deletion fraction and matched-fit ordering can flip.
  - `Phi-mini-MoE-instruct` `7.65B` (`results/dt_phi_moe.md`, independent public study): `0.6108%` deleted on 512 expert gates gave `+11.15` pts on all 1,319 GSM8K (`55.95% -> 67.10%`) with minimal prior-task drift (`64.30 -> 64.46`), whereas LoRA reached `74.98%` and untuned Full FT did not match at `1e-5` or `3e-5`.
  - **Still unmeasured:** (1) `dryrun2-1234` capstone checkpoint (awaits TSAI staging/Docker fix), (2) Qwen3 `4B`/`8B` ladder (`jobs/2026-11-23-g10-dt-large-model.md`, queued), and (3) GRPO DT vs LoRA vs Full FT on GPU (only CPU rehearsal + staged wrapper log completed so far).
