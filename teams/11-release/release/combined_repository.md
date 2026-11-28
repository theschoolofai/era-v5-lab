# ERA V5 Lab: plan for the combined repository

**Date:** 28 Nov 2026
**Owner of this file:** Release

The combined repository holds the final code of every stage, from the data to the quantized files. One README runs each stage on a small sample. A list says what each team contributed. This file is the plan. It names the code of each stage on main today, and what each team still sends.

## How the combined repository is built

- Each stage takes the code of the main pipeline that TSAI runs, at the commit of the main run. A team's own build is checked by TSAI, not merged (Capstone Lab 5, section 1).
- Each stage has one command that runs it on a small sample, and one check that its output passes.
- The stages read and write the formats of the Capstone Lab 5 brief. These are the shard manifest, the packed row format, the loader contract and the tokenizer hash.
- Release writes the README and the list of contributions. Each owner team sends its command and confirms its stage.
- TSAI decides the licence of the code and where the repository is published.

## The stages

| Stage | Owner team | Code on main today | Output and its check | Command on a small sample |
|---|---|---|---|---|
| Clean, remove duplicates and write shards | Data A | `teams/01-data-a/pipeline/run_pipeline.py`, `teams/01-data-a/shards/shard_writer.py` | Shards with a shard-v1 manifest. Check: `teams/01-data-a/shards/verify_shards.py` | [waiting for Data A] |
| Indian-language rules, share and romanised cap | Data B | `teams/01-data-a/spec_v1_1/clean.py` (Data B rules), `teams/02-data-b/mix/share_split.py`, `teams/02-data-b/romanised/token_share.py` | The share file for each language | [waiting for Data B] |
| Benchmark check of the training text | Evaluation | `teams/09-evaluation/decontam/build_fingerprints.py`, `teams/09-evaluation/decontam/decontam_check.py` | The fingerprint set and the list of matches | [waiting for Evaluation] |
| Tokenizer | Tokenizer | `teams/03-tokenizer/release/` | The frozen tokenizer files. Checks: `verify_release.py` and `teams/03-tokenizer/harness/roundtrip_shards.py` | [waiting for Tokenizer] |
| Output head | KE2 | `teams/04-ke2/src/ke2/` | The head and its model code, with the configuration hash (issue [#856](https://github.com/theschoolofai/era-v5-lab/issues/856)) | [waiting for KE2] |
| Model and training | Architecture | `teams/05-architecture/harness/train_week2.py`, `teams/05-architecture/configs/config_v1.yaml` | A checkpoint and its run record, as in [#869](https://github.com/theschoolofai/era-v5-lab/pull/869) | [waiting for Architecture] |
| Loader | Performance | `teams/06-performance/dataio/loader.py` | Batches that pass `teams/07-infrastructure/ckpt/loader_contract.py` | [waiting for Performance] |
| Checkpoints and restart | Infrastructure | `teams/07-infrastructure/ckpt/ckpt.py` | A run that restarts with the same next batch | [waiting for Infrastructure] |
| Dashboard and alarms | Monitoring | `teams/08-monitoring/grafana/`, `teams/08-monitoring/alarms/` | The dashboard and the alarm log of a replay | [waiting for Monitoring] |
| Evaluation of checkpoints | Evaluation | `teams/09-evaluation/harness_lab/run_lab_ckpt.py`, `teams/09-evaluation/harness_lab/eval_watcher.py` | One row of scores for each checkpoint | [waiting for Evaluation] |
| Post-training | Post-training | `teams/10-post-training/sft/`, `teams/10-post-training/rl-loop/` | A chat model from the base model | [waiting for Post-training] |
| Quantization and export | Quantization | `teams/12-quantization/scripts/run_flow.py`, `teams/12-quantization/scripts/export_hf.py`, `teams/12-quantization/ollama/package_ollama.py` | The files for each bit width and the Ollama entry | [waiting for Quantization] |
| Checks of public text | Release | `teams/11-release/style/check_style.py` | 0 errors on every public file | `python teams/11-release/style/check_style.py <file> --numbers` |

## The README

The README of the combined repository has one part for each stage above, in the same order. Each part gives:

- what the stage does, in two or three sentences;
- the command that runs it on the small sample;
- the check that its output passes, and the expected result;
- where its output goes next.

The small sample is a public slice of the lab's data, small enough to run on one machine: [text: waiting for Data A, which slice]

## What each team contributed

| Team | Contributed |
|---|---|
| Data A | The cleaning pipeline, the duplicate removal and the shard writer, for the general text and code |
| Data B | The cleaning rules, reader audits and language checks for the Indian-language and code-adjacent text, and the share of each language |
| Tokenizer | The frozen tokenizer and its checks |
| KE2 | The KE2 output head, with its proofs and tests |
| Architecture | The model configuration, the training code and the settings of the dry runs |
| Performance | Faster training steps with correctness tests, and the loader |
| Infrastructure | The job queue, the checkpoints, the restart tests and the health checks |
| Monitoring | The dashboards and the alarms |
| Evaluation | The benchmarks, the benchmark check of the training text and the watcher that scores checkpoints |
| Post-training | The tuning code, the licence table and the chat format |
| Quantization | The quantization flow, the export and the Ollama path |
| Release | The public text, the style checker, the model card, the run report and the decision log |

Each owner team confirms its row. The list names teams only.
