# Exact-hash overlap stage (`hash_overlap.py`)

Finds exact copies (rule H1) across all packs from the clean job's `text_hash` column, without reading any document text.
It is a drop-in `"script"` for the pipeline's overlap stage, like `minhash_overlap.py`. It writes the same three files,
so dedup, apply, F2, the ledger, the shards and the reconciliation do not change. It finds no near copies (rule H2):
dedup's remove list from it is the H1 part of what `minhash_overlap.py`'s would be.

## How it works

1. **The inputs.** The clean job writes `text_hash` and `key_words` with `"text_hash": true` in its settings (see
   `pipeline/README.md`):
   - `text_hash` is the sha256 of the document's H1 key;
   - `key_words` is that key's number of words.
2. **The checks before anything is read.** The inputs folder's `job_summary.json` must record that `text_hash`, with
   h1_sha256.py's `normalize_id`.
3. **The read.** Only `doc_id`, `pack_id`, `text_hash` and `key_words` are read, by `workers` threads. Each column is
   checked with Arrow compute:
   - IDs present;
   - each hash 64 lowercase hex characters;
   - `key_words` 0 exactly when the hash is the empty key's.
4. **The grouping.** Arrow's dictionary encoding numbers the distinct hashes. NumPy `bincount` and a stable `argsort`
   give each group's first row. Every other member gets a star edge to that first row, as `minhash_overlap.py` writes
   its H1 edges.
5. **The outputs.**
   - `overlap_docs.parquet` has `minhash_overlap.py`'s columns and row order. Its `shingles` column is the key's
     5-gram positions (`words − 4`, at least 1), and 0 only for an empty key: the only value `dedup.py` reads it for.
     It is never null, because `dedup.py`'s Arrow filter would drop a null row.
   - `overlap_matches.csv` is written by one `pyarrow.csv.write_csv` call.

Memory: the table of all documents (IDs, the 64-character hash, row numbers), about 150 bytes per document.

## Running it

```bash
python teams/01-data-a/dedup/hash_overlap.py --config teams/01-data-a/dedup/hash_overlap.json
```

In a run config:

```json
"overlap": {"script": "teams/01-data-a/dedup/hash_overlap.py", "settings": "teams/01-data-a/dedup/hash_overlap.json"}
```

The clean stage then needs settings with `"text_hash": true`. An example is
`jobs/2026-11-28-d2-b3-sample-1pct/clean_text_hash.json`.

## Speed and end-to-end check

The 1% slice of tokenizer sample v0 (14,450 rows, all 86 parts), with H3 left out. The whole pipeline ran twice on it:
once with `minhash_overlap.py`, once with this stage. Details are in `jobs/2026-11-28-d2-b3-sample-1pct/README.md`.

| | MinHash | hash-only |
|---|---|---|
| overlap stage | 19.9 s, 16 workers, 266 MB peak per worker | 0.8 s, one process, 137 MB peak |
| pipeline checks | 108 / 108 | 108 / 108 |
| shards | 48 | 48, byte-identical |

Neither stage found a copy in the slice: the cut breaks most copy pairs apart.

## Tests

```bash
python3 -B -m pytest teams/01-data-a/dedup/tests/test_hash_overlap.py -q
```

19 tests:
- the same rows and H1 edges as `minhash_overlap.py` on the same parts;
- `dedup.py` run on the output removes only the train copies, never a held-out one, and sets empty documents aside;
- parts without text are enough;
- the input checks and the config checks.

## Limits

- Exact copies only: no near copies, no translations.
- The key is the H1 key, so two texts that differ only in case or whitespace are copies (as in every overlap stage).
- No test at corpus scale. With the whole table in memory, about 150 bytes per document, a billion documents would need
  partitioning the hash pass by the hash's first byte.
