# Hindi post-training data: inventory v1 (Data B Lab 5 task 8 / Team 10 #882, Hindi line)

By riyaagrahari, 28 Nov 2026.

Facts checked on 28 Nov 2026 from the dataset cards, the HF API, the upstream repos and the Airavata report
(arXiv 2401.15006, which gives the licence of each indic-instruct subset). Open items are listed in section 3.

Rules applied (from `teams/10-post-training/docs/data_request_teams1_2_v1.md` and TSAI 28 Nov):
- NC, ND and unstated licences are now allowed, but every source records its licence and where it was found.
- If a model made the data, record the generator model and that model's licence terms.
- RL training text is written by people, never by a model (TSAI rule, 3 Nov). Model text is eval-only.
- No benchmark items as training data (e.g. MGSM, the Hindi part of benchmarks; HellaSwag excluded 28 Nov because of
  the wikiHow DMCA takedown).
- Native script, ZWJ/ZWNJ kept, no NFKC, 1% romanised ceiling.

## 1. SFT (instruction data), Hindi

| # | Source | Hindi rows | Written by | Generator model | Licence (where found) | Status for us |
|---|---|---:|---|---|---|---|
| 1 | `CohereLabs/aya_dataset` (language_code `hin`) | 1,153 | human annotators | none | apache-2.0 (HF tag) | **Already in licence table** (`sft-indic-aya-dataset`). Usable, but small. |
| 2 | `CohereLabs/aya_collection`, human-templated Hindi subsets | see #399 | human templates on human NLP data | none | apache-2.0 + source licences (#399) | **Already in licence table.** Team 10 notes the Hindi count is low. |
| 3 | `CohereLabs/aya_collection`, translated subsets | — | translated | NLLB-3.3B (CC-BY-NC-4.0) | apache-2.0 (HF tag) | **Excluded** in licence table. |
| 4 | `ai4bharat/indic-align`, `OpenAssistant_T` subset | 19,909 rows (one column per language) | human (oasst1), translated | IndicTrans2 (MIT) | cc-by-4.0 (HF tag) | **Already in licence table.** |
| 5 | `ai4bharat/indic-instruct-data-v0.1`, `wikihow` (hi) | 6,055 | wikiHow authors (human-moderated) | none | CC-0 (Airavata report, wikiHow subset) | **Flag:** wikiHow content was the reason HellaSwag was excluded (DMCA, 28 Nov). Ask TSAI before use. |
| 6 | `ai4bharat/indic-instruct-data-v0.1`, `anudesh` (hi) | 7,577 | crowd-written prompts | responses from Llama-2-70B (Llama 2 Community Licence) | CC-BY-4.0 (Airavata report, Anudesh) | Prompts human, responses model-made. Record generator; likely eval-only or needs TSAI ruling. |
| 7 | `ai4bharat/indic-instruct-data-v0.1`, `dolly` (hi) | 15,011 | human (databricks-dolly-15k), translated | IndicTrans2 (MIT) | CC-BY-SA-3.0 (Airavata report, Dolly) | Translated, so check translationese ("zero translationese" filter in #882). |
| 8 | `ai4bharat/indic-instruct-data-v0.1`, `oasst1` (hi) | 20,128 | human (oasst1), translated | IndicTrans2 (MIT) | apache-2.0 (oasst1) | Overlaps row 4 (same oasst source). Dedup against it. |
| 9 | `ai4bharat/indic-instruct-data-v0.1`, `flan_v2` (hi) | 67,463 | templated, translated | IndicTrans2 (MIT) | apache-2.0 (Airavata report, FLAN-v2) | FLAN mixes benchmark tasks: needs a decontam pass (Team 9 F2). |
| 10 | `ai4bharat/indic-instruct-data-v0.1`, `hh-rlhf` (hi) | 5,000 | human prompts | responses from an Anthropic model, translated | MIT (Airavata report, hh-rlhf) | **Flag:** model-made responses from a closed model. Record generator; ask TSAI. |
| 11 | `ai4bharat/indic-instruct-data-v0.1`, `lm_sys` (hi) | 50,000 | user prompts | responses from many chat models (some closed) | LMSYS-Chat-1M Dataset License Agreement (Airavata report) | **Flag:** mixed closed-model output and a restrictive upstream licence. Likely exclude. |
| 12 | `ai4bharat/indic-instruct-data-v0.1`, `nmt-seed` (hi) | 50,000 | human-annotated (BPCC-Human) | none | CC-BY-4.0 (Airavata report, NMT) | Translation task data, not chat. Low value for Stage 1. |
| 13 | `Cognitive-Lab/Aya_Hindi` | 1M–10M (tag) | from aya_collection | includes NLLB-translated parts | apache-2.0 (HF tag), gated | Derived from rows 2–3. Adds nothing new and carries the NLLB issue. Skip. |
| 14 | `ai4bharat` Updesh (2025) | 9.5M across 13 languages (paper) | synthetic | not named in the sources found (open) | "Microsoft research licence" (AIKosh listing) | Synthetic and non-standard licence. Record; likely exclude. |
| 15 | `rishiraj/hindichat` | 10,000 (card) | not stated in the card summary | not stated | CC-BY-NC-4.0 (HF tag) | Provenance unclear. Record only. |
| 16 | `guneetsk99/hindi_instruction_set_187K` | ~187k | not stated (empty card) | not stated | CC-BY-NC-ND-4.0 (HF tag) | No card, provenance unknown. Record only. |

**Gap (SFT, Hindi):** clean, human-written native Hindi chat data is small (row 1 about 1.2k rows; row 5 about 6k
with a legal flag). Most volume is translated (rows 7–9) or model-made (rows 6, 10, 11). What must be written:
native Hindi instructions in everyday domains (government forms, health, farming, money), multi-turn chat, and
long Hindi documents with Q&A for the 8k–32k band.

## 2. RL prompts with checkable answers, Hindi

| # | Source | Size | Written by | Answer check | Licence (where found) | Status for us |
|---|---|---:|---|---|---|---|
| 1 | Team 10 human templates `hi_f1_left`, `hi_f1_change`, `hi_f6_minutes`, `hi_f3_weekday` | 4 templates (unlimited items via `generate.py`) | gmrammohan15, reviewed by riteshverma | `rl/indic/indic_verifier.py` | repo | **train** (#781) |
| 2 | HAWP (LTRC, IIIT-Hyderabad, LREC 2022), github.com/hellomasaya/hawp | 2,336 problems | human | each item has an `Equation` field, so the answer can be computed | **unstated** (no LICENSE file; checked 28 Nov) | Candidate. Many answers are decimals, while the verifier's F1 is integer: use the integer-answer subset or add a decimal rule. Not in Team 9 or Team 10 eval files on main (checked 28 Nov); Team 9 to confirm with decontam_check.py. |
| 3 | MGSM (Hindi part) | — | — | — | — | **Excluded:** benchmark. |

**Gap (RL, Hindi):** family **F2** (number words to digits) now has a Hindi template in PR #932, waiting for Team 2
sign-off. Families **F4** (Indic digits: compare, order, add) and **F5** (a name, number or place from a short passage)
still have **no Hindi template**. These must be
written by a Hindi speaker and checked by a second Team 2 reader (rule: a template naming a model as source fails
the lint).

## 3. Proposed next steps

1. Ask TSAI for rulings on rows 5 (wikiHow), 6, 10 and 11 (model-made responses).
2. Add the indic-instruct rows (with the per-subset licences above) to `teams/10-post-training/licences/licence_table.md`.
3. Count the human-templated Hindi rows of aya_collection from #399, and dedup rows 4 and 8.
4. Hindi templates: F2 is in PR #932 (written by Riya, review asked from Ritesh). F4 and F5 still open.
5. Test HAWP's integer subset against `indic_verifier.py`.

## Sources

- Team 10 request: `teams/10-post-training/docs/data_request_teams1_2_v1.md`; templates and rules:
  `teams/10-post-training/rl/indic_prompts_v0.md`, `rl/indic/templates/indic_templates.yaml`; licence table:
  `teams/10-post-training/licences/licence_table.md`.
- HF API tags and the dataset-server row filter (28 Nov) for aya_dataset, indic-align, Aya_Hindi,
  indic-instruct-data-v0.1.
- https://huggingface.co/datasets/ai4bharat/indic-instruct-data-v0.1 and the Airavata report, https://arxiv.org/abs/2401.15006
- https://github.com/hellomasaya/hawp and https://aclanthology.org/2022.lrec-1.373
- https://arxiv.org/abs/2509.21294 (Updesh) and https://aikosh.indiaai.gov.in/home/datasets/details/updesh.html
- https://huggingface.co/datasets/rishiraj/hindichat, https://huggingface.co/datasets/guneetsk99/hindi_instruction_set_187K
