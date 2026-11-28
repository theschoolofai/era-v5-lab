"""run_lab5_dt_study.py: a two-step run of every arm kind, and the gradient-coverage check.

    python -m pytest dt/test_lab5_dt_study.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("torch")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_lab5_dt_study as study  # noqa: E402


def test_a_short_run_reports_every_requested_arm(tmp_path):
    out = tmp_path / "study.json"
    arms = ["full", "full_muon", "lora", "dt_official_64", "dt_muon_gates_0.001", "dt_keep_64_recompute"]
    assert study.main(["--seeds", "1", "--steps", "2", "--pretrain-steps", "2", "--corpus-bytes", "20000",
                       "--only", *arms, "--out", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert [r["arm"] for r in report["arms"]] == [a for a in (s["arm"] for s in study.arms(1)) if a in arms]
    by = {r["arm"]: r for r in report["arms"]}
    assert by["dt_official_64"]["ship"].startswith("packed keep mask") and by["dt_official_64"]["mask_bits"] > 0
    assert by["dt_keep_64_recompute"]["saved_activation_bytes"] < by["dt_official_64"]["saved_activation_bytes"]
    assert all(f"`{a}`" in report["table"] for a in arms)


def test_recompute_leaves_the_gradient_coverage_lists_unchanged_and_explained(tmp_path):
    out = tmp_path / "coverage.json"
    assert study.main(["--seeds", "1", "--coverage", "--out", str(out)]) == 0
    checks = json.loads(out.read_text(encoding="utf-8"))["checks"]
    assert [c["check"] for c in checks] == ["full_recompute", "lora_recompute", "dt_recompute"]
    for c in checks:
        assert c["pass"] and c["lists_identical"] and c["ref_coverage"]["zero_grad_count"] > 0
