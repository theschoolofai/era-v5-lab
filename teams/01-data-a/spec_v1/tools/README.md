# Cleaner build and validation tools

Paths and commands below start at the repository root. Install [../requirements.txt](../requirements.txt) before running data-dependent tools. [The cleaner guide](../README_clean.md) covers runner options; [shared tools](../../tools/README.md) and the [harm-test harness](../../harmtest/README.md) cover gold and contributor inputs.

| Purpose | Scripts | Inputs / outputs |
|---|---|---|
| Generate the cleaner | [build_clean.py](build_clean.py) | Reviewed `sheets/specv1.md` → `clean.py`; `--out` supports a temporary rebuild for comparison |
| Integrate Indic and validated sibling scopes | [integrate_indic.py](integrate_indic.py), [extend_indic_siblings.py](extend_indic_siblings.py) | [Indic guide](../README_indic.md); native/receiving diagnosis packs and own-pack gold |
| Validate the executable sheet | [validate_specv1.py](validate_specv1.py) | Original packs and own-pack gold → `results/cleaner/specv1_validation.json` |
| Validate generated cleaner behavior and harm | [make_harm_tests.py](make_harm_tests.py) | Checkout, pack folders → per-pack reports and `harm_tests.md` |
| Compare an Indic build with a baseline | [check_indic_integration.py](check_indic_integration.py) | Explicit baseline file and diagnosis/gold packs; see Indic guide |
| Check code equivalence and privacy behavior | [verify_clean.py](verify_clean.py), [f1_eval.py](f1_eval.py) | Code diagnosis packs, source sheet, labels/gold; IDs and counts only |
| Run English equivalence, order, privacy, and stress checks | [verify_clean_english.py](verify_clean_english.py), [order_checks_english.py](order_checks_english.py), [f1_eval_english.py](f1_eval_english.py), [make_harm_tests_english.py](make_harm_tests_english.py) | [English commands and order](README_english.md) |
| Validate Indic F1 and optional F2 | [harm_f1_indic.py](harm_f1_indic.py), [validate_f2_indic.py](validate_f2_indic.py) | [Indic commands](../README_indic.md#optional-f2-validation); current own-pack gold, full pinned G9 set for F2 |
| Run the tokenizer sample cleaning job | [run_tokenizer_sample.py](run_tokenizer_sample.py) | [Pinned sample config/manifest](../jobs/README.md); outputs under fresh `out/<job>/` |
| Shared runtime rules and matching helpers | [f1_rule.py](f1_rule.py), [f2_rule.py](f2_rule.py), [normalize.py](normalize.py) | F1 is embedded by the builder; F2 is opt-in through `run_clean.py --f2`; normalization also has a Team 09 version contract |

The [sheet-reproduction helpers](../../oneoff/README.md) have a separate role: reconstructing contributor evidence and explaining selection decisions. Report files and their snapshot status are indexed in [../results/README.md](../results/README.md).
