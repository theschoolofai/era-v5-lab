# ERA V5 Lab: publish plan

**Date:** 28 Nov 2026
**Owner of this file:** Release

This plan lists how the lab publishes its release: the site, the Hugging Face uploads, the laptop run and the weekly progress post. Each part has an owner team and a check before it goes public. TSAI decides what is released and when.

## The site: lightning2.theschoolofai.in

The site follows the format of the V4 site (https://lightninglm.theschoolofai.in/). No fact comes from the V4 site.

| Page | What it shows | Source | Owner team | Ready when |
|---|---|---|---|---|
| Home | What the model is, in plain words, with links to every page | The Overview of the model card | Release | TSAI approves the Overview |
| Run report | The technical report of the run | `report/report_outline.md` | Release, with the section owners | TSAI approves each section |
| Training dashboard | The live dashboard of the training run | The public dashboard of Monitoring | Monitoring | Monitoring sends the link |
| Evaluation tables | The scores of each benchmark, for the full model and each bit width | The tables of Evaluation and Quantization | Evaluation, Quantization | TSAI approves the scores |
| Model card | The model card | `model_card/model_card_v0.md` | Release | TSAI approves the card |
| Downloads | The links to the files on Hugging Face and the Ollama entry | The upload checklist below | Release, Quantization | The files are uploaded and checked |
| Run it on a laptop | How to run the model on a laptop | The laptop run below | Quantization | The export of the lab's model passes its checks |
| Progress | The weekly progress posts | The weekly progress post below | Release | Each week |

TSAI decides where the site is hosted, and sets up the address.

## Hugging Face uploads

Each file gets a sha256 hash in the decision log before it goes public.

| Upload | What it holds | Owner team | Check before upload |
|---|---|---|---|
| Weights, full precision | The weights of the main run | TSAI, Quantization | The hash of each file. The weights load and give the scores in the evaluation tables. |
| Weights, smaller bit widths | One file for each bit width that TSAI chooses | Quantization | The size, memory, speed and quality table of each bit width. The export checks pass. |
| Tokenizer | The frozen tokenizer files | Tokenizer | The files match `teams/03-tokenizer/release/SHA256SUMS`, and `verify_release.py` passes. |
| Unit dictionary | The dictionary of units, if the released model uses one | Tokenizer, KE2 | The hash of the dictionary. TSAI decides whether it is released. |
| Chat format | The chat template and the special tokens | Post-training, Tokenizer | The special-token file is on main, confirmed by Post-training ([#873](https://github.com/theschoolofai/era-v5-lab/pull/873)). The files match `teams/03-tokenizer/release/SHA256SUMS`. |
| Model card | The model card, as the README of each model page | Release | TSAI approves the card. |
| Evaluation results | The scores of the released model | Evaluation | TSAI approves each score. |
| Dataset card | A card for the data that TSAI may release | Data A, Data B, Release | The licence of each source, from `teams/10-post-training/licences/licence_table.md`. TSAI decides what is released. |
| Licence | The licence of the model | TSAI | TSAI decides the licence. |

## The laptop run

Quantization's goal is a small, accurate model that runs on a laptop with 16 GB or 32 GB of memory. Its path exports the lab's model to a standard format that Ollama and llama.cpp run (`teams/12-quantization/ollama/README.md`). That file lists the parts that the standard format cannot carry, and measures what each costs.

- The path works on a stand-in model with the shape of the second dry run ([#834](https://github.com/theschoolofai/era-v5-lab/pull/834), [#838](https://github.com/theschoolofai/era-v5-lab/pull/838)).
- The steps for a reader, from download to chat: [text: waiting for Quantization, after the export of the lab's model]
- The memory and speed of each bit width on a laptop: [number: waiting for Quantization and TSAI]

## The weekly progress post

Each week, Release writes one short public post. It says what the lab did, links to the live dashboard and gives one number that moved.

- Every number in the post needs TSAI approval (`public_internal.md`).
- The post names teams only, and gives a source for each fact.
- `check_style.py --numbers` gives 0 errors on the post.
- TSAI decides where the post goes.

The form of the post:

> ERA V5 Lab, week [number]: [one sentence on what changed]. [One number that moved, with its source.] Live dashboard: [link]. All the work is in the public lab repository: https://github.com/theschoolofai/era-v5-lab

The first post, drafted for week 4. It waits for the link to the training dashboard from Monitoring, and for TSAI to say where it goes:

> ERA V5 Lab, week 4: the second dry run finished all its planned steps with the KE2 output head. The held-out bits per byte fell from 2.1607 to 2.0561 in one run with one seed (TSAI's result on [#705](https://github.com/theschoolofai/era-v5-lab/pull/705)). Live dashboard: [link: waiting for Monitoring]. All the work is in the public lab repository: https://github.com/theschoolofai/era-v5-lab
