# Packed rows with a document mask: approach

**Brief item (Team 5, Tasks):** "Confirm the packed-row format with document mask (your packing plan) and how a trainer reads it. Match Team 6's loader." Evidence: a PR with the packed format and the config.
**Owner:** Deepjyoti Saha. **Hand-off:** Team 6 builds its mixture-aware loader to this format.

## What it delivers

1. A format spec: what one packed training row contains, field by field.
2. A `run.pack` switch in the G5 trainer, off by default.
3. The document mask and per-document positions in the model.
4. Tests, and a measured fill and step-time number.

## Why

Today each training row holds one window of one document and the rest is padding (`harness/week2/data.py`, `batch()`: "every row is one window of one document"). On two sample-v0 shards, 43.1% of positions at 2,048 hold a real target; on all 41 shards #825 reports 35.22% at 2,048 and 19.48% at 4,096. Dry run 2 logged 41.8% (`run_report.py` on #869). Packing documents end to end needs about 0.43 times today's positions at 2,048 and 0.25 times at 4,096 for the same tokens (`docs/packing_plan.md`, #831). The current code keeps documents from attending to each other on purpose; a document mask keeps that rule while filling the rows.

## The format (proposal, for Team 6 to confirm)

One packed row has length `L` (= `data.seq_len`). Five arrays, one value per position:

| Field | Type | Meaning |
|---|---|---|
| `input_ids` | int64 | Token fed in at this position. |
| `targets` | int64 | Token to predict; `-100` on padding (ignored by the loss). |
| `byte_lengths` | int64 | UTF-8 bytes of the target token, for bits per byte (as today). `0` on padding. |
| `doc_ids` | int32 | Which piece this position belongs to: 1, 2, 3 ... within the row; `0` is padding. |
| `pos_ids` | int32 | Position inside its piece, starting at 0 for each piece. |

**Pieces are today's windows.** A document longer than `L` is split exactly as now: windows of at most `L` targets, the first input of each window is BOS (first window) or the token before it (later windows). This keeps the targets and the bits-per-byte accounting identical to today.

**Filling a row.** The loader keeps a pool of the next 16 pieces in the sampler's shuffled order. Each row repeatedly takes the largest pooled piece that still fits (the earliest on a tie), refilling the pool after each take, until nothing in the pool fits; the rest of the row is padding. No piece is ever cut by packing.

**End of a pass.** The pool only refills from the current pass. When the pass runs out, the pool drains first, and the next pass is shuffled and starts once the pool is empty. So every pass places each piece exactly once. (Refilling across the boundary, as the first version did, let a next-pass piece jump ahead of a waiting one: within a pass, up to 15 pieces were placed twice and as many not at all.)

Why a pool: taking pieces strictly in order leaves rows only about 78% full at 2,048 on two sample-v0 shards, because a full 2,048 window that arrives when a row is half used wastes the rest of that row. Best fit from 16 upcoming pieces reaches 99.2% at 2,048 and 99.6% at 4,096 (measured below). The size is a setting, `run.pack_pool` (default 16); a pool of 1 is strict order. It only reorders pieces within a window of 16, and the pool is saved in the sampler's state, so the data order is still fixed by the seed and a resumed run continues exactly.

**Positions: settled.** Every window restarts its positions at 0, including the later windows of a long document, as today. TSAI accepted this on the PR (28 Nov): the model cannot see an earlier window, so restarting is consistent.

**Open point for Team 6: start and end of a document.** The shards end every document with EOS (130822) and carry no BOS. The G5 trainer feeds BOS (130725) as the first input of each document and does not train on EOS. The proposal is that packed rows follow the same rule, so a row built by Team 6's loader and a row built by this reader are identical; asked on the PR, 28 Nov.

## How the trainer reads it

- **Switch.** `run.pack: true` in the G5 arm, off by default. Works with `attn_impl: eager` and `attn_impl: sdpa`; refused with `run.tst`.
- **Loader (`week2/data.py`).** `DocumentWindows.packed_batch()` builds the rows; `BatchStream(..., pack=True)` fills them with the pool rule above. With the switch off, the current `batch()` and `BatchStream` run unchanged, and a checkpoint's sampler state has exactly today's keys.
- **Steps and data order.** With packing, a step still has a fixed number of rows (fixed positions per step), but it consumes a varying number of windows. The sampler state records the order, the offset and the pool, so a resumed run continues at the same window (Team 7's restart test).
- **Positions (`week2/model.py`, `rotary`).** Today the angle uses `arange(t)` for every row. With packing it uses `pos_ids` per row.
- **Attention mask (`eager_attention`).** Today: causal, intersected with the local window on local layers. With packing: also "same piece" (`doc_ids[i] == doc_ids[j]`). Padding positions (id 0) attend only to earlier padding and themselves, so no row of scores is all masked (that would give NaN in the softmax); their targets are `-100`, so they add nothing to the loss.
- **Multi-token prediction.** When MTP is on, the "token after next" target is dropped where it would come from the next piece in the row.
- **SDPA path (opt-in, #804).** Takes the same mask, causal and same piece, as an explicit boolean `attn_mask`. A custom mask rules out the flash kernel, so PyTorch uses another fused kernel or the math path; whether SDPA with the mask still beats eager is measured by `measure_attention.py` (below).
- **MoE.** The valid-token mask is unchanged: padding is still padding, and real tokens of every piece are routed as today.
- **Held-out evaluation.** Stays unpacked, so its numbers stay comparable with every earlier run.
- **TST.** Off in dry run 2; packing with TST on is refused until tested.

## Checks

| # | Test | Pass when |
|---|---|---|
| a | Packing off | Loss bit-identical to main on the fixture model |
| b | Packing on, one piece per row | Same loss as packing off |
| c | Two short documents in one row | Each token's loss equals its loss with the document alone |
| d | Positions | `pos_ids` restart at 0 for each piece; the rotary angles match today's for each piece |
| e | Bytes | Total target bytes and bits per byte unchanged |
| f | Fill | Fewer rows for the same windows; `measure_fill.py` gives the same row count as the loader on the same order |
| g | Resume | Stopping and resuming the sampler gives the same windows in the same order, also while the pool drains at the end of a pass |
| h | Id types | `doc_ids` and `pos_ids` are 32-bit integers |
| i | One pass, each piece once | Over several passes, every pass places each window exactly once |
| j | SDPA with the mask | Same logits and gradients as eager on a packed row |
| k | Gradient coverage | The parameters with a None or all-zero gradient are the same with SDPA and with eager |
| l | Pool size | `run.pack_pool` is checked (a whole number, at least 1); a pool of 1 gives the same rows as strict order |

All are in `tests/test_packed_rows.py` (18 tests), plus the full G5 test suite.

## Measured

Two full sample-v0 shards (`code-python-train-000000`, `en-fineweb-edu-train-000000`; the files used in #831), 106,665 documents, 113,426,354 content tokens, window order shuffled with seed 1234:

```
python teams/05-architecture/lab5/packed_rows/measure_fill.py \
    --index code-python-train-000000.idx.npy en-fineweb-edu-train-000000.idx.npy --windows 2048 4096
```

| Window | Rows today | Rows packed (loader) | Fill today | Fill in strict order | Fill packed (loader) | Packed / today |
|---:|---:|---:|---:|---:|---:|---:|
| 2,048 | 128,545 | 55,827 | 43.1% | 78.0% | 99.2% | 0.43x |
| 4,096 | 113,015 | 27,813 | 24.5% | 79.9% | 99.6% | 0.25x |

The packed figures are within 1% of #831's continuous-stream estimate (55,437 rows at 2,048; 27,719 at 4,096), which cuts windows to fill rows; the loader never cuts one.

All 41 sample-v0 shards (the `.idx.npy` files only; 1,200,725 documents, 1,008,187,260 content tokens), same command with all 41 files:

| Window | Rows today | Rows packed (loader) | Fill today | Fill in strict order | Fill packed (loader) | Packed / today |
|---:|---:|---:|---:|---:|---:|---:|
| 2,048 | 1,397,555 | 494,570 | 35.2% | 77.9% | 99.5% | 0.35x |
| 4,096 | 1,263,667 | 246,683 | 19.5% | 80.3% | 99.8% | 0.20x |

The "fill today" column matches #825's figures for the same 41 shards (35.22% at 2,048, 19.48% at 4,096), a check on the measurement. `measure_fill.py` measures one pass, so its numbers already follow the end-of-pass rule above.

**Pool size** (`run.pack_pool`), all 41 shards, same command with `--pool 1 4 8 16 32 64`:

| Pool | Fill at 2,048 | Fill at 4,096 |
|---:|---:|---:|
| 1 (strict order) | 77.9% | 80.3% |
| 4 | 97.1% | 98.0% |
| 8 | 99.0% | 99.5% |
| 16 (default) | 99.5% | 99.8% |
| 32 | 99.7% | 99.9% |
| 64 | 99.7% | 99.9% |

16 is where the gain flattens: 32 and 64 add 0.2 points or less, and a bigger pool moves windows further from their shuffled order.

**Eager against SDPA with the mask** (TSAI's review). `measure_attention.py` runs four arms on the same documents, model (the T2 arm, vocabulary 32,768) and seed: packed rows with eager, packed rows with SDPA and the mask, and one window per row (today) with eager and with causal SDPA. It reports real tokens per second over forward and backward, peak GPU memory, and the gradient-coverage list for each arm:

```
python teams/05-architecture/lab5/packed_rows/measure_attention.py \n    --index en-fineweb-edu-train-000000.idx.npy --window 2048 --batch 2 --steps 20 --dtype fp16
```

**CPU, for the direction only** (a laptop CPU, fp32, window 2,048, one row per step, 4 steps with the first left out of the timing; document lengths from `en-fineweb-edu-train-000000`):

```
python teams/05-architecture/lab5/packed_rows/measure_attention.py     --index en-fineweb-edu-train-000000.idx.npy --window 2048 --batch 1 --steps 4 --warmup 1 --dtype fp32
```

| Arm | Fill | Real tokens/s | vs eager packed |
|---|---:|---:|---:|
| eager, packed | 99.3% | 224 | 1.00x |
| SDPA with the mask, packed | 99.3% | 200 | 0.89x |
| eager, one window per row | 50.1% | 126 | 0.56x |
| SDPA causal, one window per row | 50.1% | 143 | 0.64x |

A packed row costs about the same as a padded row, so real tokens per second rise with the fill: 224 against 126 on eager, 1.78 times (the fill ratio is 1.98; the rest is noise over three timed steps and the cost of attending within longer rows). On this CPU, SDPA with the mask is slower than eager; the CPU says nothing about GPU kernels. Gradient coverage is the same on all four arms (no parameter without a gradient).

**T4, the answer to TSAI's question** (Google Colab, Tesla T4, torch 2.14.1, fp16 because the T4 has no fast bf16; window 2,048, 2 rows per step, 20 steps with the first 3 left out of the timing; vocabulary 32,768; document lengths from `en-fineweb-edu-train-000000`; the command above with `--batch 2 --steps 20 --dtype fp16`):

| Arm | Fill | Real tokens/s | vs eager packed | Peak memory (GiB) | Gradient None or zero |
|---|---:|---:|---:|---:|---:|
| eager, packed | 98.4% | 7,540 | 1.00x | 10.23 | 0 |
| SDPA with the mask, packed | 98.4% | 9,744 | 1.29x | 7.25 | 0 |
| eager, one window per row | 40.1% | 3,100 | 0.41x | 10.19 | 0 |
| SDPA causal, one window per row | 40.1% | 4,346 | 0.58x | 7.11 | 0 |

- **SDPA keeps its speed-up with the document mask:** 1.29 times eager's real tokens per second on packed rows, with 29% less peak memory (7.25 against 10.23 GiB). That is close to the ~1.33x measured without packing, so packed runs should use `attn_impl: sdpa`.
- **Packing more than doubles real tokens per second:** SDPA packed against SDPA one window per row is 2.24 times; against today's eager trainer with one window per row, 3.14 times. The gain follows the fill (98.4% against 40.1%).
- **Gradient coverage** (TSAI's rule for speed claims): no parameter has a missing or all-zero gradient on any arm; the lists are identical for eager and SDPA.

Every number is for a T4 with this model, not the training GPU; the ratios, not the absolute speeds, are the result.

## What it needs from others

- **Team 6:** confirm the five fields, their types and the open point above; their loader writes the same arrays.
- **Team 7:** the sampler offset in windows for the restart test.

## What it cannot tell

- The real speed gain on the training GPU: the T4 numbers show the direction, not the size. Team 6's profile measures the GPU number.
- Whether a variable-length (mask-aware) flash kernel would add more: on the T4, SDPA with the mask is already 1.29 times eager; the training GPU may differ.

## Plan and dates

| Step | What | By |
|---|---|---|
| 1 | Format spec (this note) agreed with Team 6 | Sun 29 Nov |
| 2 | Loader, mask, positions, wiring | Mon 30 Nov |
| 3 | Tests a to g, measurements, PR | Mon 30 Nov |
| 4 | Review comments, Team 6 differences written down | Wed 2 Dec, 07:00 |
