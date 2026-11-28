# B4: validation shards from held-out parts (28 Nov 2026)

Evidence for `run_shards.py --split`, the fixed-seed validation slice (`--validation-fraction`, `--validation-seed`) and
the `n_bytes` / `n_raw_bytes` columns of `docs.parquet`. IDs, counts and hashes only, never text.

## Input

The `smoke-corpus-v1` pipeline run (local, not in the repository): sample v0's 38 packs, 76 parts (38 train, 38 held-out),
7,168 raw docs; after clean, dedup and F2, **6,979 final docs: 3,700 train and 3,279 held-out**. Its `final/` folder is the
input of every run below.

- `pipeline_manifest.json` sha256 `c22e1ac5e0932e36…`; pack table (`pack_metadata.json`, with licences) `0fef5b82fe096ba5…`
- tokenizer: G3's frozen p1536, sha256 `e6b93a93a60520d7…`; `dataset_version` `corpus-v1`
- this is a small input for checking the format and the checks, not for rates or bits per byte

## Commands (from the repository root)

```bash
R=out/pipeline/smoke-corpus-v1; T=<p1536>/tokenizer.json; P=out/smoke-corpus-v1-inputs/pack_metadata.json
S="--input $R/final --manifest $R/pipeline_manifest.json --tokenizer $T --dataset-version corpus-v1 --pack-table $P --workers 1"
RAYON_NUM_THREADS=1 python -I teams/01-data-a/shards/run_shards.py $S --split validation --out out/b4-evidence/validation-all
RAYON_NUM_THREADS=1 python -I teams/01-data-a/shards/run_shards.py $S --split validation --validation-fraction 0.1 --out out/b4-evidence/validation-slice10
RAYON_NUM_THREADS=1 python -I teams/01-data-a/shards/run_shards.py $S --split validation --validation-fraction 0.1 --out out/b4-evidence/validation-slice10-again
RAYON_NUM_THREADS=1 python -I teams/01-data-a/shards/run_shards.py $S --out out/b4-evidence/train-default
python -I teams/01-data-a/shards/verify_shards.py --out out/b4-evidence/<run> --manifest $R/pipeline_manifest.json --tokenizer $T --pack-table $P
python -I teams/01-data-a/pipeline/reconcile_shards.py --ledger $R/ledger --shards out/b4-evidence/<run> --out out/b4-evidence/reconcile_<run>
```

Commit `a8f82c75`. AMD Ryzen 7 6800H (16 threads), Python 3.12.15, PyArrow 26.0.0, NumPy 2.5.2, tokenizers 0.23.3.

## Results

| Check | Result |
|---|---|
| `--split validation` (every held-out doc) | 38 validation shards, one per pack; 3,266 docs (13 left out as `secret`), 2,974,658 tokens; 38 train parts `not_sharded` |
| `--validation-fraction 0.1` (seed 20261101) | 38 validation shards; 370 docs, 341,657 tokens; 2,908 `not_in_slice`, 1 `secret` |
| `verify_shards.py` | 0 problems for both (`verify_validation-all.txt`, `verify_validation-slice10.txt`); first and last doc of each shard re-encoded from `final/`, `n_bytes` and `n_raw_bytes` checked |
| `reconcile_shards.py` | passes for both: every kept doc accounted for. The slice run adds the slice check: no shard doc outside the slice, and every part's `not_in_slice` count (counted by the writer, not listed) is the slice recomputed |
| Same command twice (slice 0.1) | 229 of 229 files byte-identical (every `.bin`, `.idx.npy`, `docs.parquet`, manifest, quality report, dump) |
| Default `--split` (train) against the shards written before this branch (`smoke-corpus-v1/shards`) | 76 of 76 `.bin` and `.idx.npy` byte-identical; 38 of 38 `docs.parquet` equal apart from the two new byte columns |
| `n_bytes` against `n_raw_bytes` | 17,775,691 against 17,807,813 bytes; they differ in 214 of 3,266 docs (the tokenizer's normalizer changes those texts) |

Per lane (validation shards, from the manifests and `docs.parquet`):

| Lane | Packs | Docs | Tokens | `n_bytes` | Docs (slice 0.1) | Tokens (slice 0.1) | `n_bytes` (slice 0.1) |
|---|---:|---:|---:|---:|---:|---:|---:|
| code | 6 | 581 | 660,728 | 2,544,876 | 64 | 47,323 | 178,582 |
| code-adjacent | 3 | 294 | 348,264 | 1,314,996 | 24 | 21,796 | 84,608 |
| english | 4 | 387 | 294,449 | 1,388,536 | 44 | 42,766 | 197,127 |
| indic | 22 | 1,768 | 1,256,041 | 10,848,864 | 205 | 188,357 | 1,471,623 |
| math | 2 | 176 | 215,271 | 834,311 | 25 | 29,888 | 109,417 |
| science | 1 | 60 | 199,905 | 844,108 | 8 | 11,527 | 50,308 |
| **total** | **38** | **3,266** | **2,974,658** | **17,775,691** | **370** | **341,657** | **2,091,665** |

## Files

- `summaries/validation-all/`, `summaries/validation-slice10/`: `shards_summary.json` (per part: status, shards, docs,
  tokens, left out per reason; the run's settings, with `split`, `validation_fraction` and `validation_seed`) and
  `reconcile_summary.json`
- `verify_validation-all.txt`, `verify_validation-slice10.txt`: `verify_shards.py` output
- `manifests_validation-all.sha256`: the sha256 of each of the 38 validation shard manifests (`--split validation`, every
  held-out doc). Each manifest pins its shard's files by sha256

## Not in this run

- The leak check of train against validation (B4's third part) comes next. Dedup rule 0 already removes every train copy
  of a held-out doc, so it verifies that on the final data.
- Which validation fraction the main run uses is TSAI's to say; the default (1) keeps every held-out doc.
- Rates: the runs above are dominated by starting a writer process per part; the shard writer's rate is B5's.
