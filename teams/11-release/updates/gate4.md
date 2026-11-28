# ERA V5 Lab: Gate 4 update

**Date:** 28 Nov 2026
**Period:** 22 Nov to 28 Nov 2026

At this gate, TSAI reviewed the second dry run and decided whether the main training run starts. Each decision uses
the words that TSAI approved.

## The second dry run

A dry run is a short test of the whole training setup before the main training run.

The second dry run tested the training settings for the main run on a small model, including the KE2 output head. The
run's own record confirms that the run used this head. The dry run checked that the run finishes all its planned
steps, and that the loss stays a valid number.

The run finished all 1,221 of its planned steps, inside its time limit, and the loss stayed a valid number at every
step. The training loss fell from 10.27 at the first step to 5.25 at the last. The held-out validation bits per byte,
the prediction loss on text set aside from training, fell from 2.1607 to 2.0561. This is one run with one seed, and
the held-out value moves by about 0.1 between checks. So the final value is not a stable estimate. The run trained on
one English web shard, not on the first 41 shards. So its scores on code and Indian-language text come from a model
that saw English only. TSAI accepted this run as the Gate 4 evidence for the second dry run.

## The model card

Release wrote the first draft of the model card, and TSAI approved it on 24 Nov 2026. It now has the training data
section from Data A and Data B, and Data A's part of the data cleaning section. It also has the Evaluation section,
which names the benchmarks, and the licence and attribution text from Post-training. Release wrote the overview, the
contributors and where to find more. The other sections wait for their owner teams. The card also has new sections,
still empty, on what it does not claim, what is released, its sources and how to cite it.
The KE2 section now covers the KE2 output head, which TSAI chose at Gate 3 in place of the dense untied head.
Architecture added this head to the training code on 24 Nov 2026.

## Gate 4 evidence from the teams

Each team showed its work for Gate 4 in public pull requests.

- **Tokenizer:** The frozen tokenizer p1536 turns the tokens in the training files back into the original text,
  with no change. Its files include the lab's chat format. A public link lets Evaluation download it without
  signing in. Tokenizer also gave Architecture the token counts of the training text, with their sources.
- **Data A:** Data A updated the pipeline for the full corpus and checked scoped cleaning fixes. It also made the step
  that writes the training files use less memory. The team completed its assigned sample audits and posted the results
  of its cross-language duplicate check. TSAI approved removing these duplicates between Hindi and English, and the
  change waits to merge. For Sanskrit and Odia, the check remains report-only. Verified full-corpus shards and their
  training-token count are still pending.
- **Data B:** Data B measured every part of its Gate 3 summary of the Indian-language text. Cleaning lost none of
  the joiners, the invisible marks that some Indian scripts need. Native readers read samples in their own
  languages, and most of the damage that they found was in the raw text, before cleaning. Every Indian-language
  pack of corpus v1 has a check of its training files, or is marked as not covered. Data B's part of the training
  data section of the model card is on main.
- **KE2:** KE2 gave Architecture reference values for the KE2 layers, so the training code can be checked against
  KE2's own version. Its job request to time these layers with the frozen tokenizer is on main.
- **Architecture:** Architecture wrote the settings of the second dry run, and its job request is on main. The
  settings use the KE2 output head and the learning rate that TSAI set for the Muon optimizer. The exact size of the
  model is still open.
- **Performance:** Performance added an optional faster way to compute attention as a separate setting, so the second
  dry run itself stays unchanged. Its tools now read the training settings for balancing the experts and for the
  router's optimizer. It also wrote a smaller profiling job for the first dry run.
- **Infrastructure:** Infrastructure wrote the job request for a planned stop and restart in the second dry run, and a
  script that checks the restart. Its runbook now covers failed machines, stuck communication between GPUs and damaged
  checkpoints. Its settings keep the checkpoints that Evaluation scores, and its checkpoint plan now uses
  Performance's timing of a full-size save.
- **Monitoring:** Monitoring added panels to the public dashboard for the pace of training and for the training text
  in each pack. It now stores every restart, saved checkpoint and alarm of a run, and shows them on its private
  dashboard. It built, with Evaluation, the alarm for late checkpoint scoring, and its job request to watch the second
  dry run live is on main. Its new tests feed faults, such as a dead expert or a sudden memory jump, into its alarms
  and record which faults they miss.
- **Evaluation:** Evaluation built, with Monitoring, an alarm that warns when the scoring of saved checkpoints falls
  behind training. Each of the first 41 shards now has a second check against the benchmark questions. Evaluation's
  watcher job for the second dry run is on main. Its scores of the run are pending.
- **Post-training:** Post-training adapted its fine-tuning and reinforcement learning code to the KE2 output head, and
  added a reader for the checkpoints that Infrastructure saves. Its job requests to compare tuning methods on the
  second dry run are on main. Its licence and attribution text for the model card is on main.
- **Quantization:** Quantization widened its benchmark tests and measured how smaller file formats change the scores
  of similar public models, including a model for Indian languages. The format closest to full size kept the scores on
  every model. The smallest format lost points on every model, most of all on the Indian-language model's reading
  tasks. Its proposal on the format for the lab's model is with TSAI for a decision at this gate. Its tools turn a
  checkpoint of the lab's model into files that people can run in Ollama, tested on a stand-in model.

## Decisions

| Decision | Team that proposed it | Decision text |
|---|---|---|
| The second dry run | Architecture, Infrastructure | TSAI accepted the second dry run as the Gate 4 evidence. |
| The main training run | Architecture, Infrastructure | Go or no-go: [waiting for TSAI] |
| The launch announcement | Release | TSAI approved the draft of the launch announcement on 24 Nov 2026. The date and the link to the public dashboard come before it is published. |
| The learning rate for the Muon optimizer | Architecture | TSAI set the learning rate for the Muon optimizer to 0.006, the current estimate. The second dry run uses this rate. |

Short forms: Corpus v1 is the first version of the lab's cleaned training text. KE2 is the lab team that tests its
embedding method on the lab's tokenizer. The output head is the last part of the model, which scores each token as the
next token. A dense untied head is the standard output head.

## Next

[waiting for TSAI]

---

## Review record (remove this section before publishing)

This record is public, like the rest of the pull request. Put only public facts in it: yes or no, and links to
public pull requests. Never link to the CAP chat. Chat links are internal.

How to fill it:

1. Infrastructure sends the summary of the second dry run, or names the pull request that has it. Each lead links
   the Gate 4 evidence of their team in a comment on this pull request. Write one plain line for each team, and
   remove the line of a team that sends no evidence by Sat 28.
2. Paste each text above. Edit it only for style, and send the edit back to the writer.
3. After TSAI decides, write each decision in the words that TSAI approves. Remove a row if TSAI does not decide it
   at this gate, and add a row for each other decision that TSAI makes. If TSAI does not decide go or no-go at this
   gate, change the opening sentence too. Add a decision row for each "Open from Gate 3" row that TSAI decides. The
   other open rows carry over to the next gate.
4. Give the source of each fact: a public pull request or a file in this repository. Gate 4 needs a source for each
   fact.
5. The lead of each team gives an OK on the text about their team.
6. Write `[number: waiting for TSAI]` for any number that TSAI has not approved yet.
7. Run `python teams/11-release/style/check_style.py <this file> --numbers` and clear every error.
8. TSAI approves this pull request before the G11 lead merges it.

| Fact | Team | Source | Text received | Lead OK |
|---|---|---|---|---|
| The second dry run | Architecture, Infrastructure, Evaluation | Plan: job request [#720](https://github.com/theschoolofai/era-v5-lab/pull/720) (Architecture), with the KE2 output head in its settings ([#717](https://github.com/theschoolofai/era-v5-lab/pull/717)). The planned stop and restart: [#738](https://github.com/theschoolofai/era-v5-lab/pull/738) and [#743](https://github.com/theschoolofai/era-v5-lab/pull/743) (Infrastructure). The checkpoint scores: [#707](https://github.com/theschoolofai/era-v5-lab/pull/707) (Evaluation). The training text, the first 41 shards: the job on main, [#787](https://github.com/theschoolofai/era-v5-lab/pull/787); the check against the benchmark questions, [#641](https://github.com/theschoolofai/era-v5-lab/pull/641). TSAI set this text for the dry run on 24 Nov, in place of corpus v1 ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7159006781)). Result: ([TSAI comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7216776806)). The run itself trained on one English web shard, not the first 41 shards, so the plan sentence on the 41 shards is gone. All numbers in the result come from that comment. The KE2 output head: the dry run 2 settings turn it on ([#717](https://github.com/theschoolofai/era-v5-lab/pull/717), [#787](https://github.com/theschoolofai/era-v5-lab/pull/787)). TSAI's record of the run, [#869](https://github.com/theschoolofai/era-v5-lab/pull/869), shows that the run used it (`manifest.json`). TSAI confirmed this to Release on 28 Nov 2026 | plan: yes, from the job requests. Result: yes, from TSAI, with no new number | Architecture: yes for the KE2 head sentence and the result section ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7228537509)), and for the head and the learning rate ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7135446665)). The training text: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7161567538)). Infrastructure: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7234579117)). Evaluation: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7134626582)) |
| The first draft of the model card | Release, Data A, Data B, Evaluation, Post-training | `model_card/model_card_v0.md`, [#759](https://github.com/theschoolofai/era-v5-lab/pull/759), approved and merged by TSAI on 24 Nov. Evaluation section: [#770](https://github.com/theschoolofai/era-v5-lab/pull/770), [#784](https://github.com/theschoolofai/era-v5-lab/pull/784). Data B problems in the code-adjacent text, the overview and the KE2 section: [#782](https://github.com/theschoolofai/era-v5-lab/pull/782), [#791](https://github.com/theschoolofai/era-v5-lab/pull/791), merged by TSAI on 25 Nov. New sections of the outline: [#803](https://github.com/theschoolofai/era-v5-lab/pull/803), merged by TSAI on 25 Nov. Data A's training data and cleaning text, the Post-training licence text, the MILU credit and the new sections: [#811](https://github.com/theschoolofai/era-v5-lab/pull/811), merged by TSAI on 26 Nov. Owner and status of each section: `model_card/model_card_outline.md` | yes | Release: yes; Data B: yes for the first part ([comment on #759](https://github.com/theschoolofai/era-v5-lab/pull/759#issuecomment-7108567909)). The code-adjacent problems: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7223729241)). Evaluation: yes ([comment on #784](https://github.com/theschoolofai/era-v5-lab/pull/784#issuecomment-7129730898)); Data A: yes ([comment on #811](https://github.com/theschoolofai/era-v5-lab/pull/811#issuecomment-7169583801)); Post-training: yes ([comment on #811](https://github.com/theschoolofai/era-v5-lab/pull/811#issuecomment-7160236414)) |
| The KE2 output head in the model card | KE2 | TSAI decision in `teams/04-ke2/gate3.md`, merged in [#694](https://github.com/theschoolofai/era-v5-lab/pull/694), corrected in [#702](https://github.com/theschoolofai/era-v5-lab/pull/702). Gate 3 update: [#701](https://github.com/theschoolofai/era-v5-lab/pull/701). Model card outline: [#704](https://github.com/theschoolofai/era-v5-lab/pull/704). The KE2 section of the model card: [#791](https://github.com/theschoolofai/era-v5-lab/pull/791), merged by TSAI on 25 Nov | yes | KE2: yes for the text before the date edit ([comment on #791](https://github.com/theschoolofai/era-v5-lab/pull/791#issuecomment-7142627011)), and for the date edit ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7230047772)) |
| The KE2 output head in the training code | Architecture | [#717](https://github.com/theschoolofai/era-v5-lab/pull/717), merged by TSAI on 24 Nov. The Gate 3 update said that Architecture adds the head to the training code | yes | Architecture: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7134663706)) |
| Decision: the second dry run | Architecture, Infrastructure | TSAI accepted the run as the Gate 4 evidence ([TSAI comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7216776806)) | yes | TSAI: yes ([TSAI comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7216776806)) |
| Decision: the main training run | Architecture, Infrastructure | TSAI decision at Gate 4 | no | no |
| Decision: the launch announcement | Release | `launch/launch_announcement_v0.md`, [#600](https://github.com/theschoolofai/era-v5-lab/pull/600), [#603](https://github.com/theschoolofai/era-v5-lab/pull/603). Week 4 draft: [#753](https://github.com/theschoolofai/era-v5-lab/pull/753), approved and merged by TSAI on 24 Nov. The KE2 head row of its review record: [#796](https://github.com/theschoolofai/era-v5-lab/pull/796), merged by TSAI on 25 Nov | yes | Release: yes |
| Open from Gate 3: the evaluation schedule | Evaluation | [#662](https://github.com/theschoolofai/era-v5-lab/pull/662). Version 1.2 of the schedule: [#722](https://github.com/theschoolofai/era-v5-lab/pull/722). Gate 3 left it open only for the lag alarm, which TSAI merged in [#769](https://github.com/theschoolofai/era-v5-lab/pull/769). TSAI decides whether it closes at this gate | yes | Evaluation: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7182415245)) |
| Open from Gate 3: the tuning method after the main training | Post-training | [#524](https://github.com/theschoolofai/era-v5-lab/pull/524), [#593](https://github.com/theschoolofai/era-v5-lab/pull/593), [#634](https://github.com/theschoolofai/era-v5-lab/pull/634) | no | no |
| Open from Gate 3: serving and quantization | Quantization | [#538](https://github.com/theschoolofai/era-v5-lab/pull/538). The bit-width proposal, version 2: [#853](https://github.com/theschoolofai/era-v5-lab/pull/853), merged 27 Nov. TSAI decides the bit width at this gate ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7214091806)) | yes | no |
| Decision: the learning rate for the Muon optimizer (open from Gate 3) | Architecture | `updates/gate3.md` (the learning rate). Decided: TSAI's correction in [#725](https://github.com/theschoolofai/era-v5-lab/pull/725), which sets the rate in config v1 and in the second dry run | yes | Architecture: yes, 0.006 is the current estimate ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7135446665)) |
| Open from Gate 3: the exact model size | Architecture | `updates/gate3.md` (model layout and size) | no | no |
| Gate 4 evidence: Tokenizer | Tokenizer | Round trip on the p1536 shards: [#658](https://github.com/theschoolofai/era-v5-lab/pull/658). Chat format: [#642](https://github.com/theschoolofai/era-v5-lab/pull/642), [#686](https://github.com/theschoolofai/era-v5-lab/pull/686). Public download link: [#700](https://github.com/theschoolofai/era-v5-lab/pull/700). Token counts for Architecture: [#719](https://github.com/theschoolofai/era-v5-lab/pull/719). Links from the Tokenizer lead ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7139242515)) | yes | Tokenizer: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7182854394)) |
| Gate 4 evidence: Data A | Data A | The pipeline and the cleaning fixes: [#767](https://github.com/theschoolofai/era-v5-lab/pull/767), merged 24 Nov. The sample audits: collated in a pull request on Data A's fork, outside this repository. Cross-language duplicate detection: [#816](https://github.com/theschoolofai/era-v5-lab/pull/816), a draft; its results: [#858](https://github.com/theschoolofai/era-v5-lab/pull/858), merged 27 Nov; the Hindi and English removal that TSAI approved on 27 Nov: [#860](https://github.com/theschoolofai/era-v5-lab/pull/860), open. The step that writes the training files: [#823](https://github.com/theschoolofai/era-v5-lab/pull/823), merged 26 Nov. The production shards and the token count of corpus v1 are still pending. Links and wording from the Data A lead ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7166660403)) | yes. Updated by Release after the Data A lead's new links ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7218134226)) | Data A: yes for the first line ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7166660403)); the updated line: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7218323997)) |
| Gate 4 evidence: Data B | Data B | Gate 3 summary of the Indian-language text, `teams/02-data-b/audit/gate3_indic.md`: [#526](https://github.com/theschoolofai/era-v5-lab/pull/526), [#783](https://github.com/theschoolofai/era-v5-lab/pull/783). Joiners: [#653](https://github.com/theschoolofai/era-v5-lab/pull/653). The cleaning problem in [issue #734](https://github.com/theschoolofai/era-v5-lab/issues/734), fixed on main by [#767](https://github.com/theschoolofai/era-v5-lab/pull/767). Language labels: [#673](https://github.com/theschoolofai/era-v5-lab/pull/673). The mix of the training text: [#723](https://github.com/theschoolofai/era-v5-lab/pull/723), and [#794](https://github.com/theschoolofai/era-v5-lab/pull/794), merged by TSAI on 25 Nov. Model card text: [#525](https://github.com/theschoolofai/era-v5-lab/pull/525), [#782](https://github.com/theschoolofai/era-v5-lab/pull/782). Reader audits merged by TSAI on 25 Nov: [#788](https://github.com/theschoolofai/era-v5-lab/pull/788), [#806](https://github.com/theschoolofai/era-v5-lab/pull/806). Merged on 26 Nov: [#818](https://github.com/theschoolofai/era-v5-lab/pull/818), [#824](https://github.com/theschoolofai/era-v5-lab/pull/824). Still open: [issue #795](https://github.com/theschoolofai/era-v5-lab/issues/795), for one Marathi pack. Links from the Data B lead ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7155962319)) | yes | Data B: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7198159282)) |
| Gate 4 evidence: Architecture | Architecture | The job on main, `teams/05-architecture/jobs/2026-11-22-dryrun2.md`: [#787](https://github.com/theschoolofai/era-v5-lab/pull/787). The KE2 output head: [#717](https://github.com/theschoolofai/era-v5-lab/pull/717). The Muon learning rate: [#725](https://github.com/theschoolofai/era-v5-lab/pull/725). The router settings: [#736](https://github.com/theschoolofai/era-v5-lab/pull/736), [#748](https://github.com/theschoolofai/era-v5-lab/pull/748). A separate test with faster attention: [#804](https://github.com/theschoolofai/era-v5-lab/pull/804), merged by TSAI on 25 Nov. The model size is still open. Links from the Architecture lead, with no result claimed ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7159006781)). More merged Architecture work, listed by an Architecture member ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7209383033)). The training plan: [#706](https://github.com/theschoolofai/era-v5-lab/pull/706), [#713](https://github.com/theschoolofai/era-v5-lab/pull/713), [#748](https://github.com/theschoolofai/era-v5-lab/pull/748), [#750](https://github.com/theschoolofai/era-v5-lab/pull/750), [#712](https://github.com/theschoolofai/era-v5-lab/pull/712). The dry run 2 job and its corrections: [#720](https://github.com/theschoolofai/era-v5-lab/pull/720), [#727](https://github.com/theschoolofai/era-v5-lab/pull/727), [#740](https://github.com/theschoolofai/era-v5-lab/pull/740). Checks of the KE2 head in the training code: [#772](https://github.com/theschoolofai/era-v5-lab/pull/772), [#785](https://github.com/theschoolofai/era-v5-lab/pull/785), [#798](https://github.com/theschoolofai/era-v5-lab/pull/798), [#799](https://github.com/theschoolofai/era-v5-lab/pull/799), [#773](https://github.com/theschoolofai/era-v5-lab/pull/773). Main-run inputs with no decision yet: [#825](https://github.com/theschoolofai/era-v5-lab/pull/825), [#821](https://github.com/theschoolofai/era-v5-lab/pull/821), [#831](https://github.com/theschoolofai/era-v5-lab/pull/831). The report tool for the dry run 2 result: [#829](https://github.com/theschoolofai/era-v5-lab/pull/829) | yes | Architecture: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7161567538)) |
| Gate 4 evidence: Evaluation | Evaluation | The lag alarm, built with Monitoring: [#769](https://github.com/theschoolofai/era-v5-lab/pull/769); the follow-up with Monitoring's review points: [#822](https://github.com/theschoolofai/era-v5-lab/pull/822), merged on 26 Nov. The second check of the last shards: [#754](https://github.com/theschoolofai/era-v5-lab/pull/754). The dry run 2 watcher: job [#707](https://github.com/theschoolofai/era-v5-lab/pull/707) and run details [#747](https://github.com/theschoolofai/era-v5-lab/pull/747). Links and wording from the Evaluation lead ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7182415245)) | yes, with two sentences changed after the dry run 2 result, the second in the Evaluation lead's own words | Evaluation: yes for the text before the edit ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7182415245)). The two changes after the dry run 2 result: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7224391503)) |
| Gate 4 evidence: KE2 | KE2 | [#765](https://github.com/theschoolofai/era-v5-lab/pull/765), [#731](https://github.com/theschoolofai/era-v5-lab/pull/731), all merged. Drafted by Release from the team's merged pull requests, with no plan and no dry run 2 result. Waiting for the lead's OK or own line | yes | KE2: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7230047772)) |
| Gate 4 evidence: Performance | Performance | [#804](https://github.com/theschoolofai/era-v5-lab/pull/804), [#749](https://github.com/theschoolofai/era-v5-lab/pull/749), [#776](https://github.com/theschoolofai/era-v5-lab/pull/776), all merged. The first dry run profiling job ([#776](https://github.com/theschoolofai/era-v5-lab/pull/776)) is the only Performance run in the line. The test run of the faster-attention setting ([#805](https://github.com/theschoolofai/era-v5-lab/pull/805)) is queued and has not run, so the line claims no result for it ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7220768786)). Drafted by Release from the team's merged pull requests, with no plan and no dry run 2 result. Waiting for the lead's OK or own line | yes | Performance: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7220768786)) |
| Gate 4 evidence: Infrastructure | Infrastructure | [#738](https://github.com/theschoolofai/era-v5-lab/pull/738), [#743](https://github.com/theschoolofai/era-v5-lab/pull/743), [#756](https://github.com/theschoolofai/era-v5-lab/pull/756), [#828](https://github.com/theschoolofai/era-v5-lab/pull/828), [#654](https://github.com/theschoolofai/era-v5-lab/pull/654), [#739](https://github.com/theschoolofai/era-v5-lab/pull/739), [#745](https://github.com/theschoolofai/era-v5-lab/pull/745), all merged. Drafted by Release from the team's merged pull requests, with no plan and no dry run 2 result. Waiting for the lead's OK or own line | yes | Infrastructure: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7234579117)) |
| Gate 4 evidence: Monitoring | Monitoring | [#779](https://github.com/theschoolofai/era-v5-lab/pull/779), [#817](https://github.com/theschoolofai/era-v5-lab/pull/817), [#774](https://github.com/theschoolofai/era-v5-lab/pull/774), [#769](https://github.com/theschoolofai/era-v5-lab/pull/769), [#822](https://github.com/theschoolofai/era-v5-lab/pull/822), [#833](https://github.com/theschoolofai/era-v5-lab/pull/833), [#839](https://github.com/theschoolofai/era-v5-lab/pull/839), all merged. Also merged, from the Monitoring lead's list: [#732](https://github.com/theschoolofai/era-v5-lab/pull/732), [#841](https://github.com/theschoolofai/era-v5-lab/pull/841), [#863](https://github.com/theschoolofai/era-v5-lab/pull/863). [#864](https://github.com/theschoolofai/era-v5-lab/pull/864), merged 27 Nov (synthetic replay, no dry run 2 data). It tests the lag alarm at real pace, because the run's logs have not been returned. Added at a Monitoring member's request ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7223212823)); the line itself has no edit. Drafted by Release from the team's merged pull requests, with no plan and no dry run 2 result. Waiting for the lead's OK or own line | yes | Monitoring: yes, with no edit ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7224774883)) |
| Gate 4 evidence: Post-training | Post-training | [#746](https://github.com/theschoolofai/era-v5-lab/pull/746), [#778](https://github.com/theschoolofai/era-v5-lab/pull/778), [#797](https://github.com/theschoolofai/era-v5-lab/pull/797), [#835](https://github.com/theschoolofai/era-v5-lab/pull/835), [#811](https://github.com/theschoolofai/era-v5-lab/pull/811), [#836](https://github.com/theschoolofai/era-v5-lab/pull/836), all merged. The dry run 2 job approvals and the Indian-language training sign-offs: [#861](https://github.com/theschoolofai/era-v5-lab/pull/861), merged on 28 Nov. Drafted by Release from the team's merged pull requests, with no plan and no dry run 2 result. Waiting for the lead's OK or own line | yes | Post-training: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7219768872)) |
| Gate 4 evidence: Quantization | Quantization | [#714](https://github.com/theschoolofai/era-v5-lab/pull/714), [#737](https://github.com/theschoolofai/era-v5-lab/pull/737), [#786](https://github.com/theschoolofai/era-v5-lab/pull/786), [#808](https://github.com/theschoolofai/era-v5-lab/pull/808), [#812](https://github.com/theschoolofai/era-v5-lab/pull/812), [#780](https://github.com/theschoolofai/era-v5-lab/pull/780), [#834](https://github.com/theschoolofai/era-v5-lab/pull/834), [#838](https://github.com/theschoolofai/era-v5-lab/pull/838), [#840](https://github.com/theschoolofai/era-v5-lab/pull/840), [#843](https://github.com/theschoolofai/era-v5-lab/pull/843), [#844](https://github.com/theschoolofai/era-v5-lab/pull/844), [#848](https://github.com/theschoolofai/era-v5-lab/pull/848), [#850](https://github.com/theschoolofai/era-v5-lab/pull/850), [#853](https://github.com/theschoolofai/era-v5-lab/pull/853), all merged. The lead-in from the Quantization lead ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7210869613)). The capped MILU set, the sources and the bit-width proposal from a Quantization member ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7214091806)). The member's longer text has numbers that TSAI has not approved, so the line keeps only what needs no number. The first sentence leaves out the benchmark names, so that it needs no short forms | yes | Quantization: yes, with the lead-in ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7210869613)) |

- [x] `check_style.py` gives 0 errors
- [x] Every number in the text has TSAI approval. 41 comes from the approved Gate 3 update. The dry run 2 numbers come from TSAI's result ([TSAI comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7216776806)). 0.006 was set by TSAI in [#725](https://github.com/theschoolofai/era-v5-lab/pull/725). The other numbers are gate numbers and dates
- [x] The text names teams only, and no person
- [x] Nothing from the internal list in `public_internal.md`. The KE2 line leaves out the design of the head
- [ ] No `waiting for` placeholder left in the text
- [x] A team member commented on this pull request (member reviews on 23 Nov and 26 Nov 2026)
- [ ] TSAI approved on: <DD Mon YYYY>
- [ ] Merged after TSAI approved
