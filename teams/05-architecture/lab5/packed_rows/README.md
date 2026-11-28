# Packed rows with a document mask

**Brief item (Team 5, Tasks):** "Confirm the packed-row format with document mask (your packing plan) and how a trainer reads it. Match Team 6's loader." Evidence: a PR with the packed format and the config.
**Owner:** Deepjyoti Saha (Team 5). **PR:** #890. **Hand-off:** Team 6 builds its mixture-aware loader to this format.

**In one paragraph.** Today about two thirds of every training row is padding. This PR fills rows with several whole documents, keeps each document blind to the others with a document mask, and restarts positions per document. On all 41 sample-v0 shards, rows go from 35.2% to 99.5% real tokens at 2,048. On a T4, packed rows with SDPA train on 2.24 times the real tokens per second of today's rows, and SDPA keeps its speed-up over eager with the mask. It is behind `run.pack` (off by default), with 18 tests. Left: Team 6's confirmation of the format and of one rule (start and end of a document).

Contents: 1. The problem · 2. The solution · 3. Approach and experiments · 4. TSAI's review and what changed · 5. Results · 6. Tests · 7. What is left · 8. Limits

## 1. The problem

The G5 trainer puts **one window of one document in each row** and pads the rest (`harness/week2/data.py`, `batch()`: "every row is one window of one document"). A window is a piece of a document of at most `L` tokens (`L` = 2,048 in dry run 2); a long document gives several windows.

Most documents are much shorter than 2,048 tokens, so most of each row is padding, and padding costs compute but teaches nothing:

| Source | Real tokens per row position |
|---|---:|
| Dry run 2, logged (`run_report.py` on #869) | 41.8% |
| Two sample-v0 shards, at 2,048 (#831) | 43.1% |
| All 41 sample-v0 shards, at 2,048 (#825) | 35.2% |
| All 41 sample-v0 shards, at 4,096 (#825) | 19.5% |

Doubling the context to 4,096 makes it worse: rows get longer but documents do not.

The padding exists on purpose: it keeps documents from attending to each other. Any fix must keep that rule.

## 2. The solution

**Pack several whole windows into each row, and add a document mask so each window sees only itself.**

One packed row of length `L` carries five arrays, one value per position:

| Field | Type | Meaning |
|---|---|---|
| `input_ids` | int64 | Token fed in at this position. |
| `targets` | int64 | Token to predict; `-100` on padding (ignored by the loss). |
| `byte_lengths` | int64 | UTF-8 bytes of the target token, for bits per byte (as today); `0` on padding. |
| `doc_ids` | int32 | Which window this position belongs to: 1, 2, 3 ... within the row; `0` is padding. |
| `pos_ids` | int32 | Position inside its window, starting at 0 for each window. |

- **Windows are cut exactly as today.** Windows of at most `L` targets; the first input of a window is BOS (first window of a document) or the token before it (later windows). Targets and the bits-per-byte accounting stay identical to today. Packing never cuts a window.
- **Document mask.** A token may attend to an earlier token only if both have the same `doc_ids` (causal and same window). Padding (id 0) attends only to earlier padding and itself, so no row of scores is all masked (that would give NaN in the softmax); its targets are `-100`, so it adds nothing to the loss.
- **Positions restart at 0 for every window**, including later windows of a long document, as today. Settled with TSAI (section 4).
- **Filling a row: best fit from a pool.** The loader keeps the next 16 windows of the shuffled order in a pool. Each row repeatedly takes the largest pooled window that still fits (the earliest on a tie) and refills the pool, until nothing fits; the rest is padding. The pool size is a setting, `run.pack_pool` (default 16); a pool of 1 is strict order.
- **End of a pass.** The pool refills only from the current pass. When a pass runs out, the pool drains first, and the next pass starts once it is empty, so every pass places each window exactly once.
- **Data order and resume.** The pool only reorders windows within a span of 16, and it is saved in the sampler's state, so the order is still fixed by the seed and a resumed run continues at the same window.

**How the trainer reads it:**
- **Switch.** `run.pack: true` in the G5 arm, off by default. Works with `attn_impl: eager` and `attn_impl: sdpa`; refused with `run.tst` (not tested together). With the switch off, `batch()` and `BatchStream` run unchanged and a checkpoint's sampler state has exactly today's keys.
- **Loader (`week2/data.py`).** `DocumentWindows.packed_batch()` builds the rows; `BatchStream(..., pack=True, pool=...)` fills them.
- **Steps.** A step still has a fixed number of rows (fixed positions per step) but consumes a varying number of windows.
- **Positions (`week2/model.py`, `rotary`).** The angle uses `pos_ids` per row instead of `arange(t)`.
- **Attention.** Eager: the mask is intersected with the causal (and, on local layers, the window) mask in `eager_attention`. SDPA: the same causal-and-same-window mask is passed as an explicit boolean `attn_mask`.
- **Multi-token prediction.** The "token after next" target is dropped where it would come from the next window in the row.
- **MoE.** The valid-token mask is unchanged; real tokens of every window are routed as today.
- **Held-out evaluation.** Stays unpacked, so its numbers stay comparable with every earlier run.

## 3. Approach and experiments

| # | Question | How it was answered | Answer |
|---|---|---|---|
| 1 | How much padding is there today? | #825 and #831; `measure_fill.py` | 35% to 43% real tokens at 2,048 |
| 2 | Which way of filling rows? | Four ways compared on two shards (below) | Best fit from a pool of 16 |
| 3 | How big a pool? | `measure_fill.py --pool` on 41 shards | 16: the gain flattens there |
| 4 | Does packing change what the model computes per token? | Tests c and j (section 6) | No: each token's output equals its document alone |
| 5 | Does packing lose SDPA's speed-up? (TSAI) | `measure_attention.py`, four arms on a T4 | No: SDPA with the mask is 1.29x eager |
| 6 | Is a training run needed? | Reasoned from 4 and 5 | Not for this PR (section 8) |

**Ways of filling rows considered** (two sample-v0 shards, 2,048):

| Way | What | Fill | Why not / why |
|---|---|---:|---|
| 1. Pad (today) | One window per row | 43.1% | The problem |
| 2. Group by length | Rows of similar-length windows, row length cut to fit | about 99% | Rows of different lengths per step; not what the trainer or Team 6's loader do |
| 3. One long stream, cut every `L` | Join everything and cut | about 100% | Cuts documents at arbitrary places; only about 0.5% fewer rows than way 4 on the 41 shards (492,280 against 494,570) |
| 4. Best fit from a pool (chosen) | Whole windows, largest that fits | 99.2% | No cuts, fixed row length, near-full |
| Strict order | Way 4 with a pool of 1 | 78.0% | A long window arriving when a row is half used wastes the rest |

## 4. TSAI's review and what changed

TSAI (Rohan) reviewed the first version on 28 Nov: "I approve the format as proposed once these are in."

| His point | What changed | Evidence |
|---|---|---|
| Positions restart at 0 for each window, including later windows of a long document | Accepted as proposed: "the model cannot see an earlier window, so restarting is consistent" | No change needed |
| Use 32-bit integers for `doc_ids` and `pos_ids` in the code (they were 64-bit, copied from the token array) | `packed_batch()` creates both as int32 | Test h |
| One switch name, `run.pack`, in the PR body, the note and the code (the note also said `data.pack`) | `data.pack` removed from the note and `docs/packing_plan.md`; the PR body rewritten | No `data.pack` left in `teams/05-architecture` |
| Eager is acceptable for now, but the SDPA speed-up would be lost; also measure SDPA with an explicit block mask, tokens/s and peak memory for both (with TSAI's lab rule: a gradient-coverage check for every speed claim) | SDPA takes the mask as `attn_mask`; the refusal and its config check are removed; `measure_attention.py` measures four arms | Tests j and k; T4 table in section 5 |
| The pool can hand out a window twice across the end of a pass; stop topping up, or state the duplicates | The pool refills only from the current pass and drains before the next | Tests g and i |

Also added after the review: `run.pack_pool` with a sweep (question 3), and the fill on all 41 shards.

## 5. Results

**Fill on all 41 sample-v0 shards** (the `.idx.npy` files only; 1,200,725 documents, 1,008,187,260 content tokens; window order shuffled with seed 1234):

```
python teams/05-architecture/lab5/packed_rows/measure_fill.py --index <41 shard .idx.npy files> --windows 2048 4096 --pool 1 4 8 16 32 64
```

| Window | Rows today | Rows packed | Fill today | Fill in strict order | Fill packed | Packed / today |
|---:|---:|---:|---:|---:|---:|---:|
| 2,048 | 1,397,555 | 494,570 | 35.2% | 77.9% | 99.5% | 0.35x |
| 4,096 | 1,263,667 | 246,683 | 19.5% | 80.3% | 99.8% | 0.20x |

"Fill today" matches #825 for the same shards (35.22%, 19.48%), a check on the measurement. On the two shards of #831 (`code-python-train-000000`, `en-fineweb-edu-train-000000`; 106,665 documents) the packed fill is 99.2% at 2,048 and 99.6% at 4,096, within 1% of #831's estimate.

**Pool size** (`run.pack_pool`), all 41 shards:

| Pool | Fill at 2,048 | Fill at 4,096 |
|---:|---:|---:|
| 1 (strict order) | 77.9% | 80.3% |
| 4 | 97.1% | 98.0% |
| 8 | 99.0% | 99.5% |
| **16 (default)** | **99.5%** | **99.8%** |
| 32 | 99.7% | 99.9% |
| 64 | 99.7% | 99.9% |

16 is where the gain flattens: 32 and 64 add 0.2 points or less, and a bigger pool moves windows further from their shuffled order.

**Speed: eager against SDPA with the mask, packed against one window per row.** `measure_attention.py` runs four arms on the same documents, model (the T2 arm with a 32,768 vocabulary, so the output head does not swamp attention) and seed, and reports real tokens per second over forward and backward, peak GPU memory, and the gradient-coverage list. T4 (Google Colab, torch 2.14.1, fp16 because the T4 has no fast bf16; window 2,048, 2 rows per step, 20 steps with the first 3 untimed; document lengths from `en-fineweb-edu-train-000000`):

```
python teams/05-architecture/lab5/packed_rows/measure_attention.py --index en-fineweb-edu-train-000000.idx.npy --window 2048 --batch 2 --steps 20 --dtype fp16
```

| Arm | Fill | Real tokens/s | vs eager packed | Peak memory (GiB) | Gradient None or zero |
|---|---:|---:|---:|---:|---:|
| eager, packed | 98.4% | 7,540 | 1.00x | 10.23 | 0 |
| **SDPA with the mask, packed** | 98.4% | **9,744** | **1.29x** | **7.25** | 0 |
| eager, one window per row (today) | 40.1% | 3,100 | 0.41x | 10.19 | 0 |
| SDPA causal, one window per row | 40.1% | 4,346 | 0.58x | 7.11 | 0 |

- **SDPA keeps its speed-up with the mask:** 1.29 times eager on packed rows, with 29% less peak memory. That is close to the ~1.33x quoted for SDPA without packing, so packed runs should use `attn_impl: sdpa`.
- **Packing more than doubles real tokens per second:** 2.24 times on SDPA, and 3.14 times against today's eager trainer. The gain follows the fill.
- **Gradient coverage:** no parameter has a missing or all-zero gradient on any arm; eager and SDPA match.

A laptop CPU run (fp32, one row per step, 3 timed steps; `--batch 1 --steps 4 --warmup 1 --dtype fp32`) shows the same direction for packing (eager packed 224 real tokens/s against 126 for one window per row) but not for SDPA (200, slower than eager); a CPU says nothing about GPU kernels.

## 6. Tests

| # | Test | Pass when |
|---|---|---|
| a | Packing off | Loss bit-identical to main on the fixture model |
| b | Packing on, one window per row | Same loss as packing off |
| c | Two short documents in one row | Each token's output equals its output with the document alone |
| d | Positions | `pos_ids` restart at 0 for each window; the rotary angles match today's for each window |
| e | Bytes | Total target bytes and bits per byte unchanged |
| f | Fill | Fewer rows for the same windows; `measure_fill.py` gives the same row count as the loader on the same order |
| g | Resume | Stopping and resuming the sampler gives the same windows in the same order, also while the pool drains at the end of a pass |
| h | Id types | `doc_ids` and `pos_ids` are 32-bit integers |
| i | One pass, each window once | Over several passes, every pass places each window exactly once |
| j | SDPA with the mask | Same logits and gradients as eager on a packed row |
| k | Gradient coverage | The parameters with a None or all-zero gradient are the same with SDPA and with eager |
| l | Pool size | `run.pack_pool` is checked (a whole number, at least 1); a pool of 1 gives the same rows as strict order |

All in `tests/test_packed_rows.py`: 18 passed. Full Team 5 suite: 322 passed, 12 skipped (CPU).

## 7. What is left

| Item | Who | Due |
|---|---|---|
| Confirm the five fields and their types; their loader writes the same arrays | Team 6 (Raj H, Vaibhav Lohar) | Sun 29 Nov, 18:00 |
| One rule for the start and end of a document. The shards end every document with EOS (130822) and carry no BOS; the G5 trainer feeds BOS (130725) as the first input of each document and does not train on EOS. Proposal: packed rows follow the trainer's rule, so rows from Team 6's loader and from this reader are identical. Asked on the PR, 28 Nov | Team 6 to answer; then a line here and a test | Sun 29 Nov |
| The sampler offset in windows for the restart test | Team 7 | With their restart test |
| Mark #890 ready for review | Deepjyoti | After Team 6 confirms |

## 8. Limits

- **Speed on the training GPU.** The T4 numbers are for a T4 with this model in fp16; the ratios are the result, not the absolute speeds. Team 6's profile measures the training GPU.
- **A mask-aware flash kernel.** With a custom mask PyTorch cannot use the flash kernel; on the T4 SDPA is still 1.29x eager. A variable-length kernel might add more on the training GPU.
- **Training quality.** Not measured with a training run. Test c shows each token's output is unchanged by packing; what changes is that a step holds about twice the real tokens, which is a batch-size question for the main-run recipe, not for the format. A training-scale check belongs in Team 6's or the main run's A/B.
