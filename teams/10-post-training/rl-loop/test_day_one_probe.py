"""Failure-path contracts for the aggregate-only TSAI probe."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "capstone"))
import day_one_probe as probe

parametrize = pytest.mark.parametrize


@parametrize("fail", [False, True])
def test_arm_cleans_private_outputs_on_success_and_failure(tmp_path, fail):
    arm = tmp_path / "sft_full"
    arm.mkdir()
    # Run a real child: it writes the artifacts before either returning or failing.
    code = """import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
(p / 'model.safetensors').write_bytes(b'weights')
(p / 'generations.jsonl').write_text('private generation')
(p / 'sft_report.json').write_text(json.dumps({'before': {}, 'after': {}}))
raise SystemExit(int(sys.argv[2]))
"""
    cmd = [sys.executable, "-c", code, str(arm), str(int(fail))]
    if fail:
        with pytest.raises(RuntimeError):
            probe.run_sft_arm(tmp_path, "full", cmd)
    else:
        assert probe.run_sft_arm(tmp_path, "full", cmd)["before"] == {}
    assert sorted(p.name for p in arm.iterdir()) == ["sft_report.json"]


def test_failed_step_does_not_hide_success_or_return_zero(tmp_path):
    def broken():
        raise RuntimeError("failed arm")
    results = {"bad": probe.step(tmp_path, "bad", broken),
               "good": probe.step(tmp_path, "good", lambda: {"value": 3})}
    assert results["good"]["value"] == 3
    assert probe.finish(tmp_path, results) == 1
    assert json.loads((tmp_path / "summary.json").read_text())["failed_steps"] == ["bad"]
    assert probe.finish(tmp_path, {"good": results["good"]}) == 0
