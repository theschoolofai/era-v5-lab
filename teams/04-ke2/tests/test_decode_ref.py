"""Reference inverse: IDs/bytes, scoring, collision ties and deterministic hashes."""

import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "src/decode_ref.py"
spec = importlib.util.spec_from_file_location("ke2_decode_ref", SCRIPT)
ref = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ref
spec.loader.exec_module(ref)


def test_scores_margins_and_raw_byte_fragments():
    """Check hand-calculated distances/margins and preservation of raw fragments."""
    table = ref.CodeTable([[0, 0], [2, 0], [0, 3]], [b"\xd0", b"\xd1", b"\x00"], [77, 173, 9])
    results = ref.decode_ref([[0, 0], [1.8, 0]], table)
    assert results[0] == ref.DecodeResult(77, b"\xd0", 0.0, 4.0, 4.0)
    assert results[1].token_id == 173 and results[1].raw_bytes == b"\xd1"
    assert results[1].best_distance == pytest.approx(0.04)
    assert results[1].margin == pytest.approx(3.2)
    assert table.codes.dtype == np.float64


def test_ties_choose_smallest_id_and_return_zero_margin():
    """Check that exact ties use the smallest ID, independently of table order."""
    table = ref.CodeTable([[0, 0], [0, 0], [2, 0]], [b"A", b"B", b"C"], [19, 3, 1])
    result = ref.decode_ref([[0, 0]], table)[0]
    assert result.token_id == 3 and result.raw_bytes == b"B" and result.margin == 0
    assert ref.decode_ref([[1, 0]], table)[0].token_id == 1


def test_repeated_hash_and_candidate_chunk_sizes_agree():
    """Check stable results across chunk sizes and hashes sensitive to order/margins."""
    rng = np.random.default_rng(7)
    codes = rng.normal(size=(19, 31))
    table = ref.CodeTable(codes, [bytes([i]) for i in range(19)])
    queries = codes[[17, 0, 5]] + 0.001
    first = ref.decode_ref(queries, table, chunk_size=1)
    for size in (2, 7, 256):
        other = ref.decode_ref(queries, table, chunk_size=size)
        assert other == first and ref.results_sha256(other) == ref.results_sha256(first)
    assert ref.results_sha256(first) != ref.results_sha256(list(reversed(first)))
    changed = [ref.DecodeResult(r.token_id, r.raw_bytes, r.best_distance, r.second_distance, r.margin + 1) for r in first]
    assert ref.results_sha256(changed) != ref.results_sha256(first)


def test_validation_and_empty_batch():
    """Check malformed input rejection and the valid empty-query-batch case."""
    with pytest.raises(ValueError):
        ref.CodeTable([[0]], [b"a"])
    with pytest.raises(ValueError):
        ref.CodeTable([[0], [1]], [b"a", b"b"], [1, 1])
    with pytest.raises(ValueError):
        ref.CodeTable([[0], [np.nan]], [b"a", b"b"])
    table = ref.CodeTable([[0], [1]], [b"a", b"b"])
    for queries in ([[float("inf")]], [[1, 2]], [1]):
        with pytest.raises(ValueError):
            ref.decode_ref(queries, table)
    assert ref.decode_ref(np.empty((0, 1)), table) == []
    with pytest.raises(ValueError, match="real-valued"):
        ref.decode_ref(np.array([[1j]]), table)
    for size in (True, 0, -1, 1.5):
        with pytest.raises(ValueError, match="chunk_size"):
            ref.decode_ref([[0]], table, chunk_size=size)


def test_distance_reduction_overflow_never_returns_infinite_scores_or_nan_margin():
    """Reject overflowing sums, including when only the runner-up overflows."""
    for codes in ([[1e154, 1e154], [1.1e154, 1.1e154]], [[0, 0], [1e154, 1e154]]):
        table = ref.CodeTable(codes, [b"a", b"b"])
        with pytest.raises(FloatingPointError):
            ref.decode_ref([[0, 0]], table)


def test_code_table_owns_its_inputs_and_rejects_invalid_ids():
    """Check copied input ownership and integer/unique/nonnegative ID requirements."""
    codes = np.array([[0.0], [2.0]])
    ids = np.array([3, 9])
    table = ref.CodeTable(codes, [b"a", b"b"], ids)
    codes[0, 0] = 100
    ids[0] = 100
    assert ref.decode_ref([[0]], table)[0].token_id == 3
    for bad in ([0.0, 1.0], [-1, 0], [True, False], [0]):
        with pytest.raises(ValueError):
            ref.CodeTable([[0], [1]], [b"a", b"b"], bad)


def test_noisy_query_and_exact_score_agree_with_independent_oracle():
    """Compare noisy-query results against a separately calculated Python oracle."""
    rng = np.random.default_rng(11)
    codes = rng.normal(size=(13, 5))
    ids = rng.permutation(np.arange(13)) + 20
    queries = codes[[2, 7, 1]] + rng.normal(scale=0.01, size=(3, 5))
    table = ref.CodeTable(codes, [bytes([i]) for i in range(13)], ids)
    for query, result in zip(queries, ref.decode_ref(queries, table)):
        scored = sorted((sum((float(x) - float(y)) ** 2 for x, y in zip(row, query)), int(tid), i)
                        for i, (row, tid) in enumerate(zip(codes, ids)))
        assert result.token_id == scored[0][1]
        assert result.raw_bytes == bytes([scored[0][2]])
        assert result.best_distance == pytest.approx(scored[0][0], rel=1e-14)
        assert result.second_distance == pytest.approx(scored[1][0], rel=1e-14)
        assert result.margin == pytest.approx(scored[1][0] - scored[0][0], rel=1e-14)


def _ke2_codec():
    """Load the authorized local codec class, or skip its integration tests.

    Takes no arguments. KE2_SRC supplies the external src-directory path.
    Returns the KroneckerCodec class after checking its import location.
    """
    source = os.environ.get("KE2_SRC")
    if not source:
        pytest.skip("set KE2_SRC to the authorized local KE2 src directory")
    sys.path.insert(0, str(Path(source).resolve()))
    import kronecker_v2.codec as module
    assert Path(module.__file__).resolve().parent == Path(source).resolve() / "kronecker_v2"
    return module.KroneckerCodec


def test_ke2_float64_roundtrip_three_thousand_ids():
    """Check 3,000 native-code ID/byte round trips using the local KE2 dependency."""
    codec = _ke2_codec()(d_c=8, L_max=8)
    raw = [i.to_bytes(4, "little") for i in range(3000)]
    ids = np.arange(3000, dtype=np.int64)[::-1] + 17
    table = ref.CodeTable.from_codec(codec, raw, ids)
    queries = codec.encode(raw[::-1])
    assert queries.dtype == np.float64
    results = ref.decode_ref(queries, table)
    assert [r.token_id for r in results] == ids[::-1].tolist()
    assert [r.raw_bytes for r in results] == raw[::-1]
    assert all(r.best_distance == 0 and r.margin > 0 for r in results)
    assert codec.decode(queries) == raw[::-1]


def test_ke2_production_width_raw_fragments_and_truncation_collisions():
    """Check realistic widths, raw-byte edge cases and explicit overflow ambiguity."""
    codec_type = _ke2_codec()
    raw = [b"", b"\x00", b"\x00\x00", b"\xd0", b"\xd1", b"\x95", "क".encode(), "🙂".encode()]
    ids = [99, 18, 7, 77, 173, 62, 12, 4]
    for P in (32, 64):
        codec = codec_type(d_c=64, L_max=P)
        table = ref.CodeTable.from_codec(codec, raw, ids)
        results = ref.decode_ref(codec.encode(raw), table)
        assert [r.token_id for r in results] == ids
        assert [r.raw_bytes for r in results] == raw
        assert all(r.margin > 0 for r in results)
        long = [b"x" * P + b"A", b"x" * P + b"B"]
        collided = ref.CodeTable.from_codec(codec, long, [8, 2])
        result = ref.decode_ref(codec.encode(long[:1]), collided)[0]
        assert result.token_id == 2 and result.raw_bytes == long[1] and result.margin == 0


def test_encode_decode_three_thousand_structured_codes():
    """Check 3,000 distinct structured codes without requiring the KE2 dependency."""
    # Small independent byte-position encoder: 4 byte values x 6 positions.
    # 3,000 distinct sequences give 3,000 distinct forward code vectors.
    sequences = [bytes((number // (4 ** p)) % 4 for p in range(6)) for number in range(3000)]
    codes = np.zeros((3000, 24), dtype=np.float64)
    for i, data in enumerate(sequences):
        codes[i, np.array(list(data)) * 6 + np.arange(6)] = 1 / np.sqrt(6)
    codes = (codes - codes.mean(axis=1, keepdims=True)) / (codes.std(axis=1, ddof=1, keepdims=True) + 1e-6)
    ids = np.arange(3000, dtype=np.int64)[::-1]
    table = ref.CodeTable(codes, sequences, ids)
    results = ref.decode_ref(codes, table)
    assert [r.token_id for r in results] == ids.tolist()
    assert [r.raw_bytes for r in results] == sequences
    assert all(r.best_distance == 0 and r.margin > 0 for r in results)
