# F2 results: G9 fingerprints v1

The [Indic report](indic_gold_validation.json) was refreshed after #362 for cleaner `22d818c7…`: all 18 Indic own-pack gold sets (2,193 documents) pass with F2 alone and after cleaning, and F2 alone drops zero raw gold documents. See the [PR #244 evidence packet](../cleaner/pr244_gold_refresh/README.md) for hashes and results, or [validate_f2_indic.py](../../../spec_v1/validate/validate_f2_indic.py) with the [documented inputs](../../../spec_v1/README_indic.md#optional-f2-validation) to reproduce it. F2 remains opt-in and does not cover Itihasa.

The 13 non-Indic pack results and drop review below remain historical snapshots tied to their recorded hashes. They were not rerun in this gold refresh.

`run_clean.py --f2` and the F2 harm tests on the 13 Data A packs. Fingerprint set `11e290a44d1467875fdf8bebc55eab21f0a6367f411aab98a4a027a546fd372e` (full set, pinned in `spec_v1/f2_rule.py`), `clean.py` `a5a1a596a0e7`, `spec_v1/f2_rule.py` `0f6968be84b1`. The reports of F2 alone are `f2_<pack>_harm.json`.

| pack | docs | dropped by `clean.py` | **dropped by F2** | kept | errors | gold hit by F2 alone | gold hit by `clean.py` then F2 | gold docs | limit | harm |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| `code-cpp` | 500 | 10 | **0** | 490 | 0 | 0 | 0 (0 by F2) | 122 | 1 | PASS |
| `code-go` | 500 | 44 | **0** | 456 | 0 | 0 | 0 (0 by F2) | 163 | 1 | PASS |
| `code-java` | 500 | 11 | **0** | 489 | 0 | 0 | 0 (0 by F2) | 116 | 1 | PASS |
| `code-js-ts` | 500 | 22 | **0** | 478 | 0 | 0 | 0 (0 by F2) | 204 | 2 | PASS |
| `code-python` | 500 | 16 | **0** | 484 | 0 | 0 | 0 (0 by F2) | 141 | 1 | PASS |
| `code-rust` | 500 | 17 | **0** | 483 | 0 | 0 | 0 (0 by F2) | 234 | 2 | PASS |
| `en-dclm` | 500 | 9 | **0** | 491 | 0 | 0 | 0 (0 by F2) | 62 | 1 | PASS |
| `en-fineweb-edu` | 500 | 1 | **1** | 498 | 0 | 1 | 1 (1 by F2) | 158 | 1 | PASS |
| `en-nemotroncc` | 500 | 17 | **0** | 483 | 0 | 0 | 0 (0 by F2) | 129 | 1 | PASS |
| `en-nemotroncc-synth` | 500 | 1 | **0** | 499 | 0 | 0 | 0 (0 by F2) | 326 | 3 | PASS |
| `math-finemath` | 500 | 13 | **7** | 480 | 0 | 0 | 0 (0 by F2) | 86 | 1 | PASS |
| `math-megamath` | 500 | 10 | **2** | 488 | 0 | 0 | 0 (0 by F2) | 26 | 1 | PASS |
| `sci-finepdfs` | 500 | 13 | **3** | 484 | 0 | 0 | 0 (0 by F2) | 202 | 2 | PASS |

- **F2 alone:** `harm_test.py --rule F2` on the raw gold docs.
- **`clean.py` then F2:** each gold doc through `clean.py`, then F2 on the text it keeps, as `run_clean.py --f2` does. A gold doc counts once, changed or dropped. `clean.py` changes no gold doc on these packs, so the two agree.
- **kept + dropped + errors = docs** on every pack (`final` in the summary).

## Every doc F2 drops, reviewed

The offset is in the cleaned text. **Possible** means benchmark content may be in the doc; **shared text** means the match is text that many pages share. F2 drops all of them.

| pack | doc | benchmark items | offset | review | why |
|---|---|---|---:|---|---|
| `en-fineweb-edu` | `dabaf841592d630e` | `milu:test:19374` | 2,108 | possible: a passage only | A clause of Article 15 of the Indian Constitution that a MILU item quotes. The question is not in the doc. A gold doc. |
| `math-finemath` | `90bbe1d4fc081caa` | `mmlu:test:5219`, `mmlu:test:1329` ... | 5,586 | shared text | An answer-option layout (I only, II only, ...) that 17 MMLU items share. |
| `math-finemath` | `9fd5f2644b8c04d8` | `milu:test:10689`, `mmlu:test:6524` | 4,994 | shared text | An 8-word question stem used in many exams. The doc is a physics past paper with another question. |
| `math-finemath` | `e9bc93d8821adcec` | `milu:test:16197`, `milu:test:6786` ... | 109,563 | possible: instructions only | A practice test of the same question types as MILU. Only the standard instructions match, across 15 items; no question does. |
| `math-finemath` | `263a5308b96d2e4a` | `milu:test:10090` | 3,850 | possible: a question | The same train-and-man speed question as the MILU item, with options and a worked answer. Two runs match; the words between them differ, so the wording is close, not the same. |
| `math-finemath` | `376e639903abfe9a` | `milu:test:11752` | 1,614 | shared text | Data-sufficiency instructions, standard in GMAT-style tests. |
| `math-finemath` | `65a9730b24a24909` | `livecodebench:release_v6:3047` | 5,591 | shared text | The definition of a perfect square, also in a LiveCodeBench statement. |
| `math-finemath` | `3a2ccc88dfcd67c9` | `milu:test:16177` | 10,018 | shared text | Data-sufficiency instructions, 3 runs of one MILU item's instructions. |
| `math-megamath` | `1ad9fec1410f4b83` | `mmlu:test:5219`, `mmlu:test:1329` ... | 1,543 | shared text | The same answer-option layout, 17 MMLU items. |
| `math-megamath` | `8aee157afdb8bb59` | `livecodebench:release_v6:2953` | 97 | shared text | The definition of the distance between two points, also in a LiveCodeBench statement. |
| `sci-finepdfs` | `d20d4f04e5704ba7` | `hle:test:6724d81d42ec04c22a24aa83` | 37,440 | shared text | A paper citation (NAACL proceedings) that an HLE item also cites. |
| `sci-finepdfs` | `35eb8b91a98d3a41` | `mmlu:test:5817`, `mmlu:test:5654` ... | 1,111,191 | possible: a passage only | A public Jefferson passage that three MMLU history questions quote. The questions and options are not in the doc. G9's README names it as a false hit. |
| `sci-finepdfs` | `3f91dba6d4dcbafd` | `hle:test:6724d81d42ec04c22a24aa83` | 22,947 | shared text | The same citation, 4 times. |

4 possible, 9 shared text, 0 not reviewed. Only one holds a benchmark question; the other possible ones hold a quoted passage or instructions.
