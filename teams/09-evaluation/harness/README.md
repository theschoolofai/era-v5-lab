# G9 evaluation harness: `eval_mini`

Week-1 item 4 of team 09-evaluation. A thin, reproducible wrapper around EleutherAI's
[lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) (`lm_eval`) that runs a fixed
task set, `eval_mini`, on open models and writes machine-readable results that other teams can diff against.

Outputs live in [`../results/`](../results/): `eval_mini_v0.json` (the artefact Team 12 compares quantized
models against) and `compare_v0.md` (tables and the within-2-points verdicts).

## The `eval_mini` task set

Six lm_eval tasks, each with one **primary metric** that `compare_v0.md` reports (the JSON keeps every metric):

| lm_eval task     | Primary metric                     | Notes                                                        |
|------------------|------------------------------------|--------------------------------------------------------------|
| `arc_challenge`  | `acc_norm`                         |                                                              |
| `arc_easy`       | `acc_norm`                         | only in `check`, to form SmolLM2's "ARC (Average)"           |
| `hellaswag`      | `acc_norm`                         |                                                              |
| `mmlu`           | `acc` (57-subject aggregate)       | `--limit` applies per subject                                |
| `gsm8k`          | `exact_match`, `flexible-extract`  | greedy; `strict-match` is also recorded                      |
| `truthfulqa_mc2` | `acc`                              | 0-shot by construction (fixed QA prompt in lm_eval)          |

Two **profiles** fix, per task, the shot count and the number of items (`PROFILES` in `run_eval_mini.py`):

| Profile | Task runs                                                                                                  | Purpose                                                   |
|---------|------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| `mini`  | ARC-C 0-shot 500; HellaSwag 0-shot 400; MMLU 0-shot 10/subject (570); GSM8K 5-shot 200; TruthfulQA 0-shot 200 | cheap, uniform; the set Team 12 reruns and diffs against |
| `check` | full splits: TruthfulQA 0-shot (817); GSM8K 5-shot (1319); ARC-Easy + ARC-Challenge 0-shot (2376 + 1172)    | within-2-points check in the publishers' settings        |

Why 0-shot in `mini`: on a laptop GPU the cost of a multiple-choice task is items × choices × prompt tokens, and a
25-shot ARC prompt (~1500 tokens) costs as much as ~20 zero-shot items. `mini` exists for a *relative* comparison
(bf16 versus quantized), where a tight standard error matters more than matching a published table, so it buys
items instead of shots. GSM8K keeps 5 shots because base models need the format examples to answer at all.
0-shot ARC and HellaSwag are also exactly what the SmolLM2 card reports.

Why these `check` tasks: full TruthfulQA, GSM8K and 0-shot ARC are the full-split runs an M2 Pro can finish in
under an hour per model (GSM8K: up to 72 min for the 1.7B). Full 25-shot ARC-C (~7M prompt tokens) was run for the
two Qwen models (26 and 75 min); full 10-shot HellaSwag or 5-shot MMLU (36M and 45M tokens) were not
affordable; on a CUDA GPU they are a `--tasks ... --num-fewshot` call away and the records slot into the same JSON.

`--num-fewshot k` overrides the shot count for one call (used for GSM8K 4-shot, the Qwen2.5 report's setting, and
ARC-C 25-shot). The shot count is part of every record and of the raw output file name, so variants never collide.

`lm_eval` takes the *first* n items, so a limited run is deterministic. The seed (default 42) is applied to
`random`, `numpy`, `torch` and the few-shot sampler. All other lm_eval defaults (prompt templates, `until` stop
strings, 256 max generated tokens) are untouched, so a plain `lm_eval` command with the same task, shots and
limit reproduces each number.

## The v0 run (24 to 25 Oct 2026)

Three ungated base models with published per-task numbers, all in bf16 at a pinned commit:

| Model                        | Revision                                   | Published numbers used                      |
|------------------------------|--------------------------------------------|---------------------------------------------|
| `Qwen/Qwen2.5-0.5B`          | `060db6499f32faf8b98477b0a26969ef7d8b9987` | Qwen2.5 blog and technical report, sec. 5.1 |
| `Qwen/Qwen2.5-1.5B`          | `8faed761d45a263340a0528343f099c05c9a4323` | same, plus the SmolLM2 card's re-evaluation |
| `HuggingFaceTB/SmolLM2-1.7B` | `effd688a12921b4cc83e3312b6feb579f70f9c71` | SmolLM2-1.7B model card (lighteval)         |

Llama-3.2-1B and Gemma-3-1B were not used: both repos are gated and need a Hugging Face token.

Hardware: Apple M2 Pro, 32 GB unified memory, PyTorch MPS, bf16, batch size 8, one model at a time. Wall clock per
model (model loading excluded; per-task times are in `../results/compare_v0.md`):

| Model        | `mini` (5 tasks) | `check` (full TruthfulQA, ARC-E, ARC-C 0-shot, GSM8K 5-shot) | extra `check` runs (GSM8K 4-shot, ARC-C 25-shot) |
|--------------|-----------------:|-------------------------------------------------------------:|-------------------------------------------------:|
| Qwen2.5-0.5B |           10 min |                                                       36 min |                                           48 min |
| Qwen2.5-1.5B |           20 min |                                                       83 min |                                          120 min |
| SmolLM2-1.7B |           24 min |                                                      116 min |                                                – |

GSM8K is the expensive task (1319 greedy generations); the multiple-choice full splits take 2 to 34 minutes each.
On this machine bf16 runs about 1.6x slower than fp16 (the M2 has no hardware bf16); the baseline stays bf16 because
that is what quantized models are compared against.

## Set-up

```bash
uv venv --python /opt/homebrew/opt/python@3.13/libexec/bin/python3 .venv   # Apple Silicon; plain `uv venv .venv` elsewhere
uv pip install --python .venv/bin/python -r teams/09-evaluation/harness/requirements.txt
```

The pins in `requirements.txt` are the versions used for v0 (lm_eval 0.4.13, torch 2.14.1, transformers 5.20.2).
No Hugging Face token is needed: the three v0 models are ungated.

## Running

From the repository root:

```bash
# all five tasks, limited
.venv/bin/python teams/09-evaluation/harness/run_eval_mini.py --model Qwen/Qwen2.5-0.5B --profile mini

# full TruthfulQA and GSM8K for the published-score check
.venv/bin/python teams/09-evaluation/harness/run_eval_mini.py --model Qwen/Qwen2.5-0.5B --profile check --tasks truthfulqa_mc2 gsm8k

# a variant: full GSM8K at 4 shots
.venv/bin/python teams/09-evaluation/harness/run_eval_mini.py --model Qwen/Qwen2.5-0.5B --profile check --tasks gsm8k --num-fewshot 4

# smoke test of the pipeline
.venv/bin/python teams/09-evaluation/harness/run_eval_mini.py --model Qwen/Qwen2.5-0.5B --tasks arc_challenge --limit 5
```

`run_all_v0.sh` is the exact sequence behind v0 (five stages, most useful first). Wrap it in `caffeinate -i` on a Mac.

Options: `--device auto|cuda|mps|cpu` (auto picks CUDA, then MPS, then CPU), `--dtype bfloat16` (default),
`--batch-size 8` (default; lm_eval's `auto` batch size needs CUDA), `--seed 42`, `--revision <ref>`.
The runner resolves `--revision` to a commit sha through the Hub API and loads exactly that commit.

Each run writes to `runs/<model>/<profile>/` (gitignored):

- `<task>_<k>shot.json`: the raw lm_eval result for that task at k shots (no per-sample logs);
- `summary.json`: run metadata plus one record per `(task, shots, metric, filter)`.

Re-running one task (`--tasks gsm8k`) replaces only that task's records at that shot count in `summary.json`.

Then build the committed artefacts:

```bash
.venv/bin/python teams/09-evaluation/harness/build_results.py
```

This merges every `runs/*/<profile>/summary.json` into `../results/eval_mini_v0.json` and renders
`../results/compare_v0.md` from the records, `published_scores.json` and the notes in `build_results.py`.

## `eval_mini_v0.json` schema (for Team 12)

Top level: `schema_version` (`"eval_mini_v0"`), `generated_at`, `harness` (package versions), `task_set` (primary
metric per task), `profiles` (shots and limit per task), `models` (revision, dtype, hardware, wall clock per
profile), `field_docs` (the list below, machine-readable) and `records`.

One record per model, profile, task, shot count, metric and filter. `arc_average` records are derived (mean of
`arc_easy` and `arc_challenge` at the same shots; they carry `derived_from`):

| Field             | Meaning                                                                                      |
|-------------------|----------------------------------------------------------------------------------------------|
| `model`           | Hugging Face model id                                                                        |
| `model_revision`  | commit sha of the model repo that was loaded                                                 |
| `dtype`           | torch dtype of the weights (`bfloat16` for the baseline)                                     |
| `task`            | lm_eval task name; `mmlu` is the 57-subject aggregate; `arc_average` is derived              |
| `profile`         | `mini` (limited) or `check` (full split)                                                     |
| `metric`          | `acc`, `acc_norm` or `exact_match`                                                           |
| `filter`          | `none` for multiple choice; `strict-match` or `flexible-extract` for GSM8K                   |
| `value`, `stderr` | as the harness reports them: fractions in [0, 1]. Multiply by 100 for points.                |
| `n_items`         | items actually scored; `n_items_total` is the full split size                                |
| `num_fewshot`     | shots in the prompt, as the harness reports                                                  |
| `primary`         | `true` for the one metric per task that `compare_v0.md` uses                                 |
| `limit`           | items requested per task (per subject for `mmlu`); `null` means the full split               |
| `seed`            | seed used for random, numpy, torch and few-shot sampling                                     |
| `harness_version` | lm_eval package version                                                                      |
| `run_date`        | UTC date of the run                                                                          |
| `device`, `hardware`, `batch_size`, `wall_clock_s` | where and how long the task ran (model loading excluded)   |

To compare a quantized model: run the same `--profile mini` (and `check` if you can afford it) on it, then diff
the `primary` records on `(task, num_fewshot, metric, filter)`; the baseline's `stderr` tells you what a meaningful
gap is (roughly two standard errors). Keep `num_fewshot`, `limit` and `seed` identical, or the comparison is not
like for like. Field names will not change inside `eval_mini_v0`; additions get a new `schema_version`.

## Pitfall the runner handles: `generation_config.max_new_tokens`

lm_eval caps generation at `max_gen_toks` (256) by passing `max_length` to `generate()`. Qwen2.5's
`generation_config.json` sets `max_new_tokens: 2048`, and transformers lets that win, so a batch keeps decoding until
every sequence hits a stop string or 2048 tokens: about 8x slower, and the GSM8K answer filter then sees a longer
generation than a standard harness run. `run_eval_mini.py` clears the field after loading the model and logs that it
did. If you run plain `lm_eval` on these models, expect the same effect unless you pass `max_new_tokens` yourself.

## What is deliberately not here

- No hand-rolled scoring. Every number comes from `lm_eval.simple_evaluate`.
- No model weights, datasets or raw run directories in git (`.gitignore` covers `runs/`, `.venv/`, `hf_cache/`).
- No chat templates or system prompts: these are base models, evaluated the way their publishers report them.
