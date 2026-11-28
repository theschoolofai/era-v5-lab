# G5 design task 2 — two sparse model designs

`tanmays369`, 28 Nov 2026. **Approach note, published before the build**, as TSAI asked for on #890.

Companion to `model_study_table.md` (§ numbers there are the reference set this builds on).

**What is measured and what is estimated.** Every parameter count in this note is *computed* from a model's
`config.json` by `../scripts/model_study_table.py` — those are exact arithmetic, not estimates. Every memory figure
is *estimated* from a stated sharding formula (`../scripts/model_design_search.py`) with a 20 GB activation
reserve; no memory number here has been measured on a GPU. No loss number exists for either design — nothing has
been trained.

**Status:** parameter budget and feasibility only. The shape claims in §2 are falsifiable by the 49M–100M test in
design task 6, which has not been run.

Every number below is computed from the formulas in §4 by `../scripts/model_design_search.py`.
Nothing is copied from a model card.

**Measured vs estimated.** Parameter counts: computed exactly from `config.json`. Memory figures: estimated from the
sharding formula with a 20 GB activation reserve — **none measured on a GPU**. Loss: none — nothing trained.

---

## 1. The two hard constraints, stated first

**Constraint 1 — the stated hardware does not train the stated model.** The brief's planning assumption is
"one node, 8 GPUs with 80 GB each". With full ZeRO-3 sharding, bf16 weights and gradients, and Muon's 1 buffer
(4 B/param):

| Model | weights/GPU | grads/GPU | optimizer/GPU | + 20 GB activations | Fits 80 GB? |
|---|---:|---:|---:|---:|---|
| 30 B | 7.5 | 7.5 | 15.1 | **50.2 GB** | ✅ yes |
| 100 B | 25.0 | 25.0 | 50.0 | **120.0 GB** | ❌ **no** |

**A 100B model does not fit on 8×80 GB with the optimizer resident.** It fits only if the optimizer state is
offloaded to host memory (weights + grads on GPU = 70 GB incl. activations, and **401 GB of CPU RAM** for Muon
state; 802 GB if AdamW). That is a real requirement someone must confirm, not an implementation detail.

Maximum model that fits on the node *without* offload, Muon, 20 GB activations: **≈60 B** (60 B → 80.0 GB exactly).

**Constraint 2 — 100 B at 2–3 % active has less compute per token than 30 B at 10 %.**
100 B × 2–3 % = **2.0–3.0 B active**; 30 B × 10 % = **3.0 B active**. Design (b) is therefore *not* "a bigger
model" in the compute sense — it is the same per-token cost with 3× the memory. Its only justification is
**stored capacity** (more knowledge at equal FLOPs). That is a legitimate MoE argument, but it must be stated,
because a reviewer will otherwise read (b) as the more expensive model.

---

## 2. Design (a) — ~30 B at 8–10 % active

### The obvious candidate is a copy, so I rejected it

The parameter sweep's only combination that lands exactly on 30 B / 8–10 % with 8-GPU-divisible experts is:
`d=2048, L=48, E=128, k=8, d_ex=768` → 30.17 B / 2.99 B (9.9 %).

That is **Qwen3-30B-A3B to the decimal** (30.21 B / 3.03 B, 10.0 %). Reproducing an existing model is not a
design, so the recommendation is deliberately shaped differently.

### Recommended: **A1 — wider and shallower**

| Field | Value |
|---|---|
| layers | **32** |
| width | **3072** |
| attention | GQA, 24 Q / 4 KV heads, head dim 128 |
| routed experts | **128** (16 per GPU) |
| active experts (top-k) | **8** |
| expert width | 768 |
| shared experts | 0 |
| vocab | 131,072 (p1536) |
| **total / active** | **30.10 B / 2.92 B (9.7 %)** |
| D_crit at W=3072 | 34 → **L/D_crit = 0.93** (just inside) |
| memory/GPU | **50.1 GB** (optimizer resident) |

**Why this shape and not Qwen3's:** the Depth Delusion paper's central result is that width should grow ~2.8×
faster than depth (`D* ∝ C^0.12`, `W* ∝ C^0.34`). At equal parameter budget, holding Qwen3's 48 layers at
`d=2048` sits at `L/D_crit = 48/29 = 1.66`, i.e. **66 % past the critical depth**. A1 sits at **0.93** — inside
it. If the paper's finding holds at our scale, A1 should reach a lower loss for the same parameters; if it does
not, that is a publishable negative result and the brief explicitly asks for those.

**Two alternatives, if A1 fails a smoke test:**

| | shape | total / active | act % | D_crit | L/D_crit | mem/GPU | what it tests |
|---|---|---|---|---|---|---|---|
| **A2** | d=3072, L=32, E=64, k=4, d_ex=1536 | 30.10 B / 2.92 B | 9.7 | 34 | 0.93 | 50.1 GB | fewer, fatter experts at the same budget |
| **A3** | d=2560, L=40, E=128, k=8, d_ex=768 | 31.16 B / 2.85 B | 9.2 | 32 | 1.27 | 51.2 GB | a middle point between A1 and Qwen3's shape |

**Experts per GPU (constraint: expert count divides evenly over 8):**
`E=64 → 8/GPU`, `E=96 → 12`, `E=128 → 16`, `E=192 → 24`, `E=256 → 32`, `E=384 → 48`, `E=512 → 64`. All three
designs use E ∈ {64, 128}, both divisible.

---

## 3. Design (b) — ~100 B at 2–3 % active

### Recommendation: **B3**, and it needs optimizer offload

| Field | Value |
|---|---|
| layers | **40** |
| width | **4096** |
| attention | GQA, 64 Q / 8 KV heads, head dim 128 |
| routed experts | **256** (32 per GPU) |
| active experts (top-k) | **6** |
| expert width | 768 |
| shared experts | 0 |
| vocab | 131,072 |
| **total / active** | **100.19 B / 5.82 B (5.8 %)** |
| D_crit at W=4096 | 39 → **L/D_crit = 1.03** |
| memory/GPU | **70.1 GB with optimizer offloaded**; 120.2 GB with it resident ❌ |
| CPU RAM for optimizer | **401 GB** |

### The brief's 2–3 % cannot be met at 100 B without a different trade

Every 100 B combination I could build with this parameterisation lands at **3.6–6.4 % active**, never inside
2–3 %. The reason is arithmetic: to reach 100 B total at 2.5 % the model needs **2.5 B active**, and with
`d=4096` the embedding + attention alone contribute ~1.0 B of that, leaving very little for experts. Reaching
2–3 % at 100 B requires either a much narrower model with far more experts, or counting the embedding as
inactive.

**So design (b) is presented at 5.8 % active, with the reason stated.** If 2–3 % is mandatory, the honest
alternative is the Qwen3-Next shape (d=2048, 512 experts, k=10 → 78.5 B / 2.73 B = 3.5 %), which is closer to
the target but is again a copy of an existing model.

| | shape | total / active | act % | D_crit | L/D_crit | mem w/ offload | CPU RAM |
|---|---|---|---|---|---|---|---|
| **B3 (recommended)** | d=4096, L=40, E=256, k=6, d_ex=768 | 100.19 B / 5.82 B | 5.8 | 39 | 1.03 | 70.1 GB ✅ | 401 GB |
| B2 | d=3072, L=64, E=256, k=6, d_ex=1024 | 157.84 B / 6.85 B | 4.3 | 34 | 1.88 | 98.9 GB ❌ | 631 GB |
| B1 | d=4096, L=48, E=256, k=6, d_ex=1280 | 197.43 B / 8.69 B | 4.4 | 39 | 1.23 | 118.7 GB ❌ | 790 GB |

B1 and B2 **do not fit even with offload** and are recorded as rejected.

---

## 4. What has to be true for either design to be built

| Requirement | For (a) | For (b) | Who confirms |
|---|---|---|---|
| 8 × 80 GB node, full ZeRO-3 | ✅ 50 GB/GPU | ✅ 70 GB/GPU with offload | Team 7 |
| Optimizer state offload to host | not needed | **required, 401 GB RAM** | Team 7 |
| Expert count divisible by 8 | ✅ 16/GPU | ✅ 32/GPU | arithmetic |
| KV cache at 2,048 context | 24×4×128×2×32 layers ≈ 0.75 MB/token/seq… see note | larger | Team 9 (memory budget) |
| Packed-row format with document mask | needed by both | needed by both | Team 5 task 1 (Deepjyoti) |
| Token count from corpus-v1 | still unknown | still unknown | Team 1 |

**Note on KV:** the figures above are parameter counts, not decode cost. GQA 24/4 at `d=3072` stores
`2 × 4 × 128 = 1,024` elements per token per layer (same as Qwen3-30B), so (a) has no KV disadvantage versus
the reference. (b) at 64/8 stores 2,048, twice as much — acceptable at 40 layers, but the long-context claim must
be checked against it.

---

## 5. What I am **not** claiming

- These are **parameter-budget designs, not trained models.** No loss number exists for either. Task 6
  ("architecture discovery at 49M–100M") is what would test the shape claims cheaply, and the A1-vs-Qwen3-shape
  comparison is exactly the experiment to run there.
- The Depth Delusion critical-depth rule is used as a **design prior**, not a law — §3 of the study table shows
  every production MoE is 11–55 layers past it at its own width, so the rule clearly does not extrapolate to MoE
  unchanged. A1 is placed inside it deliberately; that is a bet, and it is falsifiable.
- The 5.8 % active ratio for (b) is a deviation from the brief. It is stated rather than hidden.

---

## 6. Deliverable status

| Item | Status |
|---|---|
| Study table (task 1) | ✅ `g5_study_table.md` |
| Two designs (task 2) | ✅ this file |
| Experts-per-GPU arithmetic | ✅ §2–3 |
| Memory feasibility | ✅ §1, §4 — **100 B needs offload, 401 GB RAM** |
| Smoke test at 49M–100M to test the shape | ⬜ task 6, not started |
| PR to upstream | ⬜ Monday (fork → PR; no push access) |
