# ERA V5 Lab: Gate 4 update

**Date:** 28 Nov 2026
**Period:** 22 Nov to 28 Nov 2026

At this gate, TSAI reviewed the second dry run and decided whether the main training run starts. Each decision uses
the words that TSAI approved.

## The second dry run

A dry run is a short test of the whole training setup before the main training run.

The second dry run tests the training settings for the main run on a small model, including the KE2 output head. It
trains on the first 41 shards, which the lab made from a sample of its data with the frozen tokenizer p1536.
Evaluation checked these shards against the benchmark questions before the run. The dry run checks that the run
finishes all its planned steps, and that the loss stays a valid number. During the run,
Infrastructure stops it on purpose and restarts it from the last saved checkpoint. Evaluation scores each saved
checkpoint as the run goes, and checks that the first scores are near those of a random guess.

[text: waiting for the result of the second dry run]

## The model card

Release wrote the first draft of the model card, and TSAI approved it on 24 Nov. It now has the Data B part of the
training data section, and the Evaluation section, which names the benchmarks. Release wrote the overview, the
contributors and where to find more. The other sections wait for their owner teams. The outline now also has
sections on what the card does not claim, what is released, its sources and how to cite it.
The KE2 section now covers the KE2 output head, which TSAI chose at Gate 3 in place of the dense untied head.
Architecture added this head to the training code on 24 Nov.

## Gate 4 evidence from the teams

Each team showed its work for Gate 4 in public pull requests.

- **Tokenizer:** The frozen tokenizer p1536 turns the tokens in the training files back into the original text,
  with no change. Its files include the lab's chat format. A public link lets Evaluation download it without
  signing in. Tokenizer also gave Architecture the token counts of the training text, with their sources.
- **Data A:** [text: waiting for Data A]
- **Data B:** Data B measured every part of its Gate 3 summary of the Indian-language text. Cleaning lost none of
  the joiners, the invisible marks that some Indian scripts need. Native readers read samples in their own
  languages, and most of the damage that they found was in the raw text, before cleaning. Every Indian-language
  pack of corpus v1 has a check of its training files, or is marked as not covered. Data B's part of the training
  data section of the model card is on main.
- **KE2:** [text: waiting for KE2]
- **Architecture:** Architecture wrote the settings of the second dry run, and its job request is on main. The
  settings use the KE2 output head and the learning rate that TSAI set for the Muon optimizer. The exact size of the
  model is still open.
- **Performance:** [text: waiting for Performance]
- **Infrastructure:** [text: waiting for Infrastructure]
- **Monitoring:** [text: waiting for Monitoring]
- **Evaluation:** [text: waiting for Evaluation]
- **Post-training:** [text: waiting for Post-training]
- **Quantization:** [text: waiting for Quantization]

## Decisions

| Decision | Team that proposed it | Decision text |
|---|---|---|
| The second dry run | Architecture, Infrastructure | [waiting for TSAI] |
| The main training run | Architecture, Infrastructure | Go or no-go: [waiting for TSAI] |
| The launch announcement | Release | TSAI approved the draft of the launch announcement on 24 Nov. The date and the link to the public dashboard come before it is published. |
| The learning rate for the Muon optimizer | Architecture | TSAI set the learning rate for the Muon optimizer to 0.006, the current estimate. The second dry run uses this rate. |

Short forms: KE2 is the lab team that tests its embedding method on the lab's tokenizer. The output head is the last
part of the model, which scores each token as the next token. A dense untied head is the standard output head.

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
| The second dry run | Architecture, Infrastructure, Evaluation | Plan: job request [#720](https://github.com/theschoolofai/era-v5-lab/pull/720) (Architecture), with the KE2 output head in its settings ([#717](https://github.com/theschoolofai/era-v5-lab/pull/717)). The planned stop and restart: [#738](https://github.com/theschoolofai/era-v5-lab/pull/738) and [#743](https://github.com/theschoolofai/era-v5-lab/pull/743) (Infrastructure). The checkpoint scores: [#707](https://github.com/theschoolofai/era-v5-lab/pull/707) (Evaluation). The training text, the first 41 shards: the job on main, [#787](https://github.com/theschoolofai/era-v5-lab/pull/787); the check against the benchmark questions, [#641](https://github.com/theschoolofai/era-v5-lab/pull/641). TSAI set this text for the dry run on 24 Nov, in place of corpus v1 ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7159006781)). Result: [link: waiting for the dry run 2 result] | plan: yes, from the job requests. Result: no | Architecture: yes for the head and the learning rate ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7135446665)). The training text: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7161567538)). Infrastructure: no. Evaluation: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7134626582)) |
| The first draft of the model card | Release, Data B | `model_card/model_card_v0.md`, [#759](https://github.com/theschoolofai/era-v5-lab/pull/759), approved and merged by TSAI on 24 Nov. Evaluation section: [#770](https://github.com/theschoolofai/era-v5-lab/pull/770), [#784](https://github.com/theschoolofai/era-v5-lab/pull/784). Data B problems in the code-adjacent text, the overview and the KE2 section: [#782](https://github.com/theschoolofai/era-v5-lab/pull/782), [#791](https://github.com/theschoolofai/era-v5-lab/pull/791), merged by TSAI on 25 Nov. New sections of the outline: [#803](https://github.com/theschoolofai/era-v5-lab/pull/803), merged by TSAI on 25 Nov. Owner and status of each section: `model_card/model_card_outline.md` | yes | Release: yes; Data B: yes ([comment on #759](https://github.com/theschoolofai/era-v5-lab/pull/759#issuecomment-7108567909)); Evaluation: yes ([comment on #784](https://github.com/theschoolofai/era-v5-lab/pull/784#issuecomment-7129730898)) |
| The KE2 output head in the model card | KE2 | TSAI decision in `teams/04-ke2/gate3.md`, merged in [#694](https://github.com/theschoolofai/era-v5-lab/pull/694), corrected in [#702](https://github.com/theschoolofai/era-v5-lab/pull/702). Gate 3 update: [#701](https://github.com/theschoolofai/era-v5-lab/pull/701). Model card outline: [#704](https://github.com/theschoolofai/era-v5-lab/pull/704). The KE2 section of the model card: [#791](https://github.com/theschoolofai/era-v5-lab/pull/791), merged by TSAI on 25 Nov | yes | KE2: yes ([comment on #791](https://github.com/theschoolofai/era-v5-lab/pull/791#issuecomment-7142627011)) |
| The KE2 output head in the training code | Architecture | [#717](https://github.com/theschoolofai/era-v5-lab/pull/717), merged by TSAI on 24 Nov. The Gate 3 update said that Architecture adds the head to the training code | yes | Architecture: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7134663706)) |
| Decision: the second dry run | Architecture, Infrastructure | TSAI decision at Gate 4 | no | no |
| Decision: the main training run | Architecture, Infrastructure | TSAI decision at Gate 4 | no | no |
| Decision: the launch announcement | Release | `launch/launch_announcement_v0.md`, [#600](https://github.com/theschoolofai/era-v5-lab/pull/600), [#603](https://github.com/theschoolofai/era-v5-lab/pull/603). Week 4 draft: [#753](https://github.com/theschoolofai/era-v5-lab/pull/753), approved and merged by TSAI on 24 Nov. The KE2 head row of its review record: [#796](https://github.com/theschoolofai/era-v5-lab/pull/796), merged by TSAI on 25 Nov | yes | Release: yes |
| Open from Gate 3: the evaluation schedule | Evaluation | [#662](https://github.com/theschoolofai/era-v5-lab/pull/662). Version 1.2 of the schedule: [#722](https://github.com/theschoolofai/era-v5-lab/pull/722) | no | no |
| Open from Gate 3: the tuning method after the main training | Post-training | [#524](https://github.com/theschoolofai/era-v5-lab/pull/524), [#593](https://github.com/theschoolofai/era-v5-lab/pull/593), [#634](https://github.com/theschoolofai/era-v5-lab/pull/634) | no | no |
| Open from Gate 3: serving and quantization | Quantization | [#538](https://github.com/theschoolofai/era-v5-lab/pull/538) | no | no |
| Decision: the learning rate for the Muon optimizer (open from Gate 3) | Architecture | `updates/gate3.md` (the learning rate). Decided: TSAI's correction in [#725](https://github.com/theschoolofai/era-v5-lab/pull/725), which sets the rate in config v1 and in the second dry run | yes | Architecture: yes, 0.006 is the current estimate ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7135446665)) |
| Open from Gate 3: the exact model size | Architecture | `updates/gate3.md` (model layout and size) | no | no |
| Gate 4 evidence: Tokenizer | Tokenizer | Round trip on the p1536 shards: [#658](https://github.com/theschoolofai/era-v5-lab/pull/658). Chat format: [#642](https://github.com/theschoolofai/era-v5-lab/pull/642), [#686](https://github.com/theschoolofai/era-v5-lab/pull/686). Public download link: [#700](https://github.com/theschoolofai/era-v5-lab/pull/700). Token counts for Architecture: [#719](https://github.com/theschoolofai/era-v5-lab/pull/719). Links from the Tokenizer lead ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7139242515)) | yes | Tokenizer: no |
| Gate 4 evidence: Data B | Data B | Gate 3 summary of the Indian-language text, `teams/02-data-b/audit/gate3_indic.md`: [#526](https://github.com/theschoolofai/era-v5-lab/pull/526), [#783](https://github.com/theschoolofai/era-v5-lab/pull/783). Joiners: [#653](https://github.com/theschoolofai/era-v5-lab/pull/653). The cleaning problem in [issue #734](https://github.com/theschoolofai/era-v5-lab/issues/734), fixed on main by [#767](https://github.com/theschoolofai/era-v5-lab/pull/767). Language labels: [#673](https://github.com/theschoolofai/era-v5-lab/pull/673). The mix of the training text: [#723](https://github.com/theschoolofai/era-v5-lab/pull/723); [#794](https://github.com/theschoolofai/era-v5-lab/pull/794) is open. Model card text: [#525](https://github.com/theschoolofai/era-v5-lab/pull/525), [#782](https://github.com/theschoolofai/era-v5-lab/pull/782). Still open before Fri: [#788](https://github.com/theschoolofai/era-v5-lab/pull/788), [#806](https://github.com/theschoolofai/era-v5-lab/pull/806), [issue #795](https://github.com/theschoolofai/era-v5-lab/issues/795). Links from the Data B lead ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7155962319)) | yes | Data B: no |
| Gate 4 evidence: Architecture | Architecture | The job on main, `teams/05-architecture/jobs/2026-11-22-dryrun2.md`: [#787](https://github.com/theschoolofai/era-v5-lab/pull/787). The KE2 output head: [#717](https://github.com/theschoolofai/era-v5-lab/pull/717). The Muon learning rate: [#725](https://github.com/theschoolofai/era-v5-lab/pull/725). The router settings: [#736](https://github.com/theschoolofai/era-v5-lab/pull/736), [#748](https://github.com/theschoolofai/era-v5-lab/pull/748). A separate test with faster attention: [#804](https://github.com/theschoolofai/era-v5-lab/pull/804), open. The model size is still open. Links from the Architecture lead, with no result claimed ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7159006781)) | yes | Architecture: yes ([comment on #705](https://github.com/theschoolofai/era-v5-lab/pull/705#issuecomment-7161567538)) |

- [ ] `check_style.py` gives 0 errors
- [ ] Every number in the text has TSAI approval
- [ ] The text names teams only, and no person
- [ ] Nothing from the internal list in `public_internal.md`
- [ ] No `waiting for` placeholder left in the text
- [ ] A team member commented on this pull request
- [ ] TSAI approved on: <DD Mon YYYY>
- [ ] Merged after TSAI approved
