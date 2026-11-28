# ERA V5 Lab: README of the combined repository (draft v0)

**Date:** 28 Nov 2026
**Owner of this file:** Release

This is the draft of the README for the combined repository. The combined repository holds the final code of every
stage, from the data to the quantized files. This README runs each stage on a small sample. The plan behind it, and the
list of what each team contributed, are in `combined_repository.md`.

Each stage below gives four things:

- what the stage does;
- the command that runs it on a small sample;
- the check that its output passes;
- where its output goes next.

A stage marked **Run by Release** ran on main on 28 Nov 2026, on the CPU of one laptop. Each part names the commit. Its wall time is a
rough guide from that laptop, not a target. The other stages wait for the owner team's command on the small sample. TSAI decides the licence of the code and where the repository
is published.

## Before you start

Get the code with the line endings of the repository. On Windows, Git can change them, and then the hash check of the
tokenizer files fails.

```
git clone -c core.autocrlf=false https://github.com/theschoolofai/era-v5-lab
cd era-v5-lab
```

Make one Python environment for every stage. Install the packages into the environment itself. Data A's pipeline runs
its steps with `python -I`, which does not see packages in the user folder.

```
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r teams/04-ke2/src/requirements.txt
pip install safetensors pyarrow pyyaml
```

The KE2 requirements file pins torch 2.14.1 and the `kronecker-embeddings` codec. The restore test and the checkpoint
scorer refuse an older torch. Release ran the stages with Python 3.12 and these versions. A fresh install from these
two lines is not yet tested.

Get the frozen tokenizer p1536 from the link in `teams/03-tokenizer/release/README.md`. Put it at
`teams/03-tokenizer/release/tokenizer.json`. Its sha256 is
`e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`.

The small sample: [text: waiting for Data A, which public slice of the data]

## 1. Clean, remove duplicates and write shards (Data A)

The pipeline cleans the text, removes duplicates, and writes tokenised training shards with a shard-v1 manifest. It
checks the text against Evaluation's benchmark fingerprints before tokenisation.

The commands below are from Data A's README, `teams/01-data-a/pipeline/local_trial/README.md`. Release has not run
them yet. The first line checks the config and prints the command of each step, and writes nothing.

```
python -I teams/01-data-a/pipeline/run_pipeline.py --config teams/01-data-a/pipeline/local_trial/configs/1-full.json --plan
python -I teams/01-data-a/pipeline/run_pipeline.py --config teams/01-data-a/pipeline/local_trial/configs/1-full.json
```

The local trial needs the sample folder of tokenizer sample v0. [text: waiting for Data A, the command on the public
small sample]

**Check:**
`python -I teams/01-data-a/shards/verify_shards.py --out <shards dir> --manifest <run>/pipeline_manifest.json --tokenizer teams/03-tokenizer/release/tokenizer.json`

**Output goes to:** the loader (stage 7).

## 2. Indian-language rules, share and romanised cap (Data B). Run by Release

Data B's rules for the Indian-language and code-adjacent text run inside Data A's cleaner. Data B then sets the share of
each language in a batch, and caps the romanised text.

The test of Data B's rules, from `teams/02-data-b/indic_rules/README.md`:

```
cd teams/02-data-b/indic_rules
python -I test_indic_rules.py
cd ../../..
```

**Check:** the last line is `RESULT: ALL CHECKS PASS`.

**Run by Release:** on main `493e8da3`, all checks pass for the 260 rules, in 1 s.

[text: waiting for Data B, the command for the share step on the small sample]

**Code on main:** `teams/02-data-b/mix/share_split.py`, which stops if the tokenizer sha256 does not match, and
`teams/02-data-b/romanised/token_share.py`.

**Output goes to:** the mix of the training batches.

## 3. Benchmark check of the training text (Evaluation). Run by Release

The check cuts each document into runs of words and looks up each run in the fingerprints of the benchmarks. It flags
a document that shares a run with a benchmark item, or that holds a benchmark canary line.

```
python teams/09-evaluation/decontam/decontam_check.py docs.jsonl --id-field id --text-field text > flagged.jsonl
python teams/09-evaluation/decontam/canary_scan.py docs.jsonl --id-field id --text-field text
```

Run these two tools with plain `python`, not `python -I`. They import files from their own folder, and `-I` leaves that
folder off the import path.

`docs.jsonl` holds one document per line, with the fields `id` and `text`. Parquet shards with the columns `doc_id` and
`text` also work, with no field options.

**Check:** the first line of the output names fingerprint set v2,
`2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a`. It is the set of the check of the first 41 shards
([#641](https://github.com/theschoolofai/era-v5-lab/pull/641)). Plain text gives no flag.

**Run by Release:** on main `317b31f3`, two test documents, one of them with the lab canary line. Both tools flagged that document, and
not the other. 13 s and 1 s.

**Output goes to:** the data teams, who remove the flagged documents.

## 4. Tokenizer (Tokenizer). Run by Release

The frozen tokenizer p1536 splits text into tokens. Its release files and their hashes are in
`teams/03-tokenizer/release/`.

```
cd teams/03-tokenizer
sha256sum -c release/SHA256SUMS          # macOS: shasum -a 256 -c release/SHA256SUMS
python release/verify_release.py release/tokenizer.json
cd ../..
```

**Check:** every file matches its hash, and `verify_release.py` ends with `RESULT: PASS`. Tokenizer confirmed this
command ([comment on #879](https://github.com/theschoolofai/era-v5-lab/pull/879#issuecomment-7237393184)).

**Run by Release:** on main `317b31f3`, PASS, in 53 s.

Also on main: `teams/03-tokenizer/harness/roundtrip_shards.py`, which checks that shards decode back to their text, and
`teams/03-tokenizer/harness/determinism_shards.py`, which checks that shards are the same on every run
([#874](https://github.com/theschoolofai/era-v5-lab/pull/874)).

**Output goes to:** every stage that reads tokens.

## 5. Output head (KE2). Run by Release

The byte table of the tokenizer, which the KE2 code reads. The command is the one in `teams/04-ke2/src/build_tables.py`:

```
python teams/04-ke2/src/build_tables.py --tokenizer teams/03-tokenizer/release/tokenizer.json --out tables --pos-dims 32
```

**Check:** the raw table has one row for each of the 131,072 ids, with no truncated row. Its content sha256 starts
`21072027`, the same as the table in the manifest of the first dry run
(`teams/05-architecture/jobs/evidence/2026-11-15-dryrun1-full/manifest.json`).

**Run by Release:** on main `493e8da3`, the same sha256, in 5 s.

[text: waiting for KE2, a command that runs the output head on the small sample]

**Code on main:** `teams/04-ke2/src/ke2/`. Tests: `teams/04-ke2/tests/`.

**Output goes to:** the model code (stage 6).

## 6. Model and training (Architecture). Run by Release

The unit tests of the training code, from the test log of the first dry run
(`teams/05-architecture/jobs/evidence/2026-11-15-dryrun1/smoke.md`):

```
python -m unittest discover -s teams/05-architecture/tests -p "test_week2*.py"
```

**Check:** the last line is `OK`.

**Run by Release:** on main `493e8da3`, 292 tests OK and 9 skipped, in 145 s.

[text: waiting for Architecture, a command that trains on the small sample]

**Code on main:** `teams/05-architecture/harness/train_week2.py`, with the configuration
`teams/05-architecture/configs/config_v1.yaml`. The restore test in stage 8 trains the tiny model in
`teams/05-architecture/harness/train.py`, so it runs a small part of this stage.

**Output goes to:** checkpoints, which stages 8 and 10 read.

## 7. Loader (Performance)

[text: waiting for Performance, the command on the small sample]

**Code on main:** `teams/06-performance/dataio/loader.py`.

**Check:** Infrastructure's loader contract, `teams/07-infrastructure/ckpt/loader_contract.py --factory <module>:<function>`.

**Output goes to:** the training step (stage 6).

## 8. Checkpoints and restart (Infrastructure). Run by Release

The restore test trains a tiny model, saves a checkpoint and stops. New processes restore the checkpoint and train on.
The test compares every step after the restore with a run that never stopped.

```
python teams/07-infrastructure/jobs/restore_test/restore_test.py
```

**Check:** the last line starts with `PASS restore_test`. Steps 101 to 200 give bit-equal losses and the same batch ids.

**Run by Release:** on main `317b31f3`, PASS with one process on the CPU, in 36 s. After [#899](https://github.com/theschoolofai/era-v5-lab/pull/899)
merged, it ran again on main `725fa613` with the same result. #899 adds `--optim muon` and `--resume-nproc`, which
restores at another world size.

**Output goes to:** the checkpoint store, which stage 10 reads.

## 9. Dashboard and alarms (Monitoring). Run by Release

The alarms, replayed on the metrics file of a short test run that Architecture keeps as evidence. The command is from
`teams/08-monitoring/alarms/README.md`:

```
python -I teams/08-monitoring/alarms/alarms.py --jsonl teams/05-architecture/experiments/evidence/run_a/metrics.jsonl
```

**Check:** it reads every step and reports the alarms.

**Run by Release:** on main `493e8da3`, it read 40 steps and raised no alarm, in under 1 s.

The dashboard itself needs the ClickHouse store. Its replay commands are in `teams/08-monitoring/alarms_dryrun1.md`.

**Output goes to:** the public dashboard.

## 10. Evaluation of checkpoints (Evaluation). Run by Release

The scorer reads a checkpoint from the store and checks the sha256 of every file. It scores the checkpoint and writes
one eval-mini v1 file.

```
python teams/09-evaluation/harness_lab/run_lab_ckpt.py --run-dir teams/07-infrastructure/jobs/restore_test/out/ckpt_store/restore-b
```

**Check:** all seven checks of the output file print `ok`.

**Run by Release:** on main `317b31f3`, on the checkpoint of stage 8, one record, in 6 s. It ran again on main `725fa613` with the same result. The default scorer tests the pipeline. It is not an
evaluation score.

**Output goes to:** the evaluation tables.

## 11. Post-training (Post-training). Run by Release

The tests of the chat format, which the chat model uses, from `teams/10-post-training/chat-format/README.md`:

```
python -m pytest teams/10-post-training/tests/test_chat_template.py teams/10-post-training/tests/test_render.py -q
```

**Check:** every test passes.

**Run by Release:** on main `493e8da3`, 15 passed, in 32 s.

[text: waiting for Post-training, a command that tunes on the small sample]

**Plan:** `teams/10-post-training/docs/post_training_plan_v1.md` ([#882](https://github.com/theschoolofai/era-v5-lab/pull/882)).
**Code on main:** `teams/10-post-training/sft/` and `teams/10-post-training/rl-loop/`.

**Output goes to:** the chat model.

## 12. Quantization and export (Quantization). Run by Release

The tests of the tokenizer files for serving:

```
python -m pytest teams/12-quantization/tokenizer -q
```

**Check:** every test passes. Two tests need a llama.cpp checkout and skip without one.

**Run by Release:** on main `493e8da3`, 4 passed and 2 skipped, in 13 s.

[text: waiting for Quantization, a command that quantizes the small model, with llama.cpp]

**Code on main:** `teams/12-quantization/scripts/` and `teams/12-quantization/ollama/package_ollama.py`. The files on
Hugging Face carry the model card that TSAI approves (`publish_plan.md`, "One model card for Hugging Face and Ollama", proposed in [#921](https://github.com/theschoolofai/era-v5-lab/pull/921)).

**Output goes to:** the downloads and the laptop run.

## 13. Checks of public text (Release). Run by Release

```
python teams/11-release/style/check_style.py <file> --numbers
```

**Check:** 0 errors.

**Run by Release:** on every Release file of Capstone Lab 5.

**Output goes to:** TSAI's review of the public text.

## What each team contributed

The table is in `combined_repository.md`. Each owner team confirms its row.
