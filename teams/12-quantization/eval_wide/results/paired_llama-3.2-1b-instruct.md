Paired against **bf16** on the same items. Differences in points (format minus base); b = right in base, wrong in format; c = the reverse.

| Format | Task | n | Base | Format | Difference (95% CI) | b / c | McNemar p |
|---|---|---|---|---|---|---|---|
| Q4_K_M | mmlu | 14042 | 48.2 | 47.4 | -0.9 (-1.4 to -0.4) | 792 / 667 | 0.001 |
| Q4_K_M | arc_challenge | 1172 | 37.9 | 38.1 | +0.3 (-1.3 to +1.8) | 41 / 44 | 0.828 |
| Q4_K_M | belebele_hin_Deva | 900 | 34.0 | 32.7 | -1.3 (-3.4 to +0.7) | 50 / 38 | 0.241 |
| Q5_K_M | mmlu | 14042 | 48.2 | 47.5 | -0.8 (-1.2 to -0.3) | 527 / 420 | 0.001 |
| Q5_K_M | arc_challenge | 1172 | 37.9 | 37.6 | -0.3 (-1.4 to +0.9) | 26 / 23 | 0.775 |
| Q5_K_M | belebele_hin_Deva | 900 | 34.0 | 33.7 | -0.3 (-2.1 to +1.5) | 36 / 33 | 0.810 |
| Q6_K | mmlu | 14042 | 48.2 | 48.4 | +0.1 (-0.2 to +0.5) | 275 / 292 | 0.502 |
| Q6_K | arc_challenge | 1172 | 37.9 | 37.9 | +0.0 (-0.9 to +0.9) | 13 / 13 | 1.000 |
| Q6_K | belebele_hin_Deva | 900 | 34.0 | 32.7 | -1.3 (-2.6 to -0.0) | 24 / 12 | 0.065 |
| Q8_0 | mmlu | 14042 | 48.2 | 48.3 | +0.1 (-0.1 to +0.3) | 123 / 138 | 0.386 |
| Q8_0 | arc_challenge | 1172 | 37.9 | 38.1 | +0.2 (-0.5 to +0.9) | 8 / 10 | 0.815 |
| Q8_0 | belebele_hin_Deva | 900 | 34.0 | 34.2 | +0.2 (-0.8 to +1.2) | 9 / 11 | 0.824 |

Q5_K_M rows: scored with the guard's check 4 in warn mode (`EVAL_GUARD_CHECK4=warn`, #857; check 4 missed, checks 1 to 3 passed), so they are not in the ship table. Every other row was scored under the default guard.
