# Eval schedule v0 (Team 09)

**Status:** v0, 11 Nov 2026, for Gate 2. Lead: `rahulni`.

TSAI's list of 10 Nov names "the eval schedule proposal" among the Gate 2 files. The CAP plan sheet makes this file a
week-3 task ("Write eval_schedule.md: the benchmarks for each step of the run"), and TSAI approves it in week 3
("TSAI approves the eval schedule for the training run"). This v0 fixes the structure. Week 3 closes the open items in
section 5. The scores TSAI uses for the config freeze are in
[`results/config_freeze_proposal.md`](results/config_freeze_proposal.md).

## 1. Dates (CAP plan sheet)

| Date | Event | What evaluation must show |
|---|---|---|
| Sat 14 Nov | Gate 2: tokenizer and config frozen | nothing in this file |
| Sun 15 to Sat 21 Nov | Dry run 1 | Gate 3: "The watcher scores each dry run 1 checkpoint, and the first shards have zero fingerprint hits." |
| 24 to 26 Nov | Dry run 2 | Gate 4: "Step-0 scores are near random, and the watcher survives the planned failure of dry run 2." |
| Sat 28 Nov | Training starts | nothing in this file |

## 2. What runs at each step

| Tier | When | Tasks | Items | Use |
|---|---|---|---|---|
| A | Every checkpoint the watcher sees: dry run 1, dry run 2 and the run | The freeze set: `mmlu` (0-shot, the first 10 per subject) and `milu_Hindi`, `milu_Telugu`, `milu_Tamil`, `milu_Bengali` (5-shot, eval-mini spec items) | 970 | Trend panel, and the guard in `results/config_freeze_proposal.md`. Log-likelihood only |
| B | Every N-th checkpoint (N is open item 4) | `arc_challenge` (0-shot, first 500), `leaderboard_mmlu_pro` (5-shot, 300 spec items), `belebele_hin_Deva`, `belebele_tel_Telu`, `belebele_tam_Taml` (5-shot, 100 spec items each), `hellaswag` (0-shot, first 400) | 1,500 | Internal diagnostics, labelled "not decontaminated" and "not a score for our model". Only if TSAI allows them (proposal, decision 4) |
| C | Step 0 of dry run 2; the restored checkpoint after the planned failure of dry run 2 | Tier A, plus Tier B if allowed | 970 or 2,470 | The two Gate 4 checks |
| Later | When Tier A scores leave chance | Benchmarks marked "Evaluation" in `benchmarks_v1.md` | not set | Not in v0. A later version adds them, with TSAI approval |

All items are the ones eval-mini already has (`harness/run_eval_mini.py`, profile `mini`;
`harness_code_indic/eval_mini_v0_spec.json`), so every score can be read next to the public-model scores in
`results/eval_mini_v1.json`.

## 3. Near random at step 0 (Gate 4)

Chance is 25 on all Tier A items (four options each). Bands of chance ± 2 standard errors:

| Scope | Items | Band |
|---|---|---|
| Pooled Tier A | 970 | 22.2 to 27.8 |
| `mmlu` | 570 | 21.4 to 28.6 |
| each `milu_*` | 100 | 16.3 to 33.7 |

These bands assume no answer bias. A step-0 model often prefers one answer letter and then scores that letter's share
of the items, so the bands are checked against the answer-letter shares in week 3 (open item 5). A score above the band
at step 0 means the checkpoint is not step 0, or the evaluation has a bug.

## 4. How scoring works

- **Finding checkpoints:** only the folder that `latest.json` or a `commits.jsonl` line names, never one found by
  listing; weights through `export_safetensors()` (Team 7, PR #245; `results/eval_mini_v1_schema.md` section 6).
- **Scoring:** `harness_lab/run_lab_ckpt.py` writes eval-mini v1 records with the `checkpoint` fields.
  `eval_watcher.py` (week 3) runs it on each new checkpoint.
- **Storage:** Team 8's ClickHouse table `eval_mini` (`teams/08-monitoring/clickhouse/schema_v1.sql`). Team 8's eval
  tables are due 18 Nov (plan sheet). Team 8 plots scores by `checkpoint.step`.
- **Compute:** TSAI gives a GPU slot for the watcher (plan sheet, week 3).
- **Eval files** stay in the eval folder (`firewall/eval_firewall.md`). Results carry task names, IDs and scores only.
- **Public scores:** TSAI approves each one (plan sheet, week 4). Nothing in this schedule is public by default.

## 5. Open items for week 3

1. Checkpoint interval of the V5 run: Team 7. `teams/07-infrastructure/docs/checkpoint_design_v0.md` says the final
   V5 numbers wait for the model configuration; V4 saved every 500 steps or 30 minutes.
2. Size of the watcher's GPU slot: TSAI.
3. Time for one Tier A and one Tier B run on a lab checkpoint: measured in the job for the Team 4 and Team 5
   checkpoints (`results/eval_mini_lab_ckpts.md`, due Fri 13 Nov).
4. N for Tier B, from items 1 to 3.
5. The step-0 bands against the answer-letter shares of the Tier A items (section 3).
6. Whether Tier B runs at all (proposal, decision 4).
7. Benchmark names and score format for Team 11 (plan sheet, week 4).
