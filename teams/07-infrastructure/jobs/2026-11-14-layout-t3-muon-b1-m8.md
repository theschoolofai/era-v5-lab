# Layout speed: T3 with Muon, one GPU, b = 1, m = 8

DRAFT. Not submitted. **Blocked:** `t3_muon.yaml` does not exist yet. Team 5 must add it first; its text is at the end of this request.

```text
Team:            07-infrastructure
Owner:           <your name as on Axiom> (<github handle>)
Lead approval:   pending, sureshmantha
Question:        What are the tokens per second and the memory of T3 with Muon on one GPU at 1 sequence per forward and 8 forwards per optimizer step?
Script:          teams/05-architecture/harness/train_week2.py   (Team 5, merged; not edited)
Command:         python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/t3_muon.yaml --runtime teams/05-architecture/configs/runtime.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout.jsonl --device cuda --seed 1234 --smoke --smoke-steps 110 --no-checkpoint --out ./out/t3-b1-m8
Config:          teams/05-architecture/configs/arms/t3_muon.yaml + teams/05-architecture/configs/runtime.yaml
Inputs:          the TSAI-staged bundle of official job #310: tokenizer v0, its P32 raw byte table, train and held-out JSONL
Hardware:        1 GPU with native bf16 and at least 24 GiB (peak estimate 11.5 GiB)
Max time:        20 minutes
Precision:       bf16 (autocast, fp32 weights, as the harness does)
Measures:        median and p10/p90 of tokens_per_second over steps 11-110, median perf/step_ms, median gpu_alloc_gb, out of memory yes/no, GPU name
Expected result: gpu_alloc_gb about 5.2 GiB; peak about 11.5 GiB, so no out of memory on the stated GPU; tokens/s has no estimate (see below)
Outputs:         out/t3-b1-m8/metrics.jsonl, summary.json, manifest.json (under 5 MB); no checkpoint
Test log:        pending: the owner's EC2 run of this command
```

## What this run is

One row of `results/layouts.md`, section 2: T3 (10 layers, width 640, 391.5M parameters) with Muon, as config v1 (PR 447) decides, at
b = 1 sequences of 2,048 tokens per forward and m = 8 forwards per optimizer step, 16,384 tokens
per step. In the command, the runtime's micro-batch 1 and the arm's batch 8 give b = 1, m = 8. 

`--smoke` is needed: without it the harness refuses to run while the approvals in `runtime.yaml` are pending.
It keeps the shape, bf16 on CUDA and Muon, sets 110 steps and marks the output as not a quality result.

The memory estimates are from `python layout/parallel_layout_v1a.py --arm ../05-architecture/configs/arms/t3.yaml
--layout b=1,m=8` with config v1 as in PR 447. `gpu_alloc_gb` is the memory still allocated at the end of a
step: weights, gradients, Muon and AdamW state, and the bf16 logits of the last micro-batch. The harness does not
log the peak; out of memory, or none, checks it. Tokens/s is what the job measures; it has no estimate because
the speed of Team 5's model with Muon was never measured.

The same question at the other splits and shape: [t2-b1-m8](2026-11-14-layout-t2-muon-b1-m8.md), [t2-b1-m1](2026-11-14-layout-t2-muon-b1-m1.md), [t2-b2-m1](2026-11-14-layout-t2-muon-b2-m1.md), [t2-b4-m1](2026-11-14-layout-t2-muon-b4-m1.md), [t2-b8-m1](2026-11-14-layout-t2-muon-b8-m1.md), [t3-b1-m1](2026-11-14-layout-t3-muon-b1-m1.md), [t3-b2-m1](2026-11-14-layout-t3-muon-b2-m1.md), [t3-b4-m1](2026-11-14-layout-t3-muon-b4-m1.md), [t3-b8-m1](2026-11-14-layout-t3-muon-b8-m1.md).

## Needs from Team 5 before this runs

`teams/05-architecture/configs/arms/t3_muon.yaml`:

```yaml
# T3 Muon arm for Team 7's one-GPU layout speed job. muon_lr 0.01 is copied from exp2_muon.yaml: provisional, not a decision.
inherit: t3.yaml
intended:
  arm: t3-muon
  official_step_time: false
  comparison_final: false
optim:
  name: muon
  lr: 0.001
  muon_lr: 0.01
```
