# Local run: first-training pipeline on 5 packs (19 Nov 2026)

The same script as `jobs/2026-11-19-first-training.md`, run locally on 5 packs of tokenizer sample v0 (JOB_REQUEST.md
rule 2). It is not a production run: there is no inventory, and the shards use a test tokenizer.

| | |
|---|---|
| Code | `g1-pipeline` `9965416`, plus the `csv_rows` fix in this PR |
| Command | `python -I teams/01-data-a/pipeline/run_pipeline.py --config out/local-5pack/run.json` (`config/run.json`) |
| Inputs | 13 raw parts of sample v0 (8 train, 5 held-out): `ind-sa-fw2`, `ind-hi-fw2`, `en-fineweb-edu` (H3's three packs), `code-go`, `code-rust`, picked with `only` from the 86-part manifest (sha256 `7fd647c8…`) |
| H3 | `config/h3.json`: the job's `h3.json` with `max_docs_per_pack` 2000 and `max_minutes` 30. LaBSE `model.safetensors` sha256 `deaceb20…` (in `h3_summary.json`), on MPS in fp32 |
| Shards | `any_tokenizer` (dataset_version `test`), `tokens` 2^22 so that parts roll over; `config/pack_table.json` is the repo's table with lane `local-trial` for the three non-code packs |
| Hardware | `environment.txt`: Apple M4, 10 cores, 16 GB; Python 3.12.10 with the package versions listed |

There were three invocations, each logged; each resume used `"from"`, after the runner checked the earlier stages' digests:
1. `1-clean.log`: clean; interrupted during overlap.
2. `2-from-overlap.log`: overlap and H3; stopped by the `csv_rows` bug (`h3_matches.csv: cannot be read as CSV with a "pack_id_a" column`).
3. `3-from-h3.log`: H3 to reconcile, with the fix.

## Result

All stages from clean to reconcile ran; 118 checks, 0 failed (`summaries/pipeline_manifest.json`).

| Stage | Result | Time |
|---|---|---|
| clean (spec v1.1) | 13 parts, 0 errors; 237,898 raw → 228,313 cleaned | 288 s |
| overlap | 6 H1 groups; 556 qualifying pairs (H1 6, H2 550) | 1,095 s (one core) |
| H3 | 677 pairs verified, 0 qualifying (2,000 documents per pack) | 147 s (vectors from the cache; 308 s uncached) |
| dedup, apply | 32 groups, 83 removed, 0 held-out removed | 5 s |
| F2 (pool, 4 workers) | 246 dropped, 0 errors | 628 s |
| survivor loss | 32 groups: 1 lost, 31 untouched; equal to dedup's summary and to the ledger | 0 s |
| ledger (mode B) | 237,898 rows: kept 227,984, clean 9,585, dedup 83, F2 246 | 7 s |
| shards | 8 train parts → 63 shards, 0 truncated, verified on disk; 5 held-out parts not sharded | 266 s |
| reconcile | 227,984 kept = 225,471 in shards + 199 left out (secret) + 2,314 held-out | 1 s |

Peak resident memory: 2.7 GB (overlap) and 2.0 GB (H3 to reconcile).

| Pack | Split | Raw | −clean | Cleaned | −dedup | −F2 | Final |
|---|---|---|---|---|---|---|---|
| code-go | train | 83,267 | 6,312 | 76,955 | 6 | 96 | 76,853 |
| code-go | held-out | 872 | 62 | 810 | 0 | 2 | 808 |
| code-rust | train | 60,126 | 1,926 | 58,200 | 58 | 36 | 58,106 |
| code-rust | held-out | 612 | 17 | 595 | 0 | 0 | 595 |
| en-fineweb-edu | train | 71,933 | 559 | 71,374 | 7 | 84 | 71,283 |
| en-fineweb-edu | held-out | 732 | 6 | 726 | 0 | 0 | 726 |
| ind-hi-fw2 | train | 14,261 | 460 | 13,801 | 0 | 28 | 13,773 |
| ind-hi-fw2 | held-out | 132 | 1 | 131 | 0 | 0 | 131 |
| ind-sa-fw2 | train | 5,908 | 241 | 5,667 | 12 | 0 | 5,655 |
| ind-sa-fw2 | held-out | 55 | 1 | 54 | 0 | 0 | 54 |
| **total** | | **237,898** | **9,585** | **228,313** | **83** | **246** | **227,984** |

## Not covered

- The p1536 tokenizer, the production lanes and the licence fields.
- `inventory`, `build_inventory.py` and `prepare_run.py`, which need all 38 packs.
- H3 on every document, and per-pair sentence thresholds.
- The shard stage's `empty`, `all_left_out` and restart paths.
