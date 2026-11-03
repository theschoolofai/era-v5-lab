# Indic integration

The generated cleaner now includes the Indic family from `sheets/medicine_indic.md`. The original source sheet and contributor functions remain unchanged. The consolidated `sheets/specv1.md` contains all 176 source cards, with 115 selected candidates and 61 explicitly deferred cards. The final cleaner has 185 sheet rules plus the existing shared F1, across five families and 29 validated packs (16 Indic).

Selections remain CANDIDATE. Loading and compatibility checks do not establish positive-case recall or independent approval.

## Selection and deferred rules

`tools/integrate_indic.py` checks return values, mutation, ordinary synthetic prose, ZWJ/ZWNJ preservation, idempotence and unrelated-pack guards. It checks source rules on available full diagnosis packs for runtime errors and single-rule idempotence, then iteratively defers rules that act again after the selected full pipeline. It also runs every source rule on its own current gold when both the week-1 diagnosis pack and Data B gold file exist. Missing own-pack inputs are NOT TESTABLE and explicitly defer the affected rules. Empty gold records "Gold set empty, not testable" and defers the rules without aborting review of other packs. Combined gold failures defer the affected pack's selected pipeline.

For each of the 43 overlapping pack/disease groups, the first eligible source candidate is provisionally selected; later alternatives are deferred. This avoids stacking competing treatments. It is a deterministic integration choice, not a finding that the selected rule has better precision or recall. Positive-case review is still required.

Four C3 candidates fail synthetic ordinary-prose/joiner probes: `DB-C3-003`, `DB-C3-005`, `DB-C3-009`, `DB-C3-012`. Both legacy Sanskrit F2 candidates are deferred: `DB-F2-001` needs an approved benchmark and `ITIHASA_TEST_SN`; `DB-F2-002` returns text unchanged and does not implement benchmark remediation. Source algorithms are not silently patched or wrapped in exception-to-keep fallbacks. PR #26 separately adds G9 decontamination as `run_clean.py --f2`, after the default cleaner. It is opt-in, pinned to G9 v1 and does not cover Itihasa. It is not a `clean.py` function or a reason to enable the legacy Sanskrit detectors. Optional F2 gold evidence for the 16 supported Indic packs is in `results/f2/indic_gold_validation.json`.

Each deferred card has `STATUS = "DEFERRED"`, `DEFER_REASON`, and a `python deferred` fence. These fences are intentionally excluded by the repository harm runner. The builder validates the complete numbered inventory but emits only executable candidates. `clean.DEFERRED_RULES` records the exclusions; they are absent from executable `SCOPE`, `_RULE`, and family pipelines.

All 176 source IDs retain their `DB-` prefix. The builder accepts both `DA-` and `DB-`, recognizes the Indic `_PACKS = frozenset(ORIGIN.split(", "))` guard, intersects it with `SPEC_PACKS`, and redirects both to its central `SCOPE` table. Each rule still has an isolated closure. New disease functions include D2, D5, F3, G1, G2, G4 and H3. All legacy G3 and F2 candidates are deferred in this snapshot, so those functions are not emitted; the builder supports them when an eligible rule is added. F1 remains last in the disease registry; per-family execution follows source section order.

## Scope and privacy

Indic uses the pack guard, independently of whether a source language tag uses `mr` or `mar_Deva`. The shared F1 remains restricted to code, math and science; Indic uses its selected source F1 rules. Three supported packs lack a selected F1 candidate after sibling validation: `ind-bn-fw2`, `ind-bn-sangraha-v`, `ind-ta-sangraha-v`. Do not interpret a clean gold pass as full privacy coverage.

The source contributes native candidates from 13 packs. Its sibling policy is declared near the top of `sheets/medicine_indic.md`, separately from the copied contributor code. Integration tests selected donors on same-language receivers and writes accepted `ORIGIN`/`SPEC_PACKS` scopes to `sheets/specv1.md`, with `SOURCE_ORIGIN` retaining the donor. Native disease selections take priority; only missing diseases are filled. `clean.py` is generated from those scopes.

The current review accepts **81 additional rule/pack scopes**, extending coverage to **16 Indic packs**. Newly supported: `ind-bn-sangraha-v`, `ind-hi-indiccorp`, `ind-te-sangraha-v`. Existing packs also gain validated rules for previously uncovered diseases. See `results/cleaner/indic_sibling_scopes.json` for every attempted scope, rejection reason, gold result and combined full-pack check.

Still unsupported: `ind-hi-sangraha-s`, `ind-hi-sangraha-v`, `ind-ta-fw2`, `ind-ta-sangraha-s` (no usable receiving gold), and `ind-ml-fw2`, `ind-or-fw2` (no same-language donor). They are not registered merely because their language is known. `run_clean.py` rejects unsupported packs.

## Rebuild and validate

Run from the repository root, using Python with `spec_v1/requirements.txt` installed:

```bash
python teams/01-data-a/spec_v1/tools/integrate_indic.py \
  --packs ../erav5-lab-other-files/packs \
  --gold teams/02-data-b/gold
python teams/01-data-a/spec_v1/tools/build_clean.py
python -m pytest teams/01-data-a/spec_v1/tests -q
python teams/01-data-a/spec_v1/tools/validate_specv1.py \
  --packs ../erav5-lab-other-files/packs \
  --gold teams/01-data-a/gold \
  --indic-gold teams/02-data-b/gold \
  --allow-missing
```

The integration step refreshes native decisions, then automatically reviews sibling scopes from the source policy. `tools/extend_indic_siblings.py --packs <packs folder>` can recheck scopes using cached native decisions only if source Python blocks and native input digests still match; otherwise rerun integration. The builder still reads only the consolidated spec: rerunning it alone does not discover changes to an individual medicine sheet. To promote or change a selection, update the review policy/source evidence, rerun integration, rebuild, and validate.

The validator uses the repository minimum-one policy, `max(1, floor(1% × gold_count))`. With `--allow-missing`, it records missing inputs and exits 2; actual test failures exit 1. Exit 0 requires all required inputs and tests to pass. The sheet validator tests the executable sheet; generated-cleaner validation additionally exercises dispatch, closures and the shared F1.

Week-2 training shards are not substitutes for the week-1 diagnosis packs: they intentionally contain different document IDs. All 13 native diagnosis packs and the three newly supported receivers have nonempty own-pack gold. Other receiving packs remain unregistered until the required inputs and checks are available. Week-2 heldout data is not substituted for diagnosis gold.

For an independent comparison with the cleaner before integration:

```bash
git show a6eab62:teams/01-data-a/spec_v1/clean.py > /tmp/clean_before_indic.py
python teams/01-data-a/spec_v1/tools/check_indic_integration.py \
  --packs ../erav5-lab-other-files/packs \
  --gold teams/02-data-b/gold \
  --baseline /tmp/clean_before_indic.py
```

This compares actions and text for the original 13 packs, distinguishes matching pre-existing exceptions from new regressions, and tests available Indic gold, full packs and second-run changes. It exits 2 for missing Indic inputs and 1 for regressions, failures, new errors or non-idempotence. A matching baseline exception is recorded, not represented as successful cleaning.

## Measured verification

- The full unit/contract suite, F2 runner tests and sibling-scope tests pass **884 tests** after rebuilding.
- All 16 supported Indic generated pipelines pass their own gold sets (1,300 documents total). Current gold impact: Hindi FW2 drops 1/234; Marathi FW2 changes 1/140; Sanskrit changes 1/68; the other 13 packs have zero gold impact. Each is within its own minimum-one limit.
- All 8,000 supported Indic diagnosis documents execute without errors or second-pass changes.
- Comparing all 6,500 original code/English/math/science documents with the pre-refresh baseline finds zero behavior differences. Three documents raise the same pre-existing exceptions in both cleaners (one Java, two Python); they remain recorded rather than counted as successful cleaning.
- G9 F2 alone and the default cleaner followed by F2 pass gold on all 16 supported Indic packs. This does not establish Itihasa coverage or positive-case recall.
- Synthetic source/factory equivalence, pack isolation, joiners, source-trigger cases and build reproducibility are covered by the tests. These checks do not imply final approval.

## Evidence

- `results/cleaner/indic_sibling_scopes.json`: source policy, accepted rule scopes and every receiving-pack validation attempt.
- `results/f2/indic_gold_validation.json`: G9 F2 alone and the composed pipeline on supported Indic gold.
- `results/cleaner/indic_integration.json`: source digest, every candidate's decision, all overlap selections, synthetic findings and current own-pack gold tests.
- `results/cleaner/specv1_validation.json`: executable sheet rules and combined pipelines, per-pack snapshots, missing inputs and out-of-pack guard checks.
- `results/cleaner/indic_clean_validation.json`: generated cleaner versus the saved baseline, Indic gold/full-pack outcomes and second-run changes.

Reports contain IDs, counts, digests and error types, not source text. The original four medicine sheets, shared F1 implementation and normalization fingerprints are unchanged by this integration.
