"""Live JSONL event record contract."""
import json
import io
import threading
from types import SimpleNamespace

import pytest
import torch

from perfkit.events import JsonlWriter, StepTimingStreamer, gpu_sample_record
from perfkit.metrics import GpuSampler


def test_jsonl_writer_flushes_one_json_record_per_line(tmp_path):
    path = tmp_path / "run.jsonl"
    with JsonlWriter(path) as writer:
        writer.write({"event": "first", "step": 1})
        assert path.read_text(encoding="utf-8").splitlines() == ['{"event":"first","step":1}']
        writer.write({"event": "second", "step": 2})

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["step"] for row in rows] == [1, 2]
    with pytest.raises(FileExistsError):
        with JsonlWriter(path):
            pass


def test_gpu_sample_record_contains_g8_identity_and_raw_mib_metrics():
    record = gpu_sample_record(
        run_id="run-123", node_id="node-2",
        gpu={"name": "Example GPU", "index": 1, "uuid": "GPU-example", "pci_bus_id": "0000:02:00.0"},
        metrics={"gpu_util_pct": 95, "mem_used_mib": 1200}, slowdown_flags=["SwPowerCap"],
        step=41, timestamp="2026-10-30T12:00:00.000Z",
    )
    assert record == {
        "schema_version": 1, "event": "gpu_sample", "timestamp": "2026-10-30T12:00:00.000Z",
        "run_id": "run-123", "node_id": "node-2",
        "gpu": {"name": "Example GPU", "index": 1, "uuid": "GPU-example", "pci_bus_id": "0000:02:00.0"},
        "step": 41, "metrics": {"gpu_util_pct": 95, "mem_used_mib": 1200},
        "slowdown_flags": ["SwPowerCap"],
    }


def test_gpu_sampler_stream_callback_receives_sample_and_current_step():
    lines = "1, Example GPU, GPU-example, 00000000:02:00.0, 95, 40, 1200, 1410, 1600, 300.0, 65, 0x0000000000000004\n"
    samples = []
    sampler = GpuSampler(torch.device("cpu"), on_sample=lambda row, step: samples.append((row, step)))
    sampler.reason = "clocks_event_reasons.active"
    sampler._proc = SimpleNamespace(stdout=io.StringIO(lines))
    sampler.set_step(12)

    sampler._read_samples()

    assert len(samples) == 1 and samples[0][1] == 12
    assert samples[0][0]["memory.used"] == 1200
    assert samples[0][0]["uuid"] == "GPU-example"
    assert samples[0][0][sampler.reason] == 4


def test_gpu_sampler_streams_distinct_rows_for_multiple_gpus():
    lines = (
        "0, GPU A, GPU-a, 00000000:01:00.0, 95, 40, 1200, 1410, 1600, 300.0, 65, 0x0\n"
        "1, GPU B, GPU-b, 00000000:02:00.0, 75, 30, 800, 1200, 1400, 200.0, 55, 0x0\n"
    )
    samples = []
    sampler = GpuSampler(torch.device("cpu"), on_sample=lambda row, step: samples.append((row, step)))
    sampler.reason = "clocks_event_reasons.active"
    sampler._proc = SimpleNamespace(stdout=io.StringIO(lines))
    sampler.set_step(8)

    sampler._read_samples()

    assert [row["uuid"] for row, _ in samples] == ["GPU-a", "GPU-b"]
    assert [step for _, step in samples] == [8, 8]


def test_step_timing_streamer_reports_data_and_raw_step_ms_off_thread_without_sync(tmp_path):
    path = tmp_path / "steps.jsonl"
    caller_thread = threading.get_ident()

    class StartEvent:
        elapsed_thread = None

        def elapsed_time(self, end):
            self.elapsed_thread = threading.get_ident()
            assert end.query_thread == self.elapsed_thread
            return 12.34567

    class EndEvent:
        query_thread = None

        def query(self):
            self.query_thread = threading.get_ident()
            return True

        def synchronize(self):
            raise AssertionError("step event reporting must not synchronize CUDA")

    start, end = StartEvent(), EndEvent()
    with JsonlWriter(path) as writer:
        with StepTimingStreamer(writer, run_id="run-1", node_id="node-a", rank=3, local_rank=1) as stream:
            stream.submit(4, 0.45678, "event", (start, end))

    row = json.loads(path.read_text(encoding="utf-8"))
    assert row["event"] == "step_timing"
    assert (row["run_id"], row["node_id"], row["rank"], row["local_rank"], row["step"]) == (
        "run-1", "node-a", 3, 1, 4)
    assert row["data_ms"] == 0.4568 and row["raw_step_ms"] == 12.3457
    assert start.elapsed_thread == end.query_thread != caller_thread
