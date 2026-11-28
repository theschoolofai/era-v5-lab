# G5 design task 2 — two sparse model designs

`tanmays369`, 28 Nov 2026. **Approach note, published before the build**, as TSAI asked for on #890.

Companion to `model_study_table.md` (§ numbers there are the reference set this builds on).

**Corrected 28 Nov after review by @UditSinghania.** Three fixes, all his:

1. **Head dim is derived, not chosen.** `model.py` (`GQA.__init__`) sets `self.d = w // self.nh`. With the published
   numbers that gives A1 = 3072/24 = **128** (unchanged) but B3 = 4096/64 = **64**, not the 128 I wrote. B3 is
   restated at head dim 64; using 128 would need `n_head=32`.
2. **Head dim settled at 128 for both designs.** B3 uses `n_head=32`, not 64, so `d // n_head = 128` and the two
   designs share an attention shape. At `n_head=64` B3 would be head dim 64 — 98.16 B instead of 98.33 B, a 0.2 %
   difference that changes no conclusion. Switching removes an open question rather than leaving it in the spec.
3. **The embedding term is KAS V2, not vocab-sized.** `kas_v2.py` has `KASInput.projection = Linear(2048, n_embd)`
   and `KASHead.W_out = (n_embd, 2048)`, so the term is **2 · d · 2048**, not `V · d`. My figures overcounted by
   0.39 B (A1) and 0.52 B (B3). The counts below now reproduce G5's sizing formula to within 0.02 B (norms/biases).
4. **The trainer keeps FP32 parameters and gradients** and autocasts the computation. My memory table assumed bf16,
   which was the wrong case — see §1.

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

**Constraint 1 — in FP32, a 100B model does not fit 8×80 GB at all.**
The trainer keeps FP32 parameters and gradients and autocasts the computation. With full ZeRO-3 sharding and
Muon's single 4 B/param buffer:

| Design | total | fp32 resident | fp32 + optimizer offload | bf16 + optimizer offload |
|---|---:|---:|---:|---:|
| **A1** | 29.71 B | **64.6 GB** ✅ | 49.7 GB ✅ | 34.9 GB ✅ |
| **B3** | 98.33 B | **167.5 GB** ❌ | **118.3 GB** ❌ | 69.2 GB ✅ |

**A1 fits as-is. B3 fits only if weights and gradients are bf16 *and* the optimizer state is offloaded to host
memory, which needs 393 GB of CPU RAM** (785 GB with AdamW). Optimizer offload alone is *not* sufficient — the
dtype is the blocker. That has to be settled before B3 is treated as buildable. **Note:** Team 7 has not decided this — their own Lab 5 split lists *"Memory budget + fit more (design 1, 2)"* as **open, to be assigned** (28 Nov 12:03), and no message in G7 mentions fp32 vs bf16. So this is an unowned question, not a Team 7 decision to check.

Maximum that fits 8×80 GB in FP32 with Muon resident, over the 20 GB activation reserve: **about 40 B**
(40 B → 80.0 GB exactly). That supersedes the ~60 B I wrote earlier, which assumed bf16.

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
| **total / active** | **29.71 B / 2.53 B (8.5 %)** — G5 sizing formula |
| D_crit at W=3072 | 34 → **L/D_crit = 0.93** (just inside) |
| memory/GPU | **64.6 GB fp32 resident** (was 50.1 GB under the wrong bf16 assumption) |

**Why this shape and not Qwen3's:** the Depth Delusion paper's central result is that width should grow ~2.8×
faster than depth (`D* ∝ C^0.12`, `W* ∝ C^0.34`). At equal parameter budget, holding Qwen3's 48 layers at
`d=2048` sits at `L/D_crit = 48/29 = 1.66`, i.e. **66 % past the critical depth**. A1 sits at **0.93** — inside
it. If the paper's finding holds at our scale, A1 should reach a lower loss for the same parameters; if it does
not, that is a publishable negative result and the brief explicitly asks for those.

**One alternative, if A1 fails a smoke test:** (the earlier A2, 64 experts at 1536, is arithmetically identical to A1 — 64×1536 = 128×768 — so it is not a real alternative and is dropped.)

| | shape | total / active | act % | D_crit | L/D_crit | mem/GPU | what it tests |
|---|---|---|---|---|---|---|---|
| **A3** | d=2560, L=40, E=128, k=8, d_ex=768 | 30.84 B / 2.53 B | 8.2 | 32 | 1.27 | 66.3 GB | a middle point between A1 and Qwen3's shape |

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
| **total / active** | **98.33 B / 3.96 B (4.0 %)** — G5 sizing formula, **head dim 128** (`n_head=32`) |
| D_crit at W=4096 | 39 → **L/D_crit = 1.03** |
| memory/GPU | **167.2 GB fp32 resident** ❌; **118.2 GB with the optimizer offloaded** ❌; **69.1 GB only if weights and grads are bf16** ✅ |
| CPU RAM for optimizer | **393 GB** (Muon) / 785 GB (AdamW) |

### The brief's 2–3 % cannot be met at 100 B without a different trade

Every 100 B combination I could build with this parameterisation lands at **3.6–6.4 % active** (before the KAS
correction; 3.9–6.4 % after it), never inside 2–3 %. The reason is arithmetic: to reach 100 B total at 2.5 % the model needs **2.5 B active**, and with
`d=4096` the embedding + attention alone contribute ~1.0 B of that, leaving very little for experts. Reaching
2–3 % at 100 B requires either a much narrower model with far more experts, or counting the embedding as
inactive.

**So design (b) is presented at 3.9 % active, which is *above* the brief's 2–3 % band — stated rather than hidden.**
If 2–3 % is mandatory, the honest alternative is the Qwen3-Next shape (d=2048, 512 experts, k=10 → 78.5 B /
2.73 B = 3.5 %), which is closer to the target but is again a copy of an existing model. **On the corrected KAS
sizing, B3's active ratio is 3.96 B of 98.33 B.**

| | shape | total / active | act % | D_crit | L/D_crit | mem w/ offload | CPU RAM |
|---|---|---|---|---|---|---|---|
| **B3 (recommended)** | d=4096, L=40, E=256, k=6, d_ex=768, **head dim 128** (`n_head=32`) | 98.33 B / 3.96 B | 4.0 | 39 | 1.03 | bf16 offload only: 69.2 GB ✅ | 393 GB |
| B2 | d=3072, L=64, E=256, k=6, d_ex=1024 | 157.84 B / 6.85 B | 4.3 | 34 | 1.88 | 98.9 GB ❌ | 631 GB |
| B1 | d=4096, L=48, E=256, k=6, d_ex=1280 | 197.43 B / 8.69 B | 4.4 | 39 | 1.23 | 118.7 GB ❌ | 790 GB |

B1 and B2 **do not fit even with offload** and are recorded as rejected.

---

## 4. What has to be true for either design to be built

| Requirement | For (a) | For (b) | Who confirms |
|---|---|---|---|
| 8 × 80 GB node, full ZeRO-3 | ✅ 50 GB/GPU | ✅ 70 GB/GPU with offload | Team 7 |
| Optimizer state offload to host | not needed | **required, 393 GB RAM, and only with bf16 weights+grads** | **unowned** — Team 7's own Lab 5 split lists "Memory budget + fit more (design 1, 2)" as *open, Suresh to assign* (28 Nov 12:03). No dtype decision exists yet. |
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
- The head dim for (b) is 64, derived from `d // n_head`. If 128 is wanted the design needs `n_head=32`, which changes
the attention cost but not the total much (98.85 B). It is stated rather than hidden.

---

## 6. Deliverable status

| Item | Status |
|---|---|
| Study table (task 1) | ✅ `g5_study_table.md` |
| Two designs (task 2) | ✅ this file |
| Experts-per-GPU arithmetic | ✅ §2–3 |
| Memory feasibility | ✅ §1, §4 — **100 B needs bf16 *and* offload (393 GB RAM); in FP32 it does not fit at all** |
| Smoke test at 49M–100M to test the shape | ⬜ task 6, not started |
| PR to upstream | ⬜ Monday (fork → PR; no push access) |
