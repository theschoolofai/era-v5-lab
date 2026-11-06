# SFT decontamination report

Run for G10 on 2026-11-05. Every set was checked against Team 9's benchmark fingerprints **v2** with the **full set** (no `--benchmarks`, `--tags` or `--exclude`), and scanned for canaries.

- **set_sha256:** `2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a`
- **Tools:** `teams/09-evaluation/decontam/decontam_check.py` and `canary_scan.py`, lab main `c6b0ce0961028020b3e3eaf86fe0c5873fca3bc0`. sha256 of the files used:
  - `canary_scan.py`: `322066d675e13af8bee0d05602f755f49e33da5a148bf664306ce6d6a9f908c2`
  - `decontam_check.py`: `62a269a25123543b5470c4956ba1be530ea257c597bc2be2eab19201cb62df8f`
  - `fpset.py`: `7f5f48d08506d619ebfadd2742e86d29ec3ea28e5fcfd729f13cd8d959689c59`
  - `lab_canary.py`: `373536a777c9f16367cf6affcc2cc6243755ac23e75850a2624eadf65918ea09`
  - `normalize.py`: `570dcb820ac2ae6c667b1abc5ea1d781a6795aa42a7735aa94377e756d7d70e9`
- **Runner and reconciliation:** `sft/decontam_run.py`; this file is written by `sft/decontam_report.py`.
- **Sets run:** 3. **Rows in:** 2,414. **Removed (flagged or canary):** 567 (23.49%). **Kept:** 1,847.
- No benchmark item text is in this file or in the run records: only set names, counts, document ids, benchmark item ids, offsets and sha256 values.

## 1. Result per set

| Set | Rows in | Flagged | Canary | Removed | Rows kept | Clean file sha256 |
|---|---:|---:|---:|---:|---:|---|
| `sft-code-codeforces-cots` | 972 | 496 | 0 | 496 (51.03%) | 476 | `ff74435ced50…` |
| `sft-code-swe-rebench-openhands` | 442 | 71 | 0 | 71 (16.06%) | 371 | `2a16677599f0…` |
| `sft-indic-aya-dataset` | 1,000 | 0 | 0 | 0 (0.00%) | 1,000 | `df0c80c61c55…` |
| **Total** | **2,414** | **567** | **0** | **567** (23.49%) | **1,847** | |

A row that is both flagged and carries a canary counts once in Removed.

## 2. Flagged documents by benchmark

| Set | `codeforces` | `hle` | `livecodebench` | `swe_bench_live` | `swe_bench_verified` |
|---|---:|---:|---:|---:|---:|
| `sft-code-codeforces-cots` | 451 | 40 | 281 | 0 | 0 |
| `sft-code-swe-rebench-openhands` | 0 | 0 | 0 | 64 | 17 |
| `sft-indic-aya-dataset` | 0 | 0 | 0 | 0 | 0 |

A document is flagged when it shares at least one 13-word run (20 tokens for code) with a benchmark item. The whole document is removed. The count is documents per benchmark, so a document that matches two benchmarks counts in both columns.

## 3. Flagged documents by coverage

Coverage is the share of one benchmark item's runs that the document contains (the highest over its hits). The bands are for reading the result; every flagged document is removed whatever its band.

| Set | Flagged | Coverage 0.5 or more | 0.1 to 0.5 | Below 0.1 |
|---|---:|---:|---:|---:|
| `sft-code-codeforces-cots` | 496 | 0 | 32 | 464 |
| `sft-code-swe-rebench-openhands` | 71 | 2 | 4 | 65 |
| `sft-indic-aya-dataset` | 0 | 0 | 0 | 0 |

## 4. Benchmark items with the largest overlap

**`sft-code-codeforces-cots`**: at least 191 different benchmark items found in 496 documents (top 15 by coverage; the checker lists the best 5 items per document, so this is a lower bound)

| Benchmark item | Documents | Highest coverage | Shared runs / item runs | Example document | Offset |
|---|---:|---:|---:|---|---:|
| `codeforces:test:2018/B` | 102 | 0.152 | 32 / 210 | `sft-code-codeforces-cots/190` | 1226 |
| `codeforces:test:2060/D` | 50 | 0.150 | 32 / 214 | `sft-code-codeforces-cots/190` | 1226 |
| `codeforces:test:2056/D` | 54 | 0.136 | 37 / 273 | `sft-code-codeforces-cots/190` | 1226 |
| `codeforces:test:2010/A` | 64 | 0.113 | 12 / 106 | `sft-code-codeforces-cots/775` | 1245 |
| `codeforces:test:2065/C1` | 30 | 0.107 | 33 / 307 | `sft-code-codeforces-cots/265` | 1455 |
| `codeforces:test:2013/E` | 5 | 0.106 | 27 / 254 | `sft-code-codeforces-cots/785` | 1345 |
| `codeforces:test:2049/B` | 4 | 0.105 | 33 / 313 | `sft-code-codeforces-cots/320` | 1495 |
| `codeforces:test:2018/D` | 23 | 0.104 | 34 / 328 | `sft-code-codeforces-cots/190` | 1226 |
| `codeforces:test:2018/C` | 10 | 0.103 | 28 / 271 | `sft-code-codeforces-cots/785` | 1345 |
| `codeforces:test:2065/C2` | 20 | 0.101 | 33 / 326 | `sft-code-codeforces-cots/265` | 1455 |
| `codeforces:test:2019/A` | 24 | 0.099 | 28 / 284 | `sft-code-codeforces-cots/190` | 1226 |
| `codeforces:test:2038/B` | 116 | 0.096 | 17 / 178 | `sft-code-codeforces-cots/135` | 2131 |
| `codeforces:test:2022/B` | 10 | 0.085 | 22 / 259 | `sft-code-codeforces-cots/495` | 2212 |
| `codeforces:test:1993/B` | 59 | 0.084 | 23 / 274 | `sft-code-codeforces-cots/670` | 1763 |
| `codeforces:test:2031/B` | 4 | 0.082 | 34 / 417 | `sft-code-codeforces-cots/320` | 1495 |

**`sft-code-swe-rebench-openhands`**: at least 49 different benchmark items found in 71 documents (top 15 by coverage; the checker lists the best 5 items per document, so this is a lower bound)

| Benchmark item | Documents | Highest coverage | Shared runs / item runs | Example document | Offset |
|---|---:|---:|---:|---|---:|
| `swe_bench_live:test:streamlink__streamlink-6242` | 1 | 0.924 | 171 / 185 | `sft-code-swe-rebench-openhands/92` | 27523 |
| `swe_bench_live:test:beeware__briefcase-1638` | 1 | 0.920 | 103 / 112 | `sft-code-swe-rebench-openhands/257` | 27514 |
| `swe_bench_live:test:streamlink__streamlink-6353` | 1 | 0.326 | 112 / 344 | `sft-code-swe-rebench-openhands/92` | 27609 |
| `swe_bench_live:test:streamlink__streamlink-6389` | 1 | 0.316 | 112 / 354 | `sft-code-swe-rebench-openhands/92` | 27609 |
| `swe_bench_live:test:streamlink__streamlink-5858` | 1 | 0.304 | 80 / 263 | `sft-code-swe-rebench-openhands/92` | 27609 |
| `swe_bench_live:test:streamlink__streamlink-6420` | 1 | 0.304 | 112 / 369 | `sft-code-swe-rebench-openhands/92` | 27609 |
| `swe_bench_live:test:python-pillow__Pillow-9105` | 2 | 0.192 | 68 / 354 | `sft-code-swe-rebench-openhands/487` | 27590 |
| `swe_bench_live:test:joke2k__faker-2155` | 1 | 0.164 | 69 / 422 | `sft-code-swe-rebench-openhands/310` | 27505 |
| `swe_bench_live:test:beeware__briefcase-1598` | 2 | 0.117 | 109 / 928 | `sft-code-swe-rebench-openhands/257` | 129123 |
| `swe_bench_live:test:encode__starlette-2711` | 1 | 0.114 | 28 / 246 | `sft-code-swe-rebench-openhands/183` | 30233 |
| `swe_bench_live:test:deepset-ai__haystack-8969` | 1 | 0.076 | 10 / 131 | `sft-code-swe-rebench-openhands/581` | 31001 |
| `swe_bench_live:test:encode__starlette-2812` | 1 | 0.075 | 28 / 372 | `sft-code-swe-rebench-openhands/183` | 30233 |
| `swe_bench_verified:test:django__django-14238` | 11 | 0.072 | 28 / 389 | `sft-code-swe-rebench-openhands/257` | 41676 |
| `swe_bench_live:test:deepset-ai__haystack-7681` | 1 | 0.048 | 10 / 209 | `sft-code-swe-rebench-openhands/581` | 31001 |
| `swe_bench_live:test:deepset-ai__haystack-9227` | 1 | 0.043 | 7 / 161 | `sft-code-swe-rebench-openhands/581` | 31022 |

Coverage is the share of the item's runs found in the document. A value near 1.0 is a full copy; a low value is a short shared passage, for example a common problem statement. The ids above are enough to find the document in the set; the item text stays in Team 9's restricted folder.

## 5. Checks

| Check | Sets passed |
|---|---:|
| `canary_ids_in_input` | 3 of 3 |
| `canary_scan_complete` | 3 of 3 |
| `clean_file_flags_0` | 3 of 3 |
| `docs_match_checker` | 3 of 3 |
| `flagged_count_matches` | 3 of 3 |
| `flagged_ids_in_input` | 3 of 3 |
| `ids_unique` | 3 of 3 |
| `rows_in_eq_kept_plus_removed` | 3 of 3 |

`rows_in_eq_kept_plus_removed`: rows in = rows kept + rows removed. `clean_file_flags_0`: the checker, run again on the clean file, flags 0 of the kept rows. `canary_scan_complete`: `canary_scan.py` read every file (exit 0 or 1). A set with a failed check or a canary is not in this report (the script stops).

## 6. Inputs (to reproduce a run)

| Set | Input file | Bytes | sha256 |
|---|---|---:|---|
| `sft-code-codeforces-cots` | `codeforces-cots.jsonl` | 38,519,683 | `349852407044cdf8bb9548ffb38ee179a0e1191b069504493d655d4229f7e2a2` |
| `sft-code-swe-rebench-openhands` | `swe-rebench-openhands.jsonl` | 104,052,372 | `b6cf83e02e5cb7bac12f3c97cbb9aad86d452fe6abb949eed4c3d55938a8b93f` |
| `sft-indic-aya-dataset` | `aya-dataset.jsonl` | 2,339,073 | `df0c80c61c55ea71fcfa5ef2f99067715989eda0aee504428623995241e7d768` |

```
python teams/10-post-training/sft/decontam_run.py --set <set-id> --input <set>.jsonl --out-dir decontam_out
python teams/10-post-training/sft/decontam_report.py --records decontam_out --out teams/10-post-training/sft/decontam_report.md --sets <set-id> ...
```

## 7. Sets not run yet

| Set | Why |
|---|---|
| `sft-agentic-nemotron-agentic-v1` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-agentic-nemotron-sft-agentic-v2-tool-calling` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-bespoke-stratos-17k` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-chat-nemotron-if-v1` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-chat-nemotron-if-v2` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-code-codeforces-cots (rows after 1,000)` | only the first 1,000 rows of the split were run |
| `sft-code-commitpackft` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-code-nemotron-cascade-swe` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-code-nemotron-terminal` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-code-opencodereasoning` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-code-opencodereasoning-2` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-code-self-oss-instruct` | `excluded` (StarCoder2 generator, TSAI 3 Nov); not run |
| `sft-code-swe-rebench-openhands (rows after 1,000)` | only the first 1,000 rows of the split were run |
| `sft-dolly-15k` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-indic-aya-collection` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-indic-aya-dataset (rows after the first 1,000 Indic rows)` | only the first 1,000 Indic rows were run |
| `sft-math-nemotron-math-v2` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-math-nemotron-proofs` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-math-openr1-math` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-oasst2` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-rl-math-openmathreasoning` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-safety-aegis-v1` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-safety-indicguard` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-safety-nemotron-guard-v3` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-safety-nemotron-sft-v2` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-safety-wildjailbreak` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-salesforce-xlam-60k` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-science-glm51-phd` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-science-nemotron-science` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-science-nemotron-science-v2` | no `convert.py` adapter yet (T-081); not downloaded |
| `sft-stem-code-openthoughts3` | no `convert.py` adapter yet (T-081); not downloaded |

## 8. What this check does not cover

- **Benchmarks outside the set.** This fingerprint set holds 20 benchmark entries: `aime_2024`, `aime_2025`, `bfcl_v3`, `codeforces`, `flores200`, `gaia`, `gpqa_diamond`, `gsm8k`, `heldout_g5_v1`, `hle`, `in22_conv`, `in22_gen`, `livecodebench`, `longbench_v2`, `milu`, `mmlu`, `swe_bench_live`, `swe_bench_pro`, `swe_bench_verified`, `terminal_bench_2`.
  It has no entry for HumanEval, HumanEval+, MBPP, MBPP+, ARC-Challenge, ARC-Easy, HellaSwag, TruthfulQA, MMLU-Pro, BBH, MuSR, Belebele, which Team 9's harnesses run (eval firewall, section 5, known gap), so a clean result says nothing about them.
  `sft_mix_proposal.md` section 1 lists HumanEval+ and MBPP+ among the benchmarks of this check; this set does not contain them.
- **Paraphrase.** The check finds copied runs of words. A reworded or translated item is not found.
- **Other rows of a set.** Only the rows that were run are covered. A set that was sampled (for example the first rows of a split) is not cleared as a whole.
- **Frozen tokenizer.** The check reads the rendered `text`, so it does not depend on the tokenizer. The effort tiers of the rows do, and Team 3 freezes the tokenizer on Sat 14 Nov.
- **A rerun is needed** when Team 9 publishes a new fingerprint set (a different set_sha256), and for any set whose rows change.

