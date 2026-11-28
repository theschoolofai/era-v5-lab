# Fast RL Rollouts Survey & Quantized-Rollout GRPO Plan (Lab 5 Task 5 & Design Task 4)

Rollout generation accounts for **70–85%** of wall-clock time in verifiable-reward GRPO (`16` prompts × `8` completions × `1,536+` tokens per step). This document compares published rollout acceleration methods, states their quality/mismatch costs, names the method Team 10 will test first, and specifies the integration with **Team 12** (quantized policy copy) and **Team 9** (mini-benchmark check every `N` steps).

---

## 1. Comparison of Published Rollout Speedup Methods

| Method | Mechanism | Reported Speedup | Quality / Mismatch Cost | Implementation Complexity |
|---|---|---|---|---|
| **1. Batched KV-cached native decoding (`g5_batch`)** | Pre-allocated KV cache + grouped-head attention across all prompts of a step (`rl-loop/g5_decode.py`) | **12.8x** measured vs unbatched `policy` on T4 (`44.3 s -> 3.45 s`/prompt, `results/b5_sampler_2026-11-23.md`) | **Zero precision mismatch** (`K3 KL = 0` at equal dtype; `logprob_gate` verified) | Already built and merged (`#746`, `#797`) |
| **2. FP8 / INT8 Quantized Rollouts + Mismatch Correction (`FlashRL`, `QuRL`, NVIDIA FP8 RL)** | Generate rollouts with an FP8 or INT8/Q8_0 quantized copy of the policy (`vLLM`/`SGLang`/Team 12 quant copy), compute trainer log-probs and updates in BF16/FP32, and correct off-policy drift with Truncated Importance Sampling (**TIS**, `min(exp(lp_train - lp_rollout), C)`) or trust-region masking (`objective_v1`) | **1.4x–2.2x** rollout throughput (higher memory headroom allows larger batch/concurrency) | Small precision gap (`K3 KL ~ 1e-4 to 1e-2`); **can destabilize RL without TIS/trust-region correction**, especially on long CoT and MoE routing flips | Medium — `rl-loop/grpo.py` already implements `mismatch()` (`K3`, `|log ratio|`) and `tis_weights(tis_clip)`; needs Team 12 quantized copy + fast weight refresh |
| **3. 4-bit Quantized Rollouts with LoRA/Error Compensation (`QeRL`)** | NF4/INT4 quantized rollout weights plus low-rank / adaptive quantization-noise compensation | **2x–3x** memory reduction and higher decode throughput on memory-bound GPUs | Higher token-level log-prob divergence (`K3 KL` up to `10x` FP8); Team 12 wide-pass (`#853`) showed `Q4_K_M` degrades weakest Indic languages first | High — unacceptable Indic drift risk at `Q4_K_M` per Team 12 `#853` |
| **4. Speculative / Draft Decoding (with Team 6)** | Small draft model proposes `k` tokens verified in parallel by the policy model | **1.5x–2.5x** on greedy/low-temp code; lower at `T=0.8–1.0` sampling | **Exact** (mathematically lossless under rejection sampling) | Medium-High — requires a draft model matched to `p1536` tokenizer + Team 6 serving integration |
| **5. Async / One-Step Off-Policy Rollout Pipeline** | Overlap rollout generation of step `t+1` with learner update of step `t` | **1.3x–1.8x** end-to-end step throughput (eliminates GPU idle time) | 1-step policy staleness; requires TIS / trust-region mask (`tr_epsilon = 0.2`) | Medium — needs separate rollout & learner GPU pools |

---

## 2. Which Method Team 10 Tests First (Pick-First Decision) & Team 12 Baselines

**Pick-first: `Q8_0` (and `Q6_K` secondary) Quantized Rollouts (Method 2) on top of `g5_batch` / `vLLM` with TIS + trust-region mismatch correction.**

### Measured Mismatch Data: First-48 (`#894`, `#908`) & Balanced 50-Prompt PyTorch `bf16` Ref (`#190` / Team 12 `#965`)

1. **`llama.cpp` `bf16` ref (`#894`, `teams/12-quantization/rollout/results/rollout_mismatch_sarvam-1.md`):** `sarvam-1`, Kaggle T4 x2, `384` rollouts/format (`48` prompts: **40 English, 8 Indic, 0 code**), `max_new = 256`, `eps = 0.2`, `temperature = 1.0`.
2. **PyTorch `bf16` trainer ref — first-48 (`#180` / `#908`, `results/quant_rollout_mismatch_pytorch.md`):** same 48 prompts, `llama.cpp` GGUF sampler vs PyTorch (`bfloat16` weights, `fp32` logits — `rl-loop/policy.py` setup) with prompt-clustered 95% intervals (`Q8_0` `k3=0.0079`, `Q6_K` `0.0141`, `Q5_K_M` `0.0276`, `Q4_K_M` `0.0751` [`0.0739` against `llama.cpp` `bf16`]).
3. **Balanced 50-prompt PyTorch `bf16` trainer ref with `bf16` engine-floor row (`#190` / Team 12 `#965`):** `10` each of English, Indic, code, tool-call, and reasoning (`400` rollouts/format) on both **`sarvam-1`** (`results/quant_rollout_mismatch_pytorch_balanced_sarvam-1.md`) and **`Qwen2.5-Coder-1.5B`** (`results/quant_rollout_mismatch_pytorch_balanced_qwen2.5-coder-1.5b.md`), plus Team 12's 20k simulated 16-prompt step spread:

| Model & Format | PyTorch Outside `[0.8, 1.2]` (95% CI) | PyTorch `k3` (95% CI) | Top-1 | `tok/s` (T4, vs `llama.cpp bf16`) | Sim. 16-prompt steps `> 0.05` (`#965`) | Team 10 Gate (`k3 <= 0.05`) |
|---|---:|---:|---:|---:|---:|---|
| `sarvam-1` `bf16` (floor) | `0.35%` `[0.22%, 0.49%]` | `0.0012` `[0.0010, 0.0015]` | `97.25%` | `47.6` (`1.00x`) | — | Engine floor |
| `sarvam-1` `Q8_0` | **9.91%** `[8.45%, 11.25%]` | **0.0071** `[0.0062, 0.0079]` | `95.06%` | `76.4` (`1.61x`) | `0%` | **PASS (pick-first)** |
| `sarvam-1` `Q6_K` | **16.16%** `[14.21%, 17.93%]` | **0.0131** `[0.0116, 0.0145]` | `93.61%` | `82.5` (`1.73x`) | `0%` | **PASS (secondary)** |
| `sarvam-1` `Q5_K_M` | `22.61%` `[20.31%, 24.86%]` | `0.0241` `[0.0219, 0.0263]` | `92.11%` | `94.8` (`1.99x`) | `0%` | PASS (`22.61%` masked) |
| `sarvam-1` `Q4_K_M` | `36.70%` `[33.10%, 39.83%]` | **`0.0734`** `[0.0664, 0.0802]` | `86.44%` | `103.3` (`2.17x`) | `100%` | **REJECTED on `sarvam-1`** |
| `Qwen2.5-Coder-1.5B` `bf16` (floor) | `0.31%` `[0.17%, 0.49%]` | `0.0007` `[0.0005, 0.0008]` | `98.30%` | `58.7` (`1.00x`) | — | Engine floor |
| `Qwen2.5-Coder-1.5B` `Q8_0` | **1.58%** `[1.10%, 2.11%]` | **0.0018** `[0.0015, 0.0023]` | `97.69%` | `81.4` (`1.39x`) | `0%` | **PASS (pick-first)** |
| `Qwen2.5-Coder-1.5B` `Q6_K` | **6.20%** `[5.06%, 7.34%]` | **0.0053** `[0.0043, 0.0064]` | `96.26%` | `84.8` (`1.45x`) | `0%` | **PASS (secondary)** |
| `Qwen2.5-Coder-1.5B` `Q5_K_M` | `13.75%` `[11.95%, 15.55%]` | `0.0124` `[0.0104, 0.0145]` | `94.07%` | `90.4` (`1.54x`) | `0%` | PASS (`13.75%` masked) |
| `Qwen2.5-Coder-1.5B` `Q4_K_M` | `25.45%` `[22.47%, 28.16%]` | `0.0468` `[0.0364, 0.0621]` | `90.28%` | `92.3` (`1.57x`) | `35.7%` | **Borderline / mixed-pool risk** |

**Implications for GRPO:**
1. **`Q8_0` is locked as pick-first, with `Q6_K` secondary:** On balanced 50-prompt runs across both models, `Q8_0` (`k3 = 0.0071` on `sarvam-1`, `0.0018` on `Qwen2.5-Coder-1.5B`), `Q6_K`, and `Q5_K_M` stay under `0.05` (with their 95% CIs) and have **`0%` simulated 16-prompt steps above `0.05`**.
2. **`Q4_K_M` is model- and prompt-mix-dependent:** It is **rejected on `sarvam-1`** (`k3 = 0.0734 [0.0664, 0.0802]` balanced; `0.0751` PyTorch / `0.0739` `llama.cpp` on the first-48 prompts) and **borderline on `Qwen2.5-Coder-1.5B`** (`k3 = 0.0468`, CI `[0.0364, 0.0621]` straddles `0.05`, `25.45%` tokens masked). Per-category breakdown (`#190`) shows code is robust (`0.0261`) while **Indic is worst (`0.0910`, `70%` of Indic prompts `> 0.05`)**, causing `35.7%` of simulated 16-prompt mixed steps to trip a per-step `0.05` limit for little extra speed over `Q8_0` (`1.57x` vs `1.39x`). Do not use `Q4_K_M` on mixed Indic+code RL pools without explicit per-model/domain calibration.
3. **Masking vs reweighting:** Because `objective_v1` hard-masks tokens outside `[0.8, 1.2]` (`1.58%`–`9.91%` for `Q8_0`, `6.20%`–`16.16%` for `Q6_K`), compare **`objective_v1` (hard mask)** against **`grpo --tis-clip 2.0` (TIS reweighting)** when live quantized rollouts run.
4. **Existing mismatch instrumentation:** `rl-loop/grpo.py`, `rl-loop/quant_rollout.py`, and `rl-loop/train.py` already compute per-step `mismatch_k3`, `mismatch_abs_logratio`, `tis_clip` importance weights, and `objective_v1`'s closed trust-region mask (`tr_epsilon = 0.2`), plus `capstone/mismatch_g5.py` tracks MoE top-k expert flip rates between engines.
5. **Zero extra model needed:** Unlike speculative decoding, it needs no separate `p1536` draft model.

---

## 3. Experimental Protocol with Team 12 and Team 9 (Design Task 4)

1. **Quantized rollout copy (from Team 12):** Receive Team 12's `Q8_0` / `FP8` policy export (`agreement and KL report` against `bf16` base weights) for the target small model or `dryrun2-1234`.
2. **High-precision learner (Team 10):** Recompute token log-probs in `bf16` autocast with `fp32` master weights in `rl-loop/train.py`, applying `--tis-clip 2.0` (under `grpo`) or `tr_epsilon = 0.2` (under `objective_v1`).
3. **Periodic quality guard (from Team 9):** Every `N = 10` RL updates, evaluate the rollout policy copy on **Team 9's mini-benchmark** (`suite definition`, firewalled).
4. **Metrics reported in PR:**
   - Rollout throughput (`tokens/s` quantized vs `bf16` baseline) and GPU idle time.
   - Mismatch metric (`mean_mismatch_k3`, `p95 |log ratio|`, top-k MoE expert flip rate vs `bf16` rollouts).
   - Held-out verifiable reward curve and Team 9 mini-benchmark score every `N` steps.
   - **Hard stop rule:** abort quantized rollouts if `mean_mismatch_k3 > 0.05` or if Team 9 mini-benchmark drops by `> 2 * stderr` relative to the `bf16` control arm.

### External Dependencies to Execute Live Run
- **Team 12:** Merge `#965` and provide a live quantized policy copy (`Q8_0` / `vLLM` `FP8` / `W4A16`) for the RL loop (balanced 50-prompt `sarvam-1` + `Qwen2.5-Coder-1.5B` PyTorch-ref mismatch + `bf16` sampler baselines already landed via `#190`).
- **Team 9:** Merge `#929` (`minibench_v1` suite definition) for every-`N`-step rollout policy checks (`rl-loop/rollout_check.py`).
