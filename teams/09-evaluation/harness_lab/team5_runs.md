# harness_lab: eval-mini on Team 5 lab checkpoints

This complements [`run_lab_ckpt.py`](README.md) (Team 7's checkpoint layout, #376): `run_team5_runs.py` scores Team 5
run folders (`checkpoint.pt` + `manifest.json`, the layout `run_lab_ckpt.py` does not read yet), and [`lm_eval_lab.py`](lm_eval_lab.py)
is the lm-eval wrapper that `run_lab_ckpt.py --scorer` is reserved for.

`run_team5_runs.py` scores Team 5 lab checkpoints with eval-mini and writes eval-mini v1 records
([`../results/eval_mini_v1_schema.md`](../results/eval_mini_v1_schema.md), section 6 for lab checkpoints).
The task list is [`eval_lab_v1.yaml`](eval_lab_v1.yaml):

| Role | Tasks | Items | Use |
|---|---|---|---|
| freeze set (the guard) | `mmlu` 0-shot, first 10 per subject; `milu_Hindi`, `milu_Telugu`, `milu_Tamil`, `milu_Bengali` 5-shot, eval-mini spec items | 570 + 400 | decisions 1–3 of [`../results/config_freeze_proposal.md`](../results/config_freeze_proposal.md), accepted by TSAI on #357 |
| diagnostic | `arc_challenge` 0-shot first 500; `hellaswag` 0-shot first 400; `leaderboard_mmlu_pro` 5-shot, 300 spec items; `belebele_hin_Deva`, `belebele_tel_Telu`, `belebele_tam_Taml` 5-shot, 100 spec items each | 1,500 | TSAI decision 4 on #357: every number is labelled "diagnostic, not cleared for contamination"; never picks or blocks a candidate |

Items and seeds are the ones eval-mini already uses (`../harness/run_eval_mini.py` profile `mini`, seed 42;
`../harness_code_indic/eval_mini_v0_spec.json`, lm-eval 0.4.13 default seeds), so lab scores can be read next to the
public-model scores in `../results/eval_mini_v1.json`.

## How it works

- A **run folder** is what `teams/05-architecture/harness/train_week2.py` writes: `manifest.json` (the resolved config and
  the tokenizer and table hashes), `checkpoint.pt` and, for a finished run, `summary.json`.
- The model is built with Team 5's own code (`week2/model.py`, `week2/artifacts.py`), imported as is.
- The script refuses a run whose `manifest.json` names a different tokenizer or **byte-table content hash** than the
  files passed with `--tokenizer` and `--byte-table`.
- [`lm_eval_lab.py`](lm_eval_lab.py) is the lm-eval model class. It scores log-likelihood requests like lm-eval's HF
  model (and like Team 12's `llamacpp_lm.py`): BOS + context, trailing spaces moved to the continuation, left
  truncation to the model's context, summed log-probability of the continuation tokens. No generation.

## Inputs and outputs

```
python teams/09-evaluation/harness_lab/run_team5_runs.py --runs <run folder or folder of run folders> \
    --tokenizer <tokenizer_v0.json> --byte-table <raw P32 table the runs used> \
    --hf-home <HF cache with the datasets> --offline --device cuda --out ./out
```

| Output | What |
|---|---|
| `out/eval_mini_lab.json` | eval-mini v1 records; `model` = `lab:<run folder>`, `model_revision` = sha256 of `checkpoint.pt`; passes `../results/convert_v0_to_v1.check` |
| `out/guard.json` | pooled freeze-set accuracy per run and whether it is under the 22.2 floor (decision 3 needs the experiment's baseline too, so the verdict is written in `results/eval_mini_lab_ckpts.md`) |
| `out/run.json` | versions, input hashes, per-run step, status and wall time |

`--limit N` is for tests only (the first N items per task; every record then says "TEST RUN").

## Firewall

Section 3 of [`../firewall/eval_firewall.md`](../firewall/eval_firewall.md): with `--offline` the script needs no
network and reads only its inputs; it writes only to `--out`; it never uses `log_samples` and never logs prompts or item
text. Before results leave the lab: `python teams/09-evaluation/decontam/canary_scan.py out <log> --lab-only` exits 0.

## Tests

`pytest teams/09-evaluation/harness_lab/tests -q` checks `LabLM` against a hand-computed sum on a stub model, with and
without batching, with left truncation, and that two runs give the same numbers. The CPU test of the whole script on a
`train_week2.py --smoke` checkpoint is in `../jobs/2026-11-12-eval-mini-lab-ckpts.log`.
