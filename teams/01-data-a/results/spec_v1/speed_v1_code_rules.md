# clean.py speed log: code rules (spec v1.1)

Follow-up to [speed_v1_code.md](speed_v1_code.md), which covers `DA-E3-004` and the shared F1 on the code packs (measured on the v1 cleaner, 11 Nov). This log covers five more slow rules of the six code packs (`code-cpp`, `code-go`, `code-java`, `code-js-ts`, `code-python`, `code-rust`), made on the spec v1.1 build: for each, what the fix was, docs/s per core before and after, and the checks showing that nothing else changed. The fixes are made in the spec v1.1 sheet (`spec_v1_1/sheets/specv1_1.md`, the sheet `clean.py` is built from; spec v1 is frozen). Same format as [speed_v1_math.md](speed_v1_math.md) and [speed_v1_f1.md](speed_v1_f1.md). Last updated 17 Nov 2026. Reports counts, hashes and timings only, never document text.

The fixes were made in two rounds, each measured with its own `speed_compare` run: round 1, four rules together (`--rules DA-A4-002,DA-A6-001,DA-E3-003,DA-E2-001`, commit `a92ccb6`); round 2, `DA-E3-004` (`--rules DA-E3-004`, before is the build of round 1). Every fix passes three checks before it is logged:

1. **Output sha256 unchanged** on every pack tested (`doc_id`, final action and final cleaned text of every document, in order).
2. **Harm tests unchanged** (every rule and `clean()` on each pack: same harm result, same gold changed/dropped counts).
3. **Pytest suite passes.**

## 1. Speed, docs/s per core, before and after

### Round 1: four rules

500-doc sample packs, one core pinned to CPU 0, `clean()` loop only, best of 3 passes. The rule rows are the time of that rule in the per-rule profile (ms per doc, before to after); the last row is the whole `clean()` loop (docs/s per core, before to after, and the ratio).

| # | rule (what it checks) | code-cpp | code-go | code-java | code-js-ts | code-python | code-rust |
|---|---|---|---|---|---|---|---|
| 1 | `DA-A4-002` (replacement-character comments), ms/doc | 0.097 to 0.001 | 0.059 to 0.002 | 0.056 to 0.001 | 0.045 to 0.001 | 0.099 to 0.001 | 0.072 to 0.001 |
| 2 | `DA-A6-001` (Cyrillic look-alike letters), ms/doc | 0.160 to 0.030 | 0.126 to 0.022 | 0.098 to 0.018 | 0.075 to 0.017 | 0.174 to 0.031 | 0.127 to 0.024 |
| 3 | `DA-E3-003` (known keys and seeds), ms/doc | 0.311 to 0.037 | 0.183 to 0.034 | 0.189 to 0.034 | 0.146 to 0.018 | 0.353 to 0.074 | 0.236 to 0.031 |
| 4 | `DA-E2-001` (byte-array and base64 blobs), ms/doc | 0.169 to 0.095 | 0.100 to 0.056 | 0.102 to 0.055 | 0.074 to 0.041 | 0.179 to 0.090 | 0.113 to 0.058 |
| all four together | docs/s before to after | 655.5 to 1018.2 (1.55x) | 727.6 to 933.6 (1.28x) | 899.9 to 1257.3 (1.40x) | 1469.5 to 2319.1 (1.58x) | 650.1 to 986.6 (1.52x) | 1001.6 to 1705.6 (1.70x) |

Reading the table:

- `DA-A4-002` is now close to free (0.001 to 0.002 ms/doc, 30 to 100 times faster), `DA-E3-003` is 5 to 8 times faster and `DA-A6-001` 4 to 6 times faster. What is left of `DA-A6-001` (0.02 to 0.03 ms/doc) is the one `[\u0400-\u04ff]` search over each text.
- `DA-E2-001` is only 1.8 to 2.0 times faster, as expected: the byte-array half is guarded, the base64 half is not and now sets its cost.
- The four rules together took 0.34 to 0.81 ms/doc before (js-ts 0.34, cpp 0.74, python 0.81) and now take 0.08 to 0.20 ms/doc (js-ts 0.08, cpp 0.16, python 0.20), the sum of the four rows above. The whole loop gains less than that in ratio (1.28x to 1.70x), because the rest of `clean()` is unchanged.
- Slowest rules left after round 1 (share of the `clean()` time): `DA-E3-004` is first on five of the six packs (31% to 52%, 0.24 to 0.56 ms/doc; `code-go` has `DA-C3-002` first at 39%, 0.48 ms/doc and `DA-E3-004` second at 24%). Next come `f1_rule.py` (9% to 23%), then `DA-E1-007`, `DA-C1-005`, `DA-E1-008` and `DA-E1-004` on one or two packs each. `DA-E3-004` was done next (round 2).

### Round 2: `DA-E3-004`

Same sample packs and method. Before is `clean.py` `d932badc1fc5` (after round 1), after is `6a57276c0e83`.

| rule / measure | code-cpp | code-go | code-java | code-js-ts | code-python | code-rust |
|---|---|---|---|---|---|---|
| `DA-E3-004` (known keys and assigned secrets), ms/doc | 0.437 to 0.060 | 0.287 to 0.056 | 0.264 to 0.050 | 0.222 to 0.074 | 0.588 to 0.173 | 0.297 to 0.056 |
| whole `clean()` loop, docs/s before to after | 1045.6 to 1596.2 (1.53x) | 956.8 to 1167.6 (1.22x) | 1276.9 to 1666.9 (1.31x) | 2306.8 to 3415.7 (1.48x) | 991.6 to 1598.4 (1.61x) | 1730.9 to 2777.5 (1.60x) |

- `DA-E3-004` is 3.0 to 7.3 times faster (cpp 7.3x, go 5.1x, java 5.3x, rust 5.3x, js-ts 3.0x, python 3.4x), and the whole loop 1.22x to 1.61x.
- What is left on `code-python` (0.17 ms/doc) is mostly the third test, the search for a name word followed by its value: a separate timing of that search on the python sample gave about 0.10 ms/doc, because 86 of the 500 python files pass the second test (a quoted string of 16 or more characters after an `=` or `:`) and have a name word somewhere.
- Slowest rules left after round 2 (share of the `clean()` time): `f1_rule.py` is first on four packs (cpp 28%, js-ts 28%, python 31%, rust 37%; 0.12 to 0.21 ms/doc). `code-go` has `DA-C3-002` first at 49% (0.49 ms/doc), `code-java` has `DA-C1-005` at 19% (0.12 ms/doc, with `f1_rule.py` at 19%). Then `DA-E1-007` (cpp 18%), `DA-E1-008` (js-ts 26%), `DA-E2-001` (11% to 15% on five packs, its base64 half), `DA-E4-005` and `DA-E4-009`, and `DA-E3-003` (python 11%). `DA-C3-002` is the biggest single rule left.

## 2. Status of the fixes

| # | rule | output sha256 | harm tests | pytest | documents changed or dropped, 500 docs each | `clean.py` before | `clean.py` after | commit |
|---|---|---|---|---|---|---|---|---|
| 1 to 4 | `DA-A4-002`, `DA-A6-001`, `DA-E3-003`, `DA-E2-001` | the same on 31 of 31 packs | unchanged on 31 of 31 packs, all result files identical | 3120 passed | see below | `716c9a90093f` | `d932badc1fc5` | `a92ccb6` |
| 5 | `DA-E3-004` | the same on 31 of 31 packs | unchanged on 31 of 31 packs, all result files identical | 4067 passed | java 1, js-ts 2, rust 1 fixed (4 of 3,000) | `d932badc1fc5` | `6a57276c0e83` | this commit |

- **Baseline:** `clean.py` `716c9a90093f`, the build from `specv1_1.md` in commit `9c7d3c2` (after the math fixes); round 2 starts from `d932badc1fc5`, the build of round 1.
- **Pytest:** the whole suite (`teams/01-data-a/tests` and `spec_v1_1/tests`), 1 test skipped, 51 subtests passed. Round 1: 3120 passed, 159 of them new. Round 2: 4067 passed, 947 new, all in `tests/spec_v1/test_speed_equivalence_code_rules.py` (1106 tests in that file).
- **Harm tests:** as in [speed_v1_f1.md section 5](speed_v1_f1.md#5-commands): all 31 packs, the Indic gold copied into both trees. Result: unchanged, all result files identical before and after (every gold changed/dropped count and PASS). The `speed_compare` run reported `RESULT: PASS`.
- **Documents changed or dropped by the four rules** (the 500-doc sample of each code pack, 3,000 documents in all; counts from the after tree, and the output sha256 is the same as before, so the before tree gives the same):

| pack | `DA-A4-002` | `DA-A6-001` | `DA-E3-003` | `DA-E2-001` |
|---|---|---|---|---|
| code-cpp | 0 fixed | 1 fixed | 0 fixed | 1 dropped |
| code-go | 1 fixed | 2 fixed | 1 fixed | 0 |
| code-java | 0 | 0 | 0 | 0 |
| code-js-ts | 0 | 0 | 0 | 0 |
| code-python | 0 | 0 | 0 | 0 |
| code-rust | 0 | 0 | 0 | 0 |

  The rules are rare on these packs (1, 3, 1 and 1 documents of 3,000), which is why a guard that skips the regex on a text without the trigger pays off: nearly every text is kept as it is. The output sha256 is the same on all 31 packs, so the Indic and other non-code packs are untouched as well.
- **Round 2** (`DA-E3-004`, same packs and method): the output sha256 is the same on 31 of 31 packs; harm tests unchanged (all result files identical, every gold changed/dropped count and PASS); the `speed_compare` run reported `RESULT: PASS`. The rule fixes 4 of the 3,000 sampled documents, before and after (code-java 1, code-js-ts 2, code-rust 1; code-cpp, code-go and code-python 0).

## 3. What each fix did

Each fix is a necessary-condition guard: a cheap test that is true whenever the regex could match, so a text that fails it is returned as it is, and every other text goes through the original code. The regexes, their order and their replacements are unchanged.

1. **`DA-A4-002`, replacement-character comments.** The rule deletes a `//` comment line that holds U+FFFD and no ASCII letter or digit. `LOST` was run on every text. Every match holds a U+FFFD, so a text without one (nearly all) is kept without running it.

2. **`DA-A6-001`, Cyrillic look-alike letters.** The rule turns a Cyrillic look-alike inside a word that also has Latin letters into the Latin letter. `MIXED` starts with `\b` and two look-aheads, so the engine tried it at every position of every text. Every match holds a character of U+0400 to U+04FF (the range `MIXED` itself asks for), so a text with none is kept without running it.

3. **`DA-E3-003`, known keys and base32 seeds.** Two parts, both guarded. The five `KEYS` patterns each need a literal (`AKIA`, one of `ghp_ gho_ ghu_ ghs_ ghr_`, `sk-`, `xox`, `-----BEGIN `); each runs only when the text at that step holds one of its own, and the text is tested before each substitution, so the order and any cascade stay as they were. `SEED` is case-insensitive and was the larger cost: it needs an `=`, a quote and one of `secret`, `seed`, `totp`, `otp`, so it runs only when the text has `=` and `"` and the casefolded text holds `secret`, `seed` or `otp` (`totp` holds `otp`). The casefold matters: `(?i)` also lets U+017F (long s) match `s`, so `ſecret = "..."` is still found. A test checks, for every character below U+20000, that any character `(?i)` lets match a letter of these words keeps that letter under `casefold()`.

4. **`DA-E2-001`, byte-array and base64 blobs.** The rule drops a file when byte-array literals (`0x1f, 0x2a, ...`, 24 or more in a row) cover 10% of it, or base64-looking runs of 200 or more characters cover 40%. The byte-array regex needs 24 groups that each start with `0x`, so it runs only when the text holds 24 or more `0x` (`str.count` is exact here: `0x` cannot overlap itself). The base64 half has no cheap exact guard (it is a scan for a run of 200 characters of a wide class) and is unchanged.

5. **`DA-E3-004`, known keys and assigned secrets (round 2).** The rule replaces known key formats and a quoted value of 16 or more characters (200 at most) that looks random and is assigned to a secret-like name. The known formats were already tested for a literal; two things were slow. (a) The `ASSIGNED` regex starts with `\b[\w\-]*` and a case-insensitive list of eleven name alternatives, so it is tried from every word start, and the test that decided whether to run it (`ASSIGNED_HINT`, a case-insensitive regex for `secret`, `token`, `key`, `passw`, `pwd`) cost 0.07 to 0.19 ms/doc on its own. (b) The `gh` hint matched in 38% to 58% of code files ("right", "high"). Now: the hint for the GitHub-token pattern is `ghp_ gho_ ghu_ ghs_ ghr_`; and `ASSIGNED` runs only on a text that passes three tests, each true whenever `ASSIGNED` could match: (1) the casefolded text holds `secret`, `token`, `key`, `passw` or `pwd` (casefold, because `(?i)` also lets U+017F and U+212A match `s` and `k`; a test checks every code point below U+110000); (2) `[:=>]\s*` then a quote, 16 to 200 characters of the value class and the same quote, which is the end of any operator (`:=`, `=>`, `=`, `:`) and the value; (3) a name word followed by `ASSIGNED`'s own tail up to the closing quote, which is true wherever `ASSIGNED` matches because every name of `ASSIGNED` holds one of the five words and is followed by `[\w\-]*`, and which avoids searching from every word start. The tests are applied in that order to the text after the known-key step, as before. `ASSIGNED` itself, `_looks_random` and the replacements are unchanged. On the 500-doc samples the second test passes 3 to 86 documents per pack and `ASSIGNED` itself now runs on 1 to 4 (it ran on 90 to 174 documents per pack); it matches in 0 to 4.

The round 1 edits are to the `DA-A4-002`, `DA-A6-001`, `DA-E3-003` and `DA-E2-001` cards of `specv1_1.md`; round 2 is to the `DA-E3-004` card; the `medicine_<family>.md` files are not read by the build and are not changed. Tests: `tests/spec_v1/test_speed_equivalence_code_rules.py` (159 tests), against frozen copies of the old rules (`a4_reference`, `a6_reference`, `e2_reference` and `e3_reference`, inside the test file; the new rules are read from `specv1_1.md`): hand cases at the edge of every guard (23 and 24 `0x`, the first and last character of the Cyrillic range, each key shape and its too-short form, each seed word in each case), a sweep of the 10% share of `DA-E2-001` across its threshold, 10,000 or more random texts per rule with coverage assertions for every outcome, spies showing each regex is skipped when its guard fails and run when it holds, and the pack scope in `clean.py`. 19 hand-made mutations of the guards (a wrong literal, range edge, threshold, missing hint, `lower()` for `casefold()`, a guard removed) were all caught.

Round 2 tests (947, last section of the same file, helper names start with `e4_`), against `code_speed_reference.e3_reference` (`DA-E3-004` as in spec v1): the `ASSIGNED` pattern is the old one; every name of `ASSIGNED` holds a word of test 1; the operator class holds the last character of every operator; the casefold test over every code point; 53 names x 15 operator spellings x 3 quotes, value lengths from 1 to 300 (15, 16, 200 and 201 at the edges) with a missing or different closing quote, 37 structure cases (JSON, Rust and TypeScript types, `:=`, `=>`, a newline between name and operator, a long identifier, a long file with a late match, a dotted or dummy value), each known key shape and its edges, the five `gh` letters and every other character after `gh`; spies showing which of the three tests stops a text; 25,000 random texts with an assertion that whenever `ASSIGNED` matches, all three tests pass, and coverage for every outcome. 36 hand-made mutations (a dropped name word, an operator character, a length edge, `lower()` for `casefold()`, a changed tail, a test removed, a wrong hint) were all caught.

## 4. Method and commands

x86_64, Python 3.12.15, one run at a time pinned to CPU 0 (`taskset -c 0`); timings vary by about 5%, so treat ratios under 1.1x as about equal. Before is the committed `clean.py` (`HEAD`), after is the rebuilt working copy (`python -I spec_v1/build/build_clean.py`, which builds from `specv1_1.md`); only `clean.py` differs between the two trees. Commands as in [speed_v1_f1.md section 5](speed_v1_f1.md#5-commands): `--before HEAD --after worktree --rules DA-A4-002,DA-A6-001,DA-E3-003,DA-E2-001 --profile-packs "code-cpp code-go code-java code-js-ts code-python code-rust"` for round 1 and `--rules DA-E3-004` with the same packs for round 2 (before is `HEAD`, which then holds round 1), with the `build` and `trees` steps first, the Indic gold copied into both trees, then `speed profile harm count`.
