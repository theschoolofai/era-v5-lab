"""Tests for decode_shard.py (G9, week 3 task 2).

    pytest teams/09-evaluation/decontam/tests/test_decode_shard.py -q

The unit tests build tiny shards in shard format v1 with a small word-level tokenizer, so they need numpy, pyarrow and
tokenizers but not the C3 tokenizer.json (8 MB, not in the repo). They are skipped without those packages.

One more test runs on a real shard when ERA_SHARD (a <shard_id>.bin with its .idx.npy, .docs.parquet and .json next to
it) and ERA_C3_TOKENIZER (the frozen C3 tokenizer.json) are set; ERA_SHARD_CLEAN (the run_clean.py *_clean.parquet it
came from) adds the round-trip check. Data A's sample shard (teams/01-data-a/shards/sample/README.md) can be rebuilt
for this with the two commands in its README.
"""

import hashlib
import json
import os
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")
tokenizers = pytest.importorskip("tokenizers")

import decode_shard as ds  # noqa: E402
from decontam_check import read_docs  # noqa: E402

EOS, SPECIAL = 9, 9  # toy vocab: id 9 is the EOS and the first special id
VOCAB = {"[UNK]": 0, "hello": 1, "world": 2, "foo": 3, "bar": 4, "baz": 5, "<x>": 8, "<eos>": 9}
DOCS = {"d1": "hello world", "d2": "foo bar baz", "d3": "world"}


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.fixture
def toy_tokenizer(tmp_path):
    from tokenizers import Tokenizer, models, pre_tokenizers
    tok = Tokenizer(models.WordLevel(VOCAB, unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    path = tmp_path / "toy_tokenizer.json"
    tok.save(str(path))
    return path


def write_shard(folder, tok_path, docs=DOCS, shard_id="toy-train-000000", eos=EOS, tamper=None):
    """Write <shard_id>.{bin,idx.npy,docs.parquet,json} like shard_writer.py. tamper(files) may edit before the manifest."""
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(tok_path))
    seqs = [tok.encode(text).ids + [eos] for text in docs.values()]
    tokens = np.array([t for s in seqs for t in s], dtype="<u4")
    starts = np.concatenate([[0], np.cumsum([len(s) for s in seqs])]).astype(np.int64)
    folder = Path(folder)
    files = {"bin": folder / f"{shard_id}.bin", "idx": folder / f"{shard_id}.idx.npy",
             "docs": folder / f"{shard_id}.docs.parquet", "manifest": folder / f"{shard_id}.json"}
    header = np.zeros(256, dtype="<i4")
    header[:3] = [ds.MAGIC, ds.VERSION, len(tokens)]
    files["bin"].write_bytes(header.tobytes() + tokens.tobytes())
    np.save(files["idx"], starts)
    pq.write_table(pa.table({"doc_id": list(docs), "n_tokens": np.diff(starts)}), files["docs"])
    if tamper:
        tamper(files)
    manifest = {"shard_id": shard_id, "payload_sha256": _sha(files["bin"]), "index_sha256": _sha(files["idx"]),
                "sample_metadata_sha256": _sha(files["docs"]), "doc_count": len(docs), "token_count": len(tokens),
                "eos_token_id": eos, "tokenizer_sha256": _sha(tok_path)}
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    return files


def _decode(files, tok_path):
    tok, sha = ds.load_tokenizer(tok_path, any_tokenizer=True)
    return ds.decode_shard(files["bin"], tok, sha, eos_id=EOS, special_from=SPECIAL)


def test_decode_round_trip(tmp_path, toy_tokenizer):
    files = write_shard(tmp_path, toy_tokenizer)
    table = _decode(files, toy_tokenizer)
    assert table.column("doc_id").to_pylist() == list(DOCS)
    assert table.column("text").to_pylist() == list(DOCS.values())
    assert table.column("n_tokens").to_pylist() == [3, 4, 2]  # tokens plus the final EOS
    assert set(table.column("shard_id").to_pylist()) == {"toy-train-000000"}


def test_output_reads_in_decontam_check(tmp_path, toy_tokenizer):
    files = write_shard(tmp_path, toy_tokenizer)
    out = tmp_path / "toy.text.parquet"
    pq.write_table(_decode(files, toy_tokenizer), out)
    assert list(read_docs([out], "doc_id", "text")) == list(DOCS.items())


def test_check_text_finds_a_changed_document(tmp_path, toy_tokenizer):
    files = write_shard(tmp_path, toy_tokenizer)
    table = _decode(files, toy_tokenizer)
    clean = tmp_path / "clean.parquet"
    pq.write_table(pa.table({"doc_id": list(DOCS), "text": list(DOCS.values())}), clean)
    tok, _ = ds.load_tokenizer(toy_tokenizer, any_tokenizer=True)
    assert ds.check_text(table, clean, tok) == (3, [])
    pq.write_table(pa.table({"doc_id": ["d1", "d2"], "text": ["hello world", "foo baz"]}), clean)
    checked, bad = ds.check_text(table, clean, tok)
    assert checked == 3 and dict(bad) == {"d2": "text differs", "d3": "not in source"}


def test_cli_writes_one_file_per_shard(tmp_path, toy_tokenizer, capsys):
    shards = tmp_path / "shards"
    shards.mkdir()
    write_shard(shards, toy_tokenizer, shard_id="toy-train-000000")
    write_shard(shards, toy_tokenizer, docs={"e1": "baz foo"}, shard_id="toy-train-000001")
    old = (ds.EOS_ID, ds.SPECIAL_FROM)
    ds.EOS_ID, ds.SPECIAL_FROM = EOS, SPECIAL
    try:
        rc = ds.main([str(shards), "--tokenizer", str(toy_tokenizer), "--out", str(tmp_path / "out"), "--any-tokenizer"])
    finally:
        ds.EOS_ID, ds.SPECIAL_FROM = old
    assert rc == 0
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["toy-train-000000.text.parquet",
                                                                    "toy-train-000001.text.parquet"]
    assert "decoded 2 of 2 shard(s)" in capsys.readouterr().err


def test_refuses_a_tokenizer_that_is_not_c3(toy_tokenizer):
    with pytest.raises(ds.ShardError, match="not the frozen C3"):
        ds.load_tokenizer(toy_tokenizer)


def _set_header(index, value):
    def tamper(files):
        raw = bytearray(files["bin"].read_bytes())
        raw[4 * index:4 * index + 4] = int(value).to_bytes(4, "little", signed=True)
        files["bin"].write_bytes(bytes(raw))
    return tamper


@pytest.mark.parametrize("tamper, message", [
    (_set_header(0, 1234), "bad header"),
    (_set_header(1, 1), "bad header"),
    (lambda f: f["bin"].write_bytes(f["bin"].read_bytes()[:-4]), "size"),
    (lambda f: np.save(f["idx"], np.array([0, 3, 7], dtype=np.int64)), "end at the token count"),
    (lambda f: np.save(f["idx"], np.array([0, 3, 3, 9], dtype=np.int64)), "rise"),
    (lambda f: pq.write_table(pa.table({"doc_id": ["d1", "d2"]}), f["docs"]), "rows"),
])
def test_bad_shard_files_are_refused(tmp_path, toy_tokenizer, tamper, message):
    files = write_shard(tmp_path, toy_tokenizer, tamper=tamper)
    with pytest.raises(ds.ShardError, match=message):
        _decode(files, toy_tokenizer)


def test_manifest_hash_mismatch_is_refused(tmp_path, toy_tokenizer):
    files = write_shard(tmp_path, toy_tokenizer)
    m = json.loads(files["manifest"].read_text())
    m["payload_sha256"] = "0" * 64
    files["manifest"].write_text(json.dumps(m))
    with pytest.raises(ds.ShardError, match="payload_sha256"):
        _decode(files, toy_tokenizer)


def test_document_without_eos_is_refused(tmp_path, toy_tokenizer):
    def drop_last_eos(files):
        raw = bytearray(files["bin"].read_bytes())
        raw[-4:] = (2).to_bytes(4, "little")  # last doc ends with "world" instead of EOS
        files["bin"].write_bytes(bytes(raw))
    files = write_shard(tmp_path, toy_tokenizer, tamper=drop_last_eos)
    with pytest.raises(ds.ShardError, match="does not end with EOS"):
        _decode(files, toy_tokenizer)


def test_special_id_inside_a_document_is_refused(tmp_path, toy_tokenizer):
    def put_special_in_d2(files):
        raw = bytearray(files["bin"].read_bytes())
        pos = ds.HEADER_BYTES + 4 * 4  # token 4 = second token of d2 ("bar")
        raw[pos:pos + 4] = (8).to_bytes(4, "little")
        files["bin"].write_bytes(bytes(raw))
    files = write_shard(tmp_path, toy_tokenizer, tamper=put_special_in_d2)
    tok, sha = ds.load_tokenizer(toy_tokenizer, any_tokenizer=True)
    with pytest.raises(ds.ShardError, match="special id 8 inside document d2"):
        ds.decode_shard(files["bin"], tok, sha, eos_id=EOS, special_from=8)


def test_missing_file_is_refused(tmp_path, toy_tokenizer):
    files = write_shard(tmp_path, toy_tokenizer)
    files["docs"].unlink()
    with pytest.raises(ds.ShardError, match="missing"):
        _decode(files, toy_tokenizer)


real = pytest.mark.skipif(not (os.environ.get("ERA_SHARD") and os.environ.get("ERA_C3_TOKENIZER")),
                          reason="set ERA_SHARD and ERA_C3_TOKENIZER to test a real shard")


@real
def test_real_shard_decodes_and_matches_its_manifest():
    tok, sha = ds.load_tokenizer(os.environ["ERA_C3_TOKENIZER"])
    table = ds.decode_shard(os.environ["ERA_SHARD"], tok, sha)
    manifest = json.loads(ds.shard_files(os.environ["ERA_SHARD"])["manifest"].read_text(encoding="utf-8"))
    assert table.num_rows == manifest["doc_count"]
    assert sum(table.column("n_tokens").to_pylist()) == manifest["token_count"]
    if os.environ.get("ERA_SHARD_CLEAN"):
        checked, bad = ds.check_text(table, os.environ["ERA_SHARD_CLEAN"], tok)
        assert bad == [], f"{len(bad)} of {checked} documents do not round-trip"
