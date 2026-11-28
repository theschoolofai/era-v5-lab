"""Gradient-coverage check for speed and kernel claims (Lab rule, 28 Nov).

After one forward and backward, list every trainable parameter whose gradient is None or all zero, say why each one
is allowed, run it with the fast path on and off, and compare the two lists. A faster step that skips a gradient is not faster.

Library use (any team, any torch model):

    from grad_coverage import scan, compare
    off = scan(model, lambda: loss_fn(model, batch).backward())
    on  = scan(fast_model, lambda: loss_fn(fast_model, batch).backward())
    print(compare(off, on))

Command line, on the Team 5 reference model with a tiny config (CPU, seconds):

    python teams/05-architecture/lab5/gradient_coverage/grad_coverage.py --fast model.attn_impl=sdpa
    python teams/05-architecture/lab5/gradient_coverage/grad_coverage.py --fast model.attn_impl=sdpa --json out.json

Exit code 0: both lists are explained and identical. 1: a parameter is uncovered without a reason, or the two lists differ.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

import torch

OK, NONE, ZERO = "ok", "none", "zero"


def scan(model, step):
    """Zero the grads (set to None), call step() (it must run forward AND backward), classify every trainable parameter.

    Returns {name: {"state": ok|none|zero, "numel": int, "grad_abs_max": float|None}}.
    """
    model.zero_grad(set_to_none=True)
    step()
    out = {}
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if p.grad is None:
            out[name] = {"state": NONE, "numel": p.numel(), "grad_abs_max": None}
            continue
        m = float(p.grad.detach().abs().max()) if p.numel() else 0.0
        out[name] = {"state": ZERO if m == 0.0 else OK, "numel": p.numel(), "grad_abs_max": m}
    return out


def uncovered(result):
    return {n: r["state"] for n, r in result.items() if r["state"] != OK}


def compare(off, on):
    """Parameters whose coverage state differs between the two runs (or exists in only one)."""
    diffs = []
    for name in sorted(set(off) | set(on)):
        a = off.get(name, {}).get("state", "missing")
        b = on.get(name, {}).get("state", "missing")
        if a != b:
            diffs.append({"name": name, "off": a, "on": b})
    return diffs


def explain(name, state, allow=(), expert_load=None):
    """A reason an uncovered parameter is allowed, or None. `allow` is a list of (regex, reason).

    Built in: an expert that received 0 tokens in this batch has an all-zero gradient by construction
    (needs `expert_load` = {layer_index: [tokens per expert]}).
    """
    m = re.match(r"blocks\.(\d+)\.moe\.experts\.(\d+)\.", name)
    if m and expert_load is not None and state == ZERO:
        layer, e = int(m.group(1)), int(m.group(2))
        if layer in expert_load and int(expert_load[layer][e]) == 0:
            return f"expert {e} of layer {layer} received 0 tokens in this batch"
    for pattern, reason in allow:
        if re.search(pattern, name):
            return reason
    return None


def report(result, allow=(), expert_load=None):
    rows = []
    for name, state in uncovered(result).items():
        rows.append({"name": name, "state": state, "numel": result[name]["numel"],
                     "reason": explain(name, state, allow, expert_load)})
    return rows


# ---- Team 5 reference model driver -------------------------------------------------------------------------------

def _team5():
    team = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(team / "harness"))
    sys.path.insert(0, str(team / "tests"))
    return team


def _set(cfg, dotted):
    key, _, value = dotted.partition("=")
    node = cfg
    *path, leaf = key.split(".")
    for part in path:
        node = node[part]
    node[leaf] = json.loads(value) if value[:1] in '0123456789-[{"tf' else value


def build(overrides=(), seed=1234, batch=2, length=8):
    """Tiny T1-style model plus one fixed batch. Overrides are dotted `model.attn_impl=sdpa` pairs."""
    team = _team5()
    from test_week2_model import fixture
    from week2.model import LanguageModel

    c, rows, lengths = fixture()
    for o in overrides:
        _set(c, o)
    torch.manual_seed(seed)
    model = LanguageModel(c["model"], rows, lengths)
    g = torch.Generator().manual_seed(seed)
    v = c["model"]["vocab_size"]
    ids = torch.randint(0, v, (batch, length), generator=g)
    targets = torch.randint(0, v, (batch, length), generator=g)
    return model, ids, targets


def team5_step(model, ids, targets):
    _team5()
    from train_week2 import scored_ntp_loss

    def step():
        model.start_expert_load()
        model.train()
        scored_ntp_loss(model, ids, targets).backward()
    return step


def expert_loads(model):
    return {i: b.moe.expert_load.tolist() for i, b in enumerate(model.blocks) if b.moe.expert_load is not None}


def run(fast, allow, seed=1234):
    """fast: list of dotted overrides that switch the fast path ON. Same seed, same weights, same batch for both."""
    results = {}
    loads = {}
    for label, ov in (("off", []), ("on", list(fast))):
        model, ids, targets = build(ov, seed)
        if label == "on":
            base, _, _ = build([], seed)
            model.load_state_dict(base.state_dict())   # identical weights; only the fast path differs
        results[label] = scan(model, team5_step(model, ids, targets))
        loads[label] = expert_loads(model)
    return {
        "off": report(results["off"], allow, loads["off"]),
        "on": report(results["on"], allow, loads["on"]),
        "differences": compare(results["off"], results["on"]),
        "trainable": {k: len(v) for k, v in results.items()},
    }


def render(res, fast):
    lines = [f"# Gradient coverage, fast path = {', '.join(fast) or '(none)'}", ""]
    for label in ("off", "on"):
        rows = res[label]
        lines += [f"## Fast path {label}: {len(rows)} of {res['trainable'][label]} trainable parameters not covered", ""]
        if rows:
            lines += ["| parameter | state | numel | why allowed |", "|---|---|---:|---|"]
            lines += [f"| `{r['name']}` | {r['state']} | {r['numel']} | {r['reason'] or '**UNEXPLAINED**'} |" for r in rows]
            lines.append("")
    d = res["differences"]
    lines += [f"## Difference between the two lists: {len(d)}", ""]
    lines += [f"- `{x['name']}`: off={x['off']}, on={x['on']}" for x in d] or ["Identical."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fast", action="append", default=[], help="dotted override that turns the fast path on, e.g. model.attn_impl=sdpa")
    ap.add_argument("--allow", action="append", default=[], metavar="REGEX=REASON", help="an uncovered parameter that is allowed, with the reason")
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    allow = [tuple(x.split("=", 1)) for x in a.allow]
    res = run(a.fast, allow, a.seed)
    sys.stdout.write(render(res, a.fast))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
    bad = any(r["reason"] is None for lab in ("off", "on") for r in res[lab]) or res["differences"]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
