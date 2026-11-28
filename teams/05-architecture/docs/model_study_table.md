# Design task 1 — study table (G5, Lab 5)

Prepared by `tanmays369`. **Approach note, published before any build.** Companion to `model_designs_v1.md`.

Sources: the `config.json` of each model on Hugging Face, read 28 Nov 2026.
Parameter counts are computed from the configs by `../scripts/model_study_table.py`, not copied from model cards,
so they can differ in the last digit.

**Measured vs estimated.** All parameter counts here are exact arithmetic from `config.json`. Nothing in this file
is an estimate. No memory or loss numbers appear in this table.

## 1. Study table

| Model | Layers | width | heads | KV | routed E | top-k | expert width | shared width | vocab | total B | active B | active % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-30B-A3B | 48 | 2048 | 32 | 4 | 128 | 8 | 768 | 0 | 151,936 | 30.21 | 3.03 | 10.0 |
| Qwen3-235B-A22B | 94 | 4096 | 64 | 4 | 128 | 8 | 1536 | 0 | 151,936 | 234.42 | 21.52 | 9.2 |
| Qwen3-Next-80B-A3B | 48 | 2048 | 16 | 2 | 512 | 10 | 512 | 512 | 151,936 | 78.53 | 2.73 | 3.5 |
| DeepSeek-V3 | 61 | 7168 | 128 | 128 | 256 | 8 | 2048 | 1 | 129,280 | 671.12 | 37.64 | 5.6 |
| DeepSeek-V3.2 | 61 | 7168 | 128 | 128 | 256 | 8 | 2048 | 1 | 129,280 | 671.12 | 37.64 | 5.6 |
| GLM-4.5 | 92 | 5120 | 96 | 8 | 160 | 8 | 1536 | 1 | 151,552 | 351.95 | 32.78 | 9.3 |
| MiniMax-M2 | 62 | 3072 | 48 | 8 | 256 | 8 | 1536 | 0 | 200,064 | 228.03 | 10.37 | 4.5 |
| Kimi-K2-Instruct | 61 | 7168 | 64 | 64 | 384 | 8 | 2048 | 1 | 163,840 | 1031.44 | 37.89 | 3.7 |

**Validation of the parameter arithmetic** (computed vs the published figure):

| Model | computed total | published | computed active | published |
|---|---:|---:|---:|---:|
| Qwen3-30B-A3B | 30.21 B | ~30 B | 3.03 B | ~3 B |
| Qwen3-235B-A22B | 234.42 B | ~235 B | 21.52 B | ~22 B |
| DeepSeek-V3 | 671.12 B | 671 B | 37.64 B | 37 B |
| GLM-4.5 | 351.95 B | ~355 B | 32.78 B | ~32 B |
| MiniMax-M2 | 228.03 B | ~230 B | 10.37 B | ~10 B |

All within rounding, so the formulas in §4 are sound.

## 2. Attention and context

| Model | attention | Q/KV heads | head dim | rope theta | max positions (config) | dense-prefix layers |
|---|---|---|---:|---:|---:|---:|
| Qwen3-30B-A3B | GQA | 32 / 4 | 128 | 1e6 | 40,960 | 0 |
| Qwen3-235B-A22B | GQA | 64 / 4 | 128 | 1e6 | 40,960 | 0 |
| Qwen3-Next-80B-A3B | hybrid linear + full | 16 / 2 | 256 | 1e7 | 262,144 | 0 |
| DeepSeek-V3 / V3.2 | MLA | 128 / 128 | — | 1e4 | 163,840 | 3 |
| GLM-4.5 | GQA | 96 / 8 | 128 | 1e6 | 131,072 | 3 |
| MiniMax-M2 | GQA | 48 / 8 | 128 | 5e6 | 196,608 | 0 |
| Kimi-K2-Instruct | MLA | 64 / 64 | — | 5e4 | 131,072 | 1 |

Two patterns matter for our design, and one caveat:

1. **The three highest-active-ratio models (9.2–10.0%) all use GQA.** At the low end, 2 of 3 use MLA or hybrid. But **MiniMax-M2 is a clear counter-example**: 4.5% active with plain GQA (48 Q / 8 KV heads, head dim 128 = 2,048 KV elements per token). So low active ratio does *not* force MLA; it only correlates.
2. **Only DeepSeek-V3/V3.2, GLM-4.5 and Kimi-K2 use a dense prefix.** The other four are pure MoE at every layer.
3. **KV cost differs by an order of magnitude.** Per token per layer: GQA models here 1,024–2,048 elements, Kimi-K2 (MLA) 16,384, DeepSeek-V3 (MLA) 32,768 — MLA trades a larger stored latent for a much smaller *attention* cost. Comparing them by stored size alone is misleading, which is why the attention choice in task 2 must be justified by measured decode cost, not by KV bytes.

## 3. The critical-depth problem (a finding, not a table entry)

The brief says to use "the critical-depth rule of the Depth Delusion paper, arXiv 2601.20994". The paper is real and gives:

- power form: `D_crit ∝ W^0.44` (its eq. 4)
- practical fit: `D_crit ≈ 2.43 · ln(W)`, stated as valid for `W ∈ [256, 1536]`, and the paper **verifies nothing above 1536 width** (its largest model is 7B at width 4096 but the D_crit fit is drawn from the 256–1536 range).

Applying both to the widths in the table:

| Model | width | L | D_crit (W^0.44) | D_crit (2.43·lnW) | L − D_crit(pow) |
|---|---:|---:|---:|---:|---:|
| Qwen3-30B-A3B | 2048 | 48 | 29 | 19 | **+19** |
| Qwen3-235B-A22B | 4096 | 94 | 39 | 20 | **+55** |
| Qwen3-Next-80B | 2048 | 48 | 29 | 19 | **+19** |
| DeepSeek-V3 | 7168 | 61 | 50 | 22 | **+11** |
| GLM-4.5 | 5120 | 92 | 43 | 21 | **+49** |
| MiniMax-M2 | 3072 | 62 | 34 | 20 | **+28** |
| Kimi-K2 | 7168 | 61 | 50 | 22 | **+11** |

Three conclusions, and they change how we should use the rule:

1. **The two forms disagree by 50–60% at our widths** (29 vs 19 at W=2048; 50 vs 22 at W=7168). They only agree inside the paper's fitted range. Any design that quotes "critical depth" must say which form it used.
2. **Every production MoE is deeper than D_crit.** If D_crit were a hard ceiling at these widths, all seven models would be badly over-deep. Two explanations fit the data: the law does not extrapolate past W≈1536, or **an MoE layer is not equivalent to a dense layer** — the paper's grid was dense, and a sparse layer with k of E experts carries far less signal per layer. The second is more likely and is the interesting hypothesis.
3. **Therefore the rule cannot be the primary basis for our design.** It can bound the *dense* baseline and it gives a sanity ceiling, but for MoE we should state depth in terms of D_crit measured on the *dense* model of the same width, then record the MoE depth as a multiple of it with the reasoning. Presenting `D_crit ∝ W^0.44` as if it settled our layer count would be wrong, and a reviewer who reads the paper will catch it.

**What I will do in task 2:** run the D_crit formula for the *dense* equivalent of each design, state the MoE depth as a deliberate multiple with justification (expert count, active ratio, KV budget), and give both D_crit values so the assumption is visible.

## 4. Formulas used (so every number is reproducible)

```
embedding        = V · d
attention/layer  = d·h_d·n_h  +  2·d·h_d·n_kv  +  d·h_d·n_h      (q, k+v, o)
dense FFN/layer  = 3·d·d_ff                                        (gate, up, down)
expert FFN       = 3·d·d_expert  per expert, per MoE layer
shared experts   = n_shared · 3·d·d_shared
total            = emb + L·attn + n_dense·3·d·d_ff + n_moe·E·3·d·d_ex + shared
active           = emb + L·attn + n_dense·3·d·d_ff + n_moe·k·3·d·d_ex + shared
```

Reproduce with `../scripts/model_study_table.py <configs-dir>` (the script fetches nothing; download each
`config.json` into a directory first, the command is in the script header). No published number is copied except as a cross-check in §1.

## 5. What this table means for our two designs

Constraints that fall out of the data:

| | our 30B, 8–10% active | our 100B, 2–3% active |
|---|---|---|
| Closest reference | Qwen3-30B-A3B (10.0%), GLM-4.5 (9.3%), Qwen3-235B (9.2%) | Qwen3-Next-80B (3.5%), Kimi-K2 (3.7%), MiniMax-M2 (4.5%), DeepSeek-V3 (5.6%) |
| Attention | GQA is what every model in this band uses | **no firm pattern** — GQA (MiniMax), MLA (Kimi-K2) and hybrid (Qwen3-Next) all appear; decide on measured decode cost |
| Expert count | 128 routed, 8 active (both Qwen3 models); GLM-4.5 uses 160 | 256 (DeepSeek, MiniMax), 384 (Kimi-K2), 512 (Qwen3-Next) routed; 8–10 active |
| Dense prefix | optional (3 of 7 use one) | optional |
| Depth | cannot lean on D_crit (§3) | same |

Task 2 will fix numbers against these constraints and state the arithmetic for experts-per-GPU on 8×80 GB.
