"""completion_logprobs for Team 5's policy: the output head runs on the completion positions only (change 1).
It must give the values of the old path
(full forward sliced, log_softmax + gather) to float rounding, in every caller (job RLM, 24 Nov 2026)."""
from __future__ import annotations

import sys
from pathlib import Path

import torch
from torch import nn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import policy as P  # noqa: E402
import train  # noqa: E402
from test_g5_sample_many import adapter_yaml, bundle, needs_standin  # noqa: E402,F401  Team 5 run folder (stand-in)


def _old_lp(pol, seq, plen):
    """The code before job RLM, verbatim."""
    logits = pol.logits(seq)[:, plen - 1:-1, :].float()
    return torch.log_softmax(logits, -1).gather(-1, seq[:, plen:, None]).squeeze(-1)


# --- change 1: head on completion positions only --------------------------------------------------------------------

class _HeadSpy:
    """Tokens per head call (all leading dims flattened)."""

    def __init__(self, model):
        self.calls = []
        self.handle = model.head.register_forward_pre_hook(
            lambda mod, args: self.calls.append(args[0].numel() // args[0].shape[-1]))

    def close(self):
        self.handle.remove()


def _seq(V, rows, plen, new, seed=3):
    g = torch.Generator().manual_seed(seed)
    return torch.randint(16, min(V, 30000), (rows, plen + new), generator=g)


@needs_standin
def test_team5_policy_runs_the_head_on_completion_positions_only_in_every_caller(bundle):
    """No caller may fall back to the full-sequence head for Team 5's policy: the update, old_lp (chunked), the
    identical-weights gate and kl_to_start all go through completion_logprobs. Fails if the policy loses hidden/head
    (the head then sees plen + new positions) or if a caller bypasses the split path."""
    pol = bundle.policy()
    assert pol._hidden is not None and pol._head is not None
    plen, new = 7, 5
    seq = _seq(bundle.spec["vocab_size"], 3, plen, new)
    cmask = torch.ones(3, new, dtype=torch.bool)
    spy = _HeadSpy(bundle.model)
    try:
        with torch.no_grad():
            old = train.chunked_logprobs(pol, seq, plen, 2)
        n_tok = int(cmask.sum())
        train.backward_objective_v1(pol, (seq, cmask, torch.tensor([1.0, -1.0, 0.5]), old, None, plen, None), 0.2,
                                    n_tok, 1)
        gate = train.logprob_gate(pol, bundle.model, [(seq, cmask, plen, None)], "eval", 0.2, 2)
        roll = type("R", (), {"seq": seq, "cmask": cmask})()

        class _Start:
            def swap(self):
                pass
        train.kl_to_start(pol, _Start(), [roll], [[0] * plen])
    finally:
        spy.close()
    # rows per call are 1 to 3, so the split path gives multiples of `new` (5, 10, 15) and the old full-sequence head
    # gives multiples of plen + new (12, 24, 36): disjoint
    assert spy.calls and set(spy.calls) <= {new, 2 * new, 3 * new}, spy.calls
    assert gate["ok"]


@needs_standin
def test_team5_split_path_equals_the_old_full_forward(bundle):
    pol = bundle.policy()
    plen, new = 6, 9
    seq = _seq(bundle.spec["vocab_size"], 2, plen, new, seed=4)
    with torch.no_grad():
        new_lp = P.completion_logprobs(pol, seq, plen).double()
        old_lp = _old_lp(pol, seq, plen).double()
        logits64 = pol.logits(seq)[:, plen - 1:-1, :].double()
        ref = torch.log_softmax(logits64, -1).gather(-1, seq[:, plen:, None]).squeeze(-1)
    assert (new_lp - old_lp).abs().max() < 5e-5
    assert (new_lp - ref).abs().max() <= (old_lp - ref).abs().max() + 1e-6


def test_split_head_gradients_equal_the_old_path():
    """A per-position head on a toy trunk: loss and gradients of the split path equal the old one (fp32)."""
    torch.manual_seed(5)

    class Toy(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb, self.mix, self.head = nn.Embedding(50, 8), nn.Linear(8, 8), nn.Linear(8, 50)

        def hidden(self, ids, valid):
            x = self.emb(ids)
            return torch.tanh(self.mix(x.cumsum(1)))  # causal mixing over positions

        def forward(self, ids, valid):
            return self.head(self.hidden(ids, valid))

    m = Toy()
    seq = torch.randint(0, 50, (2, 11))
    plen = 4
    grads = []
    for pol, fn in ((P.module_policy(m), _old_lp), (P.module_policy(m, split_head=True), P.completion_logprobs)):
        m.zero_grad()
        lp = fn(pol, seq, plen)
        lp.sum().backward()
        grads.append(([p.grad.clone() for p in m.parameters()], lp.detach()))
    (g0, lp0), (g1, lp1) = grads
    assert (lp0 - lp1).abs().max() < 1e-5
    assert max(float((a - b).abs().max()) for a, b in zip(g0, g1)) < 1e-6 * max(float(a.abs().max()) for a in g0) + 1e-7


def test_policy_needs_hidden_and_head_together():
    import pytest
    with pytest.raises(ValueError):
        P.Policy(nn.Linear(2, 2), lambda m, i, k: m(i), hidden=lambda m, i, k: i)

