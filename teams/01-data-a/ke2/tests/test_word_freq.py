"""Tests for word_freq.py (KE2 request R1). Tiny made-up packs only: no real data."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
pytest.importorskip("regex")
import pyarrow.parquet as pq  # noqa: E402

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import word_freq as wf  # noqa: E402


@pytest.mark.parametrize("text, expected", [
    ("Don't x_velocity COVID-19 The the", ["Don", "t", "x", "velocity", "COVID", "The", "the"]),  # separators, case kept
    ("नमस्ते दुनिया", ["नमस्ते", "दुनिया"]),            # Devanagari: virama and vowel signs stay inside
    ("క్షమించండి", ["క్షమించండి"]),                       # Telugu conjuncts
    ("ലോകം, ಕನ್ನಡ.", ["ലോകം", "ಕನ್ನಡ"]),                 # Malayalam, Kannada; punctuation separates
    ("ক্‍ষ ‌abc‌", ["ক্‍ষ", "abc"]),  # ZWJ kept inside a word, ZWNJ dropped at the edges
    ("ﬁne café", ["ﬁne", "café"]),                        # no NFKC: the ligature stays
    ("café", ["café"]),                             # NFC: e + combining acute becomes é
    ("123 4.5 ___ --", []),                               # no letters, no words
])
def test_word_rule(text, expected):
    assert wf.words(text) == expected


def part(path, texts, pack):
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"doc_id": [f"{pack}-{i}" for i in range(len(texts))], "pack_id": [pack] * len(texts),
                             "text": texts}), path)
    return {"path": f"train/{pack}/{path.name}", "split": "train", "pack_id": pack, "rows": len(texts),
            "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def setup(tmp_path, monkeypatch):
    """Two packs in one (lane, language), one in another, in the course download's layout; a manifest; a held-out part
    that must not be read."""
    monkeypatch.setattr(wf, "REPO", tmp_path)
    packs = tmp_path / "packs"
    shards = [
        part(packs / "en-a/Part_1/part-00000.parquet", ["the cat", "The cat sat"], "en-a"),
        part(packs / "en-a/Part_2/part-00001.parquet", ["the dog"], "en-a"),
        part(packs / "en-b/Part_1/part-00000.parquet", ["the end"], "en-b"),
        part(packs / "ind-hi/Part_1/part-00000.parquet", ["नमस्ते नमस्ते", None], "ind-hi"),
    ]
    held = part(packs / "en-a/Heldout/part-00000.parquet", ["heldout words only"], "en-a")
    held.update(split="heldout", path="heldout/en-a/part-00000.parquet")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"shards": shards + [held]}), encoding="utf-8")
    approved = tmp_path / "approved.json"
    approved.write_text(json.dumps({"packs": [
        {"pack_id": "en-a", "language": "en", "lane": "english", "source": "src/a", "license": "odc-by",
         "license_source": "table@x"},
        {"pack_id": "en-b", "language": "en", "lane": "english", "source": "src/b", "license": "cc-by-4.0",
         "license_source": "table@x"},
        {"pack_id": "ind-hi", "language": "hi", "lane": "indic", "source": "src/h", "license": "cc0",
         "license_source": "table@x"},
    ]}), encoding="utf-8")
    return packs, manifest, approved


def run(monkeypatch, tmp_path, packs, manifest, approved, out="out/r1"):
    monkeypatch.setattr(sys, "argv", ["word_freq.py", "--packs", str(packs), "--manifest", str(manifest),
                                      "--approved", str(approved), "--out", out, "--workers", "1"])
    wf.main()
    return tmp_path / out


def rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def test_tables_per_language_and_lane(tmp_path, monkeypatch):
    out = run(monkeypatch, tmp_path, *setup(tmp_path, monkeypatch))
    assert rows(out / "english__en.csv") == [["word", "count", "lang", "lane"], ["the", "3", "en", "english"],
                                             ["cat", "2", "en", "english"], ["The", "1", "en", "english"],
                                             ["dog", "1", "en", "english"], ["end", "1", "en", "english"],
                                             ["sat", "1", "en", "english"]]
    assert rows(out / "indic__hi.csv")[1:] == [["नमस्ते", "2", "hi", "indic"]]
    assert "heldout" not in (out / "english__en.csv").read_text(encoding="utf-8")   # held-out parts are not read
    packs = {r["pack_id"]: r for r in csv.DictReader(open(out / "packs.csv", encoding="utf-8"))}
    assert packs["en-b"]["license"] == "cc-by-4.0" and packs["en-a"]["file"] == "english__en.csv"
    assert packs["en-a"]["docs"] == "3" and packs["ind-hi"]["docs"] == "2"          # a null text is a document
    summary = json.loads((out / "r1_summary.json").read_text(encoding="utf-8"))
    assert summary["docs"] == 6 and summary["parts"] == 4 and summary["packs"] == 3
    assert summary["files"]["english__en.csv"]["sha256"] == hashlib.sha256((out / "english__en.csv").read_bytes()).hexdigest()
    assert all(p["path"].startswith("train/") for p in summary["inputs"])


def test_same_input_same_tables(tmp_path, monkeypatch):
    args = setup(tmp_path, monkeypatch)
    one, two = run(monkeypatch, tmp_path, *args, out="out/one"), run(monkeypatch, tmp_path, *args, out="out/two")
    for name in ("english__en.csv", "indic__hi.csv", "packs.csv"):
        assert (one / name).read_bytes() == (two / name).read_bytes()


def test_a_listed_part_that_is_missing_stops_the_run(tmp_path, monkeypatch):
    packs, manifest, approved = setup(tmp_path, monkeypatch)
    (packs / "en-a/Part_2/part-00001.parquet").unlink()
    with pytest.raises(SystemExit, match="part-00001"):
        run(monkeypatch, tmp_path, packs, manifest, approved)


def test_a_changed_part_stops_the_run(tmp_path, monkeypatch):
    packs, manifest, approved = setup(tmp_path, monkeypatch)
    part(packs / "en-b/Part_1/part-00000.parquet", ["the end", "a new row"], "en-b")   # same path, other bytes
    with pytest.raises(SystemExit, match="sha256"):
        run(monkeypatch, tmp_path, packs, manifest, approved)


def test_out_must_be_inside_out_and_empty(tmp_path, monkeypatch):
    args = setup(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="inside the repository's out/"):
        run(monkeypatch, tmp_path, *args, out="elsewhere")
    run(monkeypatch, tmp_path, *args, out="out/r1")
    with pytest.raises(SystemExit, match="not empty"):
        run(monkeypatch, tmp_path, *args, out="out/r1")
