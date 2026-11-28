# Dry run 2 (dryrun2-1234): run report

**What:** the output of `harness/run_report.py` (#829) on dry run 2's committed record (#869). Health, training loss and clipping, learning rate, real-token throughput and row fill, held-out bits per byte at every eval and per slice, and expert load per layer.
**Source:** `teams/05-architecture/results/dryrun2-1234/metrics.jsonl` on main (from #869; job dryrun2-1234, eager arm, `head_mode: kas_v2`, `bias_gamma: 0.001`).
**Reproduce** (from the repository root):

```
python teams/05-architecture/harness/run_report.py teams/05-architecture/results/dryrun2-1234/metrics.jsonl
```

The text below is that command's output, unedited.

**Read with TSAI's two notes on the run:** one seed (1234), and held-out bits per byte move by about 0.1 between evals; the training text was one English web shard of 25M tokens, so the Indic slices getting worse is what a model that saw only English does, not a finding about the recipe.

---

# Run report: dryrun2-1234

## Health

- Steps recorded: 1221 training rows, last step 1221.
- Non-finite loss or gradient norm: none.

## Training loss

- Mean of the first 50 steps: 8.2105; mean of the last 50: 5.4125; lowest single step: 5.0615.
- Gradient norm before clipping: median 0.821, max 26.871; clipped on 222 of 1221 steps (18.2%).

## Learning rate

- First 1.64e-05, peak 0.001 (first reached at step 61), last 0.

## Throughput

- Real (scored) tokens per second: 2,299 over 1.01 h of step time.
- Row fill: 8,365,665 scored tokens in 20,004,864 input positions (41.8%).
- The trainer's tokens_per_second counts padded positions; the line above does not.

## Held-out bits per byte

| Step | val/bpb |
|---:|---:|
| 0 | 2.1607 |
| 50 | 2.2759 |
| 100 | 2.3887 |
| 150 | 2.3771 |
| 200 | 2.2256 |
| 250 | 2.2483 |
| 300 | 2.3262 |
| 350 | 2.3840 |
| 400 | 2.4267 |
| 450 | 2.3341 |
| 500 | 2.3787 |
| 550 | 2.4366 |
| 600 | 2.3851 |
| 650 | 2.1653 |
| 700 | 2.1864 |
| 750 | 2.0677 |
| 800 | 2.1377 |
| 850 | 2.0653 |
| 900 | 2.3596 |
| 950 | 2.2068 |
| 1000 | 2.0841 |
| 1050 | 2.0689 |
| 1100 | 2.1629 |
| 1150 | 2.3115 |
| 1200 | 2.0931 |
| 1221 | 2.0561 |

Per slice, step 0 to step 1221:

| Slice | First | Last | Change |
|---|---:|---:|---:|
| as | 1.8544 | 2.2327 | +0.3782 |
| bn | 1.7753 | 2.1579 | +0.3826 |
| code | 4.1426 | 3.4073 | -0.7352 |
| en | 3.1880 | 1.7687 | -1.4193 |
| gu | 1.7269 | 2.0647 | +0.3378 |
| hi | 1.3230 | 1.8982 | +0.5752 |
| kn | 1.6985 | 1.8780 | +0.1795 |
| math | 4.1350 | 2.4825 | -1.6526 |
| ml | 1.4898 | 1.7142 | +0.2244 |
| mr | 1.3736 | 1.8624 | +0.4888 |
| or | 1.5378 | 1.7946 | +0.2567 |
| pa | 1.9737 | 2.2553 | +0.2816 |
| sci | 3.0340 | 1.6108 | -1.4232 |
| ta | 1.4283 | 1.7834 | +0.3551 |
| te | 1.6855 | 1.8892 | +0.2038 |

## Expert load

- Recorded at 24 steps (first 50, last 1200).
- Reference, TSAI 24 Nov (balanced, router on Muon): busiest expert 7.3% to 9.0% per layer, max/mean 1.44, CV 0.105.

At step 1200 (fair share 6.25% with 16 experts):

| Layer | Busiest expert | Max/mean | CV | Dead experts |
|---:|---:|---:|---:|---:|
| 0 | 11.2% | 1.79 | 0.272 | 0 |
| 1 | 15.2% | 2.43 | 0.452 | 0 |
| 2 | 14.2% | 2.27 | 0.429 | 0 |
| 3 | 9.2% | 1.47 | 0.304 | 1 |
| 4 | 10.3% | 1.65 | 0.350 | 0 |
| 5 | 10.6% | 1.69 | 0.336 | 0 |
| 6 | 8.7% | 1.39 | 0.181 | 0 |
| 7 | 15.5% | 2.48 | 0.527 | 1 |

Busiest expert over the run (worst layer at each recorded step):

| Step | Worst busiest share | Layers with a dead expert |
|---:|---:|---:|
| 50 | 50.0% | 8 |
| 100 | 47.7% | 5 |
| 150 | 45.4% | 1 |
| 200 | 41.3% | 1 |
| 250 | 38.3% | 1 |
| 300 | 38.3% | 0 |
| 350 | 31.1% | 0 |
| 400 | 17.8% | 0 |
| 450 | 14.2% | 1 |
| 500 | 14.6% | 1 |
| 550 | 15.0% | 1 |
| 600 | 16.2% | 1 |
| 650 | 12.4% | 1 |
| 700 | 16.2% | 0 |
| 750 | 16.6% | 2 |
| 800 | 16.6% | 2 |
| 850 | 17.4% | 2 |
| 900 | 19.2% | 3 |
| 950 | 16.9% | 2 |
| 1000 | 12.5% | 4 |
| 1050 | 15.8% | 4 |
| 1100 | 17.6% | 3 |
| 1150 | 21.6% | 3 |
| 1200 | 15.5% | 2 |

