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

**Filling a row.** Pieces are taken in the sampler's shuffled order and placed end to end; when the next piece does not fit in the space left, the rest of the row is padding and the piece starts the next row. No piece is ever cut by packing.

**Open point for Team 6.** Today every window restarts its positions at 0, including the second window of a long document. The proposal keeps that, so the model sees exactly the positions it sees today. If Team 6's loader prefers continuing positions across a long document's windows, that is a separate change with its own test.

## How the trainer reads it

- **Loader (`week2/data.py`).** A packed batch builder used only when `data.pack: true`. It walks the same shuffled window order as `BatchStream` and fills rows as above. Byte conservation is checked as today. With the switch off, the current `batch()` runs unchanged.
- **Steps and data order.** With packing, a step still has a fixed number of rows (fixed positions per step), but it consumes a varying number of windows. The sampler must record its offset in windows so that a resumed run continues at the same window (Team 7's restart test).
- **Positions (`week2/model.py`, `rotary`).** Today the angle uses `arange(t)` for every row. With packing it uses `pos_ids` per row.
- **Attention mask (`eager_attention`).** Today: causal, intersected with the local window on local layers. With packing: also "same piece" (`doc_ids[i] == doc_ids[j]`). Padding positions may only attend to themselves, so that no row of scores is all masked (that would give NaN in the softmax); their targets are `-100`, so they add nothing to the loss.
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
| f | Fill | Positions used per pass are close to `harness/packing_fill.py`'s packed estimate on the same input; the gap is reported (the loader never cuts a window, so it pads a little more than the estimate's continuous stream) |
| g | Resume | Stopping and resuming the sampler gives the same windows in the same order |

Plus the full G5 test suite.

## Measurements in the PR

- Rows per pass, packed and unpacked, on the two sample-v0 shards used in #831 (command in the PR).
- One-step CPU time on the fixture model, packed and unpacked, so the gain per real token is measured, not assumed.

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
