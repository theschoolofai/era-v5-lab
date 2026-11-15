# eval_watcher on dry run 1: eval-mini on every checkpoint (week 3, task 1)

Week-3 work order, Team 9 task 1: "Write eval_watcher.py. It scores each new checkpoint and writes the result to
ClickHouse." Gate 3 evidence: "The watcher scores each dry run 1 checkpoint". TSAI in G9 (14 Nov): "move lm_eval_lab.py
into the watcher PR. State the time per checkpoint in the PR. TSAI approves the slot there."

```text
Team:            09-evaluation
Owner:           Team 9 lead (rahulni). Lab rule 3 (Lab 3 briefing): no person names in the lab repo.
Lead approval:   rahulni (Team 9 lead). The GPU slot is for TSAI to approve in this PR.
Question:        Does every dry run 1 checkpoint get its eval-mini scores in ClickHouse without a person in the loop, and how long does one checkpoint take on the eval slot?
Script:          teams/09-evaluation/harness_lab/eval_watcher.py (this PR). For each commit it runs harness_lab/run_lab_ckpt.py --scorer lm_eval_lab:team5 in its own process, then teams/08-monitoring/clickhouse/load_jsonl.py.
Command:         python teams/09-evaluation/harness_lab/eval_watcher.py --run-dir <dry run 1 run folder> --label tier-a --until-final --scorer lm_eval_lab:team5 --clickhouse-url <ClickHouse URL> -- --device cuda --tier A --model-config <dry run 1 arm YAML> --tokenizer ./inputs/tokenizer.json --tokenizer-sha256 15468e66457b43af79f695cbe585c0d03e3cfe7a4a5d04d189dd3c6b9f02ddc3 --byte-table ./inputs/raw_table_P32.npz --hf-home ./inputs/hf --offline
Config:          teams/09-evaluation/harness_lab/eval_lab_v1.yaml; items from teams/09-evaluation/harness_code_indic/eval_mini_v0_spec.json (sha256 94de47d2…)
Inputs:          (1) the dry run 1 run folder (commits.jsonl, latest.json, <branch>/step_<N>-e<E>/), read only, on a local or mounted path; the path and run ID come with Team 7's dry run 1 job package (jobs/dryrun1/).
                 (2) the dry run 1 model config: the Team 5 arm YAML that run trains, or its resolved model map as JSON.
                 (3) ./inputs/tokenizer.json, the frozen C3 sample-v0 (sha256 15468e66…02ddc3), and ./inputs/raw_table_P32.npz, Team 4's raw table for it (teams/04-ke2/src/build_tables.py; content sha256 fc5e5f8f… when built on the laptop). Use the table of the dry run 1 package if it has one.
                 (4) ./inputs/hf: a Hugging Face cache with the datasets of the 11 tasks at the revisions below, placed by TSAI in this job's folder only and deleted after the job (eval_firewall.md section 3, rule 4). It must be writable: on the first checkpoint lm-eval's hellaswag preprocessing writes its datasets map cache there (93 MB), and later checkpoints reuse it.
Hardware:        1 GPU with native bf16, not a training node (eval_firewall.md section 3, rule 4). Both watchers below share it through one slot lock, so only one model is loaded at a time.
Packages:        torch >= 2.14.1 (run_lab_ckpt.py checks it), lm_eval 0.4.13 (the scorer stops on another version), datasets 5.1.0, tokenizers 0.23.3, safetensors, pyyaml. The env line of the test log has the versions it ran with.
Max time:        The job runs for the length of dry run 1. Per checkpoint, Tier A (970 items, 3,880 requests): 659 s on a laptop CPU for a T1-shape model (58M parameters, fp32: export 14 s, scoring 615 s; logs/watcher_cpu_test.log; the same checkpoint took 501 to 622 s in other runs on this laptop). The GPU time for a T2-shape model (237M parameters) is being measured on Kaggle; its log comes into this PR as logs/watcher_gpu_test.log. Each scorer process is stopped after --timeout 1800 s. With --until-final each watcher exits by itself once the run's final checkpoint (Team 7's trainer commits it with reason "final") is committed and every checkpoint it owns is done. If the run ends without one, TSAI stops the watchers with SIGTERM: they save their state and exit 75, and a restart continues where they stopped.
Precision:       bf16 (fp32 on a GPU without native bf16, recorded in each record's format)
Measures:        per checkpoint and task: acc and acc_norm, stderr, items scored; the pooled freeze-set accuracy (decision 3 of results/config_freeze_proposal.md); the scorer's wall time per checkpoint and the lag from commit to score
Expected result: near chance on every task for dry run 1 checkpoints (25 for the four-option tasks, about 10 for MMLU-Pro). A score far above chance would be a bug to report. The watchers keep up if, on the one GPU, a Tier A checkpoint plus a tenth of a Tier B checkpoint takes less than the 600 s save interval.
Outputs:         out/watcher/<run>.<label>.every<N>/: one eval-mini v1 file per checkpoint (6 KB for Tier A, 13 KB for Tier B), one log per checkpoint (12 KB for Tier A), state.json; the rows in ClickHouse eval_mini. About 21 MB for 1,000 checkpoints of Tier A and 100 of Tier B.
Test log:        teams/09-evaluation/harness_lab/logs/watcher_cpu_test.log (this PR): the same scripts on CPU on a T1-shape Team 5 model saved through Team 7's Checkpointer, with the C3 tokenizer, --offline. GPU: to follow in this PR (Kaggle, T2-shape model).
```

## The two watchers

Run both on the same eval slot. They take turns on the GPU (the slot lock), and each has its own label, results,
state and ClickHouse run_ids.

| Watcher | `--label` | `--every` | `--tier` | Tasks | Items | Requests per checkpoint |
|---|---|---|---|---|---|---|
| Tier A (the command above) | `tier-a` | 1 | `A` | `mmlu` 0-shot, first 10 per subject; `milu_Hindi`, `milu_Telugu`, `milu_Tamil`, `milu_Bengali` 5-shot, spec items | 970 | 3,880 |
| Tier B | `tier-b` | 10 | `B` | `arc_challenge` 0-shot first 500; `hellaswag` 0-shot first 400; `leaderboard_mmlu_pro` 5-shot, 300 spec items; `belebele_hin_Deva`, `belebele_tel_Telu`, `belebele_tam_Taml` 5-shot, 100 spec items each | 1,500 | 7,800 |

Tier B is the same command with `--label tier-b --every 10` and `--tier B` (and `--until-final`). "Run Tier B on every 10th checkpoint"
is TSAI's comment on #357, and every Tier B number carries the label "diagnostic, not cleared for contamination".

Retention in dry run 1 is `--keep 9 --protect-every 15` at a 600 s interval (Team 7, `docs/checkpoint_interval.md`).
Every 10th commit is not a protected one, so a Tier B checkpoint must be scored within about 90 minutes of its commit;
one that retention deletes first is recorded as `gone`. Team 9 names the protected step count in `eval_schedule.md`
(task 4).

## Datasets

The ones lm-eval 0.4.13 loads for the 11 tasks (from #387, Hugging Face cache, `datasets` 5.1.0). One online run with
`HF_HOME=./inputs/hf` fills the cache; MILU needs an account that accepted its terms.

| Dataset | Revision | Tasks |
|---|---|---|
| `cais/mmlu` | `c30699e8356da336a370243923dbaf21066bb9fe` | `mmlu` (57 subjects) |
| `ai4bharat/MILU` | `846d7016558b2004386f30e59a2158731262492f` | `milu_Hindi`, `milu_Telugu`, `milu_Tamil`, `milu_Bengali` |
| `allenai/ai2_arc` | `210d026faf9955653af8916fad021475a3f00453` | `arc_challenge` |
| `Rowan/hellaswag` | `218ec52e09a7e7462a5400043bb9a69a41d06b76` | `hellaswag` (internal only, `benchmarks_v1.md` Decision 8) |
| `TIGER-Lab/MMLU-Pro` | `b189ec765aa7ed75c8acfea42df31fdae71f97be` | `leaderboard_mmlu_pro` |
| `facebook/belebele` | `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2` | `belebele_hin_Deva`, `belebele_tel_Telu`, `belebele_tam_Taml` |

## Network and firewall (eval_firewall.md, section 3)

- With `--offline` the scorer needs no network. The watcher's only network use is the ClickHouse URL TSAI gives. With
  `--no-load` instead it needs none, and a later run without `--no-load` loads the stored results.
- Rule 4: the datasets in `./inputs/hf` are eval files, placed in this job's folder only and deleted when it ends.
- Rule 5: scores only. No `log_samples`, no item text in `out/` or in the logs. Before the results come back:
  `python teams/09-evaluation/decontam/canary_scan.py out <job logs> --lab-only` must exit 0.
- The watcher only reads the run folder. It never writes to the store or deletes from it.

## Not known yet

- The dry run 1 run folder, run ID and model config (Team 7's `jobs/dryrun1/`, with Team 5).
- The ClickHouse URL of the eval slot and whether Team 8's eval tables are up (work order: D3, Tue 17).
- The time per checkpoint on a GPU (Kaggle, T2 shape, 237M parameters: to follow) and at the dry run 1 model size.
