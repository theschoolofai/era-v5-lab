# Bench report — h200_v1_muon_loop

**GPU:** NVIDIA H200  |  **dtype:** bf16  |  **B x T:** 32 x 512  |  **torch:** 2.11.0+cu128
**commit:** `19221759f9d820ce0563d5d2f44e22eac0de53d2`  |  **tag:** h200_v1_muon_loop

## Step (clean)

- median: 409.588 ms
- p10..p90: 307.964 .. 580.358 ms
- tokens/s: 40,001
- MFU: 1.3%  |  HFU: 1.7%

## Diagnostics

### CUDA timing-event allocations

- [OK] clean: events_created_during_steps=0
- [OK] layer: events_created_during_steps=0
- [OK] layer.inner_pass: events_created_during_steps=0

### Benchmark warnings

- [warn] rule 3b: checkpoint and comm not measured; add checkpoint,comm to --modes
- [warn] 26 gated part(s) have p10..p90 spread > 10%, so may miss the 5% check: data, fwd, fwd:stack, fwd:block0, fwd:block1, fwd:block2 (+20 more)

## Regions

| part | median ms | p90 | % of step | level |
| :--- | ---: | ---: | ---: | ---: |
| data | 0.678 | 0.739 | 0.2 | 1 |
| fwd | 61.570 | 67.309 | 15.0 | 1 |
| fwd:embed | 1.974 | 2.008 | 0.5 | 2 |
| fwd:embed.ke | 1.931 | 1.965 | 0.5 | 3 |
| fwd:stack | 43.382 | 49.087 | 10.6 | 1 |
| fwd:block0 | 3.741 | 5.925 | 0.9 | 2 |
| fwd:block0.ln1 | 0.033 | 0.033 | 0.0 | 3 |
| fwd:block0.attn.qkv | 0.025 | 0.026 | 0.0 | 3 |
| fwd:block0.attn.sdpa | 0.043 | 0.043 | 0.0 | 3 |
| fwd:block0.attn.proj | 0.018 | 0.019 | 0.0 | 3 |
| fwd:block0.ln2 | 0.032 | 0.033 | 0.0 | 3 |
| fwd:block0.moe.router | 0.088 | 0.089 | 0.0 | 3 |
| fwd:block0.moe.dispatch | 3.485 | 4.126 | 0.9 | 3 |
| fwd:block0.moe.dispatch.expert0 | 0.383 | 0.595 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert1 | 0.414 | 0.609 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert2 | 0.499 | 0.571 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert3 | 0.485 | 0.532 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert4 | 0.492 | 0.577 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert5 | 0.490 | 0.543 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert6 | 0.389 | 0.517 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert7 | 0.283 | 0.534 | 0.1 | 3 |
| fwd:block0.moe.shared | 0.135 | 0.146 | 0.0 | 3 |
| fwd:block1 | 5.409 | 7.206 | 1.3 | 2 |
| fwd:block1.ln1 | 0.055 | 0.058 | 0.0 | 3 |
| fwd:block1.attn.qkv | 0.077 | 0.103 | 0.0 | 3 |
| fwd:block1.attn.sdpa | 0.089 | 0.096 | 0.0 | 3 |
| fwd:block1.attn.proj | 0.039 | 0.061 | 0.0 | 3 |
| fwd:block1.ln2 | 0.039 | 0.046 | 0.0 | 3 |
| fwd:block1.moe.router | 0.165 | 0.200 | 0.0 | 3 |
| fwd:block1.moe.dispatch | 3.720 | 5.572 | 0.9 | 3 |
| fwd:block1.moe.dispatch.expert0 | 0.401 | 0.596 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert1 | 0.518 | 1.881 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert2 | 0.393 | 0.537 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert3 | 0.307 | 0.531 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert4 | 0.494 | 1.877 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert5 | 0.362 | 0.542 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert6 | 0.337 | 0.507 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert7 | 0.480 | 0.586 | 0.1 | 3 |
| fwd:block1.moe.shared | 0.136 | 0.151 | 0.0 | 3 |
| fwd:block2 | 5.378 | 7.687 | 1.3 | 2 |
| fwd:block2.ln1 | 0.055 | 0.059 | 0.0 | 3 |
| fwd:block2.attn.qkv | 0.076 | 0.100 | 0.0 | 3 |
| fwd:block2.attn.sdpa | 0.090 | 0.094 | 0.0 | 3 |
| fwd:block2.attn.proj | 0.039 | 0.054 | 0.0 | 3 |
| fwd:block2.ln2 | 0.039 | 0.043 | 0.0 | 3 |
| fwd:block2.moe.router | 0.163 | 0.189 | 0.0 | 3 |
| fwd:block2.moe.dispatch | 4.124 | 5.971 | 1.0 | 3 |
| fwd:block2.moe.dispatch.expert0 | 0.561 | 0.661 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert1 | 0.314 | 0.534 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert2 | 0.499 | 2.196 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert3 | 0.525 | 2.372 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert4 | 0.353 | 0.527 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert5 | 0.473 | 0.589 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert6 | 0.414 | 0.519 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert7 | 0.457 | 0.525 | 0.1 | 3 |
| fwd:block2.moe.shared | 0.136 | 0.151 | 0.0 | 3 |
| fwd:block3 | 4.086 | 6.271 | 1.0 | 2 |
| fwd:block3.ln1 | 0.055 | 0.059 | 0.0 | 3 |
| fwd:block3.attn.qkv | 0.077 | 0.101 | 0.0 | 3 |
| fwd:block3.attn.sdpa | 0.089 | 0.095 | 0.0 | 3 |
| fwd:block3.attn.proj | 0.038 | 0.055 | 0.0 | 3 |
| fwd:block3.ln2 | 0.038 | 0.043 | 0.0 | 3 |
| fwd:block3.moe.router | 0.164 | 0.190 | 0.0 | 3 |
| fwd:block3.moe.dispatch | 3.626 | 5.389 | 0.9 | 3 |
| fwd:block3.moe.dispatch.expert0 | 0.556 | 1.888 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert1 | 0.506 | 0.603 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert2 | 0.342 | 0.521 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert3 | 0.473 | 0.552 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert4 | 0.287 | 0.522 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert5 | 0.489 | 1.786 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert6 | 0.315 | 0.515 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert7 | 0.323 | 0.513 | 0.1 | 3 |
| fwd:block3.moe.shared | 0.135 | 0.144 | 0.0 | 3 |
| fwd:block4 | 4.990 | 6.249 | 1.2 | 2 |
| fwd:block4.ln1 | 0.055 | 0.056 | 0.0 | 3 |
| fwd:block4.attn.qkv | 0.077 | 0.096 | 0.0 | 3 |
| fwd:block4.attn.sdpa | 0.089 | 0.093 | 0.0 | 3 |
| fwd:block4.attn.proj | 0.039 | 0.054 | 0.0 | 3 |
| fwd:block4.ln2 | 0.038 | 0.043 | 0.0 | 3 |
| fwd:block4.moe.router | 0.162 | 0.192 | 0.0 | 3 |
| fwd:block4.moe.dispatch | 3.857 | 5.510 | 0.9 | 3 |
| fwd:block4.moe.dispatch.expert0 | 0.559 | 0.648 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert1 | 0.505 | 0.602 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert2 | 0.491 | 0.577 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert3 | 0.483 | 0.535 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert4 | 0.315 | 0.522 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert5 | 0.329 | 0.510 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert6 | 0.477 | 0.572 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert7 | 0.489 | 1.963 | 0.1 | 3 |
| fwd:block4.moe.shared | 0.136 | 0.147 | 0.0 | 3 |
| fwd:block5 | 4.097 | 6.440 | 1.0 | 2 |
| fwd:block5.ln1 | 0.055 | 0.058 | 0.0 | 3 |
| fwd:block5.attn.qkv | 0.076 | 0.106 | 0.0 | 3 |
| fwd:block5.attn.sdpa | 0.090 | 0.095 | 0.0 | 3 |
| fwd:block5.attn.proj | 0.038 | 0.055 | 0.0 | 3 |
| fwd:block5.ln2 | 0.038 | 0.044 | 0.0 | 3 |
| fwd:block5.moe.router | 0.165 | 0.196 | 0.0 | 3 |
| fwd:block5.moe.dispatch | 3.810 | 5.517 | 0.9 | 3 |
| fwd:block5.moe.dispatch.expert0 | 0.555 | 0.630 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert1 | 0.512 | 0.623 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert2 | 0.482 | 0.588 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert3 | 0.464 | 0.514 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert4 | 0.462 | 0.521 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert5 | 0.479 | 0.539 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert6 | 0.476 | 0.554 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert7 | 0.486 | 0.621 | 0.1 | 3 |
| fwd:block5.moe.shared | 0.137 | 0.148 | 0.0 | 3 |
| fwd:block6 | 4.973 | 6.696 | 1.2 | 2 |
| fwd:block6.ln1 | 0.055 | 0.058 | 0.0 | 3 |
| fwd:block6.attn.qkv | 0.078 | 0.098 | 0.0 | 3 |
| fwd:block6.attn.sdpa | 0.089 | 0.093 | 0.0 | 3 |
| fwd:block6.attn.proj | 0.038 | 0.057 | 0.0 | 3 |
| fwd:block6.ln2 | 0.038 | 0.044 | 0.0 | 3 |
| fwd:block6.moe.router | 0.164 | 0.193 | 0.0 | 3 |
| fwd:block6.moe.dispatch | 4.400 | 6.082 | 1.1 | 3 |
| fwd:block6.moe.dispatch.expert0 | 0.561 | 0.678 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert1 | 0.503 | 0.575 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert2 | 0.493 | 1.823 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert3 | 0.472 | 1.505 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert4 | 0.478 | 0.536 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert5 | 0.492 | 1.981 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert6 | 0.478 | 0.552 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert7 | 0.490 | 0.641 | 0.1 | 3 |
| fwd:block6.moe.shared | 0.136 | 0.150 | 0.0 | 3 |
| fwd:block7 | 4.106 | 6.619 | 1.0 | 2 |
| fwd:block7.ln1 | 0.055 | 0.060 | 0.0 | 3 |
| fwd:block7.attn.qkv | 0.078 | 0.106 | 0.0 | 3 |
| fwd:block7.attn.sdpa | 0.089 | 0.095 | 0.0 | 3 |
| fwd:block7.attn.proj | 0.039 | 0.056 | 0.0 | 3 |
| fwd:block7.ln2 | 0.038 | 0.044 | 0.0 | 3 |
| fwd:block7.moe.router | 0.164 | 0.191 | 0.0 | 3 |
| fwd:block7.moe.dispatch | 3.805 | 5.430 | 0.9 | 3 |
| fwd:block7.moe.dispatch.expert0 | 0.434 | 0.592 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert1 | 0.393 | 0.523 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert2 | 0.496 | 1.859 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert3 | 0.474 | 0.543 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert4 | 0.477 | 1.835 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert5 | 0.478 | 0.513 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert6 | 0.473 | 0.561 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert7 | 0.475 | 0.589 | 0.1 | 3 |
| fwd:block7.moe.shared | 0.136 | 0.144 | 0.0 | 3 |
| fwd:block8 | 3.964 | 6.021 | 1.0 | 2 |
| fwd:block8.ln1 | 0.055 | 0.058 | 0.0 | 3 |
| fwd:block8.attn.qkv | 0.076 | 0.097 | 0.0 | 3 |
| fwd:block8.attn.sdpa | 0.089 | 0.095 | 0.0 | 3 |
| fwd:block8.attn.proj | 0.038 | 0.056 | 0.0 | 3 |
| fwd:block8.ln2 | 0.039 | 0.044 | 0.0 | 3 |
| fwd:block8.moe.router | 0.163 | 0.199 | 0.0 | 3 |
| fwd:block8.moe.dispatch | 3.834 | 5.785 | 0.9 | 3 |
| fwd:block8.moe.dispatch.expert0 | 0.564 | 1.904 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert1 | 0.507 | 1.251 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert2 | 0.482 | 0.568 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert3 | 0.471 | 0.569 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert4 | 0.471 | 0.580 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert5 | 0.469 | 0.516 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert6 | 0.473 | 0.605 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert7 | 0.472 | 0.561 | 0.1 | 3 |
| fwd:block8.moe.shared | 0.135 | 0.144 | 0.0 | 3 |
| fwd:head+loss | 16.163 | 16.231 | 3.9 | 2 |
| bwd | 144.002 | 154.700 | 35.2 | 1 |
| bwd:head+loss | 16.308 | 16.321 | 4.0 | 2 |
| bwd:stack | 127.442 | 138.132 | 31.1 | 1 |
| bwd:block8 | 12.621 | 16.507 | 3.1 | 2 |
| bwd.invert:block8 | 2.737 | 2.812 | 0.7 | 3 |
| bwd.invert:block8.ln1 | 0.035 | 0.035 | 0.0 | 3 |
| bwd.invert:block8.attn.qkv | 0.026 | 0.027 | 0.0 | 3 |
| bwd.invert:block8.attn.sdpa | 0.043 | 0.043 | 0.0 | 3 |
| bwd.invert:block8.attn.proj | 0.018 | 0.018 | 0.0 | 3 |
| bwd.invert:block8.ln2 | 0.032 | 0.033 | 0.0 | 3 |
| bwd.invert:block8.moe.router | 0.037 | 0.038 | 0.0 | 3 |
| bwd.invert:block8.moe.dispatch | 2.238 | 2.317 | 0.5 | 3 |
| bwd.invert:block8.moe.dispatch.expert0 | 0.330 | 0.375 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert1 | 0.274 | 0.318 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert2 | 0.247 | 0.290 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert3 | 0.239 | 0.288 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert4 | 0.237 | 0.277 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert5 | 0.234 | 0.267 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert6 | 0.234 | 0.279 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert7 | 0.234 | 0.278 | 0.1 | 3 |
| bwd.invert:block8.moe.shared | 0.133 | 0.142 | 0.0 | 3 |
| bwd.recompute:block8 | 3.240 | 3.321 | 0.8 | 3 |
| bwd.recompute:block8.ln1 | 0.062 | 0.065 | 0.0 | 3 |
| bwd.recompute:block8.attn.qkv | 0.098 | 0.120 | 0.0 | 3 |
| bwd.recompute:block8.attn.sdpa | 0.101 | 0.109 | 0.0 | 3 |
| bwd.recompute:block8.attn.proj | 0.050 | 0.068 | 0.0 | 3 |
| bwd.recompute:block8.ln2 | 0.042 | 0.047 | 0.0 | 3 |
| bwd.recompute:block8.moe.router | 0.132 | 0.147 | 0.0 | 3 |
| bwd.recompute:block8.moe.dispatch | 2.415 | 2.495 | 0.6 | 3 |
| bwd.recompute:block8.moe.dispatch.expert0 | 0.329 | 0.379 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert1 | 0.274 | 0.330 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert2 | 0.262 | 0.321 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert3 | 0.256 | 0.311 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert4 | 0.253 | 0.305 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert5 | 0.251 | 0.288 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert6 | 0.256 | 0.315 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert7 | 0.252 | 0.298 | 0.1 | 3 |
| bwd.recompute:block8.moe.shared | 0.137 | 0.147 | 0.0 | 3 |
| bwd:block8.grad | 7.593 | 10.087 | 1.9 | 3 |
| bwd:block7 | 12.967 | 18.128 | 3.2 | 2 |
| bwd.invert:block7 | 3.097 | 3.168 | 0.8 | 3 |
| bwd.invert:block7.ln1 | 0.060 | 0.065 | 0.0 | 3 |
| bwd.invert:block7.attn.qkv | 0.097 | 0.126 | 0.0 | 3 |
| bwd.invert:block7.attn.sdpa | 0.085 | 0.092 | 0.0 | 3 |
| bwd.invert:block7.attn.proj | 0.041 | 0.060 | 0.0 | 3 |
| bwd.invert:block7.ln2 | 0.040 | 0.046 | 0.0 | 3 |
| bwd.invert:block7.moe.router | 0.125 | 0.149 | 0.0 | 3 |
| bwd.invert:block7.moe.dispatch | 2.258 | 2.334 | 0.6 | 3 |
| bwd.invert:block7.moe.dispatch.expert0 | 0.321 | 0.365 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert1 | 0.260 | 0.310 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert2 | 0.245 | 0.289 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert3 | 0.237 | 0.282 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert4 | 0.236 | 0.270 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert5 | 0.235 | 0.278 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert6 | 0.233 | 0.268 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert7 | 0.233 | 0.264 | 0.1 | 3 |
| bwd.invert:block7.moe.shared | 0.133 | 0.139 | 0.0 | 3 |
| bwd.recompute:block7 | 3.314 | 3.387 | 0.8 | 3 |
| bwd.recompute:block7.ln1 | 0.062 | 0.065 | 0.0 | 3 |
| bwd.recompute:block7.attn.qkv | 0.096 | 0.106 | 0.0 | 3 |
| bwd.recompute:block7.attn.sdpa | 0.098 | 0.103 | 0.0 | 3 |
| bwd.recompute:block7.attn.proj | 0.048 | 0.068 | 0.0 | 3 |
| bwd.recompute:block7.ln2 | 0.042 | 0.048 | 0.0 | 3 |
| bwd.recompute:block7.moe.router | 0.132 | 0.158 | 0.0 | 3 |
| bwd.recompute:block7.moe.dispatch | 2.395 | 2.479 | 0.6 | 3 |
| bwd.recompute:block7.moe.dispatch.expert0 | 0.324 | 0.405 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert1 | 0.273 | 0.326 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert2 | 0.262 | 0.309 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert3 | 0.256 | 0.299 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert4 | 0.256 | 0.303 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert5 | 0.252 | 0.301 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert6 | 0.253 | 0.298 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert7 | 0.251 | 0.298 | 0.1 | 3 |
| bwd.recompute:block7.moe.shared | 0.137 | 0.144 | 0.0 | 3 |
| bwd:block7.grad | 7.438 | 9.962 | 1.8 | 3 |
| bwd:block6 | 14.332 | 18.402 | 3.5 | 2 |
| bwd.invert:block6 | 3.095 | 3.170 | 0.8 | 3 |
| bwd.invert:block6.ln1 | 0.060 | 0.063 | 0.0 | 3 |
| bwd.invert:block6.attn.qkv | 0.096 | 0.120 | 0.0 | 3 |
| bwd.invert:block6.attn.sdpa | 0.086 | 0.093 | 0.0 | 3 |
| bwd.invert:block6.attn.proj | 0.042 | 0.054 | 0.0 | 3 |
| bwd.invert:block6.ln2 | 0.040 | 0.045 | 0.0 | 3 |
| bwd.invert:block6.moe.router | 0.124 | 0.148 | 0.0 | 3 |
| bwd.invert:block6.moe.dispatch | 2.246 | 2.340 | 0.5 | 3 |
| bwd.invert:block6.moe.dispatch.expert0 | 0.319 | 0.371 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert1 | 0.258 | 0.302 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert2 | 0.242 | 0.275 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert3 | 0.237 | 0.269 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert4 | 0.235 | 0.280 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert5 | 0.235 | 0.292 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert6 | 0.232 | 0.282 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert7 | 0.233 | 0.273 | 0.1 | 3 |
| bwd.invert:block6.moe.shared | 0.132 | 0.138 | 0.0 | 3 |
| bwd.recompute:block6 | 3.290 | 3.350 | 0.8 | 3 |
| bwd.recompute:block6.ln1 | 0.062 | 0.067 | 0.0 | 3 |
| bwd.recompute:block6.attn.qkv | 0.096 | 0.129 | 0.0 | 3 |
| bwd.recompute:block6.attn.sdpa | 0.097 | 0.104 | 0.0 | 3 |
| bwd.recompute:block6.attn.proj | 0.048 | 0.070 | 0.0 | 3 |
| bwd.recompute:block6.ln2 | 0.042 | 0.048 | 0.0 | 3 |
| bwd.recompute:block6.moe.router | 0.129 | 0.151 | 0.0 | 3 |
| bwd.recompute:block6.moe.dispatch | 2.366 | 2.455 | 0.6 | 3 |
| bwd.recompute:block6.moe.dispatch.expert0 | 0.324 | 0.371 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert1 | 0.273 | 0.318 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert2 | 0.261 | 0.315 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert3 | 0.253 | 0.299 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert4 | 0.252 | 0.284 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert5 | 0.250 | 0.292 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert6 | 0.251 | 0.291 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert7 | 0.251 | 0.294 | 0.1 | 3 |
| bwd.recompute:block6.moe.shared | 0.136 | 0.146 | 0.0 | 3 |
| bwd:block6.grad | 8.349 | 11.454 | 2.0 | 3 |
| bwd:block5 | 12.906 | 18.053 | 3.2 | 2 |
| bwd.invert:block5 | 3.089 | 3.158 | 0.8 | 3 |
| bwd.invert:block5.ln1 | 0.060 | 0.062 | 0.0 | 3 |
| bwd.invert:block5.attn.qkv | 0.095 | 0.112 | 0.0 | 3 |
| bwd.invert:block5.attn.sdpa | 0.086 | 0.094 | 0.0 | 3 |
| bwd.invert:block5.attn.proj | 0.042 | 0.056 | 0.0 | 3 |
| bwd.invert:block5.ln2 | 0.040 | 0.045 | 0.0 | 3 |
| bwd.invert:block5.moe.router | 0.124 | 0.147 | 0.0 | 3 |
| bwd.invert:block5.moe.dispatch | 2.256 | 2.334 | 0.6 | 3 |
| bwd.invert:block5.moe.dispatch.expert0 | 0.316 | 0.362 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert1 | 0.258 | 0.312 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert2 | 0.240 | 0.289 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert3 | 0.236 | 0.285 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert4 | 0.235 | 0.290 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert5 | 0.234 | 0.273 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert6 | 0.232 | 0.267 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert7 | 0.233 | 0.286 | 0.1 | 3 |
| bwd.invert:block5.moe.shared | 0.133 | 0.140 | 0.0 | 3 |
| bwd.recompute:block5 | 3.293 | 3.355 | 0.8 | 3 |
| bwd.recompute:block5.ln1 | 0.062 | 0.066 | 0.0 | 3 |
| bwd.recompute:block5.attn.qkv | 0.097 | 0.125 | 0.0 | 3 |
| bwd.recompute:block5.attn.sdpa | 0.095 | 0.102 | 0.0 | 3 |
| bwd.recompute:block5.attn.proj | 0.047 | 0.067 | 0.0 | 3 |
| bwd.recompute:block5.ln2 | 0.042 | 0.047 | 0.0 | 3 |
| bwd.recompute:block5.moe.router | 0.129 | 0.157 | 0.0 | 3 |
| bwd.recompute:block5.moe.dispatch | 2.380 | 2.468 | 0.6 | 3 |
| bwd.recompute:block5.moe.dispatch.expert0 | 0.323 | 0.350 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert1 | 0.271 | 0.318 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert2 | 0.259 | 0.309 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert3 | 0.253 | 0.301 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert4 | 0.252 | 0.297 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert5 | 0.250 | 0.303 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert6 | 0.253 | 0.304 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert7 | 0.252 | 0.300 | 0.1 | 3 |
| bwd.recompute:block5.moe.shared | 0.136 | 0.144 | 0.0 | 3 |
| bwd:block5.grad | 7.355 | 10.188 | 1.8 | 3 |
| bwd:block4 | 14.253 | 17.263 | 3.5 | 2 |
| bwd.invert:block4 | 3.097 | 3.160 | 0.8 | 3 |
| bwd.invert:block4.ln1 | 0.061 | 0.064 | 0.0 | 3 |
| bwd.invert:block4.attn.qkv | 0.096 | 0.120 | 0.0 | 3 |
| bwd.invert:block4.attn.sdpa | 0.085 | 0.093 | 0.0 | 3 |
| bwd.invert:block4.attn.proj | 0.041 | 0.057 | 0.0 | 3 |
| bwd.invert:block4.ln2 | 0.040 | 0.045 | 0.0 | 3 |
| bwd.invert:block4.moe.router | 0.124 | 0.149 | 0.0 | 3 |
| bwd.invert:block4.moe.dispatch | 2.271 | 2.338 | 0.6 | 3 |
| bwd.invert:block4.moe.dispatch.expert0 | 0.318 | 0.371 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert1 | 0.257 | 0.306 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert2 | 0.241 | 0.287 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert3 | 0.236 | 0.278 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert4 | 0.236 | 0.289 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert5 | 0.234 | 0.285 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert6 | 0.235 | 0.281 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert7 | 0.237 | 0.277 | 0.1 | 3 |
| bwd.invert:block4.moe.shared | 0.132 | 0.140 | 0.0 | 3 |
| bwd.recompute:block4 | 3.290 | 3.351 | 0.8 | 3 |
| bwd.recompute:block4.ln1 | 0.061 | 0.064 | 0.0 | 3 |
| bwd.recompute:block4.attn.qkv | 0.097 | 0.122 | 0.0 | 3 |
| bwd.recompute:block4.attn.sdpa | 0.094 | 0.101 | 0.0 | 3 |
| bwd.recompute:block4.attn.proj | 0.046 | 0.064 | 0.0 | 3 |
| bwd.recompute:block4.ln2 | 0.042 | 0.047 | 0.0 | 3 |
| bwd.recompute:block4.moe.router | 0.129 | 0.153 | 0.0 | 3 |
| bwd.recompute:block4.moe.dispatch | 2.388 | 2.464 | 0.6 | 3 |
| bwd.recompute:block4.moe.dispatch.expert0 | 0.322 | 0.371 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert1 | 0.272 | 0.328 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert2 | 0.260 | 0.308 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert3 | 0.254 | 0.302 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert4 | 0.251 | 0.302 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert5 | 0.250 | 0.299 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert6 | 0.251 | 0.293 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert7 | 0.253 | 0.309 | 0.1 | 3 |
| bwd.recompute:block4.moe.shared | 0.136 | 0.146 | 0.0 | 3 |
| bwd:block4.grad | 7.462 | 9.758 | 1.8 | 3 |
| bwd:block3 | 12.883 | 17.922 | 3.1 | 2 |
| bwd.invert:block3 | 3.080 | 3.147 | 0.8 | 3 |
| bwd.invert:block3.ln1 | 0.060 | 0.064 | 0.0 | 3 |
| bwd.invert:block3.attn.qkv | 0.096 | 0.114 | 0.0 | 3 |
| bwd.invert:block3.attn.sdpa | 0.085 | 0.093 | 0.0 | 3 |
| bwd.invert:block3.attn.proj | 0.041 | 0.055 | 0.0 | 3 |
| bwd.invert:block3.ln2 | 0.039 | 0.044 | 0.0 | 3 |
| bwd.invert:block3.moe.router | 0.123 | 0.147 | 0.0 | 3 |
| bwd.invert:block3.moe.dispatch | 2.252 | 2.337 | 0.5 | 3 |
| bwd.invert:block3.moe.dispatch.expert0 | 0.318 | 0.356 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert1 | 0.258 | 0.273 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert2 | 0.241 | 0.279 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert3 | 0.236 | 0.289 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert4 | 0.235 | 0.275 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert5 | 0.235 | 0.288 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert6 | 0.232 | 0.281 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert7 | 0.233 | 0.276 | 0.1 | 3 |
| bwd.invert:block3.moe.shared | 0.133 | 0.141 | 0.0 | 3 |
| bwd.recompute:block3 | 3.278 | 3.350 | 0.8 | 3 |
| bwd.recompute:block3.ln1 | 0.061 | 0.065 | 0.0 | 3 |
| bwd.recompute:block3.attn.qkv | 0.096 | 0.123 | 0.0 | 3 |
| bwd.recompute:block3.attn.sdpa | 0.094 | 0.102 | 0.0 | 3 |
| bwd.recompute:block3.attn.proj | 0.046 | 0.070 | 0.0 | 3 |
| bwd.recompute:block3.ln2 | 0.042 | 0.048 | 0.0 | 3 |
| bwd.recompute:block3.moe.router | 0.130 | 0.162 | 0.0 | 3 |
| bwd.recompute:block3.moe.dispatch | 2.351 | 2.470 | 0.6 | 3 |
| bwd.recompute:block3.moe.dispatch.expert0 | 0.324 | 0.359 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert1 | 0.271 | 0.314 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert2 | 0.260 | 0.318 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert3 | 0.253 | 0.285 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert4 | 0.251 | 0.268 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert5 | 0.251 | 0.301 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert6 | 0.252 | 0.307 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert7 | 0.249 | 0.295 | 0.1 | 3 |
| bwd.recompute:block3.moe.shared | 0.136 | 0.144 | 0.0 | 3 |
| bwd:block3.grad | 6.928 | 9.585 | 1.7 | 3 |
| bwd:block2 | 14.367 | 18.800 | 3.5 | 2 |
| bwd.invert:block2 | 3.068 | 3.144 | 0.7 | 3 |
| bwd.invert:block2.ln1 | 0.060 | 0.065 | 0.0 | 3 |
| bwd.invert:block2.attn.qkv | 0.095 | 0.125 | 0.0 | 3 |
| bwd.invert:block2.attn.sdpa | 0.085 | 0.092 | 0.0 | 3 |
| bwd.invert:block2.attn.proj | 0.040 | 0.057 | 0.0 | 3 |
| bwd.invert:block2.ln2 | 0.039 | 0.045 | 0.0 | 3 |
| bwd.invert:block2.moe.router | 0.124 | 0.146 | 0.0 | 3 |
| bwd.invert:block2.moe.dispatch | 2.213 | 2.338 | 0.5 | 3 |
| bwd.invert:block2.moe.dispatch.expert0 | 0.319 | 0.351 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert1 | 0.257 | 0.291 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert2 | 0.244 | 0.287 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert3 | 0.242 | 0.266 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert4 | 0.236 | 0.275 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert5 | 0.232 | 0.280 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert6 | 0.232 | 0.281 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert7 | 0.231 | 0.282 | 0.1 | 3 |
| bwd.invert:block2.moe.shared | 0.132 | 0.142 | 0.0 | 3 |
| bwd.recompute:block2 | 3.299 | 3.397 | 0.8 | 3 |
| bwd.recompute:block2.ln1 | 0.062 | 0.067 | 0.0 | 3 |
| bwd.recompute:block2.attn.qkv | 0.097 | 0.122 | 0.0 | 3 |
| bwd.recompute:block2.attn.sdpa | 0.094 | 0.100 | 0.0 | 3 |
| bwd.recompute:block2.attn.proj | 0.047 | 0.060 | 0.0 | 3 |
| bwd.recompute:block2.ln2 | 0.042 | 0.047 | 0.0 | 3 |
| bwd.recompute:block2.moe.router | 0.128 | 0.157 | 0.0 | 3 |
| bwd.recompute:block2.moe.dispatch | 2.397 | 2.501 | 0.6 | 3 |
| bwd.recompute:block2.moe.dispatch.expert0 | 0.326 | 0.391 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert1 | 0.273 | 0.329 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert2 | 0.262 | 0.305 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert3 | 0.259 | 0.291 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert4 | 0.253 | 0.292 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert5 | 0.250 | 0.290 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert6 | 0.251 | 0.282 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert7 | 0.249 | 0.290 | 0.1 | 3 |
| bwd.recompute:block2.moe.shared | 0.135 | 0.146 | 0.0 | 3 |
| bwd:block2.grad | 7.910 | 11.115 | 1.9 | 3 |
| bwd:block1 | 14.524 | 18.615 | 3.5 | 2 |
| bwd.invert:block1 | 3.083 | 3.153 | 0.8 | 3 |
| bwd.invert:block1.ln1 | 0.060 | 0.063 | 0.0 | 3 |
| bwd.invert:block1.attn.qkv | 0.093 | 0.119 | 0.0 | 3 |
| bwd.invert:block1.attn.sdpa | 0.084 | 0.091 | 0.0 | 3 |
| bwd.invert:block1.attn.proj | 0.040 | 0.062 | 0.0 | 3 |
| bwd.invert:block1.ln2 | 0.040 | 0.045 | 0.0 | 3 |
| bwd.invert:block1.moe.router | 0.123 | 0.148 | 0.0 | 3 |
| bwd.invert:block1.moe.dispatch | 2.257 | 2.346 | 0.6 | 3 |
| bwd.invert:block1.moe.dispatch.expert0 | 0.319 | 0.361 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert1 | 0.260 | 0.290 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert2 | 0.241 | 0.275 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert3 | 0.236 | 0.281 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert4 | 0.240 | 0.290 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert5 | 0.234 | 0.305 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert6 | 0.232 | 0.263 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert7 | 0.234 | 0.272 | 0.1 | 3 |
| bwd.invert:block1.moe.shared | 0.132 | 0.143 | 0.0 | 3 |
| bwd.recompute:block1 | 3.294 | 3.372 | 0.8 | 3 |
| bwd.recompute:block1.ln1 | 0.061 | 0.064 | 0.0 | 3 |
| bwd.recompute:block1.attn.qkv | 0.097 | 0.121 | 0.0 | 3 |
| bwd.recompute:block1.attn.sdpa | 0.094 | 0.097 | 0.0 | 3 |
| bwd.recompute:block1.attn.proj | 0.047 | 0.060 | 0.0 | 3 |
| bwd.recompute:block1.ln2 | 0.041 | 0.046 | 0.0 | 3 |
| bwd.recompute:block1.moe.router | 0.128 | 0.154 | 0.0 | 3 |
| bwd.recompute:block1.moe.dispatch | 2.404 | 2.471 | 0.6 | 3 |
| bwd.recompute:block1.moe.dispatch.expert0 | 0.323 | 0.362 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert1 | 0.273 | 0.329 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert2 | 0.261 | 0.322 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert3 | 0.256 | 0.307 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert4 | 0.254 | 0.292 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert5 | 0.250 | 0.289 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert6 | 0.251 | 0.307 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert7 | 0.250 | 0.307 | 0.1 | 3 |
| bwd.recompute:block1.moe.shared | 0.135 | 0.150 | 0.0 | 3 |
| bwd:block1.grad | 7.081 | 10.597 | 1.7 | 3 |
| bwd:block0 | 12.573 | 16.960 | 3.1 | 2 |
| bwd.invert:block0 | 3.090 | 3.161 | 0.8 | 3 |
| bwd.invert:block0.ln1 | 0.061 | 0.065 | 0.0 | 3 |
| bwd.invert:block0.attn.qkv | 0.093 | 0.116 | 0.0 | 3 |
| bwd.invert:block0.attn.sdpa | 0.084 | 0.090 | 0.0 | 3 |
| bwd.invert:block0.attn.proj | 0.041 | 0.053 | 0.0 | 3 |
| bwd.invert:block0.ln2 | 0.040 | 0.044 | 0.0 | 3 |
| bwd.invert:block0.moe.router | 0.123 | 0.150 | 0.0 | 3 |
| bwd.invert:block0.moe.dispatch | 2.279 | 2.355 | 0.6 | 3 |
| bwd.invert:block0.moe.dispatch.expert0 | 0.320 | 0.371 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert1 | 0.260 | 0.301 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert2 | 0.243 | 0.276 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert3 | 0.237 | 0.279 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert4 | 0.239 | 0.301 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert5 | 0.235 | 0.281 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert6 | 0.233 | 0.261 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert7 | 0.231 | 0.275 | 0.1 | 3 |
| bwd.invert:block0.moe.shared | 0.132 | 0.141 | 0.0 | 3 |
| bwd.recompute:block0 | 3.291 | 3.348 | 0.8 | 3 |
| bwd.recompute:block0.ln1 | 0.062 | 0.065 | 0.0 | 3 |
| bwd.recompute:block0.attn.qkv | 0.097 | 0.118 | 0.0 | 3 |
| bwd.recompute:block0.attn.sdpa | 0.094 | 0.098 | 0.0 | 3 |
| bwd.recompute:block0.attn.proj | 0.046 | 0.063 | 0.0 | 3 |
| bwd.recompute:block0.ln2 | 0.042 | 0.046 | 0.0 | 3 |
| bwd.recompute:block0.moe.router | 0.128 | 0.155 | 0.0 | 3 |
| bwd.recompute:block0.moe.dispatch | 2.399 | 2.464 | 0.6 | 3 |
| bwd.recompute:block0.moe.dispatch.expert0 | 0.324 | 0.387 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert1 | 0.272 | 0.318 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert2 | 0.260 | 0.303 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert3 | 0.254 | 0.313 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert4 | 0.254 | 0.294 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert5 | 0.251 | 0.284 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert6 | 0.251 | 0.284 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert7 | 0.249 | 0.303 | 0.1 | 3 |
| bwd.recompute:block0.moe.shared | 0.135 | 0.146 | 0.0 | 3 |
| bwd:block0.grad | 6.771 | 7.987 | 1.7 | 3 |
| bwd:embed | 0.235 | 0.275 | 0.1 | 2 |
| opt | 77.333 | 78.138 | 18.9 | 1 |
| opt:opt.clip | 2.831 | 3.100 | 0.7 | 2 |
| opt:opt.muon | 72.196 | 72.911 | 17.6 | 2 |
| opt:opt.muon.ns | 68.712 | 69.396 | 16.8 | 3 |
| opt:opt.adamw | 1.091 | 1.180 | 0.3 | 2 |
| opt:opt.moe_bias | 0.455 | 0.508 | 0.1 | 3 |
| opt:opt.zero_grad | 0.566 | 0.674 | 0.1 | 3 |

## Time by part type (sum over layers)

| part type | median ms sum | % of step |
| :--- | ---: | ---: |
| bwd | 144.002 | 35.2 |
| bwd:stack | 127.442 | 31.1 |
| bwd:block* | 121.426 | 29.6 |
| opt | 77.333 | 18.9 |
| opt:opt.muon | 72.196 | 17.6 |
| opt:opt.muon.ns | 68.712 | 16.8 |
| bwd:block*.grad | 66.888 | 16.3 |
| fwd | 61.570 | 15.0 |
| fwd:stack | 43.382 | 10.6 |
| fwd:block* | 40.746 | 9.9 |
| fwd:block*.moe.dispatch | 34.662 | 8.5 |
| bwd.recompute:block* | 29.590 | 7.2 |
| bwd.invert:block* | 27.436 | 6.7 |
| bwd.recompute:block*.moe.dispatch | 21.495 | 5.2 |
| bwd.invert:block*.moe.dispatch | 20.269 | 4.9 |
| bwd:head+loss | 16.308 | 4.0 |
| fwd:head+loss | 16.163 | 3.9 |
| fwd:block*.moe.dispatch.expert0 | 4.575 | 1.1 |
| fwd:block*.moe.dispatch.expert2 | 4.178 | 1.0 |
| fwd:block*.moe.dispatch.expert1 | 4.173 | 1.0 |
| fwd:block*.moe.dispatch.expert3 | 4.154 | 1.0 |
| fwd:block*.moe.dispatch.expert5 | 4.062 | 1.0 |
| fwd:block*.moe.dispatch.expert7 | 3.955 | 1.0 |
| fwd:block*.moe.dispatch.expert6 | 3.832 | 0.9 |
| fwd:block*.moe.dispatch.expert4 | 3.830 | 0.9 |
| bwd.recompute:block*.moe.dispatch.expert0 | 2.917 | 0.7 |
| bwd.invert:block*.moe.dispatch.expert0 | 2.880 | 0.7 |
| opt:opt.clip | 2.831 | 0.7 |
| bwd.recompute:block*.moe.dispatch.expert1 | 2.453 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert2 | 2.347 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert1 | 2.341 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert3 | 2.295 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert4 | 2.275 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert6 | 2.269 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert5 | 2.256 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert7 | 2.256 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert2 | 2.185 | 0.5 |
| bwd.invert:block*.moe.dispatch.expert3 | 2.135 | 0.5 |
| bwd.invert:block*.moe.dispatch.expert4 | 2.128 | 0.5 |
| bwd.invert:block*.moe.dispatch.expert5 | 2.107 | 0.5 |
| bwd.invert:block*.moe.dispatch.expert7 | 2.099 | 0.5 |
| bwd.invert:block*.moe.dispatch.expert6 | 2.095 | 0.5 |
| fwd:embed | 1.974 | 0.5 |
| fwd:embed.ke | 1.931 | 0.5 |
| fwd:block*.moe.router | 1.397 | 0.3 |
| fwd:block*.moe.shared | 1.222 | 0.3 |
| bwd.recompute:block*.moe.shared | 1.222 | 0.3 |
| bwd.invert:block*.moe.shared | 1.192 | 0.3 |
| bwd.recompute:block*.moe.router | 1.165 | 0.3 |
| opt:opt.adamw | 1.091 | 0.3 |
| bwd.invert:block*.moe.router | 1.027 | 0.3 |
| bwd.recompute:block*.attn.qkv | 0.871 | 0.2 |
| bwd.recompute:block*.attn.sdpa | 0.860 | 0.2 |
| bwd.invert:block*.attn.qkv | 0.786 | 0.2 |
| fwd:block*.attn.sdpa | 0.758 | 0.2 |
| bwd.invert:block*.attn.sdpa | 0.724 | 0.2 |
| data | 0.678 | 0.2 |
| fwd:block*.attn.qkv | 0.641 | 0.2 |
| opt:opt.zero_grad | 0.566 | 0.1 |
| bwd.recompute:block*.ln1 | 0.554 | 0.1 |
| bwd.invert:block*.ln1 | 0.518 | 0.1 |
| fwd:block*.ln1 | 0.472 | 0.1 |
| opt:opt.moe_bias | 0.455 | 0.1 |
| bwd.recompute:block*.attn.proj | 0.425 | 0.1 |
| bwd.recompute:block*.ln2 | 0.376 | 0.1 |
| bwd.invert:block*.ln2 | 0.350 | 0.1 |
| bwd.invert:block*.attn.proj | 0.347 | 0.1 |
| fwd:block*.ln2 | 0.340 | 0.1 |
| fwd:block*.attn.proj | 0.327 | 0.1 |
| bwd:embed | 0.235 | 0.1 |

## Five slowest leaf parts

1. `opt:opt.muon.ns` — 68.712 ms (16.8% of step)
2. `bwd:block6.grad` — 8.349 ms (2.0% of step)
3. `bwd:block2.grad` — 7.910 ms (1.9% of step)
4. `bwd:block8.grad` — 7.593 ms (1.9% of step)
5. `bwd:block4.grad` — 7.462 ms (1.8% of step)
