# RL code tasks and verifier

`verifier.py` turns a model completion into a binary reward for a task in `tasks/<task_id>/`. The design and the cheating cases are in `design_note.md`.

## Use

```bash
python teams/10-post-training/rl/verifier.py --check-task teams/10-post-training/rl/tasks/<task_id>               # lint, and the reference must score 1
python teams/10-post-training/rl/verifier.py --reward teams/10-post-training/rl/tasks/<task_id> completion.txt    # {"reward": 0|1, ...}
python teams/10-post-training/rl/verifier.py --reward teams/10-post-training/rl/tasks/<task_id> completion.txt --sandbox docker   # for training
python -m pytest teams/10-post-training/rl/test_verifier.py -q -p no:cacheprovider
```

The reply holds counts for humans and logs. The training loop must use only the `reward` value. The reply holds counts for humans and logs; the training loop must use only the `reward` value. Docker mode needs the image `python:3.12-slim` (or set `G10_RL_IMAGE`). The docker tests are skipped when docker or the image is missing.

## Writing a task

A task is a folder `tasks/<task_id>/` (the folder name equals `id`):

| File | Content |
|---|---|
| `task.json` | `id`, `title`, `entry_point`, `time_limit_s`, `difficulty` (easy, medium, hard), `source` (starts with `original`, then the author and date), `tags` |
| `prompt.md` | the problem, the exact signature, 2-3 examples. Never a hidden input |
| `visible_tests.json` | 2-3 cases, the same ones the prompt shows |
| `hidden_tests.json` | 10 or more cases: edge cases, other sizes, other kinds of input |
| `reference.py` | your own solution to the task |

A case is `{"args": [...], "kwargs": {...}, "expected": <json value>}`, or `{"args": [...], "raises": "ValueError"}` when the function must raise. Expected values are plain JSON; a returned tuple is compared as a list.

Rules for the dataset: tasks must be original (not taken from HumanEval, MBPP or any benchmark), the reference solution must score 1, and the hidden tests must not appear in the prompt. Run the repository's decontamination check on the prompts before merging.
