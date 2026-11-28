# Design 3 (Lab 5): packing, one window per row vs packed with and without a document mask

**Owners:** Shashank, Sunil (official table on Sunil's GPU).
**Status:** bring-up done on Colab Tesla T4 with the small G6 model and real FineWeb documents; document mask, study tool and tests in this PR. Official table pending: the 1(b) baseline (V4 body + KAS head, p1536) on Sunil's GPU, and Vaibhav's packing loader after S5.
**Raw results:** https://gist.github.com/shank343/a8f7d00c9a211aea0bd5b53fedaf8a1c (result JSONs, run log).
**Brief:** "3. Packing. The dry run filled about a third of the positions in each row. Measure real tokens per row with one window per row, with packing and a document mask, and with packing and no mask: tokens per second and bits per byte." Fill here = scored targets / positions (Raj, 28 Nov; Dry Run 2, #869: median 41.2%).

## What is in this PR

- `models/gpt.py`: `document_mask(doc_ids, pos_ids=None)`, an opt-in context. Inside it, attention also blocks other documents (eager, or sdpa with an explicit boolean mask) and learned positions restart at each document; with `mtp` the t+2 target that would come from the next document is ignored. Outside it nothing changes. `triton` raises instead of ignoring the mask. It takes #890's packed-row fields as they are (`doc_ids` 1, 2, ... with 0 on padding; `pos_ids`).
- `correctness/test_document_mask.py`: a packed row with the mask equals each document run alone, in fp64 (logits, loss and every gradient; learned positions, RoPE, reversible stack); sdpa with the mask equals eager with the mask (MHA, GQA, RoPE; logits and every gradient); #890 rows with padding and explicit `pos_ids` equal the documents alone with no NaN; the mtp loss does not cross documents; one document per row equals the plain causal model; without the mask the documents leak.
- `perfkit/packing.py`: the study. Same model, seed, data order; three arms: `window` (one window per row, the rest padded and not scored: the G5 trainer's rows today), `packed_mask` (several windows per row, `document_mask`), `packed_nomask` (the same rows, no mask). Two row formats:
  - `--rows 890` (default, for the official run): #890's format, which Team 6's loader follows. Windows of at most T targets with BOS (or the previous token) as the first input, so every document token is a target and no end-of-text is; windows in #890's seeded order; packed rows by best fit from a pool of 16, never cutting a window. On the same windows and order the rows are identical to #890's `BatchStream.next_packed` (checked against #890's code, below).
  - `--rows stream`: the bring-up format of the tables below: documents with their end-of-text end to end, rows cut every T (documents cut at row ends); window rows of T+1 tokens of one document.
  - In both formats every arm scores the same targets, each once (`correctness/test_packing.py`). `--attn eager|sdpa` picks the attention for every arm.
- Reported per arm: fill, median step time, positions/s, scored tokens/s, bytes/s (UTF-8 bytes of the scored targets, #888), peak memory, held-out bpb, and the window fill at T = 256 to 4096 from the document lengths.

**Check against #890's code.** `perfkit/packing.py`'s `pool_rows` and #890's `BatchStream.next_packed` (head `ceec7796`) on the same windows and the same seeded order give identical rows (`input_ids`, `targets`, `doc_ids`, `pos_ids`) for a whole pass: T = 64 / 256 / 64 / 128 with pools of 16 / 16 / 1 / 4 (216, 475, 192 and 200 rows; on the last row of a pass up to the end of its windows, where #890 continues into the next pass). A `--rows stream` CPU smoke run gives the same fill, loss and bpb as the first version of this PR.

## Setup

The numbers below are the bring-up: `--rows stream` with eager attention (the first version of this PR). The #890 format with sdpa is not measured yet (Next, 1).

Colab **Tesla T4**, dtype **fp16** (bf16 requested; the bench falls back on T4), base `081b6efe` = class main + #888 head (dirty: only the files of this PR), `configs/base.yaml` (d=256, 6 layers, dense MLP, reversible) with `model.attn_impl=eager`, seeds 0 and 1, 10 warmup steps. Documents: 5,971 FineWeb documents (3,998,491 tokens, median 386 tokens) from 2 train shards (`dataio.prepare_fineweb`, BrahmicTokenizer-131K); held-out: the first 200 documents of the val shard, scored one window per row in every arm. **bpb is provisional**: same held-out bytes for all arms, but not the G5 held-out set.

## 1. Window fill against row length (from the document lengths)

| T | 256 | 512 | 1024 | 2048 | 4096 |
|---|---:|---:|---:|---:|---:|
| window fill | 84.2% | 70.8% | 50.8% | 30.3% | 16.0% |

Packed rows fill 99.8% at both lengths measured (the 0.2% is the one target per document boundary).

## 2. T=256, B=16, 200 steps per arm

Seed 0 / seed 1.

| Arm | Fill | Step (median) | Positions/s | Scored tokens/s | Bytes/s | Held-out bpb |
|---|---:|---:|---:|---:|---:|---:|
| window | 83.8% | 216.5 / 223.3 ms | 18,916 / 18,341 | 15,849 / 15,368 | 74,029 / 71,781 | 2.2428 / 2.2421 |
| packed_mask | 99.8% | 223.4 / 227.9 ms | 18,332 / 17,969 | 18,303 / 17,941 | 85,157 / 83,472 | 2.2189 / 2.2209 |
| packed_nomask | 99.8% | 223.4 / 228.2 ms | 18,336 / 17,948 | 18,308 / 17,920 | 85,178 / 83,375 | 2.2228 / 2.2235 |

Peak allocated 6.54 GiB in all arms. Equal steps, so the packed arms saw 19% more scored tokens (817,919 vs 686,392).

## 3. T=2048, B=4, equal scored-token budget

T=2048 is Dry Run 2's row length (`teams/05-architecture/configs/arms/t2.yaml`: block_size 2048, batch_size 8); B=4 here because the notebook ran on a 16 GB GPU, so a step has 8,192 positions, half of Dry Run 2's. `model.ce_impl=chunked`. Budget: every arm trains until it has scored 492,044 tokens, the window arm's count in 200 steps (packed arms: 61 steps, 498,927 tokens).

| Arm | Steps | Fill | Step (median) | Positions/s | Scored tokens/s | Bytes/s | Held-out bpb |
|---|---:|---:|---:|---:|---:|---:|---:|
| window | 200 | 30.0% | 965.8 / 977.5 ms | 8,482 / 8,380 | 2,547 / 2,517 | 11,985 / 11,841 | 2.2933 / 2.2917 |
| packed_mask | 61 | 99.8% | 1,009.6 / 1,011.4 ms | 8,114 / 8,099 | 8,101 / 8,087 | 38,007 / 37,938 | 2.3742 / 2.3699 |
| packed_nomask | 61 | 99.8% | 999.1 / 999.4 ms | 8,199 / 8,197 | 8,186 / 8,184 | 38,405 / 38,395 | 2.3823 / 2.3799 |

Peak allocated 2.48 to 2.49 GiB (B=8 would likely fit a T4; the notebook's 20 GB threshold was cautious).

## Findings

1. **At Dry Run 2's row length, one window per row wastes about 70% of the positions.** Window fill is 30.0% at T=2048 on these documents (Dry Run 2 logged 41.2% on its own data and tokenizer). Packing fills 99.8%, so the same step processes **3.2x the scored tokens** (8,101 vs 2,547 per second with the mask) and 3.2x the bytes. At T=256 the gain is only 16% because most documents already fill a 256-token window.
2. **The mask costs little.** Step time with the mask is within 0.1% of the unmasked packed rows at T=256 and 1.1% to 1.2% above them at T=2048 (eager attention builds a [B, 1, T, T] mask).
3. **The mask helps bpb a little, in every pair.** packed_mask beats packed_nomask by 0.0026 to 0.0039 at T=256 and 0.008 to 0.010 at T=2048, both seeds.
4. **Equal tokens is not equal steps (negative result).** With the token budget fixed and B fixed, the packed arms take 61 optimizer steps where the window arm takes 200, and end with worse held-out bpb (2.37 vs 2.29). In this short run the number of updates matters more than the tokens; it is not evidence that packing hurts quality. A fair quality comparison needs equal steps with a larger batch for the window arm, or the main-run regime (fixed steps, packed rows carry 3.2x the data per step).
5. Wall time for the same 492k scored tokens: window 200 x 0.97 s = 193 s, packed 61 x 1.0 s = 61 s.

## What this cannot tell

- The model: G6's small dense model with softmax attention, not V4 (gated DeltaNet + GSA). For the DeltaNet layers a document mask means resetting the recurrent state at each document start (variable-length sequences), not an attention mask; that is not implemented here.
- Data and tokenizer: FineWeb English with BrahmicTokenizer-131K, not the main-run mix with p1536; fill depends on the document-length mix (Dry Run 2: 41.2% at T=2048, here 30.0%).
- Shape and GPU: T4, fp16, B=4 at T=2048; short runs (61 to 200 steps), two seeds; bpb provisional.
- Loader: packing is done in this script; Vaibhav's mixture-aware loader (S5) does the packing in the main pipeline.

## Next

1. The same study in the #890 format with sdpa (`--rows 890 --attn sdpa`), as the bridge between these numbers and the official ones.
2. Official runs on Sunil's GPU against the 1(b) baseline (V4 body + KAS head, p1536; Sunil's entry point: perfkit step loop + #888 metrics): fixed steps at the baseline shape, at least 2 seeds. Needs the V4 body to take `doc_ids`: a mask in the GSA layers and a state reset per document in the DeltaNet layers.
3. Rows from Vaibhav's loader after S5 (#890 format): check they equal `--rows 890` on the same windows and order.
4. Quality at equal steps: window arm with a batch scaled by 1 / fill against packed rows.

## Commands

The bring-up tables above (`--rows stream`; the first version of this PR ran the same commands without the flag, which was then the only format):

```bash
cd teams/06-performance
python -m dataio.prepare_fineweb --out /content/fineweb-brahmic131k --train-shards 2 --tokens-per-shard 2000000
python -B perfkit/packing.py --rows stream --source fineweb --data-dir /content/fineweb-brahmic131k --warmup 10 --seeds 0 1 --out packing_T256_B16_steps200.json --steps 200 run.dtype=bf16 run.batch_size=16
python -B perfkit/packing.py --rows stream --source fineweb --data-dir /content/fineweb-brahmic131k --warmup 10 --seeds 0 1 --out packing_T2048_B4_budget.json --steps 200 --equal-budget run.dtype=bf16 run.batch_size=4 model.block_size=2048 model.ce_impl=chunked
python -m pytest correctness/test_document_mask.py correctness/test_packing.py -q --all-configs
```

The #890 format (Next, 1): the same commands with `--rows 890 --attn sdpa` in place of `--rows stream`.

## Files (sha256)

| File | sha256 |
|---|---|
| `packing_T256_B16_steps200.json` | `23ac219bcce2e3c5f3ca7a447a94d924f95456e06ae89fe91cb5c37e9a14685a` |
| `packing_T2048_B4_budget.json` | `62285d577dfbeff7ed8a2843e409fd9852a48cf5f9a6688c956f17e05475de50` |
| `design3_tesla_t4.log` | `2b064f93eb9bc4da64cc5536c1d8e78e5c0cdb27cba20c90c37170f06b838f9d` |
