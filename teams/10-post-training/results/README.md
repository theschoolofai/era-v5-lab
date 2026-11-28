# results: committed run reports

Index of the files in this folder. Each entry says what produced it and what it does not show. Numbers live in the linked file, not here.

## Week 3 / Gate 3 summary & core reports

| File | What it is | Limits |
|---|---|---|
| `gate4_summary.md` | Live Gate 4 evidence summary (27 Nov): `dryrun2-1234` pretraining complete (`1,221` steps, sha256 `8d1600b2...`), both dry run 2 job requests 27 Nov lead-approved with Team 9 fixes landed, 6/6 Indic templates `train`, and `#746`/`#778`/`#797`/`#835`/`#836` merged. | Index only; dry run 2 post-training GPU numbers await TSAI job execution. |
| `week4_plan.md` | Week 4 execution plan & Gate 4 tracker (dry run 2 KE2/KAS head DT vs LoRA vs full FT + DT-then-RL, Team 7 Checkpointer, 21 Nov TSAI rulings). | Plan and tracker; dry run 2 numbers land after D5 (Thu 26 Nov). |
| `b5_sampler_2026-11-23.md`, `b5_sampler_2026-11-23/` | Batched G5 RL sampler (`g5_batch`) throughput & memory study: 12.8x speedup on T4 (`44.3 s -> 3.45 s` per prompt at RL job settings). | T4 fp16 throughput/memory stand-in on random-init T2/T3 weights; not a quality number. |
| `gate3_summary.md` | Gate 3 evidence checklist, Week 3 Tasks 1–11 status, cross-team handoffs, and open TSAI decisions (20 Nov). | Index only; numbers live in the linked reports. |
| `rl_data_v1_close.md`, `rl_data_v1_closure.md` | RL data v1 rebuild kit, pool flags (`3,577` code close pool, `7,209` reserved MATH), verifier two-test evidence, and Team 9 handoff. | Pool bytes stay outside Git (rebuilt by TSAI in #564; checked 6/6 by Team 9 in #661). |
| `objective_v1_trainer.md` | Session 18 objective (`rl/objective_v1.py`) integration in `rl-loop/train.py`. | Mechanics verification; not a capstone quality claim. |
| `small_sft.md`, `small_sft_evidence/` | Small SFT run (`SmolLM2-135M`, OCR-2 slice) with `forgetting.py` verdicts (`0.05` bpb limit, `0.01` at-limit mark). | Surrogate model on C3 slice; not re-run on p1536. |
| `small_rl.md`, `code_rl_e1_20261115.md` | Small RL run on code verifiers (`Qwen2.5-Coder-7B-Instruct`, held-out pass@1 `0.151 -> 0.251`, 60 steps). | Surrogate model, one seed; dry-run-1 RL job queued in `jobs/2026-11-19-g10-rl-dryrun1.md`. |
| `dt_vs_fft.md`, `dt_sft_surrogate.md`, `dt_toy_sharpness_check_20261117.md`, `dt_lr_check_20261118.md`, `lab5_dt_muon_recompute.md`, `lab5_grad_coverage.md`, `lab5_dt_study.md`, `lab5_gpu_muon_recompute.md` | Deletion Tuning (candidate, not decided) vs LoRA vs full FT comparison (`SmolLM2-135M`/`1.7B`) + sweeps + Lab 5 Hybrid Muon, activation recompute, idle-expert Muon guard, `--dt-unseen` (`lab5_dt_muon_recompute.json`), TSAI 28 Nov Rule #6 CUDA gradient-coverage checks (`lab5_grad_coverage.json`), 1.01M Team 5 MoE DT study (`lab5_dt_study.json`, `lab5_dt_study_coverage.json`), and RTX 5070 Ti CUDA GPU `66.13M` Team 5 MoE `optim_step_share` / VRAM / recompute benchmark (`lab5_gpu_muon_recompute.json`). | Surrogate models (`dt_vs_fft.md`); `lab5_dt_muon_recompute.md`, `lab5_grad_coverage.md`, `lab5_dt_study.md`, `lab5_gpu_muon_recompute.md`: stand-in MoE checks (mechanics, gradient parity, CUDA `optim_step_share` / peak VRAM at `66.13M`, negative DT@1.01M result, and relative comparison only, not a production-scale claim). Dry run 2 capstone comparison awaits TSAI staging & run. |
| `dt_phi_moe.md` | Deletion Tuning (official code, paper values) of Phi-mini-MoE-instruct (7.65B MoE) on GSM8K SFT, with LoRA and full fine-tuning on the same data: all 1,319 GSM8K questions (chat template) 55.95% base -> 67.10 DT, 74.98 LoRA, 54.36 full FT; four-task prior mean 64.30 -> 64.46, 64.56, 63.68; forward KL per token DT 0.14, LoRA 0.27, full FT 0.48 (same 50 prompts, but the arms are at different fit: +11, +19 and -1.6 GSM8K points). A second full FT arm at lr 3e-5, meant to match DT's gain, fell to 21.83% GSM8K and 15.9% HumanEval on 164 problems (not matched at either rate; see the HumanEval decode caveat inside). | Independent study on a public model, one seed each, LoRA and full FT learning rates not tuned; not the capstone model and not Gate 4 evidence. |
| `dt_paper_size_threshold.md`, `dt_paper_size_threshold_evidence/` | Where the Deletion Tuning paper's claims start to hold, by model size, from its own tables (`../dt/paper_size_table.py`): under GRPO, DT matches full FT from 7B/8B up and trails it below (Qwen 3B reaches 64.2% of FFT's gain, Llama 1B 89.8%); under SFT it matches at 3B (Instruct starts); the low-forgetting result holds at all three Llama sizes from 1B. Plus a check of the released masks against the paper's Table 7. | A reading of the paper (arXiv 2611.10866v1) and its released masks; nothing trained; one number per cell, seeds not stated. |
| `dt_mask_anatomy.md`, `dt_mask_anatomy_evidence/` | Per-expert anatomy of the released Deletion Tuning GRPO masks (`../dt/mask_anatomy.py`). In the Qwen3-30B-A3B mask, 18 of 6,144 expert gate matrices are 39.6-42.1% deleted and hold 50.5% of deletions; on the rebuilt official calibration prompts, 15 of them got 0 tokens and 3 got 1-4. Dry run 2 `expert_load` (#869) has experts 3:11 and 7:13 at 0 tokens in every snapshot from step 1,000 to 1,200, so if the 64 SFT calibration rows also miss them, `layers_without_scores >= 2` is predicted under `--dt-unseen official` (step-0 deletion 0.916% against 0.183% under `keep`, arithmetic); a one-matrix toy of `dt/mask.py` shows the regulariser revives part of an unscored expert during training (50% to 4.4%-43% after 243 steps, depending on gradient clipping). Also the deletion share by model size for design task 2. | Independent study of the authors' released files; routing on a Q4_K_M copy, calibration only; the dry run 2 part is a prediction and a toy, not a run on the step-1,221 weights. |
| `dt_then_rl.md`, `dt_then_rl_evidence/`, `lab5_grpo_dt_vs_fft.md` | Deletion Tuning SFT followed by small RL (3-seed CPU rehearsal; 348,469 deleted weights stayed 0), 26 Nov KAS V2 staged wrapper log, and Lab 5 2-seed GRPO 3-arm comparison (`Full FT` Hybrid Muon vs `LoRA` vs `DT`) with rollout-cache reuse (`lab5_grpo_dt_vs_fft.json`). | Toy/fixture rewards on CPU; `lab5_grpo_dt_vs_fft.md`: CPU stand-in, mechanics and relative comparison only, not a scale claim (do not quote optimizer-share figures as main-run numbers). GPU canary (`jobs/2026-11-17-dt-then-rl-code.md`) awaits TSAI staging & Docker fix. |
| `quant_rollout_mismatch_pytorch.md`, `lab5_quant_rollouts.md`, `lab5_rollout_check.md` | `sarvam-1` quantized GGUF rollouts (`#180` / Team 12 `#908`) against PyTorch `bf16` reference with 95% CIs; training-loop `train.sampler: quant` + `metrics_feed.py` + CPU and RTX 5070 Ti CUDA speed/VRAM/coverage (`lab5_quant_speed_gpu.json`, `lab5_quant_coverage_gpu.json`) + learning runs (`#185`); and firewall-clean periodic Team 9 mini-benchmark rollout check (`#188`). | `quant_rollout_mismatch_pytorch.md`: 48 prompts (`40` En, `8` Indic, `0` code), no `bf16` sampler row; `lab5_quant_rollouts.md`: CPU + CUDA `bf16`/`fp16` speed & simulated `w8a8_sim`/`w4a16_sim` mismatch (no live `vLLM`/GGUF `Q8_0` loop yet); `lab5_rollout_check.md`: tested on made-up score files (`#929` open). |

## Effort suite (`eval/`)

| File | What it is | Limits |
|---|---|---|
| `effort_probe.md` | Suite design and CPU checks, 11 Nov. | Written before any generation run. It says no model had generated anything. |
| `effort_stageA_olmoe_2026-11-12/`, `effort_stageB_olmoe_2026-11-12/` | Per-cell records, per-sample summaries and pooled numbers for OLMoE-1B-7B-0924-Instruct; Stage B also has `report.md` (22 of 440 cells correct). | Not the capstone model. Cap 1024 for every label. Records carry `do_not_train: true`. |
| `attainability_survey_code2048.md` | Code arm re-run at a 2048-token cap on the Qwen stand-in. | Code arm only (32 prompts); math not re-run. A stand-in diagnostic, not a claim about the capstone model. |
| `effort_stageB_qwen_2026-11-12/` | `report.md`, `stageB_pooled.json`, and `sample0/`, `sample1/` (`summary.json`, `effort_stageB.jsonl`). Qwen3.6-35B-A3B-FP8, 55 prompts x 4 labels x 2 samples, cap 1024. | Not the capstone model. Cap 1024 for every label. Records carry `do_not_train: true`. |

## SWE environments (`../swe-envs/`)

| File | What it is | Limits |
|---|---|---|
| `swe_gold_check.md` | Gold check of the 21 environments, `linux/arm64`, 5 Nov. | Checks that tests fail before and pass after the upstream patch. No model attempt. |
| `swe_gold_check_amd64.md` | Same check on `linux/amd64`, 5 Nov. | Run under emulation on an Apple M1 Pro host, not native x86. |
| `swe_gold_reproduction.md` | Independent re-run of one environment (`python-validators__validators-191`), 5 Nov. | One environment. |
| `swe_env_review.md` | Quality review of the first environments against SWE-bench Verified criteria, 4 Nov. | Model-assisted (its header says Claude Sonnet) and "needs a human spot-check". Nothing was executed. Metadata for choosing environments, not training data. |
| `swe_rebench_pilot.md` | Admission results for five environments rebuilt from `nebius/SWE-rebench` PRs, on arm64 and amd64, with the rejected candidates listed. | A pilot of five. |

## RL reward (`../rl/`)

| File | What it is | Limits |
|---|---|---|
| `reward_pool_bench.md` | Rollouts per second with and without warm container pools, 5 Nov. | Throughput on known good and bad outputs on one Mac. It says nothing about model quality. |

## Small SWE tasks (`../swe-task/`, `../swe-task-go/`)

| File | What it is | Limits |
|---|---|---|
| `swe_e2e.md` | Calculator task, Docker. | No model. |
| `go_swe_e2e.md` | Go task, Docker. | No model. |
| `hindi_swe_e2e.md` | Hindi text-preparation task, 30 Oct. | Authored strings; no model, no score (its own statement). |
| `tamil_swe_e2e.md` | Tamil UTF-8 task, 28 Oct, local Python. | Authored strings; no model, no score (its own statement). |
| `kannada_swe_e2e.md` | Kannada serialization and SWE demonstration. | Browser appearance check is described in the report only. |

## Tokenizer and chat format (`../chat-format/`)

| File | What it is | Limits |
|---|---|---|
| `render_frozen_tokenizer.txt` | Output of a run on Team 3's tokenizer v0.1 (sha256 `a33c9907...`). | Not the Gate 2 tokenizer (sha 15468e66...), which is not in the repo as of 12 Nov. |

## Reports that live elsewhere

- SFT decontamination, conversion and OCR-2 records are under `../sft/` and `../docs/`, not here.
- RL data v1 records are in `../rl-data/` (see its README).
