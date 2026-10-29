# Bench report — h200_v1_2gpu_comm

**GPU:** NVIDIA H200  |  **dtype:** bf16  |  **B x T:** 32 x 512  |  **torch:** 2.11.0+cu128
**commit:** `19221759f9d820ce0563d5d2f44e22eac0de53d2`  |  **tag:** h200_v1_2gpu_comm

## Step (clean)

- median: 455.557 ms
- p10..p90: 308.697 .. 653.536 ms
- tokens/s: 35,965
- MFU: 1.2%  |  HFU: 1.5%

## Diagnostics

### CUDA timing-event allocations

- [OK] clean: events_created_during_steps=0
- [OK] communication.max_rank: events_created_during_steps=0

### Benchmark warnings

- [warn] rule 3b: checkpoint not measured; add checkpoint to --modes

## Five slowest leaf parts

