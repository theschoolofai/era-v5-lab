# Baseline v0: base.yaml on one A100

**Result: PASS.** Every gated part agrees within 5% (or 0.05 ms) between two runs, for the normal model and for
the MTP model. The largest gap is 3.85% on `data` (0.027 vs 0.028 ms); every other gated part is within 0.5%.

| | |
|---|---|
| GPU | NVIDIA A100-SXM4-40GB (compute capability 8.0, 39.5 GiB), Colab |
| Commit | `f1ed7f2daf525242d84e4daf45c9d0247583ed71` (g6/dev), clean tree (`dirty: false`) in all four runs |
| Software | torch 2.11.0+cu130, CUDA 13.0, driver 580.82.07, Python 3.13 |
| Config | `configs/base.yaml`, no file edits; MTP pair adds `model.mtp=true` |
| Model | KE2 embedding (G4 raw table), eager attention, 8 heads, dense MLP (ratio 4), reversible midpoint stack, 6 layers, width 256, vocabulary 131,072 (BrahmicTokenizer-131K), untied head |
| Run | bf16 autocast, B=16, T=256 (4,096 tokens per step), FineWeb sample-10BT, Polar Express Muon + AdamW (`muon_impl: batched`, `adamw_impl: foreach`), batch prefetch on, constant LR |
| Commands | `python -m perfkit.bench --level 3 --repeat 2 --tag baseline_v0` and `python -m perfkit.bench --level 3 --repeat 2 --tag mtp_v0 model.mtp=true` |
| Runs | `baseline_v0`, `baseline_v0-run2`, `mtp_v0`, `mtp_v0-run2`, each in its own Python process, back to back, 2026-10-31; run files and logs: [gist](https://gist.github.com/vaibh27/574990425455e4a9cb64822f14e3d85b) |
| Method | 10 warmup steps, then 100 measured steps per mode. Parts are timed with CUDA events and no host sync inside a step. Each number is the median over the steps. |

Tests on the same commit and GPU: `pytest correctness -q -rs --all-configs` gives 375 passed, 1 xfailed, 0 failed,
0 skipped (47 of 47 pairs, the 1.01 drill included).

## The step

| | Normal, run 1 | Normal, run 2 | MTP, run 1 | MTP, run 2 |
|---|---:|---:|---:|---:|
| Step time, median (ms) | 42.91 | 42.95 | 68.62 | 68.61 |
| p10 .. p90 (ms) | 42.89 .. 42.94 | 42.91 .. 42.98 | 68.58 .. 68.66 | 68.58 .. 68.66 |
| Tokens per second | 95,459 | 95,377 | 59,691 | 59,696 |
| MFU / HFU (bf16 dense peak 312 TFLOPS) | 7.6% / 8.4% | 7.5% / 8.4% | 8.6% / 9.1% | 8.6% / 9.1% |
| Peak memory allocated / reserved (GiB) | 6.54 / 7.43 | 6.54 / 7.43 | 8.96 / 13.54 | 8.96 / 13.54 |
| GPU busy in the trace | 50.4% | 51.3% | 80.2% | 79.1% |
| Kernels per step / host syncs per step | 1,392 / 1 | 1,393 / 1 | 1,534 / 1 | 1,576 / 1 |
| Recorder overhead (layer mode) | 0.41% | 0.41% | 0.25% | 0.25% |

The normal model has 40.5M parameters (40.4M active per token; the LM head is 33.5M of them). That makes
247 MFLOP per token for MFU and 276 MFLOP per token for HFU (HFU also counts the reversible stack's two extra
forwards and Muon's Newton-Schulz work). MTP adds a second untied head: 74.0M parameters, 448 / 477 MFLOP per
token. The method is in `docs/METRICS.md`.

Where the step goes (normal, run 1, level-1 parts): forward 14.0 ms (33%), backward 23.7 ms (55%), optimizer
5.3 ms (12%), data 0.03 ms. The head and loss alone take 23.0 ms (forward 10.7, backward 12.3): 54% of the step.

## The 5% check

Rule (TSAI, 30 Oct): the whole step, every part at level 1 or 2 and checkpoint save must be within 5%
(diff = slower / faster - 1) **or** less than 0.05 ms apart. Level-3 parts (inside a block) are timed and listed
in the run files but not gated.

| Part | Level | Normal run 1 (ms) | Normal run 2 (ms) | Diff | MTP run 1 (ms) | MTP run 2 (ms) | Diff | |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `step (clean)` | - | 42.909 | 42.946 | 0.09% | 68.620 | 68.614 | 0.01% | ok |
| `data` | 1 | 0.027 | 0.028 | 3.85% | 0.022 | 0.022 | 0.00% | ok |
| `fwd` | 1 | 14.013 | 14.021 | 0.06% | 24.701 | 24.698 | 0.01% | ok |
| `fwd:embed` | 2 | 0.395 | 0.396 | 0.26% | 0.397 | 0.397 | 0.00% | ok |
| `fwd:stack` | 1 | 2.931 | 2.935 | 0.14% | 2.955 | 2.954 | 0.03% | ok |
| `fwd:block0` | 2 | 0.482 | 0.482 | 0.00% | 0.486 | 0.486 | 0.00% | ok |
| `fwd:block1` | 2 | 0.484 | 0.485 | 0.21% | 0.489 | 0.488 | 0.21% | ok |
| `fwd:block2` | 2 | 0.484 | 0.486 | 0.42% | 0.488 | 0.488 | 0.00% | ok |
| `fwd:block3` | 2 | 0.485 | 0.486 | 0.21% | 0.490 | 0.489 | 0.21% | ok |
| `fwd:block4` | 2 | 0.485 | 0.486 | 0.11% | 0.489 | 0.489 | 0.00% | ok |
| `fwd:block5` | 2 | 0.485 | 0.485 | 0.00% | 0.489 | 0.489 | 0.00% | ok |
| `fwd:head+loss` | 2 | 10.674 | 10.678 | 0.04% | 21.336 | 21.334 | 0.01% | ok |
| `bwd` | 1 | 23.746 | 23.765 | 0.08% | 36.105 | 36.104 | 0.00% | ok |
| `bwd:head+loss` | 2 | 12.339 | 12.342 | 0.02% | 24.607 | 24.608 | 0.00% | ok |
| `bwd:stack` | 1 | 10.983 | 10.999 | 0.14% | 11.067 | 11.066 | 0.01% | ok |
| `bwd:block5` | 2 | 1.825 | 1.827 | 0.11% | 1.839 | 1.839 | 0.00% | ok |
| `bwd:block4` | 2 | 1.825 | 1.828 | 0.17% | 1.837 | 1.836 | 0.06% | ok |
| `bwd:block3` | 2 | 1.826 | 1.829 | 0.17% | 1.841 | 1.841 | 0.00% | ok |
| `bwd:block2` | 2 | 1.824 | 1.826 | 0.14% | 1.840 | 1.839 | 0.06% | ok |
| `bwd:block1` | 2 | 1.825 | 1.828 | 0.20% | 1.839 | 1.838 | 0.06% | ok |
| `bwd:block0` | 2 | 1.823 | 1.827 | 0.22% | 1.838 | 1.839 | 0.03% | ok |
| `bwd:embed` | 2 | 0.415 | 0.415 | 0.00% | 0.421 | 0.422 | 0.24% | ok |
| `opt` | 1 | 5.314 | 5.319 | 0.09% | 7.974 | 7.976 | 0.02% | ok |
| `opt:opt.clip` | 2 | 0.443 | 0.443 | 0.00% | 0.734 | 0.734 | 0.00% | ok |
| `opt:opt.polar_muon_adamw` | 2 | 4.861 | 4.866 | 0.11% | 7.228 | 7.231 | 0.04% | ok |
| `opt:opt.muon` | 2 | 2.322 | 2.328 | 0.22% | 2.349 | 2.350 | 0.04% | ok |
| `opt:opt.adamw` | 2 | 2.525 | 2.524 | 0.04% | 4.867 | 4.868 | 0.02% | ok |
| `checkpoint save` | - | 1914.178 | 1893.130 | 1.11% | 3575.717 | 3563.679 | 0.34% | ok |

The values are the medians in the run JSONs (`baseline_v0*.json`, `mtp_v0*.json`); the logs, run JSONs and
full bench output (level 3 included) are in the gist https://gist.github.com/vaibh27/574990425455e4a9cb64822f14e3d85b.

**Watch:** `data` is the only gated part with a p10..p90 spread above 10% within a run; at 0.03 ms it is far
below the 0.05 ms floor. Level-3 rows inside `fwd:block3` to `block5` and `opt.muon.ns` differ by up to 70%
between the runs while the whole blocks agree within 0.4%: they come from the separate level-3 pass, where the
extra timing events change how far the CPU runs ahead of the GPU. They are information only.

## Also measured

| | Normal, run 1 | Normal, run 2 | MTP, run 1 | MTP, run 2 |
|---|---:|---:|---:|---:|
| Checkpoint save (model + optimizer), median of 10 | 1914 ms (445 MB) | 1893 ms | 3576 ms (829 MB) | 3564 ms |
| of which copy to CPU / write and fsync | 37 / 1878 ms | 37 / 1856 ms | 67 / 3509 ms | 67 / 3497 ms |
| GPU during the clean steps (nvidia-smi): utilization, SM clock, power, temperature | 100%, 1410 MHz, 247 W, 47 C | 100%, 1410 MHz, 252 W, 48 C | 100%, 1410 MHz, 265 W, 49 C | 100%, 1410 MHz, 265 W, 49 C |
| Clock slowdowns (power or thermal) | none | none | none | none |
| Reversible reconstruction error (bf16) | 7.4e-5 | 7.4e-5 | 7.4e-5 | 7.4e-5 |
| MoE all-to-all | not applicable: `base.yaml` has `ffn: mlp` (time it with `model.ffn=moe` under `torchrun` on 2 GPUs) | | | |

## What makes the runs repeatable

- **Each run gets its own Python process** (`--repeat`). A second run in the same process as a first one that
  used the profiler was 26% slower on every CPU-bound part (measured on the v0 lab model).
- **Fewer kernel launches.** The batched Polar Express Muon (`muon_impl: batched`), the `torch._foreach` AdamW
  (`adamw_impl: foreach`) and the batch prefetch after backward cut the step from about 3,540 to 1,392 kernels and
  raised GPU busy from about 33% to 50% (same GPU type, PR #30 head against `g6/muon-batched-prefetch`). The
  parts that used to move with the host CPU (Muon, `fwd:block0`, `data`) now agree within 0.5%.
- **The same GPU, clocks steady.** The SM clock stayed at 1410 MHz with no power or thermal slowdowns.

## Other machines (same commit)

- **Colab A100-SXM4-40GB, a second session:** both pairs pass (28 of 28 parts).
- **RTX 5070 Ti, Linux, commit `190693a` (same code, docstrings only), four runs per mode:** all six normal
  and all six MTP pairs pass (28 of 28 parts, checkpoint save included, largest checkpoint gap 2.8%); step
  59.6 ms normal, 104.4 ms MTP; MFU unavailable (`unknown_gpu`)
  ([runs](https://gist.github.com/jssunil/0f0e289c5dca5630214d1de1da109ba9)). Correctness on the same host, with
  the sampler test fix: 375 passed, 1 xfailed, 0 failed, 0 skipped with `--all-configs`
  ([logs](https://gist.github.com/jssunil/0be0592d4464997a3d216fdee59fe09e)).
- **RTX 5070 Ti, Windows (WDDM, display on the same GPU), four runs, earlier result kept for the record:** every
  code part passes in all six pairs; only checkpoint save fails, in the three pairs with run 2 (7.7 to 9.5%),
  because that run's disk write was slower (and its GPU-to-CPU copy 2 ms slower). Gist linked in the PR.
- **Modal A100-80GB (SXM4 and PCIe hosts), earlier commits:** the CPU-paced parts (`opt.muon`, `fwd:embed`,
  `fwd:block0`) move between runs with the host. Week 2: capture the optimizer step as a CUDA graph so its time
  stops depending on the host CPU (`results/repeat_check_v1.md`).
