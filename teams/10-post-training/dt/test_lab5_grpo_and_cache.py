"""Tests for Lab 5 rollout cache, RL Hybrid Muon + keep_zero guard, and 3-arm GRPO stand-in."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch
import torch.nn as nn

TEAM10 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM10 / "rl-loop"))
sys.path.insert(0, str(TEAM10 / "capstone"))
sys.path.insert(0, str(TEAM10 / "dt"))

import hybrid_optim as ho  # noqa: E402
import keep_zero as kz  # noqa: E402
import rollout_cache as rc  # noqa: E402


def test_rollout_cache_roundtrip_and_key_binding(tmp_path):
    cache = rc.RolloutCache(tmp_path)
    k1 = rc.cache_key(checkpoint_sha256="abc123", prompt_ids=["p1", "p2"], sampler_cfg={"k": 4, "temp": 1.0})
    k2 = rc.cache_key(checkpoint_sha256="def456", prompt_ids=["p1", "p2"], sampler_cfg={"k": 4, "temp": 1.0})
    assert k1 != k2
    assert cache.get(k1) is None

    payload = {"seq": torch.tensor([[1, 2, 3]]), "rewards": torch.tensor([1.0])}
    cache.put(k1, payload, meta={"arm": "full"})
    got = cache.get(k1)
    assert got is not None
    assert torch.equal(got["seq"], payload["seq"])
    assert torch.equal(got["rewards"], payload["rewards"])
    assert cache.stats()["hits"] == 1 and cache.stats()["misses"] == 1


def test_keep_zero_accepts_unwrapped_adamw_and_refuses_hybrid_muon_without_enforce():
    m = nn.Sequential(nn.Linear(8, 8, bias=False))
    keep = {"0.weight": torch.ones_like(m[0].weight, dtype=torch.bool)}
    keep["0.weight"][0, 0] = False
    with torch.no_grad():
        m[0].weight[0, 0] = 0.0

    guard_no_enforce = kz.KeepZero(list(m.named_parameters()), keep, enforce=False)
    opt_adamw = ho.build_optimizer(m.named_parameters(), kind="adamw", lr=1e-4)
    guard_no_enforce.check_optimizer(opt_adamw.named[0][1])  # passes

    opt_muon = ho.build_optimizer(m.named_parameters(), kind="hybrid_muon", lr=1e-4, muon_lr=1e-3)
    with pytest.raises(ValueError, match="keep_zero gradient mask needs Adam/AdamW"):
        guard_no_enforce.check_optimizer(opt_muon)

    guard_enforce = kz.KeepZero(list(m.named_parameters()), keep, enforce=True)
    guard_enforce.check_optimizer(opt_muon)  # passes when enforce=True
