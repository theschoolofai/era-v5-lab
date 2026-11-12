# Sample shard `code-go-train-000000`

Made by `make_sample_shard.py` from `part-00001.parquet` of `code-go` (tokenizer sample v0, train), after `clean.py` and F2 (fingerprints `2826a3b88321`). The first 266 docs of the cleaned part that fit in 262,144 tokens; 0 doc(s) skipped for an email-like or secret-like string. A real shard is filled to 2^26 tokens.

Tokenizer: BrahmicTokenizer-131K as pinned by G6 (`01d968a7970b`); EOS id 36 as G6's shards. Both are open with G3.

| file | bytes | sha256 |
|---|---:|---|
| `code-go-train-000000.bin` | 1,049,460 | `48abb1309ccbed5d…` |
| `code-go-train-000000.idx.npy` | 2,264 | `3da4e596f5814cf3…` |
| `code-go-train-000000.docs.parquet` | 9,397 | `b4f49e5439c7a5e5…` |
| `cleaning_pipeline.json` | 196 | `978ee8fbbb578361…` |

## `code-go-train-000000.bin`

- header, 1,024 bytes = 256 little-endian int32: `20261025` (magic), `2` (version), `262,109` (token count), then zeros
- then 262,109 little-endian uint32 token IDs; every doc ends with 36
- checks: G6's `open_shard` reads it; size = 1,024 + 4 × 262,109; each doc's tokens equal a fresh encode; 266 of 266 docs decode back to their text exactly

## `code-go-train-000000.idx.npy`

int64, 267 entries (start of each doc, then token_count): `[0, 319, 465, 876, 1333] … [261959, 262109]`

## `code-go-train-000000.docs.parquet`

One row per doc in shard order, IDs only. First rows:

| doc_id | input_part | input_row | n_tokens | lang_label |
|---|---|---:|---:|---|
| `bca061a4cf90b329` | `code-go_part-00001_clean.parquet` | 0 | 319 | code |
| `009e279dfca8ad00` | `code-go_part-00001_clean.parquet` | 1 | 146 | code |
| `ded7462c63ff1929` | `code-go_part-00001_clean.parquet` | 2 | 411 | code |
| `1922dd43189cde78` | `code-go_part-00001_clean.parquet` | 3 | 457 | code |
| `edc27d46452dd366` | `code-go_part-00001_clean.parquet` | 4 | 427 | code |

Doc length in tokens: min 41, median 514, max 11,923.
