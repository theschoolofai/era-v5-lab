# clean.py speed: before and after the F1 and D3 fixes

Spec v1.1, Gate 2. Measured on 11 Nov 2026. Reports counts, hashes and timings only, never document text.

**Result.** `clean.py` is 4.3x to 6.3x faster on the four English packs (en-dclm 49.9 to 311 docs/s per core) and the output is byte-identical on all 13 sample packs and on two large week-2 parts (100,249 docs). The harm test results are unchanged. The code, math and science packs are not slower (1.0x). The next slowest rule is `DA-C5-002`.

## 1. What was measured

| | before | after |
|---|---|---|
| `clean.py` sha256 (first 12) | `97c1a55b89f4` | `fc6d1a2deea4` |
| source | `730253d^` (the last commit before the F1 fix; same file as `8da2ac4`) | HEAD `bb0d997` |
| the two fixes | none | `DA-F1-005` per-line ORGANISATION search, skipped on lines with no `@` or digit (`730253d`); `DA-D3-003` ASCII fast path and cached script lookup per character (`8a74553`) |

The "after" file also contains the Indic refresh (`3b91add`). It changes rule scopes for Indic packs only; none of the 13 packs below is Indic, and their outputs match.

- Machine: AMD Ryzen 7 6800H, Python 3.12.15, each run pinned to one core with `taskset -c 0` (the two large runs ran at the same time, on cores 0 and 1).
- Timing: only the `clean(doc)` loop, packs already in memory. Best of 3 passes on the 500-doc packs; one pass on the large parts.
- Tool: [`oneoff/speed_check.py`](../../oneoff/speed_check.py). The output sha256 of a pack covers, for every document in file order, its `doc_id`, the final action (keep, fix or drop) and the final cleaned text, so equal sha256 means byte-identical output. Input pack hashes were equal too.

## 2. Speed, docs/s per core

The 500-doc sample packs (the packs TSAI timed):

| pack | before | after | speed-up | TSAI's number (main, `d3464bda`) |
|---|---:|---:|---:|---|
| en-dclm | 49.9 | 311.0 | 6.2x | about 45 |
| en-fineweb-edu | 97.9 | 419.9 | 4.3x | about 30,000 (see note) |
| en-nemotroncc | 102.5 | 521.6 | 5.1x | |
| en-nemotroncc-synth | 165.3 | 1047.3 | 6.3x | |

Large parts, `week-2/train/<pack>/part-00000.parquet`:

| pack | docs | before | after | speed-up |
|---|---:|---:|---:|---:|
| en-dclm | 46,245 | 45.7 | 193.4 | 4.2x |
| en-fineweb-edu | 54,004 | 97.3 | 236.2 | 2.4x |

Other packs, 500 docs each (not targeted by the fixes; re-measured twice, alternating before and after, best of 5): code-cpp 322/313, code-go 427/425, code-java 482/482, code-js-ts 699/679, code-python 300/299, code-rust 444/449, all 1.0x. The first run showed 0.8x to 0.9x on the code packs; the repeats show that was noise. math-finemath 166/175, math-megamath 504/534 and sci-finepdfs 151/152 are 1.0x to 1.1x.

**Note on en-fineweb-edu.** We measured 98 docs/s before the fix on this machine, not 30,000. We do not know how the 30,000 was obtained (a different sample, or rules not running); please check with TSAI. The numbers here are all measured on one machine, with the same input files before and after.

The speed-up is smaller on the large parts than on the 500-doc packs (en-dclm 4.2x against 6.2x), and the large parts run slower per doc after the fix (193 against 311 docs/s). We did not find out why. The 500-doc profile in section 5 may therefore not match the cost at scale, and should be repeated on a large slice (for example `--limit 5000` of a week-2 part) before Gate 2.

## 3. Same output (sha256)

All 13 sample packs have the same output sha256 before and after (500 docs each):

| pack | output sha256 (first 16) | pack | output sha256 (first 16) |
|---|---|---|---|
| code-cpp | `86df31e9a4b16abb` | en-nemotroncc | `f111b95a31e6d718` |
| code-go | `6c2c667bdbd4e89e` | en-nemotroncc-synth | `3dc350e529a4139d` |
| code-java | `0ae70771c29dbe0b` | math-finemath | `4e79a08fd226f614` |
| code-js-ts | `f4437f3607e8ddbe` | math-megamath | `51c5b8452f45d195` |
| code-python | `b0e431e0431423eb` | sci-finepdfs | `f67b3fa5b7a92b53` |
| code-rust | `ad6141d053488d1c` | en-dclm | `3fdbc3056421bbe7` |
| | | en-fineweb-edu | `4c8be607c9590b8e` |

The two large parts are also identical: en-dclm part-00000 (46,245 docs) `2066a50c9d45f631`, en-fineweb-edu part-00000 (54,004 docs) `2a845063667d63e3`. The same actions were also seen on the 500-doc en-dclm pack: 437 kept, 54 fixed, 9 dropped, both before and after.

## 4. Harm tests unchanged

`spec_v1/validate/make_harm_tests.py` was run with each `clean.py` on the same packs and the same gold (`harm_test.py` unchanged). Every rule alone, every disease code, and `clean()` on each of the 13 packs gave the same results before and after: the 13 per-pack result files differ only in `rules_file_sha256` (the new `clean.py` hash), and no PASS cell and no gold changed or dropped count differs.

`harm_tests.md` has three further differences, all about the Indic pack `ind-hi-sangraha-s`, which is not on this machine: it is added to the "not run on" list of the F1 rows, a row `G3` (applies to none of the 13 packs) and a "pack not on this machine" line. `clean.py` has no mention of `ind-hi-sangraha-s` at `730253d^` and 43 at `3b91add`, so these come from the Indic refresh and not from the two speed fixes.

## 5. Profile, and the next slowest rule

`run_clean.py` per-rule time on the 500-doc packs, one core, top 3 rules and the two fixed rules:

en-dclm (rules took 10.2 s before, 1.6 s after)

| rule | before: share, ms/doc | after: share, ms/doc |
|---|---|---|
| `DA-F1-005` (PII) | 83.3%, 17.284 | 13.2%, 0.435 |
| `DA-D3-003` (foreign lines) | 4.2%, 0.872 | 6.3%, 0.211 |
| `DA-C5-002` (keyword lists) | 3.2%, 0.651 | **20.4%, 0.668** |
| `DA-B4-010` | 2.4%, 0.503 | 15.5%, 0.513 |

en-fineweb-edu (rules took 5.1 s before, 1.2 s after): `DA-F1-005` 75.0% (7.653 ms/doc) to 14.6% (0.338), `DA-D3-003` 6.8% (0.690) to 5.6% (0.130), `DA-C5-002` 4.8% (0.492) to **21.3% (0.495)**.

**Next slowest rule: `DA-C5-002`** (English C5, drops a document with two or more injected-keyword markers or a run of short pipe-separated phrases): 0.668 ms/doc, 20.4% of the time on en-dclm and 21.3% on en-fineweb-edu. Then `DA-B4-010` (15.5% and 16.4%), then `DA-F1-005` again at about 13% to 15% and `DA-B4-008` (10% and 11%). The profile is flat now: no rule takes more than about 21%, so speeding up one more rule gains at most 1.25x. This was not changed here.

## 6. Reproduce

```
python -I oneoff/speed_check.py run --clean-dir <tree>/teams/01-data-a/spec_v1 --packs <packs> --exclude ind-mr-sangraha-v --repeat 3 --out run.json   # once per clean.py
python -I oneoff/speed_check.py compare before.json after.json
python -I spec_v1/run_clean.py --pack <packs>/en-dclm.parquet --out <dir>                                        # per-rule profile
```
