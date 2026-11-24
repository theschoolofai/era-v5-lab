# ERA V5 Lab: Gate 4 update

**Date:** 28 Nov 2026
**Period:** 22 Nov to 28 Nov 2026

At this gate, TSAI reviewed the second dry run and decided whether the main training run starts. Each decision uses
the words that TSAI approved.

## The second dry run

A dry run is a short test of the whole training setup before the main training run.

[text: waiting for the result of the second dry run]

## The model card

Release wrote the first draft of the model card, and TSAI approved it on 24 Nov. It has the Data B part of the
training data section, and text from Release for the overview, the contributors and where to find more. The other sections wait for their owner teams.
The KE2 section now covers the KE2 output head, which TSAI chose at Gate 3 in place of the dense untied head.
Architecture added this head to the training code on 24 Nov.

## Decisions

| Decision | Team that proposed it | Decision text |
|---|---|---|
| The second dry run | Architecture, Infrastructure | [waiting for TSAI] |
| The main training run | Architecture, Infrastructure | Go or no-go: [waiting for TSAI] |
| The launch announcement | Release | TSAI approved the draft of the launch announcement on 24 Nov. The date and the link to the public dashboard come before it is published. |
| The learning rate for the Muon optimizer | Architecture | TSAI set the learning rate for the Muon optimizer to 0.006. The second dry run uses this rate. |

Short forms: KE2 is the lab team that tests its embedding method on the lab's tokenizer. The output head is the last
part of the model, which scores each token as the next token. A dense untied head is the standard output head.

## Next

[waiting for TSAI]

---

## Review record (remove this section before publishing)

This record is public, like the rest of the pull request. Put only public facts in it: yes or no, and links to
public pull requests. Never link to the CAP chat. Chat links are internal.

How to fill it:

1. Infrastructure sends the summary of the second dry run, or names the pull request that has it.
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
| The second dry run | Architecture, Infrastructure | Job request: [#720](https://github.com/theschoolofai/era-v5-lab/pull/720). Result: [link: waiting for the dry run 2 result] | no | no |
| The first draft of the model card | Release, Data B | `model_card/model_card_v0.md`, [#759](https://github.com/theschoolofai/era-v5-lab/pull/759), approved and merged by TSAI on 24 Nov. Owner and status of each section: `model_card/model_card_outline.md` | yes | Release: yes; Data B: yes ([comment on #759](https://github.com/theschoolofai/era-v5-lab/pull/759#issuecomment-7108567909)) |
| The KE2 output head in the model card | KE2 | TSAI decision in `teams/04-ke2/gate3.md`, merged in [#694](https://github.com/theschoolofai/era-v5-lab/pull/694), corrected in [#702](https://github.com/theschoolofai/era-v5-lab/pull/702). Gate 3 update: [#701](https://github.com/theschoolofai/era-v5-lab/pull/701). Model card outline: [#704](https://github.com/theschoolofai/era-v5-lab/pull/704) | yes | no |
| The KE2 output head in the training code | Architecture | [#717](https://github.com/theschoolofai/era-v5-lab/pull/717), merged by TSAI on 24 Nov. The Gate 3 update said that Architecture adds the head to the training code | yes | Architecture: no |
| Decision: the second dry run | Architecture, Infrastructure | TSAI decision at Gate 4 | no | no |
| Decision: the main training run | Architecture, Infrastructure | TSAI decision at Gate 4 | no | no |
| Decision: the launch announcement | Release | `launch/launch_announcement_v0.md`, [#600](https://github.com/theschoolofai/era-v5-lab/pull/600), [#603](https://github.com/theschoolofai/era-v5-lab/pull/603). Week 4 draft: [#753](https://github.com/theschoolofai/era-v5-lab/pull/753), approved and merged by TSAI on 24 Nov | yes | Release: yes |
| Open from Gate 3: the evaluation schedule | Evaluation | [#662](https://github.com/theschoolofai/era-v5-lab/pull/662) | no | no |
| Open from Gate 3: the tuning method after the main training | Post-training | [#524](https://github.com/theschoolofai/era-v5-lab/pull/524), [#593](https://github.com/theschoolofai/era-v5-lab/pull/593), [#634](https://github.com/theschoolofai/era-v5-lab/pull/634) | no | no |
| Open from Gate 3: serving and quantization | Quantization | [#538](https://github.com/theschoolofai/era-v5-lab/pull/538) | no | no |
| Decision: the learning rate for the Muon optimizer (open from Gate 3) | Architecture | `updates/gate3.md` (the learning rate). Decided: TSAI's correction in [#725](https://github.com/theschoolofai/era-v5-lab/pull/725), which sets the rate in config v1 and in the second dry run | yes | no |
| Open from Gate 3: the exact model size | Architecture | `updates/gate3.md` (model layout and size) | no | no |

- [ ] `check_style.py` gives 0 errors
- [ ] Every number in the text has TSAI approval
- [ ] The text names teams only, and no person
- [ ] Nothing from the internal list in `public_internal.md`
- [ ] No `waiting for` placeholder left in the text
- [ ] A team member commented on this pull request
- [ ] TSAI approved on: <DD Mon YYYY>
- [ ] Merged after TSAI approved
