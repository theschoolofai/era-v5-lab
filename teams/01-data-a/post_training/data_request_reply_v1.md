# Team 1 (Data A) reply to Team 10's data request (#882), v1

Team 10's request: `teams/10-post-training/docs/data_request_teams1_2_v1.md` on `saitej123:g10-week5-post-training`
(#882, 72128349). This file answers the Team 1 rows that Sourav took in G1 on 28 Nov: the RL math pool (request §3,
row 2) and the code, tool-calling, math / general and long-context SFT rows (§2, rows 1, 3, 5, 6), plus F2 per file
(§1). The agentic row (§2, row 2) and the RL code pool (§3, row 1) are noted where the numbers touch them. Indic rows
are Team 2's.

Status words, as Team 10 asked: **available** (the data exists at a pinned revision, with its licence and generator
recorded and an F2 rate measured; only the RL math pool is built so far, with its pack_table row; SFT pack_table rows
come when Team 10 picks the subsets), **partial** (usable in part, or a step or a decision is needed first), **not
available**. Every number below comes from a command in
[§7](#7-how-to-reproduce); anything not run is marked "not run".

Two rules, as TSAI answered them in G1 on 28 Nov (08:02 UTC), after Aneesha asked:
- **Licence.** One rule for all data, post-training too: NC, ND and unstated licences are allowed; keep the licence and
  its source on every row, and for post-training data also the generator model and that model's licence terms.
  Every source below has them (recorded per source, not as columns in the data). (Team 10's generator rule, which keeps out text written by closed or Llama models, is a
  separate rule and is applied as their licence table applies it.)
- **Normalisation.** NFC only, never NFKC; ZWJ and ZWNJ are never removed. The RL math pool is built that way.

## 0. Summary

| Request row | Status | What Team 1 can hand over | Rows | p1536 tokens | Licence | Generator | F2 |
|---|---|---|---:|---:|---|---|---|
| RL math (§3 row 2) | **available** (needs its row in Team 10's licence table) | `rl-math-omr-aops-v1`, built from `nvidia/Nemotron-RL-math-OpenMathReasoning` @219bf017 | 109,246 (41,180 with an exact-number answer) | 7,017,379 (prompts) | CC BY 4.0 | none for the problem text (AoPS forum posts); problems refined and answers extracted with Qwen2.5-32B-Instruct (Apache-2.0) | 0 flagged, 0 canary (full set) |
| RL math, more | partial | `nvidia/Nemotron-RL-math-stack_overflow` @81ee8592: 110,976 exact-number rows after the same checks | 436,307 | 39,644,606 (q + a, before filters) | CC BY-SA 4.0 | not named on the card ("similar to" OpenMathReasoning's method) | 606 flagged before filtering |
| RL math, more | partial | `open-r1/OpenR1-Math-220k` default @e4e141ec, the human-curated sources only (`cn_contest`, `inequalities`, `number_theory`, `olympiads_ref`), not MCQ: 4,809 exact-number rows | 93,733 | 9,320,319 (q + a, before filters) | Apache-2.0 | problems: NuminaMath-1.5 (the card names LLM parsing for `olympiads` and translation by an unnamed model); answers from the source | 316 flagged before filtering |
| RL math, others checked | not available | see [§2](#2-other-rl-math-candidates-checked) | | | | | |
| RL code (§3 row 1) | Team 10's own pool | `#564`: 3,251 train / 255 held-out (`rl_data_v1_close.json`) | | | | | Team 10's record |
| SFT code (§2 row 1) | **available**; OpenCodeReasoning-2 partial until its question text is rebuilt (Team 10's #565 recipe) | OpenCodeReasoning-2 (allowed), Nemotron-SFT-OpenCode-v1, OpenCodeInstruct, codeforces-cots, commitpackft | 2,572,641 + 383,000 + 5,000,000 + 40,665 + ≈158,024 | ≈27.5B after F2 (est.; OCR-2 without its questions) | cc-by-4.0 / mit | open models only (table in [§3](#3-sft-rows)) | sample F2: 0% to 47% (codeforces-cots) |
| SFT agentic (§2 row 2) | **available** | SWE-Zero, Nemotron-Cascade-SFT-SWE, Nemotron-Terminal-Corpus, SWE-rebench-openhands | 318,115 + 162,262 + 366,154 + 67,074 | ≈16.5B after F2 (est.) | cc-by-4.0 | Qwen3-Coder-480B, DeepSeek-R1-0528, DeepSeek-V3.2 | sample F2: 0.4% to 20% (SWE-bench Live) |
| SFT tool calling (§2 row 3) | **available** | Nemotron-Agentic-v1 `tool_calling`, Nemotron-SFT-Agentic-v2 `tool_calling`; xlam-60k not sampled (gated: our Hub account has to accept its terms first) | 316,094 + 707,052 | ≈5.4B after F2 (est.) | cc-by-4.0 (+ apache-2.0, mit) | Qwen3 family, gpt-oss-120b, DeepSeek-V3.2, GLM-4.6 | sample F2: 0.4% to 1.0% |
| SFT math / general (§2 row 5) | **available** | OpenThoughts3 (needs a subset: 17.5B tokens), Nemotron-Science-v1, dolly-15k, Nemotron-SFT-Math-v4 problems ([§1.3](#13-overlap-with-the-sft-math-candidates)); oasst2 not sampled | 1,200,000 + 226,334 + 15,011 + 545,431 | ≈18.4B after F2 (est., without SFT-Math-v4) | apache-2.0 / cc-by-4.0 / cc-by-sa-3.0 | QwQ-32B, gpt-oss-120b, none (dolly) | sample F2: 0% to 1.6% |
| SFT long context (§2 row 6) | **available** | rows of 8k to 32k p1536 tokens in the sources above | ≥50,000 asked; OpenThoughts3 ≈1.14M, OpenCodeReasoning-2 ≈1.02M, OpenCode ≈349k, Terminal ≈304k, SWE-Zero ≈225k (after F2, est.) | | | | see [§4](#4-long-context-8k-to-32k-tokens) |

## 1. RL math pool v1: `rl-math-omr-aops-v1`

**Source.** `nvidia/Nemotron-RL-math-OpenMathReasoning`, file `train.jsonl` at revision
`219bf0170cd87cd5db2bbf33715ce9ea43a2c59c` (sha256 `cdcf89ed…1823`, 112,867 lines). Card: "mathematical problems and
solutions sourced from the AoPS forums … Only problems for which an answer was extracted are included"; licence CC BY
4.0, "ready for commercial use". The parent dataset (`nvidia/OpenMathReasoning`, card and arXiv 2504.16891 §2.1) uses
Qwen2.5-32B-Instruct "for all processing steps unless specified otherwise" (problem extraction, classification, answer
extraction); no closed or Llama model is named for problem or answer preparation. The paper's decontamination is
LLM-based and does not name the benchmarks, so we check it ourselves below. The repository's other file,
`validation.jsonl`, is 30 AIME 2024 problems; the builder never reads it.

**Not in Team 10's licence table yet.** The table has the parent `nvidia/OpenMathReasoning` (`TSAI reserves`), not this
RL release. It needs its own licence row before staging.

**Build steps and counts** (`build_rl_math_pool.py`, `summary.json`):

| Step | Rows dropped | Rows left |
|---|---:|---:|
| read | | 112,867 |
| clean (NFC; strip U+200B / U+FEFF / ghost markers; ZWJ/ZWNJ kept): 0 rows changed | 0 | 112,867 |
| exact duplicate (question lowercased, spaces collapsed) | 38 | 112,829 |
| F2, G9 fingerprints v2 full set (`2826a3b8…`), on question + answer | 733 | 112,096 |
| MATH (train, test), MATH-500, GSM8K (train, test), Omni-MATH: equal or one shared 13-word run (Kaggle, [§1.2](#12-math-gsm8k-and-omni-math-check-on-kaggle)) | 860 | 111,236 |
| answer guessable (one letter A-E, yes/no, true/false) | 315 | 110,921 |
| answer longer than the verifier's `MAX_ANSWER_CHARS` (200) | 1,675 | **109,246** |

Of the 109,246: **41,180** answers are read as exact numbers by Team 10's `rl/math/math_verifier.py`
(`parse_number`, unchanged, so the current verifier can score them today) and **68,066** are symbolic (a root, an
expression, an interval), which the verifier would only string-match. Team 10's target is 10,000 to 40,000 prompts, so
the number-answer rows alone cover it; the symbolic rows need a symbolic checker first (not built here).

- Prompt tokens (frozen p1536, `add_special_tokens=False`): 7,017,379 in all; question median 58, p95 130.
- Output: `rl_math_pool_v1.parquet` sha256 `56394b30eb2aff0d2b18d320fe9a88f66f7c55ec1dc67df1e22406dc483e48cd`;
  two runs on the same input gave byte-identical files (parquet, `summary.json`, `pack_table_row.json`).
- **Formal F2 on the built file**: `decontam_check.py` full set, `docs 109246 flagged 0 (0.00%)`;
  `canary_scan.py`: `docs 109246 with_canary 0 hits 0`.
- **pack_table row**: [`pack_table_post_training_v1.json`](pack_table_post_training_v1.json).
- The parquet is not in the repo (data files stay out); the command in [§7](#7-how-to-reproduce) rebuilds it and the
  sha256 checks it.

### 1.1 F2 before filtering (what the checks removed)

`decontam_check.py --max-items 100000` on the whole source (question + answer): 734 of 112,867 flagged (0.65%), 733 of
them unique questions. Nearly all are one shared run, not copies: 708 share less than 10% of the item's runs and 26
share 10% to 50%; none shares more.

| Benchmark | Docs | Distinct items |
|---|---:|---:|
| AIME 2025 | 477 | 13 |
| AIME 2024 | 457 | 11 |
| HLE | 61 | 30 |
| LiveCodeBench | 39 | 32 |
| Codeforces | 33 | 6 |
| MMLU | 12 | 11 |
| G5 held-out v1 | 2 | 1 |

(A doc can hit more than one benchmark.) The AIME hits come from 24 items, so they are probably AIME's stock wording
shared by many AoPS problems; under the formal rule (one shared run) they are removed anyway.

### 1.2 MATH, GSM8K and Omni-MATH check on Kaggle

Fingerprints v2 has no MATH, MATH-500 or Omni-MATH, and TSAI's 21 Nov ruling keeps benchmark data out of training
("MATH is benchmark data … benchmark data never trains the model, reserved or not"). So
[`kaggle_math_overlap.py`](kaggle_math_overlap.py) ran on Kaggle (CPU only, eval firewall: benchmark text never came to
the dev machine) with Team 10's `math500_guard.py` method: exact match of the normalised question, or any shared
13-word run. Benchmarks: `EleutherAI/hendrycks_math` @21a56338 (Team 10's pin; 7,500 train, 5,000 test),
`HuggingFaceH4/MATH-500` @6e4ed1a2, `openai/gsm8k` @740312ad (7,473 train, 1,319 test), `KbsdJames/Omni-MATH` @40ba231d
(4,428). Output: counts and doc_ids only ([`rl_math_pool_v1_drop_list.json`](rl_math_pool_v1_drop_list.json)).

Rows flagged (exact / shared run / either), per candidate:

| Candidate | Rows | MATH train | MATH test | MATH-500 | GSM8K train | GSM8K test | Omni-MATH | Any |
|---|---:|---|---|---|---|---|---|---:|
| Nemotron-RL-math-OpenMathReasoning | 112,867 | 100 / 743 / 744 | 8 / 98 / 100 | 0 / 6 / 6 | 0 | 0 | 15 / 268 / 269 | 1,072 |
| Nemotron-RL-math-stack_overflow | 436,307 | 29 / 289 / 292 | 0 / 136 / 136 | 0 / 8 / 8 | 0 / 1 / 1 | 0 | 0 / 15 / 15 | 398 |
| Nemotron-RL-Math-v2 | 7,732 | 0 / 8 / 8 | 0 | 0 | 0 | 0 | 0 / 20 / 20 | 28 |
| DeepMath-103K | 103,022 | **5,529** / 5,162 / 5,859 | **2,909** / 2,947 / 3,307 | 0 / 63 / 63 | 0 | 0 | 0 / 34 / 34 | 8,529 |
| OpenR1-Math-220k (default) | 93,733 | 177 / 957 / 962 | 3 / 96 / 99 | 0 / 11 / 11 | 0 / 2 / 2 | 0 | 2 / 300 / 302 | 1,344 |
| Nemotron-SFT-Math-v4 (problems) | 545,431 | 78 / 489 / 489 | 0 / 122 / 122 | 0 / 10 / 10 | 0 | 0 | 20 / 227 / 227 | 768 |

GSM8K shows almost nothing in any candidate. MATH appears in all of them, as expected for AoPS-derived sets (AoPS
hosts the same contest problems).

### 1.3 Overlap with the SFT math candidates

Exact (normalised) question matches between the built pool and the SFT math sets Team 10 lists: 8,526 of the 109,246
rows (1,882 of the 41,180 number-answer rows) are also problems in `nvidia/Nemotron-SFT-Math-v4`; 126 in OpenR1-Math,
27 in DeepMath. If Team 10 runs SFT on Nemotron-SFT-Math-v4, it may want to drop those 8,526 from RL (RL on problems
seen in SFT teaches less). The doc_ids can be listed on request; this is a lower bound (exact text only).

## 2. Other RL math candidates checked

| Candidate (revision) | Status | Why |
|---|---|---|
| `nvidia/Nemotron-RL-math-stack_overflow` @81ee8592 | partial | 436,307 rows, 110,976 exact-number answers after duplicates, F2 and the Kaggle check. CC BY-SA 4.0 (share-alike). The card does not name the model that extracted the problems and answers. Not in Team 10's table. |
| `open-r1/OpenR1-Math-220k` default @e4e141ec | partial | 93,733 rows from NuminaMath-1.5 problems. Its card says `cn_contest`, `inequalities` and `number_theory` are "manually curated … provided by our data partners" and `olympiads_ref` was parsed by hand; those give 4,809 exact-number rows (not MCQ). The `olympiads` part (68,089 rows) was parsed "using generic regular expressions and LLMs" (model not named); `amc_aime` (3,403) is contest text close to the AIME benchmarks. |
| `nvidia/Nemotron-RL-Math-v2` @804418c1 | not available | 7,732 rows; 3,984 are masked DAPO-Math / Skywork-OR1 placeholders (both `excluded` in Team 10's table); the rest mix AoPS, Math StackExchange and "vendor-purchased data" with no per-row source; "All problems and expected answers are verified for correctness using GPT-5.2". |
| `zwhe99/DeepMath-103K` @5cf055d1 | not available | Team 10's table has `TSAI reserves`. Two things found: (1) the Kaggle check finds **2,909 exact copies of MATH test problems** and 5,529 of MATH train ([§1.2](#12-math-gsm8k-and-omni-math-check-on-kaggle)); (2) the paper (arXiv 2504.11456, §3 Stage 4) says "Questions phrased conversationally were rewritten into a standardized format", with "GPT-4o to process the raw questions", so part of the question text is closed-model output, and there is no source column to drop it. F2 also flags 67 near-copies of MMLU items (coverage ≥ 0.5). |
| `nvidia/Nemotron-Cascade-RL-Math` @fcd07b14 | not available | 14,476 rows; by the card: 11,217 NuminaMath-CoT, 1,578 DeepScaleR, 1,257 AceReason-Math (all `excluded` in Team 10's table), 424 OpenMathReasoning. |
| `allenai/Dolci-RL-Zero-Math-7B` @93b5e498 | not available | DAPO-Math (excluded) and Klear-Reasoner math; ODC-BY. |
| `allenai/RLVR-GSM` @b1488451 | not available, I think | GSM8K train (7,473) and test (1,319). Team 10's table says `TSAI reserves`; GSM8K test is in fingerprints v2, and TSAI's 21 Nov MATH ruling ("benchmark data never trains the model") seems to cover the GSM8K train split too. For Team 10 to confirm. |
| `EleutherAI/hendrycks_math` (MATH train) | not available | TSAI, 21 Nov. |
| `KbsdJames/Omni-MATH` @40ba231d | not available | Released only as a benchmark (4,428 rows, one `test` split); Team 10's table: `needs TSAI decision`. |
| DeepScaleR, DAPO-Math-17k, Big-Math-RL-Verified, AceReason-Math, Skywork-OR1 math, Polaris | not available | `excluded` in Team 10's table (unknown, closed or Llama generators, or excluded sources). Team 10's request names DeepScaleR and RLVR-GSM in the RL math row; both are covered above. |

## 3. SFT rows

What was measured, per source: the revision (pinned); rows, with where the count comes from (parquet footers at the
revision, the card, or the dataset viewer; "≈" = file bytes divided by the mean bytes of the sampled rows, used only
where none of those has a count); the licence tag; and a sample of up to 500 rows (250 for SWE-rebench-openhands, one
row group) drawn with seed 0 from random row groups or random byte windows (`tools/sample_sft.py`). Tokens are frozen
p1536 over every message, the reasoning, tool-call arguments and the tool schemas, without ChatML special tokens (a
few per turn). F2 is `decontam_check.py`, full set, on the sample; it is a rate, not the formal check, which must run
on whatever is staged. "Tokens after F2" = rows × (tokens of the sample rows F2 keeps ÷ rows in the sample).
Generators and decisions are copied from Team 10's licence table (not re-read here); every source below already has
a row there.

**Code (request row 1)**

| Source @revision | Rows (source of the count) | Licence (Hub tag) | Generator (Team 10 table) | Team 10 decision | Mean / p50 / p90 tokens | F2 flagged (sample) | Tokens after F2 (est.) |
|---|---:|---|---|---|---|---:|---:|
| nvidia/OpenCodeReasoning-2 (python + cpp) @eadf5359 | 2,572,641 (parquet footers) | cc-by-4.0 | DeepSeek-R1 (MIT) solutions, QwQ-32B (Apache-2.0) critiques | allowed (TSAI 11 Nov) | 7,360 / 6,790 / 14,284 | 3.2% | 18.36B |
| nvidia/OpenCodeInstruct @8f3ba5ba | 5,000,000 (parquet footers) | cc-by-4.0 | Qwen2.5-32B-Instruct + Qwen2.5-Coder-32B-Instruct (Apache-2.0) | TSAI reserves | 420 / 374 / 642 | 2.8% | 2.04B |
| nvidia/Nemotron-SFT-OpenCode-v1 @556d5237 | 383,000 (card, 5 of 6 subsets (question_tool 76K not sampled)) | cc-by-4.0 | gpt-oss-120b + Qwen3-Coder-480B-A35B-Instruct (Apache-2.0) | TSAI reserves | 17,700 / 15,283 / 29,796 | 0.4% | 6.75B |
| open-r1/codeforces-cots `solutions_decontaminated` @39ac85c1 | 40,665 (parquet footers) | cc-by-4.0 | DeepSeek-R1 (MIT) | TSAI reserves | 13,534 / 14,132 / 22,374 | 47.2% | 0.27B |
| bigcode/commitpackft (py, js, ts, java, c++, go, rust) @fc56fe33 | ≈158,024 (bytes / sampled row bytes) | mit | none (human commits) | TSAI reserves | 404 / 409 / 643 | 0.0% | 0.06B |
| nvidia/Nemotron-SFT-Competitive-Programming-v2 @778afc98 | 844,935 (card) | cc-by-4.0, odc-by, mit | not named on the card | excluded (generator not named) | 47,807 / 47,322 / 94,796 | 44.4% | 19.58B |

**Agentic: SWE and terminal (row 2)**

| Source @revision | Rows (source of the count) | Licence (Hub tag) | Generator (Team 10 table) | Team 10 decision | Mean / p50 / p90 tokens | F2 flagged (sample) | Tokens after F2 (est.) |
|---|---:|---|---|---|---|---:|---:|
| nvidia/SWE-Zero-openhands-trajectories @7b3cd106 | 318,115 (viewer) | cc-by-4.0 | Qwen3-Coder-480B-A35B-Instruct (Apache-2.0) | TSAI reserves | 26,574 / 24,914 / 40,836 | 8.8% | 7.64B |
| nvidia/Nemotron-Cascade-SFT-SWE @b4ef73ff | 162,262 (viewer) | cc-by-4.0 | DeepSeek-R1-0528 (MIT) | TSAI reserves | 7,730 / 6,439 / 15,007 | 7.8% | 1.14B |
| nebius/SWE-rebench-openhands-trajectories @35455389 | 67,074 (viewer) | cc-by-4.0 | Qwen3-Coder-480B-A35B-Instruct (Apache-2.0) | TSAI reserves | 58,100 / 55,631 / 82,652 | 20.4% | 3.00B |
| nvidia/Nemotron-Terminal-Corpus @67a3e039 | 366,154 (parquet footers) | cc-by-4.0 | DeepSeek-V3.2 (MIT) | TSAI reserves | 12,885 / 12,147 / 18,965 | 0.4% | 4.69B |

**Tool calling (row 3)**

| Source @revision | Rows (source of the count) | Licence (Hub tag) | Generator (Team 10 table) | Team 10 decision | Mean / p50 / p90 tokens | F2 flagged (sample) | Tokens after F2 (est.) |
|---|---:|---|---|---|---|---:|---:|
| nvidia/Nemotron-Agentic-v1 `tool_calling` @650d5909 | 316,094 (card) | cc-by-4.0 | Qwen3-235B-A22B / Qwen3-32B (Apache-2.0), gpt-oss-120b | TSAI reserves | 3,781 / 3,336 / 7,398 | 1.0% | 1.18B |
| nvidia/Nemotron-SFT-Agentic-v2 `tool_calling` @7c804833 | 707,052 (card) | cc-by-4.0, apache-2.0, mit | DeepSeek-V3.2 (MIT), GLM-4.6 (MIT) | TSAI reserves | 5,980 / 3,049 / 13,457 | 0.4% | 4.21B |
| nvidia/Nemotron-Agentic-v1 `interactive_agent` @650d5909 | 19,028 (card) | cc-by-4.0 | as above | TSAI reserves | 5,847 / 4,808 / 10,636 | 0.0% | 0.11B |

**Math and general (row 5)**

| Source @revision | Rows (source of the count) | Licence (Hub tag) | Generator (Team 10 table) | Team 10 decision | Mean / p50 / p90 tokens | F2 flagged (sample) | Tokens after F2 (est.) |
|---|---:|---|---|---|---|---:|---:|
| open-thoughts/OpenThoughts3-1.2M @61bcf9d4 | 1,200,000 (viewer) | apache-2.0 | QwQ-32B (Apache-2.0) | TSAI reserves | 14,848 / 15,926 / 16,817 | 1.6% | 17.53B |
| nvidia/Nemotron-Science-v1 (RQA + MCQ) @82e1af46 | 226,334 (viewer) | cc-by-4.0 | gpt-oss-120b (Apache-2.0) | TSAI reserves | 3,694 / 1,847 / 9,037 | 0.0% | 0.84B |
| databricks/databricks-dolly-15k @bdd27f4d | 15,011 (viewer) | cc-by-sa-3.0 | none (human) | allowed (CC-BY-SA) | 174 / 105 / 382 | 0.0% | 0.00B |


Notes:
- **OpenCodeReasoning-2 ships without question text**: all 500 sampled rows have `question` = `-`; the questions come
  from TACO, APPS, code_contests and open-r1/codeforces (Team 10's #565 recipe rebuilds them). Its tokens above are the
  R1 generations only, and its F2 rate will rise once the questions are in: 204 of the 500 rows are Codeforces
  problems, and codeforces-cots, which has the questions, loses 47.2% (Codeforces 220, LiveCodeBench 125 of 500).
  Status: partial until the rebuild.
- **The agentic trajectories lose most to SWE-bench Live** (SWE-rebench-openhands 47 of 250 sampled, SWE-Zero 41 of
  500, Cascade-SFT-SWE 35 of 500).
- Nemotron-SFT-Competitive-Programming-v2 is `excluded` in Team 10's table (generator not named) and is listed only
  for its sizes.
- Rows of the target size: Team 10 asks for 400k to 600k code rows, 100k to 250k agentic trajectories, 150k to 300k
  tool-calling dialogues and 200k to 400k math / general rows. Every row has more than that in candidates; the
  choice of subset (and the 32,768-token cap) is Team 10's.

## 4. Long context (8k to 32k tokens)

Team 10 asks for at least 50,000 rows of 8,192 to 32,768 tokens. Measured share of each sample in that band, and the
rows it implies after F2 (rows × share of the sample that is both in the band and kept by F2):

| Source | Share of sample in 8k-32k | Over 32k | Rows in band after F2 (est.) |
|---|---:|---:|---:|
| open-thoughts/OpenThoughts3-1.2M | 96.4% | 0.0% | 1,137,600 |
| nvidia/OpenCodeReasoning-2 (python + cpp) | 40.8% | 0.0% | 1,023,911 |
| nvidia/Nemotron-SFT-OpenCode-v1 | 91.6% | 6.0% | 349,296 |
| nvidia/Nemotron-Terminal-Corpus | 83.4% | 0.6% | 303,908 |
| nvidia/SWE-Zero-openhands-trajectories | 76.6% | 23.4% | 224,589 |
| nvidia/Nemotron-SFT-Agentic-v2 `tool_calling` | 13.8% | 2.8% | 96,159 |
| nvidia/Nemotron-SFT-Competitive-Programming-v2 | 16.6% | 64.8% | 62,525 |
| nvidia/Nemotron-Cascade-SFT-SWE | 34.8% | 0.2% | 49,328 |
| nvidia/Nemotron-Agentic-v1 `tool_calling` | 7.8% | 0.0% | 24,655 |
| nvidia/Nemotron-Science-v1 (RQA + MCQ) | 10.0% | 1.0% | 22,633 |
| open-r1/codeforces-cots `solutions_decontaminated` | 73.2% | 0.0% | 14,233 |
| nvidia/Nemotron-Agentic-v1 `interactive_agent` | 18.6% | 0.0% | 3,539 |

So the band is well covered; the long-CoT and agentic sources give most of it (OpenCodeReasoning-2's count is before its questions are added back, which makes its rows longer). SWE-rebench-openhands is almost all
over 32k (99.2% of its sample), so it does not help this band without cutting.

## 5. The 38 packs

The 38 packs are pre-training text (code, code-adjacent, English web, math web, science PDFs, Indic). None of them is
instruction, chat or RL data, so none answers a Team 10 row as it stands.

## 6. Differences from Team 10's request and licence table (findings, for Team 10 to check)

1. `nvidia/Nemotron-RL-math-OpenMathReasoning` (the source of pool v1) and `nvidia/Nemotron-RL-math-stack_overflow` are
   not in the licence table; each needs a row.
2. DeepMath-103K (`TSAI reserves`, "use") holds 2,909 exact MATH test problems and GPT-4o-rewritten questions
   ([§2](#2-other-rl-math-candidates-checked)).
3. The RL math row of the request names DeepScaleR (`excluded` in the table) and RLVR-GSM (GSM8K).
4. `nvidia/Nemotron-RL-math-OpenMathReasoning`'s `validation.jsonl` is AIME 2024; any tool that loads the repository
   whole would pull benchmark items onto the machine.
5. Fingerprints v2 has no MATH, MATH-500 or Omni-MATH; pools built from AoPS need the extra check in §1.2 (Team 10's
   `math500_guard.py` does the MATH-500 part for MATH train).

## 7. How to reproduce

From the repo root, with the lab venv (`.venv/bin/python`; pyarrow, tokenizers, huggingface_hub). Data goes to
`~/Workspace/era-v5-data/g1-pt/` (outside the repo). The frozen p1536 tokenizer is checked by sha256 in every script.

```bash
P=teams/01-data-a/post_training; T=$P/tools; D=teams/09-evaluation/decontam
# pin revisions, licence tags, file sizes and viewer row counts; save the cards
python $T/hub_info.py <cards_dir> nvidia/Nemotron-RL-math-OpenMathReasoning nvidia/Nemotron-RL-math-stack_overflow ...
# fetch the RL math candidates at their pinned revisions (train files only; big parquet sets by column)
python $T/fetch_math.py omr_rl so_rl rlmath_v2 deepmath openr1 sftmath_v4
# docs.parquet + stats.json per candidate (rows, duplicates, cleaning-contract counts, p1536 tokens)
python -I $T/prepare_pool.py omr_rl so_rl rlmath_v2 deepmath openr1 sftmath_v4
# F2 (formal tool, full set) and canary scan, per candidate; then the per-benchmark profile
python -s $D/decontam_check.py <pool>/docs.parquet --max-items 100000 > <pool>/f2_flagged.jsonl
python -s $D/canary_scan.py <pool>/docs.parquet
python -I $T/f2_profile.py <pool>/f2_flagged.jsonl
# answer types with Team 10's math_verifier.py, and exact overlap between candidates
python -I $T/answer_types.py teams/10-post-training/rl/math/math_verifier.py omr_rl so_rl rlmath_v2 deepmath openr1
python -I $T/overlap.py omr_rl so_rl rlmath_v2 deepmath openr1 sftmath_v4
# MATH / MATH-500 / GSM8K / Omni-MATH check: on Kaggle only (CPU kernel, internet on), never on the dev machine
#   kaggle kernels push -p <folder with kaggle_math_overlap.py and its kernel-metadata.json>
# build the RL math pool (twice: the files must be byte-identical), then the formal F2 on the built file
python -s $P/build_rl_math_pool.py --jsonl <train.jsonl> --drop-list $P/rl_math_pool_v1_drop_list.json --out <out>
python -s $P/build_rl_math_pool.py --jsonl <train.jsonl> --drop-list $P/rl_math_pool_v1_drop_list.json --out <out2>
# SFT samples (500 rows each, seed 0), then F2 and canary on each sample
python -I $T/sample_sft.py ocr2 cf_cots oci opencode compprog_v2 commitpackft agentic_v1_tool agentic_v1_inter \
    agentic_v2_tool ot3 science_v1 dolly swe_rebench_oh cascade_swe swe_zero terminal
# tests of the builder
python -m pytest $P/tests -q
```

Without `--jsonl`, `build_rl_math_pool.py` downloads `train.jsonl` at the pinned revision itself and checks its
sha256. The parquet is not committed; its sha256 is in `pack_table_post_training_v1.json`.
