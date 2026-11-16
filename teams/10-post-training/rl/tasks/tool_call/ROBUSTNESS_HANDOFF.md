# Single-call robustness follow-up

Status: focused suite reported passing; reward self-check and regression output verified.
Session date: 17 November 2026, IST (UTC+05:30).

Branch: `g10-tool-call-robustness-LokeshJatangi`, based directly on commit
`1c47932` from [PR #109](https://github.com/saitej123/era-v5-lab/pull/109).
PR #109 was open, not merged, when this branch was created. This follow-up
depends on it. Do not submit the core commit again as an unrelated change.
After #109 merges, compare against the updated team Week 3 branch and resolve
any base drift before opening the separate follow-up PR.

## Changes and contract

`rl/test_tool_call_robustness.py` adds boundary cases and four deterministic
mutation checks. The original reward API and production verifier are unchanged.
All expected calls stay in test code and temporary hidden fixtures. There are
no new public prompts, datasets, model runs or training changes.

Boundary coverage includes valid inputs at and below the 65,536-character
limit, oversized inputs, Unicode equivalence and mismatches, control characters,
nested duplicate keys, invalid numbers, trailing JSON, invalid transport IDs,
deep nesting and hidden-reference configuration failures. Deep nesting runs in
a child interpreter with its own recursion limit and a ten-second timeout.

Mutation tests modify only temporary verifier copies. Each copy deliberately
ignores a tool name, ignores arguments, accepts duplicate keys or bypasses the
size limit. The same independent input/score cases must pass on the original,
and each mutation must produce an incorrect reward on its designated witness.
Valid controls must still receive 1.0 on the mutant. Exceptions, stale mutation
anchors and surviving mutants fail the test harness; they do not count as
successful detection. Terminal output identifies the detecting cases.

This is a focused follow-up, not the deferred multi-turn/clarification v2
implementation. The broader v2 tests and preparation helper are not on this
branch. README stays unchanged; preserve unrelated untracked workspace files.

## Validation and next action

Static parsing/compilation passed. Validation evidence supplied during this session:

- The contributor reported "All passed" for the focused core/robustness suite.
  Its exact aggregate count and individual mutation-detection lines were not
  present in the pasted output; do not invent those details or present them as
  independently inspected logs. This is a reported passing result.
- Complete reward self-check output: correct 1.0, incorrect 0.0; 2 checked,
  0 wrong.
- Complete combined regression output: 172 passed, 6 skipped in 1.08 seconds.
  Skips are one Go image check, four code-pool image checks and one SWE image
  check. These are unrelated Docker-dependent environments, not new tool-call
  cases. Skips are not counted as passes.

No production fix was needed based on the reported results. No model was run.
The assistant did not independently execute pytest. The commands below are
reproduction instructions, not requests to repeat completed validation.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest \
  teams/10-post-training/rl/test_verifier.py \
  teams/10-post-training/rl/test_tool_call_hardening.py \
  teams/10-post-training/rl/test_tool_call_robustness.py \
  teams/10-post-training/rl-loop/test_tool_call_integration.py \
  -k 'tool_call or hf_ or g10_codec' -v -s --tb=short -p no:cacheprovider

PYTHONDONTWRITEBYTECODE=1 python3 \
  teams/10-post-training/rl/reward.py --check-all --type tool_call

PYTHONDONTWRITEBYTECODE=1 python3 -m pytest \
  teams/10-post-training/rl/test_reward.py \
  teams/10-post-training/sft/tests/test_scorers.py \
  -v -rs --tb=short -p no:cacheprovider
```

Acceptance: no failures or skips in the focused tool-call cases; all four
mutations detected; self-check reports correct 1.0, incorrect 0.0 and zero wrong
verdicts; shared reward/SFT regressions have no failures. Record Docker-dependent
skips separately. Original prompt text is unchanged, so the new test fixtures
do not create a new public task requiring prompt decontamination.

No follow-up PR has been opened. Commit and push only the robustness test and
this handoff on the follow-up branch; keep PR #109 unchanged. After #109 merges,
prepare a separate PR with the evidence distinctions above. Preserve unrelated
untracked files. No subagents were used.
