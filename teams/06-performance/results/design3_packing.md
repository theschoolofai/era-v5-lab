# Design 3 (Lab 5): packing, one window per row vs packed with and without a document mask

**Owners:** Shashank, Sunil (official table on Sunil's GPU).
**Status: bring-up.** Measured on Colab Tesla T4 with the small G6 model and real FineWeb documents, in #890's packed-row format at Dry Run 2's step shape (section A) and in the first format (sections 1 to 3); document mask, study tool and tests in this PR. **Official Design 3** (Raj, 28 Nov): on V4 (1(b) baseline, unpatched) with two arms, one window per row and packed without the mask, until a V4 mask patch lands (owner to be agreed with Tharun); bpb on G5's `heldout_v1` (official bpb only there; any other held-out is provisional). Pending on Sunil's GPU, with Vaibhav's packing loader after S5.
**Raw results:** https://gist.github.com/shank343/a8f7d00c9a211aea0bd5b53fedaf8a1c (result JSONs, run logs).
**Brief:** "3. Packing. The dry run filled about a third of the positions in each row. Measure real tokens per row with one window per row, with packing and a document mask, and with packing and no mask: tokens per second and bits per byte." Fill here = scored targets / positions (Raj, 28 Nov; Dry Run 2, #869: median 41.2%).

## What is in this PR

- `models/gpt.py`: `document_mask(doc_ids, pos_ids=None)`, an opt-in context. Inside it, attention also blocks other documents (eager, or sdpa with an explicit boolean mask) and learned positions restart at each document; with `mtp` the t+2 target that would come from the next document is ignored. Outside it nothing changes. `triton` raises instead of ignoring the mask. It takes #890's packed-row fields as they are (`doc_ids` 1, 2, ... with 0 on padding; `pos_ids`).
- `correctness/test_document_mask.py`: a packed row with the mask equals each document run alone, in fp64 (logits, loss and every gradient; learned positions, RoPE, reversible stack); sdpa with the mask equals eager with the mask (MHA, GQA, RoPE; logits and every gradient); #890 rows with padding and explicit `pos_ids` equal the documents alone with no NaN; the mtp loss does not cross documents; one document per row equals the plain causal model; without the mask the documents leak.
- `perfkit/packing.py`: the study. Same model, seed, data order; three arms: `window` (one window per row, the rest padded and not scored: the G5 trainer's rows today), `packed_mask` (several windows per row, `document_mask`), `packed_nomask` (the same rows, no mask). Two row formats:
  - `--rows 890` (default, for the official run): #890's format, which Team 6's loader follows. Windows of at most T targets with BOS (or the previous token) as the first input, so every document token is a target and no end-of-text is; windows in #890's seeded order; packed rows by best fit from a pool of 16, never cutting a window. On the same windows and order the rows are identical to #890's `BatchStream.next_packed` (checked against #890's code, below).
  - `--rows stream`: the first format (sections 1 to 3): documents with their end-of-text end to end, rows cut every T (documents cut at row ends); window rows of T+1 tokens of one document.
  - In both formats every arm scores the same targets, each once (`correctness/test_packing.py`). `--attn eager|sdpa` picks the attention for every arm.
- Reported per arm: fill, median step time, positions/s, scored tokens/s, bytes/s (UTF-8 bytes of the scored targets, #888), peak memory, held-out bpb, and the window fill at T = 256 to 4096 from the document lengths.

**Check against #890's code.** `perfkit/packing.py`'s `pool_rows` and #890's `BatchStream.next_packed` (head `ceec7796`) on the same windows and the same seeded order give identical rows (`input_ids`, `targets`, `doc_ids`, `pos_ids`) for a whole pass: T = 64 / 256 / 64 / 128 with pools of 16 / 16 / 1 / 4 (216, 475, 192 and 200 rows; on the last row of a pass up to the end of its windows, where #890 continues into the next pass). A `--rows stream` CPU smoke run gives the same fill, loss and bpb as the first version of this PR.

## A. Bring-up in the #890 format, T=2048, B=8, equal steps

**Setup.** Commit `9d25e2d` of this PR (clean checkout), Colab **Tesla T4**, **fp16** (bf16 requested; the bench falls back on T4), torch 2.14.1, `configs/base.yaml` (d=256, 6 layers, 8 heads, dense MLP, reversible), `--rows 890` (pool of 16, window order seed 1234), `model.block_size=2048 run.batch_size=8 model.ce_impl=chunked`: Dry Run 2's row length and its 16,384 positions per step. Seeds 0 / 1, 10 warmup steps. Documents: the 5,971 FineWeb documents of the bring-up without their end-of-text (3,992,520 tokens, median 385); held-out: 200 val documents, #890 windows, one per row. **All bpb in this file is provisional**: official bpb is on G5's `heldout_v1` (Raj, 28 Nov). Every arm takes the **same number of optimizer steps**, so the packed arms train on 3.2x the tokens: the main-run regime. A pass has 6,432 window rows and 1,967 packed rows; 200 steps use 1,600 rows, so no row repeats.

**SDPA, 200 steps per arm**

| Arm | Fill | Step (median) | Positions/s | Scored tokens/s | Bytes/s | Held-out bpb (provisional) |
|---|---:|---:|---:|---:|---:|---:|
| window | 30.6% | 1,004.1 / 1,007.3 ms | 16,317 / 16,266 | 4,989 / 4,973 | 22,964 / 22,891 | 2.2196 / 2.2178 |
| packed_mask | 99.1% | 1,204.7 / 1,204.3 ms | 13,600 / 13,604 | 13,483 / 13,487 | 61,900 / 61,918 | 2.1140 / 2.1139 |
| packed_nomask | 99.1% | 1,036.8 / 1,035.4 ms | 15,803 / 15,823 | 15,666 / 15,686 | 71,924 / 72,017 | 2.1271 / 2.1253 |

Peak allocated 3.67 to 3.70 GiB.

**Eager, 100 steps per arm** (for the speed ratio; bpb after 100 steps is not comparable with the table above)

| Arm | Fill | Step (median) | Positions/s | Scored tokens/s | Bytes/s | Held-out bpb (provisional) |
|---|---:|---:|---:|---:|---:|---:|
| window | 29.4% | 1,894.8 / 1,894.1 ms | 8,647 / 8,650 | 2,540 / 2,541 | 11,652 / 11,656 | 2.3284 / 2.3278 |
| packed_mask | 99.1% | 1,930.2 / 1,929.6 ms | 8,488 / 8,491 | 8,411 / 8,414 | 38,792 / 38,805 | 2.2262 / 2.2253 |
| packed_nomask | 99.1% | 1,926.2 / 1,925.7 ms | 8,506 / 8,508 | 8,429 / 8,431 | 38,873 / 38,882 | 2.2324 / 2.2307 |

Peak allocated 4.33 to 4.39 GiB. The window fill is 30.6% over the first 1,600 shuffled windows and 29.4% over the first 800 (30.3% over all documents, section 1).

**Ratios** (seed 0 / seed 1, from the JSONs):

| | SDPA | Eager |
|---|---:|---:|
| Scored tokens/s, packed_mask / window | 2.70x / 2.71x | 3.31x / 3.31x |
| Scored tokens/s, packed_nomask / window | 3.14x / 3.15x | 3.32x / 3.32x |
| Step time, packed_mask / packed_nomask (cost of the mask) | +16.2% / +16.3% | +0.2% / +0.2% |
| Held-out bpb, packed_mask minus window | -0.106 / -0.104 | -0.102 / -0.102 |
| Held-out bpb, packed_mask minus packed_nomask | -0.013 / -0.011 | -0.006 / -0.005 |

Step time, eager / SDPA: window 1.89x / 1.88x, packed_mask 1.60x / 1.60x, packed_nomask 1.86x / 1.86x.

## First format: setup (sections 1 to 3)

Sections 1 to 3 are the first bring-up: `--rows stream` with eager attention (the first version of this PR).

Colab **Tesla T4**, dtype **fp16** (bf16 requested; the bench falls back on T4), base `081b6efe` = class main + #888 head (dirty: only the files of this PR), `configs/base.yaml` (d=256, 6 layers, dense MLP, reversible) with `model.attn_impl=eager`, seeds 0 and 1, 10 warmup steps. Documents: 5,971 FineWeb documents (3,998,491 tokens, median 386 tokens) from 2 train shards (`dataio.prepare_fineweb`, BrahmicTokenizer-131K); held-out: the first 200 documents of the val shard, scored one window per row in every arm. **bpb is provisional**: same held-out bytes for all arms, but not the G5 held-out set.

## 1. Window fill against row length (from the document lengths)

| T | 256 | 512 | 1024 | 2048 | 4096 |
|---|---:|---:|---:|---:|---:|
| window fill | 84.2% | 70.8% | 50.8% | 30.3% | 16.0% |

Packed rows fill 99.8% at both lengths measured (the 0.2% is the one target per document boundary).

## 2. T=256, B=16, 200 steps per arm

Seed 0 / seed 1.

| Arm | Fill | Step (median) | Positions/s | Scored tokens/s | Bytes/s | Held-out bpb (provisional) |
|---|---:|---:|---:|---:|---:|---:|
| window | 83.8% | 216.5 / 223.3 ms | 18,916 / 18,341 | 15,849 / 15,368 | 74,029 / 71,781 | 2.2428 / 2.2421 |
| packed_mask | 99.8% | 223.4 / 227.9 ms | 18,332 / 17,969 | 18,303 / 17,941 | 85,157 / 83,472 | 2.2189 / 2.2209 |
| packed_nomask | 99.8% | 223.4 / 228.2 ms | 18,336 / 17,948 | 18,308 / 17,920 | 85,178 / 83,375 | 2.2228 / 2.2235 |

Peak allocated 6.54 GiB in all arms. Equal steps, so the packed arms saw 19% more scored tokens (817,919 vs 686,392).

## 3. T=2048, B=4, equal scored-token budget

T=2048 is Dry Run 2's row length (`teams/05-architecture/configs/arms/t2.yaml`: block_size 2048, batch_size 8); B=4 here because the notebook ran on a 16 GB GPU, so a step has 8,192 positions, half of Dry Run 2's. `model.ce_impl=chunked`. Budget: every arm trains until it has scored 492,044 tokens, the window arm's count in 200 steps (packed arms: 61 steps, 498,927 tokens).

| Arm | Steps | Fill | Step (median) | Positions/s | Scored tokens/s | Bytes/s | Held-out bpb (provisional) |
|---|---:|---:|---:|---:|---:|---:|---:|
| window | 200 | 30.0% | 965.8 / 977.5 ms | 8,482 / 8,380 | 2,547 / 2,517 | 11,985 / 11,841 | 2.2933 / 2.2917 |
| packed_mask | 61 | 99.8% | 1,009.6 / 1,011.4 ms | 8,114 / 8,099 | 8,101 / 8,087 | 38,007 / 37,938 | 2.3742 / 2.3699 |
| packed_nomask | 61 | 99.8% | 999.1 / 999.4 ms | 8,199 / 8,197 | 8,186 / 8,184 | 38,405 / 38,395 | 2.3823 / 2.3799 |

Peak allocated 2.48 to 2.49 GiB (B=8 would likely fit a T4; the notebook's 20 GB threshold was cautious).

## Findings

From section A (#890 format, T=2048, B=8, equal steps):

1. **Packing with the mask gives 2.7x the scored tokens per second with SDPA, 3.3x with eager.** One window per row fills 30.6% of the positions; packed rows fill 99.1%. With SDPA the gain is smaller than the fill ratio (3.24x) because the mask costs step time (finding 2). With eager the mask is nearly free, so the gain follows the fill.
2. **With SDPA the mask costs 16% of the step; with eager 0.2%.** With an explicit [B, 1, T, T] mask SDPA reads and applies the full mask instead of its built-in causal one. SDPA is still faster than eager with the mask (1.60x the step speed; window rows 1.88x), so packed_mask with SDPA is the fastest masked arm: 13,483 scored tokens/s against 8,411 with eager. A variable-length or block-sparse kernel could recover the 16% (#890 notes the same for its flash kernel).
3. **At equal steps packing improves bpb by about 0.10.** packed_mask 2.114 against window 2.220 / 2.218 after 200 steps, both seeds: the packed rows carry 3.2x the tokens per step. This is the main-run regime, and it settles the question the equal-token run (finding 7) left open.
4. **The mask improves bpb in every pair.** packed_mask beats packed_nomask by 0.011 to 0.013 with SDPA (200 steps) and 0.005 to 0.006 with eager (100 steps); the unmasked rows are 16% faster with SDPA. The official V4 run starts without the mask (Next, 1); this is the case for adding it once V4 can mask (Next, 2).

From sections 1 to 3 (first format, eager):

5. **The row length decides the gain.** Window fill falls from 84.2% at T=256 to 30.3% at T=2048 and 16.0% at T=4096 (section 1); at T=256 packing gains only 16% scored tokens/s.
6. **The mask helped bpb there too**: 0.0026 to 0.0039 at T=256 and 0.008 to 0.010 at T=2048, both seeds.
7. **Equal tokens is not equal steps (negative result).** With the token budget fixed and B fixed, the packed arms take 61 optimizer steps where the window arm takes 200, and end with worse held-out bpb (2.37 vs 2.29): in this short run the number of updates matters more than the tokens. Finding 3 is the comparison at equal steps.

## What this cannot tell

- The model: G6's small dense model with softmax attention, not V4 (gated DeltaNet + GSA). For the DeltaNet layers a document mask means resetting the recurrent state at each document start (variable-length sequences), not an attention mask; that is not implemented here.
- Data and tokenizer: FineWeb English with BrahmicTokenizer-131K, not the main-run mix with p1536; fill depends on the document-length mix (Dry Run 2: 41.2% at T=2048, here 30.3%).
- Shape and GPU: T4, fp16, B=8 at T=2048 (B=4 in sections 1 to 3); short runs (61 to 200 steps), two seeds; bpb provisional. The SDPA mask cost depends on the kernels the GPU has; the T4 has no flash kernel at all.
- Loader: packing is done in this script; Vaibhav's mixture-aware loader (S5) does the packing in the main pipeline.

## Next

1. Official runs on Sunil's GPU against the 1(b) baseline (V4 body + KAS head, p1536; Sunil's entry point: perfkit step loop + #888 metrics): one window per row and packed without the mask (Raj, 28 Nov), fixed steps at the baseline shape, at least 2 seeds, bpb on `heldout_v1` (`teams/05-architecture/heldout_v1/data/heldout_v1.jsonl`, the file named by `teams/05-architecture/results/heldout_v1.sha256`; fingerprints v2, Raj 28 Nov). The bpb here is on 200 FineWeb val documents, not `heldout_v1`, so it is provisional.
2. packed_mask on V4 once a mask patch lands (owner to be agreed with Tharun): a mask in the GSA layers and a state reset per document in the DeltaNet layers. Finding 4 is the reason to add it.
3. Rows from Vaibhav's loader after S5 (#890 format): check they equal `--rows 890` on the same windows and order.
4. The SDPA mask cost (finding 2) on the training GPU, and a variable-length or block-sparse attention kernel if it stays large.

## Commands

Section A (`--rows 890`, the default; notebook `g6_w5_design3_890_sdpa.ipynb` runs these on a checkout of this PR):

```bash
cd teams/06-performance
python -m dataio.prepare_fineweb --out /content/fineweb-brahmic131k --train-shards 2 --tokens-per-shard 2000000
python -B perfkit/packing.py --rows 890 --source fineweb --data-dir /content/fineweb-brahmic131k --warmup 10 --seeds 0 1 --out packing890_T2048_B8_sdpa_steps200.json --attn sdpa --steps 200 run.dtype=bf16 run.batch_size=8 model.block_size=2048 model.ce_impl=chunked
python -B perfkit/packing.py --rows 890 --source fineweb --data-dir /content/fineweb-brahmic131k --warmup 10 --seeds 0 1 --out packing890_T2048_B8_eager_steps100.json --attn eager --steps 100 run.dtype=bf16 run.batch_size=8 model.block_size=2048 model.ce_impl=chunked
python -m pytest correctness/test_document_mask.py correctness/test_packing.py -q --all-configs
```

Sections 1 to 3 (`--rows stream`; the first version of this PR ran the same commands without the flag, which was then the only format):

```bash
python -B perfkit/packing.py --rows stream --source fineweb --data-dir /content/fineweb-brahmic131k --warmup 10 --seeds 0 1 --out packing_T256_B16_steps200.json --steps 200 run.dtype=bf16 run.batch_size=16
python -B perfkit/packing.py --rows stream --source fineweb --data-dir /content/fineweb-brahmic131k --warmup 10 --seeds 0 1 --out packing_T2048_B4_budget.json --steps 200 --equal-budget run.dtype=bf16 run.batch_size=4 model.block_size=2048 model.ce_impl=chunked
```

## Files (sha256)

| File | sha256 |
|---|---|
| `packing890_T2048_B8_sdpa_steps200.json` | `685cc521906b7c92632df94346e9e10f700d05dedf573495b544c96afdcf9848` |
| `packing890_T2048_B8_eager_steps100.json` | `0e764e0ca52de9880434269c4e6b0abe2f97578ac7b92a0edc64eefe1d854424` |
| `design3_890_tesla_t4.log` | `8df69a39ae3e9bec8b27cc7864e75d23effe9d10325be25c80bcf4103cfe37f4` |
| `packing_T256_B16_steps200.json` | `23ac219bcce2e3c5f3ca7a447a94d924f95456e06ae89fe91cb5c37e9a14685a` |
| `packing_T2048_B4_budget.json` | `62285d577dfbeff7ed8a2843e409fd9852a48cf5f9a6688c956f17e05475de50` |
| `design3_tesla_t4.log` | `2b064f93eb9bc4da64cc5536c1d8e78e5c0cdb27cba20c90c37170f06b838f9d` |
