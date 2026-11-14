## Combined validation (14 Nov 2026)

`clean.py` was built from this sheet with `spec_v1/build/build_clean.py`, in a copy of the branch, not committed: the rebuild is task 2, due 17 Nov. It holds 246 rules and the shared F1: code 24, English 23, math 22, sci 24, Indic 153.
- **The harm runs:** `spec_v1/validate/make_harm_tests.py` (the #244 harness) on that `clean()`, with `harm_test.py` run as it is. ind-te-sangraha-v was run with `harm_test.py` on this sheet and Data B's gold.
- **The packs:** each is the same file as in #244 (sha256 checked).
- **Reports:** the per-pack reports (doc_ids, counts and digests only) go into the `clean.py` PR, with the rebuilt `clean.py` they test.

| pack | gold docs (limit) | `clean()`, all rules in order: changed + dropped | result | without the gold contradictions | spec v1 alone (#244) |
|---|---|---|---|---|---|
| code-cpp, code-go, code-java, code-js-ts, code-python, code-rust | 122, 163, 116, 204, 141, 234 | 0 each | PASS | — | 0 |
| en-dclm, en-fineweb-edu, en-nemotroncc-synth | 62, 158, 326 | 0 each | PASS | — | 0 |
| en-nemotroncc | 129 (1) | 2: `056cc9bc44c927e2` (`DA-A8-003`), `fd16036899796ca4` (`DA-A8-004`) | **FAIL** | 0/127 PASS | 0 |
| math-finemath | 86 (1) | 2: `2d328b828fa97706` (`DA-A8-001`), `0f119a596e8b7f63` dropped (`DA-C9-003`) | **FAIL** | 0/84 PASS | 0 |
| math-megamath | 26 (1) | 0 | PASS | — | 0 |
| sci-finepdfs | 202 (2) | 5: `920855df51f37db8` (`DA-A7-001`); `4b958ac1f45443b5`, `d0a0a41263e845f5`, `eb6ad9726f2d7ddd` (`DA-C7-004`); `b6fd81dbf90b0d17` dropped (`DA-C7-005`, a false positive) | **FAIL** | 1/198 PASS | 0 |
| ind-te-sangraha-v | 80 (1) | 2: `01418489e7410bdf`, `85644a4840025b6f` (`DB-C6-001`) | **FAIL** | 0/78 PASS | 0 |

- **Spec v1's rules first change nothing in the gold.** On every pack, the combined `clean()` changes exactly the gold docs that the v1.1 rules change on their own. Spec v1 alone changes none of them.
- **Every touched gold doc is a gold contradiction or a recorded false positive.** Vijay agreed to marking gold contradictions: they are left out of the count for their rule, and re-read at the next gold refresh.
- **Scope holds:** no rule acted on a pack it doesn't cover (`make_harm_tests.py` runs each rule on every other pack).
- **The other 17 Indic packs:** no v1.1 rule runs on them, so #244's results stand there. They need Data B's gold, and most aren't on this machine.

**Speed.** `spec_v1/run_clean.py` timed the whole `clean()`, shared F1 included, on 500 docs a pack: Apple M4, one core, Python 3.12.10, the best of 3 runs, 0 errors (the full table, `speed.md`, goes into the `clean.py` PR). Spec v1 is as on TSAI main; its math speed fixes (#43) are for the `clean.py` PR.

| pack | spec v1 → combined, docs/s |
|---|---|
| code-cpp, code-go, code-java, code-js-ts, code-python, code-rust | 500, 556, 625, 1,000, 455, 714 → the same |
| en-dclm, en-fineweb-edu, en-nemotroncc, en-nemotroncc-synth | 455, 625, 714, 1,667 → 455, 625, 556, 1,667 |
| math-finemath, math-megamath | 167, 417 → **122, 227** |
| sci-finepdfs | 125 → **70** |
| ind-te-sangraha-v | 625 → 625 |

On math and science, the v1.1 rules run on every doc, and they add about 1 s and 3 s per 500 docs. Two speed passes went into them (`../results/sheets/harm_tests.md`, "Speed"): each fix gave identical output on every doc of 8 packs. Each v1.1 rule is a regex pass over the text, or a loop over its lines (about 10 rules, which compare a line with its neighbours). Python loops over tokens are gone. A loop over characters is left in one place: `DA-A7-003`'s lowercase test on a non-ASCII line, where a regex can't stand in for `str.islower`. ASCII lines, most of them, take one regex search.
