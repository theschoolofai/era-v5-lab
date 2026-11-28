# D2 and B3: the 1% sample run (baseline and hash-only)

The whole pipeline twice on the same 1% slice of tokenizer sample v0:
- **baseline:** corpus-v1's stages with the MinHash overlap;
- **hash-only (B3):** the clean job writes `text_hash`, and the overlap stage is `dedup/hash_overlap.py`, which finds exact
  copies from that column without reading text.

Both runs are without H3: it needs the LaBSE model, and B3 does not change it.

## Commands (from the repository root)

```bash
python3 -I teams/01-data-a/pipeline/local_trial/slice_sample.py --manifest teams/01-data-a/jobs/2026-11-02-tokenizer-sample-v0-clean/tokenizer_sample_v0_manifest.json --sample <the 86 raw parts> --out inputs/sample_1pct
RAYON_NUM_THREADS=1 python3 -I teams/01-data-a/pipeline/run_pipeline.py --config teams/01-data-a/jobs/2026-11-28-d2-b3-sample-1pct/run_baseline.json
RAYON_NUM_THREADS=1 python3 -I teams/01-data-a/pipeline/run_pipeline.py --config teams/01-data-a/jobs/2026-11-28-d2-b3-sample-1pct/run_hash.json
python3 -I teams/01-data-a/shards/provenance.py --input out/pipeline/d2-1pct-hash/final/train/code-go/part-00000.parquet --manifest out/pipeline/d2-1pct-hash/pipeline_manifest.json
python3 -I teams/01-data-a/shards/verify_shards.py --out out/pipeline/d2-1pct-hash/shards --manifest out/pipeline/d2-1pct-hash/pipeline_manifest.json --tokenizer inputs/sample_1pct/tokenizer.json
```

- `RAYON_NUM_THREADS=1` keeps the tokenizer on one thread, so the shard writer's rate is a per-core rate.
- The tokenizer is not G3's p1536: its sha256 is `01d968a7…`, p1536's is `e6b93a93…`. So the shards are marked `test`
  (`any_tokenizer`), and the rate is this tokenizer's.
- Logs are in `jobs/logs/2026-11-28-d2-b3-sample-1pct/`.

## Input

The slice keeps 1% of the rows of every part, at least one row each, chosen by seed 20261128. That is all 86 parts (48
train, 38 held-out), **14,450 of 1,444,766 rows**, 62.2 MB of text. The slice manifest's sha256 is `0b1a3e43…`.

## Results

Commit `2d09b023`. Apple M4, 10 cores, 16 GiB RAM. Python 3.12, PyArrow 23.0.1, NumPy 2.4.3.

| Stage | Baseline: seconds | Hash-only: seconds | Rows (both runs) |
|---|---|---|---|
| clean | 10.1 | 12.0 | 14,450 read, 344 dropped, 14,106 kept |
| overlap | **18.5** (MinHash, 16 workers) | **0.9** (exact hash) | no qualifying pair in either run |
| dedup | 1.0 | 0.9 | 0 removed |
| apply | 0.1 | 0.1 | 14,106 |
| F2 | 35.5 | 34.6 | 14 dropped |
| survivor_loss | 0.3 | 0.3 | 0 groups |
| ledger | 0.9 | 0.9 | 14,450 raw rows accounted for |
| shards | 151.6 | 146.8 | 14,092 final, 48 shards, 11,987,677 tokens |
| reconcile | 0.5 | 0.5 | |
| **total** | **218.5** | **197.0** | |

- **Checks:** 108 of 108 pipeline checks pass in each run. Each manifest records `git_commit 2d09b023`.
- **Same shards:** the 48 shard `.bin` files are byte-identical between the two runs.
- **Overlap peak RSS:**
  - MinHash: 233 MB in its largest worker, 104 MB in the main process;
  - hash-only: 135 MB in one process. It read 14,106 hashes, all distinct.
- **Provenance:** the provenance chain of `train/code-go/part-00000` passes. The run's `cleaning_pipeline.json` records
  `"method": "exact_hash"`, with the key and its `normalize_id`.
- **`verify_shards.py`:** 0 problems.
- **Tokenizing rate, one thread:**
  - 11,987,677 tokens in 148.1 s and 143.6 s of shard-writer time (summed over parts);
  - that is **80,900–83,500 tokens per second per core**;
  - this includes each part's process start-up and Parquet I/O.
- **Logs:**
  - `jobs/logs/2026-11-28-d2-b3-sample-1pct/`: `slice.txt`, `baseline.txt`, `hash.txt`, `provenance_hash.txt`,
    `verify_shards_hash.txt`;
  - each run's `pipeline_manifest.json`, `overlap_summary.json`, `shards_summary.json` and `cleaning_pipeline.json` are
    under `summaries/`.
- **The two `pipeline_manifest.json` copies are repo-relative.** In each, the `--config` paths of the clean, overlap and
  dedup commands were written by the run as absolute paths on the machine. In the copies they read
  `out/pipeline/<run>/cfg/<stage>.json`, like every other path in the manifest. Those 3 lines are the only difference.
  The run's own files have these sha256:
  - baseline `1df062d0a387957a394488951b0e2e365363bcf9eacbe07bfe85555c8bb6fa21`;
  - hash-only `1ae939402cf1e3c7fcfc29ef32db614a6a70789f4a3f76814501862613e3a824`, the `manifest_sha256` that
    `provenance_hash.txt` records.

## Speed rule check (the changed code)

- **No GPU code.** No file imports torch or CUDA, so there is no host-device sync to check.
- **`dedup/hash_overlap.py`:**
  - The checks on each part's columns, the grouping of every hash (Arrow dictionary encoding, then NumPy `bincount`
    and `argsort`), and the docs and matches outputs all run in Arrow or NumPy.
  - Python loops only over parts, config keys and packs.
  - The static grep's `.tolist()` hit, which turned every edge into Python objects to write `overlap_matches.csv`, was
    replaced by one `pyarrow.csv.write_csv` call. The packs now come by `take()` instead of a per-row `to_numpy()`.
- **`pipeline/clean_job.py`:**
  - `text_hash` and `key_words` are computed per document, inside the loop the job already runs over each document
    for `clean.clean()`. That adds no loop and no pass.
  - The H1 key cannot be built in Arrow: it is `normalize.match_key` (Python, and frozen) followed by `casefold`, which
    Arrow's lower-casing does not match. It has to equal the key `minhash_overlap.py` hashes.
- **`shards/provenance.py`:** adds no loop; it reads two JSON summaries.
- **`pipeline/local_trial/slice_sample.py`:** picks rows with NumPy and Arrow `take`. It loops only over the 86 parts.

## What the numbers say, and do not say

- **Run-to-run noise.** Clean, F2 and shards do the same work in both runs, apart from the clean job's hash columns.
  Their differences (+1.9 s, −0.9 s, −4.8 s) are within the noise between runs on this machine. The clean job's added
  cost is not separated from that noise here.
- **Exact copies.** The 1% slice holds none, and neither stage found any. Taking 1% of each part breaks most copy pairs
  apart: the full sample has 148 documents in exact-copy groups. So this run shows that hash-only dedup is a drop-in (same
  checks, same shards, a valid provenance chain) and that it is fast. It does not show how much it removes at corpus
  scale.
- **Shards dominate at this size.** About 3 s per part for 48 parts. How much of that is process start-up and how much
  is tokenizing is not measured here.
