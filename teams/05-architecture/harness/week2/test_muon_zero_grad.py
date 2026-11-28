"""Failing test: Muon drift on a parameter whose gradient is all zeros (idle MoE expert).

The claim (Team 10 Lab 5 plan, Sat 28 Nov): in the fused MoE the expert weights are built as
`torch.stack([e.gate.weight for e in self.experts])` (`model.py:265-267`), so an expert that receives no tokens
still gets an all-zero gradient tensor rather than `None`. `Muon.step` skips only `p.grad is None`
(`optim.py:78`), so a zeros gradient falls through to `zeropower_batched`, which normalises by the gradient
norm (`optim.py:46`). A stale momentum buffer therefore comes back at full unit spectral norm and Muon applies
a normal-sized step to an expert that saw nothing.

Measured on `main` at `57bdc7b`, one real step then 50 zero-gradient steps:

    total weight drift   3.7541
    original norm        1.5093
    final norm           4.1963     (2.78x growth from ZERO gradients)

Run:

    python -m pytest teams/05-architecture/harness/week2/test_muon_zero_grad.py -q

Expected today: the two `idle_expert` tests fail, the `none_grad` control passes.
"""

import sys
from pathlib import Path

import pytest
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from optim import Muon  # noqa: E402


def _muon(lr=0.02, n=16):
    torch.manual_seed(0)
    p = torch.nn.Parameter(torch.randn(n, n) * 0.1)
    opt = Muon([p], lr=lr, momentum=0.95, nesterov=True, ns_steps=5, weight_decay=0.0)
    return p, opt


def _one_real_step_then_zero_grads(n_zero_steps):
    """Build momentum with one real gradient, then feed zeros, as an idle expert receives."""
    p, opt = _muon()
    opt.zero_grad(set_to_none=True)
    p.grad = torch.randn_like(p)
    opt.step()
    start = p.detach().clone()
    for _ in range(n_zero_steps):
        opt.zero_grad(set_to_none=True)
        p.grad = torch.zeros_like(p)      # NOT None: this is what torch.stack of expert weights produces
        opt.step()
    return start, p.detach()


def test_idle_expert_is_not_moved_by_zero_gradients():
    """A parameter that receives only zero gradients must not change after the momentum decays."""
    start, end = _one_real_step_then_zero_grads(50)
    drift = float((end - start).norm())
    assert drift < 1e-3, (
        f"Muon moved an idle parameter by {drift:.4f} on 50 zero-gradient steps "
        f"(norm {float(start.norm()):.4f} -> {float(end.norm()):.4f}). "
        "An expert that gets no tokens is being trained by its own momentum."
    )


def test_idle_expert_weight_norm_does_not_grow():
    """The weight norm must not grow from zero gradients; zeropower_batched renormalises stale momentum."""
    start, end = _one_real_step_then_zero_grads(50)
    ratio = float(end.norm()) / float(start.norm())
    assert ratio < 1.05, (
        f"idle parameter norm grew {ratio:.2f}x from ZERO gradients "
        "(zeropower_batched divides by ||X|| + eps, so stale momentum returns at unit spectral norm)"
    )


def test_none_gradient_is_still_skipped():
    """Control: the existing `p.grad is None` guard must keep working, so the fix cannot break it."""
    p, opt = _muon()
    opt.zero_grad(set_to_none=True)
    p.grad = torch.randn_like(p)
    opt.step()
    start = p.detach().clone()
    for _ in range(5):
        opt.zero_grad(set_to_none=True)
        p.grad = None
        opt.step()
    assert float((p.detach() - start).norm()) == 0.0


def test_zero_gradient_norm_is_reported():
    """The condition a fix needs: an all-zero gradient is detectable as grad.norm() == 0."""
    g = torch.zeros(16, 16)
    assert float(g.norm()) == 0.0
    assert g is not None


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
