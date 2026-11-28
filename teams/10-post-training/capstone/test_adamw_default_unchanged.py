"""The default optimizer stays what it was before the HybridOptimizer wrapper: same update, same betas, same saved layout.

    python -m pytest capstone/test_adamw_default_unchanged.py -q
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
import yaml  # noqa: E402
from torch import nn  # noqa: E402

parametrize = pytest.mark.parametrize
HERE = Path(__file__).resolve().parent
RL = HERE.parent / "rl-loop"
sys.path[:0] = [str(HERE), str(RL)]
import hybrid_optim as ho  # noqa: E402


def _net():
    torch.manual_seed(0)
    return nn.Sequential(nn.Linear(6, 6), nn.Tanh(), nn.Linear(6, 2))


def _steps(model, opt, n=4, start=0):
    for i in range(start, start + n):
        opt.zero_grad()
        model(torch.randn(8, 6, generator=torch.Generator().manual_seed(i))).pow(2).mean().backward()
        opt.step()


def _equal(a, b):
    return all(torch.equal(x, y) for x, y in zip(a.state_dict().values(), b.state_dict().values()))


def test_a_state_saved_by_plain_adamw_resumes_in_the_wrapper_and_the_reverse():
    a = _net()
    plain = torch.optim.AdamW(a.parameters(), lr=1e-2, weight_decay=0.0)
    _steps(a, plain)
    b, c = copy.deepcopy(a), copy.deepcopy(a)
    wrapped = ho.build_optimizer(b.named_parameters(), kind="adamw", lr=1e-2, betas=(0.9, 0.999))
    wrapped.load_state_dict(copy.deepcopy(plain.state_dict()))  # load_state_dict shares tensors: copy as a save would
    back = torch.optim.AdamW(c.parameters(), lr=1e-2, weight_decay=0.0)
    back.load_state_dict(copy.deepcopy(wrapped.state_dict()))
    assert set(wrapped.state_dict()) == {"state", "param_groups"}
    for model, opt in ((a, plain), (b, wrapped), (c, back)):
        _steps(model, opt, start=4)
    assert _equal(a, b) and _equal(a, c)


def test_a_state_saved_in_the_nested_layout_still_loads():
    a = _net()
    first = ho.build_optimizer(a.named_parameters(), kind="adamw", lr=1e-2)
    _steps(a, first)
    nested = {"meta": first.meta, "optim_seconds": 1.5, "steps": 4, "optimizers": {"adamw": first.named[0][1].state_dict()}}
    second = ho.build_optimizer(a.named_parameters(), kind="adamw", lr=1e-2)
    second.load_state_dict(nested)
    assert second.steps == 4 and second.state_dict()["state"].keys() == first.state_dict()["state"].keys()


def test_hybrid_muon_keeps_the_nested_layout():
    a = _net()
    opt = ho.build_optimizer(a.named_parameters(), kind="hybrid_muon", lr=1e-3, muon_lr=1e-3)
    _steps(a, opt)
    assert set(opt.state_dict()["optimizers"]) == {"muon", "adamw"}


@parametrize("kind, beta2", [("adamw", 0.999), ("hybrid_muon", 0.95)])
def test_the_rl_trainer_builds_adamw_with_these_betas(tmp_path, monkeypatch, kind, beta2):
    import train  # noqa: PLC0415  rl-loop/train.py

    seen = []

    class Recording(torch.optim.AdamW):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            seen.append((self.defaults["betas"], self.defaults["eps"], self.defaults["weight_decay"]))

    monkeypatch.setattr(torch.optim, "AdamW", Recording)
    cfg = yaml.safe_load((RL / "config" / "smoke_tiny_olmoe.yaml").read_text())
    cfg.update(out_dir=str(tmp_path / "out"), verbose=False)
    cfg["task"].update(n_train=16, n_heldout=4)
    cfg["train"].update(steps=1, eval_every=1, eval_k=2, prompts_per_step=2, k=2, ppo_epochs=1, optimizer=kind)
    train.train(cfg)
    assert seen == [((0.9, beta2), 1e-8, 0.0)]
