# Lab 5 optimizer grouping (TSAI, 28 Nov)

For `optim.name: muon`, tensor shape determines membership, regardless of name:

| Shape | Optimizer |
| --- | --- |
| Every 2D matrix | Muon, `muon_lr`, zero weight decay |
| 1D gains, biases and priors; 0D scalar gates | AdamW, `lr`, configured AdamW weight decay |

This includes attention, expert/shared or dense FFN, router, embedding/input projection,
and output-head matrices. In KAS v2, `W_out`, `tok_u` and `tok_c` use Muon;
`beta` and `unigram` use AdamW. No parameters are frozen by the factory.
Higher-rank parameters are rejected explicitly rather than silently assigned to AdamW.
The native factory continues to require a nonempty group for each optimizer.

`router_on_muon` may be omitted or `true`. `false` is rejected for Muon runs.
`head_sgd: true` is also rejected for Muon runs. Both configuration validation and
direct factory/manifest calls reject these legacy exceptions. Explicit `name: adamw`
control experiments, including their optional whole-head SGD ablation, retain their
historical behavior; no trainer defaults are changed.

Previously the Muon factory selected only `blocks.*.weight`, with a router exception.
Embedding and head matrices consequently used AdamW, including KAS matrices whose
names do not end in `.weight`. The manifest now records
`grouping: all_2d_muon_0d_1d_adamw` and counts the actual shape-selected groups.

## Checkpoints

This changes Muon/AdamW membership and optimizer state layout. Start a new run for
the new recipe; old name-grouped optimizer checkpoints are not a supported resume
source. Keep the trainer's normal code/config/artifact identity checks enabled.
There is no state migration, group reinterpretation or identity bypass here.
Same-stage resumes made with this code retain Muon momentum buffers and AdamW
counters. Model weights alone do not substitute for optimizer state on resume.

Muon numerical updates and idle-expert behavior remain the separate scope of #875.
Peak `base_lr` initialization and checkpoint scalar handling remain the separate
scope of #899; this change does not duplicate that fix.
