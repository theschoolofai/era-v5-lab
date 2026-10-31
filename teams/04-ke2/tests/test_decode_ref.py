"""Reference decoder: encode token IDs with the forward codec, decode them, and check every ID comes back.

Simple and slow on purpose. The real-tokenizer tests use the session tables from conftest.py and
are skipped without the tokenizer; the synthetic tests always run.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

import decode_ref as dr
from ke2.codec import encode_f64, encode_ids
from ke2.config import POS_DIMS
from ke2.tables import ByteTable
from ke2.tokenizer import U_FFFD

SAMPLE = 4096
SCRIPT = Path(__file__).resolve().parents[1] / "src" / "decode_ref.py"


def sample_ids(table, special_ids, n=SAMPLE, seed=0):
    return dr.sample_token_ids(table.vocab_size, special_ids, n=n, seed=seed)


@pytest.fixture(scope="module")
def code_tables(tables):
    return {key: dr.CodeTable.from_byte_table(t) for key, t in tables.items()}


# --------------------------------------------------------------------------- #
# Real tokenizer
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("P", POS_DIMS)
def test_raw_table_round_trip_recovers_every_id(tables, code_tables, tb, P):
    table, ct = tables["raw", P], code_tables["raw", P]
    ids = sample_ids(table, tb.special_ids)
    assert len(set(ids.tolist())) == SAMPLE
    result = dr.decode(encode_ids(ids, table), ct)
    assert np.array_equal(result.token_ids, ids)
    assert result.token_bytes == [table.row(int(i)) for i in ids]
    assert (result.margins > 0).all()
    assert (result.scores > 1 - 1e-9).all()


def test_same_input_gives_same_output_and_hash(tables, code_tables, tb):
    table, ct = tables["raw", 32], code_tables["raw", 32]
    vectors = encode_ids(sample_ids(table, tb.special_ids, n=512, seed=1), table)
    first, again, one_by_one = dr.decode(vectors, ct), dr.decode(vectors, ct), dr.decode(vectors, ct, chunk_rows=1)
    assert first.sha256() == again.sha256() == one_by_one.sha256()
    assert np.array_equal(first.margins, one_by_one.margins)


def test_fresh_process_gives_the_same_hash(tmp_path, tables, code_tables, tb):
    table = tables["raw", 32]
    vectors = encode_ids(sample_ids(table, tb.special_ids, n=256, seed=2), table).numpy()
    table_file, vectors_file = tmp_path / "raw_table_P32.npz", tmp_path / "codes.npy"
    table.save(table_file)
    np.save(vectors_file, vectors)
    run = subprocess.run(
        [sys.executable, str(SCRIPT), "--table", str(table_file), "--vectors", str(vectors_file)],
        capture_output=True, text=True, check=True,
    )  # fmt: skip
    assert run.stdout.strip() == dr.decode(vectors, code_tables["raw", 32]).sha256()


@pytest.mark.parametrize("P", POS_DIMS)
def test_factorized_scores_equal_dense_scores(tables, code_tables, P):
    table, ct = tables["raw", P], code_tables["raw", P]
    rng = np.random.default_rng(3)
    subset = rng.choice(table.vocab_size, 64, replace=False)
    queries = ct.codes(subset[:8]) + rng.normal(scale=0.1, size=(8, ct.dim))
    dense = queries @ ct.codes(subset).T
    np.testing.assert_allclose(ct.dot_scores(queries)[:, subset], dense, rtol=1e-12, atol=1e-9)


@pytest.mark.parametrize("P", POS_DIMS)
def test_float64_reference_matches_the_upstream_codec(tables, P):
    table = tables["raw", P]
    ids = np.arange(0, table.vocab_size, 997)
    upstream = encode_ids(ids, table).double().numpy()
    reference = encode_f64(table.bytes[ids], table.lengths[ids], P)
    np.testing.assert_allclose(reference, upstream, rtol=0, atol=1e-5)


def test_decode_table_collisions_tie_to_the_lowest_id(tables, code_tables):
    table = tables["decode", 32]
    group = np.array([i for i in range(table.vocab_size) if table.row(i) == U_FFFD])
    assert len(group) > 1
    result = dr.decode(encode_ids(group[-3:], table), code_tables["decode", 32])
    assert (result.token_ids == group.min()).all()
    assert (result.margins == 0).all()
    assert result.token_bytes == [U_FFFD] * 3


# --------------------------------------------------------------------------- #
# Synthetic table (no tokenizer needed)
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def tiny():
    """200 distinct tokens of 1..8 bytes plus one empty token (ID 5), P = 8."""
    rng = np.random.default_rng(0)
    P, rows = 8, []
    while len(rows) < 200:
        r = rng.integers(0, 256, rng.integers(2, P + 1)).astype(np.uint8).tobytes()
        if r not in rows:
            rows.append(r)
    rows.insert(5, b"")
    buf = np.zeros((len(rows), P), np.uint8)
    for i, r in enumerate(rows):
        buf[i, : len(r)] = np.frombuffer(r, np.uint8)
    lengths = np.array([len(r) for r in rows], np.int16)
    table = ByteTable("raw", P, buf, lengths, 0, 0, 1, "0" * 64)
    return table, dr.CodeTable.from_byte_table(table)


def test_tiny_round_trip_in_float32_bfloat16_and_float64(tiny):
    table, ct = tiny
    ids = np.array([i for i in range(table.vocab_size) if i != 5])
    codes = encode_ids(ids, table)
    for vectors in (codes, codes.to(torch.bfloat16), codes.double().numpy()):
        result = dr.decode(vectors, ct)
        assert np.array_equal(result.token_ids, ids)
        assert (result.margins > 0).all()


def test_empty_token_code_scores_zero(tiny):
    _, ct = tiny
    scores = ct.cosine_scores(ct.codes([0, 1]))
    assert (scores[:, 5] == 0).all()


def test_bad_inputs_are_refused(tiny):
    _, ct = tiny
    good = ct.codes([0, 1])
    with pytest.raises(dr.DecodeInputError, match="shape"):
        dr.decode(good[:, :-1], ct)
    with pytest.raises(dr.DecodeInputError, match="NaN"):
        dr.decode(np.where(np.arange(ct.dim) == 3, np.nan, good), ct)
    with pytest.raises(dr.DecodeInputError, match="zero vector"):
        dr.decode(np.zeros((1, ct.dim)), ct)
    with pytest.raises(ValueError, match="chunk_rows"):
        dr.decode(good, ct, chunk_rows=0)


def test_sample_ids_are_distinct_and_start_with_the_edges():
    ids = dr.sample_token_ids(1000, {36, 900}, n=50, seed=4)
    assert len(set(ids.tolist())) == 50
    assert ids[:6].tolist() == [0, 77, 173, 999, 36, 900]
    with pytest.raises(ValueError):
        dr.sample_token_ids(10, n=11)


def test_single_vector_is_accepted(tiny):
    _, ct = tiny
    result = dr.decode(ct.codes([7])[0], ct)
    assert result.token_ids.tolist() == [7] and len(result) == 1
