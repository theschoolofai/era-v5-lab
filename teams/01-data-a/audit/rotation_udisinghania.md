# Week 3 G1 rotation shard audit — udisinghania

**Status:** Draft, sample-only. Inspected local checkout at `f9fd0df` on 15 Nov 2026. Both assigned first-training shards are pending. Reviewer: Vijay.

## Sample rehearsal

Shard `code-go-train-000000`, dataset version `sample`. The manifest, format specification, and template are under [shards](../shards/).

| Check | Expected | Observed | Status |
| --- | --- | --- | --- |
| Manifest fields | All 28 keys in the v1 template | 28 keys, no missing or extra; SHA-256 fields are 64 lowercase hex characters | Pass |
| Index SHA-256 | `d808fcda4116f03d8017c4c6ade92c8914a64a2df5c3a530d447b92f6ada8ce0` | Exact match | Pass |
| Index offsets | int64, 272 entries for 271 documents, first offset 0, strictly increasing | All match | Pass |
| Index-derived token count | 262,032 | Last offset and sum of consecutive spans both 262,032 | Pass, index only |
| Payload size arithmetic | 1,049,152 bytes | 1,024 + 4 × 262,032 = 1,049,152 | Consistent with manifest; actual size pending |
| Quality report and cleaning pipeline hashes | Manifest values | Both match the Git blob bytes. Local Windows working copies use CRLF and yield different raw hashes. | Pass for committed bytes |
| Payload `.bin` | Manifest SHA-256, size, header, token count and EOS boundaries | File unavailable in checkout | Blocked |
| Document metadata `.docs.parquet` | Manifest SHA-256 and document metadata | File unavailable in checkout | Blocked |

Reproduce from the repository root with Python and NumPy:

```bash
python -c "import json, hashlib, numpy as np; from pathlib import Path; d=Path('teams/01-data-a/shards/sample'); m=json.loads((d/'code-go-train-000000.json').read_bytes()); t=json.loads((d.parent/'shard_manifest_v1.template.json').read_bytes()); print('fields',len(m),'missing',sorted(t.keys()-m.keys()),'extra',sorted(m.keys()-t.keys())); p=d/m['index_uri']; print('index sha256',hashlib.sha256(p.read_bytes()).hexdigest()); a=np.load(p,allow_pickle=False); print(a.dtype,a.shape,a[0],a[-1],(np.diff(a)>0).all(),np.diff(a).sum())"
git show f9fd0df:teams/01-data-a/shards/sample/code-go-train-000000.quality_report.json | sha256sum
git show f9fd0df:teams/01-data-a/shards/sample/cleaning_pipeline.json | sha256sum
```

Run the last two commands in Bash to hash the original Git bytes through the pipe.

## Assigned training shards

| Assignment | Status |
| --- | --- |
| First training shard | Pending canonical ID, manifest, and authorized artifact access |
| Second training shard | No second shard assigned yet; ID, manifest, and artifact access pending |

## Issue tracking

[Issue #448](https://github.com/theschoolofai/era-v5-lab/issues/448) tracks shard availability. No reproducible integrity defect was confirmed from the sample files inspected. When the assigned bytes arrive, record the exact versions and independently check the manifest, payload and sidecar hashes, and payload token count. Link any confirmed problems to existing issues or file reproducible reports.
