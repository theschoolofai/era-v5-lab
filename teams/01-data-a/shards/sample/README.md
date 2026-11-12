# Sample shard: code-go-train-000000

One shard from code-go (266 docs after `clean.py` and F2), with every shard file except two.

**Left out of the repo:** `code-go-train-000000.bin` (the tokens) and `code-go-train-000000.docs.parquet` (one row per doc).
pr-guard refuses `.bin` and `.parquet` files in a PR. `code-go-train-000000.dump.md` shows what both hold, and
`shard_writer.py` makes them again. Their hashes are in the manifest (`payload_sha256`, `sample_metadata_sha256`), so a
rebuilt copy can be checked against them.

**Stale:** written with the baseline tokenizer and EOS id 36, before G3's answers. It is rewritten with C3 (EOS 130822)
once the C3 `tokenizer.json` is here.
