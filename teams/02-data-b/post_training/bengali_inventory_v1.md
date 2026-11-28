# Bengali post-training data: inventory v1 (Data B Lab 5 task 8 / Team 10 #882, Bengali line)

By sourav-dhar, 29 Nov 2026. Same layout as the Hindi line (`hindi_inventory_v1.md`, #938).

Facts checked on 28–29 Nov 2026 from the dataset cards and the HF API at the revisions given, the upstream papers,
and our own counts (method in each row). Open items are in section 5. Request:
`teams/10-post-training/docs/data_request_teams1_2_v1.md` (SFT row 4, RL row 3).

Rules applied (from the request and TSAI, 28 Nov):
- NC, ND and unstated licences are allowed, but every source records its licence and where it was found.
- If a model made the data, record the generator model and that model's licence terms.
- RL training text is written by people, never by a model (TSAI, 3 Nov). Model text is eval-only.
- No benchmark items as training data.
- Native script, ZWJ/ZWNJ kept, NFC (never NFKC), 1% romanised ceiling.

Row-count methods: **footer** = parquet footer `num_rows`; **col-scan** = read only the needed columns and count the
Bengali rows; **local** = file downloaded and counted; **viewer** = datasets-server `/size` (partial = false);
**card** = the dataset card only.

## 0. Summary

- **Native, human-written Bengali SFT data is small.** `aya_dataset` has 1,534 Bengali rows (about 0.4M p1536
  tokens). With the templated news rows of `aya_collection` (19,096) and MultiNativQA's train split (13,909, NC-SA),
  the human-made Bengali total is about 34.5k rows and about 3.1M tokens (estimates from 300-row samples, section 3).
  Everything larger is translated or written by a model.
- **Two `aya_collection` subsets that Team 10's SFT v1 already reads are benchmark items.**
  `templated_indic_sentiment` (Bengali) holds every IndicSentiment validation and test item: all 1,156 English
  reviews verbatim, and all 1,156 Bengali reviews (1,110 verbatim, the other 46 with only their quote marks dropped).
  On the English side the same holds in all 10 languages of the subset. `templated_indic_paraphrase` (Bengali) holds
  1,997 of IndicXParaphrase's 2,990 distinct Bengali sentences. Team 10's `sft/convert.py` reads both subsets and
  `sft/results/sft_v1_hf_pins.json` pins the same two files (section 4).
- **RL: no Bengali template exists yet.** Families F1, F2 and F4 list Bengali as a starting language; all must be
  written by a Bengali speaker and checked by a second Team 2 reader. Human-written Bengali problems with exact answers
  exist only at olympiad level (section 2).

## 1. SFT (instruction data), Bengali

| # | Source | Bengali rows | Written by | Generator model | Licence (where found) | Status for us | Revision · count method |
|---|---|---:|---|---|---|---|---|
| 1 | `CohereLabs/aya_dataset` (`language_code` `ben`) | 1,534 (750 original annotations, 784 re-annotations) | human annotators; the card calls re-annotations "human edits of automatically generated prompts and completions" | none | apache-2.0 (HF tag, card) | **Already in licence table** (`sft-indic-aya-dataset`). Cleanest source, small. The same rows appear in aya_collection as "Aya-Dataset": do not count twice. | `f9ea04583f` · col-scan |
| 2 | `CohereLabs/aya_collection` `templated_bengali_news` | 19,096 | human news text, templates by fluent speakers | none | apache-2.0 tag; upstream CC0-1.0 per #399 (`teams/12-quantization/docs/aya_licence_check.md`) | **Already in licence table** (`sft-indic-aya-collection`). Short headline / summary tasks. 107 of 300 sampled answers start with the template phrase "সাংবাদটির শিরোনাম হল(ো)", which reads as a misspelling of সংবাদ: strip or fix the prefix before use. | `09069079fa` · footer + col-scan |
| 3 | `aya_collection` `templated_indic_sentiment` (`ben`) | 1,156 | IndicSentiment items, templated as English-to-Bengali translation | none | MIT per #399 | **Exclude: benchmark** (section 4). Today in `sft-indic-aya-collection` (TSAI reserves) and read by Team 10's `sft/convert.py`. | `09069079fa` · col-scan |
| 4 | `aya_collection` `templated_indic_paraphrase` (`ben`) | 1,001 | IndicXParaphrase items (a test-only set), templated | none | MIT per #399 | **Exclude: benchmark** (section 4). Today in `sft-indic-aya-collection` (TSAI reserves) and read by Team 10's `sft/convert.py`. | `09069079fa` · col-scan |
| 5 | `aya_collection` templated `Xlel_wd-inst` (`ben`) | 9,408 | templates over XLEL-WD | none | apache-2.0 tag; source licence not reviewed | Outside the 12 subsets #399 reviewed, so `sft-indic-aya-collection-other` (excluded) | `a3af2fde4b` (language_split) · col-scan |
| 6 | `aya_collection` translated subsets, Bengali | 4,120,142 (card: 4,120,342) | English sources, machine-translated | NLLB-3.3B (CC-BY-NC-4.0); SODA is distilled from InstructGPT (closed) | apache-2.0 tag | **Excluded** in licence table. Translationese, and it includes benchmark-derived sets (PIQA, MLQA, HotpotQA, NQ-Open, AdversarialQA, WikiQA, PAWS). | `a3af2fde4b` · col-scan |
| 7 | `ai4bharat/indic-align` `OpenAssistant_T` (`ben_Beng`) | 19,909 | human (oasst1), translated | IndicTrans2 (MIT) | cc-by-4.0 tag; oasst1 apache-2.0 | In licence table (TSAI reserves). Translationese flag. The romanised `ben_Latn` twin stays out (1% ceiling). | `032b6a9070` · col-scan |
| 8 | `indic-align` `Dolly_T` (`ben_Beng`) | 15,011 | human (dolly-15k), translated | IndicTrans2 (MIT) | cc-by-4.0 tag; dolly cc-by-sa-3.0 | Translationese flag; attribution (CC-BY-SA). | `032b6a9070` · col-scan |
| 9 | `indic-align` `WikiHow` (bn) | 20,313 | wikiHow (human), translated | IndicTrans2 | cc-by-4.0 tag | **Flag:** wikiHow is the content behind the HellaSwag exclusion (DMCA, 28 Nov). Ask TSAI. | `032b6a9070` · col-scan |
| 10 | `indic-align` `Indic_ShareLlama` / `Wiki_Conv` / `Wiki_Chat` (bn) | 21,171 / 141,435 / 198,254 | ShareGPT and crowd prompts; Wikipedia | Llama-2-70B-Chat (Llama 2 Community Licence); Wiki_Chat also Mixtral-8x7B (arXiv 2403.06350) | cc-by-4.0 tag | Excluded in licence table (30 Oct Llama rule); a re-look under the 28 Nov "record the generator" rule is TSAI's call. Wiki_Chat: Bengali non-empty checked in 1 of 32 files. | `032b6a9070` · col-scan / footers |
| 11 | `indic-align` `IndoWordNet` (bn) | 6,842,350 | IndoWordNet entries, templated | none | cc-by-4.0 tag | Dictionary lookups; low value. | `032b6a9070` · footer stats |
| 12 | `OpenAssistant/oasst1`, `oasst2` (`bn`) | 1 message each | human | none | apache-2.0 | Effectively none: the licence table's "sparse Bengali" for `sft-oasst2` is one message. | `fdf72ae082` / `179dd21fc5` · col-scan |
| 13 | `QCRI/MultiNativQA` `bangla_bd` + `bangla_in` | train 13,909 (7,018 + 6,891); dev 1,883; test 3,667 | seed queries by native speakers; questions from search "people also ask"; answers are web snippets checked and edited by annotators | GPT-4 / GPT-4o (closed) for query expansion only (arXiv 2407.09823) | CC-BY-NC-SA-4.0 (HF tag, card) | **Candidate:** the only sizeable native-Bengali QA set (Bangladesh and West Bengal). Train split only. A first look found a few question / answer pairs that may not match, so it needs a reader pass. | `018bd34d17` · local |
| 14 | `sartajekram/BanglaRQA` | train 11,912 questions on 2,400 passages | human, on Bengali Wikipedia | none | CC-BY-NC-SA-4.0 | Calls itself a benchmark (EMNLP Findings 2022); not on Team 9's list. Train split only, after Team 9's decontam, if TSAI agrees. | `f55f490265` · local |
| 15 | `csebuetnlp/dailydialogue_bn` | 11,118 / 1,000 / 1,000 | DailyDialog (English, human), translated | csebuetnlp EN→BN NMT (card) | CC-BY-NC-SA-4.0 | Multi-turn but translated; its test split is part of the BanglaNLG benchmark. | `27ea717c9e` · local |
| 16 | `rishiraj/bengalichat` | 9,500 + 500 | human (no_robots), translated | translator not stated | CC-BY-NC-4.0 | Record only. | `7db5bd2108` · footer |
| 17 | `md-nishat-008/Bangla-Instruct` (TigerLLM) | 342,391 (viewer; the card says 100K) | 500 volunteer seed tasks; instructions and answers by models | GPT-4, Claude-3.5-Sonnet (closed; card) | MIT tag | Closed-model text. Record; likely exclude. | `1a980c1086` · viewer |
| 18 | `spitfire4794/Bangla-SFT-50k` | 50,053 | model | Gemini 3 Pro Preview (seeds), DeepSeek v4 Flash (instructions scaled and answers) (card) | CC-BY-NC-4.0 | Model-made. Record. | `4b1ad3fb2a` · footer |
| 19 | Translated Alpaca / Dolly packs: `iamshnoo/alpaca-cleaned-bengali`, `BanglaLLM/bangla-alpaca-orca`, `HydraIndicLM/bengali_alpaca_dolly_67k`, `OdiaGenAI/all_combined_bengali_252k`, `bengaliAI/Dolly` | 51,760 / 172,026 / 67,017 / 252,622 / about 15k | Alpaca (text-davinci-003), Orca, Dolly and others, translated | NLLB-1.3B (iamshnoo); gpt-4o-mini-2024-07-18 (bengaliAI, `model` field); not stated for the rest | none / gpl-3.0 / none / CC-BY-NC-SA-4.0 / apache-2.0 | Translated, mostly closed-model in origin. Record; exclude. | footer / viewer / file count |
| 20 | `ai4bharat/Indic-Rag-Suite` (bn) | 3,320,042 | Wikipedia paragraph + model-written Q / A / reasoning | Meta-Llama-3.3-70B-Instruct (`model_name` in every row; Llama 3.3 Community Licence) | MIT tag | Model-made. Record. | `72117d48b0` · footer |
| 21 | Long raw text: `PleIAs/Bengali-PD`, `md-nishat-008/Bangla-TextBook` | 3,232 docs / 87,110 rows | public-domain books / school textbooks (128-word chunks) | none | no card or tag / MIT tag | Raw text, **no Q&A**: passages for people to write long-context Q&A on. PleIAs licence unverified. | `8b85267ff8` / `468ae32455` |
| 22 | `CohereLabs/aya_evaluation_suite` (`ben`) | 200 | — | — | apache-2.0 | **Excluded: benchmark.** | `e69f652e99` · col-scan |

Aggregates that repackage the rows above (`AI4BD/Mega-Bengali-Instructions`, `soketlabs/bhasha-sft`,
`kamruzzaman-asif/bangla-instruction-dataset`) are skipped: take the underlying sources directly.

**Gap (SFT, Bengali):** 750 fully human chat rows (aya_dataset's original annotations; its other 784 are human edits
of machine output), and no native multi-turn Bengali chat at all
(oasst has one message; every multi-turn set is translated or written by Llama). What must be written: native Bengali
instructions in everyday domains (forms, health, farming, money), multi-turn chat, and long Bengali documents with
Q&A for the 8k–32k band (raw long text exists in row 21).

## 2. RL prompts with checkable answers, Bengali

| # | Source | Size | Written by | Answer check | Licence (where found) | Status for us |
|---|---|---:|---|---|---|---|
| 1 | Team 10 Bengali templates | **0** train templates; 1 seed task `bn_largest_choice` (F4), written by a model, eval only | — | `rl/indic/indic_verifier.py` | repo | **Gap.** F1 (word problems), F2 (number words with লক্ষ / কোটি) and F4 (Bengali digits) list Bengali as a starting language. To be written by a Bengali speaker (Sourav offers the first ones) and checked by a second Team 2 reader (`readers.md`: aneeshads, AditeyaAItronics). |
| 2 | Kaggle "DL Sprint 3.0 – Bengali AI Math Olympiad" (competition 86200) | 209 train problems | human (olympiad) | non-negative integer answer | CC BY-SA 4.0 (competition metadata) | Human-written but small and olympiad-hard. Its public test and holdout (100 + 100) are competition benchmarks: exclude. Files not downloaded (Kaggle auth). |
| 3 | `kawchar85/Bangla-Math` (`BdMO.csv`, `dd1e9f3bd7`) | 1,455 rows, 1,215 distinct problems (1,209 after NFC and space collapse); every answer an integer (local) | Bangladesh Math Olympiad problems, OCR'd, then fixed with Gemini-flash plus a human check; CoT / PoT solutions by Qwen-14B, Qwen-32B and Gemini-pro-002 (card) | integer `Answer`, which the card lists under "Final Solution Extraction" from those solutions; about 300 problems were human-assessed | MIT tag; BdMO copyright not stated | **Candidate with flags:** a model edited the problem text, the answers look model-derived, 17 distinct problems carry conflicting answers across their duplicate rows, and about 200 problems overlap DL Sprint train. Check against official keys before training use. |
| 4 | `sartajekram/BanglaRQA` train, factoid questions | 8,329 of 11,912 | human | span answer | CC-BY-NC-SA-4.0 | F5-like, but the passages are Wikipedia (F5 wants passages written by the template author) and the set calls itself a benchmark. Ask Team 9 / TSAI. |
| 5 | GSM8K **train** translated into Bengali (`bengaliAI/gsm8k`, `Shozol/translated_gsm8k_to_bangla_train`, `shawon/gsm8k-bangla`, `Mathoctopus/GSM8KInstruct_Parallel` bn, `Emulated-Inc/multilingual-grade-school-math-training-pool` bn) | about 5.5k–7.5k each | English by people; the Bengali wording by models (gpt-4o-mini for bengaliAI; ChatGPT for MathOctopus, arXiv 2310.20246) | numeric answer | various | **Not RL-trainable** (model-written text). Eval-only at most. |
| 6 | Translated math CoT (`BanglaLLM/bangla_math_by_Ashrafur`, `z4hid/bengali-math-cot`, `Asib27/dart_math_bangla`, `laihuiyuan/mCoT-MATH` bn) | 859k / 1k / about 580k (card) / — | model-made and translated | solution text only | none / MIT / apache-2.0 / apache-2.0 | Exclude. |
| 7 | Benchmarks: MGSM bn, MSVAMP bn, `ai4bharat/indic-gsm8k` (GSM8K test, translated), `indic-math-500`, `bengaliAI/MATH`, MILU bn, Belebele `ben_Beng`, IndicQA bn, IndicXNLI bn, IndicGenBench bn, FLORES+, IN22, `hishab/titulm-bangla-mmlu`, MultiNativQA and BanglaRQA test splits | — | — | — | — | **Excluded: benchmark.** |

**Gap (RL, Bengali):** we found no human-written Bengali grade-school word problems with exact answers (every
grade-school set we found is GSM8K, machine-translated), and nothing usable as Bengali templates for F1–F6. All must
be written by a Bengali speaker.

## 3. Tokens on p1536 and a language check (300-row samples)

`bn_inventory_sample.py` draws 300 rows per source (seed 1234); `bn_sample_check.py` counts p1536 tokens (frozen,
sha256 `e6b93a93…`) and checks the script. Bengali share = Bengali letters / all letters; **bn purity** = rows with a
Bengali share of at least 0.8; **as-marked** = Assamese marker words outnumber Bengali ones (marker lists from
`audit/lang_label_config.json`). Only text fields count (ids and sampler metadata are skipped). Numbers in
`bn_sample_check_v1.json`.

| Sample | Rows in source | Tokens / row (mean, median, p95) | Est. tokens in source | Bytes / token | bn purity | Latin-heavy | as-marked | Changed by NFC |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| aya_dataset (ben) | 1,534 | 260, 200, 659 | 0.40M | 8.58 | 1.00 | 0.00 | 0.00 | 0.27 |
| aya_collection templated_bengali_news | 19,096 | 81, 78, 118 | 1.55M | 8.18 | 1.00 | 0.00 | 0.00 | 0.97 |
| indic-align OpenAssistant_T (ben_Beng) | 19,909 | 467, 383, 1,159 | 9.3M | 8.58 | 1.00 | 0.00 | 0.00 | 0.00 |
| indic-align Dolly_T (ben_Beng) | 15,011 | 137, 90, 363 | 2.1M | 8.24 | 1.00 | 0.00 | 0.00 | 0.00 |
| MultiNativQA train (bd + in) | 13,909 | 80, 79, 125 | 1.11M | 8.19 | 1.00 | 0.00 | 0.00 | 0.02 |
| Bangla-Math BdMO (problem + answer) | 1,455 | 56, 50, 115 | 0.08M | 6.46 | 0.86 | 0.05 | 0.00 | 0.13 |

- "Est. tokens in source" = rows × the sample's mean tokens (unrounded), an estimate. p95 is the nearest rank.
- All six are Bengali: no sampled row is Assamese by the marker words. Bangla-Math's lower purity comes from LaTeX
  and Latin letters in the math (`$\frac{1}{2}$`, `ABCD`). Dolly_T: 299 of 300 rows pass.
- Junk: 1 of the 300 MultiNativQA rows holds U+200B (zero-width space), which Team 10's rule strips; no chat ghost
  markers in any sample.
- "Changed by NFC" is not a fault: the rows hold the precomposed letters য় ড় ঢ় (U+09DF, U+09DC, U+09DD), which
  NFC splits into letter + nukta. Team 10's text rule applies NFC, so these rows will change; this is the same
  nukta question Team 3 raised for p1536's normalizer (G3 chat, 28 Nov).
- For scale: Team 10 asks for about 0.8B tokens of Indic SFT across 10 languages. The human-made Bengali rows above
  (rows 1, 2, 13 of section 1) come to about 3.1M tokens.

## 4. Finding: two aya_collection subsets in Team 10's SFT v1 are benchmark items

`teams/10-post-training/licences/licence_table.md` lists `templated_indic_sentiment` and `templated_indic_paraphrase`
among the 10 aya_collection subsets to consider for SFT (`sft-indic-aya-collection`, TSAI reserves), and
`teams/12-quantization/docs/aya_licence_check.md` (#399) already notes that their sources are the IndicSentiment and
IndicXParaphrase benchmarks (both in IndicXTREME). Team 10's `sft/convert.py` reads both subsets
(`AYA_COLLECTION_SUBSETS`), `sft/results/sft_v1_close.md` counts them among "the 10 usable" subsets, and
`sft/results/sft_v1_hf_pins.json` pins the same two files checked here (sha256 `f7b80de2…`, `b0a1836a…`). Neither
benchmark is in Team 9's `decontam/benchmarks.toml`.

Matches (NFC, spaces collapsed; `aya_benchmark_overlap_ben_v1.json`):

| Benchmark | Items | Found in aya rows |
|---|---:|---|
| IndicSentiment validation (bn) | 156 | English review in `inputs`: 156; Bengali review in `targets`: 146 verbatim, 156 with quote marks dropped |
| IndicSentiment test (bn) | 1,000 (998 distinct English reviews) | English review in `inputs`: 1,000; Bengali review in `targets`: 964 verbatim, 1,000 with quote marks dropped |
| IndicSentiment, English side, all 10 aya languages | 1,154 distinct English reviews | found in every language's `inputs`: 1,154 each (pan 1,153) |
| IndicXParaphrase (test-only set, bn) | 2,990 distinct Bengali sentences | 1,997 in `inputs` or `targets` |

Aya turns each sentiment review into an English-to-Bengali translation task (1,156 Bengali rows = 156 + 1,000) and
drops the review's own quote marks when it wraps it in a template, which is why 46 Bengali reviews match only without
them. So SFT v1's pinned input includes IndicSentiment's validation and test text in the 9 aya languages it keeps
(`convert.py` drops Urdu), and most of IndicXParaphrase. Proposal: mark both subsets excluded (benchmark) in the licence table and in
`convert.py`, and ask Team 9 whether IndicSentiment and IndicXParaphrase should join the fingerprint list. The Indic
side was checked for Bengali only.

## 5. Open items and next steps

1. Bengali RL templates (F1, F2, F4): Sourav writes the first ones; a second Team 2 Bengali reader checks the
   wording and five generated items.
2. A Bengali reader pass on the `templated_bengali_news` prefix (row 2) and on MultiNativQA question / answer
   matches (row 13).
3. TSAI rulings: wikiHow (row 9), the Llama / Mixtral-made indic-align subsets (row 10), BanglaRQA (row 14 and RL
   row 4), and whether Bangla-Math (RL row 3) is usable with model-derived answers.
4. Team 10 / Team 9: section 4.
5. Not verified: the upstream licence of `templated_bengali_news` (from #399 only); Bangla-Instruct's true row count
   (viewer 342,391 vs card 100K); translators of rows 16 and 19 where not stated; DL Sprint files (not downloaded);
   the licence of PleIAs Bengali-PD.

## Commands

```bash
cd teams/02-data-b/post_training
python -I bn_inventory_sample.py <samples_dir> <files_root>        # 6 samples, 300 rows each, seed 1234
python bn_sample_check.py --tokenizer <p1536 tokenizer.json> --samples <samples_dir>/*.jsonl \
    --out bn_sample_check_v1.json
# section 4: aya_collection @09069079fa (templated_indic_sentiment, templated_indic_paraphrase parquet),
# ai4bharat/IndicSentiment @dc8f3f6688 (data/{validation,test}/bn.json), ai4bharat/IndicXParaphrase @181031f9e6 (data/bn.tsv)
python aya_benchmark_overlap.py --lang ben --aya-sentiment <...>/templated_indic_sentiment/train-00000-of-00001.parquet \
    --aya-paraphrase <...>/templated_indic_paraphrase/train-00000-of-00001.parquet \
    --indicsentiment <...>/IndicSentiment/data --indicxparaphrase <...>/IndicXParaphrase/data/bn.tsv \
    --out aya_benchmark_overlap_ben_v1.json
```

Sample sha256 (the samples hold dataset text and stay out of the repo): aya_dataset_ben `a8ad4ff2…`,
templated_bengali_news `04ba49da…`, OpenAssistant_T `59120ff4…`, Dolly_T `c42ac4fb…`, MultiNativQA `ed959d20…`,
BdMO `c341cc2d…`. Input sha256 for section 4: sentiment parquet `f7b80de2…`, paraphrase parquet `b0a1836a…`,
IndicSentiment `validation/bn.json` `12d3d082…`, `test/bn.json` `af414496…`, IndicXParaphrase `bn.tsv` `b80bda6a…`.

## Checks

An independent recheck (its own code) reproduced every number in section 3 and the section 4 counts, confirmed the
revisions and licence tags of all 28 Hub repos, and re-counted most of the section 1 row counts at the stated
revisions. It also
found the points fixed in this version: the Bangla-Math answer source, the quote-mark matches and Team 10's use of
the two subsets (section 4), the 750 fully human aya_dataset rows, and a p95 off by one rank.

## Sources

- Team 10 request, licence table, Indic RL rules: `teams/10-post-training/docs/data_request_teams1_2_v1.md`,
  `licences/licence_table.md`, `rl/indic_prompts_v0.md`; Team 9 list `teams/09-evaluation/decontam/benchmarks.toml`.
- HF API `dataset_info` (revision, tags, files) for every Hub row, read 28 Nov 2026; dataset cards at those revisions.
- indic-align generators: arXiv 2403.06350. MultiNativQA method: arXiv 2407.09823. MathOctopus translation: arXiv
  2310.20246. DL Sprint 3.0: Kaggle competition page (competition 86200).
