"""indic_share (alarms.py rule 8): the native Indic share's rolling mean leaves 8% +/- the tolerance."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alarms import AlarmMonitor  # noqa: E402

G8 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
ALARMS_PY = G8 / "alarms" / "alarms.py"
DRYRUN2 = REPO / "teams/05-architecture/results/dryrun2-1234/metrics.jsonl"


def run(shares, **kwargs):
    mon = AlarmMonitor(**kwargs)
    fired = []
    for step, share in enumerate(shares, start=1):
        fired += [a for a in mon.step(step, indic_share=share) if a["rule"] == "indic_share"]
    return fired


def test_defaults_are_8_percent_plus_minus_1_point_over_50_batches():
    mon = AlarmMonitor()
    assert (mon.indic_target, mon.indic_tolerance, mon.indic_window) == (0.08, 0.01, 50)


def test_in_band_never_fires():
    # batches that wobble by whole documents (6% to 10%) but average 8%
    assert run([0.06, 0.10] * 200) == []
    assert run([0.071] * 100 + [0.089] * 100) == []


def test_fires_once_when_the_mean_leaves_the_band_and_rearms():
    shares = [0.08] * 60 + [0.0] * 60 + [0.08] * 60 + [0.12] * 60
    fired = run(shares)
    # step 67: 7 zero batches in the window -> 43 x 8% / 50 = 6.88% < 7% (6 zeros: 7.04%, still in the band);
    # back in the band once 44 of the last 50 are 8% again (re-arm); step 193: 13 batches at 12% ->
    # (37 x 8% + 13 x 12%) / 50 = 9.04% > 9% (12 of them: 8.96%).
    assert [(a["step"], a["severity"]) for a in fired] == [(67, "page"), (193, "page")]
    low, high = fired
    assert low["value"] < 0.07 and high["value"] > 0.09
    assert low["target"] == 0.08 and low["tolerance"] == 0.01 and low["window"] == 50
    assert "native Indic share" in low["detail"] and "8% +/- 1 points" in low["detail"]


def test_waits_for_a_full_window():
    assert run([0.0] * 49) == []
    assert [a["step"] for a in run([0.0] * 50)] == [50]


def test_rows_without_or_with_bad_shares_are_ignored():
    mon = AlarmMonitor()
    out = []
    for step in range(1, 200):
        out += mon.step(step, loss_ntp=3.0)  # no indic_share: the rule never runs
    assert not [a for a in out if a["rule"] == "indic_share"]
    assert run([float("nan"), -0.1, 1.5, "abc", None] * 30) == []


def test_custom_target_tolerance_window():
    assert [a["step"] for a in run([0.05] * 20, indic_target=0.05, indic_tolerance=0.005, indic_window=10)] == []
    assert [a["step"] for a in run([0.03] * 20, indic_target=0.05, indic_tolerance=0.005, indic_window=10)] == [10]
    with pytest.raises(ValueError):
        AlarmMonitor(indic_tolerance=0)
    with pytest.raises(ValueError):
        AlarmMonitor(indic_target=1.5)
    with pytest.raises(ValueError):
        AlarmMonitor(indic_window=0)


def test_state_survives_a_restart():
    shares = [0.08] * 40 + [0.0] * 60
    straight = run(shares)
    mon = AlarmMonitor()
    for step, share in enumerate(shares[:70], start=1):
        mon.step(step, indic_share=share)
    resumed = AlarmMonitor()
    resumed.load_state_dict(json.loads(json.dumps(mon.state_dict())))
    after = []
    for step, share in enumerate(shares[70:], start=71):
        after += [a for a in resumed.step(step, indic_share=share) if a["rule"] == "indic_share"]
    before = [a for a in straight if a["step"] <= 70]
    assert before + after == straight


def test_old_checkpoints_without_indic_state_load():
    state = AlarmMonitor().state_dict()
    state.pop("indic")
    mon = AlarmMonitor()
    mon.load_state_dict(state)
    assert [a["step"] for a in run([0.0] * 50)] == [50]


def _cli(*args):
    return subprocess.run([sys.executable, "-I", str(ALARMS_PY), *args], capture_output=True, text=True)


def test_cli_flags(tmp_path):
    f = tmp_path / "m.jsonl"
    f.write_text("\n".join(json.dumps({"step": s, "indic_share": 0.03}) for s in range(1, 21)) + "\n", encoding="utf-8")
    out = _cli("--jsonl", str(f), "--indic-target", "0.05", "--indic-tolerance", "0.01", "--indic-window", "10")
    assert out.returncode == 0
    hits = [json.loads(x) for x in out.stdout.splitlines()]
    assert [(a["rule"], a["step"]) for a in hits] == [("indic_share", 10)]
    assert _cli("--indic-target", "0.08").returncode != 0  # only with --jsonl
    assert _cli("--jsonl", str(f), "--indic-tolerance", "0").returncode != 0


def test_dryrun2_replay_fires_indic_share_once_at_step_50(tmp_path):
    """docs/composition_w5.md: dry run 2 trained on one English shard (#869), so the alarm fires at step 50."""
    if not DRYRUN2.exists():
        pytest.skip("dry run 2 record not in this checkout")
    merged = tmp_path / "metrics.jsonl"
    conv = subprocess.run([sys.executable, "-I", str(G8 / "metrics_logger" / "dryrun2_composition.py"), str(DRYRUN2),
                           "--out", str(merged)], capture_output=True, text=True, check=True)
    assert "1221 with composition" in conv.stderr
    out = _cli("--jsonl", str(merged))
    hits = [json.loads(x) for x in out.stdout.splitlines()]
    indic = [a for a in hits if a["rule"] == "indic_share"]
    assert [(a["step"], a["severity"], a["value"]) for a in indic] == [(50, "page", 0.0)]
