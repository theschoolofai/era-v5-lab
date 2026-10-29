# Bench report — h200_v1_muon_batched

**GPU:** NVIDIA H200  |  **dtype:** bf16  |  **B x T:** 32 x 512  |  **torch:** 2.11.0+cu128
**commit:** `19221759f9d820ce0563d5d2f44e22eac0de53d2`  |  **tag:** h200_v1_muon_batched

## Step (clean)

- median: 354.766 ms
- p10..p90: 251.949 .. 502.250 ms
- tokens/s: 46,183
- MFU: 1.5%  |  HFU: 1.9%

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
| data | 0.652 | 0.791 | 0.2 | 1 |
| fwd | 64.196 | 73.150 | 18.1 | 1 |
| fwd:embed | 1.968 | 2.039 | 0.6 | 2 |
| fwd:embed.ke | 1.927 | 1.944 | 0.5 | 3 |
| fwd:stack | 45.914 | 54.847 | 12.9 | 1 |
| fwd:block0 | 4.866 | 6.861 | 1.4 | 2 |
| fwd:block0.ln1 | 0.033 | 0.033 | 0.0 | 3 |
| fwd:block0.attn.qkv | 0.025 | 0.026 | 0.0 | 3 |
| fwd:block0.attn.sdpa | 0.043 | 0.043 | 0.0 | 3 |
| fwd:block0.attn.proj | 0.018 | 0.019 | 0.0 | 3 |
| fwd:block0.ln2 | 0.033 | 0.033 | 0.0 | 3 |
| fwd:block0.moe.router | 0.087 | 0.089 | 0.0 | 3 |
| fwd:block0.moe.dispatch | 3.617 | 5.481 | 1.0 | 3 |
| fwd:block0.moe.dispatch.expert0 | 0.364 | 0.604 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert1 | 0.477 | 0.547 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert2 | 0.507 | 0.657 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert3 | 0.345 | 0.556 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert4 | 0.474 | 0.619 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert5 | 0.497 | 1.907 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert6 | 0.474 | 0.529 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert7 | 0.268 | 0.502 | 0.1 | 3 |
| fwd:block0.moe.shared | 0.135 | 0.144 | 0.0 | 3 |
| fwd:block1 | 4.613 | 7.384 | 1.3 | 2 |
| fwd:block1.ln1 | 0.055 | 0.058 | 0.0 | 3 |
| fwd:block1.attn.qkv | 0.076 | 0.098 | 0.0 | 3 |
| fwd:block1.attn.sdpa | 0.088 | 0.094 | 0.0 | 3 |
| fwd:block1.attn.proj | 0.037 | 0.055 | 0.0 | 3 |
| fwd:block1.ln2 | 0.039 | 0.045 | 0.0 | 3 |
| fwd:block1.moe.router | 0.164 | 0.192 | 0.0 | 3 |
| fwd:block1.moe.dispatch | 3.801 | 6.166 | 1.1 | 3 |
| fwd:block1.moe.dispatch.expert0 | 0.390 | 0.579 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert1 | 0.516 | 2.028 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert2 | 0.354 | 0.582 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert3 | 0.275 | 0.528 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert4 | 0.500 | 2.098 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert5 | 0.369 | 0.510 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert6 | 0.333 | 0.520 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert7 | 0.478 | 1.697 | 0.1 | 3 |
| fwd:block1.moe.shared | 0.136 | 0.150 | 0.0 | 3 |
| fwd:block2 | 5.292 | 7.240 | 1.5 | 2 |
| fwd:block2.ln1 | 0.054 | 0.058 | 0.0 | 3 |
| fwd:block2.attn.qkv | 0.076 | 0.102 | 0.0 | 3 |
| fwd:block2.attn.sdpa | 0.088 | 0.093 | 0.0 | 3 |
| fwd:block2.attn.proj | 0.038 | 0.052 | 0.0 | 3 |
| fwd:block2.ln2 | 0.039 | 0.043 | 0.0 | 3 |
| fwd:block2.moe.router | 0.163 | 0.192 | 0.0 | 3 |
| fwd:block2.moe.dispatch | 3.761 | 5.443 | 1.1 | 3 |
| fwd:block2.moe.dispatch.expert0 | 0.561 | 0.638 | 0.2 | 3 |
| fwd:block2.moe.dispatch.expert1 | 0.397 | 0.541 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert2 | 0.492 | 0.536 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert3 | 0.502 | 2.195 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert4 | 0.309 | 0.535 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert5 | 0.464 | 0.526 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert6 | 0.463 | 0.525 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert7 | 0.473 | 0.542 | 0.1 | 3 |
| fwd:block2.moe.shared | 0.135 | 0.145 | 0.0 | 3 |
| fwd:block3 | 5.289 | 7.831 | 1.5 | 2 |
| fwd:block3.ln1 | 0.054 | 0.059 | 0.0 | 3 |
| fwd:block3.attn.qkv | 0.076 | 0.099 | 0.0 | 3 |
| fwd:block3.attn.sdpa | 0.089 | 0.093 | 0.0 | 3 |
| fwd:block3.attn.proj | 0.037 | 0.050 | 0.0 | 3 |
| fwd:block3.ln2 | 0.038 | 0.042 | 0.0 | 3 |
| fwd:block3.moe.router | 0.162 | 0.190 | 0.0 | 3 |
| fwd:block3.moe.dispatch | 4.029 | 5.761 | 1.1 | 3 |
| fwd:block3.moe.dispatch.expert0 | 0.557 | 0.705 | 0.2 | 3 |
| fwd:block3.moe.dispatch.expert1 | 0.311 | 0.531 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert2 | 0.508 | 2.157 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert3 | 0.477 | 0.568 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert4 | 0.470 | 0.535 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert5 | 0.498 | 2.038 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert6 | 0.370 | 0.507 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert7 | 0.463 | 0.529 | 0.1 | 3 |
| fwd:block3.moe.shared | 0.135 | 0.142 | 0.0 | 3 |
| fwd:block4 | 5.306 | 7.149 | 1.5 | 2 |
| fwd:block4.ln1 | 0.054 | 0.058 | 0.0 | 3 |
| fwd:block4.attn.qkv | 0.076 | 0.096 | 0.0 | 3 |
| fwd:block4.attn.sdpa | 0.088 | 0.093 | 0.0 | 3 |
| fwd:block4.attn.proj | 0.038 | 0.051 | 0.0 | 3 |
| fwd:block4.ln2 | 0.038 | 0.042 | 0.0 | 3 |
| fwd:block4.moe.router | 0.161 | 0.187 | 0.0 | 3 |
| fwd:block4.moe.dispatch | 3.947 | 5.812 | 1.1 | 3 |
| fwd:block4.moe.dispatch.expert0 | 0.553 | 0.623 | 0.2 | 3 |
| fwd:block4.moe.dispatch.expert1 | 0.502 | 0.618 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert2 | 0.487 | 0.553 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert3 | 0.490 | 2.022 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert4 | 0.352 | 0.510 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert5 | 0.376 | 0.528 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert6 | 0.488 | 2.138 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert7 | 0.477 | 0.546 | 0.1 | 3 |
| fwd:block4.moe.shared | 0.136 | 0.145 | 0.0 | 3 |
| fwd:block5 | 5.421 | 7.734 | 1.5 | 2 |
| fwd:block5.ln1 | 0.054 | 0.059 | 0.0 | 3 |
| fwd:block5.attn.qkv | 0.076 | 0.103 | 0.0 | 3 |
| fwd:block5.attn.sdpa | 0.089 | 0.094 | 0.0 | 3 |
| fwd:block5.attn.proj | 0.038 | 0.057 | 0.0 | 3 |
| fwd:block5.ln2 | 0.039 | 0.044 | 0.0 | 3 |
| fwd:block5.moe.router | 0.162 | 0.191 | 0.0 | 3 |
| fwd:block5.moe.dispatch | 4.109 | 5.626 | 1.2 | 3 |
| fwd:block5.moe.dispatch.expert0 | 0.546 | 0.651 | 0.2 | 3 |
| fwd:block5.moe.dispatch.expert1 | 0.493 | 0.553 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert2 | 0.480 | 0.595 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert3 | 0.352 | 0.511 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert4 | 0.358 | 0.500 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert5 | 0.538 | 1.691 | 0.2 | 3 |
| fwd:block5.moe.dispatch.expert6 | 0.488 | 0.599 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert7 | 0.489 | 1.860 | 0.1 | 3 |
| fwd:block5.moe.shared | 0.137 | 0.148 | 0.0 | 3 |
| fwd:block6 | 5.512 | 7.642 | 1.6 | 2 |
| fwd:block6.ln1 | 0.054 | 0.056 | 0.0 | 3 |
| fwd:block6.attn.qkv | 0.076 | 0.091 | 0.0 | 3 |
| fwd:block6.attn.sdpa | 0.089 | 0.092 | 0.0 | 3 |
| fwd:block6.attn.proj | 0.037 | 0.056 | 0.0 | 3 |
| fwd:block6.ln2 | 0.038 | 0.041 | 0.0 | 3 |
| fwd:block6.moe.router | 0.163 | 0.200 | 0.0 | 3 |
| fwd:block6.moe.dispatch | 3.888 | 5.698 | 1.1 | 3 |
| fwd:block6.moe.dispatch.expert0 | 0.554 | 0.666 | 0.2 | 3 |
| fwd:block6.moe.dispatch.expert1 | 0.501 | 0.574 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert2 | 0.473 | 0.558 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert3 | 0.476 | 0.573 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert4 | 0.479 | 0.603 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert5 | 0.483 | 1.824 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert6 | 0.475 | 0.578 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert7 | 0.481 | 0.614 | 0.1 | 3 |
| fwd:block6.moe.shared | 0.136 | 0.146 | 0.0 | 3 |
| fwd:block7 | 4.310 | 7.055 | 1.2 | 2 |
| fwd:block7.ln1 | 0.054 | 0.056 | 0.0 | 3 |
| fwd:block7.attn.qkv | 0.077 | 0.089 | 0.0 | 3 |
| fwd:block7.attn.sdpa | 0.087 | 0.090 | 0.0 | 3 |
| fwd:block7.attn.proj | 0.038 | 0.051 | 0.0 | 3 |
| fwd:block7.ln2 | 0.038 | 0.041 | 0.0 | 3 |
| fwd:block7.moe.router | 0.162 | 0.188 | 0.0 | 3 |
| fwd:block7.moe.dispatch | 3.788 | 5.760 | 1.1 | 3 |
| fwd:block7.moe.dispatch.expert0 | 0.339 | 0.586 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert1 | 0.487 | 0.606 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert2 | 0.320 | 0.557 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert3 | 0.474 | 0.537 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert4 | 0.493 | 2.101 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert5 | 0.488 | 0.592 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert6 | 0.469 | 0.552 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert7 | 0.477 | 1.659 | 0.1 | 3 |
| fwd:block7.moe.shared | 0.136 | 0.146 | 0.0 | 3 |
| fwd:block8 | 4.171 | 6.166 | 1.2 | 2 |
| fwd:block8.ln1 | 0.054 | 0.057 | 0.0 | 3 |
| fwd:block8.attn.qkv | 0.076 | 0.102 | 0.0 | 3 |
| fwd:block8.attn.sdpa | 0.088 | 0.093 | 0.0 | 3 |
| fwd:block8.attn.proj | 0.037 | 0.051 | 0.0 | 3 |
| fwd:block8.ln2 | 0.038 | 0.045 | 0.0 | 3 |
| fwd:block8.moe.router | 0.162 | 0.189 | 0.0 | 3 |
| fwd:block8.moe.dispatch | 3.714 | 5.006 | 1.0 | 3 |
| fwd:block8.moe.dispatch.expert0 | 0.550 | 1.580 | 0.2 | 3 |
| fwd:block8.moe.dispatch.expert1 | 0.492 | 0.593 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert2 | 0.480 | 0.584 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert3 | 0.469 | 0.522 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert4 | 0.470 | 0.552 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert5 | 0.470 | 0.527 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert6 | 0.462 | 0.491 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert7 | 0.467 | 0.563 | 0.1 | 3 |
| fwd:block8.moe.shared | 0.135 | 0.145 | 0.0 | 3 |
| fwd:head+loss | 16.160 | 16.237 | 4.6 | 2 |
| bwd | 147.962 | 174.020 | 41.7 | 1 |
| bwd:head+loss | 16.317 | 16.332 | 4.6 | 2 |
| bwd:stack | 131.419 | 157.463 | 37.0 | 1 |
| bwd:block8 | 13.190 | 19.409 | 3.7 | 2 |
| bwd.invert:block8 | 2.719 | 2.818 | 0.8 | 3 |
| bwd.invert:block8.ln1 | 0.034 | 0.035 | 0.0 | 3 |
| bwd.invert:block8.attn.qkv | 0.026 | 0.027 | 0.0 | 3 |
| bwd.invert:block8.attn.sdpa | 0.043 | 0.043 | 0.0 | 3 |
| bwd.invert:block8.attn.proj | 0.018 | 0.019 | 0.0 | 3 |
| bwd.invert:block8.ln2 | 0.032 | 0.033 | 0.0 | 3 |
| bwd.invert:block8.moe.router | 0.036 | 0.037 | 0.0 | 3 |
| bwd.invert:block8.moe.dispatch | 2.207 | 2.324 | 0.6 | 3 |
| bwd.invert:block8.moe.dispatch.expert0 | 0.332 | 0.365 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert1 | 0.271 | 0.313 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert2 | 0.247 | 0.294 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert3 | 0.239 | 0.286 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert4 | 0.237 | 0.287 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert5 | 0.235 | 0.274 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert6 | 0.232 | 0.265 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert7 | 0.231 | 0.265 | 0.1 | 3 |
| bwd.invert:block8.moe.shared | 0.133 | 0.139 | 0.0 | 3 |
| bwd.recompute:block8 | 3.203 | 3.323 | 0.9 | 3 |
| bwd.recompute:block8.ln1 | 0.061 | 0.065 | 0.0 | 3 |
| bwd.recompute:block8.attn.qkv | 0.096 | 0.117 | 0.0 | 3 |
| bwd.recompute:block8.attn.sdpa | 0.098 | 0.106 | 0.0 | 3 |
| bwd.recompute:block8.attn.proj | 0.049 | 0.071 | 0.0 | 3 |
| bwd.recompute:block8.ln2 | 0.042 | 0.048 | 0.0 | 3 |
| bwd.recompute:block8.moe.router | 0.130 | 0.155 | 0.0 | 3 |
| bwd.recompute:block8.moe.dispatch | 2.395 | 2.499 | 0.7 | 3 |
| bwd.recompute:block8.moe.dispatch.expert0 | 0.328 | 0.375 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert1 | 0.272 | 0.327 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert2 | 0.261 | 0.314 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert3 | 0.255 | 0.312 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert4 | 0.252 | 0.300 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert5 | 0.251 | 0.302 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert6 | 0.252 | 0.300 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert7 | 0.251 | 0.305 | 0.1 | 3 |
| bwd.recompute:block8.moe.shared | 0.136 | 0.144 | 0.0 | 3 |
| bwd:block8.grad | 7.374 | 9.019 | 2.1 | 3 |
| bwd:block7 | 14.019 | 18.879 | 4.0 | 2 |
| bwd.invert:block7 | 3.070 | 3.152 | 0.9 | 3 |
| bwd.invert:block7.ln1 | 0.060 | 0.063 | 0.0 | 3 |
| bwd.invert:block7.attn.qkv | 0.096 | 0.120 | 0.0 | 3 |
| bwd.invert:block7.attn.sdpa | 0.084 | 0.092 | 0.0 | 3 |
| bwd.invert:block7.attn.proj | 0.040 | 0.054 | 0.0 | 3 |
| bwd.invert:block7.ln2 | 0.040 | 0.044 | 0.0 | 3 |
| bwd.invert:block7.moe.router | 0.122 | 0.147 | 0.0 | 3 |
| bwd.invert:block7.moe.dispatch | 2.243 | 2.326 | 0.6 | 3 |
| bwd.invert:block7.moe.dispatch.expert0 | 0.319 | 0.371 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert1 | 0.257 | 0.309 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert2 | 0.240 | 0.294 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert3 | 0.236 | 0.284 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert4 | 0.239 | 0.287 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert5 | 0.234 | 0.258 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert6 | 0.233 | 0.269 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert7 | 0.234 | 0.278 | 0.1 | 3 |
| bwd.invert:block7.moe.shared | 0.133 | 0.140 | 0.0 | 3 |
| bwd.recompute:block7 | 3.278 | 3.359 | 0.9 | 3 |
| bwd.recompute:block7.ln1 | 0.061 | 0.064 | 0.0 | 3 |
| bwd.recompute:block7.attn.qkv | 0.094 | 0.120 | 0.0 | 3 |
| bwd.recompute:block7.attn.sdpa | 0.096 | 0.100 | 0.0 | 3 |
| bwd.recompute:block7.attn.proj | 0.046 | 0.067 | 0.0 | 3 |
| bwd.recompute:block7.ln2 | 0.041 | 0.046 | 0.0 | 3 |
| bwd.recompute:block7.moe.router | 0.129 | 0.157 | 0.0 | 3 |
| bwd.recompute:block7.moe.dispatch | 2.384 | 2.456 | 0.7 | 3 |
| bwd.recompute:block7.moe.dispatch.expert0 | 0.321 | 0.361 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert1 | 0.269 | 0.311 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert2 | 0.256 | 0.304 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert3 | 0.255 | 0.302 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert4 | 0.256 | 0.304 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert5 | 0.252 | 0.305 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert6 | 0.252 | 0.293 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert7 | 0.251 | 0.309 | 0.1 | 3 |
| bwd.recompute:block7.moe.shared | 0.136 | 0.145 | 0.0 | 3 |
| bwd:block7.grad | 7.531 | 10.800 | 2.1 | 3 |
| bwd:block6 | 15.214 | 20.567 | 4.3 | 2 |
| bwd.invert:block6 | 3.074 | 3.157 | 0.9 | 3 |
| bwd.invert:block6.ln1 | 0.060 | 0.063 | 0.0 | 3 |
| bwd.invert:block6.attn.qkv | 0.095 | 0.112 | 0.0 | 3 |
| bwd.invert:block6.attn.sdpa | 0.085 | 0.092 | 0.0 | 3 |
| bwd.invert:block6.attn.proj | 0.041 | 0.062 | 0.0 | 3 |
| bwd.invert:block6.ln2 | 0.040 | 0.044 | 0.0 | 3 |
| bwd.invert:block6.moe.router | 0.122 | 0.146 | 0.0 | 3 |
| bwd.invert:block6.moe.dispatch | 2.244 | 2.328 | 0.6 | 3 |
| bwd.invert:block6.moe.dispatch.expert0 | 0.317 | 0.366 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert1 | 0.256 | 0.297 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert2 | 0.240 | 0.286 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert3 | 0.234 | 0.287 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert4 | 0.234 | 0.280 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert5 | 0.233 | 0.281 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert6 | 0.232 | 0.282 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert7 | 0.232 | 0.257 | 0.1 | 3 |
| bwd.invert:block6.moe.shared | 0.133 | 0.139 | 0.0 | 3 |
| bwd.recompute:block6 | 3.264 | 3.336 | 0.9 | 3 |
| bwd.recompute:block6.ln1 | 0.061 | 0.065 | 0.0 | 3 |
| bwd.recompute:block6.attn.qkv | 0.095 | 0.125 | 0.0 | 3 |
| bwd.recompute:block6.attn.sdpa | 0.095 | 0.102 | 0.0 | 3 |
| bwd.recompute:block6.attn.proj | 0.046 | 0.063 | 0.0 | 3 |
| bwd.recompute:block6.ln2 | 0.042 | 0.046 | 0.0 | 3 |
| bwd.recompute:block6.moe.router | 0.127 | 0.150 | 0.0 | 3 |
| bwd.recompute:block6.moe.dispatch | 2.370 | 2.445 | 0.7 | 3 |
| bwd.recompute:block6.moe.dispatch.expert0 | 0.319 | 0.351 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert1 | 0.268 | 0.306 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert2 | 0.258 | 0.311 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert3 | 0.253 | 0.312 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert4 | 0.251 | 0.296 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert5 | 0.251 | 0.294 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert6 | 0.251 | 0.302 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert7 | 0.248 | 0.298 | 0.1 | 3 |
| bwd.recompute:block6.moe.shared | 0.136 | 0.146 | 0.0 | 3 |
| bwd:block6.grad | 7.663 | 10.832 | 2.2 | 3 |
| bwd:block5 | 14.394 | 20.170 | 4.1 | 2 |
| bwd.invert:block5 | 3.067 | 3.151 | 0.9 | 3 |
| bwd.invert:block5.ln1 | 0.060 | 0.063 | 0.0 | 3 |
| bwd.invert:block5.attn.qkv | 0.095 | 0.117 | 0.0 | 3 |
| bwd.invert:block5.attn.sdpa | 0.085 | 0.092 | 0.0 | 3 |
| bwd.invert:block5.attn.proj | 0.041 | 0.052 | 0.0 | 3 |
| bwd.invert:block5.ln2 | 0.040 | 0.046 | 0.0 | 3 |
| bwd.invert:block5.moe.router | 0.122 | 0.149 | 0.0 | 3 |
| bwd.invert:block5.moe.dispatch | 2.250 | 2.330 | 0.6 | 3 |
| bwd.invert:block5.moe.dispatch.expert0 | 0.318 | 0.388 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert1 | 0.256 | 0.299 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert2 | 0.239 | 0.284 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert3 | 0.233 | 0.285 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert4 | 0.234 | 0.285 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert5 | 0.240 | 0.276 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert6 | 0.234 | 0.267 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert7 | 0.234 | 0.276 | 0.1 | 3 |
| bwd.invert:block5.moe.shared | 0.134 | 0.140 | 0.0 | 3 |
| bwd.recompute:block5 | 3.268 | 3.336 | 0.9 | 3 |
| bwd.recompute:block5.ln1 | 0.061 | 0.064 | 0.0 | 3 |
| bwd.recompute:block5.attn.qkv | 0.094 | 0.105 | 0.0 | 3 |
| bwd.recompute:block5.attn.sdpa | 0.093 | 0.098 | 0.0 | 3 |
| bwd.recompute:block5.attn.proj | 0.045 | 0.052 | 0.0 | 3 |
| bwd.recompute:block5.ln2 | 0.041 | 0.044 | 0.0 | 3 |
| bwd.recompute:block5.moe.router | 0.126 | 0.151 | 0.0 | 3 |
| bwd.recompute:block5.moe.dispatch | 2.386 | 2.456 | 0.7 | 3 |
| bwd.recompute:block5.moe.dispatch.expert0 | 0.321 | 0.367 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert1 | 0.270 | 0.315 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert2 | 0.259 | 0.319 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert3 | 0.254 | 0.328 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert4 | 0.251 | 0.298 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert5 | 0.253 | 0.294 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert6 | 0.252 | 0.305 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert7 | 0.252 | 0.297 | 0.1 | 3 |
| bwd.recompute:block5.moe.shared | 0.136 | 0.145 | 0.0 | 3 |
| bwd:block5.grad | 7.893 | 9.947 | 2.2 | 3 |
| bwd:block4 | 14.574 | 19.266 | 4.1 | 2 |
| bwd.invert:block4 | 3.065 | 3.129 | 0.9 | 3 |
| bwd.invert:block4.ln1 | 0.060 | 0.065 | 0.0 | 3 |
| bwd.invert:block4.attn.qkv | 0.096 | 0.124 | 0.0 | 3 |
| bwd.invert:block4.attn.sdpa | 0.084 | 0.091 | 0.0 | 3 |
| bwd.invert:block4.attn.proj | 0.040 | 0.058 | 0.0 | 3 |
| bwd.invert:block4.ln2 | 0.040 | 0.046 | 0.0 | 3 |
| bwd.invert:block4.moe.router | 0.121 | 0.149 | 0.0 | 3 |
| bwd.invert:block4.moe.dispatch | 2.229 | 2.321 | 0.6 | 3 |
| bwd.invert:block4.moe.dispatch.expert0 | 0.319 | 0.360 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert1 | 0.256 | 0.295 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert2 | 0.238 | 0.287 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert3 | 0.239 | 0.275 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert4 | 0.233 | 0.277 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert5 | 0.232 | 0.253 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert6 | 0.236 | 0.281 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert7 | 0.233 | 0.290 | 0.1 | 3 |
| bwd.invert:block4.moe.shared | 0.133 | 0.143 | 0.0 | 3 |
| bwd.recompute:block4 | 3.267 | 3.345 | 0.9 | 3 |
| bwd.recompute:block4.ln1 | 0.061 | 0.065 | 0.0 | 3 |
| bwd.recompute:block4.attn.qkv | 0.095 | 0.126 | 0.0 | 3 |
| bwd.recompute:block4.attn.sdpa | 0.092 | 0.098 | 0.0 | 3 |
| bwd.recompute:block4.attn.proj | 0.046 | 0.063 | 0.0 | 3 |
| bwd.recompute:block4.ln2 | 0.041 | 0.044 | 0.0 | 3 |
| bwd.recompute:block4.moe.router | 0.127 | 0.153 | 0.0 | 3 |
| bwd.recompute:block4.moe.dispatch | 2.371 | 2.456 | 0.7 | 3 |
| bwd.recompute:block4.moe.dispatch.expert0 | 0.321 | 0.365 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert1 | 0.270 | 0.330 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert2 | 0.259 | 0.321 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert3 | 0.256 | 0.293 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert4 | 0.251 | 0.281 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert5 | 0.250 | 0.304 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert6 | 0.255 | 0.304 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert7 | 0.250 | 0.291 | 0.1 | 3 |
| bwd.recompute:block4.moe.shared | 0.136 | 0.142 | 0.0 | 3 |
| bwd:block4.grad | 7.656 | 10.189 | 2.2 | 3 |
| bwd:block3 | 14.713 | 19.861 | 4.1 | 2 |
| bwd.invert:block3 | 3.073 | 3.153 | 0.9 | 3 |
| bwd.invert:block3.ln1 | 0.060 | 0.064 | 0.0 | 3 |
| bwd.invert:block3.attn.qkv | 0.095 | 0.119 | 0.0 | 3 |
| bwd.invert:block3.attn.sdpa | 0.084 | 0.090 | 0.0 | 3 |
| bwd.invert:block3.attn.proj | 0.039 | 0.053 | 0.0 | 3 |
| bwd.invert:block3.ln2 | 0.039 | 0.044 | 0.0 | 3 |
| bwd.invert:block3.moe.router | 0.122 | 0.149 | 0.0 | 3 |
| bwd.invert:block3.moe.dispatch | 2.257 | 2.338 | 0.6 | 3 |
| bwd.invert:block3.moe.dispatch.expert0 | 0.317 | 0.370 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert1 | 0.257 | 0.302 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert2 | 0.245 | 0.291 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert3 | 0.236 | 0.282 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert4 | 0.235 | 0.278 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert5 | 0.237 | 0.270 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert6 | 0.233 | 0.282 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert7 | 0.231 | 0.273 | 0.1 | 3 |
| bwd.invert:block3.moe.shared | 0.134 | 0.141 | 0.0 | 3 |
| bwd.recompute:block3 | 3.278 | 3.353 | 0.9 | 3 |
| bwd.recompute:block3.ln1 | 0.060 | 0.066 | 0.0 | 3 |
| bwd.recompute:block3.attn.qkv | 0.095 | 0.118 | 0.0 | 3 |
| bwd.recompute:block3.attn.sdpa | 0.092 | 0.098 | 0.0 | 3 |
| bwd.recompute:block3.attn.proj | 0.045 | 0.065 | 0.0 | 3 |
| bwd.recompute:block3.ln2 | 0.041 | 0.047 | 0.0 | 3 |
| bwd.recompute:block3.moe.router | 0.126 | 0.156 | 0.0 | 3 |
| bwd.recompute:block3.moe.dispatch | 2.375 | 2.463 | 0.7 | 3 |
| bwd.recompute:block3.moe.dispatch.expert0 | 0.322 | 0.363 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert1 | 0.270 | 0.328 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert2 | 0.263 | 0.319 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert3 | 0.255 | 0.304 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert4 | 0.254 | 0.307 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert5 | 0.252 | 0.299 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert6 | 0.252 | 0.300 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert7 | 0.249 | 0.294 | 0.1 | 3 |
| bwd.recompute:block3.moe.shared | 0.136 | 0.146 | 0.0 | 3 |
| bwd:block3.grad | 7.716 | 10.625 | 2.2 | 3 |
| bwd:block2 | 15.084 | 19.852 | 4.3 | 2 |
| bwd.invert:block2 | 3.069 | 3.141 | 0.9 | 3 |
| bwd.invert:block2.ln1 | 0.060 | 0.062 | 0.0 | 3 |
| bwd.invert:block2.attn.qkv | 0.095 | 0.115 | 0.0 | 3 |
| bwd.invert:block2.attn.sdpa | 0.084 | 0.091 | 0.0 | 3 |
| bwd.invert:block2.attn.proj | 0.040 | 0.056 | 0.0 | 3 |
| bwd.invert:block2.ln2 | 0.040 | 0.045 | 0.0 | 3 |
| bwd.invert:block2.moe.router | 0.122 | 0.145 | 0.0 | 3 |
| bwd.invert:block2.moe.dispatch | 2.268 | 2.334 | 0.6 | 3 |
| bwd.invert:block2.moe.dispatch.expert0 | 0.318 | 0.384 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert1 | 0.258 | 0.303 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert2 | 0.245 | 0.285 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert3 | 0.238 | 0.279 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert4 | 0.235 | 0.286 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert5 | 0.234 | 0.288 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert6 | 0.234 | 0.278 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert7 | 0.232 | 0.282 | 0.1 | 3 |
| bwd.invert:block2.moe.shared | 0.133 | 0.139 | 0.0 | 3 |
| bwd.recompute:block2 | 3.283 | 3.357 | 0.9 | 3 |
| bwd.recompute:block2.ln1 | 0.061 | 0.064 | 0.0 | 3 |
| bwd.recompute:block2.attn.qkv | 0.095 | 0.126 | 0.0 | 3 |
| bwd.recompute:block2.attn.sdpa | 0.092 | 0.099 | 0.0 | 3 |
| bwd.recompute:block2.attn.proj | 0.045 | 0.065 | 0.0 | 3 |
| bwd.recompute:block2.ln2 | 0.041 | 0.047 | 0.0 | 3 |
| bwd.recompute:block2.moe.router | 0.127 | 0.151 | 0.0 | 3 |
| bwd.recompute:block2.moe.dispatch | 2.379 | 2.470 | 0.7 | 3 |
| bwd.recompute:block2.moe.dispatch.expert0 | 0.323 | 0.359 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert1 | 0.271 | 0.320 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert2 | 0.260 | 0.317 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert3 | 0.258 | 0.336 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert4 | 0.254 | 0.301 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert5 | 0.250 | 0.296 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert6 | 0.251 | 0.292 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert7 | 0.250 | 0.299 | 0.1 | 3 |
| bwd.recompute:block2.moe.shared | 0.136 | 0.154 | 0.0 | 3 |
| bwd:block2.grad | 7.335 | 9.872 | 2.1 | 3 |
| bwd:block1 | 13.528 | 18.093 | 3.8 | 2 |
| bwd.invert:block1 | 3.047 | 3.138 | 0.9 | 3 |
| bwd.invert:block1.ln1 | 0.060 | 0.065 | 0.0 | 3 |
| bwd.invert:block1.attn.qkv | 0.093 | 0.119 | 0.0 | 3 |
| bwd.invert:block1.attn.sdpa | 0.083 | 0.089 | 0.0 | 3 |
| bwd.invert:block1.attn.proj | 0.039 | 0.053 | 0.0 | 3 |
| bwd.invert:block1.ln2 | 0.040 | 0.045 | 0.0 | 3 |
| bwd.invert:block1.moe.router | 0.121 | 0.136 | 0.0 | 3 |
| bwd.invert:block1.moe.dispatch | 2.201 | 2.337 | 0.6 | 3 |
| bwd.invert:block1.moe.dispatch.expert0 | 0.317 | 0.331 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert1 | 0.262 | 0.296 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert2 | 0.242 | 0.296 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert3 | 0.237 | 0.293 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert4 | 0.239 | 0.279 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert5 | 0.233 | 0.262 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert6 | 0.232 | 0.259 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert7 | 0.234 | 0.256 | 0.1 | 3 |
| bwd.invert:block1.moe.shared | 0.133 | 0.147 | 0.0 | 3 |
| bwd.recompute:block1 | 3.269 | 3.339 | 0.9 | 3 |
| bwd.recompute:block1.ln1 | 0.061 | 0.066 | 0.0 | 3 |
| bwd.recompute:block1.attn.qkv | 0.096 | 0.124 | 0.0 | 3 |
| bwd.recompute:block1.attn.sdpa | 0.092 | 0.099 | 0.0 | 3 |
| bwd.recompute:block1.attn.proj | 0.046 | 0.069 | 0.0 | 3 |
| bwd.recompute:block1.ln2 | 0.041 | 0.047 | 0.0 | 3 |
| bwd.recompute:block1.moe.router | 0.127 | 0.159 | 0.0 | 3 |
| bwd.recompute:block1.moe.dispatch | 2.376 | 2.464 | 0.7 | 3 |
| bwd.recompute:block1.moe.dispatch.expert0 | 0.322 | 0.369 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert1 | 0.273 | 0.336 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert2 | 0.260 | 0.301 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert3 | 0.254 | 0.283 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert4 | 0.253 | 0.286 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert5 | 0.250 | 0.294 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert6 | 0.252 | 0.311 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert7 | 0.250 | 0.295 | 0.1 | 3 |
| bwd.recompute:block1.moe.shared | 0.136 | 0.142 | 0.0 | 3 |
| bwd:block1.grad | 7.360 | 10.868 | 2.1 | 3 |
| bwd:block0 | 14.364 | 19.225 | 4.0 | 2 |
| bwd.invert:block0 | 3.075 | 3.169 | 0.9 | 3 |
| bwd.invert:block0.ln1 | 0.061 | 0.065 | 0.0 | 3 |
| bwd.invert:block0.attn.qkv | 0.094 | 0.120 | 0.0 | 3 |
| bwd.invert:block0.attn.sdpa | 0.083 | 0.090 | 0.0 | 3 |
| bwd.invert:block0.attn.proj | 0.040 | 0.055 | 0.0 | 3 |
| bwd.invert:block0.ln2 | 0.040 | 0.045 | 0.0 | 3 |
| bwd.invert:block0.moe.router | 0.122 | 0.145 | 0.0 | 3 |
| bwd.invert:block0.moe.dispatch | 2.238 | 2.363 | 0.6 | 3 |
| bwd.invert:block0.moe.dispatch.expert0 | 0.319 | 0.349 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert1 | 0.258 | 0.306 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert2 | 0.244 | 0.297 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert3 | 0.237 | 0.269 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert4 | 0.238 | 0.268 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert5 | 0.236 | 0.270 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert6 | 0.234 | 0.283 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert7 | 0.232 | 0.282 | 0.1 | 3 |
| bwd.invert:block0.moe.shared | 0.133 | 0.141 | 0.0 | 3 |
| bwd.recompute:block0 | 3.275 | 3.350 | 0.9 | 3 |
| bwd.recompute:block0.ln1 | 0.061 | 0.067 | 0.0 | 3 |
| bwd.recompute:block0.attn.qkv | 0.096 | 0.128 | 0.0 | 3 |
| bwd.recompute:block0.attn.sdpa | 0.093 | 0.100 | 0.0 | 3 |
| bwd.recompute:block0.attn.proj | 0.045 | 0.064 | 0.0 | 3 |
| bwd.recompute:block0.ln2 | 0.042 | 0.047 | 0.0 | 3 |
| bwd.recompute:block0.moe.router | 0.127 | 0.148 | 0.0 | 3 |
| bwd.recompute:block0.moe.dispatch | 2.385 | 2.467 | 0.7 | 3 |
| bwd.recompute:block0.moe.dispatch.expert0 | 0.321 | 0.380 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert1 | 0.271 | 0.325 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert2 | 0.261 | 0.311 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert3 | 0.256 | 0.309 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert4 | 0.254 | 0.306 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert5 | 0.252 | 0.299 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert6 | 0.251 | 0.286 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert7 | 0.249 | 0.269 | 0.1 | 3 |
| bwd.recompute:block0.moe.shared | 0.136 | 0.144 | 0.0 | 3 |
| bwd:block0.grad | 6.979 | 9.889 | 2.0 | 3 |
| bwd:embed | 0.238 | 0.349 | 0.1 | 2 |
| opt | 12.333 | 15.535 | 3.5 | 1 |
| opt:opt.clip | 2.859 | 3.781 | 0.8 | 2 |
| opt:opt.muon | 7.394 | 9.008 | 2.1 | 2 |
| opt:opt.muon.ns | 3.581 | 3.657 | 1.0 | 3 |
| opt:opt.adamw | 1.033 | 1.222 | 0.3 | 2 |
| opt:opt.moe_bias | 0.458 | 0.530 | 0.1 | 3 |
| opt:opt.zero_grad | 0.551 | 0.621 | 0.2 | 3 |

## Time by part type (sum over layers)

| part type | median ms sum | % of step |
| :--- | ---: | ---: |
| bwd | 147.962 | 41.7 |
| bwd:stack | 131.419 | 37.0 |
| bwd:block* | 129.080 | 36.4 |
| bwd:block*.grad | 67.508 | 19.0 |
| fwd | 64.196 | 18.1 |
| fwd:stack | 45.914 | 12.9 |
| fwd:block* | 44.780 | 12.6 |
| fwd:block*.moe.dispatch | 34.655 | 9.8 |
| bwd.recompute:block* | 29.386 | 8.3 |
| bwd.invert:block* | 27.260 | 7.7 |
| bwd.recompute:block*.moe.dispatch | 21.422 | 6.0 |
| bwd.invert:block*.moe.dispatch | 20.137 | 5.7 |
| bwd:head+loss | 16.317 | 4.6 |
| fwd:head+loss | 16.160 | 4.6 |
| opt | 12.333 | 3.5 |
| opt:opt.muon | 7.394 | 2.1 |
| fwd:block*.moe.dispatch.expert0 | 4.414 | 1.2 |
| fwd:block*.moe.dispatch.expert5 | 4.184 | 1.2 |
| fwd:block*.moe.dispatch.expert1 | 4.175 | 1.2 |
| fwd:block*.moe.dispatch.expert2 | 4.101 | 1.2 |
| fwd:block*.moe.dispatch.expert7 | 4.075 | 1.1 |
| fwd:block*.moe.dispatch.expert6 | 4.022 | 1.1 |
| fwd:block*.moe.dispatch.expert4 | 3.905 | 1.1 |
| fwd:block*.moe.dispatch.expert3 | 3.860 | 1.1 |
| opt:opt.muon.ns | 3.581 | 1.0 |
| bwd.recompute:block*.moe.dispatch.expert0 | 2.897 | 0.8 |
| bwd.invert:block*.moe.dispatch.expert0 | 2.875 | 0.8 |
| opt:opt.clip | 2.859 | 0.8 |
| bwd.recompute:block*.moe.dispatch.expert1 | 2.434 | 0.7 |
| bwd.recompute:block*.moe.dispatch.expert2 | 2.337 | 0.7 |
| bwd.invert:block*.moe.dispatch.expert1 | 2.330 | 0.7 |
| bwd.recompute:block*.moe.dispatch.expert3 | 2.295 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert4 | 2.276 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert6 | 2.268 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert5 | 2.260 | 0.6 |
| bwd.recompute:block*.moe.dispatch.expert7 | 2.252 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert2 | 2.180 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert3 | 2.130 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert4 | 2.125 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert5 | 2.113 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert6 | 2.099 | 0.6 |
| bwd.invert:block*.moe.dispatch.expert7 | 2.093 | 0.6 |
| fwd:embed | 1.968 | 0.6 |
| fwd:embed.ke | 1.927 | 0.5 |
| fwd:block*.moe.router | 1.387 | 0.4 |
| bwd.recompute:block*.moe.shared | 1.224 | 0.3 |
| fwd:block*.moe.shared | 1.221 | 0.3 |
| bwd.invert:block*.moe.shared | 1.198 | 0.3 |
| bwd.recompute:block*.moe.router | 1.146 | 0.3 |
| opt:opt.adamw | 1.033 | 0.3 |
| bwd.invert:block*.moe.router | 1.011 | 0.3 |
| bwd.recompute:block*.attn.qkv | 0.856 | 0.2 |
| bwd.recompute:block*.attn.sdpa | 0.843 | 0.2 |
| bwd.invert:block*.attn.qkv | 0.784 | 0.2 |
| fwd:block*.attn.sdpa | 0.748 | 0.2 |
| bwd.invert:block*.attn.sdpa | 0.714 | 0.2 |
| data | 0.652 | 0.2 |
| fwd:block*.attn.qkv | 0.635 | 0.2 |
| opt:opt.zero_grad | 0.551 | 0.2 |
| bwd.recompute:block*.ln1 | 0.547 | 0.2 |
| bwd.invert:block*.ln1 | 0.517 | 0.1 |
| fwd:block*.ln1 | 0.468 | 0.1 |
| opt:opt.moe_bias | 0.458 | 0.1 |
| bwd.recompute:block*.attn.proj | 0.413 | 0.1 |
| bwd.recompute:block*.ln2 | 0.373 | 0.1 |
| bwd.invert:block*.ln2 | 0.351 | 0.1 |
| fwd:block*.ln2 | 0.340 | 0.1 |
| bwd.invert:block*.attn.proj | 0.337 | 0.1 |
| fwd:block*.attn.proj | 0.317 | 0.1 |
| bwd:embed | 0.238 | 0.1 |

## Five slowest leaf parts

1. `bwd:block5.grad` — 7.893 ms (2.2% of step)
2. `bwd:block3.grad` — 7.716 ms (2.2% of step)
3. `bwd:block6.grad` — 7.663 ms (2.2% of step)
4. `bwd:block4.grad` — 7.656 ms (2.2% of step)
5. `bwd:block7.grad` — 7.531 ms (2.1% of step)
