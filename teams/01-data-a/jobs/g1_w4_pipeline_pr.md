# G1: parallelize cleaning and fix v1.1 privacy and Sanskrit handling

## Summary

Prepare corpus-v1 cleaning in parallel, correct scoped v1.1 cleaning issues, and generate full-scope or explicit 33-pack jobs using MinHash.

- Clean parts in spawned processes, with four workers by default and an optional `stages.clean.workers` override. Preserve deterministic output/report ordering, failure records and resume behavior.
- Fix shared F1 dispatch for `code-*` rows labelled `code`: select the parser from `pack_id` while preserving explicit language labels.
- Fix Sanskrit `DB-B4-004` (#734): preserve verse numbers and years, including Devanagari digits, while retaining wiki-markup removal.
- Fix English `DA-F1-005` masking explicitly labelled binary values as phone numbers. Ambiguous numbers and explicit phone contacts retain the existing masking policy.
- Stage all seven tree-sitter grammars during network-enabled setup and reject run preparation when any grammar is missing.
- Add `build_inventory.py --packs-file` for exactly 33 distinct approved pack IDs. Freeze selected/deferred packs, require both splits for each selected pack, and generate exactly their licence/shard metadata. Full 38-pack preparation remains available.
- Explicitly select `minhash_overlap.py` in generated production configs, with the appropriate full or partial settings.
- Incorporate #89's 16-worker MinHash cap, fresh-output sizing tool, failure propagation, requested/actual scale reporting and clean → sizing → gate → adopt-clean runbook. Staged-data measurements remain pending.
- Update spec/build sources, regenerate `clean.py`, and pin the active cleaner.

## Fresh cleaner harm validation — 23 Nov 2026 (replaced after scoped #86 changes)

**Prepared and validated locally on `g1-w4-pipeline` after merged #89; these new edits are not committed or pushed yet.**

Rebuilt cleaner SHA-256: `aa1f8e534820e5218f74c9bdec4ada217002ff467ee00256113ba59978e2b393`. Independent rebuild matches. Active pipeline and tokenizer-sample job configs pin this build.

Five preservation subsets were extracted from #86's `collated_medicine.md` at `d9b2efe8689fee5abdc26a523d847018a732d344`, retaining existing active IDs, scopes and order:

| Active rule | Extracted subset |
|---|---|
| `DA-A6-001` | From `DA-A6-004`: preserve consecutive Cyrillic runs and Go test/testdata URLs |
| `DA-C2-004` | From `DA-C2-011`: line-start repeated leads and blank-line cut boundaries |
| `DA-C2-003` | From `DA-C2-009/010`: fenced-code protection only |
| `DA-C3-003` | From `DA-C3-009`: closing `”`, `’`, `»` only, within the existing four-pack scope |
| `DA-F1-005` | From `DA-F1-007/009`: DOI exclusion only; existing binary protection retained |

No long-prose trimming, last-word-test withdrawal, numeric-table heuristic, year-run exemption, broader phone policy or licence removal is adopted. Shared F1 is unchanged.

Re-ran 4,768 gold documents across 33 testable packs using Data A's `harmtest/harm_test.py` APIs and Data B's `tools/harm_test_indic.py` execution/verdict/Unicode-audit APIs. Inputs: the 38 local original pack Parquets and each team's `gold/` CSVs. Each applicable rule was tested alone, then the complete pipeline; no gold IDs were excluded.

- **31 supported packs: 27 PASS, 4 FAIL. Every per-rule and pipeline result, including affected IDs, matches the previous fresh run.**
- All five amended rules touch **zero gold documents**. Existing English F1, code shared F1 and Sanskrit `DB-B4-004` gold checks remain unchanged.
- Two unsupported packs, `cadj-commits` and `ind-ta-fw2`, pass through unchanged; this is not cleaning coverage.
- Five lack gold: `cadj-notebooks`, `cadj-stackexchange`, `ind-ml-fw2`, `ind-or-fw2`, `ind-ta-sangraha-s`.
- No execution errors, Indic joiner-count violations or normal-form violations.

| Full-pipeline raw harm failure | Gold | Changed | Dropped |
|---|---:|---:|---:|
| en-nemotroncc | 129 | 2 | 0 |
| math-finemath | 86 | 1 | 1 |
| sci-finepdfs | 202 | 4 | 1 |
| ind-te-sangraha-v | 80 | 2 | 0 |

These are the same 11 affected IDs as the historical report, which classified ten as gold contradictions and one as a short-document false positive. This rerun does not waive the four raw failures or supply fresh human adjudication.

Compared both full pipelines on **19,000 documents across all 38 sample packs**: two non-gold outputs differ (C++ genuine Cyrillic and synthetic English fenced lines retained); no new drops or new idempotence failures. The five amended rules have zero out-of-scope violations on those packs. This does not repeat all unmodified rules' historical out-of-scope checks.

The legacy `run_harm_suite.py` was retried and still requires the absent `teams/01-data-a/spec/spec_v1.md`; the current cleaner was tested through the APIs above. Reproduction adapter: `spec_v1_1/scripts/run_current_harm.py`.

The previous fresh reports/logs in `spec_v1_1/results/cleaner/harm_2026_11_23/` and the current sections of `harm_tests.md` and `README_clean.md` are replaced locally. Evidence includes hashes, per-rule reports, sample comparison, and test logs.

## Other validation

- Cleaner unit/regression suite: **1,946 passed, 9 subtests passed**, including 31 new guard-boundary cases.
- Clean-job and production-preparation suite: **125 passed**.
- #89 integration check, before these cleaner edits: 15 config checks passed; **706 tests passed, 2 skipped**, with F2 pool tests separately excluded by that checker. This is sizing preparation, not production integration evidence.

## Scope and pending release work

H3 remains report-only. #86 remains a separate audit/proposal PR; only the five documented subsets are implemented locally. Cadj email handling, broader proposal adoption and H3 removal-policy changes remain separate.

Before corpus-v1 execution:

- Review the four raw harm failures and record their disposition; missing gold and unsupported scopes remain explicit limitations.
- Commit/push these scoped cleaner changes and replaced evidence, then finalize the release commit pin.
- Use the confirmed `staged_packs_33.json` selection and verify staged files/source provenance; keep the five blocked sources excluded.
- Run staged-data MinHash sizing at 1x/2x/4x after clean; validate RAM across all measured factors and the total remaining job time including sizing.
- Run the final integration/restart rehearsal through MinHash, dedup, F2, ledger, shards and reconciliation. Sample harm checks do not establish production throughput or end-to-end readiness.
