# Spec v1.1 (Data A)

This folder holds **spec v1.1**, the cleaning spec of theschoolofai/era-v5-lab#435.
- **Gate 2 (14 Nov 2026):** TSAI made spec v1 and spec v1.1 one spec. So spec v1.1 is spec v1's rules plus the medicines for the **new** diseases that the Week 2 reading audits found in **1% or more of the docs read in a domain** (English, code, math, science).
- **The new diseases:** each has a medicine (a rule that fixes or drops a doc), unit tests and a harm test on the gold docs.
- **`clean.py` is not here.** It is rebuilt from this spec in the next PR (task 2, due 17 Nov).

Every path below is relative to the repository root.

## Start here: what to read, in order

| # | file | what it tells you |
|---|---|---|
| 1 | `teams/01-data-a/spec_v1_1/sheets/specv1_1.md` | **The spec itself:** all 364 rules (spec v1's 340, then the 24 of v1.1), in the order `clean()` runs them. Each rule is a card: the disease, examples, the python code, the action, the harm result and the side effects. Its top sections explain how the sheet is made, the combined harm results and speed, and the identity of each rule. |
| 2 | `teams/01-data-a/spec_v1_1/sheets/NEW_DISEASES.md` | **Why these rules:** every disease the readers marked new, how many docs it is in, whether it reaches the 1% bar, and the rule that treats it. It also lists the diseases that turned out not to be new, and the gold contradictions. |
| 3 | `teams/01-data-a/spec_v1_1/results/sheets/harm_tests.md` | **The record for each new disease:** its medicine, its harm test (alone, and all of a sheet's rules in order), its unit tests, the speed passes, and Harini's English findings. |
| 4 | `teams/01-data-a/spec_v1_1/results/combined/validation.md` | **The combined spec, tested:** harm of the whole `clean()` built from the spec, per pack, and its speed. `teams/01-data-a/spec_v1_1/results/combined/README.md` says how to reproduce it. |
| 5 | `teams/01-data-a/spec_v1_1/sheets/medicine_<family>.md` | **The source cards** of the v1.1 rules, one sheet per family: `medicine_english.md` (3 rules), `medicine_math.md` (8), `medicine_sci.md` (12) and `medicine_indic.md` (1, Data B's `DB-C6-001`). `decisions_<family>.md` explains the choices behind them. |

## The harm test records: `harm_tests.md`

There are two files of this name, and a tool with a similar one:

| path | what it is |
|---|---|
| `teams/01-data-a/spec_v1_1/results/sheets/harm_tests.md` | **The record to read**, written by hand from the harm runs. Its sections, in order:<br>1. how the harm tests were run;<br>2. each new disease, with its medicine and its harm result alone;<br>3. all of a sheet's rules together, per pack, with the gold docs read and the gold contradictions;<br>4. the combined spec v1.1;<br>5. speed (both speed passes, with before and after);<br>6. the unit tests of each medicine;<br>7. the other families and diseases: Indic `DB-C6-001`, and HariniJasti's C1 lines. |
| `teams/01-data-a/spec_v1_1/results/combined/harm_tests.md` | **The raw report** of `teams/01-data-a/spec_v1/validate/make_harm_tests.py` on the `clean()` built from the combined spec: `clean()` per pack, each rule alone on the gold of its packs, and each disease-code function. Its title and some wording are the harness's own. Its summary is `validation.md` in the same folder. |
| `teams/01-data-a/harmtest/harm_test.py` | The harm test **tool**, shared with spec v1, and not changed here. |

## Folder map

| folder | what is in it | made by |
|---|---|---|
| `teams/01-data-a/spec_v1_1/sheets/` | The medicine sheets, decisions and `NEW_DISEASES.md` (written by hand). `specv1_1_additions.md` holds the 24 v1.1 cards on their own, collated from the medicine sheets. `specv1_1.md` is the combined spec. | `specv1_1.md`: `teams/01-data-a/spec_v1_1/scripts/combine_spec.py`. **Don't edit it by hand**: change `teams/01-data-a/spec_v1/sheets/specv1.md` or the medicine sheets, then rerun the script. |
| `teams/01-data-a/spec_v1_1/results/sheets/` | Harm reports of the v1.1 rules on their own: `<pack>_harm.json` (doc_ids and counts only), and the Indic runs `indic_sangraha-s_harm.md` and `indic_sangraha-v_harm.md`. Also `harm_tests.md`, the record to read, and `summary.md`, the results per pack and what is open. | `teams/01-data-a/harmtest/harm_test.py`; `teams/02-data-b/tools/harm_test_indic.py` for Indic |
| `teams/01-data-a/spec_v1_1/results/combined/` | Harm and speed of the combined spec: `validation.md` (the summary, also a section of `specv1_1.md`), `specv1_<pack>_harm.json` for the 13 Data A packs, `combined_ind-te-sangraha-v_harm.json`, the harness's `harm_tests.md`, `speed.md`, and a `README.md` with the commands. | `teams/01-data-a/spec_v1/validate/make_harm_tests.py`, `harm_test.py`, `teams/01-data-a/spec_v1/run_clean.py` |
| `teams/01-data-a/spec_v1_1/results/reading/` | The reading audits, counted: `summary.md`, `diseases_by_domain.csv` (each disease per domain, with its % of docs read) and `findings_all.csv` (every reading row). | `teams/01-data-a/spec_v1_1/scripts/collect_reading_prs.py` |
| `teams/01-data-a/spec_v1_1/scripts/` | The tools of this folder; `teams/01-data-a/spec_v1_1/scripts/README.md` describes each one. `collect_reading_prs.py` counts the readings, and `show_examples.py` shows the text behind a reading row (output kept outside the repo). `build_reading_check.py` writes the reading consolidation, `reading_recall.py` counts the reading docs a rule treats, `time_rules.py` times every rule on whole packs (TSAI speed rule), and `combine_spec.py` writes `specv1_1.md`. | by hand |
| `teams/01-data-a/spec_v1_1/tests/` | Unit tests: one file per medicine sheet and per script, plus `test_code_lang_label.py` (a code rule fires on a doc labelled `lang_label = "code"`, as TSAI asked at Gate 2). All text in them is made up. | by hand |

**Files outside this folder that spec v1.1 uses (not changed here):**

| path | what it is |
|---|---|
| `teams/01-data-a/spec_v1/sheets/specv1.md` | Spec v1, the first part of the combined spec (exactly as on TSAI main) |
| `teams/01-data-a/harmtest/harm_test.py` | The team's harm test: it runs a rule on a pack's gold docs and counts the docs it changes or drops |
| `teams/02-data-b/tools/harm_test_indic.py` | Data B's harm test for Indic, with the joiner (ZWJ/ZWNJ) and normal-form checks |
| `teams/01-data-a/spec_v1/build/build_clean.py` | Builds a `clean.py` from a sheet; it shows that `specv1_1.md` builds (the real rebuild is the next PR) |
| `teams/01-data-a/spec_v1/validate/make_harm_tests.py`, `teams/01-data-a/spec_v1/run_clean.py` | Harm test and timing of a whole `clean()`, per pack |
| `teams/01-data-a/gold/<pack>_gold.csv`, `teams/02-data-b/gold/<pack>_gold.csv` | The gold docs (Data A's, Data B's): docs two readers marked clean, which a rule must not change |
| `teams/01-data-a/reading/` | The readers' audits (`reading_<pack>_<reader>.csv` and `.md`) and `reading_check_v1.md`, the consolidation of them |

## How it is built, step by step

From `teams/01-data-a` unless said otherwise:
1. **Count the readings:** `python3 -I spec_v1_1/scripts/collect_reading_prs.py` writes `spec_v1_1/results/reading/`. Options are in `spec_v1_1/scripts/README.md`.
2. **Write a medicine** for each new disease at the 1% bar, as a card in `spec_v1_1/sheets/medicine_<family>.md`, with unit tests in `spec_v1_1/tests/test_medicine_<family>.py`.
3. **Harm-test each sheet,** per pack (command below). Reports go to `spec_v1_1/results/sheets/`, never to `teams/01-data-a/rules/`.
4. **Collate the cards** into `spec_v1_1/sheets/specv1_1_additions.md`.
5. **Combine with spec v1:**
   ```
   python3 -I spec_v1_1/scripts/combine_spec.py --v1 spec_v1/sheets/specv1.md --additions spec_v1_1/sheets/specv1_1_additions.md \
     --validation spec_v1_1/results/combined/validation.md --out spec_v1_1/sheets/specv1_1.md
   ```
   `teams/01-data-a/spec_v1_1/tests/test_combine_spec.py` fails if `specv1_1.md` is out of date.
6. **Test the combined spec:** build its `clean.py` in a copy of the branch, then run its harm and timing. The commands are in `spec_v1_1/results/combined/README.md`.
7. **Unit tests:** `python3 -m unittest discover -s spec_v1_1/tests`.

## Harm test of one sheet

From the repository root, one run per pack, never pooled. `--rule all` tests each rule on its own, then all of them in sheet order.

```
python3 -I teams/01-data-a/harmtest/harm_test.py \
  --pack <packs folder>/<pack>.parquet \
  --gold teams/01-data-a/gold/<pack>_gold.csv \
  --rules teams/01-data-a/spec_v1_1/sheets/medicine_<family>.md \
  --rule all \
  --report teams/01-data-a/spec_v1_1/results/sheets/<pack>_harm.json
```

- **Limit:** gold docs changed plus dropped must be at most `max(1, floor(1% of gold))`. A pack with no gold set is NOT TESTABLE, and a result of 0 is only an upper bound on the harm (about 3/n).
- **Gold contradictions:** gold docs that hold the very disease a rule targets. Vijay agreed they are left out of the count for that rule, and re-read at the next gold refresh. The 10 of them are listed in `teams/01-data-a/spec_v1_1/sheets/NEW_DISEASES.md`.
- **The packs** are the Week 1 diagnosis packs (500 docs each). They stay outside the repo, and each report records the pack's sha256.

| pack | gold docs | limit |
|---|---|---|
| math-finemath | 86 | 1 |
| math-megamath | 26 | 1 |
| sci-finepdfs | 202 | 2 |
| code-cpp, code-go, code-java, code-js-ts, code-python, code-rust | 122, 163, 116, 204, 141, 234 | 1, 1, 1, 2, 1, 2 |
| en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth | 62, 158, 129, 326 | 1, 1, 1, 3 |
| ind-te-sangraha-v (Data B's gold) | 80 | 1 |

## Not in this PR

On Vijay's ruling of 14 Nov, this PR holds spec v1.1 only. These go into the `clean.py` PR:
- the rebuilt `clean.py`;
- Smita's spec v1 math speed fixes (patilvijay23/era-v5-lab#43);
- six whole-line labels for spec v1's `DA-C1-006`, from HariniJasti's labels (tested; see `teams/01-data-a/spec_v1_1/results/sheets/harm_tests.md`).

## Open decisions

- **The new codes** (A7, A8, B6, C6, C7, C8, C9, D6, D7) need the team's agreement, and entries in `diagnosis/DISEASES.md` and in `CODE_ORDER` in `teams/01-data-a/spec_v1/build/build_clean.py`.
- **The gold contradictions** are to be re-read at the next gold refresh.
- **Settled at Gate 2:** the harm run that counts is the combined spec, all rules in order (`teams/01-data-a/spec_v1_1/results/combined/`). The v1.1-alone runs in `teams/01-data-a/spec_v1_1/results/sheets/` stay as each rule's own evidence.
