# clean() harm tests: spec v1.1

## cadj-commits e-mail F1 (#88): 24 Nov 2026

Cleaner SHA-256 `d275556ee87a259b05ac5e474ed40b569c2e821aaaffa99d5d07035e40948989`, rebuilt byte for byte from
`sheets/specv1_1.md` and `build/f1_rule.py`. The only change from the `aa1f8e53…` cleaner tested below: the shared F1
masks private e-mail addresses on cadj-commits (family `code-adjacent`, an empty pipeline), as in the cadj-commits
medicine 1, with test domains and `mail@` kept. No phone or address masking, never a drop. cadj-notebooks,
cadj-stackexchange and the medicine's LinkedIn profile URLs are deferred; those packs still pass through unchanged.

- **cadj-commits gold** (`teams/02-data-b/gold`, week-1 pack): **0 of 413 changed or dropped, PASS** (limit 4).
- **Week-1 packs:** cadj-commits 40 of 500 changed, each only by `<EMAIL>`, 0 drops, a second pass changes nothing;
  cadj-notebooks 0 of 500. It fixes 40 of the 45 documents the cadj-commits readers labelled F1; the other 5 are not
  e-mail cases.
- **Every other pack is unchanged:** on the first 1,000 documents of each of the 37 packs of sample v0, the output equals
  the `aa1f8e53…` cleaner's on all 36 packs other than cadj-commits (36,000 documents); on cadj-commits 60 differ, each only
  by `<EMAIL>`. So the 23 Nov results below hold for every other pack.
- **cadj-commits, whole sample v0:** 4,529 of 74,753 documents changed, 7,954 addresses masked, 0 drops, no other change.
- The steps of `scripts/run_current_harm.py` on cadj-commits (each rule alone, then `clean()`): shared F1 PASS and
  `clean()` PASS, 0 changed, 0 dropped.
- Cleaner suite: 1,952 passed, 9 subtests passed.

Evidence (IDs and counts only): [summary](harm_2026_11_24_cadj_commits/summary.json), made by
[check_cadj_commits.py](harm_2026_11_24_cadj_commits/check_cadj_commits.py).

## Fresh validation: 23 Nov 2026

Rebuilt `spec_v1_1/clean.py` from `sheets/specv1_1.md` and `build/f1_rule.py`.
This replaces the previous fresh validation after the scoped #86 amendments.
The generated cleaner SHA-256 is `aa1f8e534820e5218f74c9bdec4ada217002ff467ee00256113ba59978e2b393`; the build-agreement test passes.

Five scoped preservation amendments were extracted from
[#86](https://github.com/patilvijay23/era-v5-lab/pull/86), source commit
`d9b2efe8689fee5abdc26a523d847018a732d344`, into the existing spec v1.1 rules:

| Active rule | Extracted change | Source card |
|---|---|---|
| `DA-A6-001` | Preserve consecutive Cyrillic runs and Go test/testdata URLs | `DA-A6-004` |
| `DA-C2-004` | Require a line-start repeated lead; cut partial copies only at blank-line boundaries | `DA-C2-011` |
| `DA-C2-003` | Exclude fenced Markdown code from repeated-line removal | `DA-C2-009/010`, fence subset |
| `DA-C3-003` | Recognize closing `”`, `’`, `»` as end punctuation | `DA-C3-009`, punctuation subset |
| `DA-F1-005` | Preserve digits within a DOI; retain the existing binary-value guard | `DA-F1-007/009`, DOI subset |

Rule IDs, rule order, pack scopes and shared F1 are unchanged. Closing punctuation
uses the existing four-English-pack scope consistently with straight quotes;
the source card's long-prose trimming is not adopted. Numeric-table heuristics,
year-run exemptions, broader phone/contact policy, licence removal and the
remaining proposal cards are deferred. #86 is not merged by this extraction.


The run used the 38 original pack Parquets provided locally, Data A gold in
`teams/01-data-a/gold`, and Data B gold in `teams/02-data-b/gold`. Each applicable
rule was tested alone, followed by the full `clean()` pipeline, on each pack's
own gold set using `harmtest/harm_test.py`'s APIs. Data B packs also used
`tools/harm_test_indic.py`'s execution, verdict and Unicode-audit APIs, preserving
pack/language/URL metadata through the adapter. No gold IDs were excluded.
The amended rules were also checked outside their scopes on all 19,000
documents in the 38 sample packs: zero violations. This is not a repeat of the
historical out-of-scope checks for every unmodified rule.

- **4,768 gold documents across 33 testable packs.** Of the 31 supported packs,
  **27 PASS and 4 FAIL**. Two other testable packs, `cadj-commits` and
  `ind-ta-fw2`, pass through unchanged and have no cleaning rules; their PASS
  is not evidence of implemented cleaning coverage.
- **Five NOT TESTABLE:** gold CSVs are missing for `cadj-notebooks`,
  `cadj-stackexchange`, `ind-ml-fw2`, `ind-or-fw2`, `ind-ta-sangraha-s`.
- No rule execution errors, Indic joiner-count violations or Unicode normal-form
  violations were observed.
- The amended English `DA-F1-005` on all four English packs, shared F1 on all
  six code packs, and Sanskrit `DB-B4-004` each **PASS with zero gold documents
  changed or dropped**.
- All five amended rules **PASS with zero gold changes or drops**.
- Cleaner unit/regression suite: **1,946 passed, 9 subtests passed**.

| Pack failing the raw full-pipeline harm limit | Gold | Changed | Dropped |
|---|---:|---:|---:|
| en-nemotroncc | 129 | 2 | 0 |
| math-finemath | 86 | 1 | 1 |
| sci-finepdfs | 202 | 4 | 1 |
| ind-te-sangraha-v | 80 | 2 | 0 |

The 11 affected IDs are exactly those listed in the historical report below.
That historical report classifies ten as gold contradictions and one as a
short-document false positive. This run reproduces their identities; it does
not constitute a fresh human adjudication or waive the four raw failures.
The changed Bengali gold set has 145 documents, compared with 137 in the
historical report; per-input hashes are recorded for the fresh run.

`run_harm_suite.py` was attempted but cannot run: it requires the absent legacy
`teams/01-data-a/spec/spec_v1.md` inventory, not the current executable sheet.
The current cleaner was tested through the APIs above instead. These results
cover the five subsets above in the current cleaner; they do not validate the
remaining #86 proposal cards, production-scale throughput, or a full MinHash/sharding integration run.

To reproduce the API-based run from the repository root (writes to a new
output folder; exits nonzero for failures or untestable packs):

```bash
python teams/01-data-a/spec_v1_1/scripts/run_current_harm.py --packs <original-packs-folder> --out out/harm-rerun
```

The full-pipeline comparison against cleaner `4b5e46ba…` covers all 38 sample
packs (19,000 documents). Outputs differ for two non-gold documents:
`code-cpp/782bc9665f0acdf7` (genuine Cyrillic retained) and
`en-nemotroncc-synth/ac2d7bac43b4a937` (fenced repeated lines retained).
The A6 rule alone also preserves `code-go/48b3b124a7aaa5fc` (testdata), which
is dropped later by the existing pipeline. No new drops or new idempotence
failures were found. These are sample checks, not a fresh human audit.
Clean-job and production-preparation tests: **125 PASS**.

Evidence (IDs, counts and hashes only): [summary CSV](harm_2026_11_23/summary.csv),
[provenance and coverage](harm_2026_11_23/summary.json),
[per-pack/per-rule reports](harm_2026_11_23/reports.json),
[run log](harm_2026_11_23/run.txt), [rebuild log](harm_2026_11_23/rebuild.txt),
[legacy-runner limitation](harm_2026_11_23/legacy-suite.txt),
[sample comparison](harm_2026_11_23/comparison.json),
[cleaner tests](harm_2026_11_23/cleaner-tests.txt),
[job tests](harm_2026_11_23/job-tests.txt).

## Historical validation: 17 Nov 2026

`spec_v1_1/clean.py` (sha256 `6a57276c0e83…`, built from `sheets/specv1_1.md`) on TSAI's 500-doc sample packs, one for each pack it has rules for, 17 Nov 2026. It was run on the samples only, not on the full packs.
- **The tool:** `spec_v1/validate/make_harm_tests.py`, run through `use_clean.py`, with `harmtest/harm_test.py` run as it is. On each pack it runs:
  - `clean()` on the gold docs;
  - each rule alone on the gold docs;
  - every rule that doesn't cover the pack, on all 500 docs of the sample pack, which must change nothing.
- **The gold:** Data A's (`teams/01-data-a/gold/`) for 13 packs, and Data B's (`teams/02-data-b/gold/`) for 18 Indic packs. Each pack is tested on its own gold set. The limit is `max(1, floor(1% of gold))`.
- **The packs:** TSAI's sample packs, 500 docs each, the same files as in #244 (sha256 checked).

From `teams/01-data-a`, where `<checkout>` is a copy of the repository whose `teams/01-data-a/gold/` also holds Data B's Indic gold files (the harness reads gold from there):

```
python3 -I spec_v1_1/use_clean.py spec_v1/validate/make_harm_tests.py <checkout> <packs folder> --out <out>/harm_tests.md --results <out>
```

Last lines (1 min 34 s; exit 1 because of the gold contradictions):

```
ind-te-fw2 PASS gold 0 0 | not passing: [] | out of scope acting: []
ind-te-sangraha-s PASS gold 0 0 | not passing: [] | out of scope acting: []
ind-te-sangraha-v FAIL gold 2 0 | not passing: [('DB-C6-001', 'FAIL'), ('C6', 'FAIL')] | out of scope acting: []
wrote <out>/harm_tests.md | not run: []
```

| pack | gold docs (limit) | `clean()`: changed + dropped | result | without the gold contradictions |
|---|---|---|---|---|
| code-cpp, code-go, code-java, code-js-ts, code-python, code-rust | 122, 163, 116, 204, 141, 234 | 0 each | PASS | — |
| en-dclm, en-fineweb-edu, en-nemotroncc-synth | 62, 158, 326 | 0 each | PASS | — |
| en-nemotroncc | 129 (1) | 2: `056cc9bc44c927e2` (`DA-A8-003`), `fd16036899796ca4` (`DA-A8-004`) | **FAIL** | 0/127 PASS |
| math-finemath | 86 (1) | 2: `2d328b828fa97706` (`DA-A8-001`), `0f119a596e8b7f63` dropped (`DA-C9-003`) | **FAIL** | 0/84 PASS |
| math-megamath | 26 (1) | 0 | PASS | — |
| sci-finepdfs | 202 (2) | 5: `920855df51f37db8` (`DA-A7-001`); `4b958ac1f45443b5`, `d0a0a41263e845f5`, `eb6ad9726f2d7ddd` (`DA-C7-004`); `b6fd81dbf90b0d17` dropped (`DA-C7-005`, a false positive) | **FAIL** | 1/198 PASS |
| ind-te-sangraha-v | 80 (1) | 2: `01418489e7410bdf`, `85644a4840025b6f` (`DB-C6-001`) | **FAIL** | 0/78 PASS |
| ind-bn-fw2, ind-hi-fw2, ind-hi-indiccorp | 227 (2), 218 (2), 425 (4) | 2 each (1 changed, 1 dropped) | PASS | — |
| ind-hi-sangraha-v | 219 (2) | 2 | PASS | — |
| ind-bn-sangraha-v, ind-kn-fw2, ind-mr-fw2, ind-sa-fw2, ind-ta-sangraha-v | 137, 115, 158, 71, 141 | 1 each | PASS | — |
| ind-gu-fw2, ind-hi-hplt, ind-hi-sangraha-s, ind-kn-sangraha-s, ind-kn-sangraha-v, ind-mr-sangraha-v, ind-te-fw2, ind-te-sangraha-s | 80, 37, 24, 22, 99, 99, 17, 24 | 0 each | PASS | — |

**Why 4 packs FAIL.** A pack fails when `clean()` changes or drops more of its gold docs than the limit. On these 4 packs, the docs over the limit are the 11 that spec v1.1's rules touch:

| pack | gold doc | rule | what the doc holds |
|---|---|---|---|
| en-nemotroncc | `056cc9bc44c927e2` | `DA-A8-003` | two sentences run together, with no space after the full stop |
| en-nemotroncc | `fd16036899796ca4` | `DA-A8-004` | a quote run into the speaker's name |
| math-finemath | `2d328b828fa97706` | `DA-A8-001` | two sentences run together, with no space after the full stop |
| math-finemath | `0f119a596e8b7f63`, dropped | `DA-C9-003` | a converter template page |
| sci-finepdfs | `920855df51f37db8` | `DA-A7-001` | a word split in extraction |
| sci-finepdfs | `4b958ac1f45443b5`, `d0a0a41263e845f5`, `eb6ad9726f2d7ddd` | `DA-C7-004` | empty image links |
| sci-finepdfs | `b6fd81dbf90b0d17`, dropped | `DA-C7-005` | a complete certificate of 220 characters, under the rule's 250 |
| ind-te-sangraha-v | `01418489e7410bdf`, `85644a4840025b6f` | `DB-C6-001` | a bare `..`, which the pack's reader labelled C6 in other docs |

- **10 are gold contradictions:** the gold marks the doc clean, but it holds the disease its rule targets.
- **1 is a false positive:** `DA-C7-005` drops `b6fd81dbf90b0d17`, a complete short doc. That is within the rule's own limit (1 of 202).
- **Without the 10 gold contradictions, all 4 packs pass:** en-nemotroncc 0/127, math-finemath 0/84, sci-finepdfs 1/198 and ind-te-sangraha-v 0/78. As `sheets/NEW_DISEASES.md` records (section "Open"), gold contradictions are left out of the count for their rule only, and re-read at the next gold refresh.
- **None of these rules is quarantined or turned off.** Like every rule of `sheets/specv1_1.md`, they are candidates and run in `clean.py`. The re-read of these gold docs at the next gold refresh is a release gate.
- **Spec v1.1 adds only these 11 gold docs.**
- **The other Indic gold docs** are changed by spec v1's own rules, exactly as spec v1's `clean.py` on TSAI main changes them, all within the limit. On ind-kn-fw2 and ind-ta-sangraha-v, that rule is the shared F1 (`f1_rule.py`).
- **Scope holds:** on all 31 sample packs, no rule that doesn't cover the pack changed a doc.
- **Not tested:**
  - cadj-commits: `clean()` has no rules for it and keeps every doc (`tests/test_clean.py`);
  - no gold set, so NOT TESTABLE: cadj-notebooks, cadj-stackexchange, ind-ml-fw2, ind-or-fw2, ind-ta-fw2 and ind-ta-sangraha-s.
