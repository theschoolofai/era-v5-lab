# Team 10 Post-Training Plan: Base Model to Chat Model (Lab 5, v1)

Plan from pre-trained base model to instruction-following chat model released on Hugging Face and Ollama (Team 11 & Team 12). Covers TSAI Lab 5 Task 4 and Design Tasks 0–6 (28 Nov 2026). Public text names teams only.

---

## 1. End-to-End Pipeline Overview

1. **Base checkpoint & frozen tokenizer:** Pre-trained capstone MoE checkpoint (untied KE2/KAS head `a10_kas_tokdrop`, loss-free `router_bias` `gamma=0.001`) + Team 3 frozen `p1536` tokenizer (`tokenizer.json` sha256 `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`, confirmed on PR `#873` Option (a): 15 active markers + 2 reserved `130827`/`130828` keeping frozen slot strings).
2. **Stage 1 — Instruction SFT:** Converts approved, decontaminated SFT datasets (`sft/convert.py`) into ChatML `v0` (`chat-format/chat_template.jinja`, byte-identical to Team 3 `release/tokenizer_config.json`), computes loss on **assistant tokens only**, trains with shape-based **Hybrid Muon** (`capstone/hybrid_optim.py`), and enforces frozen router weights and unchanged `router_bias`.
3. **Stage 2 — Verifiable-Reward GRPO / Session 18 RL:** Runs on top of the selected SFT checkpoint using `rl-loop/train.py` (`algo: objective_v1` / `grpo`) or production `verl` (`v0.4.x`) with exact-check verifiers (`rl/reward.py`), fast quantized rollouts (Team 12 quantized policy + mismatch correction), and frozen router / `router_bias` invariants.
4. **Stage 3 — Forgetting, Evaluation & Release Handoff:** Team 10 measures held-out bits per byte (`capstone/forget_bpb_kept.py --dtype auto`); Team 9 scores firewalled benchmarks (`ARC-Challenge`, `HellaSwag`, code/math/Indic mini-benchmark) in `bfloat16`; `sft/tests/forgetting.py` enforces the `0.05` bpb gate; Team 12 quantizes (`Q8_0` / `Q6_K`) for Hugging Face & Ollama; Team 11 publishes model card + licence attributions.

---

## 2. Stage 1 — Instruction Tuning (SFT)

| Setting | Specification | Source / Evidence |
|---|---|---|
| **Chat template & special tokens** | ChatML `v0`: `<\|im_start\|>` (`129994`), `<\|im_end\|>` (`130816`), `<\|endoftext\|>` (`130822`), `<\|think\|>`/`<\|/think\|>` (`130823`/`130824`), `<\|tool_call\|>`/`<\|/tool_call\|>` (`130773`/`130825`), `<\|tool_result\|>`/`<\|/tool_result\|>` (`130774`/`130826`). Roles (`system`, `user`, `assistant`, `tool`) and effort (`1k/4k/16k/64k`) stay plain text. No NFKC; keep `ZWJ`/`ZWNJ`. | `chat-format/chat_template.jinja`, `special-tokens/special_tokens_v1.md`, Team 3 `#873` |
| **Data & domain shares** | Code `35%`, Agentic `25%`, Tool Use `15%`, Indic `15%`, General/Math `7%` (or `10%` if Safety `0%`), Safety `3%` proposed. Every dataset logged with licence + generator model/licence in `licences/licence_table.md` and decontaminated against Team 9 `fingerprints/v2`. | `sft/sft_mix_proposal.md`, `docs/data_request_teams1_2_v1.md`, `licences/licence_table.md` |
| **Loss mask** | Assistant tokens only (`loss_mask = 1` on assistant think/tool_call/content + `<\|im_end\|>`, `0` on system/user/tool turns). | `sft/convert.py`, `chat-format/render.py` |
| **Packing** | Sequence-packed with document-boundary attention masks (never cross-attending across packed dialogues); initial context `2,048` (`4,096` first extension; admission cap `32,768`). Packing remains opt-in until held-out parity is verified against unpacked (`#831`). | `sft/max_sequence_tokens_proposal.md`, Team 5 `#825`/`#831` |
| **Optimizer** | Shape-based **Hybrid Muon** (`capstone/hybrid_optim.py`): 2D trainable weight matrices -> Muon (`wd=0.0`, `momentum=0.95`, Nesterov, NS5, `skip_zero_grad=True` for idle MoE experts); 1D params -> AdamW. Saves/restores Muon `buf` state; logs `optim_step_share`. | TSAI 28 Nov Muon rule, `results/lab5_dt_muon_recompute.md` |
| **LR & Epochs** | Full FT: `muon_lr = 1e-3..6e-3` (scaled from pre-training peak), AdamW `1e-4`, WSD warmup `5%` + cosine/linear decay, `1–2` epochs. LoRA (`r=16, alpha=32`): `1e-3`, marker rows `1e-2`. DT (`g5_gate`): AdamW `5e-4`, `alpha 100 -> 1000`, `eta=1/2048`, `lambda 1e-5 -> 0`, `--dt-unseen keep` when idle experts occur, marker rows `1e-2`. | `jobs/2026-11-26-g10-dryrun2-dt-vs-fft.md`, `results/lab5_dt_muon_recompute.md` |
| **Evaluation** | Instruction following (format validity, closed `<\|im_end\|>`, effort adherence), Code (`HumanEval+`/`MBPP+`/code verifier screen), Math (`GSM8K`/verifiable math), Indic (`MILU`/Belebele + Indic verifier), plus Forgetting (`forgetting.py`). | `sft/eval_v1.md`, Team 9 `eval_schedule.md` |

### Small SFT Run Evidence (Measured Numbers)
- **`SmolLM2-135M` OCR-2 SFT (`results/small_sft.md`, `results/dt_vs_fft.md`):** equal 400 steps; loss falls cleanly across Full FT, LoRA, and DT; `forgetting.py` verdict pipeline verified (`0.05` bpb limit, `0.01` at-limit mark).
- **7.65B MoE public study (`results/dt_phi_moe.md`, non-capstone):** on `Phi-mini-MoE-instruct` (all 1,319 GSM8K chat): base `55.95%` -> DT `67.10%` (`0.6108%` deleted), LoRA `74.98%`, Full FT `54.36%` (`1e-5`) / `21.83%` (`3e-5`).
- **Hybrid Muon + DT + Activation Recompute stand-in (`results/lab5_dt_muon_recompute.md`):** 2-seed routed MoE stand-in (`full_hybrid_muon` loss `-1.0722`/`-0.9420`, optim share `32–50%`; `dt_adamw` `-0.3458`/`-0.3292`, optim share `8.4–8.9%`; `dt_muon_recompute` gradient parity `<= 1e-6`).

---

## 3. Stage 2 — GRPO / Verifiable-Reward RL

| Setting | Specification | Source / Evidence |
|---|---|---|
| **RL framework & version** | Lab harness: `teams/10-post-training/rl-loop/train.py` (`PyTorch >= 2.4`, `objective_v1` & `grpo`/`dr_grpo`/`rloo`/`gspo`, native `g5_batch` + `vLLM` sampler hooks). At the production scale TSAI sets: **`verl` (`v0.4.x`)** with Ray + `vLLM` (`>= 0.8`) or `SGLang` rollout workers once the capstone model is exported to HF/Megatron format. | `rl-loop/train.py`, `rl/objective_v1.md` |
| **Reward functions & verifiers** | Single entrypoint `rl/reward.py:reward(env_id, output) -> (score, info)`. Verifiers: Python/stdio code (`rl/verifier.py`, `rl-data/stdio_check.py`), JS (`rl/js/`), TS (`rl/jsts/`), Go, Math (`rl/math/`), Indic (`rl/indic/` — 6/6 signed-off `train` templates, `#781`), Tool-call (`rl/tool_call_verifier.py`), Tool-result (`rl/toolresult/`), Agentic/SWE (`rl/agentic/`, `swe-envs/`). | `rl/reward.py`, `results/rl_data_v1_close.md` |
| **Rollout engine** | Small/dry-run-2 scale: `g5_batch` KV-cached batched decoder (**12.8x** speedup on T4: `44.3 s -> 3.45 s`/prompt, `results/b5_sampler_2026-11-23.md`). Production scale: colocated quantized rollout engine (Team 12 `Q8_0`/`FP8` policy copy) + mismatch correction (`rl/fast_rollouts_v1.md`). | `rl-loop/g5_decode.py`, `rl/fast_rollouts_v1.md` |
| **Batch, group size & KL** | `prompts_per_step = 16`, group size `k = 8` (`128` rollouts/step), `max_new = 1,536` (scaling with context), `micro_rows = 1`, `objective_v1`: group-centered advantage without std division, drop equal-reward groups, closed trust-region mask `tr_epsilon = 0.2`, `kl_coef = 0` (reference KL logged for monitoring via `kl_to_start`; `tis_clip = 2.0` enabled when rollout engine differs from trainer precision). | `rl/objective_v1.md`, `rl-loop/config/task11_code_canary.yaml` |
| **Small working RL runs** | (1) `Qwen2.5-Coder-7B-Instruct` (`results/small_rl.md`): 60 steps, train reward `0.299 -> 0.944`, held-out pass@1 **`0.151 -> 0.251`**. (2) DT-then-RL 3-seed CPU rehearsal (`results/dt_then_rl.md`): held-out toy reward **`0.4268 -> 0.6383`**, 348,469 deleted weights held at zero. (3) KAS V2 staged wrapper log (`jobs/2026-11-26-dt-then-rl-staged.log`): 3 scripted updates, 283 deleted entries at zero. | `results/small_rl.md`, `results/dt_then_rl.md` |
| **Team 8 RL metrics feed** | `metrics.jsonl` per step: `step`, `reward_mean`, `heldout_reward`, `mixed_group_frac`, `mismatch_k3`, `mismatch_abs_logratio`, `rollout_tok_s`, `optim_step_share`, `idle_seconds`, `peak_vram_gb`, `router_checksum_ok`. | `rl-loop/train.py` -> **Team 8** |

---

## 4. Forgetting vs Learning Separation (Design Task 5)

To separate genuine task learning from catastrophic forgetting, Team 10 enforces a **two-signal gate** (`sft/tests/forgetting.py`):
1. **Pre-training retention (Team 10):** Held-out bits per byte (`heldout_v1`, 15 slices including English, Code, and 10 Indic languages) measured in Team 9's exact `bfloat16` autocast rule (`capstone/forget_bpb_kept.py --dtype auto`). Failure threshold: `delta_bpb > +0.05` (`±0.01` flagged at limit).
2. **Firewalled general capability (Team 9):** Team 9's watcher scores base vs post-trained checkpoints on `ARC-Challenge` (500) and `HellaSwag` (400) in `bfloat16`, handed through `capstone/watcher_rows_to_report.py` (`primary: true` `acc_norm`, scaled to `[0, 1]`, checkpoint SHA-256 verified). Failure threshold: drop exceeding `max(2 * combined_stderr, 0.01)`.
3. **Task learning signal:** Measured separately on held-out SFT eval NLL, chat-format validity, closed-turn rate, and held-out verifiable RL pass rate (strictly firewalled from training pools).

---

## 5. Waste Elimination & Compute Discipline (Design Task 6 + Lab 5 Rules)

- **Share base weights across arms:** `capstone/dryrun2_dt_compare.py` measures base-model eval/forgetting **once** (`--no-before` on LoRA and DT) and reads one immutable base checkpoint across all three arms.
- **Cache rollouts & never rerun unchanged arms:** `rl-loop/train.py` saves step-level `rl_state/` checkpoints (and preserves `rl_state/` if final weight export fails so a rerun resumes without repeating training or rollouts); SFT/RL arms write independent `out/sft_<arm>/` folders keyed by input SHA-256 manifests and skip lists.
- **Rate, memory, idle & optimizer reporting:** Every run logs `tokens/s`, peak GPU memory, `optim_step_share`, and phase-synced wall times (`rollout`, `reward`, `old_logprobs`, `train`, `idle`).

---

## 6. Cross-Team Connections & What Is Missing

| Interface | Partner | Format / Check | Current Status & Gaps |
|---|---|---|---|
| Data requests -> Candidate SFT/RL data | Teams 1 & 2 | `docs/data_request_teams1_2_v1.md` -> `parquet`, `pack_table`, F2 | Request written; **missing:** full SFT parquet mix, non-benchmark RL math pool, and human Indic RL templates for 8 remaining languages (`te, kn, bn, mr, gu, ml, or, pa`) |
| Special-token confirmation | Team 3 | `release/SPECIAL_TOKENS.md`, `e6b93a93...` | Verified (`#873` Option (a) recommended); awaits TSAI merge of `#873` |
| Quantized rollout policy | Team 12 | `Q8_0`/`Q6_K` copy + agreement & KL report (`#894`) | First `llama.cpp` quantization-only mismatch report merged (`#894`, `sarvam-1`: `Q8_0` `k3=0.0065`/`9.18%` outside `[0.8, 1.2]`, `Q4_K_M` rejected at `k3=0.0739`/`40.99%`). **Missing:** PyTorch `bf16` reference run + `bf16` `tok/s` baseline and live quantized policy copy for Design Task 4 GRPO run |
| Mini-benchmark & held-out sets | Team 9 | `eval_mini_v1` suite definition | Watcher + bridge verified (`#861`); **missing:** live Tier B rows on `dryrun2-1234` SFT/RL kept arms |
| RL metrics dashboard feed | Team 8 | `metrics.jsonl` dashboard feed | Schema ready in `rl-loop/train.py`; **missing:** live GPU dry run 2 RL metrics stream |
| Plan & licences for model card | Team 11 | `post_training_plan_v1.md`, `licences/licence_table.md` | Delivered; **missing:** TSAI confirmation of 28 Nov NC/ND/unstated licence typo and final dry run 2 SFT/RL method numbers |
| Dry run 2 GPU execution | TSAI | `jobs/2026-11-28-g10-dryrun2-staging-recipe.md` | **Missing:** TSAI staging of OCR-2 shards `0–3` + RL pools and Docker runner fix on job machine |
