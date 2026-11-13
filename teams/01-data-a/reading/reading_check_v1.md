# reading_check_v1: the Week 2 reading audits of the cleaned sample, all four domains

**Built** by `spec_v1_1/scripts/build_reading_check.py` from the collector run of 2026-11-13 13:13 UTC (`spec_v1_1/results/reading/`) and from `spec_v1_1/sheets/NEW_DISEASES.md`. Don't edit this file by hand: run the collector, then this script.

**Kinds of row** (from the reading README):
- **missed:** Spec v1 has a rule for the disease, and the cleaned doc still has it.
- **new:** a disease that Spec v1 has no rule for.
- **harm:** a Spec v1 rule damaged real content.

**Occurrence rate:** the distinct docs with the disease, divided by the docs read in its domain, × 100.

**Flag:** a new disease at 1% or more, which needs a medicine and a harm test for Spec v1.1. "New" means not in `diagnosis/DISEASES.md`. A row the reader marked new that `DISEASES.md` already describes is shown, but not flagged.

## Audits per domain

| domain | docs read | readers with a reading file | readers with no file yet |
|---|---|---|---|
| english | 200 | aneesha 50, kunal 50, narasimhatejav 50, smita 50 | none |
| code | 200 | narasimhatejav 100, revant 100 | none |
| math | 299 | pyru 199, satyanarayana 100 | none |
| science | 200 | aditeya 100, utkarsh 100 | none |

Reading PRs used: mittalutkarsh/era-v5-lab#9, mittalutkarsh/era-v5-lab#8, mittalutkarsh/era-v5-lab#7, mittalutkarsh/era-v5-lab#6, mittalutkarsh/era-v5-lab#4, mittalutkarsh/era-v5-lab#3, mittalutkarsh/era-v5-lab#2, patilvijay23/era-v5-lab#36.

## 1. Diseases missed by Spec v1

A disease Spec v1 has a rule for, still in the cleaned doc. A code with no Spec v1 rule for the family ("none") is a gap in Spec v1's pack scope.

### english

| code | docs | rate | readers | Spec v1 rules for this family |
|---|---|---|---|---|
| C1 | 38 | 19.0% | aneesha kunal narasimhatejav smita | DA-C1-006 CANDIDATE |
| C3 | 6 | 3.0% | aneesha | DA-C3-001 CANDIDATE; DA-C3-003 CANDIDATE |
| B4 | 3 | 1.5% | kunal | DA-B4-007 CANDIDATE; DA-B4-008 CANDIDATE; DA-B4-012 CANDIDATE; DA-B4-010 CANDIDATE; DA-B4-011 CANDIDATE |
| D3 | 3 | 1.5% | aneesha narasimhatejav | DA-D3-003 CANDIDATE |
| B1 | 1 | 0.5% | aneesha | DA-B1-002 CANDIDATE |
| F1 | 1 | 0.5% | smita | DA-F1-005 CANDIDATE |

### code

| code | docs | rate | readers | Spec v1 rules for this family |
|---|---|---|---|---|
| E4 | 6 | 3.0% | narasimhatejav revant | DA-E4-005 CANDIDATE; DA-E4-010 CANDIDATE; DA-E4-009 CANDIDATE; DA-E4-007 CANDIDATE |
| E1 | 4 | 2.0% | narasimhatejav revant | DA-E1-001 CANDIDATE; DA-E1-004 CANDIDATE; DA-E1-008 CANDIDATE; DA-E1-006 CANDIDATE; DA-E1-005 CANDIDATE; DA-E1-007 CANDIDATE |
| C3 | 2 | 1.0% | revant | DA-C3-002 CANDIDATE |
| C1 | 1 | 0.5% | narasimhatejav | DA-C1-004 CANDIDATE; DA-C1-005 CANDIDATE |
| E2 | 1 | 0.5% | narasimhatejav | DA-E2-001 CANDIDATE |
| E3 | 1 | 0.5% | narasimhatejav | DA-E3-003 CANDIDATE; DA-E3-004 CANDIDATE |

### math

| code | docs | rate | readers | Spec v1 rules for this family |
|---|---|---|---|---|
| C1 | 167 | 55.9% | pyru satyanarayana | DA-C1-001 CANDIDATE |
| C5 | 22 | 7.4% | pyru satyanarayana | DA-C5-001 CANDIDATE; DA-C5-006 CANDIDATE |
| C2 | 20 | 6.7% | pyru satyanarayana | DA-C2-001 CANDIDATE |
| B5 | 18 | 6.0% | pyru | DA-B5-001 CANDIDATE |
| A3 | 7 | 2.3% | pyru satyanarayana | DA-A3-001 CANDIDATE |
| B4 | 5 | 1.7% | pyru satyanarayana | DA-B4-001 CANDIDATE |
| C3 | 4 | 1.3% | pyru satyanarayana | DA-C3-004 CANDIDATE; DA-C3-005 CANDIDATE |
| B2 | 3 | 1.0% | pyru | DA-B2-001 CANDIDATE |
| D3 | 1 | 0.3% | pyru | DA-D3-005 CANDIDATE |
| F2 | 1 | 0.3% | pyru | none |

### science

| code | docs | rate | readers | Spec v1 rules for this family |
|---|---|---|---|---|
| C1 | 20 | 10.0% | aditeya utkarsh | DA-C1-007 ? |
| F1 | 8 | 4.0% | aditeya utkarsh | DA-F1-006 ? |
| C2 | 6 | 3.0% | aditeya utkarsh | DA-C2-004 ? |
| A5 | 4 | 2.0% | utkarsh | none |
| A1 | 3 | 1.5% | aditeya utkarsh | DA-A1-006 ? |
| C3 | 3 | 1.5% | aditeya | DA-C3-006 ? |
| D1 | 3 | 1.5% | aditeya utkarsh | DA-D1-001 ? |
| B4 | 1 | 0.5% | utkarsh | DA-B4-013 ? |

## 2. New diseases

### english

| code | docs | rate | ≥ 1% | status | Spec v1.1 code and rule |
|---|---|---|---|---|---|
| C4 | 4 | 2.0% | yes | not new | in DISEASES.md as C4 two documents joined |
| NEW-factual-error | 4 | 2.0% | yes | new | D7, `DA-D7-001` |
| NEW-appended-qa | 3 | 1.5% | yes | new | D6, `DA-D6-002, withdrawn` |
| NEW-missing-spaces | 2 | 1.0% | yes | new | A8, `DA-A8-003` |
| NEW-abstract-with-no-paper-behind-it | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-ad-disguised-as-an-article | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-bibtex-record | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-clickbait-and-promotional-tone | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-footnote-whose-main-content-is-missing | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-grammar-error | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-header-details-stripped | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-heading-stuck-to-the-paragraph | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-hyphen-split-words | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-leftover-hyphens-from-line-breaks | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-mismatched-quotation-marks | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-missing-code | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-missing-space-after-a-full-stop | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-old-place-name-spelling | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-pronoun-slip | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-spliced-sentences | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-squashed-into-prose | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-text-describing-a-missing-video | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-text-with-the-link-gone | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-too-few-words | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-two-pieces-stuck-together-with-no-space | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-two-words-stuck-together | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-typos-and-grammar-errors | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |

### code

None found.

### math

| code | docs | rate | ≥ 1% | status | Spec v1.1 code and rule |
|---|---|---|---|---|---|
| NEW-missing-formulas | 29 | 9.7% | yes | new | C7, `DA-C7-001` |
| NEW-flattened-formulas | 22 | 7.4% | yes | new | C8, `DA-C8-001` |
| NEW-seo-filler | 15 | 5.0% | yes | new | C9, `DA-C9-001` |
| NEW-missing-spaces | 13 | 4.3% | yes | new | A8, `DA-A8-001` |
| NEW-merged-table-cells | 11 | 3.7% | yes | new | C8, `DA-C8-002` |
| NEW-template-pages | 9 | 3.0% | yes | new | C9, `DA-C9-003` |
| NEW-ai-generated-text | 8 | 2.7% | yes | new | D6, `DA-D6-001` |
| NEW-missing-figures | 5 | 1.7% | yes | new | C7, `DA-C7-002` |
| NEW-aggregated-questions | 4 | 1.3% | yes | not new | in DISEASES.md as C4 two documents joined |
| B1 | 3 | 1.0% | yes | not new | in DISEASES.md as B1 HTML entities |
| D4 | 2 | 0.7% | no | not new | in DISEASES.md (D4) |
| E2 | 2 | 0.7% | no | not new | in DISEASES.md (E2) |
| NEW-orphan-footnote-markers | 2 | 0.7% | no | new | not yet in NEW_DISEASES.md |
| A4 | 1 | 0.3% | no | not new | in DISEASES.md (A4) |
| C4 | 1 | 0.3% | no | not new | in DISEASES.md (C4) |
| D2 | 1 | 0.3% | no | not new | in DISEASES.md (D2) |
| E1 | 1 | 0.3% | no | not new | in DISEASES.md (E1) |
| NEW-dropped-ligatures | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |
| NEW-hyphen-split-words | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |
| NEW-interleaved-columns | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |
| NEW-merged-documents | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |
| NEW-missing-code-lines | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |
| NEW-missing-interactive-content | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |
| NEW-offtopic-poll | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |
| NEW-orphan-figure-labels | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |
| NEW-truncated-previews | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |
| NEW-unattributed-copy | 1 | 0.3% | no | new | not yet in NEW_DISEASES.md |

### science

| code | docs | rate | ≥ 1% | status | Spec v1.1 code and rule |
|---|---|---|---|---|---|
| NEW-page-artifact | 9 | 4.5% | yes | new | C8, `DA-C8-005` |
| NEW-underscore-blanks | 7 | 3.5% | yes | new | B6, `DA-B6-001` |
| NEW-pdf-ligatures | 5 | 2.5% | yes | not new | in DISEASES.md as A5 wrong normal form (ligatures, as in math's DA-A5-001) |
| NEW-hyphen-split-words | 3 | 1.5% | yes | new | A7, `DA-A7-001` |
| NEW-merged-table-cells | 3 | 1.5% | yes | new | C8, `DA-C8-003` |
| NEW-missing-spaces | 3 | 1.5% | yes | new | A8, `DA-A8-002` |
| NEW-missing-table-data | 3 | 1.5% | yes | new | C7, `DA-C7-003` |
| NEW-drop-cap-split | 2 | 1.0% | yes | new | A7, `DA-A7-002` |
| NEW-missing-figures | 2 | 1.0% | yes | new | C7, `DA-C7-004` |
| NEW-near-empty | 2 | 1.0% | yes | new | C7, `DA-C7-005` |
| NEW-reading-order | 2 | 1.0% | yes | new | C8, `DA-C8-004` |
| NEW-seo-filler | 2 | 1.0% | yes | new | C9, `DA-C9-002` |
| NEW-small-caps-split | 2 | 1.0% | yes | new | A7, `DA-A7-003` |
| NEW-toc-dot-leaders | 2 | 1.0% | yes | not new | in DISEASES.md as C1 boilerplate |
| C5 | 1 | 0.5% | no | not new | in DISEASES.md as C5 lists of keywords or links |
| NEW-detached-diacritics | 1 | 0.5% | no | new | A9, no ID yet (DA-A9-001) |
| NEW-empty-table-rows | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-figure-only-doc | 1 | 0.5% | no | new | C7, no ID yet (DA-C7-006) |
| NEW-generated-image-captions | 1 | 0.5% | no | new | D6, no ID yet (DA-D6-003) |
| NEW-huge-tables | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-latex-residue | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-orphan-figure-labels | 1 | 0.5% | no | new | C7, no ID yet (DA-C7-006) |
| NEW-pdf-quote-glyphs | 1 | 0.5% | no | not new | in DISEASES.md as A6 wrong or mixed script (wrong glyphs, as in math's DA-A6-001) |
| NEW-personal-names-ages | 1 | 0.5% | no | not new | in DISEASES.md as F1 personal data (names of private people with ages) |
| NEW-prose-in-code-fence | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-scrambled-vertical-text | 1 | 0.5% | no | new | not yet in NEW_DISEASES.md |
| NEW-split-superscripts | 1 | 0.5% | no | new | C8, no ID yet (DA-C8-006) |
| NEW-spun-text | 1 | 0.5% | no | new | C9, no ID yet (with DA-C9-002) |

## 3. Harm: Spec v1 rules that damaged real content

### english

| rule | docs | rate | readers | Spec v1 rule |
|---|---|---|---|---|
| DA-C2-003 | 1 | 0.5% | smita | DA-C2-003 english CANDIDATE |

### code

None found.

### math

| rule | docs | rate | readers | Spec v1 rule |
|---|---|---|---|---|
| DA-C2-001 | 6 | 2.0% | pyru | DA-C2-001 math CANDIDATE |
| DA-D3-005 | 1 | 0.3% | pyru | DA-D3-005 math CANDIDATE |

### science

None found.

## 4. Flagged: new diseases at 1% or more

| domain | code | docs | docs read | rate | Spec v1.1 code and rule |
|---|---|---|---|---|---|
| english | NEW-factual-error | 4 | 200 | 2.0% | D7, `DA-D7-001` |
| english | NEW-appended-qa | 3 | 200 | 1.5% | D6, `DA-D6-002, withdrawn` |
| english | NEW-missing-spaces | 2 | 200 | 1.0% | A8, `DA-A8-003` |
| math | NEW-missing-formulas | 29 | 299 | 9.7% | C7, `DA-C7-001` |
| math | NEW-flattened-formulas | 22 | 299 | 7.4% | C8, `DA-C8-001` |
| math | NEW-seo-filler | 15 | 299 | 5.0% | C9, `DA-C9-001` |
| math | NEW-missing-spaces | 13 | 299 | 4.3% | A8, `DA-A8-001` |
| math | NEW-merged-table-cells | 11 | 299 | 3.7% | C8, `DA-C8-002` |
| math | NEW-template-pages | 9 | 299 | 3.0% | C9, `DA-C9-003` |
| math | NEW-ai-generated-text | 8 | 299 | 2.7% | D6, `DA-D6-001` |
| math | NEW-missing-figures | 5 | 299 | 1.7% | C7, `DA-C7-002` |
| science | NEW-page-artifact | 9 | 200 | 4.5% | C8, `DA-C8-005` |
| science | NEW-underscore-blanks | 7 | 200 | 3.5% | B6, `DA-B6-001` |
| science | NEW-hyphen-split-words | 3 | 200 | 1.5% | A7, `DA-A7-001` |
| science | NEW-merged-table-cells | 3 | 200 | 1.5% | C8, `DA-C8-003` |
| science | NEW-missing-spaces | 3 | 200 | 1.5% | A8, `DA-A8-002` |
| science | NEW-missing-table-data | 3 | 200 | 1.5% | C7, `DA-C7-003` |
| science | NEW-drop-cap-split | 2 | 200 | 1.0% | A7, `DA-A7-002` |
| science | NEW-missing-figures | 2 | 200 | 1.0% | C7, `DA-C7-004` |
| science | NEW-near-empty | 2 | 200 | 1.0% | C7, `DA-C7-005` |
| science | NEW-reading-order | 2 | 200 | 1.0% | C8, `DA-C8-004` |
| science | NEW-seo-filler | 2 | 200 | 1.0% | C9, `DA-C9-002` |
| science | NEW-small-caps-split | 2 | 200 | 1.0% | A7, `DA-A7-003` |

**Flagged per domain:** english 3, code 0, math 8, science 12.

**Marked new by the reader at 1% or more, but already in `DISEASES.md`:** english C4 (2.0%), math NEW-aggregated-questions (1.3%), math B1 (1.0%), science NEW-pdf-ligatures (2.5%), science NEW-toc-dot-leaders (1.0%).

## Notes

- **Rows by source:** ai 520, manual 130. `ai` means an AI tool suggested the row and the reader checked it. Each row is a first pass until a second reader has checked it.
- **Collector warning:** patilvijay23/era-v5-lab#36: base is patilvijay23/era-v5-lab:g1-spec-v1-1, not mittalutkarsh/era-v5-lab:g1-reading
