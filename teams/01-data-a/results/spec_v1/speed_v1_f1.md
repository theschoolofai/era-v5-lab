# clean.py speed log: shared F1 rule on math, science and Indic packs

Follow-up to [speed_v1.md](speed_v1.md) (English rules) and [speed_v1_code.md](speed_v1_code.md) (code rules), in the same format. Spec v1.1, Gate 2. This log covers the shared F1 rule (`f1_rule.py`, the TSAI ruling on personal details), in two fixes: fix 1 on the packs that take its prose path (`math-finemath`, `math-megamath` and `sci-finepdfs`), and fix 2 on the 18 Indic packs that take its Indic path. It gives what each fix was, docs/s per core before and after, and the checks showing that nothing else changed. Sections 1 to 5 are about fix 1; fix 2 is in sections 2.1, 3.2, 4.1 and 5.1. Last updated 15 Nov 2026. Reports counts, hashes and timings only, never document text.

Every fix passes the same three checks before it is logged:

1. **Output sha256 unchanged** on all 13 sample packs (`doc_id`, final action and final cleaned text of every document, in order).
2. **Harm tests unchanged** (every rule and `clean()` on each pack, same harm result and same gold changed/dropped counts).
3. **Pytest suite passes.**

## 1. Where the time went (profile before the fix)

Per-rule profile of the 500-document packs, one core (`spec_v1/run_clean.py`), over `clean.py` `22d818c72c9f`:

| pack | share of rule time taken by `f1_rule.py` | ms per document |
|---|---|---|
| sci-finepdfs | **94.3%** (next rule `DA-B4-013`, 4.4%) | 6.636 |
| math-megamath | 43.6% | 0.868 |
| math-finemath | 11.3% (`DA-C1-001` is 65%) | 0.676 |

On the science pack the shared F1 rule is nearly all of the cleaning time. The science documents are long (about 48,800 characters each, against about 5,100 and 6,600 in the two math packs).

The prose path of F1 (`_f1_prose`, used for math and science) makes six passes over each text. Timing each pass on `sci-finepdfs` with a staged copy of the rule (one core, 500 documents, 7.1 ms/doc in total; this copy and its timing script are not part of the repository):

| pass | ms/doc | share |
|---|---|---|
| phone regex | 3.16 | 44% |
| email regex | 1.69 | 24% |
| street-address regex | 1.03 | 14% |
| "name at host" regex | 0.67 | 9% |
| personal-listing check | 0.30 | 4% |
| people tables | 0.29 | 4% |

Almost all of this is the regex scan itself: the code that decides what to mask (the callbacks) takes only 0.35 ms/doc of the 7.1. Most documents have no email at all (135 of 500 contain an `@`) and no `+` (354 of 500), so most of the scanning looks for something that cannot be there.

## 2. Speed, docs/s per core, before and after the fix

500-doc sample packs, one core pinned to CPU 0, `clean()` loop only, best of 3 passes, before and after timed back to back on the same machine. The rule time is the per-document time of `f1_rule.py` alone, from the per-rule profile.

| # | rule (what it checks) | sci-finepdfs docs/s | math-megamath docs/s | math-finemath docs/s | rule time sci-finepdfs, ms/doc | rule time math-megamath, ms/doc | rule time math-finemath, ms/doc |
|---|---|---|---|---|---|---|---|
| 1 | `f1_rule.py` (shared F1, prose path) | 143.4 to 203.4 (1.42x) | 510.8 to 598.7 (1.17x) | 167.0 to 176.4 (1.06x) | 6.636 to 4.830 | 0.868 to 0.566 | 0.676 to 0.424 |

The rule itself is 1.4x to 1.6x faster on the three packs. The whole-pack gain is smaller where F1 is a smaller share of the time: on `math-finemath` it is 1.06x because `DA-C1-001` (65% of that pack) is untouched here. The other ten of the 13 packs are unchanged (1.0x to 1.1x, timing noise): the code and English packs do not use the prose path.

### 2.1 Fix 2, Indic path: docs/s per core, before and after

Same method as section 2, on the four Indic packs where F1 took the largest share of the time (the profile packs of this fix). Before is `clean.py` `c1a96591cefb` (commit `ccde028`, fix 1 and the pack-id change included), after is `2aa69a36c544`.

| # | rule | ind-hi-hplt docs/s | ind-sa-fw2 docs/s | ind-bn-fw2 docs/s | ind-ta-sangraha-v docs/s | rule time hplt, ms/doc | rule time sa-fw2, ms/doc | rule time bn-fw2, ms/doc | rule time ta-sangraha-v, ms/doc |
|---|---|---|---|---|---|---|---|---|---|
| 2 | `f1_rule.py` (shared F1, Indic path) | 202.9 to 263.1 (1.30x) | 178.9 to 207.2 (1.16x) | 762.3 to 1019.5 (1.34x) | 1266.2 to 3390.3 (2.68x) | 1.496 to 0.197 | 1.354 to 0.351 | 0.558 to 0.196 | 0.605 to 0.039 |

The share of the rule time taken by `f1_rule.py` fell from 25.9% to 4.4% on `ind-hi-hplt`, 22.1% to 6.8% on `ind-sa-fw2`, 37.1% to 16.1% on `ind-bn-fw2` and 67.6% to 13.2% on `ind-ta-sangraha-v`. The rule itself is 2.8x to 15.5x faster on these four. Over all 18 Indic packs the whole-pack speed-up is 1.1x to 2.7x (1.1x `ind-te-sangraha-s`; 1.7x `ind-gu-fw2`; 1.8x `ind-mr-sangraha-v`; 2.7x `ind-ta-sangraha-v`). The other 13 of the 31 packs (code, English, math, science) are unchanged (1.0x to 1.1x, timing noise).

## 3. Status of the fix

| # | rule | output sha256 | harm tests | pytest | documents changed, 500 docs each: math-finemath / math-megamath / sci-finepdfs | `clean.py` before | `clean.py` after | commit |
|---|---|---|---|---|---|---|---|---|
| 1 | `f1_rule.py` (prose path) | same, 13 of 13 | unchanged, 31 of 31 packs (section 3.1) | 2238 passed | ran on 487, fixed 4, dropped 0 / ran on 490, fixed 26, dropped 0 / ran on 488, fixed 15, dropped 1 | `22d818c72c9f` | `3145d54a97a5` | this commit |

The baseline is `clean.py` `22d818c72c9f` (commit `5bcf6af`). Pytest counts are the whole suite at this commit (1 test skipped, 42 subtests passed). The speed-check run itself reported 1 failed and 2237 passed: the failure was `test_pr244_rerun_config_pins_current_cleaner_and_recorded_smoke`, which required the PR #244 rerun config to pin the live `clean.py` and so fails for any `clean.py` change. It was changed in this commit to check the config against its recorded smoke evidence, like the submitted-config test next to it (`test_pr244_rerun_config_matches_recorded_smoke`); the job folder itself is untouched. The output sha256 of each pack is the same as in [speed_v1.md section 6](speed_v1.md#6-output-sha256-of-the-13-sample-packs-identical-before-and-after-every-fix) (`math-finemath` `4e79a08fd226f614`, `math-megamath` `51c5b8452f45d195`, `sci-finepdfs` `f67b3fa5b7a92b53`). The rule's code path for code files is not changed, and the output sha256 of the six code packs is identical before and after.

### 3.1 Harm tests on all 31 registered packs, including the Indic ones

The shared F1 rule runs on 27 of the 31 packs `clean.py` has rules for: all 18 Indic packs (its Indic path), the 6 code, the 2 math and the science pack. The 4 English packs have their own F1 rule (`DA-F1-005`) and do not run it. The speed-check run's harm step covers the 13 non-Indic packs; to cover F1 on every pack it runs on, the harm tests were run again on all 31, before and after, with the same harm test (`make_harm_tests.py`) and the 18 Indic gold sets (`teams/02-data-b/gold`) copied into the scratch copy of the tree, since that script reads gold only from `teams/01-data-a/gold`. Every result file (every gold changed/dropped count, every rule alone, every disease-code function and `clean()`) is identical before and after, and `clean()` passes on all 31 packs.

| family | packs | gold docs | `clean()` changes + drops on gold | limit (1% of gold, at least 1 per pack) | whole packs, fixed / dropped (500 docs each) |
|---|---|---|---|---|---|
| code | 6 | 980 | 0 + 0 | PASS on 6 of 6 | 1,764 / 120 |
| English | 4 | 675 | 0 + 0 | PASS on 4 of 4 | 160 / 28 |
| math | 2 | 112 | 0 + 0 | PASS on 2 of 2 | 239 / 23 |
| science | 1 | 202 | 0 + 0 | PASS on 1 of 1 | 45 / 13 |
| Indic | 18 | 2,193 | 10 + 3 | PASS on 18 of 18 | 1,729 / 347 |
| **all** | **31** | **4,162** | | **31 of 31** | **3,937 / 531** of 15,500 |

The 10 changed and 3 dropped Indic gold documents come from the Indic rules and are the same before and after the fix; the F1 change is to the prose path, which Indic packs do not use. The Indic F1 harm test (`spec_v1/validate/harm_f1_indic.py`, F1 alone and the whole `clean()` on each pack's own gold) was also run from the before and the after tree: 18 of 18 packs PASS for both, 2,193 gold documents, F1 alone changes 2 (one each in `ind-kn-fw2` and `ind-ta-sangraha-v`) and drops 0, and the per-pack results are identical before and after.

**Seven packs were not tested.** `week1-packs` holds 38 packs: the 31 above and these 7, none of which is registered in `clean.py` (no rules, so `clean()` leaves them unchanged and no harm test runs on them). Under the new `clean.py`, `clean()` changes or drops 0 of the 500 documents of each, so the F1 change cannot affect them.

| pack | docs | gold set | why it was not tested |
|---|---|---|---|
| `cadj-commits` | 500 | yes, `teams/02-data-b/gold/cadj-commits_gold.csv` (413 rows) | not registered in `clean.py`, so the harm script has no rules to run on it |
| `cadj-notebooks` | 500 | none | no gold, not registered |
| `cadj-stackexchange` | 500 | only a 1-row file, `gold/cadj-stackexchange.csv`, not named `<pack>_gold.csv` | not registered; effectively no gold |
| `ind-ml-fw2` | 500 | none | no gold, not registered |
| `ind-or-fw2` | 500 | none | no gold, not registered |
| `ind-ta-fw2` | 500 | none | no gold, not registered |
| `ind-ta-sangraha-s` | 500 | none | no gold, not registered |

The spec v1.1 README lists the same packs, except `cadj-commits`, as having no gold. These seven can only be tested once they get rules in `clean.py` and a gold set.

### 3.2 Status of fix 2 (Indic path)

| # | rule | output sha256 | harm tests | pytest | documents changed, 500 docs each: the 18 Indic packs | `clean.py` before | `clean.py` after | commit |
|---|---|---|---|---|---|---|---|---|
| 2 | `f1_rule.py` (Indic path) | same, 31 of 31 packs | unchanged, 31 of 31 packs | 2353 passed | ran on 8,653 of 9,000, fixed 52, dropped 0 | `c1a96591cefb` | `2aa69a36c544` | this commit |

The baseline is `clean.py` `c1a96591cefb` (commit `ccde028`). Pytest is the whole suite at this commit (1 test skipped, 42 subtests passed), run on its own after the speed-check run, which did not include the pytest step. The output sha256 is the same before and after on all 31 registered packs (15,500 documents), and the 13 original packs have the same hashes as in [speed_v1.md section 6](speed_v1.md#6-output-sha256-of-the-13-sample-packs-identical-before-and-after-every-fix). The counts are from the count step of the speed-check run: F1 ran on 8,653 of the 9,000 documents of the 18 Indic packs, fixed 52 and dropped none.

Harm tests (`make_harm_tests.py`, the 18 Indic gold sets from `teams/02-data-b/gold` copied into both trees, as in section 3.1): every result file of the 31 packs is identical before and after (every gold changed/dropped count, every rule alone, every disease-code function and `clean()`), and `clean()` passes on all 31 packs. The Indic F1 harm test (`harm_f1_indic.py`, F1 alone and the whole `clean()` on each pack's own gold) gives 18 of 18 PASS before and after, on 2,193 gold documents, with the same result for every pack.

## 4. What the fix did

1. **`f1_rule.py`, shared F1, prose path (math and science).** The rule runs six regex passes over every text: personal listings, people tables, email, "name at host" mailing-list addresses, phone numbers and street addresses. Three passes are now skipped when the text cannot match them, using a condition that every match must satisfy, so the output is unchanged:
   - **Email:** the email regex needs an `@`; it runs only when the text has one (most documents do not). 1.73 to 0.67 ms/doc on `sci-finepdfs`.
   - **"Name at host":** every match holds ` at <host>.<tld>` (for example `jane at example.com`). A cheap prefilter regex for that text runs first, and the full pattern runs only if it matches (27 of 500 science documents). 0.66 to 0.27 ms/doc.
   - **Phone:** the international form of the phone pattern starts with a literal `+`. A text with no `+` uses the North American form alone, which finds exactly the same matches, because the two forms are alternatives and the second cannot match. `_F1P_PHONE` is now built from the two forms and is the same pattern as before. 3.1 to about 1.7 ms/doc on average (146 of 500 documents have a `+` and use the whole pattern).

   The edit is in `spec_v1/build/f1_rule.py`, the source that `build_clean.py` pastes into `clean.py`. It is not part of any sheet, so it applies to any build of `clean.py`, including a build from the combined spec v1.1 sheet. The Indic and code paths of F1 are not changed.

The tests are in `tests/spec_v1/test_speed_equivalence_f1.py` (121 tests), against a frozen copy of the old `_f1_prose` that uses the unchanged helpers of `clean.py`:

- hand-written cases at the edge of each guard: email forms, `name at host` forms (hyphens, digits, uppercase, missing top-level domain, text around), and 34 phone strings with ten label contexts each, with and without a `+` elsewhere in the text, and a `+` inside an email that is masked before the phone pass;
- contact cards, toll-free numbers, organisations, people tables and personal listings;
- checks that the combined phone pattern is the old one, that the international form needs a `+`, and that every match of the "name at host" pattern holds the prefilter text;
- 40,000 random near-miss phone strings, 30,000 random near-miss "name at host" strings (both compared with the old regex directly), and 4,000 random documents on the three packs that hit every branch both ways (fixes, keeps and drops all occur);
- the scope: other packs and labels are left alone.

Six deliberate breaks of the guards (email guard needing two `@`, a prefilter without hyphens, a prefilter needing a three-letter top-level domain, a phone guard looking for `+1` only, the North American form always used, the North American form without its lookbehind) each made the new tests fail. Outside the repository, the old and new prose path also gave identical results on 500 documents of each of the three packs and on larger slices of the week-2 data (1,500 science, 8,000 `math-finemath`, 8,000 `math-megamath` documents), including all drops.

### 4.1 Fix 2: what it did (Indic path)

**`f1_rule.py`, shared F1, Indic path (`_f1_indic`, the 18 Indic packs).** The Indic path translates Indic digits to 0-9, then runs three phone regexes (toll-free, mobile, landline) and an email regex over every text. Most texts hold no phone number or email, and the three phone regexes start with a lookbehind, so the regex engine tries every position of the text. Each pass is now skipped when the text cannot match it, using a condition every match must satisfy, so the output is unchanged:

- **Digit translation:** it runs only if the text holds one of the characters it maps (the digits of the nine Indic scripts); otherwise the text is its own key. `_F1I_INDIC_DIGIT` is built from the translation table itself.
- **Toll-free:** every match starts with `1800` or `1860`, so the regex runs only if the text holds one of them.
- **Mobile and landline:** each regex runs only if a short core pattern finds something: the regex without its lookarounds and optional prefixes. A core pattern starts with a character set, which the engine scans much faster than a lookbehind. `_F1I_MOBILE_CORE` is the two shapes of an Indian mobile number (`98765 43210`, `987-654-3210`); `_F1I_LANDLINE_CORE` is the area code and number.
- **Email:** the email regex needs an `@`; it runs only when the text has one.

The edit is in `spec_v1/build/f1_rule.py`, the source that `build_clean.py` pastes into `clean.py`; it is not part of any sheet. The prose and code paths of F1 are not changed.

The tests are in `tests/spec_v1/test_speed_equivalence_f1_indic.py` (97 tests), against a frozen copy of the old `_f1_indic` that uses the unchanged helpers and regexes of `clean.py`:

- phone forms in every script's digits and every label context, context edges, emails, texts with no digits, no `@` or no phone shape;
- toll-free numbers that overlap a mobile number (for example `1800 987 654 3210`), where the toll-free span blocks the mobile match. A check on the guard itself confirms that these cases do depend on it (the first version of the tests did not, see below);
- that the digit guard accepts exactly the characters the translation maps, that each core pattern is part of its full pattern, and that every match of each full pattern holds its core, on hand-written and random near-miss strings;
- that all 18 Indic packs take the Indic path whatever the language label, and 4,000 random documents that hit every branch both ways.

Eight deliberate breaks of the guards (the digit guard never translating; the digit class missing one script; the toll-free guard looking for `1800` only; the toll-free regex never run; a mobile core without the `987-654-3210` shape; a landline core needing a four-digit area code; the landline regex never run; the email guard needing two `@`) each made at least one test fail. The first version of the tests missed two breaks of the toll-free guard, because a toll-free number only matters when it overlaps a mobile number; the overlap cases above were added for that.

### 4.2 Note: what the Indic-digit guard saves, and where it does not

Open for discussion with the team. The digit guard is the weakest of the four guards of fix 2, and is kept because it is exact and costs almost nothing, not because it skips most documents.

**What it does.** The Indic path translates Indic digits to 0-9 (`str.translate`, which is slow on non-ASCII text: it looks up every character) so that one set of ASCII phone patterns serves all scripts. Before, every text was translated. Now the translation runs only if a fast scan (`_F1I_INDIC_DIGIT.search`, which stops at the first hit) finds a character the translation would change, that is an Indic-script digit. An ASCII digit does not count, since translating leaves it unchanged. Most documents have a digit, but the guard asks for an Indic one, and many packs write numbers with ASCII digits.

**Where it saves and where it does not.** 3,000 documents of each pack from the week-2 `train` part (54,000 documents; the 500-document week-1 sample gives the same picture, mean 0.198 / 0.068 / 0.074 ms/doc). The last three columns are the cost of the digit step alone, ms/doc, one core:

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

- **Effective (Indic digit in 0 to 18% of documents):** the Hindi, Telugu, Kannada, Tamil and Gujarati packs. The digit step costs 0.12 to 0.25 ms/doc without the guard (0.02 on the short `ind-hi-indiccorp` documents) and 0.002 to 0.05 with it, a saving of about 70% to 93% of that step.
- **Not effective (Indic digit in 46% to 85%):** `ind-bn-fw2`, `ind-bn-sangraha-v`, `ind-mr-fw2`, `ind-mr-sangraha-v` and `ind-sa-fw2`. The guard costs a little (one scan) and saves only 13% to 45% of the step: least on the Bengali packs and `ind-sa-fw2` (13%, 18% and 18%), most on the two Marathi packs (45% and 39%). In these packs numbers are written in the script's own digits, as the table shows (ASCII digit only in 11% to 39%), so in real use the guard is about the same as no guard there.
- **In other words:** the guard works by language and source, not by document length: it needs a pack where numbers are written with ASCII digits. A pack from a source that uses Indic digits throughout would see no saving. The 18 packs match week 1 and week 2 closely (mean Indic-digit share 21% in both), so this is not an artefact of the 500-document sample. It has not been checked on other data (the week-3 shards, for example).
- **The step is small anyway.** The saving is about 0.11 ms/doc on average (0.169 to 0.056) out of an F1 rule time that was 0.56 to 1.5 ms/doc on the four packs profiled in section 2.1. The mobile, landline, toll-free and email guards each skip their regex for 93% or more of documents on the 18 week-1 packs (at most 7% of documents have an `@`, 4% a mobile core, 3% a toll-free prefix, 1% a landline core), and together they save more than the digit guard (0.021, 0.004, 0.003 and 0.004 ms/doc left, against 0.169, 0.133, 0.063 and 0.080 without a guard).

**Two consecutive Indic digits instead of one** (the `{2}` columns above) skips a few more documents (for example 81% to 74% on `ind-bn-fw2`), but is not faster overall: 0.064 ms/doc on average against 0.056, because its regex is slightly slower per scan and the gain is small. It also changes the output. Phone numbers written with a mix of Indic and ASCII digits are rare, but the old code does mask them, so a stricter guard would stop masking them. Made-up examples that give a different output from the current rule: `Call me on 9876५ 43210 today` (number with one Indic digit: masked now, left unmasked with the stricter guard) and `contact ५98765 43210` or `Mobile 98765 43210.५ end` (a single Indic digit next to a number makes the translated text read it as a digit, which blocks the match now; with the stricter guard the number is masked). The one-digit guard gives the old output on all of these; the stricter one does not. Three of the 97 tests of fix 2 fail with the stricter guard. If the team accepts that edge case, the option is open, but it gains no speed.

## 5. Next slowest rules

After the fix, on sci-finepdfs: `f1_rule.py` is still 92.0% of the rule time (4.830 ms/doc); the next rule, `DA-B4-013`, is 4.4% (0.227 ms/doc), then `DA-B2-003` 1.6% and `DA-C1-007` 0.8%. The two largest remaining F1 costs there are the North American phone regex (about 1.7 ms/doc) and the street-address regex (about 1 ms/doc). Both start with a lookbehind or a word boundary, so the regex engine tries every position; a cheap necessary condition for them was tried and did not help, because most science documents contain digits. A fix would need to find the candidate positions first. On math-finemath: `DA-C1-001` 65.4% (3.772 ms/doc), `DA-D3-005` 6.5% and `DA-A6-003` 5.1%. On math-megamath: `DA-D3-005` 28.3% (0.481 ms/doc), `DA-A5-002` 18.2% and `DA-B4-001` 6.7%; `f1_rule.py` is 33.3% of that pack after the fix.

### 5.1 Next slowest rules after fix 2

After the fix `f1_rule.py` is no longer the main cost on the four profiled Indic packs. Next slowest rules (share of the rule time, ms/doc):

| pack | next slowest rules |
|---|---|
| ind-hi-hplt | `DB-A6-017` 23.0% (0.905), `DB-C2-021` 13.1% (0.584), `DB-B4-008` 12.7% (0.501) |
| ind-sa-fw2 | `DB-D4-009` 30.6% (1.534), `DB-C1-013` 20.4% (1.043), `DB-H3-001` 12.8% (0.658) |
| ind-bn-fw2 | `DB-F3-001` 17.7% (0.214), `DB-G4-006` 17.4% (0.193), `DB-A6-001` 14.1% (0.156) |
| ind-ta-sangraha-v | `DB-C2-016` 52.3% (0.159), `DB-G4-004` 29.1% (0.089), `DB-B4-007` 4.0% (0.012) |

These are Data B rules in the Indic sheets, not part of this change. On `ind-ta-sangraha-v` F1 is now 13.2% of the rule time (0.039 ms/doc).

## 6. Notes

- **Week-2 science label.** The science prose path of F1 accepts documents labelled `eng_Latn` (`_F1_PROSE` in `f1_rule.py`), which is how the week-1 `sci-finepdfs` pack is labelled (all 500). In the local week-2 sample, all 6,011 documents of the `train` part and all 63 of the `heldout` part of `sci-finepdfs` are labelled `en` (the week-2 README defines `lang_label` as an ISO 639-1 code), so F1 skips them. Cleaning the first 1,000 week-2 science documents under both labels, 15 differ, all `keep` as `en` and `fix` as `eng_Latn`; no other rule is affected. This was found while checking the fix, and the speed-up gives the same result as before for both labels. It was fixed afterwards, in a separate change to the same file: the prose path is now chosen by the pack id (`math-*`, `sci-*`) and not by the label. The week-1 packs are unchanged (0 of 15,500 documents in the 31 registered packs differ); on the first 2,000 week-2 science documents, 27 more get their private values masked.
- **Method:** x86_64, Python 3.12.15, one run at a time pinned to CPU 0 (`taskset -c 0`). Timings vary by about 5%, so treat ratios under 1.1x as about equal. Before is `clean.py` at `5bcf6af`, after is the rebuilt working copy; only `clean.py` differs between the two trees. The 13 original diagnosis packs (500 documents each) are in a folder of exactly those 13, as `speed_compare.sh` expects.
- **Command**, from the repository root:

```bash
teams/01-data-a/oneoff/speed_compare.sh --packs <folder with the 13 packs> --work <scratch folder> \
  --rules f1_rule.py --profile-packs "sci-finepdfs math-finemath math-megamath"
```

and the harm tests on all 31 packs (section 3.1), from the repository root, with `<packs>` the folder of the 38 sample packs:

```bash
S=teams/01-data-a/oneoff/speed_compare.sh
$S --work <scratch> --rules f1_rule.py trees
cp teams/02-data-b/gold/ind-*_gold.csv <scratch>/after/teams/01-data-a/gold/
$S --work <scratch> --packs <packs> --include-all --rules f1_rule.py harm
for side in before after; do
  (cd <scratch>/$side/teams/01-data-a && python -I -B spec_v1/validate/harm_f1_indic.py --packs <packs> --out <scratch>/f1_indic_$side.json)
done
```

For fix 2 (Indic path), the speed-check run with the four Indic profile packs and the count packs, from the repository root, with `<packs>` the folder of the 38 sample packs (it times the 31 registered packs it finds there; the count step defaults to the 27 packs the rule runs on):

```bash
teams/01-data-a/oneoff/speed_compare.sh --packs <packs> --work <scratch> --include-all \
  --rules f1_rule.py --profile-packs "ind-hi-hplt ind-sa-fw2 ind-bn-fw2 ind-ta-sangraha-v"
```

and the harm tests on all 31 packs and the Indic F1 harm test, as in section 3.1, with the 18 Indic gold sets copied into both the before and the after tree.

The routine is in [oneoff/speed_handoff.md](../../oneoff/speed_handoff.md).
