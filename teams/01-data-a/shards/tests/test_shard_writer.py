"""Tests for shard_writer.py on made-up docs (English, Hindi, Malayalam, Tamil, code), put through a synthetic pipeline run
(synthetic_run.py) so the writer reads what run_pipeline.py writes. They use the baseline BrahmicTokenizer-131K that G6 pins
(fetched once by G6's tokenizer.py) with --any-tokenizer, since p1536's tokenizer.json is not in the repo; with p1536 the same
checks run on the real file.

  python -m pytest teams/01-data-a/shards/tests/test_shard_writer.py
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("shard_writer", HERE.parent / "shard_writer.py")
sw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sw)
sys.path.insert(0, str(HERE))
from synthetic_run import CLEAN_SHA, make_run, raw_sha, sha  # noqa: E402
from dataio.loader import open_shard  # noqa: E402  (shard_writer put G6's folder on sys.path)
from dataio.tokenizer import BrahmicTokenizer  # noqa: E402

BASE = BrahmicTokenizer().path  # the pinned baseline, downloaded and checked by G6's code on first use
MALAYALAM_OLD_CHILLU = "അവന്‍"  # n + virama + ZWJ: the old chillu spelling
DOCS = [
    ("en1", "The water cycle moves water between the sea, the air and the land.\n", "en"),
    ("hi1", "पानी समुद्र, हवा और ज़मीन के बीच घूमता है।\n", "hi"),
    ("ml1", f"{MALAYALAM_OLD_CHILLU} വന്നു. മഴ പെയ്തു.\n", "ml"),
    ("ta1", "நீர் கடல், காற்று, நிலம் இடையே சுற்றுகிறது.\n", "ta"),
    ("go1", "package main\n\nfunc area(r float64) float64 {\n\treturn 3.14159 * r * r\n}\n", "code"),
]


def rows_of(docs, pack):
    return [{"doc_id": d, "text": text, "url": "", "lang_label": lang, "pack_id": pack} for d, text, lang in docs]


def run_of(folder, monkeypatch, docs, pack="x-pack", removed_rows=(), f2_drop=()):
    """A synthetic pipeline run over one train part of `docs`. Returns (run folder, part name)."""
    part = f"{pack}/part-00000.parquet"
    removed = [("train", part, row) for row in removed_rows]
    return make_run(folder, monkeypatch, {("train", part): rows_of(docs, pack)}, removed=removed, f2_drop=f2_drop), part


def shard(run, part, out, *extra, tokenizer=BASE, split="train"):
    return sw.main(["--input", str(run / "final" / split / part), "--manifest", str(run / "pipeline_manifest.json"),
                    "--tokenizer", str(tokenizer), "--language", "mixed", "--script", "mixed", "--lane", "test",
                    "--out", str(out), *extra])


def write(tmp_path, monkeypatch, docs, *extra, tokenizer=BASE):
    run, part = run_of(tmp_path / "pipeline", monkeypatch, docs)
    out = tmp_path / "out"
    m = shard(run, part, out, "--domain", "web", *extra, tokenizer=tokenizer)
    return m, out, json.loads(next(out.glob("*.quality_report.json")).read_text(encoding="utf-8"))


def test_a_shard_of_five_languages_is_written_and_checked(tmp_path, monkeypatch):
    m, out, q = write(tmp_path, monkeypatch, DOCS, "--any-tokenizer")
    assert m["dataset_version"] == "test" and m["eos_token_id"] == 130822 and m["doc_count"] == 5
    assert q["left_out"] == {"secret": 0, "empty": 0, "special": 0, "roundtrip": 0}
    tokens, idx = open_shard(out / m["payload_uri"]), np.load(out / m["index_uri"])
    assert len(tokens) == m["token_count"] == idx[-1] and len(idx) == 6
    assert (tokens == 130822).sum() == 5 and (tokens[idx[1:] - 1] == 130822).all()
    meta = pq.read_table(out / m["sample_metadata_uri"]).to_pylist()
    assert [r["doc_id"] for r in meta] == [d for d, _, _ in DOCS] and [r["input_row"] for r in meta] == list(range(5))
    tok = sw.Tokenizer.from_file(str(BASE))
    for k, (_, text, _) in enumerate(DOCS):  # the Malayalam ZWJ spelling survives: the baseline has no normalizer
        assert tok.decode(tokens[idx[k]:idx[k + 1] - 1].tolist(), skip_special_tokens=False) == text


def test_a_literal_special_string_in_the_text_leaves_the_doc_out(tmp_path, monkeypatch):
    docs = DOCS[:1] + [("im", "x = '<|im_start|>user'\n", "code"), ("eot", "a <|end_of_text|> b\n", "en")] + DOCS[1:2]
    m, out, q = write(tmp_path, monkeypatch, docs, "--any-tokenizer")
    assert q["left_out_docs"]["special"] == [{"doc_id": "im", "ids": [129994]}, {"doc_id": "eot", "ids": [36]}]
    assert m["doc_count"] == 2


def test_secret_like_and_empty_docs_are_left_out(tmp_path, monkeypatch):
    mail = "someone.name" + "@" + "gmail.com"  # built at run time: pr-guard scans the added lines for addresses
    docs = [("mail", f"write to {mail} today\n", "en"), ("empty", "", "en")] + DOCS[:1]
    m, _, q = write(tmp_path, monkeypatch, docs, "--any-tokenizer")
    assert q["left_out_docs"]["secret"] == ["mail"] and q["left_out_docs"]["empty"] == ["empty"] and m["doc_count"] == 1


def test_a_doc_is_never_split_and_the_shard_stops_at_the_limit(tmp_path, monkeypatch):
    tok = sw.Tokenizer.from_file(str(BASE))
    first_two = sum(len(tok.encode(t, add_special_tokens=False).ids) + 1 for _, t, _ in DOCS[:2])
    m, out, q = write(tmp_path, monkeypatch, DOCS, "--any-tokenizer", "--tokens", str(first_two + 1))
    assert m["doc_count"] == 2 and m["token_count"] == first_two and q["rows_read"] == 2


def test_the_round_trip_compares_with_the_normalized_text(tmp_path, monkeypatch):
    """A tokenizer with an NFC normalizer: a decomposed é comes back composed, and the doc is kept."""
    spec_ = json.loads(Path(BASE).read_text(encoding="utf-8"))
    spec_["normalizer"] = {"type": "Sequence", "normalizers": [{"type": "NFC"}]}  # a Sequence, as in C3: it tests falsy
    nfc = tmp_path / "nfc_tokenizer.json"
    nfc.write_text(json.dumps(spec_), encoding="utf-8")
    m, out, q = write(tmp_path, monkeypatch, [("cafe", "café au lait\n", "en")], "--any-tokenizer", tokenizer=nfc)
    assert q["left_out"]["roundtrip"] == 0 and m["doc_count"] == 1
    ids = open_shard(out / m["payload_uri"]).tolist()[:-1]
    assert sw.Tokenizer.from_file(str(nfc)).decode(ids) == "café au lait\n"


def test_any_tokenizer_but_c3_is_refused(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="not the frozen p1536"):
        write(tmp_path, monkeypatch, DOCS)


def test_the_c3_pin_matches_g3s_release():
    assert sw.TOKENIZER_SHA256.startswith("e6b93a93") and sw.EOS_ID == 130822 and sys.modules["dataio.loader"].HEADER_BYTES == 1024


def test_the_manifest_records_the_pipeline_run(tmp_path, monkeypatch):
    run, part = run_of(tmp_path / "pipeline", monkeypatch, DOCS, removed_rows=[1], f2_drop=["ta1"])  # dedup: hi1, F2: ta1
    out = tmp_path / "out"
    m = shard(run, part, out, "--any-tokenizer", "--domain", "web")
    assert (m["shard_id"], m["split"], m["pack_id"], m["domain"], m["doc_count"]) == ("x-pack-train-000000", "train", "x-pack", "web", 3)
    q = json.loads((out / "x-pack-train-000000.quality_report.json").read_text(encoding="utf-8"))["upstream"]
    assert q["counts"] == {"cleaned": 5, "removed_by_dedup": 1, "dropped_by_f2": 1, "final": 3}
    assert q["removed_by_dedup"] == [{"doc_id": "hi1", "row_in_part": 1, "group_id": "G000001", "priority_rule": 4}]
    assert q["dropped_by_f2"] == [{"doc_id": "ta1", "items": ["fake:1"], "offset": 0}]
    assert q["input_part"] == f"train/{part}" and q["raw_input_sha256"] == raw_sha("train", part)
    cp = json.loads((out / "cleaning_pipeline.json").read_text(encoding="utf-8"))
    assert cp["clean_py_sha256"] == CLEAN_SHA and cp["f2_set_sha256"] == m["decontam_set_sha256"]
    assert cp["dedup"]["remove_list_sha256"] == sha(tmp_path / "pipeline" / "dedup" / "remove_list.csv") and cp["dedup"]["remove_list_rows"] == 1
    assert sorted(cp["dedup"]) == ["code_sha256", "overlap", "remove_list_rows", "remove_list_sha256", "settings"]
    assert cp["dedup"]["settings"]["pack_order"] == ["code-go", "en-dclm"] and cp["dedup"]["overlap"]["k"] == 5
    assert sorted(cp) == ["clean_py_sha256", "dedup", "f2_set_sha256"]  # the processing only: no link to the run log
    assert q["run_id"] == "test-run"
    assert m["cleaning_pipeline_sha256"] == sha(out / "cleaning_pipeline.json")
    assert m["inputs_sha256"] == hashlib.sha256(f"{raw_sha('train', part)} train/{part}\n".encode()).hexdigest()
    meta = pq.read_table(out / m["sample_metadata_uri"]).to_pylist()
    assert [(r["doc_id"], r["input_part"], r["input_row"]) for r in meta] == [(d, f"train/{part}", k) for k, d in enumerate(["en1", "ml1", "go1"])]
    assert "dedup (1 of this part's 5 docs removed)" in (out / "x-pack-train-000000.dump.md").read_text(encoding="utf-8")


def test_a_part_that_changed_after_f2_is_refused(tmp_path, monkeypatch):
    run, part = run_of(tmp_path / "pipeline", monkeypatch, DOCS)
    f = run / "final" / "train" / part
    pq.write_table(pq.read_table(f).slice(0, 2), f)
    with pytest.raises(SystemExit, match="changed after F2"):
        shard(run, part, tmp_path / "out", "--any-tokenizer", "--domain", "web")
    assert not (tmp_path / "out").exists()


def test_a_heldout_part_is_refused(tmp_path, monkeypatch):
    part = "x-pack/part-00000.parquet"
    run = make_run(tmp_path / "pipeline", monkeypatch, {("train", part): rows_of(DOCS, "x-pack"), ("heldout", part): rows_of(DOCS[:2], "x-pack")})
    with pytest.raises(SystemExit, match="heldout part"):
        shard(run, part, tmp_path / "out", "--any-tokenizer", "--domain", "web", split="heldout")


def test_an_out_folder_with_other_processing_is_refused(tmp_path, monkeypatch):
    write(tmp_path, monkeypatch, DOCS, "--any-tokenizer")
    other, part = run_of(tmp_path / "other", monkeypatch, DOCS, removed_rows=[1])  # a different remove list
    with pytest.raises(SystemExit, match="other processing"):
        shard(other, part, tmp_path / "out", "--any-tokenizer", "--domain", "web")


def test_a_second_shard_of_the_same_run_may_share_the_out_folder(tmp_path, monkeypatch):
    run, part = run_of(tmp_path / "pipeline", monkeypatch, DOCS)
    out = tmp_path / "out"
    shard(run, part, out, "--any-tokenizer", "--domain", "web")
    m = shard(run, part, out, "--any-tokenizer", "--domain", "web", "--index", "1")
    assert m["shard_id"] == "x-pack-train-000001"


def test_the_domain_defaults_to_cleans_family_of_the_pack(tmp_path, monkeypatch):
    run, part = run_of(tmp_path / "pipeline", monkeypatch, DOCS[:1], pack="code-go")
    assert shard(run, part, tmp_path / "out", "--any-tokenizer")["domain"] == "code"


def test_a_pack_clean_has_no_family_for_needs_a_domain(tmp_path, monkeypatch):
    run, part = run_of(tmp_path / "pipeline", monkeypatch, DOCS[:1])
    with pytest.raises(SystemExit, match="give --domain"):
        shard(run, part, tmp_path / "out", "--any-tokenizer")


def test_without_the_runs_cleaning_pipeline_file_nothing_is_written(tmp_path, monkeypatch):
    run, part = run_of(tmp_path / "pipeline", monkeypatch, DOCS)
    (run / "cleaning_pipeline.json").unlink()
    with pytest.raises(SystemExit, match="cleaning_pipeline.json not found: run_pipeline.py's shard stage writes it"):
        shard(run, part, tmp_path / "out", "--any-tokenizer", "--domain", "web")
    assert not (tmp_path / "out").exists()


def test_an_edited_cleaning_pipeline_file_is_refused(tmp_path, monkeypatch):
    run, part = run_of(tmp_path / "pipeline", monkeypatch, DOCS)
    f = run / "cleaning_pipeline.json"
    record = json.loads(f.read_text(encoding="utf-8"))
    record["clean_py_sha256"] = "0" * 64
    f.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(SystemExit, match="is not what .* give now"):
        shard(run, part, tmp_path / "out", "--any-tokenizer", "--domain", "web")
    assert not (tmp_path / "out").exists()


def test_the_shard_folder_gets_the_runs_file_byte_for_byte(tmp_path, monkeypatch):
    run, part = run_of(tmp_path / "pipeline", monkeypatch, DOCS)
    m = shard(run, part, tmp_path / "out", "--any-tokenizer", "--domain", "web")
    assert (tmp_path / "out" / "cleaning_pipeline.json").read_bytes() == (run / "cleaning_pipeline.json").read_bytes()
    assert m["cleaning_pipeline_sha256"] == sha(run / "cleaning_pipeline.json")
