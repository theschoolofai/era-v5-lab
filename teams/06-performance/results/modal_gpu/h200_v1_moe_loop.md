# Bench report — h200_v1_moe_loop

**GPU:** NVIDIA H200  |  **dtype:** bf16  |  **B x T:** 32 x 512  |  **torch:** 2.11.0+cu128
**commit:** `19221759f9d820ce0563d5d2f44e22eac0de53d2`  |  **tag:** h200_v1_moe_loop

## Step (clean)

- median: 417.591 ms
- p10..p90: 344.154 .. 571.468 ms
- tokens/s: 39,235
- MFU: 1.3%  |  HFU: 1.6%

## Diagnostics

### CUDA timing-event allocations

- [OK] clean: events_created_during_steps=0
- [OK] layer: events_created_during_steps=0
- [OK] layer.inner_pass: events_created_during_steps=0

### Benchmark warnings

- [warn] rule 3b: checkpoint and comm not measured; add checkpoint,comm to --modes
- [warn] 28 gated part(s) have p10..p90 spread > 10%, so may miss the 5% check: data, fwd, fwd:stack, fwd:block0, fwd:block1, fwd:block2 (+22 more)

## Regions

| part | median ms | p90 | % of step | level |
| :--- | ---: | ---: | ---: | ---: |
| data | 0.742 | 0.859 | 0.2 | 1 |
| fwd | 70.891 | 76.435 | 17.0 | 1 |
| fwd:embed | 2.013 | 2.107 | 0.5 | 2 |
| fwd:embed.ke | 1.973 | 2.011 | 0.5 | 3 |
| fwd:stack | 52.572 | 58.127 | 12.6 | 1 |
| fwd:block0 | 5.934 | 7.923 | 1.4 | 2 |
| fwd:block0.ln1 | 0.033 | 0.033 | 0.0 | 3 |
| fwd:block0.attn.qkv | 0.025 | 0.026 | 0.0 | 3 |
| fwd:block0.attn.sdpa | 0.043 | 0.044 | 0.0 | 3 |
| fwd:block0.attn.proj | 0.018 | 0.018 | 0.0 | 3 |
| fwd:block0.ln2 | 0.033 | 0.033 | 0.0 | 3 |
| fwd:block0.moe.router | 0.088 | 0.090 | 0.0 | 3 |
| fwd:block0.moe.dispatch | 4.519 | 7.102 | 1.1 | 3 |
| fwd:block0.moe.dispatch.expert0 | 0.407 | 0.711 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert1 | 0.403 | 0.682 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert2 | 0.638 | 2.906 | 0.2 | 3 |
| fwd:block0.moe.dispatch.expert3 | 0.567 | 0.647 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert4 | 0.599 | 0.796 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert5 | 0.588 | 0.646 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert6 | 0.412 | 0.617 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert7 | 0.344 | 0.591 | 0.1 | 3 |
| fwd:block0.moe.shared | 0.146 | 0.155 | 0.0 | 3 |
| fwd:block1 | 5.442 | 7.501 | 1.3 | 2 |
| fwd:block1.ln1 | 0.059 | 0.062 | 0.0 | 3 |
| fwd:block1.attn.qkv | 0.096 | 0.107 | 0.0 | 3 |
| fwd:block1.attn.sdpa | 0.095 | 0.099 | 0.0 | 3 |
| fwd:block1.attn.proj | 0.053 | 0.060 | 0.0 | 3 |
| fwd:block1.ln2 | 0.044 | 0.046 | 0.0 | 3 |
| fwd:block1.moe.router | 0.198 | 0.206 | 0.0 | 3 |
| fwd:block1.moe.dispatch | 4.353 | 6.314 | 1.0 | 3 |
| fwd:block1.moe.dispatch.expert0 | 0.409 | 0.687 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert1 | 0.619 | 0.696 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert2 | 0.343 | 0.639 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert3 | 0.562 | 0.654 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert4 | 0.583 | 0.637 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert5 | 0.567 | 0.609 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert6 | 0.455 | 0.620 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert7 | 0.569 | 0.630 | 0.1 | 3 |
| fwd:block1.moe.shared | 0.147 | 0.158 | 0.0 | 3 |
| fwd:block2 | 6.317 | 8.863 | 1.5 | 2 |
| fwd:block2.ln1 | 0.059 | 0.061 | 0.0 | 3 |
| fwd:block2.attn.qkv | 0.096 | 0.110 | 0.0 | 3 |
| fwd:block2.attn.sdpa | 0.096 | 0.098 | 0.0 | 3 |
| fwd:block2.attn.proj | 0.053 | 0.065 | 0.0 | 3 |
| fwd:block2.ln2 | 0.044 | 0.046 | 0.0 | 3 |
| fwd:block2.moe.router | 0.195 | 0.209 | 0.0 | 3 |
| fwd:block2.moe.dispatch | 4.760 | 8.220 | 1.1 | 3 |
| fwd:block2.moe.dispatch.expert0 | 0.670 | 1.136 | 0.2 | 3 |
| fwd:block2.moe.dispatch.expert1 | 0.490 | 0.639 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert2 | 0.602 | 2.766 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert3 | 0.628 | 2.753 | 0.2 | 3 |
| fwd:block2.moe.dispatch.expert4 | 0.494 | 0.615 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert5 | 0.555 | 0.611 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert6 | 0.429 | 0.599 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert7 | 0.349 | 0.610 | 0.1 | 3 |
| fwd:block2.moe.shared | 0.147 | 0.157 | 0.0 | 3 |
| fwd:block3 | 4.752 | 7.316 | 1.1 | 2 |
| fwd:block3.ln1 | 0.059 | 0.060 | 0.0 | 3 |
| fwd:block3.attn.qkv | 0.096 | 0.107 | 0.0 | 3 |
| fwd:block3.attn.sdpa | 0.095 | 0.097 | 0.0 | 3 |
| fwd:block3.attn.proj | 0.053 | 0.059 | 0.0 | 3 |
| fwd:block3.ln2 | 0.043 | 0.045 | 0.0 | 3 |
| fwd:block3.moe.router | 0.196 | 0.215 | 0.0 | 3 |
| fwd:block3.moe.dispatch | 4.412 | 6.208 | 1.1 | 3 |
| fwd:block3.moe.dispatch.expert0 | 0.657 | 0.716 | 0.2 | 3 |
| fwd:block3.moe.dispatch.expert1 | 0.608 | 0.679 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert2 | 0.556 | 0.612 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert3 | 0.566 | 0.627 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert4 | 0.433 | 0.621 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert5 | 0.581 | 0.653 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert6 | 0.547 | 0.618 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert7 | 0.451 | 0.602 | 0.1 | 3 |
| fwd:block3.moe.shared | 0.145 | 0.157 | 0.0 | 3 |
| fwd:block4 | 6.000 | 7.693 | 1.4 | 2 |
| fwd:block4.ln1 | 0.058 | 0.061 | 0.0 | 3 |
| fwd:block4.attn.qkv | 0.096 | 0.109 | 0.0 | 3 |
| fwd:block4.attn.sdpa | 0.095 | 0.098 | 0.0 | 3 |
| fwd:block4.attn.proj | 0.053 | 0.059 | 0.0 | 3 |
| fwd:block4.ln2 | 0.042 | 0.044 | 0.0 | 3 |
| fwd:block4.moe.router | 0.197 | 0.209 | 0.0 | 3 |
| fwd:block4.moe.dispatch | 4.629 | 6.557 | 1.1 | 3 |
| fwd:block4.moe.dispatch.expert0 | 0.654 | 0.711 | 0.2 | 3 |
| fwd:block4.moe.dispatch.expert1 | 0.604 | 0.653 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert2 | 0.590 | 2.246 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert3 | 0.579 | 0.643 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert4 | 0.320 | 0.601 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert5 | 0.337 | 0.585 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert6 | 0.585 | 2.448 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert7 | 0.571 | 0.649 | 0.1 | 3 |
| fwd:block4.moe.shared | 0.148 | 0.158 | 0.0 | 3 |
| fwd:block5 | 4.764 | 7.065 | 1.1 | 2 |
| fwd:block5.ln1 | 0.059 | 0.061 | 0.0 | 3 |
| fwd:block5.attn.qkv | 0.097 | 0.114 | 0.0 | 3 |
| fwd:block5.attn.sdpa | 0.096 | 0.098 | 0.0 | 3 |
| fwd:block5.attn.proj | 0.053 | 0.060 | 0.0 | 3 |
| fwd:block5.ln2 | 0.044 | 0.046 | 0.0 | 3 |
| fwd:block5.moe.router | 0.197 | 0.206 | 0.0 | 3 |
| fwd:block5.moe.dispatch | 4.430 | 6.347 | 1.1 | 3 |
| fwd:block5.moe.dispatch.expert0 | 0.654 | 0.686 | 0.2 | 3 |
| fwd:block5.moe.dispatch.expert1 | 0.588 | 0.649 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert2 | 0.578 | 0.634 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert3 | 0.564 | 0.627 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert4 | 0.572 | 0.630 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert5 | 0.585 | 1.785 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert6 | 0.561 | 0.632 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert7 | 0.568 | 0.613 | 0.1 | 3 |
| fwd:block5.moe.shared | 0.146 | 0.155 | 0.0 | 3 |
| fwd:block6 | 5.602 | 7.473 | 1.3 | 2 |
| fwd:block6.ln1 | 0.059 | 0.061 | 0.0 | 3 |
| fwd:block6.attn.qkv | 0.097 | 0.109 | 0.0 | 3 |
| fwd:block6.attn.sdpa | 0.095 | 0.098 | 0.0 | 3 |
| fwd:block6.attn.proj | 0.053 | 0.065 | 0.0 | 3 |
| fwd:block6.ln2 | 0.042 | 0.045 | 0.0 | 3 |
| fwd:block6.moe.router | 0.196 | 0.213 | 0.0 | 3 |
| fwd:block6.moe.dispatch | 4.775 | 6.646 | 1.1 | 3 |
| fwd:block6.moe.dispatch.expert0 | 0.652 | 0.681 | 0.2 | 3 |
| fwd:block6.moe.dispatch.expert1 | 0.592 | 0.646 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert2 | 0.582 | 0.644 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert3 | 0.566 | 0.605 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert4 | 0.571 | 0.651 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert5 | 0.573 | 0.644 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert6 | 0.585 | 2.487 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert7 | 0.576 | 0.645 | 0.1 | 3 |
| fwd:block6.moe.shared | 0.147 | 0.159 | 0.0 | 3 |
| fwd:block7 | 4.833 | 7.845 | 1.2 | 2 |
| fwd:block7.ln1 | 0.059 | 0.061 | 0.0 | 3 |
| fwd:block7.attn.qkv | 0.096 | 0.108 | 0.0 | 3 |
| fwd:block7.attn.sdpa | 0.095 | 0.097 | 0.0 | 3 |
| fwd:block7.attn.proj | 0.053 | 0.063 | 0.0 | 3 |
| fwd:block7.ln2 | 0.042 | 0.045 | 0.0 | 3 |
| fwd:block7.moe.router | 0.196 | 0.208 | 0.0 | 3 |
| fwd:block7.moe.dispatch | 4.350 | 6.946 | 1.0 | 3 |
| fwd:block7.moe.dispatch.expert0 | 0.657 | 0.735 | 0.2 | 3 |
| fwd:block7.moe.dispatch.expert1 | 0.589 | 0.652 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert2 | 0.358 | 0.627 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert3 | 0.539 | 0.612 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert4 | 0.579 | 0.776 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert5 | 0.576 | 0.644 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert6 | 0.564 | 0.638 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert7 | 0.560 | 0.648 | 0.1 | 3 |
| fwd:block7.moe.shared | 0.147 | 0.158 | 0.0 | 3 |
| fwd:block8 | 5.891 | 7.458 | 1.4 | 2 |
| fwd:block8.ln1 | 0.059 | 0.061 | 0.0 | 3 |
| fwd:block8.attn.qkv | 0.096 | 0.113 | 0.0 | 3 |
| fwd:block8.attn.sdpa | 0.095 | 0.097 | 0.0 | 3 |
| fwd:block8.attn.proj | 0.053 | 0.062 | 0.0 | 3 |
| fwd:block8.ln2 | 0.043 | 0.046 | 0.0 | 3 |
| fwd:block8.moe.router | 0.196 | 0.209 | 0.0 | 3 |
| fwd:block8.moe.dispatch | 4.405 | 6.550 | 1.1 | 3 |
| fwd:block8.moe.dispatch.expert0 | 0.657 | 2.276 | 0.2 | 3 |
| fwd:block8.moe.dispatch.expert1 | 0.604 | 0.655 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert2 | 0.577 | 0.640 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert3 | 0.551 | 0.607 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert4 | 0.565 | 0.615 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert5 | 0.556 | 0.622 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert6 | 0.559 | 0.609 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert7 | 0.555 | 0.606 | 0.1 | 3 |
| fwd:block8.moe.shared | 0.147 | 0.157 | 0.0 | 3 |
| fwd:head+loss | 16.161 | 16.238 | 3.9 | 2 |
| bwd | 166.800 | 181.580 | 39.9 | 1 |
| bwd:head+loss | 16.309 | 16.327 | 3.9 | 2 |
| bwd:stack | 150.229 | 164.930 | 36.0 | 1 |
| bwd:block8 | 16.654 | 21.312 | 4.0 | 2 |
| bwd.invert:block8 | 3.149 | 3.320 | 0.8 | 3 |
| bwd.invert:block8.ln1 | 0.035 | 0.035 | 0.0 | 3 |
| bwd.invert:block8.attn.qkv | 0.026 | 0.028 | 0.0 | 3 |
| bwd.invert:block8.attn.sdpa | 0.043 | 0.044 | 0.0 | 3 |
| bwd.invert:block8.attn.proj | 0.018 | 0.018 | 0.0 | 3 |
| bwd.invert:block8.ln2 | 0.032 | 0.033 | 0.0 | 3 |
| bwd.invert:block8.moe.router | 0.036 | 0.037 | 0.0 | 3 |
| bwd.invert:block8.moe.dispatch | 2.620 | 2.754 | 0.6 | 3 |
| bwd.invert:block8.moe.dispatch.expert0 | 0.385 | 0.424 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert1 | 0.327 | 0.359 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert2 | 0.297 | 0.326 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert3 | 0.289 | 0.315 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert4 | 0.284 | 0.311 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert5 | 0.283 | 0.313 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert6 | 0.282 | 0.306 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert7 | 0.279 | 0.313 | 0.1 | 3 |
| bwd.invert:block8.moe.shared | 0.145 | 0.162 | 0.0 | 3 |
| bwd.recompute:block8 | 3.759 | 3.890 | 0.9 | 3 |
| bwd.recompute:block8.ln1 | 0.067 | 0.069 | 0.0 | 3 |
| bwd.recompute:block8.attn.qkv | 0.121 | 0.139 | 0.0 | 3 |
| bwd.recompute:block8.attn.sdpa | 0.107 | 0.113 | 0.0 | 3 |
| bwd.recompute:block8.attn.proj | 0.067 | 0.077 | 0.0 | 3 |
| bwd.recompute:block8.ln2 | 0.047 | 0.050 | 0.0 | 3 |
| bwd.recompute:block8.moe.router | 0.158 | 0.168 | 0.0 | 3 |
| bwd.recompute:block8.moe.dispatch | 2.811 | 2.917 | 0.7 | 3 |
| bwd.recompute:block8.moe.dispatch.expert0 | 0.387 | 0.436 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert1 | 0.326 | 0.363 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert2 | 0.313 | 0.353 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert3 | 0.306 | 0.335 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert4 | 0.303 | 0.340 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert5 | 0.302 | 0.334 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert6 | 0.304 | 0.336 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert7 | 0.301 | 0.332 | 0.1 | 3 |
| bwd.recompute:block8.moe.shared | 0.150 | 0.161 | 0.0 | 3 |
| bwd:block8.grad | 8.730 | 11.497 | 2.1 | 3 |
| bwd:block7 | 15.404 | 21.310 | 3.7 | 2 |
| bwd.invert:block7 | 3.610 | 3.694 | 0.9 | 3 |
| bwd.invert:block7.ln1 | 0.064 | 0.067 | 0.0 | 3 |
| bwd.invert:block7.attn.qkv | 0.120 | 0.130 | 0.0 | 3 |
| bwd.invert:block7.attn.sdpa | 0.090 | 0.097 | 0.0 | 3 |
| bwd.invert:block7.attn.proj | 0.056 | 0.068 | 0.0 | 3 |
| bwd.invert:block7.ln2 | 0.045 | 0.048 | 0.0 | 3 |
| bwd.invert:block7.moe.router | 0.150 | 0.173 | 0.0 | 3 |
| bwd.invert:block7.moe.dispatch | 2.660 | 2.713 | 0.6 | 3 |
| bwd.invert:block7.moe.dispatch.expert0 | 0.377 | 0.405 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert1 | 0.309 | 0.343 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert2 | 0.292 | 0.344 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert3 | 0.285 | 0.311 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert4 | 0.283 | 0.310 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert5 | 0.282 | 0.302 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert6 | 0.281 | 0.314 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert7 | 0.281 | 0.311 | 0.1 | 3 |
| bwd.invert:block7.moe.shared | 0.143 | 0.149 | 0.0 | 3 |
| bwd.recompute:block7 | 3.836 | 3.921 | 0.9 | 3 |
| bwd.recompute:block7.ln1 | 0.066 | 0.067 | 0.0 | 3 |
| bwd.recompute:block7.attn.qkv | 0.118 | 0.126 | 0.0 | 3 |
| bwd.recompute:block7.attn.sdpa | 0.103 | 0.107 | 0.0 | 3 |
| bwd.recompute:block7.attn.proj | 0.064 | 0.073 | 0.0 | 3 |
| bwd.recompute:block7.ln2 | 0.047 | 0.050 | 0.0 | 3 |
| bwd.recompute:block7.moe.router | 0.158 | 0.178 | 0.0 | 3 |
| bwd.recompute:block7.moe.dispatch | 2.800 | 2.858 | 0.7 | 3 |
| bwd.recompute:block7.moe.dispatch.expert0 | 0.379 | 0.426 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert1 | 0.323 | 0.358 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert2 | 0.311 | 0.347 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert3 | 0.306 | 0.361 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert4 | 0.305 | 0.332 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert5 | 0.304 | 0.340 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert6 | 0.301 | 0.325 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert7 | 0.301 | 0.335 | 0.1 | 3 |
| bwd.recompute:block7.moe.shared | 0.150 | 0.159 | 0.0 | 3 |
| bwd:block7.grad | 8.397 | 12.083 | 2.0 | 3 |
| bwd:block6 | 16.643 | 20.968 | 4.0 | 2 |
| bwd.invert:block6 | 3.603 | 3.692 | 0.9 | 3 |
| bwd.invert:block6.ln1 | 0.064 | 0.066 | 0.0 | 3 |
| bwd.invert:block6.attn.qkv | 0.118 | 0.128 | 0.0 | 3 |
| bwd.invert:block6.attn.sdpa | 0.091 | 0.097 | 0.0 | 3 |
| bwd.invert:block6.attn.proj | 0.056 | 0.065 | 0.0 | 3 |
| bwd.invert:block6.ln2 | 0.045 | 0.047 | 0.0 | 3 |
| bwd.invert:block6.moe.router | 0.149 | 0.158 | 0.0 | 3 |
| bwd.invert:block6.moe.dispatch | 2.654 | 2.706 | 0.6 | 3 |
| bwd.invert:block6.moe.dispatch.expert0 | 0.374 | 0.414 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert1 | 0.308 | 0.349 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert2 | 0.291 | 0.325 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert3 | 0.284 | 0.322 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert4 | 0.283 | 0.330 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert5 | 0.280 | 0.309 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert6 | 0.284 | 0.307 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert7 | 0.278 | 0.300 | 0.1 | 3 |
| bwd.invert:block6.moe.shared | 0.143 | 0.151 | 0.0 | 3 |
| bwd.recompute:block6 | 3.804 | 3.879 | 0.9 | 3 |
| bwd.recompute:block6.ln1 | 0.066 | 0.069 | 0.0 | 3 |
| bwd.recompute:block6.attn.qkv | 0.118 | 0.129 | 0.0 | 3 |
| bwd.recompute:block6.attn.sdpa | 0.103 | 0.108 | 0.0 | 3 |
| bwd.recompute:block6.attn.proj | 0.063 | 0.071 | 0.0 | 3 |
| bwd.recompute:block6.ln2 | 0.047 | 0.049 | 0.0 | 3 |
| bwd.recompute:block6.moe.router | 0.154 | 0.163 | 0.0 | 3 |
| bwd.recompute:block6.moe.dispatch | 2.785 | 2.841 | 0.7 | 3 |
| bwd.recompute:block6.moe.dispatch.expert0 | 0.374 | 0.410 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert1 | 0.321 | 0.378 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert2 | 0.311 | 0.344 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert3 | 0.304 | 0.338 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert4 | 0.303 | 0.337 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert5 | 0.300 | 0.353 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert6 | 0.305 | 0.333 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert7 | 0.298 | 0.327 | 0.1 | 3 |
| bwd.recompute:block6.moe.shared | 0.149 | 0.154 | 0.0 | 3 |
| bwd:block6.grad | 9.427 | 11.819 | 2.3 | 3 |
| bwd:block5 | 14.993 | 19.763 | 3.6 | 2 |
| bwd.invert:block5 | 3.582 | 3.658 | 0.9 | 3 |
| bwd.invert:block5.ln1 | 0.064 | 0.067 | 0.0 | 3 |
| bwd.invert:block5.attn.qkv | 0.118 | 0.129 | 0.0 | 3 |
| bwd.invert:block5.attn.sdpa | 0.091 | 0.099 | 0.0 | 3 |
| bwd.invert:block5.attn.proj | 0.057 | 0.065 | 0.0 | 3 |
| bwd.invert:block5.ln2 | 0.045 | 0.047 | 0.0 | 3 |
| bwd.invert:block5.moe.router | 0.150 | 0.160 | 0.0 | 3 |
| bwd.invert:block5.moe.dispatch | 2.638 | 2.704 | 0.6 | 3 |
| bwd.invert:block5.moe.dispatch.expert0 | 0.373 | 0.410 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert1 | 0.306 | 0.338 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert2 | 0.289 | 0.315 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert3 | 0.284 | 0.323 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert4 | 0.284 | 0.317 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert5 | 0.283 | 0.319 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert6 | 0.280 | 0.298 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert7 | 0.280 | 0.302 | 0.1 | 3 |
| bwd.invert:block5.moe.shared | 0.143 | 0.153 | 0.0 | 3 |
| bwd.recompute:block5 | 3.799 | 3.871 | 0.9 | 3 |
| bwd.recompute:block5.ln1 | 0.066 | 0.068 | 0.0 | 3 |
| bwd.recompute:block5.attn.qkv | 0.118 | 0.134 | 0.0 | 3 |
| bwd.recompute:block5.attn.sdpa | 0.100 | 0.105 | 0.0 | 3 |
| bwd.recompute:block5.attn.proj | 0.062 | 0.072 | 0.0 | 3 |
| bwd.recompute:block5.ln2 | 0.046 | 0.050 | 0.0 | 3 |
| bwd.recompute:block5.moe.router | 0.155 | 0.166 | 0.0 | 3 |
| bwd.recompute:block5.moe.dispatch | 2.776 | 2.838 | 0.7 | 3 |
| bwd.recompute:block5.moe.dispatch.expert0 | 0.379 | 0.419 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert1 | 0.321 | 0.352 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert2 | 0.310 | 0.340 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert3 | 0.302 | 0.334 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert4 | 0.300 | 0.333 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert5 | 0.300 | 0.348 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert6 | 0.300 | 0.334 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert7 | 0.298 | 0.319 | 0.1 | 3 |
| bwd.recompute:block5.moe.shared | 0.149 | 0.156 | 0.0 | 3 |
| bwd:block5.grad | 8.597 | 11.417 | 2.1 | 3 |
| bwd:block4 | 16.320 | 21.176 | 3.9 | 2 |
| bwd.invert:block4 | 3.592 | 3.646 | 0.9 | 3 |
| bwd.invert:block4.ln1 | 0.065 | 0.067 | 0.0 | 3 |
| bwd.invert:block4.attn.qkv | 0.119 | 0.132 | 0.0 | 3 |
| bwd.invert:block4.attn.sdpa | 0.090 | 0.096 | 0.0 | 3 |
| bwd.invert:block4.attn.proj | 0.056 | 0.062 | 0.0 | 3 |
| bwd.invert:block4.ln2 | 0.044 | 0.047 | 0.0 | 3 |
| bwd.invert:block4.moe.router | 0.149 | 0.159 | 0.0 | 3 |
| bwd.invert:block4.moe.dispatch | 2.652 | 2.700 | 0.6 | 3 |
| bwd.invert:block4.moe.dispatch.expert0 | 0.373 | 0.396 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert1 | 0.307 | 0.363 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert2 | 0.294 | 0.323 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert3 | 0.284 | 0.338 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert4 | 0.282 | 0.312 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert5 | 0.280 | 0.305 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert6 | 0.284 | 0.313 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert7 | 0.279 | 0.299 | 0.1 | 3 |
| bwd.invert:block4.moe.shared | 0.143 | 0.149 | 0.0 | 3 |
| bwd.recompute:block4 | 3.808 | 3.873 | 0.9 | 3 |
| bwd.recompute:block4.ln1 | 0.066 | 0.067 | 0.0 | 3 |
| bwd.recompute:block4.attn.qkv | 0.118 | 0.139 | 0.0 | 3 |
| bwd.recompute:block4.attn.sdpa | 0.099 | 0.103 | 0.0 | 3 |
| bwd.recompute:block4.attn.proj | 0.062 | 0.074 | 0.0 | 3 |
| bwd.recompute:block4.ln2 | 0.047 | 0.049 | 0.0 | 3 |
| bwd.recompute:block4.moe.router | 0.155 | 0.172 | 0.0 | 3 |
| bwd.recompute:block4.moe.dispatch | 2.785 | 2.845 | 0.7 | 3 |
| bwd.recompute:block4.moe.dispatch.expert0 | 0.374 | 0.396 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert1 | 0.321 | 0.348 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert2 | 0.311 | 0.364 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert3 | 0.305 | 0.344 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert4 | 0.302 | 0.355 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert5 | 0.299 | 0.326 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert6 | 0.304 | 0.326 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert7 | 0.299 | 0.332 | 0.1 | 3 |
| bwd.recompute:block4.moe.shared | 0.149 | 0.156 | 0.0 | 3 |
| bwd:block4.grad | 8.728 | 11.481 | 2.1 | 3 |
| bwd:block3 | 14.709 | 20.298 | 3.5 | 2 |
| bwd.invert:block3 | 3.585 | 3.650 | 0.9 | 3 |
| bwd.invert:block3.ln1 | 0.064 | 0.067 | 0.0 | 3 |
| bwd.invert:block3.attn.qkv | 0.119 | 0.134 | 0.0 | 3 |
| bwd.invert:block3.attn.sdpa | 0.090 | 0.097 | 0.0 | 3 |
| bwd.invert:block3.attn.proj | 0.055 | 0.062 | 0.0 | 3 |
| bwd.invert:block3.ln2 | 0.044 | 0.047 | 0.0 | 3 |
| bwd.invert:block3.moe.router | 0.148 | 0.158 | 0.0 | 3 |
| bwd.invert:block3.moe.dispatch | 2.644 | 2.705 | 0.6 | 3 |
| bwd.invert:block3.moe.dispatch.expert0 | 0.373 | 0.401 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert1 | 0.309 | 0.352 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert2 | 0.291 | 0.324 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert3 | 0.286 | 0.313 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert4 | 0.281 | 0.312 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert5 | 0.282 | 0.307 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert6 | 0.279 | 0.309 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert7 | 0.279 | 0.320 | 0.1 | 3 |
| bwd.invert:block3.moe.shared | 0.144 | 0.150 | 0.0 | 3 |
| bwd.recompute:block3 | 3.802 | 3.878 | 0.9 | 3 |
| bwd.recompute:block3.ln1 | 0.066 | 0.068 | 0.0 | 3 |
| bwd.recompute:block3.attn.qkv | 0.118 | 0.130 | 0.0 | 3 |
| bwd.recompute:block3.attn.sdpa | 0.099 | 0.105 | 0.0 | 3 |
| bwd.recompute:block3.attn.proj | 0.062 | 0.075 | 0.0 | 3 |
| bwd.recompute:block3.ln2 | 0.047 | 0.050 | 0.0 | 3 |
| bwd.recompute:block3.moe.router | 0.154 | 0.171 | 0.0 | 3 |
| bwd.recompute:block3.moe.dispatch | 2.779 | 2.847 | 0.7 | 3 |
| bwd.recompute:block3.moe.dispatch.expert0 | 0.376 | 0.399 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert1 | 0.322 | 0.349 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert2 | 0.309 | 0.362 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert3 | 0.303 | 0.335 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert4 | 0.302 | 0.331 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert5 | 0.301 | 0.325 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert6 | 0.300 | 0.328 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert7 | 0.299 | 0.333 | 0.1 | 3 |
| bwd.recompute:block3.moe.shared | 0.149 | 0.160 | 0.0 | 3 |
| bwd:block3.grad | 8.528 | 10.831 | 2.0 | 3 |
| bwd:block2 | 17.058 | 21.543 | 4.1 | 2 |
| bwd.invert:block2 | 3.579 | 3.661 | 0.9 | 3 |
| bwd.invert:block2.ln1 | 0.064 | 0.066 | 0.0 | 3 |
| bwd.invert:block2.attn.qkv | 0.118 | 0.126 | 0.0 | 3 |
| bwd.invert:block2.attn.sdpa | 0.090 | 0.097 | 0.0 | 3 |
| bwd.invert:block2.attn.proj | 0.055 | 0.061 | 0.0 | 3 |
| bwd.invert:block2.ln2 | 0.044 | 0.046 | 0.0 | 3 |
| bwd.invert:block2.moe.router | 0.148 | 0.156 | 0.0 | 3 |
| bwd.invert:block2.moe.dispatch | 2.650 | 2.716 | 0.6 | 3 |
| bwd.invert:block2.moe.dispatch.expert0 | 0.374 | 0.404 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert1 | 0.306 | 0.346 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert2 | 0.293 | 0.328 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert3 | 0.289 | 0.323 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert4 | 0.283 | 0.312 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert5 | 0.280 | 0.312 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert6 | 0.280 | 0.310 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert7 | 0.278 | 0.321 | 0.1 | 3 |
| bwd.invert:block2.moe.shared | 0.144 | 0.154 | 0.0 | 3 |
| bwd.recompute:block2 | 3.805 | 3.890 | 0.9 | 3 |
| bwd.recompute:block2.ln1 | 0.066 | 0.068 | 0.0 | 3 |
| bwd.recompute:block2.attn.qkv | 0.117 | 0.135 | 0.0 | 3 |
| bwd.recompute:block2.attn.sdpa | 0.099 | 0.101 | 0.0 | 3 |
| bwd.recompute:block2.attn.proj | 0.061 | 0.069 | 0.0 | 3 |
| bwd.recompute:block2.ln2 | 0.047 | 0.049 | 0.0 | 3 |
| bwd.recompute:block2.moe.router | 0.154 | 0.163 | 0.0 | 3 |
| bwd.recompute:block2.moe.dispatch | 2.791 | 2.858 | 0.7 | 3 |
| bwd.recompute:block2.moe.dispatch.expert0 | 0.377 | 0.404 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert1 | 0.321 | 0.354 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert2 | 0.311 | 0.361 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert3 | 0.308 | 0.365 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert4 | 0.301 | 0.331 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert5 | 0.299 | 0.327 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert6 | 0.300 | 0.329 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert7 | 0.298 | 0.332 | 0.1 | 3 |
| bwd.recompute:block2.moe.shared | 0.148 | 0.164 | 0.0 | 3 |
| bwd:block2.grad | 9.228 | 13.498 | 2.2 | 3 |
| bwd:block1 | 16.268 | 20.462 | 3.9 | 2 |
| bwd.invert:block1 | 3.582 | 3.645 | 0.9 | 3 |
| bwd.invert:block1.ln1 | 0.064 | 0.067 | 0.0 | 3 |
| bwd.invert:block1.attn.qkv | 0.115 | 0.126 | 0.0 | 3 |
| bwd.invert:block1.attn.sdpa | 0.089 | 0.093 | 0.0 | 3 |
| bwd.invert:block1.attn.proj | 0.055 | 0.065 | 0.0 | 3 |
| bwd.invert:block1.ln2 | 0.044 | 0.048 | 0.0 | 3 |
| bwd.invert:block1.moe.router | 0.148 | 0.156 | 0.0 | 3 |
| bwd.invert:block1.moe.dispatch | 2.649 | 2.710 | 0.6 | 3 |
| bwd.invert:block1.moe.dispatch.expert0 | 0.373 | 0.404 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert1 | 0.309 | 0.343 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert2 | 0.290 | 0.328 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert3 | 0.286 | 0.312 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert4 | 0.284 | 0.313 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert5 | 0.281 | 0.307 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert6 | 0.279 | 0.319 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert7 | 0.281 | 0.304 | 0.1 | 3 |
| bwd.invert:block1.moe.shared | 0.143 | 0.149 | 0.0 | 3 |
| bwd.recompute:block1 | 3.791 | 3.873 | 0.9 | 3 |
| bwd.recompute:block1.ln1 | 0.066 | 0.067 | 0.0 | 3 |
| bwd.recompute:block1.attn.qkv | 0.118 | 0.131 | 0.0 | 3 |
| bwd.recompute:block1.attn.sdpa | 0.099 | 0.101 | 0.0 | 3 |
| bwd.recompute:block1.attn.proj | 0.062 | 0.073 | 0.0 | 3 |
| bwd.recompute:block1.ln2 | 0.046 | 0.049 | 0.0 | 3 |
| bwd.recompute:block1.moe.router | 0.154 | 0.164 | 0.0 | 3 |
| bwd.recompute:block1.moe.dispatch | 2.776 | 2.846 | 0.7 | 3 |
| bwd.recompute:block1.moe.dispatch.expert0 | 0.375 | 0.422 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert1 | 0.323 | 0.354 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert2 | 0.309 | 0.341 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert3 | 0.304 | 0.342 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert4 | 0.303 | 0.330 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert5 | 0.298 | 0.326 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert6 | 0.299 | 0.328 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert7 | 0.299 | 0.343 | 0.1 | 3 |
| bwd.recompute:block1.moe.shared | 0.147 | 0.153 | 0.0 | 3 |
| bwd:block1.grad | 8.125 | 11.225 | 1.9 | 3 |
| bwd:block0 | 16.510 | 20.098 | 4.0 | 2 |
| bwd.invert:block0 | 3.603 | 3.690 | 0.9 | 3 |
| bwd.invert:block0.ln1 | 0.064 | 0.067 | 0.0 | 3 |
| bwd.invert:block0.attn.qkv | 0.115 | 0.125 | 0.0 | 3 |
| bwd.invert:block0.attn.sdpa | 0.089 | 0.093 | 0.0 | 3 |
| bwd.invert:block0.attn.proj | 0.056 | 0.062 | 0.0 | 3 |
| bwd.invert:block0.ln2 | 0.045 | 0.047 | 0.0 | 3 |
| bwd.invert:block0.moe.router | 0.149 | 0.159 | 0.0 | 3 |
| bwd.invert:block0.moe.dispatch | 2.667 | 2.742 | 0.6 | 3 |
| bwd.invert:block0.moe.dispatch.expert0 | 0.374 | 0.419 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert1 | 0.309 | 0.353 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert2 | 0.295 | 0.341 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert3 | 0.285 | 0.319 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert4 | 0.287 | 0.318 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert5 | 0.281 | 0.315 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert6 | 0.279 | 0.298 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert7 | 0.279 | 0.309 | 0.1 | 3 |
| bwd.invert:block0.moe.shared | 0.143 | 0.153 | 0.0 | 3 |
| bwd.recompute:block0 | 3.802 | 3.880 | 0.9 | 3 |
| bwd.recompute:block0.ln1 | 0.066 | 0.068 | 0.0 | 3 |
| bwd.recompute:block0.attn.qkv | 0.119 | 0.127 | 0.0 | 3 |
| bwd.recompute:block0.attn.sdpa | 0.099 | 0.101 | 0.0 | 3 |
| bwd.recompute:block0.attn.proj | 0.062 | 0.069 | 0.0 | 3 |
| bwd.recompute:block0.ln2 | 0.047 | 0.050 | 0.0 | 3 |
| bwd.recompute:block0.moe.router | 0.155 | 0.164 | 0.0 | 3 |
| bwd.recompute:block0.moe.dispatch | 2.788 | 2.866 | 0.7 | 3 |
| bwd.recompute:block0.moe.dispatch.expert0 | 0.378 | 0.413 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert1 | 0.323 | 0.360 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert2 | 0.313 | 0.354 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert3 | 0.304 | 0.359 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert4 | 0.304 | 0.333 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert5 | 0.301 | 0.337 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert6 | 0.300 | 0.335 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert7 | 0.296 | 0.322 | 0.1 | 3 |
| bwd.recompute:block0.moe.shared | 0.147 | 0.157 | 0.0 | 3 |
| bwd:block0.grad | 8.649 | 12.145 | 2.1 | 3 |
| bwd:embed | 0.273 | 0.388 | 0.1 | 2 |
| opt | 93.796 | 99.716 | 22.5 | 1 |
| opt:opt.clip | 3.120 | 3.657 | 0.7 | 2 |
| opt:opt.muon | 88.466 | 93.165 | 21.2 | 2 |
| opt:opt.muon.ns | 84.158 | 85.025 | 20.2 | 3 |
| opt:opt.adamw | 1.085 | 1.355 | 0.3 | 2 |
| opt:opt.moe_bias | 0.561 | 0.613 | 0.1 | 3 |
| opt:opt.zero_grad | 0.631 | 0.760 | 0.2 | 3 |

## Time by part type (sum over layers)

| part type | median ms sum | % of step |
| :--- | ---: | ---: |
| bwd | 166.800 | 39.9 |
| bwd:stack | 150.229 | 36.0 |
| bwd:block* | 144.559 | 34.6 |
| opt | 93.796 | 22.5 |
| opt:opt.muon | 88.466 | 21.2 |
| opt:opt.muon.ns | 84.158 | 20.2 |
| bwd:block*.grad | 78.410 | 18.8 |
| fwd | 70.891 | 17.0 |
| fwd:stack | 52.572 | 12.6 |
| fwd:block* | 49.536 | 11.9 |
| fwd:block*.moe.dispatch | 40.633 | 9.7 |
| bwd.recompute:block* | 34.205 | 8.2 |
| bwd.invert:block* | 31.885 | 7.6 |
| bwd.recompute:block*.moe.dispatch | 25.091 | 6.0 |
| bwd.invert:block*.moe.dispatch | 23.834 | 5.7 |
| bwd:head+loss | 16.309 | 3.9 |
| fwd:head+loss | 16.161 | 3.9 |
| fwd:block*.moe.dispatch.expert0 | 5.417 | 1.3 |
| fwd:block*.moe.dispatch.expert3 | 5.121 | 1.2 |
| fwd:block*.moe.dispatch.expert1 | 5.096 | 1.2 |
| fwd:block*.moe.dispatch.expert5 | 4.918 | 1.2 |
| fwd:block*.moe.dispatch.expert2 | 4.824 | 1.2 |
| fwd:block*.moe.dispatch.expert4 | 4.716 | 1.1 |
| fwd:block*.moe.dispatch.expert6 | 4.696 | 1.1 |
| fwd:block*.moe.dispatch.expert7 | 4.544 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert0 | 3.399 | 0.8 |
| bwd.invert:block*.moe.dispatch.expert0 | 3.376 | 0.8 |
| opt:opt.clip | 3.120 | 0.7 |
| bwd.recompute:block*.moe.dispatch.expert1 | 2.902 | 0.7 |
| bwd.recompute:block*.moe.dispatch.expert2 | 2.797 | 0.7 |
| bwd.invert:block*.moe.dispatch.expert1 | 2.790 | 0.7 |
| bwd.recompute:block*.moe.dispatch.expert3 | 2.743 | 0.7 |
| bwd.recompute:block*.moe.dispatch.expert4 | 2.722 | 0.7 |
| bwd.recompute:block*.moe.dispatch.expert6 | 2.713 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert5 | 2.702 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert7 | 2.688 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert2 | 2.631 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert3 | 2.573 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert4 | 2.552 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert5 | 2.533 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert6 | 2.528 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert7 | 2.514 | 0.6 |
| fwd:embed | 2.013 | 0.5 |
| fwd:embed.ke | 1.973 | 0.5 |
| fwd:block*.moe.router | 1.660 | 0.4 |
| bwd.recompute:block*.moe.router | 1.397 | 0.3 |
| bwd.recompute:block*.moe.shared | 1.340 | 0.3 |
| fwd:block*.moe.shared | 1.319 | 0.3 |
| bwd.invert:block*.moe.shared | 1.290 | 0.3 |
| bwd.invert:block*.moe.router | 1.226 | 0.3 |
| opt:opt.adamw | 1.085 | 0.3 |
| bwd.recompute:block*.attn.qkv | 1.063 | 0.3 |
| bwd.invert:block*.attn.qkv | 0.967 | 0.2 |
| bwd.recompute:block*.attn.sdpa | 0.908 | 0.2 |
| fwd:block*.attn.sdpa | 0.805 | 0.2 |
| fwd:block*.attn.qkv | 0.797 | 0.2 |
| bwd.invert:block*.attn.sdpa | 0.764 | 0.2 |
| data | 0.742 | 0.2 |
| opt:opt.zero_grad | 0.631 | 0.2 |
| bwd.recompute:block*.ln1 | 0.593 | 0.1 |
| bwd.recompute:block*.attn.proj | 0.565 | 0.1 |
| opt:opt.moe_bias | 0.561 | 0.1 |
| bwd.invert:block*.ln1 | 0.549 | 0.1 |
| fwd:block*.ln1 | 0.503 | 0.1 |
| bwd.invert:block*.attn.proj | 0.463 | 0.1 |
| fwd:block*.attn.proj | 0.441 | 0.1 |
| bwd.recompute:block*.ln2 | 0.421 | 0.1 |
| bwd.invert:block*.ln2 | 0.388 | 0.1 |
| fwd:block*.ln2 | 0.377 | 0.1 |
| bwd:embed | 0.273 | 0.1 |

## Five slowest leaf parts

1. `opt:opt.muon.ns` — 84.158 ms (20.2% of step)
2. `bwd:block6.grad` — 9.427 ms (2.3% of step)
3. `bwd:block2.grad` — 9.228 ms (2.2% of step)
4. `bwd:block8.grad` — 8.730 ms (2.1% of step)
5. `bwd:block4.grad` — 8.728 ms (2.1% of step)
