import math
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alarms import AlarmMonitor, max_vio_and_dead, run_synthetic


def test_synthetic_3000_steps():
    res = run_synthetic(steps=3000, seed=15)
    assert res["steps"] == 3000
    assert res["planted"] == 11
    assert res["caught"] == 11
    assert res["missed"] == 0
    assert res["false_alarms"] == 0


@pytest.mark.parametrize("bad", [
    float("nan"), float("inf"), float("-inf"),
    "nan", "inf", "-inf",
    np.float32("nan"), np.float32("inf"),
    torch.tensor(float("nan")), torch.tensor(float("-inf")),
])
def test_non_finite_fires_stop_at_once(bad):
    mon = AlarmMonitor()
    out = mon.check(0, "loss_ntp", bad)
    assert len(out) == 1
    assert out[0]["rule"] == "non_finite"
    assert out[0]["severity"] == "stop"
    assert out[0]["metric"] == "loss_ntp"


def test_spike_score_7sigma_and_no_window_poisoning():
    mon = AlarmMonitor(window=200, min_window=100, sigma_threshold=7.0)
    for s in range(150):
        # Small deterministic oscillation around 2.0 (std ~ 0.01)
        val = 2.0 + (0.01 if s % 2 == 0 else -0.01)
        assert mon.step(s, loss_ntp=val) == []

    # Two consecutive spikes must both page because the first spike does not enter the window.
    a1 = mon.step(150, loss_ntp=2.5)
    a2 = mon.step(151, loss_ntp=2.5)
    assert len(a1) == 1 and a1[0]["rule"] == "spike_score" and a1[0]["severity"] == "page"
    assert len(a2) == 1 and a2[0]["rule"] == "spike_score" and a2[0]["severity"] == "page"


def test_duplicate_loss_and_loss_ntp_fires_once():
    mon = AlarmMonitor()
    out = mon.step(0, loss_ntp=float("nan"), loss=float("nan"))
    assert len(out) == 1
    assert out[0]["metric"] == "loss_ntp"


def test_ema_z_warns_without_paging():
    mon = AlarmMonitor(window=500, min_window=100, sigma_threshold=7.0, ema_warmup=50, ema_z_threshold=2.5)
    for s in range(100):
        val = 1.0 + (0.02 if s % 2 == 0 else -0.02)
        assert mon.step(s, gradient_norm=val) == []
    # 4 sigma excursion: above EMA z=2.5 (warn), below 7 sigma (page).
    out = mon.step(100, gradient_norm=1.08)
    assert len(out) == 1
    assert out[0]["rule"] == "ema_z"
    assert out[0]["severity"] == "warn"


def test_throughput_drop_fires_once_at_patience():
    mon = AlarmMonitor(tps_window=50, tps_drop_fraction=0.10, tps_patience=100)
    # Step 0 setup is ignored.
    assert mon.step(0, tokens_per_second=500.0) == []
    for s in range(1, 51):
        assert mon.step(s, tokens_per_second=40000.0) == []
    fired = []
    for s in range(51, 170):
        fired.extend(mon.step(s, tokens_per_second=32000.0))  # 20% drop
    assert len(fired) == 1
    assert fired[0]["step"] == 150
    assert fired[0]["rule"] == "throughput_drop"


def test_moe_routing_max_vio_and_dead_experts():
    mv, dead = max_vio_and_dead([0.5, 0.5, 0.0, 0.0])
    assert math.isclose(mv, 1.0)
    assert dead == 2

    mon = AlarmMonitor(moe_max_vio_limit=1.0, moe_patience=5)
    for s in range(4):
        assert mon.step(s, expert_load=[0.7, 0.3, 0.0, 0.0]) == []
    out = mon.step(4, expert_load=[0.7, 0.3, 0.0, 0.0])
    assert len(out) == 1
    assert out[0]["rule"] == "moe_routing"
    assert out[0]["dead_experts"] == 2


def _warm_throughput(mon):
    for step in range(21):
        assert mon.step(step, tokens_per_second=100.0) == []


def test_zero_throughput_fires_once_and_rearms_after_recovery():
    mon = AlarmMonitor()
    _warm_throughput(mon)
    alarms = []
    for step in range(21, 171):
        alarms.extend(mon.step(step, tokens_per_second=0.0))
    assert [(a["step"], a["rule"], a["value"]) for a in alarms] == [
        (120, "throughput_drop", 0.0)]
    assert mon.step(171, tokens_per_second=100.0) == []
    alarms = []
    for step in range(172, 272):
        alarms.extend(mon.step(step, tokens_per_second=0.0))
    assert [a["step"] for a in alarms] == [271]


def test_zero_throughput_does_not_build_warmup_baseline():
    mon = AlarmMonitor(tps_patience=2)
    for step in range(30):
        assert mon.step(step, tokens_per_second=0.0) == []
    for step in range(30, 50):
        assert mon.step(step, tokens_per_second=100.0) == []
    assert mon.step(50, tokens_per_second=0.0) == []
    assert mon.step(51, tokens_per_second=0.0)[0]["rule"] == "throughput_drop"


@pytest.mark.parametrize("interruption", [
    {}, {"tokens_per_second": None}, {"tokens_per_second": "3.0"},
    {"tokens_per_second": -1.0}, {"tokens_per_second": True},
    {"tokens_per_second": float("nan")}, {"tokens_per_second": "inf"},
])
def test_throughput_interruption_restarts_full_patience(interruption):
    mon = AlarmMonitor(tps_patience=3)
    _warm_throughput(mon)
    for step in (21, 22):
        assert mon.step(step, tokens_per_second=75.0) == []
    # Non-finite interruptions may still emit their existing stop event.
    assert all(a["rule"] != "throughput_drop" for a in mon.step(23, **interruption))
    for step in (24, 25):
        assert mon.step(step, tokens_per_second=75.0) == []
    out = mon.step(26, tokens_per_second=75.0)
    assert len(out) == 1 and out[0]["rule"] == "throughput_drop"


@pytest.mark.parametrize("next_step", [24, 22, 10])
def test_throughput_step_discontinuity_resets_streak(next_step):
    mon = AlarmMonitor(tps_patience=3)
    _warm_throughput(mon)
    for step in (21, 22):
        assert mon.step(step, tokens_per_second=75.0) == []
    assert mon.step(next_step, tokens_per_second=75.0) == []
    assert mon.step(next_step + 1, tokens_per_second=75.0) == []
    assert mon.step(next_step + 2, tokens_per_second=75.0)[0]["rule"] == "throughput_drop"


BAD_LOAD = [0.7, 0.3, 0.0, 0.0]


@pytest.mark.parametrize("interruption", [
    {}, {"expert_load": None}, {"expert_load": []},
    {"expert_load": ["bad"]}, {"expert_load": [-1, 1, 0, 0]},
    {"expert_load": [float("nan"), 0, 0, 0]},
    {"expert_load": {"other": [0.25] * 4}},
])
def test_moe_interruption_restarts_full_patience(interruption):
    mon = AlarmMonitor(moe_patience=3)
    for step in (0, 1):
        assert mon.step(step, expert_load={"layer": BAD_LOAD}) == []
    assert all(a["rule"] != "moe_routing" for a in mon.step(2, **interruption))
    for step in (3, 4):
        assert mon.step(step, expert_load={"layer": BAD_LOAD}) == []
    out = mon.step(5, expert_load={"layer": BAD_LOAD})
    assert len(out) == 1 and out[0]["rule"] == "moe_routing"


def test_moe_missing_layer_resets_only_its_streak():
    mon = AlarmMonitor(moe_patience=3)
    for step in (0, 1):
        assert mon.step(step, expert_load={"a": BAD_LOAD, "b": BAD_LOAD}) == []
    out = mon.step(2, expert_load={"b": BAD_LOAD})
    assert len(out) == 1 and out[0]["layer"] == "b"
    for step in (3, 4):
        assert mon.step(step, expert_load={"a": BAD_LOAD, "b": BAD_LOAD}) == []
    out = mon.step(5, expert_load={"a": BAD_LOAD, "b": BAD_LOAD})
    assert len(out) == 1 and out[0]["layer"] == "a"


def _check_row(mon, step, **metrics):
    out = []
    for name, value in metrics.items():
        out.extend(mon.check(step, name, value))
    return out


def test_check_per_metric_keeps_throughput_and_moe_streaks():
    mon = AlarmMonitor(moe_patience=110)
    fired = []
    for step in range(200):
        fired += _check_row(mon, step, loss_ntp=3.0, tokens_per_second=40000.0)
    for step in range(200, 310):
        fired += _check_row(mon, step, loss_ntp=3.0, tokens_per_second=20000.0, expert_load=BAD_LOAD)
    assert [(a["rule"], a["step"]) for a in fired] == [("throughput_drop", 299), ("moe_routing", 309)]


def test_check_missing_step_for_a_metric_restarts_its_streak():
    mon = AlarmMonitor(tps_patience=3)
    _warm_throughput(mon)
    for step in (21, 22):
        assert _check_row(mon, step, loss_ntp=3.0, tokens_per_second=75.0) == []
    assert _check_row(mon, 23, loss_ntp=3.0) == []  # no throughput reported at step 23
    for step in (24, 25):
        assert _check_row(mon, step, loss_ntp=3.0, tokens_per_second=75.0) == []
    assert _check_row(mon, 26, tokens_per_second=75.0)[0]["rule"] == "throughput_drop"


def test_step_gap_resets_both_throughput_and_moe():
    mon = AlarmMonitor(tps_patience=3, moe_patience=3)
    _warm_throughput(mon)
    for step in (21, 22, 24, 25):
        assert mon.step(step, tokens_per_second=75.0, expert_load=BAD_LOAD) == []
    out = mon.step(26, tokens_per_second=75.0, expert_load=BAD_LOAD)
    assert {a["rule"] for a in out} == {"throughput_drop", "moe_routing"}


def test_static_bound_latches_and_rearms():
    mon = AlarmMonitor(bounds={"docs_dropped": (None, 10.0), "gpu_temp_c": (10.0, 85.0)})
    assert mon.step(0, docs_dropped=5.0, gpu_temp_c=65.0) == []
    # Crossing above hi fires once and latches across subsequent cumulative increases.
    a1 = mon.step(1, docs_dropped=11.0, gpu_temp_c=65.0)
    assert len(a1) == 1 and a1[0]["rule"] == "static_bound" and a1[0]["metric"] == "docs_dropped"
    assert mon.step(2, docs_dropped=15.0, gpu_temp_c=65.0) == []
    # Crossing below lo on gpu_temp_c fires once, then re-arms after returning in-bounds.
    a2 = mon.step(3, docs_dropped=15.0, gpu_temp_c=5.0)
    assert len(a2) == 1 and a2[0]["rule"] == "static_bound" and a2[0]["metric"] == "gpu_temp_c"
    assert mon.step(4, docs_dropped=15.0, gpu_temp_c=4.0) == []
    assert mon.step(5, docs_dropped=15.0, gpu_temp_c=60.0) == []
    a3 = mon.step(6, docs_dropped=15.0, gpu_temp_c=90.0)
    assert len(a3) == 1 and a3[0]["rule"] == "static_bound" and a3[0]["metric"] == "gpu_temp_c"

