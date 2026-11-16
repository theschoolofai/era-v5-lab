# JavaScript and TypeScript tasks for RL data v1 (`jsts_verifier.py`, `tasks/`)

Gate 3 deliverables "one JavaScript verifier set" and "one TypeScript verifier set": one exact check, one correct
answer, one wrong answer (work order, 14 Nov). Registered as `js/<task_id>` and `ts/<task_id>` in `../reward.py`.
Both languages share one verifier and one sandbox image because they differ only in the file extension and the fence.

```text
rl/jsts/
  README.md                  this file
  jsts_verifier.py           reward(), check_task() and the command line
  build_tasks.py             builds task folders from an Exercism track clone
  jsts.Dockerfile            the sandbox image (node 22, jest 29, babel; network off at run time)
  babel.config.cjs, jest.config.cjs
  test_jsts_verifier.py      reference and wrong answer per task, cheating candidates, lint
  tasks/js/<id>/, tasks/ts/<id>/   task.json, prompt.md, stub/<file>, hidden/<spec file>, hidden/<reference file>
```

## How a task is scored

The model sees `prompt.md`: a fixed output-format header, the upstream exercise statement, and the upstream starting
file (the stub). It answers with one fenced `javascript` or `typescript` block holding the whole solution module (the
last such block counts). In a fresh container (network off, 1 GB, 2 CPUs, 256 pids, all capabilities dropped,
non-root) the module is placed next to the hidden spec file and jest runs it. Reward 1 only if every hidden test
passes. The reply never contains test names or expected values, only a reason and a pass count.

Report integrity: a sentinel test with a random name is added and must be reported as failed, jest must exit with
code 1 and write a readable JSON report, the passed tests must equal the count measured on the reference when the task
was built, and no other test may fail. An empty module, a syntax error, a throw or `process.exit(0)` at import, an
endless loop and a candidate that replaces `expect`, `test` and `describe` all score 0 (`test_jsts_verifier.py`).

## Data

- Source: Exercism practice exercises, `exercism/javascript` and `exercism/typescript` (MIT; the statements come from
  `exercism/problem-specifications`, also MIT). Statement, stub, reference solution (`.meta/proof.ci.*`) and tests are
  upstream, human-written files. Generator: none. Each `task.json` records the upstream commit, the exercise authors
  and the date the reference was first added.
- Selection: exercises whose reference file was first added on or before 2022-12-31 (before AI-assisted
  contributions were common), one solution file, one spec file, at most 30 tests, no `fs`/`child_process`/network
  import, drawn at random with a seed (`build_tasks.py --pick N --seed 17`), not by reading them. Later edits to those
  files were not audited, and the upstream commit is recorded.
- Hidden spec: the upstream spec with `xtest`, `xit` and `xdescribe` switched on (Exercism ships only the first test
  enabled). The expected test count is measured by running the upstream reference.
- `prompt.md` starts with a fixed output-format header. **The header is harness text, not taken from a source** (the
  output protocol, no task content). TSAI has not ruled on it; if it must be human-written, replace `HEADER` in
  `build_tasks.py` and rebuild.
- Exercism exercises are public and widely copied. They are not an evaluation benchmark of ours, but a base model may
  have seen them, which raises its pass rate on them.

## Commands

```bash
docker build -f teams/10-post-training/rl/jsts/jsts.Dockerfile -t g10-jsts-rl:1 teams/10-post-training/rl/jsts   # once, needs network
python teams/10-post-training/rl/jsts/jsts_verifier.py --check-all       # reference 1, stub 0 for every task
python teams/10-post-training/rl/jsts/jsts_verifier.py --reward teams/10-post-training/rl/jsts/tasks/js/<id> completion.txt
python teams/10-post-training/rl/reward.py --check-all --type js         # or --type ts
python -m pytest teams/10-post-training/rl/jsts/test_jsts_verifier.py -q -p no:cacheprovider
python teams/10-post-training/rl/jsts/build_tasks.py --track javascript --clone <exercism/javascript clone> --slug <slug>
```

## Limits

- The candidate runs in the same process as jest, so it can read the hidden spec file in its own container and could,
  in principle, learn what the tests expect. The sentinel and the count checks stop a forged report, not reading the
  spec. The same limit is stated for SWE environments in `swe-envs/README.md`.
- TypeScript is stripped by babel and not type-checked: a type error scores like valid code.
- One test framework (jest) and one source (Exercism); a few tasks per language.
