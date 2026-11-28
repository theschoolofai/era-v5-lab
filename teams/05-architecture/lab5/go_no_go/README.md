# Lab 5, lead addition 12: go / no-go gates for the main run

**Status:** draft. Every gate and threshold here is a proposal; none is approved. TSAI sets the gates.
**Scope:** the gate sheet and one checker. It does not change the trainer, `config_v1.yaml` or the finished dry run.
The token budget stays empty until the corpus-v1 token count is posted.
**Split with #893:** the router-evenness and tokens-per-second thresholds come from #892/#893 (router balance and
recipe owner). This folder reads them; when `run_report.py --gates` lands, the checker can call it instead.

## The gates

The brief: "Write the numbers that must hold before the main run starts: loss against the scaling-law prediction at 1B
tokens, resume test pass, router evenness, evaluation pass, tokens per second." Every threshold and its source is in
`gates_v1.yaml`.

| Gate | Passes when | Input | Source of the number | Status |
|---|---|---|---|---|
| Run health | no NaN or inf loss or gradient norm | `metrics.jsonl` | run_report.py (#829) | proposal |
| Loss vs scaling-law prediction at 1B tokens | mean held-out bpb of the evals between 0.8B and 1.2B real tokens (at least 3) is at most the prediction plus max(2 × the fit's held-out error, 2 × the sd of those evals) | `metrics.jsonl` + `fit.json` | lead addition 9 fit, `bpb = E + A/N_active^α + B/D^β` | proposal; no fit yet (#946) |
| Resume test | Team 7's kill-and-restart on the main-run config passes bit-equal with equal batch ids, on Muon | Team 7 `result.json` or `detail.json` | Team 7 restart_test / restore_test (queue rules R7, R8); #899, #945 | proposal; no main-config run yet |
| Router evenness | every layer, every recorded step: busiest expert under 5 × the even share (31.25% at 16 experts); no zero-token expert after step 200 | `expert_load` in `metrics.jsonl` | brief design task 4 (the 5× line); #892 (the idle rule) | proposal; numbers owned by #892 |
| Evaluation pass | the step-0 checkpoint scores inside each Tier A task's chance band or one-letter range, with every item scored | `eval_mini_v1.json` | Team 9 `eval_schedule.md` 5.2 (D2) | proposal: Team 9's D2, not approved on main |
| Tokens per second | real (scored) tokens/s ≥ token budget / (time budget × 0.9) | `metrics.jsonl` | brief "measure the rate before you scale" | proposal; budgets empty until posted |
| Team 9 holds (#931) | Team 9 says go on early quality (held-out bpb by group against the matched baseline) and on watcher integrity and lag (Tier A age under 30 minutes) | Team 9 verdict file | #931; Team 9 owns the thresholds, the bpb tolerance to be agreed with Team 5 | proposal; this sheet only reads the verdict |

Why these choices:

- **Bits per byte, not training loss.** Held-out bpb on the same bytes is the number every run reports and the one the
  fit will be made in. The training loss depends on the batch mix.
- **A window, not one eval.** Dry run 2's held-out bpb moved by about 0.1 between evals (TSAI's note), so one eval at
  1B tokens could pass or fail by chance. The tolerance also widens when the evals in the window are noisy, so a noisy
  run is not failed on noise, and the sd is shown so the noise itself is visible.
- **Only "worse than predicted" fails.** A run that beats the prediction passes. The gap is printed either way.
- **Real tokens, not positions.** The trainer's `tokens_per_second` counts padding. Dry run 2's row fill was 41.8%,
  so the padded rate overstates the real rate by about 2.4×.
- **PENDING is a no-go.** A gate with no evidence does not pass.
- **Team 9's holds are read, not redefined.** #931 proposes holds on held-out bpb and on watcher lag; the thresholds
  are Team 9's, so the sheet takes Team 9's go or hold as one gate instead of copying numbers that are not agreed yet.

## Dry run 2 through the checker

```
python3 teams/05-architecture/lab5/go_no_go/check_gates.py --run teams/05-architecture/results/dryrun2-1234
```

Gates for `teams/05-architecture/results/dryrun2-1234`: **NO-GO**

| Gate | Result | Detail |
|---|---|---|
| Run health | PASS | 1221 training steps, all finite |
| Loss vs scaling-law prediction at 1B tokens | PENDING | no scaling-law fit yet (lead addition 9); the run has seen 8,365,665 real tokens |
| Resume test (Team 7) | PENDING | no Team 7 restart or restore result on the main-run config yet |
| Router evenness | FAIL | worst busiest expert 8.00x the even share (step 50, layer 5); line 5x = 31.25% at 16 experts; over the line at 24 layer-steps, steps 50 to 300; an expert with zero tokens after step 200 at 33 layer-steps (first: step 250, layer 7) |
| Evaluation pass at step 0 (Team 9) | PENDING | no eval_mini_v1 scores for the main run's step-0 checkpoint yet |
| Tokens per second | PENDING | measured 2,299 real tokens/s (row fill 41.8%); the token budget and the time budget are not set, so there is no floor yet |
| Team 9 holds: early quality, watcher lag (#931) | PENDING | no Team 9 verdict yet on early quality and watcher lag (#931) |

Read with TSAI's notes on dry run 2: one seed, and one English web shard, not the sample-v0 mix. Dry run 2 was not
meant to pass these gates. The run shows the checker on a real record:

- The router result agrees with the #892 report on the same file: 8 × the even share (50%) at step 50, over the
  5 × line until step 300, and experts with zero tokens late in the run.
- The tokens-per-second figure agrees with #892: 2,299 real tokens/s at 41.8% row fill.

## Tests

`python3 -m pytest -q teams/05-architecture/lab5/go_no_go/`: 31 tests. Each gate on small synthetic records
(pass, fail, pending), the prediction formula, that every gate is marked a proposal and the budgets stay empty,
and the dry run 2 record end to end.

## What is still open

1. **The fit** (lead addition 9). The loss gate needs `E, A, α, B, β`, the main model's active parameters and the
   fit's held-out error, in a `fit.json`.
2. **The token budget and the time budget.** They stay empty until posted. The corpus-v1 token count and TSAI's wall-clock budget set the
   tokens-per-second floor. With them: `--token-budget <tokens> --wall-hours <h>`. The 10% idle allowance (evals,
   saves, restarts) is an assumption to agree with Team 7.
3. **The final router numbers** from #892's tests.
4. **The main-run checkpoint's step-0 scores** from Team 9's watcher, and Team 7's restart test on the main-run config.
5. **Team 9's verdicts** on its two #931 holds, and the bpb tolerance for early quality agreed between Teams 5 and 9.

## What this cannot tell

A run that passes all seven gates at 1B tokens can still diverge later, and the gates say nothing about the data mix.
The loss gate is only as good as the fit; with a large held-out error it becomes loose.
