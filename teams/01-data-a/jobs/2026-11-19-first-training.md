# First training pipeline: inventory through reconciled train shards

```text
Team:            01-data-a
Owner:           patilvijay23
Lead approval:   patilvijay23 (pending review of this request)
Question:        Do the approved raw parts produce an exact inventory, auditable cleaned Parquets, and reconciled p1536 train shards in one pipeline run?
Script:          teams/01-data-a/jobs/2026-11-19-first-training/build_inventory.py, prepare_run.py, then teams/01-data-a/pipeline/run_pipeline.py
Command:         python -I teams/01-data-a/pipeline/run_pipeline.py --config out/first-training-inputs/run.json
Config:          out/first-training-inputs/run.json (materialized from the template below after inventory build)
Inputs:          TSAI-staged approved train and heldout parts for the 38 packs in approved_inputs.json; frozen p1536 tokenizer; offline LaBSE model; approved pack table; G9 F2 v2 fingerprints
Hardware:        1 GPU for H3; CPU workers for the remaining stages
Max time:        720 minutes for the combined job (H3's own limit is 180 minutes)
Precision:       H3 auto (bf16 on supported CUDA); shard token IDs are integers
Measures:        Raw/cleaned/dedup/F2/final counts, H3 matches, train shards and tokens, heldout not_sharded, per-part reconciliation and SHA-256 checks
Expected result: Every listed raw part reaches the ledger; each train part is written or has a justified empty/all_left_out status; heldout parts are not sharded; all checks pass; H3 removes zero documents
Outputs:         out/first-training-inputs/{input_manifest.json,expected_inventory.json,run.json}; out/pipeline/<run_id>/{clean,overlap,h3,dedup,deduped,final,report,ledger,shards,reconcile}/ and pipeline_manifest.json
Test log:        teams/01-data-a/jobs/logs/2026-11-19-first-training-rehearsal-38packs/ (all 86 parts of sample v0, 38 packs, frozen p1536, Linux + pinned env: 59/59 checks; with the inventory, prepare_run's run.json at 2691c44: 74/74); teams/01-data-a/jobs/logs/2026-11-19-first-training-local-5packs/ (5 packs, 118/118)
```

## Scope and prerequisites

This is an integration request. TSAI stages the approved raw inputs and applies the approved spec v1.1 cleaning rules as part of the agreed pipeline execution. Confirm that this combined run is acceptable under `JOB_REQUEST.md` rule 6, which reserves full-data cleaning for TSAI. The source-scope assumption is recorded in `2026-11-19-first-training/approved_inputs.json`: the 38 sample-v0 pack IDs are the complete admissible source set; production may have more parts per pack, with the same split/pack layout. Verify the fetched source revisions and subset restrictions against TSAI's source catalog before starting.

The job must be staged with these inputs before `--plan` or execution:

- All approved raw parts, at least one in each split for every pack, under `<raw>/train/<pack>/part-<number>.parquet` and `<raw>/heldout/<pack>/part-<number>.parquet`.
- The frozen p1536 `tokenizer.json` (SHA-256 `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`).
- An offline LaBSE model at the `model_path` in `2026-11-19-first-training/h3.json`, with `dedup/requirements_h3.txt` installed. H3 measures `ind-sa-fw2`, `ind-hi-fw2` and `en-fineweb-edu` in report-only mode.
- A job pack table with a non-null `language`, `script`, `domain`, `lane`, `license` and `license_source` for every approved pack. The generic `shards/pack_table.json` has null lanes and no licences and cannot serve as the production table.
- The pinned G9 F2 v2 fingerprint set and the packages in `2026-11-19-first-training/requirements_pipeline.txt` in one Python 3.12 environment. No network access or keys at runtime.

## Run from the repository root

1. Stage and verify the entire selected raw file set. Generate the manifest and expected inventory **before** cleaning. Use a new output folder:

   ```bash
   python -I teams/01-data-a/jobs/2026-11-19-first-training/build_inventory.py --input-root <raw-root> --out out/first-training-inputs
   ```

2. Generate `out/first-training-inputs/run.json` from the frozen inventory. The command checks the p1536 tokenizer SHA256, exact pack set, licences and all six required pack-table fields before writing the run config. It pins `dataset_version` to `first-training-v1` and keeps cleaned, deduped and F2 Parquets for audit.

   ```bash
   python -I teams/01-data-a/jobs/2026-11-19-first-training/prepare_run.py --bundle out/first-training-inputs --input-root <raw-root> --tokenizer <p1536-tokenizer.json> --pack-table <approved-job-pack-table.json> --run-id first-training-v1
   ```

   The generated file has this structure; its input counts and SHA256 come from the inventory rather than manual transcription:

   ```json
   {
     "run_id": "first-training-v1",
     "out": "out/pipeline",
     "inventory": "out/first-training-inputs/expected_inventory.json",
     "intermediates": "keep",
     "stages": {
       "clean": {
         "mode": "run",
         "settings": "teams/01-data-a/pipeline/clean.json",
         "input": "<raw-root>",
         "manifest": "out/first-training-inputs/input_manifest.json",
         "manifest_sha256": "<generated input_manifest_sha256>",
         "expected_parts": {"train": "<generated count>", "heldout": "<generated count>"}
       },
       "overlap": {"mode": "run", "settings": "teams/01-data-a/dedup/overlap.json"},
       "h3": {"mode": "run", "settings": "teams/01-data-a/jobs/2026-11-19-first-training/h3.json"},
       "dedup": {"mode": "run", "settings": "teams/01-data-a/dedup/dedup.json"},
       "f2": {"pool": true, "workers": 1},
       "ledger": {"raw": "<raw-root>"},
       "shards": {
         "tokenizer": "<p1536-tokenizer.json>",
         "dataset_version": "first-training-v1",
         "pack_table": "<approved-job-pack-table.json>"
       },
       "reconcile": {}
     }
   }
   ```

   The builder requires all 38 packs in both splits and rejects unknown packs, invalid part names, missing columns, changed files and duplicate numeric part indices. The generator refuses an incomplete pack table or an unfrozen tokenizer.

3. Check the generated config, then run the same file. Both commands use the same checkout and working directory:

   ```bash
   python -I teams/01-data-a/pipeline/run_pipeline.py --config out/first-training-inputs/run.json --plan
   python -I teams/01-data-a/pipeline/run_pipeline.py --config out/first-training-inputs/run.json
   ```

The runner runs clean → overlap → H3 → dedup → apply → F2 → survivor loss → raw ledger → shards → reconcile. It verifies each handoff and the inventory at the ledger/shard and reconciliation checkpoints. H3 feeds its matches to dedup with `remove: false`.

## Folder layout and audit artifacts

For `run_id = first-training-v1`, the raw layout is preserved through cleaning, dedup application and F2:

```text
<raw-root>/
  train/<pack>/part-00000.parquet
  heldout/<pack>/part-00000.parquet

out/first-training-inputs/
  input_manifest.json
  expected_inventory.json
  run.json

out/pipeline/first-training-v1/
  clean/
    train/<pack>/part-00000.parquet
    heldout/<pack>/part-00000.parquet
    reports/train/<pack>/part-00000.parquet.json
    reports/heldout/<pack>/part-00000.parquet.json
    job_summary.json
    cleaned_manifest.json
  overlap/
  h3/
  dedup/
  deduped/train/<pack>/part-00000.parquet
  deduped/heldout/<pack>/part-00000.parquet
  final/train/<pack>/part-00000.parquet
  final/heldout/<pack>/part-00000.parquet
  report/
  ledger/
  shards/
    <pack>-train-000000.bin
    <pack>-train-000000.idx.npy
    <pack>-train-000000.docs.parquet
    <pack>-train-000000.json
    <pack>-train-000000.quality_report.json
    <pack>-train-000000.dump.md
    shards_summary.json
  reconcile/
  pipeline_manifest.json
  inventory_check.json
```

Shard files are **flat under `shards/`**, not nested by split or pack. Numbering runs across a pack's train parts and may roll over to several shards for one part. Heldout parts remain as Parquet in `clean/`, `deduped/` and `final/`; `shards_summary.json` records them as `not_sharded`. A train part with no tokens can be `empty` or `all_left_out`; the inventory permits these explicit statuses and reconciliation checks their document accounting. `intermediates: keep` retains the clean output in all cases.

## Return and acceptance

Return the console log, `pipeline_manifest.json`, `inventory_check.json`, clean `job_summary.json` and `cleaned_manifest.json`, H3 summary and match counts, `shards_summary.json`, and `reconcile_summary.json` under `teams/01-data-a/jobs/results/2026-11-19-first-training/`. Keep Parquet, token binaries and document text in TSAI's job storage; report their paths and hashes without committing their content.

Acceptance requires exit code 0, inventory report `ok: true`, no missing or unlisted input part, zero heldout shards, H3 `removed: 0`, shard files verified on disk, and reconciliation of every kept train document. Include the runtime, peak memory, H3 model hash and package versions, shard/token counts, and any empty or all-left-out train parts in the returned log.
