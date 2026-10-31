# Bench report — baseline_v0

**GPU:** NVIDIA A100-SXM4-40GB  |  **dtype:** bf16  |  **B x T:** 32 x 512  |  **torch:** 2.11.0+cu130
**commit:** `f1f4986aa0e4f74c64c86ce108c65c25678174eb`  |  **tag:** baseline_v0

## Step (clean)

- median: 506.619 ms
- p10..p90: 499.635 .. 520.089 ms
- tokens/s: 32,340
- MFU: 3.3%  |  HFU: 4.2%

## Regions

| part | median ms | p90 | % of step | level |
| :--- | ---: | ---: | ---: | ---: |
| data | 0.856 | 0.881 | 0.2 | 1 |
| fwd | 102.342 | 104.567 | 20.2 | 1 |
| fwd:embed | 4.360 | 4.384 | 0.9 | 2 |
| fwd:embed.ke | 4.308 | 4.335 | 0.9 | 3 |
| fwd:stack | 55.685 | 57.859 | 11.0 | 1 |
| fwd:block0 | 5.846 | 6.099 | 1.2 | 2 |
| fwd:block0.ln1 | 0.046 | 0.047 | 0.0 | 3 |
| fwd:block0.attn.qkv | 0.049 | 0.050 | 0.0 | 3 |
| fwd:block0.attn.sdpa | 0.082 | 0.083 | 0.0 | 3 |
| fwd:block0.attn.proj | 0.038 | 0.039 | 0.0 | 3 |
| fwd:block0.ln2 | 0.047 | 0.047 | 0.0 | 3 |
| fwd:block0.moe.router | 0.138 | 0.139 | 0.0 | 3 |
| fwd:block0.moe.dispatch | 5.660 | 5.941 | 1.1 | 3 |
| fwd:block0.moe.dispatch.expert0 | 0.669 | 0.749 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert1 | 0.704 | 0.786 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert2 | 0.699 | 0.756 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert3 | 0.691 | 0.746 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert4 | 0.694 | 0.738 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert5 | 0.686 | 0.735 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert6 | 0.660 | 0.720 | 0.1 | 3 |
| fwd:block0.moe.dispatch.expert7 | 0.643 | 0.722 | 0.1 | 3 |
| fwd:block0.moe.shared | 0.342 | 0.369 | 0.1 | 3 |
| fwd:block1 | 6.156 | 6.454 | 1.2 | 2 |
| fwd:block1.ln1 | 0.089 | 0.099 | 0.0 | 3 |
| fwd:block1.attn.qkv | 0.192 | 0.215 | 0.0 | 3 |
| fwd:block1.attn.sdpa | 0.132 | 0.143 | 0.0 | 3 |
| fwd:block1.attn.proj | 0.099 | 0.126 | 0.0 | 3 |
| fwd:block1.ln2 | 0.067 | 0.076 | 0.0 | 3 |
| fwd:block1.moe.router | 0.316 | 0.355 | 0.1 | 3 |
| fwd:block1.moe.dispatch | 5.549 | 5.872 | 1.1 | 3 |
| fwd:block1.moe.dispatch.expert0 | 0.587 | 0.676 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert1 | 0.668 | 0.739 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert2 | 0.693 | 0.734 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert3 | 0.689 | 0.730 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert4 | 0.663 | 0.721 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert5 | 0.653 | 0.720 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert6 | 0.650 | 0.720 | 0.1 | 3 |
| fwd:block1.moe.dispatch.expert7 | 0.646 | 0.718 | 0.1 | 3 |
| fwd:block1.moe.shared | 0.349 | 0.375 | 0.1 | 3 |
| fwd:block2 | 6.217 | 6.485 | 1.2 | 2 |
| fwd:block2.ln1 | 0.088 | 0.094 | 0.0 | 3 |
| fwd:block2.attn.qkv | 0.189 | 0.216 | 0.0 | 3 |
| fwd:block2.attn.sdpa | 0.129 | 0.139 | 0.0 | 3 |
| fwd:block2.attn.proj | 0.098 | 0.129 | 0.0 | 3 |
| fwd:block2.ln2 | 0.063 | 0.070 | 0.0 | 3 |
| fwd:block2.moe.router | 0.307 | 0.347 | 0.1 | 3 |
| fwd:block2.moe.dispatch | 5.662 | 5.862 | 1.1 | 3 |
| fwd:block2.moe.dispatch.expert0 | 0.645 | 0.674 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert1 | 0.665 | 0.729 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert2 | 0.666 | 0.730 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert3 | 0.712 | 0.735 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert4 | 0.675 | 0.725 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert5 | 0.649 | 0.712 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert6 | 0.648 | 0.718 | 0.1 | 3 |
| fwd:block2.moe.dispatch.expert7 | 0.656 | 0.719 | 0.1 | 3 |
| fwd:block2.moe.shared | 0.349 | 0.380 | 0.1 | 3 |
| fwd:block3 | 6.196 | 6.431 | 1.2 | 2 |
| fwd:block3.ln1 | 0.088 | 0.097 | 0.0 | 3 |
| fwd:block3.attn.qkv | 0.188 | 0.214 | 0.0 | 3 |
| fwd:block3.attn.sdpa | 0.126 | 0.138 | 0.0 | 3 |
| fwd:block3.attn.proj | 0.096 | 0.125 | 0.0 | 3 |
| fwd:block3.ln2 | 0.061 | 0.077 | 0.0 | 3 |
| fwd:block3.moe.router | 0.301 | 0.343 | 0.1 | 3 |
| fwd:block3.moe.dispatch | 5.584 | 5.835 | 1.1 | 3 |
| fwd:block3.moe.dispatch.expert0 | 0.639 | 0.678 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert1 | 0.698 | 0.736 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert2 | 0.667 | 0.726 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert3 | 0.645 | 0.701 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert4 | 0.650 | 0.716 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert5 | 0.672 | 0.724 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert6 | 0.662 | 0.718 | 0.1 | 3 |
| fwd:block3.moe.dispatch.expert7 | 0.648 | 0.713 | 0.1 | 3 |
| fwd:block3.moe.shared | 0.348 | 0.359 | 0.1 | 3 |
| fwd:block4 | 6.230 | 6.473 | 1.2 | 2 |
| fwd:block4.ln1 | 0.087 | 0.093 | 0.0 | 3 |
| fwd:block4.attn.qkv | 0.185 | 0.216 | 0.0 | 3 |
| fwd:block4.attn.sdpa | 0.124 | 0.135 | 0.0 | 3 |
| fwd:block4.attn.proj | 0.094 | 0.120 | 0.0 | 3 |
| fwd:block4.ln2 | 0.060 | 0.067 | 0.0 | 3 |
| fwd:block4.moe.router | 0.303 | 0.342 | 0.1 | 3 |
| fwd:block4.moe.dispatch | 5.679 | 5.890 | 1.1 | 3 |
| fwd:block4.moe.dispatch.expert0 | 0.645 | 0.672 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert1 | 0.673 | 0.730 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert2 | 0.663 | 0.720 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert3 | 0.668 | 0.721 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert4 | 0.681 | 0.721 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert5 | 0.661 | 0.719 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert6 | 0.669 | 0.720 | 0.1 | 3 |
| fwd:block4.moe.dispatch.expert7 | 0.663 | 0.715 | 0.1 | 3 |
| fwd:block4.moe.shared | 0.346 | 0.370 | 0.1 | 3 |
| fwd:block5 | 6.174 | 6.389 | 1.2 | 2 |
| fwd:block5.ln1 | 0.086 | 0.094 | 0.0 | 3 |
| fwd:block5.attn.qkv | 0.184 | 0.213 | 0.0 | 3 |
| fwd:block5.attn.sdpa | 0.124 | 0.138 | 0.0 | 3 |
| fwd:block5.attn.proj | 0.096 | 0.122 | 0.0 | 3 |
| fwd:block5.ln2 | 0.062 | 0.070 | 0.0 | 3 |
| fwd:block5.moe.router | 0.296 | 0.341 | 0.1 | 3 |
| fwd:block5.moe.dispatch | 5.567 | 5.826 | 1.1 | 3 |
| fwd:block5.moe.dispatch.expert0 | 0.639 | 0.672 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert1 | 0.662 | 0.720 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert2 | 0.654 | 0.713 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert3 | 0.649 | 0.714 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert4 | 0.660 | 0.722 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert5 | 0.674 | 0.721 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert6 | 0.656 | 0.715 | 0.1 | 3 |
| fwd:block5.moe.dispatch.expert7 | 0.651 | 0.715 | 0.1 | 3 |
| fwd:block5.moe.shared | 0.349 | 0.377 | 0.1 | 3 |
| fwd:block6 | 6.173 | 6.423 | 1.2 | 2 |
| fwd:block6.ln1 | 0.086 | 0.095 | 0.0 | 3 |
| fwd:block6.attn.qkv | 0.183 | 0.208 | 0.0 | 3 |
| fwd:block6.attn.sdpa | 0.123 | 0.138 | 0.0 | 3 |
| fwd:block6.attn.proj | 0.093 | 0.124 | 0.0 | 3 |
| fwd:block6.ln2 | 0.062 | 0.073 | 0.0 | 3 |
| fwd:block6.moe.router | 0.299 | 0.341 | 0.1 | 3 |
| fwd:block6.moe.dispatch | 5.693 | 5.934 | 1.1 | 3 |
| fwd:block6.moe.dispatch.expert0 | 0.640 | 0.677 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert1 | 0.688 | 0.726 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert2 | 0.678 | 0.721 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert3 | 0.662 | 0.719 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert4 | 0.656 | 0.719 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert5 | 0.674 | 0.725 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert6 | 0.690 | 0.721 | 0.1 | 3 |
| fwd:block6.moe.dispatch.expert7 | 0.682 | 0.720 | 0.1 | 3 |
| fwd:block6.moe.shared | 0.351 | 0.371 | 0.1 | 3 |
| fwd:block7 | 6.141 | 6.398 | 1.2 | 2 |
| fwd:block7.ln1 | 0.086 | 0.096 | 0.0 | 3 |
| fwd:block7.attn.qkv | 0.186 | 0.210 | 0.0 | 3 |
| fwd:block7.attn.sdpa | 0.123 | 0.136 | 0.0 | 3 |
| fwd:block7.attn.proj | 0.094 | 0.123 | 0.0 | 3 |
| fwd:block7.ln2 | 0.060 | 0.073 | 0.0 | 3 |
| fwd:block7.moe.router | 0.293 | 0.345 | 0.1 | 3 |
| fwd:block7.moe.dispatch | 5.577 | 5.863 | 1.1 | 3 |
| fwd:block7.moe.dispatch.expert0 | 0.634 | 0.665 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert1 | 0.658 | 0.719 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert2 | 0.628 | 0.708 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert3 | 0.655 | 0.718 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert4 | 0.670 | 0.718 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert5 | 0.670 | 0.713 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert6 | 0.664 | 0.712 | 0.1 | 3 |
| fwd:block7.moe.dispatch.expert7 | 0.657 | 0.715 | 0.1 | 3 |
| fwd:block7.moe.shared | 0.348 | 0.373 | 0.1 | 3 |
| fwd:block8 | 6.159 | 6.401 | 1.2 | 2 |
| fwd:block8.ln1 | 0.086 | 0.095 | 0.0 | 3 |
| fwd:block8.attn.qkv | 0.184 | 0.208 | 0.0 | 3 |
| fwd:block8.attn.sdpa | 0.122 | 0.134 | 0.0 | 3 |
| fwd:block8.attn.proj | 0.092 | 0.119 | 0.0 | 3 |
| fwd:block8.ln2 | 0.061 | 0.073 | 0.0 | 3 |
| fwd:block8.moe.router | 0.296 | 0.344 | 0.1 | 3 |
| fwd:block8.moe.dispatch | 5.635 | 5.885 | 1.1 | 3 |
| fwd:block8.moe.dispatch.expert0 | 0.646 | 0.670 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert1 | 0.680 | 0.730 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert2 | 0.664 | 0.715 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert3 | 0.654 | 0.712 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert4 | 0.655 | 0.712 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert5 | 0.653 | 0.713 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert6 | 0.664 | 0.719 | 0.1 | 3 |
| fwd:block8.moe.dispatch.expert7 | 0.677 | 0.712 | 0.1 | 3 |
| fwd:block8.moe.shared | 0.348 | 0.364 | 0.1 | 3 |
| fwd:head+loss | 42.126 | 42.156 | 8.3 | 2 |
| bwd | 239.607 | 251.067 | 47.3 | 1 |
| bwd:head+loss | 48.154 | 48.167 | 9.5 | 2 |
| bwd:stack | 190.961 | 202.406 | 37.7 | 1 |
| bwd:block8 | 22.001 | 22.713 | 4.3 | 2 |
| bwd.invert:block8 | 6.423 | 6.688 | 1.3 | 3 |
| bwd.invert:block8.ln1 | 0.047 | 0.048 | 0.0 | 3 |
| bwd.invert:block8.attn.qkv | 0.050 | 0.051 | 0.0 | 3 |
| bwd.invert:block8.attn.sdpa | 0.082 | 0.083 | 0.0 | 3 |
| bwd.invert:block8.attn.proj | 0.037 | 0.038 | 0.0 | 3 |
| bwd.invert:block8.ln2 | 0.047 | 0.048 | 0.0 | 3 |
| bwd.invert:block8.moe.router | 0.066 | 0.067 | 0.0 | 3 |
| bwd.invert:block8.moe.dispatch | 5.447 | 5.695 | 1.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert0 | 1.001 | 1.075 | 0.2 | 3 |
| bwd.invert:block8.moe.dispatch.expert1 | 0.703 | 0.749 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert2 | 0.601 | 0.646 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert3 | 0.587 | 0.628 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert4 | 0.587 | 0.630 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert5 | 0.581 | 0.608 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert6 | 0.579 | 0.620 | 0.1 | 3 |
| bwd.invert:block8.moe.dispatch.expert7 | 0.575 | 0.617 | 0.1 | 3 |
| bwd.invert:block8.moe.shared | 0.337 | 0.361 | 0.1 | 3 |
| bwd.recompute:block8 | 6.965 | 7.215 | 1.4 | 3 |
| bwd.recompute:block8.ln1 | 0.114 | 0.127 | 0.0 | 3 |
| bwd.recompute:block8.attn.qkv | 0.223 | 0.254 | 0.0 | 3 |
| bwd.recompute:block8.attn.sdpa | 0.166 | 0.177 | 0.0 | 3 |
| bwd.recompute:block8.attn.proj | 0.123 | 0.157 | 0.0 | 3 |
| bwd.recompute:block8.ln2 | 0.079 | 0.093 | 0.0 | 3 |
| bwd.recompute:block8.moe.router | 0.285 | 0.318 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch | 5.252 | 5.455 | 1.0 | 3 |
| bwd.recompute:block8.moe.dispatch.expert0 | 0.617 | 0.651 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert1 | 0.616 | 0.648 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert2 | 0.613 | 0.659 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert3 | 0.611 | 0.642 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert4 | 0.613 | 0.654 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert5 | 0.609 | 0.648 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert6 | 0.612 | 0.643 | 0.1 | 3 |
| bwd.recompute:block8.moe.dispatch.expert7 | 0.611 | 0.648 | 0.1 | 3 |
| bwd.recompute:block8.moe.shared | 0.339 | 0.368 | 0.1 | 3 |
| bwd:block8.grad | 10.457 | 10.993 | 2.1 | 3 |
| bwd:block7 | 21.594 | 22.579 | 4.3 | 2 |
| bwd.invert:block7 | 6.537 | 6.928 | 1.3 | 3 |
| bwd.invert:block7.ln1 | 0.098 | 0.113 | 0.0 | 3 |
| bwd.invert:block7.attn.qkv | 0.215 | 0.253 | 0.0 | 3 |
| bwd.invert:block7.attn.sdpa | 0.133 | 0.146 | 0.0 | 3 |
| bwd.invert:block7.attn.proj | 0.105 | 0.139 | 0.0 | 3 |
| bwd.invert:block7.ln2 | 0.069 | 0.081 | 0.0 | 3 |
| bwd.invert:block7.moe.router | 0.246 | 0.279 | 0.0 | 3 |
| bwd.invert:block7.moe.dispatch | 4.912 | 5.134 | 1.0 | 3 |
| bwd.invert:block7.moe.dispatch.expert0 | 0.591 | 0.684 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert1 | 0.582 | 0.627 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert2 | 0.572 | 0.604 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert3 | 0.572 | 0.602 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert4 | 0.564 | 0.597 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert5 | 0.567 | 0.591 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert6 | 0.567 | 0.595 | 0.1 | 3 |
| bwd.invert:block7.moe.dispatch.expert7 | 0.565 | 0.596 | 0.1 | 3 |
| bwd.invert:block7.moe.shared | 0.332 | 0.354 | 0.1 | 3 |
| bwd.recompute:block7 | 6.853 | 7.214 | 1.4 | 3 |
| bwd.recompute:block7.ln1 | 0.098 | 0.110 | 0.0 | 3 |
| bwd.recompute:block7.attn.qkv | 0.218 | 0.242 | 0.0 | 3 |
| bwd.recompute:block7.attn.sdpa | 0.142 | 0.156 | 0.0 | 3 |
| bwd.recompute:block7.attn.proj | 0.112 | 0.140 | 0.0 | 3 |
| bwd.recompute:block7.ln2 | 0.072 | 0.088 | 0.0 | 3 |
| bwd.recompute:block7.moe.router | 0.258 | 0.289 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch | 5.152 | 5.354 | 1.0 | 3 |
| bwd.recompute:block7.moe.dispatch.expert0 | 0.602 | 0.641 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert1 | 0.608 | 0.641 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert2 | 0.601 | 0.636 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert3 | 0.603 | 0.646 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert4 | 0.605 | 0.636 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert5 | 0.601 | 0.630 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert6 | 0.602 | 0.639 | 0.1 | 3 |
| bwd.recompute:block7.moe.dispatch.expert7 | 0.605 | 0.636 | 0.1 | 3 |
| bwd.recompute:block7.moe.shared | 0.338 | 0.360 | 0.1 | 3 |
| bwd:block7.grad | 10.090 | 10.589 | 2.0 | 3 |
| bwd:block6 | 21.390 | 22.521 | 4.2 | 2 |
| bwd.invert:block6 | 6.447 | 6.894 | 1.3 | 3 |
| bwd.invert:block6.ln1 | 0.095 | 0.113 | 0.0 | 3 |
| bwd.invert:block6.attn.qkv | 0.201 | 0.235 | 0.0 | 3 |
| bwd.invert:block6.attn.sdpa | 0.131 | 0.146 | 0.0 | 3 |
| bwd.invert:block6.attn.proj | 0.104 | 0.139 | 0.0 | 3 |
| bwd.invert:block6.ln2 | 0.066 | 0.076 | 0.0 | 3 |
| bwd.invert:block6.moe.router | 0.236 | 0.276 | 0.0 | 3 |
| bwd.invert:block6.moe.dispatch | 4.872 | 5.129 | 1.0 | 3 |
| bwd.invert:block6.moe.dispatch.expert0 | 0.586 | 0.693 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert1 | 0.571 | 0.612 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert2 | 0.568 | 0.600 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert3 | 0.565 | 0.602 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert4 | 0.567 | 0.596 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert5 | 0.562 | 0.590 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert6 | 0.563 | 0.595 | 0.1 | 3 |
| bwd.invert:block6.moe.dispatch.expert7 | 0.561 | 0.590 | 0.1 | 3 |
| bwd.invert:block6.moe.shared | 0.332 | 0.351 | 0.1 | 3 |
| bwd.recompute:block6 | 6.772 | 7.209 | 1.3 | 3 |
| bwd.recompute:block6.ln1 | 0.096 | 0.109 | 0.0 | 3 |
| bwd.recompute:block6.attn.qkv | 0.208 | 0.233 | 0.0 | 3 |
| bwd.recompute:block6.attn.sdpa | 0.147 | 0.165 | 0.0 | 3 |
| bwd.recompute:block6.attn.proj | 0.114 | 0.147 | 0.0 | 3 |
| bwd.recompute:block6.ln2 | 0.070 | 0.080 | 0.0 | 3 |
| bwd.recompute:block6.moe.router | 0.251 | 0.283 | 0.0 | 3 |
| bwd.recompute:block6.moe.dispatch | 5.094 | 5.312 | 1.0 | 3 |
| bwd.recompute:block6.moe.dispatch.expert0 | 0.599 | 0.632 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert1 | 0.604 | 0.629 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert2 | 0.596 | 0.631 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert3 | 0.603 | 0.632 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert4 | 0.597 | 0.625 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert5 | 0.593 | 0.625 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert6 | 0.599 | 0.636 | 0.1 | 3 |
| bwd.recompute:block6.moe.dispatch.expert7 | 0.597 | 0.629 | 0.1 | 3 |
| bwd.recompute:block6.moe.shared | 0.339 | 0.365 | 0.1 | 3 |
| bwd:block6.grad | 10.269 | 10.824 | 2.0 | 3 |
| bwd:block5 | 21.236 | 22.642 | 4.2 | 2 |
| bwd.invert:block5 | 6.423 | 6.903 | 1.3 | 3 |
| bwd.invert:block5.ln1 | 0.096 | 0.112 | 0.0 | 3 |
| bwd.invert:block5.attn.qkv | 0.204 | 0.244 | 0.0 | 3 |
| bwd.invert:block5.attn.sdpa | 0.128 | 0.142 | 0.0 | 3 |
| bwd.invert:block5.attn.proj | 0.102 | 0.135 | 0.0 | 3 |
| bwd.invert:block5.ln2 | 0.066 | 0.077 | 0.0 | 3 |
| bwd.invert:block5.moe.router | 0.233 | 0.270 | 0.0 | 3 |
| bwd.invert:block5.moe.dispatch | 4.858 | 5.130 | 1.0 | 3 |
| bwd.invert:block5.moe.dispatch.expert0 | 0.589 | 0.692 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert1 | 0.577 | 0.633 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert2 | 0.564 | 0.598 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert3 | 0.569 | 0.597 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert4 | 0.565 | 0.603 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert5 | 0.562 | 0.590 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert6 | 0.560 | 0.599 | 0.1 | 3 |
| bwd.invert:block5.moe.dispatch.expert7 | 0.558 | 0.593 | 0.1 | 3 |
| bwd.invert:block5.moe.shared | 0.332 | 0.353 | 0.1 | 3 |
| bwd.recompute:block5 | 6.752 | 7.178 | 1.3 | 3 |
| bwd.recompute:block5.ln1 | 0.095 | 0.106 | 0.0 | 3 |
| bwd.recompute:block5.attn.qkv | 0.205 | 0.236 | 0.0 | 3 |
| bwd.recompute:block5.attn.sdpa | 0.146 | 0.165 | 0.0 | 3 |
| bwd.recompute:block5.attn.proj | 0.113 | 0.142 | 0.0 | 3 |
| bwd.recompute:block5.ln2 | 0.071 | 0.084 | 0.0 | 3 |
| bwd.recompute:block5.moe.router | 0.247 | 0.284 | 0.0 | 3 |
| bwd.recompute:block5.moe.dispatch | 5.094 | 5.310 | 1.0 | 3 |
| bwd.recompute:block5.moe.dispatch.expert0 | 0.599 | 0.628 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert1 | 0.601 | 0.644 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert2 | 0.597 | 0.629 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert3 | 0.599 | 0.631 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert4 | 0.597 | 0.630 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert5 | 0.596 | 0.626 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert6 | 0.594 | 0.626 | 0.1 | 3 |
| bwd.recompute:block5.moe.dispatch.expert7 | 0.595 | 0.630 | 0.1 | 3 |
| bwd.recompute:block5.moe.shared | 0.337 | 0.361 | 0.1 | 3 |
| bwd:block5.grad | 9.942 | 10.527 | 2.0 | 3 |
| bwd:block4 | 21.284 | 22.544 | 4.2 | 2 |
| bwd.invert:block4 | 6.394 | 6.853 | 1.3 | 3 |
| bwd.invert:block4.ln1 | 0.094 | 0.114 | 0.0 | 3 |
| bwd.invert:block4.attn.qkv | 0.202 | 0.233 | 0.0 | 3 |
| bwd.invert:block4.attn.sdpa | 0.126 | 0.140 | 0.0 | 3 |
| bwd.invert:block4.attn.proj | 0.098 | 0.130 | 0.0 | 3 |
| bwd.invert:block4.ln2 | 0.063 | 0.075 | 0.0 | 3 |
| bwd.invert:block4.moe.router | 0.232 | 0.273 | 0.0 | 3 |
| bwd.invert:block4.moe.dispatch | 4.863 | 5.122 | 1.0 | 3 |
| bwd.invert:block4.moe.dispatch.expert0 | 0.584 | 0.686 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert1 | 0.575 | 0.616 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert2 | 0.565 | 0.593 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert3 | 0.564 | 0.596 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert4 | 0.561 | 0.591 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert5 | 0.565 | 0.600 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert6 | 0.565 | 0.600 | 0.1 | 3 |
| bwd.invert:block4.moe.dispatch.expert7 | 0.558 | 0.596 | 0.1 | 3 |
| bwd.invert:block4.moe.shared | 0.331 | 0.356 | 0.1 | 3 |
| bwd.recompute:block4 | 6.742 | 7.153 | 1.3 | 3 |
| bwd.recompute:block4.ln1 | 0.095 | 0.111 | 0.0 | 3 |
| bwd.recompute:block4.attn.qkv | 0.206 | 0.228 | 0.0 | 3 |
| bwd.recompute:block4.attn.sdpa | 0.146 | 0.168 | 0.0 | 3 |
| bwd.recompute:block4.attn.proj | 0.113 | 0.146 | 0.0 | 3 |
| bwd.recompute:block4.ln2 | 0.070 | 0.083 | 0.0 | 3 |
| bwd.recompute:block4.moe.router | 0.248 | 0.281 | 0.0 | 3 |
| bwd.recompute:block4.moe.dispatch | 5.085 | 5.291 | 1.0 | 3 |
| bwd.recompute:block4.moe.dispatch.expert0 | 0.598 | 0.636 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert1 | 0.597 | 0.631 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert2 | 0.600 | 0.630 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert3 | 0.596 | 0.632 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert4 | 0.590 | 0.622 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert5 | 0.593 | 0.623 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert6 | 0.592 | 0.623 | 0.1 | 3 |
| bwd.recompute:block4.moe.dispatch.expert7 | 0.596 | 0.633 | 0.1 | 3 |
| bwd.recompute:block4.moe.shared | 0.337 | 0.361 | 0.1 | 3 |
| bwd:block4.grad | 10.084 | 10.709 | 2.0 | 3 |
| bwd:block3 | 21.065 | 22.440 | 4.2 | 2 |
| bwd.invert:block3 | 6.371 | 6.842 | 1.3 | 3 |
| bwd.invert:block3.ln1 | 0.094 | 0.112 | 0.0 | 3 |
| bwd.invert:block3.attn.qkv | 0.199 | 0.233 | 0.0 | 3 |
| bwd.invert:block3.attn.sdpa | 0.124 | 0.138 | 0.0 | 3 |
| bwd.invert:block3.attn.proj | 0.097 | 0.133 | 0.0 | 3 |
| bwd.invert:block3.ln2 | 0.066 | 0.082 | 0.0 | 3 |
| bwd.invert:block3.moe.router | 0.234 | 0.266 | 0.0 | 3 |
| bwd.invert:block3.moe.dispatch | 4.863 | 5.104 | 1.0 | 3 |
| bwd.invert:block3.moe.dispatch.expert0 | 0.586 | 0.691 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert1 | 0.572 | 0.620 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert2 | 0.569 | 0.601 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert3 | 0.560 | 0.591 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert4 | 0.563 | 0.592 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert5 | 0.560 | 0.589 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert6 | 0.559 | 0.588 | 0.1 | 3 |
| bwd.invert:block3.moe.dispatch.expert7 | 0.563 | 0.589 | 0.1 | 3 |
| bwd.invert:block3.moe.shared | 0.332 | 0.352 | 0.1 | 3 |
| bwd.recompute:block3 | 6.745 | 7.159 | 1.3 | 3 |
| bwd.recompute:block3.ln1 | 0.094 | 0.108 | 0.0 | 3 |
| bwd.recompute:block3.attn.qkv | 0.206 | 0.235 | 0.0 | 3 |
| bwd.recompute:block3.attn.sdpa | 0.145 | 0.164 | 0.0 | 3 |
| bwd.recompute:block3.attn.proj | 0.114 | 0.139 | 0.0 | 3 |
| bwd.recompute:block3.ln2 | 0.070 | 0.080 | 0.0 | 3 |
| bwd.recompute:block3.moe.router | 0.247 | 0.282 | 0.0 | 3 |
| bwd.recompute:block3.moe.dispatch | 5.092 | 5.296 | 1.0 | 3 |
| bwd.recompute:block3.moe.dispatch.expert0 | 0.595 | 0.629 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert1 | 0.604 | 0.641 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert2 | 0.594 | 0.631 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert3 | 0.593 | 0.622 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert4 | 0.599 | 0.629 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert5 | 0.589 | 0.622 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert6 | 0.597 | 0.629 | 0.1 | 3 |
| bwd.recompute:block3.moe.dispatch.expert7 | 0.596 | 0.633 | 0.1 | 3 |
| bwd.recompute:block3.moe.shared | 0.337 | 0.357 | 0.1 | 3 |
| bwd:block3.grad | 9.885 | 10.518 | 2.0 | 3 |
| bwd:block2 | 21.113 | 22.316 | 4.2 | 2 |
| bwd.invert:block2 | 6.359 | 6.852 | 1.3 | 3 |
| bwd.invert:block2.ln1 | 0.094 | 0.112 | 0.0 | 3 |
| bwd.invert:block2.attn.qkv | 0.197 | 0.229 | 0.0 | 3 |
| bwd.invert:block2.attn.sdpa | 0.125 | 0.138 | 0.0 | 3 |
| bwd.invert:block2.attn.proj | 0.099 | 0.131 | 0.0 | 3 |
| bwd.invert:block2.ln2 | 0.064 | 0.078 | 0.0 | 3 |
| bwd.invert:block2.moe.router | 0.238 | 0.276 | 0.0 | 3 |
| bwd.invert:block2.moe.dispatch | 4.865 | 5.088 | 1.0 | 3 |
| bwd.invert:block2.moe.dispatch.expert0 | 0.585 | 0.688 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert1 | 0.571 | 0.622 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert2 | 0.569 | 0.602 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert3 | 0.564 | 0.592 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert4 | 0.563 | 0.593 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert5 | 0.558 | 0.588 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert6 | 0.560 | 0.593 | 0.1 | 3 |
| bwd.invert:block2.moe.dispatch.expert7 | 0.563 | 0.590 | 0.1 | 3 |
| bwd.invert:block2.moe.shared | 0.331 | 0.351 | 0.1 | 3 |
| bwd.recompute:block2 | 6.709 | 7.222 | 1.3 | 3 |
| bwd.recompute:block2.ln1 | 0.094 | 0.107 | 0.0 | 3 |
| bwd.recompute:block2.attn.qkv | 0.205 | 0.232 | 0.0 | 3 |
| bwd.recompute:block2.attn.sdpa | 0.145 | 0.164 | 0.0 | 3 |
| bwd.recompute:block2.attn.proj | 0.113 | 0.141 | 0.0 | 3 |
| bwd.recompute:block2.ln2 | 0.069 | 0.080 | 0.0 | 3 |
| bwd.recompute:block2.moe.router | 0.243 | 0.282 | 0.0 | 3 |
| bwd.recompute:block2.moe.dispatch | 5.082 | 5.312 | 1.0 | 3 |
| bwd.recompute:block2.moe.dispatch.expert0 | 0.595 | 0.629 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert1 | 0.600 | 0.627 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert2 | 0.598 | 0.631 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert3 | 0.598 | 0.633 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert4 | 0.591 | 0.620 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert5 | 0.593 | 0.633 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert6 | 0.596 | 0.631 | 0.1 | 3 |
| bwd.recompute:block2.moe.dispatch.expert7 | 0.591 | 0.626 | 0.1 | 3 |
| bwd.recompute:block2.moe.shared | 0.336 | 0.355 | 0.1 | 3 |
| bwd:block2.grad | 9.946 | 10.578 | 2.0 | 3 |
| bwd:block1 | 20.954 | 22.049 | 4.1 | 2 |
| bwd.invert:block1 | 6.334 | 6.783 | 1.3 | 3 |
| bwd.invert:block1.ln1 | 0.093 | 0.112 | 0.0 | 3 |
| bwd.invert:block1.attn.qkv | 0.198 | 0.226 | 0.0 | 3 |
| bwd.invert:block1.attn.sdpa | 0.124 | 0.137 | 0.0 | 3 |
| bwd.invert:block1.attn.proj | 0.098 | 0.127 | 0.0 | 3 |
| bwd.invert:block1.ln2 | 0.062 | 0.074 | 0.0 | 3 |
| bwd.invert:block1.moe.router | 0.238 | 0.271 | 0.0 | 3 |
| bwd.invert:block1.moe.dispatch | 4.848 | 5.081 | 1.0 | 3 |
| bwd.invert:block1.moe.dispatch.expert0 | 0.589 | 0.674 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert1 | 0.571 | 0.615 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert2 | 0.566 | 0.595 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert3 | 0.556 | 0.587 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert4 | 0.563 | 0.589 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert5 | 0.560 | 0.581 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert6 | 0.560 | 0.592 | 0.1 | 3 |
| bwd.invert:block1.moe.dispatch.expert7 | 0.559 | 0.592 | 0.1 | 3 |
| bwd.invert:block1.moe.shared | 0.331 | 0.351 | 0.1 | 3 |
| bwd.recompute:block1 | 6.704 | 7.154 | 1.3 | 3 |
| bwd.recompute:block1.ln1 | 0.094 | 0.107 | 0.0 | 3 |
| bwd.recompute:block1.attn.qkv | 0.208 | 0.232 | 0.0 | 3 |
| bwd.recompute:block1.attn.sdpa | 0.145 | 0.168 | 0.0 | 3 |
| bwd.recompute:block1.attn.proj | 0.112 | 0.139 | 0.0 | 3 |
| bwd.recompute:block1.ln2 | 0.069 | 0.078 | 0.0 | 3 |
| bwd.recompute:block1.moe.router | 0.240 | 0.277 | 0.0 | 3 |
| bwd.recompute:block1.moe.dispatch | 5.062 | 5.300 | 1.0 | 3 |
| bwd.recompute:block1.moe.dispatch.expert0 | 0.597 | 0.621 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert1 | 0.598 | 0.624 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert2 | 0.594 | 0.624 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert3 | 0.596 | 0.629 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert4 | 0.591 | 0.620 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert5 | 0.591 | 0.624 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert6 | 0.592 | 0.624 | 0.1 | 3 |
| bwd.recompute:block1.moe.dispatch.expert7 | 0.592 | 0.621 | 0.1 | 3 |
| bwd.recompute:block1.moe.shared | 0.335 | 0.356 | 0.1 | 3 |
| bwd:block1.grad | 9.820 | 10.427 | 1.9 | 3 |
| bwd:block0 | 20.882 | 22.059 | 4.1 | 2 |
| bwd.invert:block0 | 6.355 | 6.762 | 1.3 | 3 |
| bwd.invert:block0.ln1 | 0.093 | 0.110 | 0.0 | 3 |
| bwd.invert:block0.attn.qkv | 0.201 | 0.231 | 0.0 | 3 |
| bwd.invert:block0.attn.sdpa | 0.124 | 0.137 | 0.0 | 3 |
| bwd.invert:block0.attn.proj | 0.095 | 0.123 | 0.0 | 3 |
| bwd.invert:block0.ln2 | 0.065 | 0.073 | 0.0 | 3 |
| bwd.invert:block0.moe.router | 0.236 | 0.263 | 0.0 | 3 |
| bwd.invert:block0.moe.dispatch | 4.838 | 5.062 | 1.0 | 3 |
| bwd.invert:block0.moe.dispatch.expert0 | 0.580 | 0.669 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert1 | 0.574 | 0.613 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert2 | 0.563 | 0.594 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert3 | 0.561 | 0.588 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert4 | 0.564 | 0.587 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert5 | 0.556 | 0.581 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert6 | 0.563 | 0.586 | 0.1 | 3 |
| bwd.invert:block0.moe.dispatch.expert7 | 0.552 | 0.581 | 0.1 | 3 |
| bwd.invert:block0.moe.shared | 0.331 | 0.354 | 0.1 | 3 |
| bwd.recompute:block0 | 6.718 | 7.065 | 1.3 | 3 |
| bwd.recompute:block0.ln1 | 0.094 | 0.109 | 0.0 | 3 |
| bwd.recompute:block0.attn.qkv | 0.201 | 0.223 | 0.0 | 3 |
| bwd.recompute:block0.attn.sdpa | 0.146 | 0.166 | 0.0 | 3 |
| bwd.recompute:block0.attn.proj | 0.117 | 0.144 | 0.0 | 3 |
| bwd.recompute:block0.ln2 | 0.069 | 0.082 | 0.0 | 3 |
| bwd.recompute:block0.moe.router | 0.245 | 0.278 | 0.0 | 3 |
| bwd.recompute:block0.moe.dispatch | 5.066 | 5.235 | 1.0 | 3 |
| bwd.recompute:block0.moe.dispatch.expert0 | 0.598 | 0.627 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert1 | 0.595 | 0.620 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert2 | 0.599 | 0.631 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert3 | 0.596 | 0.623 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert4 | 0.593 | 0.621 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert5 | 0.596 | 0.628 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert6 | 0.587 | 0.622 | 0.1 | 3 |
| bwd.recompute:block0.moe.dispatch.expert7 | 0.591 | 0.615 | 0.1 | 3 |
| bwd.recompute:block0.moe.shared | 0.335 | 0.356 | 0.1 | 3 |
| bwd:block0.grad | 9.874 | 10.435 | 1.9 | 3 |
| bwd:embed | 0.484 | 0.505 | 0.1 | 2 |
| opt | 160.840 | 164.299 | 31.7 | 1 |
| opt:opt.clip | 4.445 | 4.675 | 0.9 | 2 |
| opt:opt.muon | 152.699 | 155.992 | 30.1 | 2 |
| opt:opt.muon.ns | 145.917 | 149.190 | 28.8 | 3 |
| opt:opt.adamw | 1.658 | 1.708 | 0.3 | 2 |
| opt:opt.moe_bias | 0.862 | 0.883 | 0.2 | 3 |
| opt:opt.zero_grad | 1.076 | 1.128 | 0.2 | 3 |

## Time by part type (sum over layers)

| part type | median ms sum | % of step |
| :--- | ---: | ---: |
| bwd | 239.607 | 47.3 |
| bwd:block* | 191.517 | 37.8 |
| bwd:stack | 190.961 | 37.7 |
| opt | 160.840 | 31.7 |
| opt:opt.muon | 152.699 | 30.1 |
| opt:opt.muon.ns | 145.917 | 28.8 |
| fwd | 102.342 | 20.2 |
| bwd:block*.grad | 90.368 | 17.8 |
| bwd.recompute:block* | 60.960 | 12.0 |
| bwd.invert:block* | 57.642 | 11.4 |
| fwd:stack | 55.685 | 11.0 |
| fwd:block* | 55.291 | 10.9 |
| fwd:block*.moe.dispatch | 50.606 | 10.0 |
| bwd:head+loss | 48.154 | 9.5 |
| bwd.recompute:block*.moe.dispatch | 45.980 | 9.1 |
| bwd.invert:block*.moe.dispatch | 44.365 | 8.8 |
| fwd:head+loss | 42.126 | 8.3 |
| fwd:block*.moe.dispatch.expert1 | 6.096 | 1.2 |
| fwd:block*.moe.dispatch.expert3 | 6.025 | 1.2 |
| fwd:block*.moe.dispatch.expert2 | 6.012 | 1.2 |
| fwd:block*.moe.dispatch.expert4 | 6.004 | 1.2 |
| fwd:block*.moe.dispatch.expert5 | 5.991 | 1.2 |
| fwd:block*.moe.dispatch.expert6 | 5.964 | 1.2 |
| fwd:block*.moe.dispatch.expert7 | 5.924 | 1.2 |
| fwd:block*.moe.dispatch.expert0 | 5.744 | 1.1 |
| bwd.invert:block*.moe.dispatch.expert0 | 5.692 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert1 | 5.423 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert0 | 5.401 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert3 | 5.396 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert2 | 5.391 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert4 | 5.375 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert7 | 5.374 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert6 | 5.371 | 1.1 |
| bwd.recompute:block*.moe.dispatch.expert5 | 5.361 | 1.1 |
| bwd.invert:block*.moe.dispatch.expert1 | 5.298 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert2 | 5.137 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert3 | 5.100 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert4 | 5.097 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert6 | 5.076 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert5 | 5.071 | 1.0 |
| bwd.invert:block*.moe.dispatch.expert7 | 5.054 | 1.0 |
| opt:opt.clip | 4.445 | 0.9 |
| fwd:embed | 4.360 | 0.9 |
| fwd:embed.ke | 4.308 | 0.9 |
| fwd:block*.moe.shared | 3.131 | 0.6 |
| bwd.recompute:block*.moe.shared | 3.033 | 0.6 |
| bwd.invert:block*.moe.shared | 2.988 | 0.6 |
| fwd:block*.moe.router | 2.550 | 0.5 |
| bwd.recompute:block*.moe.router | 2.264 | 0.4 |
| bwd.invert:block*.moe.router | 1.959 | 0.4 |
| bwd.recompute:block*.attn.qkv | 1.880 | 0.4 |
| bwd.invert:block*.attn.qkv | 1.666 | 0.3 |
| opt:opt.adamw | 1.658 | 0.3 |
| fwd:block*.attn.qkv | 1.542 | 0.3 |
| bwd.recompute:block*.attn.sdpa | 1.331 | 0.3 |
| bwd.invert:block*.attn.sdpa | 1.097 | 0.2 |
| fwd:block*.attn.sdpa | 1.085 | 0.2 |
| opt:opt.zero_grad | 1.076 | 0.2 |
| bwd.recompute:block*.attn.proj | 1.029 | 0.2 |
| bwd.recompute:block*.ln1 | 0.875 | 0.2 |
| opt:opt.moe_bias | 0.862 | 0.2 |
| data | 0.856 | 0.2 |
| bwd.invert:block*.attn.proj | 0.836 | 0.2 |
| bwd.invert:block*.ln1 | 0.806 | 0.2 |
| fwd:block*.attn.proj | 0.801 | 0.2 |
| fwd:block*.ln1 | 0.742 | 0.1 |
| bwd.recompute:block*.ln2 | 0.636 | 0.1 |
| bwd.invert:block*.ln2 | 0.567 | 0.1 |
| fwd:block*.ln2 | 0.545 | 0.1 |
| bwd:embed | 0.484 | 0.1 |

## Five slowest leaf parts

1. `opt:opt.muon.ns` — 145.917 ms (28.8% of step)
2. `bwd:block8.grad` — 10.457 ms (2.1% of step)
3. `bwd:block6.grad` — 10.269 ms (2.0% of step)
4. `bwd:block7.grad` — 10.090 ms (2.0% of step)
5. `bwd:block4.grad` — 10.084 ms (2.0% of step)
