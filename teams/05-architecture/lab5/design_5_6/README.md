# Lab 5, design tasks 5, 5b, 6, and lead addition 9

Name: Shivanshu Thapliyal. GitHub: shivman. Team: 05 Architecture.

The production scale is the one TSAI sets. This note does not name one. `config_v1.yaml` is not edited. `data.seq_len` stays empty. The finished dry run is not edited.

Measured numbers are the ones in `residual_stream_result.json`, produced by the command below. Everything else in this note is not measured.

## Design task 5. Residual stream. Measured on a tiny net

The block on main is one stream. Pre-norm, then the sublayer is added back onto that same stream (`teams/05-architecture/harness/week2/model.py`, `Block.forward`).

The test arm keeps two streams and no new parameters. Attention writes one stream. The MoE writes the other. A fixed mean mixes them before the next layer and before the head. The arm is only in `residual_stream.py`. It is not in the trainer.

Command, from the repository root:

```
python teams/05-architecture/lab5/design_5_6/residual_stream.py
```

Checks:

```
python -m pytest teams/05-architecture/lab5/design_5_6/test_residual_stream.py -q
```

The run that wrote the result file: torch 2.13.0, Python 3.13.18, macOS. Width 32, 4 layers, 203,552 parameters. Batch 4, sequence 16, 20 steps, seeds 1234 and 1235. Synthetic tokens. Cross-entropy, not held-out bits per byte. Smoke step sizes, not a learning-rate recommendation: Muon 0.02, AdamW 0.001, weight decay 0. Every 2D parameter is on Muon. The 1D parameters are on AdamW.

| Seed | Arm | First loss | Last loss | Synthetic tokens/s |
|---|---|---|---|---|
| 1234 | one stream | 4.2947 | 0.6803 | 1721.32 |
| 1234 | two streams, fixed mean | 4.2849 | 1.3136 | 2143.10 |
| 1235 | one stream | 4.2926 | 0.7553 | 2162.92 |
| 1235 | two streams, fixed mean | 4.2993 | 1.2402 | 1978.52 |

After the first backward, both arms, both seeds: no parameter had a missing gradient, and no parameter had an all-zero gradient.

The one-stream last loss is lower on both seeds. The gap is larger than the spread between the two seeds of the same arm. That is not a reason to change the trainer. The tokens are synthetic, the net is 4 layers wide 32, the step size is a smoke size, and the score is not held-out bits per byte. A learned mix, a deep stack, and the real data mix were not run.

The trainer stays the one stream.

## Design task 5b. DroPE. Not measured

`GQA.rotary` applies rotary positions on every forward, for the whole run. `rotary_fraction` defaults to 1. There is no step that drops rotary positions, and there is no recalibration stage.

These four are not chosen. The 49M to 100M test the brief asks for has not been run:

- fraction of the token budget
- recalibration tokens
- sequence length
- learning rate

The test, when it is run, uses the brief's rule: 49M to 100M parameters, 100M to 500M tokens, at least two seeds, the same data order, one change at a time. It reports held-out bits per byte at the training length, a long-context check at 4 times that length, the recalibration cost, tokens per second, and peak memory. It says what the small test cannot tell you. No such log exists. No fraction is filled in here.

## Design task 6. Discovery at 49M to 100M. Not measured

The brief's four comparisons, and what the code on main does today. None of the four has a 49M to 100M result.

| Comparison | Code on main today | 49M to 100M result |
|---|---|---|
| Dense against mixture of experts, equal active parameters | The block is a mixture of experts | Not run |
| Rotary positions against no positions after a recalibration | Rotary positions are on for the whole run | Not run |
| A dense head against a factored head | `head_mode: kas_v2` selects the factored head. The dense untied head remains the other setting | Not run |
| One shared prediction block against one per depth | One head after the stack. The optional next-token head is off when `mtp` is false | Not run |

Same rule as 5b: two seeds, same held-out bytes, one change at a time, bits per byte, tokens per second, peak memory, and the limit of the small test. No run of that size is in this pull request.

## Lead addition 9. Scaling-law fit. Not measured

The fit is loss against active parameters and tokens, from small runs at three sizes and three token budgets. For a mixture of experts the size is the active parameter count. One run is held back, and the error is the miss on that run.

The nine runs do not exist, so there is no fit and no prediction. The three sizes and the three budgets are not chosen here. They stay inside the brief's small-test bounds, 49M to 100M parameters and 100M to 500M tokens, and they are chosen after a measured tokens-per-second on the first size. A plan without that rate would be a guess.

The production scale stays the one TSAI sets.
