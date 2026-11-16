# Math tasks for RL data v1 (`math_verifier.py`, `tasks/`)

Gate 3 deliverable "one math verifier set: exact answer, one correct answer, one wrong answer" (work order, 14 Nov).
Registered as `math/<task_id>` in `../reward.py`. The reward is an exact check of one boxed final answer; no candidate
code runs, so no container is needed.

```text
rl/math/
  README.md                this file
  math_verifier.py         reward(), check_task() and the command line
  build_tasks.py           writes task folders from records of the RL data v1 math pool
  test_math_verifier.py    correct and wrong answers, adversarial cases, pins
  tasks/<task_id>/task.json   pool id + SHA-256 pins of problem and answer (no text)
```

**TSAI has not ruled on whether MATH may be used for RL training.** `rl-data/build_math.py` says the same. These
tasks are the verifier set the work order asks for, built on the pool RL data v1 already holds. If TSAI rules MATH
out, delete `tasks/` and keep the verifier.

## Data

- Source: hendrycks MATH train split (EleutherAI/hendrycks_math layout), MIT, human-written problems and solutions,
  generator none. The tasks are 8 records of the decontaminated RL data v1 math pool (7,234 rows), chosen by a seeded
  random draw (`build_tasks.py --pick 8 --seed 17`: one per subject, then one more algebra record, answer of at most 24
  characters, level 2 to 4), not by reading problem texts. None is from MATH-500.
- Problem text and reference answer stay in the pool, which is data and stays out of the repository. A task folder
  has the pool id and two SHA-256 pins. `reward()` reads the record from the pool JSONL (`pool=...` or the environment
  variable `G10_MATH_POOL`) and refuses a record that does not match its pins. A missing pool, record or pin raises
  `RuntimeError`; it is never scored 0.
- The prompt is the pool's problem plus the instruction line the pool's owners use (`rl-data/math_check.py`). The
  verifier does not build it.

## What counts as the answer

Stricter than `rl-data/math_check.score` (which also accepts a bare last expression), because a policy will find the gaps:

| Reply | Reward | Why |
|---|---|---|
| `\boxed{\frac12}`, `\boxed{0.5}`, `\boxed{x=5}` for 1/2 and 5 | 1 | equivalent under math-verify 0.9.0 (units and `x=` are ignored by math-verify) |
| the right number in prose, no box ("The answer is 5.") | 0 | the answer must be boxed; stops "4 maybe 5, so 5" |
| `\boxed{4} or \boxed{5}`, `\boxed{5}\boxed{5.0}` | 0 | several different boxed answers; the same answer repeated is fine |
| `\boxed{4, 5}`, `\boxed{(2,1)}` for (1,2), `\boxed{5 or 6}` | 0 | not equal to the reference |
| boxed answer longer than 200 characters, empty box, unclosed box | 0 | |
| everything inside `<\|think\|>...<\|/think\|>`; an unclosed `<\|think\|>` | ignored / 0 | only the visible reply counts |
| only the last 20,000 characters are read | | cost of scoring does not grow with the completion |

## Commands

```bash
export G10_MATH_POOL=<path to the RL data v1 math.jsonl>
python teams/10-post-training/rl/math/math_verifier.py --check-all
python teams/10-post-training/rl/math/math_verifier.py --check-task teams/10-post-training/rl/math/tasks/<task_id>
python teams/10-post-training/rl/math/math_verifier.py --reward teams/10-post-training/rl/math/tasks/<task_id> completion.txt
python -m pytest teams/10-post-training/rl/math/test_math_verifier.py -q -p no:cacheprovider
```

Needs `pip install math-verify==0.9.0`. Without the pool the unit tests still run (fixture records, labelled as
fixtures and kept out of any pool); the tests on the real task ids are skipped and say why.

## Limits

- math-verify decides equivalence: a unit written after the number or `x=` before it passes, a thousands separator
  is read as a separator.
- Eight tasks, one reference answer each, one seed of selection.
