# Single-call robustness follow-up

Status: implemented and validated on 17 November 2026, IST (UTC+05:30).

Branch: `g10-tool-call-robustness-LokeshJatangi`, based on commit `1c47932`
from [PR #109](https://github.com/saitej123/era-v5-lab/pull/109).
PR #109 remains open. Submit this follow-up as a dependent draft against
`saitej123/era-v5-lab:g10-week3-post-training`; merge #109 first, then compare
against the updated base and resolve any drift before marking the follow-up
ready. Until then, the team-base diff also includes the core verifier changes.
The follow-up-only changes relative to `1c47932` are this note and the robustness
test file.

## Changes

`rl/test_tool_call_robustness.py` adds 61 cases to the existing 39 core cases.
The binary reward contract and production verifier are unchanged. Expected
payloads remain inside test code and temporary hidden fixtures. No new public
prompts, datasets, model runs or training changes are included.

Boundary coverage includes valid completions at and below the 65,536-character
limit, oversized completions, Unicode equivalence and mismatches, control
characters, nested duplicate keys, invalid numbers, trailing JSON, invalid
transport IDs, deep nesting and hidden-reference configuration failures.
Deep nesting runs in a child interpreter with a fixed recursion limit and a
ten-second timeout.

The mutation harness changes only temporary copies. It requires the original
to pass the same independently specified cases and each deliberately weakened
copy to produce an incorrect reward on its designated witness. Valid controls
must remain accepted. Exceptions, stale mutation anchors and surviving mutants
fail the harness; they do not count as successful detection.

## Verified results

- Focused verifier, hardening, robustness and decoder suites: **100 passed,
  50 deselected in 0.79 seconds**; no focused tests skipped.
- Reward self-check: correct completion **1.0**, incorrect completion **0.0**;
  **2 checked, 0 wrong**.
- Shared reward/SFT regressions: **172 passed, 6 skipped in 1.19 seconds**.
  The skips require Docker or images: one Go, four code-pool and one SWE case.
  They are unrelated to the new tool-call tests and are not counted as passes.
- All four targeted mutations detected:

| Deliberate defect | Detecting case |
|---|---|
| Ignore tool name | Wrong tool |
| Ignore arguments | Wrong value, Unicode mismatch, boolean/number mismatch, array-order mismatch and additional invalid-value cases |
| Accept duplicate keys | Top-level, argument and nested duplicates |
| Bypass size limit | 65,537-character completion |

These are targeted mutation checks, not exhaustive mutation coverage. No
production fix was needed. The existing prompt is unchanged; earlier prompt
contamination evidence belongs to PR #109.

## Reproduction

Run from the repository root with Python and pytest:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest \
  teams/10-post-training/rl/test_verifier.py \
  teams/10-post-training/rl/test_tool_call_hardening.py \
  teams/10-post-training/rl/test_tool_call_robustness.py \
  teams/10-post-training/rl-loop/test_tool_call_integration.py \
  -k 'tool_call or hf_ or g10_codec' -q -s --tb=short -p no:cacheprovider

PYTHONDONTWRITEBYTECODE=1 python3 \
  teams/10-post-training/rl/reward.py --check-all --type tool_call

PYTHONDONTWRITEBYTECODE=1 python3 -m pytest \
  teams/10-post-training/rl/test_reward.py \
  teams/10-post-training/sft/tests/test_scorers.py \
  -q -rs --tb=short -p no:cacheprovider
```

Broader multi-turn/clarification v2 contracts are excluded. README and unrelated
workspace files remain unchanged. The remaining work is the merge dependency
and review, not additional model evaluation or training.
