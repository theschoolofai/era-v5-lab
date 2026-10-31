# Experiment plan v0

Draft for the Saturday gate. Each arm has a metric, a pass bar, and GPU hours.
The hours below are the CPU smoke test, not the capstone run.

| Arm | What changes | Metric | Pass bar | GPU hours |
|---|---|---|---|---|
| seed-match | Two launches, seed 1234, tiny MoE, a new batch each step | `loss` | The two `losses.txt` files are identical | 0.05 |
| loss-falls | Same tiny run, on a stream of distinct batches | `loss_ntp` | Last step is below the first step, and no value is NaN | 0.05 |
| log-names | Same tiny run | the seven names below | Every step writes all seven. `gpu_alloc_gb` is read from the CUDA allocator and is 0 on CPU | 0.05 |

Names the harness writes, from the Sunday G5 list. G8 still has to confirm units and cadence:

- `tokens_per_second`
- `loss_ntp`
- `loss_mtp` is a second linear head scored at t+2. It is not a stacked MTP block.
- `loss`
- `lr`
- `gpu_alloc_gb` is `torch.cuda.memory_allocated` after the step, in GB. This run is CPU, so the value is 0.
- `gradient_norm` is the total L2 norm of the gradients before clipping, the value that `clip_grad_norm_` returns. Added for G8.

Not in this draft: a production learning rate, a model size, or the KE2 output shape. Those stay empty until TSAI and G4 fill them.
