# Data A pipeline: open items for the team

Branch `g1-pipeline-runthrough`, folder `teams/01-data-a`. Last updated 2026-11-14 (PR review comments added as section 3). Not committed (kept outside the repo).
The full chronological log is in `open-items-data-a-pipeline.full-log-2026-11-14.md` (same folder).

`[x]` done, `[ ]` open. Tests: 194 pass (119 pipeline + 75 shards), all with stand-in scripts except the one real-script run noted below.

## 1. Where we are

One run config (`pipeline.json`, copied and edited per run) drives seven stages: clean, overlap, dedup, apply, F2, survivor loss, shards (optional). The CLI is `run_pipeline.py --config <file>` (+ `--plan`). Everything a run needs (run_id, `from`/`to`, `stages.clean.only`, adopted folders) is a key in that file, which is also what a TSAI job's single `Command:` line needs.

- [x] Shard stage inside the runner; held-out folders are `not_sharded`, not failures.
- [x] `cleaning_pipeline.json` records the processing (clean.py sha256, F2 set, dedup remove list, overlap files and k/floor, dedup settings, code hashes); the shard writer re-derives it and refuses a mismatch.
- [x] Folders are decided once (`<out>/<run_id>/<stage>`); the runner generates each stage's config in `<run>/cfg/`; settings files stay unedited and are pinned by sha256.
- [x] First end-to-end run with the **real** scripts (clean, overlap, dedup, F2, shards) on a synthetic 86-part sample: all checks pass, planted duplicates and a canary came out right, `workers` 2 and 4 give the same digests.
- [x] `local_trial/`: configs, README with full commands, `show.py`, so anyone can run the whole pipeline on six small files before a job request.
- [ ] The local trial on the **real** week-2 parts has not been run yet (needs torch and a `tokenizer.json`).

## 2. Decisions needed from the team

| # | Question | Who | Recommendation |
|---|---|---|---|
| 1 | **Capability lanes** for the 32 non-code packs. `pack_table.json` has `lane: null` for them, so the runner refuses them (only `code`, `general_language`, `test` exist). | training-plan owner, G7 | Define the allowed values in `shard_format_v1.md`, validate them in `pack_table.py`; until then run shards with `packs`. |
| 2 | **Held-out parts**: shard as `validation`, or not at all? Format has `train`/`validation` only; writer refuses held-out. Today `NOT_SHARDED` (`heldout`, `validation`, `val`) is a tuple in `run_shards.py`. | G3, G9 | Not sharded for sample v0; revisit before the full run (one constant + the writer check). The PR review expects `not_sharded` too (comment 11): confirm it there. |
| 3 | **Several shards per part / truncation.** The writer fills one shard up to `--tokens` (2^26) and drops the rest; the part is flagged `truncated` but the stage still passes. Largest sample-v0 part is about 45-60M tokens (estimate; not checked with C3). | shard owner, G6, G7 | **Decided by the PR review (comments 1, 8):** continue into more shards until every selected row is processed; `truncated > 0` must not count as success. Until that exists, fail the stage on truncation. |
| 4 | **Domain label `code-adjacent`** for the three `cadj-*` packs (taken from the week-2 README). | G7 | Confirm the name or give the enum. |
| 5 | **7 packs without cleaning rules** (not in `clean._FAMILY`): `cadj-commits`, `cadj-notebooks`, `cadj-stackexchange`, `ind-ml-fw2`, `ind-or-fw2`, `ind-ta-fw2`, `ind-ta-sangraha-s`. They pass through with only the shared F1 rule (`unsupported_passthrough`, 14 parts in the review run). | owner of clean.py | Release with F1 only, or add rules first. |
| 6 | **One Python version for all stages.** `run_tokenizer_sample.py` needs 3.11+; `requirements.txt` says 3.11+ (`hashlib.file_digest`); the README still says "Python 3.9+". Stages run under the runner's interpreter, so the shard stage also needs torch/tokenizers there. | whole team | Pin 3.11+; fix README and `requirements.txt` together. |
| 7 | **TSAI packaging.** A run folder is far above the 50 MB output limit; rule 6 forbids full-data cleaning requests. | TSAI | Package only the metadata (manifest, `cleaning_pipeline.json`, `cfg/`, logs, summaries) into `jobs/results/<date>-<name>/`. A full audit run on new data needs TSAI's explicit agreement. |
| 8 | **PR order.** The default `pipeline.json` points at `teams/01-data-a/dedup/*.json`, which is not on origin/main (dedup, PR #255). A fresh checkout cannot even `--plan` the default config until it merges. `run_f2.py` is on this branch but not on origin/main yet. | team | Merge #255 first, or ship with adopt entries. |

## 3. Open PR review comments (received 2026-11-14)

Target stated by the reviewer: **final Parquet (clean + dedup + decontam) -> direct tokenization -> complete, verified storage shards.** No intermediate tokenized Parquet. 4k/8k/16k sequence packing stays outside this PR and the PR to be raised from the base branch.

**Shard completeness (comments 1-6), all open.** Today: the writer fills one shard up to `--tokens` and stops at the first document over the budget; the runner's shard check looks at failed/skipped counts, exit code, at least one written and "summary is this run's", and trusts `shards_summary.json`; a rerun into an `out` with shards stops; there is no real-writer multi-shard test.

| # | Comment | Status | What it means for the code |
|---|---|---|---|
| 1 | Prevent data loss at the token limit: continue into additional shards until every selected row is processed; `truncated > 0` is not success. | [x] done (rollover) | The writer rolls over to the next shard; shard numbers run on across a pack's parts; `shards_summary.json` maps each part to its shards; a doc longer than a shard is left out as `oversize`. Real-writer forced-rollover tests in `test_shard_writer.py` and `test_run_shards.py`. |
| 2 | Verify the actual shard artifacts before recording success: payload, index and metadata exist; hashes, format, document and token counts match. Not just `shards_summary.json`. | [ ] open | New check in the shard stage that reopens every shard it lists. |
| 3 | Verify complete input coverage from the verified final-Parquet inventory: detect missing, nested or unexpected parts. Allocate shard IDs independently of part basenames. Preflight required pack metadata (lane, domain) before writing. | [ ] open | Inventory vs parts on disk; unique shard-ID allocation; the lane check moves before any write (ties to decision 1). |
| 4 | Empty parts (emptied by F2, or fully excluded during tokenization) get explicit outcomes and reconciled counts, not a pack-ID mismatch or "no document fits". | [ ] open | New per-part outcome (for example `empty`) in the summary and the reconciliation. |
| 5 | Safe resume: write temporary artifacts, publish completion last; on rerun verify and reuse completed shards, continue unfinished work, never overwrite incompatible output. | [ ] open | Replaces today's "stops if a shard exists"; covers the existing rerun and `--skip-existing` items for the shard owner. |
| 6 | Regression tests for these cases, including real-writer multi-shard rollover and interruption/restart. | [ ] open | Needs tests that run the real `shard_writer`, not stand-ins. |

**Other comments**

| # | Comment | Status | Notes |
|---|---|---|---|
| 7 | Windows: `stage_args.py` put `str(config)` in the command (backslashes), so `test_overlap_config_gets_the_paths_and_keeps_every_setting` failed on Windows; use `config.as_posix()`. | [x] done in the working tree | `stage_args.py:130` now uses `config.as_posix()`. Not run on Windows. Check that the line is in the commit that is pushed. |
| 8 | Shards stage must also fail on `counts["truncated"] > 0` (today only `failed` and `skipped`). | [ ] open | Runner-level half of comment 1; a small change that can go first. |
| 9 | `assets/flow.svg` and `hero.svg` are built files (subset fonts, overwritten by the next build); send the wording and the reviewer rebuilds from the sources. | [ ] open, wording below | My redraw edited the built SVGs directly, so it will be lost on the next build. |
| 10 | numpy is needed by the shard writer; the README "Needs" line must say so (`python -I` ignores user installs); add it to `requirements.txt`. | [ ] open | `requirements.txt` lists numpy only under overlap, not under shards. README "Needs" still reads "Python 3.9+ with `pyarrow`" (update together with decision 6). |
| 11 | Held-out = `not_sharded`: confirm it and say it in the README (the reconciliation will expect it). | [ ] open | Confirm in the PR reply. `pipeline/README.md` does not mention `not_sharded` (grep finds nothing); `shard_format_v1.md` does. Add to the README Shards section. |

**Wording for comment 9** (new or changed text compared with the six-stage versions):
- hero: subtitle ends "... apply, f2, survivor loss, and optionally shards." and a new stage label `shards`.
- flow: new stage number `07`, tags `OPTIONAL` and `new · optional`, labels `shards`, `run_shards.py`, `→ .bin, manifest`, `final → shards` (was `final parquet`); `run_clean.py` (was `spec_v1/run_clean.py`); `→ final/, f2.json` (was `→ final/, *.f2.json`).
- flow description: "Seven stages. Clean, overlap and dedup are TSAI jobs that the runner adopts or runs; apply, f2 and survivor loss are always run by run_pipeline.py; shards is optional. Duplicates leave at apply, benchmark copies at f2, the rest is the final Parquet, which shards turns into token shards."
- hero description: "Clean, deduplicate and decontaminate the sample in one checked run: clean, overlap, dedup, apply, f2, survivor loss, and optionally shards."
- The upstream ledger stage is already in the committed SVGs; confirm the sources have it too.

## 4. Open items by owner

### Dedup teammate
- [ ] `overlap_summary.json` and `dedup_summary.json` record neither the script sha256 nor the git commit, so `code_sha256` in `cleaning_pipeline.json` stays null while those stages are adopted. Ask both scripts to write `code_sha256` and the commit, or let the runner run them (`mode: run`).
- [ ] Do `overlap_summary.versions` or `block` change what counts as a duplicate? (left out of the record; assumed no). Is `gold_dirs` only the harm check?
- [ ] Are `inputs` / `out` / `results` safe to override per run (the runner generates them)? Where will the settings files live after the merge? When the scripts take `--input`/`--out` flags, the runner's `generated_config()` can go.
- [ ] Dedup job after job 244: write `jobs/<date>-dedup/run.json` (adopt clean = job 244's folder on TSAI's machine, `to: dedup`) + the request md (`Command: python teams/01-data-a/pipeline/run_pipeline.py --config <run.json>`). The runner must be merged or in that PR. Test log = `--plan` plus a small trial with `stages.clean.only`.
- [ ] Delete the untracked placeholders in `teams/01-data-a/dedup/` once dedup merges.

### Owner of clean.py (and TSAI staging)
- [ ] The rebuilt clean.py changes the `clean_sha256` pin in `spec_v1/clean.json`; the `--input-root` rename is on hold.
- [ ] TSAI's staging of `inputs/tokenizer_sample_v0/` must include `sample_manifest.json`; otherwise set `stages.clean.manifest` to the tracked copy in `jobs/2026-11-02-…` in that job's run config. That copy (sha256 `7fd647c8…`, pinned by both submitted job configs) is the same file as `week-2/sample_manifest.json`.
- [ ] The clean script's `--out` help text says `./out/<job>/`; the code allows any named subfolder of `./out`.
- [ ] `jobs/README.md` still documents the script's own `--input-root/--out/--only` for direct smoke runs (valid when the script runs alone; the runner no longer passes them).

### F2 owner
- [ ] `run_f2.py` writes with the default codec: final parts are about 30% bigger than deduped (ZSTD, 122 row groups, to SNAPPY, 16 row groups); apply preserves them. Matters for disk on the full sample.
- [ ] F2 starts one process per pack and split, each loading the 1.1 GB fingerprint set (about 20 s): 76 loads. Per-part units would balance better but need a per-unit summary name (two parts of one pack would write the same `f2_summary.json`).

### Shard owner
- [ ] (PR comment 5) Rerun into an `out` that already has shards stops (run_shards refuses); the stop message says "exited 0: exit code 1" and hides the reason. Add the log tail to the check detail; consider a `--skip-existing`-style option.
- [ ] PR comments 1-6 and 8 (section 3): multi-shard rollover, artifact checks, input coverage, empty parts, safe resume, tests.
- [ ] Pipeline exits 1 when a pack is skipped (null lane); restrict with `packs` until decision 1.
- [ ] The committed `shards/sample/` predates pipeline-driven sharding (old `cleaning_pipeline.json` with `"dedup": null`); regenerate from a pipeline run for the release.
- [ ] `shards_summary.json` records `run_id` and `cleaning_pipeline_sha256`, but not the tokenizer or `--tokens`; add if wanted.
- [ ] The shard stage digest rehashes every file in `shards/` including the .bin files (slow on a full run; the writer already records payload sha256).
- [ ] No C3 `tokenizer.json` on this machine; smoke runs use G6's baseline with `--any-tokenizer` (shards marked `test`).
- [ ] Output layout stays flat (`<out>/<shard_id>.*`); change together with the release layout (`<pack>/<split>/...`). G7 questions in `shard_format_v1.md` (where shards live, shard size, loader contract) are not ours to close.

### Ledger teammate
- [ ] Tell them what changed in `pipeline_manifest.json` (additive): a `shards` stage entry (counts, `cleaning_pipeline_sha256`), `totals.shards_written`, every stage's `output` now resolved, new `settings*`/`config*` keys on clean/overlap/dedup, the manifest embeds the run config. New files: `<run>/cleaning_pipeline.json`, `<run>/shards/shards_summary.json`, `<run>/cfg/`. The ledger still reads `pipeline_manifest.json` and `.f2.json`.

### Me (pipeline)
- [ ] Run the local trial on the real week-2 parts and report failures (debug from `out/pipeline/<run_id>/logs/`).
- [ ] Digest claim is not true for clean, overlap, dedup, shards: identical runs differ in `wall_seconds`, `peak_rss`, `config`/`config_sha256` (run folder names), `run_id`. Add them to VOLATILE or narrow the README/docstring claim. Nothing breaks (`from` compares a folder with itself).
- [ ] The manifest embeds the config, including an absolute `stages.shards.tokenizer` path if given that way; use a repo-relative path before a manifest goes into `jobs/results/`.
- [ ] The recorded `command` of a settings stage holds the absolute path of the generated config (differs per machine).
- [ ] The runner does not pre-clean a run-mode folder: clean refuses an existing one, so a rerun of a run stage needs a new `run_id` or the folder removed.
- [ ] Package step for `jobs/results/` (decision 7).
- [ ] `assets/guards.svg` still shows the old guard list (no config/shards guards).
- [ ] README: "Python 3.9+" and "57 tests" are stale; sections Troubleshooting, Design decisions and "Measured on real data" not re-read after the changes.
- [ ] The CHECKS section of the `run_pipeline.py` docstring does not list the shards checks.
- [ ] Local trial limits: the shards stage needs torch and a `tokenizer.json` (baseline fetched once over the network); `--plan` checks that file even for a plan; overlap needs Linux/macOS, so no Windows run of the whole trial.
- [ ] Delete the stale helpers `out/e2e/` and `teams/01-data-a/pipeline/local_trial/e2e/` (superseded by `local_trial/`).
- [ ] `.gitignore` at the repo root has only `__pycache__/`: `inputs/` and `out/` are not ignored (the pipeline README says `out/` is git-ignored). `pipeline/requirements.txt` is untracked.
- [ ] Do not `git add -A` at the repo root (`out/` is untracked).

## 5. Decided (for reference)

- Run config: one hand-edited file per run, all parameters inside; CLI only `--config` and `--plan` (no second way to pass a parameter). Run-mode stages take `settings` (+ `input` for clean); `command` + `output` stay as an escape hatch; `adopt` needs `output` and works for clean/overlap/dedup only.
- Input-set keys (`manifest_sha256`, `expected_parts`, `sample`, optional `manifest`) live in `stages.clean` next to `input`; `spec_v1/clean.json` holds only clean.py's settings. A run checks the manifest file against its pin just before the clean job starts.
- `cleaning_pipeline.json` does not embed the pipeline manifest (avoids a hash cycle with the shard manifests); the shard writer reads `pipeline_manifest.json` itself. "Another run" refusal means different processing, so identical reruns may share an `out`.
- Shard step is a normal stage (manifest entry, manifest rewritten after it, `from`/`to`).
- `pack_table.json` stays in `shards/`.
- Scope of the shard work (PR review): final Parquet is tokenized directly into verified shards; no intermediate tokenized Parquet; sequence packing (4k/8k/16k) is outside this PR.
- The sample manifest describes the input data set, so it is not copied per job.

## 6. Stage map (what each stage reads and writes)

`<run>` = `<out>/<run_id>/` (default `out/pipeline/<run_id>/`). `<clean>`, `<overlap>`, `<dedup>` = `<run>/clean`, `<run>/overlap`, `<run>/dedup` unless a stage is adopted (`output` = existing folder). `<split>` = `train` or `heldout`; parts are `<pack>/part-NNNNN.parquet`.
"Used by" lists who reads that output afterwards: a later stage, the runner's checks (R), or the provenance/shard side (P).

| # | Stage and script | Input | Input comes from | Output | Output is used by |
|---|---|---|---|---|---|
| 00 | **TSAI data download**<br>done by TSAI, not by the pipeline | TSAI's public source data (the same sources as the week-1 sample) | TSAI | `<week-2>/<split>/<pack>/part-NNNNN.parquet` (raw: `doc_id, text, url, lang_label, pack_id, source`)<br>`<week-2>/sample_manifest.json` (path, rows, bytes and sha256 of every part, mix, sampling seed)<br>`SHA256SUMS`, `README.md` | clean (the parts, found and checked through the manifest)<br>anyone verifying a download |
| 01 | **clean**<br>`spec_v1/run_tokenizer_sample.py` (TSAI job) | `<week-2>/<split>/<pack>/part-NNNNN.parquet`<br>`<run>/cfg/clean.json` = `spec_v1/clean.json` (`clean_sha256`, `batch_size`, `optional_f2`, `unsupported_policy`) + the run config's `stages.clean` (`input`, `manifest_sha256`, `expected_parts`, `sample`, `only`)<br>the sample manifest (default `<input>/sample_manifest.json`) | 00 TSAI data download<br>settings file + run config | `<clean>/<split>/<pack>/part-NNNNN.parquet` (cleaned parts)<br>`<clean>/job_summary.json` (raw and cleaned part sha256, `clean_sha256`)<br>`cleaned_manifest.json`, `rule_counts.csv`, `reports/<split>/<pack>/<part>.json` | overlap, dedup (optional: `url`), apply (the parts)<br>R: row counts per part<br>P: `job_summary.json` |
| 02 | **overlap**<br>`dedup/overlap.py` (TSAI job) | `<clean>/<split>/<pack>/part-*.parquet` (pack from the `pack_id` column)<br>`<run>/cfg/overlap.json` = `dedup/overlap.json` (`k`, `floor`, `splits`, `expected_packs`) + `inputs`, `out` | 01 clean<br>settings file + runner | `<overlap>/overlap_summary.json`, `overlap_matches.csv`, `overlap_docs.parquet` (the three dedup needs)<br>also `overlap_pairs.csv`, `overlap_by_pack.csv`, `overlap_histogram.csv`, `overlap_matrix*.csv/.npz` | dedup (the three files, sha256-checked)<br>R: `documents_all`, parts and row counts<br>P: `overlap_summary.json` config (`k`, `floor`) |
| 03 | **dedup**<br>`dedup/dedup.py` (TSAI job) | `<overlap>/overlap_summary.json`, `overlap_matches.csv`, `overlap_docs.parquet`<br>`<clean>/...` (optional)<br>`<run>/cfg/dedup.json` = `dedup/dedup.json` (`pack_order`, `licence_usable`, `default_licence_usable`, `cross_pack`) + `results`, `inputs`, `out` | 02 overlap<br>01 clean<br>settings file + runner | `<dedup>/remove_list.csv`, `dedup_groups.csv`, `dedup_summary.json`<br>also `dedup_log.jsonl`, `heldout_duplicates.csv`, `empty_documents.csv` | apply (`remove_list.csv`)<br>survivor loss (`dedup_groups.csv`)<br>R: summary (status, counts, overlap hashes, held-out removed = 0)<br>P: remove list sha256 and rows, `dedup_groups.csv`, summary config, `overlap_run.checked_sha256` |
| 04 | **apply**<br>`pipeline/apply_dedup.py` (always run by the runner) | `<clean>/<split>/<pack>/part-*.parquet`<br>`<dedup>/remove_list.csv` | 01 clean<br>03 dedup | `<run>/deduped/<split>/<pack>/part-NNNNN.parquet` (untouched parts hard-linked)<br>`<run>/deduped/apply_dedup_summary.json` (per part: rows, removed, kept, input/output sha256) | F2 (parts)<br>R: counts<br>P: the summary (links clean's output to F2's input) |
| 05 | **F2**<br>`spec_v1/run_f2.py` + fingerprint set v2 (`teams/09-evaluation/fingerprints/v2`) | `<run>/deduped/<split>/<pack>/part-*.parquet` | 04 apply | `<run>/final/<split>/<pack>/part-NNNNN.parquet` (the pipeline's data output)<br>`part-NNNNN.parquet.f2.json` per part (input/output sha256, `set_sha256`, dropped doc_ids)<br>`f2_summary.json` per pack folder (with workers = 1: per split) | survivor loss (`.f2.json`)<br>shards (final parts)<br>R: summaries<br>P: each part's `.f2.json` |
| 06 | **survivor loss**<br>`pipeline/survivor_loss.py` (always run by the runner) | `<dedup>/dedup_groups.csv`<br>`<run>/final/**/*.f2.json` | 03 dedup<br>05 F2 | `<run>/report/survivor_loss.csv`, `survivor_loss_summary.json` | a report; R: group count = groups in `dedup_groups.csv` |
| 07a | **shards, step 1: processing record**<br>`shards/provenance.py` `write_record` (called by the runner) | `<run>/pipeline_manifest.json`<br>`<clean>/job_summary.json`, `<run>/deduped/apply_dedup_summary.json`<br>`<dedup>/remove_list.csv`, `dedup_summary.json`<br>`<overlap>/overlap_summary.json` | runner<br>01-04 | `<run>/cleaning_pipeline.json` | shard_writer (checks it against the manifest, copies it into `--out`)<br>run_shards (sha256 into the summary) |
| 07 | **shards, step 2: the shards**<br>`shards/run_shards.py` calls `shard_writer.py` once per part<br>+ C3 `tokenizer.json`, `shards/pack_table.json` (optional stage: `stages.shards`) | `<run>/final/<split>/<pack>/part-NNNNN.parquet` (`train` only; `heldout`, `validation`, `val` are `not_sharded`)<br>`<run>/pipeline_manifest.json`, `<run>/cleaning_pipeline.json` | 05 F2<br>runner<br>07a | `<out>/<pack>-<split>-NNNNNN.bin`, `.idx.npy`, `.docs.parquet`, `.json` (shard manifest), `.quality_report.json`, `.dump.md`<br>`<out>/cleaning_pipeline.json` (copy), `<out>/shards_summary.json`<br>(`<out>` defaults to `<run>/shards`) | runner (summary checks, stage record)<br>training loader (shard manifests, pinned by hash)<br>the ledger |
| - | **runner**<br>`pipeline/run_pipeline.py` | every stage's output folder (digests, counts, checks) | all stages | `<run>/pipeline_manifest.json` (rewritten after every stage)<br>`<run>/cfg/`, `<run>/logs/<stage>.log` | `from` (stage digests)<br>provenance and shard_writer<br>the ledger |

Review-run totals (13 Nov smoke on real data): 16,479 cleaned, 16 removed by dedup, 13 dropped by F2, 16,450 final.
