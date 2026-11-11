# Effort evaluation (Package T2): suite, manifest and CPU checks

Date: 11 Nov 2026 (IST). Code: `eval/effort_suite.py`, `eval/effort_manifest.json`, `eval/test_effort_suite.py`.
**No model has generated anything for this suite yet.** This file reports the suite and the CPU checks only.
No GPU was used.

## What the suite measures

Each fixed prompt is crossed with the four effort labels `1k, 4k, 16k, 64k`. Every record keeps the
**requested effort** (the plain-text line `Reasoning effort: {label}`, chat-format v0) apart from the
**enforced generation cap** (`max_new_tokens`). A text label is not budget enforcement, so three things are
reported apart: does the output follow the format, does it stay inside the cap, is it correct.

| Stage | Prompts | Cells | Cap | When |
|---|---:|---:|---|---|
| A | 10 (5 code, 5 math; first slot of each code judge and math level, plus one more aizu) | 40 | 1024 for every label | default; cheap canary |
| B | all 55 resolved | 220 | 1024 for every label | isolates the effect of the label text at a fixed cap |
| C | 8 preregistered (4 code, math levels 2 to 5) | 32 | label budget + 1024 reply allowance, bounded by the real context | only with `--stage C` |

The preflight checks prompt + cap against the model's real context. In A/B a prompt that cannot fit 1024 new
tokens gets one lower common cap for all four labels, and the record says so. In C a ceiling below the label
budget cannot test that label, so the cell is recorded as unsupported, not run. Neither the common 1024 cap nor
the C subset shows full four-tier compliance; long-tier work waits for a TSAI job.

Per cell: functional success (where a checker exists), G10-format parse status, tool-call validity, generated
tokens, think-plus-tool trace tokens under the converter's contract (`sft/convert.py` TRACE: spans with their
markers), stop reason, truncation, wall time, prompt and total context tokens. Cells that hit the cap are
**censored** and stay in every denominator as failures. A malformed or unclosed trace is reported as a parser
failure with its raw length; it never gets a trace length of zero. The summary also gives matched per-prompt
changes against `1k` (same prompt, same seed), and `compare` matches two checkpoints on the same manifest hash.

Backends: `hf` runs an open checkpoint with its own chat template (effort line in a system message). That is an
optimization diagnostic only. `team5` runs the G5 model with the G10 template through `rl-loop/team5_adapter.py`
and refuses anything but a READY real bundle (a fixture runs only with `--allow-fixture-smoke`, flagged in the
summary). The final G10 effort comparison uses `team5`.

## The 100 slots

| Category | Declared | Resolved | Source | Licence / decision |
|---|---:|---:|---|---|
| code | 30 | 30 (aizu 8, atcoder 7, codechef 7, hackerearth 8) | deepmind/code_contests train @ `802411c3010cb00d1b05bad57ca77365a3c699d6` | CC-BY-4.0; `rl-code-code-contests` allowed (TSAI, 6 Nov) |
| math | 25 | 25 (5 per level, 1 to 5) | EleutherAI/hendrycks_math train @ `21a5633873b6a120296cce3e2df9d5550074f4a3` | MIT; **no row in `licences/licence_table.md` yet** |
| tool/agentic | 20 | 0 | none approved | unavailable, reason in the manifest |
| Indic | 15 | 0 | none approved | unavailable, reason in the manifest |
| general | 10 | 0 | none fetched | unavailable, reason in the manifest |

Both resolved sources are human-written (generator: none). No prompt was generated with any model. The prompt is
the raw task text; an instruction wrapper is used only if a team member supplies one (`--instruction kind=FILE`),
the same rule as `rl-data/survey.py`, and its sha256 goes into every record.

Why the three categories are empty:
- **tool/agentic**: the tool-use sets in the licence table (Nemotron-Agentic-v1, Nemotron-SFT-Agentic-v2) are
  model-simulated dialogues, not human-written. The 21 `swe-envs` are human and allowed, but they are RL
  environments that need a multi-turn Docker agent harness, and using them here needs a team decision and an RL
  hold-out.
- **Indic**: the human-written candidates (aya_dataset, oasst2) are `TSAI reserves`, not cleared, and not held
  locally. The allowed indic-align `Dolly_T` / `OpenAssistant_T` subsets are IndicTrans2 machine translations,
  not human-written Indic text.
- **general**: databricks-dolly-15k is allowed (CC-BY-SA-3.0, human-written) but no pinned copy was held locally
  and none was fetched. It is in the SFT mix, so its prompts would need an SFT hold-out.
Free-form Indic and general output also needs the team's blinded human rubric; the suite records success as
`None` for them and never uses a model judge.

Selection: candidates are the local RL v1 build of 11 Nov (code_contests non-Codeforces after decontamination v2;
MATH train after decontamination v2 and the MATH-500 13-gram guard). 1,805 ids used by the earlier OLMoE runs
(their train, held-out and survey id lists) were removed first, so that checkpoint is not scored on prompts it
trained or was filtered on. Within each stratum the pick is the lowest `sha256(selection_seed:id)`.

The manifest stores no prompt text. Each slot holds dataset, revision, file and its sha256, row index, field,
the sha256 of the text (and of the tests or reference answer), licence, decision, generator and an
original-problem group. `manifest_sha256` seals the file; a changed field fails `verify` and every run.

## Training exclusion

The 55 resolved tasks are all in the RL v1 candidate files, because that is the approved pool. **RL v1 must drop
them before any training while this suite is in use.** The ids and text hashes are in
`training_exclusion`; `effort_suite.py guard --training FILE` fails on an eval task id, an eval prompt, or any
eval output record (`do_not_train: true`). Run on the local RL v1 files it flags 55 of 55 and exits 1, as
expected until the drop is made.

## What ran (CPU, 11 Nov)

| Check | Result |
|---|---|
| `pytest teams/10-post-training/eval/test_effort_suite.py` | 30 passed |
| `effort_suite.py verify` with the pinned files and the rl-data checkers | 55 prompt texts, 30 test sets and 25 reference answers match their hashes; 31 pinned files match their sha256 |
| Stage A pipeline smoke: real pinned prompts, real `math_check` and Docker `stdio_check`, **scripted completions, no model** | right answers scored 1, wrong answers 0, `print(0)` failed on real tests, a capped unclosed think was censored and malformed with raw length 1024 |
| `guard` on the local RL v1 files | 55 problems (the held-out tasks), exit 1 |

Tests cover: empty completion, over-cap censoring kept in denominators, malformed traces never reported as zero
length (unclosed think, second unclosed span, bad tool JSON, stray marker), the committed manifest hash, tampered
and resealed-bad manifests, deterministic slot-major 4-label matrix with one seed per prompt, Stage C off by
default, lowered common cap and unsupported cells from the context preflight, missing checkers giving `None`
rather than 0, output marking and the training guard, and the resolver's file, text and answer hash checks.

## Not done, and what it needs

- **No generation run.** Next: Stage A on the open OLMoE checkpoint with `--backend hf` on a GPU job (diagnostic),
  then Stage B. The G10-template comparison waits for the G5 bundle (`team5` backend; the adapter returns
  `WAITING_FOR_G5_ARTIFACT` until it arrives).
- The `hf` and `team5` backends have not been exercised on a real model here (no local model, no GPU).
- Checkers come from `rl-data/` (PR saitej123/era-v5-lab#54), which is not in this base branch yet. Without it
  functional success is `None` with the reason, never 0. Code checking needs Docker.
- 45 of 100 slots are unavailable (tool/agentic 20, Indic 15, general 10) until approved human-written sources
  and the team's rubric exist.
- A licence-table row for hendrycks MATH, and the RL v1 drop of the 55 held-out tasks.
- G9's final independent score stays separate; this suite is development evidence once inspected.

## Commands

```bash
cd teams/10-post-training
python eval/effort_suite.py verify --source-dir code_contests=DIR --source-dir hendrycks_math=DIR
python eval/effort_suite.py plan --stage B
python eval/effort_suite.py run --stage A --backend hf --model allenai/OLMoE-1B-7B-0125-DPO \
    --source-dir code_contests=DIR --source-dir hendrycks_math=DIR --out OUT_DIR   # outputs stay out of Git
python eval/effort_suite.py guard --training path/to/training.jsonl
python -m pytest eval/test_effort_suite.py -q -p no:cacheprovider
```
