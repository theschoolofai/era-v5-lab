# Memory budget and "fit more" (Lab 5, design tasks 1 and 2)

Owner: Team 07 lead. Due Wed 2 Dec 2026, 7:00 AM IST.

**Planning assumptions, not decisions:** one node, 8 GPUs with 80 GB each (Lab 5 brief). Mixed precision with
bf16 weights, an fp32 master copy and bf16 gradients. TSAI's hybrid optimizer: Muon on every 2D matrix, AdamW only
on the small 1D group (under 1% of the parameters, left out). Every number below comes from one command:

```
cd teams/07-infrastructure
python support/cost/memory_budget.py            # --gpus, --gb-per-gpu and --reserve-gb change the node
```

> **In simple words.** Each parameter costs 16 bytes with Adam (2 bf16 weight, 4 fp32 master, 2 bf16 gradient,
> 8 for two moments) and 12 bytes with Muon (one momentum buffer instead of two). The node has 640 GB. So even
> before activations, Adam states fit at most about 37B parameters, and Muon about 49B, and only if every
> state is sharded over the 8 GPUs (ZeRO-3 / FSDP). Activations then decide the rest: at 4k and 8k tokens they
> fit only with activation recompute.

## 1. Where each size stops fitting

| Total size | Adam | Muon | What it takes |
|---|---|---|---|
| **25B** | fits only with ZeRO-3 + full recompute (56 GB at 4k, 62 GB at 8k) | same (44 GB at 4k, 50 GB at 8k) | sharding everything, plus recompute. Without recompute the activations alone are 59 GB (4k) and 118 GB (8k) per GPU. |
| **50B** | **does not fit**: 108 GB per GPU at 4k even with ZeRO-3 + recompute | **does not fit**: 83 GB at 4k (states alone are 75 GB) | one more saving from section 3: drop the fp32 master (58 GB at 4k), or offload the optimizer state to CPU RAM (33 GB at 4k, 400 GB of CPU RAM). |
| **100B** | **does not fit**: states are 1,600 GB, 2.5 x the node | **does not fit**: states are 1,200 GB | only with the master and optimizer state in CPU RAM (62 GB at 4k, 73 GB at 8k per GPU; 800 GB of CPU RAM with Muon). The 8k row is at the edge. |
| **150B** | **does not fit** | **does not fit** | not even with optimizer offload (89 GB at 4k). Needs the weights offloaded too (ZeRO-Infinity to CPU RAM or NVMe) or more than one node. Training from scratch at this size is a multi-node job. |

The activation rows assume dense-equivalent shapes (12 x L x h^2 = total size). An MoE of the same total size has
a smaller width and depth, so its activations are smaller and these rows are an upper bound. The state rows do not
shrink for an MoE: every expert's weights, gradients and optimizer state stay in memory whatever the routing.
When Team 5 gives the real shapes, change `SHAPES` in the script and rerun.

## 2. The budget table

Node: 8 GPUs x 80 GB = 640 GB. Usable per GPU: 74 GB (80 - 6 reserve).

### A. Model states for the whole model, GB (before any sharding)

| Total params | bf16 weights | fp32 master | bf16 gradients | Adam state | Muon state | Total, Adam (16 B/param) | Total, Muon (12 B/param) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 25B | 50 | 100 | 50 | 200 | 100 | 400 | 300 |
| 50B | 100 | 200 | 100 | 400 | 200 | 800 | 600 |
| 100B | 200 | 400 | 200 | 800 | 400 | 1600 | 1200 |
| 150B | 300 | 600 | 300 | 1200 | 600 | 2400 | 1800 |

### B. Activations per GPU, one sequence (b = 1), GB

| Total params | Shape (h, L) | 4k | 4k, recompute | 8k | 8k, recompute |
|---|---|---:|---:|---:|---:|
| 25B | 5120, 80 | 59.2 | 6.2 | 118.4 | 12.4 |
| 50B | 7168, 80 | 82.0 | 7.8 | 164.0 | 15.7 |
| 100B | 8192, 124 | 143.6 | 11.6 | 287.2 | 23.2 |
| 150B | 10240, 120 | 173.3 | 13.6 | 346.6 | 27.3 |

### C. Per GPU with Adam: states + activations (b = 1), GB, against 74 GB

| Total params | Sharding | States | + 4k | + 4k, recompute | + 8k | + 8k, recompute |
|---|---|---:|---:|---:|---:|---:|
| 25B | none (every GPU holds everything) | 400 | 459.2 **no** | 406.2 **no** | 518.4 **no** | 412.4 **no** |
| 25B | ZeRO-1 (optimizer state + master sharded) | 138 | 196.7 **no** | 143.7 **no** | 255.9 **no** | 149.9 **no** |
| 25B | ZeRO-2 (+ gradients sharded) | 94 | 152.9 **no** | 100.0 **no** | 212.1 **no** | 106.2 **no** |
| 25B | ZeRO-3 / FSDP (everything sharded) | 50 | 109.2 **no** | 56.2 fits | 168.4 **no** | 62.4 fits |
| 50B | none (every GPU holds everything) | 800 | 882.0 **no** | 807.8 **no** | 964.0 **no** | 815.7 **no** |
| 50B | ZeRO-1 (optimizer state + master sharded) | 275 | 357.0 **no** | 282.8 **no** | 439.0 **no** | 290.7 **no** |
| 50B | ZeRO-2 (+ gradients sharded) | 188 | 269.5 **no** | 195.3 **no** | 351.5 **no** | 203.2 **no** |
| 50B | ZeRO-3 / FSDP (everything sharded) | 100 | 182.0 **no** | 107.8 **no** | 264.0 **no** | 115.7 **no** |
| 100B | none (every GPU holds everything) | 1600 | 1743.6 **no** | 1611.6 **no** | 1887.2 **no** | 1623.2 **no** |
| 100B | ZeRO-1 (optimizer state + master sharded) | 550 | 693.6 **no** | 561.6 **no** | 837.2 **no** | 573.2 **no** |
| 100B | ZeRO-2 (+ gradients sharded) | 375 | 518.6 **no** | 386.6 **no** | 662.2 **no** | 398.2 **no** |
| 100B | ZeRO-3 / FSDP (everything sharded) | 200 | 343.6 **no** | 211.6 **no** | 487.2 **no** | 223.2 **no** |
| 150B | none (every GPU holds everything) | 2400 | 2573.3 **no** | 2413.6 **no** | 2746.6 **no** | 2427.3 **no** |
| 150B | ZeRO-1 (optimizer state + master sharded) | 825 | 998.3 **no** | 838.6 **no** | 1171.6 **no** | 852.3 **no** |
| 150B | ZeRO-2 (+ gradients sharded) | 562 | 735.8 **no** | 576.1 **no** | 909.1 **no** | 589.8 **no** |
| 150B | ZeRO-3 / FSDP (everything sharded) | 300 | 473.3 **no** | 313.6 **no** | 646.6 **no** | 327.3 **no** |

### C. Per GPU with Muon: states + activations (b = 1), GB, against 74 GB

| Total params | Sharding | States | + 4k | + 4k, recompute | + 8k | + 8k, recompute |
|---|---|---:|---:|---:|---:|---:|
| 25B | none (every GPU holds everything) | 300 | 359.2 **no** | 306.2 **no** | 418.4 **no** | 312.4 **no** |
| 25B | ZeRO-1 (optimizer state + master sharded) | 125 | 184.2 **no** | 131.2 **no** | 243.4 **no** | 137.4 **no** |
| 25B | ZeRO-2 (+ gradients sharded) | 81 | 140.4 **no** | 87.5 **no** | 199.6 **no** | 93.7 **no** |
| 25B | ZeRO-3 / FSDP (everything sharded) | 38 | 96.7 **no** | 43.7 fits | 155.9 **no** | 49.9 fits |
| 50B | none (every GPU holds everything) | 600 | 682.0 **no** | 607.8 **no** | 764.0 **no** | 615.7 **no** |
| 50B | ZeRO-1 (optimizer state + master sharded) | 250 | 332.0 **no** | 257.8 **no** | 414.0 **no** | 265.7 **no** |
| 50B | ZeRO-2 (+ gradients sharded) | 162 | 244.5 **no** | 170.3 **no** | 326.5 **no** | 178.2 **no** |
| 50B | ZeRO-3 / FSDP (everything sharded) | 75 | 157.0 **no** | 82.8 **no** | 239.0 **no** | 90.7 **no** |
| 100B | none (every GPU holds everything) | 1200 | 1343.6 **no** | 1211.6 **no** | 1487.2 **no** | 1223.2 **no** |
| 100B | ZeRO-1 (optimizer state + master sharded) | 500 | 643.6 **no** | 511.6 **no** | 787.2 **no** | 523.2 **no** |
| 100B | ZeRO-2 (+ gradients sharded) | 325 | 468.6 **no** | 336.6 **no** | 612.2 **no** | 348.2 **no** |
| 100B | ZeRO-3 / FSDP (everything sharded) | 150 | 293.6 **no** | 161.6 **no** | 437.2 **no** | 173.2 **no** |
| 150B | none (every GPU holds everything) | 1800 | 1973.3 **no** | 1813.6 **no** | 2146.6 **no** | 1827.3 **no** |
| 150B | ZeRO-1 (optimizer state + master sharded) | 750 | 923.3 **no** | 763.6 **no** | 1096.6 **no** | 777.3 **no** |
| 150B | ZeRO-2 (+ gradients sharded) | 488 | 660.8 **no** | 501.1 **no** | 834.1 **no** | 514.8 **no** |
| 150B | ZeRO-3 / FSDP (everything sharded) | 225 | 398.3 **no** | 238.6 **no** | 571.6 **no** | 252.3 **no** |

### D. Largest total size whose states fit, before activations, B params

| Optimizer | none (every GPU holds everything) | ZeRO-1 (optimizer state + master sharded) | ZeRO-2 (+ gradients sharded) | ZeRO-3 / FSDP (everything sharded) |
|---|---:|---:|---:|---:|
| Adam | 4.6 | 13.5 | 19.7 | 37.0 |
| Muon | 6.2 | 14.8 | 22.8 | 49.3 |

### E. Fit more: one change at a time, ZeRO-3 + full recompute, per GPU GB (CPU RAM column: per node)

| Setting | GPU B/param | 25B 4k | 25B 8k | 50B 4k | 50B 8k | 100B 4k | 100B 8k | 150B 4k | 150B 8k | CPU RAM, 25 / 50 / 100 / 150B |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Muon, ZeRO-3 (reference) | 1.50 | 43.7 fits | 49.9 fits | 82.8 **no** | 90.7 **no** | 161.6 **no** | 173.2 **no** | 238.6 **no** | 252.3 **no** | - GB |
| + no fp32 master (bf16 weights, stochastic rounding) | 1.00 | 31.2 fits | 37.4 fits | 57.8 fits | 65.7 fits | 111.6 **no** | 123.2 **no** | 163.6 **no** | 177.3 **no** | - GB |
| + no fp32 master, 8-bit Muon momentum | 0.62 | 21.8 fits | 28.1 fits | 39.1 fits | 46.9 fits | 74.1 **no** | 85.7 **no** | 107.4 **no** | 121.0 **no** | - GB |
| + master and momentum offloaded to CPU RAM | 0.50 | 18.7 fits | 24.9 fits | 32.8 fits | 40.7 fits | 61.6 fits | 73.2 fits | 88.6 **no** | 102.3 **no** | 200 / 400 / 800 / 1200 GB |
| Adam, master and moments offloaded to CPU RAM | 0.50 | 18.7 fits | 24.9 fits | 32.8 fits | 40.7 fits | 61.6 fits | 73.2 fits | 88.6 **no** | 102.3 **no** | 300 / 600 / 1200 / 1800 GB |

Reading section C. "States" is weights + master + gradients + optimizer state on one GPU. The four columns add
the activations of one sequence. Logits for the loss (fp32, vocabulary 131,072) are in the activations: 2.1 GB at
4k, 4.3 GB at 8k.

## 3. Fit more: published ways to fit a bigger model on the same node

| Method | What it saves | Cost in speed | Cost in quality | Notes for us |
|---|---|---|---|---|
| **Sharded states** (ZeRO-1/2/3, FSDP; Rajbhandari et al. 2020) | ZeRO-1 shards optimizer state + master, ZeRO-2 adds gradients, ZeRO-3 adds weights: up to 1/8 of the states on 8 GPUs (section C) | ZeRO-1/2: small, same traffic as data parallel. ZeRO-3: about 1.5 x the communication (weights gathered each forward and backward); on one node over NVLink this is usually hidden | none | **Muon caveat:** Newton-Schulz needs the whole matrix. Shard Muon state by whole matrices (each GPU owns some matrices), or gather a matrix before its update. `results/layouts.md` already marks the ZeRO rows as reference only for Muon. |
| **Muon instead of Adam** (TSAI's choice) | one momentum buffer instead of two: 12 instead of 16 B/param, about 33% more model per node (section D) | Newton-Schulz adds compute per optimizer step (`results/layouts.md`: 2.26 TFLOP per step at T2) | TSAI's decision | already decided |
| **Activation recompute** (Chen et al. 2016; selective recompute, Korthikanti et al. 2022) | full recompute keeps one tensor per layer: 59 to 6 GB per GPU at 4k for 25B (section B) | full: about one extra forward pass, roughly 30% more compute. Selective (only attention internals): a few % | none | needed for every size here |
| **Reversible layers** (RevNet, Gomez et al. 2017; Reformer, Kitaev et al. 2020) | activations no longer grow with depth: each layer's input is rebuilt from its output in the backward pass | about one extra forward pass, like full recompute | architecture change: must be tested at small scale first (lab rules) | Team 6's week-1 lab model used a reversible stack (`teams/06-performance/results/baseline_v0.md`). A choice for Team 5, not a memory switch |
| **No fp32 master copy** (bf16 weights with stochastic rounding or Kahan summation) | 4 B/param: 50B goes from 83 to 58 GB per GPU at 4k (section E) | none to small | small risk: needs a small-model test against fp32 master, same seed and data | a decision for Team 5 and TSAI |
| **8-bit optimizer state** (Dettmers et al. 2021, 8-bit Adam) | 3 of the 4 bytes of each moment; with no master, 50B fits at 39 GB per GPU | small | near-equal for Adam in the paper; for Muon momentum not published that we know of: test first | test on the small model before using |
| **Low-rank optimizer state** (GaLore, Zhao et al. 2024) | optimizer state kept in a low-rank projection | extra projection work | small loss reported at some scales | does not combine directly with Muon's orthogonal update |
| **Offload to CPU RAM** (ZeRO-Offload, Ren et al. 2021) | master + optimizer state live in CPU RAM: GPU needs 0.5 B/param (section E). 100B fits at 62 GB per GPU (4k) | large: the optimizer step runs on the CPU or crosses PCIe every step; often several times slower | none | needs 800 GB (Muon) to 1.2 TB (Adam) of CPU RAM at 100B. Ask TSAI for the node's RAM |
| **Offload weights too, to CPU RAM or NVMe** (ZeRO-Infinity, Rajbhandari et al. 2021) | only the layer being computed stays on the GPU: 150B becomes possible | very large: bound by PCIe and NVMe bandwidth | none | for a test, not a production run |
| **Compressed frozen base + small trainable adapters** (LoRA, Hu et al. 2021; QLoRA, Dettmers et al. 2023) | base in 4 bits (0.5 B/param), frozen; only the adapters have gradients and optimizer state. 150B base is about 75 GB on the node | fast | **not pre-training**: it adapts an existing model. Quality depends on the base | fits post-training (Team 10) or a continued-training stage, not the first pre-training run |
| **Gradient accumulation** | smaller micro-batch, same global batch: activations scale with the micro-batch | more steps per update, less overlap | none | already used (`b`, `m` in `results/layouts.md`) |
| **Tensor, sequence or pipeline parallel** (Megatron-LM; Shoeybi et al. 2019) | splits weights and activations across GPUs | more communication; pipeline adds bubbles | none | needs a trainer that supports it. Today's `train_week2.py` is one process on one GPU (`slurm/mainrun.sbatch`, #820) |
| **Expert parallel** (MoE) | each GPU holds some experts | all-to-all traffic per MoE layer | none | Team 5's model is an MoE: the natural split once the trainer is distributed |

## 4. What this means for the main run

1. Today's trainer is one process on one GPU. One 80 GB GPU holds at most about **4.6B** parameters with Adam
   and **6.2B** with Muon, before activations (section D, "none"). Anything bigger needs a distributed trainer
   first. This is decision D2 in `docs/mainrun_command_checklist.md` (#819).
2. On one 8-GPU node with a distributed trainer: **25B** is the largest listed size that fits as plain mixed
   precision (ZeRO-3 + recompute). **50B** needs one more change (no fp32 master, or optimizer offload).
   **100B** needs optimizer offload. **150B** needs more than one node.
3. Each memory-saving step that changes the numbers (no master, 8-bit state, reversible layers) needs a
   small-model test first, same seed and data, as the lab's architecture rules say.

## 5. Not covered

- Real Team 5 shapes for config v1 at these sizes. The script takes them as input.
- The KE2 / KAS head and router memory, which are small next to the experts.
- Measured peak memory on a GPU. The one measured row we have (T2, AdamW, `results/layouts.md`) was 3% above
  the formula. A GPU job at one size would check the activation formula.
