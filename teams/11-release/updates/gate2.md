# ERA V5 Lab: Gate 2 update

**Date:** 14 Nov 2026
**Period:** 1 Nov to 14 Nov 2026

At this gate, TSAI reviewed the proposals from the teams below. Each decision uses the words that TSAI approved.

## Decisions

| Decision | Team that proposed it | Decision text |
|---|---|---|
| Freeze the tokenizer | Tokenizer | Freeze C3 (sample v0). It gives [number: waiting for TSAI] bits per byte against [number: waiting for TSAI] for the baseline tokenizer on the same test. eos is id [number: waiting for TSAI] ([#407](https://github.com/theschoolofai/era-v5-lab/pull/407)). After the freeze, token IDs stay fixed. TSAI approves each later fix. |
| KE2 | KE2 | Accept the KE2 validation of C3 ([#372](https://github.com/theschoolofai/era-v5-lab/pull/372)). Align the KE2 special-token map to eos id [number: waiting for TSAI]. |
| First model configuration: attention type, number of experts, optimizer and learning rate | Architecture | Muon optimizer. Keep the v0 attention. [number: waiting for TSAI] routed experts plus [number: waiting for TSAI] shared expert, top-[number: waiting for TSAI]. Learning rate [number: waiting for TSAI] stays provisional. |
| Share of Indic text in its own script, and the limit on Indic text in Latin script | Data B | Rerun [#400](https://github.com/theschoolofai/era-v5-lab/pull/400) with C3 this week. TSAI sets the share from that table. |
| Duplicate removal, source priority list and the updated data spec | Data A | One spec v1.1. Cleaner [#244](https://github.com/theschoolofai/era-v5-lab/pull/244) is merged and ran on sample v0. Run the [#255](https://github.com/theschoolofai/era-v5-lab/pull/255) dedup design on the cleaned sample. |
| Data mix for supervised fine-tuning | Post-training | [#391](https://github.com/theschoolofai/era-v5-lab/pull/391) is SFT mix v1. Week 3 adds strong SFT tests and a [method name: waiting for TSAI] study against full fine-tuning. |
| Bit widths for the smaller versions of the model | Quantization | No evidence yet. This decision moves to Gate 3. |

## Next

Next, the lab runs the first dry run and prepares the first data shards, and Release writes the public text for the dashboard.

---

## Review record (remove this section before publishing)

This record is public, like the rest of the pull request. Put only public facts in it: yes or no, and links to
public pull requests. Never link to the CAP chat. Chat links are internal.

How to fill it:

1. Each team sends its proposal by the time TSAI set. Add the public pull request of the proposal below.
2. After TSAI decides, write each decision in the words that TSAI approves.
3. The lead of each team gives an OK on the text about their decision.
4. Write `[number: waiting for TSAI]` for any number that TSAI has not approved yet.
5. Run `python teams/11-release/style/check_style.py <this file> --numbers` and clear every error.
6. TSAI approves this pull request before the G11 lead merges it.

| Team | Proposal pull request | Lead OK |
|---|---|---|
| Tokenizer | [#340](https://github.com/theschoolofai/era-v5-lab/pull/340) | no |
| KE2 | [#349](https://github.com/theschoolofai/era-v5-lab/pull/349) | no |
| Architecture | [#374](https://github.com/theschoolofai/era-v5-lab/pull/374) | no |
| Data B | [#327](https://github.com/theschoolofai/era-v5-lab/pull/327) | no |
| Data A | [#255](https://github.com/theschoolofai/era-v5-lab/pull/255), [#365](https://github.com/theschoolofai/era-v5-lab/pull/365) | no |
| Post-training | [#312](https://github.com/theschoolofai/era-v5-lab/pull/312), [#391](https://github.com/theschoolofai/era-v5-lab/pull/391) | no |
| Quantization | [#221](https://github.com/theschoolofai/era-v5-lab/pull/221) | no |

- [x] `check_style.py` gives 0 errors
- [ ] Every number in the text has TSAI approval
- [ ] The text names teams only, and no person
- [ ] Nothing from the internal list in `public_internal.md`
- [ ] No `[waiting for TSAI]` left in the text
- [ ] A team member commented on this pull request
- [ ] TSAI approved on: [DD Mon YYYY]
- [ ] Merged after TSAI approved
