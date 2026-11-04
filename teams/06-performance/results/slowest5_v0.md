# The five slowest parts (v0)

GPU: NVIDIA A100-SXM4-40GB, bf16, B=16, T=256, `configs/base.yaml`, commit `f1ed7f2`, run `baseline_v0`.
Step 42.9 ms (median of 100 steps). A part is a region summed over the 6 layers. Each trace is one occurrence
(layer 3, or the whole step for the optimizer) cut from the profiler trace: open it in https://ui.perfetto.dev or
`chrome://tracing`. It shows when the CPU queued the work and when the GPU ran it, with arrows from each launch
to its kernel. The traces and run files are in the gist https://gist.github.com/vaibh27/574990425455e4a9cb64822f14e3d85b (the run files are not
committed). The profiler slows the CPU side (the traced step takes 84 ms), so CPU times in the traces are
upper bounds; the ms column is from the timed run without the profiler.

**Two causes behind most of it.** The head and loss are memory-bound: the fp32 logits of the 131,072-token
vocabulary are 2.1 GB per step, and parts 1 and 2 (54% of the step) are the GPU moving them. The rest is many
small kernels: 1,392 kernels per step, with the GPU busy 50% of the step. Parts 3 to 5 launch hundreds of kernels
of a few microseconds each.

| # | Part | ms | % of step | Kernels in trace | CPU time in trace | GPU kernel time in trace | Trace |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | `bwd:head+loss` | 12.34 | 28.8% | 11 | 1.0 ms | 12.4 ms | `baseline_v0_parts_1_bwd_head+loss.json` |
| 2 | `fwd:head+loss` | 10.67 | 24.9% | 7 | 0.5 ms | 10.7 ms | `baseline_v0_parts_2_fwd_head+loss.json` |
| 3 | `bwd:block*.grad` | 5.10 | 11.9% | 50 (layer 3) | 3.4 ms (layer 3) | 0.8 ms (layer 3) | `baseline_v0_parts_3_bwd_block3.grad.json` |
| 4 | `opt:opt.polar_muon_adamw` | 4.86 | 11.3% | 389 | 16.0 ms | 4.6 ms | `baseline_v0_parts_4_opt_opt.polar_muon_adamw.json` |
| 5 | `opt:opt.muon.ns` (inside part 4) | 3.11 | 7.2% | 360 (4 calls) | 13.7 ms | 2.1 ms | `baseline_v0_parts_5_opt_opt.muon.ns.json` |

Parts 1 to 4 together: 33.0 ms, 77% of the step (part 5 is inside part 4). Part 5 is a level-3 number from the
separate inner pass and reads higher than the whole Muon update (`opt:opt.muon`, 2.32 ms, level 2).

## 1. Head and loss, backward: `bwd:head+loss`, 12.3 ms (29%)

- **What the trace shows:** GPU-bound; the CPU queues 11 kernels in 1.0 ms. `cunn_SoftMaxBackward` alone takes
  6.3 ms, plus 2.4 ms of bf16 casts, 1.4 ms of fills and 1.1 ms for the head's weight-gradient matmul. The fp32
  logits are 4,096 x 131,072 = 2.1 GB. The softmax backward reads two such tensors and writes one, 6.4 GB in
  6.3 ms: 1.0 TB/s, about 66% of the A100's 1.55 TB/s.
- **Cause:** memory-bound. The full fp32 logits are built, stored and read back; the matmuls are a small part.
- **Week-2 idea:** fused linear cross-entropy, which never stores the logits (Liger Kernel's
  `FusedLinearCrossEntropy` or Apple's Cut Cross-Entropy). It becomes `model.ce_impl: fused`, tested by a
  `model.base.fused` pair like `model.base.chunked`.

## 2. Head and loss, forward: `fwd:head+loss`, 10.7 ms (25%)

- **What the trace shows:** GPU-bound; 7 kernels queued in 0.5 ms. `cunn_SoftMaxForward` takes 6.2 ms, the copy
  of the bf16 logits to fp32 2.9 ms, and the head matmul 1.5 ms.
- **Cause:** memory-bound, the same logits as part 1. With `model.mtp=true` the second head doubles it
  (`fwd:head+loss` 21.3 ms, `bwd:head+loss` 24.6 ms in `mtp_v0.json`, gist above).
- **Week-2 idea:** the same fused linear cross-entropy as part 1 removes the fp32 copy and the stored softmax
  input; one change speeds up parts 1 and 2 together.

## 3. Local backward of each reversible block: `bwd:block*.grad`, 5.1 ms (12%)

- **What the trace shows:** layer 3's local backward is 50 kernels (attention, MLP, layer norms, the midpoint
  arithmetic), the largest 0.095 ms, 0.8 ms of GPU work in all. With the profiler on the CPU takes 3.4 ms to
  queue them. In the timed run the part takes 0.85 ms per layer, close to its GPU time, because the CPU is still
  ahead after the GPU-heavy head backward.
- **Cause:** many small kernels; the GPU work per kernel is a few microseconds at this width (256).
- **Week-2 idea:** compile the block's residual function `f` with `torch.compile` (regional compilation: one
  block, reused for all 6) to fuse the element-wise and normalization kernels. Separately, the reversible
  backward computes `f(p)` twice (once in `bwd.invert` without gradients, once in `bwd.recompute` with them);
  one pass with gradients removes the invert pass (`prev = curr_out - 2h * f.detach()`), checked by the existing
  `reversible.*` and `model.base` pairs.

## 4. The optimizer: `opt:opt.polar_muon_adamw`, 4.9 ms (11%)

- **What the trace shows:** 389 kernels. AdamW (embedding, head, norm gains, biases) is `torch._foreach`
  multi-tensor kernels, 2.8 ms of GPU time, mostly the 33.5M-parameter head. Muon is part 5. With the profiler
  on the CPU takes 16 ms to queue the step; without it the part (4.86 ms) is close to its GPU time (4.6 ms) on
  this host.
- **Cause:** AdamW is memory-bound on the head's parameters and state. Muon is launch-bound (part 5).
- **Supporting runs:** before the batched Muon and foreach AdamW the optimizer was about 24 ms of a 71 ms step
  (PR #30 head, same GPU type); now 5.3 ms of 42.9 ms.
- **Week-2 idea:** capture the whole optimizer step as one CUDA graph. It replays the 389 kernels with one launch,
  so the part stops depending on the host CPU (the cause of the Modal repeat-check misses), with a `@pair` test
  against the loop reference.

## 5. Muon Newton-Schulz: `opt:opt.muon.ns`, 3.1 ms (7%, inside part 4)

- **What the trace shows:** 4 calls, one per shape bucket of the block weights; 360 kernels, 2.1 ms of GPU time.
  Each Polar Express iteration is a few batched matmuls on `[n, rows, cols]` plus element-wise ops. The CPU takes
  about 3.4 ms per bucket under the profiler.
- **Cause:** launch-bound: the matrices are small (256 x 256 to 1024 x 256), so each kernel is short.
- **Week-2 idea:** the CUDA graph of part 4 covers it. Without a graph, `torch.compile` of the Newton-Schulz
  iteration fuses its element-wise ops.

## Already done in v0

- **Batched Muon** (`optim.muon_impl: batched`, the week-1 idea for the old slowest part): Muon 24 ms to 2.3 ms;
  step 71 to 43 ms, kernels 3,540 to 1,392, MFU 4.6% to 7.6% (same GPU type, B=16, T=256).
- **foreach AdamW** (`optim.adamw_impl: foreach`) and **batch prefetch** after backward (`data.prefetch: true`).
- The MoE dispatch parts of the old lab model are not in `base.yaml` (`ffn: mlp`); `model.moe.dispatch=sorted`
  is there for MoE configs.
