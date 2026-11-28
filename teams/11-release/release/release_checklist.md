# ERA V5 Lab: release checklist and delivery table

**Date:** 28 Nov 2026
**Owner of this file:** Release

The release makes the lab's work public: the model card, the run report, the site, the downloads and the combined code. This file names the owner of each part. It lists what each team gives to the release, by when, and what is blocked. Release updates it each week.

## Who owns each part of the release

| Part | Owner team | File |
|---|---|---|
| Model card | Release, with an owner team for each section | `model_card/model_card_outline.md` (the owner table) and `model_card/model_card_v0.md` |
| Run report | Release, with an owner team for each section | `report/report_outline.md` |
| Decision log | Release | `records/decision_log.md` |
| Site, downloads and progress posts | Release, Quantization, Monitoring | `release/publish_plan.md` |
| Combined code | Release, with every team | `release/combined_repository.md` |
| Launch announcement | Release | `launch/launch_announcement_v0.md` |
| What is released, the model licence and the model name | TSAI | TSAI decides. Release records each decision in the decision log. |

Every section of the model card has an owner team in `model_card/model_card_outline.md`. Its Lead OK column shows which lead confirmed the section. Two sections still wait for the Infrastructure lead: Training infrastructure and Compute.

## Delivery table

Each row is one thing that a team gives to the release. "Lab 5" means the deadline of Capstone Lab 5: 2 Dec 2026, 7:00 AM IST.

| Team | Gives to the release | Used in | Due | Status |
|---|---|---|---|---|
| Data A | The dataset list, with the source, size, token count and licence of each dataset | Model card (Training data), run report, dataset card | Lab 5 | Waiting for Data A |
| Data A | The text on its sources and cleaning for the model card | Model card (Training data, Data cleaning) | Done | On main, [#811](https://github.com/theschoolofai/era-v5-lab/pull/811). The explanation of corpus v1: [#859](https://github.com/theschoolofai/era-v5-lab/pull/859). |
| Data A | The licence lines for its sources | Model card (Licence and attribution) | Lab 5 | Waiting for the co-owners to confirm |
| Data A, Data B | The Personal data text: what the cleaner masks, what it drops and what it could not check | Model card (Personal data), dataset card | Lab 5 | Release drafted it from the code on main (`teams/01-data-a/spec_v1_1/clean.py`, `build/f1_rule.py`). Waiting for the Data A and Data B OK. [#866](https://github.com/theschoolofai/era-v5-lab/pull/866) has merged, so the text can go into the card. |
| Data B | The dataset list for Indian-language and code-adjacent text, and the language check of each pack | Model card (Languages), run report, dataset card | Lab 5 | Waiting for Data B |
| Data B | Its parts of Data cleaning, and Licence and attribution | Model card | Done | On main: `teams/02-data-b/model_card/`, merged in [#866](https://github.com/theschoolofai/era-v5-lab/pull/866). Release adds it to the card. |
| Tokenizer | The frozen tokenizer files, with their hashes | Downloads | Done | On main, `teams/03-tokenizer/release/` |
| Tokenizer | The special-token file, confirmed by Post-training | Downloads, chat format | Done | On main: `teams/03-tokenizer/release/SPECIAL_TOKENS.md` and `special_slots.json`, merged in [#873](https://github.com/theschoolofai/era-v5-lab/pull/873) on 28 Nov 2026. Post-training confirmed it in #873 and [#882](https://github.com/theschoolofai/era-v5-lab/pull/882). The tokenizer and its sha256 stay the same. |
| KE2 | The output head and its model code, with the configuration hash | Combined code, downloads | Lab 5 | Waiting for KE2, issue [#856](https://github.com/theschoolofai/era-v5-lab/issues/856) |
| Architecture | The configuration of the main run, with the model size | Model card (Architecture), run report | Lab 5 | Waiting for Architecture. TSAI decides the size. |
| Architecture | The model designs and the growth recipe | Run report (Model Design, Growth) | Lab 5 | Waiting for Architecture |
| Performance | The loader, and the speed before and after, with commands | Run report (Training Speed and Correctness), combined code | Lab 5 | The loader is on main (`teams/06-performance/dataio/loader.py`), and the timing jobs are in `teams/06-performance/jobs/`. Waiting for Performance to name the final loader and its speed before and after. |
| Infrastructure | The resume proof, the memory budget and the cost table | Model card (Training infrastructure, Compute), run report | Lab 5 | Resume proof on main for the first dry run: `teams/07-infrastructure/results/restore_dryrun1.md` ([#573](https://github.com/theschoolofai/era-v5-lab/pull/573), [#633](https://github.com/theschoolofai/era-v5-lab/pull/633)). Cost model on main: `teams/07-infrastructure/support/cost/cost_report.md`, for model sizes that the lab has not chosen yet, with no price in the repo. The Lab 5 resume task is on main ([#899](https://github.com/theschoolofai/era-v5-lab/pull/899)). It adds a restart test that kills the run at a random step, with Muon. It also restores at another world size. Its CPU result: `teams/07-infrastructure/results/restart_cpu_muon.txt`. The memory budget: waiting for Infrastructure. |
| Monitoring | The link to the training dashboard, with the dry run 2 data | Site, progress posts, launch announcement | Lab 5 | Waiting for Monitoring |
| Evaluation | The mini-benchmark, the evaluation tables and the peer table | Model card (Evaluation), run report (Results), site | The mini-benchmark and the peer table: Lab 5. The evaluation tables of the main run: after the main run | Waiting for Evaluation. Dates from the Evaluation lead ([comment on #878](https://github.com/theschoolofai/era-v5-lab/pull/878#issuecomment-7236006708)). |
| Evaluation | The safety and refusal tests and their results | Model card (Safety evaluation) | The list of tests and how they are scored: Lab 5. The results: 7 days after post-training ends | The tests run on the chat model, because the base model does not follow chat prompts. Dates from the Evaluation lead ([comment on #878](https://github.com/theschoolofai/era-v5-lab/pull/878#issuecomment-7236006708)). |
| Post-training | The licence table, and the plan from the base model to the chat model | Model card (Intended use, Post-training, Licence and attribution) | Lab 5 | Licence table on main. Post-training updates it as new sources come in, and waits for TSAI to confirm a licence fix of 28 Nov. The plan from the base model to the chat model: on main, merged in [#882](https://github.com/theschoolofai/era-v5-lab/pull/882) (`teams/10-post-training/docs/post_training_plan_v1.md`). Its numbers for the tuning method wait for the dry run 2 tests. |
| Post-training | The chat template | Downloads, laptop run | Done | On main: `teams/10-post-training/chat-format/chat_template.jinja`. Quantization has the same file (`teams/12-quantization/tokenizer/chat_template.jinja`, same sha256). The tokenizer release holds it ([#686](https://github.com/theschoolofai/era-v5-lab/pull/686)), and Tokenizer checked it on p1536 ([#642](https://github.com/theschoolofai/era-v5-lab/pull/642)). |
| Quantization | The file size, memory, speed and quality of each bit width | Model card (Quantized versions), downloads | Lab 5 | Proposal on main, [#853](https://github.com/theschoolofai/era-v5-lab/pull/853). The table builder for each bit width is on main, [#904](https://github.com/theschoolofai/era-v5-lab/pull/904). Quantization's text for the model card is on main, with its numbers waiting for TSAI ([#905](https://github.com/theschoolofai/era-v5-lab/pull/905)). |
| Quantization | The export to Hugging Face and the Ollama entry | Downloads, laptop run | After the main run | Tested on a stand-in model, [#834](https://github.com/theschoolofai/era-v5-lab/pull/834), [#838](https://github.com/theschoolofai/era-v5-lab/pull/838) |
| TSAI | The weights of the main run | Downloads, evaluation tables | After the main run | Blocked: the main run has not started |
| TSAI | The model name, the model licence and what is released | Model card, downloads, site | Before the release | Waiting for TSAI |

## What is blocked

- The weights, the final scores and the downloads wait for the main run. TSAI decides the go or no-go.
- The model size waits for the real token count of the first full corpus. Architecture proposes it, and TSAI decides.
- The laptop run waits for the export of the lab's own model. Quantization's tools work on a stand-in model so far.

## Release checklist

Release ticks each line when its evidence is in place.

- [ ] Every section of the model card is approved by TSAI, with no placeholder left.
- [ ] Every section of the run report is approved by TSAI, with a source for each claim in the claim table.
- [ ] Every number in public text has TSAI approval (`public_internal.md`).
- [ ] The public text names teams only, and nothing from the internal list.
- [ ] `check_style.py --numbers` gives 0 errors on every public file.
- [ ] TSAI has decided the model licence, the model name and what is released.
- [ ] Every data source is credited, with its licence (`teams/10-post-training/licences/licence_table.md`).
- [ ] The model card says how the lab handled personal data, and gives the safety evaluation summary.
- [ ] The decision log lists every decision, experiment and job, with its evidence.
- [ ] The downloads match the upload checklist in `release/publish_plan.md`, with a hash for each file.
- [ ] The laptop run works from the published files alone.
- [ ] The site has the run report, the dashboard, the evaluation tables and the downloads.
- [ ] The combined code runs each stage on a small sample, as `release/combined_repository.md` says.
- [ ] The launch announcement has its date, its goal and the dashboard link.
