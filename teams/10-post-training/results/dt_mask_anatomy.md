# Released Deletion Tuning masks, per expert: unseen MoE experts and our dry run 2 DT arm (28 Nov 2026)

**Evidence level: independent study; the numbers come from the authors' released files.** It reads the GRPO masks the
Deletion Tuning authors released (`Jacklu0831/deletion-tuning-masks`) and the base model's released weights. It also
runs the official calibration prompts through a 4-bit copy of Qwen3-30B-A3B-Base, and reads TSAI's dry run 2 record
(#869). The only training is a one-matrix CPU toy of G10's own `dt/mask.py`. It is not Gate 4 evidence. The
`--dt-unseen` ablation itself stays in `lab5_dt_muon_recompute.md` §3. Section 4 is a prediction and a toy for the
dry run 2 DT arm, not a run.

Script: `../dt/mask_anatomy.py` (subcommands `masks`, `weights`, `calib`, `routing`, `load`, `revive`), with tests in
`../dt/tests/test_mask_anatomy.py`. The output of every command is in `dt_mask_anatomy_evidence/`, with local paths
replaced by placeholders such as `<masks>`.

## Summary

1. The paper released one MoE mask: Qwen3-30B-A3B-Base, GRPO on SimpleRL-Zoo. In it, **18 of the 6,144 expert gate
   matrices are 39.6% to 42.1% deleted, and they hold 50.5% of all its deletions**. Every other expert is at most
   0.166% deleted (mean 0.118%).
2. The 18 are close to the official start for an expert with no Wanda prior, which is 50% deleted at random. They end
   about 41% deleted, with only a mild lean: 47.6% of their smallest tenth of weights are deleted, against 36.9% of
   their largest tenth. The other experts delete their smallest weights.
3. We rebuilt the official calibration prompts and ran them through a 4-bit copy of the model. **15 of the 18 got 0
   calibration tokens and the other 3 got 1 to 4.** So, within the limits in §3 and §6, the heavy experts are the ones
   the Wanda calibration did not reach. That is what `--dt-unseen official` does.
4. Our dry run 2 record has **two experts at 0 routed tokens in every snapshot from step 1,000 to 1,200** (block 3
   expert 11 and block 7 expert 13). If the 64 calibration rows miss them too, the DT report should show
   `layers_without_scores` of at least 2. The step-0 deletion would then be about 0.92% instead of about 0.18% under
   `--dt-unseen keep` (arithmetic). In G10's code the regulariser is expected to revive part of an unscored expert during
   training (toy, §4). In that one-matrix toy, how much depends on how far gradient clipping scales the gradients: from 50% to 4.4%
   after 243 steps at full gradient, but only to 43% at 1/1,000 of it (§4).

## 1. Per-expert deletions in the released MoE mask

```bash
python dt/mask_anatomy.py masks <masks>/grpo/qwen3-30b-a3b-base-simplerl-zoo --partners 1
```
```
6144 gate matrices of 1,572,864 weights; deleted 22,954,392 = 0.2375%
heavy experts (> 1% deleted): 18, 39.625% to 42.109%, holding 50.5% of all deletions
other experts: mean 0.1180%, median 0.1170%, max 0.1663%
heavy (layer:expert): 2:105 3:83 7:102 13:56 13:99 16:86 16:96 17:101 18:36 25:56 28:86 37:56 40:86 41:24 42:51 44:74 44:124 46:65
per-layer deleted share: median 0.118% (0.113% to 0.122%) in the 33 layers without a heavy expert; 0.42% to 0.76% in the 15 with one
```

- Decoding follows the official `src/apply_mask.py` (zstd, then `np.unpackbits`, then the first `numel` bits; 1 keeps).
  It reproduces `config.json`'s `total_params` and `zero_params` exactly; the script stops if they differ.
- No expert lies between 0.17% and 39.6%. The masks cover every expert's `gate_proj` and nothing else
  (`mask_target_modules: [gate_proj]` in the official `hf_model.yaml`); the router is not masked.

## 2. What the heavy experts delete

`--partners 1` also picks one other expert from the same layer for each heavy expert. It uses one
`np.random.default_rng(1)` stream, with the heavy experts in order and no repeats. The bf16 base weights of these 36
gate matrices were read from `Qwen/Qwen3-30B-A3B-Base` (revision `1b75feb7`) by HTTP range requests:

```bash
python dt/mask_anatomy.py weights <masks>/grpo/qwen3-30b-a3b-base-simplerl-zoo Qwen/Qwen3-30B-A3B-Base 2:105 2:60 3:83 ...
```

| pooled over the weights of | deleted | mean abs W, deleted / kept | mean abs-W rank of deleted (0 smallest, 1 largest) | share deleted among the smallest 10% abs W | among the largest 10% | deleted with W < 0 |
|---|---:|---:|---:|---:|---:|---:|
| 18 heavy experts | 40.905% | 0.917 | 0.479 | 47.57% | 36.85% | 0.500 |
| 18 other experts | 0.117% | 0.481 | 0.250 | 0.58% | 0.05% | 0.498 |

- If deletions were random, the mean rank would be 0.5 and both tenths would sit at the overall share. Heavy experts
  are close to that (0.479; 47.6% against 36.9%). The other experts delete mostly small weights (0.250; 0.58% against
  0.05%).
- The official code explains the start (read, not run). `differentiable_mask.py` starts every logit at N(0, 0.01²).
  `wanda_calibration.py` then shifts each scored matrix: its lowest-η Wanda scores go down by 3 std, the rest go up.
  An expert that no calibration token reached has no scores, so it gets no shift and starts about 50% deleted. G10's
  `dt/mask.py::apply_wanda_prior` describes the same case for `unseen="official"`.
- The heavy experts end near 41%, not 50%, with a lean towards keeping their larger weights. So their logits did get
  gradients in training. The official stack pins transformers 4.57.6 (`requirements_grpo.txt`). Its Qwen3-MoE block
  runs only the experts a token was routed to, and the regulariser term is computed inside the masked layer's forward
  (`sparse_linear.py`). So the training forward passes on the rollouts routed at least some tokens to these experts. We
  cannot tell how many. The change fits the regulariser, which the actor subtracts from the loss (`dp_actor.py`): it
  rewards keeping weights, and more so for large |W|. Their final masks have about 41% of the gate weights deleted.

## 3. Routing check: the heavy experts are the ones calibration did not reach

The official `verl_adapters._wanda_scores` calibrates on 2,048 prompts from the training parquet
(`df.sample(n=2048, random_state=42)`). Each prompt gets the chat template and is right-padded to 512 tokens. The pad
positions count too: `compute_wanda_scores` adds the input norms of every position, with no padding mask. `calib`
rebuilds exactly that text, and `llama-imatrix` (llama.cpp b11669) counts the tokens routed to each expert:

```bash
python dt/mask_anatomy.py calib <SimpleRL-Zoo-Data>/simplelr_qwen_level3to5/train.parquet <Qwen3-30B-A3B-Base tokenizer> parts/
for p in parts/part*.txt; do llama-imatrix -m Qwen3-30B-A3B-Base.Q4_K_M.gguf -f $p -o ${p%.txt}.gguf -c 512 -ngl 99 --parse-special --no-ppl; done
python dt/mask_anatomy.py routing <masks>/grpo/qwen3-30b-a3b-base-simplerl-zoo parts/part*.gguf
```
```
2,048 prompts of 8,523 rows in ...; each 512 tokens after padding ('<|endoftext|>'); 230,928 real + 817,648 pad tokens; truncated: 22
48 layers x 128 experts; routed slots per layer 8,388,608 to 8,388,608; layer medians 4,348 to 14,932
experts with zero calibration tokens: 20; heavy experts: 18; heavy with zero tokens: 15; zero-token experts that are not heavy: 5
```

- 15 heavy experts got 0 tokens. The other three got 2 (18:36), 4 (41:24) and 1 (42:51), against medians of 4,730,
  13,167 and 9,559 in their layers. The per-expert lines are in `dt_mask_anatomy_evidence/routing.txt`.
- Five ordinary experts also got 0 tokens here (0:15, 23:83, 40:96, 41:107, 42:11) and are 0.070% to 0.111% deleted.
  Two things can make this replay differ from the authors' calibration:
  - **The 4-bit copy:** near-ties in routing.
  - **The pad positions**, which are 817,648 of the 1,048,576 positions. verl's `fsdp_workers.py` loads the actor
    with `flash_attention_2` by default (not overridden in `train_grpo.sh` or `simplerl_zoo.yaml`). With a padding
    mask, transformers 4.57.6 returns a zero attention output at pad positions (`pad_input`, which fills zeros). So in the authors' run
    every pad position probably had the same hidden state and the same experts. In llama.cpp the pads attend to every
    earlier position, so they can reach more experts.

  This may also explain the 3 heavy experts with 1 to 4 tokens.
- `-c 512` makes one llama.cpp chunk one padded prompt, and `calib` checks that each part tokenizes back to exactly
  64 × 512 tokens (the HF tokenizer), and every `llama-imatrix` log reports 64 chunks with `n_ctx=512`. `llama-imatrix` reads the text with escapes off (`params.escape = false` in b11669); passing `-e`
  would turn the prompts' LaTeX backslashes into escapes and change the count. The 32 parts were checked byte for byte
  against the ones behind these counts.

## 4. What this means for our dry run 2 DT arm (a prediction and a toy, not a run)

TSAI's dry run 2 record (#869, `teams/05-architecture/results/dryrun2-1234/metrics.jsonl`) logs `expert_load` every 50
steps. It counts the routed token slots per expert over one training step, for scored positions only (`targets != -100`), with the
balancer's `router_bias` included (`train_week2.py`, `model.py`).

```bash
python dt/mask_anatomy.py load metrics.jsonl --gate 768x512
```
```
5 snapshots, steps 1,000 to 1,200; 8 layers x 16 experts
step 1,200: routed slots per layer 17,394 to 17,394, even share per expert 1,087 to 1,087
experts at 0 tokens in all 5 snapshots: 3:11 7:13
experts below 1% of the even share at step 1,200 (counts per snapshot):
  1:1: 3,402, 1,658, 2, 1,129, 9 (even share 1,087)
  2:11: 3,437, 2,235, 47, 4, 3 (even share 1,087)
  3:11: 0, 0, 0, 0, 0 (even share 1,087)
  7:13: 0, 0, 0, 0, 0 (even share 1,087)
expected deleted share at step 0 (arithmetic, not run; --dt-targets g5_gate: one masked 768x512 gate per routed expert and 1 shared, 136 in all; a calibrated one 0.1834%):
  if the experts at 0 in every snapshot (2) get no calibration token: official 0.916%, keep 0.183%
  if all experts listed above (4) get no calibration token: official 1.649%, keep 0.182%
```

- Over all 24 snapshots (`--last 24`), 7:13 is at 0 from step 750 on and 3:11 from step 1,000 on. Experts 1:1 and
  2:11 are near 0 at step 1,200 but were not idle earlier (1:1 went from 2 tokens to 1,129 and back to 9).
- The dry run 2 DT job passes `--dt-targets g5_gate` (`jobs/2026-11-26-g10-dryrun2-dt-vs-fft.md`). It passes no
  `--dt-unseen` and no `--dt-calib-rows`, so it runs with `official` and 64 rows (`capstone/dryrun2_dt_compare.py`).
  With `g5_gate`, each routed expert has one masked matrix, so `layers_without_scores` counts the idle routed experts
  directly. The shared expert sees every token.
- The calibration routes tokens the way training does (`dt/mask.py::wanda_scores` uses `g5_expert_choice`, which
  includes `router_bias`). So an expert the trained router never picked in the last snapshots will probably get none
  of the 64 rows either. This holds only if the SFT rows route like the pretraining text (one English web shard).
- **The step-0 gap is not the end state in our code.** Unlike the official stack, G10's
  `dt/mask.py::regulariser_backward_` adds the keep-gradient to every masked layer, routed or not, so an idle expert's
  logits still move. `revive` runs `dt/mask.py` on one unscored 768×512 gate with only the regulariser and the job's
  DT settings (AdamW lr 5e-4, warmup 10, cosine to 0.1, betas 0.9/0.95, eps 1e-8, wd 0, λ 1e-5 decaying to 0, α 100
  to 1000, 243 steps):

  | gradient scale | `official`: deleted at step 0 / 50 / 243 | `keep`: deleted at step 0 / 243 |
  |---:|---|---|
  | 1 | 50.127% / 9.446% / 4.356% | 0.136% / 0.000% |
  | 0.1 | 50.127% / 25.124% / 17.869% | 0.136% / 0.000% |
  | 0.01 | 50.127% / 38.712% / 32.224% | 0.136% / 0.008% |
  | 0.001 | 50.127% / 47.450% / 43.149% | 0.136% / 0.062% |

  The regulariser's gradients are small: at scale 1 and step 0 their median is 7.3e-8, and 82% are above Adam's eps
  1e-8. So how far they get depends on their size against eps. Two things set that size:
  - **The clip.** The global clip (`--clip 1.0` on the gradient norm of all trainable parameters) multiplies every
    gradient by 0.1, 0.01 or 0.001 at a gradient norm of 10, 100 or 1,000.
  - **W².** The gradient grows with W². The toy's `nn.Linear`-init weights have mean |W| of about 0.022, and the
    trained gates may be larger or smaller.

  So the logged gradient norm alone does not pick the row. The real run will show which case applies. Its log records
  `grad_norm` at each logged step, and the DT report's `deletion_at_init` and `deletion_final` give `per_layer_max`, which shows
  whether an unscored expert stays highly deleted. This is a toy: one matrix with `nn.Linear` init weights instead of
  the trained ones, no task gradient, and a constant scale instead of the real clip.
- `keep` changes only matrices without scores, so every calibrated expert starts the same under both policies. It starts
  the unseen ones at the same Φ(−3) ≈ 0.135% tail as the rest. The stand-in in `lab5_dt_muon_recompute.md` §3 shows
  the same step-0 effect (16.76% to 16.87% under `official`, against 0.16% to 0.18% under `keep`, with 4 of 12 experts
  idle). An idle expert's deleted weights matter once tokens reach it, and our SFT, Indic or code text may reach
  experts that this English web shard does not.

## 5. Deletion share by model size (input for design task 2, `lab5_dt_muon_recompute.md` §4)

Same `masks` command on each released Qwen GRPO mask (SimpleRL-Zoo). The share is of the targeted `gate_proj`
weights, not of all weights.

| Model | gate matrices | weights per matrix | deleted share |
|---|---:|---:|---:|
| Qwen2.5-0.5B | 24 | 4,358,144 | 0.1908% |
| Qwen2.5-3B | 36 | 22,544,384 | 0.1447% |
| Qwen2.5-7B | 28 | 67,895,296 | 0.1663% |
| Qwen2.5-14B | 48 | 70,778,880 | 0.1411% |
| Qwen3-30B-A3B-Base (MoE) | 6,144 | 1,572,864 | 0.2375% (0.1180% mean over the 6,126 experts that are not heavy) |

The dense shares stay between 0.14% and 0.19% at every size and do not move steadily with size. They are close to the
step-0 share of about 0.18% (0.1834% by the arithmetic in §4; `dt_phi_moe.md` measured 0.1837% at step 0). So the
deletion count alone does not show the size where the paper's claims start to hold. That needs task and forgetting
numbers per size. These GRPO masks also sit below the 0.5% to 1% that `lab5_dt_muon_recompute.md` §4 mentions. The
SFT masks were not read here.

## 6. Limits

- The routing is measured on a 4-bit copy (Q4_K_M experts, router kept in F32), not the authors' bf16 model, and the
  pad positions are handled differently (§3). Only calibration is replayed, not the training rollouts. So heavy =
  unseen is a match (15 at 0 tokens and 3 at 1 to 4), not a replay of the authors' run.
- §4 is a prediction from training-time routing on English web text. It is not a run on the step-1,221 weights,
  which TSAI holds, or on the 64 SFT calibration rows. Unlike the official code, G10's `dt/mask.py` leaves padding out
  of the Wanda norms, so for our model only real calibration tokens count. The `revive` toy shows the direction during
  training, not the size in the real run.
- Only the five Qwen GRPO (SimpleRL-Zoo) masks were read. The 30B mask is the only MoE mask in the release. No SFT,
  SDFT or Llama masks were read.

## Inputs and reproduction

| Input | Revision or hash |
|---|---|
| `Jacklu0831/deletion-tuning-masks`, `grpo/<model>-simplerl-zoo/{config.json,model.safetensors}` | revision `dfe80f9f`; `model.safetensors` sha256 30B `ac9fa906`, 0.5B `c4c77d5a`, 3B `7307d27f`, 7B `5e3ad147`, 14B `21bfa763` |
| `Qwen/Qwen3-30B-A3B-Base` (tokenizer, shard index, 36 expert gate tensors by range read) | revision `1b75feb7` |
| `hkust-nlp/SimpleRL-Zoo-Data`, `simplelr_qwen_level3to5/train.parquet` (8,523 rows) | revision `50ec8f09`; sha256 `a6ce0b30` |
| `mradermacher/Qwen3-30B-A3B-Base-GGUF`, `Qwen3-30B-A3B-Base.Q4_K_M.gguf` (18,556,686,336 bytes) | revision `c8063198`; sha256 `9f993bc9` |
| official code `agentic-learning-ai-lab/deleting-weights` (read, not run) | commit `94f0340` |
| dry run 2 record, #869 `metrics.jsonl` | commit `0d3df057`; sha256 `2b764501` |
| llama.cpp `llama-imatrix` | b11669 (commit `620d222`), Metal |
| Python | numpy 2.5.5, zstandard 0.25.0, safetensors 0.8.0, gguf 0.19.0, pandas 3.1.1, transformers 4.57.6; `revive`: torch 2.15.0 |

Run on an Apple M6 Mac (32 GB). `masks`, `load` and `revive` take seconds. `weights` reads about 113 MB in about 3
minutes. `llama-imatrix` needs the 18.6 GB GGUF (32 parts of 64 prompts). Tests:
`python -m pytest dt/tests/test_mask_anatomy.py -q` (12 tests, CPU, no download). Seven need zstandard and safetensors,
and one of those also needs gguf; the `revive` test needs torch; the four `load` tests need only numpy. A test skips
when its package is missing.
