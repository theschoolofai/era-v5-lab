# EXP-3 expert topology at T2

Draft for Dharshan Thaigu and G5 lead review.

```text
Team:            05-architecture
Owner:           Dharshan Thaigu (GitHub handle to confirm)
Lead approval:   Pending Shivanshu Thapliyal review
Question:        At T2, does changing the routed expert count or removing the shared expert improve held-out BPB relative to 16 routed and 1 shared expert?
Script:          teams/05-architecture/harness/train_week2.py
Command:         python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/t2.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1234 --out ./out/exp3-base-1234
Config:          Four existing arm configs listed below
Inputs:          TSAI-approved training split from the EXP-1 bundle, tokenizer v0, matching G4 P32 v0 table, approved held-out v1 with source map, checksum and G9 zero-match report, approved resolution
Hardware:        1 GPU with native BF16 support
Max time:        90 minutes per run, 12 runs, 1,080 GPU-minutes maximum
Precision:       bf16
Measures:        BPB for every slice, three-group mean, code BPB, mean Indic BPB, seed spread, completed steps, step time and peak GPU allocation
Expected result: Four three-seed BPB estimates. A change must beat the baseline beyond seed spread to enter config v1.
Outputs:         ./out/<arm>-<seed>/{metrics.jsonl,summary.json,manifest.json,losses.txt}, 50 MB total return limit. Retain checkpoints on the job machine.
Test log:        evidence/2026-11-12-exp3-t2-smoke.txt
```

| Arm | Existing config | Routed experts | Shared experts |
| --- | --- | ---: | ---: |
| exp3-base | `teams/05-architecture/configs/arms/t2.yaml` | 16 | 1 |
| exp3-experts-8 | `teams/05-architecture/configs/arms/exp3_experts_8.yaml` | 8 | 1 |
| exp3-experts-32 | `teams/05-architecture/configs/arms/exp3_experts_32.yaml` | 32 | 1 |
| exp3-shared-0 | `teams/05-architecture/configs/arms/exp3_shared_0.yaml` | 16 | 0 |

## Run controls

- Keep T2 width 512, eight layers, eight query heads, two KV heads, top-2 routing, 768-wide expert FFN, context 2,048, global batch 8 and 1,221 training steps. The G5 harness takes the absolute expert width from the arm contract. G6 official step timing remains a separate handoff.
- Keep AdamW and the same approved training data, evaluation data, runtime resolution and seed set across arms. The commands use LR 0.001 provisionally. Confirm the common LR with the lead and update every command together if it changes. Mark fallback runs provisional.
- Stage the approved EXP-1 training split and confirm the held-out v1 bundle with the lead and TSAI before filing. Record the actual input, tokenizer, table and resolution hashes. Stage the held-out file as `heldout_v1.jsonl` to match its checksum manifest. Use the P32 table built for tokenizer v0.
- Run from the repo root. Stage inputs in `./inputs/` and give each run its own directory under `./out/`. The commands run offline.
- Report complete runs with finite losses. If any run hits its cap before step 1,221, mark it incomplete. Keep the four comparisons on the same three seeds. An eligible challenger must lower the three-group mean BPB by more than the larger seed spread versus the baseline and pass the plan's code and Indic regression guards. If no challenger passes, retain the config v0 default.

## Commands in run order

```bash
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/t2.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1234 --out ./out/exp3-base-1234
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp3_experts_8.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1234 --out ./out/exp3-experts-8-1234
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp3_experts_32.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1234 --out ./out/exp3-experts-32-1234
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp3_shared_0.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1234 --out ./out/exp3-shared-0-1234
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/t2.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1235 --out ./out/exp3-base-1235
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp3_experts_8.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1235 --out ./out/exp3-experts-8-1235
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp3_experts_32.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1235 --out ./out/exp3-experts-32-1235
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp3_shared_0.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1235 --out ./out/exp3-shared-0-1235
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/t2.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1236 --out ./out/exp3-base-1236
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp3_experts_8.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1236 --out ./out/exp3-experts-8-1236
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp3_experts_32.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1236 --out ./out/exp3-experts-32-1236
python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/exp3_shared_0.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --lr 0.001 --seed 1236 --out ./out/exp3-shared-0-1236
```

