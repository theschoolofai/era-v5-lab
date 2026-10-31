"""Table construction: shapes, the decode-table bug, and the raw-table fix."""

import numpy as np
import pytest

import build_tables as bt

V = 131_072


@pytest.mark.parametrize("P", bt.POS_DIMS)
@pytest.mark.parametrize("kind", ["decode", "raw"])
def test_shapes_and_dtypes(tables, kind, P):
    t = tables[kind, P]
    assert t.bytes.shape == (V, P) and t.bytes.dtype == np.uint8
    assert t.lengths.shape == (V,) and t.lengths.dtype == np.int16
    assert int(t.lengths.min()) >= 0 and int(t.lengths.max()) <= P
    # padding beyond the length is zero
    for i in (0, 77, 66526, V - 1):
        assert not t.bytes[i, int(t.lengths[i]) :].any()


def test_no_truncation_on_this_tokenizer(tables, tb):
    assert max(len(bt.raw_bytes_for_id(tb, i)) for i in range(V)) == 32
    for t in tables.values():
        assert t.n_truncated == 0


def test_bytelevel_alphabet_is_bijection():
    assert len(bt.BYTE_TO_UNI) == 256 and len(bt.UNI_TO_BYTE) == 256
    for b in range(256):
        assert bt.UNI_TO_BYTE[bt.BYTE_TO_UNI[b]] == b
    assert bt.piece_to_raw_bytes("Ġhello") == b" hello"
    assert bt.piece_to_raw_bytes("Ð") == b"\xd0"


def test_decode_table_has_the_known_issue(dec32, raw32):
    """Partial-character tokens become U+FFFD and share one row."""
    assert raw32.row(77) == b"\xd0" and raw32.row(173) == b"\xd1"
    assert dec32.row(77) == dec32.row(173) == bt.U_FFFD
    assert dec32.n_fffd_rows == 1326
    corrupted = [i for i in range(V) if dec32.row(i) != raw32.row(i)]
    assert len(corrupted) == 1306
    assert all(bt.U_FFFD in dec32.row(i) for i in corrupted)
    assert len({dec32.row(i) for i in range(V)}) == V - 1141


def test_raw_table_fixes_it(tables):
    for P in bt.POS_DIMS:
        t = tables["raw", P]
        rows = {t.row(i) for i in range(V)}
        assert len(rows) == V, "raw table must be injective"
        # only genuine U+FFFD tokens contain EF BF BD
        assert t.n_fffd_rows == 20


def test_raw_rows_are_valid_or_partial_utf8_but_never_replacement(tb, raw32):
    """A raw row that is not valid UTF-8 must be an *incomplete* sequence, not garbage."""
    n_invalid = 0
    for i in range(V):
        r = raw32.row(i)
        try:
            r.decode("utf-8")
        except UnicodeDecodeError:
            n_invalid += 1
            assert bt.U_FFFD not in r
    assert n_invalid == 1306


def test_upstream_build_byte_buffer_matches_expected_table(tb, dec32, raw32):
    """Upstream unpatched == our decode table (the bug); upstream with
    patches/0001-tokenizer-utils-bytelevel-exact-bytes.patch == our raw table (the fix)."""
    transformers = pytest.importorskip("transformers")
    import kronecker_embeddings.tokenizer_utils as tu

    hf = transformers.PreTrainedTokenizerFast(tokenizer_file=str(tb.path))
    byte_buf, len_buf = tu.build_byte_buffer(hf, pos_dim=32)
    assert byte_buf.shape == (V, 32)
    expected = raw32 if hasattr(tu, "bytelevel_inverse") else dec32
    assert np.array_equal(byte_buf.numpy(), expected.bytes)
    assert np.array_equal(len_buf.numpy(), expected.lengths)


def test_p64_is_p32_zero_padded(tables):
    r32, r64 = tables["raw", 32], tables["raw", 64]
    assert np.array_equal(r64.bytes[:, :32], r32.bytes)
    assert not r64.bytes[:, 32:].any()
    assert np.array_equal(r64.lengths, r32.lengths)


def test_special_tokens_are_literal_content(tb, raw32, dec32):
    for tid in (36, 130725, 130726, 130727):
        content = tb.added[tid]["content"].encode()
        assert raw32.row(tid) == content == dec32.row(tid)
    assert raw32.row(36) == b"<|end_of_text|>"


def test_save_load_roundtrip(tmp_path, tb, raw32):
    p = tmp_path / "raw_table_P32.npz"
    raw32.save(p)
    t = bt.ByteTable.load(p, tokenizer=tb)
    assert t.kind == "raw" and t.pos_dim == 32
    assert np.array_equal(t.bytes, raw32.bytes) and np.array_equal(t.lengths, raw32.lengths)
    assert t.sha256() == raw32.sha256()
