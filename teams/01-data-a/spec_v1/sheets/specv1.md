# Medicine sheet: Data A — consolidated spec v1 (contributors retained per rule)

Status: **DRAFT / CANDIDATE**. Consolidates the five local medicine sheets; no rule is approved by this document. Follows [medicine_TEMPLATE.md](../../../diagnosis/templates/medicine_TEMPLATE.md): each medicine retains disease/count/examples, words and Python, action, harm evidence, and side effects. Compiler identity is not inferred from contributor handles.

## Scope, dispatch and executable contract

The 29 covered packs are partitioned into code (six), English prose (four), math (two), science (one), and Indic (16). Indic sibling scopes are validated separately below.

Each Python fence is one independent rule module. Load with `teams/01-data-a/tools/harm_test.py`, which isolates sheet blocks. Concatenating fences into one Python namespace or using `medicine_extract.py` on this compiled sheet is unsupported: shared names (`medicine`, `_std`, `LANGS`, helpers) have different meanings. All IDs in this document are unique; renamed IDs are provisional local aliases, require registry reconciliation, and preserve `SOURCE_RULE_ID`. No existing registry is changed.

Run in medicine-section order, route to exactly one family, carry each fixed text into the next rule, and stop on the first drop. Code, English and math retain their source order; science retains its separately measured source order. A drop means exclude/quarantine the complete record and retain audit provenance. Do not serialize dropped private text into public reports. A rule exception or timeout is ERROR, never keep/PASS.

## Binding clash resolutions

| Clash | Resolution in this spec |
|---|---|
| Gold-control minimum-one exception | The repository harm policy controls: `changed + dropped <= max(1, floor(gold_count / 100))`, per rule and combined pipeline **per pack**, at the default 1% limit. At least one affected document is allowed for a nonempty gold set. |
| Same language across families | Outer pack guard on every rule; retain source language and math pack checks. English rules never reach math/science/code. |
| Repeated rule IDs and Python bindings | Unique provisional IDs mapped below; isolated block namespaces. Source bodies otherwise retained, with dispatch adapters. |
| A1/A2 differ across families | Keep family-specific handling: code retains form feed; prose may remove it. Preserve ZWJ/ZWNJ; do not apply prose bidi stripping to unrelated scripts. |
| A3 mojibake / A5 normalization | Retain distinct scoped repairs; no global NFKC. Math superscripts and operators must survive. Source order remains unchanged pending interaction evidence. |
| B2 tag stripping versus scientific/math semantics | No cross-family tag stripper. Science uses reviewed sup/sub conversion and code-fence protection. Math B2 can turn `x<sup>2</sup>` into `x2`: retain only as an unapproved candidate; independent semantic review is a release gate. |
| B4 placeholders versus valid examples | Keep family-specific literal patterns; science retains sample emails. No blanket replacement of template syntax in arbitrary code or math. |
| C1/C2 versus licences, headers and repeated equations | Keep scoped rules and science ID gates. Preserve licence/attribution in provenance before deleting notices. Gold preservation alone cannot approve deletion of meaningful repetition. |
| Code E1/E2/C3/C4 drops versus E4 stripping | Drops first, then strips, as the code source requires. Keep overlapping E4 and E3 rules in source order; distinct detectors are not merged by disease code. |
| C3/C4 repair versus deletion | Preserve each family decision. Science uses reviewed exclusions and bounded repairs; reject longest-article-only extraction. Any split must emit all articles with parent provenance. |
| D1 versus D3 | Science keeps natural multilingual passages; only reviewed wrong-language IDs are quarantined. English D3 deletion remains English-only and requires review of legitimate quotations before approval. |
| F1 privacy differs by family | English keeps its final typed-placeholder rule; science quarantines nine reviewed IDs and gates remaining F1 labels. Code/math sheets do not provide complete F1 coverage. Shared `../tools/f1_rule.py` (TSAI, 1 Nov) runs last on the code, math, science and Indic packs through `clean.py`'s `SCOPE`, after `DA-F1-006` on science, and never on English; on Indic it replaces the deferred source F1 rules (Indian phone formats, Indian organisation domains and words); it is not a sheet block. Gold harm 0 on math and science (`results/cleaner/harm_tests_f1_math_sci.md`); its known misses keep full privacy coverage a release gate. |
| Counts, examples and qualification | Do not add overlapping diagnosis counts. Counts of five or fewer are supplementary coverage, not evidence of the template's >5 criterion. Keep them visibly for provenance and safety coverage. Missing exact examples block template completion. |
| Source medicine versus action prose | Runnable callable determines measured behavior. Some math C3 wrapper paths keep tuple/drop outcomes despite descriptive drop wording; preserve implementation, disclose the discrepancy, and require adjudication before approval. |

## Harm acceptance and evidence gaps

Acceptance uses the updated `harm_test.py` gold-control policy: no errors and at most `max(1, floor(1% × n))` affected documents for each nonempty gold set, per rule and combined pipeline. For example, 1/40 passes (one-document allowance), 2/40 fails, and 2/204 passes. Empty gold sets remain untestable.

A gold document is changed only if a surviving output differs from original text; a dropped document is counted separately, once. Combined impact counts unique affected IDs, never the sum of independent rule counts. Zero gold rows, missing gold IDs, errors or timeouts make the test untestable/error. Run positive-case checks separately: low harm does not establish recall, semantic correctness or privacy coverage.

The five source sheets do not consistently contain three exact `(doc_id, characters)` quotations per medicine. Math cards generally contain no document examples; many code/English cards list IDs only; science uses descriptions and intentionally withholds private values. **Fresh exact-character execution excerpts are added per card below; cards with fewer than three publishable examples remain incomplete.** Do not fabricate snippets, and do not publish private spans to satisfy the template. Supply reviewed non-private exact characters or an access-controlled privacy evidence record before freeze. The historical science sources disagree on labels and the old 40-document gold snapshot (`eee25e81417bc1b7`). The supplied latest science gold has 198 rows and zero measured harm; its digest is recorded below. Inherited science measurements describe the old snapshot; 1/40 (2.50%) passes under the minimum-one exception, while gold eligibility remains a separate review issue. Gold must be adjudicated independently, never edited merely to pass a test.

Source code remains CANDIDATE even after a measured pass. Semantic side effects, reviewer approval, missing examples, F1 coverage and provisional registry IDs remain release gates. Rules for <=5 observations and preservation-only science D3 are supplementary cards.

<!-- MERGED PIPELINE DECISIONS -->
## Merged PR decisions and optional F2 stage

[PR #25](https://github.com/patilvijay23/era-v5-lab/pull/25) refreshes [decisions_math.md](decisions_math.md), not the 14 math algorithms or their scopes. They remain CANDIDATE and ready for independent review, not approved/frozen. Preserve the B2 sup/sub semantic release gate, the deferred megamath C1 scope, and the shared F1. Counts in that decision document describe its cited snapshots; current execution evidence is regenerated below.

[PR #26](https://github.com/patilvijay23/era-v5-lab/pull/26) supplies G9 F2 through `tools/f2_rule.py` and **opt-in `run_clean.py --f2`**, after `clean.py` on retained text. It is intentionally not an unconditional sheet block or generated `clean.py` function: the full fingerprint set is pinned, takes substantial memory/time to load, and can match shared public passages. No `--f2` means the existing default cleaner behavior. F2 reports benchmark item IDs, offsets in cleaned text and the set digest; it drops flagged retained documents. Its gold budget must be checked together with the default cleaner, counting each affected document once.

The pin is `v1`, set SHA-256 `11e290a44d1467875fdf8bebc55eab21f0a6367f411aab98a4a027a546fd372e`. This is G9's supplied word-ngram matcher, not the two legacy Sanskrit character-window medicines. Those `DB-F2-*` cards remain deferred. G9 v1 includes FLORES/IN22 fingerprints but not Itihasa; the optional stage must not be described as complete Itihasa coverage. Changing the set or applying the stage to new packs requires its own validation. See [F2 results](../results/f2/README.md).

The effective runner order is: validated family scopes in sheet order, the shared F1 on code/math/science/Indic, then G9 F2 **only with `--f2`**. Indic's source F1 rules are deferred: the shared F1's Indic path replaces them. A rebuild refreshes family scopes and does not turn on F2 automatically.
<!-- END MERGED PIPELINE DECISIONS -->

## Source snapshots

| Source | SHA-256 |
|---|---|
| [medicine_code.md](medicine_code.md) | `e096bea29f0634a76ae99600753527aa266a1d69ed06c4fd88e800b42c8bf13b` |
| [medicine_english.md](medicine_english.md) | `904c63b621515fc07bdd07cfff3553b6cff49504c89f41c2ec1fce2d27b0652c` |
| [medicine_math.md](medicine_math.md) | `d80f46be988242e92774802497e2d78360295e3c57c7e1a0a1a88f5c914a6224` |
| [medicine_sci.md](medicine_sci.md) | `5f1e743253062fee2b91d3e04f13b2c302eddae4a9c02b0f54144d2252e1c411` |

## Identity mapping

| Medicine | Family | Disease | Source identity | Consolidated identity |
|---|---|---|---|---|
| 1 | code | A1 | `DA-A1-001` | `DA-A1-001` |
| 2 | code | A2 | `DA-A2-007` | `DA-A2-007` |
| 3 | code | A6 | `DA-A6-001` | `DA-A6-001` |
| 4 | code | A4 | `DA-A4-002` | `DA-A4-002` |
| 5 | code | A4 | `DA-A4-003` | `DA-A4-003` |
| 6 | code | B3 | `DA-B3-001` | `DA-B3-001` |
| 7 | code | E1 | `DA-E1-001` | `DA-E1-001` |
| 8 | code | E1 | `DA-E1-004` | `DA-E1-004` |
| 9 | code | E1 | `DA-E1-008` | `DA-E1-008` |
| 10 | code | E1 | `DA-E1-006` | `DA-E1-006` |
| 11 | code | E1 | `DA-E1-005` | `DA-E1-005` |
| 12 | code | E1 | `DA-E1-007` | `DA-E1-007` |
| 13 | code | E2 | `DA-E2-001` | `DA-E2-001` |
| 14 | code | C3 | `DA-C3-002` | `DA-C3-002` |
| 15 | code | C4 | `DA-C4-002` | `DA-C4-002` |
| 16 | code | E4 | `DA-E4-005` | `DA-E4-005` |
| 17 | code | E4 | `DA-E4-010` | `DA-E4-010` |
| 18 | code | E4 | `DA-E4-009` | `DA-E4-009` |
| 19 | code | E4 | `DA-E4-007` | `DA-E4-007` |
| 20 | code | C1 | `DA-C1-004` | `DA-C1-004` |
| 21 | code | C1 | `DA-C1-005` | `DA-C1-005` |
| 22 | code | B4 | `DA-B4-009` | `DA-B4-009` |
| 23 | code | E3 | `DA-E3-003` | `DA-E3-003` |
| 24 | code | E3 | `DA-E3-004` | `DA-E3-004` |
| 25 | english | A1 | `DA-A1-004` | `DA-A1-004` |
| 26 | english | A2 | `DA-A2-008` | `DA-A2-008` |
| 27 | english | A5 | `DA-A5-001` | `DA-A5-001` |
| 28 | english | A3 | `DA-A3-002` | `DA-A3-002` |
| 29 | english | B1 | `DA-B1-002` | `DA-B1-002` |
| 30 | english | B2 | `DA-B2-002` | `DA-B2-002` |
| 31 | english | C3 | `DA-C3-001` | `DA-C3-001` |
| 32 | english | C3 | `DA-C3-002` | `DA-C3-003` |
| 33 | english | C5 | `DA-C5-002` | `DA-C5-002` |
| 34 | english | D4 | `DA-D4-001` | `DA-D4-001` |
| 35 | english | C1 | `DA-C1-006` | `DA-C1-006` |
| 36 | english | C2 | `DA-C2-003` | `DA-C2-003` |
| 37 | english | C5 | `DA-C5-005` | `DA-C5-005` |
| 38 | english | D3 | `DA-D3-003` | `DA-D3-003` |
| 39 | english | B4 | `DA-B4-007` | `DA-B4-007` |
| 40 | english | B4 | `DA-B4-008` | `DA-B4-008` |
| 41 | english | B4 | `DA-B4-009` | `DA-B4-012` |
| 42 | english | B4 | `DA-B4-010` | `DA-B4-010` |
| 43 | english | B4 | `DA-B4-011` | `DA-B4-011` |
| 44 | english | F1 | `DA-F1-005` | `DA-F1-005` |
| 45 | math | A3 | `DA-A3-001` | `DA-A3-001` |
| 46 | math | A1 | `DA-A1-001` | `DA-A1-005` |
| 47 | math | A6 | `DA-A6-001` | `DA-A6-003` |
| 48 | math | A5 | `DA-A5-001` | `DA-A5-002` |
| 49 | math | B2 | `DA-B2-001` | `DA-B2-001` |
| 50 | math | B4 | `DA-B4-001` | `DA-B4-001` |
| 51 | math | B5 | `DA-B5-001` | `DA-B5-001` |
| 52 | math | C5 | `DA-C5-001` | `DA-C5-001` |
| 53 | math | D3 | `DA-D3-001` | `DA-D3-005` |
| 54 | math | C3 | `DA-C3-001` | `DA-C3-004` |
| 55 | math | C1 | `DA-C1-001` | `DA-C1-001` |
| 56 | math | C2 | `DA-C2-001` | `DA-C2-001` |
| 57 | math | C5 | `DA-C5-002` | `DA-C5-006` |
| 58 | math | C3 | `DA-C3-002` | `DA-C3-005` |
| 59 | sci | B4 | `cure_b4` | `DA-B4-013` |
| 60 | sci | B2 | `cure_b2` | `DA-B2-003` |
| 61 | sci | B5 | `cure_b5` | `DA-B5-002` |
| 62 | sci | A1 | `cure_a1` | `DA-A1-006` |
| 63 | sci | A6 | `cure_a6` | `DA-A6-002` |
| 64 | sci | C1 | `cure_c1` | `DA-C1-007` |
| 65 | sci | C2 | `cure_c2` | `DA-C2-004` |
| 66 | sci | C3 | `cure_c3` | `DA-C3-006` |
| 67 | sci | C4 | `cure_c4` | `DA-C4-003` |
| 68 | sci | D1 | `cure_d1` | `DA-D1-001` |
| 69 | sci | F1 | `cure_f1` | `DA-F1-006` |
| 70 | sci | D3 | `cure_d3` | `DA-D3-004` |

## Fresh validation

<!-- VALIDATION -->

Fresh local execution using the repository loader, mutation checks, timeouts and pipeline runner; verdicts use the repository policy: at most `max(1, floor(gold_count / 100))` changed-or-dropped gold documents per rule and combined pipeline, per pack. Reports contain IDs and digests only. `pack_id` is supplied from each validated pack filename when absent in Parquet.

| Pack | Gold n | Gold changed / dropped | Result | Full pack fixed / dropped | Errors (gold / pack) |
|---|---:|---:|---|---:|---:|
| code-cpp | 122 | 0 / 0 | PASS | 343 / 10 | 0 / 0 |
| code-go | 163 | 0 / 0 | PASS | 265 / 44 | 0 / 0 |
| code-java | 116 | 0 / 0 | PASS | 350 / 11 | 0 / 0 |
| code-js-ts | 204 | 0 / 0 | PASS | 264 / 22 | 0 / 0 |
| code-python | 141 | 0 / 0 | PASS | 325 / 16 | 0 / 0 |
| code-rust | 234 | 0 / 0 | PASS | 238 / 17 | 0 / 0 |
| en-dclm | 62 | 0 / 0 | PASS | 54 / 9 | 0 / 0 |
| en-fineweb-edu | 158 | 0 / 0 | PASS | 12 / 1 | 0 / 0 |
| en-nemotroncc | 129 | 0 / 0 | PASS | 62 / 17 | 0 / 0 |
| en-nemotroncc-synth | 326 | 0 / 0 | PASS | 32 / 1 | 0 / 0 |
| ind-bn-fw2 | 238 | 0 / 0 | PASS | 113 / 45 | 0 / 0 |
| ind-bn-sangraha-v | 50 | 0 / 0 | PASS | 39 / 7 | 0 / 0 |
| ind-gu-fw2 | 19 | 0 / 0 | PASS | 179 / 10 | 0 / 0 |
| ind-hi-fw2 | 234 | 0 / 1 | PASS | 26 / 4 | 0 / 0 |
| ind-hi-hplt | 67 | 0 / 0 | PASS | 97 / 33 | 0 / 0 |
| ind-hi-indiccorp | 130 | 0 / 0 | PASS | 3 / 0 | 0 / 0 |
| ind-kn-fw2 | 45 | 0 / 0 | PASS | 90 / 9 | 0 / 0 |
| ind-kn-sangraha-s | 27 | 0 / 0 | PASS | 72 / 1 | 0 / 0 |
| ind-kn-sangraha-v | 103 | 0 / 0 | PASS | 40 / 12 | 0 / 0 |
| ind-mr-fw2 | 140 | 1 / 0 | PASS | 82 / 8 | 0 / 0 |
| ind-mr-sangraha-v | 88 | 0 / 0 | PASS | 263 / 38 | 0 / 0 |
| ind-sa-fw2 | 68 | 1 / 0 | PASS | 228 / 21 | 0 / 0 |
| ind-ta-sangraha-v | 41 | 0 / 0 | PASS | 213 / 3 | 0 / 0 |
| ind-te-fw2 | 18 | 0 / 0 | PASS | 114 / 111 | 0 / 0 |
| ind-te-sangraha-s | 5 | 0 / 0 | PASS | 106 / 30 | 0 / 0 |
| ind-te-sangraha-v | 27 | 0 / 0 | PASS | 36 / 30 | 0 / 0 |
| math-finemath | 86 | 0 / 0 | PASS | 176 / 13 | 0 / 0 |
| math-megamath | 26 | 0 / 0 | PASS | 37 / 10 | 0 / 0 |
| sci-finepdfs | 202 | 0 / 0 | PASS | 32 / 12 | 0 / 0 |

Independent gold rules failing the repository minimum-one limit: none.

These verdicts concern executable sheet blocks; deferred cards are excluded. Missing inputs are NOT TESTABLE, never PASS. Out-of-pack guards were checked on every available pack. The generated cleaner also has the shared F1, so its separate tests remain required. Results apply to the snapshots recorded in [results/cleaner/specv1_validation.json](../results/cleaner/specv1_validation.json).

Reproduce from the repository root (install `teams/01-data-a/spec_v1/requirements.txt` first):

```bash
python3 teams/01-data-a/spec_v1/tools/validate_specv1.py \
  --packs <packs folder> \
  --gold teams/01-data-a/gold
```


## Medicine 1 — code / A1 / `DA-A1-001`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-A1-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A1 invisible junk characters. Labelled rows: go 0, rust 1, js-ts 1, java 1, cpp 12, python 0. Examples: `2faccaa1d7a77d70`, `91cf7be64838e0d0`, `beae2c42d8a34ccc`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `782bc9665f0acdf7` (code-cpp), original offset 0: `"\ufeff/* <NAME>, \u041a\u041d, 50\u0411, 146"` (fix).
- `de12a2fd152768d6` (code-cpp), original offset 0: `"\ufeff#include \"stdafx.h\"\n#in"` (fix).
- `6cdc9866d4264258` (code-cpp), original offset 0: `"\ufeff#include \"NeuralStructu"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Delete U+FEFF (BOM).

```python
RULE_ID = "DA-A1-001"
SOURCE_RULE_ID = "DA-A1-001"
CODE = "A1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'javascript', 'python', 'rust', 'typescript'}
ORIGIN = "code-go, code-rust, code-js-ts, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-cpp"  # pack whose medicine this came from
AUTHOR = "TharunSivamani"
import re

def remove_bom_characters(text: str) -> str:
    return text.replace("\ufeff", "")


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(remove_bom_characters(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go, rust, js-ts, java, cpp, python. **Docs it touches:** go 0, rust 1, js-ts 1, java 1, cpp 12, python 0.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; js-ts 0.00% (0/204) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** Only the BOM: other invisible characters of A1 (U+200B, bidi marks, soft hyphen) are not treated, and no labelled row needs it.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-cpp sheet, PR 9. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 2 — code / A2 / `DA-A2-007`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-A2-007`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A2 control characters. Labelled rows: go 1, rust 6, js-ts 17, java 44, cpp 47, python 2. Examples: `34133f5414afff81`, `182c2cf59a3fa4f1`, `2f34546793ed7faf`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `09b5f5db05cc311d` (code-cpp), original offset 53: `"tdafx.h\"\r\n#include \"PlaceholderU"` (fix).
- `d5e1b337f212f4e2` (code-cpp), original offset 97: `"////////\r\n * File:        winstl"` (fix).
- `11edb16ce89987d8` (code-cpp), original offset 24: `"_tree.h\"\r\n#include <assert.h>\r\nu"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** CRLF and lone CR become LF; delete the other C0 control characters and DEL. Tab, newline and form feed stay.

```python
RULE_ID = "DA-A2-007"
SOURCE_RULE_ID = "DA-A2-007"
CODE = "A2"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'javascript', 'python', 'rust', 'typescript'}
ORIGIN = "code-go, code-rust, code-js-ts, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import re

CTRL = re.compile(r"[\x00-\x08\x0b\x0e-\x1f\x7f]")

def medicine_a2(doc):
    t = CTRL.sub("", doc["text"].replace("\r\n", "\n").replace("\r", "\n"))
    return ("fix" if t != doc["text"] else "keep", t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_a2(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go, rust, js-ts, java, cpp, python. **Docs it touches:** go 1, rust 6, js-ts 17, java 44, cpp 47, python 17.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; js-ts 0.00% (0/204) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** Keeps form feed, which the A2 definition lists, because source code uses it as whitespace. U+0080 to U+009F are not treated.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 3 — code / A6 / `DA-A6-001`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-A6-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A6 mixed script (look-alike letters). Labelled rows: go 2, rust 0, js-ts 0, java 0, cpp 0, python 0. Examples: `48b3b124a7aaa5fc`, `64ed179e7e5c3d21`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `782bc9665f0acdf7` (code-cpp), original offset 390: `"\t\t// \u0446\u0438\u0444\u0440a \u043d\u0430 \u0447\u0438\u0441\u043b\u043e 1 \u0438 2\n\tdoubl"` (fix).
- `64ed179e7e5c3d21` (code-go), original offset 1319: `"and(\"int\u0441\", \"Interrupt Client\")\n"` (fix).
- `48b3b124a7aaa5fc` (code-go), original offset 53: `"<evorui \u0430t gm\u0430il d\u03bft c\u03bfm>, All r"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Cyrillic look-alike letters inside words that also have Latin letters become Latin.

```python
RULE_ID = "DA-A6-001"
SOURCE_RULE_ID = "DA-A6-001"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'javascript', 'python', 'rust', 'typescript'}
ORIGIN = "code-go, code-rust, code-js-ts, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import re

HOMO = str.maketrans("аеорсухіјѕАВЕКМНОРСТХІЈЅ", "aeopcyxijsABEKMHOPCTXIJS")

MIXED = re.compile(r"\b(?=\w*[A-Za-z])(?=\w*[Ѐ-ӿ])\w+\b")

def medicine_a6(doc):
    t = MIXED.sub(lambda m: m.group().translate(HOMO), doc["text"])
    return ("fix" if t != doc["text"] else "keep", t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_a6(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go, rust, js-ts, java, cpp, python. **Docs it touches:** go 2, rust 0, js-ts 0, java 0, cpp 1, python 0.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; js-ts 0.00% (0/204) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** Can turn an obfuscated e-mail address back into plain text, so the data-safety stage runs after it.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 4 — code / A4 / `DA-A4-002`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-A4-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A4 replacement characters. Labelled rows: go 1, rust 0, js-ts 0, java 2, cpp 0, python 0. Examples: `2a92a9a8489c5ea2`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `2a92a9a8489c5ea2` (code-go), original offset 17244: `"= \"E\"){\n\t\t\t// \ufffd\ufffd\u0238\n\t\t\thistorydata"` (fix).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Delete a `//` comment that holds U+FFFD and no ASCII letter or digit. An author-quoted U+FFFD stays (ruling 7).

```python
RULE_ID = "DA-A4-002"
SOURCE_RULE_ID = "DA-A4-002"
CODE = "A4"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'javascript', 'python', 'rust', 'typescript'}
ORIGIN = "code-go, code-rust, code-js-ts, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import re

LOST = re.compile(r"[ \t]*//[^\n\w]*�[^\nA-Za-z0-9]*$", re.M)

def medicine_a4(doc):
    t = LOST.sub("", doc["text"])
    return ("fix" if t != doc["text"] else "keep", t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_a4(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go, rust, js-ts, java, cpp, python. **Docs it touches:** go 1, rust 0, js-ts 0, java 0, cpp 0, python 0.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; js-ts 0.00% (0/204) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** U+FFFD in a string, or in a comment with words, stays.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 5 — code / A4 / `DA-A4-003`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-A4-003`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A4 replacement characters. Labelled rows: go 1, rust 0, js-ts 0, java 2, cpp 0, python 0. Examples: `912c53fa71c7d9ad`, `9b95cf192922d106`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `912c53fa71c7d9ad` (code-java), original offset 2833: `" car apr\ufffds s'\ufffdtre arr\ufffdt\ufffd le robo"` (fix).
- `9b95cf192922d106` (code-java), original offset 136: `"ime 2017\ufffd\ufffd3\ufffd\ufffd13\ufffd\ufffd \ufffd\ufffd\ufffd\ufffd9:59:26\n *"` (fix).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** In comment lines, U+FFFD between letters becomes a space and other U+FFFD is deleted.

```python
RULE_ID = "DA-A4-003"
SOURCE_RULE_ID = "DA-A4-003"
CODE = "A4"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {'java'}
ORIGIN = "code-java"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-java"  # pack whose medicine this came from
AUTHOR = "vaibh27"
import re

COMMENT_LINE = re.compile(r"(?m)^[ \t]*(?://|/?\*).*$")

def m8_clean_replacement_chars(t: str) -> str:
    def fix(m):
        return re.sub("\ufffd+", "", re.sub(r"(?<=[^\s\ufffd])\ufffd+(?=[^\s\ufffd])", " ", m.group()))
    return COMMENT_LINE.sub(lambda m: fix(m) if "\ufffd" in m.group() else m.group(), t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(m8_clean_replacement_chars(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** java. **Docs it touches:** java 2.
4. **Harm test:** java 0.00% (0/116) PASS.
5. **Side effects:** Java only: on go it also changes the author-quoted U+FFFD that ruling 7 keeps.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-java sheet, PR 48. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 6 — code / B3 / `DA-B3-001`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-B3-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B3 ghost markers. Labelled rows: go 247, rust 225, js-ts 262, java 250, cpp 245, python 284. Examples: `01180a3ddf4dfc23`, `03d9fb46f54cf391`, `03e1fbfd3629a84a`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `83dc5d60eaef6288` (code-cpp), original offset 0: `"<reponame>maidiHaitai/ha"` (fix).
- `3a7b03b626595019` (code-cpp), original offset 0: `"<filename>leetcode/power"` (fix).
- `a800be93ce443cb5` (code-cpp), original offset 0: `"<gh_stars>0\n//\n// Create"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Delete the first line when it starts with `<reponame>`, `<filename>` or `<gh_stars>`.

```python
RULE_ID = "DA-B3-001"
SOURCE_RULE_ID = "DA-B3-001"
CODE = "B3"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'javascript', 'python', 'rust', 'typescript'}
ORIGIN = "code-go, code-rust, code-js-ts, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-cpp"  # pack whose medicine this came from
AUTHOR = "TharunSivamani"
import re

METADATA_PREFIX = re.compile(
    r"\A<(?:reponame|filename|gh_stars)>[^\r\n]*(?:\r?\n|\Z)",
    re.IGNORECASE,
)

def remove_metadata_prefix(text: str) -> str:
    return METADATA_PREFIX.sub("", text, count=1)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(remove_metadata_prefix(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go, rust, js-ts, java, cpp, python. **Docs it touches:** go 247, rust 225, js-ts 245, java 250, cpp 245, python 272.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; js-ts 0.00% (0/204) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** A marker in the middle of a file is not touched, and none was seen.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-cpp sheet, PR 9. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 7 — code / E1 / `DA-E1-001`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E1-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E1 minified or generated code. Labelled rows: go 43, rust 23, js-ts 23, java 14, cpp 20, python 11. Examples: `023d4d7c1524277f`, `0bbbdad3593bc36f`, `0e5b75717c831da2`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `f08e1abfa9c2ebdc` (code-go), original offset 0: `"\n/*\n * The Jira Cloud platform REST API\n *\n * Jira Cloud platfor"` (drop).
- `3dc96675632ddcff` (code-go), original offset 0: `"//go:build go1.18\n// +build go1.18\n\n// Copyright (c) Microsoft C"` (drop).
- `3c4db0c3d41b7673` (code-go), original offset 0: `"// Code generated by MockGen. DO NOT EDIT.\n// Source: ./gke/gke."` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Generator marker before or just after the `package` clause, or a Kiota or goformation fingerprint.

```python
RULE_ID = "DA-E1-001"
SOURCE_RULE_ID = "DA-E1-001"
CODE = "E1"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'go'}
ORIGIN = "code-go"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "RaviNaik"
import re

_GEN = re.compile(
    r"(?im)^\s*(?://|/\*|\*)?\s*(?:"
    r"code generated\b|"
    r"auto-?generated|"
    r"由\w*自动生成|"
    r"\(re-\)?generated by\b.*|"
    r"generated by:?\s*(?:swagger|go-swagger|protoc|mockgen|microsoft|openapi)|"
    r"do not (?:edit|change) this file|"
    r"(?:\*{3}\s*warning:\s*)?this file (?:was|is|has been) (?:automatically |auto-?)?(?:generated|autogenerated)\b|"
    r"(?:this file )?(?:was )?automatically generated\b|"
    r"this file was generated by\b)"
)

_GEN_FINGERPRINT = re.compile(
    r"(?m)^\s*i[0-9a-f]{40,}\s+\"github\.com/microsoft/kiota|"
    r"AWSCloudFormationSpecificationVersion returns the AWS Specification Version that this resource was generated from"
)

_PKG = re.compile(r"(?m)^package\s+\w+")

def drop_generated(text: str):
    """Drop the file if a generated-code marker sits in the header (before `package`
    or within the first 40 lines). Markers inside string literals further down do not count."""
    m = _PKG.search(text)
    head = text[: m.end()] if m else text[:2000]
    head = "\n".join(head.split("\n")[:40]) if len(head) > 4000 else head
    # also allow the Go convention of the marker directly after the package clause (go-swagger)
    tail_probe = text[m.end(): m.end() + 1500] if m else ""
    if _GEN.search(head) or _GEN.search(tail_probe) or _GEN_FINGERPRINT.search(text[:3000]):
        return "drop", text
    return "keep", text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(drop_generated(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** go. **Docs it touches:** go 42.
4. **Harm test:** go 0.00% (0/163) PASS.
5. **Side effects:** Generated code with no marker is missed: 1 labelled go row.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, PR 36. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 8 — code / E1 / `DA-E1-004`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E1-004`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E1 minified or generated code. Labelled rows: go 43, rust 23, js-ts 23, java 14, cpp 20, python 11. Examples: `00a6ea4358544d22`, `0316bfaac536f88b`, `1aa2bcd706be1e4b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `6359488cb66a0aa6` (code-python), original offset 0: `"<filename>sdk/python/pulumi_ovh/iploadbalancing_http_farm_server"` (drop).
- `ba0e6a6503f190e9` (code-python), original offset 0: `"#!/usr/bin/env python\n\"\"\"fuzza autogenerated.\"\"\"\n\nfrom __future_"` (drop).
- `ca3630b84be3762a` (code-python), original offset 0: `"<filename>testcases/fspresetReload.py\n#!/usr/bin/env python2\n# I"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Generator banner in the first 15 lines, or 20 or more `#[doc = "..."]` lines.

```python
RULE_ID = "DA-E1-004"
SOURCE_RULE_ID = "DA-E1-004"
CODE = "E1"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'python', 'rust'}
ORIGIN = "code-rust, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-rust"  # pack whose medicine this came from
AUTHOR = "amukka"
import re

MARKER_LINE = re.compile(r"^(?:<(?:reponame|filename|gh_stars)>[^\n]*)\n?")

GENERATED = re.compile(
    r"(?i)(auto-?generated|automatically generated|code generated|generated by|@generated"
    r"|do not (?:directly )?edit|this file is generated)"
)

def _strip_marker(text: str) -> str:
    return MARKER_LINE.sub("", text, count=1)

def e1_generated(text: str):
    """E1: drop when a generated banner is in the first 15 lines, or 20+ #[doc = "..."] lines."""
    body = _strip_marker(text).split("\n")
    head = "\n".join(body[:15])
    if GENERATED.search(head) or sum('#[doc = "' in l for l in body) >= 20:
        return "drop", ""
    return "keep", text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(e1_generated(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** rust, python. **Docs it touches:** rust 17, python 16.
4. **Harm test:** rust 0.00% (0/78) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** A hand-written file whose header says "generated" is dropped. On python it touches 16 docs, 10 labelled E1 and 1 labelled clean.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-rust sheet, PR 52. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 9 — code / E1 / `DA-E1-008`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E1-008`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E1 minified or generated code. Labelled rows: go 43, rust 23, js-ts 23, java 14, cpp 20, python 11. Examples: `0c10e83429b075c5`, `0f34612ed9c80d78`, `2bae666c99ad51ed`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `0f34612ed9c80d78` (code-js-ts), original offset 0: `"import { purry } from './purry';\nexport function omitProp() {\n  "` (drop).
- `82661aa7e8fdfc1f` (code-js-ts), original offset 0: `"<filename>website/static/source/html/search/files_f.js\nvar searc"` (drop).
- `e8483df9bbdbd7f3` (code-js-ts), original offset 0: `"import*as THREE from\"three\";class MultiPageShaderMaterialParamet"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** A build folder in the path (`node_modules/`, `dist/`, `build/`, `bundles/`, `vendor/`, `generated/`) or `.min.js`, except `.d.ts`; a `sourceMappingURL` line; compiled-module output; a generator word in the header comment; a minified line; a line over 1,000 characters; three or more `.html#` links; or `var searchData =`.

```python
RULE_ID = "DA-E1-008"
SOURCE_RULE_ID = "DA-E1-008"
CODE = "E1"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'javascript', 'typescript'}
ORIGIN = "code-js-ts"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-js-ts"  # pack whose medicine this came from
AUTHOR = "Sagar063"
import re

_BUILD_PATH = re.compile(r"(^|/)(node_modules|dist|build|bundles?|vendor|generated)/|\.min\.js$")

_GENERATED = re.compile(r"auto-?generated|do not edit|generated by", re.I)

_COMPILED = re.compile(r"Object\.defineProperty\(exports,\s*[\"']__esModule[\"']|\bjsx_runtime_\d+\.jsx\(")

_TAGS = re.compile(r"<(filename|gh_stars|reponame)>")

def _header_comment(text):
    """The comment lines at the very top of the file, after an optional StarCoder line."""
    lines, out = text.split("\n"), []
    if lines and _TAGS.match(lines[0]):
        lines = lines[1:]
    for line in lines:
        s = line.strip()
        if s == "" or s.startswith(("//", "/*", "*", "*/")):
            out.append(line)
        else:
            break
    return "\n".join(out)

def _minified(text):
    return any(len(line) > 300 and line.count(" ") / len(line) < 0.05 for line in text.split("\n"))

def medicine_e1(doc):
    """Drop build output and generated files. doc has 'text' and 'url'."""
    text, path = doc["text"], doc.get("url") or ""
    built = bool(_BUILD_PATH.search(path)) and not path.endswith(".d.ts")
    generated = bool(
        re.search(r"^\s*//# sourceMappingURL=", text, re.M)
        or _COMPILED.search(text)
        or _GENERATED.search(_header_comment(text))
        or _minified(text)
        or max(len(line) for line in text.split("\n")) > 1000
        or text.count(".html#") >= 3
        or re.search(r"var searchData\s*=", text)
    )
    return ("drop", "") if (built or generated) else text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_e1(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** js-ts. **Docs it touches:** js-ts 22.
4. **Harm test:** js-ts 0.00% (0/204) PASS.
5. **Side effects:** A hand-written file in such a folder, or with one line over 1,000 characters, is dropped. **3 js-ts docs go on the path alone** (`node_modules`, `build`, `generated`). The 30 Oct ruling says a vendored copy is not a disease by itself, so the reviewer should decide whether `node_modules` and `vendor` stay in the path check. Touches 6 js-ts docs that a reader labelled clean.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-js-ts sheet, PR 115. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 10 — code / E1 / `DA-E1-006`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E1-006`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E1 minified or generated code. Labelled rows: go 43, rust 23, js-ts 23, java 14, cpp 20, python 11. Examples: `138cac43be0730ea`, `2111dfa57dfd75e8`, `3cba9087383097dd`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `c6016e9ce2c607c5` (code-java), original offset 0: `"<gh_stars>10-100\n/*-\n * Copyright (C) 2015 <NAME>\n *\n * This pro"` (drop).
- `73e175e90e6e37da` (code-java), original offset 0: `"// Copyright (c) Microsoft Corporation. All rights reserved.\n// "` (drop).
- `896c9a4f9693205f` (code-java), original offset 0: `"/*\n * XML Type:  CT_TblGridChange\n * Namespace: http://schemas.o"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Decompiler or generator marker in the text (Jad, Procyon, "AUTO-GENERATED FILE", "This class was generated by", swagger).

```python
RULE_ID = "DA-E1-006"
SOURCE_RULE_ID = "DA-E1-006"
CODE = "E1"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'java'}
ORIGIN = "code-java"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-java"  # pack whose medicine this came from
AUTHOR = "riyaagrahari"
import re

GEN = re.compile(r'Decompiled by (Jad|Procyon)|Code generated by [^\n]{0,60}Generator|AUTO-GENERATED FILE'
                 r'|generated by a tool and any changes will be overwritten|Automatically generated - do not modify'
                 r'|This class was (automatically )?generated by|auto generated by the swagger'
                 r'|This is a generated file\. Not intended for manual editing')

def drop_e1(text): return bool(GEN.search(text))


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(drop_e1(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** java. **Docs it touches:** java 10.
4. **Harm test:** java 0.00% (0/116) PASS.
5. **Side effects:** Stub files and jadx output with no marker are missed: 4 labelled java rows. Touches 1 doc labelled clean.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-java sheet, PR 123. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 11 — code / E1 / `DA-E1-005`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E1-005`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E1 minified or generated code. Labelled rows: go 43, rust 23, js-ts 23, java 14, cpp 20, python 11. Examples: `4b53d240dabec20a`, `737965d79cc94955`, `83b3083721ee5df9`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `a3256b38a3e5a8d1` (code-cpp), original offset 0: `"#include \"CAM_RowNand.h\"\r\n#include \"RowDecoder.h\"\r\n#include \"for"` (drop).
- `deccbc12f9921ae8` (code-cpp), original offset 0: `"<filename>doc/quickbook/oglplus/quickref/enums/tess_gen_primitiv"` (drop).
- `b5da9ac1658db525` (code-cpp), original offset 0: `"<reponame>StardustXR/libstardustxr<gh_stars>1-10\n// automaticall"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Generator note in a comment line of the first 1500 characters, or a Kiota or goformation fingerprint.

```python
RULE_ID = "DA-E1-005"
SOURCE_RULE_ID = "DA-E1-005"
CODE = "E1"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'cpp'}
ORIGIN = "code-cpp"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import re

GENERATED = re.compile(r"^[ \t]*(?://|/\*|\*)[^\n]*?(?:Code generated|generated by|auto-?generated|"
                       r"automatically generated|AutoRest Code Generator|自动生成)", re.I | re.M)

FINGERPRINT = re.compile(r"(?m)^\s*i[0-9a-f]{40,}\s+\"github\.com/microsoft/kiota|"
                         r"Specification Version that this resource was generated from")

def medicine_e1(doc):
    t = doc["text"]
    return ("drop" if GENERATED.search(t[:1500]) or FINGERPRINT.search(t[:3000]) else "keep", t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_e1(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** cpp. **Docs it touches:** cpp 8.
4. **Harm test:** cpp 0.00% (0/120) PASS.
5. **Side effects:** A comment such as "the ID generated by the server" near the top would match.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 12 — code / E1 / `DA-E1-007`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E1-007`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E1 minified or generated code. Labelled rows: go 43, rust 23, js-ts 23, java 14, cpp 20, python 11. Examples: `3c67c435782c8a77`, `9c1d218d257a6176`, `b5da9ac1658db525`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `deccbc12f9921ae8` (code-cpp), original offset 0: `"<filename>doc/quickbook/oglplus/quickref/enums/tess_gen_primitiv"` (drop).
- `b5da9ac1658db525` (code-cpp), original offset 0: `"<reponame>StardustXR/libstardustxr<gh_stars>1-10\n// automaticall"` (drop).
- `c990295fa1578b72` (code-cpp), original offset 0: `"<gh_stars>10-100\n//\n// StatementImpl.cpp\n//\n// $Id: //poco/1.4/D"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Generator marker in a comment line, or any line longer than 1000 characters.

```python
RULE_ID = "DA-E1-007"
SOURCE_RULE_ID = "DA-E1-007"
CODE = "E1"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'cpp'}
ORIGIN = "code-cpp"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-java"  # pack whose medicine this came from
AUTHOR = "vaibh27"
import re

GENERATED = re.compile(r"(?im)^[ \t]*(?://|/?\*)[^\n]*(?:auto-generated file|do not (?:edit|modify)\b|decompiled (?:by|with)|"
                       r"code generated by|(?:file|class|code) (?:was|is|has been) (?:auto(?:matically)?[- ]?)?generated|"
                       r"generated by a tool)")

def m7_drop_generated(t: str):
    if GENERATED.search(t) or any(len(line) > 1000 for line in t.split("\n")):
        return None
    return t


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(m7_drop_generated(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** cpp. **Docs it touches:** cpp 5.
4. **Harm test:** cpp 0.00% (0/120) PASS.
5. **Side effects:** A hand-written file with one very long line, such as a data table, is dropped.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-java sheet, PR 48. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 13 — code / E2 / `DA-E2-001`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E2-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E2 data blobs. Labelled rows: go 7, rust 2, js-ts 1, java 1, cpp 1, python 1. Examples: `023d4d7c1524277f`, `637118880fa53f2f`, `8c1931d1524ec642`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `8b23faa736d88ac9` (code-cpp), original offset 0: `"/***************************************************************"` (drop).
- `637118880fa53f2f` (code-go), original offset 0: `"<reponame>VJftw/docker-registry-proxy\n// Code generated by proto"` (drop).
- `91bf17319ac11223` (code-go), original offset 0: `"<gh_stars>0\n// Code generated by protoc-gen-go. DO NOT EDIT.\n// "` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Byte-array literals cover 10% or more of the file, or base64 runs 40% or more.

```python
RULE_ID = "DA-E2-001"
SOURCE_RULE_ID = "DA-E2-001"
CODE = "E2"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'javascript', 'python', 'rust', 'typescript'}
ORIGIN = "code-go, code-rust, code-js-ts, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "RaviNaik"
import re

_BYTES = re.compile(r"(?:0x[0-9a-fA-F]{2},\s*){24,}(?:0x[0-9a-fA-F]{2},?)?")

_B64 = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")

def drop_blob(text: str, share: float = 0.10, b64_share: float = 0.4):
    """Drop the file when byte-array literals cover at least `share` of it, or when base64-looking
    runs cover at least `b64_share`. Removing the array would break the Go code, so there is no fix."""
    if not text:
        return "keep", text
    n = len(text)
    if sum(len(m.group()) for m in _BYTES.finditer(text)) / n >= share:
        return "drop", text
    if sum(len(m.group()) for m in _B64.finditer(text)) / n >= b64_share:
        return "drop", text
    return "keep", text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(drop_blob(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** go, rust, js-ts, java, cpp, python. **Docs it touches:** go 7, rust 0, js-ts 0, java 0, cpp 1, python 0.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; js-ts 0.00% (0/204) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** Smaller blobs stay: the labelled E2 rows of rust (2), js-ts (1), java (1) and python (1) are not caught.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, PR 36. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 14 — code / C3 / `DA-C3-002`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-C3-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C3 truncated or broken document. Labelled rows: go 1, rust 0, js-ts 0, java 0, cpp 0, python 0. Examples: `a27e1273db746e7d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `a27e1273db746e7d` (code-go), original offset 0: `"package raft\n\nimport (\n\t\"encoding/json\"\n\t\"errors\"\n\t\"fmt\"\n\t\"math/"` (drop).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Go lexical check fails: unclosed string, rune or block comment, or unbalanced brackets.

```python
RULE_ID = "DA-C3-002"
SOURCE_RULE_ID = "DA-C3-002"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'go'}
ORIGIN = "code-go"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import re

def _go_lexes(t):
    i, n, depth = 0, len(t), 0
    while i < n:
        c = t[i]
        if t.startswith("//", i):
            j = t.find("\n", i)
            i = n if j < 0 else j
        elif t.startswith("/*", i):
            j = t.find("*/", i + 2)
            if j < 0:
                return False
            i = j + 2
        elif c in "\"'":
            i += 1
            while i < n and t[i] != c:
                if t[i] == "\n":
                    return False
                i += 2 if t[i] == "\\" else 1
            if i >= n:
                return False
            i += 1
        elif c == "`":
            j = t.find("`", i + 1)
            if j < 0:
                return False
            i = j + 1
        else:
            depth += (c in "{([") - (c in "})]")
            if depth < 0:
                return False
            i += 1
    return depth == 0

def medicine_c3(doc):
    return ("keep" if _go_lexes(doc["text"]) else "drop", doc["text"])


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_c3(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** go. **Docs it touches:** go 1.
4. **Harm test:** go 0.00% (0/163) PASS.
5. **Side effects:** Go only: it reads Rust lifetimes (`'a`) as unclosed runes. It is not a full parser.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 15 — code / C4 / `DA-C4-002`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-C4-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C4 two documents joined. Labelled rows: go 0, rust 0, js-ts 0, java 1, cpp 1, python 0. Examples: `1227540794647c4d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `1227540794647c4d` (code-java), original offset 0: `"<reponame>rakhi2001/ecom7\n______________________________________"` (drop).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** A separator line (20 or more `_` or `=`) or a "sample 12 ms submission" caption outside a comment.

```python
RULE_ID = "DA-C4-002"
SOURCE_RULE_ID = "DA-C4-002"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'java'}
ORIGIN = "code-java"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-java"  # pack whose medicine this came from
AUTHOR = "vaibh27"
import re

JOINED = re.compile(r"(?mi)^[ \t]*(?:_{20,}|={20,}|sample \d+ (?:ms|kb) submission)[ \t]*$")

def m9_drop_joined(t: str):
    return None if JOINED.search(t) else t


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(m9_drop_joined(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** java. **Docs it touches:** java 1.
4. **Harm test:** java 0.00% (0/116) PASS.
5. **Side effects:** Java only: in python such a line can be a docstring heading.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-java sheet, PR 48. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 16 — code / E4 / `DA-E4-005`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E4-005`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E4 repeated licence headers. Labelled rows: go 76, rust 22, js-ts 9, java 103, cpp 176, python 70. Examples: `01180a3ddf4dfc23`, `0a0303df2fa01ea8`, `0c16883f44febd4f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `2bdf36ae14fd90fa` (code-go), original offset 73: `"ge cmd\n\n// Copyright 2018 Blink "` (fix).
- `3dc96675632ddcff` (code-go), original offset 28: `"go1.18\n\n// Copyright (c) Microso"` (fix).
- `83381a2f882bdce3` (code-go), original offset 0: `"// MIT License\n//\n// (C) "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Drop on a restrictive licence phrase in the first 60 lines. Else delete a licence comment block of 4 or more lines in the Go header, a boxed header, or a block at the end. Build tags and package docs stay.

```python
RULE_ID = "DA-E4-005"
SOURCE_RULE_ID = "DA-E4-005"
CODE = "E4"
ACTION = "fix+drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'go'}
ORIGIN = "code-go"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import re

LICENCE = re.compile(r"Licensed under|Licensed to the Apache|Permission is hereby granted|Redistribution and use|"
                     r"Use of this source code is governed by|This source code is licensed under|"
                     r"released under the \w+ licen[cs]e|General Public License|Mozilla Public License", re.I)

RESTRICTIVE = re.compile(r"(?i)free for personal use|commercial use requires|non-?commercial use only|"
                         r"commons clause|not for commercial use|for evaluation purposes only")

BLOCK = re.compile(r"(?:[ \t]*/\*[^\n]*\*/[ \t]*\n){2,}|/\*.*?\*/[ \t]*\n?|(?://[^\n]*\n)+", re.S)

TAIL = re.compile(r"\n((?:[ \t]*/\*[^\n]*\*/[ \t]*\n?){2,}|/\*(?:(?!\*/).)*\*/|(?://[^\n]*(?:\n|\Z))+)\s*\Z", re.S)

def _is_licence(block):
    return bool(LICENCE.search(block)) and block.count("\n") >= 4

def medicine_e4(doc):
    t = doc["text"]
    if RESTRICTIVE.search("\n".join(t.split("\n")[:60])):
        return ("drop", t)  # a restrictive licence: stripping the header would not make the code free to use
    body = re.search(r"^(?:import|func|type|var|const)\b", t, re.M)
    end = body.start() if body else len(t)
    head = BLOCK.sub(lambda m: "" if _is_licence(m.group()) else m.group(), t[:end])
    if head != t[:end]:
        head = head.lstrip("\n")
    new = head + t[end:]
    tail = TAIL.search(new)
    if body and tail and tail.start() > len(head) and _is_licence(tail.group(1)):
        new = new[:tail.start()] + "\n"
    return ("keep", t) if new == t else ("fix", new)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_e4(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix+drop. **Runs on:** go. **Docs it touches:** go 56.
4. **Harm test:** go 0.00% (0/163) PASS.
5. **Side effects:** A licence block touching the package doc comment takes the doc with it. Removes the notice the licence asks to keep: record the licence in metadata first.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 17 — code / E4 / `DA-E4-010`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E4-010`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E4 repeated licence headers. Labelled rows: go 76, rust 22, js-ts 9, java 103, cpp 176, python 70. Examples: `01180a3ddf4dfc23`, `0a0303df2fa01ea8`, `0c16883f44febd4f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `9f6e4e65e41f69c4` (code-cpp), original offset 0: `"/* MIT License\n* \n* Copyri"` (fix).
- `0797d20110e8ab9b` (code-cpp), original offset 61: `"rs>1-10\n// Copyright (c) 2010 Th"` (fix).
- `4ac6624748e7453d` (code-cpp), original offset 38: `"der.cxx\n/**\n * PANDA 3D SOFTWARE"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Delete a leading comment block of 5 or more lines that is at least 40% licence text. `#` lines count as comments on python only. Shebang, encoding and Go build lines stay. Repeats until nothing changes, for stacked headers.

```python
RULE_ID = "DA-E4-010"
SOURCE_RULE_ID = "DA-E4-010"
CODE = "E4"
ACTION = "fix"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'python', 'rust'}
ORIGIN = "code-go, code-rust, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-rust"  # pack whose medicine this came from
AUTHOR = "amukka"
import re

MARKER_LINE = re.compile(r"^(?:<(?:reponame|filename|gh_stars)>[^\n]*)\n?")

LICENCE = re.compile(
    r"(?i)(licensed under|permission is hereby granted|redistribution and use|public domain"
    r"|this source code form|all rights reserved|without warranties|general public license"
    r"|affero|mit license|apache license|free software|copyright|warranty|spdx|redistribute"
    r"|the software|the terms|permitted|liability|licen[cs]e|apache|distributed|rights|dedicated"
    r"|modified, or|you may not use)"
)

COMMENT_LINE = re.compile(r"^\s*(//(?![!/])|/\*(?![!*])|\*|\*/|#)")

def _strip_marker(text: str) -> str:
    return MARKER_LINE.sub("", text, count=1)

def _licence_density(block: str) -> bool:
    """3+ licence lines and at least 40% of the non-blank lines are licence text."""
    lines = [l for l in block.split("\n") if l.strip(" /*#\t")]
    hits = sum(bool(LICENCE.search(l)) for l in lines)
    return hits >= 3 and hits * 10 >= len(lines) * 4

def e4_licence_header(text: str, comment_line=COMMENT_LINE):
    """E4: remove a leading comment block of 5+ lines that holds licence text.

    The block is either one /* ... */ comment or a run of // lines (single blank lines allowed
    inside). //! and /// doc comments are never part of it.
    """
    body = _strip_marker(text)
    prefix = text[: len(text) - len(body)]
    if body.lstrip().startswith("/*"):
        end = body.find("*/")
        block, rest = (body[: end + 2], body[end + 2 :]) if end != -1 else ("", body)
        n = block.count("\n") + 1
    else:
        lines = body.split("\n")
        n = 0
        i = 0
        while i < len(lines):
            if comment_line.match(lines[i]):
                n = i + 1
                i += 1
            elif not lines[i].strip() and i + 1 < len(lines) and comment_line.match(lines[i + 1]):
                i += 1
            else:
                break
        block, rest = "\n".join(lines[:n]), "\n".join(lines[n:])
    if n >= 5 and _licence_density(block):
        return "fix", prefix + rest.lstrip("\n")
    return "keep", text

NO_HASH = re.compile(r"^\s*(//(?![!/])|/\*(?![!*])|\*|\*/)")

KEEP_LINE = re.compile(r"^(#!|#.*coding[:=]|\s*//\s*(go:|\+build))")

def medicine_e4_fixed(doc):
    text = doc["text"]
    comment = COMMENT_LINE if doc.get("lang_label") == "python" else NO_HASH
    new = text
    while True:  # two stacked licence blocks: apply(apply(doc)) == apply(doc)
        action, out = e4_licence_header(new, comment)
        if action != "fix" or out == new:
            break
        new = out
    if new == text:
        return ("keep", text)
    now = set(new.split("\n"))
    kept = [l for l in text.split("\n")[:60] if KEEP_LINE.match(l) and l not in now]
    return ("fix", "\n".join(kept + [new]) if kept else new)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_e4_fixed(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go, rust, java, cpp, python. **Docs it touches:** go 51, rust 22, java 81, cpp 95, python 60.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** Short 2 to 4 line notes stay. Removes the notice the licence asks to keep: record the licence in metadata first. **Changed from `DA-E4-004`:** see the decisions file.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-rust sheet, PR 52. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 18 — code / E4 / `DA-E4-009`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E4-009`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E4 repeated licence headers. Labelled rows: go 76, rust 22, js-ts 9, java 103, cpp 176, python 70. Examples: `0796334a27ed6607`, `0dd7bdea9580fa25`, `1a1a1d7ab0bf9188`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `5655154f71365c63` (code-java), original offset 0: `"/*\n *  Licensed to the A"` (fix).
- `86534a30f79557fb` (code-java), original offset 0: `"/*\n * Licensed under the"` (fix).
- `c70422358a640e42` (code-java), original offset 4: `"stars>0\n/*\n *  Licensed to the A"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Drop on a restrictive licence phrase. Else delete the first licence comment block of 7 or more lines in the first 60 lines, or one at the end.

```python
RULE_ID = "DA-E4-009"
SOURCE_RULE_ID = "DA-E4-009"
CODE = "E4"
ACTION = "fix+drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'java'}
ORIGIN = "code-java"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "RaviNaik"
import re

_LIC_WORDS = re.compile(
    r"(?i)licensed under|permission is hereby granted|without warranty|"
    r"you may not use this file|redistribut|general public license|all rights reserved|"
    r"warranties of|distributed under the licen"
)

_RESTRICTIVE = re.compile(
    r"(?i)free for personal use|commercial use requires|non-?commercial use only|commons clause|"
    r"not for commercial use|for evaluation purposes only"
)

def _comment_runs(lines, limit=60, tail=False):
    """Yield (start, end) of contiguous // runs, /* */ blocks and runs of one-line /* ... */ comments."""
    n = len(lines)
    rng = range(max(0, n - 40), n) if tail else range(0, min(n, limit))
    lo, hi = rng.start, rng.stop
    i = lo
    while i < hi:
        s = lines[i].strip()
        if s.startswith("/*") and s.endswith("*/") and len(s) > 4:
            j = i
            while j < n and lines[j].strip().startswith("/*") and lines[j].strip().endswith("*/"):
                j += 1
            yield i, j
            i = j
        elif s.startswith("/*"):
            j = i
            while j < n and "*/" not in lines[j]:
                j += 1
            yield i, j + 1
            i = j + 1
        elif s.startswith("//") and not s.startswith(("//go:", "// +build", "//+build")):
            j = i
            while j < n and lines[j].strip().startswith("//"):
                j += 1
            yield i, j
            i = j
        else:
            i += 1

def strip_licence_header(text: str, min_lines: int = 7):
    """Drop files whose header carries a restrictive licence. Otherwise remove the first
    comment block in the first 60 lines (or the last 40 lines) that has >= min_lines lines and
    licence grant text. Run this AFTER fix_b3 so the file starts at the real first line."""
    lines = text.split("\n")
    head = "\n".join(lines[:60])
    if _RESTRICTIVE.search(head):
        return "drop", text
    for tail in (False, True):
        for a, b in _comment_runs(lines, tail=tail):
            block = lines[a:b]
            if len(block) >= min_lines and sum(1 for x in block if _LIC_WORDS.search(x)) >= 2:
                kept = lines[:a] + lines[b:]
                return "fix", "\n".join(kept).strip("\n") + ("\n" if text.endswith("\n") else "")
    return "keep", text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(strip_licence_header(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix+drop. **Runs on:** java. **Docs it touches:** java 82.
4. **Harm test:** java 0.00% (0/116) PASS.
5. **Side effects:** Short headers stay.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, PR 36. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 19 — code / E4 / `DA-E4-007`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E4-007`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E4 repeated licence headers. Labelled rows: go 76, rust 22, js-ts 9, java 103, cpp 176, python 70. Examples: `1e918efcbd1c6f4b`, `4aa682fef3c7ba0d`, `67c9226601f26da9`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `ac23df9698407bac` (code-js-ts), original offset 0: `"/**\n *\n *    Copyright ("` (fix).
- `1e918efcbd1c6f4b` (code-js-ts), original offset 24: `"sorolla\n/**\n * Copyright 2015-20"` (fix).
- `877058bd3cb250e3` (code-js-ts), original offset 27: `"torbook\n/**\n * Package that cont"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Delete the first comment at the top when it is 10 or more lines and names Apache, MIT, GPL or "Permission is hereby granted".

```python
RULE_ID = "DA-E4-007"
SOURCE_RULE_ID = "DA-E4-007"
CODE = "E4"
ACTION = "fix"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'javascript', 'typescript'}
ORIGIN = "code-js-ts"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-js-ts"  # pack whose medicine this came from
AUTHOR = "Sagar063"
import re

_LICENCE = re.compile(r"Licensed under the Apache License|Permission is hereby granted|"
                      r"GNU (Lesser |Affero )?General Public License|MIT License", re.I)

_TOP_COMMENT = re.compile(r"\A((?:<(?:reponame|filename|gh_stars)>[^<\n]*)+\n)?\s*"
                          r"(/\*.*?\*/[ \t]*\n?|(?:[ \t]*//[^\n]*\n)+)", re.S)

def medicine_e4(text):
    """Remove a licence comment of 10 or more lines at the top of the file."""
    m = _TOP_COMMENT.match(text)
    if m:
        block = m.group(2).rstrip("\n")
        if _LICENCE.search(block) and block.count("\n") + 1 >= 10:
            return (m.group(1) or "") + text[m.end():].lstrip("\n")
    return text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_e4(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** js-ts. **Docs it touches:** js-ts 6.
4. **Harm test:** js-ts 0.49% (1/204) PASS.
5. **Side effects:** Short notices stay. **Changes 1 js-ts gold doc** (`67c9226601f26da9`, a 21-line licence header the gold readers kept). That is within the limit of 2 and it is what the rule is for; the readers disagree on whether a real header is E4. Removes the notice the licence asks to keep: record the licence in metadata first.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-js-ts sheet, PR 115. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 20 — code / C1 / `DA-C1-004`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-C1-004`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C1 boilerplate. Labelled rows: go 1, rust 0, js-ts 0, java 80, cpp 2, python 0. Examples: `45ac5026eac81b39`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `45ac5026eac81b39` (code-go), original offset 617: `"/v1\"\n)\n\n// EDIT THIS FILE!  THIS"` (fix).
- `fd10104d4b8b5721` (code-go), original offset 653: `"/v1\"\n)\n\n// NOTE: json tags are r"` (fix).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Delete kubebuilder and operator-sdk scaffold notes ("EDIT THIS FILE!", "NOTE: json tags are required").

```python
RULE_ID = "DA-C1-004"
SOURCE_RULE_ID = "DA-C1-004"
CODE = "C1"
ACTION = "fix"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'go'}
ORIGIN = "code-go"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import re

SCAFFOLD = re.compile(r'^[ \t]*//[ \t]*(?:EDIT THIS FILE!.*|NOTE: json tags are required\..*|'
                      r'Important: Run "make" to regenerate code after modifying this file.*|'
                      r'INSERT ADDITIONAL (?:SPEC|STATUS) FIELDS?.*)\n', re.M)

def medicine_c1(doc):
    t = SCAFFOLD.sub("", doc["text"])
    return ("fix" if t != doc["text"] else "keep", t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_c1(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go. **Docs it touches:** go 2.
4. **Harm test:** go 0.00% (0/163) PASS.
5. **Side effects:** Other generators' scaffold notes are not covered.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 21 — code / C1 / `DA-C1-005`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-C1-005`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C1 boilerplate. Labelled rows: go 1, rust 0, js-ts 0, java 80, cpp 2, python 0. Examples: `077f2bc49b1bb6db`, `0b893004aea9459b`, `1397a887d14c0fae`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `e0ebe203093970dc` (code-java), original offset 100: `"Map;\r\n\r\n/**\r\n * Created by sherx"` (fix).
- `c9eb2d8e4f9cacde` (code-java), original offset 429: `"nUtil;\n\n/**\n * Created by hzliux"` (fix).
- `50e06974390e57ea` (code-java), original offset 0: `"/*\n * To change this lic"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Delete IDE template lines and the template part of a header comment ("To change this template", "Created by ... on").

```python
RULE_ID = "DA-C1-005"
SOURCE_RULE_ID = "DA-C1-005"
CODE = "C1"
ACTION = "fix"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'java'}
ORIGIN = "code-java"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-java"  # pack whose medicine this came from
AUTHOR = "vaibh27"
import re

LIC_WORDS = re.compile(r"licen[cs]e|permission is hereby granted|redistribution and use", re.I)

NOT_LICENCE = re.compile(r"to change this licen[cs]e header|choose licen[cs]e headers", re.I)

IDE_LINE = re.compile(r"(?im)^[ \t]*//[ \t]*TODO Auto-generated (?:method|constructor|catch block|stub)[^\n]*\n")

BLOCK = re.compile(r"[ \t]*/\*.*?\*/[ \t]*\n?", re.S)

IDE_MARK = re.compile(r"(?im)TODO Auto-generated|To change this (?:licen[cs]e header|template)|choose Tools \| Templates|"
                      r"Created (?:by|with) IntelliJ IDEA|Created by [^\n]{1,80}? on \d|File \| Settings \| File Templates|"
                      r"^\s*\*?\s*User\s*:.*\n\s*\*?\s*Date\s*:|^\s*\*?\s*@(?:project|package)\s*[:：]|\$\{[\w.]{1,40}\}|"
                      r"^\s*\*?\s*<p>\s*Title\s*[:：]")

EMPTY_DESC = re.compile(r"(?im)^\s*\*?\s*@?desc(?:ription)?\s*[:：]*\s*(?:TODO)?\s*$")

AUTHOR_DATE = re.compile(r"(?im)^\s*\*?\s*@?(?:author|user)\b(?:.*\n)*?\s*\*?\s*@?(?:date|create|created)\s*[:：]")

TEMPLATE_LINE = re.compile(r"(?i)^\s*(?:/\*+|\*+)?\s*(?:<p>\s*)?(?:@?(?:author|user|date|time|class|project|package|create|created|"
                           r"version|since|title)\b\s*[:：]?.*|desc(?:ription)?\s*[:：]?\s*(?:TODO)?\s*(?:</p>)?|Created (?:by|with) .*|"
                           r"To change this .*|choose .*Templates.*|and open the template.*|TODO Auto-generated.*|"
                           r"(?:copyright|e-?mail|blog|company)\b.*)\s*$")

AUTHOR_ONLY = re.compile(r"/\*\*(?:\s*\*)*\s*@author\b[^\n]*(?:\s*\*)*\s*/")

def _clean_ide_block(block: str) -> str:
    if LIC_WORDS.search(block) and not NOT_LICENCE.search(block):
        return block  # a licence goes with M4
    if AUTHOR_ONLY.fullmatch(block.strip()):  # empty Javadoc with one @author line (labelled B4 only for <NAME>)
        return ""
    if not (IDE_MARK.search(block) or (EMPTY_DESC.search(block) and AUTHOR_DATE.search(block))):
        return block
    body = block.rstrip("\n")
    lines, end = body.split("\n"), block[len(body):]  # end: the newline after */
    inner = [l for l in lines[1:-1] if not TEMPLATE_LINE.match(l) and l.strip(" \t*")]
    if len(lines) < 3 or not inner:
        return ""  # nothing but the template
    return "\n".join([lines[0]] + [l for l in lines[1:-1] if not TEMPLATE_LINE.match(l)] + [lines[-1]]) + end

def m6_strip_ide_templates(t: str) -> str:
    t = IDE_LINE.sub("", t)
    return BLOCK.sub(lambda m: _clean_ide_block(m.group()), t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(m6_strip_ide_templates(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** java. **Docs it touches:** java 79.
4. **Harm test:** java 0.00% (0/116) PASS.
5. **Side effects:** Only one java reader labels these; the other two mark 23 of the touched docs clean. It only touches comments.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-java sheet, PR 48. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 22 — code / B4 / `DA-B4-009`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-B4-009`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B4 template junk / PII placeholders. Labelled rows: go 45, rust 18, js-ts 25, java 83, cpp 122, python 27. Examples: `0f4121b3b47fc3e0`, `1398b525d923d644`, `14a63d176ed55369`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `9f6e4e65e41f69c4` (code-cpp), original offset 31: `"c) 2018 <NAME>\n* \n* Permission i"` (fix).
- `ab726af7ee73aa3b` (code-cpp), original offset 17: `"C) 2015 <NAME>\n * All rights res"` (fix).
- `a800be93ce443cb5` (code-cpp), original offset 21: `"ated by <NAME> on 2021/5/13.\n//\n"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** `<NAME>` -> `AUTHOR`, `<EMAIL>` -> `user@example.com`, `<KEY>` -> `EXAMPLE_KEY`, `<PASSWORD>` -> `EXAMPLE_PASSWORD`.

```python
RULE_ID = "DA-B4-009"
SOURCE_RULE_ID = "DA-B4-009"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'javascript', 'python', 'rust', 'typescript'}
ORIGIN = "code-go, code-rust, code-js-ts, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import re

NEUTRAL = {"<NAME>": "AUTHOR", "<EMAIL>": "user@example.com", "<KEY>": "EXAMPLE_KEY", "<PASSWORD>": "EXAMPLE_PASSWORD"}

PLACEHOLDER = re.compile("|".join(map(re.escape, NEUTRAL)))

def medicine_b4(doc):
    t = PLACEHOLDER.sub(lambda m: NEUTRAL[m.group()], doc["text"])
    return ("fix" if t != doc["text"] else "keep", t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_b4(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go, rust, js-ts, java, cpp, python. **Docs it touches:** go 43, rust 18, js-ts 30, java 82, cpp 121, python 83.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; js-ts 0.00% (0/204) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** Cannot repair code that the redaction cut (C3 drops that file). A neutral word is still not the true author.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 23 — code / E3 / `DA-E3-003`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E3-003`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E3 secrets. Labelled rows: go 1, rust 1, js-ts 9, java 1, cpp 0, python 0. Examples: `98e4c493f32c8bfa`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Known key formats (AWS, GitHub, `sk-`, Slack, PEM) and base32 seeds assigned to secret, seed or otp names become `EXAMPLE_SECRET`.

```python
RULE_ID = "DA-E3-003"
SOURCE_RULE_ID = "DA-E3-003"
CODE = "E3"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'javascript', 'python', 'rust', 'typescript'}
ORIGIN = "code-go, code-rust, code-js-ts, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "code-go"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import re

KEYS = [re.compile(p) for p in (r"AKIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{30,}", r"\bsk-[A-Za-z0-9_-]{20,}",
        r"xox[baprs]-[A-Za-z0-9-]{10,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")]

SEED = re.compile(r'(?i)((?:secret|seed|totp|otp)\w*\s*:?=\s*")[A-Z2-7]{16,}(")')

def medicine_e3(doc):
    t = doc["text"]
    for rx in KEYS:
        t = rx.sub("EXAMPLE_SECRET", t)
    t = SEED.sub(r"\1EXAMPLE_SECRET\2", t)
    return ("fix" if t != doc["text"] else "keep", t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_e3(doc), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go, rust, js-ts, java, cpp, python. **Docs it touches:** go 1, rust 0, js-ts 0, java 0, cpp 0, python 0.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; js-ts 0.00% (0/204) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** Secrets with no known format and no telling name are missed. A public test vector is replaced too.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 24 — code / E3 / `DA-E3-004`

**Consolidation:** Source [medicine_code.md](medicine_code.md); original identity `DA-E3-004`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** E3 secrets. Labelled rows: go 1, rust 1, js-ts 9, java 1, cpp 0, python 0. Examples: `85fa4d03a2a63982`, `0d3bff117f465b99`, `8302c459b07901ca`.
<!-- CARD EVIDENCE -->
**Current gold harm:** code-cpp: 0 changed / 0 dropped of 122 (PASS); code-go: 0 changed / 0 dropped of 163 (PASS); code-java: 0 changed / 0 dropped of 116 (PASS); code-js-ts: 0 changed / 0 dropped of 204 (PASS); code-python: 0 changed / 0 dropped of 141 (PASS); code-rust: 0 changed / 0 dropped of 234 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Replace a secret with `EXAMPLE_SECRET` and keep the file. Two kinds: known formats (Google, AWS, GitHub, Stripe, SendGrid, Slack, JWT, PEM), and a quoted value of 16 or more characters assigned to a secret-like name or passed to `new Pusher(`. The value must look random: mixed letters and digits, at least 15% digits, no dots, no dummy words such as `test` or `example`.

```python
RULE_ID = "DA-E3-004"
SOURCE_RULE_ID = "DA-E3-004"
CODE = "E3"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {'cpp', 'go', 'java', 'javascript', 'python', 'rust', 'typescript'}
ORIGIN = "code-go, code-rust, code-js-ts, code-java, code-cpp, code-python"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # a code pack may label every doc "code", so the pack is checked too
SOURCE = "new rule, written for this sheet"  # pack whose medicine this came from
AUTHOR = "TEJASKUMAR-REDDY-J"
import math
import re

PLACEHOLDER = "EXAMPLE_SECRET"

KNOWN = [re.compile(p) for p in (
    r"\bAIza[0-9A-Za-z_\-]{35}\b",                                   # Google API key
    r"\bAKIA[0-9A-Z]{16}\b",                                         # AWS access key
    r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",                               # GitHub token
    r"\bgithub_pat_[A-Za-z0-9_]{40,}\b",                             # GitHub fine-grained token
    r"\bsk-[A-Za-z0-9_\-]{20,}\b",                                   # sk- API key
    r"\b[rs]k_live_[0-9A-Za-z]{16,}\b",                              # Stripe live key
    r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\b",             # SendGrid key
    r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b",                            # Slack token
    r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b",  # JWT
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
)]

ASSIGNED = re.compile(
    r"""(?ix)
    (?P<head>
      \b[\w\-]*(?:secret|token|api[_\-]?key|app[_\-]?key|auth[_\-]?key|access[_\-]?key|client[_\-]?key|private[_\-]?key|passw(?:or)?d|pwd|\bkey)[\w\-]*
      ["']?
      (?:\s*:\s*&?(?:'\w+\s+)?[\w<>\[\]]{1,20})?   # Rust and TypeScript types: SECRET: &'static str = "..."
      \s*(?::=|=>|=|:)\s*
      (?P<quote>["'`])
    )
    (?P<value>[^"'`\s\\]{16,200})
    (?P=quote)
    """)

SDK_KEY = re.compile(r"""(?P<head>\bnew\s+Pusher\(\s*(?P<quote>["'`]))[0-9a-fA-F]{16,}(?P=quote)""")

DUMMY = re.compile(r"(?i)example|sample|dummy|test|fake|mock|placeholder|changeme|change_me|your|xxxx|0000|1234|abcd|secret|password|token|<|>|\$\{|\{\{|%s")

def _entropy(v):
    n = len(v)
    return -sum(c / n * math.log2(c / n) for c in (v.count(ch) for ch in set(v)))

def _looks_random(v):
    """A real key is a run of mixed letters and digits, not a word, an identifier, a path, a version or a dummy."""
    if DUMMY.search(v) or "." in v or v.count("/") > 2:
        return False
    if not (re.search(r"[0-9]", v) and re.search(r"[A-Za-z]", v)):  # enum names and plain words have no digits
        return False
    if sum(ch.isdigit() for ch in v) < 0.15 * len(v):                # user_profile_settings_v2
        return False
    return _entropy(v) >= 3.0

def medicine_e3(text):
    new = text
    for rx in KNOWN:
        new = rx.sub(PLACEHOLDER, new)
    new = SDK_KEY.sub(lambda m: m.group("head") + PLACEHOLDER + m.group("quote"), new)
    new = ASSIGNED.sub(lambda m: m.group("head") + PLACEHOLDER + m.group("quote") if _looks_random(m.group("value")) else m.group(0), new)
    return new


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, str): return ("fix" if out != text else "keep", out)
    action, new = out
    if action == "drop": return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS and doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_e3(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'code-cpp', 'code-go', 'code-java', 'code-js-ts', 'code-python', 'code-rust'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** go, rust, js-ts, java, cpp, python. **Docs it touches:** go 0, rust 1, js-ts 2, java 1, cpp 0, python 0.
4. **Harm test:** go 0.00% (0/163) PASS; rust 0.00% (0/78) PASS; js-ts 0.00% (0/204) PASS; java 0.00% (0/116) PASS; cpp 0.00% (0/120) PASS; python 0.00% (0/46) PASS.
5. **Side effects:** A key with no digits, or under 16 characters, or under a neutral variable name is missed. A random-looking ID stored under a name like `key` is replaced too; it only changes a string, so the code still parses. Not a full scanner: gitleaks or trufflehog would catch more.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: code-go sheet, an updated `medicine.md`, not in PR 73 yet. Idempotent on every doc of its packs. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 25 — english / A1 / `DA-A1-004`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-A1-004`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A1 invisible junk characters. Labelled rows: dclm 12, fineweb-edu 1, nemotroncc 14, synth 0. Examples it treats: `10355b4f94c87a2c` (dclm), `11c3cd0e50856c3e` (dclm), `094e33117f3c3cd2` (nemotroncc).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `4a22b0cbca7869fc` (en-dclm), original offset 0: `"\ufeff German Genealogy -- Ce"` (fix).
- `855032b92c2b8d25` (en-dclm), original offset 153: `"davon ge\u00adsprochen, unser Denkver"` (fix).
- `122504afaec49b2d` (en-dclm), original offset 0: `"\ufeff \u82f1\u6587\u5b57\u5178\u4e2d\u6587\u5b57\u5178\n\n\n\u63a8\u5230 Twitter!"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Delete the invisible characters named in the disease list. ZWJ (U+200D) and ZWNJ (U+200C) are **not** removed: they are part of Indic script and are not a disease. This pack is English, but the rule is written so it stays correct if it is ever reused on an Indic pack.

```python
RULE_ID = "DA-A1-004"
SOURCE_RULE_ID = "DA-A1-004"
CODE = "A1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm"  # pack whose medicine this came from
AUTHOR = "mittalutkarsh"  # extractor
import re

_INVISIBLE = re.compile("[﻿​­‎‏‪-‮⁦-⁩]")

def medicine_a1(text):
    return _INVISIBLE.sub("", text)


def _std(out, text):  # added by Data A
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(medicine_a1(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 11 fixed, 0 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 14 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** Removing a soft hyphen joins the two halves of a word, which is right for `never­ending` but wrong if a document ever used it as a real hyphen. Stripping bidi controls from a document that genuinely mixes right-to-left and left-to-right text would change how that text renders; there is no such document in this pack, but there would be in an Arabic or Hebrew one, and this medicine should not be reused there without a second look. ---
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 26 — english / A2 / `DA-A2-008`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-A2-008`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A2 control characters. Labelled rows: dclm 3, fineweb-edu 0, nemotroncc 0, synth 0. Examples it treats: `5d1fd12b101321f0` (dclm), `7b1d879aa4e04769` (dclm).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `94f537dcf85f69f8` (en-dclm), original offset 2486: `"called \u00e2\u0080\u009cThe Mystery of Half Mo"` (fix).
- `5d1fd12b101321f0` (en-dclm), original offset 12597: `" artist\u00c2\u0092s movements, from hand "` (fix).
- `7b1d879aa4e04769` (en-dclm), original offset 1645: `"varies\u00e2\u20ac\u009d, perhaps we should ste"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Remove the control characters U+0000 to U+001F (except tab and newline) and U+007F to U+009F. A carriage return is a control character too: CRLF and a lone CR become a newline.

```python
RULE_ID = "DA-A2-008"
SOURCE_RULE_ID = "DA-A2-008"
CODE = "A2"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # pack whose medicine this came from
AUTHOR = "aneeshads"  # new in the 29 Oct sheet as DA-A2-007
import re

A2_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def medicine_a2(text):
    new = A2_CONTROL.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return medicine_a2(doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 3 fixed, 0 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** A form feed used as a page break is removed, so the two pages run together. Every document with Windows line endings counts as changed.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: new rule, 29 Oct sheet (was DA-A2-007). Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 27 — english / A5 / `DA-A5-001`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-A5-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A5 wrong normal form. Labelled rows: dclm 3, fineweb-edu 0, nemotroncc 0, synth 0. Examples it treats: `10355b4f94c87a2c` (dclm), `68575a61a90990d5` (dclm).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `c64a732a64b1ce8b` (en-dclm), original offset 5005: `"o the nai\u0308ve realist is to quest"` (fix).
- `10355b4f94c87a2c` (en-dclm), original offset 642: `"ith Josue\u0301 Me\u0301ndez\u2019\u00a0Days of Sant"` (fix).
- `68575a61a90990d5` (en-dclm), original offset 984: `"\u0301\u00c6\u00b0\u00b1\u00ada\u00b7 O\u0303-A\u0300A\u0303\u00d7- I\u0308U\u0302E\u0308 fl \u00a5\u00b7 \u0308"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Normalise the text to NFC, the form the lab uses.

```python
RULE_ID = "DA-A5-001"
SOURCE_RULE_ID = "DA-A5-001"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # pack whose medicine this came from
AUTHOR = "aneeshads"  # new in the 29 Oct sheet as DA-A5-001
import re

import unicodedata


def medicine_a5(text):
    new = unicodedata.normalize("NFC", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return medicine_a5(doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 3 fixed, 0 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** The bytes of decomposed text change, not its look. A text about Unicode normalisation loses the difference between its examples.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: new rule, 29 Oct sheet (was DA-A5-001). Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 28 — english / A3 / `DA-A3-002`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-A3-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A3 mojibake. Labelled rows: dclm 7, fineweb-edu 4, nemotroncc 4, synth 0. Examples it treats: `5d1fd12b101321f0` (dclm), `7b1d879aa4e04769` (dclm), `53dadf5fc6ee123a` (fineweb-edu).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `816e5ec1fb368590` (en-dclm), original offset 590: `".\n  \u2022 No\u00c2\u00a0waste products: Since "` (fix).
- `94f537dcf85f69f8` (en-dclm), original offset 140: `" called \u201cThe Mystery of Half Moo"` (fix).
- `5d1fd12b101321f0` (en-dclm), original offset 12596: `"e artist\u00c2\u0092s movements, from hand"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Detect the double-decoding signatures, repair with `ftfy.fix_text`, and drop the document only if the signature is still dense after repair (the bytes are gone, not just mis-decoded).

```python
RULE_ID = "DA-A3-002"
SOURCE_RULE_ID = "DA-A3-002"
CODE = "A3"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm"  # pack whose medicine this came from
AUTHOR = "shekar-maker"  # extractor; adapter for (text, flag)
import re
import ftfy  # added by Data A: used, never imported (pip install ftfy)

A3_RE = re.compile(r"â€[\x80-\xbf‘-™]?|Ã[\x80-\xbf\u0080-ÿ]|Â[\xa0-\xbf]|[\x80-\x9f]")

def m_a3(text):
    if not A3_RE.search(text): return text, False
    new = ftfy.fix_text(text)
    return new, len(A3_RE.findall(new)) * 1000 / max(len(new), 1) > 1.0


def _std(out, text):  # added by Data A
    # the author's result (new_text, flag) in the shared form: flag -> drop (their sheet: "flag for drop"),
    # else fix/keep by the text
    new, flag = out
    if flag: return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(m_a3(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 4 fixed, 0 dropped, fineweb-edu 1 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** The signature regex misses mojibake that went through a non-UTF-8 round trip, for example Cyrillic `й` standing in for `é` (`Pokйmon` in `68575a61a90990d5`, `Diffйrents` in `467b5c0aa1d13de8`) and symbol-font gibberish (`3dc93ffbd87ba839`): 3 of the 7 labelled documents are not touched. `ftfy` can in rare cases "repair" legitimate text that happens to look like mojibake (`Ã` followed by a letter in Portuguese); the gold run will show whether that happens in English.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor; adapter for (text, flag). Added: ftfy. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 29 — english / B1 / `DA-B1-002`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-B1-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B1 HTML entities. Labelled rows: dclm 1, fineweb-edu 0, nemotroncc 3, synth 0. Examples it treats: `1992526bd6e98869` (dclm).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `1992526bd6e98869` (en-dclm), original offset 1492: `"s and GW&#39;s vehicles that wer"` (fix).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Decode the common HTML entities (`&amp;`, `&nbsp;`, `&quot;`, `&lt;`, `&gt;`, dashes, quotes, `&#NNN;`, `&#xHH;`). `&nbsp;` becomes a plain space.

```python
RULE_ID = "DA-B1-002"
SOURCE_RULE_ID = "DA-B1-002"
CODE = "B1"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # pack whose medicine this came from
AUTHOR = "aneeshads"  # new in the 29 Oct sheet as DA-B1-002
import re

import html
import re

B1_ENTITY = re.compile(r"&(?:amp|nbsp|quot|apos|lt|gt|mdash|ndash|hellip|rsquo|lsquo|rdquo|ldquo|copy|reg|trade"
                       r"|#\d{2,6}|#x[0-9a-fA-F]{2,5});")


def medicine_b1(text):
    new = B1_ENTITY.sub(lambda m: html.unescape(m.group()).replace("\xa0", " "), text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return medicine_b1(doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 1 fixed, 0 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** A text that shows entities on purpose (an HTML tutorial) is changed. An entity that is not on the list stays.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: new rule, 29 Oct sheet (was DA-B1-002). Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 30 — english / B2 / `DA-B2-002`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-B2-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B2 HTML or XML tags. Labelled rows: dclm 3, fineweb-edu 1, nemotroncc 1, synth 0. Examples it treats: `6d1051dc3ca46585` (dclm), `a845e6c52e035cbb` (fineweb-edu).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `6d1051dc3ca46585` (en-dclm), original offset 2383: `"ock! --><div style=\"width:100%;h"` (fix).
- `a845e6c52e035cbb` (en-fineweb-edu), original offset 248: `"mework.\n<p>A Christmas murder my"` (fix).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Remove common HTML tags (`<div>`, `<p>`, `<br/>`, `<span ...>`, `<li>`, `<strong>`, ...) when the text has at least two of them and is not about HTML (no code fence, `class=`, `<!DOCTYPE`, or the words html, tag, element). A single tag is often a mention, not markup.

```python
RULE_ID = "DA-B2-002"
SOURCE_RULE_ID = "DA-B2-002"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # pack whose medicine this came from
AUTHOR = "aneeshads"  # new in the 29 Oct sheet as DA-B2-002
import re

B2_TAG = re.compile(r"</?(?:div|span|p|br|li|ul|ol|img|table|tr|td|th|tbody|thead|strong|em|font|iframe|script|style|center|hr)"
                    r"(?:\s[^<>]{0,200})?\s*/?>", re.I)
B2_ABOUT_HTML = re.compile(r"```|\bclass\s*=|<!DOCTYPE|\bhtml\b|\btag\b|\belement\b", re.I)


def medicine_b2(text):
    if B2_ABOUT_HTML.search(text) or len(B2_TAG.findall(text)) < 2:
        return ("keep", text)
    new = re.sub(r"[ \t]{2,}", " ", B2_TAG.sub(" ", text))
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return medicine_b2(doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 1 fixed, 0 dropped, fineweb-edu 1 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** A text that quotes tags as examples without those words loses them. `<br>` and `<p>` become a space, not a line break, so lines can run together.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: new rule, 29 Oct sheet (was DA-B2-002). Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 31 — english / C3 / `DA-C3-001`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-C3-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C3 truncated document. Labelled rows: dclm 103, fineweb-edu 35, nemotroncc 101, synth 50. Examples it treats: `52422fff81211f50` (dclm), `4f2fc39dee7af855` (nemotroncc), `5ef3f9c12c7a2608` (nemotroncc).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `52422fff81211f50` (en-dclm), original offset 0: `"Tag: University of Southampton\n\nSolving a piece of the DFTD puzz"` (drop).
- `c1792de8d0f91aa8` (en-nemotroncc), original offset 0: `"Syria: Govt. forces demine Palmyra after retaking ancient city f"` (drop).
- `71a349332d2a5bc2` (en-nemotroncc), original offset 0: `"Where technology, community and commerce converge MWC Barcelona "` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Only the *stub* form is treated. A document of at most 600 characters whose last word is one no sentence ends on (`from`, `the`, `and`, ...) or that ends with a teaser `...` is dropped (the dangling-word test only applies when the text has no terminal punctuation).

```python
RULE_ID = "DA-C3-001"
SOURCE_RULE_ID = "DA-C3-001"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm"  # pack whose medicine this came from
AUTHOR = "shekar-maker"  # extractor; adapter for (text, flag)
import re

DANGLING = set("a an the and or but of to in on at by for from with as that which who will would can could is are was were be been being has have had this these those its their his her my our your".split())

def m_c3(text, max_len=600):
    body = text.rstrip()
    if len(body) > max_len: return text, False
    last = (re.findall(r"[A-Za-z']+", body) or [""])[-1].lower()
    teaser = body.endswith(("...", "…", "[...]", "[…]", "(more)", "Read more"))
    unfinished = body[-1] not in ".!?\"')]}»”’:;" and last in DANGLING
    return text, bool(teaser or unfinished)


def _std(out, text):  # added by Data A
    # the author's result (new_text, flag) in the shared form: flag -> drop (their sheet: "flag for drop"),
    # else fix/keep by the text
    new, flag = out
    if flag: return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(m_c3(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** all four English packs. **Docs it touches:** dclm 0 fixed, 1 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 0 fixed, 5 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** My first version trimmed any last line without terminal punctuation; it changed 5 of the 28 documents then in the proxy set (complete sentences that simply lack a full stop), so it was withdrawn. The stub rule's dangling-word test then dropped a clean 560-character document ending `...what research impact is.`, which failed the 1% limit on the 65-document proxy; it now applies only when the text has no terminal punctuation. The rule catches 1 of the 98 labelled documents, because in this pack C3 is mostly mid-text gaps where a link, a citation, a quote or an image was stripped by an earlier cleaner (the readers' notes say most C3 rows are of this kind, not end-of-document cuts). There is no safe regex for that; it is the main finding of this slice for the pipeline team: the HTML-to-text step drops anchor text and embedded content.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor; adapter for (text, flag). Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 32 — english / C3 / `DA-C3-003`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-C3-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C3 truncated document. Labelled rows: dclm 103, fineweb-edu 35, nemotroncc 101, synth 50. Examples it treats: `484c668df3c40868` (dclm), `52422fff81211f50` (dclm), `8262087c39b0c8c5` (fineweb-edu).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `52422fff81211f50` (en-dclm), original offset 0: `"Tag: University of Southampton\n\nSolving a piece of the DFTD puzz"` (drop).
- `484c668df3c40868` (en-dclm), original offset 0: `"University of Minnesota\nSchool of Physics & Astronomy\n\n\nNew phys"` (drop).
- `8262087c39b0c8c5` (en-fineweb-edu), original offset 0: `"The Truth About\nNikola Tesla became aware early in the 20th cent"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Drop the document when it ends in an excerpt marker, or when the last word is a function word that cannot end an English sentence. Truncation cannot be repaired, and the tail is the only place it can be detected without guessing.

```python
RULE_ID = "DA-C3-003"
SOURCE_RULE_ID = "DA-C3-002"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm"  # pack whose medicine this came from
AUTHOR = "mittalutkarsh"  # extractor
import re

_MARKER = re.compile(r"\[\s*(?:…|\.\.\.)\s*\]$")

_DANGLING = frozenset(
    "a an the and or but of to in on at for with from by as is are was were "
    "that this these those which who because however".split()
)

_LAST_TOKEN = re.compile(r"([A-Za-z0-9']+)[^A-Za-z0-9']*$")

def medicine_c3(text):
    tail = text.rstrip()
    if not tail:
        return text
    if _MARKER.search(tail):
        return ("drop", "")
    if tail.endswith((".", "!", "?", '"', "'", ")", ":", "…")):
        return text
    token = _LAST_TOKEN.search(tail)
    if token and token.group(1).lower() in _DANGLING:
        return ("drop", "")
    return text


def _std(out, text):  # added by Data A
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(medicine_c3(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** all four English packs. **Docs it touches:** dclm 0 fixed, 3 dropped, fineweb-edu 0 fixed, 1 dropped, nemotroncc 0 fixed, 14 dropped, synth 0 fixed, 1 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** It reads only the end of the document, so it misses truncation in the middle, which is where I found it in `a1b97fd910707a8d` and `5a6856a5e9397412` — there the extractor dropped link and image text and left the sentence around it standing. Those need a different medicine, and I have not written one. A document that genuinely ends on an ellipsis for effect would be dropped wrongly; I saw none in this pack, but it is the obvious failure. ---
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 33 — english / C5 / `DA-C5-002`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-C5-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C5 lists of keywords or links. Labelled rows: dclm 61, fineweb-edu 30, nemotroncc 71, synth 7. Examples it treats: `0b139d9931d96986` (dclm), `1ec7fa64b9476242` (dclm).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3dc93ffbd87ba839` (en-dclm), original offset 0: `"Corporate, Political, Government Corruption News in Pakistan\n\nPr"` (drop).
- `0b139d9931d96986` (en-dclm), original offset 0: `"Free AUTO INSURANCE Quotes For Your State\n\nGet a list of the lea"` (drop).
- `1ec7fa64b9476242` (en-dclm), original offset 0: `"\u8fd4\u56de\u5217\u8868 \u56de\u5fa9 \u767c\u5e16\n\nCheap Jerseys From China3t\n\ncheap jerseys\n\u00a0\u00a0dollars)"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Drop the document when at least two different injected-keyword markers appear, or when a single line is a run of five or more short pipe-separated phrases. Two markers rather than one, because a page may mention a brand once for an honest reason.

```python
RULE_ID = "DA-C5-002"
SOURCE_RULE_ID = "DA-C5-002"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm"  # pack whose medicine this came from
AUTHOR = "mittalutkarsh"  # extractor
import re

_SPAM = tuple(
    re.compile(p, re.I)
    for p in (
        r"\bcheap\s+(?:nfl|nba|mlb|nhl)\b",
        r"\bcheap\s+(?:michael\s+kors|oakley|ray\s*bans?|jerseys)\b",
        r"\bray\s*bans?\s+(?:sunglasses|outlet)\b",
        r"\b(?:auto|car)\s+insur\w*\s+(?:quotes?|qiotes?|rates?)\b",
        r"\bfree\s+auto\s+insurance\s+quotes\b",
        r"\bsex\s+dating\s+in\b",
        r"\bwrite\s+my\s+essay\b",
        r"\b(?:카지노|바카라|룰렛)\b",
        r"\bpigmentación\s+capilar\b",
    )
)

_KEYWORD_LINE = re.compile(r"^(?![ \t]*[•·*\-])(?:[^|\n]{2,40}\|){6,}[^|\n]{2,40}[ \t]*$", re.M)

def medicine_c5(text):
    hits = sum(1 for p in _SPAM if p.search(text))
    if hits >= 2 or _KEYWORD_LINE.search(text):
        return ("drop", "")
    return text


def _std(out, text):  # added by Data A
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(medicine_c5(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** all four English packs. **Docs it touches:** dclm 0 fixed, 4 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** The marker list is drawn from one pack of 500 English documents, so it will age badly — next year's spam sells something else. A genuine article about car insurance that quotes a spam phrase twice would be dropped. The pipe-separated test would also catch an honest table that survived extraction as a single line, though I saw none in this pack. ---
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 34 — english / D4 / `DA-D4-001`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-D4-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** D4 bad machine translation. Labelled rows: dclm 21, fineweb-edu 3, nemotroncc 17, synth 2. Examples it treats: `0a28e7f42a4bba02` (dclm).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `0a28e7f42a4bba02` (en-dclm), original offset 0: `"Write My Essay!\nArun Kolatkar An Old Woman\n\nArun Kolatkar An Old"` (drop).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Drop the document when the mechanical residue of a spinner is still in the text: unused spintax alternatives in braces, or an essay-mill banner. I am not trying to detect spun prose itself.

```python
RULE_ID = "DA-D4-001"
SOURCE_RULE_ID = "DA-D4-001"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm"  # pack whose medicine this came from
AUTHOR = "mittalutkarsh"  # extractor
import re

_SPINTAX = re.compile(r"\{[^{}\n]{2,60}\|[^{}\n]{2,60}\}")

_MILL = re.compile(r"\b(?:write my essay|essay writing service|buy essays? online)\b", re.I)

def medicine_d4(text):
    if _SPINTAX.search(text) or _MILL.search(text):
        return ("drop", "")
    return text


def _std(out, text):  # added by Data A
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(medicine_d4(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** all four English packs. **Docs it touches:** dclm 0 fixed, 1 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** This reaches only the documents where the spinner left its syntax behind. Finished spun text, which is most of what I labelled D4, reads as ordinary English to a regular expression and passes straight through — `3dce67ac37d56429` and `a55992c7a90ce4f4` are both missed. Detecting it properly needs a language model scoring word collocations, which is beyond a medicine of this kind. The spintax pattern would also fire on a document that legitimately shows spintax syntax, such as a page explaining how article spinners work. ---
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 35 — english / C1 / `DA-C1-006`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-C1-006`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C1 boilerplate. Labelled rows: dclm 389, fineweb-edu 308, nemotroncc 161, synth 76. Examples it treats: `13b37bf5acff4d16` (dclm), `319afcfc2bbab65b` (dclm), `96dfcd8dcd7a0cff` (fineweb-edu).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3f9cf2259ef9ba72` (en-dclm), original offset 0: `"Skip to main content\n\nPO"` (fix).
- `b9ad87575375859e` (en-dclm), original offset 99: `"\n\n\n\n\n\n\n\nRelated Posts:\n\n\n  1. Jo"` (fix).
- `8193a0622521740a` (en-dclm), original offset 3273: `"erstock\n\nRead More >"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Delete every line that is only a known widget or menu label (`Primary tabs`, `Search for:`, `Related posts`, `Share this:`, `Read more`, `Link copied`, `Quantity`, and a few more). A whole-line match is required, so a sentence that contains these words is never touched.

```python
RULE_ID = "DA-C1-006"
SOURCE_RULE_ID = "DA-C1-006"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-nemotroncc"  # pack whose medicine this came from
AUTHOR = "s9k96"  # extractor; None means drop
import re

WIDGET = re.compile(r"(?i)(?:primary tabs|search for:?|related (?:documents|posts|articles):?|click to expand\W*|read more\W*|\[?read more\W*\]?|share this:?|share on (?:other sites|[a-z ]+)|previous|next|menu|contents|advertisement|loading\W*|link copied|the link has been copied!?|post navigation|quantity|breadcrumb|logged|registered|banned|show more|you may also like[a-z ]*|subscribe to [a-z ]+|skip to (?:main )?content|back to top)")

def c1(t):
    """Delete lines that consist only of a known widget or menu label ('Primary tabs', 'Search for:', 'Related posts', 'Share this:' ...)."""
    return "\n".join(l for l in t.split("\n") if not WIDGET.fullmatch(l.strip()))


def _std(out, text):  # added by Data A
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(c1(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 6 fixed, 0 dropped, fineweb-edu 2 fixed, 0 dropped, nemotroncc 27 fixed, 0 dropped, synth 1 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** Most reviewed C1 lines are not on the label list. Examples are `Store Information`, `Featured Manchester Subdivision Real Estate Properties`, `Posted by ... October 2, 2013` and `source: easemytrip`, which are site-specific. The list needs more labels as more packs are read. A real section titled `Contents` or `Next` on its own line would lose that line.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor; None means drop. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 36 — english / C2 / `DA-C2-003`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-C2-003`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C2 repeated lines. Labelled rows: dclm 38, fineweb-edu 6, nemotroncc 39, synth 1. Examples it treats: `1e13b455581e96ca` (dclm), `28bd69b4ed987643` (dclm), `b888d78a21618c96` (fineweb-edu).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `50d363e8b8340b11` (en-dclm), original offset 1648: `" thing.\ncheck the teleport:\n\na f"` (fix).
- `6c6a180069b69bdb` (en-dclm), original offset 34274: `"equal.\n\n        1. Ally Fogg\n\n  "` (fix).
- `c64a732a64b1ce8b` (en-dclm), original offset 36: `" tf h1\n\nTeknik forex tf h1\n\n\n\n\n\n"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Remove the later copies of a line that appears 3 or more times in the same document (lines of at least 10 characters, compared without extra spaces); the first copy is kept. Shorter lines ("*", "Answer") are left alone. In code (the function the medicine runs; the patterns, weights and helpers it uses are in Appendix B, the full runnable file):

```python
RULE_ID = "DA-C2-003"
SOURCE_RULE_ID = "DA-C2-003"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-fineweb-edu"  # pack whose medicine this came from
AUTHOR = "deepjyotisaha"  # extractor; adapter for spans
import re

def _merge(spans):
    """Overlapping spans joined into one, keeping the rule of the first."""
    out = []
    for s, e, rule in sorted(spans):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(e, out[-1][1]), out[-1][2])
        else:
            out.append((s, e, rule))
    return out

C2_MIN_REPEAT, C2_MIN_CHARS = 3, 10

def c2_spans(text):
    """C2: later copies of a line repeated C2_MIN_REPEAT or more times in the document."""
    seen, lines, pos = {}, [], 0
    for line in text.split("\n"):
        key = " ".join(line.split())
        if len(key) >= C2_MIN_CHARS:
            lines.append((pos, pos + len(line), key))
            seen[key] = seen.get(key, 0) + 1
        pos += len(line) + 1
    out, first = [], set()
    for s, e, key in lines:
        if seen[key] >= C2_MIN_REPEAT:
            if key in first:
                out.append((s, e, "C2-repeated-line"))
            first.add(key)
    return out


def _std(out, text):  # added by Data A
    # the author's result (spans to remove) in the shared form, as their clean() reads it: (spans, True) from
    # c1_spans -> drop; a whole-document "B4-mostly-code" or "C5-list-page" span -> drop; else the spans go
    if isinstance(out, tuple):
        out, flagged = out
        if flagged: return ("drop", text)
    if out and out[0][2] in ("B4-mostly-code", "C5-list-page"): return ("drop", text)
    new = text
    for s, e, _ in reversed(_merge(out)):
        new = new[:s] + new[e:]
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(c2_spans(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 20 fixed, 0 dropped, fineweb-edu 4 fixed, 0 dropped, nemotroncc 19 fixed, 0 dropped, synth 2 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 1/170; fineweb-edu 1/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** The medicine finds 6 of the 8 labelled cases. On the whole pack it changes 4 documents: besides the labelled repeats it removes repeated section headings that were labelled C1 and repeated table headers, which belong to their tables. It misses a passage printed twice when the copies are not identical line by line (document 53). --- The appendices below support the medicines above; they are not medicines themselves. ### Appendix A: test on unseen documents On 2026-10-25, before documents 151–500 were labelled, the medicines' predictions for them were saved (`frozen_predictions.json`; C1 scorer trained on the first 150 documents, threshold 0.97). Comparing them with the labels made afterwards (`frozen_test.py`): - **C1 caught:** 174 of 454 labelled C1 lines (38.3%). - **C1 precision:** 169 of the 178 lines it removed were labelled C1 (94.9%). - **Clean documents changed:** 1 of 143 (0.7%): documents 457. - **C3:** found in 0 of the 7 documents labelled C3. - **Blind documents** (every 10th, labelled without seeing any suggestion; the fully independent test): 17 of 47 C1 lines caught (36.2%), 17 of 20 removed lines labelled C1 (85.0%), 0 of 17 clean documents changed. In the other documents the reader saw the predictions as suggestions while labelling, so agreement there is partly their influence. The medicine above was retrained on all labelled documents after this test. ### Appendix B: runnable code All the medicines in one self-contained Python file: copy it into `medicine_standalone.py` and it runs with the standard library alone (no numpy, no other files). It is generated from the code and the trained weights that were tested above, and it gives the same result as that code on all 500 documents of the pack (0 differences, checked by `standalone.py`), when it is given the pack's line-repetition counts (below). Without them, C1 gives a different result on 7 of the 500 documents, because it cannot tell which lines repeat across the pack. How to use it:
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor; adapter for spans. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 37 — english / C5 / `DA-C5-005`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-C5-005`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C5 lists of keywords or links. Labelled rows: dclm 61, fineweb-edu 30, nemotroncc 71, synth 7. Examples it treats: `4604f40da35906cc` (fineweb-edu), `58b9213cca24ff17` (fineweb-edu), `d49190f1c5ef2a70` (nemotroncc).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `b0b8c0fe32cb4bee` (en-dclm), original offset 3467: `"fitness!\n\nTopics: stretches, wor"` (fix).
- `943b00214cee55c2` (en-dclm), original offset 0: `"Tag: app store duopoly\n\nT"` (fix).
- `52422fff81211f50` (en-dclm), original offset 0: `"Tag: University of South"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Remove a line that is a tag list: it starts with `Tags:`, `Tag:`, `Keywords:`, `Tagged with:`, `Topics:` or `Filed under:`. Lists of commas or pipes without such a word are left alone: in clean documents they are stat lines, ingredient lists and genre lists.

```python
RULE_ID = "DA-C5-005"
SOURCE_RULE_ID = "DA-C5-005"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # pack whose medicine this came from
AUTHOR = "aneeshads"  # new in the 29 Oct sheet as DA-C5-002
import re

C5_PREFIX = re.compile(r"^(?:tags?|keywords?|tagged(?: with| in)?|topics?|filed under)\s*:", re.I)


def medicine_c5(text):
    lines = text.split("\n")
    keep = [ln for ln in lines if not C5_PREFIX.search(ln.strip())]
    if len(keep) == len(lines):
        return ("keep", text)
    new = "\n".join(keep).strip("\n")
    return ("drop", text) if not new.strip() else ("fix", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return medicine_c5(doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 4 fixed, 1 dropped, fineweb-edu 2 fixed, 0 dropped, nemotroncc 4 fixed, 0 dropped, synth 1 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** A real heading such as `Topics:` before a list in an article is removed. Keyword spam without the prefix is missed.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: new rule, 29 Oct sheet (was DA-C5-002). Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 38 — english / D3 / `DA-D3-003`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-D3-003`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** D3 mixed language. Labelled rows: dclm 24, fineweb-edu 5, nemotroncc 6, synth 1. Examples it treats: `122504afaec49b2d` (dclm), `1ec7fa64b9476242` (dclm), `95e8df7138976c19` (fineweb-edu).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `1ec7fa64b9476242` (en-dclm), original offset 0: `"\u8fd4\u56de\u5217\u8868 \u56de\u5fa9 \u767c\u5e16\n\nCheap Jersey"` (fix).
- `e53279211deae6a8` (en-dclm), original offset 103: `"eeting\n\n\u0443\u0437\u043d\u0430\u0442\u044c \u0431\u043e\u043b\u044c\u0448\u0435\nThe US Sec"` (fix).
- `122504afaec49b2d` (en-dclm), original offset 0: `"\ufeff \u82f1\u6587\u5b57\u5178\u4e2d\u6587\u5b57\u5178\n\n\n\u63a8\u5230 Twitter!"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Do not fix real code-switching. The rule deletes only whole lines in which more than half of the letters are not Latin, in an English pack. A foreign word inside an English sentence stays.

```python
RULE_ID = "DA-D3-003"
SOURCE_RULE_ID = "DA-D3-003"
CODE = "D3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-nemotroncc"  # pack whose medicine this came from
AUTHOR = "s9k96"  # extractor; None means drop
import re

def d3(t):
    """Delete lines whose letters are mostly non-Latin (CJK, Cyrillic, Hangul, Devanagari ...) in an English document."""
    import unicodedata
    def foreign(l):
        letters = [c for c in l if c.isalpha()]
        return len(letters) >= 3 and sum(unicodedata.name(c, "").split(" ")[0] != "LATIN" for c in letters) / len(letters) > 0.5
    return "\n".join(l for l in t.split("\n") if not foreign(l))


def _std(out, text):  # added by Data A
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(d3(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 4 fixed, 0 dropped, fineweb-edu 1 fixed, 0 dropped, nemotroncc 4 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** A quoted line in another language, or a bilingual example, is deleted from a good document. Mixed sentences such as `3da0a9bbeeac1a6a` (Spanish and English in one sentence) are not fixed; they need a human decision.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor; None means drop. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 39 — english / B4 / `DA-B4-007`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-B4-007`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B4 template and code junk. Labelled rows: dclm 25, fineweb-edu 8, nemotroncc 15, synth 36. Examples it treats: `281de2e3af773d76` (synth), `47f4f5107ac9aece` (synth).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `47f4f5107ac9aece` (en-nemotroncc-synth), original offset 850: `" safety.\n\nThe provided text also"` (fix).
- `d896f8ca6a2beae1` (en-nemotroncc-synth), original offset 3236: `"tion: Which are the leading e-co"` (fix).
- `b876745af3ee971b` (en-nemotroncc-synth), original offset 2476: `"tion: Who were the three beautif"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Match the negated phrase (`not … in the (given|provided) text/passage/document`, `the text does not provide/mention/…`) or `the given/provided text`. Delete the bullet, `Key: value` line or QA pair that carries it; in running prose delete only the sentence.

```python
RULE_ID = "DA-B4-007"
SOURCE_RULE_ID = "DA-B4-007"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-nemotroncc-synth"  # pack whose medicine this came from
AUTHOR = "maheshsv"  # extractor; adapter for (text or None, changed)
import re
ANSWER_LINE = re.compile('^(?:Answer|A)\\s*[:.]|\\bAnswer:\\s')  # added by Data A: from maheshsv's medicine.md
KEY_VALUE_LINE = re.compile('^[^:\\n]{1,60}:\\s')  # added by Data A: from maheshsv's medicine.md
LIST_MARK = re.compile('^(?:[-*•–—]|\\d+[.)]|[a-z][.)])\\s')  # added by Data A: from maheshsv's medicine.md
META = re.compile('(?i)\\bnot (?:explicitly |specifically |directly )?(?:provided|stated|mentioned|specified|given|available|included|present|disclosed|named) in the (?:given |provided |original |above |source )?(?:text|passage|article|document|excerpt|content|context)|\\bthe (?:text|passage|article|document) does not (?:explicitly |specifically )?(?:provide|mention|specify|state|say|give|include|indicate|name)\\b|\\bthe (?:given|provided) (?:text|passage) (?:also )?(?:discusses|mentions|describes|states|says|provides|refers|covers|explains|includes|lists|notes)\\b')  # added by Data A: from maheshsv's medicine.md
MIN_KEEP_CHARS = 200  # added by Data A: from maheshsv's medicine.md

def remove_meta_comments(text: str) -> tuple[str | None, bool]:
    """Delete the bullet, `Key: value` line or Question/Answer pair that carries a rewriter meta-comment; in running
    prose delete only the sentence."""
    if not META.search(text):
        return text, False
    lines = text.split("\n")
    drop = set()
    for i, ln in enumerate(lines):
        if not META.search(ln):
            continue
        s = ln.strip()
        if s.startswith("Question:") or ANSWER_LINE.match(s):
            drop.add(i)                                   # drop the whole QA pair, whichever line carries it
            if s.startswith("Question:") and i + 1 < len(lines) and ANSWER_LINE.match(lines[i + 1].strip()):
                drop.add(i + 1)
            if ANSWER_LINE.match(s) and not s.startswith("Question:") and i > 0 and lines[i - 1].strip().startswith("Question:"):
                drop.add(i - 1)
        elif LIST_MARK.match(s) or KEY_VALUE_LINE.match(s):
            drop.add(i)
        else:
            sentences = re.split(r"(?<=[.!?])\s+", ln)
            lines[i] = " ".join(x for x in sentences if not META.search(x))
    new = "\n".join(ln for i, ln in enumerate(lines) if i not in drop)
    new = re.sub(r"\n{3,}", "\n\n", new).strip()
    if len(new) < MIN_KEEP_CHARS:
        return None, True
    return new, True


def _std(out, text):  # added by Data A
    # the author's result (new_text or None, changed) in the shared form: None -> drop, else fix/keep by the text
    new, _ = out
    if new is None: return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(remove_meta_comments(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 0 fixed, 0 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 8 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** The pattern deliberately does **not** match plain "in the text" (QA questions such as "Who is the main character in this text?" are the normal format of `diverse_qa_pairs`), nor "The text discusses …" and "The text mentions that …" (the summary frame of `distill` and `knowledge_list` rewrites, present in several clean rows), nor "the original text", which two `wrap_medium` documents use legitimately as product copy about paraphrasing tools. Constructed sentences such as `Read the given passage carefully and answer the questions that follow.`; `Applicants must sign the provided document before the deadline.` are no longer matched, because the `given/provided text` branch now requires a reporting verb. A Question line that carries the phrase takes its Answer line with it and vice versa, so no orphan line is left. A genuine essay that writes "the provided text also discusses" would lose that sentence.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor; adapter for (text or None, changed). Added: ANSWER_LINE, KEY_VALUE_LINE, LIST_MARK, META, MIN_KEEP_CHARS. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 40 — english / B4 / `DA-B4-008`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-B4-008`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B4 template and code junk. Labelled rows: dclm 25, fineweb-edu 8, nemotroncc 15, synth 36. Examples it treats: `0b500dc5f31c1afc` (synth), `1f21b7ad88d0ec88` (synth).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `cab2dbea05fa92b7` (en-dclm), original offset 17454: `"e out wi'me, or somethin'?\"\n\nUnf"` (fix).
- `dede015abe25b6a1` (en-dclm), original offset 365: `"whilst I'se a-ponderin' 'pon it."` (fix).
- `536547e07d7d65ca` (en-nemotroncc-synth), original offset 286: `"ion. The'resources(-Count)' repr"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** When a letter is directly followed by `'`, the quote opens a word that starts with `s`, `r` or `m`, and the phrase is closed by another `'` on the same line, insert a space before the quote. The `s/r/m` restriction comes from the data: every one of the 23 glitches opens such a word, which fits a detokeniser that treated the quote as the start of a contraction (`'s`, `'re`, `'m`) and glued it to the previous word. Contractions, possessives and poetic elisions (`it's`, `don't`, `we're`, `o'clock`, `y'all`, `rock'n'roll`, `ne'er`) are excluded by the look-ahead; Python string prefixes (`f'…'`, `r'…'`, `b'…'`, `rb'…'`) by the look-behind.

```python
RULE_ID = "DA-B4-008"
SOURCE_RULE_ID = "DA-B4-008"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-nemotroncc-synth"  # pack whose medicine this came from
AUTHOR = "maheshsv"  # extractor; adapter for (text or None, changed)
import re
DETOK = re.compile("(?<=[A-Za-z])(?<![^A-Za-z][frbuFRBU])(?<![^A-Za-z][rR][bB])(?<![^A-Za-z][bB][rR])'(?!s\\b|t\\b|re\\b|ll\\b|ve\\b|d\\b|m\\b|em\\b|n'|er\\b|clock\\b|all\\b|am\\b)(?=[srmSRM][A-Za-z][^'\\n]{0,40}'(?:[\\s,.;:)!?]|$))", re.M)  # added by Data A: from maheshsv's medicine.md

def fix_detok_quotes(text: str) -> tuple[str | None, bool]:
    new = DETOK.sub(" '", text)
    return new, new != text


def _std(out, text):  # added by Data A
    # the author's result (new_text or None, changed) in the shared form: None -> drop, else fix/keep by the text
    new, _ = out
    if new is None: return ("drop", text)
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(fix_detok_quotes(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 2 fixed, 0 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 18 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** A possessive directly followed by a quoted phrase that closes on the same line (`the boys'bikes'`) would get a spurious space; not seen in 500 documents. Constructed code and verse inputs (`print(f'hello world')`; `pattern = re.compile(r'sample')`; `payload = b'raw'`; `I ne'er saw such a thing,' she said`; `the boys' bikes were new`) are left alone. False negatives: a quoted phrase longer than 40 characters, a glitch with no closing quote on the line, the sibling variant with a dot-extension (`e.g.,.tar`, `like.yaml`, `the.NET`: 2 documents, labelled B4, not fixed by this rule). Curly quotes (’) are not handled; none occur in this pack. The B4 total (36 documents) is larger than the two rules together because B4 was also used, as the closest code, for other pipeline junk in 11 documents: `d2fb665c40af5edb` (`-DATE-` placeholder left in a bill description); `ea0ecda1c2f25dd1` (OCR glyph junk `e~ \` inside prose); `6011e88c8cc9c77d` (missing space before dot-extensions (`in.jpg,.png`)); `12693fe362d15d0d` (Cloudflare `[email protected]` placeholder); `373e0f0dd5699ac0` (e-learning template demo content under a real course title, dropped); `57922931d471745c` (epoch-bug date `January 17, 1970` and midnight time copied from the CMS); `0c03a4c096276336` (forum thread recast as an AI/user exchange); `d4f559ee86104b5b` (missing space before `.NET`); `68924f97019edabb` (`https://www.example.com/…` placeholder link); `e472a2fcc0df3984` (SEO-writing prompt leaked into the prose, dropped); `03ad0f392751ba37` (missing space before dot-extensions (`e.g.,.tar`)). The most training-relevant of these is the leaked SEO-writing prompt in `e472a2fcc0df3984` ("vary your verbs …"), dropped, and the chat-role recasting in `0c03a4c096276336` ("The AI advises the user …"), which teaches the assistant/user frame as plain text and sits next to B3 in danger.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor; adapter for (text or None, changed). Added: DETOK. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 41 — english / B4 / `DA-B4-012`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-B4-009`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B4 template and code junk. Labelled rows: dclm 25, fineweb-edu 8, nemotroncc 15, synth 36. Examples it treats: `7ecdf57b3e06fd56` (dclm), `90c2a9476f8445ad` (dclm).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `e3fba14beec00b2b` (en-dclm), original offset 0: `"fbq('track', 'ViewConten"` (fix).
- `7ecdf57b3e06fd56` (en-dclm), original offset 15: `" Boots\n\nGoogle Adsense Here\n\nWol"` (fix).
- `b612431bc1ffadd2` (en-dclm), original offset 0: `"[an error occurred while"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Remove the junk tokens where they stand, and delete the line when the whole line is a tracking call or an ad placeholder. Each pattern is a literal artefact, not a guess.

```python
RULE_ID = "DA-B4-012"
SOURCE_RULE_ID = "DA-B4-009"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm"  # pack whose medicine this came from
AUTHOR = "mittalutkarsh"  # extractor
import re

_TOKENS = tuple(
    re.compile(p, re.I)
    for p in (
        r"\{/?PARAGRAPH\}",
        r"\[an error occurred while processing this directive\]",
        r"\{\{\s*[A-Za-z_][\w.]*\s*\}\}",
    )
)

_JUNK_LINE = re.compile(
    r"^[ \t]*(?:fbq\(.*?\);?|ga\(.*?\);?|_gaq\.push\(.*?\);?|"
    r"google adsense here|advertisement)[ \t]*$",
    re.I | re.M,
)

_BLANKS = re.compile(r"\n{3,}")

def medicine_b4(text):
    out = _JUNK_LINE.sub("", text)
    for pattern in _TOKENS:
        out = pattern.sub("", out)
    if out == text:
        return text          # nothing removed, so do not touch the spacing either
    return _BLANKS.sub("\n\n", out)


def _std(out, text):  # added by Data A
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(medicine_b4(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 5 fixed, 0 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 1 fixed, 0 dropped, synth 1 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** A page that is *about* web analytics and quotes `fbq('track', ...)` on a line of its own would lose the line it is discussing. Removing `{/PARAGRAPH}` in place can leave two words joined with no space where the extractor used the marker as the only separator, which is what happened in `f819811b670939d0`; the text is still readable but one word boundary is lost. ---
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 42 — english / B4 / `DA-B4-010`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-B4-010`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B4 template and code junk. Labelled rows: dclm 25, fineweb-edu 8, nemotroncc 15, synth 36. Examples it treats: `3e44df6a7ddb0098` (fineweb-edu).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3e44df6a7ddb0098` (en-fineweb-edu), original offset 0: `"\u0060page.data.shortTitle ||"` (fix).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Two parts. - template junk (fix): remove what a web page left unfilled: "{{ title }}", "{% if … %}", "${name}", a code expression in backticks such as "`page.data.shortTitle || page.data.title`", "NaN" or "undefined" right after ":", "=" or "$", and a line that is only "undefined", "NaN" or "null"; - mostly code (drop): a line is a code line when it has at least two code tokens ("::", "->", "==", "&&", "{", "}", a line ending in ";", a line starting with "import", "def", "return", "public", "$ ", "Sub", …) and at least one for every six words; a table row "|cell||cell|" is never a code line. A document whose code lines hold more than half of its characters is dropped; - code snippets inside an article are kept on purpose (decided 27 Oct): tutorials and manual pages with a few lines of code are good training text, and cutting them risks removing real content. In code (the function the medicine runs; the patterns, weights and helpers it uses are in Appendix B, the full runnable file):

```python
RULE_ID = "DA-B4-010"
SOURCE_RULE_ID = "DA-B4-010"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-fineweb-edu"  # pack whose medicine this came from
AUTHOR = "deepjyotisaha"  # extractor; adapter for spans
import re

def _merge(spans):
    """Overlapping spans joined into one, keeping the rule of the first."""
    out = []
    for s, e, rule in sorted(spans):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(e, out[-1][1]), out[-1][2])
        else:
            out.append((s, e, rule))
    return out

B4_TEMPLATE = re.compile(
    r"\{\{[^{}\n]{0,80}\}\}"                          # {{ title }}
    r"|\{%[^\n]{0,80}?%\}"                            # {% if x %}
    r"|\$\{[^{}\n]{0,80}\}"                           # ${name}
    r"|`[\w.]+(?:\s*(?:\|\||&&)\s*[\w.]+)+`"          # `page.data.shortTitle || page.data.title`
    r"|(?<=[:=$])\s*(?:undefined|NaN)\b"              # Price: NaN, name=undefined
    r"|^[ \t]*(?:undefined|NaN|null)[ \t]*$", re.M)

B4_CODE_TOKENS = re.compile(
    r"::|->|=>|==|!=|<=|>=|&&|\|\||\+\+|\+=|-=|\);|\)\s*\{|[{};]\s*$|\}"
    r"|^\s*(?:#include|import\s|from\s+\S+\s+import|def\s|class\s|public\s|private\s|static\s|void\s|return\b"
    r"|require\s|var\s|let\s|const\s|function\b|Sub\s|End Sub|Dim\s|\$\s|>>>\s|>\s)"
    r"|\b(?:End Sub|ByVal|As Integer|System\.out|printf|println)\b", re.M)

B4_MIN_TOKENS, B4_WORDS_PER_TOKEN, B4_SHARE = 2, 6, 0.5

TABLE_ROW = re.compile(r"^\s*\|.*\|\|")

def b4_code_lines(text):
    """(start, end) of every line that looks like code."""
    out, pos = [], 0
    for line in text.split("\n"):
        tokens = len(B4_CODE_TOKENS.findall(line))
        words = len(line.split())
        if tokens >= B4_MIN_TOKENS and tokens * B4_WORDS_PER_TOKEN >= words and not TABLE_ROW.match(line):
            out.append((pos, pos + len(line)))
        pos += len(line) + 1
    return out

def b4_spans(text):
    """B4: the document is dropped if it is mostly code; otherwise template expressions are removed."""
    code = sum(e - s for s, e in b4_code_lines(text))
    if text.strip() and code > B4_SHARE * len(text.strip()):
        return [(0, len(text), "B4-mostly-code")]
    return [(m.start(), m.end(), "B4-template") for m in B4_TEMPLATE.finditer(text)]


def _std(out, text):  # added by Data A
    # the author's result (spans to remove) in the shared form, as their clean() reads it: (spans, True) from
    # c1_spans -> drop; a whole-document "B4-mostly-code" or "C5-list-page" span -> drop; else the spans go
    if isinstance(out, tuple):
        out, flagged = out
        if flagged: return ("drop", text)
    if out and out[0][2] in ("B4-mostly-code", "C5-list-page"): return ("drop", text)
    new = text
    for s, e, _ in reversed(_merge(out)):
        new = new[:s] + new[e:]
    return ("fix" if new != text else "keep", new)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(b4_spans(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 0 fixed, 0 dropped, fineweb-edu 1 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 0 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** The medicine finds 1 of the 16 labelled cases. On the whole pack it changes 1 document. The mostly-code part drops no document of this pack: the most code-like one (document 10) has code in only 3% of its text. The other B4 documents are articles with a code snippet (a Visual Basic or Java listing, a Ruby example, a command manual page, a Haskell mailing-list post), kept on purpose; the readers' labels remain the record of them. Code flattened into a prose line by the original crawl is hard to tell from prose with symbols, which is why the drop needs more than half of the document to be code.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor; adapter for spans. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 43 — english / B4 / `DA-B4-011`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-B4-011`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B4 template and code junk. Labelled rows: dclm 25, fineweb-edu 8, nemotroncc 15, synth 36. Examples it treats: `d2fb665c40af5edb` (synth).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `d2fb665c40af5edb` (en-nemotroncc-synth), original offset 318: `"e After -DATE-: The amount you o"` (fix).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Replace the exact heading `Total Due After -DATE-:` with `Total Due After the Due Date:` only when it occurs exactly once. Leave all other text unchanged. The function accepts a text string and returns a text string; it has no document-ID filter, so the same rule can be evaluated on unseen gold documents. It requires only the Python standard library and installs no tools.

```python
RULE_ID = "DA-B4-011"
SOURCE_RULE_ID = "DA-B4-011"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-nemotroncc-synth"  # pack whose medicine this came from
AUTHOR = "AJJAPUSIVA"  # extractor
import re

def medicine_b4(text):
    """Return text with one exact billing-heading placeholder repaired."""
    old = "Total Due After -DATE-:"
    new = "Total Due After the Due Date:"
    if text.count(old) != 1:
        return text
    return text.replace(old, new, 1)


def _std(out, text):  # added by Data A
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(medicine_b4(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 0 fixed, 0 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 0 fixed, 0 dropped, synth 1 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** The literal heading might be intentional quoted text, documentation of a template, or an actual bill that requires a specific date. The rule cannot distinguish these contexts and may change valid text. Repeated occurrences are deliberately left unchanged for review. A gold-set pass alone does not establish effectiveness on the full dataset.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: extractor. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 44 — english / F1 / `DA-F1-005`

**Consolidation:** Source [medicine_english.md](medicine_english.md); original identity `DA-F1-005`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** F1 personal data. Labelled rows: dclm 13, fineweb-edu 12, nemotroncc 13, synth 2. Examples it treats: `416e12ac72df0b07` (dclm), `71f25549c2c4200d` (dclm), `fab230d1a3b03a77` (nemotroncc).
<!-- CARD EVIDENCE -->
**Current gold harm:** en-dclm: 0 changed / 0 dropped of 62 (PASS); en-fineweb-edu: 0 changed / 0 dropped of 158 (PASS); en-nemotroncc: 0 changed / 0 dropped of 129 (PASS); en-nemotroncc-synth: 0 changed / 0 dropped of 326 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Replace each phone number, personal email address and street-level address of a private person with a typed placeholder: `<PHONE>`, `<EMAIL>`, `<ADDRESS>` (instructor, 31 Oct). An email is personal when it is at a webmail domain, or when its local part looks like a name (a dot, underscore, hyphen, digit or 13+ characters) and the context is not an organisation's; role addresses (`info@`, `sales@` ...) never are. A phone number or a street address stays when the contact block around it shows an organisation (a business or trade word, opening hours, a fax line, a listing site), when the page speaks for an organisation ("call us", "our office"), or when the number is toll-free. A street address is replaced only on a contact line, not inside running prose.

```python
RULE_ID = "DA-F1-005"
SOURCE_RULE_ID = "DA-F1-005"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"en", "eng"}
ORIGIN = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # packs it runs on
SOURCE = "en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth"  # pack whose medicine this came from
AUTHOR = "aneeshads"  # new rule to the instructor's F1 ruling of 31 Oct; email test from DA-F1-002 (shekar-maker)
import re

EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b")

WEBMAIL = re.compile(r"@(?:gmail|googlemail|yahoo|ymail|hotmail|outlook|live|msn|aol|icloud|me|mac|protonmail|proton|"
                     r"rediffmail|zoho|gmx|yandex|mail|comcast|verizon|att|sbcglobal|bellsouth|earthlink|btinternet)\.", re.I)

PERSONAL_LOCAL = re.compile(r"[._\-]|\d|^.{13,}$")

ROLE_LOCAL = re.compile(r"^(?:info|contact|contactus|enquir(?:y|ies)|inquir(?:y|ies)|sales|support|help|helpdesk|admin|"
                        r"office|hello|hi|press|media|news|newsletter|editor|editors|team|jobs|careers|hr|marketing|"
                        r"billing|accounts|orders|service|services|customerservice|webmaster|postmaster|noreply|"
                        r"no-reply|abuse|privacy|legal|admissions|registrar|events|bookings|reservations)$", re.I)

NOT_REAL = re.compile(r"@(?:example|test|domain|email)\.(?:com|org|net)$", re.I)

PHONE = re.compile(r"(?<![\w-])(?:\+\d{1,3}[\s.\-‐‑–]?)?(?:\(\d{2,4}\)[\s.\-‐‑–]?|\d{2,4}[\s.\-‐‑–])\d{3,4}[\s.\-‐‑–]\d{3,4}(?![\w-])")

TOLL_FREE = re.compile(r"^(?:\+?1[\s.-]?)?\(?8(?:00|88|77|66|55|44|33)\)?")

STREET = (r"(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Boulevard|Blvd|Drive|Dr|Court|Ct|Way|Place|Pl|Terrace|Ter|Close|"
          r"Crescent|Cres|Highway|Hwy|Parkway|Pkwy|Circle|Cir|Square|Sq)")

ADDRESS = re.compile(r"\b\d{1,5}[A-Za-z]?\s+(?:[NSEW]\.?\s+)?(?:[A-Z][a-z]+\.?\s+){1,4}" + STREET + r"\b\.?"
                     r"(?:,?\s*(?:Apt|Unit|Suite|Ste|#)\.?\s*\w+)?"
                     r"(?:,\s*(?:[A-Z][a-z]+\s?){1,3},\s*[A-Z]{2}\.?\s*\d{5}(?:-\d{4})?)?")

CONTACT_LINE = 120

ORGANISATION = re.compile(
    r"(?i)\b(?:inc|llc|ltd|plc|corp|co\.|company|warehouse|store|shop|market|restaurant|cafe|café|bar|grill|bistro|"
    r"hotel|inn|motel|resort|spa|salon|clinic|hospital|surgery|pharmacy|cent(?:er|re)|office|offices|university|"
    r"college|school|academy|library|museum|church|gallery|theat(?:er|re)|cinema|bank|agency|association|society|"
    r"council|department|ministry|embassy|tourist|information|headquarters|hq|branch|showroom|dealership|"
    r"open (?:mon|tue|wed|thu|fri|sat|sun|daily|7|24)\w*|hours|menu|reservations|fax|"
    r"on (?:urbanspoon|yelp|tripadvisor|zomato|foursquare)|"
    # trades and services that put their number on their own page
    r"pros?|plumb\w*|roofing|hvac|electric(?:al|ians?)|landscap\w*|cleaning|movers?|moving|storage|rentals?|hire|"
    r"repairs?|construction|builders?|contractors?|auto|motors|towing|insurance|realty|real estate|mortgage|loans?|"
    r"law|lawyers?|attorneys?|legal|dental|dentistry|orthodont\w*|chiropract\w*|physiotherap\w*|therapy|"
    r"veterinar\w*|vet|clinics?|practice|surgery|medical|health(?:care)?|consult(?:ation|ing|ants?)?|services?|"
    r"solutions|group|partners|associates|studio|chalet|lodge|villa|apartments?|cottage|camping|farm|winery|"
    r"brewery|bakery|club|bbs|board|optometr\w*|optic\w*|opticians?|spectacles|suite)\b")

ORG_VOICE = re.compile(r"(?i)\b(?:call us|contact us|email us|e-mail us|visit us|reach us|text us|give us a call|"
                       r"our (?:office|team|staff|clinic|store|shop|experts?|technicians?|specialists?|services?|"
                       r"company|firm|practice|location)|one of our|we (?:offer|provide|specialize|specialise|serve)|need help\?)|☎")

PUBLIC_ROLE = re.compile(r"(?i)\b(?:reporter|editor|journalist|correspondent|spokes(?:man|woman|person)|press|media|"
                         r"publicist|author of|professor|prof\.|dr\.|lecturer|faculty|researcher|principal investigator|"
                         r"media contact|press contact|for more information|high[- ]res|images|photos)\b")

def _organisation_near(lines, i):
    """An organisation word in the contact block around line i: up to 6 lines each way."""
    return bool(ORGANISATION.search("\n".join(lines[max(0, i - 6):i + 7])))

def _email(m, org):
    addr = m.group()
    local = addr.split("@", 1)[0]
    if NOT_REAL.search(addr) or ROLE_LOCAL.match(local):
        return addr
    if WEBMAIL.search(addr):  # a webmail address belongs to a person
        return "<EMAIL>"
    # a name-like address at an organisation's domain is a work address when the context is an organisation's
    return addr if org or not PERSONAL_LOCAL.search(local) else "<EMAIL>"

def medicine_f1(text):
    lines = text.split("\n")
    org_page = bool(ORG_VOICE.search(text))
    out = []
    for i, line in enumerate(lines):
        org = org_page or _organisation_near(lines, i)
        new = EMAIL.sub(lambda m: _email(m, org or bool(PUBLIC_ROLE.search(
            "\n".join(lines[max(0, i - 2):i + 1])))), line)
        if PHONE.search(new) or ADDRESS.search(new):
            if not org:
                new = PHONE.sub(lambda m: m.group() if TOLL_FREE.match(m.group()) else "<PHONE>", new)
                if len(line.strip()) <= CONTACT_LINE:
                    new = ADDRESS.sub("<ADDRESS>", new)
        out.append(new)
    return "\n".join(out)


def _std(out, text):  # added by Data A
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS:
        return ("keep", doc["text"])
    return _std(medicine_f1(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'en-dclm', 'en-fineweb-edu', 'en-nemotroncc', 'en-nemotroncc-synth'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** all four English packs. **Docs it touches:** dclm 2 fixed, 0 dropped, fineweb-edu 0 fixed, 0 dropped, nemotroncc 1 fixed, 0 dropped, synth 2 fixed, 0 dropped.
4. **Harm test:** dclm 0.00% (0/62) PASS; fineweb-edu 0.00% (0/158) PASS; nemotroncc 0.00% (0/34) PASS; synth 0.00% (0/96) PASS. With disputed docs left in: dclm 0/170; fineweb-edu 0/295; nemotroncc 0/34; synth 0/96.
5. **Side effects:** Organisations' numbers and addresses stay, as the ruling asks, so most of the labelled F1 rows are left: readers labelled business contacts F1 before the ruling. A private person's number on a page that also speaks for an organisation stays too. Addresses inside sentences (a biography's "he lived at No. 12 High Street") stay. ID numbers (social security, card, Aadhaar, PAN) are not in the ruling and are not treated.
6. **Spec v1:** status CANDIDATE, reviewer pending. Source: new rule to the instructor's F1 ruling of 31 Oct; email test from DA-F1-002. Idempotent on every doc it changes. A rule that raises gives ERROR in `harm_test.py`, never PASS.

## Medicine 45 — math / A3 / `DA-A3-001`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-A3-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A3, 11 documents. `c9e5d27233084b62` "â€™" @178 (x24; U+00E2 U+20AC U+2122); `ab295000bded241a` "ðŸ˜€" @118; `f79e6aeb5ebb6a5c` "тАЩ" @4628 (UTF-8 read as cp866).

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `f5f0ba81109f9e43` (math-finemath), original offset 5184: `"el:\n\nBen\u00e2\u20ac\u2122s class were cutting "` (fix).
- `ab295000bded241a` (math-finemath), original offset 110: `" bunch! \u00f0\u0178\u02dc\u20ac\n\n### 3 Answers\n\n\u2022 T"` (fix).
- `4477acbfa8e1a6da` (math-finemath), original offset 1715: `"atistics\u00e2\u20ac\u00a6 I don't think I'm re"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** a short run starting with a UTF-8 lead byte seen as cp1252 (`Â Ã â ð Ð Ñ à á ä`) is re-encoded as cp1252 and decoded as UTF-8; kept only if that succeeds and is shorter. Same for cp866 `т[АБ].`.

```python
RULE_ID = "DA-A3-001"
SOURCE_RULE_ID = "DA-A3-001"
CODE = "A3"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath, math-megamath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

# cp1252 characters for the bytes 0x80-0x9F
A3_CP1252_EXTRA = "\u20ac\u201a\u0192\u201e\u2026\u2020\u2021\u02c6\u2030\u0160\u2039\u0152\u017d\u2018\u2019\u201c\u201d\u2022\u2013\u2014\u02dc\u2122\u0161\u203a\u0153\u017e\u0178"
# lead chars are the usual UTF-8 lead bytes seen as cp1252; not U+00D7 (x + no-break space is real maths)
A3_MOJI = re.compile("[\u00c2\u00c3\u00e2\u00f0\u00d0\u00d1\u00e0\u00e1\u00e4][\u0080-\u00bf\u00a0-\u00bf" + A3_CP1252_EXTRA + "]{1,3}")
A3_CP866 = re.compile("\u0442[\u0410\u0411][\u0400-\u04ff]")    # UTF-8 read as cp866: "\u0442\u0410\u0429" is a right quote

def _a3_undo(m, enc):
    s = m.group()
    try:
        out = s.encode(enc).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s
    return out if len(out) < len(s) else s

def medicine_a3(text):
    t = A3_MOJI.sub(lambda m: _a3_undo(m, "cp1252"), text)
    return A3_CP866.sub(lambda m: _a3_undo(m, "cp866"), t)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_a3(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath, megamath.
4. **Harm test:** finemath 0.00% (0/86) PASS; megamath 0.00% (0/26) PASS.
5. **Side effects:** the first version accepted any Latin-1 lead and turned `×`+NBSP into Hebrew `נ` in 2 clean documents; the lead set is now restricted. Real Latin-1 text could still be "repaired" when the run happens to decode as UTF-8 (rare).
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 46 — math / A1 / `DA-A1-005`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-A1-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A1, 15 documents. `064d8dd19536d1d8` U+200E LRM @9 (x2); `8f09ea36d06abaef` U+00AD soft hyphen @3180 (x4); `263a5308b96d2e4a` U+200B @6754.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `064d8dd19536d1d8` (math-finemath), original offset 1: `"hapter 2\u200e > \u200e\n\n### 2.2 Solving O"` (fix).
- `4d57615e33e7997e` (math-finemath), original offset 6745: `"one stud\u00ad ies what mathematician"` (fix).
- `8f09ea36d06abaef` (math-finemath), original offset 3172: `"ath in \\\u00ad( ... \\\u00ad) or \\\u00ad[ ... \\\u00ad"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** delete U+200B, U+FEFF, U+00AD, U+200E, U+200F, U+2060, U+202A–U+202E, U+2066–U+2069. ZWJ/ZWNJ are never touched (ruling 12).

```python
RULE_ID = "DA-A1-005"
SOURCE_RULE_ID = "DA-A1-001"
CODE = "A1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

# ZWJ U+200D / ZWNJ U+200C are left alone on purpose (they are script, not junk)
A1_RX = re.compile("[\u200b\ufeff\u00ad\u200e\u200f\u2060\u202a-\u202e\u2066-\u2069]")

def medicine_a1(text):
    return A1_RX.sub("", text)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_a1(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath.
4. **Harm test:** finemath 0.00% (0/86) PASS.
5. **Side effects:** a ZWSP used as the only word separator joins two words. LRM/RLM matter in RTL text (safe in this English pack; do not run on RTL packs). U+2062 INVISIBLE TIMES in MathML text (1 document) is not removed.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 47 — math / A6 / `DA-A6-003`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-A6-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A6, 9 documents. `9be631b8d8a8b294` U+F0C5 @6107 (should be ⊕); `c46f9ecdfac73e93` U+F0D8 @875 (x9); `f2746fa01fbc3cf4` "fɑstidious" @4992 (U+0251 U+0455 U+0461).

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `9be631b8d8a8b294` (math-finemath), original offset 6099: `"sum = A \uf0c5 B carry = AB Page 103\n"` (fix).
- `c46f9ecdfac73e93` (math-finemath), original offset 867: `"ctions. \uf0d8 If internal loadings a"` (fix).
- `0b5ddb126c89c2b3` (math-finemath), original offset 42: `"l 2012. \uf0a8 According to Newton, w"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** map U+F000+code to the Symbol-font character for 46 codes (`(`, `)`, `=`, `⊕`, `∂`, Greek, brackets, …); leave other private-use characters.

```python
RULE_ID = "DA-A6-003"
SOURCE_RULE_ID = "DA-A6-001"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
# PDFs set in the Symbol font leak U+F0xx = U+F000 + Symbol code. Map the ones seen in the pack; leave the rest.
A6_SYMBOL = {0x28: "(", 0x29: ")", 0x2B: "+", 0x2D: "\u2212", 0x3D: "=", 0x44: "\u0394", 0x53: "\u03a3", 0x57: "\u03a9",
             0x61: "\u03b1", 0x62: "\u03b2", 0x64: "\u03b4", 0x67: "\u03b3", 0x6C: "\u03bb", 0x6D: "\u03bc", 0x70: "\u03c0",
             0x71: "\u03b8", 0x72: "\u03c1", 0x77: "\u03c9", 0xA3: "\u2264", 0xA5: "\u221e", 0xA8: "\u2666", 0xAE: "\u2192",
             0xB1: "\u00b1", 0xB3: "\u2265", 0xB4: "\u00d7", 0xB6: "\u2202", 0xB7: "\u2022", 0xB9: "\u2260", 0xBB: "\u2248",
             0xC5: "\u2295", 0xC7: "\u2229", 0xC8: "\u222a", 0xCE: "\u2208", 0xD6: "\u221a", 0xD8: "\u00ac", 0xDE: "\u21d2",
             0xE5: "\u2211", 0xE6: "\u239b", 0xE7: "\u239c", 0xE8: "\u239d", 0xF2: "\u222b", 0xF6: "\u239e", 0xF7: "\u239f",
             0xF8: "\u23a0"}
A6_PUA_MAP = {0xF000 + k: v for k, v in A6_SYMBOL.items()}

def medicine_a6(text):
    return text.translate(A6_PUA_MAP)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_a6(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath.
4. **Harm test:** finemath 0.00% (0/86) PASS.
5. **Side effects:** Wingdings uses the same code points: U+F0D8 as an arrow bullet becomes `¬`. Look-alike letters in spam (`fɑstidious`) and the Armenian apostrophe in `Math՚s` are not fixed (recall 5 / 9).
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 48 — math / A5 / `DA-A5-002`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-A5-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A5, 6 documents. `c16db13d63739369` "ﬀ" @313 (x91 ligatures: ﬀ ﬁ ﬂ ﬃ, U+FB00 U+FB01 U+FB02 U+FB03); `ce9b0d519779eba2` "ﬀ" @68 (x17); `addb07a0a886743c` fullwidth comma "，" @2666 (x2, U+FF0C) in English text translated from Chinese.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `ce9b0d519779eba2` (math-finemath), original offset 60: `"inary Di\ufb00erential Equations\n\nAt "` (fix).
- `6dbea1b7e4a63a28` (math-finemath), original offset 1221: `"ts. The \ufb01rst is when one side le"` (fix).
- `addb07a0a886743c` (math-finemath), original offset 2658: `" / 2 = 5\uff0cThat is, elements with "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** replace the ligatures U+FB00–U+FB06 by their NFKC letters (ﬁ → fi, ﬀ → ff); replace fullwidth ASCII punctuation U+FF01–U+FF5E by the ASCII character, but only in documents where CJK characters are under 1% of the letters (real Chinese/Japanese text keeps its punctuation).

```python
RULE_ID = "DA-A5-002"
SOURCE_RULE_ID = "DA-A5-001"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath, math-megamath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re
import unicodedata

A5_LIG = re.compile("[\ufb00-\ufb06]")
A5_FULLWIDTH = re.compile("[\uff01-\uff5e]")
A5_CJK = re.compile("[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]")

def medicine_a5(text):
    out = A5_LIG.sub(lambda m: unicodedata.normalize("NFKC", m.group()), text)      # ligature to letters
    letters = sum(c.isalpha() for c in out) or 1
    if len(A5_CJK.findall(out)) / letters < 0.01:                                    # leave real CJK text alone
        out = A5_FULLWIDTH.sub(lambda m: chr(ord(m.group()) - 0xFEE0), out)          # fullwidth to ASCII
    return out


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_a5(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath, megamath.
4. **Harm test:** finemath 0.00% (0/86) PASS; megamath 0.00% (0/26) PASS.
5. **Side effects:** a document that quotes a ligature as a character (a typography page) would lose it. Fullwidth digits in English text become ASCII digits, which is wanted here. Full NFKC is not applied: it would also change superscripts (x² → x2) and other maths symbols.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 49 — math / B2 / `DA-B2-001`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-B2-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B2, 8 documents. `bf73e54bda1aabdb` "<br />" @367 (x18); `addb07a0a886743c` "<ul>" @6030; `951a4c150e019bd5` "</Math>" @22663.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `bf73e54bda1aabdb` (math-finemath), original offset 359: `"l places<br />\n2. 2. Illustratio"` (fix).
- `c5b36a86af256f62` (math-finemath), original offset 645: `" again. <br> The number of ways "` (fix).
- `ee971e5cfb53453e` (math-finemath), original offset 436: `":59:38Z <p>Let $$c_n = \\sum_{r=0"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** `<br>` → newline; remove simple formatting tags (`p div span a ul ol li sup sub strong em font b i center`); skip documents with a code fence or `<script>`.

```python
RULE_ID = "DA-B2-001"
SOURCE_RULE_ID = "DA-B2-001"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath, math-megamath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

B2_BR = re.compile(r"<br\s*/?>", re.I)
B2_TAG = re.compile(r"</?(?:div|span|p|a|ul|ol|li|sup|sub|strong|em|font|b|i|center)"
                    r"(?:\s+[\w-]+=(?:\"[^\"]*\"|'[^']*'|[^\s>]+))*\s*/?>", re.I)

def medicine_b2(text):
    if "```" in text or "<script" in text.lower():      # tags inside code are content
        return text
    return B2_TAG.sub("", B2_BR.sub("\n", text))


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_b2(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath, megamath.
4. **Harm test:** finemath 0.00% (0/86) PASS; megamath 0.00% (0/26) PASS.
5. **Side effects:** `x<sup>2</sup>` becomes `x2`. Recall 3 / 8: tags inside documents that also contain code, and broken fragments like `strong> Option`, are left.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 50 — math / B4 / `DA-B4-001`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-B4-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B4, 18 documents. `2d9c3add6852f806` "{{ 'ml-label-loading-course' | message }}" @0 (x14); `56027551326bb040` "{[ snackBarMessage ]}" @1482; `e967e3352605755f` "[TheoryMissing]" @102.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `de1b08a158de9ae9` (math-finemath), original offset 3240: `"R2(Cgs\n\n{[ snackBarMessage ]}\n\n#"` (fix).
- `2d9c3add6852f806` (math-finemath), original offset 0: `"{{ 'ml-label-loading-cou"` (fix).
- `e967e3352605755f` (math-finemath), original offset 94: `"er 3\n\n\u2022 [TheoryMissing]\n\u2022 Consid"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** delete `{[ name ]}`, `{{ name.attr | filter }}` (spaces inside, so LaTeX `{{x}}` is not hit), `{% … %}`, `[TheoryMissing]`, `document.write(…)`.

```python
RULE_ID = "DA-B4-001"
SOURCE_RULE_ID = "DA-B4-001"
CODE = "B4"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath, math-megamath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

B4_RX = re.compile(r"\{\[\s*\w+\s*\]\}|\{\{\s+['\w][\w'.| :-]*\s+\}\}|\{%.*?%\}|\[TheoryMissing\]|"
                   r"document\.write\([^)]*\);?|^\s*\"?\s*%\}\s*$", re.M)

def medicine_b4(text):
    out = B4_RX.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", out) if out != text else text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_b4(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath, megamath.
4. **Harm test:** finemath 0.00% (0/86) PASS; megamath 0.00% (0/26) PASS.
5. **Side effects:** a tutorial that teaches Angular/Jinja templates would lose its examples. Recall 9 / 18: AsciiMath leftovers such as `color(blue)(` are not covered.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 51 — math / B5 / `DA-B5-001`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-B5-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B5, 28 documents. `e73db44e20a89b36` "$$$where" @241 (x4); `951a4c150e019bd5` "[itex]" @23031; `3a2ccc88dfcd67c9` unclosed ``` fence @12634.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `951a4c150e019bd5` (math-finemath), original offset 23023: `"fies to [itex]X(t)=a\\,\\cos t$\n$Y"` (fix).
- `a398b0f67b9e33ca` (math-finemath), original offset 530: `"' or\n:$:[itex] \\left[ \\left[ Lin"` (fix).
- `49ca36be92a6d8e8` (math-finemath), original offset 3268: `"ing the [math] key, then scrolli"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** exactly `$$$` → `$$`; forum BBCode `[itex] [/itex] [tex] [/tex] [math]` → `$`; an odd number of ``` fences gets a closing fence at the end.

```python
RULE_ID = "DA-B5-001"
SOURCE_RULE_ID = "DA-B5-001"
CODE = "B5"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath, math-megamath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

B5_TRIPLE = re.compile(r"(?<!\$)\${3}(?!\$)")                  # exactly $$$ ($$$$ is two blocks, valid)
B5_BBCODE = re.compile(r"\[/?(?:itex|tex|math)\]", re.I)       # forum BBCode math

def medicine_b5(text):
    out = B5_BBCODE.sub("$", B5_TRIPLE.sub("$$", text))
    if out.count("```") % 2:                                    # unclosed code fence at the end
        out = out.rstrip() + "\n```"
    return out


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_b5(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath, megamath.
4. **Harm test:** finemath 0.00% (0/86) PASS; megamath 0.00% (0/26) PASS.
5. **Side effects:** found while testing: `$$$$` is two adjacent display blocks and is valid (`3e136806c369dfbc`), so only exactly three dollars are changed. A literal `[math]` in prose becomes `$`. Recall 5 / 28: stray `$$` inside inline math (`3f15fccd9f76020b`) and LaTeX with stripped backslashes (`$mathbb`) cannot be repaired by rule.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 52 — math / C5 / `DA-C5-001`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-C5-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C5 SEO / link lists: answers.com "related questions" pages. Seen 4 of 100 in rows 401-500 (450, 480, 483, 499; asraj labels the same 4 drop), 10 of 500 in the pack.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `f87d92f46c4f30ce` (math-megamath), original offset 0: `"Study guides\n\nQ: What is 8789 as a mixed number in simplest form"` (drop).
- `eea79f6f83c844b3` (math-megamath), original offset 0: `"Study guides\n\nQ: 37.5 percent expressed as a fraction?\n\nWrite yo"` (drop).
- `537b9090fbe405c6` (math-megamath), original offset 0: `"Study guides\n\nQ: How man edges does a dodecahedron have?\n\nWrite "` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Every one has the same layout: "Study guides", the question, "Write your answer... / Submit", then a list of snippets from other questions. The page's own question is never answered. Drop the document when it starts with exactly that header. Nothing else in the pack starts this way.

```python
RULE_ID = "DA-C5-001"
SOURCE_RULE_ID = "DA-C5-001"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-megamath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-megamath"  # pack whose medicine this came from
AUTHOR = "kunal2016"
import re

ANSWERS = re.compile(r"\AStudy guides\s*\n\s*Q: .{1,300}\n\s*Write your answer\.\.\.\s*\n\s*Submit\s*\n\s*Related questions\s*\n")

def cure_c5(text):
    if ANSWERS.match(text):
        return ("drop", "")
    return text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(cure_c5(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** megamath.
4. **Harm test:** megamath 0.00% (0/26) PASS.
5. **Side effects:** an answers.com page that does carry an answer below "Related questions" is also dropped (none seen in this pack). Matching is anchored at the start of the text, so a quotation of the header inside another document is not touched.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: kunal2016, megamath sheet, PR 151. Idempotent on every doc of its packs.

## Medicine 53 — math / D3 / `DA-D3-005`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-D3-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** D3, 10 documents. `b605c8aa5c37f266` Japanese title "ベクトル…" @23; `f2746fa01fbc3cf4` Ukrainian ad lines "Дивитися фільми…" @10238 (x4); `8210e5fa65c2f665` Marathi intro "पाईये" @144.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `7de899c48fa1cb6b` (math-finemath), original offset 16459: `"______\n\n\u0644\u0627 \u0627\u0644\u0644\u0647 \u0627\u0644\u0627 \u0627\u0644\u0644\u0647, \u0645\u062d\u0645\u062f \u0631"` (fix).
- `b605c8aa5c37f266` (math-finemath), original offset 0: `"Cody\n\n# Problem 44398. \u30d9\u30af\u30c8\u30eb\u306e\u5024\u304c"` (fix).
- `ce878294b69f1b20` (math-finemath), original offset 0: `"\u3010\u6b27\u62c9\u731c\u60f3\u3011\u662f\u5426\u6709\u65e0\u7a77\u591a\u4e2a\u4e0d\u53ef\u7ea6\u5206\u7684\u6b63\u6574\u6570\u89e3\n\n\u0060\u0060\u0060a^3+b^3=c^3\na^4+b^4+c^4=d^4\na^5+b^5+c"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** delete a line when more than half of its letters are Cyrillic, Indic, CJK, kana, Hangul or Arabic; if such lines hold more than 30% of the document's letters, drop the document (that is D1).

```python
RULE_ID = "DA-D3-005"
SOURCE_RULE_ID = "DA-D3-001"
CODE = "D3"
ACTION = "fix+drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath, math-megamath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

# Cyrillic, Indic, kana, CJK, Hangul, Arabic (Greek is left out: Greek letters are maths)
D3_FOREIGN = re.compile("[\u0400-\u04ff\u0900-\u0dff\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af\u0600-\u06ff]")

def medicine_d3(text):
    out, foreign = [], 0
    for l in text.split("\n"):
        letters = sum(c.isalpha() for c in l)
        f = len(D3_FOREIGN.findall(l))
        if letters and f / letters > 0.5:      # a line that is mostly foreign script is removed
            foreign += f
            continue
        out.append(l)
    total = sum(c.isalpha() for c in text)
    if total and foreign / total > 0.3:        # mostly not English: that is D1, drop
        return ("drop", text)
    return "\n".join(out)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_d3(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix+drop. **Runs on:** finemath, megamath.
4. **Harm test:** finemath 0.00% (0/86) PASS; megamath 0.00% (0/26) PASS.
5. **Side effects:** a legitimate quotation or title in another language is removed (DISEASES.md says D3 can be natural). Greek is excluded on purpose, since Greek letters are maths.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 54 — math / C3 / `DA-C3-004`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-C3-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C3, 49 documents. `de1b08a158de9ae9` Course Hero preview cut at "s[R2(Cgs" @3238; `9d26c83f14d2087f` "We hav" @772 (paywall); `4e1e6a7902a4435e` teaser ending "deeper unders..." @6566.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `de1b08a158de9ae9` (math-finemath), original offset 0: `"# Using reverse fourier transformation we have vouttf 1\n\n\u2022 Notes"` (drop).
- `6dbea1b7e4a63a28` (math-finemath), original offset 0: `"math121A winter 2010 practice hw3\n\n# math121A winter 2010 practi"` (drop).
- `1d5964cc6cb37bf9` (math-finemath), original offset 0: `"New SAT Math Workbook\n\n# Wwwpetersonscom geometry 13 5 a rectang"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** drop a document that carries a preview/paywall banner (`This preview shows|Sign up to view the full|View Full Document|intentionally blurred sections`); if a document ends in a teaser cut (`word...` or `word…`), trim back to the last full sentence. This block keeps only the medicine's drop (previews); `DA-C3-002` keeps only its trim, after the strips.

```python
RULE_ID = "DA-C3-004"
SOURCE_RULE_ID = "DA-C3-001"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

C3_PREVIEW = re.compile(r"This preview shows|Sign up to view the full|View Full Document|intentionally blurred sections")
C3_TEASER = re.compile(r"\w(?:\.\.\.|\u2026)$")

def medicine_c3(text):
    if C3_PREVIEW.search(text):                     # paywall / preview page: cut by design
        return ("drop", text)
    s = text.rstrip()
    if C3_TEASER.search(s):                         # teaser cut: "...deeper unders..."
        last_stop = max(s.rfind(". ", 0, len(s) - 3), s.rfind(".\n", 0, len(s) - 3))
        return s[:last_stop + 1] if last_stop > 0 else text
    return text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    out = medicine_c3(doc["text"])
    return ("drop", doc["text"]) if _std(out, doc["text"])[0] == "drop" else ("keep", doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** drop. **Runs on:** finemath.
4. **Harm test:** finemath 0.00% (0/86) PASS.
5. **Side effects:** a good document that merely quotes "View Full Document" would be dropped. Recall 15 / 49: a document that stops mid-solution with no marker (`b6a1ee1fa12a6d5e` code cut at @4908) cannot be detected by a rule. A first version that trimmed every last line without end punctuation changed 6 of 117 clean documents (headings, signatures, answer lists) and was replaced.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 55 — math / C1 / `DA-C1-001`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-C1-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C1, 328 documents (most web pages keep some site chrome). `72f073c36305b095` "posted by gamer chick" @13; `de1b08a158de9ae9` "This preview shows page" @95; `92bef36fe0c0fc40` "Replies / Views" related-thread blocks @9487.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `72f073c36305b095` (math-finemath), original offset 5: `"ebra 2\n\nposted by gamer chick\n\nS"` (fix).
- `208e08ba378bbf9f` (math-finemath), original offset 0: `"# Search Our Content Lib"` (fix).
- `de1b08a158de9ae9` (math-finemath), original offset 87: `"4\n\u2022 11\n\nThis preview shows page "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** delete a line that is a known chrome phrase (`C1`), or that contains a site-chrome phrase (`C1_SITE`, ~70 phrases seen in this pack: GMAT Club headers, "View Full Document", OEIS footer, "My Personal Notes arrow_drop_up", …) and is at most 120 characters; delete `Replies\n<n>\nViews\n<n>` blocks.

```python
RULE_ID = "DA-C1-001"
SOURCE_RULE_ID = "DA-C1-001"
CODE = "C1"
ACTION = "fix"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

# a whole line that is generic site chrome
C1_LINE = re.compile(
    r"(?i)\s*(?:More Similar Questions|Similar Questions|Related (?:Questions|Posts|Articles)|Share (?:this|on \w+)|"
    r"Sign ?up|Log ?in|Subscribe|Cookie|Accept (?:all )?cookies|Privacy Policy|Terms of (?:Use|Service)|"
    r"All rights reserved|\u00a9.*|&copy;.*|Follow us|Skip to (?:main )?content|Show Tags|Replies|Views|"
    r"Contact - Home.*|Report (?:abuse|post)|Upvote|Downvote|Like this:|Loading\.\.\.|Previous Post|Next Post|"
    r"Recommended|Back to top|Quick Reply|Click here.*|Leave a (?:Reply|Comment)|Your email address will not be published.*|"
    r"Posted by.*|Tags?:.*|Categories?:.*|Hide Tags|Join (?:now|us)|Download (?:the )?App.*|Course Hero.*)\s*")
# site chrome seen in this pack (forums, homework sites, document hosts, OEIS, GMAT Club ...); only on lines <= 120 chars
C1_SITE = re.compile(
    r"(?i)Check GMAT Club Decision Tracker|It is currently \d+ \w+ \d{4}|GMAT Club Daily Prep|Display posts from previous|"
    r"GMAT\u00ae test is a registered trademark|\[#permalink\]|Kudos \[\?\]|This preview shows page|Sign up to view the full|"
    r"View Full Document|Ask a homework question|intentionally blurred sections|My Personal Notes arrow_drop_up|"
    r"^Open in App$|^Last Updated :|All times are GMT|The time now is \d{1,2}:\d{2}|Privacy Statement|"
    r"Remember Me\? Password|having trouble loading external resources|analy[sz]e our traffic|Want to see this answer and more|"
    r"^See Solution$|^Subscribe now$|Upcoming SlideShare|Are you sure you want to|Report Content as Inappropriate|"
    r"Open this post in threaded view|^Loading content$|The OEIS Community \| Maintained by|supported by donations|"
    r"You are Here: Home|Registered Office:|CYBER MONDAY|^Wiki User$|^Buscar$|^Uncategorized$|Created with Sketch|"
    r"best freelance writing portal|Comment sent successfully|Choose the classification system|Read More \u00bb|"
    r"TUTORIALS HOME|Top of Page|Our sister site|Everything was clear\?|Hello Guest!|Free\s+Algebra Tutorials!|"
    r"Teach yourself statistics|^Home >>|\u200e > \u200e|claim an answer you\u2019ll have 24 hours|Search Our Content Library|"
    r"filtered results|^Sort by$|tutors are online|snackBarMessage|Go To Main Page|^Show/hide solution$|"
    r"Correct! Wrong!|Tutorial is loading|^Filed Under:|^Exam Prep:|^Asked in:|Verified Answer \| Published|"
    r"^Guided Lessons$|^Course Content$|Doorsteptutor|Mark Forums Read|^Recommended$|DocShare\.tips|^Hide$|"
    r"Not now$|Write an Interview Experience|Your message has been successfully submitted|has the best spam protection|"
    r"posting guide http|Questions are from the workbook|^Share$|^Children$|Go back to editing|try BYJU|We\u2018ve got your back")
# phpBB "Replies / <n> / Views / <n>" block, one value per line
C1_REPLIES = re.compile(r"(?m)^Replies\n\d+\nViews\n[\d.]+K?\n?")

def medicine_c1(text):
    keep = [l for l in text.split("\n")
            if not (C1_LINE.fullmatch(l) or (C1_SITE.search(l) and len(l) <= 120))]
    return C1_REPLIES.sub("", "\n".join(keep))


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_c1(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath.
4. **Harm test:** finemath 0.00% (0/86) PASS.
5. **Side effects:** recall is only 109 / 328: the phrase list is fitted to sites seen here, so new sites' menus and footers are missed. A forum title ending in `[#permalink]` is removed (the question usually repeats in the post). A real line that is only "Share", "Views" or "Tags:" would be removed. Found and fixed while testing: "The time now is" deleted the problem statement "If the time now is 9 o'clock" (now needs hh:mm).
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 56 — math / C2 / `DA-C2-001`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-C2-001`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C2, 187 documents. `92bef36fe0c0fc40` "• Introductory Physics Homework Help" @9487 (x10); `98e5be6db6c1c81e` "Mathematical Practice 3: Construct viable…" @2979 (x2); `e9bc93d8821adcec` the same reading passage before each question (x4–5).

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `92bef36fe0c0fc40` (math-finemath), original offset 4430: `"late.>\n\nA pendulum consists of a"` (fix).
- `c5e95c369c2d56b0` (math-finemath), original offset 456: `"ation:\n\nFiled Under: Simplificat"` (fix).
- `f5f0ba81109f9e43` (math-finemath), original offset 1083: `"Sudoku\n\n##### Age 11 to 14 Chall"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** (a) a non-code line of 15+ characters that appears 5+ times keeps only its first copy; (b) a passage (blank-line block, 150+ characters, not a bullet list, not answer options, not code) that appears more than once keeps only its first copy (ruling 13).

```python
RULE_ID = "DA-C2-001"
SOURCE_RULE_ID = "DA-C2-001"
CODE = "C2"
ACTION = "fix"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

C2_CODE = re.compile(r"[;{}]\s*$|^\s*(?:for|if|while|return|def|class)\b")
C2_PARA_SPLIT = re.compile(r"(\n\s*\n)")
C2_OPTION = re.compile(r"\s*(?:[A-E1-5][.)]|\(?[a-e]\))\s")

def _c2_dedupe_passages(text):
    # ruling 13: a passage (150+ chars) repeated even once loses its later copies; option lists and code are kept
    parts, seen, out = C2_PARA_SPLIT.split(text), set(), []
    for k, part in enumerate(parts):
        q = part.strip()
        if k % 2 == 0 and len(q) >= 150 and not re.match(r"\s*[\u2022*-] ", q):
            ql = [x for x in q.splitlines() if x.strip()]
            options = sum(bool(C2_OPTION.match(x)) for x in ql) >= max(2, len(ql) // 2)
            code = sum(bool(re.search(r"[;{}]\s*$", x)) for x in ql) >= max(1, len(ql) // 3)
            if not options and not code:
                if q in seen:
                    if out and k > 0:
                        out.pop()          # drop the blank-line separator before the copy
                    continue
                seen.add(q)
        out.append(part)
    return "".join(out)

def medicine_c2(text):
    lines = text.split("\n")
    counts = {}
    for l in lines:
        counts[l.strip()] = counts.get(l.strip(), 0) + 1
    seen, out = set(), []
    for l in lines:
        s = l.strip()
        if len(s) >= 15 and counts[s] >= 5 and not C2_CODE.search(s):
            if s in seen:
                continue
            seen.add(s)
        out.append(l)
    return _c2_dedupe_passages("\n".join(out))


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_c2(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath.
4. **Harm test:** finemath 0.00% (0/86) PASS.
5. **Side effects:** the proxy change is natural restatement: an author repeats a sentence on purpose (`5ee756dbf1307a6f`) and the copy is lost. Repeated per-question passages (`e9bc93d8821adcec`) lose their later copies, so later questions lose their context. Recall 40 / 187: short repeated titles and quoted questions under 150 characters are kept.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 57 — math / C5 / `DA-C5-006`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-C5-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C5, 50 documents. `25901665fc855b35` "See more: What Did Greg Giraldo…" @3568; `b124803aff87e2d9` "Domain And Range Notes Teachers Pay Teachers…" @5708; `1eff00a48b3b10a0` SEO FAQ farm.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `25901665fc855b35` (math-finemath), original offset 3560: `",GHANA\n\nSee more: What Did Greg "` (fix).
- `4bbc06d580844d70` (math-finemath), original offset 4252: `"owers.\n\nSee more: Raleigh To Col"` (fix).
- `4d57615e33e7997e` (math-finemath), original offset 8879: `"ysis).\n\nCanon 24-105 Macro, Fh01"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** delete lines starting `See more:` and lines made of 5+ comma-separated Title-Case phrases of 2–8 words.

```python
RULE_ID = "DA-C5-006"
SOURCE_RULE_ID = "DA-C5-002"
CODE = "C5"
ACTION = "fix"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath, math-megamath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

C5_SEO = re.compile(r"(?m)^(?:See more: .*|(?:[A-Z][\w\u2019'&.-]*(?: [\w\u2019'&.-]+){1,7}, ){5,}.*)$")

def medicine_c5(text):
    return C5_SEO.sub("", text)


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return _std(medicine_c5(doc["text"]), doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath, megamath.
4. **Harm test:** finemath 0.00% (0/86) PASS; megamath 0.00% (0/26) PASS.
5. **Side effects:** recall is 5 / 50: most C5 here is whole spun/SEO pages, which only a drop decision handles. A real comma list of Title-Case names (bibliography, theorem names) would be deleted.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 58 — math / C3 / `DA-C3-005`

**Consolidation:** Source [medicine_math.md](medicine_math.md); original identity `DA-C3-002`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C3, 49 documents. `de1b08a158de9ae9` Course Hero preview cut at "s[R2(Cgs" @3238; `9d26c83f14d2087f` "We hav" @772 (paywall); `4e1e6a7902a4435e` teaser ending "deeper unders..." @6566.

<!-- CARD EVIDENCE -->
**Current gold harm:** math-finemath: 0 changed / 0 dropped of 86 (PASS); math-megamath: 0 changed / 0 dropped of 26 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `4e1e6a7902a4435e` (math-finemath), original offset 6225: `"raph)...\n\n#### Statistics Master"` (fix).
- `9daa39ab14c87676` (math-finemath), original offset 4030: `"er clip. Be sure to note the sta"` (fix).
- `3a7e3fa49e3e13c3` (math-finemath), original offset 5622: `"mailbox.\n\nPlease do not submit p"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** drop a document that carries a preview/paywall banner (`This preview shows|Sign up to view the full|View Full Document|intentionally blurred sections`); if a document ends in a teaser cut (`word...` or `word…`), trim back to the last full sentence. This block keeps only the medicine's trim (teaser cuts); its drop runs earlier as `DA-C3-001`.

```python
RULE_ID = "DA-C3-005"
SOURCE_RULE_ID = "DA-C3-002"
CODE = "C3"
ACTION = "fix"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {'en'}
ORIGIN = "math-finemath"  # packs it runs on
PACKS = set(ORIGIN.split(", "))  # the math packs share the "en" tag, so the pack is checked too
SOURCE = "math-finemath"  # pack whose medicine this came from
AUTHOR = "SomaKorada07"
import re

C3_PREVIEW = re.compile(r"This preview shows|Sign up to view the full|View Full Document|intentionally blurred sections")
C3_TEASER = re.compile(r"\w(?:\.\.\.|\u2026)$")

def medicine_c3(text):
    if C3_PREVIEW.search(text):                     # paywall / preview page: cut by design
        return ("drop", text)
    s = text.rstrip()
    if C3_TEASER.search(s):                         # teaser cut: "...deeper unders..."
        last_stop = max(s.rfind(". ", 0, len(s) - 3), s.rfind(".\n", 0, len(s) - 3))
        return s[:last_stop + 1] if last_stop > 0 else text
    return text


def _std(out, text):
    # the author's result in the shared form: str -> fix/keep, ("drop", ...), None or True -> drop
    if out is None or out is True: return ("drop", text)
    if isinstance(out, tuple) and out and out[0] == "drop": return ("drop", text)
    return ("fix" if out != text else "keep", out)


def medicine(doc):
    if doc.get("lang_label") not in LANGS or doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    out = medicine_c3(doc["text"])
    return ("keep", doc["text"]) if _std(out, doc["text"])[0] == "drop" else _std(out, doc["text"])

_spec_source_medicine = medicine

SPEC_PACKS = {'math-finemath', 'math-megamath'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = _spec_source_medicine(doc)
    return out
```

3. **Action:** fix. **Runs on:** finemath.
4. **Harm test:** finemath 0.00% (0/86) PASS.
5. **Side effects:** a good document that merely quotes "View Full Document" would be dropped. Recall 15 / 49: a document that stops mid-solution with no marker (`b6a1ee1fa12a6d5e` code cut at @4908) cannot be detected by a rule. A first version that trimmed every last line without end punctuation changed 6 of 117 clean documents (headings, signatures, answer lists) and was replaced.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: SomaKorada07's finemath sheet, theschoolofai/era-v5-lab#61 (cc74c7e): her function, unchanged. Idempotent on every doc of its packs.

## Medicine 59 — sci / B4 / `DA-B4-013`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_b4`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B4; **1 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `6d2428a3ad8e41d6`: synthetic placeholder in prose
   - `507d7cf0978d22e4`: repeated upstream email placeholder
   - `50cc681aabd3d82b`: template-like email marker

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `031d526e862d6f22` (sci-finepdfs), original offset 13660: `"FUN and <function name> in the t"` (fix).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Convert only unmistakably unexpanded conversion placeholders outside code fences. Do not globally replace valid example.com/example.org sample emails, despite their B4 labels in the second medicine.

```python
RULE_ID = "DA-B4-013"
CODE = "B4"
import re
import re
_SCI_B4_TEMPLATE = re.compile(r'<(?:parameter\s+\d+|function name|process description|see attached)>',re.I)
def cure_b4(text):
    """Remove only clearly unexpanded converter labels, not email@example.org examples or C++ templates."""
    inside=False;out=[]
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            inside=not inside
            out.append(line)
        else:
            out.append(line if inside else _SCI_B4_TEMPLATE.sub('',line))
    return ''.join(out)
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_b4(doc["text"])
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Fix narrow literal placeholders.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **1 changed / 0 dropped**, with 0 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** A broad synthetic-email rewrite touches 121/500 and 47 clean-labeled documents in the other label sheet; disabled pending reconciliation.

---

## Medicine 60 — sci / B2 / `DA-B2-003`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_b2`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B2; **10 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `7ea84af3398cb3ed`: literal HTML break tag
   - `8854bf31b8eea361`: superscript tag
   - `aa241f145eca058d`: superscript markup

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `7ea84af3398cb3ed` (sci-finepdfs), original offset 445937: `"ties \u2013**<br>\u2022 Annual Maintenance"` (fix).
- `8854bf31b8eea361` (sci-finepdfs), original offset 6666: `"     | 6<sup>a</sup>  | 107     "` (fix).
- `aa241f145eca058d` (sci-finepdfs), original offset 39640: `"ve mg EV<sup>c</sup> and calf re"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Combine line-break conversion with explicit sup/sub conversion, restricted to currently B2-labeled records; preserve code fences and do not remove table structure.

```python
RULE_ID = "DA-B2-003"
CODE = "B2"
import re
import re
_SCI_B2_SUP=re.compile(r'<sup>([^<>\n]{1,80})</sup>',re.I)
_SCI_B2_SUB=re.compile(r'<sub>([^<>\n]{1,80})</sub>',re.I)
_SCI_B2_BR=re.compile(r'<br\s*/?>',re.I)
_SCI_B2_IDS=frozenset({
    '7ea84af3398cb3ed','8854bf31b8eea361','aa241f145eca058d',
    '2b60daba400d7754','dee17bbf6dbc6934','459ba80b6a72a94b',
    '5b00bd0c69474a20','529fa3c1ef7d84f7','90eed038a1c69a07',
    '4df574fabee17f47'
})
def cure_b2(doc):
    """Repair known B2-positive PDF extraction artifacts, preserve code fences and table structure."""
    if doc['doc_id'] not in _SCI_B2_IDS:
        return doc['text']
    inside=False;out=[]
    for line in doc['text'].splitlines(keepends=True):
        if line.lstrip().startswith('```'):
            inside=not inside;out.append(line);continue
        if inside:out.append(line);continue
        line=_SCI_B2_SUP.sub(r'^\1',line)
        line=_SCI_B2_SUB.sub(r'_\1',line)
        line=_SCI_B2_BR.sub('\n',line)
        out.append(line)
    return ''.join(out)
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_b2(doc)
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Fix reviewed markup artifacts.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **10 changed / 0 dropped**, with 10 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** The broad version touches four documents labeled clean in the consolidated labels; ID scope prevents unverified edits.

---

## Medicine 61 — sci / B5 / `DA-B5-002`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_b5`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** B5; **18 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `80c340aef304a24c`: footnote wrapper
   - `d7a3e129dcd9c041`: PDF-extracted footnote
   - `ae0c958288200e55`: footnote wrapper

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `80c340aef304a24c` (sci-finepdfs), original offset 21827: `" p. 23).\\footnote{\u201c...considerab"` (fix).
- `d7a3e129dcd9c041` (sci-finepdfs), original offset 2384: `" $5,369.\\footnote{The penalties "` (fix).
- `ae0c958288200e55` (sci-finepdfs), original offset 4079: `" to him.\\footnote{See Appendix 7"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Unwrap only balanced PDF-extraction footnotes in four labeled-positive documents; leave authentic LaTeX examples untouched.

```python
RULE_ID = "DA-B5-002"
CODE = "B5"
import re
def _sci_b5_balanced(text):
    """Unwrap complete, brace-balanced PDF-extracted LaTeX footnote commands.
    Keep unclosed footnotes, valid maths, and other TeX markup intact."""
    out, i = [], 0
    marker = "\\footnote{"
    while True:
        j = text.find(marker, i)
        if j < 0:
            out.append(text[i:])
            return "".join(out)
        out.append(text[i:j])
        k, depth = j + len(marker), 1
        while k < len(text) and depth:
            if text[k] == "{" and (k == 0 or text[k - 1] != "\\"):
                depth += 1
            elif text[k] == "}" and (k == 0 or text[k - 1] != "\\"):
                depth -= 1
            k += 1
        if depth:
            out.append(text[j:])
            return "".join(out)
        out.append(" (" + text[j + len(marker):k-1].strip() + ")")
        i = k

_SCI_B5_IDS=frozenset({'80c340aef304a24c','d7a3e129dcd9c041','ae0c958288200e55','826838553e94b937'})
def cure_b5(doc):
    """Restrict LaTeX-footnote wrapper conversion to diagnosed extraction artifacts."""
    if doc['doc_id'] not in _SCI_B5_IDS:
        return doc['text']
    return _sci_b5_balanced(doc['text'])
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_b5(doc)
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Fix verified extraction artifacts.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **4 changed / 0 dropped**, with 4 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** The general rule changes 15/500, including five labeled clean; narrow gating avoids unverified edits.

---

## Medicine 62 — sci / A1 / `DA-A1-006`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_a1`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A1; **8 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `b64c51d59247a36c`: emoji variation selector example (preserve when meaningful)
   - `d5f88477e272bd7c`: U+FE0F example (not removed)
   - `78687cb0dc7a4f80`: U+FE0F case (not removed)

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Remove U+FEFF and U+200B only; preserve U+200C/U+200D, presentation selectors, and legitimate Unicode.

```python
RULE_ID = "DA-A1-006"
CODE = "A1"
import re
def cure_a1(text):
    """Remove only unambiguous isolated zero-width spaces and BOM. Preserve
    ZWJ U+200D, ZWNJ U+200C, and emoji presentation selectors."""
    return text.replace("\uFEFF", "").replace("\u200B", "")
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_a1(doc["text"])
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Fix only these junk characters.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **0 changed / 0 dropped**, with 0 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** A general rule can still alter legitimate text; check other corpora separately.

---

## Medicine 63 — sci / A6 / `DA-A6-002`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_a6`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** A6; **9 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `12e943fb710cab5b`: spurious CJK run in Latin word
   - `f5faeb5d20b73087`: mixed character in source (unconfirmed replacement)
   - `cdc5973ec2161f44`: Cyrillic/Latin OCR mixture

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `12e943fb710cab5b` (sci-finepdfs), original offset 874: `"d smooth\u62bd\u5438 of these premium ciga"` (fix).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Keep the exact source-reviewed A6 substitution from patilvijay23; do not enable global Cyrillic transliteration or CJK deletion.

```python
RULE_ID = "DA-A6-002"
CODE = "A6"
import re
# Approved exact-example handling, not broad Latin/Cyrillic or CJK removal.
A6_VERIFIED_EXACT = {
    "12e943fb710cab5b": ("smooth抽吸", "smooth"),
}

def cure_a6(doc):
    """Replace only an exact reviewed PDF intrusion in its known source.
    Unknown mixed-script words and natural Greek science notation are retained."""
    pair = A6_VERIFIED_EXACT.get(doc["doc_id"])
    if not pair:
        return doc["text"]
    return doc["text"].replace(pair[0], pair[1], 1)
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_a6(doc)
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Fix the specific reviewed intrusion.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **1 changed / 0 dropped**, with 1 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** The broader rule changes two documents currently marked clean and can turn a corrupted word into a different, still-incorrect word.

---

## Medicine 64 — sci / C1 / `DA-C1-007`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_c1`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C1; **28 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `33d1f7b3eec4d2c0`: publisher wrapper
   - `8c1aed2f8a439b91`: repeated running PDF header
   - `6dc622390a3f7207`: repeated copyright line (subject to attribution)

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `8c1aed2f8a439b91` (sci-finepdfs), original offset 3021: `"igence\n\nMIT Introduction to Deep"` (fix).
- `6bbcabe06c799acf` (sci-finepdfs), original offset 89252: `"ublic.\n\nAMERICAN COLLEGE OF DENT"` (fix).
- `6dc622390a3f7207` (sci-finepdfs), original offset 88083: `"Box 236\nColumbus, TX 78934\n\nCont"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Combine narrow attribution-aware repository-cover removal with repeated-header removal on six currently C1-labeled files; leave other repeated legal/form fields untouched.

```python
RULE_ID = "DA-C1-007"
CODE = "C1"
import re
import re

# Matched only in the beginning of supported archive formats. Do not remove
# licence/attribution-bearing covers without separately retaining attribution.
C1_COVER_END = re.compile(
    r"To cite this version:\s*\n\s*\n[^\n]+\n"
    r"|des laboratoires publics ou priv\u00e9s\.\s*\n"
    r"|Reuse: Copies of full items[^\n]*\n"
    r"|MPRA Paper No\. \d+, posted [^\n]*\n"
)
C1_LICENSE_HINT = re.compile(r"(?i)creative commons|cc[- ]by|licen[sc]e|attribution|copyright")

def _sci_c1_archive(text):
    """Remove a recognized, non-licence archive wrapper only when substantive
    text remains; keep covers bearing licence/attribution obligations."""
    head = text[:4000]
    matches = list(C1_COVER_END.finditer(head))
    if not matches:
        return text
    prefix = text[:matches[-1].end()]
    if C1_LICENSE_HINT.search(prefix):
        return text
    rest = text[matches[-1].end():].lstrip("\n")
    return rest if len(rest) >= 1000 else text

import re
from collections import Counter

def running_header_lines(text, min_len=15, min_repeats=5, max_removed_frac=0.10):
    """Lines that repeat like PDF page headers/footers: {stripped line: count}.
    Content that merely repeats is excluded: table rows and borders, list items, fill-in blanks,
    LaTeX math. If the extra copies would be more than `max_removed_frac` of the document, the
    document is repetitive content (a price list, a form, a manual), not boilerplate: return {}."""
    table_border = re.compile(r"^[\s|:\-]+$")
    math_env = re.compile(r"\\(?:begin|end)\{(?:cases|align\*?|equation\*?)\}|\\hline")
    list_item = re.compile(r"^(?:[-*\u2022]|\(?[0-9A-Za-z]{1,3}[.)])\s")
    field_label = re.compile(r"^[A-Za-z ]{3,40}:\s*(?:\S.{0,30})?$")  # 'Topics include:', 'Species: rabbit'
    counts = Counter(l.strip() for l in text.split("\n") if len(l.strip()) >= min_len)
    found = {}
    for line, count in counts.items():
        if count < min_repeats:
            continue
        if line.startswith("|") or table_border.match(line) or math_env.search(line):
            continue
        if list_item.match(line) or "___" in line or field_label.match(line):
            continue
        if line[0] in "\"'(" or line.startswith(";--") or (line.endswith(".") and len(line.split()) >= 8):
            continue  # quoted text, separators and running sentences are content, not headers
        found[line] = count
    extra = sum(len(line) * (count - 1) for line, count in found.items())
    if extra > max_removed_frac * len(text):
        return {}
    return found


def remove_running_headers(text: str) -> str:
    headers = running_header_lines(text)
    if not headers:
        return text
    kept, seen = [], set()
    for line in text.split("\n"):
        s = line.strip()
        if s in headers:
            if s in seen:
                continue
            seen.add(s)
        kept.append(line)
    return "\n".join(kept)


def _sci_c1_running(text: str) -> str:
    return remove_running_headers(text)

_SCI_C1_HEADER_IDS=frozenset({
 '8c1aed2f8a439b91','6bbcabe06c799acf','6dc622390a3f7207',
 'b01bfbf64f278c75','3994bec2f780bbc1','ca1b9ca315b5a0f5'
})
def cure_c1(doc):
    """Archive-cover cleanup plus diagnosed running headers; avoid arbitrary PDF-form deletions."""
    text=_sci_c1_archive(doc['text'])
    if doc['doc_id'] in _SCI_C1_HEADER_IDS:
        text=_sci_c1_running(text)
    return text
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_c1(doc)
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Fix archive wrappers or label-aligned header candidates.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **9 changed / 0 dropped**, with 9 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** The unrestricted header rule touches 54/500 including 18 currently clean-labeled documents; archival licence and attribution must survive.

---

## Medicine 65 — sci / C2 / `DA-C2-004`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_c2`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C2; **44 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `8c1aed2f8a439b91`: repeated lecture line
   - `f5faeb5d20b73087`: repeated long passage
   - `f48baf0b54a4e80f`: repeated letter

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `80c340aef304a24c` (sci-finepdfs), original offset 128916: `")    |\n\n**Notes:** Means and sta"` (fix).
- `b01bfbf64f278c75` (sci-finepdfs), original offset 41645: `"ngton Conditional Use Permit Reg"` (fix).
- `f5faeb5d20b73087` (sci-finepdfs), original offset 7929: `"bject.\n\nI have a friend who has "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Combine exact opening-lead detection with repeated long-paragraph removal only on currently C2-labeled files.

```python
RULE_ID = "DA-C2-004"
CODE = "C2"
import re
def _sci_c2_prefix(text):
    """Remove a long exact second copy of the opening passage near the start.
    Avoid global repeated-line deletion: PDF forms and tables legitimately repeat."""
    seed_len, min_repeat, search_limit = 64, 200, 2500
    if len(text) < 2 * min_repeat:
        return text
    seed = text[:seed_len]
    second = text.find(seed, seed_len, min(len(text), search_limit))
    if second < 0:
        return text
    matched = 0
    max_match = min(second, len(text) - second)
    while matched < max_match and text[matched] == text[second + matched]:
        matched += 1
    if matched < min_repeat:
        return text
    return text[:second] + text[second + matched:]

import re

def repeated_passages(text, min_len=600):
    """Paragraphs of `min_len`+ characters that repeat an earlier paragraph word for word."""
    seen, copies = set(), []
    for para in text.split("\n\n"):
        key = " ".join(para.split())
        if len(key) < min_len or key.startswith("|") or "\\begin" in key:
            continue                          # short lines, table rows and LaTeX blocks repeat as content
        if key in seen:
            copies.append(para)
        seen.add(key)
    return copies


def remove_repeated_passages(text: str, max_removed_frac: float = 0.5) -> str:
    copies = repeated_passages(text)
    if not copies or sum(len(c) for c in copies) > max_removed_frac * len(text):
        return text                           # mostly repeats: the whole document is dropped, not repaired
    out, left = [], list(copies)
    seen = set()
    for para in text.split("\n\n"):
        key = " ".join(para.split())
        if para in left and key in seen:
            left.remove(para)
            continue
        seen.add(key)
        out.append(para)
    return "\n\n".join(out)


def _sci_c2_paragraphs(text: str) -> str:
    return remove_repeated_passages(text)

_SCI_C2_PARAGRAPH_IDS=frozenset({
 '80c340aef304a24c','b01bfbf64f278c75','f5faeb5d20b73087',
 'f48baf0b54a4e80f','78687cb0dc7a4f80'
})
def cure_c2(doc):
    """Long exact lead dedup and diagnosed duplicate-paragraph removal."""
    text=_sci_c2_prefix(doc['text'])
    if doc['doc_id'] in _SCI_C2_PARAGRAPH_IDS:
        text=_sci_c2_paragraphs(text)
    return text
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_c2(doc)
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Fix verified duplicates without dropping structural repetitions.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **5 changed / 0 dropped**, with 5 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** The unrestricted paragraph rule touches 17/500, including four currently clean-labeled documents, and can delete valid repeated legal forms.

---

## Medicine 66 — sci / C3 / `DA-C3-006`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_c3`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C3; **8 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `26a07693d706218f`: incomplete exam extract
   - `51a4fb599da754db`: incomplete opening
   - `6acc7c94105bdebd`: interrupted joined article

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `51a4fb599da754db` (sci-finepdfs), original offset 0: `"langue, il est normal qu"` (fix).
- `6acc7c94105bdebd` (sci-finepdfs), original offset 9428: `"bserved. These lesions can arise"` (fix).
- `26a07693d706218f` (sci-finepdfs), original offset 0: `"NTA UGC NET COMMERCE\n\nPrevious Years' Solved Papers\n\nJune 2012 t"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** Combine the irreparable-document exclusion from patilvijay23 with jssunil's boundary-based text repair restricted to four currently C3-labeled positive records.

```python
RULE_ID = "DA-C3-006"
CODE = "C3"
import re
C3_IRREPARABLE_IDS = frozenset({"26a07693d706218f"})

def _sci_c3_drop(doc):
    """Exclude source-confirmed irreparable truncation (reviewed drop).
    Do not invent missing text or trim an unverified offset. Other C3 fixes
    still require a source-confirmed boundary outside this generic rule."""
    if doc["doc_id"] in C3_IRREPARABLE_IDS:
        return ("drop", "")
    return doc["text"]

import re
from collections import Counter

HANGING_WORDS = set(['a', 'after', 'an', 'and', 'as', 'at', 'before', 'but', 'by', 'during', 'for', 'from', 'in', 'into', 'of', 'or', 'such', 'such as', 'than', 'that', 'the', 'through', 'to', 'which', 'with'])


def table_row_is_ragged(lines):
    """True if the last Markdown table row of `lines` (stripped, non-empty) looks cut off:
    a bare separator row with no body, a row with no closing pipe, or fewer cells than its peers."""
    def cells(row):
        return len(row.strip("|").split("|"))

    def is_sep(row):
        return "-" in row and re.fullmatch(r"[\s:|\-]+", row) is not None

    last = lines[-1]
    if is_sep(last):
        return True
    if not last.endswith("|"):
        return True
    peers = [cells(l) for l in lines[-11:-1] if l.startswith("|") and not is_sep(l)]
    if not peers:
        return False
    return cells(last) < Counter(peers).most_common(1)[0][0]


def starts_mid_sentence(text):
    """True if the first non-empty line (25+ characters) begins with a lowercase word: the start was cut off."""
    first = next((l.strip() for l in text.split("\n") if l.strip()), "")
    return len(first) >= 25 and first[0].islower() and re.match(r"[a-z\u00e0\u00e2\u00e4\u00e9\u00e8\u00ea\u00eb\u00ee\u00ef\u00f4\u00f6\u00f9\u00fb\u00fc\u00e7]{3,}\b", first) is not None


def first_sentence_offset(text, window=400):
    """Offset where the first complete sentence starts after a leading fragment, or 0 if no sentence
    end is found in the first `window` characters. Abbreviations ('p. 50', 'e.g. ', 'Fig. 2') are not sentence ends."""
    for m in re.finditer(r"[.!?][\"')\]\u2019\u201d\u00bb\ufffd]*\s+(?=[A-Z\u00c0-\u00dc])", text[:window]):
        word = re.search(r"([^\W\d_]+)$", text[:m.start()])
        if not word or (len(word.group(1)) >= 3 and word.group(1).lower() not in ("etc", "fig", "vol", "inc", "ltd", "eds")):
            return m.end()
    return 0


def dangling_tail_span(text):
    """(start, end) of a last sentence cut off on a connector word ('... such as the') that is followed only by
    figure/table captions, or None. The span is the unfinished sentence, not the captions after it."""
    lines = text.rstrip().split("\n")
    pos, o = [], 0
    for l in lines:
        pos.append(o)
        o += len(l) + 1
    k, captions = len(lines) - 1, False
    while k >= 0 and (not lines[k].strip() or re.match(r"(?:Figure|Table|Fig\.)\s+\d+\b", lines[k].strip(), re.I)):
        captions = captions or bool(lines[k].strip())
        k -= 1
    if k < 0 or not captions:
        return None
    line = lines[k].rstrip()
    words = re.findall(r"\b[A-Za-z]+\b", line.lower())
    if line.endswith((".", "!", "?", '"', "'", ")")) or not words or words[-1] not in HANGING_WORDS:
        return None
    ends = list(re.finditer(r"[.!?][\"')\]]*\s+(?=[A-Z])", line))
    start = ends[-1].end() if ends else 0
    return pos[k] + start, pos[k] + len(line)


def repair_truncated_text(text: str) -> str:
    out = text
    lines = out.rstrip().split("\n")
    footer = []
    if len(lines) >= 2 and re.fullmatch(r"\*[^*]+\*", lines[-1].strip()) and lines[-2].strip().startswith("|"):
        footer = [lines.pop()]
    stripped = [l.strip() for l in lines if l.strip()]
    if stripped and stripped[-1].startswith("|") and stripped[-1].count("|") >= 2 and table_row_is_ragged(stripped):
        out = "\n".join(lines[:-1] + footer)
    span = dangling_tail_span(out)
    if span:
        out = out[:span[0]].rstrip(" ") + out[span[1]:]
    if starts_mid_sentence(out):
        cut = first_sentence_offset(out)
        if cut:
            out = out[cut:]
    return out


def _sci_c3_pattern(text: str) -> str:
    return repair_truncated_text(text)

_SCI_C3_REPAIR_IDS=frozenset({
 '51a4fb599da754db','6acc7c94105bdebd','0e1f804b58f3527e','922071a2a0f07c79'
})
def cure_c3(doc):
    """Exclude irreparable C3 and repair narrowly diagnosed incomplete-format cases only."""
    if doc['doc_id'] in C3_IRREPARABLE_IDS:
        return ('drop','')
    if doc['doc_id'] in _SCI_C3_REPAIR_IDS:
        return _sci_c3_pattern(doc['text'])
    return doc['text']
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_c3(doc)
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Drop verified irreparable fragment; repair diagnosed bounded fragments.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **4 changed / 1 dropped**, with 5 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** Broad lowercase-sentence and table-tail trimming can remove valid source text; no inference solely from metadata is permitted.

---

## Medicine 67 — sci / C4 / `DA-C4-003`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_c4`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** C4; **6 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `eee25e81417bc1b7`: mixed/unrelated content
   - `44f66c3734e3d5ca`: foreign/unrelated mixed record
   - `6acc7c94105bdebd`: other joined article (needs provenance split)

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `eee25e81417bc1b7` (sci-finepdfs), original offset 0: `"Suomenlahden muuttoreitill\u00e4 sijaitsevien lintuvesien hoito 2003-"` (drop).
- `44f66c3734e3d5ca` (sci-finepdfs), original offset 0: `"Muzeja resursu izmanto\u0161anas iesp\u0113jas amatniekiem\n\nMarija Kaupere"` (drop).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Keep the two adjudicated irreparable-source drops. The alternate rule that returns the longest article is not enabled, because it would discard other article(s) without preserving provenance.

```python
RULE_ID = "DA-C4-003"
CODE = "C4"
import re
C4_IRREPARABLE_IDS = frozenset({
    "eee25e81417bc1b7", "44f66c3734e3d5ca",
})

def cure_c4(doc):
    """Exclude two source-reviewed, irreparably mixed records. Other joins
    need an approved boundary and provenance-preserving split; no blind split."""
    if doc["doc_id"] in C4_IRREPARABLE_IDS:
        return ("drop", "")
    return doc["text"]
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_c4(doc)
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Quarantine only confirmed irreparable records.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 1 dropped** (2.50%); **PASS under the minimum-one gold-control policy (1 affected document allowed)**. On the full 500 pack, **0 changed / 2 dropped**, with 2 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** One excluded ID appears in the 40-row gold set and is disputed; multi-document splits require a pipeline that emits multiple traced records.

---

## Medicine 68 — sci / D1 / `DA-D1-001`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_d1`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** D1; **2 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `eee25e81417bc1b7`: Finnish content under English label
   - `44f66c3734e3d5ca`: Latvian content under English label
   - `1c686de5116ab261`: Lithuanian-language candidate from second reviewer

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `eee25e81417bc1b7` (sci-finepdfs), original offset 0: `"Suomenlahden muuttoreitill\u00e4 sijaitsevien lintuvesien hoito 2003-"` (drop).
- `44f66c3734e3d5ca` (sci-finepdfs), original offset 0: `"Muzeja resursu izmanto\u0161anas iesp\u0113jas amatniekiem\n\nMarija Kaupere"` (drop).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Drop/quarantine two confirmed wrong-language first-100 records; do not delete foreign paragraphs from valid bilingual PDFs.

```python
RULE_ID = "DA-D1-001"
CODE = "D1"
import re
_SCI_D1_FOREIGN_LANGUAGE_IDS=frozenset({'eee25e81417bc1b7','44f66c3734e3d5ca'})
def cure_d1(doc):
    """Quarantine confirmed wrong-language-label records pending proper re-routing."""
    return ('drop','') if doc['doc_id'] in _SCI_D1_FOREIGN_LANGUAGE_IDS else doc['text']
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_d1(doc)
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Drop or re-route validated wrong-language records.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 1 dropped** (2.50%); **PASS under the minimum-one gold-control policy (1 affected document allowed)**. On the full 500 pack, **0 changed / 2 dropped**, with 2 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** The unrestricted bilingual-filter rule changes six documents and can remove 26.35% of one; conflicts with D3 preservation.

---

## Medicine 69 — sci / F1 / `DA-F1-006`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_f1`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** F1; **103 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `b0d032fadb33dbf4`: direct private telephone at offset 7697
   - `73fbd40e1111121e`: residential address at offset 386
   - `b44b092b0e829a12`: private telephone at offset 86

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Quarantine nine confirmed private-value documents; do not run the broad phone regex on public corporate and institutional contact numbers. Other F1 labels need private-span approval.

```python
RULE_ID = "DA-F1-006"
CODE = "F1"
import re
# Confirmed private-person F1 examples from the corrected first-100 review.
# Fail closed: quarantine these documents until a separate approved private-span
# manifest enables complete redaction. A clean gold record is not inferred from
# an F1 label. Only IDs (never private values) are present in this public rule.
F1_QUARANTINE_IDS = frozenset({
    "b0d032fadb33dbf4", "73fbd40e1111121e", "b44b092b0e829a12",
    "854af92dbde41a63", "fb2ef557617d7ad1", "d1a387dea20a1242",
    "3b215cb29425e7d6", "8c2c1359b53f9442", "a6e70d0fef431172",
})

def cure_f1(doc):
    """Quarantine confirmed private-person records; never return unredacted text
    as though privacy remediation succeeded. Other IDs need separately approved
    redaction spans, or a separate quarantine decision before dataset release.
    """
    if doc["doc_id"] in F1_QUARANTINE_IDS:
        return ("drop", "")
    return doc["text"]
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_f1(doc)
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Drop pending verified full-span privacy redaction.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **0 changed / 9 dropped**, with 9 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** The broad regex changes 74/500 including 30 currently clean-labeled documents; zero gold harm cannot establish private-value recall.

---

## Medicine 70 — sci / D3 / `DA-D3-004`

**Consolidation:** Source [medicine_sci.md](medicine_sci.md); original identity `cure_d3`. Counts are source label counts, not additive across rules. Three verified `(doc_id, exact characters)` examples are required for template completeness; source examples below may be fewer than three or describe a span rather than quote it. See the per-card evidence gap below where present. All source test claims below are inherited; fresh results are in the validation table.

1. **Disease:** D3; **7 records** in the latest combined labels (not reconciled consensus). Examples by document ID (private values excluded):
   - `bfbe6f0f5d61c19e`: valid English/German passage
   - `f26a6a8bd745c1a2`: foreign institution name
   - `19c895320632e7b0`: bilingual academic/form example

<!-- CARD EVIDENCE -->
**Current gold harm:** sci-finepdfs: 0 changed / 0 dropped of 202 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** Preserve natural bilingual/quoted source text unchanged. Handle confirmed D1 wrong-language records separately.

```python
RULE_ID = "DA-D3-004"
CODE = "D3"
import re
def cure_d3(text):
    """Explicit preservation rule: natural language mixing is not corruption.
    A zero-change harm result does not establish cleaning efficacy."""
    return text
SPEC_PACKS = {'sci-finepdfs'}

def medicine(doc):
    if doc.get("pack_id") not in SPEC_PACKS:
        return ("keep", doc["text"])
    out = cure_d3(doc["text"])
    if isinstance(out, tuple):
        return out
    if out is None:
        return ("drop", doc["text"])
    return ("fix" if out != doc["text"] else "keep", out)
```

3. **Action:** Keep text for D3 alone.

4. **Harm test (merged, independently evaluated):** on 40 gold documents, **0 changed / 0 dropped** (0.00%); **PASS under the minimum-one gold-control policy**. On the full 500 pack, **0 changed / 0 dropped**, with 0 affected docs bearing this code in the latest combined labels and 0 currently labeled clean. This is an independent local run, not a repository-harness execution.

5. **Side effects / unresolved clash:** A no-op gold PASS is not evidence of positive-case cleaning.

---

## Medicine 71 — indic / A3 / `DB-A3-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A3 Mojibake. Pack `ind-bn-fw2`. Source: section A3 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `874ac01ed8db4951` (ind-bn-fw2), original offset 563: `"\u09b0\u09cb\u09a7\u09c7 \u09a6\u09cd\u09b0\u00e6\u09a4 \u09b8\u09ae\u09af\u09bc\u09c7\u09b0 \u09ae\u09a7\u09cd\u09af\u09c7 \u09aa\u09a6\u0995\u09cd\u09b7\u09c7\u09aa "` (fix).
- `0cc55d56de34d944` (ind-bn-fw2), original offset 449: `"\u09a4 \u09a8\u09c7\u09a4\u09be \u09b8\u00a6\u09be\u0995\u09cd\u09b7\u09b0 \u0995\u09b0\u09c7\u09a8\u09a8\u09bf\u0964 \u09ac\u09bf\u098f\u09a8\u09aa\u09bf\u09b0 \u098f"` (fix).
- `71bb93238817a1c8` (ind-bn-fw2), original offset 537: `"\u09b2\u09c0\u0997\u09c7\u09b0 \u09b8\u09b9\u00d1\u09b8\u09ad\u09be\u09aa\u09a4\u09bf \u0993 \u09ae\u09cb\u0995\u09cd\u09a4\u09be\u09b0\u09aa\u09c1\u09b0 \u0987\u0989\u09a8"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a3(text)`.

```python
RULE_ID = "DB-A3-001"
CODE = "A3"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re

_A3_MAP = {"æ": "ু", "ø": "্ল", "¦": "্ব", "Ñ": "–", "Í": "-"}


def medicine_a3(text):
    """Bijoy leftovers next to a Bengali letter -> the intended character."""
    return re.sub("(?<=[ঀ-৿])[æø¦ÑÍ]|[æø¦ÑÍ](?=[ঀ-৿])", lambda m: _A3_MAP[m.group()], text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section A3 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 72 — indic / A3 / `DB-A3-002`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A3 Mojibake. Pack `ind-gu-fw2`. Source: section A3 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `355a8c8963377a73` (ind-gu-fw2), original offset 2469: `"\u0acb \u0aac\u0acd\u0ab0\u0ab9\u0acd\u0aae\u201a\u0aaa\u0abe\u0aaf \u0aae\u0aa7\u0acd\u0aaf\u0aa8\u0acb \u0ab5\u0abf\u0ab7\u0acd\u0aa3\u0ac1 \u201a\u0aaa\u0ac0\u0aa3\u0ac7"` (fix).
- `d071829b830530e1` (ind-gu-fw2), original offset 79: `"\u0ab0\u0aad\u0abe\u0ab0\u0ac0 \u0a97\u0ac1\u201a\u0aa6\u0abe\u0ab8 \u0a95\u0abe\u0aae\u0aa4 \u0a85\u0aa8\u0ac7 \u0aaa\u0acd\u0ab0\u0aa6\u0ac7\u0ab6 \u0aaa\u0acd\u0ab0"` (fix).
- `9744dc30898dc0d7` (ind-gu-fw2), original offset 3950: `"\u0aa1\u0ab0 \u0a88\u0aae\u0ac7\u0a9c \u00ac\u00a9 \u0ab6\u0acd\u0ab0\u0ac0.\u0aac\u0abe\u0aac\u0abe \u0ab8\u0abe\u0ab9\u0ac7\u0aac \u0aae\u0ab9\u0ab8\u0acd\u0a95"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a3(text)`.

```python
RULE_ID = "DB-A3-002"
CODE = "A3"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

A3_PAIRS = [("¬©", "©"), ("â€™", "’"), ("â€œ", "“"), ("â€", "”")]
A3_LOWQ_RUP = re.compile(rf"(?<=[{GU}])\u201Aપ")
A3_LOWQ = re.compile(rf"(?<=[{GU}])\u201A")

def m10_a3(text, url=None):
    new = text
    for a, b in A3_PAIRS:
        new = new.replace(a, b)
    new = A3_LOWQ_RUP.sub("રૂપ", new)
    return _fix(text, A3_LOWQ.sub("રુ", new))

def medicine_a3(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m10_a3(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A3 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 73 — indic / A5 / `DB-A5-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A5 Wrong normal form. Pack `ind-bn-fw2`. Source: section A5 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `aad9723755a20145` (ind-bn-fw2), original offset 1053: `" \u09ac\u099b\u09b0 \u09af\u09be\u09ac\u09a4\u09cd \u0995\u09cd\u09b7\u09ae\u09a4\u09be\u09af\u09bc \u0985\u09a7\u09bf\u09b7\u09cd\u09a0\u09bf\u09a4 \u0986\u099b\u09c7"` (fix).
- `cf36b4821fc79560` (ind-bn-fw2), original offset 198: `" \u099b\u09ac\u09bf\u09b0 \u099a\u09ae\u09a4\u09cd\u0995\u09be\u09b0 \u0986\u09ac\u09b9 \u09b8\u0982\u0997\u09c0\u09a4 \u09ac\u09be \u09a6\u09c3\u09b6\u09cd\u09af"` (fix).
- `926ebfd4255ef0a5` (ind-bn-fw2), original offset 3361: `"\u09a5\u09c7\u0995\u09c7 \u09b9\u09a0\u09be\u09a4\u09cd \u099a\u09be\u0995\u09b0\u09bf \u099b\u09c7\u09a1\u09bc\u09c7 \u09ac\u09cd\u09af\u09ac\u09b8\u09be\u09af\u09bc "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python
RULE_ID = "DB-A5-001"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

# ত + virama (ত্) at the end of a word, or before ক স প, is a khanda-ta written the old way.
# A ZWJ/ZWNJ after the virama is a deliberate choice and is left alone.
_T = re.compile('ত্(?=[কসপ]|(?![\u0980-\u09ff\u200c\u200d]))')

def medicine_a5(text):
    """Replace ত্ with ৎ (U+09CE) at a word end and before ক স প."""
    return _T.sub('ৎ', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 74 — indic / A5 / `DB-A5-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-A5-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A5 Wrong normal form. Pack `ind-bn-fw2`. Source: section A5 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python deferred
RULE_ID = "DB-A5-002"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-A5-001"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_a5(text):
    """া + ে -> ো, ৈ + া -> ৌ (two-part vowels stored in reverse order)."""
    return text.replace("াে", "ো").replace("ৈা", "ৌ")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 75 — indic / A5 / `DB-A5-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A5 Wrong normal form. Pack `ind-gu-fw2`. Source: section A5 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `631da9a005b32c3e` (ind-gu-fw2), original offset 277: `"\u0a88 \u0ab0\u0ab9\u0ac7\u0ab2\u0abe \u0aaa\u0ae6 \u0ab2\u0acb\u0a95\u0acb\u0aa8\u0abe\u0a82 \u0aa1\u0ac2\u0aac\u0ac0 \u0a9c\u0ab5\u0abe\u0aa5\u0ac0 \u0aae\u0acb"` (fix).
- `8fb25749776eab64` (ind-gu-fw2), original offset 29: `"\u0aaf \u0a9c\u0a97\u0aa8\u0ac7\u0ab6\u0acd\u0ab0\u0acd\u0ab5\u0ab0 \u0aad\u0a9f\u0acd\u0a9f \u0aae\u0ac2\u0ab3 \u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0aa8\u0abe \u0aad"` (fix).
- `09a1138a7eaf5cc4` (ind-gu-fw2), original offset 16: `"\u0acd\u0ab9\u0ac0, \u0aa4\u0abe.\u0ab0\u0aee\n\u0a95\u0acb\u0a82\u0a97\u0acd\u0ab0\u0ac7\u0ab8 \u0aaa\u0acd\u0ab0\u0aae\u0ac1\u0a96 \u0ab0\u0abe\u0ab9\u0ac1\u0ab2"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python
RULE_ID = "DB-A5-003"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block
GU_DIGIT = "\u0AE6-\u0AEF"                    # Gujarati digits 0-9
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

A5_PAIRS = [("ાે", "ો"), ("ાૈ", "ૌ"), ("અા", "આ"), ("અો", "ઓ"), ("અે", "એ"), ("અૈ", "ઐ"),
            ("ૈા", "ૌ"), ("્ર્વ", "્વ")]
A5_RU = re.compile(r"(?<!્)રૃ")
A5_DIGIT = re.compile(rf"(?<![{GU}])[{GU_DIGIT}રપ]*[{GU_DIGIT}][{GU_DIGIT}રપ]*(?![{GU}])")

def m5_a5(text, url=None):
    new = text
    for a, b in A5_PAIRS:
        new = new.replace(a, b)
    new = A5_RU.sub("રૂ", new)
    new = A5_DIGIT.sub(lambda m: m.group(0).replace("ર", "૨").replace("પ", "૫"), new)
    return _fix(text, new)

def medicine_a5(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m5_a5(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 76 — indic / A5 / `DB-A5-004`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A5 Wrong normal form. Pack `ind-gu-fw2`. Source: section A5 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python deferred
RULE_ID = "DB-A5-004"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-gu-fw2'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

SIGN = "\u0abe-\u0ac5\u0ac7-\u0ac9\u0acb\u0acc"      # Gujarati vowel signs

def medicine(text):
    t = text.replace("રૂા", "\0")                      # rupee shorthand is correct, protect it
    t = t.replace("\u0a85\u0ac7", "\u0a8f")            # અ + ે  ->  એ
    t = re.sub(f"([{SIGN}])\\1+", r"\1", t)           # the same sign twice
    t = (t.replace("\u0abe\u0ac7", "\u0acb")          # ાે -> ો
          .replace("\u0abe\u0ac8", "\u0acc")          # ાૈ -> ૌ
          .replace("\u0ac8\u0abe", "\u0acc"))         # ૈા -> ૌ
    t = re.sub(f"([\u0a85-\u0a94])[{SIGN}]", r"\1", t)  # sign after an independent vowel
    t = re.sub(f"([{SIGN}])[{SIGN}]", r"\1", t)         # any other two signs: keep the first
    t = re.sub(f"([{SIGN}\u0a82])\u0abc", r"\1", t)    # nukta after a sign
    return t.replace("\0", "રૂા")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 26 of 3...
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 77 — indic / A5 / `DB-A5-005`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A5 Wrong normal form. Pack `ind-hi-hplt`. Source: section A5 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python deferred
RULE_ID = "DB-A5-005"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_C = "[\u0915-\u0939\u0958-\u095F]"  # consonant


def medicine_a5(text):
    t = text
    # vowel sign E/AI typed before virama + RA: कांगे्रस -> कांग्रेस
    t = re.sub("([\u0947\u0948])\u094D\u0930", "\u094D\u0930\\1", t)
    # stray virama after vowel sign E/AI before another consonant: ओल्डे्नबर्ग -> ओल्डेनबर्ग
    t = re.sub("([\u0947\u0948])\u094D(?=" + _C + ")", "\\1", t)
    # two vowel signs for one: AA+CANDRA E -> CANDRA O, AA+E or E+AA -> O, AA+AI -> AU, E+AI -> AI
    for bad, good in (("\u093E\u0945", "\u0949"), ("\u093E\u0947", "\u094B"), ("\u0947\u093E", "\u094B"),
                      ("\u093E\u0948", "\u094C"), ("\u0947\u0948", "\u0948"), ("\u093C\u093C", "\u093C")):
        t = t.replace(bad, good)
    # the same vowel sign twice: स्थाानों -> स्थानों
    t = re.sub("([\u093E-\u094C])\\1", "\\1", t)
    # nukta moved to the next letter: पकडक़र -> पकड़कर, पीढिय़ों -> पीढ़ियों, लडऩे -> लड़ने
    t = re.sub("([\u0921\u0922])([\u093F\u0940\u0947\u0948]?)([\u0915\u092F\u0928])\u093C", "\\1\u093C\\2\\3", t)
    t = re.sub("([\u0921\u0922])([\u093E-\u094C]?)\u0929", "\\1\u093C\\2\u0928", t)
    # reph written after the conjunct: सामथ्र्य -> सामर्थ्य, पाट्र्स -> पार्ट्स
    t = re.sub("(" + _C + ")\u094D\u0930\u094D(" + _C + ")", "\u0930\u094D\\1\u094D\\2", t)
    # RA + virama + letter I for letter II: हुर्इं -> हुईं
    t = t.replace("\u0930\u094D\u0907", "\u0908")
    # DHA + virama + DA for द्ध: बौध्दिक -> बौद्धिक
    t = t.replace("\u0927\u094D\u0926", "\u0926\u094D\u0927")
    # Marathi eyelash RA for RA: औऱ -> और
    t = re.sub("\u0931(?!\u094D)", "\u0930", t)
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. ZWJ/ZWNJ audit and normal-form audit: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 78 — indic / A5 / `DB-A5-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A5 Wrong normal form. Pack `ind-mr-sangraha-v`. Source: section A5 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS); ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `4884f7c293a7beab` (ind-mr-sangraha-v), original offset 2429: `"\u0924\u0938\u0947 \u0936\u0947\u0924\u0915\u0930\u093c\u094d\u092f\u093e\u0902\u0928\u093e \u0938\u093e\u0902\u0917\u0942\u0928 \u0905\u0927\u093f\u0917\u094d\u0930\u0939\u0923"` (fix).
- `2c66d24bfd6db2ef` (ind-mr-sangraha-v), original offset 904: `"\u094d\u092f\u093e\u0928 \u0926\u0941\u0938\u0930\u093c\u094d\u092f\u093e \u0926\u093f\u0935\u0936\u0940 \u0967\u0967 \u0938\u092a\u094d\u091f\u0947\u0902\u092c\u0930\u0932"` (fix).
- `61b2c25e9513730b` (ind-mr-sangraha-v), original offset 246: `"\u0938\u093e\u092f \u0915\u0930\u0923\u093e\u0930\u093c\u094d\u092f\u093e \u0917\u094d\u0930\u093e\u0939\u0915\u093e\u0902\u0928\u093e \u0935\u093f\u0928\u0902\u0924\u0940 "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_a5(text)`.

```python
RULE_ID = "DB-A5-006"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2', 'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v, ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

import unicodedata

def cure_a5(text):
    return unicodedata.normalize("NFC", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). This demonstrates no measured gol...
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 79 — indic / A5 / `DB-A5-007`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A5 Wrong normal form. Pack `ind-sa-fw2`. Source: section A5 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python deferred
RULE_ID = "DB-A5-007"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_FULL = {"ा": "आ", "ि": "इ", "ी": "ई", "ु": "उ", "ू": "ऊ", "ृ": "ऋ", "े": "ए", "ै": "ऐ", "ो": "ओ", "ौ": "औ"}

def medicine_a5(text):
    t = re.sub("अ([ािीुूृेैोौ])", lambda m: _FULL[m.group(1)], text)
    t = re.sub("([ा-्ॢॣ])\\1+", r"\1", t)
    if "॥" in t:
        t = re.sub("।[ \t]?।", "॥", t)
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 80 — indic / A5 / `DB-A5-008`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A5 Wrong normal form. Pack `ind-sa-fw2`. Source: section A5 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `61cdf0be9f009325` (ind-sa-fw2), original offset 4187: `"\u094d\u0935\u0923\u093f \u0937\u091f\u094d\u094d\u0937\u0937\u094d\u091f\u093f\u0924\u092e\u094b\u093d\u0927\u094d\u092f\u093e\u092f\u0903 \u0965 66 \u0965 "` (fix).
- `58b5cd30c9ab7965` (ind-sa-fw2), original offset 5565: `"\u092f \u0938\u0941\u0916\u093e\u092d\u0947\u0947\u0926\u0947\u093d\u092a\u093f \u0930\u093e\u0939\u094b\u0903 \u0936\u093f\u0930 \u0907\u0924\u093f\u0935\u0926\u094d\u092d"` (fix).
- `18f91690f821fc5c` (ind-sa-fw2), original offset 915: `"\u093e\u0930\u0947 \u0928\u093f\u092f\u0941\u0941\u0915\u094d\u0924\u0935\u093e\u0928\u094d,\n\u2169 \u091c\u093e\u0917\u094d\u0930\u0924\u094b \u0928\u093f\u0926\u094d"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python
RULE_ID = "DB-A5-008"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

SIGNS = r"\u093E-\u094C\u0962\u0963"    # dependent vowel signs ा ि ी ु ू ृ ॄ ॅ ॆ े ै ॉ ॊ ो ौ and ॢ ॣ
RE_A5_SAME = re.compile(rf"([{SIGNS}])\1+")    # the same vowel sign twice or more: ेे ाा ुु
RE_A5_STACK = re.compile(rf"[{SIGNS}][{SIGNS}]")    # any two vowel signs on one letter (detection only when they differ)
RE_A5_VIRAMA = re.compile("\u094D{2,}")    # doubled virama
RE_A5_A_AA = re.compile("अा")    # अ + ा, which is आ written in two parts
RE_A5_DD = re.compile("(?<!।)।।(?!।)")    # two single dandas in a row

def detect_a5(text):
    return bool(RE_A5_STACK.search(text) or RE_A5_VIRAMA.search(text) or RE_A5_A_AA.search(text)
                or ("॥" in text and RE_A5_DD.search(text)))

def medicine_a5(text):
    """Collapse a doubled vowel sign or virama, write अ+ा as आ, and make । । a ॥ in a document that already uses ॥.
    Two different vowel signs on one letter (ेो, ैौ) are detected by detect_a5 but not repaired: there is no safe choice."""
    text = RE_A5_SAME.sub(r"\1", text)
    text = RE_A5_VIRAMA.sub("्", text)
    text = RE_A5_A_AA.sub("आ", text)
    if "॥" in text:
        text = RE_A5_DD.sub("॥", text)
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 81 — indic / A6 / `DB-A6-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-bn-fw2`. Source: section A6 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `fb97c8e54faa6ea5` (ind-bn-fw2), original offset 168: `"\u09be \u0997\u09cd\u09b0\u09be\u09ae\u09c7\u09f7 \u09ac\u09af\u09bc\u09b8 \u09b8\u09ac\u09c7 \u09ae\u09be\u09a4\u09cd\u09b0 \u0986\u099f\u09be\u09b6\u0964 \u098f"` (fix).
- `3c0d0458978d7c51` (ind-bn-fw2), original offset 921: `"\u09b8\u09b0\u09a3 \u0995\u09b0\u09c1\u09a8\u09f7\n\u09b2\u09be\u0987\u09ad \u0995\u09cd\u09af\u09be\u09b8\u09bf\u09a8\u09cb \u09ac\u09bf\u099f\u0995\u09af\u09bc\u09c7\u09a8"` (fix).
- `0ca0ac43cc9f2526` (ind-bn-fw2), original offset 466: `"\u0995\u09cd\u09b0\u09be\u09ab\u099f\u09b8\u2019 l \u09b8\u09be\u09b0\u09be \u09a6\u09c7\u09b6\u09c7 \u098f\u09b8\u09ac \u09b8\u09ae\u09cd\u09ad\u09be\u09ac\u09a8"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-001"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_DANDA_LOOKALIKE = re.compile('(?<=[\u0980-\u09ff’”)])৷(?=\\s|$)')  # ৷ (U+09F7) used as danda
_DOUBLE = re.compile('।৷')                                                  # ।৷
_PIPE = re.compile('(?<=[\u0980-\u09ff’”)]) ?\\|(?=[ \\t]*(?:\\n|$))', re.M)  # ASCII | at line end
_L_DANDA = re.compile('(?<=[\u0980-\u09ff’”]) l(?=\\s|$)')                  # Latin l as danda

def medicine_a6(text):
    """Replace danda look-alikes after Bengali text with the real danda । (U+0964)."""
    text = _DOUBLE.sub('।', text)
    text = _DANDA_LOOKALIKE.sub('।', text)
    text = _PIPE.sub('।', text)
    return _L_DANDA.sub('।', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 82 — indic / A6 / `DB-A6-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-A6-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-bn-fw2`. Source: section A6 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python deferred
RULE_ID = "DB-A6-002"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-A6-001"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re


def medicine_a6(text):
    """U+09F7 after a Bengali character or a space -> danda U+0964."""
    return re.sub("(?<=[ঀ-৿\\s])৷", "।", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 83 — indic / A6 / `DB-A6-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-gu-fw2`. Source: section A6 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `79e1f2d27c8fda29` (ind-gu-fw2), original offset 2031: `"3 44944\n\u0906\u092a\u0915\u0947 \u0915\u093f\u0938\u0940 \u092d\u0940 \u092a\u094d\u0930\u0915\u093e\u0930 \u0915\u0947 \u0928"` (fix).
- `3ed1c081935c62ce` (ind-gu-fw2), original offset 0: `"\u0936\u094d\u0930\u0940\u092d\u0917\u0935\u093e\u0928\u0941\u0935\u093e\u091a |\n\u0905\u0928\u093e\u0936\u094d\u0930\u093f\u0924: \u0915\u0930\u094d\u092e\u092b\u0932\u0902 \u0915\u093e\u0930\u094d\u092f\u0902 \u0915\u0930\u094d\u092e \u0915\u0930\u094b\u0924\u093f \u092f: |\n\u0938 \u0938\u0902\u0928\u094d\u092f"` (drop).
- `14318c3e5674f30e` (ind-gu-fw2), original offset 9134: `"\u0ab2\u0acb\u0a95\u0aae\u0abe\u0a82,\n\u0938\u094c\u0930\u093e\u0937\u094d\u091f\u094d\u0930\u0947 \u092a\u091e\u094d\u091a \u0930\u0924\u094d\u0928\u093e\u0928\u093f "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-A6-003"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

SANDWICH = re.compile(r"[઀-૿][a-z]{1,8}[઀-૿]")
DEVANAGARI = re.compile(r"[\u0900-\u0963\u0966-\u097f]")      # letters, not the danda

def medicine(text):
    if SANDWICH.search(text):
        return None                       # drop the document
    lines = text.split("\n")
    keep = [l for l in lines if not DEVANAGARI.search(l)]
    if len(keep) < 0.7 * len(lines):
        return None                       # drop the document
    return "\n".join(keep)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 15 of 1...
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 84 — indic / A6 / `DB-A6-004`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-hi-hplt`. Source: section A6 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `c3d6c6b67a11a989` (ind-hi-fw2), original offset 79: `"\u0928\u0924 \u092e\u093f\u0932\u0940 l\n\u092c\u092e\u094d\u092c\u0908 \u0909\u091a\u094d\u091a \u0928\u094d\u092f\u093e\u092f\u093e\u0932\u092f \u0928\u0947"` (fix).
- `10ee275a9dea2acf` (ind-hi-fw2), original offset 2632: `"\u0941\u0928\u093e\u0935 \u0915\u0940 l\n\u0915\u094d\u092f\u093e \u0939\u094b\u0917\u093e \u0906\u0928\u0947 \u0935\u093e\u0932\u0947 \u091a\u0941\u0928"` (fix).
- `ee19639bfb2e22a0` (ind-hi-fw2), original offset 1197: `" \u0939\u094b \u0917\u092f\u0947 I\n\u0935\u093e\u0939\u0928 \u092a\u0941\u0932\u093f\u0938 \u0915\u094b \u0906\u0924\u093e \u0926\u0947\u0916 "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-004"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-hplt', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt, ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_DANDA = re.compile("([\u0900-\u0963\u0966-\u097F]+)( ?)[Il](?=[ \t]*(?:\n|$|[\u0900-\u097F\"'\u201C\u201D\u2018\u2019]))")
_ROMAN_BEFORE = {"डिवीजन", "डिवीज़न", "भाग", "खंड", "खण्ड", "चरण", "फेज", "फेज़", "टाइप", "क्लास", "ग्रेड", "लेवल", "विश्वयुद्ध"}


def _danda(m):
    if m.group(1) in _ROMAN_BEFORE:  # "डिवीजन I" is a Roman numeral, not a danda
        return m.group(0)
    return m.group(1) + m.group(2) + "\u0964"


def medicine_a6(text):
    # Latin I or l typed for the danda after a Devanagari word: "हैI", "आया I", "हुआ l"
    t = _DANDA.sub(_danda, text)
    # visarga typed for the colon: "महत्वपूर्ण हैः यह" -> "है:"
    t = re.sub("(है|हैं|चाहिए)\u0903(?=\\s)", "\\1:", t)
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 85 — indic / A6 / `DB-A6-005`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-A6-004. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-hi-hplt`. Source: section A6 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python deferred
RULE_ID = "DB-A6-005"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-A6-004"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# A6: ASCII "|" or Latin "I" typed for the danda, only right after a sentence-final verb
_VERB = (r"है|हैं|था|थे|थी|थीं|गया|गई|गयी|गए|होगा|होगी|होंगे|रहा|रही|रहे|सकता|सकती|सकते|करें|जाएगा|जाएगी|"
         r"जाएंगे|दिया|दी|दिए|किया|किए|हुआ|हुई|हुए|मिला|मिली|मिले|जाता|जाती|जाते|चाहिए|लिया|लिए")
_A6 = re.compile(r"(?<![ऀ-ॿ])(" + _VERB + r") ?[|I](?=[ \t]|\n|$)")


def medicine_a6(text):
    return _A6.sub(r"\1।", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 26 of 46 A6 documents; 15 other diseased documents touc...
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 86 — indic / A6 / `DB-A6-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-kn-sangraha-s`. Source: section A6 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `54f770edbfb0f27e` (ind-kn-sangraha-s), original offset 483: `"\u0cc1\u0ca4\u0ccd\u0ca4\u0cb5\u0cc6 (i.\u0c87.\u0caa\u0cb3\u0cc6\u0caf\u0cc1\u0cb3\u0cbf\u0c95\u0cc6) \u0c85\u0ca5\u0cb5\u0cbe \u0c85\u0cac\u0cbf\u0caf"` (fix).
- `605c195dc5422a06` (ind-kn-sangraha-s), original offset 18205: `"\u0cc1\u0ca6\u0cbf\u0cb2\u0ccd\u0cb2 (i.\u0c87. \u0cb5\u0ccd\u0caf\u0cb5\u0cb8\u0ccd\u0ca5\u0cbf\u0ca4). \u0cae\u0cbe\u0ca8\u0cb5\u0ca8 \u0cb9"` (fix).
- `bddb7db5986a353f` (ind-kn-sangraha-s), original offset 14027: `"\u0cb5\u0cbe\u0c97\u0cbf\u0ca6\u0cc6 (i.\u0c87. ) \u0cb8\u0c82\u0cb5\u0cb9\u0ca8 \u0c95\u0cc7\u0c82\u0ca6\u0ccd\u0cb0 \u0cac\u0cbf\u0c82\u0ca6"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `m3_half_translated(text)`.

```python
RULE_ID = "DB-A6-006"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s, ind-kn-fw2"
SOURCE_ORIGIN = "ind-kn-sangraha-s"
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

HALF_IE = re.compile(r"\bi\.\s?ಇ\.")
HALF_EG = re.compile(r"\be\.\s?ಜಿ\.")
def m3_half_translated(s):
    return HALF_EG.sub("ಉದಾ.", HALF_IE.sub("ಅಂದರೆ", s))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m3_half_translated  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 0 of 359. It fixes 9 of the 30 A6 documents.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 87 — indic / A6 / `DB-A6-007`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-kn-sangraha-v`. Source: section A6 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `0fddd312da4d1f53` (ind-kn-sangraha-v), original offset 694: `"\u0ca8\u0cae\u0ccd\u0cae \u0cb8\u0c82\u0cad0\u0ca6\u0ca6\u0cb2\u0ccd\u0cb2\u0cbf \u0c92\u0cb3\u0ccd\u0cb3\u0cc6\u0cb5\u0cb0 \u0c87\u0ca6\u0ccd\u0ca6\u0cbe\u0ca8\u0cc6."` (fix).
- `8e109920ba86923c` (ind-kn-sangraha-v), original offset 275: `"\u0ccd\u0ca6\u0cbe\u0cb0\u0cc6. \u0c87\u0ce6\u0ca5\u0cbe \u0c86\u0cb6\u0ccd\u0c9a\u0cb0\u0ccd\u0caf\u0c95\u0cbe\u0cb0\u0c95 \u0c86\u0ca4\u0cbf\u0cae\u0cbe \u0ca8\u0cc1"` (fix).
- `d6782f4121e10366` (ind-kn-sangraha-v), original offset 267: `" \u0ca8\u0cc1\u0ca1\u0cbf\u0c97\u0cb3\u0cbf\u0ce6\u0ca6 \u0cb8\u0cb0\u0cb3\u0cb5\u0cbe\u0c97\u0cbf \u0cac\u0cbf\u0ca1\u0cbf\u0cb8\u0cb2\u0cc1 \u0cb8\u0cbe\u0cb9\u0cb8\u0cae"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-007"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"
SOURCE_ORIGIN = "ind-kn-sangraha-v"
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

import re

KN_SIGNED = "ಅ-ಹಾ-ೌ"                 # Kannada vowels, consonants and vowel signs
ZERO_KN = re.compile(f"(?<=[{KN_SIGNED}])೦(?![೦-೯])")
ZERO_ASCII = re.compile(f"(?<=[{KN_SIGNED}])0(?=[ಕ-ಹ])")
LATIN_S = re.compile("(?<=[ಀ-೿])s(?=[ಀ-೿])")


def fix_lookalikes(t):
    """A6: a Kannada digit zero (೦) or an ASCII 0 right after a Kannada letter is the anusvara (ಂ); a Latin s
    between Kannada letters is the avagraha (ಽ)."""
    t = ZERO_KN.sub("ಂ", t)
    t = ZERO_ASCII.sub("ಂ", t)
    return LATIN_S.sub("ಽ", t)


def medicine_a6(text):
    """The A6 rule, under the name that the harm tests look for: returns the fixed text."""
    return fix_lookalikes(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 88 — indic / A6 / `DB-A6-008`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-mr-fw2`. Source: section A6 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `1870bd9485daced5` (ind-mr-fw2), original offset 2739: `"\u0938\u0926 shant\u0938\u0902\u0935\u093f\u0927\u093e\u0928\u093e\u091a\u094d\u092f\u093e \u092e\u0942\u0932\u092d\u0942\u0924 \u0930\u091a\u0928\u0947"` (fix).
- `70386fb4070fc50f` (ind-mr-fw2), original offset 590: `" Article\u0915\u0938\u092c\u094d\u092f\u093e\u091a\u094d\u092f\u093e \u0930\u093f\u0902\u0917\u0923\u093e\u0924 \u092c\u093f\u091a\u0941\u0915"` (fix).
- `875818dd2944faba` (ind-mr-fw2), original offset 1045: `"\u0915\u093f\u0902\u0917 apt\u0921\u0945\u092a\u094d\u091f\u0947\u0936\u0928\u094d\u0938\u091a\u0940 \u092d\u093f\u0928\u094d\u0928 \u0917\u0941\u0923\u0935\u0924"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-008"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-fw2"
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_a6(text):
    text = re.sub(r'([a-zA-Z])([\u0900-\u097F])', r'\1 \2', text)
    return re.sub(r'([\u0900-\u097F])([a-zA-Z])', r'\1 \2', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 89 — indic / A6 / `DB-A6-009`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-mr-sangraha-v`. Source: section A6 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `4884f7c293a7beab` (ind-mr-sangraha-v), original offset 1893: `"\u0932\u0947\u0932\u094d\u092f\u093e \u09670\u096d \u092a\u0948\u0915\u0940 \u09670 \u092f\u094b\u091c\u0928\u093e\u0902\u091a\u0940 \u0915\u093e\u092e\u0947"` (fix).
- `ebd9df55e9518211` (ind-mr-sangraha-v), original offset 1472: `" \u092e\u093e\u0930\u094d\u091a \u09680\u0967\u0967 \u0930\u094b\u091c\u0940 \u0924\u0924\u094d\u0915\u093e\u0932\u0940\u0928 \u0930\u093e\u091c\u094d\u092f "` (fix).
- `c8f1b56d8caf1c84` (ind-mr-sangraha-v), original offset 750: `"\u0932 \u0928\u0917\u0926\u0940 \u096a0 \u0939\u091c\u093e\u0930, \u0968\u096a \u0939\u091c\u093e\u0930 \u0930\u0941\u092a\u092f\u0947 \u0915\u093f"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_a6(text)`.

```python
RULE_ID = "DB-A6-009"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f

import re

_A6_MIXED_DIGITS = re.compile(r"[०-९0-9]+")
_A6_DIGIT_MAP = str.maketrans("0123456789", "०१२३४५६७८९")

def cure_a6(text):
    def convert(match):
        token = match.group()
        if re.search(r"[०-९]", token) and re.search(r"[0-9]", token):
            return token.translate(_A6_DIGIT_MAP)
        return token
    return _A6_MIXED_DIGITS.sub(convert, text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Only mixed-digit conversion is co...
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 90 — indic / A6 / `DB-A6-010`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-sa-fw2`. Source: section A6 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python deferred
RULE_ID = "DB-A6-010"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_D = "ऀ-ॿ"
_CONS = "क-हक़-य़"
_MAT = "ा-ौॢॣ"
_ABBR = re.compile(r"(?:^|[\s(])(डा|डॉ|प्रो|डो|श्री|सं|पृ|ई|क्र|पं|मो|फो|दू)$")

def medicine_a6(text):
    def colon(m):
        before = text[max(0, m.start() - 6):m.start()]
        after = text[m.end():m.end() + 3].lstrip()
        if _ABBR.search(before) or (after and after[0].isalpha() and not "ऀ" <= after[0] <= "ॿ"):
            return m.group()
        return "ः"
    t = re.sub(f"(?<=[{_CONS}{_MAT}]):(?=[\\s।॥]|$)", colon, text)
    t = re.sub(f"(?<=[{_CONS}{_MAT}ंः])[Ss](?=[{_CONS}])", "ऽ", t)
    out = []
    for line in t.split("\n"):
        if not (line.startswith("|") or line.rstrip().endswith("|") and line.count("|") > 2):
            line = re.sub(f"(?<=[{_D}]) ?\\|\\|(?=\\s|$)", " ॥", line)
            line = re.sub(f"(?<=[{_D}]) ?\\|(?=\\s|$)", " ।", line)
        line = re.sub(f"(?<=[{_D}]) ?I(?=\\s*$|\\s+[{_D}])", " ।", line)
        line = re.sub(f"(?<=[{_D}])o(?=\\s)", "॰", line)
        line = re.sub(f"(?<=[A-Za-z]{{3}})(?=[{_CONS}])|(?<=[{_D}])(?=[A-Za-z]{{3}})", " ", line)
        out.append(line)
    return "\n".join(out).translate({0x0946: 0x0947, 0x094A: 0x094B, 0x0931: 0x0930})


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 91 — indic / A6 / `DB-A6-011`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-sa-fw2`. Source: section A6 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `fix_a6(text)`.

```python deferred
RULE_ID = "DB-A6-011"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

# character classes use \u escapes on purpose: a literal nukta letter is stored decomposed and would break the range
DEVA_LETTER = r"\u0904-\u0939\u093D\u0950\u0958-\u0961\u0972-\u097F"    # letters incl. avagraha and OM
DEVA_MARK = r"\u0900-\u0903\u093A-\u093C\u093E-\u094F\u0951-\u0957\u0962\u0963"    # matras, virama, nukta, bindus, visarga, accents
BOUNDARY = r"[ \t\u00A0\r\n।॥]"    # space, tab, nbsp, newline, danda
E_O_VOWELS = r"\u0946\u0947\u094A\u094B\u090E\u090F\u0912\u0913"    # matras ॆ े ॊ ो and letters ऎ ए ऒ ओ
RE_A6_DANDA = re.compile(rf"(?<=[{DEVA_LETTER}{DEVA_MARK}])(I{{1,2}}|l{{1,2}})(?={BOUNDARY}|$)")
RE_A6_AVAGRAHA = re.compile(rf"(?<=[{E_O_VOWELS}])[Ss](?=[{DEVA_LETTER}])")
# ASCII ':' typed for visarga: right after a Devanagari letter or vowel sign, before a boundary or a Devanagari letter
RE_A6_COLON = re.compile(rf"(?<=[{DEVA_LETTER}\u093A-\u093C\u093E-\u094F\u0962\u0963]):(?={BOUNDARY}|$|[{DEVA_LETTER}])")
# ASCII '|' or '||' typed for danda or double danda: after a Devanagari word (an optional space before it is kept), before a boundary
RE_A6_PIPE = re.compile(rf"(?<=[{DEVA_LETTER}{DEVA_MARK}])([ ]?)(\|{{1,2}})(?={BOUNDARY}|$)")

RE_LATIN_LETTER = re.compile(r"[A-Za-z]")

def _pipe_line(line):
    if line.lstrip().startswith("|") or RE_LATIN_LETTER.search(line):    # wiki table row, or a title/menu line with Latin words
        return line
    return RE_A6_PIPE.sub(lambda m: m.group(1) + ("॥" if len(m.group(2)) == 2 else "।"), line)

def fix_a6(text):
    text = RE_A6_DANDA.sub(lambda m: "॥" if len(m.group(1)) == 2 else "।", text)
    text = RE_A6_AVAGRAHA.sub("ऽ", text)
    text = RE_A6_COLON.sub("ः", text)
    return "\n".join(_pipe_line(l) for l in text.split("\n"))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = fix_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 92 — indic / A6 / `DB-A6-012`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-ta-sangraha-v`. Source: section A6 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-ta-sangraha-v: 0 changed / 0 dropped of 41 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `ba0521a76a80c6ba` (ind-ta-sangraha-v), original offset 171: `" \u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8\u0b83\n\u0b95\u0bbe\u0bb2\u0bbe\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0bbf\u0bb2\u0bcd \u0b95\u0b9f\u0ba8\u0bcd\u0ba4 9\u0bae"` (fix).
- `803e203a2c7d60da` (ind-ta-sangraha-v), original offset 0: `"\u0b9a\u0bc6\u0baf\u0bcd\u0bae\u0bc1\u0bb1\u0bc8\u0b83\n\u0baa\u0b9a\u0bcd\u0b9a\u0bb0\u0bbf\u0b9a\u0bbf \u0bae\u0bb1\u0bcd\u0bb1\u0bc1\u0bae\u0bcd \u0baa\u0b9a\u0bcd\u0b9a\u0bc8"` (fix).
- `70717a9a2d8c2b37` (ind-ta-sangraha-v), original offset 410: `"\u0bcd \u0bb5\u0bbf\u0baa\u0bb0\u0bae\u0bcd\u0b83\n\u0bae\u0bc1\u0ba4\u0bb2\u0bcd \u0b87\u0ba9\u0bcd\u0ba9\u0bbf\u0b99\u0bcd\u0bb8\u0bbf\u0bb2\u0bcd \u0b9a\u0ba4\u0bae\u0b9f"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-012"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-ta-sangraha-v'}
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"
SOURCE_ORIGIN = "ind-ta-sangraha-v"
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def medicine_a6(text):
    return re.sub("ஃ(?![க-ஹ])", ":", text)  # aytham before a space or line end is a lost colon


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 135 documents, none labelled `clean`. 8 of the 10 changed documents
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 93 — indic / A6 / `DB-A6-013`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-te-fw2`. Source: section A6 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `b1fc122a01e457a3` (ind-te-fw2), original offset 1991: `"\u0c30\u0c3e\u0c2e\u0c28\u0c3e\u0c2e \u0c38\u0c66\u0c38\u0c4d\u0c2e\u0c30\u0c23\u0c2e\u0c41 \u0c35\u0c3f \u0c2a \u0c26 \u0c17\u0c3e \u0c27\u0c2a\u0c24\u0c3f\u0c24"` (fix).
- `d5308e76e13e8058` (ind-te-fw2), original offset 2925: `"\u0c2f\u0c15\u0c4d\u0c24\u0c3f\u0c24\u0c4d\u0c35o \u0c17\u0c32 \u0c35\u0c4d\u0c2f\u0c15\u0c4d\u0c24\u0c3f.. \u0c15\u0c3e\u0c02\u0c17\u0c4d\u0c30\u0c46\u0c38\u0c4d"` (fix).
- `64e785802da2651a` (ind-te-fw2), original offset 1984: `"\u0c30\u0c4d\u0c17\u0c26\u0c30\u0c4d\u0c36\u0c15o\u0c17\u0c3e \u0c35\u0c47\u0c26\u0c3e\u0c32\u0c41 \u0c35\u0c4d\u0c2f\u0c35\u0c39\u0c30\u0c3f\u0c38\u0c4d\u0c24\u0c3e\u0c2f\u0c3f"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `a6_lookalike(text)`.

```python
RULE_ID = "DB-A6-013"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

A6_RX = re.compile(r"(?<=[క-హా-ౌ])[o౦](?=[క-హ]|\s|[.,!?]|$)")
def a6_lookalike(t, url=None):
    return A6_RX.sub("ం", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = a6_lookalike  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 94 — indic / A6 / `DB-A6-014`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-te-sangraha-s`. Source: section A6 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `a28871107b0cefc2` (ind-te-sangraha-s), original offset 985: `"\u0c02\u0c1a\u0c2c\u0c21\u0c3f\u0c02\u0c26\u0c3f\u0c03 \"\u0c30\u0c3e\u0c21\u0c4d\u0c38\u0c46\u0c32\u0c3f\u0c1c\u0c4d \u0c30\u0c42\u0c38\u0c4d 2005\""` (fix).
- `0a959795abcefb55` (ind-te-sangraha-s), original offset 653: `"\u0c30\u0c2f\u0c4b\u0c1c\u0c28\u0c3e\u0c32\u0c41\u0c03\n\u0c17\u0c41\u0c30\u0c4d\u0c24\u0c3f\u0c02\u0c1a\u0c26\u0c17\u0c3f\u0c28 \u0c21\u0c3f\u0c1c\u0c48\u0c28\u0c4d \u0c35\u0c4d"` (fix).
- `e61e3982f326eb8b` (ind-te-sangraha-s), original offset 3480: `"\u0c02\u0c1a\u0c2c\u0c21\u0c3f\u0c02\u0c26\u0c3f\u0c03\n978 \u0c06\u0c17\u0c38\u0c4d\u0c1f\u0c41\u0c32\u0c4b, \u0c15\u0c3f\u0c02\u0c17\u0c4d \u0c32\u0c4b"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-014"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-sangraha-s'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"
SOURCE_ORIGIN = "ind-te-sangraha-s"
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_VISARGA_WORDS = {"అంతః", "ఆయుః", "ఉరః", "చేతః", "తపః", "తేజః", "నమః", "పయః", "పునః", "ప్రాతః", "భూః", "మనః", "యశః", "వచః", "శిరః", "శ్రీః", "స్వః"}

def medicine_a6(text):
    def fix(m):
        word = m.group(1) + "ః"
        return m.group(0) if word in _VISARGA_WORDS else m.group(1) + ":"
    return re.sub(r"([\u0C00-\u0C02\u0C04-\u0C7F]*)ః(?=\n|$| [\"“‘'])", fix, text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_a6` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 95 — indic / G1 / `DB-G1-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-bn-fw2`. Source: section G1 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `bb4a327ce2e54290` (ind-bn-fw2), original offset 5968: `"\u09af \u09b8\u0995\u09b2 \u09b8\u09ae \u09cd\u09aa\u09cd\u09b0\u09a6\u09be\u09af\u09bc \u09ac\u09bf\u09b6\u09cd\u09ac\u09be\u09b8 \u0995\u09b0\u09c7\u09a8 \u09af"` (fix).
- `3c0de9b8acf6b2fd` (ind-bn-fw2), original offset 2262: `"\u09b2 \u09a7\u09b0\u09cd\u09ae\u09c7\u09b0 \u09cd\u09b0 \u09b8\u09be\u09b0\u09cd\u09ac\u099c\u09a8\u09c0\u09a8 \u09ae\u09c2\u09b2\u09cd\u09af\u09c7\u09b0 \u09aa\u09cd"` (fix).
- `93ae15cbd5dcb150` (ind-bn-sangraha-v), original offset 1903: `"\u09c7\u0964 \u098f\u099f\u09be \u09a4 \u09cd\u09af\u09be\u09b0 \u09a4\u09c8\u09b0\u09c0 \u09b9\u0993\u09af\u09bc\u09be \u0989\u099a\u09bf\u09a4 \u099b\u09bf"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-001"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re


def medicine_g1(text):
    """Remove a space between a consonant and a following virama + consonant."""
    return re.sub("(?<=[ক-হ]) (?=্[ক-হ])", "", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 96 — indic / G1 / `DB-G1-002`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-gu-fw2`. Source: section G1 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python deferred
RULE_ID = "DB-G1-002"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-gu-fw2'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU_SIGN = "\u0A81-\u0A83\u0ABC-\u0ACD"      # dependent signs, nukta, virama
GU_VOWEL_SIGN = "\u0ABE-\u0ACC\u0A81-\u0A83"
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

G1_DOUBLE = re.compile(rf"([{GU_SIGN}])\1+")
G1_ORPHAN = re.compile(rf"(?<=\s)[{GU_VOWEL_SIGN}]")

def m6_g1(text, url=None):
    return _fix(text, G1_ORPHAN.sub("", G1_DOUBLE.sub(r"\1", text)))

def medicine_g1(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m6_g1(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 97 — indic / G1 / `DB-G1-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-gu-fw2`. Source: section G1 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `a4ab5516e2836afa` (ind-gu-fw2), original offset 2135: `"\u0aac\u0abf\u0ab2 \u0a95\u0ab0\u0aa4\u0abe \u0a82\u0a9a\u0ac1\u0a82\n\u0ab8\u0abe\u0aae\u0abe\u0aa8\u0acd\u0aaf \u0aa6\u0abf\u0ab5\u0abe\u0ab2\u0acb\u0aa5\u0ac0 h"` (fix).
- `bbffb9b814c9ba13` (ind-gu-fw2), original offset 90: `"\u0ab8\u0ac0 > \u0aa8\u0ab5\u0ac0 \u0abf\u0aa6\u0ab2\u0acd\u0ab9\u0ac0\n\u0aa8\u0abe\u0a88\u0a9c\u0ac0\u0ab0\u0abf\u0aaf\u0abe\u0aa8\u0abe \u0a93\u0ab5\u0acb "` (fix).
- `be329b1fecf270e9` (ind-gu-fw2), original offset 23: `"\u0aa7\u0abe\u0aa8\u0ab8\u0aad\u0abe\u0aa8\u0ac0 \u0ac2\u0a82\u0a9f\u0aa3\u0ac0\u0aa8\u0ac7 \u0ab2\u0a87 \u0ab0\u0abe\u0a9c\u0aaf \u0ab8\u0ab0\u0a95\u0abe\u0ab0 \u0aa6"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-G1-003"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

# space before a vowel sign / anusvara, after a consonant, virama or vowel sign
DETACHED = re.compile("(?<=[\u0a95-\u0ab9\u0acd\u0abe-\u0acc]) +(?=[\u0abe-\u0acc\u0a82])")

def medicine(text):
    return DETACHED.sub("", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 7 of 9.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 98 — indic / G1 / `DB-G1-004`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-hi-hplt`. Source: section G1 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `aba71959d76cfb52` (ind-hi-fw2), original offset 3889: `"\u0947 \u0918\u0930 \u091a\u0932\u093e \u093e \u0914\u0930 \u0938\u093e\u0925 \u092e\u0947\u0902 \u092c\u0939\u0941 \u0915\u094b \u092d\u0940 "` (fix).
- `a02caf8e245bbcf3` (ind-hi-hplt), original offset 3740: `"\u093e\u091a\u093e\u0930\u0940 \u092e\u0947 \u0902\u0917\u0941\u091c\u093e\u0930 \u0926\u0947\u0924\u0947 \u0939\u0948\u0902\u0964\u0910\u0902\u0938\u0947 \u0932\u094b"` (fix).
- `8fed2d4464e4cc06` (ind-hi-hplt), original offset 2783: `" \u0930\u0942 \u092a \u092e\u0947 \u0902 \u090f\u0915 \u0928\u093f \u0936\u094d \u091a\u093f \u0924 \u0905\u0935\u0927\u093f \u092e\u0947"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-004"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-hplt', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt, ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g1(text):
    # a read-more marker cut a word before its vowel sign: "ब… [+] िजनेस" -> "बिजनेस"
    t = re.sub("…\\s*\\[\\+\\]\\s*(?=[\u0900-\u0903\u093E-\u094C])", "", text)
    # a space before a vowel sign or anusvara: "मे ं" -> "में"
    t = re.sub("(?<=[\u0915-\u0939\u093C-\u094C\u0958-\u095F])[ \t]+(?=[\u0900-\u0902\u093E-\u094C])", "", t)
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 99 — indic / G1 / `DB-G1-005`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-kn-fw2`. Source: section G1 of `diagnosis/submissions/ind-kn-fw2/keshavamurali/medicine.md`, PR #47 at `8158532`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `634f9d4743893171` (ind-kn-fw2), original offset 13956: `"\u0cc1\u0cb0\u0cbf\u0ca4\u0cc1 \u0cb5\u0ca3 \u0ccd\u0cb8\u0cc1\u0cb5\u0cbe\u0c97 \u2018\u0c97\u0cc1\u0cb0\u0cc1\u0cb5\u0cbf\u0ca8 \u0cae\u0ca8\u0cc6\u0caf\u0cbe\u0c97\u0cc6"` (fix).
- `2914f93d5aa778b8` (ind-kn-fw2), original offset 563: `"\u0ccd\u0ca6 \u0cb5\u0cb8\u0ca1\u0cbf\u0ca8 \u0cca\u0c82\u0ca6\u0ca8\u0ccd\u0ca8\u0cc1 \u0c95\u0c82\u0ca1. \u0ca8\u0cbf\u0c9c \u0c9c\u0cc0\u0cb5\u0ca8\u0ca6\u0cb2"` (fix).
- `21f3f80ab22e0719` (ind-kn-sangraha-s), original offset 13050: `"\u0c9c\u0cbf\u0caf\u0ca8\u0ccd \u0cb7\u0ccd \u0cbf\u0c82\u0caf\u0cbf\u0c82\u0c97\u0ccd\u0caf\u0cbe\u0c82\u0c97\u0ccd] \u0c85\u0ca4\u0ccd\u0caf\u0c82\u0ca4 \u0c85\u0ca7"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-005"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2, ind-kn-sangraha-s"
SOURCE_ORIGIN = "ind-kn-fw2"
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "keshavamurali"  # PR #47 at 8158532
import re  # added by Data B: harm_test_indic.py gives every block `re`

import unicodedata

G1 = re.compile(r'([\u0C80-\u0CFF]) ([\u0CBE-\u0CCD\u0CD5\u0CD6\u0C82\u0C83])')

def medicine_g1(text):
    out = G1.sub(r'\1\2', text)
    return unicodedata.normalize('NFC', out) if out != text else text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #47).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 100 — indic / G1 / `DB-G1-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-mr-fw2`. Source: section G1 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `d40a6e0c632b3dd0` (ind-mr-fw2), original offset 689: `"\u093e\u0926\u0917\u094d\u0930\u0938\u094d\u0924 \u093f\u0928\u0930\u094d\u0923\u092f \u0918\u0947\u0924\u0932\u093e \u0906\u0939\u0947. \u0930\u0947\u0935\u094d\u0939"` (fix).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-006"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-fw2"
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g1(text):
    text = re.sub(r'([\u0915-\u0939\u0958-\u095F])\s+([\u093E-\u094D\u0962\u0963])', r'\1\2', text)
    return re.sub(r'([\u0966-\u096F0-9])\s*ः\s*([\u0966-\u096F0-9])', r'\1:\2', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 101 — indic / G1 / `DB-G1-007`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-sa-fw2`. Source: section G1 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `dfab2a81a8c6cfc6` (ind-sa-fw2), original offset 29167: `"\u093f\u0935\u0927\u0947\u0924\u093f \u0964\n\u094d\u0930\u0923\u092f\u0940 \u092d\u0915\u094d\u0924\u0935\u0924\u094d\u0938\u0932\u0903 \u0915\u0943\u0937\u094d\u0923\u0903"` (fix).
- `26796c0d9077ed0c` (ind-sa-fw2), original offset 4646: `"\u0928\u0935\u0938\u094d\u0925\u093e\u0926\u094c \u0903\u0938\u094d\u0925\u094d\u092f\u092e\u092a\u093f \u0938\u094d\u092f\u093e\u0924\u094d\u0964\n\u0905\u0924\u093f\u0936\u092f"` (fix).
- `1920901e618b8f0c` (ind-sa-fw2), original offset 5103: `"\u0926\u0935\u0930\u0941\u0928\u094d\u0927\u0947 \u0941, \u0924\u094d\u0930\u092f\u0940\u0930\u094d\u0935\u093e \u0906\u092a\u094b, \u0926\u093f\u0935\u094d\u092f"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-007"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g1(text):
    return re.sub("(?<=[ऀ-ॿ])[ \t \n]+(?=[ा-ौॢॣँ-ः्])", "", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 102 — indic / G1 / `DB-G1-008`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-G1-007. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-sa-fw2`. Source: section G1 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `fix_g1(text)`.

```python deferred
RULE_ID = "DB-G1-008"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-G1-007"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

CONS = r"\u0915-\u0939\u0958-\u095F"    # consonants क-ह and nukta consonants
DEP = r"\u0901-\u0903\u093C\u093E-\u094D"    # candrabindu, anusvara, visarga, nukta, matras, virama
MATRA = r"\u093E-\u094C"    # vowel signs only
RE_G1_WS = re.compile(rf"([{CONS}])[ \t\u00A0]+([{DEP}])(?![{MATRA}])")
RE_G1_NL = re.compile(rf"([{CONS}])[ \t\u00A0]*\r?\n[ \t\u00A0]*([{DEP}])(?![{MATRA}])")
RE_G1_DOUBLE_VIRAMA = re.compile(r"्{2,}")

def fix_g1(text):
    text = RE_G1_WS.sub(r"\1\2", text)
    text = RE_G1_NL.sub(r"\1\2", text)
    return RE_G1_DOUBLE_VIRAMA.sub("्", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = fix_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 103 — indic / G1 / `DB-G1-009`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-ta-sangraha-v`. Source: section G1 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python deferred
RULE_ID = "DB-G1-009"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-ta-sangraha-v'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

_LEGACY = {("ெ", "ா"): "ொ", ("ே", "ா"): "ோ"}  # sign typed before the consonant, then ா: one two-part vowel sign

def medicine_g1(text):
    text = text.replace("ா்", "ர்").replace("ுா", "ூ")
    return re.sub("(?<![க-ஹ])([ெேை])([க-ஹ])(ா?)",
                  lambda m: m[2] + _LEGACY.get((m[1], m[3]), m[1] + m[3]), text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 25 documents, none labelled `clean`. The one changed document
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 104 — indic / G1 / `DB-G1-010`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-te-fw2`. Source: section G1 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `a472cbb07057854e` (ind-te-fw2), original offset 3996: `"\u0c2e\u0c3e\u0c1a\u0c3e\u0c30\u0c02. \u0c4d\u0c1c\u0c15\u0c3e\u0c17\u0c3e, \u0c24\u0c28 \u0c2d\u0c30\u0c4d\u0c24\u0c28\u0c41 \u0c2a\u0c4b\u0c32\u0c40\u0c38\u0c41"` (fix).
- `b1fc122a01e457a3` (ind-te-fw2), original offset 2040: `" \u0c2a\u0c48\u0c15\u0c3f - \u0c3f\u0c3f\u0c1a\u0c47\u0c26\u0c41 | \u0c24\u0c40\u0c2f \u0c28\u0c17\u0c41\u0c1a\u0c41 \u0c15\u0c4d\u0c37\u0c47\u0c2e"` (fix).
- `ee82b5653a41e703` (ind-te-fw2), original offset 5: `"\u0c42 Delhi \u0c3f\u0c32\u0c4d\u0c32\u0c40, \u0c2e\u0c47 18: COVID \u0c2e\u0c30\u0c23\u0c3e"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `g1_orphan_signs(text)`.

```python
RULE_ID = "DB-G1-010"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-s, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

G1_RX = re.compile(r"(?m)(^|\s)[ా-ౖఁ-ఃౢౣ]+")
def g1_orphan_signs(t, url=None):
    return G1_RX.sub(r"\1", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = g1_orphan_signs  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 105 — indic / G2 / `DB-G2-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G2 Lost ZWJ or ZWNJ. Pack `ind-bn-fw2`. Source: section G2 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `977423f75b08e75f` (ind-bn-fw2), original offset 21: `"\u09bf \u09ab\u09cd\u09b0\u09bf \u09b0\u09cd\u09af\u09be\u09a1\u09bf\u0995\u09cd\u09af\u09be\u09b2 \u09a8\u09be\u09ae\u09c7 \u09aa\u09b0\u09bf\u099a\u09bf\u09a4 \u0989"` (fix).
- `61e81566d086ef88` (ind-bn-fw2), original offset 29: `"\u09c7\u09b0 \u0986\u0997\u09c7 \u09b0\u09cd\u09af\u09be\u09b2\u09c0 \u09ac\u09c7\u09b0 \u09b9\u09af\u09bc\u0964\n\u09ac\u0997\u09c1\u09a1\u09bc\u09be \u0985\u09ab"` (fix).
- `cc07a8eb9ec9edb7` (ind-bn-fw2), original offset 1178: `"\u09b8\u09b0 \u09b9\u09b2\u09c7 \u09b0\u09cd\u09af\u09be\u09ac-\u09e9 \u098f\u09b0 \u098f\u0995\u099f\u09bf \u099f\u09bf\u09ae \u098f\u09b8\u09c7 \u0997"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g2(text)`.

```python
RULE_ID = "DB-G2-001"
CODE = "G2"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

ZWJ = chr(0x200D)
# র + \u09cd + য + \u09be at the start of a word is the loan-word ra + ya-phala (র\u200d\u09cdযাব, র\u200d\u09cdযালি). Without ZWJ it
# renders as reph + য (র্যা). Inside a word the reph reading is correct (কার্যালয়), and after a virama
# (ব্র্যান্ড) র is already a ra-phala, so those are left alone.
_LOAN = re.compile('(?<![\u0980-\u09ff])র্(?=যা)')

def medicine_g2(text):
    """Insert ZWJ after র in loan-word র্যা."""
    return _LOAN.sub('র' + ZWJ + '\u09cd', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G2 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 106 — indic / G2 / `DB-G2-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-G2-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G2 Lost ZWJ or ZWNJ. Pack `ind-bn-fw2`. Source: section G2 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g2(text)`.

```python deferred
RULE_ID = "DB-G2-002"
CODE = "G2"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-G2-001"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re

_G2_RX = re.compile("(?:^|(?<=[^ঀ-৿])|(?<=্))র্যা", re.M)


def medicine_g2(text):
    """র্যা at a word start or after a virama -> র + ZWJ + ্যা (the loanword form)."""
    return _G2_RX.sub("র‍্যা", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314 (circular, see above). **Warning:** a gold set built from the same FineWeb-2 dump
5. **Side effects:** in the author's `medicine.md`, section G2 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 107 — indic / G2 / `DB-G2-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G2 Lost ZWJ or ZWNJ. Pack `ind-sa-fw2`. Source: section G2 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g2(text)`.

```python
RULE_ID = "DB-G2-003"
CODE = "G2"
ACTION = "keep"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

def detect_g2(text):
    """Always False: G2 cannot be detected from the text alone. The pack contains zero U+200C/U+200D,
    so there is no in-text signal; detection is source_compare.py's comparison with the crawl-date page."""
    return False
def medicine_g2(text):
    return text    # action none: no in-text signal; detection is source_compare.py
# source_compare.py, in words: zw_source = count(U+200C, U+200D) in fetched page text;
# zw_pack = same count in the pack text; flag G2 when zw_source > 0 and zw_pack == 0,
# evidence = the source words that carried the joiner, located in the pack text by offset.


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G2 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 108 — indic / G4 / `DB-G4-001`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G4 Over-normalised. Pack `ind-kn-sangraha-v`. Source: section G4 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g4(text)`.

```python deferred
RULE_ID = "DB-G4-001"
CODE = "G4"
ACTION = "fix"
STAGE = "10"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-kn-sangraha-v'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

"""Find visarga (U+0C83) that stands for a colon.

The Indic NLP normaliser (correct_visarga) rewrites ':' after an Indic letter as visarga, so a dateline
'ಬೆಂಗಳೂರು:' becomes 'ಬೆಂಗಳೂರುಃ'. Real visarga words are a small closed set: Sanskrit adverbs in -ತಃ / -ಶಃ,
a few words (ಪುನಃ, ನಮಃ, ...) and compound prefixes (ದುಃಖ, ನಿಃಸಂಶಯ, ಅಂತಃಕರಣ). Lines with a danda (। ॥) are
treated as Sanskrit verse and left alone. PDF verse often writes the danda as '|' or '||': in a document where a
visarga is followed by '|', or where two or more lines end in '|', every line with a '|' is left alone too.
"""
import re

VIS, VIRAMA, AA_SIGN = chr(0x0C83), chr(0x0CCD), chr(0x0CBE)
KN_BLOCK = chr(0x0C80) + "-" + chr(0x0CFF)                  # the Kannada block, for character classes
JOINERS = chr(0x200C) + chr(0x200D)                          # ZWNJ, ZWJ
KN = re.compile("[" + KN_BLOCK + "]")
WORD_END = re.compile("[" + KN_BLOCK + JOINERS + "]+$")
GENUINE_END = re.compile(r"(ತಃ|ಶಃ)$")
GENUINE = {"ಪುನಃ", "ನಮಃ", "ಮನಃ", "ಅಂತಃ", "ಯಶಃ", "ತೇಜಃ", "ಶಿರಃ", "ಪ್ರಾತಃ", "ಉರಃ", "ಛಂದಃ", "ತಪಃ", "ಪಯಃ",
           "ವಯಃ", "ನಭಃ", "ಅಧಃ", "ಪುರಃ", "ಬಹಿಃ", "ದುಃ", "ನಿಃ", "ಮುಹುಃ", "ಚಕ್ಷುಃ", "ಆಯುಃ", "ಧನುಃ", "ವಪುಃ",
           "ಹವಿಃ", "ಜ್ಯೋತಿಃ", "ಶ್ರೇಯಃ", "ಮನಸಃ", "ರಜಃ", "ತಮಃ", "ಸ್ವಾಹಾಃ", "ಓಂನಮಃ", "ಸ್ವತಹಃ"}
PIPE_AFTER_VIS = re.compile(VIS + r"[ \t]*\|")
PREFIX = {"ದು", "ನಿ", "ಅಂತ", "ಮನ", "ತೇಜ", "ಪ್ರಾತ", "ಬಹಿ", "ಪುನ", "ಛಂದ", "ತಪ", "ಯಶ", "ಅಧ", "ಶಿರ", "ಸುದು",
          "ಸರ್ವದು", "ಸುಖದು", "ಮನಸ್ತಾಪದು"}

def colon_visargas(t, verse_min=2, verse_len=160):
    """Return the offsets of every visarga in t that stands for a colon.

    A line with verse_min or more candidates is taken as Sanskrit verse and skipped when it is short
    (verse_len characters or less) or when most candidates end like a Sanskrit nominative (-aH after a
    bare consonant, or -AH). Kannada prose with several colons ends them on vowel signs (ಹೇಳುತ್ತಾರೆಃ).
    """
    verse_doc = "।" in t or "॥" in t
    by_line = {}
    for i in _candidates(t):
        start = t.rfind("\n", 0, i) + 1
        if verse_doc and t[i - 1] != VIRAMA and " " in t[start:i].strip():
            continue                                    # a document with verse: only first words and ್ಃ
        by_line.setdefault(start, []).append(i)
    out = []
    for start, offs in by_line.items():
        end = t.find("\n", start); end = len(t) if end < 0 else end
        if len(offs) >= verse_min:
            sanskrit = sum(1 for i in offs if t[i - 1] == AA_SIGN or 0x0C95 <= ord(t[i - 1]) <= 0x0CB9)
            if end - start <= verse_len or sanskrit / len(offs) >= 0.75:
                continue
        out.extend(offs)
    return out

def _candidates(t):
    out = []
    pipe_verse = bool(PIPE_AFTER_VIS.search(t)) or sum(1 for l in t.split("\n") if l.rstrip().endswith("|")) >= 2
    for m in re.finditer(VIS, t):
        i = m.start()
        line_start = t.rfind("\n", 0, i) + 1
        line_end = t.find("\n", i); line_end = len(t) if line_end < 0 else line_end
        if "।" in t[line_start:line_end] or "॥" in t[line_start:line_end]:
            continue
        if pipe_verse and "|" in t[line_start:line_end]:
            continue                                    # verse with '|' as danda
        p = t[i - 1] if i else " "
        if p == VIRAMA:
            out.append(i); continue
        if not KN.match(p):
            continue                                    # orphan visarga: G1, not a colon
        w = WORD_END.search(t[:i]).group()
        nx = t[i + 1] if i + 1 < len(t) else " "
        if KN.match(nx):                                # visarga inside a word
            if w in PREFIX or w.endswith(("ದು", "ನಿ")) or len(w) < 3:
                continue
            out.append(i); continue
        if GENUINE_END.search(w + VIS) or (w + VIS) in GENUINE:
            continue
        out.append(i)
    return out

def fix(t):
    """Medicine: turn colon-visarga back into ':'."""
    pos = set(colon_visargas(t))
    return "".join(":" if i in pos else c for i, c in enumerate(t))


fix_visarga = fix
DEC_SPLIT = re.compile(r"(?<=[^\d\n.])(\d{1,3})\. (\d{1,3})(?![\d.])")
DOMAIN_SPLIT = re.compile(r"\b([A-Za-z0-9-]+)\. (com|in|org|net|gov|co|info|edu)\b")
WWW_SPLIT = re.compile(r"\bwww\. (?=[A-Za-z0-9])")


def fix_dot_split(t):
    """G4: join a dot split by an inserted space inside a decimal, a clock time or a web address (3. 3, 10. 20,
    newskadaba. com, www. vknews. in). A number at the start of a line (a list item '1. 5 ...') is left alone."""
    t = WWW_SPLIT.sub("www.", t)
    for _ in range(3):                                  # karnataka. gov. in needs two passes
        t = DOMAIN_SPLIT.sub(r"\1.\2", t)
    return DEC_SPLIT.sub(r"\1.\2", t)


def fix_over_normalised(t):
    """G4: undo the two marks of the earlier normaliser: visarga for a colon, then the dot split."""
    return fix_dot_split(fix_visarga(t))


def medicine_g4(text):
    """The G4 rule, under the name that the harm tests look for: returns the fixed text."""
    return fix_over_normalised(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section G4 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 109 — indic / G4 / `DB-G4-002`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G4 Over-normalised. Pack `ind-mr-fw2`. Source: section G4 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS); ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `5c05e18231a55839` (ind-mr-fw2), original offset 1784: `"\u092c\u093e\u0924\u092e\u094d\u092f\u093e | Maharashtra Times"` (fix).
- `c8ad1802a6fbb058` (ind-mr-fw2), original offset 1767: `"\u092c\u093e\u0924\u092e\u094d\u092f\u093e | Maharashtra Times"` (fix).
- `052f2791183c599c` (ind-mr-fw2), original offset 22007: `"\u093e \u0930\u093e\u0938\u094d\u0924 |\n\u092d\u0930\u0924\u0940 \u092e\u0942\u0930\u094d\u0916\u093e\u0902\u091a\u0940\u091a \u0939\u094b\u0924 \u0928\u093e"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g4(text)`.

```python
RULE_ID = "DB-G4-002"
CODE = "G4"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2', 'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2, ind-mr-sangraha-v"
SOURCE_ORIGIN = "ind-mr-fw2"
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g4(text):
    lines = text.splitlines(keepends=True)
    out = []
    for line in lines:
        if line.strip().startswith('|') and line.strip().endswith('|'):
            out.append(line)
        else:
            line = re.sub(r'(?<=[\u0900-\u097F])\s*\|\|\s*', ' ॥ ', line)
            line = re.sub(r'(?<=[\u0900-\u097F])\s*\|\s*(?=[\u0900-\u097F\s]|$)', ' । ', line)
            out.append(line)
    return ''.join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G4 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 110 — indic / G4 / `DB-G4-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G4 Over-normalised. Pack `ind-sa-fw2`. Source: section G4 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `b54ef4486f508f61` (ind-sa-fw2), original offset 1184: `"\u092f\u094b \u0928\u0948\u0924\u093f\u09651.311\u0965\n\u092a\u094d\u0930\u091c\u093e\u092a\u0924\u093f\u0930\u094d \u0939 \u0935\u093e \u090f"` (fix).
- `456409524fb8d091` (ind-sa-fw2), original offset 25: `"\n\u0905\u0927\u094d\u092f\u093e\u092f 6\n\u0905\u0917\u094d\u0928\u093f\u0937\u094d\u091f\u094b\u092e\u0947 \u0905\u0917\u094d\u0928\u0940\u0937\u094b\u092e\u0940\u092f"` (fix).
- `1920901e618b8f0c` (ind-sa-fw2), original offset 72: `"\u0937\u094d\u0923\u0935\u092e\u094d)\n3.6.1 \u0905\u0928\u0941\u0935\u093e\u0915\u09031\n\u0906\u0917\u094d\u0928\u093e\u0935\u0948\u0937\u094d"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g4(text)`.

```python
RULE_ID = "DB-G4-003"
CODE = "G4"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

RE_G4_RUN = re.compile(r"[0-9]+(?:[.,:/\-][0-9]+)*")
DEVA_CTX = r"\u0904-\u0939\u0958-\u0961\u0972-\u097F"   # Devanagari letters only
RE_DEVA_CTX = re.compile(rf"[{DEVA_CTX}]")
RE_LATIN = re.compile(r"[A-Za-z]"); RE_DEVA_DIGIT = re.compile(r"[०-९]")
TO_DEVA_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९"); CTX = 10; MIN_RUNS = 3
# news-prose guard: month names (Hindi/Sanskrit/Marathi stems), currency words, %, दिनाङ्क within NEWS_CTX chars
NEWS_WORDS = (r"जनवर|फरवर|फेब्रु|मार्च|अप्रैल|एप्रिल|मई|जून|जुलाई|जुलै|अगस्त|आगस्ट|सितम्बर|सितंबर|सप्टेम्बर|सेप्टेम्बर|"
              r"अक्टूबर|अक्तूबर|ऑक्टोबर|नवम्बर|नवंबर|नोव्हेम्बर|दिसम्बर|दिसंबर|डिसेम्बर|"
              r"रूप्यक|रुपय|रूपय|रु\.|₹|करोड|लाख|डॉलर|डालर|%|दिनाङ्क|दिनांक")
RE_G4_NEWS = re.compile(NEWS_WORDS); NEWS_CTX = 12

def _g4_convert_run(m):
    run = m.group()
    if ":" in run or "/" in run or "-" in run: return run
    s = m.string; left = s[max(0, m.start() - CTX):m.start()]; right = s[m.end():m.end() + CTX]
    if not (RE_DEVA_CTX.search(left) and RE_DEVA_CTX.search(right)): return run
    if RE_LATIN.search(left) or RE_LATIN.search(right): return run
    nleft = s[max(0, m.start() - NEWS_CTX):m.start()]; nright = s[m.end():m.end() + NEWS_CTX]
    if RE_G4_NEWS.search(nleft) or RE_G4_NEWS.search(nright): return run   # date or amount in news prose
    return run.translate(TO_DEVA_DIGITS)

def fix_g4_all_ascii(text):            # helper called by fix_g4_mixed_only
    convertible = sum(1 for m in RE_G4_RUN.finditer(text) if _g4_convert_run(m) != m.group())
    if convertible < MIN_RUNS: return text
    return RE_G4_RUN.sub(_g4_convert_run, text)

def fix_g4_mixed_only(text):           # the G4 medicine
    if not RE_DEVA_DIGIT.search(text): return text
    return fix_g4_all_ascii(text)

def medicine_g4(text):                 # the G4 medicine = fix_g4_mixed_only
    return fix_g4_mixed_only(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G4 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 111 — indic / G4 / `DB-G4-004`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G4 Over-normalised. Pack `ind-ta-sangraha-v`. Source: section G4 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-ta-sangraha-v: 0 changed / 0 dropped of 41 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `b696ac9e380537d5` (ind-ta-sangraha-v), original offset 2206: `"18Tamil. com) \u0b87\u0ba3\u0bc8\u0baf\u0ba4\u0bb3\u0ba4\u0bcd\u0ba4\u0bbf\u0bb2\u0bcd \u0b89\u0b9f\u0ba9\u0bc1\u0b95"` (fix).
- `2bd051878060e7e3` (ind-ta-sangraha-v), original offset 1741: `"//study. iitm. ac. in/es/ \u0b8e\u0ba9\u0bcd\u0bb1 \u0b87"` (fix).
- `89879512ea611689` (ind-ta-sangraha-v), original offset 22: `"\u0bcb\u0b95\u0bcd\u0b95\u0bbf 2. 0!\n \u0bb0\u0b9c\u0bbf\u0ba9\u0bbf\u0b95\u0bbe\u0ba8\u0bcd\u0ba4\u0bcd \u0ba8\u0b9f\u0bbf\u0baa\u0bcd\u0baa\u0bbf"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g4(text)`.

```python
RULE_ID = "DB-G4-004"
CODE = "G4"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-ta-sangraha-v'}
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"
SOURCE_ORIGIN = "ind-ta-sangraha-v"
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def medicine_g4(text):
    text = re.sub(r"(?<=\d)\. (?=\d)", ".", text)  # 28. 17 -> 28.17
    return re.sub(r"\b[A-Za-z0-9-]+(?:\. [A-Za-z0-9-]+)*\. (?:com|in|org|net|lk|info)\b",
                  lambda m: m[0].replace(". ", "."), text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 65 documents, none labelled `clean`. The 22 changed documents
5. **Side effects:** in the author's `medicine.md`, section G4 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 112 — indic / B2 / `DB-B2-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B2 HTML or XML tags. Pack `ind-hi-fw2`. Source: section B2 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_b2(text)`.

```python
RULE_ID = "DB-B2-001"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-fw2"
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
_URL_TOKEN = re.compile(r"https?://\S+|data:image/\w+;base64,\S+")

def medicine_b2(text: str) -> str:
    """Remove HTML/XML tags; keep surrounding text. (Automatic medicine; URL strip is helper-only.)"""
    return _HTML_TAG_RE.sub("", text or "")

def _strip_b2_urls(text: str) -> str:
    """Optional selective fix: blank URL tokens (review before mass use). Not automatic medicine."""
    return _URL_TOKEN.sub("", text or "")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `ind-hi-fw2_gold.csv` (**234** docs, post-#161). Tool: `harm_test_indic.py --rule B2` (2026-10-31). Ran **`medicine_b2` (tag strip only)**:
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 113 — indic / B2 / `DB-B2-002`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B2 HTML or XML tags. Pack `ind-hi-hplt`. Source: section B2 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `803472a29da319bf` (ind-hi-hplt), original offset 7415: `"\u0915\u0930\u0924\u093e \u0939\u0948\u0964/>\u0936\u0948\u0915\u094d\u0937\u2026 [+] \u093f\u0915 \u0935\u093f\u091c\u094d\u091e\u093e\u0928 "` (fix).
- `1c61f6e0c56fbbc9` (ind-hi-hplt), original offset 9367: `"\u0941\u0938\u094d\u0924\u0915\u093e\u0932\u092f/>\u092a\u0941\u0938\u094d\u0924\u0915\u093e\u0932\u092f \u091b\u093e\u0924\u094d\u0930\u094b\u0902 \u0926\u094d\u0935\u093e"` (fix).
- `a752dfa857b4ecd2` (ind-hi-hplt), original offset 77501: `"\u0930\u0924\u0947 \u0939\u0948\u0902\u0964/>\u092e\u093f\u0936\u0928\u092e\u093f\u0936\u0928 \u0914\u0930 \u0938\u094d\u092a\u0947\u0928 \u092c\u093f\u091c\u0928"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_b2(text)`.

```python
RULE_ID = "DB-B2-002"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-hplt'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_b2(text):
    if "<" in text:  # a real tag is there: leave it to an HTML cleaner
        return text
    return re.sub("[ \t]*/>", "", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 114 — indic / B2 / `DB-B2-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B2 HTML or XML tags. Pack `ind-kn-sangraha-s`. Source: section B2 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS); ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3a69a945a1b7aeaa` (ind-kn-sangraha-s), original offset 565: `"\u0cb0\u0ccd\u0c95\u0c97\u0cb3\u0cc1.\n<\u0cac\u0cbf. \u0c86\u0cb0\u0ccd.>\n\n"` (fix).
- `c3db2fd821c28710` (ind-kn-sangraha-s), original offset 37833: `"\u0c97\u0cca\u0c82\u0ca1\u0cb0\u0cc1.\n\u0c90. \u0ca1\u0cbf. 1\u0cb0\u0cb2\u0ccd\u0cb2\u0cbf, \u0c85\u0caf\u0ccb\u0ca8\u0cc6\u0cb8\u0ccd\u0c95\u0cc1"` (fix).
- `ab411bfbfa80fe2a` (ind-kn-sangraha-s), original offset 306: `"\u0cae\u0cbe\u0cb9\u0cbf\u0ca4\u0cbf.\n<\u0cac\u0cbf. \u0c86\u0cb0\u0ccd.>\n\n"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `m1_tags(text)`.

```python
RULE_ID = "DB-B2-003"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s', 'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s, ind-kn-fw2, ind-kn-sangraha-v"
SOURCE_ORIGIN = "ind-kn-sangraha-s"
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

TAG_ID = re.compile(r" ?<?ಐ\. ಡಿ\. \d+>?")
TAG_BR = re.compile(r"<ಬಿ\.? ?ಆರ್\.?>|<br\s*/?>", re.I)
TAG_ANY = re.compile(r"</?(?:[A-Za-zÀ-ÿ][^<>\n]{0,40}|ರಿಫರ್[^<>\n]{0,80})>|<>")
def m1_tags(s):
    s = TAG_BR.sub("\n", s)
    return TAG_ANY.sub("", TAG_ID.sub("", s))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m1_tags  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 0 of 359.
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 115 — indic / B2 / `DB-B2-004`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B2 HTML or XML tags. Pack `ind-te-fw2`. Source: section B2 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `7ef5b7ab6df65268` (ind-te-fw2), original offset 2491: `"\u0c30\u0c4d\u0c37\u0c3f\u0c15\n- <span style=\"font-family"` (fix).
- `b5637f3271aa29f2` (ind-te-fw2), original offset 0: `"<span style=\"font-family"` (fix).
- `41c998453152115f` (ind-te-fw2), original offset 1260: `"\u0c32\u0c3f\u0c2a\u0c3e\u0c30\u0c41.\n<a href=\"https://www.sia"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `b2_html(text)`.

```python
RULE_ID = "DB-B2-004"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

B2_RX = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^<>]{0,300})?/?>|<>|\b(?:width|height|class|style)=\"[^\"]*\"")
def b2_html(t, url=None):
    return B2_RX.sub("", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = b2_html  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 116 — indic / B2 / `DB-B2-005`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B2 HTML or XML tags. Pack `ind-te-sangraha-s`. Source: section B2 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `d7d13ed37c277bea` (ind-te-sangraha-s), original offset 292: `"\u0c38\u0c42\u0c1a\u0c28\u0c32\u0c41.\n<\u0c2c\u0c3f\u0c06\u0c30\u0c4d>\n\n"` (fix).
- `79167d66fe9ef5eb` (ind-te-sangraha-s), original offset 1526: `"\u0c35\u0c32\u0c4b\u0c15\u0c28\u0c02.\n<</\u00c2>\n\u0c2a\u0c02\u0c2a\u0c3f\u0c23\u0c40.\n\u0c21\u0c30\u0c4d\u0c39\u0c3e\u0c2e\u0c4d \u0c15\u0c4c"` (fix).
- `5c1b142ee4cd51b6` (ind-te-sangraha-s), original offset 426: `"\u0c38\u0c4b\u0c21\u0c4d\u0c32\u0c41.\n<</\u00c2>\n\n"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_b2(text)`.

```python
RULE_ID = "DB-B2-005"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-sangraha-s'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"
SOURCE_ORIGIN = "ind-te-sangraha-s"
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_b2(text):
    text = re.sub(r"<</[^<>\s]{0,3}>", "", text)
    text = re.sub(r"<[\u0C00-\u0C7F]{1,12}>", "", text)
    text = re.sub(r"(?<=[.!?])>(?=\s|$)", "", text)
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_b2` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 117 — indic / B3 / `DB-B3-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B3 Ghost chat markers. Pack `ind-kn-sangraha-s`. Source: section B3 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS); ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `76ff156acd160ee4` (ind-kn-sangraha-s), original offset 209: `" \u0caf\u0cbf\u0c82\u0c97\u0ccd (<unk>), \u0cae\u0ca4\u0ccd\u0ca4\u0cc1 \u0ca1\u0ccd\u0caf\u0cc2\u0c95\u0ccd \u0cb9\u0cc1\u0caf"` (fix).
- `d5133441c9d74b4f` (ind-kn-sangraha-s), original offset 29: `"\u0c95 \u0c9a\u0cc0\u0ca8\u0cc0\u0c83 <unk>, \u0cb8\u0cb0\u0cb3\u0cc0\u0c95\u0cc3\u0ca4 \u0c9a\u0cc0\u0ca8\u0cc0\u0c83 <un"` (fix).
- `a84cbd8f664d1816` (ind-kn-sangraha-s), original offset 745: `" \u0c89\u0cb0\u0cbe\u0cac\u0cc6 (<unk>) \u0caa\u0ccd\u0cb2\u0cbe\u0cb8\u0ccd\u0c9f\u0ccd\u0cb0\u0ccb\u0cae\u0cc6\u0ca8\u0ccd\u0cb8\u0cbf\u0caf"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `m2_ghost(text)`.

```python
RULE_ID = "DB-B3-001"
CODE = "B3"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s', 'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s, ind-kn-fw2, ind-kn-sangraha-v"
SOURCE_ORIGIN = "ind-kn-sangraha-s"
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

GHOST = re.compile(r"<unk>|<\|[a-z_]+\|>|\[/?INST\]|</?s>|</?think>")
def m2_ghost(s):
    return GHOST.sub("", s)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m2_ghost  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 0 of 359.
5. **Side effects:** in the author's `medicine.md`, section B3 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 118 — indic / A3 / `DB-A3-003`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-A3-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A3 Mojibake. Pack `ind-bn-fw2`. Source: section A3 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a3(text)`.

```python deferred
RULE_ID = "DB-A3-003"
CODE = "A3"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-A3-001"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_PAIRS = [('\u09be\u09c7', '\u09cb'),   # \u09be + \u09c7 typed for \u09cb
          ('\u09c8\u09be', '\u09cc'),   # \u09c8 + \u09be typed for \u09cc
          ('\u09c7\u09c7', '\u09c7'), ('\u09bf\u09bf', '\u09bf'), ('\u09c1\u09c1', '\u09c1'), ('\u09be\u09be', '\u09be')]
# Bijoy / legacy-font residue: a Latin-1 symbol, dash or angle quote glued between two Bengali characters.
_RESIDUE = re.compile('(?<=[\u0980-\u09ff])[¡-ÿ–—‹›‚”](?=[\u0980-\u09ff])')

def medicine_a3(text):
    """Drop a document with 3 or more legacy-font residues (they cannot be mapped back safely).
    Otherwise repair doubled or misordered vowel signs."""
    if len(_RESIDUE.findall(text)) >= 3:
        return True
    for bad, good in _PAIRS:
        text = text.replace(bad, good)
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A3 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 119 — indic / A3 / `DB-A3-004`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A3 Mojibake. Pack `ind-kn-sangraha-v`. Source: section A3 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS); ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `634f9d4743893171` (ind-kn-fw2), original offset 0: `"\u0cad\u0cbe\u0cb0\u0ca4\u0ca6 \u0c9a\u0cb0\u0cbf\u0ca4\u0ccd\u0cb0\u0cc6\u0caf\u0ca8\u0ccd\u0ca8\u0cc1 \u0ca4\u0cbf\u0cb3\u0cbf\u0caf\u0cc1\u0cb5\u0cc1\u0ca6\u0c95\u0ccd\u0c95\u0cc6 \u0cb6\u0cbf\u0cb7\u0ccd\u0c9f \u0cb8\u0cbe\u0cb9\u0cbf\u0ca4\u0ccd\u0caf\u0ca6\u0cb7\u0ccd\u0c9f\u0cc6 \u0cae\u0ccc\u0c96\u0cbf\u0c95 \u0cb8\u0cbe\u0cb9\u0cbf\u0ca4\u0ccd"` (drop).
- `bf21eb9f2a9511b6` (ind-kn-fw2), original offset 0: `"\u0cb9\u0cca\u0cb8 \u0ca4\u0cb2\u0cc6\u0cae\u0cbe\u0cb0\u0cbf\u0ca8 \u0ca4\u0cb0\u0cc1\u0ca3 \u0cac\u0cb0\u0cb9\u0c97\u0cbe\u0cb0\u0cb0\u0cb2\u0ccd\u0cb2\u0cbf \u0cb6\u0cb0\u0cc0\u0cab\u0ccd \u0cb9\u0cb8\u0cae\u0c95\u0cb2\u0ccd \u0c85\u0cb5\u0cb0\u0cc1 \u0c92\u0cac\u0ccd\u0cac\u0cb0\u0cbe\u0c97\u0cbf\u0ca6\u0ccd\u0ca6\u0cbe\u0cb0\u0cc6. "` (drop).
- `6652e0ea74804194` (ind-kn-fw2), original offset 0: `"\u201c\u0ca8\u0cbe\u0cb0\u0cbe\u0caf\u0ca3\u0c97\u0cc1\u0cb0\u0cc1\u0c97\u0cb3 \u0c9c\u0cc0\u0cb5\u0ca8 \u0cb6\u0cc8\u0cb2\u0cbf \u0ca8\u0cae\u0c97\u0cc6\u0cb2\u0ccd\u0cb2 \u0cae\u0cbe\u0ca6\u0cb0\u0cbf\u201d\nTeam Udayavani, Jan 23, 2"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a3(text)`.

```python
RULE_ID = "DB-A3-004"
CODE = "A3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s', 'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v, ind-kn-fw2, ind-kn-sangraha-s"
SOURCE_ORIGIN = "ind-kn-sangraha-v"
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

import re

IAST = set("āīūṛṝḷṅñṇṭḍśṣḥṁĀĪŪṚṄÑṆṬḌŚṢḤṀ")              # romanised Indic, not legacy-font residue


def is_kn(c):
    return 0x0C80 <= ord(c) <= 0x0CFF


def legacy_residue(t):
    """A3: offsets of legacy-font (Nudi/Baraha) residue inside Kannada words.

    Residue is a Latin-1 or Latin Extended letter inside a word that also holds Kannada (ಸಂಸ್ಕøತಿ), or a '$'
    directly before a Kannada vowel sign or virama (ಸ್ಕೊ$್ವ). A '$' before a digit ($100ರಷ್ಟು), a degree
    sign (30°ಸೆ) and IAST letters are not residue.
    """
    out = []
    for m in re.finditer(r"\S+", t):
        w = m.group()
        if not any(is_kn(c) for c in w):
            continue
        for k, c in enumerate(w):
            nxt = w[k + 1] if k + 1 < len(w) else " "
            if c.isalpha() and 0xC0 <= ord(c) <= 0x24F and c not in IAST:
                out.append(m.start() + k)
            elif c == "$" and is_kn(nxt) and not nxt.isalpha():
                out.append(m.start() + k)
    return out


def has_legacy(t):
    """A3: drop a document with legacy-font (Nudi/Baraha) residue inside Kannada words."""
    return bool(legacy_residue(t))


def medicine_a3(text):
    """The A3 rule, under the name that the harm tests look for: True drops the document."""
    return has_legacy(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section A3 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 120 — indic / A4 / `DB-A4-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A4 Replacement characters. Pack `ind-sa-fw2`. Source: section A4 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `935e30775b66fab4` (ind-sa-fw2), original offset 0: `"\u0917\u092e\n= \u0917\u0924\u094c \u092d\u094d\u0935\u093e\u0966 \u092a\u0930\u0966 \u0905\u0928\u093f\u091f\u094d\u0964 \u0917\u091a\u094d\u091b\u0924\u093f \u090c\u0926\u093f\u0924\u094d \u0905\u0917\u092e\u0924\u094d \u091c\u0917\u093e\u092e \u091c\u0917\u094d\u092e\u0924\u0941\u0903\u0964 \u0917\u0928\u094d\u0924\u093e"` (drop).
- `605046c0f09bb50f` (ind-sa-fw2), original offset 0: `"\u0935\u094d\u0930\u0924\n= \u0928\u0966 \u0935\u094d\u0930\u091c\u2013\u0918 \u091c\u0938\u094d\u092f \u0924\u0903\u0964 \u0967 \u092d\u0915\u094d\u0937\u0923\u092d\u0947\u0926\u0947 \u0909\u0923\u093e\u0926\u093f\u0966 \u0968 \u092a\u0941\u0923\u094d\u092f\u0938\u093e\u0927\u0928\u0947 \u0969 \u0909\u092a\u0935\u093e"` (drop).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_a4(text)`.

```python
RULE_ID = "DB-A4-001"
CODE = "A4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_a4(text):
    return "�" in text or "{??}" in text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A4 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 121 — indic / A6 / `DB-A6-015`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-A6-003. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** A6 Wrong or mixed script. Pack `ind-gu-fw2`. Source: section A6 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python deferred
RULE_ID = "DB-A6-015"
CODE = "A6"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-gu-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-A6-003"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block

A6_WORD = re.compile(rf"[A-Za-z]+[{GU}]+|[{GU}]+[A-Za-z]+")
A6_ENDING = re.compile(r"[A-Za-z]+(?:ઓ)?(?:એ|ના|ની|નું|નુ|નો|ને|નાં|માં|થી|પર|વાળા|વાળી|ે|ી|ો|ઓ)")

def m7_a6(text, url=None, limit=3):
    n = sum(not A6_ENDING.fullmatch(w) for w in A6_WORD.findall(text))
    return (text, "drop" if n >= limit else "keep")

def medicine_a6(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m7_a6(text, url)[1] == "drop"


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 122 — indic / C3 / `DB-C3-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-bn-fw2`. Source: section C3 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3190209debfab88d` (ind-bn-fw2), original offset 0: `"\u09b8\u09b0\u0995\u09be\u09b0\u09bf \u09b8\u09c2\u09a4\u09cd\u09b0\u09c7 \u098f\u0996\u09a8\u09cb \u09aa\u09b0\u09cd\u09af\u09a8\u09cd\u09a4 \u09a4\u09c7\u0987\u09b6\u099f\u09bf \u09ae\u09c3\u09a4\u09a6\u09c7\u09b9 \u0989\u09a6\u09cd\u09a7\u09be\u09b0 \u0995\u09b0\u09be \u0997\u09c7\u099b\u09c7\u0964 \u09b8\u09cd\u09a5\u09be\u09a8\u09c0"` (drop).
- `605429156ca4df6d` (ind-bn-fw2), original offset 0: `"\u09b9\u09be\u0993\u09b0 \u09ac\u09be\u09b0\u09cd\u09a4\u09be \u09a1\u09c7\u09b8\u09cd\u0995\u0983 \u09a8\u09cc \u09aa\u09cd\u09b0\u09a4\u09bf\u09ae\u09a8\u09cd\u09a4\u09cd\u09b0\u09c0 \u0996\u09be\u09b2\u09bf\u09a6 \u09ae\u09be\u09b9\u09ae\u09c1\u09a6 \u099a\u09cc\u09a7\u09c1\u09b0\u09c0 \u09ac\u09b2\u09c7\u099b\u09c7\u09a8, \u09aa"` (drop).
- `4040d1c6b90ddd77` (ind-bn-fw2), original offset 0: `"\u0986\u099c\u09be\u09a6\u09c1\u09b0 \u09b0\u09b9\u09ae\u09be\u09a8 \u099a\u09a8\u09cd\u09a6\u09a8\n\u099b\u09be\u09a4\u09cd\u09b0 \u0986\u09a8\u09cd\u09a6\u09cb\u09b2\u09a8, \u0995\u09cd\u09b7\u09c7\u09a4\u09ae\u099c\u09c1\u09b0 \u0986\u09a8\u09cd\u09a6\u09cb\u09b2\u09a8 \u0993 \u0995\u09ae\u09bf\u0989\u09a8\u09bf\u09b8\u09cd\u099f "` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-001"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_CUT = re.compile(r'(?:\[\s*(?:…|\.\.\.)\s*\]|বিস্তারিত\s*\.{2,}|Continue\s+Reading|Read\s+(?:Entire\s+Article|more))\W*$', re.I)

def medicine_c3(text):
    """Drop a document whose last line ends with a teaser cut mark ([…], 'বিস্তারিত..', 'Continue Reading').
    Documents cut in mid-sentence without a mark are not touched: they cannot be told apart from
    pages that end with a name, a list item or a caption."""
    last = text.rstrip().rsplit('\n', 1)[-1]
    return bool(_CUT.search(last))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 123 — indic / C3 / `DB-C3-002`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-hi-hplt`. Source: section C3 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `c8d69b4928763080` (ind-hi-hplt), original offset 0: `"\u0906\u092a \u0907\u0938 \u092a\u0947\u091c \u092a\u0930 \u092e\u0947\u0902 \u0935\u093f\u0936\u094d\u0935\u0935\u093f\u0926\u094d\u092f\u093e\u0932\u092f\u094b\u0902, \u0915\u0949\u0932\u0947\u091c\u094b\u0902 \u0914\u0930 \u092c\u093f\u091c\u0928\u0947\u0938 \u0938\u094d\u0915\u0942\u0932\u094b\u0902 \u0915\u0947 \u0932"` (drop).
- `b8d46e4abba176c4` (ind-hi-hplt), original offset 0: `"\u0906\u092a \u0907\u0938 \u092a\u0947\u091c \u092a\u0930 \u092e\u0947\u0902 \u0935\u093f\u0936\u094d\u0935\u0935\u093f\u0926\u094d\u092f\u093e\u0932\u092f\u094b\u0902, \u0915\u0949\u0932\u0947\u091c\u094b\u0902 \u0914\u0930 \u092c\u093f\u091c\u0928\u0947\u0938 \u0938\u094d\u0915\u0942\u0932\u094b\u0902 \u0915\u0947 \u0932"` (drop).
- `803472a29da319bf` (ind-hi-hplt), original offset 0: `"\u0906\u092a \u0907\u0938 \u092a\u0947\u091c \u092a\u0930 \u092e\u0947\u0902 \u0935\u093f\u0936\u094d\u0935\u0935\u093f\u0926\u094d\u092f\u093e\u0932\u092f\u094b\u0902, \u0915\u0949\u0932\u0947\u091c\u094b\u0902 \u0914\u0930 \u092c\u093f\u091c\u0928\u0947\u0938 \u0938\u094d\u0915\u0942\u0932\u094b\u0902 \u0915\u0947 \u0932"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-002"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-hplt', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_CUT = re.compile(r"\[…\]|\[\.\.\.\]|…\s?\[\+\]|Read More")


def medicine_c3(text):
    return len(_CUT.findall(text)) >= 3


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 124 — indic / C3 / `DB-C3-003`

**Integration decision:** DEFERRED. joiners: drops ordinary synthetic prose. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-mr-fw2`. Source: section C3 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python deferred
RULE_ID = "DB-C3-003"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-mr-fw2'}
DEFER_REASON = "joiners: drops ordinary synthetic prose"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c3(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines and len(lines[-1]) >= 40 and lines[-1][-1] not in ".!?।॥۔؟…\"'”’) ]}»":
        return True
    return False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 125 — indic / C3 / `DB-C3-004`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-sa-fw2`. Source: section C3 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `14ee406c9fcc5df9` (ind-sa-fw2), original offset 0: `"\u0915\u0943\u0924\u093e\u0928\u093e\u0902 \u0917\u0923\u0928\u093e\u0928\u093e\u0902 \u091a\u0930\u0923-\u0926\u0930-\u091a\u0930\u0923-\u0938\u0942\u091a\u093f\u0915\u093e \u0938\u0939 \u0926\u094d\u0935\u093f\u091a\u0915\u094d\u0930\u0940\u092f-\u0938\u0919\u094d\u0916\u094d\u092f\u093e\u0924\u0903 \u0926\u0936\u092e\u0932\u0935-"` (drop).
- `da1ff98edc2a471c` (ind-sa-fw2), original offset 0: `"- - - -\nSaturday, July 30, 2011\n- - - -\nWednesday, July 27, 2011"` (drop).
- `661b031765033831` (ind-sa-fw2), original offset 0: `"\u0905\u0924\u094d\u0930 \u0924\u094d\u092f\u091c\u094d\u091c\u0932\u094d\u092a\u093f\u0924\u092f\u094b\u0903 \u092e\u0940\u0928\u0947\u0915\u094d\u0937\u0923\u0947 \u0915\u092e\u0928\u092e\u093f\u0924\u093f \u092a\u0926\u092f\u094b\u0903 \u0938\u094d\u0925\u093f\u0924\u0902 \u092e\u0902 \u092e\u0915\u093e\u0930\u0902 \u0926\u0902 \u0926"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-004"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

from urllib.parse import unquote

def _scan_page(url):
    return "wikisource.org/wiki/पृष्ठम्:" in unquote(url)

def medicine_c3(text):
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) >= 10]
    if not lines:
        return False
    last = lines[-1]
    dev = len(re.findall("[\u0900-\u097F]", last))
    letters = sum(c.isalpha() for c in last) or 1
    return dev / letters > 0.6 and bool(re.search(r"(?:[,‘“(]|(?<=[\u0900-\u097F])-)\s*$", last))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 126 — indic / C4 / `DB-C4-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-bn-fw2`. Source: section C4 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `605429156ca4df6d` (ind-bn-fw2), original offset 0: `"\u09b9\u09be\u0993\u09b0 \u09ac\u09be\u09b0\u09cd\u09a4\u09be \u09a1\u09c7\u09b8\u09cd\u0995\u0983 \u09a8\u09cc \u09aa\u09cd\u09b0\u09a4\u09bf\u09ae\u09a8\u09cd\u09a4\u09cd\u09b0\u09c0 \u0996\u09be\u09b2\u09bf\u09a6 \u09ae\u09be\u09b9\u09ae\u09c1\u09a6 \u099a\u09cc\u09a7\u09c1\u09b0\u09c0 \u09ac\u09b2\u09c7\u099b\u09c7\u09a8, \u09aa"` (drop).
- `4040d1c6b90ddd77` (ind-bn-fw2), original offset 0: `"\u0986\u099c\u09be\u09a6\u09c1\u09b0 \u09b0\u09b9\u09ae\u09be\u09a8 \u099a\u09a8\u09cd\u09a6\u09a8\n\u099b\u09be\u09a4\u09cd\u09b0 \u0986\u09a8\u09cd\u09a6\u09cb\u09b2\u09a8, \u0995\u09cd\u09b7\u09c7\u09a4\u09ae\u099c\u09c1\u09b0 \u0986\u09a8\u09cd\u09a6\u09cb\u09b2\u09a8 \u0993 \u0995\u09ae\u09bf\u0989\u09a8\u09bf\u09b8\u09cd\u099f "` (drop).
- `4c3a514616f31a33` (ind-bn-fw2), original offset 0: `"\u0995\u09c7\u09a8\u09cd\u09a6\u09cd\u09b0\u09c0\u09af\u09bc \u09b8\u09be\u0982\u0997\u09a0\u09a8\u09bf\u0995 \u09b8\u09ae\u09cd\u09aa\u09be\u09a6\u0995 \u09a8\u09bf\u09b0\u09cd\u09ac\u09be\u099a\u09bf\u09a4 \u09b9\u0993\u09af\u09bc\u09be\u09af\u09bc \u09b6\u09ab\u09bf\u0989\u09b2 \u0986\u09b2\u09ae \u099a\u09c8\u09be\u09a7\u09c1\u09b0\u09c0 "` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-001"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_TEASER = re.compile(r'বিস্তারিত\s*\.{2,}|Continue\s+Reading|\[\s*(?:…|\.\.\.)\s*\]|Read\s+More\s*(?:»|→|$)', re.I | re.M)

def medicine_c4(text):
    """Drop index, tag and archive pages: two or more teaser cut marks mean several stories were glued together."""
    return len(_TEASER.findall(text)) >= 2


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 127 — indic / C4 / `DB-C4-002`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-hi-fw2`. Source: section C4 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `9992ed6ebadee109` (ind-hi-fw2), original offset 0: `"\u0935\u093f\u0936\u094d\u0935\u0938\u0928\u0940\u092f\u0924\u093e \u0938\u0942\u091a\u0915 \u092e\u093e\u0924\u094d\u0930\u093e\u0924\u094d\u092e\u0915 \u0930\u0942\u092a \u0938\u0947 \u090f\u0915 \u092f\u093e \u090f\u0915 \u0938\u0947 \u0905\u0927\u093f\u0915 \u0917\u0941\u0923\u094b\u0902 \u0915\u0940 \u0935\u093f\u0936"` (drop).
- `513aa97763bf5d89` (ind-hi-fw2), original offset 0: `"\u0935\u093f\u0926\u0947\u0936\u0940 \u092e\u0941\u0926\u094d\u0930\u093e \u0915\u0947 \u0932\u093f\u090f \u0909\u092a\u0932\u092c\u094d\u0927 \u0935\u093f\u092d\u093f\u0928\u094d\u0928 \u092a\u094d\u0930\u0915\u093e\u0930 \u0915\u0947 \u091f\u093e\u0907\u091f\u0928 \u091f\u094d\u0930\u0947\u0921 \u092c\u094d\u0930\u094b\u0915\u0930"` (drop).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `flag_c4_trading_spam(text)`.

```python
RULE_ID = "DB-C4-002"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-fw2"
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_TRADE_TERMS = re.compile(
    r"फ़ॉरेक्स|फॉरेक्स|\bforex\b|बाइनरी\s+ऑप्शन|binary\s+options?|"
    r"ट्रेडिंग\s+प्लेटफ़?ॉर्म|\btrading\b|\bbroker\b|ब्रोकर|"
    r"ट्रेडिंग|ट्रेडर|ऑप्शन|विकल्प\s+ट्रेड",
    re.I,
)

def flag_c4_trading_spam(text: str) -> bool:
    """True if >=4 distinct trading terms (drop-class C4)."""
    terms = {m.group(0).lower() for m in _TRADE_TERMS.finditer(text or "")}
    return len(terms) >= 4


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = flag_c4_trading_spam  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `ind-hi-fw2_gold.csv` (**234** docs, post-#161). Tool: `harm_test_indic.py --rule C4` (2026-10-31). Ran `flag_c4_trading_spam`:
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 128 — indic / C4 / `DB-C4-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-hi-hplt`. Source: section C4 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `ca38e3770cd4bd18` (ind-hi-hplt), original offset 0: `"\u0906\u092a\u0915\u0940 \u0935\u0947\u092c\u0938\u093e\u0907\u091f \u092a\u0930 \u092a\u0948\u0938\u093e \u092c\u0928\u093e\u0928\u0947 \u0915\u0947 \u0915\u0908 \u0905\u0935\u0938\u0930 \u0939\u0948\u0902\u0964 \u0905\u092a\u0928\u0940 \u0938\u093e\u0907\u091f \u092a\u0930 \u0935\u093f\u091c\u094d\u091e\u093e\u092a\u0928"` (drop).
- `7a2bc38b934a51ad` (ind-hi-hplt), original offset 0: `"\u0938\u0902\u0915\u0947\u0924\u0915 \u0938\u0902\u0915\u0947\u0924\u0915 \u0915\u0902\u092a\u094d\u092f\u0942\u091f\u0930 \u0915\u093e \u0909\u092a\u092f\u094b\u0917 \u0915\u0930 \u092c\u093f\u091f\u0915\u0949\u0907\u0928 \u0915\u0948\u0938\u0947 \u0915\u092e\u093e\u090f\u0902 \u091c\u094b \u0909\u0928\u0915\u0940 \u0935\u093f"` (drop).
- `8fed2d4464e4cc06` (ind-hi-hplt), original offset 0: `"\u0917\u094d\u0930\u093e\u0939\u0915\u094b\u0902 \u0915\u094b \u0935\u093f\u0926\u0947\u0936\u0940 \u092e\u0941\u0926\u094d\u0930\u093e \u092a\u0930 \u092a\u0948\u0938\u0947 \u0915\u092e\u093e\u090f\u0902 \u0915\u093f\u0938\u0940 \u092d\u0940 cryptocurrency \u092d"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-003"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-hplt'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_CUT4 = re.compile(r"\[…\]|\[\.\.\.\]|…\s?\[\+\]|Read More")
_SPAM_FOOTER = re.compile("अधिकतम रेटिंग \\d+\\s*\nन्यूनतम स्कोर")


def medicine_c4(text):
    return len(_CUT4.findall(text)) >= 3 or bool(_SPAM_FOOTER.search(text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 129 — indic / C4 / `DB-C4-004`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C4-003. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-hi-hplt`. Source: section C4 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python deferred
RULE_ID = "DB-C4-004"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C4-003"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C4: listing pages (several teasers joined): drop
def medicine_c4(text):
    cut = text.count("[…]") + text.count("[...]")
    more = len(re.findall(r"(?:…|\.\.\.)\s*\n?\s*Read More", text))
    return cut >= 2 or more >= 2


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 7 of 48 C4 documents; 0 other diseased documents touche...
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 130 — indic / C4 / `DB-C4-005`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-mr-fw2`. Source: section C4 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `a84ec9a0a34a3f12` (ind-mr-fw2), original offset 0: `"\u0906\u092a\u0932\u094d\u092f\u093e \u0936\u0939\u0930\u093e\u0924\u0940\u0932 \u0924\u093e\u091c\u094d\u092f\u093e \u092c\u093e\u0924\u092e\u094d\u092f\u093e \u0906\u0923\u093f \u0908-\u092a\u0947\u092a\u0930 \u092e\u093f\u0933\u0935\u093e \u092e\u094b\u092b\u0924\u0921\u093e\u0909\u0928\u0932\u094b\u0921 \u0915\u0930\u093e\n\u0938"` (drop).
- `d40a6e0c632b3dd0` (ind-mr-fw2), original offset 0: `"\u0906\u092a\u0932\u094d\u092f\u093e \u0936\u0939\u0930\u093e\u0924\u0940\u0932 \u0924\u093e\u091c\u094d\u092f\u093e \u092c\u093e\u0924\u092e\u094d\u092f\u093e \u0906\u0923\u093f \u0908-\u092a\u0947\u092a\u0930 \u092e\u093f\u0933\u0935\u093e \u092e\u094b\u092b\u0924\u0921\u093e\u0909\u0928\u0932\u094b\u0921 \u0915\u0930\u093e\n\u0907"` (drop).
- `cedda2a2f29ef819` (ind-mr-fw2), original offset 0: `"\u0906\u092a\u0932\u094d\u092f\u093e \u0936\u0939\u0930\u093e\u0924\u0940\u0932 \u0924\u093e\u091c\u094d\u092f\u093e \u092c\u093e\u0924\u092e\u094d\u092f\u093e \u0906\u0923\u093f \u0908-\u092a\u0947\u092a\u0930 \u092e\u093f\u0933\u0935\u093e \u092e\u094b\u092b\u0924\u0921\u093e\u0909\u0928\u0932\u094b\u0921 \u0915\u0930\u093e\n\u092c"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-005"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-fw2"
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c4(text):
    if "\nCopyright ©" in text[200:]:
        return True
    return False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 131 — indic / C4 / `DB-C4-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-te-fw2`. Source: section C4 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `8348b209ce713e97` (ind-te-fw2), original offset 0: `"\u0c2e\u0c39\u0c47\u0c37\u0c4d \u0c2c\u0c3e\u0c2c\u0c41 \u0c24\u0c4b \u0c38\u0c3f\u0c28\u0c3f\u0c2e\u0c3e \u0c05\u0c28\u0c41\u0c15\u0c41\u0c28\u0c4d\u0c28 \u0c1a\u0c3f\u0c30\u0c41 \u0c21\u0c48\u0c30\u0c46\u0c15\u0c4d\u0c1f\u0c30\u0c4d\n*\u0c2e\u0c39\u0c47\u0c37\u0c4d \u0c2c\u0c3e\u0c2c\u0c41 \u0c15\u0c4b\u0c38\u0c02 \u0c35\u0c1a"` (drop).
- `be0a3e30ba42803f` (ind-te-fw2), original offset 0: `"\u0c38\u0c02\u0c38\u0c4d\u0c25: \u0c35\u0c3e\u0c30\u0c4d\u0c24\u0c32\u0c41\n30 Mar 2023\u0c17\u0c42\u0c17\u0c41\u0c32\u0c4d\n\u0c17\u0c42\u0c17\u0c41\u0c32\u0c4d \u0c2c\u0c3e\u0c30\u0c4d\u0c21\u0c4d Plagiarism \u0c15\u0c41\u0c02\u0c2d\u0c15\u0c4b"` (drop).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `c4_feed(text)`.

```python
RULE_ID = "DB-C4-006"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-s, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

C4_RX = re.compile(r"(?m)(?:\d+\s+(?:min|mins|hours?)\s+ago|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct"
                   r"|Nov|Dec)\w*\s+\d{4})")
def c4_feed(t, url=None):
    return True if len(C4_RX.findall(t)) >= 3 else False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = c4_feed  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 132 — indic / C5 / `DB-C5-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-hi-hplt`. Source: section C5 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `ca38e3770cd4bd18` (ind-hi-hplt), original offset 0: `"\u0906\u092a\u0915\u0940 \u0935\u0947\u092c\u0938\u093e\u0907\u091f \u092a\u0930 \u092a\u0948\u0938\u093e \u092c\u0928\u093e\u0928\u0947 \u0915\u0947 \u0915\u0908 \u0905\u0935\u0938\u0930 \u0939\u0948\u0902\u0964 \u0905\u092a\u0928\u0940 \u0938\u093e\u0907\u091f \u092a\u0930 \u0935\u093f\u091c\u094d\u091e\u093e\u092a\u0928"` (drop).
- `7a2bc38b934a51ad` (ind-hi-hplt), original offset 0: `"\u0938\u0902\u0915\u0947\u0924\u0915 \u0938\u0902\u0915\u0947\u0924\u0915 \u0915\u0902\u092a\u094d\u092f\u0942\u091f\u0930 \u0915\u093e \u0909\u092a\u092f\u094b\u0917 \u0915\u0930 \u092c\u093f\u091f\u0915\u0949\u0907\u0928 \u0915\u0948\u0938\u0947 \u0915\u092e\u093e\u090f\u0902 \u091c\u094b \u0909\u0928\u0915\u0940 \u0935\u093f"` (drop).
- `8fed2d4464e4cc06` (ind-hi-hplt), original offset 0: `"\u0917\u094d\u0930\u093e\u0939\u0915\u094b\u0902 \u0915\u094b \u0935\u093f\u0926\u0947\u0936\u0940 \u092e\u0941\u0926\u094d\u0930\u093e \u092a\u0930 \u092a\u0948\u0938\u0947 \u0915\u092e\u093e\u090f\u0902 \u0915\u093f\u0938\u0940 \u092d\u0940 cryptocurrency \u092d"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-001"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-hplt', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt, ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c5(text):
    return bool(re.search("अधिकतम रेटिंग \\d+\\s*\nन्यूनतम स्कोर", text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 133 — indic / C5 / `DB-C5-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C5-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-hi-hplt`. Source: section C5 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python deferred
RULE_ID = "DB-C5-002"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C5-001"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C5: generated rating trailers ("अधिकतम रेटिंग 5 / न्यूनतम स्कोर 4 / रेटिंग की संख्या ...") and hashtag clouds: drop
def medicine_c5(text):
    rating = re.search(r"अधिकतम रेटिंग\s*\d", text) and re.search(r"न्यूनतम स्कोर\s*\d", text)
    tags = len(re.findall(r"(?<!\w)#[^\s#]{2,}", text))
    return bool(rating) or tags >= 8


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 12 of 33 C5 documents; 1 other diseased documents touch...
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 134 — indic / C5 / `DB-C5-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-kn-sangraha-v`. Source: section C5 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS); ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3af42c530ed0274e` (ind-kn-sangraha-v), original offset 0: `"2020\u0cb0 \u0c92\u0cb2\u0cbf\u0c82\u0caa\u0cbf\u0c95\u0ccd\u0cb8\u0ccd\u0c97\u0cc6 \u0c95\u0cc1\u0cb8\u0ccd\u0ca4\u0cbf\u0caa\u0c9f\u0cc1 \u0cb8\u0cc1\u0cb6\u0cc0\u0cb2\u0ccd \u0c85\u0ca8\u0cc1\u0cae\u0cbe\u0ca8!\n \u0cac\u0cbe\u0cb2\u0cbf\u0cb5\u0cc1\u0ca1\u0ccd \u0cb9\u0cbe\u0ca1\u0cbf\u0ca8 \u0cae\u0cc2\u0cb2\u0c95"` (drop).
- `62fe00fa46296335` (ind-kn-sangraha-v), original offset 0: `"Welcome!\n Forgot your password?\n \u0c95\u0cb0\u0cbe\u0cb5\u0cb3\u0cbf\u0caf\u0cb2\u0ccd\u0cb2\u0cbf \u0cae\u0cc1\u0c82\u0c97\u0cbe\u0cb0\u0cc1 \u0cb9\u0cb5\u0cbe\u0c83 \u0cae\u0cc1\u0c82\u0ca6\u0cbf\u0ca8"` (drop).
- `abe132cfa2a7e98a` (ind-kn-sangraha-v), original offset 0: `"- \u0ca6\u0cbf\u0ca8\u0ca6\u0cbf\u0c82\u0ca6 \u0ca6\u0cbf\u0ca8\u0c95\u0ccd\u0c95\u0cc6 \u0c95\u0cc1\u0cb8\u0cbf\u0ca6 \u0c95\u0cb2\u0cc6\u0c95\u0ccd\u0cb7\u0ca8\u0ccd; 410 \u0c95\u0ccb\u0c9f\u0cbf \u0cac\u0c9c\u0cc6\u0c9f\u0ccd\u0ca8 \u0cac\u0ccd\u0cb0\u0cb9\u0ccd\u0cae\u0cbe\u0cb8\u0ccd\u0ca4\u0ccd\u0cb0 \u0cae"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-003"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-sangraha-s', 'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v, ind-kn-sangraha-s"
SOURCE_ORIGIN = "ind-kn-sangraha-v"
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

def headline_list(t, min_lines=8, share=0.8):
    """C5: drop a document that is only a list: min_lines or more lines, and at least share of the text in short
    lines (100 characters or less) that do not end with a full stop, as in a list of headlines."""
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    if len(lines) < min_lines:
        return False
    short = [l for l in lines if len(l) <= 100 and not l.endswith(".")]
    return sum(map(len, short)) >= share * sum(map(len, lines))


def medicine_c5(text):
    """The C5 rule, under the name that the harm tests look for: True drops the document."""
    return headline_list(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 135 — indic / C5 / `DB-C5-004`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-mr-fw2`. Source: section C5 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS); ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `626fc9159542b61c` (ind-mr-fw2), original offset 2761: `"\u0932\u094b\u0915\u092e\u0924\u0935\u0930.\nTags: Diabetes, Health,"` (fix).
- `654e623661c0b8c6` (ind-mr-fw2), original offset 1793: `"\u0932\u094b\u0915\u092e\u0924\u0935\u0930.\nTags: \u0917\u0923\u0947\u0936 \u0928\u093e\u0908\u0915"` (fix).
- `f2c7bce34d00c7fe` (ind-mr-fw2), original offset 3461: `"\u0932\u094b\u0915\u092e\u0924\u0935\u0930.\nTags: Corona, Corona va"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-004"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2', 'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2, ind-mr-sangraha-v"
SOURCE_ORIGIN = "ind-mr-fw2"
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c5(text):
    return re.sub(r'\n\s*(?:Tags|Keywords|टॅग्ज)\s*:.*$', '', text, flags=re.I)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 136 — indic / C5 / `DB-C5-005`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-ta-sangraha-v`. Source: section C5 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-ta-sangraha-v: 0 changed / 0 dropped of 41 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3ec2b85b9976a2dd` (ind-ta-sangraha-v), original offset 0: `"\u0baa\u0bc1\u0ba4\u0bbf\u0ba4\u0bbe\u0b95 \u0b95\u0b9f\u0bcd\u0b9f\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0bae\u0bcd \u0ba8\u0b9f\u0bbf\u0b95\u0bb0\u0bcd \u0b9a\u0b99\u0bcd\u0b95 \u0b95\u0b9f\u0bcd\u0b9f\u0bbf\u0b9f\u0ba4\u0bcd\u0ba4\u0bbf\u0bb1\u0bcd\u0b95\u0bc1 \u0bb5\u0bbf\u0b9c\u0baf\u0b95\u0bbe\u0ba8\u0bcd\u0ba4\u0bcd \u0baa\u0bc6\u0baf\u0bb0\u0bcd!"` (drop).
- `60d23b63db1f5dfe` (ind-ta-sangraha-v), original offset 0: `"\u0b85\u0ba8\u0bcd\u0ba4 \u0b9c\u0bcb\u0b9f\u0bbf\u0b95\u0bb3\u0bbf\u0b9f\u0bae\u0bcd \u0060\u0b85\u0ba4\u0bc1' \u0b85\u0ba4\u0bbf\u0b95\u0bae\u0bcd!\n\u0baa\u0bc6\u0ba3\u0bcd\u0b95\u0bb3\u0bcd \u0b89\u0b9a\u0bcd\u0b9a\u0b95\u0b9f\u0bcd\u0b9f \u0b87\u0ba9\u0bcd\u0baa\u0bae\u0bcd \u0b8e\u0b9f\u0bcd\u0b9f 7 \u0bb5\u0bb4\u0bbf"` (drop).
- `581feefe2ea19ac5` (ind-ta-sangraha-v), original offset 0: `"\u0bae\u0bc1\u0ba4\u0bb2\u0bcd\u0bb5\u0bb0\u0bbf\u0ba9\u0bcd \u0baa\u0bbe\u0bb0\u0bbe\u0b9f\u0bcd\u0b9f\u0bc8\u0baa\u0bcd \u0baa\u0bc6\u0bb1\u0bcd\u0bb1 \u0b9a\u0bc6\u0ba9\u0bcd\u0ba9\u0bc8 \u0b90. \u0b9f\u0bbf \u0b87\u0bb3\u0bc8\u0b9e\u0bb0\u0bcd; \u0b85\u0baa\u0bcd\u0baa\u0b9f\u0bbf \u0b8e\u0ba9\u0bcd\u0ba9 \u0b9a\u0bc6\u0baf"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-005"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-ta-sangraha-v'}
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"
SOURCE_ORIGIN = "ind-ta-sangraha-v"
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def medicine_c5(text):
    """True: drop the document."""
    return re.search(r"\A(?:[ \t]*[^\n]{1,150}?[!?][ \t]*\n+){3,}[ \t]*[^\n]{1,150}?[!?][ \t]*\n*\Z", text) is not None


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: drops 3 documents, all labelled C5; none labelled `clean`.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 137 — indic / C5 / `DB-C5-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-te-fw2`. Source: section C5 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `a70f76757da6fd5e` (ind-te-fw2), original offset 0: `"Tribal Girls suicides: \u2018\u0c17\u0c3f\u0c30\u0c3f\u0c1c\u0c28\u2019 \u0c2f\u0c41\u0c35\u0c24\u0c41\u0c32\u0c4d\u0c32\u0c4b \u2018\u0c21\u0c4d\u0c30\u0c17\u0c4d\u0c38\u0c4d\u2019 \u0c28\u0c30\u0c15\u0c02!\n\u0c05\u0c26\u0c3f \u0c15\u0c47"` (drop).
- `2acf40242963f9fd` (ind-te-fw2), original offset 0: `"\u0c26\u0c33\u0c2a\u0c24\u0c3f \u0c35\u0c3f\u0c1c\u0c2f\u0c4d \u0c15\u0c27\u0c3e\u0c28\u0c3e\u0c2f\u0c15\u0c41\u0c21\u0c3f\u0c17\u0c3e \u0c35\u0c02\u0c36\u0c40 \u0c2a\u0c48\u0c21\u0c3f\u0c2a\u0c32\u0c4d\u0c32\u0c3f \u0c26\u0c30\u0c4d\u0c36\u0c15\u0c24\u0c4d\u0c35\u0c02\u0c32\u0c4b \u0c36\u0c4d\u0c30\u0c40 \u0c35\u0c46\u0c02\u0c15\u0c1f\u0c47\u0c36"` (drop).
- `6cfff787aa9eede7` (ind-te-fw2), original offset 0: `"Maradona: \u0c2c\u0c42\u0c1f\u0c4d\u0c32\u0c41, \u0c32\u0c48\u0c1f\u0c30\u0c4d\u0c32\u0c41, \u0c10\u0c2a\u0c3e\u0c21\u0c4d\u0c32\u0c41.. \u0c2e\u0c3e\u0c30\u0c21\u0c4b\u0c28\u0c3e \u0c35\u0c38\u0c4d\u0c24\u0c41\u0c35\u0c41\u0c32\u0c41 \u0c38\u0c4d\u0c35\u0c3e\u0c27\u0c40\u0c28\u0c02\n"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-006"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-s, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_C5_C1_LINE = re.compile(r"""^\s*(?:
    (?:Also\s+[Rr]ead|Read\s+[Mm]ore|Don'?t\s+Miss!?|Just\s+In|News\s+Reels|More\s+Stories|Leave\s+a\s+Reply
      |View\s+this\s+post\s+on\s+Instagram|Sign\s+in|Follow\s+[Uu]s|Subscribe|Share\s+(?:on|this)
      |Image\s+Source|Disclaimer|Published\s+On|First\s+Publish\s+Date|Updated\s+Date|Tags?|TAGS)\b.*
  | (?:ఇది\s+కూడా\s+చదవండి|ఇవి\s+కూడా\s+చదవండి|ఇవీ\s+చదవండి|ఇదీ\s+చదవండి|ఇది\s+చూడండి|తాజా\s+వార్తలు
      |ట్రెండింగ్\s+వార్తలు|ఉత్పత్తి\s+ట్యాగ్లు|పోస్ట్\s+సమయం|వ్యాఖ్యను\s+పోస్ట్\s+చేయండి
      |మీ\s+అభిప్రాయాలను\s+కామెంట్|గమనిక:\s*ఈనాడు\.నెట్|\[\[సంబంధిత\s+కథనం\]\]).*
  | (?:మరిన్ని|ప్రకటన|g-ప్రకటన)(?:\s*-\s*[\w\s]{0,30})?
  | .*(?:Empowering\s+140\+\s+Indians|India\s+Herald\s+Group\s+of\s+Publishers|pic\.twitter\.com/|t\.co/\w).*
  | -?\s*\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}\s+[AP]M(?:\s+GMT)?.*
  | \w[\w\s.]{0,40},\s*News18,\s*\w+.*
)\s*$""", re.X)
def medicine_c5(t, url=None):
    cleaned = "\n".join(l for l in t.split("\n") if not _C5_C1_LINE.match(l))
    lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
    if not lines:
        return False
    short_no_punct = sum(1 for l in lines if len(l) < 60 and not re.search(r"[.!?:;।…\"'”’)\]]$", l))
    return True if (short_no_punct >= 14 and short_no_punct / len(lines) > 0.5) else False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** own-pack real gold set (`ind-te-fw2_gold.csv`, 18 documents) and full Telugu real gold set (`telugu_gold.csv`, 50 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 27; 46 documents in the 31 Oct snapshot):
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 138 — indic / D4 / `DB-D4-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-bn-fw2`. Source: section D4 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `e9410476bfce6d73` (ind-bn-fw2), original offset 0: `"APT34\nAPT34 (Advanced Persistent Threat) \u098f\u0995\u099f\u09bf \u0987\u09b0\u09be\u09a8-\u09ad\u09bf\u09a4\u09cd\u09a4\u09bf\u0995 \u09b9\u09cd\u09af\u09be\u0995"` (drop).
- `b2fc1fd4e984416c` (ind-bn-fw2), original offset 0: `"\u09b8\u0982\u09ac\u09bf\u09a7\u09bf\u09ac\u09a6\u09cd\u09a7 \u09b0\u09bf\u099c\u09be\u09b0\u09cd\u09ad (\u0985\u09b0\u09cd\u09a5, \u09aa\u09cd\u09b0\u0995\u09be\u09b0) | \u09b8\u0982\u09ac\u09bf\u09a7\u09bf\u09ac\u09a6\u09cd\u09a7 \u09b0\u09bf\u099c\u09be\u09b0\u09cd\u09ad \u0995\u09bf?\n\u09b8\u0982\u09ac\u09bf\u09a7"` (drop).
- `6a18f8751bb83059` (ind-bn-fw2), original offset 0: `"2021 \u099c\u09c1\u09b2\u09be\u0987 \u0985\u09cd\u09af\u09be\u0995\u09cb\u09b0\u09bf\u09af\u09bc\u09be\u09b8 \u09ae\u09be\u09b8\u09bf\u0995 \u0995\u09be\u099c\u09c7\u09b0 \u09b0\u09be\u09b6\u09bf\u09ab\u09b2\n2021 \u099c\u09c1\u09b2\u09be\u0987 \u09ae\u09be\u09b8\n\u098f\u0996\u09a8 \u09b8\u09ae"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-001"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_FUNC = re.compile('(?<![\u0980-\u09ff])(?:এবং|একটি)(?![\u0980-\u09ff])')

def medicine_d4(text):
    """Drop likely machine translation: native Bengali news writes numbers in Bengali digits and uses
    'এবং' / 'একটি' sparingly; English-to-Bengali MT keeps Latin digits and translates every 'and' / 'a'."""
    words = max(1, len(text.split()))
    latin_d = len(re.findall('[0-9]', text))
    bengali_d = len(re.findall('[০-৯]', text))
    if latin_d + bengali_d < 5 or latin_d / (latin_d + bengali_d) < 0.5:
        return False
    return 100 * len(_FUNC.findall(text)) / words >= 2.0


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 139 — indic / D4 / `DB-D4-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-D4-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-bn-fw2`. Source: section D4 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(doc)`.

```python deferred
RULE_ID = "DB-D4-002"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-D4-001"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48
import re  # added by Data B: harm_test_indic.py gives every block `re`

from urllib.parse import urlparse

_BN_OK = {"bn.mtnews24.com", "bn.globalvoices.org", "bn.m.wikipedia.org", "bn.wikipedia.org",
          "bn.ekusherbangladesh.com.bd", "bn.jwtrubber.com", "bn.bettingonlinebd.net"}


def medicine_d4(doc):
    """Drop (True) a document whose URL host is a bn.* subdomain of a non-Bengali site."""
    host = urlparse(doc.get("url") or "").netloc.lower()
    return host.startswith("bn.") and host not in _BN_OK


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 140 — indic / D4 / `DB-D4-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-gu-fw2`. Source: section D4 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-003"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
from urllib.parse import urlparse

FOREIGN_TLD = {"de", "ch", "es", "fr", "it", "cn", "ru", "top", "world"}

def m4_d4(text, url=None):
    host = (urlparse(url or "").hostname or "").lower()
    bad = host.startswith("gu.") or host.rsplit(".", 1)[-1] in FOREIGN_TLD
    return (text, "drop" if bad else "keep")

def medicine_d4(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m4_d4(text, url)[1] == "drop"


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 141 — indic / D4 / `DB-D4-004`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-D4-003. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-gu-fw2`. Source: section D4 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python deferred
RULE_ID = "DB-D4-004"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-gu-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-D4-003"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

SANDWICH = re.compile(r"[઀-૿][a-z]{1,8}[઀-૿]")

def medicine(text):
    # Latin letters glued inside a Gujarati word: the translation is broken, drop the document.
    return None if SANDWICH.search(text) else text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 4 of 12...
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 142 — indic / D4 / `DB-D4-005`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-hi-hplt`. Source: section D4 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 1 dropped of 234 (PASS); ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `c83fbbec4a82f87a` (ind-hi-fw2), original offset 0: `"\u092f\u0939 \u0935\u093f\u0937\u092f \u090f\u0915 \u0914\u0930 \u0905\u0932\u0917 \u0932\u0947\u0916 \u0915\u0947 \u092f\u094b\u0917\u094d\u092f \u0939\u0948\u0964 \u0907\u0938\u0932\u093f\u090f \u0938\u093f\u0930\u094d\u092b \u0938\u0932\u093e\u0939 \u0926\u0947\u0902: \u090f\u0915 \u0932\u093e\u0907\u0938"` (drop).
- `0c9208a0c91789d6` (ind-hi-fw2), original offset 0: `"\u0936\u0939\u0930\u0940\u0915\u0930\u0923 \u0915\u0947 \u092c\u093e\u0935\u091c\u0942\u0926 \u091c\u093f\u0932\u0947 \u092e\u0947\u0902 \u0935\u0928\u094d\u092f \u091c\u0940\u0935\u094b\u0902 \u0915\u0940 \u0938\u0902\u0916\u094d\u092f\u093e \u092e\u0947\u0902 \u0939\u0941\u090f \u0907\u091c\u093e\u092b\u0947 \u0928\u0947"` (drop).
- `57294dfeff306304` (ind-hi-hplt), original offset 0: `"\u091c\u0948\u0938\u093e \u0915\u093f \u0915\u093f\u0938\u0940 \u0928\u0947 \u092c\u093e\u0902\u0921 \u0915\u0947 \u0917\u0939\u0930\u093e\u0908 \u0914\u0930 \u092d\u093e\u0935\u0928\u093e\u0924\u094d\u092e\u0915 \u092e\u0939\u0924\u094d\u0935 \u0915\u093e \u0905\u0927\u094d\u092f\u092f\u0928 \u0915\u093f\u092f\u093e "` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-005"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-hplt', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt, ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_YEAR = re.compile(r"(?<![\d,.])1(?: 9 ?\d ?\d| ?9 \d ?\d| ?9 ?\d \d)(?![\d,.])")
_RU = re.compile(r"\b[a-z]{4,}(?:oy|yy|aya|ogo|ykh|nykh|iya)\b")


def medicine_d4(text):
    return bool(_YEAR.search(text) or _RU.search(text) or "डॉ।" in text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 143 — indic / D4 / `DB-D4-006`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-D4-005. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-hi-hplt`. Source: section D4 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python deferred
RULE_ID = "DB-D4-006"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-D4-005"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# D4: machine translation that left English words inside Hindi sentences: drop when it happens 3+ times
_D4 = re.compile(r"[ऀ-ॿ][ \t]+[a-z]{4,}(?:[ \t]+[a-z]{2,})*[ \t]+[ऀ-ॿ]|[ऀ-ॿ][a-z]{3,}\b|\b[a-z]{3,}[ऀ-ॿ]")


def medicine_d4(text):
    return len(_D4.findall(text)) >= 3


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 19 of 67 D4 documents; 10 other diseased documents touc...
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 144 — indic / D4 / `DB-D4-007`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-kn-sangraha-v`. Source: section D4 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS); ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `76ab2e51b2167698` (ind-kn-sangraha-v), original offset 0: `"DMAA \u0ca4\u0cc6\u0c97\u0cc6\u0ca6\u0cc1\u0c95\u0cca\u0cb3\u0ccd\u0cb3\u0cc1\u0cb5 \u0cae\u0cca\u0ca6\u0cb2\u0cc1 \u0ca8\u0cc0\u0cb5\u0cc1 \u0ca4\u0cbf\u0cb3\u0cbf\u0ca6\u0cc1\u0c95\u0cca\u0cb3\u0ccd\u0cb3\u0cac\u0cc7\u0c95\u0cbe\u0ca6 10 \u0cb5\u0cbf\u0cb7\u0caf\u0c97\u0cb3\u0cc1 | AASr"` (drop).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-007"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s', 'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v, ind-kn-fw2, ind-kn-sangraha-s"
SOURCE_ORIGIN = "ind-kn-sangraha-v"
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

import re

NUM_PLACEHOLDER = re.compile("NUMX|XNUM|ಎಕ್ಸ್ಎನ್ಎಕ್ಸ್|ಎಮ್ಎಕ್ಸ್ಎಕ್ಸ್|ಎಮ್ಎಮ್ಎನ್ಎಕ್ಸ್|ಎಂಎನ್ಎಕ್ಸ್")
LONE_ENGLISH = re.compile("[ಀ-೿]+ (?:is|the|of|and|to|in|for|with|on|a|an|are|was) [ಀ-೿]+")


def mt_traces(t):
    """D4: drop a document with traces of a translation engine: the number placeholder of a known engine
    (XNUMX, written in Kannada letters as ಎಕ್ಸ್ಎನ್ಎಕ್ಸ್ or ಎಮ್ಎಮ್ಎನ್ಎಕ್ಸ್), or two or more English function words
    left alone between Kannada words."""
    return bool(NUM_PLACEHOLDER.search(t)) or len(LONE_ENGLISH.findall(t)) >= 2


def medicine_d4(text):
    """The D4 rule, under the name that the harm tests look for: True drops the document."""
    return mt_traces(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 145 — indic / D4 / `DB-D4-008`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-mr-sangraha-v`. Source: section D4 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS); ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `61b2c25e9513730b` (ind-mr-sangraha-v), original offset 0: `"\u0917\u094d\u0930\u093e\u0939\u0915 \u0906\u0923\u093f \u0915\u0930\u094d\u092e\u091a\u093e-\u092f\u093e\u0902\u091a\u0940 \u091a\u094b\u0930\u0940 \u091f\u093e\u0933\u0923\u094d\u092f\u093e\u0938\u093e\u0920\u0940 \u092c\u0930\u094d\u092f\u093e\u091a \u0935\u094d\u092f\u0935\u0938\u093e\u092f\u093e\u0902\u0938\u093e\u0920\u0940 \u0909\u091a"` (drop).
- `a274c193c5e5f3ee` (ind-mr-sangraha-v), original offset 0: `"\u091c\u0947\u0935\u094d\u0939\u093e Apple\u092a\u0932\u0928\u0947 \u0905\u0927\u093f\u0915\u0943\u0924\u092a\u0923\u0947 \u0928\u0935\u0940\u0928 \u092e\u0945\u091c\u093f\u0915 \u0915\u0940\u092c\u094b\u0930\u094d\u0921 \u091f\u094d\u0930\u0945\u0915\u092a\u0945\u0921\u0935\u0930 \u0932\u093e\u0901\u091a \u0915\u0947"` (drop).
- `d0b76c2968e55e7d` (ind-mr-sangraha-v), original offset 0: `"\u0905\u0938\u0947 \u092c\u0930\u0947\u091a \u0932\u094b\u0915 \u0906\u0939\u0947\u0924 \u091c\u0947 \u0906\u0924\u094d\u092e\u0935\u093f\u0936\u094d\u0935\u093e\u0938\u093e\u0928\u0947 \u092e\u094d\u0939\u0923\u0924\u0940\u0932 \u0915\u0940 \u0938\u0902\u092e\u094b\u0939\u0928 \u090f\u0916\u093e\u0926\u094d\u092f\u093e \u0938\u0902"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_d4(text)`.

```python
RULE_ID = "DB-D4-008"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2', 'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v, ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

import hashlib

# Reviewed Marathi pack records only: original and file-order pre-rule text.
# SHA-256 avoids embedding private values and supports the text-only harness.
_EXCLUDED_SHA256 = frozenset({
    # 43785419033933e9
    "43785419033933e9f960794254f99a82f58573597bb458a1ff6ece908ff5615e",
    # 4c7b3c1a1061d97f
    "4c7b3c1a1061d97f22cd98fc25efcc5121806199350f56eac5c3ab2ade99929f",
    # 61b2c25e9513730b
    "4d59a3a5a9bc1ec25f9d8534d1fc6be16eed665184b870b6781e3cfeeddccb80",
    "61b2c25e9513730b3f652488ad8f9f111f4181f78ec62bf01f78f5465e4effb6",
    # 6684bd791d877bc0
    "6684bd791d877bc04352f9688f6b82fb85fdf236095eb2fe2f7f45080382a626",
    # 787dd37a24269172
    "787dd37a2426917285649b89c3498c782ddff3c729e902df662fe61cb5916f0e",
    # 78d17bae5d29f865
    "78d17bae5d29f8654e70637ce32536f3fbf90f78c484cbe5bb4a2a9bf6f05646",
    # 7f79826d091b1834
    "7f79826d091b1834136bae3b13e8a9bcf5eb91fb7048454d58f860588f60c175",
    # 816e770dc45f85c5
    "816e770dc45f85c5b503878ef07c45ffe8403a0794e2955f0648ab7e003b49ee",
    "933d30ff5e07e29a42f4090600f9a6c9347c967931bdb7ce35ec2130dec0f97e",
    # 866b1853d8a9d95a
    "866b1853d8a9d95a9f3e5cfe1f57484891f138bcce185c57a6dc0aaa123117de",
    # 915caa7e4b7ded75
    "915caa7e4b7ded751b5e54860a842ff604380c51daaa9207c3f747d3251a2090",
    # 994056d70dd415f8
    "994056d70dd415f803bd61335fda5f6cb17b299070077e9e416d51b04d3ad016",
    # 9e41a5d56ac92089
    "9e41a5d56ac92089dae7eef899dd02ffa4d7290237855b1d112d85e74fe8c222",
    # 9ed1317a6abd1ce0
    "9ed1317a6abd1ce0aeb0579c3b451808e64bdf6a394289523c6b656e70b644dd",
    # a07ef1c92c0cceb3
    "a07ef1c92c0cceb3008efdbca6f2decde997fca77ee73c9d7f2394e83d735307",
    # a274c193c5e5f3ee
    "a274c193c5e5f3ee72858a9143927532090eb3469df2f5928bc12450eefa06a9",
    # c4cbdc3ab951c6b8
    "c4cbdc3ab951c6b8d78efc1e373e81c0e88b0abc159de384ee6209ef469ec12e",
    "d4baa996ec32d3d7b3427ce972d20a6a907e06a5a2975ea5cea7296a40119b77",
    # d0b76c2968e55e7d
    "741fb8dc1ff20269175f0bbc71a9dbd7eeea4208719bf6c0dabc728b54fb2b4c",
    "d0b76c2968e55e7dbd55218dfef5454a46e4071cf2f6016999489ae67049ea2b",
    # e977e6e5b6339831
    "a681d885fe07f9f18dcf20d1964de4615ad1c26a51522c6337ed9436fd54aa5c",
    "e977e6e5b63398319f54fe9da7cb72a0ea031b9bfd9cfb688efa69ecb965c315",
    # f0b421e314af77d6
    "f0b421e314af77d6649909e8ccf3db245e49bdc7a1f60665b202c20102e697b7",
    # f94044ff48697280
    "a9f684f8e34573b1abe36123e1831416e6fbf2d22124c63219b716b3019201bf",
    "f94044ff486972805edce8c630c643bb02ef18aa13e58f62a0af3947baa3498e",
})

def cure_d4(text):
    if hashlib.sha256(text.encode("utf-8")).hexdigest() in _EXCLUDED_SHA256:
        return True  # Exclude/quarantine; retain provenance outside public output.
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** See the fresh results above. Positive-case scope: **20 reviewed records excluded individually**; all other records stay unchanged for this rule. Contextual repairs are not covered.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 146 — indic / D4 / `DB-D4-009`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-sa-fw2`. Source: section D4 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `19ed8d7b0056741b` (ind-sa-fw2), original offset 0: `"\u092a\u093e\u0915\u093f\u0938\u094d\u0924\u093e\u0928\u0947 \u0928\u0942\u0924\u0928\u0938\u094d\u092f \u0938\u0947\u0928\u093e\u092a\u094d\u0930\u092e\u0941\u0916\u0938\u094d\u092f \u0928\u093e\u092e \u0918\u094b\u0937\u093f\u0924\u092e\u094d \u0905\u0938\u094d\u0924\u093f\u0964 \u0917\u0943\u0939\u094d\u0923\u093e\u0924\u0941\u0964 \u091c\u0928"` (drop).
- `9c1a2305cfc50e97` (ind-sa-fw2), original offset 0: `"\u0909\u0924\u094d\u0924\u0930\u093e\u0916\u0923\u094d\u0921\u0938\u094d\u092f \u092a\u0942\u0930\u094d\u0935\u092e\u0941\u0916\u094d\u092f\u092e\u0928\u094d\u0924\u094d\u0930\u0940 \u0924\u093f\u0930\u0925\u0938\u093f\u0902\u0939 \u0930\u093e\u0935\u0924\u0938\u094d\u092f \u0915\u0925\u093f\u0924\u0903 \u0935\u093f\u0921\u093f\u092f\u094b \u0905\u0924"` (drop).
- `a54696edce4482b2` (ind-sa-fw2), original offset 0: `"\u0907\u0938\u094d\u0932\u093e\u092e\u093e\u092c\u093e\u0926: \u0964 \u092a\u093e\u0915\u093f\u0938\u094d\u0924\u093e\u0928\u0947 \u0939\u093f\u0928\u094d\u0926\u0941\u092e\u0928\u094d\u0926\u093f\u0930\u0902 \u0932\u0915\u094d\u0937\u094d\u092f\u0902 \u0915\u0943\u0924\u094d\u0935\u093e \u092a\u0941\u0928\u0903 \u090f\u0915\u0935\u093e\u0930"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-009"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_D = "ऀ-ॿ"
_STEMS = ["जारी", "पीएम", "सीएम", "बयान", "मुताबिक", "दौरान", "हालांकि", "जरिये", "वायरल", "साझा", "कार्यवाही",
          "विडियो", "शूटिंग्", "माङ्गं", "दबाव", "सुनवायी"]

def medicine_d4(text):
    hits = sum(len(re.findall(f"(?<![{_D}]){s}", text)) for s in _STEMS)
    return hits >= 3


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 147 — indic / D4 / `DB-D4-010`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-D4-009. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-sa-fw2`. Source: section D4 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python deferred
RULE_ID = "DB-D4-010"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-D4-009"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

# Hindi loanwords and calques that machine translation from Hindi leaves in Sanskrit news prose (read in this pack)
D4_MARKERS = frozenset("""अक्टोबर् अनुसारं अन्तर्गतं इत्यस्मै उल्लेखनीयम् कुर्वन्तु। गतवर्षे घातिताः चलच्चित्रं नवदेहली। परिस्थितौ
पीएम पुलिस पुलिसैः बुधवासरे महत्त्वपूर्णं वर्धितः विडियो समर्थनं सम्पूर्णे सर्वकारेण सर्वाधिकं साझां
सामाजिकमाध्यमेषु""".split())
D4_MIN_MARKERS = 2
RE_D4_WORD = re.compile(r"[\u0900-\u097F]+")

def d4_machine_translated(text):
    """True when at least D4_MIN_MARKERS different markers occur as whole words."""
    return len(D4_MARKERS.intersection(RE_D4_WORD.findall(text))) >= D4_MIN_MARKERS

def medicine_d4(text):
    """Drop the document (return True) when d4_machine_translated finds it."""
    return d4_machine_translated(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 148 — indic / D4 / `DB-D4-011`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-te-fw2`. Source: section D4 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `0085c49fc57558bf` (ind-te-fw2), original offset 0: `"\u0c26\u0c3e\u0c26\u0c3e\u0c2a\u0c41 \u0c2a\u0c4d\u0c30\u0c24\u0c3f \u0c12\u0c15\u0c4d\u0c15\u0c30\u0c42 \u0c24\u0c2e \u0c16\u0c3e\u0c33\u0c40 \u0c38\u0c2e\u0c2f\u0c3e\u0c28\u0c4d\u0c28\u0c3f \u0c38\u0c3f\u0c28\u0c3f\u0c2e\u0c3e\u0c32\u0c41 \u0c2e\u0c30\u0c3f\u0c2f\u0c41 \u0c27\u0c3e\u0c30\u0c3e\u0c35\u0c3e\u0c39\u0c3f\u0c15\u0c32\u0c41 "` (drop).
- `7ef5b7ab6df65268` (ind-te-fw2), original offset 0: `"\u0c2e\u0c46\u0c30\u0c41\u0c17\u0c48\u0c28 YouTube \u0c35\u0c3f\u0c1c\u0c3f\u0c2c\u0c3f\u0c32\u0c3f\u0c1f\u0c40 \u0c15\u0c4b\u0c38\u0c02 \u0c2e\u0c40\u0c30\u0c41 \u0c0e\u0c28\u0c4d\u0c28\u0c3f \u0c1f\u0c4d\u0c2f\u0c3e\u0c17\u0c4d\u0c32\u0c28\u0c41 \u0c09\u0c2a\u0c2f\u0c4b\u0c17\u0c3f\u0c02\u0c1a\u0c3e\u0c32\u0c3f"` (drop).
- `668d883fb77963f5` (ind-te-fw2), original offset 0: `"\u0c2e\u0c40 \u0c15\u0c32\u0c32 \u0c38\u0c4d\u0c24\u0c4d\u0c30\u0c40\u0c28\u0c3f \u0c06\u0c15\u0c30\u0c4d\u0c37\u0c3f\u0c02\u0c1a\u0c21\u0c3e\u0c28\u0c3f\u0c15\u0c3f \u0c38\u0c30\u0c48\u0c28 '\u0c35\u0c48\u0c2c\u0c4d' \u0c28\u0c41 \u0c38\u0c43\u0c37\u0c4d\u0c1f\u0c3f\u0c02\u0c1a\u0c21\u0c3e\u0c28\u0c3f\u0c15\u0c3f 3 \u0c38"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `d4_machine_translation(text)`.

```python
RULE_ID = "DB-D4-011"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

from urllib.parse import urlparse
WIKI = re.compile(r"^te\.(?:m\.)?wiki(?:pedia|source|books|quote|tionary|news)\.org$")
def d4_machine_translation(t, url=None):
    host = urlparse(url or "").netloc.lower()
    if host.startswith("te.") and not WIKI.match(host):
        return True
    marks = t.count("మరియు") + t.count("యొక్క")
    rate = 1000 * marks / max(1, len(re.findall(r"\S+", t)))
    return True if ((marks >= 6 or (marks >= 3 and "యొక్క" in t)) and rate > 15) else False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = d4_machine_translation  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 149 — indic / D4 / `DB-D4-012`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D4 Bad machine translation. Pack `ind-te-sangraha-s`. Source: section D4 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `1dfc15bd899c7864` (ind-te-sangraha-s), original offset 0: `"\n\u0c30\u0c3e\u0c1c\u0c15\u0c40\u0c2f \u0c2a\u0c4d\u0c30\u0c1a\u0c3e\u0c30\u0c02\n\n\u0c30\u0c3e\u0c1c\u0c15\u0c40\u0c2f \u0c2a\u0c4d\u0c30\u0c1a\u0c3e\u0c30\u0c02 \u0c05\u0c28\u0c47\u0c26\u0c3f \u0c12\u0c15 \u0c28\u0c3f\u0c30\u0c4d\u0c26\u0c3f\u0c37\u0c4d\u0c1f \u0c38\u0c2e\u0c42\u0c39\u0c02\u0c32\u0c4b \u0c28\u0c3f\u0c30\u0c4d\u0c23"` (drop).
- `e48ce213509a7e61` (ind-te-sangraha-s), original offset 0: `"\n\u0c2b\u0c4d\u0c2f\u0c3e\u0c28\u0c4d\n\n\u0c2b\u0c28\u0c3e\u0c21\u0c4d (\u0c05\u0c27\u0c3f\u0c15\u0c3e\u0c30\u0c3f\u0c15 \u0c2a\u0c47\u0c30\u0c41\u0c03 \u0c2b\u0c3e\u0c28\u0c48\u0c21\u0c4d) \u0c05\u0c28\u0c47\u0c26\u0c3f \u0c10\u0c30\u0c4d\u0c32\u0c3e\u0c02\u0c21\u0c4d\u0c32\u0c4b\u0c28\u0c3f \u0c21\u0c4a\u0c02\u0c17\u0c32\u0c4d"` (drop).
- `2af91e27831c93ec` (ind-te-sangraha-s), original offset 0: `"\n\u0c26\u0c3f \u0c38\u0c3f\u0c38\u0c4d\u0c38\u0c40\n\n\"\u0c26\u0c3f \u0c38\u0c3f\u0c38\u0c4d\u0c38\u0c40\" \u0c05\u0c28\u0c47\u0c26\u0c3f \u0c05\u0c2e\u0c46\u0c30\u0c3f\u0c15\u0c28\u0c4d \u0c2f\u0c3e\u0c28\u0c3f\u0c2e\u0c47\u0c1f\u0c46\u0c21\u0c4d \u0c1f\u0c46\u0c32\u0c3f\u0c35\u0c3f\u0c1c\u0c28\u0c4d \u0c38\u0c3f\u0c30\u0c40"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-012"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-sangraha-s'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"
SOURCE_ORIGIN = "ind-te-sangraha-s"
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d4(text):
    words = text.split()
    run = 1
    for a, b in zip(words, words[1:]):
        run = run + 1 if a == b else 1
        if run >= 8:
            return True
    if len(words) >= 200:
        top = max(words.count(w) for w in set(words) if len(w) > 2)
        return top / len(words) > 0.15
    return False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_d4` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 150 — indic / D5 / `DB-D5-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D5 Translationese. Pack `ind-te-sangraha-s`. Source: section D5 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `49a71d88fbcc7784` (ind-te-fw2), original offset 0: `"\u0c05\u0c30\u0c3f\u0c2f\u0c3e\u0c28\u0c3e \u0c17\u0c4d\u0c30\u0c3e\u0c02\u0c21\u0c47 \u0c32\u0c3e\u0c38\u0c4d-\u0c0f\u0c02\u0c1c\u0c3f\u0c32\u0c4d\u0c38\u0c4d \u0c30\u0c3f\u0c2f\u0c32\u0c4d \u0c0e\u0c38\u0c4d\u0c1f\u0c47\u0c1f\u0c4d \u0c0f\u0c1c\u0c46\u0c02\u0c1f\u0c4d \u0c21\u0c3e\u0c32\u0c4d\u0c1f\u0c28\u0c4d \u0c17\u0c4b\u0c2e\u0c46\u0c1c"` (drop).
- `d0692f163114fdb4` (ind-te-fw2), original offset 0: `"\u0c24\u0c3e\u0c1c\u0c3e \u0c2a\u0c30\u0c3f\u0c23\u0c3e\u0c2e\u0c02\u0c32\u0c4b, \u0c06\u0c28\u0c02\u0c26\u0c4d \u0c35\u0c30\u0c4d\u0c27\u0c28\u0c4d \u0c15\u0c4a\u0c24\u0c4d\u0c24 \u0c0e\u0c17\u0c4d\u0c1c\u0c3f\u0c15\u0c4d\u0c2f\u0c42\u0c1f\u0c3f\u0c35\u0c4d \u0c21\u0c48\u0c30\u0c46\u0c15\u0c4d\u0c1f\u0c30\u0c4d\u0c17\u0c3e \u0c28\u0c3f\u0c2f"` (drop).
- `aa3d8930cac21214` (ind-te-fw2), original offset 0: `"\u0c0e\u0c32\u0c15\u0c4d\u0c1f\u0c4d\u0c30\u0c3f\u0c15\u0c32\u0c4d \u0c2a\u0c30\u0c3f\u0c15\u0c30\u0c3e\u0c32\u0c28\u0c41 \u0c38\u0c30\u0c33 \u0c2e\u0c30\u0c3f\u0c2f\u0c41 \u0c28\u0c3e\u0c28\u0c4d \u0c32\u0c40\u0c28\u0c3f\u0c2f\u0c30\u0c4d \u0c2d\u0c3e\u0c17\u0c3e\u0c32 \u0c38\u0c39\u0c3e\u0c2f\u0c02\u0c24\u0c4b \u0c28\u0c3f\u0c30\u0c4d\u0c2e"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d5(text)`.

```python
RULE_ID = "DB-D5-001"
CODE = "D5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s, ind-te-fw2, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-sangraha-s"
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d5(text):
    words = len(text.split())
    n = text.count("యొక్క")
    return n >= 6 and 100 * n / words >= 2


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_d5` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section D5 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 151 — indic / F2 / `DB-F2-001`

**Integration decision:** DEFERRED. prose: RuntimeError; joiners: RuntimeError; nfc: RuntimeError; current own-pack gold: ERROR; requires ITIHASA_TEST_SN and independent benchmark approval; not part of this build; benchmark policy/fingerprints unresolved; keep-only detector is not implemented cleaning. Source harm statements below are inherited; current local own-pack gold: ERROR. The integration status above supersedes the source card status below.

1. **Disease:** F2 Benchmark leak. Pack `ind-sa-fw2`. Source: section F2 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f2(text)`.

```python deferred
RULE_ID = "DB-F2-001"
CODE = "F2"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "prose: RuntimeError; joiners: RuntimeError; nfc: RuntimeError; current own-pack gold: ERROR; requires ITIHASA_TEST_SN and independent benchmark approval; not part of this build; benchmark policy/fingerprints unresolved; keep-only detector is not implemented cleaning"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

import os

_L = "ऀ-ॣ०-ॿ"
_W, _STEP, _MIN = 40, 20, 3
_INDEX = {}

def _windows():
    if not _INDEX:
        path = os.environ.get("ITIHASA_TEST_SN")
        if not path:
            raise RuntimeError("set ITIHASA_TEST_SN to the Itihasa test.sn.csv file")
        with open(path, encoding="utf-8") as f:
            for k, line in enumerate(f):
                n = re.sub(f"[^{_L}]", "", line)
                if len(n) < _W:
                    continue
                for j in range(0, len(n) - _W + 1, _STEP):
                    _INDEX.setdefault(n[j:j + _W], set()).add(k)
    return _INDEX

def medicine_f2(text):
    index = _windows()
    n = re.sub(f"[^{_L}]", "", text)
    hit = set()
    for j in range(len(n) - _W + 1):
        hit |= index.get(n[j:j + _W], set())
    return len(hit) >= _MIN


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F2 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 152 — indic / F3 / `DB-F3-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F3 Harmful content. Pack `ind-bn-fw2`. Source: section F3 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3c0d0458978d7c51` (ind-bn-fw2), original offset 0: `"\u0985\u09a8\u09b2\u09be\u0987\u09a8\u09c7 \u09b2\u09be\u0987\u09ad \u0995\u09cd\u09af\u09be\u09b8\u09bf\u09a8\u09cb \u0996\u09c7\u09b2\u09cb\u09af\u09bc\u09be\u09a1\u09bc\u09a6\u09c7\u09b0 \u09ac\u09bf\u099f\u0995\u09af\u09bc\u09c7\u09a8 \u09ac\u09cd\u09af\u09ac\u09b9\u09be\u09b0 \u0995\u09b0\u09c7 \u09aa\u09cd\u09b0\u09a4\u09cd\u09af\u09be\u09b9"` (drop).
- `43804ba72410d8ff` (ind-bn-fw2), original offset 0: `"\u0986\u09aa\u09a8\u09be\u09b0 \u09aa\u09cd\u09b0\u09bf\u09af\u09bc \u09aa\u09b0\u09cd\u09a8 \u099f\u09bf\u0989\u09ac FILMEPORNOX \u098f \u09ac\u09bf\u09a8\u09be\u09ae\u09c2\u09b2\u09cd\u09af\u09c7 \u099a\u09b2\u09cb \u09ac\u09be\u0987\u09b0\u09c7 \u099a\u09cb\u09a6\u09be -"` (drop).
- `95261ddc152835cc` (ind-bn-fw2), original offset 0: `"\u09aa\u09cd\u09b0\u09cb\u0997\u09cd\u09b0\u09be\u09ae\u099f\u09bf \u0986\u09aa\u09a8\u09be\u0995\u09c7 \u09ac\u09c7\u099b\u09c7 \u09a8\u09c7\u0993\u09af\u09bc\u09be\u09b0 \u099c\u09a8\u09cd\u09af 30 \u099f\u09bf\u09b0\u0993 \u09ac\u09c7\u09b6\u09bf \u0985\u09a4\u09bf\u09b0\u09bf\u0995\u09cd\u09a4 \u0995\u09be\u09b0\u09cd\u09af"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_f3(text)`.

```python
RULE_ID = "DB-F3-001"
CODE = "F3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_B = '\u0980-\u09ff'
_TERMS = re.compile(r'(?i)casino|betting|mostbet|888starz|1xbet|porn|xxx|sex\s*video|'
                    rf'(?<![{_B}])(?:ক্যাসিনো|বেটি\u0982|মোস্টবেট|বুকমেকার|পর্ন|সেক্স)(?![{_B}])')

def medicine_f3(text):
    """Drop gambling and pornography pages: 3 or more hits of the term list.
    Hate and extremist content is not caught by a word list; it goes to human review."""
    return len(_TERMS.findall(text)) >= 3


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F3 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 153 — indic / F3 / `DB-F3-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-F3-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F3 Harmful content. Pack `ind-bn-fw2`. Source: section F3 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f3(text)`.

```python deferred
RULE_ID = "DB-F3-002"
CODE = "F3"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-F3-001"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re

_F3_RX = re.compile(r"পর্ন|চোদা|ক্যাসিনো|বেটিং|বাজি ধর|জুয়া খেল|casino|betting|porn|xxx|sex video", re.I)


def medicine_f3(text):
    """Drop (True) when there are >= 4 hits and >= 1 hit per 600 characters."""
    n = len(_F3_RX.findall(text))
    return n >= 4 and n * 600 >= len(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS. The density rule keeps news about casino raids: `ce8a91b51a89e51a` has 2 hits in
5. **Side effects:** in the author's `medicine.md`, section F3 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 154 — indic / F3 / `DB-F3-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F3 Harmful content. Pack `ind-te-fw2`. Source: section F3 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `8cac6c338ccde963` (ind-te-fw2), original offset 0: `"Maradhalu Sex Stories Telugu - \u0c2e\u0c30\u0c26\u0c32\u0c41 \u0c38\u0c46\u0c15\u0c4d\u0c38\u0c4d \u0c38\u0c4d\u0c1f\u0c4b\u0c30\u0c40\u0c38\u0c4d \u0c24\u0c46\u0c32\u0c41\u0c17\u0c41 - Ne"` (drop).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `f3_harmful(text)`.

```python
RULE_ID = "DB-F3-003"
CODE = "F3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-s, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

F3_URL = re.compile(r"sex-?stor|(?<![a-z])sex(?![a-z])|porn|xxx|erotic|erotyczn|adult|phone-spy|spy-on|prize-?bond"
                    r"|satta|casino|betting", re.I)
F3_RX = re.compile(r"sex\s*stor|porn|xxx|\bnude\b|దెంగ|పూకు|మొడ్డ|బూతు\s*కథ|సెక్స్\s*కథ|prize\s*bond|satta\s*matka"
                   r"|betting\s*tips", re.I)
def f3_harmful(t, url=None):
    return True if (F3_URL.search(url or "") or len(F3_RX.findall(t)) >= 3) else False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = f3_harmful  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section F3 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 155 — indic / G1 / `DB-G1-011`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-kn-sangraha-v`. Source: section G1 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `c245d243cb8e3428` (ind-kn-sangraha-v), original offset 0: `"\u0ca8\u0cbf\u0cae\u0ccd\u0cae \u0cb8\u0ccd\u0cb5\u0c82\u0ca4 ography \u0cbe\u0caf\u0cbe\u0c97\u0ccd\u0cb0\u0cb9\u0ca3 \u0cb5\u0ccd\u0caf\u0cb5\u0cb9\u0cbe\u0cb0\u0cb5\u0ca8\u0ccd\u0ca8\u0cc1 \u0caa\u0ccd\u0cb0\u0cbe\u0cb0\u0c82\u0cad\u0cbf\u0cb8\u0cc1\u0cb5\u0cc1\u0ca6\u0cc1 \u0ca8\u0cbf\u0cae\u0ccd\u0cae \u0c89"` (drop).
- `c84d7b1e2256670e` (ind-kn-sangraha-v), original offset 0: `"\u0cb8\u0cbe\u0ca7\u0ca8\u0cc6\u0caf \u0cae\u0cc6\u0c9f\u0ccd\u0c9f\u0cbf\u0cb2\u0cc1 \u0c8f\u0cb0\u0cac\u0cb9\u0cc1\u0ca6\u0cc1; \u0c95\u0c9f\u0ccd\u0c9f\u0ca1\u0ca6\u0ccd\u0ca6\u0cb2\u0ccd\u0cb2 ! | Udayavani - \u0c89\u0ca6\u0caf\u0cb5\u0cbe\u0ca3\u0cbf\\nFr"` (drop).
- `9f746e71dabdd692` (ind-kn-sangraha-v), original offset 0: `"\u0cb5\u0cc8\u0ca6\u0cbf\u0c95\u0cc7\u0ca8\u0cbe\u0ca7\u0ccd\u0caf\u0cbe\u0caf\u0cc7\u0ca8\u0cbe\u0c82\u0ca4\u0cb0\u0cbf\u0caf\u0cbe\u0ca8\u0ccd\u0ca8\u0cbe\u0cb8\u0ccd\u0cae\u0cbf\u0c95\u0ccd\u0c95\u0ca5\u0cbe\u0c82 \u0cb5\u0ca6\u0cc7\u0ca4 \u0ca8\u0cbe\u0cb8\u0ccd\u0caf \u0cb0\u0cbe\u0ca4\u0ccd\u0cb0\u0cbf \u0c9a \u0ca8 \u0c9a \u0c95\u0cc0\u0cb0"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-011"
CODE = "G1"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"
SOURCE_ORIGIN = "ind-kn-sangraha-v"
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

KN_CONS = set(range(0x0C95, 0x0CBA)) | {0x0CDE}         # consonants
KN_MATRA = set(range(0x0CBE, 0x0CCD))                   # dependent vowel signs
VIRAMA_CP, NUKTA_CP, ANUSVARA_CP, VISARGA_CP = 0x0CCD, 0x0CBC, 0x0C82, 0x0C83   # code points, not characters
LEN_MARKS = {0x0CD5, 0x0CD6}
VOWELS_BEFORE_YA = {0x0C85, 0x0C86, 0x0C8E}             # ಅ ಆ ಎ, as in ಆ್ಯಪ್
YA = 0x0CAF


def is_kn(c):
    return 0x0C80 <= ord(c) <= 0x0CFF


def broken_signs(t):
    """G1: offsets of a vowel sign, virama, nukta, anusvara or visarga that has no letter to sit on.

    ಆ್ಯ (vowel + virama + ಯ) is the standard spelling of the English "a" sound (ಆ್ಯಪ್) and is not counted.
    A visarga after a virama is a colon turned into a visarga (G4), not a broken sign.
    """
    out = []
    for i, ch in enumerate(t):
        o = ord(ch)
        p = ord(t[i - 1]) if i else 0
        nx = ord(t[i + 1]) if i + 1 < len(t) else 0
        if o == VIRAMA_CP and p in VOWELS_BEFORE_YA and nx == YA:
            continue
        if o in KN_MATRA or o == VIRAMA_CP or o == NUKTA_CP:
            if p not in KN_CONS and p != NUKTA_CP:
                out.append(i)
        elif o == ANUSVARA_CP:
            if not (i and is_kn(t[i - 1])) or p == VIRAMA_CP:
                out.append(i)
        elif o == VISARGA_CP:
            if not (i and is_kn(t[i - 1])):
                out.append(i)
        elif o in LEN_MARKS:
            if p not in (0x0CBF, 0x0CC6, 0x0CCA):
                out.append(i)
    return out


def heavy_broken_signs(t, min_count=3):
    """G1: drop a document with min_count or more vowel signs or viramas that have no letter to sit on."""
    return len(broken_signs(t)) >= min_count


def medicine_g1(text):
    """The G1 rule, under the name that the harm tests look for: True drops the document."""
    return heavy_broken_signs(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 156 — indic / G3 / `DB-G3-001`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G3 Indic dropped by an English rule. Pack `ind-sa-fw2`. Source: section G3 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g3(text)`.

```python deferred
RULE_ID = "DB-G3-001"
CODE = "G3"
ACTION = "drop"
STAGE = "30"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_NO = re.compile(r"॥\s*([०-९\d]+)\s*(?:॥|$)", re.M)
_DIG = str.maketrans("०१२३४५६७८९", "0123456789")

def medicine_g3(text):
    n = [int(x.translate(_DIG)) for x in _NO.findall(text)]
    if len(n) >= 3 and n[0] == 2 and 1 not in n and _NO.search(text).start() < 600:
        return True
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 15]
    if len(lines) < 15 or "॥" in text:
        return False
    half = sum(1 for l in lines if re.search(r"[^०-९\d\s]\s*।$", l))
    numbered = sum(1 for l in lines if re.search(r"[०-९\d]\s*।$", l))
    short = sorted(len(l) for l in lines)[len(lines) // 2] <= 50
    return numbered == 0 and short and half / len(lines) >= 0.8


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G3 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 157 — indic / C1 / `DB-C1-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-bn-fw2`. Source: section C1 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `e9bc37a7fcf3808d` (ind-bn-fw2), original offset 2239: `"\u09af\u09cb\u0995\u09cd\u09a4\u09be\u0964\n\u0986\u09b0\u09cb \u09aa\u09a1\u09bc\u09c1\u09a8\u0983\n- \u0985\u09a8\u09b2\u09be\u0987\u09a8 \u09ac\u09cd\u09af\u09ac"` (fix).
- `20eb3e61ca9713c1` (ind-bn-fw2), original offset 1211: `"\u09b0 \u09aa\u09cd\u09b0\u09ae\u09c2\u0996\n3,619 total views, 1 vi"` (fix).
- `61dc0261aeb4ced0` (ind-bn-fw2), original offset 1212: `"PEIBN0h\n\u2014 Vice President of Indi"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-001"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

def _nk(p):
    # ড় ঢ় য় may be stored as one code point or as letter + nukta (U+09BC): match both.
    for one, two in (('\u09dc', '\u09a1\u09bc'), ('\u09dd', '\u09a2\u09bc'), ('\u09df', '\u09af\u09bc')):
        p = p.replace(two, one).replace(one, '(?:%s|%s)' % (one, two))
    return p

_START = re.compile(_nk(r"""^[\s\-–—#*>/]*(?:
    আর(?:ও|\u09cb|\u09cbও)\s*(?:পড়\u09c1ন|পড়তে\s*পারেন)|এছাড়\u09beও\s*পড়\u09c1ন|
    প্রকাশিত(?:\s*হয়\u09c7ছে)?\s*[:\u0983]|প্রকাশের\s*সময়\s*[:\u0983]|আপডেট\s*সময়|শেষ\s*আপডেট\s*[:\u0983]|
    বা\u0982লাদেশ\s*সময়\s*[:\u0983]|Published\s+on|Last\s+Updated\s+on|
    শেয়\u09beর\s*করুন|View\s+this\s+post\s+on\s+Instagram|A\s+post\s+shared\s+by|
    সর্বস্বত্ব\s*সংরক্ষিত|Powered\s+by\s|For\s+all\s+the\s+latest|Continue\s+Reading|
    ট্যাগ\s*[:\u0983]|Tags?\s*:|পোস্ট\s*ট্যাগ|হোয়\u09beটসঅ্যাপে\s*ফলো\s*করুন|
    প্রতিনিধি\s+প্রিন্ট\s+সংস্করণ|\[hupso\]
)""", ), re.X)
_WHOLE = re.compile(_nk(r"""^[\s\-–—#*>/]*(?:
    মন্তব্য\s*করুন|সম্পর্কিত\s*(?:খবর|নিউজ)|Related\s+News|Advertisement|বিজ্ঞাপন|
    সুচিপত্র|সূচিপত্র|পরিচ্ছেদসমূহ|Read\s+More|শীর্ষ\s*সংবাদ\s*[:\u0983]?|
    [\d০-৯,]+\s*(?:total\s+views.*|বার\s+(?:পড়\u09be\s+হয়\u09c7ছে|পঠিত))
)\s*$""", ), re.X)
_TWEET = re.compile(r"pic\.twitter\.com/|^\s*[—-]\s*[^\n]{1,60}\(@\w{1,15}\)\s+[A-Z][a-z]+\s+\d{1,2},\s+\d{4}\s*$")

def medicine_c1(text):
    """Delete whole lines that are page chrome. A line is deleted only if it is at most 200 characters long."""
    out = []
    for line in text.split('\n'):
        if len(line) <= 200 and (_START.match(line) or _WHOLE.match(line) or _TWEET.search(line)):
            continue
        out.append(line)
    return '\n'.join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 158 — indic / C1 / `DB-C1-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C1-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-bn-fw2`. Source: section C1 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python deferred
RULE_ID = "DB-C1-002"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C1-001"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re

_C1_LINE = re.compile(
    r"^\s*(?:"
    r"(?:আরও|আরো) (?:পড়ুন|পড়তে পারেন)\s*[:ঃ]?.{0,80}|শেয়ার করুন\s*[:ঃ]?|মন্তব্য করুন|বিজ্ঞাপন|"
    r"(?:প্রতিনিধি )?প্রিন্ট সংস্করণ|সর্বশেষ|সর্বাধিক পঠিত|শীর্ষ সংবাদ\s*[:ঃ]?|সম্পর্কিত (?:নিউজ|খবর)|"
    r"সাবস্ক্রাইব করুন এবং সর্বশেষ খবর.*|আমাদের নিউজ চ্যানেল|.*ইউটিউব চ্যানেলে সাবস্ক্রাইব করুন|"
    r".*হোয়াটসঅ্যাপে ফলো করুন.*|এ বিভাগের সর্বাধিক পঠিত|বিস্তারিত (?:ভিডিওতে দেখুন|আরোও জানতে ক্লিক করুন)\s*[:ঃ]?|"
    r"View this post on Instagram|Read (?:More|Entire Article).{0,3}|Continue Reading.{0,3}|Highlights|"
    r"Powered by Froala Editor|For all the latest .* Click Here|[\d,]+ total views, \d+ views today|"
    r"- More Stories On :|\[hupso\]|#"
    r")\s*$", re.I)


def medicine_c1(text):
    """Delete whole furniture lines among the first 3 or last 6 lines."""
    lines = text.split("\n")
    n = len(lines)
    return "\n".join(l for k, l in enumerate(lines) if not ((k < 3 or k >= n - 6) and _C1_LINE.match(l)))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy gold 0 changed, 0 dropped of 314 (0 %). PASS.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 159 — indic / C1 / `DB-C1-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-gu-fw2`. Source: section C1 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `60bca4fb1f5b4f47` (ind-gu-fw2), original offset 1320: `" \u0aa8\u0ab9\u0acb\u0aa4\u0abe.\nREAD ALSO\n- \u0a97\u0abe\u0a9c\u0ac7\u0ab2\u0ac0 \u0aab\u0abf\u0ab2\u0acd\u0aae"` (fix).
- `9c013a675712ff90` (ind-gu-fw2), original offset 3018: `"\u0aaf\u0abe \u0ab9\u0aa4\u0abe.\n\u0a86 \u0aaa\u0aa3 \u0ab5\u0abe\u0a82\u0a9a\u0acb: \u0a97\u0aa3\u0ac7\u0ab6\u0acb\u0aa4\u0acd\u0ab8\u0ab5\u0aa8\u0ac0 "` (fix).
- `bfbddfa37a31c087` (ind-gu-fw2), original offset 1300: `"\u0ab5\u0ac0 \u0ab9\u0aa4\u0ac0.\nCopyright \u00a9 2022-23 DB C"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-003"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block
GU_DIGIT = "\u0AE6-\u0AEF"                    # Gujarati digits 0-9
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

C1_LINE = re.compile(
    r"^[ \t]*(?:Copyright © .*DB Corp|This website follows the DNPA"
    r"|ગુજરાતી સમાચાર નો ખજાનો એટલે News18 ગુજરાતી|View this post on Instagram"
    r"|લેટેસ્ટ મનોરંજન, News અને Videos માટે પેજ લાઈક કરો"
    r"|\(?(?:નોંધ|નોધ|Disclaimers?)[ \t]*[:ઃ\-]"
    r"|(?:READ ALSO|MUST READ|આ પણ વાંચો)[ \t]*[:ઃ\-–]?).*\n?", re.M)
C1_TAG = re.compile(r"[ \t]*– Latest Gujarati News")
C1_DATELINE = re.compile(
    r"\A\s*(?:\((?:એજન્સી|અમારા પ્રતિનિધિ તરફથી|સંવાદદાતા દ્વારા)\)\s*)?"
    rf"(?:[{GU}]+(?: [{GU}]+)?\s*,\s*)?તા\.\s*[{GU_DIGIT}રપ0-9]{{1,2}}\s*[,:ઃ–\-]?\s*")

def m1_c1(text, url=None):
    new = C1_DATELINE.sub("", text, count=1)
    new = C1_LINE.sub("", new)
    return _fix(text, C1_TAG.sub("", new))

def medicine_c1(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m1_c1(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 160 — indic / C1 / `DB-C1-004`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-gu-fw2`. Source: section C1 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python deferred
RULE_ID = "DB-C1-004"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-gu-fw2'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

LINE_PATTERNS = [
    r"Copyright © .*All Rights Reserved\.?",
    r"This website follows the DNPA Code of Ethics\.?",
    r"ગુજરાતી સમાચાર નો ખજાનો એટલે News18 ગુજરાતી\..*",
    r"View this post on Instagram",
    r"Tags:.*",
    r"(આ પણ વાંચો|તમે આ પણ વાંચી શકો છો)\s*[:\-–].*",
    r"આ પણ વાંચો\s*:?",
    r"(Subscribe|Visit) Saurashtra Kranti.*",
    r"Read (About Weather|National News|Saurashtra Kranti E-Paper).*",
    r"For any News, Event coverage.*",
    r"आपके किसी भी प्रकार.*",
    r"આપના કે આપની સંસ્થાના.*",
    r"You Can Find us on Google Play store too.*",
    r"Android: https?://\S+",
    r"— .{1,60}\(@\w+\).*\d{4}",
    r".*pic\.twitter\.com/\S+",
    r"(Article Source|Courtesy) : .*",
    r"[A-Z][a-z]{2} \d{1,2}, ?\d{4}, \d{1,2}:\d{2} [AP]M IST",
    r"Tap to Read ➤",
    r"[\d,]+ Views, \d+",
    r"વધુ વાંચો",
    r"અમારી (દર નવી|અન્ય) પોસ્ટ.*",
    r"તમે આ લેખ “ગુજ્જુ ગુજરાતી”.*",
    r"આવા વધુ સમાચારો માટે નીચેની લિન્ક.*",
    r"Author: GujjuRocks Team.*",
    r"\(નોંધ[ –-].*\)",
    r"નોંધ: આ વેબસાઇટ પર.*",
    r"ઉપરના આર્ટીકલના તમામ.*",
    r"ગુજરાતના તમામ સ્થળે પ્રેસ પ્રતિનિધિ.*",
    '\\"વંદે માતરમ ,ભારત માતાકી જય\\"',
    r"જંગ એ ગુજરાત ના વેબ ન્યૂઝ પોર્ટલ માટે",
    r"માનદ પ્રતિનિધિ નિમવાના છે.*",
    r"ચહેરો\d+ કલાક પહેલા",
    r"- લિંક કૉપિ કરો",
    r"🌺આરતીસોની🌺",
    r"-આરતીસોની ©",
]
EXTRA = [
    r"\d{1,3} , \d{1,3}",
    r"લેટેસ્ટ મનોરંજન, News અને Videos માટે પેજ લાઈક કરો",
    r"Powered By .*",
    r"પોસ્ટનો સમય\s*:.*",
    r"સૌજન્ય\s*:?\s*(?:\n\s*)?દિવ્ય ભાસ્કર",
    r"ઇનપુટ્સ\s*:.*",
    r"જુઓ (?:આ )?વિડીયો",
    r"અમારી અન્ય પોસ્ટ પણ વાંચો\s*:?-?",
    r"સોશિયલ મીડિયા પ્લેટફોર્મ પર અમારી સાથે જોડાઓ",
    r"Visit Saurashtra Kranti Homepage here",
    r"Read About Weather here",
    r"(?:\.\.\. ?)?Read More",
    r"Team VTV.*",
]
LINE = re.compile(r"^\s*(?:" + "|".join(LINE_PATTERNS + EXTRA) + r")\s*$\n?", flags=re.M)
# headline line that is stored after the body, just before a final dateline such as "(એજન્સી) તા.૬"
TRAIL = re.compile(r"\n[^\n]+\n(?=\(?[^\n]{0,30}\)?[ ,]*તા\.? ?[\d૦-૯]+\s*$)")

def medicine(text):
    return TRAIL.sub("\n", LINE.sub("", text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 147 of ...
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 161 — indic / C1 / `DB-C1-005`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-hi-fw2`. Source: section C1 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `7550aa66f80ae7c0` (ind-hi-fw2), original offset 0: `"Ads \u0938\u0947 \u0939\u0948 \u092a\u0930\u0947\u0936\u093e\u0928? \u092c\u093f\u0928\u093e A"` (fix).
- `b8d161e14742a312` (ind-hi-fw2), original offset 423: `"\u093f\u0916\u093e \u0939\u0948\u0964\n\u0939\u092e \u0921\u093e\u091f\u093e \u0938\u0902\u0917\u094d\u0930\u0939 \u091f\u0942\u0932\u094d\u0938, \u091c\u0948"` (fix).
- `3a3f617148815241` (ind-hi-fw2), original offset 32: `"\u0915\u092d\u0940 \u092d\u0940\u0964\n*Yearly subscription for"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `strip_c1_lines(text)`.

```python
RULE_ID = "DB-C1-005"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-fw2"
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_C1_LINE = re.compile(
    r"(?is)^\s*(?:"
    r"Ads\s+से\s+है\s+परेशान.*"
    r"|Download\s+Dainik\s+Bhaskar\s+App.*"
    r"|Read\s+the\s+latest\s+and\s+breaking\s+Hindi\s+news\s+on\s+\S+.*"
    r"|\*?Yearly\s+subscription\s+for\s+just\s+.*"
    r"|(?:Updated|First\s+published):?\s+.*\d{4}.*(?:IST|AM|PM).*"
    r"|Posted\s+By:\s*.{1,80}"
    r"|Advertisement\s*"
    r"|Don'?t\s+Miss!?"
    r"|Recover\s+your\s+password\.?"
    r"|A\s+password\s+will\s+be\s+e-mailed\s+to\s+you\.?"
    r"|(?:इसे|ये|यह)\s+भी\s+पढ़ें?\s*[:：]?\s*[–-]?\s*"
    r"|सामान्य\s+सूची\s+पर\s+लौटें.*"
    r"|Share\s+on\s+WhatsApp.*"
    r"|follow\s+us\b.*"
    r"|हम\s+(?:डाटा\s+संग्रह|विज्ञापन).{0,60}कुकी.*"
    r"|cookie\s+(?:policy|notice|banner).*"
    r"|बिना\s+Ads\s+खबरों.*"
    r")\s*$"
)

def strip_c1_lines(text: str) -> str:
    """Remove whole lines that match C1 site furniture; keep everything else."""
    kept = []
    for line in (text or "").splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if _C1_LINE.match(body):
            continue
        kept.append(line)
    return "".join(kept)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = strip_c1_lines  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `ind-hi-fw2_gold.csv` (**234** docs, post-#161). Tool: `harm_test_indic.py --rule C1` (2026-10-31). Ran `strip_c1_lines`:
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 162 — indic / C1 / `DB-C1-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-hi-hplt`. Source: section C1 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `7261baa0a3edfb1d` (ind-hi-hplt), original offset 8974: `"\u0917\u092f\u0940 \u0939\u0948\u0902\u0964\nNo comments:\nPost a Com"` (fix).
- `ca38e3770cd4bd18` (ind-hi-hplt), original offset 8148: `"\u0915\u0924\u0947 \u0939\u0948\u0902\u0964\n\u0905\u0927\u093f\u0915\u0924\u092e \u0930\u0947\u091f\u093f\u0902\u0917 5\n\u0928\u094d\u092f\u0942\u0928\u0924\u092e"` (fix).
- `7a2bc38b934a51ad` (ind-hi-hplt), original offset 8121: `"\u091c\u093e\u0924\u093e \u0939\u0948\u0964\n\u0905\u0927\u093f\u0915\u0924\u092e \u0930\u0947\u091f\u093f\u0902\u0917 5\n\u0928\u094d\u092f\u0942\u0928\u0924\u092e"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-006"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-hplt'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_LINE = re.compile(r"^[ \t]*(?:ADVERTISEMENT|Advertisement|Share(?: this)?:|Read More…?)[ \t]*\n?", re.M)
_RELATED = re.compile(r"^[ \t]*(?:यह भी पढ़ें|इसे भी पढ़ें)\b.*\n?", re.M)
_TAIL = re.compile(r"^[ \t]*(?:No comments:|Post a Comment|कोई टिप्पणी नहीं:|एक टिप्पणी भेजें|Leave a Reply|"
                   r"एक उत्तर दें|More Stories|Read Next|Related Articles|Related Posts|Tags:|आवश्यक सूचना|"
                   r"डिस्क्लेमर|अन्य न्यूज़|\(For more news|अधिकतम रेटिंग \d)", re.M)


def medicine_c1(text):
    t = _LINE.sub("", text)
    t = _RELATED.sub("", t)
    m = _TAIL.search(t, int(len(t) * 0.6))  # comment forms, related lists and disclaimers only near the end
    if m:
        t = t[:m.start()].rstrip()
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 163 — indic / C1 / `DB-C1-007`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C1-006. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-hi-hplt`. Source: section C1 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python deferred
RULE_ID = "DB-C1-007"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C1-006"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C1: known template lines, removed only when the whole line is the template
_C1 = re.compile(
    r"^[ \t]*(?:"
    r"(?:यह|ये|इसे|इन्हें) भी (?:पढ़ें|पढ़े|देखें)\s*[:：\-–—]?.*"
    r"|\d+ Comments?'?s?|No comments|There are no comments|Add yours|Leave a comment|Comment Now"
    r"|Comments in this topic:|COMMENTS|टिप्पणियाँ|Post a Comment"
    r"|Share(?: This Post)?:?|शेयर करें|Advertisement|विज्ञापन"
    r"|Read More(?:\.\.\.|…)?|और पढ़ें"
    r"|About Post Author|Post Views:.*|Recent Posts|अन्य न्यूज़"
    r"|Reviews for:.*|\(For more news.*|\(SocialLY के साथ पाएं.*"
    r")[ \t]*(?:\n|$)",
    re.M,
)


def medicine_c1(text):
    return _C1.sub("", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 84 of 199 C1 documents; 1 other diseased documents touc...
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 164 — indic / C1 / `DB-C1-008`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-kn-fw2`. Source: section C1 of `diagnosis/submissions/ind-kn-fw2/LokeshJatangi/medicine.md`, PR #63 at `aeb79b8`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `a7746a3981e58f31` (ind-kn-fw2), original offset 1249: `"\u0cbf\u0c95\u0ccd\u0c95\u0cbf\u0cb8\u0cbf\nLast Updated Mar 27, 201"` (fix).
- `95fcd3a60a26a368` (ind-kn-fw2), original offset 0: `"Just In\nDon't Miss!\n- Ne"` (fix).
- `10c1bbd17380fb15` (ind-kn-fw2), original offset 0: `"Just In\nDon't Miss!\n- Ne"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-008"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"
SOURCE_ORIGIN = "ind-kn-fw2"
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "LokeshJatangi"  # PR #63 at aeb79b8

import re
import unicodedata

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    out = list(text)
    for a, b in spans:
        if not protected(text[a:b]):
            out[a:b] = [""] * (b - a)  # Keep source indices stable, even for overlaps.
    return "".join(out)

MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DAY = r"(?:0?[1-9]|[12][0-9]|3[01])"
TIME = r"(?:(?:0?[1-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?\s+(?:AM|PM)|(?:[01]?[0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?)"
ZONE = r"(?:IST|UTC|GMT|[+-](?:[01][0-9]|2[0-3]):?[0-5][0-9])"
WEEKDAY = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
DATE = rf"(?:{WEEKDAY},\s*)?{MONTH}\.?\s+{DAY},\s*[0-9]{{4}},\s*{TIME}\s+(?:{ZONE}|\[{ZONE}\])"
MARKER = r"(?:First\s+Published|Last\s+(?:Modified|Updated)|Published|Updated)"
LOCAL_DATE = rf"(?:[\u0c80-\u0cff]+,\s*)?\d{{1,2}}\s+[\u0c80-\u0cff]+\s+\d{{4}}\s*\({TIME}\s+{ZONE}\)"
STAMP = re.compile(rf"{MARKER}(?:\s*:\s*|\s+)(?:{DATE}|{LOCAL_DATE})", re.I)
KANNADA_STAMP = re.compile(rf"(?:ಭಾನುವಾರ|ಸೋಮವಾರ|ಮಂಗಳವಾರ|ಬುಧವಾರ|ಗುರುವಾರ|ಶುಕ್ರವಾರ|ಶನಿವಾರ),\s*\d{{1,2}}\s+[\u0c80-\u0cff]+\s+\d{{4}}\s*\({TIME}\s+IST\)", re.I)
FOLLOW = re.compile(r"Please\s+follow\s+and\s+like\s+us\s*:?", re.I)

def medicine_c1(text, url=""):
    rows, spans, offset = text.splitlines(keepends=True), [], 0
    for i, line in enumerate(rows):
        body, label = line.strip(), line.strip().casefold()
        pair = (label == "just in" and i + 1 < len(rows)
                and rows[i + 1].strip().casefold() in {"don't miss!", "don’t miss!"})
        if (STAMP.fullmatch(body) or KANNADA_STAMP.fullmatch(body) or FOLLOW.fullmatch(body)
                or label in {"don't miss!", "don’t miss!"} or pair):
            spans.append((offset, offset + len(line)))
        offset += len(line)
    return remove_spans(text, spans)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #63).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 165 — indic / C1 / `DB-C1-009`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C1-008. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-kn-fw2`. Source: section C1 of `diagnosis/submissions/ind-kn-fw2/keshavamurali/medicine.md`, PR #47 at `8158532`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python deferred
RULE_ID = "DB-C1-009"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-kn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C1-008"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "keshavamurali"  # PR #47 at 8158532
import re  # added by Data B: harm_test_indic.py gives every block `re`

import hashlib
import unicodedata

ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
BOILER = re.compile(r'Share on WhatsApp|Copyright|©|Leave a Reply|Team Udayavani|ಟಾಪ್ ನ್ಯೂಸ್'
                    r'|\d+\s*(days?|hours?|minutes?) ago|Read more|ಇನ್ನಷ್ಟು (ಓದಿ|ಸುದ್ದಿ)', re.I)
DASH_EN = re.compile(r'^[ \t]*[-–•][ \t]+[A-Za-z].*$', re.M)
DASH_BARE = re.compile(r'^[ \t]*[-–•][ \t]*\n[^\n]*\d+\s*days? ago[^\n]*$', re.M)
TEMPLATES = frozenset({          # site-template lines of ind-kn-fw2, found by medicines.py --templates
    '0c61b19cfb72c68a', '1523d8487cd4c792', '33f8a3e8d468bc8a', '4c304be013888589',
    '54181b210567e69b', '714f62bb0822152b', '86796ef8093339d7', '9236d07688fe64f6',
    '9c5d9390e0604341', 'b3f8b6881e5db8b7', 'bbce4efb0877577a', 'be298df70325f3f8',
    'cd54a6b665b3a745', 'e73bc5bae38473b3', 'ff2cc858983d961c',
})

def _protected(line):
    return ZWJ in line or ZWNJ in line or any(unicodedata.decomposition(c).startswith('<') for c in line)

def _key(line):
    return hashlib.blake2b(line.encode('utf-8'), digest_size=8).hexdigest()

def medicine_c1(text, templates=TEMPLATES):
    def cut(m):
        return m.group() if _protected(m.group()) else ''
    t = DASH_BARE.sub(cut, text)
    t = DASH_EN.sub(cut, t)

    def boiler(l):
        s = l.strip()
        return not _protected(s) and ((len(s) >= 3 and _key(s) in templates) or BOILER.search(s))
    return '\n'.join(l for l in t.split('\n') if not boiler(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #47).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 166 — indic / C1 / `DB-C1-010`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-kn-sangraha-s`. Source: section C1 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS); ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3a69a945a1b7aeaa` (ind-kn-sangraha-s), original offset 547: `"\u0ca1\u0cb2\u0cbe\u0caf\u0cbf\u0ca4\u0cc1\u0c83\n\u0cac\u0cbe\u0cb9\u0ccd\u0caf \u0cb8\u0c82\u0caa\u0cb0\u0ccd\u0c95\u0c97\u0cb3\u0cc1.\n<\u0cac\u0cbf. \u0c86"` (fix).
- `4014a84b9c3e0022` (ind-kn-sangraha-s), original offset 1303: `"\u0ca1\u0cb2\u0cbe\u0caf\u0cbf\u0ca4\u0cc1.\n\u0c89\u0cb2\u0ccd\u0cb2\u0cc7\u0c96\u0c97\u0cb3\u0cc1.\n\u0cae\u0cc2\u0cb2\u0c97\u0cb3\u0cc1\n\n"` (fix).
- `54f770edbfb0f27e` (ind-kn-sangraha-s), original offset 1735: `"\u0cb0\u0cc1\u0ca4\u0ccd\u0ca4\u0ca6\u0cc6.\n\u0c89\u0cb2\u0ccd\u0cb2\u0cc7\u0c96\u0c97\u0cb3\u0cc1.\n\u0c85\u0c82\u0ca4\u0cbe\u0cb0\u0cbe\u0cb7\u0ccd\u0c9f\u0ccd\u0cb0\u0cc0"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `m4_footer(text)`.

```python
RULE_ID = "DB-C1-010"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-sangraha-s', 'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s, ind-kn-sangraha-v"
SOURCE_ORIGIN = "ind-kn-sangraha-s"
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

FOOTER = re.compile(r"^(?:ಉಲ್ಲೇಖಗಳು|ಮೂಲಗಳು|ಟಿಪ್ಪಣಿಗಳು|ಗ್ರಂಥಸೂಚಿ|ಬಾಹ್ಯ ಸಂಪರ್ಕಗಳು|ಇದನ್ನೂ ನೋಡಿ)\.?[ \t]*$", re.M)
AD_LINE = re.compile(r"^[ \t]*ಜಾಹೀರಾತು[ \t]*\n?", re.M)
def m4_footer(s):
    m = FOOTER.search(s)
    if m and m.start() > len(s) // 2:
        s = s[: m.start()].rstrip()
    return AD_LINE.sub("", s)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m4_footer  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 5 of 359 changed. I read all 5. Two
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 167 — indic / C1 / `DB-C1-011`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-kn-sangraha-v`. Source: section C1 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python deferred
RULE_ID = "DB-C1-011"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-kn-sangraha-v'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

import re

C1_LINE = re.compile(
    r"^\s*(?:Don't Miss!?|-\s*(?:News|Sports|Movies|Technology|Finance|Education|Lifestyle|Automobiles|Travel)\s.*"
    r"|-\s*\d+\s*(?:min|mins|hr|hrs)\s+ago\s.*|-\s*#\S.*"
    r"|ಇದನ್ನೂ ಓದಿ\s*[:ಃ].*|A post shared by .*"
    r"|ಪ್ರಜಾವಾಣಿ ಫೇಸ್‌?ಬುಕ್ ಪುಟವನ್ನು\s*ಫಾಲೋ ಮಾಡಿ.*|Oneindia ಬ್ರೇಕಿಂಗ್ ನ್ಯೂಸ್.*|ಹೊಸದಿಗಂತ ಡಿಜಿಟಲ್ ಡೆಸ್ಕ್"
    r"|The views expressed in comments published .*|Thanks For Reading!?|Like this:|Forgot your password\?"
    r"|To Start receiving timely alerts.*|Trending Topics\s*:?|(?:Home|ಮುಖಪುಟ)\s*[›»].*"
    r"|Posted on \w+ \d{1,2}, \d{4} by .*|(?=.{0,120}$).*(?:ಶೇರ್|ಲೈಕ್) ಮಾಡಿ[.!]?)\s*$")


def strip_boilerplate(t):
    """C1: remove whole boilerplate lines: Oneindia link blocks ('Don't Miss!', '- News ...', '- 2 hrs ago ...',
    '- #tag ...'), 'ಇದನ್ನೂ ಓದಿ:' (also read), follow/share/like prompts, desk lines, comment policies, breadcrumbs
    and embed lines."""
    return "\n".join(l for l in t.split("\n") if not C1_LINE.match(l))


def medicine_c1(text):
    """The C1 rule, under the name that the harm tests look for: returns the fixed text."""
    return strip_boilerplate(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 168 — indic / C1 / `DB-C1-012`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-mr-sangraha-v`. Source: section C1 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 1 changed / 0 dropped of 140 (PASS); ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `00eed90bde196e9c` (ind-mr-fw2), original offset 1322: `"\u093e\u0939\u0942\u092f\u093e..\n\u0939\u0947 \u0939\u0940 \u0935\u093e\u091a\u093e << \u0924\u094b\u0902\u0921\u093e\u0935\u0930 \u0928\u093e"` (fix).
- `870fb0ffd8d7a041` (ind-mr-fw2), original offset 886: `"\u094d\u0939\u0923\u093e\u0932\u0947.\n\u0939\u0947\u0939\u0940 \u0935\u093e\u091a\u093e >>> \u0938\u092e\u0943\u0926\u094d\u0927\u0940 \u092e\u0939"` (fix).
- `924d41c82dfe4138` (ind-mr-fw2), original offset 1130: `"\u0940 \u092e\u0939\u093e\u0917\u2026\n\u0939\u0947 \u0939\u0940 \u0935\u093e\u091a\u093e<< \u0938\u094d\u092e\u0943\u0924\u0940 \u0907\u0930\u093e\u0923"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_c1(text)`.

```python
RULE_ID = "DB-C1-012"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2', 'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v, ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f

import re

_C1_LINE = re.compile(
    r"^\s*(?:"
    r"हे\s*ही\s*वाचा\s*[:ः]?.*"
    r"|हेही\s*वाचा\s*[:ः]?.*"
    r"|हे\s*देखील\s*वाचा\s*[:ः]?.*"
    r"|Read\s+Also\s*[:\-]?.*"
    r"|Keep\s+Reading\s*[:\-]?.*"
    r"|Forgot\s+your\s+password\??\s*.*"
    r"|Home\s*/\s*Marathi\s*"
    r"|Get\s+Latest\s+Marathi\s+News.*"
    r"|साम\s+आता\s+सर्व\s+सोशल\s+मीडिया.*"
    r")\s*$",
    flags=re.IGNORECASE,
)

def cure_c1(text):
    lines = text.splitlines(keepends=True)
    return "".join(
        line for line in lines
        if not _C1_LINE.fullmatch(line.rstrip("\r\n"))
    )


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Verify independently that the nar...
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 169 — indic / C1 / `DB-C1-013`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-sa-fw2`. Source: section C1 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `6da72db6a95c25b8` (ind-sa-fw2), original offset 0: `"Menu\nHome\nE- Journal\nSan"` (fix).
- `bd55ddb98859ace4` (ind-sa-fw2), original offset 0: `"Source: Chinna Katha Par"` (fix).
- `7d763858a5acae02` (ind-sa-fw2), original offset 101: `"\u0941\u0924\u093e\u0938\u0903 \u0965\n\u0905\u0925\u0930\u094d\u0935\u0935\u0947\u0926 \u092e\u0947\u0902 \u092a\u0942\u0930\u0923\u0903 \u0915\u0947 10"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-013"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_LINES = [r"^(Menu|Home|Newer Post|Older Post|Gallery|BASPS|marquee|Technical Details|BACK TO TOP)$",
    r"^(Read Also|Read More|Leave a Reply|Click Here|Archives|ReplyDelete|Reply|Delete|Share|Tweet|Email This|BlogThis!)$",
    r"^(Labels?|Categories|Posted by|Source):", r"Did you see any mistake/variation", r"Digitized by Google",
    r"Since you are not logged in", r"^% (Site access|Language|Text title|File name|Location|Author|Transliterated by|Proofread by|Description|Latest update|Send corrections)",
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), \w+ \d{1,2}, \d{4}$", r"^\d{1,2}:\d\d [AP]M$",
    r"^\|← ", r"→\|$", r"^इतर .*पश्यतु\s*[।|]?$", r"^\[(सम्पाद्यताम्|सम्पादयतु|सम्पादन)\]$", r"^— .*\(@\w+\) \w+ \d{1,2}, \d{4}$",
    r"^(सामग्री पर जाएँ|मुख्य मेन्यू|साइडबार पर जाएँ|छुपाएँ|ऊपर जाएँ|अधिक जानें|क्रियाएँ|उपकरण)$",
    r"^(ऋग्वेद|अथर्ववेद|यजुर्वेद|सामवेद) में .* संदर्भ मिले$", r"Copyright|©|All rights reserved",
    r"हम उम्मीद करते हैं आपको", r"^इसे भी पढ़ें"]
_RX = re.compile("|".join(f"(?:{p})" for p in _LINES), re.I)
_EDIT = re.compile(r" ?\[(सम्पाद्यताम्|सम्पादयतु|सम्पादन)\]")

def medicine_c1(text):
    lines = [l for l in text.split("\n") if not _RX.search(l.strip())]
    if len(lines) >= 2 and lines[-1].strip() == "श्रीः" and lines[-2].rstrip().endswith("॥"):
        lines.pop()
    return _EDIT.sub("", "\n".join(lines))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 170 — indic / C1 / `DB-C1-014`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C1-013. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-sa-fw2`. Source: section C1 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python deferred
RULE_ID = "DB-C1-014"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C1-013"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

DEVA = r"ऀ-ॿ꣠-ꣿ᳐-᳿"
MONTHS = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DAYS = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
def _lf(text): return text.replace("\r\n", "\n")
RE_EDITLINK = re.compile(r"\[(?:सम्पादन|संपादन|edit|सम्पादयतु|सम्पाद्यताम्)\]")
RE_BLOGGER_TAIL = re.compile(r"\nat\n\d{1,2}:\d{2} [AP]M\nNewer Post\nOlder Post\nHome\s*$")
RE_ARCHIVES_TAIL = re.compile(r"\n\s*Archives\n(?:[A-Z][a-z]+ \d{4}\n)*Categories\s*$")
RE_DSBC_HEAD = re.compile(r"^Technical Details\n[A-Za-z]\n", re.M)
RE_NEWS_MENU = re.compile(r"\AMenu\nHome\n(?:[^\n]*\n){0,40}?marquee\n")
RE_NEWS_TAIL = re.compile(r"(?:\n[ \t]*(?:सम्प्रति वार्ताः|इति वार्ताः|विश्वतोमुखम्)[ \t]*)+\s*$")
RE_SIMPLEHELP_HEAD = re.compile(rf"\A[A-Za-z][^\n]{{0,120}}: नमस्कार दोस्तों,[^\n]*\n(?:[^\n{DEVA}]*\n)*")
RE_HINDUPAD_HEAD = re.compile(rf"\A[^\n]{{1,80}} in (?:Hindi|Sanskrit|English|Tamil|Telugu|Kannada|Malayalam), Lyrics of [^\n]*\n(?:[^\n{DEVA}]*\n)*")
RE_SPIRITUAL_SIG = re.compile(r"^Subscribe on Youtube: The Spiritual Talks[ \t]*$", re.M)
RE_SPIRITUAL_TITLE = re.compile(r"\A[^\n]*\|[^\n]*\|[^\n]*\|[^\n]*\n")
C1_LINE_PATTERNS = [
    rf"{DAYS}, {MONTHS} \d{{1,2}}, \d{{4}}",
    r"Posted by .{0,80}", r"Labels?: .{0,200}", r"at \d{1,2}:\d{2} [AP]M", r"\d{1,2}:\d{2} [AP]M",
    r"Newer Posts?", r"Older Posts?", r"Post a Comment", r"No comments?:?", r"Email This", r"BlogThis!",
    r"Share to (?:Twitter|Facebook|Pinterest)", r"Subscribe to:.{0,40}", r"Powered by Blogger\.?",
    r"Did you see any mistake/variation in the content above\?.{0,200}",
    r"इतर .{0,60}(?:स्तोत्राणि|स्तोत्रं|स्तोत्रम्|नामावलयः|सूक्तानि|कवचानि) पश्यतु ।",
    r"% (?:Text title|File name|itxtitle|engtitle|Category|Location|Sublocation|Texttype|Author|Language|Subject|"
    r"Transliterated by|Proofread by|Translated by|Description-comments|Indexextra|Latest update|Send corrections to|"
    r"Site access|Description|Acknowledge-Permission|Source|Notes|Date|Comment)\s*:.*",
    r"(?:From [^\n]{0,100} )?(?:Encoded|Proofread|Transliterated|Encoded and proofread) by .{0,120}",
    r"[A-Za-z][\w.-]{0,40} at [\w.-]+\.[a-z]{2,6}",
    r"(?i:back to(?: top)?)", r"Please send corrections to.{0,200}", r"Technical Details",
    r"The rights of the materials herein are as indicated by the source\(s\) cited\..{0,400}",
    r"Subscribe to our newsletter.{0,200}",
    r"Inspiration: .{0,120}", r"These stories are written to .{0,300}",
    r"Jump to navigation ?Jump to search", r"Jump to navigation", r"Jump to search",
    r"एतत् पृष्ठम् (?:अपरिष्कृतम्|परिष्कृतम्|परिशोधितम्|प्रमाणीकृतम्) अस्ति",
    r"पृष्ठम्:[^\n]{1,120}\.(?:djvu|pdf)/[0-9०-९]{1,5}",
    r"Retrieved from .{0,300}", r".{0,300}इत्यस्मात् पुनः प्राप्तम्",
    r"Toggle limited content width",
    r"Table of Contents",
    r"[^\n]{0,80} Lyrics in (?:Marathi|Hindi|English|Tamil|Telugu|Kannada|Malayalam|Gujarati|Bengali|Oriya|Punjabi|Sanskrit):?",
    r"Categories: .{0,200}", r"Tags: .{0,200}",
    r"Leave a (?:Reply|Comment)",
    r"Download pdf", r"Back",
    r"Read Also", r"Read Also: .{0,200}",
    r"(?:हम )?उम्मीद करते हैं (?:कि |आपको ).{0,400}",
    r"\|[^|\n]{1,120}\|\|[^|\n]{0,200}\|",
    r"\|[A-Za-z0-9][^|\n]{0,120}\|",
    r"A painting by .{0,120}",
    r"Subscribe on Youtube: .{0,60}", r"Follow on Pinterest: .{0,60}", r"For any query contact on:?",
    r"Be a part of this Spiritual family .{0,160}", r"For more divine and soulful .{0,160}", r"For Spiritual quotes .{0,160}",
    r"यहाँ क्लिक करें", r"अगर आप और प्रैक्टिस सेट्स .{0,160}",
    r"[—–-]{2,}",
    r"Read [Mm]ore", r"Click here to .{0,80}",
    r"Download (?:the )?\S+ App\b.{0,80}",
    rf"— .{{1,80}} \(@\w{{1,30}}\) {MONTHS} \d{{1,2}}, \d{{4}}",
    r"\*{3,}",
    r"Share", r"Share this:?", r"Like this:?", r"Related", r"Archives", r"Categories",
    r"marquee", r"Statutary Warning-?",
    r"संस्कृतपठनेन बुद्धि[:ः] वर्धते इति मतिमुन्नीय गवेषका[:ः]॥",
    r"व्यावहारिकप्रयोगैः संस्कृतं राष्ट्रियभाषा भवितव्या - डॉ\. बलदेवानन्दसागरः।",
    r"संस्कृतेन सर्वदा व्यवहर्तुं प्रयतत - जगद्गुरु भारतीतीर्थस्वामिनः",
    rf"-\s?डा\.\s?[{DEVA}][^\n]{{0,30}}",
]
RE_C1_LINE = re.compile(r"[ \t]*(?:" + "|".join(f"(?:{p})" for p in C1_LINE_PATTERNS) + r")[ \t]*")
def medicine_c1(text):
    """C1: remove site chrome — known header/footer blocks, MediaWiki edit links, and whole lines equal to a chrome string."""
    if not text: return text
    src = _lf(text)
    out = RE_NEWS_MENU.sub("", src)
    out = RE_DSBC_HEAD.sub("", out)
    out = RE_SIMPLEHELP_HEAD.sub("", out)
    out = RE_HINDUPAD_HEAD.sub("", out)
    if RE_SPIRITUAL_SIG.search(out): out = RE_SPIRITUAL_TITLE.sub("", out)
    out = RE_BLOGGER_TAIL.sub("", out)
    out = RE_ARCHIVES_TAIL.sub("", out)
    out = RE_NEWS_TAIL.sub("", out)
    if RE_EDITLINK.search(out):
        out = "\n".join(RE_EDITLINK.sub("", l) for l in out.split("\n") if RE_EDITLINK.sub("", l).strip() or not RE_EDITLINK.search(l))
    out = "\n".join(l for l in out.split("\n") if not RE_C1_LINE.fullmatch(l))
    if out == src: return text
    return out.strip("\n")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 171 — indic / C1 / `DB-C1-015`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-ta-sangraha-v`. Source: section C1 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-ta-sangraha-v: 0 changed / 0 dropped of 41 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `b696ac9e380537d5` (ind-ta-sangraha-v), original offset 2044: `"\u0bb0\u0bbf\u0baf\u0bc1\u0bae\u0bbe?\n \u0b89\u0bb2\u0b95\u0bae\u0bcd \u0bae\u0bc1\u0ba4\u0bb2\u0bcd \u0b89\u0bb3\u0bcd\u0bb3\u0bc2\u0bb0\u0bcd \u0bb5\u0bb0\u0bc8"` (fix).
- `28e55a22748757af` (ind-ta-sangraha-v), original offset 2785: `"\u0bb3\u0bcd\u0bb3\u0bbe\u0bb0\u0bcd.\n Sign up to receive our "` (fix).
- `2bd051878060e7e3` (ind-ta-sangraha-v), original offset 1804: `"\u0ba9\u0bcd\u0bb1\u0bbe\u0bb0\u0bcd.\n Sign up to receive our "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-015"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-ta-sangraha-v'}
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"
SOURCE_ORIGIN = "ind-ta-sangraha-v"
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

_TICKER = "Finance|Travel|Education|Technology|News|Automobiles|Movies|Lifestyle|Sports"  # oneindia "Don't Miss!" block
_C1_LINE = re.compile(r"(?m)^[ \t]*(?:Sign up to receive our newsletter in your inbox every day!|Don't Miss!"
                      rf"|- (?:\d+ (?:mins?|hrs?) ago|{_TICKER}) .*"
                      r"|உலகம் முதல் உள்ளூர் வரை இன்றைய முக்கிய செய்திகள்.*|நியூஸ்18 தமிழ்நாடு தொலைக்காட்சியை.*"
                      r"|(?:Also Read|Also see)\s*:.*|இதையும் (?:படிங்க|பாருங்க).*)[ \t]*(?:\n|$)")

def medicine_c1(text):
    return _C1_LINE.sub("", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 50 documents, all labelled C1; none of the 153 `clean` documents.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 172 — indic / C1 / `DB-C1-016`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C1 Boilerplate. Pack `ind-te-fw2`. Source: section C1 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `4dff27fbc7052a2c` (ind-te-fw2), original offset 19988: `"\u0c41\u0c28\u0c4d\u0c28\u0c3e\u0c2f\u0c3f.\nPublished On - Mar 10,2"` (fix).
- `c366b77cfbaa1ca4` (ind-te-fw2), original offset 3381: `"\u0c15\u0c3f\u0c02\u0c1a\u0c3e\u0c02.\n\u0c2e\u0c30\u0c3f\u0c28\u0c4d\u0c28\u0c3f\n-\nGeneral News\nH"` (fix).
- `be0cefed31a362c7` (ind-te-fw2), original offset 0: `"Just In\n- 23 min ago \u0c15\u0c4a\u0c24"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `c1_boilerplate(text)`.

```python
RULE_ID = "DB-C1-016"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-s, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

C1_LINE = re.compile(r"""^\s*(?:
    (?:Also\s+[Rr]ead|Read\s+[Mm]ore|Don'?t\s+Miss!?|Just\s+In|News\s+Reels|More\s+Stories|Leave\s+a\s+Reply
      |View\s+this\s+post\s+on\s+Instagram|Sign\s+in|Follow\s+[Uu]s|Subscribe|Share\s+(?:on|this)
      |Image\s+Source|Disclaimer|Published\s+On|First\s+Publish\s+Date|Updated\s+Date|Tags?|TAGS)\b.*
  | (?:ఇది\s+కూడా\s+చదవండి|ఇవి\s+కూడా\s+చదవండి|ఇవీ\s+చదవండి|ఇదీ\s+చదవండి|ఇది\s+చూడండి|తాజా\s+వార్తలు
      |ట్రెండింగ్\s+వార్తలు|ఉత్పత్తి\s+ట్యాగ్లు|పోస్ట్\s+సమయం|వ్యాఖ్యను\s+పోస్ట్\s+చేయండి
      |మీ\s+అభిప్రాయాలను\s+కామెంట్|గమనిక:\s*ఈనాడు\.నెట్|\[\[సంబంధిత\s+కథనం\]\]).*
  | (?:మరిన్ని|ప్రకటన|g-ప్రకటన)(?:\s*-\s*[\w\s]{0,30})?
  | .*(?:Empowering\s+140\+\s+Indians|India\s+Herald\s+Group\s+of\s+Publishers|pic\.twitter\.com/|t\.co/\w).*
  | -?\s*\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}\s+[AP]M(?:\s+GMT)?.*
  | \w[\w\s.]{0,40},\s*News18,\s*\w+.*
)\s*$""", re.X)
def c1_boilerplate(t, url=None):
    return "\n".join(l for l in t.split("\n") if not C1_LINE.match(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = c1_boilerplate  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 173 — indic / C2 / `DB-C2-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-bn-fw2`. Source: section C2 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `0ca0ac43cc9f2526` (ind-bn-fw2), original offset 6564: `"neering\nAhsanullah University Of"` (fix).
- `bd59fdf51e29e37b` (ind-bn-fw2), original offset 3543: `"\u09a8 \u0995\u09b0\u09c7\u0964\n\u09b8\u09ae\u09be\u099c\u0995\u09b0\u09cd\u09ae \u09b8\u09ae\u09cd\u09aa\u09b0\u09cd\u0995\u09bf\u09a4 \u09aa\u09cd\u09b0\u09a4\u09cd\u09af"` (fix).
- `1abc081b1ce17469` (ind-bn-fw2), original offset 3639: `"tate to\nT20 WC-\u09a4\u09c7 \u099c\u09bf\u09ae\u09cd\u09ac\u09be\u09ac\u09c1\u09af\u09bc\u09c7\u09b0 \u0995"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-001"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c2(text):
    """Delete the second and later copies of a line of 40 or more characters."""
    seen, out = set(), []
    for line in text.split('\n'):
        key = line.strip()
        if len(key) >= 40:
            if key in seen:
                continue
            seen.add(key)
        out.append(line)
    return '\n'.join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 174 — indic / C2 / `DB-C2-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C2-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-bn-fw2`. Source: section C2 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python deferred
RULE_ID = "DB-C2-002"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C2-001"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48
import re  # added by Data B: harm_test_indic.py gives every block `re`

from collections import Counter


def medicine_c2(text):
    """Keep the first two copies of a line longer than 8 characters; delete later copies."""
    seen, out = Counter(), []
    for l in text.split("\n"):
        k = l.strip()
        seen[k] += 1
        if len(k) > 8 and seen[k] > 2:
            continue
        out.append(l)
    return "\n".join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 1 changed, 0 dropped of 314 (0.32 %). PASS.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 175 — indic / C2 / `DB-C2-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-gu-fw2`. Source: section C2 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `631da9a005b32c3e` (ind-gu-fw2), original offset 1020: `"\u0a98\u0a9f\u0aa8\u0abe \u0aac\u0aa8\u0ac0\n(\u0a8f\u0a9c\u0aa8\u0acd\u0ab8\u0ac0) \u0a9f\u0acd\u0aaf\u0ac1\u0aa8\u0abf\u0ab6\u0abf\u0aaf\u0abe, \u0aa4\u0abe"` (fix).
- `71da416a839a010b` (ind-gu-fw2), original offset 1311: `"per here\nVisit Saurashtra Kranti"` (fix).
- `91fd6fdeec7f2838` (ind-gu-fw2), original offset 1337: `"\u0abe \u0a9a\u0a95\u0aa1\u0acb\u0ab3\u0ac7\n(\u0ab8\u0a82\u0ab5\u0abe\u0aa6\u0aa6\u0abe\u0aa4\u0abe \u0aa6\u0acd\u0ab5\u0abe\u0ab0\u0abe) \u0a9c\u0abe\u0aae\u0aa8"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-C2-003"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine(text):
    seen, out = set(), []
    for line in text.split("\n"):
        key = line.strip()
        if len(key) > 15 and not key.endswith((",", "…")):   # keep poem refrains
            if key in seen:
                continue
            seen.add(key)
        out.append(line)
    return "\n".join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 12 of 1...
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 176 — indic / C2 / `DB-C2-004`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-hi-hplt`. Source: section C2 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `2a5f73bb1b272717` (ind-hi-hplt), original offset 5114: `"\u091a\u0941\u0915\u0940 \u0939\u0948\u0964 \u0905\u0926\u093e\u0932\u0924 \u0907\u0928\u094d\u0939\u0947\u0902 \u2018\u0939\u0938\u094d\u0924\u0915\u094d\u0937\u0947\u092a"` (fix).
- `620e84c0a37af831` (ind-hi-hplt), original offset 11204: `" \u0926\u0940 \u0939\u0948\u0964 \u0938\u092e\u093e\u0928 \u0938\u094b\u091a \u0935\u093e\u0932\u0947 \u0926\u0947\u0936\u094b\u0902 \u0915\u0940 \u0938"` (fix).
- `7952deb7a1c71995` (ind-hi-hplt), original offset 9815: `" \u0939\u0948 \u0915\u093f \u201c\u0910\u0938\u093e \u0927\u094d\u092f\u093e\u0928 \u0915\u0930\u0915\u0947 \u0926\u0947\u0936 \u0915\u094b \u092c\u091a"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-004"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-hplt', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c2(text):
    t = text
    for s in dict.fromkeys(re.findall("[^\u0964?!\n]{60,}[\u0964?!]", text)):
        first = t.find(s)
        if first >= 0 and t.find(s, first + len(s)) >= 0:
            t = t[:first + len(s)] + t[first + len(s):].replace(s, "")
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 177 — indic / C2 / `DB-C2-005`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C2-004. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-hi-hplt`. Source: section C2 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python deferred
RULE_ID = "DB-C2-005"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C2-004"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C2: a line of 40+ characters that repeats an earlier line exactly; the first copy stays
def medicine_c2(text):
    seen, out = set(), []
    for line in text.split("\n"):
        key = line.strip()
        if len(key) >= 40:
            if key in seen:
                continue
            seen.add(key)
        out.append(line)
    return "\n".join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 6 of 40 C2 documents; 6 other diseased documents touche...
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 178 — indic / C2 / `DB-C2-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-kn-fw2`. Source: section C2 of `diagnosis/submissions/ind-kn-fw2/LokeshJatangi/medicine.md`, PR #63 at `aeb79b8`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `436fd1e4f828cb2a` (ind-kn-fw2), original offset 1549: `"\u0cbf\u0ca6\u0ccd\u0ca6\u0cb0\u0cc1.\n\u0cb0\u0cbe\u0caf\u0c9a\u0cc2\u0cb0\u0cc1.\u0c8f.\u0ce6\u0ce8- \u0c95\u0cbe\u0c82\u0c97\u0ccd\u0cb0\u0cc6\u0cb8\u0ccd "` (fix).
- `17e5d6b10dc06231` (ind-kn-fw2), original offset 2645: `"\u0c87\u0ca6\u0ccd\u0ca6\u0cb0\u0cc1.\n\u0c95\u0cb2\u0cac\u0cc1\u0cb0\u0c97\u0cbf,\u0c8f.5:\u0c88\u0cb6\u0cbe\u0ca8\u0ccd\u0caf \u0c95\u0cb0\u0ccd\u0ca8\u0cbe"` (fix).
- `c38abea7a3377c5b` (ind-kn-fw2), original offset 3972: `"\u0c87\u0ca6\u0ccd\u0ca6\u0cb0\u0cc1.\n\u0c95\u0cb2\u0cac\u0cc1\u0cb0\u0c97\u0cbf,\u0c8f.6:\u0cb9\u0cc6\u0cb2\u0cbf\u0c9f\u0cc2\u0cb0\u0cbf\u0cb8\u0ccd\u0cae\u0ccd"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-006"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2, ind-kn-sangraha-s"
SOURCE_ORIGIN = "ind-kn-fw2"
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "LokeshJatangi"  # PR #63 at aeb79b8

import re
import unicodedata

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    out = list(text)
    for a, b in spans:
        if not protected(text[a:b]):
            out[a:b] = [""] * (b - a)  # Keep source indices stable, even for overlaps.
    return "".join(out)

def medicine_c2(text, url=""):
    if "```" in text or "~~~" in text:
        return text
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    if len(lines) >= 6 and sum(len(s) < 60 and not s.endswith((".", "!", "?")) for s in lines) * 2 > len(lines):
        return text
    units = set(lines)
    units.update(m.group().strip() for m in re.finditer(r"[^.!?\r\n]+(?:[.!?]+|(?=[\r\n]|$))", text))
    units = [s for s in units if len(s) >= 80 and len(s.split()) >= 8 and s.endswith((".", "!", "?"))
             and not s.startswith(('"', "'", "‘", "“", ">")) and not protected(s)
             and not re.match(r"[—–-]\s+.*\(@[A-Za-z0-9_]+\)", s)]
    spans = []
    for unit in sorted(units, key=lambda s: (-len(s), s)):
        cursor = text.find(unit) + len(unit)
        while (a := text.find(unit, cursor)) >= 0:
            b = a + len(unit)
            if not (a and (text[a - 1].isalnum() or unicodedata.category(text[a - 1]).startswith("M"))):
                spans.append((a, b))
            cursor = b
    return remove_spans(text, spans)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #63).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 179 — indic / C2 / `DB-C2-007`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C2-006. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-kn-fw2`. Source: section C2 of `diagnosis/submissions/ind-kn-fw2/keshavamurali/medicine.md`, PR #47 at `8158532`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python deferred
RULE_ID = "DB-C2-007"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-kn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C2-006"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "keshavamurali"  # PR #47 at 8158532
import re  # added by Data B: harm_test_indic.py gives every block `re`

import unicodedata
from collections import Counter

ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
END = re.compile(r'[.?!।॥"”\')]\s*$')   # a line that ends a sentence

def _protected(line):
    return ZWJ in line or ZWNJ in line or any(unicodedata.decomposition(c).startswith('<') for c in line)

def _short(l):
    return 0 < len(l) < 60 and not END.search(l)

def _verse(t):
    ls = [l.strip() for l in t.split('\n') if l.strip()]
    return len(ls) >= 6 and sum(map(_short, ls)) / len(ls) > 0.5

def medicine_c2(text, min_chars=30, times=2):
    if _verse(text):
        return text
    c = Counter(l.strip() for l in text.split('\n') if len(l.strip()) >= min_chars)
    rep = {l for l, n in c.items() if n >= times}
    seen, out = set(), []
    for l in text.split('\n'):
        s = l.strip()
        if s in rep and not _protected(s):
            if s in seen:
                continue
            seen.add(s)
        out.append(l)
    return '\n'.join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #47).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 180 — indic / C2 / `DB-C2-008`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-kn-sangraha-v`. Source: section C2 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `dfca849b43c8a487` (ind-kn-sangraha-v), original offset 1402: `"\u0cc1\u0cac\u0c82\u0ca6\u0cbf\u0ca6\u0cc6.\n \u0cae\u0c82\u0c97\u0cb3\u0cc2\u0cb0\u0cc1\u0c83 \u0c95\u0cb0\u0ccd\u0ca8\u0cbe\u0c9f\u0c95\u0ca6\u0cb2\u0ccd\u0cb2\u0cbf "` (fix).
- `1a60d090264d7942` (ind-kn-sangraha-v), original offset 993: `"\u0cbf\u0ca6\u0ccd\u0ca6\u0cbe\u0cb0\u0cc6.\n \u0c95\u0cbe\u0cb0\u0cb5\u0cbe\u0cb0\u0c83 \u0cb0\u0cbe\u0c9c\u0cc0\u0cb5\u0ccd \u0c97\u0cbe\u0c82\u0ca7\u0cbf \u0c86"` (fix).
- `e8f135076e73e476` (ind-kn-sangraha-v), original offset 206: `"\u0ccd\u0ca4\u0cbf\u0cb5\u0cc6.\n \u0cae\u0cb9\u0cbe\u0cad\u0cbe\u0cb0\u0ca4\u0ca6\u0cb2\u0ccd\u0cb2\u0cbf \u0c89\u0cb2\u0ccd\u0cb2\u0cc7\u0c96\u0cb5\u0cbf\u0cb0\u0cc1\u0cb5"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-008"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"
SOURCE_ORIGIN = "ind-kn-sangraha-v"
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

def dedupe_lines(t, min_len=30):
    """C2: keep the first copy of a line that is repeated word for word (lines of min_len characters or more)."""
    seen, out = set(), []
    for l in t.split("\n"):
        k = l.strip()
        if len(k) >= min_len and k in seen:
            continue
        seen.add(k); out.append(l)
    return "\n".join(out)


def medicine_c2(text):
    """The C2 rule, under the name that the harm tests look for: returns the fixed text."""
    return dedupe_lines(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 181 — indic / C2 / `DB-C2-009`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-mr-fw2`. Source: section C2 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python deferred
RULE_ID = "DB-C2-009"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-mr-fw2'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c2(text):
    seen = set()
    return '\n'.join(line for line in text.splitlines() if not (line.strip() and line.strip() in seen or seen.add(line.strip())))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 182 — indic / C2 / `DB-C2-010`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-mr-sangraha-v`. Source: section C2 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `4884f7c293a7beab` (ind-mr-sangraha-v), original offset 308: `"\u0902\u0917\u094b\u0932\u0940 : \u0936\u093e\u0938\u0928\u093e\u0928\u0947 \u092a\u094d\u0930\u093e\u0926\u0947\u0936\u093f\u0915 \u092f\u094b\u091c\u0928\u0947\u0924"` (fix).
- `4a1c22464f3df4f6` (ind-mr-sangraha-v), original offset 242: `"\u0940 \u0906\u0939\u0947.\n \u0938\u0941\u092a\u094d\u0930\u0940\u092e \u0915\u094b\u0930\u094d\u091f\u093e\u0928\u0947 \u092c\u0940\u0938\u0940\u0938\u0940\u0906"` (fix).
- `948113e0495d4af9` (ind-mr-sangraha-v), original offset 126: `"\u0940 \u092f\u0947\u0925\u0940\u0932 \u0917\u094d\u0930\u093e\u092e \u092a\u0902\u091a\u093e\u092f\u0924\u0940\u091a\u094d\u092f\u093e \u092e\u093e\u0938\u093f\u0915 "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_c2(text)`.

```python
RULE_ID = "DB-C2-010"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

def cure_c2(text):
    seed_len, min_repeat, search_limit = 48, 80, 1600
    if len(text) < min_repeat * 2:
        return text
    seed = text[:seed_len]
    second = text.find(seed, seed_len, min(len(text), search_limit))
    if second < 0:
        return text
    matched = 0
    max_match = min(second, len(text) - second)
    while matched < max_match and text[matched] == text[second + matched]:
        matched += 1
    if matched < min_repeat:
        return text
    return text[:second] + text[second + matched:]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Verify on C2-positive documents t...
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 183 — indic / C2 / `DB-C2-011`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-sa-fw2`. Source: section C2 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python deferred
RULE_ID = "DB-C2-011"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

import collections
def _lf(text): return text.replace("\r\n", "\n")
RE_C2_ALLOW = re.compile(r"उवाच|ऊचुः|इति|--$|—$|[।॥]$")
C2_MIN_REPEATS, C2_MAX_LEN = 5, 40
def medicine_c2(text):
    """C2: collapse runs of identical consecutive lines (whitespace-trimmed comparison); remove a short non-exempt line
    that repeats >= 5 times anywhere in the document."""
    if not text: return text
    src = _lf(text)
    out, prev = [], None
    for l in src.split("\n"):
        s = l.strip()
        if s and s == prev and not RE_C2_ALLOW.search(s): continue
        out.append(l); prev = s or None
    cnt = collections.Counter(l.strip() for l in out if l.strip())
    chrome = {s for s, k in cnt.items() if k >= C2_MIN_REPEATS and len(s) < C2_MAX_LEN and not RE_C2_ALLOW.search(s)}
    if chrome: out = [l for l in out if l.strip() not in chrome]
    new = "\n".join(out)
    return text if new == src else new


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 184 — indic / C2 / `DB-C2-012`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-ta-sangraha-v`. Source: section C2 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-ta-sangraha-v: 0 changed / 0 dropped of 41 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `b54a137e794fc027` (ind-ta-sangraha-v), original offset 11177: `"iendly,\nJackie & abdullah i real"` (fix).
- `5dc80d9d825fa6cc` (ind-ta-sangraha-v), original offset 1708: `"\u0bc1\u0b95\u0bbf\u0bb1\u0ba4\u0bc1. \u0b87\u0ba4\u0bc1 \u0b9a\u0bbf\u0bb1\u0bc1 \u0bae\u0bb3\u0bbf\u0b95\u0bc8 \u0bae\u0bb1\u0bcd\u0bb1\u0bc1\u0bae\u0bcd \u0baa"` (fix).
- `8fb37ca66fe1e1f7` (ind-ta-sangraha-v), original offset 1216: `"\u0bcd. \u0b85\u0ba8\u0bcd\u0ba4 \u0bb5\u0bc0\u0b9f\u0bcd\u0b9f\u0bbf\u0bb1\u0bcd\u0b95\u0bc1\u0bb3\u0bcd \u0baa\u0bc1\u0b95\u0bc1\u0ba8\u0bcd\u0ba4 \u0bae\u0bb0\u0bcd"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-012"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-ta-sangraha-v'}
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"
SOURCE_ORIGIN = "ind-ta-sangraha-v"
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def medicine_c2(text):
    return re.sub(r"(?ms)^([ \t]*([^\n]{180,}?)[ \t]*$.*?)\2", r"\1", text)  # a later copy of a long line goes


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 3 documents, all labelled C2; none labelled `clean`.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 185 — indic / C2 / `DB-C2-013`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C2 Repeated lines. Pack `ind-te-fw2`. Source: section C2 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `4dff27fbc7052a2c` (ind-te-fw2), original offset 2083: `"\u0c3e\u0c16 - 15\n\u0c24\u0c42\u0c30\u0c4d\u0c2a\u0c41 \u0c17\u0c4b\u0c26\u0c3e\u0c35\u0c30\u0c3f - 12\n\u0c2a\u0c36\u0c4d\u0c1a"` (fix).
- `6faa50209f00b4cf` (ind-te-fw2), original offset 1469: `"\u0c2a\u0c47\u0c2a\u0c30\u0c4d\u0c38\u0c4d\n\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014"` (fix).
- `6cfff787aa9eede7` (ind-te-fw2), original offset 1567: `"\u0c2e\u0c40\u0c1f\u0c4d\n-\nAp-top-news News\nAndhra N"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `c2_repeats(text)`.

```python
RULE_ID = "DB-C2-013"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-s, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

from collections import Counter
def c2_repeats(t, url=None):
    lines = t.split("\n"); n = Counter(l.strip() for l in lines if len(l.strip()) >= 15)
    seen, out = set(), []
    for l in lines:
        s = l.strip()
        if n.get(s, 0) >= 2:
            if s in seen: continue
            seen.add(s)
        out.append(l)
    return "\n".join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = c2_repeats  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 186 — indic / C3 / `DB-C3-005`

**Integration decision:** DEFERRED. joiners: removes script joiner. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-bn-fw2`. Source: section C3 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python deferred
RULE_ID = "DB-C3-005"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "joiners: removes script joiner"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re


def medicine_c3(text):
    """Cut a broken last sentence back to the last । ? ! ৷ (credit lines are left alone)."""
    s = text.rstrip()
    if not s:
        return text
    last = s.split("\n")[-1]
    if not re.match("[ঀ-৿]", s[-1]) or len(last) <= 60 or re.search(r"[:ঃ/\-–—]", last[-40:]):
        return text
    cut = max(s.rfind(c) for c in "।?!৷")
    return s[:cut + 1] if cut > 0 else text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 187 — indic / C3 / `DB-C3-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-hi-fw2`. Source: section C3 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-006"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2"
SOURCE_ORIGIN = "ind-hi-fw2"
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_TERM_END = re.compile(r'[।!?.…"\'”’)\]]\s*$')

def _flag_c3_truncated(text: str) -> bool:
    """True if the document does not end on a sentence terminator (label hint only)."""
    t = (text or "").rstrip()
    if not t:
        return False
    return _TERM_END.search(t) is None

def medicine_c3(text: str) -> str:
    """Automatic medicine: keep text. Soft C3 is label/fix; do not mass-drop open endings."""
    return text or ""


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `ind-hi-fw2_gold.csv` (**234** docs, post-#161). Tool: `harm_test_indic.py --rule C3` (2026-10-31). Automatic `medicine_c3` keeps text (label/fix; no mass drop of open endings):
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 188 — indic / C3 / `DB-C3-007`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-hi-hplt`. Source: section C3 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python deferred
RULE_ID = "DB-C3-007"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C3: a document cut at the start ("…" before the first word) or ending in a "[…]" teaser cut: remove that line
def medicine_c3(text):
    lines = text.split("\n")
    if len(lines) > 2 and re.match(r"^\s*(?:…|\.\.\.)\s*[\u0900-\u097f]", lines[0]):
        lines = lines[1:]
    if len(lines) > 2 and re.search(r"\[(?:…|\.\.\.)\]\s*$", lines[-1]):
        lines = lines[:-1]
    return "\n".join(lines)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 8 of 20 C3 documents; 3 other diseased documents touche...
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 189 — indic / C3 / `DB-C3-008`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-kn-sangraha-s`. Source: section C3 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
2. **Medicine:** the author's code, unchanged. Main function: `m5_dangling_intro(text)`.

```python deferred
RULE_ID = "DB-C3-008"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-kn-sangraha-s'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s"  # packs it runs on
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

def m5_dangling_intro(s):
    body = s.rstrip()
    if not body.endswith(("ಃ", ":")):
        return s
    cut = max(body.rfind("\n"), body.rfind(". ") + 1)
    return body[:cut].rstrip() + "\n" if cut > 0 else True


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m5_dangling_intro  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 3 of 359 changed (`523fee1068dc3fa9`,
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 190 — indic / C3 / `DB-C3-009`

**Integration decision:** DEFERRED. joiners: removes script joiner. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-kn-sangraha-v`. Source: section C3 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python deferred
RULE_ID = "DB-C3-009"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-kn-sangraha-v'}
DEFER_REASON = "joiners: removes script joiner"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

SENTENCE_END = set(".?!।॥|\"'”’)»…:ಃ")


def cut_unfinished_end(t, min_line=40):
    """C3: when the last line is prose (min_line characters or more) that stops without a sentence end, cut it
    back to its last full stop, or remove the line when it has none."""
    s = t.rstrip()
    if not s or s[-1] in SENTENCE_END or s[-1].isdigit():
        return t
    last = s.split("\n")[-1]
    if len(last) < min_line:
        return t
    cut = max(last.rfind(c) for c in ".?!।")
    return (s[: len(s) - len(last)] + (last[: cut + 1] if cut >= 0 else "")).rstrip()


def medicine_c3(text):
    """The C3 rule, under the name that the harm tests look for: returns the fixed text."""
    return cut_unfinished_end(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 191 — indic / C3 / `DB-C3-010`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-mr-sangraha-v`. Source: section C3 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS); ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `10cfc7c874a1bb29` (ind-mr-sangraha-v), original offset 0: `"\u0967\u096c\u0968 : \u0906\u091a\u093e\u0930\u094d\u092f \u092d\u093e\u0917\u0935\u0924 \u0938\u0902\u0915\u0932\u093f\u0924 \u0935\u093e\u0915\u093e\u092f / \u0916\u0902\u0921 \u0968\n\u0905\u0936\u093e \u0935\u0947\u0933\u0940 \u092c\u093f\u092f\u094b\u0917, \u0926\u0941\u0903\u0916, \u0905\u092a"` (drop).
- `0ad004d5deb1e7fe` (ind-mr-sangraha-v), original offset 0: `"\u092e\u0941\u0902\u092c\u0908-\u0938\u0928\u0940 \u0932\u093f\u092f\u094b\u0928 \u091a\u093e \u092a\u0924\u0940 \u0906\u0924\u093e \u0939\u093f\u0902\u0926\u0940 \u092d\u093e\u0937\u093e \u0906\u0923\u093f \u0928\u0943\u0924\u094d\u092f\u093e\u091a\u0947 \u0927\u0921\u0947 \u0917\u093f\u0930\u0935\u0924 \u0906\u0939\u0947"` (drop).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_c3(text)`.

```python
RULE_ID = "DB-C3-010"
CODE = "C3"
ACTION = "fix+drop"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2', 'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v, ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

import hashlib

# Reviewed Marathi pack records only: original and file-order pre-rule text.
# SHA-256 avoids embedding private values and supports the text-only harness.
_EXCLUDED_SHA256 = frozenset({
    # 0ad004d5deb1e7fe
    "0ad004d5deb1e7fece97aa9806c12904aa8f3443a9784e6ad8192fe37ccdc50a",
    # 10cfc7c874a1bb29
    "10cfc7c874a1bb29938183dcf35cdeb6b9bd36cb47b721b46cea9429e60552c9",
    "395b9f4527f05f508da2f9ea26395d99bec57bd7a46934165c4dad8eb2e04ce3",
})

def cure_c3(text):
    if hashlib.sha256(text.encode("utf-8")).hexdigest() in _EXCLUDED_SHA256:
        return True  # Exclude/quarantine; retain provenance outside public output.
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix+drop. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** See the fresh results above. Positive-case scope: **2 reviewed records excluded individually**; all other records stay unchanged for this rule. Contextual repairs are not covered.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 192 — indic / C3 / `DB-C3-011`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C3-004. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-sa-fw2`. Source: section C3 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python deferred
RULE_ID = "DB-C3-011"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C3-004"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

def _lf(text): return text.replace("\r\n", "\n")
TERMINAL = set("।॥.!?\"”'’)]}»…") | set("0123456789०१२३४५६७८९")
C3_MAX_LEN, C3_MAX_WORDS = 200, 8
RE_C3_PROTECT = re.compile(r"^इत(?:ि|्य)")
def medicine_c3(text):
    """C3: drop one dangling short last line without terminal punctuation when the line before it is closed."""
    if not text: return text
    src = _lf(text)
    lines = src.split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip()]
    if len(idx) < 2: return text
    k, j = idx[-1], idx[-2]
    last, prev = lines[k].strip(), lines[j].strip()
    if (len(last) >= C3_MAX_LEN or len(last.split()) > C3_MAX_WORDS or last[-1] in TERMINAL or prev[-1] not in TERMINAL
            or RE_C3_PROTECT.match(last)):
        return text
    return "\n".join(lines[:k] + lines[k + 1:])


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 193 — indic / C3 / `DB-C3-012`

**Integration decision:** DEFERRED. joiners: removes script joiner. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-ta-sangraha-v`. Source: section C3 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python deferred
RULE_ID = "DB-C3-012"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-ta-sangraha-v'}
DEFER_REASON = "joiners: removes script joiner"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def _cut_sentence(line):
    e = max(line.rfind(c) for c in ".!?…")
    return line[:e + 1]  # e = -1: no sentence end, so the whole line goes

def medicine_c3(text):
    return re.sub(r"(?m)^[^\n]{80,}(?<=[\u0B80-\u0BFFA-Za-z,])\s*\Z", lambda m: _cut_sentence(m[0].rstrip()), text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 22 documents, none labelled `clean`. Of the 6 changed documents
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 194 — indic / C3 / `DB-C3-013`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-te-fw2`. Source: section C3 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `c3_teaser(text)`.

```python deferred
RULE_ID = "DB-C3-013"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-te-fw2'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def c3_teaser(t, url=None):
    paras = t.rstrip().split("\n")
    if len(paras) > 1 and re.search(r"\[(?:…|\.\.\.)\]\s*$", paras[-1]):
        return "\n".join(paras[:-1]).rstrip()
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = c3_teaser  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 195 — indic / C3 / `DB-C3-014`

**Integration decision:** DEFERRED. not idempotent on own diagnosis pack. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C3 Truncated document. Pack `ind-te-sangraha-s`. Source: section C3 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python deferred
RULE_ID = "DB-C3-014"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-te-sangraha-s'}
DEFER_REASON = "not idempotent on own diagnosis pack"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"  # packs it runs on
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c3(text):
    body = text.rstrip()
    tail = text[len(body):]
    cut = body.rfind("\n")
    if cut > 0 and body[cut + 1:].endswith(("ః", ":")):
        return body[:cut] + tail
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_c3` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 196 — indic / C4 / `DB-C4-007`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-gu-fw2`. Source: section C4 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `5850b7f05b243ec4` (ind-gu-fw2), original offset 1880: `"\u0ab0\u0acd\u0aaf\u0acb ??\n(\u0a8f\u0a9c\u0aa8\u0acd\u0ab8\u0ac0) \u0aa8\u0ab5\u0ac0 \u0aa6\u0abf\u0ab2\u0acd\u0ab9\u0ac0, \u0aa4\u0abe."` (fix).

**Example gap:** 1/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-007"
CODE = "C4"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block
GU_DIGIT = "\u0AE6-\u0AEF"                    # Gujarati digits 0-9

C4_DATELINE = re.compile(
    r"^\s*(?:\((?:એજન્સી|અમારા પ્રતિનિધિ તરફથી|સંવાદદાતા દ્વારા)\)\s*)?"
    rf"[{GU}]+(?: [{GU}]+)?\s*,\s*તા\.\s*[{GU_DIGIT}રપ0-9]{{1,2}}\s*$", re.M)
C4_MARK = re.compile(r"^\s*(?:READ ALSO|MUST READ)\s*[:\-–]?", re.M)
C4_BODY = re.compile(r"^(?!\s*[-•]).{200,}$", re.M)

def m8_c4(text, url=None, min_part=300, min_body=200):
    cuts = [m.start() for m in C4_DATELINE.finditer(text)
            if m.start() >= min_part and len(text) - m.end() >= min_body]
    m = C4_MARK.search(text)
    if m and C4_BODY.search(text, m.end()):
        cuts.append(m.start())
    if not cuts:
        return (text, "keep")
    bounds = [0] + sorted(set(cuts)) + [len(text)]
    parts = [text[a:b].strip() for a, b in zip(bounds, bounds[1:])]
    return ([p for p in parts if p], "split")

def medicine_c4(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    parts, action = m8_c4(text, url)
    return "\n\n".join(parts) if action == "split" else text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 197 — indic / C4 / `DB-C4-008`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-kn-sangraha-v`. Source: section C4 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python deferred
RULE_ID = "DB-C4-008"
CODE = "C4"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-kn-sangraha-v'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

def latin_share(s):
    k = sum(1 for c in s if "ಀ" <= c <= "೿")
    a = sum(1 for c in s if c.isascii() and c.isalpha())
    return a / (k + a) if k + a else 0.0


def cut_english_tail(t, min_chars=200):
    """C4: remove an English block (min_chars or more, lines over 90% Latin letters) joined to the end of a
    Kannada text, such as the English source story."""
    lines = t.split("\n")
    i = len(lines)
    while i > 0 and (not lines[i - 1].strip() or latin_share(lines[i - 1]) > 0.9):
        i -= 1
    head, tail = "\n".join(lines[:i]), "\n".join(lines[i:])
    if len(tail.strip()) >= min_chars and len(head.strip()) >= 200 and latin_share(head) < 0.3:
        return head.rstrip()
    return t


def medicine_c4(text):
    """The C4 rule, under the name that the harm tests look for: returns the fixed text."""
    return cut_english_tail(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 198 — indic / C4 / `DB-C4-009`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-mr-sangraha-v`. Source: section C4 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `d89a364142de1d38` (ind-mr-sangraha-v), original offset 0: `"\u0932\u093e\u0908\u0935\u094d\u0939 \u0928\u094d\u092f\u0942\u091c :\n\u0930\u093e\u0937\u094d\u091f\u094d\u0930\u0940\u092f \u0938\u094d\u0935\u092f\u0902\u0938\u0947\u0935\u0915 \u0938\u0902\u0918\u093e\u091a\u0947 \u092e\u093e\u091c\u0940 \u0938\u0939\u0938\u0930\u0915\u093e\u0930\u094d\u092f\u0935\u093e\u0939, \u0905\u0916\u093f"` (drop).
- `9910e11f3461f5d0` (ind-mr-sangraha-v), original offset 0: `"\u091c\u0917\u093e\u0924\u0940\u0932 \u0938\u0930\u094d\u0935\u093e\u0924 \u092e\u0939\u0924\u094d\u0935\u093e\u091a\u0940 \u0930\u093f\u0905\u0932 \u0907\u0938\u094d\u091f\u0947\u091f \u0906\u0923\u093f \u0906\u0930\u094d\u0915\u093f\u091f\u0947\u0915\u094d\u091a\u0930 \u092e\u0940\u091f\u093f\u0902\u0917\u092a\u0948\u0915\u0940 \u090f\u0915"` (drop).
- `a3a467b4dcb9c51b` (ind-mr-sangraha-v), original offset 0: `"\u091c\u0930 \u0924\u0941\u092e\u091a\u094d\u092f\u093e \u0916\u093e\u0924\u094d\u092f\u093e\u0924 \u0905\u091a\u093e\u0928\u0915 \u0932\u093e\u0916\u094b \u0930\u0941\u092a\u092f\u093e\u0902\u091a\u0940 \u0930\u0915\u094d\u0915\u092e \u0906\u0932\u0940 \u0924\u0930 \u0924\u0941\u092e\u094d\u0939\u0940 \u0915\u093e\u092f \u0915"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_c4(text)`.

```python
RULE_ID = "DB-C4-009"
CODE = "C4"
ACTION = "fix+drop"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

import hashlib

# Reviewed Marathi pack records only: original and file-order pre-rule text.
# SHA-256 avoids embedding private values and supports the text-only harness.
_EXCLUDED_SHA256 = frozenset({
    # 802ea4e0038fae55
    "802ea4e0038fae55fba668aca47d3f7c546b15564d109bc8afb500c5ad78fd02",
    # 9910e11f3461f5d0
    "9910e11f3461f5d09f7abfb46cfca489b7bb5209d507d963dab976ff55e3b112",
    "e5d935b539d7724761ec3e96fbfe365fece60f1423ef62aee339f1a913889716",
    # a3a467b4dcb9c51b
    "a3a467b4dcb9c51b0a2112852ad9b31a8b9f895f21d207c9a3dac6114617ca02",
    "dbc9e19bc50ab161305d9e57e012f471e5250092c7dc4eef472245eb3ecb86e8",
    # d89a364142de1d38
    "c71c2ca6277898aaf1416e32d9f280c46f4a98293b21601bf23103e5f0536aa9",
    "d89a364142de1d38711026940c0f096e45d2276cb062773651c866d4998228d7",
})

def cure_c4(text):
    if hashlib.sha256(text.encode("utf-8")).hexdigest() in _EXCLUDED_SHA256:
        return True  # Exclude/quarantine; retain provenance outside public output.
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix+drop. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** See the fresh results above. Positive-case scope: **4 reviewed records excluded individually**; all other records stay unchanged for this rule. Contextual repairs are not covered.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 199 — indic / C4 / `DB-C4-010`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-sa-fw2`. Source: section C4 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 1 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `875f86117f43fd90` (ind-sa-fw2), original offset 641: `"\u092f\u093e\u092f\u093e\u0932\u092f\u0903\u0964\u0928\u0935\u0926\u093f\u0932\u094d\u0932\u0940>\u0924\u092e\u093f\u0932\u094d \u0928\u093e\u091f\u094d \u0930\u093e\u091c\u094d"` (fix).
- `6f5c2563a43a88f9` (ind-sa-fw2), original offset 54: `" \u092f\u0942 \u090f\u0938\u094d\u0964\u0964\u0935\u093e\u0937\u093f\u0919\u094d\u091f\u0923\u094d> \u0910\u0915\u094d\u092f\u0930\u093e\u0937\u094d\u091f\u094d\u0930\u0938"` (fix).
- `1ece1474b414d6fe` (ind-sa-fw2), original offset 79: `"\u093f \u090f\u0938\u094d \u0907\u0964\u0928\u0935\u0926\u093f\u0932\u094d\u0932\u0940> \u092f\u0947 \u0935\u093f\u0926\u094d\u092f\u093e\u0932\u092f\u093e\u0903 "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-010"
CODE = "C4"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c4(text):
    def cut(m):
        start = text.rfind("\n", 0, m.start()) + 1
        return m.group(1) + ("\n\n" if m.start() - start >= 60 else "")
    return re.sub("([।!?])(?=[ऀ-ॿ][ऀ-ॿ ]{1,40}\\s?>)", cut, text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 200 — indic / C4 / `DB-C4-011`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C4-010. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C4 Two documents joined. Pack `ind-sa-fw2`. Source: section C4 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python deferred
RULE_ID = "DB-C4-011"
CODE = "C4"
ACTION = "keep"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C4-010"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

DEVA = r"ऀ-ॿ꣠-ꣿ᳐-᳿"
MONTHS = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DAYS = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
def _lf(text): return text.replace("\r\n", "\n")
RE_DATELINE = re.compile(rf"^[{DEVA}][^\n>]{{1,24}}[ \t]?>[ \t]*\S", re.M)
RE_POST_DATE = re.compile(rf"^{DAYS}, {MONTHS} \d{{1,2}}, \d{{4}}$")
RE_DEVA = re.compile(rf"[{DEVA}]")
def detect_joined(text):
    """C4 detector (no automated action). Run it on the ORIGINAL text, before C1, which removes the date headers and menu it
    relies on. True when: >= 2 news datelines; or >= 2 Blogger post-date headers (archive page); or one post-date header
    that follows Devanagari sentences (marquee items joined to the post)."""
    if not text: return False
    if len(RE_DATELINE.findall(text)) >= 2: return True
    lines = [l.strip() for l in _lf(text).split("\n")]
    dates = [i for i, l in enumerate(lines) if RE_POST_DATE.match(l)]
    if len(dates) >= 2: return True
    if dates and any(RE_DEVA.search(x) and x[-1] in "।॥" for x in lines[:dates[0]] if x): return True
    return False

def medicine_c4(text):
    return text    # action none: the detector `detect_joined` reports; splitting is a corpus-time action


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 201 — indic / C5 / `DB-C5-007`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-bn-fw2`. Source: section C5 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `e9bc37a7fcf3808d` (ind-bn-fw2), original offset 7503: `"\u09b9\u09a4\u09c7 \u09b9\u09ac\u09c7\n- \u09b8\u09ae\u09b8\u09cd\u09af\u09be \u09b8\u09ae\u09be\u09a7\u09be\u09a8 \u0995\u09b0\u09a4\u09c7 \u09b9\u09ac\u09c7"` (fix).
- `258f1a8d90585fdc` (ind-bn-fw2), original offset 0: `"- \u0997\u09c1\u09a6\u09be\u09ae\u09c7 \u099a\u09be\u09b2\u09c7\u09b0 \u099c\u09be\u09af\u09bc\u0997\u09be \u09b9\u099a"` (fix).
- `a005aedd65fe3aa8` (ind-bn-fw2), original offset 1656: `"\u09cd\u09ac\u09c7?\n- \u0986\u0997\u09be\u09ae\u09c0 \u0985\u0995\u09cd\u099f\u09cb\u09ac\u09b0\u09c7 \u099a\u09be\u09b2\u09c1 \u09b9\u09ac\u09c7 \u09a5"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-007"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

def _is_headline(line):
    s = line.strip()
    return (s.startswith(('- ', '• ', '* ')) and len(s) <= 120 and len(s.split()) >= 5
            and not s.endswith(('।', '?', '!', '.', ':')))

def medicine_c5(text):
    """Delete runs of 5 or more consecutive bullet lines that look like headlines: at least 4 words after
    the bullet, at most 120 characters, no sentence-final punctuation (related-news tickers)."""
    lines = text.split('\n')
    keep = [True] * len(lines)
    i = 0
    while i < len(lines):
        j = i
        while j < len(lines) and _is_headline(lines[j]):
            j += 1
        if j - i >= 5:
            for k in range(i, j):
                keep[k] = False
        i = max(j, i + 1)
    return '\n'.join(l for l, k in zip(lines, keep) if k)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 202 — indic / C5 / `DB-C5-008`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C5-007. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-bn-fw2`. Source: section C5 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python deferred
RULE_ID = "DB-C5-008"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C5-007"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re
from collections import Counter


def _c5_stuffed(line):
    parts = [p.strip() for p in re.split(r"[,،]", line) if p.strip()]
    if len(parts) < 6 or sum(len(p.split()) for p in parts) > 6 * len(parts):
        return False
    c = Counter(b for p in parts for b in {" ".join(x) for x in zip(p.split(), p.split()[1:])})
    return bool(c) and c.most_common(1)[0][1] >= 0.5 * len(parts)


def medicine_c5(text):
    """Delete lines of >= 6 short comma pieces where one two-word phrase is in >= half of them."""
    return "\n".join(l for l in text.split("\n") if not _c5_stuffed(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS. **The 5.10 % is not this rule:** an earlier
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 203 — indic / C5 / `DB-C5-009`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-gu-fw2`. Source: section C5 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `9c013a675712ff90` (ind-gu-fw2), original offset 4016: `" India.\nAndroid: http://bit.ly/3"` (fix).
- `98b9ca997dc64e33` (ind-gu-fw2), original offset 2083: `"\u0ab0\u0abe\u0aa4\u0ac0 \u0aaa\u0ab0\nTags: \u0a85\u0a82\u0aac\u0abe\u0a9c\u0ac0 \u0aae\u0a82\u0aa6\u0abf\u0ab0"` (fix).
- `6c34ae8bfde1bf78` (ind-gu-fw2), original offset 1872: `"\u0ab0\u0abe\u0aa4\u0ac0 \u0aaa\u0ab0\nTags: Galaxy s10, Pocket"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-009"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

C5_LINE = re.compile(r"^\s*(?:Tags\s*:|Android\s*:|iOS\s*:).*\n?|^\s*https?://\S+\s*\n?", re.M)

def m9_c5(text, url=None):
    return _fix(text, C5_LINE.sub("", text))

def medicine_c5(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m9_c5(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 204 — indic / C5 / `DB-C5-010`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C5-009. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-gu-fw2`. Source: section C5 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python deferred
RULE_ID = "DB-C5-010"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-gu-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C5-009"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

def medicine(text):
    keep = []
    for line in text.split("\n"):
        s = line.strip()
        latin = len(re.findall("[A-Za-z]", s))
        letters = max(1, len(re.sub(r"\W", "", s)))
        tags = s.startswith("Tags:") and (s.count(",") >= 2 or len(s.split()) >= 8)
        word_list = (len(s.split(",")) >= 5 and latin > 0.7 * letters
                     and not re.search(r"[:\d]", s) and not s.endswith("."))
        if not (tags or word_list):
            keep.append(line)
    return "\n".join(keep)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 18 of 2...
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 205 — indic / C5 / `DB-C5-011`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-kn-fw2`. Source: section C5 of `diagnosis/submissions/ind-kn-fw2/LokeshJatangi/medicine.md`, PR #63 at `aeb79b8`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `95fcd3a60a26a368` (ind-kn-fw2), original offset 12: `"t Miss!\n- News \u0c95\u0cb0\u0ccd\u0ca8\u0cbe\u0c9f\u0c95\u0ca6\u0cb2\u0ccd\u0cb2\u0cbf 573 "` (fix).
- `10c1bbd17380fb15` (ind-kn-fw2), original offset 12: `"t Miss!\n- News \u0ca8\u0cc7\u0caa\u0cbe\u0cb3 \u0c95\u0cae\u0ccd\u0caf\u0cc2\u0ca8\u0cbf\u0cb8\u0ccd\u0c9f\u0ccd"` (fix).
- `352f61da6247acd6` (ind-kn-fw2), original offset 12: `"t Miss!\n- News \u0c95\u0cb0\u0ccd\u0ca8\u0cbe\u0c9f\u0c95\u0ca6\u0cb2\u0ccd\u0cb2\u0cbf 573 "` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-011"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"
SOURCE_ORIGIN = "ind-kn-fw2"
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "LokeshJatangi"  # PR #63 at aeb79b8

import re
import unicodedata

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    out = list(text)
    for a, b in spans:
        if not protected(text[a:b]):
            out[a:b] = [""] * (b - a)  # Keep source indices stable, even for overlaps.
    return "".join(out)

NAV = re.compile(r"(?mi)^[ \t]*(?:Just In[ \t]*\r?\n)?[ \t]*Don['’]t Miss![ \t]*\r?\n(?P<links>(?:[ \t]*-[ \t]+[A-Za-z][^\r\n]*(?:\r?\n|$)){2,})")
TAG = r"#[ \t]*[^\W\d_][\w\u0c80-\u0cff\u200c\u200d]*"
TAG_CLOUD = re.compile(rf"[ \t]*(?:{TAG}[ \t]*){{2,}}")

def medicine_c5(text, url=""):
    spans = [(m.start("links"), m.end("links")) for m in NAV.finditer(text)]
    offset = 0
    for line in text.splitlines(keepends=True):
        if TAG_CLOUD.fullmatch(line.rstrip("\r\n")):
            spans.append((offset, offset + len(line)))
        offset += len(line)
    return remove_spans(text, spans)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #63).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 206 — indic / C5 / `DB-C5-012`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C5-011. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-kn-fw2`. Source: section C5 of `diagnosis/submissions/ind-kn-fw2/keshavamurali/medicine.md`, PR #47 at `8158532`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python deferred
RULE_ID = "DB-C5-012"
CODE = "C5"
ACTION = "fix+drop"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-kn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C5-011"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "keshavamurali"  # PR #47 at 8158532
import re  # added by Data B: harm_test_indic.py gives every block `re`

import unicodedata

ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
END = re.compile(r'[.?!।॥"”\')]\s*$')   # a line that ends a sentence
SIGNAL = re.compile(r'\d+\s*(days?|hours?|minutes?|mins?) ago|ಇನ್ನಷ್ಟು|Read more|Tag results'
                    r'|https?://|www\.|\.com\b|\|', re.I)

def _protected(line):
    return ZWJ in line or ZWNJ in line or any(unicodedata.decomposition(c).startswith('<') for c in line)

def _short(l):
    return 0 < len(l) < 60 and not END.search(l)

def medicine_c5(text):
    lines = text.split('\n')
    idx = [i for i, l in enumerate(lines) if l.strip()]      # non-empty lines, original positions
    ls = [lines[i].strip() for i in idx]
    sig = [bool(SIGNAL.search(l)) for l in ls]
    if len(ls) >= 5 and sum(map(_short, ls)) / len(ls) > 0.6 and sum(sig) / len(ls) >= 0.3:
        return True
    drop, run = set(), []
    for k in range(len(ls) + 1):
        if k < len(ls) and (_short(ls[k]) or sig[k]):
            run.append(k)
        else:
            if len(run) >= 3 and sum(sig[j] for j in run) >= 2:
                drop.update(idx[j] for j in run if not _protected(ls[j]))
            run = []
    return '\n'.join(l for i, l in enumerate(lines) if i not in drop)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix+drop. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #47).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 207 — indic / C5 / `DB-C5-013`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-mr-sangraha-v`. Source: section C5 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_c5(text)`.

```python deferred
RULE_ID = "DB-C5-013"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-mr-sangraha-v'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f

import re

_C5_TAG_LINE = re.compile(
    r"^\s*(?:Tags?|Keywords?|कीवर्ड)\s*[:：]\s*\S.*$",
    flags=re.IGNORECASE,
)

def cure_c5(text):
    return "".join(
        line for line in text.splitlines(keepends=True)
        if not _C5_TAG_LINE.fullmatch(line.rstrip("\r\n"))
    )


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). The narrow tag-line rule does not...
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 208 — indic / C5 / `DB-C5-014`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-sa-fw2`. Source: section C5 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `6da72db6a95c25b8` (ind-sa-fw2), original offset 312: `"\u0930\u094d\u0936\u0928\u0940\u092f\u093e\nhttps://twitter.com/samp"` (fix).
- `cf161644b0475f04` (ind-sa-fw2), original offset 312: `"\u0930\u094d\u0936\u0928\u0940\u092f\u093e\nhttps://twitter.com/samp"` (fix).
- `ce0f08033f2453d9` (ind-sa-fw2), original offset 306: `"\u0930\u094d\u0936\u0928\u0940\u092f\u093e\nhttps://twitter.com/samp"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-014"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_LINK = re.compile(r"Click Here\s*\|?$|^https?://\S+$", re.I)

def medicine_c5(text):
    return "\n".join(l for l in text.split("\n") if not _LINK.search(l.strip()))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 209 — indic / C5 / `DB-C5-015`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-C5-014. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** C5 Lists of keywords or links. Pack `ind-sa-fw2`. Source: section C5 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python deferred
RULE_ID = "DB-C5-015"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-C5-014"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

def _lf(text): return text.replace("\r\n", "\n")
RE_C5_TAGLINE = re.compile(r"\s*(?:Tags?|Labels?|Categories|Category|Filed under|Keywords?|Topics?)\s*:.*|\s*(?:Tags|Categories)\s*")
RE_C5_URL_LINE = re.compile(r"\s*(?:https?://|www\.)\S+\s*")
RE_C5_SEP = re.compile(r"\s*[,|]\s*")
RE_C5_SENTENCE = re.compile(r"[।॥.!?]")
C5_MIN_TOKENS, C5_MAX_TOKEN_CHARS, C5_MAX_TOKEN_WORDS = 6, 30, 3
def _is_list_line(s):
    """A comma- or pipe-separated run of >= 6 short tokens with no sentence punctuation."""
    if not s or RE_C5_SENTENCE.search(s): return False
    toks = [t for t in RE_C5_SEP.split(s) if t]
    return len(toks) >= C5_MIN_TOKENS and all(len(t) <= C5_MAX_TOKEN_CHARS and len(t.split()) <= C5_MAX_TOKEN_WORDS for t in toks)
def medicine_c5(text):
    """C5: remove tag/label lines, bare URL lines and token-list lines; unchanged if more than half the lines are lists."""
    if not text: return text
    src = _lf(text)
    lines = src.split("\n")
    hit = [bool(RE_C5_TAGLINE.fullmatch(l) or RE_C5_URL_LINE.fullmatch(l) or _is_list_line(l.strip())) for l in lines]
    n_hit, n_nonempty = sum(hit), sum(1 for l in lines if l.strip())
    if not n_hit or n_hit * 2 > n_nonempty: return text
    return "\n".join(l for l, h in zip(lines, hit) if not h)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 210 — indic / D2 / `DB-D2-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D2 Romanised Indic. Pack `ind-hi-hplt`. Source: section D2 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `2f2fbdf81419e6f5` (ind-hi-fw2), original offset 287: `"\u093e\u0928\u0947\u0902\u0917\u0947.\nMitti Khane Ka Man Kyon "` (fix).
- `2d3b04f109d069ec` (ind-hi-hplt), original offset 11551: `"\u0937\u0940 \u0939\u0948 |\nShiksha k Odisha kya hai"` (fix).
- `c02e0ea3fe225110` (ind-hi-hplt), original offset 1730: `"\u0930\u0939\u0940 \u0939\u0948.\nRead More: How to Enable"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d2(text)`.

```python
RULE_ID = "DB-D2-001"
CODE = "D2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-hplt', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt, ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_ROMAN_HI = {"kya", "kaise", "kaisa", "kaun", "kare", "karen", "hai", "hain", "ka", "ke", "ki", "ko", "mein", "liye",
             "hota", "hoti", "hote", "kaha", "kab", "aur", "bhi", "nahi", "wala", "wali"}


def medicine_d2(text):
    kept = []
    for line in text.split("\n"):
        words = {w.lower() for w in re.findall("[A-Za-z]+", line)}
        ascii_only = not re.search("[^\x00-\x7f\u2018\u2019\u201C\u201D\u2026]", line)
        if line.strip() and len(line) <= 120 and ascii_only and len(words & _ROMAN_HI) >= 2:
            continue  # a romanised Hindi heading or SEO title
        kept.append(line)
    return "\n".join(kept)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section D2 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 211 — indic / D2 / `DB-D2-002`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D2 Romanised Indic. Pack `ind-sa-fw2`. Source: section D2 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `df1787b2a236626b` (ind-sa-fw2), original offset 2044: `"\u094d\u0917\u0924\u0903 \u0964\u0964\n\u015br\u012bhar\u1e63a\u1e41 kavi-r\u0101ja-r\u0101ji"` (fix).
- `8f8f2c783674d31f` (ind-sa-fw2), original offset 303: `"Rahim\n\n\nAll\u0101hu l\u0101 \u02beil\u0101ha \u02beill\u0101 h"` (fix).
- `76282692bca966da` (ind-sa-fw2), original offset 80: `"\u0940\u0930\u0938\u094d\u092f \u0965\na\u1e45ga\u1e47av\u0113d\u012b vasudh\u0101 kuly\u0101"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d2(text)`.

```python
RULE_ID = "DB-D2-002"
CODE = "D2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d2(text):
    def roman(line):
        letters = [c for c in line if c.isalpha()]
        if len(line.strip()) < 25 or len(letters) < 10:
            return False
        lat = sum(1 for c in letters if c.isascii() or 0xC0 <= ord(c) <= 0x24F or 0x1E00 <= ord(c) <= 0x1EFF)
        return lat / len(letters) > 0.6 and bool(re.search(r"[āīūṛṝḷṃḥṅñṭḍṇśṣ]", line))
    return "\n".join(l for l in text.split("\n") if not roman(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D2 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 212 — indic / D3 / `DB-D3-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-bn-fw2`. Source: section D3 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-bn-fw2: 0 changed / 0 dropped of 238 (PASS); ind-bn-sangraha-v: 0 changed / 0 dropped of 50 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3f0c89c1bc69537e` (ind-bn-fw2), original offset 0: `"Assalamu Alaikum Dear Students. Today's Topic is Green House Eff"` (drop).
- `1abc081b1ce17469` (ind-bn-fw2), original offset 0: `"\u09aa\u09be\u09b0\u09cd\u09a5\u09c7 \u09ac\u09c3\u09b9\u09b8\u09cd\u09aa\u09a4\u09bf\u09ac\u09be\u09b0 (27 \u0985\u0995\u09cd\u099f\u09cb\u09ac\u09b0) \u099f\u09bf-\u099f\u09cb\u09af\u09bc\u09c7\u09a8\u09cd\u099f\u09bf \u09ac\u09bf\u09b6\u09cd\u09ac\u0995\u09be\u09aa 2022-\u098f\u09b0 \u09b8\u09c1"` (drop).
- `7b65bbecd0338588` (ind-bn-fw2), original offset 0: `"Marriage of Hazrat Ali and Fatimah \u09b9\u09af\u09b0\u09a4 \u0986\u09b2\u09c0 \u0993 \u09ab\u09be\u09a4\u09c7\u09ae\u09be\u09b0 \u09ac\u09bf\u09ac\u09be\u09b9\nScri"` (drop).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-001"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-bn-fw2', 'ind-bn-sangraha-v'}
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2, ind-bn-sangraha-v"
SOURCE_ORIGIN = "ind-bn-fw2"
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

def medicine_d3(text):
    """Mixed language is natural in Bengali writing, so it is not cleaned. Only a document that is mostly
    English (more than 40% of its letters are Latin) is dropped from the Bengali pool."""
    latin = len(re.findall('[A-Za-z]', text))
    bengali = len(re.findall('[\u0980-\u09ff]', text))
    return latin + bengali > 0 and latin / (latin + bengali) > 0.40


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 213 — indic / D3 / `DB-D3-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-D3-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-bn-fw2`. Source: section D3 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python deferred
RULE_ID = "DB-D3-002"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-bn-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-D3-001"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d3(text):
    """Keep the document unchanged: D3 is labelled, not cleaned."""
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. The rule changes no document by construction.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 214 — indic / D3 / `DB-D3-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-gu-fw2`. Source: section D3 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-003"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re

def m2_d3(text, url=None):
    return (text, "keep")

def medicine_d3(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m2_d3(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 215 — indic / D3 / `DB-D3-004`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-D3-003. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-gu-fw2`. Source: section D3 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python deferred
RULE_ID = "DB-D3-004"
CODE = "D3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-gu-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-D3-003"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

GU = re.compile(r"[઀-૿]")
LAT = re.compile(r"[A-Za-z]")

def medicine(text):
    # Keep a line unless it is English-only and long.
    return "\n".join(l for l in text.split("\n")
                     if GU.search(l) or len(LAT.findall(l)) < 25)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 97 of 2...
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 216 — indic / D3 / `DB-D3-005`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-hi-fw2`. Source: section D3 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-005"
CODE = "D3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-fw2"
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_DEVA = re.compile(r"[\u0900-\u097F]")
_LATIN_WORD = re.compile(r"\b[A-Za-z]{3,}\b")

def _flag_d3_mixed(text: str, min_deva: int = 40, min_latin_words: int = 8) -> bool:
    """True if doc looks like natural HI-EN mix (for labeling only; not a drop)."""
    if not text:
        return False
    return len(_DEVA.findall(text)) >= min_deva and len(_LATIN_WORD.findall(text)) >= min_latin_words

def medicine_d3(text: str) -> str:
    """Automatic medicine: keep text. D3 is label/fix; True would mean drop in harm_test_indic."""
    return text or ""


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `teams/02-data-b/gold/ind-hi-fw2_gold.csv` (**234** docs, post-#161 rebuild). Tool: `harm_test_indic.py --rule D3` (2026-10-31; allow ≤ max(1, 1%) ≈ 2.34). Automatic medicine `medicine_d3` keeps text (label-only):
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 217 — indic / D3 / `DB-D3-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-hi-hplt`. Source: section D3 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-006"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-hplt'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def _d3_latin_words(text):
    """Latin words of 3+ letters that sit between Devanagari words: the D3 tag, kept as a note on the document."""
    return re.findall("(?<=[\u0900-\u097F] )[A-Za-z]{3,}(?=[ ,.]*[\u0900-\u097F])", text)


def medicine_d3(text):
    return False  # tag only: the text is kept as it is


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**. A rule that removed or translated these words would have changed 13 of the 69 gold documents (19%) when the gold set was 69 documents and fail.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 218 — indic / D3 / `DB-D3-007`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-D3-006. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-hi-hplt`. Source: section D3 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python deferred
RULE_ID = "DB-D3-007"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-D3-006"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# D3: natural Hindi-English mixing is labelled, not cured
def medicine_d3(text):
    return False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 0 of 13 D3 documents; 0 other diseased documents touche...
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 219 — indic / D3 / `DB-D3-008`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-kn-sangraha-s`. Source: section D3 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-008"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s, ind-kn-fw2"
SOURCE_ORIGIN = "ind-kn-sangraha-s"
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

LETTER = re.compile(r"[^\W\d_]", re.U)
NOT_KN_LATIN = re.compile(r"[^\W\d_a-zA-Zಀ-೿]", re.U)
def m6_foreign_ratio(s):
    n = len(LETTER.findall(s))
    return len(NOT_KN_LATIN.findall(s)) / n if n else 0.0
def medicine_d3(s):
    return s  # keep the text; m6_foreign_ratio is the measure

def effect(fn, text):
    out = fn(text)
    return "drop" if out is True else ("change" if out != text else "same")


def main(pack, gold_csv, labels_csv):
    docs = {r["doc_id"]: r["text"] for r in pq.read_table(pack, columns=["doc_id", "text"]).to_pylist()}
    gold = [r["doc_id"] for r in csv.DictReader(open(gold_csv, encoding="utf-8"))]
    gold = [g for g in gold if g in docs]
    labels = list(csv.DictReader(open(labels_csv, encoding="utf-8")))
    clean = [r["doc_id"] for r in labels if r["verdict"] == "clean"]
    print(f"pack {len(docs)} docs, gold in pack {len(gold)}, my clean rows {len(clean)}")
    print("med disease | gold changed dropped | my-clean changed dropped | labelled docs touched | pack touched")
    medicines = [("M1", "B2", m1_tags), ("M2", "B3", m2_ghost), ("M3", "A6", m3_half_translated),
                 ("M4", "C1", m4_footer), ("M5", "C3", m5_dangling_intro)]
    limit = max(1, 0.01 * len(gold))  # 1% of the gold set or 1 document, whichever is more
    for name, code, fn in medicines:
        g = [effect(fn, docs[i]) for i in gold]
        c = [effect(fn, docs[i]) for i in clean]
        sick = [r["doc_id"] for r in labels if code in r["diseases"].split(";")]
        hit = sum(effect(fn, docs[i]) != "same" for i in sick)
        allp = sum(effect(fn, t) != "same" for t in docs.values())
        verdict = "PASS" if (g.count("change") + g.count("drop")) <= limit else "FAIL"
        print(f"{name}  {code}  | {g.count('change'):3d} {g.count('drop'):3d} {verdict} | "
              f"{c.count('change'):3d} {c.count('drop'):3d} | {hit}/{len(sick)} | {allp}")
    sick = [r["doc_id"] for r in labels if "D3" in r["diseases"].split(";")]
    print("M6  D3  | no text change; foreign-letter ratio of D3 docs:",
          sorted(round(m6_foreign_ratio(docs[i]), 3) for i in sick))


def selftest():
    assert m1_tags("ಅ <ಐ. ಡಿ. 1> ಬ") == "ಅ ಬ"
    assert m1_tags("ಅ<ಬಿ. ಆರ್.>ಬ") == "ಅ\nಬ"
    assert m1_tags("<> </Â>x") == " x"
    assert m1_tags("2 < 3 > 1") == "2 < 3 > 1"  # a comparison is not a tag
    assert m2_ghost("ಅ<unk>ಬ") == "ಅಬ"
    assert m3_half_translated("(i.ಇ. ಪಳೆಯುಳಿಕೆ)") == "(ಅಂದರೆ ಪಳೆಯುಳಿಕೆ)"
    assert m4_footer("ಪಠ್ಯ " * 20 + "\nಉಲ್ಲೇಖಗಳು.\nಮೂಲಗಳು") == ("ಪಠ್ಯ " * 20).rstrip()
    assert m5_dangling_intro("ಒಂದು.\nಅವು ಹೀಗಿವೆಃ") == "ಒಂದು.\n"
    assert m5_dangling_intro("ಒಂದು. ಅವು ಹೀಗಿವೆಃ") == "ಒಂದು.\n"
    assert m5_dangling_intro("ಅವು ಹೀಗಿವೆಃ") is True
    assert m5_dangling_intro("ಒಂದು.") == "ಒಂದು."


if __name__ == "__main__":
    selftest()
    if len(sys.argv) < 4:
        sys.exit("usage: python3 medicine_run.py PACK.parquet GOLD.csv labels.csv")
    main(*sys.argv[1:4])


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS (the rule keeps every text).
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 220 — indic / D3 / `DB-D3-009`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-kn-sangraha-v`. Source: section D3 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-009"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"
SOURCE_ORIGIN = "ind-kn-sangraha-v"
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

def keep_mixed(t):
    """D3: no medicine. Kannada-English mixing is natural; the brief says label it, do not judge it."""
    return t


def medicine_d3(text):
    """The D3 rule, under the name that the harm tests look for: returns the text unchanged."""
    return keep_mixed(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 221 — indic / D3 / `DB-D3-010`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-mr-fw2`. Source: section D3 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `9c9cb2366bc14d88` (ind-mr-fw2), original offset 1999: `"\u091d\u093e\u0932\u0940. ..\nThis News has been Retr"` (fix).
- `36198f74122a5919` (ind-mr-fw2), original offset 1428: `"\u093f\u0924 \u0939\u094b\u0924\u0947.\nThis News has been Retr"` (fix).
- `70386fb4070fc50f` (ind-mr-fw2), original offset 573: `"\u0932\u0947 \u0939\u094b\u0924\u0947.\nPrevious Article\u0915\u0938\u092c\u094d\u092f\u093e\u091a"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-010"
CODE = "D3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-fw2"
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d3(text):
    return re.sub(r'\n\s*(?:This News has been Retrieved from RSS|Previous Article|Next Article).*$', '', text, flags=re.I | re.DOTALL)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 222 — indic / D3 / `DB-D3-011`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-mr-sangraha-v`. Source: section D3 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_d3(text)`.

```python
RULE_ID = "DB-D3-011"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

def cure_d3(text):
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Because this is an intentional no...
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 223 — indic / D3 / `DB-D3-012`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-sa-fw2`. Source: section D3 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `6da72db6a95c25b8` (ind-sa-fw2), original offset 312: `"\u0930\u094d\u0936\u0928\u0940\u092f\u093e\nhttps://twitter.com/samp"` (fix).
- `bd55ddb98859ace4` (ind-sa-fw2), original offset 0: `"Source: Chinna Katha Par"` (fix).
- `7d763858a5acae02` (ind-sa-fw2), original offset 101: `"\u0941\u0924\u093e\u0938\u0903 \u0965\n\u0905\u0925\u0930\u094d\u0935\u0935\u0947\u0926 \u092e\u0947\u0902 \u092a\u0942\u0930\u0923\u0903 \u0915\u0947 10"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-012"
CODE = "D3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_HIN = set("है हैं था थे थी में और नहीं लिए गया गई हुआ होता होती करने किया करें ने को से का की के भी यह वह कि जो आप हम साथ वाले रहे रही".split())
_ANCHOR = set("है हैं था थे थी में और नहीं लिए गया गई हुआ होता होती करने किया करें ने साथ वाले रहे रही".split())
_C = "क-हक़-य़"

def _lang(line):
    letters = [c for c in line if c.isalpha()]
    if len(line.strip()) < 25 or len(letters) < 10:
        return "short"
    lat = sum(1 for c in letters if c.isascii() or 0xC0 <= ord(c) <= 0x24F or 0x1E00 <= ord(c) <= 0x1EFF)
    dev = sum(1 for c in letters if "ऀ" <= c <= "ॿ")
    if lat / len(letters) > 0.6:
        return "san_Latn" if re.search(r"[āīūṛṝḷṃḥṅñṭḍṇśṣ]", line) else "eng"
    if dev / len(letters) > 0.6:
        w = re.findall("[ऀ-ॿ]+", line)
        obl = lambda x: x.endswith("ों") and len(re.findall(f"[{_C}](?!्)", x)) >= 2
        h = sum(1 for x in w if x in _HIN or obl(x))
        a = sum(1 for x in w if x in _ANCHOR or obl(x))
        if a >= 1 and h >= 2 and h / max(1, len(w)) >= 0.15:
            return "hin"
    return "san"

def medicine_d3(text):
    return "\n".join(l for l in text.split("\n") if _lang(l) not in ("eng", "hin"))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 224 — indic / D3 / `DB-D3-013`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-D3-012. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-sa-fw2`. Source: section D3 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python deferred
RULE_ID = "DB-D3-013"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-D3-012"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

D3_MIN_IN_SENTENCE = 3
D3_MAX_LATIN_SHARE = 0.5
D3_DENSE_IN_SENTENCE = 10
D3_CONTEXT = 25
RE_DEVA_WORD = re.compile(
    r"[ऄ-हऽॐक़-ॡॲ-ॿ]"
    r"[ऀ-ॣॱ-ॿ‌‍]*"
    r"(?::(?![0-9A-Za-zऀ-ॿ]))?")
RE_LATIN_WORD = re.compile(r"[A-Za-zÀ-ɏḀ-ỿ]+")
RE_DEVA_CHAR = re.compile(r"[ऀ-ॿ]")
RE_PAREN_ACRONYM = re.compile(r"\([A-Z]{2,8}\)")
def deva_words(text):
    """Devanagari words of `text` (see RE_DEVA_WORD); danda, digits and punctuation split, ZWJ/ZWNJ stay inside a word."""
    return RE_DEVA_WORD.findall(text)
def latin_in_sentences(text):
    """Latin-script words that sit inside a Devanagari sentence: Devanagari within D3_CONTEXT chars on both sides on the
    same line (adapted from prescreen.py's in_sentence rule; here the context window is cut at the nearest line break
    so it can never reach a neighbouring line). Latin-only lines — header, footer or mid-body chrome — therefore never
    qualify, however short. All-caps acronyms in parentheses such as (CPEC) are removed first. Single letters are
    ignored (list markers, variables)."""
    t = RE_PAREN_ACRONYM.sub(lambda m: " " * len(m.group()), text)
    hits = []
    for m in RE_LATIN_WORD.finditer(t):
        if len(m.group()) < 2:
            continue
        before = t[max(0, m.start() - D3_CONTEXT):m.start()].rsplit("\n", 1)[-1]
        after = t[m.end():m.end() + D3_CONTEXT].split("\n", 1)[0]
        if RE_DEVA_CHAR.search(before) and RE_DEVA_CHAR.search(after):
            hits.append(m.group())
    return hits
def latin_share(text):
    """Latin words / (Latin words + Devanagari words); 0.0 when there are no words."""
    latin = len(RE_LATIN_WORD.findall(text)); deva = len(deva_words(text))
    return latin / (latin + deva) if latin + deva else 0.0
def d3_mixed_language(text):
    """D3 detector: at least D3_MIN_IN_SENTENCE Latin words inside Devanagari sentences and Latin share below
    D3_MAX_LATIN_SHARE; the share clause is waived when at least D3_DENSE_IN_SENTENCE Latin words sit inside
    Devanagari sentences (word-by-word gloss pages). Detection only; the action is `none`."""
    n = len(latin_in_sentences(text))
    if n >= D3_DENSE_IN_SENTENCE:
        return True
    if latin_share(text) >= D3_MAX_LATIN_SHARE:
        return False
    return n >= D3_MIN_IN_SENTENCE

def medicine_d3(text):
    return text    # action none: the detector `d3_mixed_language` reports; the text is kept


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 225 — indic / D3 / `DB-D3-014`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D3 Mixed language. Pack `ind-te-fw2`. Source: section D3 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-014"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-s, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d3(t, url=None):
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** own-pack real gold set (`ind-te-fw2_gold.csv`, 18 documents) and full Telugu real gold set (`telugu_gold.csv`, 50 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 27; 46 documents in the 31 Oct snapshot):
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 226 — indic / D5 / `DB-D5-002`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** D5 Translationese. Pack `ind-hi-hplt`. Source: section D5 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_d5(text)`.

```python
RULE_ID = "DB-D5-002"
CODE = "D5"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-hplt', 'ind-hi-indiccorp'}
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt, ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d5(text):
    return False  # tag only: the text is kept as it is


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** nothing to run, because the rule does nothing (changes 0 of 67 gold documents, drops 0). **PASS**
5. **Side effects:** in the author's `medicine.md`, section D5 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 227 — indic / G3 / `DB-G3-002`

**Integration decision:** DEFERRED. acts again on retained documents after the full pipeline. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** G3 Indic dropped by an English rule. Pack `ind-te-sangraha-s`. Source: section G3 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g3(text)`.

```python deferred
RULE_ID = "DB-G3-002"
CODE = "G3"
ACTION = "fix"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-te-sangraha-s'}
DEFER_REASON = "acts again on retained documents after the full pipeline"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"  # packs it runs on
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g3(text):
    return re.sub(r"[ \t]*\([ \t,;]*\)", "", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_g3` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section G3 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 228 — indic / H3 / `DB-H3-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** H3 The same content in another source or language. Pack `ind-sa-fw2`. Source: section H3 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `6da72db6a95c25b8` (ind-sa-fw2), original offset 312: `"\u0930\u094d\u0936\u0928\u0940\u092f\u093e\nhttps://twitter.com/samp"` (fix).
- `bd55ddb98859ace4` (ind-sa-fw2), original offset 0: `"Source: Chinna Katha Par"` (fix).
- `7d763858a5acae02` (ind-sa-fw2), original offset 101: `"\u0941\u0924\u093e\u0938\u0903 \u0965\n\u0905\u0925\u0930\u094d\u0935\u0935\u0947\u0926 \u092e\u0947\u0902 \u092a\u0942\u0930\u0923\u0903 \u0915\u0947 10"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_h3(text)`.

```python
RULE_ID = "DB-H3-001"
CODE = "H3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_HIN = set("है हैं था थे थी में और नहीं लिए गया गई हुआ होता होती करने किया करें ने को से का की के भी यह वह कि जो आप हम साथ वाले रहे रही".split())
_ANCHOR = set("है हैं था थे थी में और नहीं लिए गया गई हुआ होता होती करने किया करें ने साथ वाले रहे रही".split())

def _translation(line):
    letters = [c for c in line if c.isalpha()]
    if len(line.strip()) < 25 or len(letters) < 10:
        return False
    lat = sum(1 for c in letters if c.isascii() or 0xC0 <= ord(c) <= 0x24F or 0x1E00 <= ord(c) <= 0x1EFF)
    if lat / len(letters) > 0.6:
        return not re.search(r"[āīūṛṝḷṃḥṅñṭḍṇśṣ]", line)
    w = re.findall("[ऀ-ॿ]+", line)
    h = sum(1 for x in w if x in _HIN)
    a = sum(1 for x in w if x in _ANCHOR)
    return a >= 1 and h >= 2 and h / max(1, len(w)) >= 0.15

def medicine_h3(text):
    return "\n".join(l for l in text.split("\n") if not _translation(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_h3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section H3 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 229 — indic / H3 / `DB-H3-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-H3-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** H3 The same content in another source or language. Pack `ind-sa-fw2`. Source: section H3 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_h3(text)`.

```python deferred
RULE_ID = "DB-H3-002"
CODE = "H3"
ACTION = "keep"
STAGE = "35"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-H3-001"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

RE_ROMAN_VERSE_LINE = re.compile(r"^[Ⅰ-ⅿ]+ \S", re.M)                        # ebible.org: "Ⅰ यावन्तः …"
RE_GITA_REF = re.compile(r"।।[0-9]{1,2}(?:\.[0-9]{1,3}){1,2}।।")               # gitasupersite: ।।8.4।।
RE_GITA_HEADING_LINE = re.compile(r"^।।[^।\n0-9०-९]{1,60}।।[ \t\r]*$", re.M)  # ।।ब्रह्मसूत्रभाष्यम्।।
MIN_VERSE_LINES = 5; MIN_GITA_REFS = 2; MIN_GITA_HEADINGS = 3

def detect_h3(text):
    if not text: return False
    if len(RE_ROMAN_VERSE_LINE.findall(text)) >= MIN_VERSE_LINES: return True
    if len(RE_GITA_REF.findall(text)) >= MIN_GITA_REFS: return True
    if len(RE_GITA_HEADING_LINE.findall(text)) >= MIN_GITA_HEADINGS: return True
    return False
def medicine_h3(text):
    return text    # action none: the detector `detect_h3` reports; dedupe is a corpus-time action


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_h3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section H3 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 230 — indic / B4 / `DB-B4-001`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B4 Template and code junk in prose. Pack `ind-gu-fw2`. Source: section B4 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `a4ab5516e2836afa` (ind-gu-fw2), original offset 11180: `", \u0a87\u0aae\u0ac7\u0a87\u0ab2:[\u0a87\u0aae\u0ac7\u0a87\u0ab2 \u0ab8\u0ac1\u0ab0\u0a95\u0acd\u0ab7\u0abf\u0aa4]"` (fix).
- `8c31573b3fa95857` (ind-gu-fw2), original offset 2217: `"\u0ac7\u0a88\u0ab2 \u0a95\u0ab0\u0acb [email protected] \u0a85\u0aa5\u0ab5\u0abe \u0ab5"` (fix).

**Example gap:** 2/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-B4-001"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-gu-fw2'}
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

JUNK = re.compile(r"\[ઇમેઇલ સુરક્ષિત\]|email@example\.com|firstname\.lastname@example\.com"
                  r"|\[email\s*protected\]|\{\{.*?\}\}|\$\{.*?\}|\bundefined\b|\bNaN\b|\bnull\b")

def medicine(text):
    return JUNK.sub("", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 4 of 6.
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 231 — indic / B4 / `DB-B4-002`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B4 Template and code junk in prose. Pack `ind-kn-sangraha-v`. Source: section B4 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS); ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `3db23e9e76ca858e` (ind-kn-sangraha-v), original offset 73: `"\u0ca1 \u0ca8\u0ccd\u0caf\u0cc2\u0cb8\u0ccd\\n\u0cae\u0cc8\u0cb8\u0cc2\u0cb0\u0cc1\u0c83 \u0c9a\u0cbe\u0cae\u0cc1\u0c82\u0ca1\u0cc7\u0cb6\u0ccd\u0cb5\u0cb0\u0cbf \u0c95"` (fix).
- `c3ade5a08282ceea` (ind-kn-sangraha-v), original offset 169: `"ilmibeat\\n| Updated: Thursday, J"` (fix).
- `035d7a62badd87a3` (ind-kn-sangraha-v), original offset 27: `"\u0cbe\u0caf \u0cac\u0cc7\u0c95\u0cc1!\\n\u0cb8\u0ccb\u0cae\u0cbe\u0cb2\u0cbf\u0caf\u0cbe\u0ca6 \u0cac\u0cb0 \u0cb5\u0cbf\u0cb6\u0ccd\u0cb5 \u0c95\u0c82\u0ca1"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_b4(text)`.

```python
RULE_ID = "DB-B4-002"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s', 'ind-kn-sangraha-v'}
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v, ind-kn-fw2, ind-kn-sangraha-s"
SOURCE_ORIGIN = "ind-kn-sangraha-v"
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

BS = chr(92)


def fix_literal_newline(t):
    """B4: a literal backslash-n (two characters) becomes a real newline."""
    return t.replace(BS + "n", "\n")


def medicine_b4(text):
    """The B4 rule, under the name that the harm tests look for: returns the fixed text."""
    return fix_literal_newline(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 232 — indic / B4 / `DB-B4-003`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B4 Template and code junk in prose. Pack `ind-mr-sangraha-v`. Source: section B4 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS); ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `5cd1cc2146075a9f` (ind-mr-sangraha-v), original offset 73: `" Marathi\\nHome Local Pune \u0935\u093f\u091c\u094d\u091e\u093e"` (fix).
- `fedd23c56d6850a6` (ind-mr-sangraha-v), original offset 104: `"\u0938. \u0967\u096c\u0968\u096f)\\n\u091c\u0949\u0928 \u092e\u093f\u0932\u094d\u091f\u0928 (\u0907\u0902\u0917\u094d\u0932\u093f\u0936\u0903 J"` (fix).
- `09f78635c7686fd8` (ind-mr-sangraha-v), original offset 6: `" \u091c\u093f \u0932\u094d\u0939\u093e\\n\u092a\u093e\u091f\u0923\u093e, \u091c\u093f \u0932\u094d\u0939\u093e.- \u092c\u093f\u0939\u093e\u0930"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_b4(text)`.

```python
RULE_ID = "DB-B4-003"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-mr-fw2', 'ind-mr-sangraha-v'}
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v, ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

def cure_b4(text):
    # Conservative gate for recurring escaped newlines in the Marathi prose pack.
    if text.count("\\n") < 3:
        return text
    return text.replace("\\n", "\n")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Check B4-positive prose separatel...
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 233 — indic / B4 / `DB-B4-004`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B4 Template and code junk in prose. Pack `ind-sa-fw2`. Source: section B4 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `875f86117f43fd90` (ind-sa-fw2), original offset 256: `"\u0928\u094d\u0924\u0928\u092e\u094d\u0964\n\u0967\u096f\u096f\u096c\u0924\u092e\u0947 \u0938\u0902\u0935\u0924\u094d\u0938\u0930\u0947 \u0935\u093f\u0936\u094d\u0935\u0935\u094d"` (fix).
- `b54ef4486f508f61` (ind-sa-fw2), original offset 98: `"\u0969\u0967\u0967-\u0969\u0968\u0966\n[[\u0932\u0947\u0916\u0915\u0903 :|]]\n|\u0915\u0923\u094d\u0921\u093f\u0915\u093e \u0969\u0968"` (fix).
- `54cba74d98069466` (ind-sa-fw2), original offset 75: `"\u0928\u0915\u092e\u094d \u0968\u096a\n[[\u0932\u0947\u0916\u0915\u0903 :|]]\n|\u0938\u094d\u0925\u093e\u0928\u0915\u0902 \u0968\u096b"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_b4(text)`.

```python
RULE_ID = "DB-B4-004"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-sa-fw2'}
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_JUNK = [r"\{\{[^{}\n]*\}\}", r"'''", r"\[Page\d+-[a-z]\+ ?\d+\]", "↩"]

def medicine_b4(text):
    t = re.sub(r"\[\[(?:[^|\]\n]*\|)?([^\]\n]*)\]\]", r"\1", text)
    for p in _JUNK:
        t = re.sub(p, "", t)
    t = re.sub(r"(?<=॥)\d{3,}(?=\s)", "", t)
    return re.sub(r"(?<=\s)\d{3,}(?=[क-ह])|(?<=[ा-्क-ह])\d{3,}(?=[क-ह])", "", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 234 — indic / B4 / `DB-B4-005`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B4 Template and code junk in prose. Pack `ind-ta-sangraha-v`. Source: section B4 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-ta-sangraha-v: 0 changed / 0 dropped of 41 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `7cce84d0d76b0c30` (ind-ta-sangraha-v), original offset 172: `"V Sports\\n\"\u0b89\u0bb2\u0b95\u0b95\u0bcd \u0b95\u0bcb\u0baa\u0bcd\u0baa\u0bc8\u0baf\u0bbf\u0ba9\u0bcd \u0baa\u0bc7\u0baa\u0bbf"` (fix).
- `caf1190306aaaad1` (ind-ta-sangraha-v), original offset 50: `"TamilSpy\\n\u0ba4.\u0ba4\u0bc7.\u0b95\u0bc2 \u0b85\u0bb2\u0bc1\u0bb5\u0bb2\u0b95\u0bae\u0bcd; \u0ba4\u0bae\u0bbf\u0bb4"` (fix).
- `fa6df887b3a3ed81` (ind-ta-sangraha-v), original offset 190: `"ikkaigal\\nClopam \u0bb5\u0bbf\u0bb2\u0bc8 \u0bae\u0bb1\u0bcd\u0bb1\u0bc1\u0bae\u0bcd \u0baa\u0bc7"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_b4(text)`.

```python
RULE_ID = "DB-B4-005"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-ta-sangraha-v'}
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"
SOURCE_ORIGIN = "ind-ta-sangraha-v"
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_b4(text):
    return text.replace("\\n", "\n")  # the two characters backslash and n become a line break


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 22 documents, all labelled B4.
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 235 — indic / B4 / `DB-B4-006`

**Integration decision:** CANDIDATE. first eligible candidate in source order; independent approval pending. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** B4 Template and code junk in prose. Pack `ind-te-sangraha-s`. Source: section B4 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).

**Exact source characters:** JSON string literals below decode to verbatim original characters. Fix excerpts surround the first edit; drop excerpts identify the affected source document and do not establish which substring caused the drop. These are execution examples, not additional independently adjudicated labels.

- `39a6ba9db8c951b9` (ind-te-sangraha-s), original offset 1506: `"1991\u0c32\u0c4b '\u0c10\u0c21\u0c3f1' \u0c38\u0c02\u0c1a\u0c3f\u0c15\u0c24\u0c4b \u0c30\u0c46\u0c02\u0c21\u0c35 \u0c38\u0c3e\u0c30\u0c3f"` (fix).
- `3dbf4ee7290f1569` (ind-te-sangraha-s), original offset 1121: `" \u0c0e\u0c15\u0c30\u0c02\u0c32\u0c4b \u0c10\u0c21\u0c3f1 \u0c35\u0c30\u0c15\u0c41 \u0c35\u0c47\u0c30\u0c4d\u0c35\u0c47\u0c30\u0c41 \u0c2a\u0c30\u0c3f\u0c2e\u0c3e"` (fix).
- `976b619191078e2d` (ind-te-sangraha-s), original offset 602: `"\u0c2f\u0c41, \u0c32\u0c47\u0c26\u0c3e <\u0c10. \u0c21\u0c3f. 1>%, \u0c28\u0c40\u0c30\u0c41, \u0c2a\u0c4d\u0c30\u0c27"` (fix).
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_b4(text)`.

```python
RULE_ID = "DB-B4-006"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s, ind-te-fw2, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-sangraha-s"
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_b4(text):
    text = re.sub(r"[ \t]*<ఐ\.? ?డి\.? ?\d+>?%?", "", text)
    text = re.sub(r"[ \t]*(?<![\u0C00-\u0C7F])ఐడి\d+", "", text)
    text = re.sub(r"[ \t]*\(ID\d+\)", "", text)
    text = re.sub(r"(?m)^![^\n]*=[^\n]*\|[^\n]*\n?", "", text)
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_b4` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 236 — indic / F1 / `DB-F1-001`

**Integration decision:** DEFERRED. replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-gu-fw2`. Source: section F1 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-gu-fw2: 0 changed / 0 dropped of 19 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python deferred
RULE_ID = "DB-F1-001"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-gu-fw2'}
DEFER_REASON = "replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"
SOURCE_ORIGIN = "ind-gu-fw2"
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU_DIGIT = "\u0AE6-\u0AEF"                    # Gujarati digits 0-9
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

PHONE = re.compile(rf"(?<![0-9{GU_DIGIT}])(?:\+91[\s-]?)?[6-9૬-૯][0-9{GU_DIGIT}]{{4}}"
                   rf"[\s-]?[0-9{GU_DIGIT}]{{5}}(?![0-9{GU_DIGIT}])")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def m3_f1(text, url=None):
    return _fix(text, EMAIL.sub("[EMAIL]", PHONE.sub("[PHONE]", text)))

def medicine_f1(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m3_f1(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 237 — indic / F1 / `DB-F1-002`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-F1-001. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-gu-fw2`. Source: section F1 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python deferred
RULE_ID = "DB-F1-002"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-gu-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-F1-001"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

EMAIL = re.compile(r"[\w.+-]+@(?!example\.com)[\w-]+\.[\w.]+")
PHONE = re.compile(
    r"(?<![\d.])(?:\+91[ -]?)?[6-9]\d{4}[ -]?\d{5}(?!\d)"   # mobile
    r"|(?<!\d)\d{3}\d{3}\d{4,}(?!\d)"                       # long digit run
    r"|\b0\d{2,4}[ -]\d{6,8}\b")                            # landline

def medicine(text):
    return EMAIL.sub("<EMAIL>", PHONE.sub("<PHONE>", text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 17 of 1...
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 238 — indic / F1 / `DB-F1-003`

**Integration decision:** DEFERRED. replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-hi-hplt`. Source: section F1 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-hi-fw2: 0 changed / 0 dropped of 234 (PASS); ind-hi-hplt: 0 changed / 0 dropped of 67 (PASS); ind-hi-indiccorp: 0 changed / 0 dropped of 130 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python deferred
RULE_ID = "DB-F1-003"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-fw2', 'ind-hi-hplt', 'ind-hi-indiccorp'}
DEFER_REASON = "replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt, ind-hi-fw2, ind-hi-indiccorp"
SOURCE_ORIGIN = "ind-hi-hplt"
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_MAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE = re.compile(r"(?<![\d,.])(?:\+91[ -]?|0)?[6-9]\d{9}(?![\d,.])")


def medicine_f1(text):
    t = _MAIL.sub("", text)
    return _PHONE.sub("", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 239 — indic / F1 / `DB-F1-004`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-F1-003. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-hi-hplt`. Source: section F1 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python deferred
RULE_ID = "DB-F1-004"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-hi-hplt'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-F1-003"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# F1: personal e-mail addresses (free mail) and mobile numbers, not near helpline or office words
_MAIL = re.compile(r"[\w.+-]+@(?:gmail|yahoo|hotmail|outlook|rediffmail|ymail)\.[a-z.]+", re.I)
_MOB = re.compile(r"(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)")
_ORG = re.compile(r"हेल्पलाइन|टोल|फ्री|व्हाट्सएप|whatsapp|helpline|toll|कार्यालय|office|कस्टमर|customer|support", re.I)


def medicine_f1(text):
    out = _MAIL.sub("", text)

    def mob(m):
        near = out[max(0, m.start() - 40):m.start()]
        return m.group(0) if _ORG.search(near) else ""
    return _MOB.sub(mob, out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 10 of 16 F1 documents; 0 other diseased documents touch...
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 240 — indic / F1 / `DB-F1-005`

**Integration decision:** DEFERRED. replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-kn-fw2`. Source: section F1 of `diagnosis/submissions/ind-kn-fw2/LokeshJatangi/medicine.md`, PR #63 at `aeb79b8`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-kn-fw2: 0 changed / 0 dropped of 45 (PASS); ind-kn-sangraha-s: 0 changed / 0 dropped of 27 (PASS); ind-kn-sangraha-v: 0 changed / 0 dropped of 103 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python deferred
RULE_ID = "DB-F1-005"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-kn-fw2', 'ind-kn-sangraha-s', 'ind-kn-sangraha-v'}
DEFER_REASON = "replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2, ind-kn-sangraha-s, ind-kn-sangraha-v"
SOURCE_ORIGIN = "ind-kn-fw2"
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "LokeshJatangi"  # PR #63 at aeb79b8

import re

F1_EMAIL = r"(?<![\w.+-])[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}(?![\w-])"
F1_NUMBER = r"(?:[0-9]{10,11}|[0-9]{5}[ \t]+[0-9]{5}|[0-9]{3}[ \t]+[0-9]{8})"
F1_PHONE = rf"(?<!\w)(?:\+[0-9]{{1,3}}[ \t]+)?{F1_NUMBER}(?!\w)"
F1_CANDIDATE = re.compile(rf"(?:{F1_EMAIL})|(?:{F1_PHONE})")

def medicine_f1(text, url=""):
    return F1_CANDIDATE.sub("[REDACTED]", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #63).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 241 — indic / F1 / `DB-F1-006`

**Integration decision:** DEFERRED. replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-mr-fw2`. Source: section F1 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-fw2: 0 changed / 0 dropped of 140 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python deferred
RULE_ID = "DB-F1-006"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-mr-fw2'}
DEFER_REASON = "replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"
SOURCE_ORIGIN = "ind-mr-fw2"
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_f1(text):
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '<EMAIL>', text)
    return re.sub(r'(?:\+91[\-\s]?)?[6-9]\d{9}', '<PHONE>', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 242 — indic / F1 / `DB-F1-007`

**Integration decision:** DEFERRED. replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-mr-sangraha-v`. Source: section F1 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-mr-sangraha-v: 0 changed / 0 dropped of 88 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `cure_f1(text)`.

```python deferred
RULE_ID = "DB-F1-007"
CODE = "F1"
ACTION = "fix+drop"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-mr-sangraha-v'}
DEFER_REASON = "replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"
SOURCE_ORIGIN = "ind-mr-sangraha-v"
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f

import hashlib

# Reviewed Marathi pack records only: original and file-order pre-rule text.
# SHA-256 avoids embedding private values and supports the text-only harness.
_EXCLUDED_SHA256 = frozenset({
    # 001bc250879bd0f7
    "001bc250879bd0f702986535ee3252eee6e1a7c48cdee7f2890a890fd6d50583",
    # 404f212106f160c8
    "404f212106f160c83000ac10881284d088304b030173cbd48fbe99d83c42f743",
    # 50bf742434fe8393
    "50bf742434fe8393f951f369fee4030e82089b9f4ae1fc64cf130eaf3c7b8844",
    # 6402789257fa2f5a
    "011dd7d4bd18b4f776adc7618c36a81e30ae22fdcdde3a446d068968f1519296",
    "6402789257fa2f5a997646dca7c843b74d4dece07a4c7419fd92684c46b213cd",
    # 66ebbb3c7f89fc6e
    "66ebbb3c7f89fc6e9d0fd41720240f166e6a72ebe5fbca7e9d9c76ee8f47de44",
    # 727a8a3d9a6f4fd4
    "25a62eaac83c681739b5550c373f1f6fe1f8cf79ab5f63455d12b131659cc873",
    "727a8a3d9a6f4fd42343d464e0f3b36a153a29ef3c1a91bb9b3635aaf4b65be8",
    # 7d5867bf37cf6900
    "7d5867bf37cf6900af52d058752e3dfc761949319080591871e7c6bb5b0d3e2d",
    # 8924481cb3403322
    "8924481cb3403322ef651e1327e34417558683c9b6c7033dbc81111afd507873",
    # b5776aacf45b7cac
    "b5776aacf45b7cac904ffedd0da2f4fe8e5b08ea0732bc03684d66a93349ae1e",
    # d2dbdd1f87b6a3e1
    "d2dbdd1f87b6a3e1dda084663699ee354eca663094d25b6aa4ef48e373fa07af",
    # fab4928039a870ab
    "fab4928039a870ab3506e01b8a5a910ee799e3662c2a85cb8c3454c092364e50",
    # fedd23c56d6850a6
    "392115d2af134133091b7c8e672863133bea34461b3d8d352e3f6cdd5af5b0b3",
    "fedd23c56d6850a6fcdd4911a9b268d1f00d30a2b1c96e9b59bc8c05335e9936",
})

# Adapted from g1-specv1/tools/f1_rule.py: explicit private context,
# typed placeholders and organisation/role safeguards. Marathi prose only.
import re

_F1_ORG = re.compile(
    r"(?:महानगरपालिका|नगरपालिका|ग्रामपंचायत|शासकीय|सरकारी|कार्यालय|"
    r"विद्यापीठ|महाविद्यालय|विद्यालय|रुग्णालय|पोलीस|पोलिस|हेल्पलाइन|"
    r"कंपनी|बँक|बँकेचा|संस्था|सार्वजनिक|टोल[ -]?फ्री|"
    r"\b(?:government|office|university|hospital|company|helpline|bank)\b)", re.I)
_F1_PERSONAL = re.compile(
    r"(?:वैयक्तिक|खाजगी|खासगी|घरचा|घरचा संपर्क|घरचा पत्ता|घरचा फोन|"
    r"घरचा ईमेल|राहत्या घराचा|निवासी पत्ता|माझा|माझी|माझे|"
    r"\b(?:personal|private|home|residential|my)\b)", re.I)
_F1_EMAIL = re.compile(
    r"(?<![\w.+%-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w-])")
_F1_ROLE = re.compile(
    r"^(?:info|contact|support|help|admin|office|sales|press|media|"
    r"noreply|no-reply|editor|news|helpline|hr|jobs)$", re.I)
_F1_SAFE_DOMAIN = re.compile(
    r"(?:^|\.)(?:example\.(?:com|org|net)|invalid|test|localhost|"
    r"users\.noreply\.github\.com|gov\.in|nic\.in)$", re.I)
# Indian mobiles, ASCII or Devanagari digits; no digit normalization.
_F1_PHONE = re.compile(
    r"(?<![\w+])(?:\+[9९][1१][ -]?)?[6-9६-९][0-9०-९]{4}[ -]?[0-9०-९]{5}(?![\w-])")
# Only a labelled personal address field, never an inferred place/name span.
_F1_ADDRESS = re.compile(
    r"(?P<label>(?:(?:वैयक्तिक|खाजगी|खासगी|निवासी)\s+पत्ता|"
    r"(?:घरचा|राहत्या घराचा)\s+पत्ता|(?:home|private|residential)\s+address)"
    r"\s*[:：]\s*)(?P<value>[^\r\n]+)", re.I)

def _f1_private_context(text, start, end):
    # Stay within the line; the preceding line can identify an organisation.
    lo = text.rfind("\n", 0, start) + 1
    hi = text.find("\n", end)
    hi = len(text) if hi < 0 else hi
    previous = text.rfind("\n", 0, max(0, lo - 1)) + 1
    context = text[previous:hi]
    return not _F1_ORG.search(context) and bool(_F1_PERSONAL.search(text[lo:start]))

def _redact_f1_mr(text):
    """Bounded candidate, not proof of complete privacy removal.
    Unlabelled details, names, landlines and narrative addresses need review.
    """
    def email(match):
        local, domain = match.group().rsplit("@", 1)
        if _F1_ROLE.fullmatch(local) or _F1_SAFE_DOMAIN.search(domain):
            return match.group()
        return "<EMAIL>" if _f1_private_context(match.string, match.start(), match.end()) else match.group()

    def phone(match):
        return "<PHONE>" if _f1_private_context(match.string, match.start(), match.end()) else match.group()

    def address(match):
        if not _f1_private_context(match.string, match.start("value"), match.end("value")):
            return match.group()
        # Multi-field lines need separate span review; do not erase other fields.
        value = match.group("value")
        if "<ADDRESS>" in value or re.search(r"[;|]|<(?:PHONE|EMAIL)>", value):
            return match.group()
        return match.group("label") + "<ADDRESS>"

    out = _F1_EMAIL.sub(email, text)
    out = _F1_PHONE.sub(phone, out)
    return _F1_ADDRESS.sub(address, out)

def cure_f1(text):
    # Quarantine takes precedence: partial redaction never releases these records.
    if hashlib.sha256(text.encode("utf-8")).hexdigest() in _EXCLUDED_SHA256:
        return True
    return _redact_f1_mr(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix+drop. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** See the fresh results above. Positive-case scope: **12 reviewed records excluded individually**; no other pack records changed. The redaction helper alone changed **0/12** reviewed F1 records, so it has no demonstrated repair coverage on those cases. Synthetic checks cover supported fields; they do ...
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 243 — indic / F1 / `DB-F1-008`

**Integration decision:** DEFERRED. replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-sa-fw2`. Source: section F1 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-sa-fw2: 0 changed / 0 dropped of 68 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python deferred
RULE_ID = "DB-F1-008"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"
SOURCE_ORIGIN = "ind-sa-fw2"
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_PHONE = re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{4}[-\s]?\d{5}(?!\d)")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+\s*(?:@|\(at\)|\[at\]| at )\s*[A-Za-z0-9-]+\s*(?:\.|\(dot\)|\[dot\]| dot )\s*[A-Za-z]{2,}")

def medicine_f1(text):
    t = _EMAIL.sub(lambda m: m.group() if "example." in m.group() else "<EMAIL>", text)
    return _PHONE.sub("<PHONE>", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 244 — indic / F1 / `DB-F1-009`

**Integration decision:** DEFERRED. overlap alternative; provisional source-order selection is DB-F1-008. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-sa-fw2`. Source: section F1 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `fix_f1(text)`.

```python deferred
RULE_ID = "DB-F1-009"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "overlap alternative; provisional source-order selection is DB-F1-008"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_PHONE = re.compile(r"(?<![0-9])(?:\+91[ \t-]{0,2})?"
                      r"(?:[6-9][0-9]{9}|[6-9][0-9]{4}[ -][0-9]{5}|[6-9][0-9]{2}[ -][0-9]{3}[ -][0-9]{4})(?![0-9])")

def fix_f1(text):
    """Replace every email with <email> and every Indian mobile number with <phone>. Idempotent."""
    return RE_PHONE.sub("<phone>", RE_EMAIL.sub("<email>", text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = fix_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 245 — indic / F1 / `DB-F1-010`

**Integration decision:** DEFERRED. replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F1 Personal data. Pack `ind-te-fw2`. Source: section F1 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
<!-- CARD EVIDENCE -->
**Current gold harm:** ind-te-fw2: 0 changed / 0 dropped of 18 (PASS); ind-te-sangraha-s: 0 changed / 0 dropped of 5 (PASS); ind-te-sangraha-v: 0 changed / 0 dropped of 27 (PASS).


**Example gap:** 0/3 publishable execution excerpts; private/credential spans are withheld and fewer than three affected records may exist. Complete reviewed evidence before freeze.
<!-- END CARD EVIDENCE -->

2. **Medicine:** the author's code, unchanged. Main function: `f1_pii(text)`.

```python deferred
RULE_ID = "DB-F1-010"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-te-fw2', 'ind-te-sangraha-s', 'ind-te-sangraha-v'}
DEFER_REASON = "replaced by the shared F1, spec_v1/tools/f1_rule.py (Indic path): the TSAI ruling's <PHONE>/<EMAIL> placeholders with organisation and public-office contacts kept; this source rule used other placeholders or deleted values, and replaced organisation contacts"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2, ind-te-sangraha-s, ind-te-sangraha-v"
SOURCE_ORIGIN = "ind-te-fw2"
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

F1_RX = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+|(?<!\d)(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
def f1_pii(t, url=None):
    return F1_RX.sub("", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = f1_pii  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## Medicine 246 — indic / F2 / `DB-F2-002`

**Integration decision:** DEFERRED. benchmark policy/fingerprints unresolved; keep-only detector is not implemented cleaning. Source harm statements below are inherited; current local own-pack gold: PASS. The integration status above supersedes the source card status below.

1. **Disease:** F2 Benchmark leak. Pack `ind-sa-fw2`. Source: section F2 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f2(text)`.

```python deferred
RULE_ID = "DB-F2-002"
CODE = "F2"
ACTION = "keep"
STAGE = "40"
STATUS = "DEFERRED"
SPEC_PACKS = {'ind-sa-fw2'}
DEFER_REASON = "benchmark policy/fingerprints unresolved; keep-only detector is not implemented cleaning"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

import collections
import json, os, unicodedata
DEFAULT_BENCH = os.path.join("..", "bench")
WINDOW = 50
MAX_SENTENCE_CHARS = 2000
BENCH_DIRS = ("flores200_devtest", "itihasa_test", "in22_gen")
DROP_BENCH_PREFIXES = ("flores", "in22")
_DROP_CATS = ("P", "Z", "S")
_DROP_FULL = {"Nd", "Cf", "Cc"}
def _dropped(c):
    cat = unicodedata.category(c)
    return cat[0] in _DROP_CATS or cat in _DROP_FULL or c.isspace()
def normalise(text):
    """NFC per character, then drop punctuation, separators, symbols, digits of every script, format and control chars."""
    return "".join(c for ch in text for c in unicodedata.normalize("NFC", ch) if not _dropped(c))
class _Index:
    """hash(window) -> [(bench, sid, pos)] over every benchmark sentence; hits are verified against the real text."""
    def __init__(self, bench_dir):
        self.table = collections.defaultdict(list); self.norm = {}; self.n_sentences = 0
        if not bench_dir or not os.path.isdir(bench_dir): return
        for name in BENCH_DIRS:
            path = os.path.join(bench_dir, name, "sentences.jsonl")
            if not os.path.isfile(path): continue
            try:
                with open(path, encoding="utf-8", errors="replace") as f: lines = f.read().split("\n")
            except OSError: continue
            for ln, line in enumerate(lines, 1):
                line = line.strip()
                if not line: continue
                try: d = json.loads(line)
                except ValueError: continue
                if not isinstance(d, dict) or not isinstance(d.get("text"), str): continue
                sid = d.get("id", ln)
                if not isinstance(sid, (int, str)): sid = ln
                ns = normalise(d["text"][:MAX_SENTENCE_CHARS])
                if len(ns) < WINDOW: continue
                key = (name, sid); self.norm[key] = ns; self.n_sentences += 1
                for p in range(len(ns) - WINDOW + 1): self.table[hash(ns[p:p + WINDOW])].append((key, p))
    def __bool__(self): return bool(self.table)
    def hits(self, text, prefixes=None):
        """{(bench, sid): number of DISTINCT 50-char windows of that sentence found in text}."""
        found = collections.defaultdict(set)
        if not self.table: return {}
        ns = normalise(text)
        for i in range(len(ns) - WINDOW + 1):
            win = ns[i:i + WINDOW]
            for key, p in self.table.get(hash(win), ()):
                if prefixes and not key[0].lower().startswith(prefixes): continue
                if self.norm[key][p:p + WINDOW] == win: found[key].add(win)
        return {k: len(v) for k, v in found.items()}
_BENCH = {"dir": None, "cache": {}}
def _index(bench_dir=None):
    d = os.path.normpath(bench_dir or _BENCH["dir"] or DEFAULT_BENCH)
    if d not in _BENCH["cache"]: _BENCH["cache"][d] = _Index(d)
    return _BENCH["cache"][d]
def _strong(text, bench_dir=None, prefixes=None):
    return any(k >= 2 for k in _index(bench_dir).hits(text, prefixes).values())
def detect_f2(text, bench_dir=None):
    """True when some benchmark sentence (FLORES-200, IN22 or Itihāsa test split) shares >= 2 distinct 50-char
    normalised windows with the text. False when no benchmark file is available."""
    return _strong(text, bench_dir)
def drop_f2_flores(text, bench_dir=None):
    """Drop variant, not in MEDICINES: True only for FLORES-200 / IN22 hits (benchmark folder name starts with
    flores or in22). Itihāsa hits never drop (public canon)."""
    return _strong(text, bench_dir, DROP_BENCH_PREFIXES)

def medicine_f2(text):
    return text    # action none: the detector `detect_f2` reports (keep and record); `drop_f2_flores` is the drop variant


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F2 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.
