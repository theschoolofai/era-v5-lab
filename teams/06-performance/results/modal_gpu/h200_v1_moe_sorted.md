# Bench report — h200_v1_moe_sorted

**GPU:** NVIDIA H200  |  **dtype:** bf16  |  **B x T:** 32 x 512  |  **torch:** 2.11.0+cu128
**commit:** `19221759f9d820ce0563d5d2f44e22eac0de53d2`  |  **tag:** h200_v1_moe_sorted

## Step (clean)

- median: 206.777 ms
- p10..p90: 201.010 .. 211.516 ms
- tokens/s: 79,235
- MFU: 2.6%  |  HFU: 3.3%

## Diagnostics

### CUDA timing-event allocations

- [OK] clean: events_created_during_steps=0
- [OK] layer: events_created_during_steps=0
- [OK] layer.inner_pass: events_created_during_steps=0

### Benchmark warnings

- [warn] rule 3b: checkpoint and comm not measured; add checkpoint,comm to --modes
- [warn] 26 gated part(s) have p10..p90 spread > 10%, so may miss the 5% check: data, fwd:stack, fwd:block0, fwd:block1, fwd:block2, fwd:block3 (+20 more)

## Regions

| part | median ms | p90 | % of step | level |
| :--- | ---: | ---: | ---: | ---: |
| data | 0.722 | 0.913 | 0.3 | 1 |
| fwd | 35.171 | 37.171 | 17.0 | 1 |
| fwd:embed | 2.016 | 2.149 | 1.0 | 2 |
| fwd:embed.ke | 1.989 | 2.060 | 1.0 | 3 |
| fwd:stack | 16.891 | 18.773 | 8.2 | 1 |
| fwd:block0 | 1.450 | 2.001 | 0.7 | 2 |
| fwd:block0.ln1 | 0.033 | 0.033 | 0.0 | 3 |
| fwd:block0.attn.qkv | 0.026 | 0.028 | 0.0 | 3 |
| fwd:block0.attn.sdpa | 0.043 | 0.043 | 0.0 | 3 |
| fwd:block0.attn.proj | 0.018 | 0.019 | 0.0 | 3 |
| fwd:block0.ln2 | 0.033 | 0.033 | 0.0 | 3 |
| fwd:block0.moe.router | 0.089 | 0.090 | 0.0 | 3 |
| fwd:block0.moe.dispatch | 1.038 | 1.209 | 0.5 | 3 |
| fwd:block0.moe.dispatch.grouped | 0.500 | 0.660 | 0.2 | 3 |
| fwd:block0.moe.shared | 0.151 | 0.183 | 0.1 | 3 |
| fwd:block1 | 1.837 | 2.343 | 0.9 | 2 |
| fwd:block1.ln1 | 0.059 | 0.061 | 0.0 | 3 |
| fwd:block1.attn.qkv | 0.102 | 0.111 | 0.0 | 3 |
| fwd:block1.attn.sdpa | 0.094 | 0.097 | 0.0 | 3 |
| fwd:block1.attn.proj | 0.058 | 0.067 | 0.0 | 3 |
| fwd:block1.ln2 | 0.045 | 0.048 | 0.0 | 3 |
| fwd:block1.moe.router | 0.203 | 0.213 | 0.1 | 3 |
| fwd:block1.moe.dispatch | 1.136 | 1.483 | 0.5 | 3 |
| fwd:block1.moe.dispatch.grouped | 0.468 | 0.814 | 0.2 | 3 |
| fwd:block1.moe.shared | 0.122 | 0.172 | 0.1 | 3 |
| fwd:block2 | 1.862 | 2.275 | 0.9 | 2 |
| fwd:block2.ln1 | 0.059 | 0.061 | 0.0 | 3 |
| fwd:block2.attn.qkv | 0.102 | 0.110 | 0.0 | 3 |
| fwd:block2.attn.sdpa | 0.094 | 0.097 | 0.0 | 3 |
| fwd:block2.attn.proj | 0.058 | 0.066 | 0.0 | 3 |
| fwd:block2.ln2 | 0.045 | 0.048 | 0.0 | 3 |
| fwd:block2.moe.router | 0.202 | 0.213 | 0.1 | 3 |
| fwd:block2.moe.dispatch | 1.191 | 1.545 | 0.6 | 3 |
| fwd:block2.moe.dispatch.grouped | 0.519 | 0.882 | 0.3 | 3 |
| fwd:block2.moe.shared | 0.106 | 0.170 | 0.1 | 3 |
| fwd:block3 | 1.799 | 2.270 | 0.9 | 2 |
| fwd:block3.ln1 | 0.058 | 0.060 | 0.0 | 3 |
| fwd:block3.attn.qkv | 0.103 | 0.109 | 0.0 | 3 |
| fwd:block3.attn.sdpa | 0.093 | 0.095 | 0.0 | 3 |
| fwd:block3.attn.proj | 0.058 | 0.065 | 0.0 | 3 |
| fwd:block3.ln2 | 0.045 | 0.047 | 0.0 | 3 |
| fwd:block3.moe.router | 0.203 | 0.221 | 0.1 | 3 |
| fwd:block3.moe.dispatch | 1.157 | 1.512 | 0.6 | 3 |
| fwd:block3.moe.dispatch.grouped | 0.496 | 0.842 | 0.2 | 3 |
| fwd:block3.moe.shared | 0.124 | 0.166 | 0.1 | 3 |
| fwd:block4 | 1.834 | 2.277 | 0.9 | 2 |
| fwd:block4.ln1 | 0.058 | 0.061 | 0.0 | 3 |
| fwd:block4.attn.qkv | 0.101 | 0.110 | 0.0 | 3 |
| fwd:block4.attn.sdpa | 0.093 | 0.096 | 0.0 | 3 |
| fwd:block4.attn.proj | 0.058 | 0.065 | 0.0 | 3 |
| fwd:block4.ln2 | 0.045 | 0.047 | 0.0 | 3 |
| fwd:block4.moe.router | 0.203 | 0.226 | 0.1 | 3 |
| fwd:block4.moe.dispatch | 1.134 | 1.482 | 0.5 | 3 |
| fwd:block4.moe.dispatch.grouped | 0.466 | 0.804 | 0.2 | 3 |
| fwd:block4.moe.shared | 0.110 | 0.167 | 0.1 | 3 |
| fwd:block5 | 1.818 | 2.593 | 0.9 | 2 |
| fwd:block5.ln1 | 0.058 | 0.061 | 0.0 | 3 |
| fwd:block5.attn.qkv | 0.101 | 0.112 | 0.0 | 3 |
| fwd:block5.attn.sdpa | 0.093 | 0.096 | 0.0 | 3 |
| fwd:block5.attn.proj | 0.058 | 0.067 | 0.0 | 3 |
| fwd:block5.ln2 | 0.045 | 0.048 | 0.0 | 3 |
| fwd:block5.moe.router | 0.203 | 0.224 | 0.1 | 3 |
| fwd:block5.moe.dispatch | 1.154 | 1.246 | 0.6 | 3 |
| fwd:block5.moe.dispatch.grouped | 0.493 | 0.579 | 0.2 | 3 |
| fwd:block5.moe.shared | 0.114 | 0.169 | 0.1 | 3 |
| fwd:block6 | 1.841 | 2.449 | 0.9 | 2 |
| fwd:block6.ln1 | 0.058 | 0.060 | 0.0 | 3 |
| fwd:block6.attn.qkv | 0.102 | 0.110 | 0.0 | 3 |
| fwd:block6.attn.sdpa | 0.094 | 0.097 | 0.0 | 3 |
| fwd:block6.attn.proj | 0.059 | 0.070 | 0.0 | 3 |
| fwd:block6.ln2 | 0.045 | 0.048 | 0.0 | 3 |
| fwd:block6.moe.router | 0.203 | 0.219 | 0.1 | 3 |
| fwd:block6.moe.dispatch | 1.181 | 1.288 | 0.6 | 3 |
| fwd:block6.moe.dispatch.grouped | 0.504 | 0.602 | 0.2 | 3 |
| fwd:block6.moe.shared | 0.104 | 0.161 | 0.1 | 3 |
| fwd:block7 | 1.805 | 2.260 | 0.9 | 2 |
| fwd:block7.ln1 | 0.058 | 0.060 | 0.0 | 3 |
| fwd:block7.attn.qkv | 0.102 | 0.112 | 0.0 | 3 |
| fwd:block7.attn.sdpa | 0.094 | 0.096 | 0.0 | 3 |
| fwd:block7.attn.proj | 0.058 | 0.070 | 0.0 | 3 |
| fwd:block7.ln2 | 0.045 | 0.048 | 0.0 | 3 |
| fwd:block7.moe.router | 0.202 | 0.223 | 0.1 | 3 |
| fwd:block7.moe.dispatch | 1.166 | 1.295 | 0.6 | 3 |
| fwd:block7.moe.dispatch.grouped | 0.474 | 0.596 | 0.2 | 3 |
| fwd:block7.moe.shared | 0.105 | 0.172 | 0.1 | 3 |
| fwd:block8 | 1.825 | 2.272 | 0.9 | 2 |
| fwd:block8.ln1 | 0.057 | 0.060 | 0.0 | 3 |
| fwd:block8.attn.qkv | 0.100 | 0.109 | 0.0 | 3 |
| fwd:block8.attn.sdpa | 0.093 | 0.097 | 0.0 | 3 |
| fwd:block8.attn.proj | 0.057 | 0.063 | 0.0 | 3 |
| fwd:block8.ln2 | 0.044 | 0.046 | 0.0 | 3 |
| fwd:block8.moe.router | 0.201 | 0.218 | 0.1 | 3 |
| fwd:block8.moe.dispatch | 1.165 | 1.488 | 0.6 | 3 |
| fwd:block8.moe.dispatch.grouped | 0.499 | 0.803 | 0.2 | 3 |
| fwd:block8.moe.shared | 0.108 | 0.164 | 0.1 | 3 |
| fwd:head+loss | 16.138 | 16.212 | 7.8 | 2 |
| bwd | 74.577 | 79.331 | 36.1 | 1 |
| bwd:head+loss | 16.319 | 16.332 | 7.9 | 2 |
| bwd:stack | 58.011 | 62.697 | 28.1 | 1 |
| bwd:block8 | 6.306 | 8.284 | 3.0 | 2 |
| bwd.invert:block8 | 1.380 | 1.604 | 0.7 | 3 |
| bwd.invert:block8.ln1 | 0.035 | 0.035 | 0.0 | 3 |
| bwd.invert:block8.attn.qkv | 0.028 | 0.029 | 0.0 | 3 |
| bwd.invert:block8.attn.sdpa | 0.043 | 0.043 | 0.0 | 3 |
| bwd.invert:block8.attn.proj | 0.018 | 0.019 | 0.0 | 3 |
| bwd.invert:block8.ln2 | 0.033 | 0.033 | 0.0 | 3 |
| bwd.invert:block8.moe.router | 0.037 | 0.039 | 0.0 | 3 |
| bwd.invert:block8.moe.dispatch | 0.998 | 1.212 | 0.5 | 3 |
| bwd.invert:block8.moe.dispatch.grouped | 0.443 | 0.567 | 0.2 | 3 |
| bwd.invert:block8.moe.shared | 0.103 | 0.105 | 0.0 | 3 |
| bwd.recompute:block8 | 1.947 | 2.148 | 0.9 | 3 |
| bwd.recompute:block8.ln1 | 0.035 | 0.071 | 0.0 | 3 |
| bwd.recompute:block8.attn.qkv | 0.105 | 0.140 | 0.1 | 3 |
| bwd.recompute:block8.attn.sdpa | 0.104 | 0.124 | 0.1 | 3 |
| bwd.recompute:block8.attn.proj | 0.080 | 0.095 | 0.0 | 3 |
| bwd.recompute:block8.ln2 | 0.051 | 0.055 | 0.0 | 3 |
| bwd.recompute:block8.moe.router | 0.168 | 0.187 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch | 1.161 | 1.295 | 0.6 | 3 |
| bwd.recompute:block8.moe.dispatch.grouped | 0.445 | 0.570 | 0.2 | 3 |
| bwd.recompute:block8.moe.shared | 0.103 | 0.106 | 0.0 | 3 |
| bwd:block8.grad | 2.658 | 4.007 | 1.3 | 3 |
| bwd:block7 | 6.733 | 7.693 | 3.3 | 2 |
| bwd.invert:block7 | 1.959 | 2.135 | 0.9 | 3 |
| bwd.invert:block7.ln1 | 0.065 | 0.067 | 0.0 | 3 |
| bwd.invert:block7.attn.qkv | 0.124 | 0.134 | 0.1 | 3 |
| bwd.invert:block7.attn.sdpa | 0.092 | 0.101 | 0.0 | 3 |
| bwd.invert:block7.attn.proj | 0.063 | 0.076 | 0.0 | 3 |
| bwd.invert:block7.ln2 | 0.047 | 0.051 | 0.0 | 3 |
| bwd.invert:block7.moe.router | 0.158 | 0.178 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch | 1.105 | 1.292 | 0.5 | 3 |
| bwd.invert:block7.moe.dispatch.grouped | 0.405 | 0.591 | 0.2 | 3 |
| bwd.invert:block7.moe.shared | 0.104 | 0.106 | 0.1 | 3 |
| bwd.recompute:block7 | 1.905 | 1.984 | 0.9 | 3 |
| bwd.recompute:block7.ln1 | 0.035 | 0.066 | 0.0 | 3 |
| bwd.recompute:block7.attn.qkv | 0.101 | 0.126 | 0.0 | 3 |
| bwd.recompute:block7.attn.sdpa | 0.099 | 0.103 | 0.0 | 3 |
| bwd.recompute:block7.attn.proj | 0.069 | 0.076 | 0.0 | 3 |
| bwd.recompute:block7.ln2 | 0.049 | 0.053 | 0.0 | 3 |
| bwd.recompute:block7.moe.router | 0.166 | 0.179 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch | 1.132 | 1.312 | 0.5 | 3 |
| bwd.recompute:block7.moe.dispatch.grouped | 0.410 | 0.593 | 0.2 | 3 |
| bwd.recompute:block7.moe.shared | 0.104 | 0.106 | 0.1 | 3 |
| bwd:block7.grad | 2.541 | 3.666 | 1.2 | 3 |
| bwd:block6 | 6.824 | 7.746 | 3.3 | 2 |
| bwd.invert:block6 | 1.970 | 2.101 | 1.0 | 3 |
| bwd.invert:block6.ln1 | 0.065 | 0.068 | 0.0 | 3 |
| bwd.invert:block6.attn.qkv | 0.124 | 0.137 | 0.1 | 3 |
| bwd.invert:block6.attn.sdpa | 0.091 | 0.094 | 0.0 | 3 |
| bwd.invert:block6.attn.proj | 0.062 | 0.070 | 0.0 | 3 |
| bwd.invert:block6.ln2 | 0.047 | 0.049 | 0.0 | 3 |
| bwd.invert:block6.moe.router | 0.157 | 0.165 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch | 1.145 | 1.264 | 0.6 | 3 |
| bwd.invert:block6.moe.dispatch.grouped | 0.461 | 0.583 | 0.2 | 3 |
| bwd.invert:block6.moe.shared | 0.104 | 0.106 | 0.1 | 3 |
| bwd.recompute:block6 | 1.891 | 1.965 | 0.9 | 3 |
| bwd.recompute:block6.ln1 | 0.035 | 0.065 | 0.0 | 3 |
| bwd.recompute:block6.attn.qkv | 0.047 | 0.119 | 0.0 | 3 |
| bwd.recompute:block6.attn.sdpa | 0.098 | 0.103 | 0.0 | 3 |
| bwd.recompute:block6.attn.proj | 0.068 | 0.083 | 0.0 | 3 |
| bwd.recompute:block6.ln2 | 0.049 | 0.053 | 0.0 | 3 |
| bwd.recompute:block6.moe.router | 0.163 | 0.172 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch | 1.183 | 1.302 | 0.6 | 3 |
| bwd.recompute:block6.moe.dispatch.grouped | 0.472 | 0.586 | 0.2 | 3 |
| bwd.recompute:block6.moe.shared | 0.104 | 0.106 | 0.1 | 3 |
| bwd:block6.grad | 2.562 | 3.647 | 1.2 | 3 |
| bwd:block5 | 6.785 | 7.695 | 3.3 | 2 |
| bwd.invert:block5 | 1.943 | 2.039 | 0.9 | 3 |
| bwd.invert:block5.ln1 | 0.065 | 0.067 | 0.0 | 3 |
| bwd.invert:block5.attn.qkv | 0.124 | 0.135 | 0.1 | 3 |
| bwd.invert:block5.attn.sdpa | 0.090 | 0.094 | 0.0 | 3 |
| bwd.invert:block5.attn.proj | 0.062 | 0.072 | 0.0 | 3 |
| bwd.invert:block5.ln2 | 0.047 | 0.049 | 0.0 | 3 |
| bwd.invert:block5.moe.router | 0.157 | 0.179 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch | 1.120 | 1.199 | 0.5 | 3 |
| bwd.invert:block5.moe.dispatch.grouped | 0.435 | 0.483 | 0.2 | 3 |
| bwd.invert:block5.moe.shared | 0.105 | 0.106 | 0.1 | 3 |
| bwd.recompute:block5 | 1.867 | 1.953 | 0.9 | 3 |
| bwd.recompute:block5.ln1 | 0.035 | 0.061 | 0.0 | 3 |
| bwd.recompute:block5.attn.qkv | 0.074 | 0.122 | 0.0 | 3 |
| bwd.recompute:block5.attn.sdpa | 0.098 | 0.101 | 0.0 | 3 |
| bwd.recompute:block5.attn.proj | 0.068 | 0.083 | 0.0 | 3 |
| bwd.recompute:block5.ln2 | 0.049 | 0.052 | 0.0 | 3 |
| bwd.recompute:block5.moe.router | 0.163 | 0.182 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch | 1.136 | 1.228 | 0.5 | 3 |
| bwd.recompute:block5.moe.dispatch.grouped | 0.437 | 0.505 | 0.2 | 3 |
| bwd.recompute:block5.moe.shared | 0.104 | 0.106 | 0.1 | 3 |
| bwd:block5.grad | 2.486 | 3.613 | 1.2 | 3 |
| bwd:block4 | 6.787 | 7.260 | 3.3 | 2 |
| bwd.invert:block4 | 1.918 | 2.110 | 0.9 | 3 |
| bwd.invert:block4.ln1 | 0.065 | 0.068 | 0.0 | 3 |
| bwd.invert:block4.attn.qkv | 0.123 | 0.135 | 0.1 | 3 |
| bwd.invert:block4.attn.sdpa | 0.090 | 0.094 | 0.0 | 3 |
| bwd.invert:block4.attn.proj | 0.062 | 0.070 | 0.0 | 3 |
| bwd.invert:block4.ln2 | 0.046 | 0.048 | 0.0 | 3 |
| bwd.invert:block4.moe.router | 0.157 | 0.163 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch | 1.082 | 1.289 | 0.5 | 3 |
| bwd.invert:block4.moe.dispatch.grouped | 0.401 | 0.615 | 0.2 | 3 |
| bwd.invert:block4.moe.shared | 0.104 | 0.106 | 0.1 | 3 |
| bwd.recompute:block4 | 1.861 | 1.943 | 0.9 | 3 |
| bwd.recompute:block4.ln1 | 0.035 | 0.065 | 0.0 | 3 |
| bwd.recompute:block4.attn.qkv | 0.101 | 0.119 | 0.0 | 3 |
| bwd.recompute:block4.attn.sdpa | 0.097 | 0.100 | 0.0 | 3 |
| bwd.recompute:block4.attn.proj | 0.067 | 0.079 | 0.0 | 3 |
| bwd.recompute:block4.ln2 | 0.049 | 0.052 | 0.0 | 3 |
| bwd.recompute:block4.moe.router | 0.161 | 0.169 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch | 1.108 | 1.316 | 0.5 | 3 |
| bwd.recompute:block4.moe.dispatch.grouped | 0.405 | 0.618 | 0.2 | 3 |
| bwd.recompute:block4.moe.shared | 0.104 | 0.106 | 0.1 | 3 |
| bwd:block4.grad | 2.508 | 3.738 | 1.2 | 3 |
| bwd:block3 | 6.721 | 7.276 | 3.3 | 2 |
| bwd.invert:block3 | 1.924 | 2.043 | 0.9 | 3 |
| bwd.invert:block3.ln1 | 0.065 | 0.067 | 0.0 | 3 |
| bwd.invert:block3.attn.qkv | 0.123 | 0.131 | 0.1 | 3 |
| bwd.invert:block3.attn.sdpa | 0.089 | 0.092 | 0.0 | 3 |
| bwd.invert:block3.attn.proj | 0.062 | 0.067 | 0.0 | 3 |
| bwd.invert:block3.ln2 | 0.046 | 0.049 | 0.0 | 3 |
| bwd.invert:block3.moe.router | 0.157 | 0.164 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch | 1.097 | 1.218 | 0.5 | 3 |
| bwd.invert:block3.moe.dispatch.grouped | 0.395 | 0.530 | 0.2 | 3 |
| bwd.invert:block3.moe.shared | 0.104 | 0.106 | 0.1 | 3 |
| bwd.recompute:block3 | 1.870 | 1.936 | 0.9 | 3 |
| bwd.recompute:block3.ln1 | 0.035 | 0.066 | 0.0 | 3 |
| bwd.recompute:block3.attn.qkv | 0.093 | 0.118 | 0.0 | 3 |
| bwd.recompute:block3.attn.sdpa | 0.097 | 0.100 | 0.0 | 3 |
| bwd.recompute:block3.attn.proj | 0.067 | 0.078 | 0.0 | 3 |
| bwd.recompute:block3.ln2 | 0.049 | 0.051 | 0.0 | 3 |
| bwd.recompute:block3.moe.router | 0.161 | 0.180 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch | 1.118 | 1.240 | 0.5 | 3 |
| bwd.recompute:block3.moe.dispatch.grouped | 0.396 | 0.536 | 0.2 | 3 |
| bwd.recompute:block3.moe.shared | 0.104 | 0.106 | 0.1 | 3 |
| bwd:block3.grad | 2.569 | 3.836 | 1.2 | 3 |
| bwd:block2 | 6.792 | 7.402 | 3.3 | 2 |
| bwd.invert:block2 | 1.985 | 2.067 | 1.0 | 3 |
| bwd.invert:block2.ln1 | 0.065 | 0.067 | 0.0 | 3 |
| bwd.invert:block2.attn.qkv | 0.122 | 0.129 | 0.1 | 3 |
| bwd.invert:block2.attn.sdpa | 0.089 | 0.093 | 0.0 | 3 |
| bwd.invert:block2.attn.proj | 0.061 | 0.068 | 0.0 | 3 |
| bwd.invert:block2.ln2 | 0.046 | 0.049 | 0.0 | 3 |
| bwd.invert:block2.moe.router | 0.157 | 0.165 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch | 1.163 | 1.239 | 0.6 | 3 |
| bwd.invert:block2.moe.dispatch.grouped | 0.488 | 0.535 | 0.2 | 3 |
| bwd.invert:block2.moe.shared | 0.103 | 0.105 | 0.0 | 3 |
| bwd.recompute:block2 | 1.854 | 1.926 | 0.9 | 3 |
| bwd.recompute:block2.ln1 | 0.035 | 0.035 | 0.0 | 3 |
| bwd.recompute:block2.attn.qkv | 0.028 | 0.103 | 0.0 | 3 |
| bwd.recompute:block2.attn.sdpa | 0.095 | 0.099 | 0.0 | 3 |
| bwd.recompute:block2.attn.proj | 0.066 | 0.074 | 0.0 | 3 |
| bwd.recompute:block2.ln2 | 0.049 | 0.052 | 0.0 | 3 |
| bwd.recompute:block2.moe.router | 0.161 | 0.172 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch | 1.185 | 1.265 | 0.6 | 3 |
| bwd.recompute:block2.moe.dispatch.grouped | 0.494 | 0.537 | 0.2 | 3 |
| bwd.recompute:block2.moe.shared | 0.103 | 0.106 | 0.1 | 3 |
| bwd:block2.grad | 2.466 | 3.922 | 1.2 | 3 |
| bwd:block1 | 6.701 | 7.438 | 3.2 | 2 |
| bwd.invert:block1 | 1.893 | 2.076 | 0.9 | 3 |
| bwd.invert:block1.ln1 | 0.065 | 0.067 | 0.0 | 3 |
| bwd.invert:block1.attn.qkv | 0.122 | 0.140 | 0.1 | 3 |
| bwd.invert:block1.attn.sdpa | 0.090 | 0.093 | 0.0 | 3 |
| bwd.invert:block1.attn.proj | 0.062 | 0.078 | 0.0 | 3 |
| bwd.invert:block1.ln2 | 0.046 | 0.050 | 0.0 | 3 |
| bwd.invert:block1.moe.router | 0.157 | 0.166 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch | 1.077 | 1.219 | 0.5 | 3 |
| bwd.invert:block1.moe.dispatch.grouped | 0.397 | 0.537 | 0.2 | 3 |
| bwd.invert:block1.moe.shared | 0.103 | 0.106 | 0.0 | 3 |
| bwd.recompute:block1 | 1.849 | 1.927 | 0.9 | 3 |
| bwd.recompute:block1.ln1 | 0.035 | 0.065 | 0.0 | 3 |
| bwd.recompute:block1.attn.qkv | 0.109 | 0.120 | 0.1 | 3 |
| bwd.recompute:block1.attn.sdpa | 0.097 | 0.099 | 0.0 | 3 |
| bwd.recompute:block1.attn.proj | 0.066 | 0.079 | 0.0 | 3 |
| bwd.recompute:block1.ln2 | 0.048 | 0.051 | 0.0 | 3 |
| bwd.recompute:block1.moe.router | 0.162 | 0.174 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch | 1.092 | 1.223 | 0.5 | 3 |
| bwd.recompute:block1.moe.dispatch.grouped | 0.401 | 0.539 | 0.2 | 3 |
| bwd.recompute:block1.moe.shared | 0.103 | 0.105 | 0.1 | 3 |
| bwd:block1.grad | 2.470 | 3.725 | 1.2 | 3 |
| bwd:block0 | 6.732 | 7.345 | 3.3 | 2 |
| bwd.invert:block0 | 1.875 | 2.083 | 0.9 | 3 |
| bwd.invert:block0.ln1 | 0.065 | 0.068 | 0.0 | 3 |
| bwd.invert:block0.attn.qkv | 0.122 | 0.132 | 0.1 | 3 |
| bwd.invert:block0.attn.sdpa | 0.089 | 0.094 | 0.0 | 3 |
| bwd.invert:block0.attn.proj | 0.062 | 0.072 | 0.0 | 3 |
| bwd.invert:block0.ln2 | 0.046 | 0.049 | 0.0 | 3 |
| bwd.invert:block0.moe.router | 0.157 | 0.164 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch | 1.052 | 1.256 | 0.5 | 3 |
| bwd.invert:block0.moe.dispatch.grouped | 0.371 | 0.579 | 0.2 | 3 |
| bwd.invert:block0.moe.shared | 0.103 | 0.106 | 0.0 | 3 |
| bwd.recompute:block0 | 1.855 | 1.934 | 0.9 | 3 |
| bwd.recompute:block0.ln1 | 0.048 | 0.067 | 0.0 | 3 |
| bwd.recompute:block0.attn.qkv | 0.112 | 0.122 | 0.1 | 3 |
| bwd.recompute:block0.attn.sdpa | 0.096 | 0.099 | 0.0 | 3 |
| bwd.recompute:block0.attn.proj | 0.066 | 0.072 | 0.0 | 3 |
| bwd.recompute:block0.ln2 | 0.049 | 0.051 | 0.0 | 3 |
| bwd.recompute:block0.moe.router | 0.161 | 0.173 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch | 1.074 | 1.275 | 0.5 | 3 |
| bwd.recompute:block0.moe.dispatch.grouped | 0.375 | 0.581 | 0.2 | 3 |
| bwd.recompute:block0.moe.shared | 0.103 | 0.105 | 0.0 | 3 |
| bwd:block0.grad | 2.538 | 3.673 | 1.2 | 3 |
| bwd:embed | 0.253 | 0.380 | 0.1 | 2 |
| opt | 95.509 | 103.521 | 46.2 | 1 |
| opt:opt.clip | 2.899 | 3.664 | 1.4 | 2 |
| opt:opt.muon | 90.337 | 96.340 | 43.7 | 2 |
| opt:opt.muon.ns | 86.209 | 87.425 | 41.7 | 3 |
| opt:opt.adamw | 1.145 | 1.577 | 0.6 | 2 |
| opt:opt.moe_bias | 0.572 | 0.632 | 0.3 | 3 |
| opt:opt.zero_grad | 0.578 | 0.837 | 0.3 | 3 |

## Time by part type (sum over layers)

| part type | median ms sum | % of step |
| :--- | ---: | ---: |
| opt | 95.509 | 46.2 |
| opt:opt.muon | 90.337 | 43.7 |
| opt:opt.muon.ns | 86.209 | 41.7 |
| bwd | 74.577 | 36.1 |
| bwd:block* | 60.382 | 29.2 |
| bwd:stack | 58.011 | 28.1 |
| fwd | 35.171 | 17.0 |
| bwd:block*.grad | 22.798 | 11.0 |
| bwd.recompute:block* | 16.901 | 8.2 |
| fwd:stack | 16.891 | 8.2 |
| bwd.invert:block* | 16.846 | 8.1 |
| bwd:head+loss | 16.319 | 7.9 |
| fwd:head+loss | 16.138 | 7.8 |
| fwd:block* | 16.070 | 7.8 |
| fwd:block*.moe.dispatch | 10.322 | 5.0 |
| bwd.recompute:block*.moe.dispatch | 10.188 | 4.9 |
| bwd.invert:block*.moe.dispatch | 9.839 | 4.8 |
| fwd:block*.moe.dispatch.grouped | 4.418 | 2.1 |
| bwd.recompute:block*.moe.dispatch.grouped | 3.835 | 1.9 |
| bwd.invert:block*.moe.dispatch.grouped | 3.795 | 1.8 |
| opt:opt.clip | 2.899 | 1.4 |
| fwd:embed | 2.016 | 1.0 |
| fwd:embed.ke | 1.989 | 1.0 |
| fwd:block*.moe.router | 1.709 | 0.8 |
| bwd.recompute:block*.moe.router | 1.467 | 0.7 |
| bwd.invert:block*.moe.router | 1.293 | 0.6 |
| opt:opt.adamw | 1.145 | 0.6 |
| fwd:block*.moe.shared | 1.045 | 0.5 |
| bwd.invert:block*.attn.qkv | 1.012 | 0.5 |
| bwd.invert:block*.moe.shared | 0.934 | 0.5 |
| bwd.recompute:block*.moe.shared | 0.932 | 0.5 |
| bwd.recompute:block*.attn.sdpa | 0.881 | 0.4 |
| fwd:block*.attn.qkv | 0.839 | 0.4 |
| fwd:block*.attn.sdpa | 0.791 | 0.4 |
| bwd.recompute:block*.attn.qkv | 0.769 | 0.4 |
| bwd.invert:block*.attn.sdpa | 0.764 | 0.4 |
| data | 0.722 | 0.3 |
| bwd.recompute:block*.attn.proj | 0.616 | 0.3 |
| opt:opt.zero_grad | 0.578 | 0.3 |
| opt:opt.moe_bias | 0.572 | 0.3 |
| bwd.invert:block*.ln1 | 0.556 | 0.3 |
| bwd.invert:block*.attn.proj | 0.512 | 0.2 |
| fwd:block*.ln1 | 0.497 | 0.2 |
| fwd:block*.attn.proj | 0.482 | 0.2 |
| bwd.recompute:block*.ln2 | 0.441 | 0.2 |
| bwd.invert:block*.ln2 | 0.403 | 0.2 |
| fwd:block*.ln2 | 0.390 | 0.2 |
| bwd.recompute:block*.ln1 | 0.327 | 0.2 |
| bwd:embed | 0.253 | 0.1 |

## Five slowest leaf parts

1. `opt:opt.muon.ns` — 86.209 ms (41.7% of step)
2. `bwd:block8.grad` — 2.658 ms (1.3% of step)
3. `bwd:block3.grad` — 2.569 ms (1.2% of step)
4. `bwd:block6.grad` — 2.562 ms (1.2% of step)
5. `bwd:block7.grad` — 2.541 ms (1.2% of step)
