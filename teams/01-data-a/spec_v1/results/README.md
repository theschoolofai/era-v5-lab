# Validation evidence index

These are recorded runs, not automatically refreshed attestations of the current cleaner. Read each report's input, gold, sheet/rule, cleaner, and fingerprint hashes before applying its result to a build. Historical code hashes and provenance paths are preserved during cleanup.

| Family / location | Producer | Interpretation |
|---|---|---|
| [cleaner/harm_tests.md](cleaner/harm_tests.md), `cleaner/specv1_<pack>_harm.json` | [make_harm_tests.py](../tools/make_harm_tests.py) | Generated-cleaner per-rule/function/combined harm and out-of-scope checks; inspect `rules_file_sha256` |
| [cleaner/specv1_validation.json](cleaner/specv1_validation.json) | [validate_specv1.py](../tools/validate_specv1.py) | Executable-sheet validation snapshot; code/input/gold digests are recorded separately |
| [cleaner/harm_tests_english.md](cleaner/harm_tests_english.md), `cleaner/clean_*`, `cleaner/clean_stress_*` | [English tools](../tools/README_english.md) | English cleaner, ordering, privacy, and disputed-gold snapshots |
| [cleaner/harm_tests_f1_math_sci.md](cleaner/harm_tests_f1_math_sci.md) | Shared-F1 validation documented in the [cleaner guide](../README_clean.md) | Historical math/science privacy harm snapshot |
| [cleaner/indic_integration.json](cleaner/indic_integration.json), [indic_sibling_scopes.json](cleaner/indic_sibling_scopes.json) | [integrate_indic.py](../tools/integrate_indic.py), [extend_indic_siblings.py](../tools/extend_indic_siblings.py) | Source selection, exclusions, input digests, and validated receiving scopes; sibling evidence is also read by tests |
| [cleaner/indic_clean_validation.json](cleaner/indic_clean_validation.json), [f1_indic_harm.json](cleaner/f1_indic_harm.json) | [check_indic_integration.py](../tools/check_indic_integration.py), [harm_f1_indic.py](../tools/harm_f1_indic.py) | Cleaner/baseline comparison and Indic privacy checks; use embedded cleaner hashes |
| [sheets/](sheets/): code evidence, manifests, `<pack>_harm.json`, `stress_<pack>_harm.json` | [Sheet reproduction scripts](../scripts/README.md) | Contributor selection and official/stress snapshots; manifests record input versions |
| [sheets/evidence_english.json](sheets/evidence_english.json), [equivalence_english.json](sheets/equivalence_english.json), English pack reports | [English guide](../tools/README_english.md) and English harm runner | Compilation tooling for the evidence/equivalence files is not committed; preserve this reproduction dependency |
| [f2/README.md](f2/README.md), `f2/f2_<pack>_harm.json`, [Indic F2 report](f2/indic_gold_validation.json) | [f2_rule.py](../tools/f2_rule.py), [validate_f2_indic.py](../tools/validate_f2_indic.py) | Optional full-set G9 evidence; reports bind to a fingerprint-set hash and may bind to an older cleaner |

The ten historical reports formerly directly under `results/` were removed during cleanup. Current writers target these family subdirectories. Official/stress reports can be byte-identical and still have distinct roles; keep both names while readers/writers expect them.

Run dates are available in summary headers or linked execution logs where recorded. Some raw reports contain no date: their hashes are authoritative snapshot identifiers; no date is inferred here. Reproducing real-pack evidence requires original diagnosis packs and the matching gold, not week-2 train/heldout shards.

For future report-layout changes, migrate readers/writers and import-time test inputs together before moving files. Keep job-specific execution logs and overlap evidence in the [jobs index](../../jobs/README.md).
