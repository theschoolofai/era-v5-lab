# Router balance (design task 4): approach

**Brief item (Team 5, design task 4):** "Look at expert load per layer in the dry run 2 record (metrics.jsonl, expert_load every 50 steps; the config has loss-free balancing with bias_gamma 0.001). ... Is balancing working? Test: bias step size, warm-up, a window with probabilistic routing after growth, and a small auxiliary term. Report the evenness percentage per layer over time. A chart where one expert takes 5 times the even share is a failed router."
**Owner:** Deepjyoti Saha. **Works with:** design task 3 (growth path), which needs the router setting after experts are added.

## What it delivers

1. Evenness per layer over dry run 2, as charts and a table, from #869's `metrics.jsonl`.
2. A check of the idle-expert issue in #875.
3. Small tests of the fixes TSAI lists, 2 seeds each, and a recommended setting for the main run.

## What dry run 2 already shows

From `harness/run_report.py` (#829) on #869's `metrics.jsonl` (16 routed experts plus 1 shared, top-2; a share is an expert's part of all the layer's expert choices, each token making 2, so the even share is 6.25%):

- At step 1,200 the busiest expert takes 8.7% to 15.5% of a layer's choices; the worst layer is 2.48 times the mean; layers 3 and 7 each have one expert with zero tokens.
- Early in the run it is far worse: at step 50 one expert takes 50.0% of a layer's choices (it is picked by every token, 8 times the even share) and all 8 layers have an expert with zero tokens; the worst layer is above 5 times the even share (31.25%) at every recorded step up to step 300 (38.3% at steps 250 and 300) and first gets back under it at step 350 (31.1%). From step 400 every layer stays under 22%.
- TSAI's balanced reference (24 Nov, router on Muon) was 7.3% to 9.0% busiest share, 1.44 times the mean.

So, on this run, balancing is not working well enough: it fails TSAI's 5-times line for the first 300 steps, and some experts stay unused at the end.

## Reproduce the dry run 2 figures

```
python teams/05-architecture/harness/run_report.py teams/05-architecture/results/dryrun2-1234/metrics.jsonl
```

`teams/05-architecture/results/dryrun2-1234/metrics.jsonl` is #869's record on main. The full output (health, loss, learning rate, throughput and row fill, held-out bits per byte per slice, and expert load per layer) is in [`dryrun2_report.md`](dryrun2_report.md). The expert-load part:

| Step | Worst layer's busiest share | Layers with an expert at zero choices |
|---:|---:|---:|
| 50 | 50.0% | 8 |
| 100 | 47.7% | 5 |
| 150 | 45.4% | 1 |
| 200 | 41.3% | 1 |
| 250 | 38.3% | 1 |
| 300 | 38.3% | 0 |
| 350 | 31.1% | 0 |
| 400 | 17.8% | 0 |
| 1,200 | 15.5% | 2 |

## How balancing works today (`harness/week2/model.py`, `MoE`)

- The router's softmax scores pick the top 2 experts. With `bias_gamma` set, a per-expert `router_bias` is added to the scores **only to choose** the experts; the gate values stay the unbiased softmax.
- After each optimizer step, `apply_balance_update` moves each expert's bias by `gamma` towards balance: `bias += gamma * sign(mean_load - load)`. With gamma 0.001, an expert's bias can move at most 0.001 per step.
- Expert load counts only real (non-padding) tokens.

## Approach

1. **Evenness, defined.** Per layer and recorded step: busiest share, busiest divided by mean, coefficient of variation, number of experts with zero tokens, and one headline figure, evenness = even share / busiest share (100% is perfectly even; TSAI's failure line, 5 times the even share, is 20%).
2. **Charts from dry run 2.** One line per layer over the run, and a heat map of each expert's share by step. Added to `run_report.py` as a `--charts` option so anyone can reproduce them from a `metrics.jsonl`.
3. **The #875 check.** #875 adds a failing test: an expert that receives no tokens gets an all-zero gradient, not `None`, so Muon's skip check does not fire and the expert keeps moving on its momentum. Measure on a small CPU model whether idle experts drift, and whether it can keep an expert idle. The fix (skip all-zero expert slices) touches `optim.py`, which TSAI is changing for the new Muon rule, so it goes to TSAI as a finding first.
4. **Fix tests.** A small MoE (49M to 100M parameters, 16 experts, top-2), a fixed token budget, the same data order, 2 seeds. One change per arm:

   | Arm | Change |
   |---|---|
   | base | as dry run 2: gamma 0.001 |
   | gamma low / high | gamma 0.0001 and 0.01 |
   | warm-up | bias updates start, or ramp up, after the first N steps |
   | probabilistic window | experts sampled from the softmax for a short window (also the setting after growth) |
   | auxiliary term | a small load-balancing loss added to the training loss |
   | #875 fix | idle-expert slices skipped by Muon |

   For each arm: evenness per layer over time, held-out bits per byte, tokens per second, peak memory.
5. **Recommendation.** The setting for the main run, its cost in bits per byte and speed, and the setting to use for a short window after experts are added (shared with design task 3).

## Checks

- The dry run 2 figures above are reproduced by one command (below); its full output is in `dryrun2_report.md`.
- Every arm reports the same four measures on the same held-out bytes, with 2 seeds.
- **Pass rule.** Dry run 2 fails only early, so early steps count. A setting passes only if, in every layer, the busiest expert stays under 31.25% (above the 20% evenness line) at **every** recorded step from the first one; no expert has zero choices after step 200; held-out bits per byte are no worse than the base by more than the seed spread; and real tokens per second are within 5% of the base. Dry run 2 itself fails the first condition (steps 50 to 300).

## What it needs from others

A GPU for the fix tests (49M to 100M runs). Design task 3 for the after-growth window.

## What it cannot tell

Router behaviour at the main-run size, depth and data mix; dry run 2 also trained on one English shard only, which may itself narrow which experts are used.

## Plan and dates

| Step | What | By |
|---|---|---|
| 1 | Evenness charts and table from dry run 2 | Sun 29 Nov |
| 2 | #875 check | Mon 30 Nov |
| 3 | Fix tests (GPU), 2 seeds | Tue 1 Dec |
| 4 | Results and recommendation | Wed 2 Dec, 07:00 |
