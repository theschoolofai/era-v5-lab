# G9 Rotation R1/R2 — ranjani-cse

Frozen tokenizer: p1536 (sha256 e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b)
Fingerprints: v2, full set (set_sha256 2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a)

## R1 — per shard

| shard_id | docs scanned | docs flagged | set_sha256 |
|---|---|---|---|
| code-go-train-000000 | 56588 | 0 | 2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a |
| ind-hi-sangraha-v-train-000000 | 14483 | 0 | 2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a |

## R2 — each hit

No hits: 0 flagged documents, 0 canary hits on both shards.

Decoded `.text.parquet` kept local; no document text or item text in this report.

## Task 2 shards

Chain: `decode_shard.py` (p1536 `e6b93a93…25a64b`) → `decontam_check.py` (v2 full set, `set_sha256 2826a3b8…d22a`) → `canary_scan.py`.

| shard_id | payload_sha256 | docs | tokens | flagged | canary hits | set_sha256 |
|---|---|---|---|---|---|---|
| code-go-train-000000 | b68bf390d5800853f476ede764289f045993384fd6c771db0739b74adcc5b500 | 56588 | 56698571 | 0 | 0 | 2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a |
| ind-hi-sangraha-v-train-000000 | 78aca29173b76840de617be0b1335b9417a340adce7b0b0564b23e195b919ab1 | 14483 | 9254413 | 0 | 0 | 2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a |

No hits to report. Decoded text stays local.
