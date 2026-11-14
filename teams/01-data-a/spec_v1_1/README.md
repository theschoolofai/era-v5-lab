# Spec v1.1 (Data A)

This folder holds **spec v1.1**: the medicines for the **new** diseases that the Week 2 reading audits found in **1% or more of the docs read in a domain** (English, code, math, science). Each new disease has a medicine (a rule that fixes or drops a doc), unit tests, and a harm test on the gold docs. It is theschoolofai/era-v5-lab#435.

At Gate 2 (14 Nov 2026), TSAI made spec v1 and spec v1.1 one spec v1.1. `sheets/specv1_1.md` is that spec: spec v1's 340 rules and these 24, in run order. The `clean.py` rebuild from it, with its harm and speed reports, is the next PR (task 2, due 17 Nov).

Every path below is relative to the repository root.

## Start here: what to read, in order

| # | file | what it tells you |
|---|---|---|
| 1 | `teams/01-data-a/spec_v1_1/sheets/specv1_1.md` | **The combined spec v1.1 (Gate 2):** 364 cards, spec v1's 340 then these 24, in the order `clean.py` runs them, each with its python code. Written by `scripts/combine_spec.py`; do not edit it by hand. |
| 2 | `teams/01-data-a/spec_v1_1/sheets/specv1_1_additions.md` | **The 24 spec v1.1 rules alone,** as cards in the spec v1 form: the disease, examples, the python code, the action, the harm result and the side effects. The cards and their code are copied unchanged from the four medicine sheets below. |
| 3 | `teams/01-data-a/spec_v1_1/results/combined/validation.md` | **The combined `clean()` checked:** harm per pack with all rules in order, and speed. It is also copied into `specv1_1.md`. |
| 4 | `teams/01-data-a/spec_v1_1/sheets/NEW_DISEASES.md` | **Why these rules:** every disease the readers marked new, how many docs it is in, whether it reaches the 1% bar, and the rule that treats it. It also lists the diseases that turned out not to be new, and the gold contradictions. |
| 5 | `teams/01-data-a/spec_v1_1/results/sheets/harm_tests.md` | **The record for each new disease:** its medicine, its harm test, its unit tests, the speed passes, and HariniJasti's English findings. |
| 6 | `teams/01-data-a/spec_v1_1/sheets/medicine_<family>.md` | **The source cards**, one sheet per family: `medicine_english.md` (3 rules), `medicine_math.md` (8), `medicine_sci.md` (12) and `medicine_indic.md` (1, Data B's `DB-C6-001`). `decisions_<family>.md` explains the choices behind them. |

## The harm test records: `harm_tests.md`

`teams/01-data-a/spec_v1_1/results/sheets/harm_tests.md` is written by hand from the harm runs. Its sections, in order:
1. how the harm tests were run;
2. each new disease, with its medicine and its harm result alone;
3. all of a sheet's rules together, per pack, with the gold docs read and the gold contradictions;
4. the combined spec v1.1, checked on 14 Nov (summarised in `results/combined/validation.md`);
5. speed: both speed passes, with before and after;
6. the unit tests of each medicine;
7. the other families and diseases: Indic `DB-C6-001`, and HariniJasti's C1 lines.

The per-pack reports it draws on are next to it: `<pack>_harm.json` (doc_ids and counts only), and `indic_sangraha-s_harm.md` and `indic_sangraha-v_harm.md` for Indic. The harm test tool itself is `teams/01-data-a/harmtest/harm_test.py`; it is shared with spec v1, and not changed here.

## Folder map

| folder | what is in it |
|---|---|
| `teams/01-data-a/spec_v1_1/sheets/` | **The spec:** `specv1_1.md` (combined), `specv1_1_additions.md` (the 24 cards), the four medicine sheets, `decisions_<family>.md` and `NEW_DISEASES.md`. |
| `teams/01-data-a/spec_v1_1/results/sheets/` | **The harm tests:** per-pack reports, `harm_tests.md` (the record to read) and `summary.md` (the results per pack, and what is open). |
| `teams/01-data-a/spec_v1_1/results/combined/` | `validation.md`: the combined `clean()`'s harm and speed. Its per-pack reports go into the `clean.py` PR. |
| `teams/01-data-a/spec_v1_1/scripts/` | `combine_spec.py`, which writes `specv1_1.md`. The reading collector and its counts (`scripts/`, `results/reading/`) are as merged in #365, not changed here; `scripts/README.md` describes them. |
| `teams/01-data-a/spec_v1_1/tests/` | **Unit tests:** one file per medicine sheet, `test_medicine_<family>.py`; `test_combine_spec.py` for the combined sheet; and `test_code_lang_label.py`, which shows a code rule fires on a doc labelled `lang_label = "code"`, as TSAI asked at Gate 2. All text in them is made up. The reading scripts' tests are as on main. |

**Files outside this folder that spec v1.1 uses (not changed here):**

| path | what it is |
|---|---|
| `teams/01-data-a/harmtest/harm_test.py` | The team's harm test: it runs a rule on a pack's gold docs and counts the docs it changes or drops |
| `teams/02-data-b/tools/harm_test_indic.py` | Data B's harm test for Indic, with the joiner (ZWJ/ZWNJ) and normal-form checks |
| `teams/01-data-a/gold/<pack>_gold.csv`, `teams/02-data-b/gold/<pack>_gold.csv` | The gold docs (Data A's, Data B's): docs two readers marked clean, which a rule must not change |
| `teams/01-data-a/spec_v1/sheets/specv1.md` | Spec v1, the first half of `specv1_1.md`. Its `DA-A1-001` is what `test_code_lang_label.py` tests |
| `teams/01-data-a/spec_v1/build/build_clean.py` | Builds `clean.py` from a sheet; it reads `specv1_1.md` as it is |
| `teams/01-data-a/reading/` | The readers' audits and `reading_check_v1.md`, the consolidation the 1% counts come from |

## Writing the combined sheet

From `teams/01-data-a`:

```
python3 -I spec_v1_1/scripts/combine_spec.py \
  --v1 spec_v1/sheets/specv1.md \
  --additions spec_v1_1/sheets/specv1_1_additions.md \
  --validation spec_v1_1/results/combined/validation.md \
  --out spec_v1_1/sheets/specv1_1.md
```

Spec v1's cards are copied byte for byte. Each v1.1 card gets a `pack_id` check, so it runs only on the packs in its `ORIGIN`. Each family's v1 cards run first, then its v1.1 cards; English's F1 (`DA-F1-005`) stays last.

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
| en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth | 62, 158, 129, 326 | 1, 1, 1, 3 |
| ind-te-sangraha-v (Data B's gold, with `harm_test_indic.py`) | 80 | 1 |

**Unit tests**, from `teams/01-data-a`: `python3 -m unittest discover -s spec_v1_1/tests`.

## Not in this PR

On Vijay's ruling and TSAI's note (14 Nov), #435 holds spec v1.1 only. These go into the `clean.py` PR (task 2), or the reading PR:
- the rebuilt `clean.py`, the combined `clean()`'s per-pack harm and speed reports, and the timing tool `time_rules.py` with its tests;
- **Smita's spec v1 math speed fixes** (patilvijay23/era-v5-lab#43), and six whole-line labels for spec v1's `DA-C1-006` from HariniJasti's labels (tested; see `harm_tests.md`);
- **the member reading files** of Week 2, and the collector changes since #365.

## Open decisions

- **The new codes** (A7, A8, B6, C6, C7, C8, C9, D6, D7) need the team's agreement, and entries in `diagnosis/DISEASES.md` and in `CODE_ORDER` in `teams/01-data-a/spec_v1/build/build_clean.py`.
- **The gold contradictions** are to be re-read at the next gold refresh.
