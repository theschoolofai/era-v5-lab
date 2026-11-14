# ERA V5 Lab: Gate 3 update

**Date:** 21 Nov 2026
**Period:** 15 Nov to 21 Nov 2026

At this gate, TSAI reviewed the first dry run, the first data shards and the public text for the dashboard. Each
decision uses the words that TSAI approved.

## The first dry run

A dry run is a short test of the whole training setup before the main training run.

[Text from Infrastructure, based on the summary of the first dry run. Facts only. No numbers without TSAI approval.]

## The first data shards

A shard is a file that holds cleaned text as token IDs, ready for training. Data A set the format of the shards.
Each shard keeps whole documents and marks the end of each one. Each shard comes with a manifest and a quality
report, so the lab can check it. Data A wrote a first sample shard, from code in the Go programming language, with the frozen tokenizer
([#358](https://github.com/theschoolofai/era-v5-lab/pull/358), [#373](https://github.com/theschoolofai/era-v5-lab/pull/373)).

[Data A: confirm the text above or change it, and add the first full shards if they exist by Fri 20 Nov.]

## Decisions

| Decision | Team that proposed it | Decision text |
|---|---|---|
| Bit widths for the smaller versions of the model | Quantization | [waiting for TSAI] |
| Share of Indic text in its own script, and the limit on Indic text in Latin script | Data B | [waiting for TSAI] |

## Next

[One sentence about the next steps. No dates or results without TSAI approval.]

---

## Review record (remove this section before publishing)

This record is public, like the rest of the pull request. Put only public facts in it: yes or no, and links to
public pull requests. Never link to the CAP chat. Chat links are internal.

How to fill it:

1. Infrastructure sends the summary of the first dry run. Data A sends the text about the first shards.
2. Paste each text above. Edit it only for style, and send the edit back to the writer.
3. After TSAI decides, write each decision in the words that TSAI approves. Remove a row if TSAI does not decide it
   at this gate, and add a row for each other decision that TSAI makes.
4. The lead of each team gives an OK on the text about their team.
5. Write `[number: waiting for TSAI]` for any number that TSAI has not approved yet.
6. Run `python teams/11-release/style/check_style.py <this file> --numbers` and clear every error.
7. TSAI approves this pull request before the G11 lead merges it.

| Part | Team | Source | Text received | Lead OK |
|---|---|---|---|---|
| The first dry run | Infrastructure | | no | no |
| The first data shards | Data A | [#358](https://github.com/theschoolofai/era-v5-lab/pull/358), [#373](https://github.com/theschoolofai/era-v5-lab/pull/373) | draft by Release, waiting for Data A | no |
| Bit widths (moved from Gate 2) | Quantization | [#221](https://github.com/theschoolofai/era-v5-lab/pull/221) | no | no |
| Indic share (rerun of #400 with C3, from Gate 2) | Data B | [#400](https://github.com/theschoolofai/era-v5-lab/pull/400) | no | no |

- [ ] `check_style.py` gives 0 errors
- [ ] Every number in the text has TSAI approval
- [ ] The text names teams only, and no person
- [ ] Nothing from the internal list in `public_internal.md`
- [ ] No `[waiting for TSAI]` left in the text
- [ ] A team member commented on this pull request
- [ ] TSAI approved on: [DD Mon YYYY]
- [ ] Merged after TSAI approved
