# Rotation check, keshavamurali (draft)

Week 3 rotation in Team 01 Data A, tasks R1 (check 2 tokenized shards: manifest fields, hashes and token counts) and R2 (file each problem as an issue).

**Status: DRAFT.** This file checks the **sample** shard on main, as the lead asked, while the jobs that build the real shards on the first training data are set up. It does not claim the first-training-shard check (R1.2). That check follows when Tejaskumar assigns two real shard IDs.

Checked on 15 Nov 2026 against main `ae4c03dbe69b9a46bfdd8a0922cf5d48118ab51f`.

## Scope and limits

| Item | State |
|---|---|
| Shard checked | `teams/01-data-a/shards/sample/code-go-train-000000`, `dataset_version: "sample"`. It was written to test the shard code (PR #358, #373), not from the first training data |
| `.bin` and `.docs.parquet` | Not in git (pr-guard refuses them). Their hashes, the header, the token IDs and the EOS positions were **not** checked from bytes |
| Second shard | None on main or in a PR. Already filed as issue #448, so no new issue |
| Earlier check of the same shard | #449 (shivman), merged. This check repeats it independently with its own script and adds the checks listed under "Added here" |

## How it was checked

[`check_shard.py`](check_shard.py), in this folder, reads the manifest and every file the manifest names, and reports each check as PASS, FAIL or NOT CHECKED. A file that is not present is NOT CHECKED, never PASS. It prints IDs, counts and hashes only, never document text. The same script will run on the real shards, where it also checks the `.bin` (size, header, every id below the vocab, an EOS at the end of every document and no special id inside one) and the `.docs.parquet` (rows, unique doc_ids, `n_tokens` equal to the index). It does not decode text: G9's `teams/09-evaluation/decontam/decode_shard.py` does that, and needs the `.bin`. Tests: `tests/audit/test_check_shard.py`, 14 cases on a made-up shard (a good shard, missing files, a changed byte, a wrong count, a missing EOS, a special id inside a document, an id at the vocab size, bad manifest values including a short or placeholder `created_by`, a missing field).

Rerun, from the repository root (Python 3.12, numpy 2.5.4, pyarrow 26.0.1):

```
python -I teams/01-data-a/audit/check_shard.py teams/01-data-a/shards/sample code-go-train-000000
python -m pytest teams/01-data-a/tests/audit -q
```

Last lines of output: `{'PASS': 30, 'FAIL': 1, 'NOT CHECKED': 4}` (exit code 1, from the expected `dedup` FAIL) and `14 passed`.

## Results: `code-go-train-000000`

30 PASS, 1 FAIL (expected for a sample, see note 1), 4 NOT CHECKED (the files are not in git).

### Manifest fields

| Check | Expected | Observed | Result |
|---|---|---|---|
| Fields against `shard_manifest_v1.template.json` | all 28, no others | all 28, no others | PASS |
| No empty or `<placeholder>` values | none | none | PASS |
| `schema_version` / `format` / `token_dtype` | `shard-v1` / `brahmic_u32_v2+doc_index` / `uint32` | same | PASS |
| `eos_token_id` | 130822 | 130822 | PASS |
| `tokenizer_sha256` | frozen C3 `15468e66457b43af…` | same | PASS |
| `decontam_set_sha256` | F2 v2 `2826a3b883210c65…` | same | PASS |
| `split` | `train` or `validation` | `train` | PASS |
| `shard_id` | `<pack_id>-<split>-<6 digits>` | `code-go-train-000000` | PASS |
| `payload_bytes` = 1,024 + 4 × `token_count` | 1,049,152 | 1,049,152 | PASS |
| `created_by` is a full git commit hash | 40 hex characters | `5255556c7fc4…` (traced in note 2) | PASS |

### Hashes (recomputed from the files in git)

| File | Manifest sha256 | Recomputed | Result |
|---|---|---|---|
| `code-go-train-000000.json` (manifest) | `0b062310577feec1…` in `sample/README.md` | `0b062310577feec1d38ff7aa538f7b880bd85226d826040c4646811e62959f87` | PASS |
| `code-go-train-000000.idx.npy` | `d808fcda4116f03d…` | `d808fcda4116f03d…` | PASS |
| `code-go-train-000000.quality_report.json` | `5ecae0dbc4f3c9c8…` | `5ecae0dbc4f3c9c8…` | PASS |
| `cleaning_pipeline.json` | `35611a83cfa6d6b5…` | `35611a83cfa6d6b5…` | PASS |
| `code-go-train-000000.dump.md` | `bfd2e8bea7d866e2…` in `sample/README.md` | `bfd2e8bea7d866e2…` | PASS |
| `code-go-train-000000.bin` | `a9f5e861508679e7…` | file not in git | NOT CHECKED |
| `code-go-train-000000.docs.parquet` | `215004216f384089…` | file not in git | NOT CHECKED |

### Token counts (from the index)

| Check | Expected | Observed | Result |
|---|---|---|---|
| Index dtype | int64 | int64 | PASS |
| Index length = `doc_count` + 1 | 272 | 272 | PASS |
| Index starts at 0, ends at `token_count` | 0 … 262,032 | 0 … 262,032 | PASS |
| Document lengths sum to `token_count` | 262,032 | 262,032 | PASS |
| Every document has at least 2 tokens (text + EOS) | ≥ 2 | shortest 41 | PASS |
| Shard within 2^26 tokens | ≤ 67,108,864 | 262,032 | PASS |

### Quality report and cleaning pipeline

| Check | Expected | Observed | Result |
|---|---|---|---|
| Quality report `shard_id`, `docs_in_shard` = `doc_count` | `code-go-train-000000`, 271 | same | PASS |
| `rows_read` = docs in shard + left out | 271 | 271 | PASS |
| `left_out` counts = length of each `left_out_docs` list | all 0 | all 0 | PASS |
| `cleaning_pipeline.json` F2 set = manifest `decontam_set_sha256` | `2826a3b8…` | `2826a3b8…` | PASS |
| `clean_py_sha256` = `spec_v1/clean.py` on main | `22d818c72c9f30bf…` | `22d818c72c9f30bf…` | PASS |
| `cleaning_pipeline.json` records a dedup version | a version | `null` | FAIL, expected for this sample (note 1) |

### Added here (not in #449)

- The manifest has no fields outside the template and no `<placeholder>` values.
- The quality report is consistent with itself: `rows_read`, `left_out` and the `left_out_docs` lists agree.
- The `clean.py` named in `cleaning_pipeline.json` is the `clean.py` on main today (`22d818c7…`), so the cleaning step of this sample can be re-run from main.
- The writer commit in `created_by` was traced (note 2).

## Notes

1. **`dedup: null`.** The sample was written before a dedup version existed (`dedup.py` is still in #255). This is expected for the sample and is not filed as an issue. For the real shards it must name the dedup version; a real shard with `dedup: null` will be filed.
2. **`created_by` = `5255556c7fc4e824efc0680c994da34c1c6f2125`.** This commit is not on main's history: #373 was squash-merged, so `git cat-file` on a clone of main does not find it. GitHub still serves it (dated 12 Nov 2026), and its `shard_writer.py` is byte-identical to main's (sha256 `ed634d19d332350f…`). Nothing is wrong with this shard. For the real shards, `created_by` should be a commit that main can reach, or the manifest could also record the sha256 of `shard_writer.py`. To raise with the shard owner before filing.

## Not done yet (to finish R1)

- [ ] **Rebuild the sample's `.bin` and `.docs.parquet`** with the commands in `shards/sample/README.md` and compare them with `a9f5e861…` and `215004216f…`. The C3 tokenizer (sha256 `15468e66…`), the pinned `clean.py` and the F2 v2 set are at hand. Waiting on the input part `code-go/Part_2/part-00001.parquet` from the week-2 tokenizer sample (sha256 `40aedd68…`).
- [ ] **Two real shards** from the first training data, assigned by Tejaskumar (R1.1): rerun every check above on the actual `.bin`, `.idx.npy` and `.docs.parquet`, and decode them with G9's `teams/09-evaluation/decontam/decode_shard.py`.
- [ ] **R2:** file each real problem as an issue and link it here. So far: none new (#448 already covers the missing second shard).
