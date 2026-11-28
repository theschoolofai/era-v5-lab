"""Unit tests for TSAI 28 Nov Rule #6 gradient-coverage check (dt/check_grad_coverage.py)."""
from __future__ import annotations

import sys
from pathlib import Path

import torch
import torch.nn as nn

TEAM10 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM10 / "dt"))

import check_grad_coverage as cgc  # noqa: E402


def test_grad_coverage_passes_all_fast_paths_on_cpu():
    res = cgc.run_all("cpu")
    assert res["all_pass"] is True
    for c in res["checks"]:
        assert c["pass"], c
        assert c["lists_identical"], c["check"]


def test_audit_grads_flags_unexpected_none_or_zero_grad():
    m = nn.Sequential(nn.Linear(4, 4, bias=False), nn.Linear(4, 4, bias=False))
    x = torch.randn(2, 4)
    (m[0](x)).sum().backward()  # m[1].weight never used -> grad is None
    rep = cgc.audit_grads(m)
    assert not rep["all_explained"]
    assert rep["none_grad_count"] == 1
    assert rep["unexpected_missing_or_zero"][0]["name"] == "1.weight"
