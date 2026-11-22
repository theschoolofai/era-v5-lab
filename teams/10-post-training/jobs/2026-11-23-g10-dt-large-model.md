# Job request: Deletion Tuning vs full fine-tuning vs LoRA at 8B and 4B (Qwen3 Base), seed 1

```
Team:            10-post-training
Owner:           f20201351h-maker
Lead approval:   saitej123 (asked for "deletion tuning on large model" in the G10 chat, 23 Nov; approval of this request pending)
Question:        On our SFT bench task, does pure Deletion Tuning (or DT with trained chat-marker rows) reach full fine-tuning at 8B and 4B, where our 1.7B result (pure DT 0/110 valid replies, DT+marker rows 76/110, full FT 93/110) says it does not?
Script:          teams/10-post-training/dt/run_ladder.py (this PR); it calls sft/bench/train.py and sft/bench/evaluate.py from the same commit
Command:         python teams/10-post-training/dt/run_ladder.py --config teams/10-post-training/dt/ladder_qwen3.yaml
Config:          teams/10-post-training/dt/ladder_qwen3.yaml
Seed:            1 (row order, LoRA init)
Inputs:          pinned by sha256 in the table below, under ./inputs/: Qwen/Qwen3-8B-Base @ 49e3418f and Qwen/Qwen3-4B-Base @ 906bfd4b (Apache-2.0, public), and inputs/g10-dtl/slice-v1-qwen3/ (two files, 62 MB, private bundle)
Packages:        Python 3.12, torch (CUDA build), transformers with Qwen3 support (CPU log: 5.22.1), tokenizers, numpy, pyyaml, safetensors
Hardware:        1 GPU, NVIDIA H200 (141 GB), the GPU of TSAI's returned Team 5 runs. Full fine-tuning of 8B with FP32 AdamW needs about 141 GB by our memory model, so an 80 GB A100/H100 cannot run the two 8B full arms or 8B DT+m (99 GB); every 4B arm and 8B LoRA/DT fit 80 GB
Max time:        540 minutes (estimate below: about 7.8 h; 8B runs first, so a time limit still returns the 8B arms)
Precision:       training FP32 weights / gradients / AdamW state with BF16 autocast (as the 1.7B table); evaluation BF16 autocast (evaluate.py --dtype auto)
Measures:        per arm: format validity on 110 held-out prompts with failure reasons, test target bits per byte, forgetting (bits per byte on G5 held-out v1), DT deletion fraction, step time, peak memory; writeback / frozen-weight / bake / reload checks
Expected result: untrained base 0/110 format (the chat/think marker rows look untrained in both checkpoints); pure DT at or below 10/110 at both sizes if our 1.7B finding holds at scale, rising toward full FT if the paper's scale trend holds for this task; full FT about 90/110
Outputs:         out/dtl/ladder_summary.json (rewritten after every arm), per arm out/dtl/<size>/<arm>/{train/train_report.json, test_eval.json, log.txt}, DT masks (train/dt_mask.bin, about 1 MB per arm at 8B); test.gens.jsonl per arm is model text: return it privately, not in Git. Saved FP32 models are deleted after their evaluation (keep_models: false). Under 50 MB without the generations. Needs about 70 GB free disk while an 8B arm saves and reloads its model
Test log:        teams/10-post-training/jobs/2026-11-23-g10-dt-large-model.log (CPU, every arm of the same config shape on tiny random Qwen3 models with the real tokenizer and data; plus the Kaggle T4 measurement)
```

## Why this job

The lead asked for Deletion Tuning on a large model, as the instructor suggested in Session 18 (14 Nov). The table shown in
class is the paper's GRPO table (Llama GSM8K, Qwen SimpleRL-Zoo; arXiv 2611.10866 Tables 1-2). Under SFT the paper goes up to
3B only, and both of its SFT starts are Instruct models whose chat format is already trained (Llama-3.2-1B/3B-Instruct on
MMLU-Pro and BBEH; settings in the official `scripts/train_sft.sh`). Our task starts from a base model that has to learn the turn
markers, and at 1.7B pure DT never produced a valid reply. Our trace pointed at the frozen, untrained marker rows
(`results/dt_sft_surrogate.md`). So the open question for the main run's SFT method is whether size fixes this, or whether DT
always needs trained marker rows. Qwen3 Base is a clean test: in the 4B and 8B checkpoints the chat/think rows have one identical
norm (4B 0.3566 against 0.83 to 1.37 for ordinary rows; 8B LM head 0.4009), which looks like untrained rows. That is the same
situation as SmolLM2.

## Arms (same rows, order, steps and evaluation within a size)

| arm | trains | LR | sizes |
|---|---|---|---|
| base | nothing | | 8B, 4B |
| dt | one FP32 logit per gate_proj weight (W x sigmoid(alpha G) in training, W x 1[G>0] baked for evaluation); alpha 100 to 1000, eta 1/2048, lambda 1e-5 to 0 | 2e-3 | 8B, 4B |
| dtm | dt plus the 5 mapped marker rows (embedding, and the untied LM head at 8B), labelled hybrid | 2e-3, rows 1e-4 | 8B, 4B |
| full | every weight | 1e-4 | 8B, 4B |
| lora | r 4, alpha 8, q k v o gate up down | 1e-3 | 8B, 4B |
| full_lo | full at a 10x lower LR, so a too-high full-FT LR cannot flatter DT | 1e-5 | 8B |
| dtm_800 | dtm with 800 steps (is the remaining gap a step-count effect?) | as dtm | 4B, last |

All arms: 400 optimizer steps x 8 rows, warmup 20 + cosine to 0.1, AdamW (0.9, 0.95), wd 0, clip 1, gradient checkpointing,
micro-batches of 4,096 tokens. These are the settings of the 1.7B table. The LRs come from a 135M dev selection and were not tuned
at 4B or 8B, so full_lo is the only LR check. The preregistration (question, explanations and what each predicts, endpoints, decision
rule, what does not transfer) was written before any Qwen3 run and is summarised in the PR.

## Time and memory estimate (estimates; the basis is stated for each number)

Memory (GB, by the bench runner's model: FP32 storage of every weight, AdamW FP32 moments; calibrated on the measured 1.7B L40S
peaks, where it over-predicts by 1 to 3 GB; DT arms include the regulariser step, which keeps three FP32 temporaries per gate weight):

| model | full | LoRA | DT | DT+m |
|---|---|---|---|---|
| Qwen3-8B-Base | 141 | 43 | 84 | 98 |
| Qwen3-4B-Base | 73 | 25 | 41 | 46 |

Time. Training times are scaled from the measured 1.7B L40S runs (400 steps: full 848 s, LoRA 875 s, DT 734 s). The scaling uses the
compute per token (Qwen3-8B 4.43x and 4B 2.35x of SmolLM2-1.7B, counting body plus LM head), the token count (Qwen3 makes 0.916x
the tokens on the same rows) and an assumed 2x H200-over-L40S speed (the bf16 dense peak ratio is 2.7x). Evaluation is scaled the same
way from the measured 1.7B times (bpb 60 s, format 495 s, forgetting 306 s), plus model save and reload (33 GB at 8B).

| size | per trained arm (train + eval + save) | arms | total |
|---|---|---|---|
| 8B | about 1,720 + 1,280 + 180 s | base eval + 5 trained | about 4.8 h |
| 4B | about 910 + 850 + 90 s | base eval + 4 trained | about 2.3 h |
| 4B dtm_800 | about 1,830 + 850 + 90 s | 1 | about 0.8 h |

About 7.8 h in all. If TSAI prefers shorter jobs, `--sizes 8b` (about 4.8 h) and `--sizes 4b,4b-steps` (about 3.1 h) run the same
config as two jobs with one output folder.

## Stop conditions and recovery
- An arm that fails (non-zero exit, out of memory, non-finite loss, a failed check) is recorded in `ladder_summary.json` with the
  tail of its log, and the next arm starts.
- `<out>/<size>/<arm>/DONE` marks a finished arm, so a rerun with the same command continues from the first unfinished arm.
  Mid-arm resume is not used: at 8B one FP32 resume state is 98 GB, and train.py does not implement it for DT.
- If the untrained base already scores above 50/110 on format, the summary shows it and the DT comparison is read with that flag.

## Pinned inputs

TSAI places these under `./inputs/`. The models are public (Apache-2.0) and are fetched at the pinned revisions. The two data files
hold tokenized training and test rows from admitted OCR-2 sources (bench slice-v1, re-tokenized with the Qwen3 tokenizer by
`sft/bench/retok.py` with `G10_SURROGATE_PROFILE=qwen3`). They stay out of the repository and go to TSAI as a private bundle.
Check with `shasum -a 256`.

| Path under `./inputs/` | bytes | sha256 |
|---|---|---|
| `g10-dtl/slice-v1-qwen3/train.tok.jsonl` | 55,333,297 | `f69772022582afbd4e5d191dc519f4a3087ee6af08fd4b64956b4f39021107ad` |
| `g10-dtl/slice-v1-qwen3/test.tok.jsonl` | 6,664,189 | `0d9f81ffcf11e0ad13d18873245a4c6fd6237b5a06ef0b7017239701bb584968` |
| `Qwen3-8B-Base-49e3418f/model-00001-of-00005.safetensors` | 3,996,250,744 | `9983f1b9ef2f60e7c3730d9bc11ada914e6ec630639b5b020a89bd158cd0446b` |
| `Qwen3-8B-Base-49e3418f/model-00002-of-00005.safetensors` | 3,993,160,032 | `9aa12339835bf7a093d3d0b0a0d2d77f8538301cfc7f8e7ec7a585858ebf7a1f` |
| `Qwen3-8B-Base-49e3418f/model-00003-of-00005.safetensors` | 3,959,604,768 | `c7dd5a191c8da555def0714550375b3c0117751add408fcdda0c2a79ac0186bc` |
| `Qwen3-8B-Base-49e3418f/model-00004-of-00005.safetensors` | 3,187,841,392 | `ad8b708792105133e03fe19e2d56c89c709f677f01285f8b3ede8947d59fd9fe` |
| `Qwen3-8B-Base-49e3418f/model-00005-of-00005.safetensors` | 1,244,659,840 | `fbf24915d47ea030bb68ab0b9488f4515a907185baa6dc26837c9c3f2326a550` |
| `Qwen3-4B-Base-906bfd4b/model-00001-of-00003.safetensors` | 3,957,900,840 | `4c807e2503d68ae373d508689d00a41f4b33f33c2536da97ab81a20caddc1241` |
| `Qwen3-4B-Base-906bfd4b/model-00002-of-00003.safetensors` | 3,987,450,520 | `f4707585548b2fc75a6b1d732e8465c62040a8699903c32850781beeb9b27826` |
| `Qwen3-4B-Base-906bfd4b/model-00003-of-00003.safetensors` | 99,630,640 | `c7b1aa8fb672de2e00423c99876926022e50b18d4f0d140670788510a27f9965` |
| both model folders: `tokenizer.json` | 7,031,645 | `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` |
| both model folders: `config.json`, `generation_config.json`, `model.safetensors.index.json`, `tokenizer_config.json`, `vocab.json`, `merges.txt` | | from the same pinned revision |

The forgetting metric reads `teams/05-architecture/heldout_v1`, which is already in the repository. Exec pass@1 (as in the 1.7B
table) is scored after the job, from the returned generations, with `evaluate.py --score-exec` in a sandbox. The script runs
offline and writes only to `out/`.

## What the result decides, and what it does not
It decides whether DT is a candidate SFT method for the main run at 8B, only with trained marker rows, or not at all. The rules
were fixed in advance. Pure DT is a candidate only if at 8B it reaches at least 0.9x the better full-FT arm on format and on validated exec,
with the paired bootstrap lower bound above -10 points. It is "DT only with trained marker rows" if pure DT stays at or below 10/110 at
both sizes while DT+m reaches 0.8x full FT. It does not transfer as a number: dense pretrained Qwen3 against our MoE trained from
scratch, AdamW against Muon, another tokenizer and head, one code slice, one seed.
