# Team 10 Gate 4 Evidence Summary (live status as of Thu 26 Nov 2026)

Status as of Thu 26 Nov 2026 (Week 4 D5; Gate 4 evidence due Fri 27 Nov, 11:59 PM IST; Go/No-Go Sat 28 Nov). All paths are under `teams/10-post-training/` unless noted. Public text names teams and GitHub handles only. Nothing here claims dry run 2 numbers that have not yet run.

## 1. Gate 4 / Gate 3 Item 7 Required Evidence (SFT & RL Method Decision)

Per TSAI rulings (21 Nov 2026), closing Gate 3 item 7 requires **both** results on the **dry run 2 checkpoint** (test-scale on real `corpus-v1` shards + untied KE2/KAS head `a10_kas_tokdrop` + Team 7 Checkpointer via `#608`):

| Required Evidence | Status (26 Nov) | Code / Job Ready | Blocking External Dependency |
|---|---|---|---|
| **(1) Matched-step DT vs LoRA vs Full FT on dry run 2** | **Pre-run ready & lead-approved (0% GPU run)** | `capstone/dryrun2_dt_compare.py`, `capstone/dryrun2_job_chain.sh`, `capstone/g5_source_resolver.py`, `jobs/2026-11-26-g10-dryrun2-dt-vs-fft.md` + dense (`2026-11-26-g10-dryrun2-dt-vs-fft.log`) and KAS V2 + Team 7 store (`2026-11-26-g10-dryrun2-dt-vs-fft-kas.log`) stand-in logs (`router_bias_unchanged` verified). Results table target: [`results/dt_vs_fft.md` §8](dt_vs_fft.md#8-dry-run-2-capstone-comparison-full-ft-vs-lora-vs-deletion-tuning). | Team 5's delivered dry run 2 checkpoint / run folder (`<T5_OUT>` / `/shared/ckpt/dryrun2-1234`); `#587` slice arm (`a2` vs `a4`, defaults to `a4`). |
| **(2) DT-then-RL chain on dry run 2 DT checkpoint** | **Pre-run ready & lead-approved (0% GPU run)** | `jobs/2026-11-17-dt-then-rl-code.md`, `rl-loop/config/task11_code_canary.yaml`, `capstone/rl_job_v1.py` (`--sampler g5_batch`, `micro_rows: 1`, `completion_logprobs` on completion tokens only), `jobs/2026-11-26-dt-then-rl-staged.log` (real Docker verifier exit 0 + scripted 3-update integrity run with 283 deleted entries at 0). Results table target: [`results/dt_then_rl.md`](dt_then_rl.md#dry-run-2-status--24-november-2026). | `keep_canary/dt/` (`model.safetensors`, `dt_keep_masks.bin`, `dt_keep_masks.bin.json`, `SHA256SUMS`) from job (1) above + delivered run folder & staged pool/probe inputs. |
| **(3) Held-out forgetting & Team 9 watcher verdicts on kept arms** | **Tooling ready (0% GPU run)** | `capstone/forget_bpb_kept.py` (with real-input log `jobs/2026-11-26-g10-forget-bpb-kept.log`), `capstone/watcher_rows_to_report.py`, `sft/tests/forgetting.py` (refuses cross-dtype / non-fraction rows). | Kept Team 7 run folders `keep_t7/g10-dr2-{full,lora,dt}` from job (1) + Team 9 `eval_mini_v1` ARC-Challenge/HellaSwag rows in `bfloat16`. |

## 2. Kept Checkpoints Handed to Team 9 (`eval_schedule.md` #7)

Once jobs (1) and (2) finish, Team 10 hands over these four Team 7 Checkpointer folders for Team 9 `bfloat16` Tier B scoring (`run_lab_ckpt.py --team5-run`, keyed by each folder's `MANIFEST.json` SHA-256 and the final step recorded in `summary.json`):

| Folder | Role | Precision | Step & Manifest SHA-256 | Forgetting Verdict (`forgetting.py`) |
|---|---|---|---|---|
| `keep_t7/g10-dr2-full` | Dry run 2 Full FT SFT arm | `bfloat16` autocast | *Pending dry run 2 run* | *Pending `forget_bpb_kept.py` + Team 9 rows* |
| `keep_t7/g10-dr2-lora` | Dry run 2 LoRA SFT arm | `bfloat16` autocast | *Pending dry run 2 run* | *Pending `forget_bpb_kept.py` + Team 9 rows* |
| `keep_t7/g10-dr2-dt` | Dry run 2 Deletion Tuning SFT arm | `bfloat16` autocast | *Pending dry run 2 run* | *Pending `forget_bpb_kept.py` + Team 9 rows* |
| `g10-rl-final` | Dry run 2 DT-then-RL final checkpoint | `bfloat16` autocast | *Pending DT-then-RL run* | *Pending Team 9 Tier B score* |

## 3. Independent & Supporting Week 4 Evidence Landed (`#746`, `#778`, `#797`, `#835` merged)

| Deliverable | Evidence Level | Paths | Key Numbers / Result |
|---|---|---|---|
| **KE2/KAS V2 + `router_bias` SFT/DT/RL stack** | Unit + Team 5 `#717`/`#748` + CPU stand-in | `rl-loop/team5_adapter.py`, `capstone/sft_g5.py`, `capstone/keep_weights.py`, `capstone/g5_source_resolver.py`, `dt/mask.py` | Untied `a10_kas_tokdrop` head, `router_bias_unchanged: true`, Wanda calibration & `RouteRecorder` routing with `router_bias`, layer-by-layer DT regulariser backward, and auto-checkout of exact Team 5 manifest commit. |
| **Batched G5 RL sampler (`g5_batch`) & memory fixes** | Measured (Colab T4, fp16, T2/T3) + unit | `rl-loop/g5_decode.py`, `results/b5_sampler_2026-11-23.md`, `capstone/rl_job_v1.py`, `sft/bench/train.py` | **12.8x speedup** on T4 (`44.3 s -> 3.45 s` per prompt); `micro_rows: 1`; `completion_logprobs` on completion tokens only; `cache_enabled=False` autocast frees BF16 weight copy. |
| **Team 7 Checkpointer <-> Team 9 watcher bridge** | Offline verified + real-input log | `capstone/run_folder_from_store.py`, `capstone/forget_bpb_kept.py`, `capstone/watcher_rows_to_report.py`, `sft/tests/forgetting.py`, `sft/bench/evaluate.py` | Rebuilds run folders from `#608` stores; `forget_bpb_kept.py` scores held-out bpb in Team 9's dtype; `watcher_rows_to_report.py` validates checkpoint SHA-256 and scales `0..100` points to `[0, 1]` fractions. |
| **7.65B MoE Deletion Tuning study (`Phi-mini-MoE-instruct`)** | Independent public-model study (non-capstone, 1 seed; **not Gate 4 capstone evidence**) | `results/dt_phi_moe.md` | All 1,319 GSM8K (chat): `55.95%` base -> `67.10%` DT (`0.6108%` deleted), `74.98%` LoRA (`lr 2e-4`), `54.36%` Full FT (`lr 1e-5`), `21.83%` Full FT (`lr 3e-5`, `15.9%` HumanEval on 164 problems; not matched to DT at either rate; see HumanEval decode caveat). 4-task prior mean: `64.30 -> 64.46` DT, `64.56` LoRA, `63.68` Full FT (`1e-5`), `58.46` Full FT (`3e-5`). |
| **4B / 8B Qwen3-Base DT vs LoRA vs Full FT ladder job** | Lead-approved job request (awaits TSAI GPU run) | `jobs/2026-11-23-g10-dt-large-model.md`, `.log`, `dt/run_ladder.py`, `dt/ladder_qwen3.yaml` | Pure DT, DT+markers, LoRA, Full FT, and low-LR Full FT at 4B and 8B on H200 (141 GB). |
| **Indic RL human templates (6 authored; `eval` only)** | Decontam 0/1,200 flagged; awaits Team 2 `#781` | `rl/indic/templates/indic_templates.yaml`, `rl/indic_prompts_v0.md` | 2 Tamil (`ta_appalam_sub`, `ta_pen_mult`, reviewer wording applied) + 4 Hindi (`hi_f1_*`, `hi_f6_minutes`, `hi_f3_weekday`); `eligibility: eval` until Team 2 `OK <id>` replies on `#781`. |
| **Verifier hardening, template parity & licence hygiene** | Merged (`#778`, `#797`) + Docker/local verified | `rl/js/`, `rl/jsts/`, `rl/math/`, `rl/toolresult/`, `rl/test_tool_call_hardening.py`, `rl/agentic/`, `rl-data/test_stdio_hardening.py`, `tests/test_chat_template_parity.py`, `eval/results/api_bank_nemotron_overlap.md`, `licences/licence_table.md` | 21 Nov exclusions applied (`sft-indic-nemotron-personas-india`, `rl-math-hendrycks`); API-Bank overlap mask enforced; Team 3 `release/tokenizer_config.json` parity + multi-turn/Indic tool-call tests passing; all 5 `rl/agentic/` tasks (`94 passed`, `10/10` `reward.py --check-all --type agentic`) and `test_stdio_hardening.py` (`13 passed`) verified end-to-end in Docker. |

## 4. Cross-Team Handoffs (Week 4)

| Partner Team | Item | Status (26 Nov) | Next Step |
|---|---|---|---|
| **Team 5 (Architecture)** | Dry run 2 checkpoint (`#720`, `corpus-v1`, KE2/KAS `#717`, `router_bias` `#748`) | `#717`, `#720`, and `#748` merged on `main`; G10 adapter + stand-in verified | Receive `<T5_OUT>` / `/shared/ckpt/dryrun2-1234` and launch `jobs/2026-11-26-g10-dryrun2-dt-vs-fft.md`. |
| **Team 7 (Infrastructure)** | Checkpointer wiring (both ways) | **Ready** (`#608` store read/write verified in `run_folder_from_store.py`, `keep_weights.py`, `forget_bpb_kept.py`) | Export `keep_t7/g10-dr2-{full,lora,dt}` during dry run 2 comparison. |
| **Team 9 (Evaluation)** | `eval_schedule.md` item #7 | **Aligned** (`#747` watcher + `watcher_rows_to_report.py` + `forget_bpb_kept.py`) | Hand over kept folders + `summary.json` step / `MANIFEST.json` SHA-256 after jobs (1)–(2); score `forgetting.py` verdicts. |
| **Team 2 (Data B)** | Native-reader sign-off on 6 human Indic RL templates | **Awaiting `#781` replies** (Tamil wording updated; Hindi reassigned to `@rjvim` on 25 Nov) | Set `team2_reviewer` and `eligibility: train` only after `OK <id>` replies land on `#781`. |

## 5. Remaining Open Items Before Gate 4 (Fri 27 Nov, 11:59 PM IST)

1. **Dry run 2 GPU runs & forgetting verdicts (Gate 4 required):** run `jobs/2026-11-26-g10-dryrun2-dt-vs-fft.md`, `jobs/2026-11-17-dt-then-rl-code.md`, and `capstone/forget_bpb_kept.py` + `sft/tests/forgetting.py` once Team 5 delivers the dry run 2 checkpoint; populate `results/dt_vs_fft.md` §8, `results/dt_then_rl.md`, and section 2 above.
2. **Queued TSAI logs (`#565`, `#587`, `#133`, `#142`):** record returned counts/numbers into their job notes once TSAI posts logs.
3. **Indic RL templates (`issue #781`):** flip `team2_reviewer` and `eligibility: train` once `@truesrini` (Tamil) and `@rjvim` (Hindi) reply `OK <id>`.
