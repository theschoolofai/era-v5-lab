# Deletion Tuning, LoRA, and full fine-tuning

Port of arXiv 2611.10866, read from `agentic-learning-ai-lab/deleting-weights` (`src/learnable_sparsity`, MIT). The code is `sft/deletion_tuning.py`.

The frozen weight is multiplied by `sigmoid(alpha(t) * G)` in training and by `1[G > 0]` at evaluation. `alpha` runs from `1e3` to `1e4`. Logits start from the Wanda score in equation (8), with `eta = 1/2048`. The SFT objective adds `-1e-5 * ||masked weight||^2`. The target matrix in this check is the gate.

## Equal steps on one synthetic slice

`sft/dt_vs_fft.py --steps 30 --seed 0`. Thirty-two synthetic rows. No benchmark text. The log is `jobs/2026-11-14-dt-vs-fft.log`.

| Method | Steps | Loss at step 0 | Loss at step 30 | Base weight changed | Hard-mask deleted fraction |
| --- | ---: | ---: | ---: | --- | ---: |
| Deletion Tuning | 30 | 0.020717 | 0.020717 | no | 0 |
| LoRA, rank 1, gate only | 30 | 0.020719 | 0.020687 | no |  |
| Full fine-tuning | 30 | 0.020719 | 0.002844 | yes |  |

Full fine-tuning is the method that moves the loss. Deletion Tuning's base stays frozen, and on this 4 by 4 gate the Wanda prior deletes nothing, so the soft mask is already saturated and the loss stays flat. That is a check of the update rule, not the paper's scale result.

The deletion-fraction sweep and the layer sweep (MLP gate only, all MLP, attention) are the next rows in this file. They are not filled yet.

The reproduction request is `jobs/2026-11-14-dt-vs-fft.md`. A run on one SFT data v1 slice and a small open model waits until that slice is in the repo.
