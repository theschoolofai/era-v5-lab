# clean.py speed log

Spec v1.1, Gate 2. A log of the slow rules in `clean.py` that were sped up, one entry per rule, with the speed change and the checks that show nothing else changed. Last updated 11 Nov 2026. Reports counts, hashes and timings only, never document text.

Every fix has to pass three checks before it is logged:

1. **Output sha256 unchanged.** `clean.py` before and after gives the same output sha256 on all 13 sample packs. The sha256 covers every document in file order: its `doc_id`, the final action (keep, fix or drop) and the final cleaned text. Equal sha256 means byte-identical output.
2. **Harm tests unchanged.** Every rule and `clean()` on each pack gives the same harm result and the same gold changed/dropped counts.
3. **Pytest suite passes.**

## 1. Summary

Fixed so far: 5 rules. Speed is docs/s on one core, 500-doc sample packs, best of 5 (steps 4 and 5: best of 3, see below).

| step | `clean.py` (first 12) | en-dclm | en-fineweb-edu | en-nemotroncc | en-nemotroncc-synth |
|---|---|---:|---:|---:|---:|
| baseline | `97c1a55b89f4` | 47.9 | 94.7 | 96.9 | 167.8 |
| 1. `DA-F1-005` fixed | `7a76c7eddb51` | 250.0 (5.2x) | 333.4 (3.5x) | 398.2 (4.1x) | 799.6 (4.8x) |
| 2. `DA-D3-003` fixed | `fc6d1a2deea4` | 300.3 (1.2x) | 408.0 (1.3x) | 504.2 (1.3x) | 1062.5 (1.4x) |
| 3. `DA-C5-002` fixed | `622b0d48c65f` | 341.6 (1.1x) | 461.3 (1.1x) | 547.8 (1.1x) | 1150.0 (1.1x) |
| 4. `DA-B4-010` fixed | `742787d7c310` | 397.2 (1.13x) | 546.2 (1.14x) | 679.2 (1.14x) | 1478.9 (1.17x) |
| 5. `DA-B4-008` fixed | `08e8fe016458` | 465.4 (1.16x) | 648.7 (1.16x) | 796.7 (1.16x) | 1787.2 (1.20x) |
| **all five** | | **9.7x** | **6.9x** | **8.2x** | **10.6x** |

Each step's speed-up is against the row above it. Step 2 starts from `553fcfe32796`, which is step 1 plus the Indic refresh merge; it runs at the same speed as step 1 (en-dclm 249.0 against 250.0). Steps 4 and 5 were each timed in a separate run with `speed_compare.sh` (best of 3; the before value was 352.4 and 481.2 docs/s on en-dclm and en-fineweb-edu for step 4, and 400.5 and 559.2 for step 5), so the "all five" figures mix runs and are approximate.

| # | rule | the fix | rule time, en-dclm / en-fineweb-edu (ms per doc) | output sha256 | harm tests | pytest | docs changed in en-dclm / en-fineweb-edu (500 docs, large part) | commit |
|---|---|---|---|---|---|---|---|---|
| 1 | `DA-F1-005` (PII) | search ORGANISATION once per line, cached | 17.284 to 0.435 / 7.653 to 0.338 | same, 13 of 13 | unchanged | 1138 passed | 2 and 0, 402 and 139 fixed | `730253d` |
| 2 | `DA-D3-003` (foreign lines) | skip ASCII lines, cache each letter's script | 0.872 to 0.211 / 0.690 to 0.130 | same, 13 of 13 | unchanged | 1576 passed | 3 and 1, 387 and 190 fixed | `8a74553` |
| 3 | `DA-C5-002` (keyword spam) | search the nine patterns as one union first | 0.664 to 0.272 / 0.513 to 0.202 | same, 13 of 13 | unchanged | 1596 passed | 4 and 0, 50 and 39 dropped | `2d03ebb` |
| 4 | `DA-B4-010` (template and code-like lines) | stop the code-line scan once the answer is certain; skip the template regex when no hint is present | 0.509 to 0.194 / 0.383 to 0.139 | same, 13 of 13 | unchanged | 1618 passed | 0 and 1 (500 docs; large part not counted) | `a187284` |
| 5 | `DA-B4-008` (detokenised quotes) | look at the apostrophes with `str.find` and ask the unchanged regex about each, instead of scanning every position | 0.334 to 0.007 / 0.268 to 0.003 | same, 13 of 13 | unchanged | 1630 passed | 2 and 0 (500 docs; large part not counted) | this commit |

**Next slowest rules** (after step 5, en-dclm / en-fineweb-edu): `DA-F1-005` is still the slowest at 19.6% / 22.1% of the time (0.439 / 0.414 ms/doc), already sped up once in step 1. The next rule not yet touched is **`DA-B2-002`** at 12.4% / 13.6% (0.273 / 0.255 ms/doc), then `DA-C5-002` (12.2% / 12.8%, fixed in step 3). The profile is flat: no rule other than F1 is above 14%. Not changed yet.

The code, math and science packs are not slower: 1.0x to 1.1x after the first pass and 1.0x after fixes 3 to 5 (re-timed; none of these rules run on them).

## 2. The log

### 1. `DA-F1-005`: PII (emails, phones, addresses), commit `730253d`

- **Fix:** the rule ran the ORGANISATION regex on a joined 13-line window for every line, even lines with no email, phone or address. It now runs ORGANISATION once per line, caches the per-line result and builds the window from the cached results, and a line with no `@` or digit never reaches it (the check is lazy).
- **Speed:** `clean.py` `97c1a55b89f4` to `7a76c7eddb51`. Rule time en-dclm 17.284 to 0.435 ms/doc (40x), en-fineweb-edu 7.653 to 0.338 (23x). docs/s en-dclm 47.9 to 250.0, en-fineweb-edu 94.7 to 333.4 (see section 1).
- **Share of the time:** 83.3% of the cleaning time on en-dclm before, 13.2% after the fix.
- **Output sha256:** same on all 13 sample packs (before `97c1a55b89f4`, after `7a76c7eddb51`). The same on the two large week-2 parts for the first two fixes together (section 4), and on 20,000 generated test documents when the fix was made.
- **Harm tests:** unchanged. Checked for fixes 1 and 2 together (`97c1a55b89f4` against `fc6d1a2deea4`): every per-pack result file is identical apart from the `clean.py` hash.
- **Pytest:** 1138 passed, 1 skipped at the fix commit. The tests added afterwards include a joined-window equivalence test.
- **Docs this rule changes:** it redacts PII, so its fixes are rewritten documents. 500-doc packs: en-dclm 2, en-fineweb-edu 0, en-nemotroncc 1, en-nemotroncc-synth 2. Large parts: en-dclm 402 of 46,245 (0.9%), en-fineweb-edu 139 of 54,004 (0.3%). It drops no documents.

### 2. `DA-D3-003`: lines in a foreign script, commit `8a74553`

- **Fix:** the rule looked up `unicodedata.name()` for every letter of every line. An ASCII line is never foreign (an ASCII letter is always Latin), so it is skipped, and the script of each distinct letter is looked up once and cached.
- **Speed:** `553fcfe32796` to `fc6d1a2deea4`. Rule time en-dclm 0.872 to 0.211 ms/doc, en-fineweb-edu 0.690 to 0.130. docs/s en-dclm 249.0 to 300.3, en-fineweb-edu 326.0 to 408.0.
- **Output sha256:** same on all 13 sample packs.
- **Harm tests:** unchanged (together with fix 1, as above).
- **Pytest:** 1576 passed, 1 skipped at the fix commit. The tests compare the cached lookup with `unicodedata.name` for every alphabetic code point, and the rule with the old code on 3,000 random documents.
- **Docs this rule changes:** 500-doc packs: en-dclm 3, en-fineweb-edu 1, en-nemotroncc 3, en-nemotroncc-synth 0. Large parts: en-dclm 387 of 46,245 (0.8%), en-fineweb-edu 190 of 54,004 (0.4%). All are fixes (lines removed).

### 3. `DA-C5-002`: keyword-spam pages, commit 2d03ebb

- **Fix:** the rule searched nine case-insensitive spam patterns on every document, and needs two different patterns to match before it drops. One search of the union of the nine now comes first, and the nine run one by one only when it matches (about 10 of 500 en-dclm documents). The keyword-line pattern runs only when the text has 6 or more `|`, which that pattern needs. Both checks are necessary conditions for a drop.
- **Speed:** `fc6d1a2deea4` to `622b0d48c65f`. Rule time en-dclm 0.664 to 0.272 ms/doc, en-fineweb-edu 0.513 to 0.202. docs/s en-dclm 300.3 to 341.6, en-fineweb-edu 408.0 to 461.3.
- **Output sha256:** same on all 13 sample packs.
- **Harm tests:** unchanged: the per-pack result files differ only in the `clean.py` hash and `harm_tests.md` is identical.
- **Pytest:** 1596 passed, 1 skipped. 20 new tests: 19 hand-written cases and a 4,000-document random comparison against the nine separate searches, which fail under four deliberate mutations.
- **Docs this rule changes:** it only drops. 500-doc packs: en-dclm 4, the other three 0. Large parts: en-dclm 50 of 46,245 (0.11%), en-fineweb-edu 39 of 54,004 (0.07%). Its gold harm is 0 changed, 0 dropped on all four English packs.
- **Value of the rule:** it catches few documents (about 2% of the labelled keyword-list pages) and is a hardcoded list of spam themes from en-dclm. It does no harm on the gold sets, so it was kept as it is; whether to keep it is the sheet author's and the team's decision.

### 4. `DA-B4-010`: template expressions and code-like text, commit `a187284`

- **Fix:** the rule ran a large token regex on every line to find code-like lines (only to decide whether more than half of the text is code), and then searched the whole text for template expressions. It now stops reading lines as soon as the answer cannot change (the code found already passes half the text, or the code found plus every character not yet read cannot reach it, so a prose document is settled halfway through), and it runs the template regex only when the text contains one of `{{`, `{%`, `${`, a backtick, `undefined`, `NaN` or `null`, which every alternative of that regex needs.
- **Speed:** `622b0d48c65f` to `742787d7c310`. Rule time en-dclm 0.509 to 0.194 ms/doc, en-fineweb-edu 0.383 to 0.139. docs/s en-dclm 352.4 to 397.2 (1.13x), en-fineweb-edu 481.2 to 546.2 (1.14x), en-nemotroncc 594.1 to 679.2, en-nemotroncc-synth 1263.5 to 1478.9 (best of 3, one run with `speed_compare.sh`).
- **Share of the time:** 17.7% of the cleaning time on en-dclm before, 7.5% after.
- **Output sha256:** same on all 13 sample packs.
- **Harm tests:** unchanged: all per-pack result files identical apart from the `clean.py` hash.
- **Pytest:** 1618 passed, 1 skipped. 22 new tests: hand-written cases, a sweep around the exact half-the-text threshold, and a 4,000-document comparison with the old rule code.
- **Docs this rule changes:** 500-doc packs: en-dclm 0, en-fineweb-edu 1 (a fix), en-nemotroncc 0, en-nemotroncc-synth 0, so about 1 document in 2,000; the large parts were not counted. It runs on 483 to 499 of every 500 documents and almost never changes one, which is why a cheap pre-check pays off.

### 5. `DA-B4-008`: detokenised opening quotes, this commit

- **Fix:** the rule is one regex over the whole text that puts back the space in `said'sure it is'`. It can only match at an apostrophe, but it begins with look-behinds, so Python tried it at every character position. It now finds the apostrophes with `str.find` and asks the unchanged regex about each one in place (`DETOK.match(text, i)`, which sees the same text before the position), and rebuilds the text from the pieces.
- **Speed:** `742787d7c310` to `08e8fe016458`. Rule time en-dclm 0.334 to 0.007 ms/doc (48x), en-fineweb-edu 0.268 to 0.003. docs/s en-dclm 400.5 to 465.4 (1.16x), en-fineweb-edu 559.2 to 648.7 (1.16x), en-nemotroncc 688.6 to 796.7 (1.16x), en-nemotroncc-synth 1484.5 to 1787.2 (1.20x) (best of 3, one run with `speed_compare.sh`; a first run of the same pair gave 0.88x on two packs and was discarded as disturbed: the rule time had dropped 48x and the other two packs sped up in the same run).
- **Share of the time:** 13.1% of the cleaning time on en-dclm before, under 1% after.
- **Output sha256:** same on all 13 sample packs.
- **Harm tests:** unchanged: all per-pack result files identical apart from the `clean.py` hash.
- **Pytest:** 1630 passed, 1 skipped. 21 new tests in `tests/spec_v1/test_speed_equivalence.py` (the speed-up tests were moved there from `test_clean.py` in this commit): 19 hand-written cases, a sweep around the 40-character limit of the quoted span, and a 6,000-document comparison with the old regex.
- **Docs this rule changes:** 500-doc packs: en-dclm 2, en-fineweb-edu 0, en-nemotroncc 0, en-nemotroncc-synth 18 of 499 (3.6%); the large parts were not counted. All are fixes (a space inserted).

## 3. Method

- **Machine:** CPU, Python 3.12.15. Each timing run is pinned to one core with `taskset -c 0`, one run at a time. Cores 0 and 1 are two threads of the same physical core, so never time two runs on cores 0 and 1 together.
- **Timing:** only the `clean(doc)` loop, packs already in memory. Best of 5 passes (best of 3 for steps 4 and 5). Timings vary by about 5% between runs on this laptop, so treat ratios under 1.1x as about equal.
- **Versions compared:** all from git, only `clean.py` differs.

  | label | `clean.py` (first 12) | source |
  |---|---|---|
  | baseline | `97c1a55b89f4` | `730253d^` (same file as `8da2ac4`) |
  | fix 1 | `7a76c7eddb51` | `730253d` |
  | fix 1 + Indic refresh | `553fcfe32796` | `d956c6a` (merge) |
  | fix 2 | `fc6d1a2deea4` | `8a74553` (HEAD `bb0d997` has the same file) |
  | fix 3 | `622b0d48c65f` | `2d03ebb` |
  | fix 4 | `742787d7c310` | `a187284` |
  | fix 5 | `08e8fe016458` | this commit |

  The Indic refresh (`3b91add`) changes Indic rule scopes only. The baseline, fix 1 and fix 1 plus refresh give the same output sha256 on all 13 packs.
- **Rule time:** `spec_v1/run_clean.py` records the seconds each rule takes on a 500-doc pack. Docs changed per rule come from counting each rule's fixes and drops while `clean.py` runs, in pipeline order.
- **Tools:** [speed_compare.sh](../../oneoff/speed_compare.sh) runs the whole check; [speed_check.py](../../oneoff/speed_check.py) hashes and times; [make_harm_tests.py](../../spec_v1/validate/make_harm_tests.py) runs the harm tests.

### Adding the next entry

1. Edit the rule in `spec_v1/sheets/specv1.md` and `medicine_english.md`, rebuild with `python -I spec_v1/build/build_clean.py`, add tests.
2. Before committing, run `teams/01-data-a/oneoff/speed_compare.sh --rules <RULE_ID>`. It checks the fresh build, the full pytest suite, the output sha256 on the 13 packs, the harm tests, the profile and the documents the rule changes, and ends with a SUMMARY. It must say `RESULT: PASS`, `output sha256: the same on 13 of 13 packs` and `harm: unchanged`. The SUMMARY has the rule's ms/doc, the docs/s and the pytest count for the entry. (`oneoff/speed_handoff.md` has the full routine.)
3. Add a row to both tables in section 1 and an entry in section 2, and update the next slowest rule. Commit the rule fix and this log update together; write `this commit` in the commit column, or fill in its id with the next commit.

## 4. Large-part evidence for fixes 1 and 2

Week-2 train part-00000 of each pack, `clean.py` `97c1a55b89f4` against `fc6d1a2deea4`: the output sha256 is the same on both.

| pack | docs | output sha256 (first 16) | docs/s before | docs/s after |
|---|---:|---|---:|---:|
| en-dclm | 46,245 | `2066a50c9d45f631` | 45.7 | 193.4 |
| en-fineweb-edu | 54,004 | `2a845063667d63e3` | 97.3 | 236.2 |

The timings are indicative only: the two runs shared one physical core (cores 0 and 1), so both were slowed. The identical output is not affected. The large parts run slower per doc than the 500-doc packs, and a profile of the first 1,000 docs of the en-dclm part ranks the rules in the same order with higher ms/doc (`DA-C5-002` 1.08 ms against 0.65), so the 500-doc profile is a fair guide to which rule to fix next. Fix 3 was not run on the large parts.

## 5. Output sha256 of the 13 sample packs (identical before and after every fix)

| pack | output sha256 (first 16) | pack | output sha256 (first 16) |
|---|---|---|---|
| code-cpp | `86df31e9a4b16abb` | en-nemotroncc | `f111b95a31e6d718` |
| code-go | `6c2c667bdbd4e89e` | en-nemotroncc-synth | `3dc350e529a4139d` |
| code-java | `0ae70771c29dbe0b` | math-finemath | `4e79a08fd226f614` |
| code-js-ts | `f4437f3607e8ddbe` | math-megamath | `51c5b8452f45d195` |
| code-python | `b0e431e0431423eb` | sci-finepdfs | `f67b3fa5b7a92b53` |
| code-rust | `ad6141d053488d1c` | en-dclm | `3fdbc3056421bbe7` |
| | | en-fineweb-edu | `4c8be607c9590b8e` |

## 6. Notes

- **TSAI's figures:** en-dclm about 45 docs/s matches what we measured before the fixes. The en-fineweb-edu figure of about 30,000 docs/s does not: we measure 94.7 docs/s on the same pack before the fixes. How it was obtained is unknown (a different sample, or rules not running); it should be checked with TSAI.
- **Indic packs** are not measured here. The 13 packs exclude `ind-mr-sangraha-v`.
- **Harm test difference to expect:** `harm_tests.md` for fixes 1 and 2 together has extra Indic lines for `ind-hi-sangraha-s` (not on this machine) that come from the Indic refresh in the "after" file, not from the fixes.
