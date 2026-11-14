# clean() speed: spec v1 against the combined spec v1.1 (14 Nov 2026)

`spec_v1/run_clean.py` on each 500-doc pack: the whole `clean()`, shared F1 included. Each pack was timed 3 times with spec v1's `clean.py` as on TSAI main (sha256 `22d818c72c9f…`), and 3 times with the one built from the combined sheet (`2034fe8f84b3…`); the best of 3 counts. Hardware: Apple M4 (arm64, 10 cores, 16 GB), macOS, Python 3.12.10; one process, so one core, no core pinning. `run_clean.py` reports seconds to 0.1 s.

Spec v1 here has no speed fixes of its own beyond TSAI main. Smita's spec v1 math speed fixes (patilvijay23/era-v5-lab#43), which make math-finemath 2.3x faster, go into the `clean.py` PR, on Vijay's ruling.

```bash
cd teams/01-data-a/spec_v1 && python3 -I run_clean.py --pack <pack>.parquet --out <out>
```

Output, one line per pack: the three runs and the best of each version.

```
code-cpp PASS gold 0 0 | not passing: [] | out of scope acting: []
code-go PASS gold 0 0 | not passing: [] | out of scope acting: []
code-java PASS gold 0 0 | not passing: [] | out of scope acting: []
code-js-ts PASS gold 0 0 | not passing: [] | out of scope acting: []
code-python PASS gold 0 0 | not passing: [] | out of scope acting: []
code-rust PASS gold 0 0 | not passing: [] | out of scope acting: []
en-dclm PASS gold 0 0 | not passing: [] | out of scope acting: []
en-fineweb-edu PASS gold 0 0 | not passing: [] | out of scope acting: []
en-nemotroncc FAIL gold 2 0 | not passing: [('A8', 'FAIL')] | out of scope acting: []
en-nemotroncc-synth PASS gold 0 0 | not passing: [] | out of scope acting: []
math-finemath FAIL gold 1 1 | not passing: [] | out of scope acting: []
math-megamath PASS gold 0 0 | not passing: [] | out of scope acting: []
sci-finepdfs FAIL gold 4 1 | not passing: [('DA-C7-004', 'FAIL'), ('C7', 'FAIL')] | out of scope acting: []
code-cpp | spec_v1 runs: 1.0 1.0 1.2 best 1.0 s = 500 docs/s, errors 0 | combined runs: 1.0 1.0 1.0 best 1.0 s = 500 docs/s, errors 0
code-go | spec_v1 runs: 0.9 0.9 0.9 best 0.9 s = 556 docs/s, errors 0 | combined runs: 0.9 0.9 0.9 best 0.9 s = 556 docs/s, errors 0
code-java | spec_v1 runs: 0.8 0.8 0.8 best 0.8 s = 625 docs/s, errors 0 | combined runs: 0.8 0.8 0.8 best 0.8 s = 625 docs/s, errors 0
code-js-ts | spec_v1 runs: 0.5 0.5 0.5 best 0.5 s = 1000 docs/s, errors 0 | combined runs: 0.5 0.5 0.5 best 0.5 s = 1000 docs/s, errors 0
code-python | spec_v1 runs: 1.1 1.1 1.3 best 1.1 s = 455 docs/s, errors 0 | combined runs: 1.3 1.1 1.1 best 1.1 s = 455 docs/s, errors 0
code-rust | spec_v1 runs: 0.7 0.7 0.7 best 0.7 s = 714 docs/s, errors 0 | combined runs: 0.7 0.7 0.7 best 0.7 s = 714 docs/s, errors 0
en-dclm | spec_v1 runs: 1.1 1.1 1.1 best 1.1 s = 455 docs/s, errors 0 | combined runs: 1.1 1.1 1.1 best 1.1 s = 455 docs/s, errors 0
en-fineweb-edu | spec_v1 runs: 0.8 0.8 0.8 best 0.8 s = 625 docs/s, errors 0 | combined runs: 0.8 0.8 0.8 best 0.8 s = 625 docs/s, errors 0
en-nemotroncc | spec_v1 runs: 0.7 0.7 0.7 best 0.7 s = 714 docs/s, errors 0 | combined runs: 0.9 0.9 0.9 best 0.9 s = 556 docs/s, errors 0
en-nemotroncc-synth | spec_v1 runs: 0.4 0.3 0.3 best 0.3 s = 1667 docs/s, errors 0 | combined runs: 0.4 0.4 0.3 best 0.3 s = 1667 docs/s, errors 0
math-finemath | spec_v1 runs: 3.0 3.0 3.2 best 3.0 s = 167 docs/s, errors 0 | combined runs: 4.4 4.1 4.1 best 4.1 s = 122 docs/s, errors 0
math-megamath | spec_v1 runs: 1.3 1.2 1.2 best 1.2 s = 417 docs/s, errors 0 | combined runs: 2.2 2.2 2.2 best 2.2 s = 227 docs/s, errors 0
sci-finepdfs | spec_v1 runs: 4.0 4.0 4.0 best 4.0 s = 125 docs/s, errors 0 | combined runs: 7.2 7.1 7.3 best 7.1 s = 70 docs/s, errors 0
ind-te-sangraha-v | spec_v1 runs: 0.8 0.8 0.8 best 0.8 s = 625 docs/s, errors 0 | combined runs: 0.8 0.8 0.8 best 0.8 s = 625 docs/s, errors 0
```
