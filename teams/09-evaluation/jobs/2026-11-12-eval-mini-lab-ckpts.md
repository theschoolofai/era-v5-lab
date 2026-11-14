# eval-mini on Team 5 lab checkpoints (Gate 2 evidence, week-2 brief)

Week-2 brief (G9, 31 Oct): "Lead and Member D: submit a job request for eval-mini on the Team 4 and Team 5 checkpoints.
Write results/eval_mini_lab_ckpts.md." The task list is the one TSAI accepted on #357: the freeze set is the guard of
`results/config_freeze_proposal.md` (decisions 1–3), and the diagnostics are decision 4, labelled
"diagnostic, not cleared for contamination".

```text
Team:            09-evaluation
Owner:           Rahul Uniyal (rahulni)
Lead approval:   rahulni
Question:        On the completed Team 5 runs that TSAI keeps, what does each checkpoint score on the eval-mini freeze set (the guard of config_freeze_proposal.md) and on the labelled diagnostics?
Script:          teams/09-evaluation/harness_lab/run_team5_runs.py (in this PR), with harness_lab/lm_eval_lab.py
Command:         python teams/09-evaluation/harness_lab/run_team5_runs.py --runs ./inputs/runs --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --hf-home ./inputs/hf --offline --device cuda --out ./out
Config:          teams/09-evaluation/harness_lab/eval_lab_v1.yaml; items from teams/09-evaluation/harness_code_indic/eval_mini_v0_spec.json (sha256 94de47d2…)
Inputs:          (1) ./inputs/runs/<run>/: the run folders TSAI kept (manifest.json, checkpoint.pt, summary.json); see "Runs" below.
                 (2) ./inputs/tokenizer_v0.json (sha256 2de039f2…) and ./inputs/raw_table_P32.npz, the v0 P32 table those runs used (its content hash must equal the one in each manifest.json; the script checks it).
                 (3) ./inputs/hf: a Hugging Face cache with the datasets of the 11 tasks, placed by TSAI in this job's folder and deleted after the job (eval_firewall.md section 3, rule 4); see "Datasets" below.
Hardware:        1 GPU (bf16, as the runs were trained). Not a training node (eval_firewall.md section 3, rule 4).
Max time:        180 minutes. About 11,700 log-likelihood requests per run (MMLU 570 x 4 answers, ARC-Challenge 500 x 4, HellaSwag 400 x 4, MILU 400 x 4, MMLU-Pro 300 x 10, Belebele 300 x 4), so about 176,000 for 15 T1 runs, plus one lm-eval task index of about 14,000 files per job.
Precision:       bf16
Measures:        per run and task: acc and acc_norm, stderr, items scored; pooled freeze-set accuracy (decision 3 of the proposal); wall time
Expected result: near chance on every task (25 for the four-option tasks, about 10 for MMLU-Pro): T1 runs are 56M parameters after about 2M training tokens. A score far above chance at this size would be a bug to report.
Outputs:         out/eval_mini_lab.json, out/guard.json, out/run.json (under 1 MB in total)
Test log:        teams/09-evaluation/jobs/2026-11-12-eval-mini-lab-ckpts.log (this PR): the same command on CPU, on a train_week2.py --smoke checkpoint, with --limit 2 and --offline
```

## Runs

The 15 EXP-1 runs of #310 (T1, AdamW rates 1e-4, 3e-4, 1e-3, 3e-3 and 1e-2, seeds 1234, 1235 and 1236, 245 steps
each; TSAI's results comment on #310, 7 Nov). Team 5's Gate 2 proposal (#374, 12 Nov) says EXP-2, EXP-3 and attention
have no bits per byte yet, so these are the only Team 5 runs with results. If a T2 run of the attention job
(`teams/05-architecture/jobs/2026-11-10-attention-t2.md`) or of EXP-2 (#354) has finished by the time the job runs,
please add its folder too. One run folder each, under `./inputs/runs/`. Asked TSAI in G9 on 12 Nov whether the EXP-1
run folders are kept.

**Team 4:** the brief says "Team 4 and Team 5 checkpoints", but Team 4's week-2 work trains no model and `main` has no
Team 4 checkpoint. Asked TSAI in G9 on 12 Nov; if TSAI names one, it is added here.

## Datasets

What lm-eval 0.4.13 loaded for the 11 tasks in the CPU test (Hugging Face cache, `datasets` 5.1.0). These are the
files TSAI places in `./inputs/hf`: one online run with `HF_HOME=./inputs/hf` fills it, and MILU needs an account
that accepted its terms.

| Dataset | Revision | Tasks |
|---|---|---|
| `cais/mmlu` | `c30699e8356da336a370243923dbaf21066bb9fe` | `mmlu` (57 subjects) |
| `ai4bharat/MILU` | `846d7016558b2004386f30e59a2158731262492f` | `milu_Hindi`, `milu_Telugu`, `milu_Tamil`, `milu_Bengali` |
| `allenai/ai2_arc` | `210d026faf9955653af8916fad021475a3f00453` | `arc_challenge` |
| `Rowan/hellaswag` | `218ec52e09a7e7462a5400043bb9a69a41d06b76` | `hellaswag` (internal only, `benchmarks_v1.md` Decision 8) |
| `TIGER-Lab/MMLU-Pro` | `b189ec765aa7ed75c8acfea42df31fdae71f97be` | `leaderboard_mmlu_pro` |
| `facebook/belebele` | `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2` | `belebele_hin_Deva`, `belebele_tel_Telu`, `belebele_tam_Taml` |

The MILU, MMLU-Pro and Belebele revisions are the ones in `harness_code_indic/eval_mini_v0_spec.json`; MMLU's is the
one in `benchmarks_v1.md`.

## Firewall (eval_firewall.md, section 3)

- Rule 4: the datasets in `./inputs/hf` are eval files. TSAI places them in this job's folder only and deletes them
  when the job ends.
- Rule 5: the script writes scores only. It never uses `log_samples`, writes no item text to `./out/` or to the log,
  and sets lm-eval's logging to WARNING. Before the results come back:
  `python teams/09-evaluation/decontam/canary_scan.py out <job log> --lab-only` must exit 0.
- The script reads only `--runs`, `--tokenizer`, `--byte-table` and `--hf-home`, and with `--offline` it needs no
  network.

## Why the CPU test uses a smoke checkpoint, not the tiny MoE

The brief says to test on CPU with Team 5's tiny MoE. That model (`teams/05-architecture/configs/small/tiny_moe.yaml`,
`harness/train.py`) has a 64-symbol byte vocabulary and saves no checkpoint, so it cannot run these tasks or this
loader. The test uses the format the job reads: a `train_week2.py --smoke` checkpoint of the EXP-1 T1 shape
(`configs/arms/exp1/lr_1e-3.yaml`), trained for 2 steps on synthetic text.
