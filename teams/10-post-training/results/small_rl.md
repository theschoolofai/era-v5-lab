# Small RL test

Local run of `rl/small_rl.py` on 14 Nov 2026. Seed 0, 20 steps, group size 4, task `next_business_day`. The policy is a categorical distribution over two fenced completions. Scores come from `rl/verifier.py` in process mode. The update is `rl/objective_v1.py`.

| Completion | Verifier reward |
| --- | ---: |
| `tasks/next_business_day/reference.py` | 1 |
| stub that returns `None` | 0 |

| Measure | Value |
| --- | ---: |
| Mean reward, first group | 0.5 |
| Mean reward, last group | 1.0 |
| Probability of the reference completion after 20 steps | 0.958 |

Groups whose two rewards were equal were dropped, and those steps did not change the policy. The full JSON is `jobs/2026-11-14-small-rl.log`. The reproduction request is `jobs/2026-11-14-small-rl.md`.

This run does not sample a small open model. That sampler needs its own tested script before a GPU request.
