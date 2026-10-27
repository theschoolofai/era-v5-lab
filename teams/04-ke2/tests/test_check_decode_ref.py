"""Source-table integrity and fresh-process reference-check runner."""

import importlib.util
import os
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "src/check_decode_ref.py"
spec = importlib.util.spec_from_file_location("check_decode_ref", SCRIPT)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def _source_table(path):
    """Write a five-row source-table fixture, including empty and fragment bytes.

    Parameters
    ----------
    path : pathlib.Path
        Temporary .npz destination supplied by the calling test.

    Returns
    -------
    tuple of (list of bytes, dict)
        Expected payloads and mutable artifact fields for corruption tests.
    """
    raw = [b"", b"a", b"\xd0", b"\xd1", b"\x00"]
    buf = np.zeros((len(raw), 8), dtype=np.uint8)
    lengths = np.array([len(r) for r in raw], dtype=np.int16)
    for i, payload in enumerate(raw):
        if payload:
            buf[i, :len(payload)] = np.frombuffer(payload, dtype=np.uint8)
    h = check.hashlib.sha256(b"ke2-table-v2|raw|8|")
    h.update(buf.tobytes())
    h.update(lengths.tobytes())
    fields = dict(format_version=2, kind="raw", pos_dim=8, bytes=buf, lengths=lengths,
                  tokenizer_sha256=check.TOKENIZER_SHA, table_sha256=h.hexdigest(), n_truncated=0)
    np.savez(path, **fields)
    return raw, fields


def test_source_integrity_and_three_run_validation(tmp_path):
    """Check artifact integrity and rejection of incomplete/disagreeing run reports.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest's isolated writable temporary-directory fixture.
    """
    path = tmp_path / "raw.npz"
    raw, fields = _source_table(path)
    assert check.load_raw_bytes(path, check.TOKENIZER_SHA)[0] == raw
    with pytest.raises(ValueError, match="identity"):
        check.load_raw_bytes(path, "wrong")
    fields["bytes"][1, 0] = 2
    np.savez(path, **fields)
    with pytest.raises(ValueError, match="content hash"):
        check.load_raw_bytes(path, check.TOKENIZER_SHA)
    check.verify_runs([{"hash": "same"}] * 3)
    for runs in ([{}, {}], [{"hash": "a"}, {"hash": "a"}, {"hash": "b"}]):
        with pytest.raises(ValueError):
            check.verify_runs(runs)


def test_three_fresh_ke2_processes(tmp_path):
    """Exercise the coordinator, worker CLI and output files with the local codec.

    Parameters
    ----------
    tmp_path : pathlib.Path
        Pytest's isolated directory for the synthetic input and generated results.
        KE2_SRC selects the external codec; the test skips when it is unset.
    """
    source = os.environ.get("KE2_SRC")
    if not source:
        pytest.skip("set KE2_SRC for the local KE2 integration runner")
    path = tmp_path / "raw.npz"
    _source_table(path)
    output = tmp_path / "results"
    assert check.main(["--raw-table", str(path), "--ke2-src", source,
                       "--sample-size", "5", "--out", str(output)]) == 0
    report = check.json.loads((output / "decode_ref_results.json").read_text())
    assert report["all_three_runs_identical"]
    assert len((output / "decode_ref_cpu_sha256.txt").read_text().splitlines()) == 7
    for run in report["runs"]:
        assert run["environment"]["dtype"] == "float64"
        assert all(t["ids_and_raw_bytes_match"] and t["native_inverse_agrees"] for t in run["tables"].values())
