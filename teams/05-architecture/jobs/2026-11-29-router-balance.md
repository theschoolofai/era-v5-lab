# Router balance (design task 4): eight test arms on dry run 2's setup

REQUEST FOR LEAD/TSAI REVIEW. No lead approval and no run result is claimed.

```text
Team:            05-architecture
Owner:           Deepjyoti Saha (@deepjyotisaha)
Lead approval:   pending review by shivman (Shivanshu Thapliyal)
Question:        TSAI's Lab 5 design task 4: "Is balancing working? Test: bias step size, warm-up, a window with probabilistic routing after growth, and a small auxiliary term." Dry run 2 (#869) fails TSAI's 5x line (busiest expert above 31.25% of a layer's choices) at every logged step up to step 300, and later leaves experts at zero choices for hundreds of steps. Which setting fixes both, at what cost in bits per byte and speed?
Script:          teams/05-architecture/harness/train_week2.py from #892's branch (current main plus the arm files and switches), the same command as dry run 2 (jobs/2026-11-22-dryrun2.md) with --config set to each arm file and --expert-load-every 25. All arms of a phase on one commit; the manifest records it.
Command (arm X): PYTHONPATH=teams/07-infrastructure python teams/05-architecture/harness/train_week2.py --config teams/05-architecture/configs/arms/router_balance/<arm>.yaml --runtime teams/05-architecture/configs/runtime.yaml --resolution ./inputs/resolution.yaml --tokenizer-release frozen-p1536 --tokenizer ./inputs/tokenizer_p1536.json --byte-table teams/04-ke2/results/tables/p1536-s0/raw_table_P32.npz --train-data ./inputs/train.jsonl --heldout-data ./inputs/heldout_v1.jsonl --heldout-sources ./inputs/heldout_v1_sources.jsonl --heldout-sha256 ./inputs/heldout_v1.sha256 --heldout-report ./inputs/heldout_report.json --device cuda --seed <seed> --run-id rb-<arm>-<seed> --checkpoint-store /shared/ckpt --checkpoint-interval-s 600 --checkpoint-at-start --expert-load-every 25 --out ./out/rb-<arm>-<seed>
Config:          teams/05-architecture/configs/arms/router_balance/<arm>.yaml: base, gamma_low, gamma_high, fast_start, sample_window, aux_loss, zero_guard, guard_row_mask. Each inherits configs/arms/dryrun2.yaml and changes one thing (table below). Same model as dry run 2 (T2: 8 blocks, width 512, 16 routed experts + 1 shared, top-2, KAS v2 head; 176.4M parameters, dry run 2's manifest), same recipe, same data, eager attention.
Inputs:          the same TSAI-staged inputs as dry run 2 (the same ./inputs/train.jsonl, heldout_v1, frozen p1536 tokenizer e6b93a93..., raw P32 table).
Hardware:        1 GPU with native bf16, as dry run 2 (one run at a time)
Max time:        90 minutes per run (dry run 2 took 79.8 minutes for 1,221 steps)
Precision:       bf16, as dry run 2
Measures:        expert_load every 25 steps; val/bpb and per-slice bpb at the runtime's eval steps; loss, gradient norm, perf/step_ms, real tokens/s; gpu_peak_gb (peak GPU memory, new in this PR); wall time and time outside training steps (summary.json against the step times, printed by run_report.py); the manifest's config and commit
Expected result: no outcome is assumed. A run that stops early is INCOMPLETE_NOT_A_RESULT; a NaN or inf voids the run.
Outputs:         per run, in ./out/rb-<arm>-<seed>/: metrics.jsonl, manifest.json, summary.json (50 MB or less in total; dry run 2's were 0.7 MB). Checkpoints go to the checkpoint store as in dry run 2, only to resume a run that stops.
Test log:        teams/05-architecture/jobs/evidence/2026-11-29-router-balance/test-log.md (the same script on a Colab T4 at full shape, and every arm on a laptop CPU)
```

## Why this needs the team GPU

The arms were sized on a Colab T4 first: in fp32 (the T4 has no fast bf16) one step takes 9.2 s, and 2 or more rows per pass run out of its 14.6 GB, so a 1,221-step run would take about 3 hours and the eleven runs about 35 hours. On dry run 2's GPU a run takes about 80 minutes. Full length also matters for the question: the idle experts appear only after step 650, which short runs cannot reach. The T4 sizing run reproduced dry run 2's start exactly (held-out bits per byte 2.1607 at step 0; the busiest expert at 45% to 50% in every layer by step 10), so the setup is right.

## The arms (one change each; all ready)

| Arm | File | Change from dry run 2 | Tests (hypothesis) | Source |
|---|---|---|---|---|
| A0 base | base.yaml | none | Control, run fresh on the same commit (main has changed since dry run 2: #899 touched optim.py, and #913 may merge) | dry run 2's arm |
| A1 | gamma_low.yaml | `moe.bias_gamma: 0.0001` | Is the early collapse set by the bias step size? (slow side) | TSAI's "bias step size" |
| A2 | gamma_high.yaml | `moe.bias_gamma: 0.01` | The same, fast side; does a large step cost bits per byte later? | TSAI's "bias step size" |
| A3 | fast_start.yaml | `moe.bias_gamma_start: 0.01`, `moe.bias_gamma_start_steps: 200` (then 0.001) | A fast correction early without a large step later | TSAI's "warm-up" (our reading, see assumptions) |
| A4 | sample_window.yaml | `moe.route_sample_steps: 200`: the 2 experts are sampled from the router's probabilities for the first 200 steps | Does the collapse come from how routing starts? | TSAI's "probabilistic routing window"; the same switch serves Udit's growth step (#897) |
| A5 | aux_loss.yaml | `moe.aux_loss_weight: 0.001`: the Switch Transformer load-balancing loss | A second test of how routing starts | TSAI's "small auxiliary term"; Fedus et al. 2021 (Switch Transformer) |
| A6 | zero_guard.yaml | `optim.skip_zero_grad: true`: Muon skips all-zero gradients (idle experts keep weights and momentum) | Does idle-expert drift keep experts at zero? | Udit Singhania's #919 (#875's finding, Tanmay Sharma) |
| A7 | guard_row_mask.yaml | `optim.skip_zero_grad: true`, `optim.mask_idle_rows: true`: also rows with no gradient signal (an idle expert's router row) | Does router-row drift keep experts at zero? | Sourav Dhar's commit bb78dd5e; arm set as Udit asked (guard only, guard plus mask) |

All switches are off by default, so dry run 2's arm and every other arm are unchanged; the Team 5 suite passes with them in, plus 18 new tests (`tests/test_router_balance_arms.py`), and each new arm ran 2 steps through the trainer on CPU.

## TSAI's rules, item by item

**Job request rules (JOB_REQUEST.md):**

| Rule | Status |
|---|---|
| One file per job, in the template | Follows: this file, every template line filled |
| Owner, lead approval | Follows: Owner is the Axiom name and GitHub handle; lead approval requested from Shivanshu |
| One question | Follows: "is balancing working, and which setting fixes it?"; every arm answers it with one change |
| One-line command, no pipes | Follows (an environment variable and one command, as dry run 2's request) |
| 1 GPU | Follows: one GPU, one run at a time |
| No network or keys; reads only its inputs; writes only to ./out/ | Follows: the trainer reads the staged inputs; outputs to ./out/rb-&lt;arm&gt;-&lt;seed&gt;/; checkpoints to the store, as dry run 2 |
| Test log | Follows: test-log.md (Colab T4 at full shape; every arm on CPU) |
| Outputs 50 MB or less | Follows: about 0.7 MB per run (dry run 2's size) |
| No secrets or personal data | Follows |
| Two failures and it comes back | Noted |

**Lab 5 compute rules and the architecture-experiment protocol:**

| Rule | Status | How, or why not |
|---|---|---|
| Freeze the inputs and prove them on a sample first | Follows | The inputs are dry run 2's staged set, unchanged (hashes in dry run 2's manifest). Proven on a sample: the Colab T4 run on 10M tokens of one sample-v0 shard reproduced dry run 2's step-0 held-out score (2.1607) and its early collapse |
| Measure the rate and peak memory before scaling | Follows for the rate; peak memory from this PR on | Rate on the team GPU, from dry run 2: about 3.0 s per step (median), 2,299 real tokens per second; on a T4: 9.2 s per step, 692 real tokens per second, 2+ rows per pass out of memory. Dry run 2 logged only the memory in use between steps (2.17 GiB at most), not the peak; this PR adds <code>gpu_peak_gb</code>, so every arm reports its peak |
| Report idle time | Follows | <code>run_report.py</code> prints wall time and the time outside training steps. Dry run 2: 79.8 minutes, 19.2 of them (24%) outside training steps (start-up and the 26 held-out evaluations). Each arm's report gives the same line |
| Rerun only the broken part | Follows | One run per arm and seed, so a failed arm reruns alone; with the checkpoint flags (as dry run 2), a stopped run resumes from its last checkpoint instead of starting over |
| One change at a time | Follows | Each arm file changes one thing from dry run 2's arm; a test checks it |
| At least 2 seeds | Partly | Seed 1235 for A0 and the best two arms (3 more runs). All eight at two seeds is 16 runs, about 21 GPU hours; if the time is there, the remaining five repeats are welcome |
| 49M to 100M parameters | Cannot, by choice | The question is about dry run 2's router, so the arms use dry run 2's model: 176.4M parameters in total (165.7M on Muon, 10.7M on AdamW; manifest). Only 2 of 16 routed experts run per token, so far fewer are active per token, but the total is above the range. A smaller model would not test dry run 2's failure |
| 100M to 500M tokens | Cannot, within the time | Each run is dry run 2's length: 1,221 steps, about 8.4M real tokens, which is where both problems happen (the collapse by step 300, idle experts from step 650). 100M real tokens at dry run 2's 2,299 per second is about 12 hours per run, about 130 GPU hours for eleven runs: not possible before Wed 2 Dec. The limit is stated in the results |

**Lab rules (28 Nov):** no speed or kernel claim is made, so no gradient-coverage check is required; the test suite has no failing tests; the PR description carries name, GitHub handle and team.

## Assumptions

1. **Dry run 2's setup is the right base.** Same model (176.4M parameters), recipe, data and length, so each arm compares directly with dry run 2 and A0.
2. **Length: dry run 2's 1,221 steps (about 8.4 million real tokens), not TSAI's 100M to 500M tokens.** Both problems happen inside those steps; the deviation is stated in the results.
3. **"Warm-up" means a larger bias step early** (A3: 0.01 for 200 steps). Dry run 2 is out of the collapse by about step 350, so 200 steps cover most of it without a large step later.
4. **The sampling window and the extra loss sizes** (200 steps; weight 0.001) are first values, chosen small so they do not dominate training; the results say if they need tuning.
5. **In the sampling window, the choice ignores the bias** (the bias keeps updating from the load); gates stay the router probabilities, as in the other arms.
6. **The extra loss** is weighted per microbatch by its share of the batch, so the step's total is the batch average; it is added to the loss, not logged separately.
7. **A6 and A7 use the guards as written by their authors,** behind switches, so they can be compared without merging #919 (which waits on Team 7's checkpoint tests).
8. **Seeds:** 1234 for all arms; 1235 for A0 and the best two (TSAI's two seeds for the best).

## Runs, in order

1. **Phase 1:** A0 to A7 at seed 1234 (8 runs, about 11 hours). All on one commit.
2. **Phase 2:** A0 and the best two arms at seed 1235 (3 runs, about 4 hours).

About 15 GPU hours in all. If time is short, the first four (A0, A2, A3, A4) answer the main question.

## How the result will be read

An arm passes only if, in every layer: the busiest expert stays under 31.25% at every logged step from the first; no expert has zero choices at any logged step after step 200; held-out bits per byte at the end are no worse than A0 by more than the seed spread; and real tokens per second are within 5% of A0. The recommendation is the simplest arm that passes; if none does, the note says which condition failed and by how much. Results go to #892 with `run_report.py --charts` for every run and the command for every number.
