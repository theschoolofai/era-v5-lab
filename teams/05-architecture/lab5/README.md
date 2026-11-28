# Team 5, Lab 5: approach notes (Deepjyoti Saha)

TSAI's Lab 5 brief for Team 5 (28 Nov 2026) is due **Wed 2 Dec, 07:00 IST**, with 70% by day 3 (Mon 30 Nov). These notes say how I plan to do the four pieces I took in 05 Architecture. They are written before the work so that the team can comment early. Each note says what it delivers, the approach, the checks, what it needs from other teams, and what it cannot tell us. Each note opens as its own draft PR, and that task's code is added to the same PR, so the plan and the evidence stay together. The recipe and gates note opens only if that work is confirmed as mine.

| Note | Brief item | Delivers | GPU |
|---|---|---|---|
| [packed_rows/](packed_rows/README.md) | Tasks: "Confirm the packed-row format with document mask ... Match Team 6's loader." | Format spec, loader switch, document mask, tests | No |
| [sequence_length/](sequence_length/README.md) | Tasks: "Write a sequence-length strategy ... review published methods that speed up pre-training" | Stage plan and a speed-up review | Optional |
| [router_balance/](router_balance/README.md) | Design task 4: "Router balance ... Is balancing working?" | Evenness charts from dry run 2, fix tests, recommendation | Yes, for the tests |
| [recipe_and_gates/](recipe_and_gates/README.md) | Lead additions 10 and 12, only if no one else takes them | Training recipe, router and throughput gates | Yes, for the tests |

Other Lab 5 pieces claimed in 05 Architecture on 28 Nov: design tasks 1 and 2 (study table and the two designs), design task 3 (growth path) and design task 7 (speed profile). Where my notes depend on them, they say so.

## Rules these notes follow (from the brief)

- Every number comes with the command or file that produced it.
- Small experiments: 49M to 100M parameters, a fixed token budget, the same data order, at least 2 seeds, one change at a time; report bits per byte on the same held-out bytes, tokens per second and peak memory.
- Negative results are written down. Each note says what a small test cannot tell.
- Builds go to TSAI as PRs with evidence; TSAI checks them against the shared formats.
