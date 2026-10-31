# Roofline estimator

`perfkit/roofline.py` estimates the forward-pass cost of each timed region from the model shapes in the config:
FLOPs, bytes moved and a rough kernel count. It turns them into three lower bounds (compute, memory bandwidth,
kernel launch) and predicts each region's time as the largest of the three. Use it to form profiling
hypotheses; judge performance by the measured timings.

## Run it

From `teams/06-performance`:

```bash
python -m perfkit.roofline --config configs/base.yaml \
  --gpu "NVIDIA A100-SXM4-40GB" --run results/runs/baseline_v0.json
```

- `--run` (optional) is any bench run JSON: your own `results/runs/<tag>.json`, or `baseline_v0.json` from the
  baseline gist (https://gist.github.com/vaibh27/574990425455e4a9cb64822f14e3d85b). With it, each matching
  region also shows the measured median and the measured / estimated ratio.
- `--batch-size`, `--seq-len`: override the config's B and T.
- `--peak-tflops`, `--bandwidth-gbs`: override the GPU's dense peak or memory bandwidth (use a measured
  profile when you have one). For a GPU not in the tables (for example the RTX 5070 Ti), both are required:
  without them the estimator stops with an error.
- `--launch-us`: launch cost per kernel, default 5 microseconds (a heuristic).

The output is a plain-text table, in the same style as the correctness summary.

## The model

```text
compute_ms   = FLOPs / (dense peak TFLOP/s * 1e9)
bandwidth_ms = estimated bytes / (memory bandwidth GB/s * 1e6)
launch_ms    = estimated kernels * launch latency in microseconds / 1000
region_ms    = max(compute_ms, bandwidth_ms, launch_ms)
```

- **Peaks** come from `perfkit/metrics.py` (dense); **bandwidth** from the table in `roofline.py` (theoretical
  device specifications, not measured sustained bandwidth).
- **Scope:** forward only. Backward, optimizer, data loading and communication are not estimated.
- **Rows:** `part` = one estimate; `sum` = a region that rolls up its children (`fwd:block0`, `fwd:stack`);
  `total` = the three top-level regions (`fwd:embed`, `fwd:stack`, `fwd:head+loss`) that are added into the
  total. Do not add a `sum` row to its own parts.

## Reading the ratio

A large measured / estimated ratio points at launch gaps, host syncs, memory traffic beyond the simple model, or
slow kernels. A ratio near 1 is not a target: the estimates are lower bounds.

On the committed baseline (`base.yaml`, A100-SXM4-40GB, B=16, T=256, commit `f1ed7f2`):

| Region | Estimate (ms) | Bound | Measured (ms) | Measured / estimate |
|---|---:|---|---:|---:|
| `fwd:embed` | 0.015 | launch | 0.395 | 26x (KE2 not modelled, see Limits) |
| `fwd:block0` | 0.095 | launch | 0.482 | 5.1x |
| `fwd:block0.attn.sdpa` | 0.005 | bandwidth | 0.291 | 54x (eager attention not modelled) |
| `fwd:block0.mlp` | 0.030 | launch | 0.082 | 2.7x |
| `fwd:stack` | 0.570 | launch | 2.931 | 5.1x |
| `fwd:head+loss` | 2.116 | bandwidth | 10.674 | 5.0x |
| forward total | 2.355 | bandwidth | 14.013 | 6.0x |

The head is 5x its bandwidth bound (the fp32 logits) and each block 5x its launch bound (many small kernels):
the same two causes as `results/slowest5_v0.md`.

## Limits

The estimates simplify real execution: byte counts assume little cache reuse and kernel counts are heuristic.
Three parts of `configs/base.yaml` are not modelled yet (a code fix in `roofline.py` is planned for week 2):

1. **KE2** (`model.embedding: ke2`): only `ke1` has a codec / projection estimate. KE2 falls back to the plain
   table lookup, so `fwd:embed` has no `fwd:embed.ke` row and its estimate is too low.
2. **Eager attention** (`model.attn_impl: eager`): the estimate assumes flash-style attention (no score matrix,
   one kernel). Eager attention builds the full T x T scores in several kernels, so `attn.sdpa` reads far above
   its estimate.
3. **MTP** (`model.mtp=true`): the head is counted once; the second head and its loss are not, so `fwd:head+loss`
   is about half the real cost.

## Other GPUs

To validate on another GPU, save a `--modes clean,layer` run JSON on it and run the estimator with that GPU's
name and the same config, batch size and sequence length. The committed baseline is an A100 run only; H100,
H200, B200 and consumer GPUs need their own run files.
