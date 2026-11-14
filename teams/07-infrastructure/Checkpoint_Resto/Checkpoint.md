# ckpt.py — State Checkpointing & Restoration 
For large-scale training preemption or hardware faults may interrupt a run. ckpt.py is intended to save and restore the state needed to resume training with minimal divergence.
## Key design patterns 
- Comprehensive state capture: Saves model weights (state_dict), optimizer state (including momentum or variance buffers), and random-number-generator states for Python, NumPy, and PyTorch. 
- Atomic file writes: Writes to a temporary file and then uses os.replace to reduce the chance of leaving a partially written checkpoint. 
- CPU-safe restore: Loads checkpoint tensors onto CPU first using map_location='cpu' to help avoid GPU-memory spikes during recovery. 
### Reproducibility caveat: Restoring the saved state is necessary but may not guarantee bit-for-bit identical continuation on every distributed setup. Exact trajectory matching can depend on deterministic kernels, data-loader/sampler position, gradient-scaler state, scheduler state, distributed RNG state, software versions, and hardware/runtime behavior.