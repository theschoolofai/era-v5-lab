# Team 10 Written Data Request to Teams 1 (Data A) and 2 (Data B) — Lab 5

Prepared for **Team 1 (Data A)** and **Team 2 (Data B)** per TSAI Lab 5 Design Task 0 (due Sunday 29 Nov 2026; full Lab 5 evidence due Wed 2 Dec, 7:00 AM IST). All paths are under `teams/10-post-training/`.

---

## 1. Contract & Format Requirements (Public Formats and Checks)

Every candidate SFT or RL dataset handed from Teams 1 & 2 to Team 10 must satisfy:
- **Delivery format:** Parquet (`*.parquet`) with a corresponding `pack_table` row (source ID, HF repo/revision commit SHA, row count, token count on frozen `p1536`, licence, generator model + licence, and SHA-256).
- **Tokenizer pin:** Team 3 frozen `p1536` (`tokenizer.json` sha256 `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`).
- **Cleaning & F2 checks:**
  - Strip invisible zero-width junk (`U+200B`, `U+FEFF`) and upstream chat ghost markers (`[INST]`, `[/INST]`, `<think>`, `### Assistant:`).
  - **Do NOT apply NFKC** to content; **preserve `ZWJ` (`U+200D`) and `ZWNJ` (`U+200C`)** verbatim for Indic scripts.
  - Pass F2 contamination/integrity checks and Team 9 `decontam_check.py` (fingerprints v2, `set_sha256` `2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a`) + `canary_scan.py` with **0 flagged** rows.
- **Licence & generator rule (`licences/licence_table.md` — TSAI 28 Nov rule):**
  - **NC, ND and unstated licences are allowed** for all data, post-training data included (TSAI 28 Nov Lab Rules #1).
  - For every source, record the **licence** and **where you found it**; if a model made the data, also record the **generator model** and the **licence terms of that model**.
  - **Benchmark exclusion:** Do not stage benchmark datasets as training data (`rl-math-hendrycks` excluded 21 Nov; HellaSwag excluded 28 Nov due to wikiHow DMCA takedown HTTP 451).

---

## 2. SFT Instruction Data Request (Stage 1 — Base to Chat)

Target schema: chat messages JSON/Parquet (`messages: [{role, content, think?, tool_calls?}]`, optional `tools`, `effort`, `language`, `source_id`) convertible by `teams/10-post-training/sft/convert.py` into ChatML `v0` with assistant-only loss masks (`1` on `assistant` turns, `0` on `system`/`user`/`tool`).

| # | Domain | Target Share | Requested Volume (Rows / Tokens) | Target Team | Candidate Sources (`licences/licence_table.md`) | Quality Filter |
|---|---|---:|---|---|---|---|
| 1 | **Code** | 35% | ~400k–600k rows (~2.5B tok) | Team 1 | `nvidia/OpenCodeReasoning` & `OpenCodeReasoning-2` (`pass_rate == 1.0`, firewalled), `open-r1/codeforces-cots`, `bigcode/commitpackft` | Execution-verified (`pass_rate=1.0`), `<= 32,768` tok, eval-firewall applied against RL & effort suites |
| 2 | **Agentic (SWE / Terminal)** | 25% | ~100k–250k trajectories (~1.5B tok) | Team 1 | `nebius/SWE-rebench-openhands-trajectories`, `nvidia/Nemotron-Cascade-SFT-SWE`, `nvidia/Nemotron-Terminal-Corpus` | Verified pass trajectories, deduped by instance ID, zero SWE-bench Verified/Live/Pro repo overlap |
| 3 | **Tool Calling** | 15% | ~150k–300k dialogues (~0.8B tok) | Team 1 | `Salesforce/xlam-function-calling-60k`, `nvidia/Nemotron-Agentic-v1`, `nvidia/Nemotron-SFT-Agentic-v2` (tool-calling split only) | Valid JSON schema binding, multi-turn + negative ("no tool needed") turns, API-Bank overlap mask applied |
| 4 | **Indic Instructions** | 15% | ~150k–300k dialogues (~0.8B tok) | **Team 2** | `CohereLabs/aya_dataset`, `CohereLabs/aya_collection` (10 permissive subsets from `#399`), plus any native-script cleaned Indic instruction packs across all 10 languages (`hi, mr, ta, te, kn, bn, gu, ml, or, pa`) | Human-written / native-reader checked, zero translationese, `ZWJ`/`ZWNJ` intact, 1% romanised ceiling, Odia/Malayalam/Punjabi gap coverage requested |
| 5 | **Math & General Instruction** | 7–10% | ~200k–400k rows (~0.6B tok) | Team 1 | `open-thoughts/OpenThoughts3-1.2M`, `nvidia/OpenMathReasoning`, `open-r1/OpenR1-Math-220k`, `nvidia/Nemotron-Math-v2`, `nvidia/Nemotron-Science-v1`, `databricks/databricks-dolly-15k`, `sft-oasst2` | Verified math answers where applicable; short-response `1k` effort anchors included |
| 6 | **Long Context (8k–32k)** | Included across 1–5 | >= 50k rows in `8k–32k` band | Teams 1 & 2 | Multi-file repo edits (`SWE-rebench`, `commitpackft`), long CoT (`OpenCodeReasoning-2` `16k–32k`), long Indic documents/Q&A | Verified up to `32,768` tokens (`sft/max_sequence_tokens_proposal.md`), no mid-sentence truncation |

---

## 3. RL Prompt Pools Request (Stage 2 — GRPO with Verifiable Rewards)

Every RL prompt pool must exclude all benchmark items (never train on `MATH`, `HumanEval`, `MBPP`, `SWE-bench Verified`, etc.) and keep expected answers/hidden tests strictly inside verifier files.

| # | RL Pool | Target Volume | Target Team | Checker / Verifier | Requested Inputs & Quality Filter |
|---|---|---:|---|---|---|
| 1 | **Code with hidden tests** | 3,500–20,000 tasks | Team 1 | `rl/verifier.py`, `rl-data/stdio_check.py`, `rl/js/`, `rl/jsts/`, `rl/agentic/`, `swe-envs/` | `deepmind/code_contests` non-Codeforces (`3,251` train / `255` held-out already pinned in `#564`, excluding 66 free-reward IDs & 15 `>65,536`-char output IDs), plus verified Python/JS/TS/Go execution tasks and SWE-rebench tasks |
| 2 | **Math with exact checkable answers** | 10,000–40,000 prompts | Team 1 | `rl/math/math_verifier.py` | Commercial-safe, non-benchmark competition math (`agentica-org/DeepScaleR-Preview-Dataset`, `allenai/RLVR-GSM`, `nvidia/OpenMathReasoning` verifiable subset). **Exclude `rl-math-hendrycks` (TSAI 21 Nov ruling).** |
| 3 | **Indic with checkable answers** | 2,000–10,000 prompts across 10 languages | **Team 2** | `rl/indic/indic_verifier.py`, `rl/indic/generate.py` | Human-written templates + Team 2 native-reader sign-off (`team2_reviewer`). Currently **6 templates (`4 hi, 2 ta`) are signed off (`eligibility: train`, `#781`)**; **missing 8 languages (`te, kn, bn, mr, gu, ml, or, pa`)** and families `F2`/`F4`/`F5`. |

---

## 4. Teams 1 & 2 Reply & Gap Tracking (to be filled upon reply)

| Request Area | Partner Team | Status (28 Nov) | Reply / Parquet & `pack_table` Pointer | Identified Gaps |
|---|---|---|---|---|
| SFT Code / Agentic / Tool / Math / Long Context | Team 1 (Data A) | Sent 28 Nov | *Awaiting Team 1 reply* | `OCR-2` shards `0–3` ready via `#565` recipe; full SFT mix parquet staging & long-context share pending |
| SFT Indic (10 languages) | Team 2 (Data B) | Sent 28 Nov | *Awaiting Team 2 reply* | `aya_collection` lacks Odia (`or`) and has low Hindi count; native packs needed across all 10 scripts |
| RL Code & Math pools | Team 1 (Data A) | Sent 28 Nov | *Awaiting Team 1 reply* | Code pool v1 pinned (`#564`, 3,251 train); non-benchmark RL math pool not yet staged (`rl-math-hendrycks` excluded) |
| RL Indic templates & pools | Team 2 (Data B) | Sent 28 Nov | *Awaiting Team 2 reply* | 6 templates (`hi`, `ta`) signed off (`#781`); missing human templates for `te, kn, bn, mr, gu, ml, or, pa` |
