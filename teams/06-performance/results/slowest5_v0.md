# The five slowest parts (v0)

GPU: NVIDIA A100-SXM4-40GB, bf16, B=32, T=512, `configs/lab_small.yaml`, commit `f1f4986`, run `baseline_v0`.
Step 507 ms (median of 150 steps). A part is a region summed over the 9 layers. Each trace is one occurrence
(layer 4, or the whole step for Muon) cut from the profiler trace: open it in https://ui.perfetto.dev or
`chrome://tracing`. It shows when the CPU queued the work and when the GPU ran it, with arrows from each launch
to its kernel.

**One cause behind most of it:** the step is CPU-bound. The GPU is busy only 25% of the step: 18,400 kernels and
433 host syncs per step. In parts 1, 2, 3 and 5 below the CPU takes 4 to 8 times longer than the GPU work it
launches. Part 4 is the exception: the GPU is busy all the time, moving memory.

| # | Part | ms | % of step | CPU time in trace | GPU kernel time in trace | Trace |
|---|---|---:|---:|---:|---:|---|
| 1 | `opt:opt.muon.ns` | 145.9 | 28.8% | 69.9 ms (48 of 189 matrices) | 8.3 ms | `runs/baseline_v0_parts/1_opt_opt.muon.ns.json` |
| 2 | `bwd:block*.grad` | 90.4 | 17.8% | 18.1 ms (layer 4) | 4.1 ms | `runs/baseline_v0_parts/2_bwd_block4.grad.json` |
| 3 | `fwd:block*.moe.dispatch` | 50.6 | 10.0% | 8.6 ms (layer 4) | 1.3 ms | `runs/baseline_v0_parts/3_fwd_block4.moe.dispatch.json` |
| 4 | `bwd:head+loss` | 48.2 | 9.5% | 1.4 ms | 48.1 ms | `runs/baseline_v0_parts/4_bwd_head+loss.json` |
| 5 | `bwd.recompute:block*.moe.dispatch` | 46.0 | 9.1% | 8.4 ms (layer 4) | 1.3 ms | `runs/baseline_v0_parts/5_bwd.recompute_block4.moe.dispatch.json` |

Together: 381 ms, 75% of the step.

## 1. Muon Newton-Schulz: `opt:opt.muon.ns`, 146 ms (29%)

- **What the trace shows:** Muon orthogonalizes each of the 189 block weight matrices separately: 5 iterations
  of 3 small matmuls plus element-wise ops, about 43 kernel launches per matrix. The trace keeps every 4th
  matrix, 48 of 189 from the first to the last (the file is capped at 4.5 MB). For those 48 the CPU takes 70 ms
  and the GPU 8 ms, about 1.5 ms against 0.17 ms per matrix; the GPU waits between kernels. This trace is from
  a later run at `b278601`, which changed only how the trace is cut, not the model or the optimizer.
- **Cause:** launch-bound. The matrices are small (8x256 up to 1024x256), and each runs alone.
- **Supporting run:** the same model with AdamW instead of Muon runs 157 ms faster per step (what-if table below).
- **Week-2 idea:** batch matrices of the same shape and run Newton-Schulz on the stack with `torch.bmm`. There
  are 5 shapes; the 162 expert matrices are 1024x256 or its transpose, so one batch holds them all. That is about
  5 chains of launches instead of 189. Switch: `optim.muon_impl: loop -> batched`, with a `@pair` test against
  the per-matrix loop.

## 2. Local backward of each reversible block: `bwd:block*.grad`, 90 ms (18%)

- **What the trace shows:** layer 4's backward makes 386 kernel launches and 85 memsets (613 CUDA runtime
  calls in all); the CPU takes 18.1 ms, the GPU 4.1 ms.
  The largest kernels are element-wise ops, reductions and a radix sort (from the MoE gather / `index_add_`
  backward), each under 1 ms.
- **Cause:** launch-bound. Many small kernels per block: attention, 8 experts' MLPs, gathers and scatters, all
  in backward.
- **Week-2 idea:** compile the block's residual function `f` with `torch.compile` (regional compilation: one
  block, reused for all 9). This fuses the element-wise and normalization kernels and cuts launches. It needs part
  3 first: the MoE host syncs break the compiled graph.

## 3. MoE dispatch, forward: `fwd:block*.moe.dispatch`, 51 ms (10%)

- **What the trace shows:** layer 4's dispatch takes 8.6 ms on the CPU for 1.3 ms of GPU work. It makes 16 host
  syncs: 2 per expert, at `models/moe.py:72` (`tok.any()`) and `:74` (`nonzero`). Each one stops the CPU until
  the GPU catches up.
- **Cause:** the loop dispatch handles one expert at a time and asks the GPU which tokens it has. Across the
  forward, invert and recompute passes that makes 432 of the step's 433 host syncs.
- **Week-2 idea:** sort the tokens by expert once and run all experts in one grouped matmul
  (`torch.nn.functional.grouped_mm`, bf16, SM80 and newer). The group sizes stay on the GPU, so there is no sync.
  It becomes a new `DISPATCH` entry (`model.moe.dispatch: loop -> grouped`), tested by every `moe.<d>` pair in
  `correctness/test_moe.py` with no change to the tests.

## 4. Head and loss, backward: `bwd:head+loss`, 48 ms (10%)

- **What the trace shows:** GPU-bound; the CPU queues 17 kernel launches in 1.4 ms. `cunn_SoftMaxBackward` alone takes
  25 ms, plus 15 ms of element-wise kernels. The fp32 logits are 16,384 x 131,072 = 8.6 GB. The softmax backward
  reads two such tensors and writes one, 25.8 GB in 25 ms: 1.0 TB/s, about 66% of the A100's 1.55 TB/s.
- **Cause:** memory-bound. The full fp32 logits are built, stored and read back. Together with the forward
  (42 ms) the head and loss take 90 ms (18%) and most of the 25.1 GiB peak memory.
- **Supporting run:** `model.ce_impl=chunked` (the head in 8 pieces) cuts peak memory from 25.1 to 4.2 GiB but
  costs 10% step time, because it computes the head twice.
- **Week-2 idea:** fused linear cross-entropy, which never stores the logits: Liger Kernel's
  `FusedLinearCrossEntropy` or Apple's Cut Cross-Entropy (CCE). It becomes `model.ce_impl: fused`, tested by a
  `model.lab_small.fused` pair like `model.lab_small.chunked`.

## 5. MoE dispatch, recomputed in the reversible backward: `bwd.recompute:block*.moe.dispatch`, 46 ms (9%)

- **What the trace shows:** the same pattern as part 3 (8.4 ms on the CPU, 1.3 ms on the GPU, 16 syncs), because
  the reversible backward runs each block's forward again.
- **Cause:** for each block, the reversible backward computes `f(p)` twice on the same input: once in
  `bwd.invert` to rebuild the previous state, without gradients (`models/reversible.py:112`), and once in
  `bwd.recompute`, with gradients (`:117`). Together the two passes take 119 ms: invert 57.6 ms, recompute 61.0 ms.
- **Week-2 idea:** compute `f(p)` once with gradients and rebuild the previous state from it:
  `prev = curr_out - 2h * f.detach()`. The maths is the same and the invert pass goes away, about 58 ms. It is
  checked by the existing `reversible.*` and `model.lab_small` pairs, and the HFU formula in `perfkit/metrics.py`
  drops one of the two extra forwards.

## What-if runs

Same GPU, clean steps only, measured before the MoE count fix (step 514 ms then). Each run switches off one
candidate, which bounds what fixing it can give.

| Run | Step (ms) | Change | Peak memory | Shows |
|---|---:|---:|---:|---|
| lab_small | 514 | | 25.1 GiB | |
| AdamW instead of Muon | 357 | -157 ms | 25.3 GiB | the most that part 1 can give |
| Plain residual stack instead of reversible | 389 | -125 ms | 28.2 GiB | the reversible stack saves only 3 GiB here, because the logits dominate memory (a question for the architecture team) |
| Chunked cross-entropy | 565 | +52 ms | 4.2 GiB | part 4: memory can drop 21 GiB, but not with the chunked version |
| Plain NanoGPT (`configs/base.yaml`) | 112 | | 25.8 GiB | nvidia-smi utilization 100%, MFU 12%: the floor of this setup |

Already done in v0: the MoE token counts no longer sync with the host (`models/moe.py`): 649 to 433 syncs per
step, 514 to 497-517 ms across the seven runs since on this GPU.
