mkdir -p ~/era-v5-lab/teams/10-post-training/indic
cat > ~/era-v5-lab/teams/10-post-training/indic/indic_prompts_s18.md << 'EOF'
# S18 — Indic Prompts with Checkable Answers (v0 draft)

Owner: Ranjani (G10 post-training)
Status: draft — TBDs where waiting on inputs
Last updated: 28 Nov 2026

## Table

| Source | Language(s) | Size | Answer type | Checker | Licence | Gap |
|---|---|---|---|---|---|---|
| Tamil templates (#861) | Tamil | TBD | TBD | Follows #149 pattern (to confirm) | TBD | Confirm answers are exact-match checkable |
| Team 2 Indic pools | te, kn, bn, mr, gu, ml, or, pa | TBD (waiting) | TBD | TBD | TBD | Awaiting Team 2 reply |
| Team 1 Indic share | TBD | TBD | TBD | TBD | TBD | Awaiting Team 1 reply |

## What's missing

- Per-source prompt sizes (all TBD)
- Answer types not locked for non-math Indic sources
- Checker for non-math Indic answers not yet designed (only #149 math pattern exists)
- Licence status unrecorded for each new source
- Confirmation that #861 Tamil template answers are exact-match checkable
- Coverage for the 8 missing Indic RL languages: te, kn, bn, mr, gu, ml, or, pa

## Licence rows

| Source | Licence | NC/ND/unstated | Generator model + terms | Recorded by |
|---|---|---|---|---|
| Tamil templates (#861) | TBD | TBD | TBD | Ranjani |
| Team 2 Indic pools | TBD | TBD | TBD | Ranjani |

Rule: NC, ND and unstated are allowed — record them, do not exclude.
For post-training data, record the generator model and its licence terms (Team 11 needs both).

## Open questions to Sai Teja

1. Team 3 confirmed special-token file (`special_tokens.md` + tokenizer hash)
2. Path/format where Teams 1 & 2 parquet + `pack_table` rows land
3. Is #861 the Indic anchor, or another set?
4. Is the 8-missing-Indic-languages gap mine to track?
