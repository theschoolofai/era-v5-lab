# Growth strategy (design task 3): approach

**Owner:** Udit Singhania. **Status:** approach note, before implementation; no growth result or production readiness is claimed.
**Due:** Wed 2 Dec 2026, 07:00 IST; 70% checkpoint Mon 30 Nov.

## What it delivers

A path from a small trained dense model to each of the two designs from design task 2: about 30B total with 8%-10% active, and about 100B total with 2%-3% active. The deliverables are the growth recipe, conversion code and tests, small-run comparisons, kill/resume evidence at every tested stage, and a proposed eight-GPU placement for every target-scale stage. We do not train the target models this week.

The recipe covers inherited FFN experts (clone and perturb, never random expert initialization), depth mappings and the output-head interface, expert-count expansion, transfer by tensor role, and strict loading. I also take the **learning-rate reset/warm-up after growth** portion of [#893](https://github.com/theschoolofai/era-v5-lab/pull/893), with a draft policy and test plan by Sunday 29 Nov. General launch-config recommendations remain outside this task.

## Starting point: reuse the lab

Code inspected at `8440077f24e89fab7d8baefa86d857ccd8c2978f`:

- [`week2/model.py`](../../harness/week2/model.py) already provides SwiGLU, GQA/RoPE, KAS V2, routed/shared experts, balancing buffers and expert-load sampling. G5 blocks currently always construct an MoE; there is no growth converter.
- Team 6's [`models/gpt.py`](../../../06-performance/models/gpt.py) already supports dense and MoE SwiGLU. It is a reference to reuse, not a drop-in G5 checkpoint: names, initialization and interfaces differ.
- Reuse [`sizing.py`](../../harness/sizing.py), the G5 sampler, original-byte BPB scorer, and existing native/Team 7 checkpoint integration. Do not replace their contracts or weaken normal resume identity checks.
- [#869](https://github.com/theschoolofai/era-v5-lab/pull/869) provides dry-run records, not the trained weights. Its manifest describes a 176.4M MoE, so it is neither a dense seed nor a model in the required 49M-100M experiment range.
- Audit existing Session 14 artifacts for useful trained sources and conversion checks before training a new seed. For example, [my submission](https://github.com/udisinghania/ERAv5/tree/main/Week%2014) has a different tokenizer, architecture, optimizer and training protocol; its historical results are supporting evidence, not current-capstone results. Availability and compatibility must be verified before selecting a source.

## Reading and proposed choices

| Source | What informs this recipe | Boundary |
|---|---|---|
| [LightningLM, sections 5 and 7](https://arxiv.org/html/2606.07404) | Inherited experts, terminal-aware mappings, target-key construction, role-aware expansion and clone-family starvation. | Test these principles on our architecture. Some reported comparisons are transcript-grade; partial reinitialization is not automatically adopted under this brief. |
| [Depth Delusion](https://arxiv.org/html/2601.20994v1) | Depth/width tradeoffs guide candidate stages. | Its fitted rules are not a universal sparse-model depth limit; coordinate depth and attention period with the target-design owner. |
| [Qwen upcycling](https://qwenlm.github.io/blog/qwen-moe/), [Qwen3](https://arxiv.org/html/2505.09388v1), [Qwen3.5](https://huggingface.co/Qwen/Qwen3.5-397B-A17B) | Inherited/partitioned experts, balancing scope and hybrid layer roles. | A final model configuration is not proof of an undocumented growth path. |
| [Kolibri](https://aleph-alpha.com/downloads/tech-report.pdf), [DeepSeek-V3](https://arxiv.org/html/2412.19437v2), [DeepSeek-V4](https://arxiv.org/html/2606.19348) | Expert/router interfaces, attention patterns, optimization and placement constraints. | Their optimizer splits and weight decay do not override TSAI's current rule. |
| [Expert Upcycling](https://arxiv.org/html/2604.19835v2), [Orthogonal Growth](https://arxiv.org/html/2510.08008v2), [EMO](https://arxiv.org/html/2605.13247v2) | Fixed-top-k expansion, interposed layer copying, and progressive stages/token allocation. | These use different settings. Increasing top-k changes active compute and is a separate choice, not an assumed improvement. |

## Approach

### 1. Freeze the source and stage specifications

Select a compatible, genuinely trained dense checkpoint, or specify the missing small seed training if no suitable source is available. Freeze its model/tokenizer/data identities, code revision, trained-token count and available optimizer state. Do not silently convert between incompatible tokenizers or relabel an MoE checkpoint as dense.

Write a stage table for both target designs: depth, width, attention pattern, routed/shared expert counts and widths, top-k, total/active parameters, source checkpoint and transition. Small experiments test the transformations; target-scale entries are estimates until independently validated.

### 2. Dense FFN to MoE

Copy trained FFN weights into experts and introduce explicit, seeded perturbations. Partition inherited neurons only where required by the proposed expert width; use the same neuron indices for SwiGLU gate/up rows and down columns. Specify fresh router initialization separately from inherited expert weights.

First establish a copy-only reference where exact equivalence is mathematically applicable, then measure the perturbation's effect. **Output scaling must be explicit:** G5 adds shared output to the normalized routed sum. Copying the full dense FFN into both does not preserve the whole layer. G5 also currently gives routed and shared experts the same width; a full-width shared FFN plus narrower routed experts requires explicit support.

Measure immediate held-out loss/BPB change, continued-learning recovery and expert utilization against matched dense continuation. A finite loss or a valid checkpoint alone does not establish successful transfer.

### 3. Depth growth and the head

Write explicit source-to-destination layer maps. Compare stack/reentry and interposed-copy candidates at the same destination shape where compatible with attention roles and period. Include the briefing's case of an interior-ending mapping whose short-run loss is better than a trained-terminal-ending mapping.

Do not choose by the last training loss alone. The proposed default is to preserve the trained terminal layer; an interior-ending candidate needs deliberate head adaptation and held-out revalidation before adoption. Ending on the same source layer does not itself guarantee an unchanged hidden-state distribution. Specify the adaptation policy and its token/LR cost in the test plan.

### 4. Expert-count expansion

Clone trained experts into named families, perturb them reproducibly, and explicitly map router rows and balancing buffers. Start with a **fixed-top-k expansion candidate** to study added capacity without silently increasing active FFN compute. Even exact clones can crowd out other source families under top-k, so whole-model function preservation must be measured, not assumed.

Coordinate with Deepjyoti's [#892](https://github.com/theschoolofai/era-v5-lab/pull/892): I provide the conversion, source-to-clone map and reproducible checkpoint/config; the proposed split leaves routing-window implementation and balance recommendation with his router task. Agree sampling semantics, window length, shared source, seeds and metrics before a joint comparison. Record family-level utilization and zero-token experts, not just a model-wide average. Reuse the same evidence in the two reports rather than duplicate runs.

### 5. Strict transfer, optimizer state and LR

Construct each converted checkpoint by walking the **target** state. Every parameter and persistent buffer has a recorded action: copy, layer map, expert map, partition, perturb or explicit initialization. Audit head/embedding/auxiliary tensors separately; matching shapes are not enough. Require strict key/shape/dtype checks and mapped-value checks. Explicitly populate compatibility buffers such as `router_bias`, rather than relying on the loader to fill omissions.

Distinguish two operations:

- **Architecture transition:** new stage identity and lineage; explicit transfer/reset policy for unchanged and expanded optimizer state, the data cursor, schedule progress, post-growth peak LR and re-warm duration. Determine this policy before runs; an Adam-moment mapping is not automatically a valid Muon-buffer mapping.
- **Ordinary resume within a stage:** restore model, Muon momentum, AdamW state, CPU/CUDA/Python/NumPy RNG, sampler position, progress and schedule. Do not restart warm-up or silently reset state.

Follow TSAI's 28 Nov rule: every 2D weight matrix uses Muon by shape, the small 1D group uses AdamW, no Muon weight decay, no SGD or frozen 1D parameters, and report optimizer step-time share. At the inspected revision G5 still has the older grouping. Coordinate TSAI's update and the idle-expert policy from [#875](https://github.com/theschoolofai/era-v5-lab/pull/875); Deepjyoti owns its investigation. The G10 helper in [#882](https://github.com/theschoolofai/era-v5-lab/pull/882) is draft supporting work, not a landed G5 update. D3/D4 ([#826](https://github.com/theschoolofai/era-v5-lab/pull/826), [#847](https://github.com/theschoolofai/era-v5-lab/pull/847)) remain separate drafts, not growth dependencies to assume merged.

### 6. Eight-GPU stage mapping

For each target-scale stage, show experts per GPU, placement of shared/dense components, proposed sharding/parallelism and redistribution at growth. Expert counts must divide evenly across eight. Estimate weights, gradients, actual Muon/AdamW state, activations, buffers, communication and runtime headroom against the one-node, 8 x 80 GB planning assumption. Divisibility alone does not establish fit; local tests do not establish distributed throughput or bitwise replay after changing layout.

## Test and evidence plan

| Check | Acceptance evidence |
|---|---|
| Transfer correctness | Every destination key/buffer and source omission accounted for; strict load and role/value checks; missing/misnamed mappings fail. Source artifact remains unchanged. |
| Upcycling | Copy-reference equivalence where applicable; perturbation receipt; before/after BPB and matched continuation. Report output scaling and active-compute differences. |
| Depth mapping | Explicit maps, matched destination shape/data/budget, held-out results and head policy; report rejected mappings too. |
| Expert expansion | Parent-family map, routing/update exposure over time, BPB and cost; distinguish nominal from utilized capacity. |
| Kill/resume at every tested stage | Separate interrupted and uninterrupted processes; matching restored state, next batches and continuation in the same supported environment, including nonempty Muon momentum. Test an interrupted conversion's atomic publication/skip behavior too. |
| LR after growth | Recorded peak rate, schedule progress and re-warm; resume does not repeat the transition. Any compared LR policies use otherwise matched conditions. |
| Reference comparison | Reproduction commands, input/output hashes and all differences from the named check. |

Architecture comparisons follow the briefing: **49M-100M parameters, fixed 100M-500M-token budgets, at least two training seeds, same data order, same held-out bytes, one change at a time**. Report total and active counts, BPB, useful tokens/s, peak memory and optimizer time. State incremental and cumulative token budgets, source-training cost and any reused controls. Mechanics smokes are labelled separately, not substituted for architecture results. Exact shapes, run counts, token allocations and numerical tolerances are frozen in the experiment plan before expensive runs; no result-dependent thresholds.

Freeze and hash inputs, prove them on a sample and measure rate before scaling. Every stage has a manifest and completion/skip records; interruption resumes completed work and only affected stages rerun. Preserve supplied dedup/overlap evidence; perform any new overlap check in the tokenization pass. Report idle time and cause. Negative results and limits concerning scale, depth and data mix are deliverables.

## Dependencies and open decisions

- **Design 1/2 owner:** draft specifications and attention motifs for both targets. Prototype mechanics need not wait for final sizes.
- **Deepjyoti:** agree the post-growth routing experiment boundary and LR/schedule interface with #892/#893. Freeze one loader/data-order configuration alongside #890/#891 for comparisons.
- **TSAI/G5 optimizer maintainer:** the shape-based optimizer revision and agreed idle-expert behavior before freezing a training baseline.
- **Teams 6/7:** loader limits and memory/topology/sharding constraints for the final stage table. Reuse existing contracts; request only missing details.
- **Team 9:** existing held-out artifacts/checks, and clarification only where the public evaluation contract leaves a gap.
- **Local decisions:** source checkpoint compatibility; small-model dimensions/growth factors; perturbation/state/LR policies; Kaggle hardware/quota and measured run budget. No target-model GPU allocation is assumed.

## Plan and dates

| By (IST) | Deliverable |
|---|---|
| Sat 28 Nov | Approach note; identify source artifacts, candidate transitions and dependencies. |
| Sun 29 Nov | Draft LR transition policy/test plan for #893; source decision and explicit conversion/experiment matrix. |
| Mon 30 Nov | 70% checkpoint against agreed deliverables: core conversion/strict-loading and recovery checks, with initial comparison evidence. Report compute/dependency shortfalls early; do not count a plan as completed experiments. |
| Tue 1 Dec | Complete comparisons and recovery evidence; both target-stage/placement tables; reproduce and review differences. |
| Wed 2 Dec, 07:00 | Final growth recipe, code/tests and evidence PR. No new work in TSAI's review window. |

## What this cannot establish

Small tests do not establish final 30B/100B quality, production memory/throughput, target-scale router specialization or multi-GPU replay. Historical assignments and another report's measurements are not our results. Final target recipes depend on the design and hardware inputs above; every untested estimate or unresolved choice stays labelled.
