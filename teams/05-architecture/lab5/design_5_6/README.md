# Lab 5, design tasks 5, 5b, 6, and lead addition 9

Name: Shivanshu Thapliyal. GitHub: shivman. Team: 05 Architecture.

The production scale is the one TSAI sets. This note does not name one. `config_v1.yaml` is not edited. `data.seq_len` stays empty. The finished dry run is not edited. The block on main is unchanged.

Measured numbers are the ones in `residual_stream_result.json`, produced by the command below. Everything else in this note is not measured.

## Design task 5. Residual stream. Measured on a small net

The block on main is one stream. Pre-norm, then the sublayer is added back onto that same stream (`teams/05-architecture/harness/week2/model.py`, `Block.forward`).

The other arm is only in `residual_stream.py`. The first block reads the embedding twice. Attention starts one stream and the MoE starts the other. Each later block mixes the two streams with a learned 2 by 2, initialized so the softmax is an equal mix, then writes attention back to the first stream and the MoE back to the second. A last 2 by 2 mixes the two streams into the head. That is 8 mixes, 32 parameters. The one-stream arm has 1,219,648 parameters and does not include them.

The sequences follow one rule: each later token is the sum of the two tokens before it, modulo 64. The run draws 128 distinct train sequences and 32 further distinct sequences. Those 32 are never used in an update. The score is cross-entropy on them. It is not held-out bits per byte on heldout_v1.

Command, from the repository root:

```
python teams/05-architecture/lab5/design_5_6/residual_stream.py
```

Checks:

```
python -m pytest teams/05-architecture/lab5/design_5_6/test_residual_stream.py -q
```

The run that wrote the result file: torch 2.13.0, Python 3.13.18, macOS-26.6.2-arm64. Width 64, 8 layers, vocabulary 64. Batch 8, sequence 32, 240 steps, seeds 1234, 1235, and 1236. Rates are the dry-run rates, not retuned for this net: Muon 0.006, AdamW 0.001, weight decay 0. Every 2D parameter is on Muon, including the 2 by 2 mixes. The 1D parameters are on AdamW.

| Seed | Arm | Train start | Train end | Held-out start | Held-out end | Synthetic tokens/s |
|---|---|---|---|---|---|---|
| 1234 | one stream | 4.3123 | 0.5388 | 4.3417 | 2.7698 | 1261.23 |
| 1234 | mixed streams | 4.3126 | 0.4786 | 4.3489 | 2.3589 | 1266.97 |
| 1235 | one stream | 4.3214 | 0.5732 | 4.3224 | 2.8484 | 1257.87 |
| 1235 | mixed streams | 4.3200 | 0.5618 | 4.3202 | 2.5226 | 1279.98 |
| 1236 | one stream | 4.3238 | 0.5010 | 4.3733 | 2.8690 | 1307.06 |
| 1236 | mixed streams | 4.3275 | 0.4927 | 4.3740 | 2.5122 | 1286.58 |

After the first backward, both arms, all three seeds: no parameter had a missing gradient, and no parameter had an all-zero gradient. The mix parameters are in that list.

The process peak for the whole script is 327,483,392 bytes (`peak_rss_bytes` in the result file). On this Mac, `ru_maxrss` is bytes. It covers both arms and all three seeds.

The mixed arm's held-out cross-entropy is lower on all three seeds. The smallest gap is 0.3258, on seed 1235. The spread inside the mixed arm is 0.1637, and the spread inside the one-stream arm is 0.0992. The gap is larger than either spread. Tokens per second stay in the same band. The mixes leave the equal start. Their values are in the result file.

This net is 1,219,648 parameters, width 64, 8 layers. The tokens are a two-token sum. The score is cross-entropy on those held-out rows. A result at this size does not choose the stream for the run TSAI starts.

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
