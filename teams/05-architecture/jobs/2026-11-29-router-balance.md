# Router balance (design task 4): eight test arms on dry run 2's setup

REQUEST FOR LEAD/TSAI REVIEW. No lead approval and no run result is claimed.

```text
Team:            05-architecture
Owner:           Deepjyoti Saha (@deepjyotisaha)
Lead approval:   pending review by Shivanshu
Question:        TSAI's Lab 5 design task 4: "Is balancing working? Test: bias step size, warm-up, a window with probabilistic routing after growth, and a small auxiliary term." Dry run 2 (#869) fails TSAI's 5x line (busiest expert above 31.25% of a layer's choices) at every logged step up to step 300, and later leaves experts at zero choices for hundreds of steps. Which setting fixes both, at what cost in bits per byte and speed?
Script:          teams/05-architecture/harness/train_week2.py from #892's branch (current main plus the arm files), the same command as dry run 2 (jobs/2026-11-22-dryrun2.md) with --config set to each arm file and --expert-load-every 25. All arms of a phase on one commit; the manifest records it.
Command (arm X): PYTHONPATH=teams/07-infrastructure python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/router_balance/<arm>.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer-release frozen-p1536 --tokenizer ./inputs/tokenizer_p1536.json --byte-table teams/04-ke2/results/tables/p1536-s0/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --seed <seed> --run-id rb-<arm>-<seed> --expert-load-every 25 --out ./out/rb-<arm>-<seed>
Config:          every arm file inherits configs/arms/dryrun2.yaml and changes one thing (table below). Same model (T2: 8 blocks, width 512, 16 routed experts + 1 shared, top-2, KAS v2 head), same recipe, same data, eager attention, bf16.
Inputs:          the same TSAI-staged inputs as dry run 2 (the same ./inputs/train.jsonl, heldout_v1, frozen p1536 tokenizer e6b93a93..., raw P32 table).
Hardware:        1 GPU with native bf16, as dry run 2
Max time:        90 minutes per run (dry run 2 took 79.8 minutes for 1,221 steps)
Measures:        expert_load every 25 steps; val/bpb and per-slice bpb at the runtime's eval steps; loss, gradient norm, perf/step_ms, real tokens/s, peak memory; the manifest's config
Expected result: no outcome is assumed. A run that stops early is INCOMPLETE_NOT_A_RESULT; a NaN or inf voids the run.
Outputs:         per run: metrics.jsonl, manifest.json, summary.json (50 MB or less each). Checkpoints are not needed.
```

## Why this needs the team GPU

The arms were sized on a Colab T4 first: in fp32 (the T4 has no fast bf16) one step takes 9.2 s, and 2 or more rows per pass run out of its 14.6 GB, so a 1,221-step run would take about 3 hours and the eleven runs about 35 hours. On dry run 2's GPU a run takes about 80 minutes. Full length also matters for the question: the idle experts appear only after step 650, which short runs cannot reach. The T4 sizing run reproduced dry run 2's start exactly (held-out bits per byte 2.1607 at step 0; the busiest expert at 45% to 50% in every layer by step 10), so the setup is right.

## The arms (one change each)

| Arm | File | Change from dry run 2 | Tests | Ready |
|---|---|---|---|---|
| A0 base | base.yaml | none | Control, run fresh on the same commit as the other arms (main has changed since dry run 2: #899 touched optim.py, and #913 may merge) | Now |
| A1 | gamma_low.yaml | `moe.bias_gamma: 0.0001` | Is the early collapse set by the bias step size? (slow side) | Now (config only) |
| A2 | gamma_high.yaml | `moe.bias_gamma: 0.01` | The same, fast side; does a large step cost bits per byte later? | Now (config only) |
| A3 | fast_start.yaml | gamma 0.01 for the first 200 steps, then 0.001 | TSAI's "warm-up" | After the switch lands in #892 |
| A4 | sample_window.yaml | sample the 2 experts from the router's probabilities for the first 200 steps | TSAI's "probabilistic routing window" (the same switch Udit's growth path uses) | After the switch lands in #892 |
| A5 | aux_loss.yaml | a small load-balancing loss, weight 0.001 | TSAI's "small auxiliary term" | After the switch lands in #892 |
| A6 | zero_guard.yaml | idle experts' weights and momentum kept (#919's exact-zero guard) | Does idle-expert drift keep experts at zero? | After #919's guard is in #892's branch |
| A7 | guard_row_mask.yaml | #919's guard plus Sourav's router-row mask (bb78dd5e) | Does router-row drift? | After both are in #892's branch |

## Runs, in order

1. **Phase 1 (now):** A0, A1 and A2 at seed 1234, all on the same main commit. Three runs, about 4 hours.
2. **Phase 2 (after #892's switches land, Sun 29 to Mon 30):** A3 to A7 at seed 1234. Five runs, about 7 hours.
3. **Phase 3:** A0 and the best two arms at seed 1235 (two seeds, as the architecture-experiment rules ask). Three runs, about 4 hours.

## How the result will be read

An arm passes only if, in every layer: the busiest expert stays under 31.25% at every logged step from the first; no expert has zero choices at any logged step after step 200; held-out bits per byte at the end are no worse than A0 by more than the seed spread; and real tokens per second are within 5% of A0. The recommendation is the simplest arm that passes; if none does, the note says which condition failed and by how much. Results go to #892 with the command for every number.
