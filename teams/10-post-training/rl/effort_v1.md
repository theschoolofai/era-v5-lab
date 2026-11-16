# Effort in RL data v1: subgroups and the length penalty

Status: **confirmed for v1 (16 Nov 2026, week 3, task 4).** Nothing here has been trained yet. The penalty is code (`effort_reward.py`, 34 CPU tests); its constants (`ramp=1024`, no bonus under budget) are fixed as the v1 baseline and will be revisited if a trained checkpoint shows a failure mode. The effort test on the fixed prompts exists in part (see "The 100 fixed prompts" below) and says what a trained model still has to show.

## What an effort label means

The first system turn of every prompt carries `Reasoning effort: {level}` (chat format v0). The levels are `1k`,
`4k`, `16k` and `64k`, with budgets of 1,024, 4,096, 16,384 and 65,536 tokens. A budget covers the **reasoning
trace**: the think, tool-call and tool-result spans of the assistant turn, counted in tokens. The final visible
reply is not counted. `sft/convert.py` uses the same rule (its `TRACE` pattern) to give each SFT row its tier, so a
tool result counts toward the budget in SFT and RL alike. The label is text: the renderer does not enforce it.

## Effort subgroups

RL data v1 has one prompt per task. v1 adds one field to each RL row, `effort`, one of the four labels.

- **A subgroup is a pair (task, effort).** The prompt of a subgroup carries that label.
- **A rollout group never mixes labels.** The k completions that `objective_v1` turns into one group come from one
  subgroup, so a completion is compared with others that had the same budget. A group that mixed labels would
  reward a short answer for the label that allowed it.
- A task can appear in more than one subgroup. Each one is its own group and its own row.
- **Shares.** Proposed default: the SFT mix targets, 30% `1k`, 35% `4k`, 25% `16k`, 10% `64k`
  (`sft/sft_mix_proposal.md`, section 4), so the model is trained to follow the label in the proportions it saw in SFT.
  Rollouts at the long tiers cost the most generation, which is a reason to keep `64k` at 10%.
- **The signal filter is per subgroup.** `rl-data/filter.py` keeps a task when its pass rate is strictly between 0
  and 1. That rate depends on the label (a `1k` budget may make a hard task unsolvable), so once a checkpoint that
  reads the label exists, run the filter on each (task, effort) pair and keep the pairs that pass.
- **Held-out tasks stay out.** The 55 effort-suite tasks are already dropped from the RL pool
  (`results/rl_data_v1_close.md`). The `effort_suite.py guard` command checks a training file for them.

## Length penalty

The verifier gives 0 or 1 and stays unchanged. The trainer shapes the score before it reaches `objective_v1`:

```
over   = trace_tokens - budget(effort)
shaped = verifier_score                              when over <= 0
shaped = verifier_score * max(0, 1 - over / 1024)    when over > 0
shaped = 0                                           when the trace is malformed or unclosed
```

| Effort | Budget | Trace of | Shaped score for a correct answer |
|---|---:|---:|---:|
| `1k` | 1,024 | 900 | 1.00 |
| `1k` | 1,024 | 1,536 | 0.50 |
| `1k` | 1,024 | 2,048 | 0.00 |
| `4k` | 4,096 | 4,097 | 0.999 |
| `4k` | 4,096 | 4,608 | 0.50 |
| `64k` | 65,536 | 66,048 | 0.50 |

Code: `effort_reward.py`, `shape_reward(reward, trace_tokens, effort, ramp=1024)`. The trace length comes from the
same token count as `sft/convert.py` and the effort suite (`trace_tokens`, `None` for a malformed trace).

**Why this shape**

- **Only a correct answer is scaled.** A wrong answer is 0 at every length, so the model is never paid for a short
  wrong answer.
- **No bonus under the budget.** The label is a cap, not a target. A bonus for shortness would push every tier to
  the shortest trace and the label would stop meaning anything.
- **The same ramp at every tier.** A trace 1,024 tokens past its budget is worth 0 at every tier. This matches the
  generation cap used for a label (its budget plus a reply allowance of about 1,024 tokens, as in Stage C of the
  effort suite): a rollout cut off at the cap is incomplete and scores 0 anyway. A ramp proportional to the
  budget would be 16 times wider at `16k` than that cap leaves room for.
- **A malformed or unclosed trace is 0**, never a trace length of zero (the effort suite reports it the same way).
- **It makes some tied groups useful.** With raw 0/1 scores, a group of all-correct rollouts is tied and
  `objective_v1` drops it. With the penalty, an all-correct group that runs over its budget in some rollouts has
  different scores, is kept, and pushes the long rollouts down (tested). A group that is all correct and all
  inside the budget is still dropped.

**Not chosen, for now.** A hard rule (over budget scores 0) gives no gradient between a slight and a large
overrun. A subtracted penalty can make a correct answer worse than a wrong one. A shortness bonus is described above.

Keep two numbers in every report: the **raw verifier success rate** (0/1) and the **shaped mean**. The reward the
verifier returns is never replaced, so earlier results stay comparable.

## The 100 fixed prompts

The suite is `eval/effort_suite.py` with the manifest `eval/effort_manifest.json` (100 slots: 30 code, 25 math,
20 tool or agentic, 15 Indic, 10 general). **55 of the 100 are resolved** (30 code and 25 math, from human-written
code_contests and MATH rows). The other 45 are empty because no approved human-written source exists yet
(`results/effort_probe.md`). Each prompt is crossed with the four labels.

What was run, on open stand-in models and not the capstone model (`results/effort_stageA_*`, `results/effort_stageB_*`):

| Run | Cells | Result |
|---|---:|---|
| OLMoE-1B-7B-Instruct, Stage A, 10 prompts | 80 | correct 0, 0, 1, 1 at `1k`, `4k`, `16k`, `64k` (of 20 each) |
| OLMoE-1B-7B-Instruct, Stage B, 55 prompts | 440 | 22 correct; median length 411 to 427 tokens at every label |
| Qwen3.6-35B-A3B-FP8, Stage B, 55 prompts | 440 | 161 correct; most code cells hit the 1,024 cap |

Read from these reports: **at one fixed cap the label does nothing visible.** Median length and the correct count
do not move with the label, and the changes against `1k` are within what two samples give (noise). Every cell
parses, but only because the models write plain text with no G10 markers. That is why effort has to be trained:
SFT rows already carry the label (30/35/25/10 above), and the penalty rewards staying inside it.

**Not tested yet**

- Stage C (a cap equal to the label budget plus the reply allowance, 8 preregistered prompts) was not run.
- No model that reads the G10 chat format has been run (the `team5` backend needs a checkpoint). This needs a
  TSAI job request after the SFT checkpoint exists.
- The 45 unresolved slots (tool or agentic, Indic, general).

**What to report once a checkpoint exists**, per tier, on the same manifest: the share of rollouts with a trace
inside the budget, the correct count, the raw and shaped means, and the censored count, with counts next to each rate. No threshold is set here: there is no trained
model to set one from.

## Decisions for v1 (confirmed 16 Nov)

1. **Tool results count toward the budget:** Confirmed (`sft/convert.py` `TRACE` and `effort_reward.py` stay identical across SFT and RL).
2. **Subgroup shares:** Confirmed at the SFT mix targets (`30% 1k`, `35% 4k`, `25% 16k`, `10% 64k`).
3. **Ramp width and no-bonus rule:** Confirmed (`ramp=1024`, no bonus under the budget) as the v1 baseline.
4. **Shaped score as the training reward:** Confirmed. `rl/objective_v1.md` is updated so the trainer passes either raw 0/1 verifier scores or `shape_reward` finite scores while always logging the raw verifier success rate alongside the shaped mean (`rl/objective_v1.py` already accepts any finite reward).
5. **The 45 unresolved slots:** Keep the Gate 3 effort suite at the **55 resolved human-written slots** (30 code, 25 math) for v1; the remaining 45 tool/agentic, Indic, and general slots stay out until approved human-written sources exist (never AI-generated prompts).

## Check

```
python -m pytest -p no:cacheprovider -q teams/10-post-training/rl/test_effort_reward.py
python -m ruff check teams/10-post-training/rl/effort_reward.py teams/10-post-training/rl/test_effort_reward.py
```

CPU only, no model, no network. The function takes 0.4 microseconds per call (200,000 calls in 0.08 s).
