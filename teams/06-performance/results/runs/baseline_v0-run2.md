# Bench report — baseline_v0-run2

**GPU:** NVIDIA A100-SXM4-40GB  |  **dtype:** bf16  |  **B x T:** 32 x 512  |  **torch:** 2.11.0+cu130
**commit:** `f1f4986aa0e4f74c64c86ce108c65c25678174eb`  |  **tag:** baseline_v0-run2

## Step (clean)

- median: 516.939 ms
- p10..p90: 507.237 .. 529.046 ms
- tokens/s: 31,694
- MFU: 3.3%  |  HFU: 4.2%

## Regions

| part | median ms | p90 | % of step | level |
| :--- | ---: | ---: | ---: | ---: |
| data | 0.856 | 0.883 | 0.2 | 1 |
| fwd | 103.985 | 106.319 | 20.1 | 1 |
| fwd:embed | 4.368 | 4.391 | 0.8 | 2 |
| fwd:embed.ke | 4.318 | 4.341 | 0.8 | 3 |
| fwd:stack | 57.302 | 59.646 | 11.1 | 1 |
| fwd:block0 | 6.029 | 6.340 | 1.2 | 2 |
| fwd:block0.ln1 | 0.046 | 0.047 | 0.0 | 3 |
| fwd:block0.attn.qkv | 0.049 | 0.050 | 0.0 | 3 |
| fwd:block0.attn.sdpa | 0.082 | 0.083 | 0.0 | 3 |
| fwd:block0.attn.proj | 0.037 | 0.038 | 0.0 | 3 |
| fwd:block0.ln2 | 0.047 | 0.048 | 0.0 | 3 |
| fwd:block0.moe.router | 0.139 | 0.143 | 0.0 | 3 |
| fwd:block0.moe.dispatch | 5.823 | 6.071 | 1.1 | 3 |
| fwd:block0.moe.dispatch.expert0 | 0.672 | 0.758 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert1 | 0.736 | 0.807 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert2 | 0.748 | 0.783 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert3 | 0.689 | 0.756 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert4 | 0.694 | 0.753 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert5 | 0.712 | 0.750 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert6 | 0.680 | 0.744 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert7 | 0.669 | 0.740 | 0.1 | 3 |
| fwd:block0.moe.shared | 0.354 | 0.372 | 0.1 | 3 |
| fwd:block1 | 6.368 | 6.706 | 1.2 | 2 |
| fwd:block1.ln1 | 0.089 | 0.098 | 0.0 | 3 |
| fwd:block1.attn.qkv | 0.197 | 0.225 | 0.0 | 3 |
| fwd:block1.attn.sdpa | 0.134 | 0.144 | 0.0 | 3 |
| fwd:block1.attn.proj | 0.103 | 0.130 | 0.0 | 3 |
| fwd:block1.ln2 | 0.066 | 0.079 | 0.0 | 3 |
| fwd:block1.moe.router | 0.323 | 0.357 | 0.1 | 3 |
| fwd:block1.moe.dispatch | 5.716 | 5.961 | 1.1 | 3 |
| fwd:block1.moe.dispatch.expert0 | 0.601 | 0.686 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert1 | 0.706 | 0.775 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert2 | 0.682 | 0.746 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert3 | 0.672 | 0.735 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert4 | 0.677 | 0.744 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert5 | 0.669 | 0.736 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert6 | 0.664 | 0.734 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert7 | 0.677 | 0.743 | 0.1 | 3 |
| fwd:block1.moe.shared | 0.356 | 0.382 | 0.1 | 3 |
| fwd:block2 | 6.347 | 6.672 | 1.2 | 2 |
| fwd:block2.ln1 | 0.087 | 0.097 | 0.0 | 3 |
| fwd:block2.attn.qkv | 0.194 | 0.212 | 0.0 | 3 |
| fwd:block2.attn.sdpa | 0.129 | 0.142 | 0.0 | 3 |
| fwd:block2.attn.proj | 0.100 | 0.130 | 0.0 | 3 |
| fwd:block2.ln2 | 0.063 | 0.077 | 0.0 | 3 |
| fwd:block2.moe.router | 0.317 | 0.357 | 0.1 | 3 |
| fwd:block2.moe.dispatch | 5.755 | 6.023 | 1.1 | 3 |
| fwd:block2.moe.dispatch.expert0 | 0.669 | 0.692 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert1 | 0.680 | 0.744 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert2 | 0.682 | 0.745 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert3 | 0.730 | 0.751 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert4 | 0.681 | 0.744 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert5 | 0.665 | 0.737 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert6 | 0.667 | 0.739 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert7 | 0.668 | 0.733 | 0.1 | 3 |
| fwd:block2.moe.shared | 0.349 | 0.370 | 0.1 | 3 |
| fwd:block3 | 6.420 | 6.658 | 1.2 | 2 |
| fwd:block3.ln1 | 0.086 | 0.096 | 0.0 | 3 |
| fwd:block3.attn.qkv | 0.194 | 0.220 | 0.0 | 3 |
| fwd:block3.attn.sdpa | 0.128 | 0.141 | 0.0 | 3 |
| fwd:block3.attn.proj | 0.100 | 0.132 | 0.0 | 3 |
| fwd:block3.ln2 | 0.062 | 0.073 | 0.0 | 3 |
| fwd:block3.moe.router | 0.308 | 0.353 | 0.1 | 3 |
| fwd:block3.moe.dispatch | 5.813 | 6.100 | 1.1 | 3 |
| fwd:block3.moe.dispatch.expert0 | 0.667 | 0.691 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert1 | 0.712 | 0.753 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert2 | 0.677 | 0.745 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert3 | 0.675 | 0.744 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert4 | 0.689 | 0.744 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert5 | 0.721 | 0.748 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert6 | 0.702 | 0.743 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert7 | 0.673 | 0.738 | 0.1 | 3 |
| fwd:block3.moe.shared | 0.353 | 0.377 | 0.1 | 3 |
| fwd:block4 | 6.390 | 6.679 | 1.2 | 2 |
| fwd:block4.ln1 | 0.085 | 0.098 | 0.0 | 3 |
| fwd:block4.attn.qkv | 0.193 | 0.218 | 0.0 | 3 |
| fwd:block4.attn.sdpa | 0.127 | 0.140 | 0.0 | 3 |
| fwd:block4.attn.proj | 0.101 | 0.130 | 0.0 | 3 |
| fwd:block4.ln2 | 0.062 | 0.075 | 0.0 | 3 |
| fwd:block4.moe.router | 0.305 | 0.357 | 0.1 | 3 |
| fwd:block4.moe.dispatch | 5.797 | 6.031 | 1.1 | 3 |
| fwd:block4.moe.dispatch.expert0 | 0.669 | 0.685 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert1 | 0.709 | 0.747 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert2 | 0.673 | 0.737 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert3 | 0.669 | 0.734 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert4 | 0.698 | 0.741 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert5 | 0.674 | 0.736 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert6 | 0.687 | 0.744 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert7 | 0.689 | 0.740 | 0.1 | 3 |
| fwd:block4.moe.shared | 0.352 | 0.382 | 0.1 | 3 |
| fwd:block5 | 6.361 | 6.639 | 1.2 | 2 |
| fwd:block5.ln1 | 0.086 | 0.095 | 0.0 | 3 |
| fwd:block5.attn.qkv | 0.190 | 0.218 | 0.0 | 3 |
| fwd:block5.attn.sdpa | 0.125 | 0.139 | 0.0 | 3 |
| fwd:block5.attn.proj | 0.100 | 0.132 | 0.0 | 3 |
| fwd:block5.ln2 | 0.062 | 0.070 | 0.0 | 3 |
| fwd:block5.moe.router | 0.304 | 0.352 | 0.1 | 3 |
| fwd:block5.moe.dispatch | 5.732 | 6.012 | 1.1 | 3 |
| fwd:block5.moe.dispatch.expert0 | 0.638 | 0.682 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert1 | 0.675 | 0.740 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert2 | 0.675 | 0.738 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert3 | 0.671 | 0.731 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert4 | 0.668 | 0.728 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert5 | 0.695 | 0.740 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert6 | 0.677 | 0.735 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert7 | 0.682 | 0.743 | 0.1 | 3 |
| fwd:block5.moe.shared | 0.353 | 0.379 | 0.1 | 3 |
| fwd:block6 | 6.321 | 6.645 | 1.2 | 2 |
| fwd:block6.ln1 | 0.086 | 0.098 | 0.0 | 3 |
| fwd:block6.attn.qkv | 0.189 | 0.218 | 0.0 | 3 |
| fwd:block6.attn.sdpa | 0.125 | 0.138 | 0.0 | 3 |
| fwd:block6.attn.proj | 0.098 | 0.124 | 0.0 | 3 |
| fwd:block6.ln2 | 0.063 | 0.073 | 0.0 | 3 |
| fwd:block6.moe.router | 0.303 | 0.352 | 0.1 | 3 |
| fwd:block6.moe.dispatch | 5.773 | 6.016 | 1.1 | 3 |
| fwd:block6.moe.dispatch.expert0 | 0.653 | 0.685 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert1 | 0.705 | 0.748 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert2 | 0.675 | 0.743 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert3 | 0.669 | 0.734 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert4 | 0.682 | 0.735 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert5 | 0.688 | 0.734 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert6 | 0.691 | 0.740 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert7 | 0.675 | 0.734 | 0.1 | 3 |
| fwd:block6.moe.shared | 0.352 | 0.381 | 0.1 | 3 |
| fwd:block7 | 6.212 | 6.594 | 1.2 | 2 |
| fwd:block7.ln1 | 0.085 | 0.092 | 0.0 | 3 |
| fwd:block7.attn.qkv | 0.191 | 0.215 | 0.0 | 3 |
| fwd:block7.attn.sdpa | 0.125 | 0.139 | 0.0 | 3 |
| fwd:block7.attn.proj | 0.100 | 0.128 | 0.0 | 3 |
| fwd:block7.ln2 | 0.061 | 0.075 | 0.0 | 3 |
| fwd:block7.moe.router | 0.301 | 0.351 | 0.1 | 3 |
| fwd:block7.moe.dispatch | 5.698 | 6.012 | 1.1 | 3 |
| fwd:block7.moe.dispatch.expert0 | 0.643 | 0.686 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert1 | 0.665 | 0.738 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert2 | 0.669 | 0.735 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert3 | 0.672 | 0.730 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert4 | 0.667 | 0.738 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert5 | 0.692 | 0.736 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert6 | 0.665 | 0.729 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert7 | 0.677 | 0.742 | 0.1 | 3 |
| fwd:block7.moe.shared | 0.354 | 0.384 | 0.1 | 3 |
| fwd:block8 | 6.317 | 6.547 | 1.2 | 2 |
| fwd:block8.ln1 | 0.086 | 0.095 | 0.0 | 3 |
| fwd:block8.attn.qkv | 0.189 | 0.216 | 0.0 | 3 |
| fwd:block8.attn.sdpa | 0.124 | 0.138 | 0.0 | 3 |
| fwd:block8.attn.proj | 0.099 | 0.128 | 0.0 | 3 |
| fwd:block8.ln2 | 0.062 | 0.069 | 0.0 | 3 |
| fwd:block8.moe.router | 0.294 | 0.356 | 0.1 | 3 |
| fwd:block8.moe.dispatch | 5.773 | 6.052 | 1.1 | 3 |
| fwd:block8.moe.dispatch.expert0 | 0.650 | 0.677 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert1 | 0.697 | 0.739 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert2 | 0.705 | 0.743 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert3 | 0.670 | 0.730 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert4 | 0.664 | 0.731 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert5 | 0.672 | 0.732 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert6 | 0.684 | 0.735 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert7 | 0.695 | 0.739 | 0.1 | 3 |
| fwd:block8.moe.shared | 0.352 | 0.378 | 0.1 | 3 |
| fwd:head+loss | 42.133 | 42.160 | 8.2 | 2 |
| bwd | 243.275 | 254.077 | 47.1 | 1 |
| bwd:head+loss | 48.153 | 48.166 | 9.3 | 2 |
| bwd:stack | 194.639 | 205.418 | 37.7 | 1 |
| bwd:block8 | 22.237 | 23.023 | 4.3 | 2 |
| bwd.invert:block8 | 6.440 | 6.580 | 1.2 | 3 |
| bwd.invert:block8.ln1 | 0.047 | 0.047 | 0.0 | 3 |
| bwd.invert:block8.attn.qkv | 0.049 | 0.050 | 0.0 | 3 |
| bwd.invert:block8.attn.sdpa | 0.081 | 0.083 | 0.0 | 3 |
| bwd.invert:block8.attn.proj | 0.037 | 0.038 | 0.0 | 3 |
| bwd.invert:block8.ln2 | 0.047 | 0.048 | 0.0 | 3 |
| bwd.invert:block8.moe.router | 0.065 | 0.066 | 0.0 | 3 |
| bwd.invert:block8.moe.dispatch | 5.459 | 5.584 | 1.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert0 | 0.977 | 1.040 | 0.2 | 3 |
| bwd.invert:block8.moe.dispatch.expert1 | 0.704 | 0.730 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert2 | 0.600 | 0.625 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert3 | 0.585 | 0.607 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert4 | 0.585 | 0.603 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert5 | 0.579 | 0.602 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert6 | 0.585 | 0.605 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert7 | 0.577 | 0.596 | 0.1 | 3 |
| bwd.invert:block8.moe.shared | 0.342 | 0.360 | 0.1 | 3 |
| bwd.recompute:block8 | 7.005 | 7.152 | 1.4 | 3 |
| bwd.recompute:block8.ln1 | 0.112 | 0.127 | 0.0 | 3 |
| bwd.recompute:block8.attn.qkv | 0.223 | 0.248 | 0.0 | 3 |
| bwd.recompute:block8.attn.sdpa | 0.168 | 0.178 | 0.0 | 3 |
| bwd.recompute:block8.attn.proj | 0.122 | 0.152 | 0.0 | 3 |
| bwd.recompute:block8.ln2 | 0.079 | 0.084 | 0.0 | 3 |
| bwd.recompute:block8.moe.router | 0.286 | 0.310 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch | 5.284 | 5.401 | 1.0 | 3 |
| bwd.recompute:block8.moe.dispatch.expert0 | 0.621 | 0.638 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert1 | 0.624 | 0.641 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert2 | 0.621 | 0.639 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert3 | 0.617 | 0.636 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert4 | 0.618 | 0.636 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert5 | 0.614 | 0.635 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert6 | 0.621 | 0.642 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert7 | 0.612 | 0.634 | 0.1 | 3 |
| bwd.recompute:block8.moe.shared | 0.340 | 0.361 | 0.1 | 3 |
| bwd:block8.grad | 10.605 | 11.086 | 2.1 | 3 |
| bwd:block7 | 21.732 | 23.003 | 4.2 | 2 |
| bwd.invert:block7 | 6.566 | 6.869 | 1.3 | 3 |
| bwd.invert:block7.ln1 | 0.097 | 0.111 | 0.0 | 3 |
| bwd.invert:block7.attn.qkv | 0.216 | 0.248 | 0.0 | 3 |
| bwd.invert:block7.attn.sdpa | 0.134 | 0.142 | 0.0 | 3 |
| bwd.invert:block7.attn.proj | 0.106 | 0.133 | 0.0 | 3 |
| bwd.invert:block7.ln2 | 0.067 | 0.074 | 0.0 | 3 |
| bwd.invert:block7.moe.router | 0.247 | 0.273 | 0.0 | 3 |
| bwd.invert:block7.moe.dispatch | 4.937 | 5.103 | 1.0 | 3 |
| bwd.invert:block7.moe.dispatch.expert0 | 0.600 | 0.667 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert1 | 0.584 | 0.614 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert2 | 0.574 | 0.598 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert3 | 0.573 | 0.591 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert4 | 0.566 | 0.589 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert5 | 0.569 | 0.589 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert6 | 0.568 | 0.588 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert7 | 0.567 | 0.588 | 0.1 | 3 |
| bwd.invert:block7.moe.shared | 0.333 | 0.353 | 0.1 | 3 |
| bwd.recompute:block7 | 6.942 | 7.184 | 1.3 | 3 |
| bwd.recompute:block7.ln1 | 0.095 | 0.105 | 0.0 | 3 |
| bwd.recompute:block7.attn.qkv | 0.220 | 0.242 | 0.0 | 3 |
| bwd.recompute:block7.attn.sdpa | 0.143 | 0.156 | 0.0 | 3 |
| bwd.recompute:block7.attn.proj | 0.114 | 0.139 | 0.0 | 3 |
| bwd.recompute:block7.ln2 | 0.072 | 0.088 | 0.0 | 3 |
| bwd.recompute:block7.moe.router | 0.257 | 0.281 | 0.0 | 3 |
| bwd.recompute:block7.moe.dispatch | 5.206 | 5.317 | 1.0 | 3 |
| bwd.recompute:block7.moe.dispatch.expert0 | 0.609 | 0.632 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert1 | 0.611 | 0.633 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert2 | 0.608 | 0.628 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert3 | 0.607 | 0.627 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert4 | 0.611 | 0.634 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert5 | 0.612 | 0.631 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert6 | 0.608 | 0.633 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert7 | 0.612 | 0.637 | 0.1 | 3 |
| bwd.recompute:block7.moe.shared | 0.339 | 0.357 | 0.1 | 3 |
| bwd:block7.grad | 10.265 | 10.757 | 2.0 | 3 |
| bwd:block6 | 21.654 | 23.132 | 4.2 | 2 |
| bwd.invert:block6 | 6.448 | 6.785 | 1.2 | 3 |
| bwd.invert:block6.ln1 | 0.095 | 0.109 | 0.0 | 3 |
| bwd.invert:block6.attn.qkv | 0.206 | 0.230 | 0.0 | 3 |
| bwd.invert:block6.attn.sdpa | 0.130 | 0.141 | 0.0 | 3 |
| bwd.invert:block6.attn.proj | 0.104 | 0.127 | 0.0 | 3 |
| bwd.invert:block6.ln2 | 0.065 | 0.073 | 0.0 | 3 |
| bwd.invert:block6.moe.router | 0.239 | 0.269 | 0.0 | 3 |
| bwd.invert:block6.moe.dispatch | 4.890 | 5.068 | 0.9 | 3 |
| bwd.invert:block6.moe.dispatch.expert0 | 0.592 | 0.667 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert1 | 0.578 | 0.607 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert2 | 0.568 | 0.591 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert3 | 0.566 | 0.588 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert4 | 0.569 | 0.590 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert5 | 0.568 | 0.587 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert6 | 0.564 | 0.587 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert7 | 0.559 | 0.585 | 0.1 | 3 |
| bwd.invert:block6.moe.shared | 0.333 | 0.348 | 0.1 | 3 |
| bwd.recompute:block6 | 6.855 | 7.181 | 1.3 | 3 |
| bwd.recompute:block6.ln1 | 0.094 | 0.104 | 0.0 | 3 |
| bwd.recompute:block6.attn.qkv | 0.208 | 0.235 | 0.0 | 3 |
| bwd.recompute:block6.attn.sdpa | 0.147 | 0.165 | 0.0 | 3 |
| bwd.recompute:block6.attn.proj | 0.118 | 0.146 | 0.0 | 3 |
| bwd.recompute:block6.ln2 | 0.071 | 0.080 | 0.0 | 3 |
| bwd.recompute:block6.moe.router | 0.253 | 0.279 | 0.0 | 3 |
| bwd.recompute:block6.moe.dispatch | 5.166 | 5.294 | 1.0 | 3 |
| bwd.recompute:block6.moe.dispatch.expert0 | 0.601 | 0.628 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert1 | 0.607 | 0.629 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert2 | 0.608 | 0.629 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert3 | 0.606 | 0.625 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert4 | 0.607 | 0.628 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert5 | 0.605 | 0.626 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert6 | 0.604 | 0.628 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert7 | 0.603 | 0.626 | 0.1 | 3 |
| bwd.recompute:block6.moe.shared | 0.338 | 0.355 | 0.1 | 3 |
| bwd:block6.grad | 10.288 | 10.865 | 2.0 | 3 |
| bwd:block5 | 21.671 | 23.150 | 4.2 | 2 |
| bwd.invert:block5 | 6.421 | 6.792 | 1.2 | 3 |
| bwd.invert:block5.ln1 | 0.092 | 0.110 | 0.0 | 3 |
| bwd.invert:block5.attn.qkv | 0.202 | 0.231 | 0.0 | 3 |
| bwd.invert:block5.attn.sdpa | 0.127 | 0.140 | 0.0 | 3 |
| bwd.invert:block5.attn.proj | 0.103 | 0.126 | 0.0 | 3 |
| bwd.invert:block5.ln2 | 0.065 | 0.074 | 0.0 | 3 |
| bwd.invert:block5.moe.router | 0.236 | 0.279 | 0.0 | 3 |
| bwd.invert:block5.moe.dispatch | 4.876 | 5.078 | 0.9 | 3 |
| bwd.invert:block5.moe.dispatch.expert0 | 0.589 | 0.662 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert1 | 0.578 | 0.614 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert2 | 0.573 | 0.594 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert3 | 0.560 | 0.587 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert4 | 0.569 | 0.591 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert5 | 0.564 | 0.580 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert6 | 0.566 | 0.585 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert7 | 0.563 | 0.585 | 0.1 | 3 |
| bwd.invert:block5.moe.shared | 0.333 | 0.346 | 0.1 | 3 |
| bwd.recompute:block5 | 6.837 | 7.137 | 1.3 | 3 |
| bwd.recompute:block5.ln1 | 0.093 | 0.104 | 0.0 | 3 |
| bwd.recompute:block5.attn.qkv | 0.214 | 0.234 | 0.0 | 3 |
| bwd.recompute:block5.attn.sdpa | 0.147 | 0.164 | 0.0 | 3 |
| bwd.recompute:block5.attn.proj | 0.113 | 0.138 | 0.0 | 3 |
| bwd.recompute:block5.ln2 | 0.070 | 0.076 | 0.0 | 3 |
| bwd.recompute:block5.moe.router | 0.246 | 0.275 | 0.0 | 3 |
| bwd.recompute:block5.moe.dispatch | 5.162 | 5.281 | 1.0 | 3 |
| bwd.recompute:block5.moe.dispatch.expert0 | 0.603 | 0.621 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert1 | 0.609 | 0.630 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert2 | 0.604 | 0.628 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert3 | 0.605 | 0.627 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert4 | 0.602 | 0.628 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert5 | 0.600 | 0.621 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert6 | 0.608 | 0.631 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert7 | 0.605 | 0.631 | 0.1 | 3 |
| bwd.recompute:block5.moe.shared | 0.339 | 0.361 | 0.1 | 3 |
| bwd:block5.grad | 10.280 | 10.743 | 2.0 | 3 |
| bwd:block4 | 21.571 | 23.092 | 4.2 | 2 |
| bwd.invert:block4 | 6.405 | 6.766 | 1.2 | 3 |
| bwd.invert:block4.ln1 | 0.092 | 0.106 | 0.0 | 3 |
| bwd.invert:block4.attn.qkv | 0.204 | 0.231 | 0.0 | 3 |
| bwd.invert:block4.attn.sdpa | 0.127 | 0.139 | 0.0 | 3 |
| bwd.invert:block4.attn.proj | 0.102 | 0.131 | 0.0 | 3 |
| bwd.invert:block4.ln2 | 0.063 | 0.074 | 0.0 | 3 |
| bwd.invert:block4.moe.router | 0.232 | 0.264 | 0.0 | 3 |
| bwd.invert:block4.moe.dispatch | 4.880 | 5.060 | 0.9 | 3 |
| bwd.invert:block4.moe.dispatch.expert0 | 0.589 | 0.654 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert1 | 0.574 | 0.603 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert2 | 0.573 | 0.593 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert3 | 0.563 | 0.588 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert4 | 0.567 | 0.590 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert5 | 0.564 | 0.583 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert6 | 0.565 | 0.586 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert7 | 0.565 | 0.582 | 0.1 | 3 |
| bwd.invert:block4.moe.shared | 0.332 | 0.350 | 0.1 | 3 |
| bwd.recompute:block4 | 6.821 | 7.132 | 1.3 | 3 |
| bwd.recompute:block4.ln1 | 0.094 | 0.106 | 0.0 | 3 |
| bwd.recompute:block4.attn.qkv | 0.212 | 0.234 | 0.0 | 3 |
| bwd.recompute:block4.attn.sdpa | 0.147 | 0.167 | 0.0 | 3 |
| bwd.recompute:block4.attn.proj | 0.115 | 0.144 | 0.0 | 3 |
| bwd.recompute:block4.ln2 | 0.070 | 0.078 | 0.0 | 3 |
| bwd.recompute:block4.moe.router | 0.243 | 0.286 | 0.0 | 3 |
| bwd.recompute:block4.moe.dispatch | 5.150 | 5.320 | 1.0 | 3 |
| bwd.recompute:block4.moe.dispatch.expert0 | 0.603 | 0.629 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert1 | 0.605 | 0.628 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert2 | 0.605 | 0.629 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert3 | 0.602 | 0.625 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert4 | 0.600 | 0.624 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert5 | 0.599 | 0.620 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert6 | 0.605 | 0.633 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert7 | 0.602 | 0.625 | 0.1 | 3 |
| bwd.recompute:block4.moe.shared | 0.340 | 0.359 | 0.1 | 3 |
| bwd:block4.grad | 10.225 | 10.735 | 2.0 | 3 |
| bwd:block3 | 21.489 | 23.068 | 4.2 | 2 |
| bwd.invert:block3 | 6.408 | 6.746 | 1.2 | 3 |
| bwd.invert:block3.ln1 | 0.094 | 0.108 | 0.0 | 3 |
| bwd.invert:block3.attn.qkv | 0.199 | 0.228 | 0.0 | 3 |
| bwd.invert:block3.attn.sdpa | 0.126 | 0.138 | 0.0 | 3 |
| bwd.invert:block3.attn.proj | 0.099 | 0.132 | 0.0 | 3 |
| bwd.invert:block3.ln2 | 0.063 | 0.075 | 0.0 | 3 |
| bwd.invert:block3.moe.router | 0.238 | 0.267 | 0.0 | 3 |
| bwd.invert:block3.moe.dispatch | 4.890 | 5.068 | 0.9 | 3 |
| bwd.invert:block3.moe.dispatch.expert0 | 0.586 | 0.674 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert1 | 0.577 | 0.610 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert2 | 0.568 | 0.590 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert3 | 0.565 | 0.587 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert4 | 0.568 | 0.587 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert5 | 0.561 | 0.588 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert6 | 0.566 | 0.588 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert7 | 0.561 | 0.589 | 0.1 | 3 |
| bwd.invert:block3.moe.shared | 0.334 | 0.350 | 0.1 | 3 |
| bwd.recompute:block3 | 6.831 | 7.150 | 1.3 | 3 |
| bwd.recompute:block3.ln1 | 0.093 | 0.103 | 0.0 | 3 |
| bwd.recompute:block3.attn.qkv | 0.207 | 0.228 | 0.0 | 3 |
| bwd.recompute:block3.attn.sdpa | 0.147 | 0.163 | 0.0 | 3 |
| bwd.recompute:block3.attn.proj | 0.115 | 0.144 | 0.0 | 3 |
| bwd.recompute:block3.ln2 | 0.070 | 0.080 | 0.0 | 3 |
| bwd.recompute:block3.moe.router | 0.241 | 0.280 | 0.0 | 3 |
| bwd.recompute:block3.moe.dispatch | 5.168 | 5.313 | 1.0 | 3 |
| bwd.recompute:block3.moe.dispatch.expert0 | 0.604 | 0.630 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert1 | 0.605 | 0.634 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert2 | 0.604 | 0.627 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert3 | 0.603 | 0.626 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert4 | 0.602 | 0.630 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert5 | 0.606 | 0.631 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert6 | 0.603 | 0.629 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert7 | 0.604 | 0.627 | 0.1 | 3 |
| bwd.recompute:block3.moe.shared | 0.338 | 0.356 | 0.1 | 3 |
| bwd:block3.grad | 10.270 | 10.820 | 2.0 | 3 |
| bwd:block2 | 21.445 | 22.761 | 4.1 | 2 |
| bwd.invert:block2 | 6.383 | 6.732 | 1.2 | 3 |
| bwd.invert:block2.ln1 | 0.092 | 0.110 | 0.0 | 3 |
| bwd.invert:block2.attn.qkv | 0.202 | 0.230 | 0.0 | 3 |
| bwd.invert:block2.attn.sdpa | 0.127 | 0.137 | 0.0 | 3 |
| bwd.invert:block2.attn.proj | 0.099 | 0.121 | 0.0 | 3 |
| bwd.invert:block2.ln2 | 0.062 | 0.072 | 0.0 | 3 |
| bwd.invert:block2.moe.router | 0.235 | 0.269 | 0.0 | 3 |
| bwd.invert:block2.moe.dispatch | 4.873 | 5.052 | 0.9 | 3 |
| bwd.invert:block2.moe.dispatch.expert0 | 0.586 | 0.659 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert1 | 0.580 | 0.611 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert2 | 0.571 | 0.597 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert3 | 0.565 | 0.590 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert4 | 0.566 | 0.593 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert5 | 0.562 | 0.582 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert6 | 0.566 | 0.585 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert7 | 0.561 | 0.580 | 0.1 | 3 |
| bwd.invert:block2.moe.shared | 0.331 | 0.347 | 0.1 | 3 |
| bwd.recompute:block2 | 6.804 | 7.141 | 1.3 | 3 |
| bwd.recompute:block2.ln1 | 0.093 | 0.104 | 0.0 | 3 |
| bwd.recompute:block2.attn.qkv | 0.206 | 0.231 | 0.0 | 3 |
| bwd.recompute:block2.attn.sdpa | 0.146 | 0.166 | 0.0 | 3 |
| bwd.recompute:block2.attn.proj | 0.115 | 0.143 | 0.0 | 3 |
| bwd.recompute:block2.ln2 | 0.069 | 0.078 | 0.0 | 3 |
| bwd.recompute:block2.moe.router | 0.245 | 0.275 | 0.0 | 3 |
| bwd.recompute:block2.moe.dispatch | 5.155 | 5.317 | 1.0 | 3 |
| bwd.recompute:block2.moe.dispatch.expert0 | 0.601 | 0.626 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert1 | 0.606 | 0.632 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert2 | 0.607 | 0.627 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert3 | 0.606 | 0.634 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert4 | 0.600 | 0.622 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert5 | 0.603 | 0.626 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert6 | 0.601 | 0.625 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert7 | 0.599 | 0.622 | 0.1 | 3 |
| bwd.recompute:block2.moe.shared | 0.336 | 0.353 | 0.1 | 3 |
| bwd:block2.grad | 10.093 | 10.635 | 2.0 | 3 |
| bwd:block1 | 21.360 | 22.604 | 4.1 | 2 |
| bwd.invert:block1 | 6.381 | 6.759 | 1.2 | 3 |
| bwd.invert:block1.ln1 | 0.092 | 0.109 | 0.0 | 3 |
| bwd.invert:block1.attn.qkv | 0.201 | 0.228 | 0.0 | 3 |
| bwd.invert:block1.attn.sdpa | 0.125 | 0.137 | 0.0 | 3 |
| bwd.invert:block1.attn.proj | 0.100 | 0.126 | 0.0 | 3 |
| bwd.invert:block1.ln2 | 0.062 | 0.072 | 0.0 | 3 |
| bwd.invert:block1.moe.router | 0.235 | 0.271 | 0.0 | 3 |
| bwd.invert:block1.moe.dispatch | 4.866 | 5.065 | 0.9 | 3 |
| bwd.invert:block1.moe.dispatch.expert0 | 0.585 | 0.665 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert1 | 0.582 | 0.619 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert2 | 0.573 | 0.594 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert3 | 0.563 | 0.586 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert4 | 0.567 | 0.589 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert5 | 0.562 | 0.584 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert6 | 0.565 | 0.582 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert7 | 0.562 | 0.583 | 0.1 | 3 |
| bwd.invert:block1.moe.shared | 0.331 | 0.346 | 0.1 | 3 |
| bwd.recompute:block1 | 6.819 | 7.129 | 1.3 | 3 |
| bwd.recompute:block1.ln1 | 0.092 | 0.103 | 0.0 | 3 |
| bwd.recompute:block1.attn.qkv | 0.209 | 0.231 | 0.0 | 3 |
| bwd.recompute:block1.attn.sdpa | 0.145 | 0.166 | 0.0 | 3 |
| bwd.recompute:block1.attn.proj | 0.113 | 0.141 | 0.0 | 3 |
| bwd.recompute:block1.ln2 | 0.069 | 0.080 | 0.0 | 3 |
| bwd.recompute:block1.moe.router | 0.241 | 0.273 | 0.0 | 3 |
| bwd.recompute:block1.moe.dispatch | 5.166 | 5.323 | 1.0 | 3 |
| bwd.recompute:block1.moe.dispatch.expert0 | 0.604 | 0.626 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert1 | 0.611 | 0.643 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert2 | 0.606 | 0.636 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert3 | 0.606 | 0.632 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert4 | 0.603 | 0.630 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert5 | 0.599 | 0.625 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert6 | 0.605 | 0.626 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert7 | 0.598 | 0.622 | 0.1 | 3 |
| bwd.recompute:block1.moe.shared | 0.338 | 0.359 | 0.1 | 3 |
| bwd:block1.grad | 10.127 | 10.490 | 2.0 | 3 |
| bwd:block0 | 21.368 | 22.531 | 4.1 | 2 |
| bwd.invert:block0 | 6.393 | 6.771 | 1.2 | 3 |
| bwd.invert:block0.ln1 | 0.093 | 0.110 | 0.0 | 3 |
| bwd.invert:block0.attn.qkv | 0.201 | 0.225 | 0.0 | 3 |
| bwd.invert:block0.attn.sdpa | 0.125 | 0.136 | 0.0 | 3 |
| bwd.invert:block0.attn.proj | 0.098 | 0.126 | 0.0 | 3 |
| bwd.invert:block0.ln2 | 0.065 | 0.074 | 0.0 | 3 |
| bwd.invert:block0.moe.router | 0.233 | 0.265 | 0.0 | 3 |
| bwd.invert:block0.moe.dispatch | 4.880 | 5.089 | 0.9 | 3 |
| bwd.invert:block0.moe.dispatch.expert0 | 0.587 | 0.662 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert1 | 0.573 | 0.599 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert2 | 0.577 | 0.606 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert3 | 0.563 | 0.583 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert4 | 0.566 | 0.590 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert5 | 0.561 | 0.591 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert6 | 0.563 | 0.584 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert7 | 0.563 | 0.593 | 0.1 | 3 |
| bwd.invert:block0.moe.shared | 0.331 | 0.350 | 0.1 | 3 |
| bwd.recompute:block0 | 6.801 | 7.123 | 1.3 | 3 |
| bwd.recompute:block0.ln1 | 0.093 | 0.105 | 0.0 | 3 |
| bwd.recompute:block0.attn.qkv | 0.209 | 0.232 | 0.0 | 3 |
| bwd.recompute:block0.attn.sdpa | 0.145 | 0.165 | 0.0 | 3 |
| bwd.recompute:block0.attn.proj | 0.116 | 0.142 | 0.0 | 3 |
| bwd.recompute:block0.ln2 | 0.070 | 0.085 | 0.0 | 3 |
| bwd.recompute:block0.moe.router | 0.246 | 0.281 | 0.0 | 3 |
| bwd.recompute:block0.moe.dispatch | 5.149 | 5.310 | 1.0 | 3 |
| bwd.recompute:block0.moe.dispatch.expert0 | 0.605 | 0.625 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert1 | 0.605 | 0.629 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert2 | 0.612 | 0.644 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert3 | 0.604 | 0.628 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert4 | 0.602 | 0.625 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert5 | 0.601 | 0.625 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert6 | 0.596 | 0.618 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert7 | 0.602 | 0.626 | 0.1 | 3 |
| bwd.recompute:block0.moe.shared | 0.336 | 0.348 | 0.1 | 3 |
| bwd:block0.grad | 10.134 | 10.657 | 2.0 | 3 |
| bwd:embed | 0.486 | 0.509 | 0.1 | 2 |
| opt | 166.407 | 170.176 | 32.2 | 1 |
| opt:opt.clip | 4.470 | 4.733 | 0.9 | 2 |
| opt:opt.muon | 158.199 | 161.973 | 30.6 | 2 |
| opt:opt.muon.ns | 151.135 | 154.456 | 29.2 | 3 |
| opt:opt.adamw | 1.640 | 1.733 | 0.3 | 2 |
| opt:opt.moe_bias | 0.896 | 0.925 | 0.2 | 3 |
| opt:opt.zero_grad | 1.061 | 1.109 | 0.2 | 3 |

## Time by part type (sum over layers)

| part type | median ms sum | % of step |
| :--- | ---: | ---: |
| bwd | 243.275 | 47.1 |
| bwd:stack | 194.639 | 37.7 |
| bwd:block* | 194.528 | 37.6 |
| opt | 166.407 | 32.2 |
| opt:opt.muon | 158.199 | 30.6 |
| opt:opt.muon.ns | 151.135 | 29.2 |
| fwd | 103.985 | 20.1 |
| bwd:block*.grad | 92.286 | 17.9 |
| bwd.recompute:block* | 61.714 | 11.9 |
| bwd.invert:block* | 57.844 | 11.2 |
| fwd:stack | 57.302 | 11.1 |
| fwd:block* | 56.765 | 11.0 |
| fwd:block*.moe.dispatch | 51.880 | 10.0 |
| bwd:head+loss | 48.153 | 9.3 |
| bwd.recompute:block*.moe.dispatch | 46.606 | 9.0 |
| bwd.invert:block*.moe.dispatch | 44.551 | 8.6 |
| fwd:head+loss | 42.133 | 8.2 |
| fwd:block*.moe.dispatch.expert1 | 6.285 | 1.2 |
| fwd:block*.moe.dispatch.expert5 | 6.188 | 1.2 |
| fwd:block*.moe.dispatch.expert2 | 6.188 | 1.2 |
| fwd:block*.moe.dispatch.expert4 | 6.120 | 1.2 |
| fwd:block*.moe.dispatch.expert6 | 6.117 | 1.2 |
| fwd:block*.moe.dispatch.expert3 | 6.116 | 1.2 |
| fwd:block*.moe.dispatch.expert7 | 6.104 | 1.2 |
| fwd:block*.moe.dispatch.expert0 | 5.860 | 1.1 |
| bwd.invert:block*.moe.dispatch.expert0 | 5.690 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert1 | 5.483 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert2 | 5.475 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert3 | 5.457 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert0 | 5.452 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert6 | 5.451 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert4 | 5.445 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert5 | 5.439 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert7 | 5.436 | 1.1 |
| bwd.invert:block*.moe.dispatch.expert1 | 5.329 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert2 | 5.178 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert4 | 5.124 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert6 | 5.109 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert3 | 5.104 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert5 | 5.091 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert7 | 5.078 | 1.0 |
| opt:opt.clip | 4.470 | 0.9 |
| fwd:embed | 4.368 | 0.8 |
| fwd:embed.ke | 4.318 | 0.8 |
| fwd:block*.moe.shared | 3.176 | 0.6 |
| bwd.recompute:block*.moe.shared | 3.045 | 0.6 |
| bwd.invert:block*.moe.shared | 2.999 | 0.6 |
| fwd:block*.moe.router | 2.593 | 0.5 |
| bwd.recompute:block*.moe.router | 2.256 | 0.4 |
| bwd.invert:block*.moe.router | 1.960 | 0.4 |
| bwd.recompute:block*.attn.qkv | 1.908 | 0.4 |
| bwd.invert:block*.attn.qkv | 1.679 | 0.3 |
| opt:opt.adamw | 1.640 | 0.3 |
| fwd:block*.attn.qkv | 1.587 | 0.3 |
| bwd.recompute:block*.attn.sdpa | 1.338 | 0.3 |
| bwd.invert:block*.attn.sdpa | 1.102 | 0.2 |
| fwd:block*.attn.sdpa | 1.099 | 0.2 |
| opt:opt.zero_grad | 1.061 | 0.2 |
| bwd.recompute:block*.attn.proj | 1.039 | 0.2 |
| opt:opt.moe_bias | 0.896 | 0.2 |
| bwd.recompute:block*.ln1 | 0.860 | 0.2 |
| data | 0.856 | 0.2 |
| bwd.invert:block*.attn.proj | 0.851 | 0.2 |
| fwd:block*.attn.proj | 0.840 | 0.2 |
| bwd.invert:block*.ln1 | 0.795 | 0.2 |
| fwd:block*.ln1 | 0.736 | 0.1 |
| bwd.recompute:block*.ln2 | 0.637 | 0.1 |
| bwd.invert:block*.ln2 | 0.559 | 0.1 |
| fwd:block*.ln2 | 0.551 | 0.1 |
| bwd:embed | 0.486 | 0.1 |

## Five slowest leaf parts

1. `opt:opt.muon.ns` — 151.135 ms (29.2% of step)
2. `bwd:block8.grad` — 10.605 ms (2.1% of step)
3. `bwd:block6.grad` — 10.288 ms (2.0% of step)
4. `bwd:block5.grad` — 10.280 ms (2.0% of step)
5. `bwd:block3.grad` — 10.270 ms (2.0% of step)
