"""Regression checks for the Brahmic source tokenizer and token-shard contract."""
import json
import os

import numpy as np
import pytest
import torch

from dataio.loader import Loader, open_shard
from dataio.prepare_fineweb import write_shard
from dataio.tokenizer import BrahmicTokenizer, REVISION, SHA256, VOCAB_SIZE

fixture = pytest.fixture


@fixture(scope="module")
def tokenizer():
    return BrahmicTokenizer(os.environ.get("BRAHMIC_TOKENIZER_PATH"))


def test_source_vocabulary_and_byte_table(tokenizer):
    rows = tokenizer.raw_token_bytes()
    assert len(rows) == VOCAB_SIZE == 131072
    assert min(map(len, rows)) == 1
    assert max(map(len, rows)) == 32
    table, lens = tokenizer.token_bytes()
    assert table.shape == (VOCAB_SIZE, 32)
    for idx, raw in enumerate(rows):
        assert bytes(table[idx, :lens[idx]].tolist()) == raw
    vocab = tokenizer.spec["model"]["vocab"]
    assert rows[vocab["<|end_of_text|>"]] == b"<|end_of_text|>"
    # Retain incomplete UTF-8 bytes instead of decoding them to replacement chars.
    assert b"\x80" in rows
    assert tokenizer.encode("\u092d\u093e\u0930\u0924 \u090f\u0915 \u0926\u0947\u0936 \u0939\u0948") == [66526, 2420, 13092, 732]
    with pytest.raises(ValueError, match="byte positions"):
        tokenizer.token_bytes(31)


def test_untrusted_artifact_rejected(tmp_path):
    path = tmp_path / "tokenizer.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        BrahmicTokenizer(path)


def test_uint32_and_synthetic_use_real_vocabulary(tmp_path, tokenizer):
    ids = [0, 65536, 131071, 42, 100000]
    path = tmp_path / "fineweb_train_000001.bin"
    write_shard(path, ids)
    assert open_shard(path).dtype == np.dtype("<u4")
    assert open_shard(path).tolist() == ids
    (tmp_path / "tokenizer.json.meta").write_text(json.dumps(
        {"revision": REVISION, "sha256": SHA256, "vocab_size": VOCAB_SIZE}))
    ld = Loader("fineweb10b", 1, 4, "cpu", data_dir=tmp_path, tokenizer_path=tokenizer.path)
    x, y = ld.next_batch()
    assert x.tolist() == [ids[:-1]]
    assert y.tolist() == [ids[1:]]
    synthetic = Loader("synthetic", 1, 4, "cpu", tokenizer_path=tokenizer.path)
    actual, lens = synthetic.token_bytes(32)
    expected, expected_lens = tokenizer.token_bytes(32)
    assert torch.equal(actual, expected) and torch.equal(lens, expected_lens)
    with pytest.raises(ValueError, match="vocabulary"):
        Loader("synthetic", 1, 4, "cpu", vocab_size=50304, tokenizer_path=tokenizer.path)
    # Old uint16 headers must fail before token IDs can be misinterpreted.
    # Use a separate path because open_shard returns a memory map that Windows locks.
    legacy_path = tmp_path / "fineweb_train_legacy.bin"
    legacy_path.write_bytes(np.array([20240520, 1, 5] + [0] * 253, dtype="<i4").tobytes())
    with pytest.raises(ValueError, match="Brahmic uint32"):
        open_shard(legacy_path)
