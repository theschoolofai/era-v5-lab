"""Original KE1 CPU/MPS checks: portable helpers plus opt-in Apple GPU integration."""

import importlib.util
import os
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "src/determinism/codec_v1_cpu_mps.py"
spec = importlib.util.spec_from_file_location("codec_v1_cpu_mps", SCRIPT)
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)


def test_output_hash_includes_shape_and_preserves_batch_boundaries():
    a, b = cm.output_digest(32, 2), cm.output_digest(32, 2)
    a.update(b"abcd")
    b.update(b"ab")
    b.update(b"cd")
    assert a.hexdigest() == b.hexdigest()
    assert cm.output_digest(32, 2).hexdigest() != cm.output_digest(64, 2).hexdigest()
    assert cm.output_digest(32, 2).hexdigest() != cm.output_digest(32, 1).hexdigest()


def test_summary_separates_repeatability_cpu_agreement_and_strict_support():
    def run(mps_hash="mps"):
        entry = {
            "table_sha256": "table",
            "rows": 2,
            "vocabulary_size": 3,
            "first_id": 0,
            "last_id": 1,
            "batch_size": 2,
            "mps_sha256": mps_hash,
            "cpu_sha256": "cpu",
            "values_outside_tolerance": 0,
            "max_absolute_difference": 1e-6,
            "strict_probe": {"status": "rejected_no_deterministic_implementation"},
        }
        return {"environment": {"device": "mps"}, "tables": {"32": entry.copy(), "64": entry.copy()}}

    summary = cm.summarize([run(), run(), run()])["32"]
    assert summary["mps_three_hashes_match"] and summary["cpu_mps_all_close"]
    assert not summary["cpu_mps_bitwise_equal"] and not summary["full_vocabulary"]
    assert not cm.summarize([run(), run(), run("different")])["32"]["mps_three_hashes_match"]
    changed = run()
    changed["tables"]["32"]["values_outside_tolerance"] = 1
    assert not cm.summarize([run(), run(), changed])["32"]["cpu_mps_all_close"]
    changed = run()
    changed["tables"]["32"]["table_sha256"] = "changed"
    with pytest.raises(ValueError, match="coverage"):
        cm.summarize([run(), run(), changed])


def test_table_validation_detects_corruption_and_wrong_tokenizer(tmp_path):
    np = pytest.importorskip("numpy")
    buf = np.zeros((2, 32), dtype=np.uint8)
    lengths = np.array([1, 2], dtype=np.int16)
    h = cm.hashlib.sha256(b"ke2-table-v2|raw|32|")
    h.update(buf.tobytes())
    h.update(lengths.tobytes())
    fields = dict(
        format_version=2,
        kind="raw",
        pos_dim=32,
        tokenizer_sha256="artifact",
        bytes=buf,
        lengths=lengths,
        table_sha256=h.hexdigest(),
    )
    path = tmp_path / "table.npz"
    np.savez(path, **fields)
    assert cm.read_table(path, 32, "artifact")[2] == h.hexdigest()
    with pytest.raises(ValueError, match="different tokenizer"):
        cm.read_table(path, 32, "other")
    buf[0, 0] = 1
    np.savez(path, **fields)
    with pytest.raises(ValueError, match="hash mismatch"):
        cm.read_table(path, 32, "artifact")


def test_mps_integration_opt_in(tmp_path):
    if os.environ.get("KE2_RUN_V1_MPS_TESTS") != "1":
        pytest.skip("optional GPU check: set KE2_RUN_V1_MPS_TESTS=1, KE2_V1_MPS_TABLES and KE2_V1_CODEC_SRC")
    args = [
        "--tables",
        os.environ["KE2_V1_MPS_TABLES"],
        "--codec-src",
        os.environ["KE2_V1_CODEC_SRC"],
        "--limit",
        "16",
        "--out",
        str(tmp_path),
    ]
    assert cm.main(args) == 0
    report = cm.json.loads((tmp_path / "codec_v1_cpu_mps_results.json").read_text())
    for summary in report["summary"].values():
        assert summary["rows_per_run"] == 16 and summary["mps_three_hashes_match"]
        assert summary["cpu_mps_all_close"]
