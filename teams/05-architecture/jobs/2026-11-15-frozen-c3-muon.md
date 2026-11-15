# Week 3 job request: frozen C3 tokenizer, T2 Muon

Draft for G5 lead and TSAI review. One new run is requested, paired with an existing Gate 2 seed. Results go in [frozen_tok.md](../experiments/results/frozen_tok.md), due Wed 18 Nov.

```text
Team:            05-architecture
Owner:           Udit Singhania (udisinghania)
Lead approval:   Pending shivman review
Question:        How does frozen C3 change held-out bits per original UTF-8 byte versus tokenizer v0 for the same T2 Muon arm and seed?
Script:          teams/05-architecture/harness/train_week2.py at 71bc0fb, with the TSAI Gate 2 speed fixes and the C3 scoring patch linked below
Command:         python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp2_muon.yaml --runtime teams/05-architecture/configs/runtime_fast.yaml --resolution ./inputs/resolution.yaml --tokenizer-release frozen-c3 --tokenizer ./inputs/tokenizer_c3.json --byte-table ./inputs/raw_table_c3_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --seed 1235 --out ./out/frozen-c3-muon-1235
Config:          teams/05-architecture/configs/arms/exp2_muon.yaml, runtime_fast.yaml and the matched seed's TSAI resolution
Inputs:          Exact Gate 2 training text from the #310 v0-clean train split, original heldout_v1 with its source map/checksum/report, frozen C3 tokenizer and matching raw P32 table
Hardware:        1 GPU with native BF16 support
Max time:        90 minutes requested, matching the EXP-2 job
Precision:       bf16
Measures:        Final val/bpb, val/nll_nats, val/utf8_bytes, val/encoded_utf8_bytes, scored tokens, per-slice and grouped BPB, completed steps, finite loss and gradient norm, step and wall time
Expected result: 1,221 completed steps and BPB on the original heldout_v1 bytes. Report frozen-minus-old BPB at the matched seed. No direction assumed.
Outputs:         ./out/frozen-c3-muon-1235/{manifest.json,summary.json,metrics.jsonl,losses.txt,total_losses.txt}, 50 MB or less in total. Retain the checkpoint on the job machine.
Test log:        teams/05-architecture/jobs/evidence/2026-11-15-frozen-c3-muon/smoke.md
```

## Source and staging

- Start from [71bc0fb](https://github.com/theschoolofai/era-v5-lab/commit/71bc0fbb99fbe5e90d8a09055b7622010e8ab23f) and apply TSAI's Gate 2 implementation from [#441](https://github.com/theschoolofai/era-v5-lab/pull/441), followed by the [C3 scoring patch](evidence/2026-11-15-frozen-c3-muon/c3-original-byte-bpb.patch). Use the staged `runtime_fast.yaml`. Record the effective source and runtime hashes. Disable `G5_DOCUMENT_CACHE_DIR` for this comparison because the current cache assumes token bytes equal original bytes. Stage everything before running offline.
- Seed `1235` is proposed to match a Gate 2 run with batched Muon. Confirm the old seed, baseline BPB and manifest before execution. Match its resolved settings, including the actual matrix LR, optimizer and attention paths, training text, holdout, context, batch settings, and step budget. The T2 job lists context 2,048, global batch 8, `optim.lr: 0.001` and `muon_lr: 0.01`. Use the baseline manifest to confirm these settings and microbatch 2.
- Confirm the exact staged `train.jsonl` path and SHA-256 from the old run. Preflight the staged inputs with the frozen tokenizer. Use the repository's original `heldout_v1` data, sources, checksum and report, and verify the old run used the same holdout hash.
- Stage the pinned C3 tokenizer and matching raw P32 table using the hashes in [frozen_tok.md](../experiments/results/frozen_tok.md). Build the table offline with `python teams/04-ke2/src/build_tables.py --tokenizer ./inputs/tokenizer_c3.json --pos-dims 32 --out ./out/c3-tables`. Verify the embedded tokenizer and raw table content hashes. Stage the resulting raw table for the run.

## Scoring and reporting

Use the unchanged `heldout_v1` text for both runs. C3 normalizes inside the tokenizer. The harness checks its token bytes against that normalized text, while total and per-slice BPB divide by the original source byte counts. The full holdout has 1,059 documents and 3,775,551 original UTF-8 bytes. The 74 changed documents remain in the score. Reuse the old seed's original score as directed by TSAI. Report the matched delta, with the three-seed mean 1.6607 as context. A timeout before step 1,221 is `INCOMPLETE_NOT_A_RESULT`.
