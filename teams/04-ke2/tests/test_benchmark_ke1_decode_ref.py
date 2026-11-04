"""Independent distance checks and a small real benchmark coordinator run."""

import json

import benchmark_ke1_decode_ref as benchmark
import numpy as np

from ke2.tables import ByteTable


def test_dense_baseline_distances_and_ties():
    """Verify hand-calculated distances, gaps and tie ordering across chunks."""
    codes = np.array([[0.0, 0.0], [2.0, 0.0], [0.0, 3.0]])
    queries = np.array([[1.8, 0.0], [1.0, 0.0]])
    for chunk in (1, 2, 256):
        rows, best, margins = benchmark.dense_distance_baseline(queries, codes, chunk)
        np.testing.assert_array_equal(rows, [1, 0])
        np.testing.assert_allclose(best, [0.04, 1.0])
        np.testing.assert_allclose(margins, [3.2, 0.0])


def test_comparison_uses_identical_inputs_and_records_both_methods(tmp_path):
    """Run separate CPU workers and verify input identity and result coverage."""
    buf = np.array([[97, 0, 0, 0], [98, 0, 0, 0], [97, 98, 0, 0], [99, 98, 97, 0]], dtype=np.uint8)
    lengths = np.array([1, 1, 2, 3], dtype=np.int16)
    table = ByteTable("raw", 4, buf, lengths, 0, 0, 0, benchmark.TOKENIZER_SHA256)
    table.save(tmp_path / "raw_table_P4.npz")
    output = tmp_path / "comparison.json"
    assert (
        benchmark.main(
            [
                "--tables",
                str(tmp_path),
                "--out",
                str(output),
                "--pos-dims",
                "4",
                "--candidates",
                "4",
                "--queries",
                "4",
                "--repeats",
                "2",
            ]
        )
        == 0
    )
    report = json.loads(output.read_text())
    a, b = report["measurements"]
    assert a["method"] == "cosine" and b["method"] == "dense_euclidean"
    assert a["candidate_ids_sha256"] == b["candidate_ids_sha256"]
    assert a["query_vectors_sha256"] == b["query_vectors_sha256"]
    assert a["query_token_ids"] == b["query_token_ids"]
    for result in (a, b):
        assert result["ids_and_stored_bytes_match"] and result["repeat_fingerprints_match"]
        assert len(result["decode_seconds"]) == 2
