# Baseline v0: lab_small on one A100

**Result: PASS.** Every gated part agrees within 5% between two runs. The largest difference is 3.63% (`fwd:block3`).

| | |
|---|---|
| GPU | NVIDIA A100-SXM4-40GB (compute capability 8.0, 39.5 GiB), Colab |
| Commit | `f1f4986aa0e4f74c64c86ce108c65c25678174eb`, clean tree (`dirty: false`) |
| Software | torch 2.11.0+cu130, CUDA 13.0, driver 580.82.07, Python 3.13 |
| Config | `configs/lab_small.yaml`, no model overrides (`--level 3` sets `bench.level=3`) |
| Model | KE v1 embedding, GQA 8/2 heads, MoE 1 shared + top-2 of 8, reversible midpoint stack, 9 layers, width 256, vocabulary 131,072 (BrahmicTokenizer-131K) |
| Run | bf16 autocast, B=32, T=512 (16,384 tokens per step), FineWeb sample-10BT, Muon + AdamW, constant LR |
| Command | `python -m perfkit.bench --config configs/lab_small.yaml --level 3 --repeat 2 --tag baseline_v0` |
| Runs | `baseline_v0` and `baseline_v0-run2`, each in its own Python process, back to back, 2026-10-27 |
| Method | 10 warmup steps, then 150 measured steps per mode. Parts are timed with CUDA events and no host sync inside a step. Each number is the median over the steps. |

## The step

| | Run 1 | Run 2 |
|---|---:|---:|
| Step time, median (ms) | 506.6 | 516.9 |
| p10 .. p90 (ms) | 499.6 .. 520.1 | 507.2 .. 529.0 |
| Tokens per second | 32,340 | 31,694 |
| MFU / HFU (bf16 dense peak 312 TFLOPS) | 3.3% / 4.2% | 3.3% / 4.2% |
| Peak memory allocated / reserved (GiB) | 25.1 / 29.4 | 25.1 / 29.4 |
| GPU busy in the trace | 24.9% | 24.6% |
| Kernels per step / host syncs per step | 18,428 / 433 | 18,431 / 433 |
| Recorder overhead (layer mode) | 0.06% | 0.51% |

The model has 79.9M parameters, 51.3M of them active per token (the LM head is 33.5M of those). That makes
322 MFLOP per token for MFU and 410 MFLOP per token for HFU. HFU also counts the reversible stack's two extra
forwards and Muon's Newton-Schulz work. The method is in `docs/METRICS.md`.

Where the step goes (run 1, level-1 parts): forward 102 ms (20%), backward 240 ms (47%), optimizer 161 ms (32%),
data 0.9 ms.

## The 5% check

Rule: the whole step and every part at level 1 or 2 must agree within 5%, with no exemption for small parts.
Diff = slower / faster - 1. Level-3 parts (inside a block) are timed and listed in the run files but not gated.

| Part | Level | Run 1 (ms) | Run 2 (ms) | Diff | |
|---|---:|---:|---:|---:|---|
| `step (clean)` | - | 506.619 | 516.939 | 2.04% | ok |
| `data` | 1 | 0.856 | 0.856 | 0.00% | ok |
| `fwd` | 1 | 102.342 | 103.985 | 1.61% | ok |
| `fwd:embed` | 2 | 4.360 | 4.368 | 0.19% | ok |
| `fwd:stack` | 1 | 55.685 | 57.302 | 2.90% | ok |
| `fwd:block0` | 2 | 5.846 | 6.029 | 3.14% | ok |
| `fwd:block1` | 2 | 6.156 | 6.368 | 3.44% | ok |
| `fwd:block2` | 2 | 6.217 | 6.347 | 2.08% | ok |
| `fwd:block3` | 2 | 6.196 | 6.420 | 3.63% | ok |
| `fwd:block4` | 2 | 6.230 | 6.390 | 2.58% | ok |
| `fwd:block5` | 2 | 6.174 | 6.361 | 3.03% | ok |
| `fwd:block6` | 2 | 6.173 | 6.321 | 2.41% | ok |
| `fwd:block7` | 2 | 6.141 | 6.212 | 1.15% | ok |
| `fwd:block8` | 2 | 6.159 | 6.317 | 2.57% | ok |
| `fwd:head+loss` | 2 | 42.126 | 42.133 | 0.02% | ok |
| `bwd` | 1 | 239.607 | 243.275 | 1.53% | ok |
| `bwd:head+loss` | 2 | 48.154 | 48.153 | 0.00% | ok |
| `bwd:stack` | 1 | 190.961 | 194.639 | 1.93% | ok |
| `bwd:block8` | 2 | 22.001 | 22.237 | 1.08% | ok |
| `bwd:block7` | 2 | 21.594 | 21.732 | 0.64% | ok |
| `bwd:block6` | 2 | 21.390 | 21.654 | 1.24% | ok |
| `bwd:block5` | 2 | 21.236 | 21.671 | 2.05% | ok |
| `bwd:block4` | 2 | 21.284 | 21.571 | 1.35% | ok |
| `bwd:block3` | 2 | 21.065 | 21.489 | 2.01% | ok |
| `bwd:block2` | 2 | 21.113 | 21.445 | 1.57% | ok |
| `bwd:block1` | 2 | 20.954 | 21.360 | 1.94% | ok |
| `bwd:block0` | 2 | 20.882 | 21.368 | 2.33% | ok |
| `bwd:embed` | 2 | 0.484 | 0.486 | 0.42% | ok |
| `opt` | 1 | 160.840 | 166.407 | 3.46% | ok |
| `opt:opt.clip` | 2 | 4.445 | 4.470 | 0.55% | ok |
| `opt:opt.muon` | 2 | 152.699 | 158.199 | 3.60% | ok |
| `opt:opt.adamw` | 2 | 1.658 | 1.640 | 1.09% | ok |
| `checkpoint save` | - | 3161.193 | 3156.190 | 0.16% | ok |

**Watch:** the per-block parts have a p10..p90 spread of 6 to 11% within a run (run 2 flags six of them above
10%), and run 2 is 1 to 4% slower on the CPU-bound parts (the blocks, Muon). That is inside 5%, but with less
margin than the GPU-bound parts, which agree within 0.2% (`fwd:embed`, `head+loss`).

## Also measured

| | Run 1 | Run 2 |
|---|---:|---:|
| Checkpoint save (model + optimizer, 747 MiB), median of 10 | 3161 ms | 3156 ms |
| of which copy to CPU / write and fsync | 65 / 3096 ms | 65 / 3091 ms |
| GPU during the clean steps (nvidia-smi, 77 and 78 samples): utilization, SM clock, power, temperature | 59%, 1410 MHz, 127 W, 39 C | 39%, 1410 MHz, 122 W, 39 C |
| Clock slowdowns (power or thermal) | none | none |
| Reversible reconstruction error (bf16) | 2.4e-4 | 2.4e-4 |
| MoE all-to-all | not timed: one GPU. Payload 32 MiB per call, 72 calls per step (needs `torchrun` on 2 GPUs) | |

nvidia-smi's utilization counts the time at least one kernel runs, sampled once a second, so it moves between
runs (59% vs 39%) while the step time does not. The trace's GPU busy figure (25%) is the measured one.

## What makes the runs repeatable

- **Each run gets its own Python process.** A second run in the same process as a first one that used the
  profiler was 26% slower on every CPU-bound part, while the GPU-bound ones (the head, the embedding) did not change.
  The step is CPU-bound (25% GPU busy), so anything that slows the CPU shows up in the timings.
- **The same GPU, clocks steady.** The SM clock stayed at 1410 MHz with no power or thermal slowdowns in either
  run, so GPU clocks do not explain the remaining 0 to 4%.
- **Other pairs on the same GPU agreed too:** three earlier two-run pairs agreed within 4.7%, 3.8% and 3.0%.
