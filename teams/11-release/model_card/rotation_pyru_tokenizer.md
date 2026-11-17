# Rotation review: model card, Tokenizer row

**Date:** 17 Nov 2026

Week 3 rotation in the Release team. The Release lead wrote this review as cover, because no rotation pull request came for this row. This file reviews the Tokenizer row of `model_card_outline.md` (R1) and marks each claim that has no evidence (R2).

Checked against main at commit `8732384`.

The Tokenizer section has no text yet, so this review covers the current outline row and its evidence.

## R1: review of the Tokenizer row

The row says: "How the model splits text into pieces."
The owner team is Tokenizer. The status is empty. The Lead OK cell records an OK from the Tokenizer lead.

### What the evidence supports

- The lab trains with one frozen tokenizer, p1536, in place of C3 from Gate 2. The release is in `teams/03-tokenizer/release/README.md` ([#504](https://github.com/theschoolofai/era-v5-lab/pull/504)).
- TSAI used the same words in a [comment on #460](https://github.com/theschoolofai/era-v5-lab/pull/460#issuecomment-6909024067): the first shards use the frozen tokenizer p1536, not C3.
- The release folder explains how to download the tokenizer and check it with `verify_release.py`.
- The Tokenizer lead confirmed the row in a [comment on #384](https://github.com/theschoolofai/era-v5-lab/pull/384#issuecomment-6829903858).
- The status "empty" is correct. No Tokenizer section text is in `teams/11-release/model_card/`.

### What the evidence does not support yet

- **Token IDs.** `TOKENIZER_CARD.md` says the token IDs are identical to C3. The release README says every C3 ID keeps its token, except a set of IDs that now hold new Indic merges. The two files disagree.
- **Freeze date.** `TOKENIZER_CARD.md` says TSAI froze p1536 on 15 Nov 2026. The release README says 16 Nov 2026.
- **Scores per language.** The scores in section 5 of `TOKENIZER_CARD.md` are for C3, and its model-side scores are still marked TODO. The p1536 scores in the release README have no TSAI approval for public text.
- **Numbers.** The vocabulary size, the merges and the count of special tokens have no TSAI approval for public text.

### Suggestions for the owner team

1. Write the section from the release README, not from the C3 parts of the card.
2. Fix the two mismatches in `TOKENIZER_CARD.md`: the token IDs and the freeze date.
3. Write `[number: waiting for TSAI]` for every number that TSAI has not approved.
4. Agree with Data A and Data B on the Languages row, which Tokenizer also owns, so that no fact appears in two sections.

## R2: claims and evidence

| # | Claim | Evidence | Result |
|---|---|---|---|
| 1 | The owner team is Tokenizer | `model_card_outline.md` on main | has evidence |
| 2 | The status is empty | No Tokenizer section text is on main | has evidence |
| 3 | The Tokenizer lead confirmed the row | [Comment on #384](https://github.com/theschoolofai/era-v5-lab/pull/384#issuecomment-6829903858) | has evidence |
| 4 | The lab trains with the frozen tokenizer p1536, not C3 | [#504](https://github.com/theschoolofai/era-v5-lab/pull/504), `release/README.md`, [TSAI comment on #460](https://github.com/theschoolofai/era-v5-lab/pull/460#issuecomment-6909024067) | has evidence |
| 5 | Each token ID is the same as in C3 | The card says yes. The release README says a set of IDs changed | evidence conflicts |
| 6 | TSAI froze p1536 on a known date | The card and the release README give different dates | evidence conflicts |
| 7 | Scores per language for p1536 | The release README cites [#436](https://github.com/theschoolofai/era-v5-lab/pull/436). TSAI has not approved them for public text | no evidence for public text |
| 8 | Any number about the tokenizer | TSAI has approved none for public text | no evidence. Write `[number: waiting for TSAI]` |

## No evidence

- Claims 5 and 6: the Tokenizer team fixes the card or confirms the right text.
- Claim 7: evidence comes when TSAI approves the scores.
- Claim 8: evidence comes when TSAI approves each number.
