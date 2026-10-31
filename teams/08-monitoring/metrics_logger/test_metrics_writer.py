import json

import numpy as np
import pytest
import torch

from metrics_writer import MetricsWriter


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "metrics.jsonl")


def rows(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def test_flush_at_step_10(path):
    w = MetricsWriter(path)
    for step in range(1, 10):
        w.write(step, loss_ntp=1.0)
    assert rows(path) == []
    w.write(10, loss_ntp=1.0)
    assert [r["step"] for r in rows(path)] == list(range(1, 11))
    w.close()


@pytest.mark.parametrize("bad, stored", [
    (float("nan"), "nan"), (float("inf"), "inf"), (float("-inf"), "-inf")])
def test_nonfinite_flushes_at_once(path, bad, stored):
    w = MetricsWriter(path)
    w.write(1, loss_ntp=1.0)
    w.write(2, loss_ntp=bad)
    assert [r["loss_ntp"] for r in rows(path)] == [1.0, stored]
    w.close()


def test_alias_gpu_alloc_gb(path):
    with MetricsWriter(path) as w:
        w.write(1, gpu_alloc_gb=1.5)
    row = rows(path)[0]
    assert row["gpu_alloc_gib"] == 1.5
    assert "gpu_alloc_gb" not in row


def test_unknown_name_skipped_with_one_warning(path, capsys):
    with MetricsWriter(path) as w:
        w.write(1, gradient_nrom=1.0, loss_ntp=1.0)
        w.write(2, gradient_nrom=2.0)
    assert all("gradient_nrom" not in r for r in rows(path))
    assert rows(path)[0]["loss_ntp"] == 1.0
    assert capsys.readouterr().err.count("gradient_nrom") == 1


def test_numpy_scalar(path):
    with MetricsWriter(path) as w:
        w.write(1, lr=np.float32(0.5), loss_ntp=np.float32("nan"))
    row = rows(path)[0]
    assert row["lr"] == 0.5
    assert row["loss_ntp"] == "nan"


def test_torch_scalar(path):
    with MetricsWriter(path) as w:
        w.write(1, gradient_norm=torch.tensor(2.5), loss_mtp=torch.tensor(float("inf")))
    row = rows(path)[0]
    assert row["gradient_norm"] == 2.5
    assert row["loss_mtp"] == "inf"


def test_list_of_tensors_and_arrays(path):
    with MetricsWriter(path) as w:
        w.write(1, expert_load=np.array([0.25, 0.75]), update_weight_ratio=[torch.tensor(1.0)])
    row = rows(path)[0]
    assert row["expert_load"] == [0.25, 0.75]
    assert row["update_weight_ratio"] == [1.0]


def test_close_twice(path):
    w = MetricsWriter(path)
    w.write(1, loss_ntp=1.0)
    w.close()
    w.close()
    assert len(rows(path)) == 1
