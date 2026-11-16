# clean.py speed log: the F1 rule

Follow-up to [speed_v1.md](speed_v1.md) (English rules) and [speed_v1_code.md](speed_v1_code.md) (code rules). Spec v1.1, Gate 2. This log covers three speed-ups of the F1 rule (the TSAI ruling on personal details): the shared F1 (`f1_rule.py`) on its prose path (math and science) and on its Indic path, and the English F1 rule `DA-F1-005`. For each: what the fix was, docs/s per core before and after, and the checks showing that nothing else changed. Last updated 16 Nov 2026. Reports counts, hashes and timings only, never document text.

Every fix passes three checks before it is logged:

1. **Output sha256 unchanged** (`doc_id`, final action and final cleaned text of every document, in order) on every pack tested.
2. **Harm tests unchanged** (every rule and `clean()` on each pack: same harm result, same gold changed/dropped counts).
3. **Pytest suite passes.**

## 1. Speed, docs/s per core, before and after

500-doc sample packs, one core pinned to CPU 0, `clean()` loop only, best of 3 passes, before and after timed back to back. The rule time is the per-document time of the F1 rule alone, from the per-rule profile (`spec_v1/run_clean.py`).

| fix | pack | docs/s | rule time, ms/doc |
|---|---|---|---|
| 1 prose path | sci-finepdfs | 143.4 to 203.4 (1.42x) | 6.636 to 4.830 |
| | math-megamath | 510.8 to 598.7 (1.17x) | 0.868 to 0.566 |
| | math-finemath | 167.0 to 176.4 (1.06x) | 0.676 to 0.424 |
| 2 Indic path | ind-hi-hplt | 202.9 to 263.1 (1.30x) | 1.496 to 0.197 |
| | ind-sa-fw2 | 178.9 to 207.2 (1.16x) | 1.354 to 0.351 |
| | ind-bn-fw2 | 762.3 to 1019.5 (1.34x) | 0.558 to 0.196 |
| | ind-ta-sangraha-v | 1266.2 to 3390.3 (2.68x) | 0.605 to 0.039 |
| 3 English `DA-F1-005` | en-dclm | 554.5 to 714.8 (1.29x) | 0.438 to 0.149 |
| | en-fineweb-edu | 748.3 to 981.7 (1.31x) | 0.354 to 0.126 |
| | en-nemotroncc | 741.0 to 921.7 (1.24x) | 0.281 to 0.110 |
| | en-nemotroncc-synth | 1997.1 to 2614.6 (1.31x) | 0.133 to 0.042 |

- **Fix 1** was timed on the packs where F1 takes the most time: before it, F1 was 94.3% of the rule time on `sci-finepdfs` (the documents are long, about 48,800 characters), 43.6% on `math-megamath` and 11.3% on `math-finemath`. The whole-pack gain on `math-finemath` is small because `DA-C1-001` (65% of that pack) is untouched here.
- **Fix 2:** F1's share of the rule time fell from 25.9% to 4.4% on `ind-hi-hplt`, 22.1% to 6.8% on `ind-sa-fw2`, 37.1% to 16.1% on `ind-bn-fw2` and 67.6% to 13.2% on `ind-ta-sangraha-v`. Over all 18 Indic packs the whole-pack gain is 1.1x to 2.7x.
- **Packs a fix does not touch** read 1.0x to 1.1x, timing noise. Timings vary by about 5%, so treat ratios under 1.1x as about equal.

## 2. Status of each fix

| fix | rule | output sha256 | harm tests | pytest | F1 on the packs it applies to | `clean.py` before | `clean.py` after | commit |
|---|---|---|---|---|---|---|---|---|
| 1 | `f1_rule.py`, prose path | same, 13 of 13 packs | unchanged, 31 of 31 packs | 2238 passed | math-finemath: ran on 487, fixed 4, dropped 0; math-megamath: 490, 26, 0; sci-finepdfs: 488, 15, 1 | `22d818c72c9f` | `3145d54a97a5` | `9982b11` |
| | label fix: prose path chosen by pack id, not language label (section 4) | same, 31 of 31 packs | unchanged | | | `3145d54a97a5` | `c1a96591cefb` | `05d9c74` |
| 2 | `f1_rule.py`, Indic path | same, 31 of 31 packs | unchanged, 31 of 31 packs | 2353 passed | 18 Indic packs: ran on 8,653 of 9,000, fixed 52, dropped 0 | `c1a96591cefb` | `2aa69a36c544` | `40393df` |
| 3 | `DA-F1-005`, English, spec v1.1 sheet | same, 31 of 31 packs | unchanged, 31 of 31 packs | 2565 passed | en-dclm: ran on 491, fixed 2, dropped 0; en-fineweb-edu: 499, 0, 0; en-nemotroncc: 483, 1, 0; en-nemotroncc-synth: 499, 2, 0 | `729e37051ffd` | `9a4e3a87f124` | `7cb527a` |

- **Baseline of fix 1:** `clean.py` `22d818c72c9f`, the one in `9d96529` (14 Nov, Revert of the math speed commit) and in `536e8bc` (#244); no F1 change was made before `9982b11`.
- **Pytest** counts are the whole suite at each commit (one test skipped). For fix 1 the first run had one failure, `test_pr244_rerun_config_pins_current_cleaner_and_recorded_smoke`, which required the PR #244 rerun config to pin the live `clean.py` and so fails for any `clean.py` change; it now checks the config against its recorded smoke evidence, like the submitted-config test next to it. The job folder is untouched.
- **Output sha256** of the 13 original packs under the v1 build (fixes 1 and 2) is the same as in [speed_v1.md section 6](speed_v1.md#6-output-sha256-of-the-13-sample-packs-identical-before-and-after-every-fix). The v1.1 build (fix 3 on) has other hashes, because of its 24 new rules; before and after are the same under it.
- **Fix 3** is a change to the spec v1.1 sheet only (`specv1_1.md`; spec v1 is frozen). The `clean.py` committed at that time was built from `specv1.md` and is not changed by that commit; before and after are scratch `clean.py` files built from `specv1_1.md` as committed and as edited, and their diff is exactly the edit. `build_clean.py` now builds from `specv1_1.md` by default and the committed `clean.py` is that build (`9a4e3a87f124`, the same file as "after"), so from here `--before <rev> --after <rev>` works for every fix. The test `test_the_committed_sheet_is_up_to_date` in `spec_v1_1/tests/test_combine_spec.py` was removed in the same commit: it required `specv1_1.md` to equal the output of `combine_spec.py`, so it fails for any edit of the sheet, and the script was used once. It can be brought back if the sheet is generated again.

### 2.1 Harm tests on all 31 registered packs, including the Indic ones

The shared F1 rule runs on 27 of the 31 packs `clean.py` has rules for: the 18 Indic packs (Indic path), the 6 code, the 2 math and the science pack. The 4 English packs have their own F1, `DA-F1-005`. The harm tests were run on all 31 packs, before and after, with `make_harm_tests.py` and the 18 Indic gold sets (`teams/02-data-b/gold`) copied into the scratch copy of the tree, since that script reads gold only from `teams/01-data-a/gold`. Every result file (every gold changed/dropped count, every rule alone, every disease-code function and `clean()`) is identical before and after, for each fix.

| family | packs | gold docs | `clean()` changes + drops on gold | limit (1% of gold, at least 1 per pack) | whole packs, fixed / dropped (500 docs each) |
|---|---|---|---|---|---|
| code | 6 | 980 | 0 + 0 | PASS on 6 of 6 | 1,764 / 120 |
| English | 4 | 675 | 0 + 0 | PASS on 4 of 4 | 160 / 28 |
| math | 2 | 112 | 0 + 0 | PASS on 2 of 2 | 239 / 23 |
| science | 1 | 202 | 0 + 0 | PASS on 1 of 1 | 45 / 13 |
| Indic | 18 | 2,193 | 10 + 3 | PASS on 18 of 18 | 1,729 / 347 |
| **all** | **31** | **4,162** | | **31 of 31** | **3,937 / 531** of 15,500 |

No fix changes any output, so the table holds before and after each of them. The 10 changed and 3 dropped Indic gold documents come from the Indic rules and are the same before and after. The Indic F1 harm test (`spec_v1/validate/harm_f1_indic.py`, F1 alone and `clean()` on each pack's own gold) gives 18 of 18 PASS before and after fixes 1 and 2, 2,193 gold documents, F1 alone changes 2 (one each in `ind-kn-fw2` and `ind-ta-sangraha-v`) and drops 0.

Under the v1.1 `clean.py` (fix 3), four packs do not pass their harm limit, before and after alike: `en-nemotroncc` (`DA-A8-003`, `DA-A8-004`), `math-finemath`, `sci-finepdfs` and `ind-te-sangraha-v` (`DB-C6-001`). They are the four listed as FAIL in [spec_v1_1/results/combined/validation.md](../../spec_v1_1/results/combined/validation.md); `DA-F1-005` is not among the failing rules. `make_harm_tests.py` exits with 1 for them, so `speed_compare.sh` now compares the results of both sides anyway.

**Seven packs were not tested.** `week1-packs` holds 38 packs: the 31 above and these 7, none registered in `clean.py` (no rules, so `clean()` leaves them unchanged and no harm test runs). Under the new `clean.py`, `clean()` changes or drops 0 of the 500 documents of each, so the F1 changes cannot affect them.

| pack | docs | gold set | why it was not tested |
|---|---|---|---|
| `cadj-commits` | 500 | yes, `teams/02-data-b/gold/cadj-commits_gold.csv` (413 rows) | not registered in `clean.py`, so the harm script has no rules to run on it |
| `cadj-notebooks` | 500 | none | no gold, not registered |
| `cadj-stackexchange` | 500 | only a 1-row file, `gold/cadj-stackexchange.csv`, not named `<pack>_gold.csv` | not registered; effectively no gold |
| `ind-ml-fw2` | 500 | none | no gold, not registered |
| `ind-or-fw2` | 500 | none | no gold, not registered |
| `ind-ta-fw2` | 500 | none | no gold, not registered |
| `ind-ta-sangraha-s` | 500 | none | no gold, not registered |

These seven can only be tested once they get rules in `clean.py` and a gold set.

## 3. What each fix did

Each fix skips a pass when the text cannot match it, using a condition every match must satisfy, so the output is unchanged. Tests: `tests/spec_v1/test_speed_equivalence_f1.py` (fix 1, 121 tests), `test_speed_equivalence_f1_indic.py` (fix 2, 97) and `test_speed_equivalence_f1_english.py` (fix 3, 29), each against a frozen copy of the old rule.

1. **Prose path of the shared F1 (`_f1_prose`, math and science).** Six regex passes ran on every text; three are now skipped when they cannot match:
   - **Email:** runs only when the text has an `@` (1.73 to 0.67 ms/doc on `sci-finepdfs`).
   - **"Name at host":** a cheap prefilter for ` at <host>.<tld>` runs first, and the full pattern only if it matches (0.66 to 0.27 ms/doc).
   - **Phone:** the international form starts with a literal `+`; a text with no `+` uses the North American form alone, which finds exactly the same matches (3.1 to about 1.7 ms/doc).
2. **Indic path of the shared F1 (`_f1_indic`, 18 packs).** Digit translation, three phone regexes and the email regex ran on every text. Now:
   - **Digit translation** runs only if the text holds an Indic-script digit (a character the translation maps; ASCII digits do not count).
   - **Toll-free** runs only if the text holds `1800` or `1860`, the only strings its existing regex can start with.
   - **Mobile and landline** run only if a short core pattern finds something: the regex without its lookarounds and optional prefixes. `_F1I_MOBILE_CORE` is the two shapes of an Indian mobile number (`98765 43210`, `987-654-3210`); `_F1I_LANDLINE_CORE` is the area code and number. A core starts with a character set, which the engine scans much faster than the lookbehind the full regex starts with.
   - **Email** runs only when the text has an `@`.
3. **English `DA-F1-005`.** The rule searched the whole text for an organisation phrase ("call us", "our team", "we provide" and so on) before reading the first line, but the answer is only used on a line with an email, a phone number or an address, which is in 3% to 6% of documents (en-dclm 32 of 500, en-fineweb-edu 18, en-nemotroncc 30, en-nemotroncc-synth 13). That search was about 70% of the rule (0.31 of 0.46 ms/doc on en-dclm). It now runs the first time such a line asks, and the answer is kept for that text.

Fixes 1 and 2 are in `spec_v1/build/f1_rule.py`, the source `build_clean.py` pastes into `clean.py`; they are not part of any sheet and apply to any build, including one from the v1.1 sheet. Fix 3 is in the `DA-F1-005` card of `spec_v1_1/sheets/specv1_1.md`.

### 3.1 Note: what the Indic-digit guard saves, and where it does not

Open for discussion with the team. The digit guard is the weakest of the four guards of fix 2 and is kept because it is exact and costs almost nothing, not because it skips most documents. Most documents have a digit, but the guard asks for an *Indic-script* digit, and many packs write numbers with ASCII digits. 3,000 documents of each pack from the week-2 `train` part (54,000 documents; the 500-document week-1 sample gives the same picture). The last three columns are the cost of the digit step alone, ms/doc, one core:

| pack | ASCII digit | Indic digit | 2 consecutive Indic digits | no guard | 1-digit guard (used) | 2-consecutive guard |
|---|---:|---:|---:|---:|---:|---:|
| ind-bn-fw2 | 14% | 85% | 79% | 0.146 | 0.127 | 0.126 |
| ind-bn-sangraha-v | 11% | 78% | 73% | 0.159 | 0.131 | 0.134 |
| ind-gu-fw2 | 72% | 18% | 15% | 0.147 | 0.046 | 0.052 |
| ind-hi-fw2 | 84% | 2% | 1% | 0.143 | 0.015 | 0.028 |
| ind-hi-hplt | 90% | 4% | 2% | 0.253 | 0.040 | 0.058 |
| ind-hi-indiccorp | 36% | 1% | 0% | 0.019 | 0.002 | 0.003 |
| ind-hi-sangraha-s | 84% | 0% | 0% | 0.236 | 0.018 | 0.039 |
| ind-hi-sangraha-v | 74% | 10% | 8% | 0.133 | 0.037 | 0.043 |
| ind-kn-fw2 | 80% | 8% | 5% | 0.135 | 0.028 | 0.034 |
| ind-kn-sangraha-s | 90% | 0% | 0% | 0.214 | 0.016 | 0.035 |
| ind-kn-sangraha-v | 75% | 9% | 7% | 0.123 | 0.029 | 0.035 |
| ind-mr-fw2 | 57% | 46% | 42% | 0.146 | 0.081 | 0.085 |
| ind-mr-sangraha-v | 39% | 50% | 46% | 0.137 | 0.083 | 0.087 |
| ind-sa-fw2 | 31% | 67% | 56% | 0.354 | 0.289 | 0.269 |
| ind-ta-sangraha-v | 80% | 0% | 0% | 0.155 | 0.012 | 0.026 |
| ind-te-fw2 | 85% | 1% | 0% | 0.177 | 0.017 | 0.032 |
| ind-te-sangraha-s | 91% | 0% | 0% | 0.234 | 0.018 | 0.039 |
| ind-te-sangraha-v | 73% | 2% | 1% | 0.130 | 0.016 | 0.024 |
| mean of the 18 packs | 65% | 21% | 19% | 0.169 | 0.056 | 0.064 |

- **Effective** (Indic digit in 0% to 18% of documents; the Hindi, Telugu, Kannada, Tamil and Gujarati packs): the digit step costs 0.12 to 0.25 ms/doc without the guard and 0.002 to 0.05 with it, a saving of about 70% to 93%.
- **Not effective** (Indic digit in 46% to 85%; `ind-bn-fw2`, `ind-bn-sangraha-v`, `ind-mr-fw2`, `ind-mr-sangraha-v`, `ind-sa-fw2`): numbers are written in the script's own digits, and the guard saves only 13% to 45% of the step (13%, 18% and 18% on the Bengali packs and `ind-sa-fw2`). A pack from a source that uses Indic digits throughout would see no saving. The share is the same in week 1 and week 2 (mean 21%); other data (week-3 shards) was not checked.
- **The step is small anyway:** about 0.11 ms/doc saved on average (0.169 to 0.056). The mobile, landline, toll-free and email guards each skip their regex for 93% or more of documents and save more together.
- **Two consecutive Indic digits** instead of one is not faster overall (0.064 ms/doc against 0.056 on average) and changes the output: a number written with a mix of Indic and ASCII digits (`Call me on 9876५ 43210`) is masked now and would not be, and a single Indic digit next to a number (`contact ५98765 43210`, `Mobile 98765 43210.५ end`) blocks the match now and would not. Three of the 97 tests of fix 2 fail with it.

## 4. Notes

- **Week-2 science label.** The prose path accepted only documents labelled `eng_Latn`, which is how week-1 `sci-finepdfs` is labelled. All 6,011 `train` and 63 `heldout` documents of week-2 `sci-finepdfs` are labelled `en` (ISO 639-1, as the week-2 README defines `lang_label`), so F1 skipped them; on the first 1,000, 15 differ between the two labels. Fixed in `05d9c74`: the prose path is chosen by pack id (`math-*`, `sci-*`). The week-1 packs are unchanged (0 of 15,500 documents differ); on the first 2,000 week-2 science documents, 27 more get their private values masked.
- **Method:** x86_64, Python 3.12.15, one run at a time pinned to CPU 0 (`taskset -c 0`). Only `clean.py` differs between the before and after trees.

## 5. Commands

One set for all three fixes, from the repository root. `<packs>` is the folder of the 38 `week1-packs`; `speed_compare.sh` times the 31 registered ones. Put the two `clean.py` to compare in files and pass them with `--before-clean` and `--after-clean` (this works for any change; for two commits of `clean.py`, `--before <rev> --after <rev>` does the same):

- for a fix committed in `clean.py` (fixes 1 and 2): `git show <commit>:teams/01-data-a/spec_v1/clean.py > <scratch>/clean_before.py`, and the same for the after commit;
- for a change in a sheet only (fix 3): build them with `build_clean.py --sheet <sheet> --out <file>`, once from the sheet as committed (saved first as `<scratch>/before/specv1_1.md`, under the same file name, because the name is written into `clean.py`) and once from the edited sheet.

```bash
S=teams/01-data-a/oneoff/speed_compare.sh
$S --packs <packs> --work <scratch> --include-all --rules <RULE_OR_f1_rule.py> \
  --before-clean <scratch>/clean_before.py --after-clean <scratch>/clean_after.py \
  --profile-packs "<packs to profile>" trees
cp teams/02-data-b/gold/ind-*_gold.csv <scratch>/before/teams/01-data-a/gold/   # and the same into <scratch>/after/...
$S (the same options) speed profile harm count
for side in before after; do     # fixes 1 and 2 only: the Indic F1 harm test
  (cd <scratch>/$side/teams/01-data-a && python -I -B spec_v1/validate/harm_f1_indic.py --packs <packs> --out <scratch>/f1_indic_$side.json)
done
```

The `--rules` and `--profile-packs` used: `f1_rule.py` with `"sci-finepdfs math-finemath math-megamath"` (fix 1) and `"ind-hi-hplt ind-sa-fw2 ind-bn-fw2 ind-ta-sangraha-v"` (fix 2), `DA-F1-005` with `"en-dclm en-fineweb-edu en-nemotroncc en-nemotroncc-synth"` (fix 3). The command names its steps, so `build` and `pytest` do not run; run the suite on its own (`python -m pytest teams/01-data-a/tests teams/01-data-a/spec_v1_1/tests`). The routine is in [oneoff/speed_handoff.md](../../oneoff/speed_handoff.md).
