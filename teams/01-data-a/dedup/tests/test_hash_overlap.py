"""Unit tests for hash_overlap.py, the exact-copy overlap stage that reads the clean job's text_hash column instead of text:
the same rows and H1 edges as minhash_overlap.py on the same parts, the files dedup.py and the runner read (dedup.py run on
them), no text read, and its input and config checks. Every text here is made up. The stage runs in-process with its
repository root pointed at a temporary folder.

  python3 -B -m pytest teams/01-data-a/dedup/tests/test_hash_overlap.py
"""
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pa = pytest.importorskip("pyarrow")
import pyarrow.parquet as pq  # noqa: E402

DEDUP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEDUP))
import hash_overlap as ho  # noqa: E402
from h1_sha256 import NORMALIZE_ID, h1_key  # noqa: E402

WORDS = ("river stone bridge garden market window letter silver forest engine harbour lantern meadow pencil orchard "
         "valley thunder candle mirror basket ladder copper island marble needle saddle temple violin whistle yellow").split()


def prose(rng, n=80):
    return " ".join(rng.choice(WORDS) for _ in range(n))


def sample(seed=11):
    """Planted copies. Rows (train parts in sorted order, then held-out): 0 a1, 1 a2, 2 a3, 3 a4, 4 a5 | 5 b1, 6 b2, 7 b3,
    8 b4 | 9 m1, 10 m2 | 11 hb1, 12 hb2. Exact after the H1 key: a1/b1 (case), a3/b4 (trailing spaces), a4/b3 (both
    empty), m1/m2, b2/hb1 (train and held-out). a2 is a1 with one word changed: a near copy, not an exact one."""
    rng = random.Random(seed)
    a, b, c, m = prose(rng), prose(rng), prose(rng), prose(rng) + " the answer is 42"
    w = a.split(" ")
    w[3] = "zebra"
    return {
        "train/en-a/part-00000.parquet": [("a1", a), ("a2", " ".join(w)), ("a3", c), ("a4", ""), ("a5", prose(rng))],
        "train/en-b/part-00000.parquet": [("b1", a.upper()), ("b2", b), ("b3", ""), ("b4", c + "   ")],
        "train/math-x/part-00000.parquet": [("m1", m), ("m2", m)],
        "heldout/en-b/part-00000.parquet": [("hb1", b), ("hb2", prose(rng))],
    }


def hash_columns(text):
    key = h1_key(text)
    return hashlib.sha256(key.encode("utf-8")).hexdigest(), len(key.split(" ")) if key else 0


def write(root, parts, text=True, hashed=True, spec=True, normalize_id=NORMALIZE_ID, rows_hook=None):
    """Cleaned parts as the clean job writes them with "text_hash": true, and its job_summary.json."""
    base = root / "inputs" / "cleaned"
    for split in ("train", "heldout"):
        (base / split).mkdir(parents=True, exist_ok=True)
    for name, docs in parts.items():
        rows = []
        for d, t in docs:
            row = {"doc_id": d, "pack_id": name.split("/")[1], "lang_label": "en"}
            if text:
                row["text"] = t
            if hashed:
                row["text_hash"], row["key_words"] = hash_columns(t)
            rows.append(row)
        if rows_hook:
            rows_hook(name, rows)
        schema = None
        if hashed:
            schema = pa.Table.from_pylist(rows).schema.set(
                pa.Table.from_pylist(rows).schema.get_field_index("key_words"), pa.field("key_words", pa.int32()))
        p = base / name
        p.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pylist(rows, schema=schema), p)
    summary = {"clean_sha256": "0" * 64}
    if spec:
        summary["text_hash"] = {"columns": ["text_hash", "key_words"], "normalize_id": normalize_id,
                                "key": "h1_key of dedup/h1_sha256.py"}
    (base / "job_summary.json").write_text(json.dumps(summary))


def config(root, name, out, **over):
    p = root / f"{name}.json"
    p.write_text(json.dumps({"inputs": "inputs/cleaned", "out": out, "workers": 1, **over}))
    return p


def run_hash(monkeypatch, root, cfg):
    monkeypatch.setattr(ho, "REPO", root)
    monkeypatch.setattr(sys, "argv", ["hash_overlap.py", "--config", str(cfg)])
    ho.main()
    out = root / json.loads(cfg.read_text())["out"]
    return out, json.loads((out / "overlap_summary.json").read_text())


def matches(out):
    with open(out / "overlap_matches.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture
def hash_run(tmp_path, monkeypatch):
    write(tmp_path, sample())
    return run_hash(monkeypatch, tmp_path, config(tmp_path, "h", "out/hash"))


# --- what it finds ------------------------------------------------------------------------------------------------------
def test_exact_copies_after_the_h1_key_are_star_edges_and_near_copies_are_not(hash_run):
    out, s = hash_run
    got = [(int(r["row_a"]), int(r["row_b"]), r["rule"], r["stage"], r["pack_a"], r["pack_b"], r["word_jaccard"],
            r["code_jaccard"]) for r in matches(out)]
    assert got == [(0, 5, "H1", "cross_pack", "en-a", "en-b", "1.0", ""),       # case only
                   (3, 7, "H1", "cross_pack", "en-a", "en-b", "1.0", ""),       # both empty: dedup.py sets them aside
                   (2, 8, "H1", "cross_pack", "en-a", "en-b", "1.0", ""),       # trailing spaces
                   (9, 10, "H1", "within_pack", "math-x", "math-x", "1.0", ""),
                   (6, 11, "H1", "within_pack", "en-b", "en-b", "1.0", "")]     # train <-> held-out
    assert not any({int(r["row_a"]), int(r["row_b"])} == {0, 1} for r in matches(out))   # a2: one word changed
    assert (s["h1_exact_groups"], s["documents_in_h1_exact_groups"], s["empty_documents"]) == (5, 10, 2)
    assert (s["documents_all"], s["distinct_hashes"], s["qualifying_pairs_by_rule"]) == (13, 8, {"H1": 5})


def test_the_docs_table_has_overlap_py_columns_and_shingles_zero_only_for_empty_keys_never_null(hash_run):
    out, _ = hash_run
    docs = pq.read_table(out / "overlap_docs.parquet")
    assert docs.column_names == ["row", "id", "doc_id", "pack", "split", "part", "row_in_part", "words", "shingles"]
    assert "text" not in docs.column_names and "text_hash" not in docs.column_names
    d = docs.to_pylist()
    assert [r["id"] for r in d][:2] == ["en-a-a1", "en-a-a2"] and d[11]["split"] == "heldout"
    assert [r["row_in_part"] for r in d] == [0, 1, 2, 3, 4, 0, 1, 2, 3, 0, 1, 0, 1]
    assert [r["row"] for r in d if r["shingles"] == 0] == [3, 7]
    assert [r["shingles"] for r in d] == [max(r["words"] - 4, 1) if r["words"] else 0 for r in d]   # never null
    assert docs.column("shingles").null_count == 0


def test_writes_what_dedup_and_the_runner_read(hash_run):
    out, s = hash_run
    assert s["status"] == "complete" and s["method"] == "exact_hash" and s["normalize_id"] == NORMALIZE_ID
    for name in ("overlap_matches.csv", "overlap_docs.parquet"):
        assert s["outputs"][name]["sha256"] == ho.sha256_file(out / name)
    assert [(p["part"], p["documents"]) for p in s["inputs"]["parts"]] == [
        ("train/en-a/part-00000.parquet", 5), ("train/en-b/part-00000.parquet", 4),
        ("train/math-x/part-00000.parquet", 2), ("heldout/en-b/part-00000.parquet", 2)]
    assert s["documents"]["en-b"] == {"train": 4, "heldout": 2, "all": 6}
    assert "overlap_docs.parquet" not in s["returned_files"]


def test_dedup_removes_the_exact_copies_and_never_a_heldout_document(hash_run, monkeypatch):
    import dedup
    out, _ = hash_run
    root = out.parents[1]
    monkeypatch.setattr(dedup, "REPO", root)
    cfg = root / "dedup.json"
    cfg.write_text(json.dumps({"results": "out/hash", "inputs": "", "out": "out/dedup", "cross_pack": True,
                               "pack_order": ["en-a", "en-b", "math-x"], "licence_usable": {},
                               "default_licence_usable": True, "gold_dirs": []}))
    s = dedup.run(dedup.load_config(cfg))
    log = [json.loads(line) for line in (root / "out/dedup/dedup_log.jsonl").read_text().splitlines()]
    assert sorted(e["removed_id"] for e in log) == ["b1", "b2", "b4", "m2"]   # hb1 (held-out) is kept over b2
    assert s["heldout_removed"] == 0 and s["removed"] == 4 and s["empty_documents"] == 2
    assert s["removed_by_rule"].get("H1") == 4 and not s["removed_by_rule"].get("H2")


def test_the_same_rows_and_h1_edges_as_minhash_overlap(tmp_path, monkeypatch):
    for module in ("scipy", "pandas", "pygments"):
        pytest.importorskip(module)
    import minhash_overlap as mh
    write(tmp_path, sample())
    h_out, _ = run_hash(monkeypatch, tmp_path, config(tmp_path, "h", "out/hash"))
    monkeypatch.setattr(mh, "REPO", tmp_path)
    monkeypatch.setattr(sys, "argv", ["minhash_overlap.py", "--config", str(config(tmp_path, "m", "out/mh"))])
    mh.main()
    m_out = tmp_path / "out/mh"
    cols = ["row", "id", "doc_id", "pack", "split", "part", "row_in_part", "words"]
    h_docs, m_docs = pq.read_table(h_out / "overlap_docs.parquet"), pq.read_table(m_out / "overlap_docs.parquet")
    assert h_docs.select(cols).to_pylist() == m_docs.select(cols).to_pylist()
    assert [r["shingles"] == 0 for r in h_docs.to_pylist()] == [r["shingles"] == 0 for r in m_docs.to_pylist()]
    assert matches(h_out) == [r for r in matches(m_out) if r["rule"] == "H1"]


# --- what it reads ------------------------------------------------------------------------------------------------------
def test_parts_without_text_are_enough(tmp_path, monkeypatch):
    write(tmp_path, sample(), text=False)
    out, s = run_hash(monkeypatch, tmp_path, config(tmp_path, "h", "out/hash"))
    assert s["qualifying_pairs_by_rule"] == {"H1": 5}


def refused(monkeypatch, root, message, **over):
    with pytest.raises(SystemExit) as e:
        run_hash(monkeypatch, root, config(root, "h", "out/hash", **over))
    assert message in str(e.value)


def test_parts_cleaned_without_text_hash_are_refused(tmp_path, monkeypatch):
    write(tmp_path, sample(), hashed=False)
    refused(monkeypatch, tmp_path, 'clean with "text_hash": true')


def test_a_clean_job_that_records_no_text_hash_is_refused(tmp_path, monkeypatch):
    write(tmp_path, sample(), spec=False)
    refused(monkeypatch, tmp_path, "records no text_hash")


def test_keys_of_another_normalize_are_refused(tmp_path, monkeypatch):
    write(tmp_path, sample(), normalize_id="some-other-normalize")
    refused(monkeypatch, tmp_path, "hashed keys of normalize 'some-other-normalize'")


def test_a_word_count_that_does_not_fit_the_hash_is_refused(tmp_path, monkeypatch):
    def zero_words(name, rows):
        if name == "train/en-a/part-00000.parquet":
            rows[0]["key_words"] = 0   # a non-empty key with no words
    write(tmp_path, sample(), rows_hook=zero_words)
    refused(monkeypatch, tmp_path, "do not come from one key")


def test_a_hash_that_is_not_a_sha256_is_refused(tmp_path, monkeypatch):
    def short(name, rows):
        if name == "train/math-x/part-00000.parquet":
            rows[1]["text_hash"] = "abc"
    write(tmp_path, sample(), rows_hook=short)
    refused(monkeypatch, tmp_path, "64 lowercase hex characters")


def test_the_pack_inventory_is_checked(tmp_path, monkeypatch):
    write(tmp_path, sample())
    refused(monkeypatch, tmp_path, "pack inventory mismatch", expected_packs=["en-a", "en-b"])


@pytest.mark.parametrize("over, message", [({"workers": -1}, "workers must be"), ({"workers": True}, "workers must be"),
                                           ({"max_output_mb": 60}, "at most 50"), ({"out": "elsewhere"}, "inside out/"),
                                           ({"splits": ["dev"]}, "splits must be"), ({"k": 5}, "unknown keys")])
def test_a_bad_config_is_refused(tmp_path, monkeypatch, over, message):
    monkeypatch.setattr(ho, "REPO", tmp_path)
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"inputs": "inputs/cleaned", "out": "out/t", **over}))
    with pytest.raises(SystemExit) as e:
        ho.load_config(p)
    assert message in str(e.value)


def test_the_settings_file_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr(ho, "REPO", tmp_path)
    cfg = ho.load_config(DEDUP / "hash_overlap.json")
    assert len(cfg["expected_packs"]) == 38 and cfg["splits"] == ["train", "heldout"]
