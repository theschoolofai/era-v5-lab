# ERA V5 Lab: Gate 4 update

**Date:** 28 Nov 2026
**Period:** 22 Nov to 28 Nov 2026

At this gate, TSAI reviewed the second dry run and decided whether the main training run starts. Each decision uses
the words that TSAI approved.

## The second dry run

A dry run is a short test of the whole training setup before the main training run.

[text: waiting for the result of the second dry run]

## The model card

Each section of the model card outline has an owner team and a status. The KE2 section now covers the KE2 output
head, which TSAI chose at Gate 3 in place of the dense untied head.

## Decisions

| Decision | Team that proposed it | Decision text |
|---|---|---|
| The second dry run | Architecture, Infrastructure | [waiting for TSAI] |
| The main training run | Architecture, Infrastructure | Go or no-go: [waiting for TSAI] |
| The launch announcement | Release | [waiting for TSAI] |

Short forms: KE2 is the lab team that tests its embedding method on the lab's tokenizer. The output head is the last
part of the model, which scores each token as the next token. A dense untied head is a standard output head with its
own weights.

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
   at this gate, and add a row for each other decision that TSAI makes.
4. Give the source of each fact: a public pull request or a file in this repository. Gate 4 needs a source for each
   fact.
5. The lead of each team gives an OK on the text about their team.
6. Write `[number: waiting for TSAI]` for any number that TSAI has not approved yet.
7. Run `python teams/11-release/style/check_style.py <this file> --numbers` and clear every error.
8. TSAI approves this pull request before the G11 lead merges it.

| Fact | Team | Source | Text received | Lead OK |
|---|---|---|---|---|
| The second dry run | Architecture, Infrastructure | [link: waiting for the dry run 2 pull request] | no | no |
| Model card sections each have an owner and a status | Release | `model_card/model_card_outline.md` | yes | yes |
| The KE2 output head in the model card | KE2 | TSAI decision: [#691](https://github.com/theschoolofai/era-v5-lab/pull/691). Gate 3 update: [#701](https://github.com/theschoolofai/era-v5-lab/pull/701). Model card outline: [link: waiting for the pull request] | yes | no |
| Decision: the second dry run | Architecture, Infrastructure | TSAI decision at Gate 4 | no | no |
| Decision: the main training run | Architecture, Infrastructure | TSAI decision at Gate 4 | no | no |
| Decision: the launch announcement | Release | `launch/launch_announcement_v0.md`, [#600](https://github.com/theschoolofai/era-v5-lab/pull/600), [#603](https://github.com/theschoolofai/era-v5-lab/pull/603) | yes | no |

- [ ] `check_style.py` gives 0 errors
- [ ] Every number in the text has TSAI approval
- [ ] The text names teams only, and no person
- [ ] Nothing from the internal list in `public_internal.md`
- [ ] No `[waiting for TSAI]` left in the text
- [ ] A team member commented on this pull request
- [ ] TSAI approved on: <DD Mon YYYY>
- [ ] Merged after TSAI approved
