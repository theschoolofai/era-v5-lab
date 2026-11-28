# Training recipe (lead addition 10) and two go/no-go gates (lead addition 12): approach

**Status:** approach note, open to collaborators. Anyone who wants to work on lead addition 10 or 12 can reply in 05 Architecture or on this PR; we align on who does which part, and each person submits their part in their own PR.
**Owner of this note:** Deepjyoti Saha. **Builds on:** the week-4 recipe (#713) and the router work (router_balance/).

## What it delivers

1. **Recipe.** The learning-rate schedule (warm-up, stable, decay), the batch size and its critical value, how the learning rate is reset after each growth stage, guards against loss spikes (QK-norm, z-loss, gradient clipping), and averaging the last checkpoints. Two of these tested at about 100M parameters.
2. **Two gates for the main run.** Pass levels for router evenness and for tokens per second, checked automatically from a run's `metrics.jsonl` by `run_report.py --gates`.

## Starting point

- #713 set the WSD schedule (5% warm-up, flat, 10% linear decay to zero) and added head SGD and TST as switches, off by default.
- TSAI's Lab 5 optimizer rule: Muon on every 2D matrix, including the embedding projection, the head matrices and the router; AdamW only on 1D parameters; no weight decay on Muon. The recipe follows it.
- Dry run 2 (#869): 18.2% of steps were clipped; the largest gradient norm before clipping was 26.9, with most steps between 1 and 2 (`run_report.py`).

## Approach

1. **Recipe draft** from #713, dry run 2's curves and the brief. The learning-rate reset after growth is agreed with design task 3.
2. **Two tests at about 100M**, 2 seeds each, for example z-loss on against off, and averaging the last checkpoints against the final one.
3. **Gates.** Router evenness: every layer stays above the line chosen in router_balance/ throughout the run. Tokens per second: a floor from dry run 2's measured rate scaled to the main-run model, agreed with Team 6. Implemented as `--gates`, printing pass or fail per gate.

## What it cannot tell

The recipe's behaviour at the main-run size; the tests at 100M only rank options.

## Plan and dates

| Step | What | By |
|---|---|---|
| 1 | Approach note shared with the team (this PR) | Sat 28 Nov |
| 2 | Recipe draft and gate thresholds | Mon 30 Nov |
| 3 | Two tests (GPU) | Tue 1 Dec |
| 4 | Final note and `--gates` | Wed 2 Dec, 07:00 |
