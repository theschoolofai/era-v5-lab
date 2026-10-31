"""Check the hash framing, full-ID coverage, decoder settings and fresh-process runner."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "src" / "determinism" / "tokenizer_decode_cpu.py"
spec = importlib.util.spec_from_file_location("tokenizer_decode_cpu", SCRIPT)
dc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dc)


def test_hash_preserves_bytes_ids_order_and_boundaries():
    baseline = [(0, b"a"), (1, b"bc")]
    assert dc.hash_rows(baseline) == dc.hash_rows(iter(baseline))
    variants = [
        [(0, b"ab"), (1, b"c")],
        [(0, b"a"), (1, b"bd")],
        [(2, b"a"), (1, b"bc")],
        list(reversed(baseline)),
    ]
    assert all(dc.hash_rows(rows) != dc.hash_rows(baseline) for rows in variants)


def test_vocabulary_requires_all_ids():
    assert dc.check_ids({"b": 1, "a": 0}) == [0, 1]
    for vocab in ({}, {"a": 1}, {"a": 0, "b": 2}, {"a": 0, "b": 0}):
        with pytest.raises(ValueError):
            dc.check_ids(vocab)


def test_every_id_is_decoded_including_specials():
    class Decoder:
        def __init__(self):
            self.calls = []

        def decode(self, ids, skip_special_tokens):
            self.calls.append((ids, skip_special_tokens))
            return ["क", "�", "<s>"][ids[0]]

    decoder = Decoder()
    rows = list(dc.decoded_rows(decoder, [0, 1, 2], {2: b"<s>"}))
    assert rows == [(0, "क".encode()), (1, bytes.fromhex("ef bf bd")), (2, b"<s>")]
    assert decoder.calls == [([0], False), ([1], False), ([2], False)]
    with pytest.raises(ValueError, match="special token"):
        list(dc.decoded_rows(decoder, [2], {2: b"different"}))


def test_disagreement_and_missing_runs_fail():
    run = {"sha256": "same", "token_count": 3, "tokenizer_sha256": "artifact"}
    dc.verify_runs([run.copy() for _ in range(3)])
    for key, changed in (("sha256", "different"), ("token_count", 2), ("tokenizer_sha256", "other")):
        with pytest.raises(ValueError, match="disagree"):
            dc.verify_runs([run, run, dict(run, **{key: changed})])
    with pytest.raises(ValueError, match="three"):
        dc.verify_runs([run, run])


def test_three_fresh_processes_and_cli_outputs(tmp_path):
    tokenizers = pytest.importorskip("tokenizers")
    tokenizer = tokenizers.Tokenizer(tokenizers.models.WordLevel({"[UNK]": 0, "hello": 1, "क": 2}, unk_token="[UNK]"))
    tokenizer.add_special_tokens(["<s>"])
    path = tmp_path / "tokenizer.json"
    tokenizer.save(str(path))
    expected = dc.hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="artifact"):
        dc.decode_once(path, "wrong")
    with pytest.raises(RuntimeError, match="CPU run 1 failed"):
        dc.run_three(path, "wrong")
    runs = dc.run_three(path, expected)
    assert len(runs) == 3 and runs[0]["token_count"] == 4
    assert runs[0]["sha256"] == dc.hash_rows([(0, b"[UNK]"), (1, b"hello"), (2, "क".encode()), (3, b"<s>")])
    output = tmp_path / "results"
    result = dc.subprocess.run(
        [sys.executable, str(SCRIPT), "--tokenizer", str(path), "--expected-sha256", expected, "--out", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (output / "tokenizer_decode_cpu_sha256.txt").read_text().splitlines() == [runs[0]["sha256"]] * 3
    metadata = dc.json.loads((output / "tokenizer_decode_cpu_metadata.json").read_text())
    assert metadata["all_match"] and metadata["runs"] == runs
