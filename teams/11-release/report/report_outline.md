# ERA V5 Lab: run report outline

**Date:** 3 Nov 2026
**Owner of this outline:** Release

The run report is the long public document that explains how the lab built and trained the model.
The V4 run report (https://lightninglm.theschoolofai.in/) is the model for its shape.
This file lists the sections of the run report.
Each section has an owner team, a status and a lead confirmation.

## How to use this outline

- The owner team writes the text of its section.
- Release edits the text for style and runs `check_style.py` on it.
- TSAI approves the text before it goes into the run report.
- A section can have more than one owner team. The first team named leads the section.

**Status** is one of these:

- **empty:** nobody has written the text yet.
- **in progress:** the owner team is writing the text.
- **approved:** TSAI approved the text.

**Lead OK** tracks whether the lead of each owner team confirmed the section and its scope.
Write `pending` until they confirm. Then write `OK` and the GitHub handle of each lead who confirmed.
For a shared section, name each owner team, for example `Data A OK @handle; Data B pending`.
This confirms the outline only. TSAI still approves the final text.

**First draft due** is a date that Release proposes and TSAI confirms. Sections on work that is done before the main
run have a fixed date, one week after the class of 5 Dec 2026. Sections that need the main run are due 7 days after
it ends.

## Sections

| Section | Owner team | Status | Lead OK | First draft due (proposed) |
|---|---|---|---|---|
| Abstract | Release | empty | Release OK @pyru | 7 days after the main run |
| Introduction | Release, Data B, Evaluation | empty | Release OK @pyru; Data B OK @shankarpandala; Evaluation OK @rahulni | 7 days after the main run |
| Background and Related Work | Release, Data A, Tokenizer, KE2, Architecture, Post-training | empty | Release OK @pyru; Data A OK @patilvijay23; Tokenizer OK @rjvim; KE2 pending; Architecture OK @shivman; Post-training pending | 12 Dec 2026 |
| Training Data: General Text and Code | Data A, Evaluation | empty | Data A pending; Evaluation pending | 12 Dec 2026 |
| Training Data: Indian-language and Code-adjacent Text | Data B, Evaluation | empty | Data B pending; Evaluation pending | 12 Dec 2026 |
| Tokenizer | Tokenizer | empty | OK @rjvim | 12 Dec 2026 |
| KE2 | KE2 | empty | pending | 12 Dec 2026 |
| Model Design | Architecture | empty | OK @shivman | 12 Dec 2026 |
| Growth | Architecture | empty | pending | 12 Dec 2026 |
| Training Speed and Correctness | Performance, KE2 | empty | Performance OK @raj-harit-v2; KE2 pending | 12 Dec 2026 |
| Training Infrastructure | Infrastructure | empty | pending | 12 Dec 2026 |
| Monitoring the Training Run | Monitoring | empty | OK @sandeepkunkunuru | 12 Dec 2026 |
| Evaluation | Evaluation | empty | pending | 12 Dec 2026 |
| The Training Run | Infrastructure, Data A, Architecture, Monitoring | empty | Infrastructure pending; Data A OK @patilvijay23; Architecture OK @shivman; Monitoring OK @sandeepkunkunuru | 7 days after the main run |
| What Went Wrong and How We Fixed It | Monitoring, Infrastructure | empty | Monitoring OK @sandeepkunkunuru; Infrastructure pending | 7 days after the main run |
| Post-training | Post-training | empty | pending | 7 days after the main run |
| Quantization and Serving | Quantization | empty | OK @SreekanthZipsy | 7 days after the main run |
| Results | Evaluation, Quantization | empty | Evaluation OK @rahulni; Quantization OK @SreekanthZipsy | 7 days after the main run |
| Limitations | Evaluation, Release | empty | Evaluation OK @rahulni; Release OK @pyru | 7 days after the main run |
| Reproducibility | Release, Architecture, Infrastructure | empty | Release OK @pyru; Architecture OK @shivman; Infrastructure pending | 7 days after the main run |
| Licence and Attribution | Post-training, Data A, Data B | empty | Post-training pending; Data A OK @patilvijay23; Data B OK @shankarpandala | 12 Dec 2026 |
| Conclusion | Release | empty | Release OK @pyru | 7 days after the main run |
| Contributors and Acknowledgments | Release | empty | Release OK @pyru | 12 Dec 2026 |
| Resources and Citation | Release | empty | Release OK @pyru | 7 days after the main run |

## Claim table

Each claim in the run report has a row here, with the file that proves it. A claim with no evidence file stays out
of the report. The owner team of the section adds its claims. Release checks each evidence file.

| Claim | Section | Evidence | Status |
|---|---|---|---|
| The lab froze the tokenizer p1536 for training. | Tokenizer | `updates/gate3.md`, [#504](https://github.com/theschoolofai/era-v5-lab/pull/504) | Approved at Gate 3 |
| Indian-language text in its own script is 8% of every training batch. | Training Data: Indian-language and Code-adjacent Text | `updates/gate3.md`, [#400](https://github.com/theschoolofai/era-v5-lab/pull/400), [#522](https://github.com/theschoolofai/era-v5-lab/pull/522) | Approved at Gate 3 |
| The model is a mixture of experts, with 16 routed experts and 1 shared expert, and each token goes to two of them. | Model Design | `updates/gate2.md`, `updates/gate3.md`, [#447](https://github.com/theschoolofai/era-v5-lab/pull/447) | Approved at Gate 3 |
| A test with more routed experts did worse. | Model Design | [#659](https://github.com/theschoolofai/era-v5-lab/pull/659), [#668](https://github.com/theschoolofai/era-v5-lab/pull/668) | Approved at Gate 3 |
| The model uses the KE2 output head in place of the dense untied head. | KE2 | `teams/04-ke2/gate3.md`, [#694](https://github.com/theschoolofai/era-v5-lab/pull/694), [#702](https://github.com/theschoolofai/era-v5-lab/pull/702) | Approved at Gate 3 |
| The first dry run finished, and a restore from its checkpoint matched bit for bit. | Training Infrastructure | `updates/gate3.md`, [#620](https://github.com/theschoolofai/era-v5-lab/pull/620), [#573](https://github.com/theschoolofai/era-v5-lab/pull/573), [#633](https://github.com/theschoolofai/era-v5-lab/pull/633) | Approved at Gate 3 |
| Every file of training text is checked against the benchmark questions before training reads it. | Evaluation | `model_card/model_card_v0.md`, [#784](https://github.com/theschoolofai/era-v5-lab/pull/784) | Approved in the model card |
| The second dry run finished all its planned steps with the KE2 output head. | The Training Run | `updates/gate4.md` ([#705](https://github.com/theschoolofai/era-v5-lab/pull/705)), [#869](https://github.com/theschoolofai/era-v5-lab/pull/869) | Waiting for TSAI approval of the Gate 4 update |

## A second, shorter paper

Capstone Lab 5 asks for a second, shorter paper on any new result that a team found. TSAI keeps the list of these
results, because unpublished work stays internal (`public_internal.md`). Release writes the outline of the short
paper, with an owner and a date for each section, once TSAI names the result.

## Changes to this outline

- 28 Nov 2026: Capstone Lab 5 asks for a section per team, an owner and a date for each section, and a claim table.
  Training Data is now two sections, one for Data A and one for Data B. Growth and Evaluation are new sections, for
  Architecture and Evaluation. Their leads confirm the new scopes. Each section has a proposed date for its first draft.

## Rules for every section

- Write only about work that is done. Do not promise dates, sizes or results.
- Write `[number: waiting for TSAI]` in place of any number that TSAI has not approved.
- Name teams only. Do not name any person. Contributors and Acknowledgments lists the teams.
- Follow `teams/11-release/style/style_guide.md`.
