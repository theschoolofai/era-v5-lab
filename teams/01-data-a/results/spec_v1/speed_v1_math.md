# clean.py speed log: math packs

Follow-up to [speed_v1.md](speed_v1.md) (English rules) and [speed_v1_code.md](speed_v1_code.md) (code rules), in the same format. Spec v1.1, Gate 2. A log of the slow rules that run on the math packs (`math-finemath`, `math-megamath`) and were sped up: what the fix was, docs/s per core before and after, and the checks showing that nothing else changed. Last updated 14 Nov 2026. Reports counts, hashes and timings only, never document text.

Every fix passes the same three checks before it is logged:

1. **Output sha256 unchanged** on all 13 sample packs (`doc_id`, final action and final cleaned text of every document, in order).
2. **Harm tests unchanged** (every rule and `clean()` on each pack, same harm result and same gold changed/dropped counts).
3. **Pytest suite passes.**

## 1. Where the time went (profile before any fix)

Per-rule profile of the 500-document packs, one core (`spec_v1/run_clean.py`), the rules that ran:

| pack | slowest rules (share of rule time, ms per document) |
|---|---|
| math-finemath | `DA-C1-001` 64.1% (3.974), `f1_rule.py` 10.8% (0.669), `DA-D3-005` 6.0% (0.364), `DA-A6-003` 4.7% (0.287) |
| math-megamath | `f1_rule.py` 43.1% (0.867), `DA-D3-005` 23.9% (0.480), `DA-A5-002` 15.5% (0.306) |

`DA-C1-001` runs on `math-finemath` only and fixes about one document in five, so it was the first target. The megamath profile has no such outlier.

## 2. Speed, docs/s per core, before and after each fix

500-doc sample packs, one core pinned to CPU 0, `clean()` loop only, best of 3 passes, before and after timed back to back on the same machine. The rule time is the per-document time of that rule alone, from the per-rule profile.

| # | rule (what it checks) | math-finemath docs/s | math-megamath docs/s | rule time math-finemath, ms/doc | rule time math-megamath, ms/doc |
|---|---|---|---|---|---|
| 1 | `DA-C1-001` (site boilerplate lines) | 173.7 to 355.3 (2.05x) | 521.6 to 521.0 (1.00x, rule does not run) | 3.974 to 0.654 | rule does not run |
| 2 | `DA-D3-005` (foreign-script lines) | 351.3 to 406.3 (1.16x) | 514.4 to 655.7 (1.27x) | 0.372 to 0.034 | 0.473 to 0.041 |
| | **both fixes** | **173.7 to 406.3 (2.34x)** | **521.6 to 655.7 (1.26x)** | | |

The "both fixes" row is the baseline (fix 1's before) against the last row's after. The rows were timed in separate runs, so it is approximate. The other 11 packs of the 13 are unchanged in each run (1.0x to 1.1x, timing noise): fix 1 runs on `math-finemath` only, fix 2 on the two math packs only.

## 3. Status of each fix

| # | rule | output sha256 | harm tests | pytest | documents changed, 500 docs each: math-finemath / math-megamath | `clean.py` before | `clean.py` after | commit |
|---|---|---|---|---|---|---|---|---|
| 1 | `DA-C1-001` | same, 13 of 13 | unchanged | 2242 passed | ran on 487, fixed 97, dropped 0 / rule does not run | `22d818c72c9f` | `6f99ff4d9ab4` | `634de3e` |
| 2 | `DA-D3-005` | same, 13 of 13 | unchanged | 2299 passed | ran on 500, fixed 7, dropped 1 / ran on 490, fixed 3, dropped 0 | `6f99ff4d9ab4` | `8cc7458cf3bd` | `7d8001f` |

The baseline is `clean.py` `22d818c72c9f` (commit `5516cf9`, the base of this branch; the same file as at `cc6f4c8`, where fix 1 was first measured); fix 2 starts from fix 1 (commit `634de3e`). Pytest counts are the whole suite at that commit (1 test skipped, 42 subtests passed). The output sha256 of each pack is the same as in [speed_v1.md section 6](speed_v1.md#6-output-sha256-of-the-13-sample-packs-identical-before-and-after-every-fix) (`math-finemath` `4e79a08fd226f614`, `math-megamath` `51c5b8452f45d195`), so before and after are byte-identical there too. Fix 1 does not run on `math-megamath`, so its megamath figures show only that nothing else moved.

## 4. What each fix did

1. **`DA-C1-001`, site boilerplate (menus, footers, forum chrome).** The rule deletes a line that is a known chrome phrase, or that contains one of 83 site phrases (`C1_SITE`, one case-insensitive regex) and is at most 120 characters. It searched `C1_SITE` on every line and only then looked at the length, so about two thirds of the searches were on lines that are kept whatever they hold, and each search tries 83 alternatives at every position. The length test now comes first. On a pure-ASCII line the search also uses the lower-cased pattern on the lower-cased line, which gives the same answer as `(?i)` because every escape in the pattern is lower-case and it has no non-ASCII character. A non-ASCII line (about 9% of lines) still uses the original `(?i)` regex, so letters like `İ`, `ſ` and the Kelvin sign `K`, which `(?i)` treats specially, behave as before. The rule is unchanged otherwise. Edited in `specv1.md` and `medicine_math.md`.

2. **`DA-D3-005`, lines in a foreign script (Cyrillic, Indic, kana, CJK, Hangul, Arabic).** The rule deletes a line when more than half of its letters are foreign, and drops the document when the deleted lines hold more than 30% of its letters. It counted the letters of every line, and then of the whole text, with a Python loop over every character, although only 16 of 500 finemath documents (12 of 500 megamath) hold a foreign character at all, and those loops were about 85% of the rule's time. A text with no foreign character is now returned as it is (the old code rebuilt exactly the same text). In the others, letters are counted only for lines that hold a foreign character (any other line has no foreign letter, so it is never deleted), and the letters of the whole text only if a line was deleted (otherwise the drop test cannot fire). The thresholds and formulas are the author's. Edited in `specv1.md` and `medicine_math.md`.

The tests are in `tests/spec_v1/test_speed_equivalence_math.py`, against frozen copies of the old rules in `tests/spec_v1/math_speed_reference.py`.

- **Fix 1:** a made-up line for each of the 83 alternatives in upper, lower and mixed case and at several positions, a sweep of line lengths 1 to 124 around the 120 limit, non-ASCII cases, 4,000 random documents (1,500+ fixed, so both outcomes occur), and 20,000 random ASCII strings compared directly against the old regex. Four deliberate breaks of the fix (no ASCII test, limit 119, line not lower-cased, no length limit) each made the new tests fail.
- **Fix 2:** each of the six scripts as a whole line, inline and as a whole document; the first and last character of every range and the characters just outside it; characters inside the ranges that are not letters (Devanagari marks and danda, Arabic digits, Cyrillic combining marks); Greek left alone; sweeps of the 50% line threshold and the 30% document threshold (30 of 100 is a fix, 31 of 101 a drop); foreign letters in lines that are kept; edge documents; scope; and 4,000 random documents covering keep, fix and drop. Seven deliberate breaks (early return on the first line only, a regex missing Hangul and Arabic in the early return and in the line test, drop test skipped at one letter, `>=` for either threshold, one count per line) each made the new tests fail. The old and new rule also gave identical results on 20,000 week-2 finemath and 17,647 megamath documents, including all drops (213 and 123 changed, 9 and 1 dropped).

## 5. Next slowest rules

After fix 2, on math-finemath: the shared `f1_rule.py` is the slowest at 26.1% of the time (0.663 ms/doc), then `DA-C1-001` at 25.5% (0.649, already sped up once) and `DA-A6-003` at 11.6% (0.288). `DA-D3-005` is down from 13.0% to 1.4% of the time. On math-megamath: `f1_rule.py` 55.1% (0.847 ms/doc), `DA-A5-002` 19.9% (0.299) and `DA-B4-001` 7.3% (0.110); `DA-D3-005` is down from 23.8% to 2.7%. Shares rise for the rules not touched because the total gets smaller. The shared F1 rule already has a code-pack fast path ([speed_v1_code.md](speed_v1_code.md)); the math path has not been looked at yet.

## 6. Method

- **Machine:** x86_64, Python 3.12.15, one run at a time pinned to CPU 0 (`taskset -c 0`). Timings vary by about 5%, so treat ratios under 1.1x as about equal.
- **Versions compared:** fix 1: the baseline `clean.py` `22d818c72c9f` (measured at `cc6f4c8`; `5516cf9` has the same file) against the rebuilt working copy; fix 2: `clean.py` `6f99ff4d9ab4` (fix 1, `634de3e`) against the rebuilt working copy. Only `clean.py` differs between the two trees.
- **Packs:** the 13 original diagnosis packs (500 documents each), in a folder of exactly those 13, as `speed_compare.sh` expects.
- **Tools and command**, from the repository root:

```bash
teams/01-data-a/oneoff/speed_compare.sh --packs <folder with the 13 packs> --work <scratch folder> \
  --rules <RULE_ID> --profile-packs "math-finemath math-megamath"
```

The routine is in [oneoff/speed_handoff.md](../../oneoff/speed_handoff.md).
