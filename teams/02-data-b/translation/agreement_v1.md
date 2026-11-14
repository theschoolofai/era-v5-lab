# Translation rating: agreement (v1, updated 14 Nov 2026)

Part of #216. Two native readers rate the same translated documents from the #212 review pack, each on their own,
from 1 to 5 on TSAI's rubric. A language passes when both readers rated at least 20 of the same documents and their
scores are within 1 point on 80% or more of them (TSAI, G2, 31 Oct). Made with `translation/score_ratings.py`.

Sheets used (14 Nov, 09:50 IST):
- Kannada (#402): `kn_keshavamurali.csv` (#419) and `kn_subramanyanaik.csv` (#425), both merged.
- Tamil (#403): `ta_Dharshanthaigu.csv` (#432) and `ta_truesrini.csv` (#438).
- Telugu (#404): `te_shankarpandala.csv` (#429). The second reader's sheet is not in yet.
- Hindi (#401): no sheets yet.

This file is updated when more sheets come in.

## Result

| Language | Readers | Shared documents | Within 1 point | Result |
|---|---|---|---|---|
| kn | keshavamurali, subramanyanaik | 25 | 19 (76%) | FAIL |
| ta | Dharshanthaigu, truesrini | 25 | 21 (84%) | PASS |

## Notes
- Kannada fails: 19 of 25 within 1 point (76%). The second sheet is lower on 21 of the 25 and never higher (means 3.60
  and 2.52), so the two readers differ by a steady offset, not at random.
- Tamil passes: 21 of 25 within 1 point (84%), and 8 are the same score. The gap is steady here too: the second sheet
  is higher on 17 of the 25 and never lower (means 2.72 and 3.56).
- Telugu and Hindi can't be checked until each has two sheets.
