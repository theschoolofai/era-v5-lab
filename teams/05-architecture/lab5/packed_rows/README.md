# Packed rows with a document mask: approach

**Brief item (Team 5, Tasks):** "Confirm the packed-row format with document mask (your packing plan) and how a trainer reads it. Match Team 6's loader." Evidence: a PR with the packed format and the config.
**Owner:** Deepjyoti Saha. **Hand-off:** Team 6 builds its mixture-aware loader to this format.

## What it delivers

1. A format spec: what one packed training row contains, field by field.
2. A `data.pack` switch in the G5 trainer, off by default.
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

Why a pool: taking pieces strictly in order leaves rows only about 78% full at 2,048 on two sample-v0 shards, because a full 2,048 window that arrives when a row is half used wastes the rest of that row. Best fit from 16 upcoming pieces reaches 99.2% at 2,048 and 99.6% at 4,096 (measured below). It only reorders pieces within a window of 16, and the pool is saved in the sampler's state, so the data order is still fixed by the seed and a resumed run continues exactly.

**Open point for Team 6.** Today every window restarts its positions at 0, including the second window of a long document. The proposal keeps that, so the model sees exactly the positions it sees today. If Team 6's loader prefers continuing positions across a long document's windows, that is a separate change with its own test.

## How the trainer reads it

- **Switch.** `run.pack: true` in the G5 arm (the trainer's spelling of `data.pack`; off by default). Refused with `attn_impl: sdpa` or with `run.tst`.
- **Loader (`week2/data.py`).** `DocumentWindows.packed_batch()` builds the rows; `BatchStream(..., pack=True)` fills them with the pool rule above. With the switch off, the current `batch()` and `BatchStream` run unchanged, and a checkpoint's sampler state has exactly today's keys.
- **Steps and data order.** With packing, a step still has a fixed number of rows (fixed positions per step), but it consumes a varying number of windows. The sampler state records the order, the offset and the pool, so a resumed run continues at the same window (Team 7's restart test).
- **Positions (`week2/model.py`, `rotary`).** Today the angle uses `arange(t)` for every row. With packing it uses `pos_ids` per row.
- **Attention mask (`eager_attention`).** Today: causal, intersected with the local window on local layers. With packing: also "same piece" (`doc_ids[i] == doc_ids[j]`). Padding positions (id 0) attend only to earlier padding and themselves, so no row of scores is all masked (that would give NaN in the softmax); their targets are `-100`, so they add nothing to the loss.
- **Multi-token prediction.** When MTP is on, the "token after next" target is dropped where it would come from the next piece in the row.
- **SDPA path (opt-in, #804).** Refuses packing with a clear error for now. A boolean mask in SDPA turns off the fast fused kernel; that is a question for the SDPA A/B (#805) or a variable-length kernel, not this change.
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
| g | Resume | Stopping and resuming the sampler gives the same windows in the same order |

All are in `tests/test_packed_rows.py` (13 tests), plus the full G5 test suite.

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

Still to measure: one training step on CPU, packed and unpacked, for the cost per real token.

## What it needs from others

- **Team 6:** confirm the five fields, their types and the open point above; their loader writes the same arrays.
- **Team 7:** the sampler offset in windows for the restart test.

## What it cannot tell

- The real speed gain on the training GPU: the eager attention cost per row is unchanged, only the number of rows falls. Team 6's profile measures the GPU number.
- Whether a mask-aware fast kernel is needed: that comes from the SDPA A/B.

## Plan and dates

| Step | What | By |
|---|---|---|
| 1 | Format spec (this note) agreed with Team 6 | Sun 29 Nov |
| 2 | Loader, mask, positions, wiring | Mon 30 Nov |
| 3 | Tests a to g, measurements, PR | Mon 30 Nov |
| 4 | Review comments, Team 6 differences written down | Wed 2 Dec, 07:00 |
