"""Native Muon idle-state regressions, including the actual fused MoE autograd path."""
import io
from pathlib import Path
import sys

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from week2.model import MoE
from week2.optim import Muon, zeropower_batched


def parameter(shape=(16, 16)):
    return torch.nn.Parameter(torch.randn(shape) * 0.1)


def baseline_step(p, buf, grad, *, lr=0.02, momentum=0.95, nesterov=True, weight_decay=0.0):
    """Pre-guard native update, retaining foreach and batched numerical operations."""
    torch._foreach_lerp_([buf], [grad], 1 - momentum)
    gs = torch._foreach_lerp([grad], [buf], momentum) if nesterov else [buf]
    u = zeropower_batched(torch.stack(gs), 5)[0]
    with torch.no_grad():
        if weight_decay:
            p.mul_(1 - lr * weight_decay)
        p.add_(u.to(p.dtype), alpha=-lr * max(1.0, p.shape[0] / p.shape[1]) ** 0.5)


@pytest.mark.parametrize("idle", ["zero", "none"])
@pytest.mark.parametrize("weight_decay", [0.0, 0.1])
def test_idle_preserves_weights_and_momentum(idle, weight_decay):
    torch.manual_seed(0)
    p = parameter()
    opt = Muon([p], lr=0.02, weight_decay=weight_decay)
    p.grad = torch.randn_like(p)
    opt.step()
    start, buf = p.detach().clone(), opt.state[p]["buf"].clone()
    for _ in range(50):
        p.grad = torch.zeros_like(p) if idle == "zero" else None
        opt.step()
        assert torch.equal(p, start)
        assert torch.equal(opt.state[p]["buf"], buf)


@pytest.mark.parametrize("idle", ["zero", "none"])
def test_first_idle_is_lazy_and_activation_matches_fresh(idle):
    p = parameter()
    q = torch.nn.Parameter(p.detach().clone())
    opt, fresh = Muon([p], lr=0.02), Muon([q], lr=0.02)
    for _ in range(3):
        p.grad = torch.zeros_like(p) if idle == "zero" else None
        opt.step()
    assert p not in opt.state
    assert opt.state_dict()["state"] == {}
    p.grad = torch.randn_like(p)
    q.grad = p.grad.clone()
    opt.step()
    fresh.step()
    assert torch.equal(p, q)
    assert torch.equal(opt.state[p]["buf"], fresh.state[q]["buf"])


@pytest.mark.parametrize("nesterov", [False, True])
@pytest.mark.parametrize("shape", [(8, 4), (4, 8), (4, 4)])
def test_nonzero_parity_and_tiny_gradient(nesterov, shape):
    p = parameter(shape)
    q, buf = p.detach().clone(), torch.zeros_like(p)
    opt = Muon([p], lr=0.02, nesterov=nesterov, weight_decay=0.1)
    for scale in [1.0, 1e-12, 1e-30]:
        p.grad = torch.randn_like(p) * scale
        baseline_step(q, buf, p.grad, nesterov=nesterov, weight_decay=0.1)
        opt.step()
        assert torch.equal(p, q)
        assert torch.equal(opt.state[p]["buf"], buf)
    # A genuinely tiny first gradient must initialize and follow the original update too.
    r = parameter(shape)
    before = r.detach().clone()
    tiny = Muon([r], lr=0.02, nesterov=nesterov)
    r.grad = torch.full_like(r, 1e-12)
    expected, expected_buf = before.clone(), torch.zeros_like(r)
    baseline_step(expected, expected_buf, r.grad, nesterov=nesterov)
    tiny.step()
    assert torch.equal(r, expected)
    assert torch.equal(tiny.state[r]["buf"], expected_buf)
    assert not torch.equal(r, before)


def test_mixed_same_shape_group_keeps_active_results():
    ps = [parameter((4, 4)) for _ in range(4)]
    opt = Muon(ps, lr=0.02)
    for p in ps:
        p.grad = torch.randn_like(p)
    opt.step()
    before = [p.detach().clone() for p in ps]
    bufs = [opt.state[p]["buf"].clone() for p in ps]
    for i, p in enumerate(ps):
        p.grad = torch.randn_like(p) if i in (0, 3) else (torch.zeros_like(p) if i == 1 else None)
    for i in (0, 3):
        baseline_step(before[i], bufs[i], ps[i].grad)
    opt.step()
    for p, expected, buf in zip(ps, before, bufs):
        assert torch.equal(p, expected)
        assert torch.equal(opt.state[p]["buf"], buf)


def test_state_roundtrip_across_idle_with_unused_parameter():
    ps = [parameter((4, 4)), parameter((4, 4))]
    opt = Muon(ps, lr=0.02)
    ps[0].grad = torch.randn_like(ps[0])
    opt.step()
    ps[0].grad, ps[1].grad = torch.zeros_like(ps[0]), None
    opt.step()
    stream = io.BytesIO()
    torch.save(opt.state_dict(), stream)
    stream.seek(0)
    qs = [torch.nn.Parameter(p.detach().clone()) for p in ps]
    restored = Muon(qs, lr=0.02)
    restored.load_state_dict(torch.load(stream, weights_only=True))
    assert qs[1] not in restored.state
    assert torch.equal(restored.state[qs[0]]["buf"], opt.state[ps[0]]["buf"])
    for mode in ("zero", "active", "none", "active"):
        for p, q in zip(ps, qs):
            p.grad = torch.randn_like(p) if mode == "active" else (torch.zeros_like(p) if mode == "zero" else None)
            q.grad = None if p.grad is None else p.grad.clone()
        opt.step()
        restored.step()
        for p, q in zip(ps, qs):
            assert torch.equal(p, q)
            if p in opt.state:
                assert torch.equal(opt.state[p]["buf"], restored.state[q]["buf"])


def test_real_fused_moe_zero_gradients_skip_only_idle_expert():
    torch.manual_seed(42)
    m = MoE({"n_embd": 4, "moe": {"ffn_hidden": 4, "top_k": 1,
            "num_experts": 2, "num_shared": 0, "bias": False}})
    params = [p for e in m.experts for p in e.parameters()]
    opt = Muon(params, lr=0.02)
    x, valid = torch.ones(1, 3, 4), torch.ones(1, 3, dtype=torch.bool)
    def backward_for(expert):
        m.zero_grad(set_to_none=True)
        with torch.no_grad():
            m.router.weight.fill_(-1)
            m.router.weight[expert].fill_(1)
        m(x, valid).square().sum().backward()
    # Populate the soon-idle expert's real momentum first.
    backward_for(1)
    opt.step()
    before = [p.detach().clone() for p in params]
    idle_bufs = [opt.state[p]["buf"].clone() for p in m.experts[1].parameters()]
    backward_for(0)
    for p in m.experts[1].parameters():
        assert p.grad is not None
        assert torch.count_nonzero(p.grad) == 0
    for p in m.experts[0].parameters():
        assert torch.count_nonzero(p.grad) > 0
    opt.step()
    for p, prior in zip(m.experts[0].parameters(), before[:3]):
        assert not torch.equal(p, prior)
    for p, prior, buf in zip(m.experts[1].parameters(), before[3:], idle_bufs):
        assert torch.equal(p, prior)
        assert torch.equal(opt.state[p]["buf"], buf)
