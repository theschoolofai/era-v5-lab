# clean.py speed log: math rules

Follow-up to [speed_v1.md](speed_v1.md) (English rules), [speed_v1_code.md](speed_v1_code.md) (code rules) and [speed_v1_f1.md](speed_v1_f1.md) (F1 rule). Spec v1.1, Gate 2. This log covers the slow rules of the math packs (`math-finemath`, `math-megamath`): for each, what the fix was, docs/s per core before and after, and the checks showing that nothing else changed. The fixes are made in the spec v1.1 sheet (`spec_v1_1/sheets/specv1_1.md`, the sheet `clean.py` is built from; spec v1 is frozen). Last updated 16 Nov 2026. Reports counts, hashes and timings only, never document text.

Every fix passes three checks before it is logged:

1. **Output sha256 unchanged** on every pack tested (`doc_id`, final action and final cleaned text of every document, in order).
2. **Harm tests unchanged** (every rule and `clean()` on each pack: same harm result, same gold changed/dropped counts).
3. **Pytest suite passes.**

## 1. Speed, docs/s per core, before and after

500-doc sample packs, one core pinned to CPU 0, `clean()` loop only, best of 3 passes, before and after timed back to back. The rule time is the per-document time of the rule alone, from the per-rule profile (`spec_v1/run_clean.py`). Before the fix, `DA-C1-001` was 64% of the rule time on `math-finemath` (3.9 ms/doc); it does not run on `math-megamath`.

| # | rule (what it checks) | math-finemath docs/s | math-megamath docs/s | rule time math-finemath, ms/doc |
|---|---|---|---|---|
| 1 | `DA-C1-001` (site boilerplate) | 127.3 to 242.7 (1.91x) | 259.3 to 286.6 (1.11x) | 3.858 to 0.606 |

The other 29 of the 31 packs are 1.0x to 1.2x, timing noise (the packs this rule does not run on read about 1.1x in the same run, so about 5% of `math-megamath`'s figure is the same noise).

## 2. Status of each fix

| # | rule | output sha256 | harm tests | pytest | documents changed (math-finemath, 500 docs) | `clean.py` before | `clean.py` after | commit |
|---|---|---|---|---|---|---|---|---|
| 1 | `DA-C1-001` | same, 31 of 31 packs | unchanged, 31 of 31 packs | 2763 passed | ran on 487, fixed 97, dropped 0 | `9a4e3a87f124` | `ddf379d68e29` | this commit |

- **Baseline:** `clean.py` `9a4e3a87f124`, the build from `specv1_1.md` in commit `4149bcc`. The output sha256 of the two math packs under it: `math-finemath` `c6a3183c9d076f12`, `math-megamath` `6fb0de7bad7c44e0` (the v1.1 build; the hashes in [speed_v1.md section 6](speed_v1.md#6-output-sha256-of-the-13-sample-packs-identical-before-and-after-every-fix) are for the v1 build, which has 24 fewer rules).
- **Pytest:** the whole suite (`teams/01-data-a/tests` and `spec_v1_1/tests`), 1 test skipped, 51 subtests passed.
- **Harm tests:** `make_harm_tests.py` on all 31 packs, with the 18 Indic gold sets copied into both trees (as in [speed_v1_f1.md section 5](speed_v1_f1.md#5-commands)): every result file is identical before and after. Four packs do not pass their harm limit under the v1.1 `clean.py`, before and after alike (`en-nemotroncc`, `math-finemath`, `sci-finepdfs`, `ind-te-sangraha-v`; see [spec_v1_1/results/combined/validation.md](../../spec_v1_1/results/combined/validation.md)); `DA-C1-001` is not among the failing rules.

## 3. What each fix did

1. **`DA-C1-001`, site boilerplate (math-finemath).** The rule deletes a line that is generic site chrome (`C1_LINE`), or that holds one of 83 site phrases (`C1_SITE`, case-insensitive) and is at most 120 characters. It searched `C1_SITE` on every line first and tested the length second. Now the length test goes first (a line over 120 characters is kept whatever `C1_SITE` finds), and on a pure-ASCII line the search uses the lower-cased pattern on the lower-cased line instead of the `(?i)` pattern, which the engine runs much more slowly (3.3 to 0.57 ms/doc on the pack). The lower-cased pattern is the same pattern: every escape in `C1_SITE` is lower-case and it has no non-ASCII character, so `lower()` cannot change its meaning. A line with a non-ASCII character keeps the original `(?i)` regex.

The edit is to the `DA-C1-001` card of `specv1_1.md`; the `medicine_<family>.md` files are not read by the build and are not changed. Tests: `tests/spec_v1/test_speed_equivalence_math.py` (126 tests), against a frozen copy of the old rule (`c1_reference`, inside the test file).

## 4. Method and commands

x86_64, Python 3.12.15, one run at a time pinned to CPU 0 (`taskset -c 0`); timings vary by about 5%, so treat ratios under 1.1x as about equal. Before is the committed `clean.py` (`HEAD`), after is the rebuilt working copy (`python -I spec_v1/build/build_clean.py`, which builds from `specv1_1.md`); only `clean.py` differs between the two trees. Commands as in [speed_v1_f1.md section 5](speed_v1_f1.md#5-commands): `--before HEAD --after worktree --rules DA-C1-001 --profile-packs "math-finemath math-megamath"`, with the `build` and `trees` steps first, the Indic gold copied into both trees, then `speed profile harm count`.
