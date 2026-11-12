# Decisions for config v1

Gate 2 proposal, 12 Nov 2026. TSAI signs this on 14 Nov. The numbers are in `experiments/results_v1.md`. No arm is named a winner. An arm with no bits per byte keeps the config v0 default. Model sizes are not copied in from the test-size line.

| Setting | Decision | Why |
|---|---|---|
| optim.lr | null | EXP-1 has a whole-file val/bpb table. The three-group mean, the code guard, and the Indic guard are not in it, so the plan rule does not name a winner. |
| optim.name | adamw | EXP-2 has no held-out bits per byte. |
| moe.n_expert | null | EXP-3 has no bits per byte. The test-size count is not copied in. |
| shared expert | unset | EXP-3 has no bits per byte. The test-size line is not copied in. |
| attention.impl | eager | The attention runs have no official bits per byte. RoPE and the window are not copied in. |
| embedding.ke2_output_dim | null | TSAI decides the output head. Every test model uses the dense untied head. |
| model.n_layer, model.d_model, model.n_head, model.d_ff, moe.top_k, data.seq_len | null | These stay empty. The T1, T2, and T3 lines are test sizes, not this file. |
| precision | null | Production precision is not chosen. |

EXP-4 is week 3. It is not in this file.

EXP-2, filed in pull request 354, uses AdamW 0.001 and Muon 0.01 with the comparison marked not final. Those rates are not copied into config v1.
