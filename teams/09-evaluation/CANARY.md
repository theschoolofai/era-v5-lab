# Lab canary (G9)

The lab uses **one lab-wide canary string**. It goes into every eval file that Team 9 publishes, and it is
recorded once, here (TSAI, G9 chat, 2 Nov). Each eval set keeps its own fingerprint file for the
decontamination check (`fingerprints/`).

```
ERA V5 LAB EVALUATION DATA. IT MUST NEVER APPEAR IN TRAINING DATA. canary GUID era-v5-lab:eval:43c1a566-5d44-4c5b-96ae-b53b4188b0ec
```

- The scanners look for the GUID part, `era-v5-lab:eval:...`. One occurrence in a training document means eval data
  reached the training data.
- It is plain ASCII text, not a special token (TSAI, G10 chat, 29 Oct): a special token never comes out of normal
  tokenization, so leaked text would not contain it.
- Never change it. Files stamped with the old string would no longer be found.
- `decontam/lab_canary.py` reads the string from this file. Code never writes it out a second time.

## Where it is written

| File | Writer | How |
|---|---|---|
| `results/eval_mini_v0.json` | `harness/build_results.py` | `"canary"` key, first |
| `results/compare_v0.md` | `harness/build_results.py` | first line, HTML comment |
| `results/eval_mini_v0_code_indic.json` | `harness_code_indic/compare.py` | `"canary"` key, first |
| `results/compare_v0_code_indic.md` | `harness_code_indic/compare.py` | first line, HTML comment |
| `harness_code_indic/eval_mini_v0_spec.json` | `harness_code_indic/make_eval_mini_spec.py` | `"canary"` key, first |
| `harness_code_indic/runs/eval_mini_v0_items.json` (local, gitignored) | `make_eval_mini_items.py` | in the file and in every item |
| `harness_code_indic/runs/<model>/<tag>/samples_<n>.jsonl` (local, gitignored) | `run_lm_eval.py --log-samples` | in every line |

A new script that writes an eval file calls `lab_canary.stamp(record)` (JSON) or writes `lab_canary.MARKDOWN_LINE`
as the first line (Markdown). `decontam/tests/test_canary.py` checks that every published eval file carries it.

Find it: `python decontam/canary_scan.py <files or folders>` (see `decontam/README.md`). Scans of this repo find it in
this file and in the files above, as expected.
