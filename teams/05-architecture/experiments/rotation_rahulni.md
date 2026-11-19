# Rotation: exp3-experts-32 at seed 1243

`rahulni` (Team 09). Week 3 rotation into Team 05.

**Assignment.** Run the T2 arm `exp3-experts-32` (`configs/arms/exp3_experts_32.yaml`, 32 routed experts in place of 16) again at a new seed, 1243. Report its bits per byte next to the seeds already run. The job request is pull request 466 (`jobs/2026-11-14-rotation-experts32-seed1243.md`), approved by the lead and TSAI and merged on 16 Nov 2026. As Team 05 set out, one new seed names no winner and does not change config v1. The T2 reference was not run again.

**Status: result pending.** TSAI has not posted the result of pull request 466 yet. It was asked for on pull request 466 and in the Team 05 group on 19 Nov 2026. This file states the R2 rule now, so the verdict follows from the number alone. The number goes in the same day it comes.

## R1: the run

| Held-out bits per byte at step 1,221 | exp3-experts-32, seed 1243 |
|---|---|
| Steps finished | pending (of 1,221) |
| val/bpb (whole held-out file) | pending |
| English | pending |
| Code | pending |
| Indic (mean of slices) | pending |

Lower is better. The run is pinned to trainer `71bc0fb` with `runtime_fast.yaml` and the TSAI speed fixes, the same setup as the week 2 T2 runs.

## R2: does it hold?

The T2 reference (16 routed experts) at four seeds, from the TSAI comment on pull request 462 of 15 Nov 2026 (the same numbers as `rotation_pradeep-kumar-gs.md`):

| | Seed 1234 | Seed 1235 | Seed 1236 | Seed 1237 | Mean | Range (high − low) | SD |
|---|---|---|---|---|---|---|---|
| T2 reference, val/bpb | 1.7673 | 1.7796 | 1.7792 | 1.7542 | 1.7701 | 0.0254 | 0.0120 |

The SD is the sample standard deviation of the four reference seeds.

**The rule, fixed before the result:**

- **The result holds** if seed 1243 lies inside the reference's own seed range, 1.7542 to 1.7796. Then 32 experts cannot be told apart from 16 at this size on one seed, which is TSAI's week 2 reading ("The expert count (8, 16 or 32) and the shared expert make no measurable difference at this size").
- **If it lies outside**, this file gives how far outside, and the gap to the reference mean against the SD.
- Either way, one seed names no winner, and config v1 is unchanged.

**Verdict:** pending the TSAI result.

## Limits

- **No per-seed values of the arm itself.** The TSAI T2 table of 13 Nov gives exp3-experts-32 at 2 seeds as a mean (1.7716) only. Until the seed values are posted, the only spread is the reference's, and the comparison crosses seeds and arms.
- **Same seed, different data order.** The seed also drives the training batch sampler, so seed 1243 trains on a different order of windows from the reference seeds. The held-out set is the same.
- **Old tokenizer.** This run uses trainer `71bc0fb` and tokenizer v0, like the week 2 EXP-3 runs. The week 3 p1536 numbers (dry run 1, pull request 475) use a different tokenizer and must not be compared with it.

## Evidence

- Job request and CPU smoke log: `jobs/2026-11-14-rotation-experts32-seed1243.md` and `jobs/evidence/2026-11-14-rotation-experts32-seed1243/` (pull request 466).
- Reference numbers: the TSAI comment on pull request 462, 15 Nov 2026.
- Result: pending, expected as a TSAI comment on pull request 466.
