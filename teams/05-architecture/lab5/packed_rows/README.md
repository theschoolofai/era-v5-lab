# Packed rows with a document mask

**Brief item (Team 5, Tasks):** "Confirm the packed-row format with document mask (your packing plan) and how a trainer reads it. Match Team 6's loader." Evidence: a PR with the packed format and the config.
**Owner:** Deepjyoti Saha (Team 5). **PR:** #890. **Hand-off:** Team 6 builds its mixture-aware loader to this format.

**In one paragraph.** Today about two thirds of every training row is padding. This PR fills rows with several whole documents, keeps each document blind to the others with a document mask, and restarts positions per document. On all 41 sample-v0 shards, rows go from 35.2% to 99.5% real tokens at 2,048. On a T4, packed rows with SDPA train on 2.24 times the real tokens per second of today's rows, and SDPA keeps its speed-up over eager with the mask. Each document starts with BOS and ends with EOS as its last target, as agreed with Team 6, and the contract with Team 6's loader is per piece: `piece_check.py` builds the pieces from a shard alone and checks any loader against them (Team 5's reader matches on 300 random documents of a real shard). It is behind `run.pack` (off by default), with 24 tests. Left: Team 6 runs `piece_check.py` on their pieces.

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

- **Windows are cut as today, with one token more per document.** Windows of at most `L` targets; the first input of a window is BOS (first window of a document) or the token before it (later windows). Packing never cuts a window.
- **Start and end of a document (agreed with Team 6, 28 Nov).** The shards store every document ending with EOS (130822) and no BOS. In packed training rows, BOS (130725) is the first input of each document, as today, and **EOS is its last target**, with byte length 0 (it stands for no text), as Team 6's loader does. So the model learns where a document ends, and bits per byte is unchanged (EOS adds no bytes). A document of exactly `L` tokens has its EOS as a one-token second window. Only packed training rows change: unpacked training and held-out data are as today.
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
- **Held-out evaluation.** Stays unpacked and without EOS, so its numbers stay comparable with every earlier run.
- **EOS id.** Read from the tokenizer (`<|endoftext|>`); `run.pack` stops with an error if the tokenizer has none. The window cache (`G5_DOCUMENT_CACHE_DIR`) is refused with packed rows, since it stores documents without EOS (it is already refused for the p1536 tokenizer).

**The contract with Team 6's loader: per piece, not per row.** Team 6's loader picks documents from many datasets to meet the mixture shares in every batch, so whole rows will differ from ours; the pieces must not. A piece is one window of one document, and two loaders agree when every piece has the same four fields:

| Field | Value |
|---|---|
| `targets` | the document's tokens as the shard stores them, at most `L` per piece; the last piece ends with EOS |
| `input_ids` | BOS, then `targets[:-1]`; a later piece of a long document starts with the last target of the piece before |
| `byte_lengths` | UTF-8 bytes of each target from Team 4's raw byte table; 0 for EOS |
| `pos_ids` | 0, 1, 2, ... restarting in every piece |

`doc_ids` (1, 2, 3 ... per piece in a row) depends on the row and is not part of the piece check.

`piece_check.py` computes these pieces from a shard alone (its `.bin`, `.idx.npy` and `.json`) and compares any loader's pieces field by field:

```
# our pieces of some documents, for Team 6 to compare with theirs
python teams/05-architecture/lab5/packed_rows/piece_check.py --shard <dir>/en-fineweb-edu-train-000000.bin --byte-table teams/04-ke2/results/tables/p1536-s0/raw_table_P32.npz --docs 0 1 2 --out ours.json
# check a loader's pieces (JSON list of {doc, piece, input_ids, targets, byte_lengths, pos_ids}); exit 1 on a difference
python teams/05-architecture/lab5/packed_rows/piece_check.py --shard ... --byte-table ... --check theirs.json
# check Team 5's reader: documents rebuilt as text from the byte table and read as the trainer reads them
python teams/05-architecture/lab5/packed_rows/piece_check.py --shard ... --byte-table ... --tokenizer <p1536 tokenizer.json> --docs 0 1 2 --against-reader
```

## 3. Approach and experiments

| # | Question | How it was answered | Answer |
|---|---|---|---|
| 1 | How much padding is there today? | #825 and #831; `measure_fill.py` | 35% to 43% real tokens at 2,048 |
| 2 | Which way of filling rows? | Four ways compared on two shards (below) | Best fit from a pool of 16 |
| 3 | How big a pool? | `measure_fill.py --pool` on 41 shards | 16: the gain flattens there |
| 4 | Does packing change what the model computes per token? | Tests c and j (section 6) | No: each token's output equals its document alone |
| 5 | Does packing lose SDPA's speed-up? (TSAI) | `measure_attention.py`, four arms on a T4 | No: SDPA with the mask is 1.29x eager |
| 6 | Is a training run needed? | Reasoned from 4 and 5 | Not for this PR (section 8) |
| 7 | Do our pieces match the pieces built from a shard alone? (Team 6) | `piece_check.py --against-reader` on real shard documents | Yes: 300 random documents of `en-fineweb-edu-train-000000`, plus documents of 2,048, 2,049 and 2,050 tokens (with EOS) and of 3 to 10 pieces, all match field by field |

**Ways of filling rows considered** (two sample-v0 shards, 2,048):

| Way | What | Fill | Why not / why |
|---|---|---:|---|
| 1. Pad (today) | One window per row | 43.1% | The problem |
| 2. Group by length | Rows of similar-length windows, row length cut to fit | about 99% | Rows of different lengths per step; not what the trainer or Team 6's loader do |
| 3. One long stream, cut every `L` | Join everything and cut | about 100% | Cuts documents at arbitrary places; only about 0.5% fewer rows than way 4 on the 41 shards (492,280 against 494,570, both measured before EOS was counted) |
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

**Fill on all 41 sample-v0 shards** (the `.idx.npy` files only; 1,200,725 documents, 1,008,187,260 content tokens, 1,009,387,985 in packed rows with each document's EOS; window order shuffled with seed 1234; "today" without EOS, as today's trainer):

```
python teams/05-architecture/lab5/packed_rows/measure_fill.py --index <41 shard .idx.npy files> --windows 2048 4096 --pool 1 4 8 16 32 64
```

| Window | Rows today | Rows packed | Fill today | Fill in strict order | Fill packed | Packed / today |
|---:|---:|---:|---:|---:|---:|---:|
| 2,048 | 1,397,555 | 495,174 | 35.2% | 77.9% | 99.5% | 0.35x |
| 4,096 | 1,263,667 | 246,981 | 19.5% | 80.3% | 99.8% | 0.20x |

Counting each document's EOS adds 604 packed rows at 2,048 (494,570 before) and 298 at 4,096 (246,683); the percentages do not change.

"Fill today" matches #825 for the same shards (35.22%, 19.48%), a check on the measurement. On the two shards of #831 (`code-python-train-000000`, `en-fineweb-edu-train-000000`; 106,665 documents) the packed fill is 99.2% at 2,048 and 99.6% at 4,096, within 1% of #831's estimate.

**Pool size** (`run.pack_pool`), all 41 shards:

| Pool | Fill at 2,048 | Fill at 4,096 |
|---:|---:|---:|
| 1 (strict order) | 77.9% | 80.3% |
| 4 | 97.1% | 98.0% |
| 8 | 99.0% | 99.4% |
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
| m | EOS ends each document | The last target is EOS with byte length 0; text bytes unchanged; without EOS documents are as today; a document of exactly `L` tokens gives EOS as a one-token piece |
| n | Pieces match the format | The reader's pieces equal `piece_check.py`'s pieces built from the stored document; a wrong EOS byte length is caught |
| o | Packed rows and the cache | A packed row carries both documents' EOS targets with 0 bytes and positions restarting; the window cache is refused with EOS |

All in `tests/test_packed_rows.py`: 24 passed. Full Team 5 suite: 328 passed, 12 skipped (CPU).

## 7. What is left

| Item | Who | Due |
|---|---|---|
| Run `piece_check.py --check` on pieces from their loader (or diff against `--out`), and confirm the per-piece contract (section 2) | Team 6 (Raj H, Vaibhav Lohar) | Asked on the PR, 29 Nov |
| Start and end of a document: BOS first, EOS as the last target with 0 bytes | Agreed with Team 6 (Vaibhav, 28 Nov); in the code and tested (m, n) | Done |
| The sampler offset in windows for the restart test | Team 7 | With their restart test |
| Mark #890 ready for review | Deepjyoti | After Team 6's check |

## 8. Limits

- **Speed on the training GPU.** The T4 numbers are for a T4 with this model in fp16; the ratios are the result, not the absolute speeds. Team 6's profile measures the training GPU.
- **A mask-aware flash kernel.** With a custom mask PyTorch cannot use the flash kernel; on the T4 SDPA is still 1.29x eager. A variable-length kernel might add more on the training GPU.
- **Training quality.** Not measured with a training run. Test c shows each token's output is unchanged by packing; what changes is that a step holds about twice the real tokens, which is a batch-size question for the main-run recipe, not for the format. A training-scale check belongs in Team 6's or the main run's A/B.
