"""Tests for dt/bench_gpu_muon_recompute.py (works on CPU in CI and verifies Rule #6 coverage)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bench_gpu_muon_recompute as bgmr  # noqa: E402


def test_bench_gpu_muon_recompute_cpu_smoke_and_coverage_lists_match(tmp_path):
    out = tmp_path / "out.json"
    rc = bgmr.main([
        "--device", "cpu",
        "--layers", "2",
        "--embd", "32",
        "--heads", "4",
        "--kv-heads", "2",
        "--ffn-hidden", "16",
        "--vocab", "128",
        "--batch", "2",
        "--seq-len", "16",
        "--no-bf16",
        "--warmup", "1",
        "--steps", "2",
        "--out", str(out),
    ])
    assert rc == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    arms = {r["arm"]: r for r in doc["arms"]}
    assert set(arms) == {
        "full_adamw",
        "full_hybrid_muon",
        "full_hybrid_muon_recompute",
        "lora_adamw",
        "dt_adamw",
        "dt_adamw_recompute",
    }
    for r in arms.values():
        assert r["median_step_ms"] > 0
        assert 0.0 <= r["optim_step_share"] <= 1.0
        assert r["tok_s"] > 0
    assert doc["gradient_coverage"], "Rule #6 coverage entries must be present"
    for cov in doc["gradient_coverage"]:
        assert cov["lists_identical"] is True, f"Coverage mismatch on {cov['pair']}"
        assert cov["fast_off"]["none_grads"] == []
        assert cov["fast_on"]["none_grads"] == []
        assert cov["max_abs_grad_diff"] < 1e-4
