# KE2 request R3: held-out code with identifiers (Python, JS/TS, C++)

Requested by Team 4 (KE2) for Lab 5 design task 00 (spelling, new words, rare words): R3, "code with identifiers
(Python, JS/TS, C++; names like x_velocity), held-out, 10-20 MB per language", run through the F2 check, with the licence
column kept.

```
python -I teams/01-data-a/ke2/heldout_code.py --packs <folder with the raw sample-v0 packs> --out out/ke2_r3
```

Needs pyarrow, regex and the cleaner's pins (`tree-sitter==0.26.0`, `tree-sitter-language-pack==1.22.1`, `ftfy==6.3.1`,
as in `jobs/2026-11-19-first-training/requirements_pipeline.txt`). About 40 s on two cores.

## What it gives

The held-out part of each of `code-python`, `code-js-ts` and `code-cpp` in sample v0 (the part the manifest lists for
the held-out split, checked by sha256 and row count). Each doc goes through, in order:

1. **Exact match with train:** a doc whose text equals a doc in the same pack's train parts is left out (none were).
2. **The pipeline's pinned cleaner** (`pipeline/clean.json`: `spec_v1_1/clean.py`, sha256 `d275556e…`), unchanged, so
   the text looks like training text (for example StarCoder's `<reponame>`/`<filename>`/`<gh_stars>` lines are removed).
3. **F2** (`spec_v1/run_f2.py`, G9's fingerprint set v2 `2826a3b8…`): G9's decontam check and canary strings. There is no
   separate decontam or canary run; F2 is that check.

| File | Held-out docs | In train | Cleaner dropped | Cleaner fixed | F2 dropped | Docs | Text (UTF-8) | sha256 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `code__python/docs.parquet` | 718 | 0 | 17 | 413 | 1 | 700 | 3.28 MB | `6fe42e91…` |
| `code__js-ts/docs.parquet` | 1,234 | 0 | 89 | 638 | 3 | 1,142 | 3.25 MB | `b33ca970…` |
| `code__cpp/docs.parquet` | 613 | 0 | 6 | 430 | 1 | 606 | 3.63 MB | `f327453d…` |
| **total** | 2,565 | 0 | 112 | 1,481 | 5 | 2,448 | 10.16 MB | |

F2's 5 drops are SWE-bench Live test items (3 docs) and two of G5's held-out JS items; their doc_ids and items are in
`r3_summary.json`. Compound identifiers (an inner `_` as in `x_velocity`, or a lower-to-upper step as in `xVelocity`):
17,765 distinct in Python, 16,634 in JS/TS, 24,242 in C++.

Columns: `doc_id, text, url, lang, lane, pack_id, source, license, license_source`, sorted by doc_id, zstd. `url` is
StarCoder's repo/path of the file, the attribution its licence asks for. Two runs give byte-identical files.

## Limits

- **Size: about 3.3–3.6 MB per language, not 10–20 MB.** Sample v0 holds one held-out part per pack, and train parts are
  not held-out. Corpus-v1's held-out split, when it lands, is the top-up: the same script reruns on it.
- **Source:** sample v0 (raw packs, cleaned here), not corpus-v1's shards.
- **Licence:** the pack-level licence of `approved_inputs.json` ("per-file permissive Stack licences; attribution
  required"). The packs carry no per-file licence; `url` names each file's repository for that.
- **Exact match only** against train: a near duplicate of a train doc (MinHash range) is not checked here.

## Files

- In the repository: `ke2/heldout_code.py`, `ke2/tests/test_heldout_code.py`, `ke2/results/r3/r3_summary.json` (no
  document text) and `ke2/results/r3/run.log`.
- Not committed (document text): the three `docs.parquet` in `out/ke2_r3/`, shared as `ke2_r3_heldout_code.tar`.
- **Link:** <to be added>
