# Gradient-coverage check (Lab rule of 28 Nov)

Author: Vardhan Walavalkar (`vpw`), Team 5 (Architecture).

TSAI's rule: every speed or kernel claim comes with a gradient-coverage check. After one forward and backward, list every trainable
parameter whose gradient is None or all zero, say why each is allowed, run it with the fast path on and off, and compare the two lists.

`grad_coverage.py` does that for any torch model (`scan`, `compare`, `report`) and has a driver for the Team 5 reference model.

```sh
python teams/05-architecture/lab5/gradient_coverage/grad_coverage.py --fast model.attn_impl=sdpa
python teams/05-architecture/lab5/gradient_coverage/grad_coverage.py --fast model.attn_impl=sdpa --allow 'mtp_head=unused when mtp is false' --json out.json
python -m pytest teams/05-architecture/tests/test_lab5_grad_coverage.py
```

- Same seed, same weights, same batch for both runs; only the listed overrides differ. Exit code 0 means every uncovered parameter has a
  reason and the two lists are identical; 1 otherwise.
- States: `none` (grad is None), `zero` (all elements exactly 0), `ok`. Exactly-zero only. A near-zero gradient (about 1e-10) counts as
  covered; that is the router-row case sourav dhar raised on #892, which this check cannot see by design.
- Built-in reason: an expert that received 0 tokens in the batch has an all-zero gradient (checked against the recorded expert load).
  Anything else needs `--allow REGEX=REASON`, or it prints **UNEXPLAINED**.
- For another fast path, pass any dotted config override (`--fast model.moe.xxx=true`), or use the library calls with your own step function.

## What was run, and what was not
- Run: the tiny T1-style fixture of `tests/test_week2_model.py` (2 layers, 4 experts, CPU). Eager vs `attn_impl=sdpa`: 0 uncovered, identical lists.
- Not run: the T2 or dry-run-2 shapes (needs a GPU), `head_mode: kas_v2`, `mtp: true`, and the batched MoE path under bf16. The driver accepts them as
  overrides but they are untested here. Dry-run-2 numbers are in #869, not reproduced here.
- Unit tests include a negative control: a path that skips `a` is caught by `compare`, and an idle expert is explained only when its recorded load is 0.
