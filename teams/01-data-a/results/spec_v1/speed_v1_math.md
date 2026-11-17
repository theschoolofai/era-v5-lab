# clean.py speed log: math rules

Follow-up to [speed_v1.md](speed_v1.md) (English rules), [speed_v1_code.md](speed_v1_code.md) (code rules) and [speed_v1_f1.md](speed_v1_f1.md) (F1 rule). Spec v1.1, Gate 2. This log covers the slow rules of the math packs (`math-finemath`, `math-megamath`): for each, what the fix was, docs/s per core before and after, and the checks showing that nothing else changed. The fixes are made in the spec v1.1 sheet (`spec_v1_1/sheets/specv1_1.md`, the sheet `clean.py` is built from; spec v1 is frozen). Last updated 16 Nov 2026. Reports counts, hashes and timings only, never document text.

Every fix passes three checks before it is logged:

1. **Output sha256 unchanged** on every pack tested (`doc_id`, final action and final cleaned text of every document, in order).
2. **Harm tests unchanged** (every rule and `clean()` on each pack: same harm result, same gold changed/dropped counts).
3. **Pytest suite passes.**

## 1. Speed, docs/s per core, before and after

500-doc sample packs, one core pinned to CPU 0, `clean()` loop only, best of 3 passes, before and after timed back to back. The rule time is the per-document time of the rule alone, from the per-rule profile (`spec_v1/run_clean.py`). Before fix 1, `DA-C1-001` was 64% of the rule time on `math-finemath` (3.9 ms/doc); it does not run on `math-megamath`. The rows were timed in separate runs, so the docs/s before of one row is not the docs/s after of the row above.

| # | rule (what it checks) | math-finemath docs/s | math-megamath docs/s | rule time math-finemath, ms/doc | rule time math-megamath, ms/doc |
|---|---|---|---|---|---|
| 1 | `DA-C1-001` (site boilerplate) | 127.3 to 242.7 (1.91x) | 259.3 to 286.6 (1.11x) | 3.858 to 0.606 | n/a (rule not on this pack) |
| 2 | `DA-D3-005` (foreign-script lines) | 253.6 to 279.9 (1.10x) | 296.9 to 339.8 (1.14x) | 0.358 to 0.033 | 0.434 to 0.038 |
| 3 | `DA-C7-001` (content lost in extraction) | 274.4 to 304.2 (1.11x) | 328.2 to 392.6 (1.20x) | 0.757 to 0.353 | 0.912 to 0.423 |
| 4 | `DA-A5-002` (ligatures and fullwidth letters) | 281.8 to 298.0 (1.06x) | 363.7 to 403.3 (1.11x) | 0.296 to 0.064 | 0.311 to 0.082 |
| 5 | `DA-A8-001` (words run together) | 308.3 to 329.9 (1.07x) | 412.6 to 455.5 (1.10x) | 0.339 to 0.129 | 0.388 to 0.187 |

In fix 2 the rule itself is 11x faster on both packs, but it was a small share of the time (about 9% and 15% before), so the whole-pack gain is 1.10x and 1.14x. In fix 3 the rule is 2.2x faster on both packs; it was the largest rule on them (20% and 28% of the time), so the whole-pack gain is 1.11x and 1.20x. In fix 4 the rule is 4.6x and 3.8x faster; it was about 9% and 12% of the time, so the whole-pack gain is 1.06x and 1.11x. In fix 5 the rule is 2.6x and 2.1x faster; it was about 10% and 15% of the time, so the whole-pack gain is 1.07x and 1.10x. The packs a fix does not touch read 1.0x to 1.2x, timing noise (for example `math-megamath` in fix 1: the rule is not on that pack).

## 2. Status of each fix

| # | rule | output sha256 | harm tests | pytest | documents changed, 500 docs each: math-finemath / math-megamath | `clean.py` before | `clean.py` after | commit |
|---|---|---|---|---|---|---|---|---|
| 1 | `DA-C1-001` | same, 31 of 31 packs | unchanged, 31 of 31 packs | 2763 passed | ran on 487, fixed 97, dropped 0 / not on this pack | `9a4e3a87f124` | `ddf379d68e29` | `10e4635` |
| 2 | `DA-D3-005` | same, 31 of 31 packs | unchanged, 31 of 31 packs | 2820 passed | ran on 500, fixed 7, dropped 1 / ran on 490, fixed 3, dropped 0 | `ddf379d68e29` | `ea14b0899085` | `5022efb` |
| 3 | `DA-C7-001` | same, 31 of 31 packs | unchanged, 31 of 31 packs | 2896 passed | ran on 479, fixed 0, dropped 12 / ran on 487, fixed 0, dropped 18 | `ea14b0899085` | `55f8653af9a1` | `72f4674` |
| 4 | `DA-A5-002` | same, 31 of 31 packs | unchanged, 31 of 31 packs | 2920 passed | ran on 500, fixed 6, dropped 0 / ran on 500, fixed 11, dropped 0 | `55f8653af9a1` | `097eb0a4fd3e` | `aabb1ec` |
| 5 | `DA-A8-001` | same, 31 of 31 packs | unchanged, 31 of 31 packs | 2961 passed | ran on 487, fixed 37, dropped 0 / ran on 490, fixed 32, dropped 0 | `097eb0a4fd3e` | `716c9a90093f` | this commit |

- **Baseline:** fix 1: `clean.py` `9a4e3a87f124`, the build from `specv1_1.md` in commit `3089352`; fix 2: `ddf379d68e29`, with fix 1 (`10e4635`); fix 3: `ea14b0899085`, with fix 2 (`5022efb`, merged as #49); fix 4: `55f8653af9a1`, with fix 3 (`72f4674`); fix 5: `097eb0a4fd3e`, with fix 4 (`aabb1ec`). The output sha256 of the two math packs under it: `math-finemath` `c6a3183c9d076f12`, `math-megamath` `6fb0de7bad7c44e0` (the v1.1 build; the hashes in [speed_v1.md section 6](speed_v1.md#6-output-sha256-of-the-13-sample-packs-identical-before-and-after-every-fix) are for the v1 build, which has 24 fewer rules).
- **Pytest:** the whole suite (`teams/01-data-a/tests` and `spec_v1_1/tests`), 1 test skipped, 51 subtests passed.
- **Harm tests:** `make_harm_tests.py` on all 31 packs, with the 18 Indic gold sets copied into both trees (as in [speed_v1_f1.md section 5](speed_v1_f1.md#5-commands)): every result file is identical before and after. Four packs do not pass their harm limit under the v1.1 `clean.py`, before and after alike (`en-nemotroncc`, `math-finemath`, `sci-finepdfs`, `ind-te-sangraha-v`; see [spec_v1_1/results/combined/validation.md](../../spec_v1_1/results/combined/validation.md)); `DA-C1-001`, `DA-D3-005`, `DA-C7-001`, `DA-A5-002` and `DA-A8-001` are not among the failing rules.

## 3. What each fix did

1. **`DA-C1-001`, site boilerplate (math-finemath).** The rule deletes a line that is generic site chrome (`C1_LINE`), or that holds one of 83 site phrases (`C1_SITE`, case-insensitive) and is at most 120 characters. It searched `C1_SITE` on every line first and tested the length second. Now the length test goes first (a line over 120 characters is kept whatever `C1_SITE` finds), and on a pure-ASCII line the search uses the lower-cased pattern on the lower-cased line instead of the `(?i)` pattern, which the engine runs much more slowly (3.3 to 0.57 ms/doc on the pack). The lower-cased pattern is the same pattern: every escape in `C1_SITE` is lower-case and it has no non-ASCII character, so `lower()` cannot change its meaning. A line with a non-ASCII character keeps the original `(?i)` regex.

2. **`DA-D3-005`, foreign-script lines (both math packs).** The rule removes a line that is mostly Cyrillic, Indic, kana, CJK, Hangul or Arabic script, and drops the document if more than 30% of its letters were in removed lines. It counted the letters of every line, and then of the whole text, even though a line with no foreign character is never removed and its count is never used. Now the whole text is returned as it is when it holds no foreign character (most documents), letters are counted only on lines that hold one, and the letters of the whole text are counted only when a line was removed (otherwise the drop test cannot fire). Documents with foreign script behave as before.

3. **`DA-C7-001`, content lost in extraction (both math packs).** The rule drops a document with four or more "gaps": a formula that was lost, leaving a sentence cut at `=` or at a dangling word ("the slope is"), an empty answer option, a keyword followed by a lone `.` `,` or `;` ("show that ."), or a `?` where a value was. The 14 Nov guards already skipped most work; what was left took 0.76 ms/doc (20%) on `math-finemath` and 0.91 ms/doc (28%) on `math-megamath`, in three places. All three are exact:
   - **Keyword followed by punctuation (`C7_NO_OBJECT`).** The regex starts with `\b`, so the engine tried it at every position. The punctuation is found first, with a regex that starts with a character set, and for each hit the whole word before it is checked with the same keyword regex. The counts are the same.
   - **Question marks.** The regex has two halves; the second starts with a lookbehind and was tried at every position. It is now searched only when the text holds `???`. The halves never overlap, so their counts add up.
   - **Candidate lines.** One search of three patterns joined with `|` over the whole text is replaced by a per-line test: a line that can be a gap ends, after its trailing blanks, in `=`, a letter, `)` or `.`, and only those lines run the three regexes. The loop that follows is unchanged.

4. **`DA-A5-002`, ligatures and fullwidth letters (both math packs).** The rule turns ligatures (`ﬁ`, `ﬃ`) into letters and fullwidth characters (`Ａ`, `１`, `！`) into ASCII, unless more than 1% of the letters are Chinese, Japanese or Korean (then the text is real CJK text and is left alone). It counted the letters of every document with a Python loop before looking for a fullwidth character, although the fullwidth step does nothing without one, and almost no document has one (2 and 3 of 500 do; the rule changes 6 and 11, mostly through ligatures). Now a text with no fullwidth character is returned after the ligature step, and the letters are counted only for a text that has one. The result is the same for every text.

5. **`DA-A8-001`, words run together (both math packs).** The rule puts back the space in `ProblemsThe` and `here.The` when the second word is a sentence opener (`The`, `Find`, `Question` and about 80 others), unless the line is code or inside a fence. It tested every line with `A8_CODE` and `A8_GLUED`, which both start with a lookbehind or `\b` and are tried at every position, although only 7% of documents change. Now a line is tested only if it holds the shape every match must have: a lowercase letter, an optional `.`, a capital and a lowercase letter. Other lines are returned as they are. A text with no three backticks has no fence, so the fence loop is skipped for it; a text with them uses the original loop. The result is the same for every text.

The edits are to the `DA-C1-001`, `DA-D3-005`, `DA-C7-001`, `DA-A5-002` and `DA-A8-001` cards of `specv1_1.md`; the `medicine_<family>.md` files are not read by the build and are not changed. Tests: `tests/spec_v1/test_speed_equivalence_math.py` (126 tests for fix 1, 57 for fix 2, 76 for fix 3, 24 for fix 4 and 41 for fix 5), against frozen copies of the old rules (`c1_reference`, `d3_reference`, `c7_reference`, `a5_reference` and `a8_reference`, inside the test file; the tests of fixes 3 to 5 read the new rule from `specv1_1.md`).

## 4. Method and commands

x86_64, Python 3.12.15, one run at a time pinned to CPU 0 (`taskset -c 0`); timings vary by about 5%, so treat ratios under 1.1x as about equal. Before is the committed `clean.py` (`HEAD`), after is the rebuilt working copy (`python -I spec_v1/build/build_clean.py`, which builds from `specv1_1.md`); only `clean.py` differs between the two trees. Commands as in [speed_v1_f1.md section 5](speed_v1_f1.md#5-commands): `--before HEAD --after worktree --rules <RULE_ID> --profile-packs "math-finemath math-megamath"`, with the `build` and `trees` steps first, the Indic gold copied into both trees, then `speed profile harm count`.
