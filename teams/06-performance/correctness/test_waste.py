"""perfkit/waste.py (Design 6): the between-run arithmetic on a hand-made run record, and a CPU smoke of within."""
import json
from pathlib import Path

import pytest

from perfkit import waste

ROOT = Path(__file__).resolve().parents[1]


def _record(d: Path):
    # 4 steps of 100 ms, an eval after step 2 and after step 4; commits at steps 0, 2, 4.
    rows = [{"step": s, "perf/step_ms": 100.0, "train/input_positions": 10, "train/scored_tokens": 4}
            for s in range(1, 5)]
    rows[1]["val/bpb"] = 1.0
    rows[3]["val/bpb"] = 1.0
    (d / "metrics.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    (d / "summary.json").write_text(json.dumps({"run_id": "t", "status": "COMPLETED", "wall_seconds": 2.0}))
    commits = [{"step": 0, "time": 10.0}, {"step": 2, "time": 10.9}, {"step": 4, "time": 11.8}]
    (d / "commits.jsonl").write_text("\n".join(json.dumps(c) for c in commits) + "\n")


def test_between_splits_wall_into_steps_and_outside(tmp_path):
    _record(tmp_path)
    r = waste.between(str(tmp_path))
    assert r["steps"] == 4 and r["in_steps_s"] == pytest.approx(0.4)
    assert r["outside_steps_s"] == pytest.approx(1.6) and r["outside_steps_pct"] == pytest.approx(80.0)
    assert r["fill_scored_over_positions"]["median"] == pytest.approx(0.4)
    assert r["eval_steps"] == 2
    iv = r["commit_intervals"]
    assert [(x["from_step"], x["to_step"], x["evals"]) for x in iv] == [(0, 2, 1), (2, 4, 1)]
    assert iv[0]["wall_s"] == pytest.approx(0.9) and iv[0]["outside_steps_s"] == pytest.approx(0.7)
    assert r["outside_commit_span_s"] == pytest.approx(0.2)
    assert "fit_outside_vs_evals" not in r           # every interval has one eval: no slope to fit


def test_within_runs_on_cpu(tmp_path):
    r = waste.within(str(ROOT / "configs" / "tiny_cpu.yaml"), ["data.source=synthetic"], steps=3, warmup=1,
                     gap_floor_ms=0.5)
    assert r["steps"] == 3 and len(r["per_step"]) == 3
    assert r["step_ms"]["n"] == 3 and r["step_ms"]["median"] > 0
    if r["device"] == "cpu":
        assert r["host_gap_ms"] is None and r["gpu_wait_share_pct"] is None
    else:
        assert r["loader_ms"]["n"] == 3 and 0 <= r["gpu_wait_share_pct"] <= 100
