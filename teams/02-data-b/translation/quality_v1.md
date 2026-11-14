# Translation rating: quality (v1, updated 14 Nov 2026)

Part of #216. The mean rating of each language's translated text (`sangraha-s`), from 1 to 5 on TSAI's rubric. A
document rated by two readers counts once, with the mean of its two scores. Made with `translation/score_ratings.py`.

Sheets used (14 Nov, 09:50 IST):
- Kannada (#402): `kn_keshavamurali.csv` (#419) and `kn_subramanyanaik.csv` (#425), both merged.
- Tamil (#403): `ta_Dharshanthaigu.csv` (#432) and `ta_truesrini.csv` (#438).
- Telugu (#404): `te_shankarpandala.csv` (#429). The second reader's sheet is not in yet.
- Hindi (#401): no sheets yet.

This file is updated when more sheets come in.

## Result

| Language | Readers | Documents rated | Mean score |
|---|---|---|---|
| kn | 2 | 50 | 3.31 |
| ta | 2 | 50 | 3.21 |
| te | 1 | 38 | 2.37 |

## What this means for the proposal on #216
Translated text counts for a language only with a mean of 3.5 or more and a passing agreement check
(`agreement_v1.md`). On 14 Nov no language meets both: Kannada is under 3.5 and fails agreement, Tamil passes agreement
but is under 3.5, Telugu has one reader, and Hindi has no ratings. So translated text is 0% in every language for now.
