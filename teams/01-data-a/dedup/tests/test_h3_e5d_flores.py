"""Unit tests for h3_e5d_flores.py, the FLORES test data for E5d's sheets: the packs and controls it builds, and the
check of the sheets against the known answers.

The "FLORES" files here are made up, a numbered sentence per line in each script; none is FLORES text. The end-to-end
test writes h3.py output folders by hand from the built packs (no model), runs h3_e5d_sheets.py on them and checks
its sheets. Everything runs in-process with the repository root pointed at a temporary folder.

  python3 -B -m pytest dedup/tests/test_h3_e5d_flores.py
"""
import json
import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pa = pytest.importorskip("pyarrow")
import pyarrow.csv as pacsv  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h3_e5d_flores as flores  # noqa: E402

LINES = 32   # 4 blocks of 8
WORDS = {"en": "English line {i} is long enough to keep.", "hi": "हिंदी पंक्ति {i} रखने के लिए काफी लंबी है।",
         "sa": "संस्कृतवाक्यम् {i} रक्षितुं पर्याप्तं दीर्घम् अस्ति।", "or": "ଓଡ଼ିଆ ଧାଡ଼ି {i} ରଖିବା ପାଇଁ ଯଥେଷ୍ଟ ଲମ୍ବା।"}


def flores_dir(tmp_path, short=None):
    d = tmp_path / "flores"
    d.mkdir()
    for lang, code in flores.LANGS.items():
        n = LINES - 1 if lang == short else LINES
        (d / f"{code}.txt").write_text("\n".join(WORDS[lang].format(i=i) for i in range(n)) + "\n", encoding="utf-8")
    return d


def build(tmp_path, monkeypatch, **kw):
    monkeypatch.setattr(flores, "REPO", tmp_path)
    flores.main(["build", "--flores-dir", str(flores_dir(tmp_path, **kw)), "--out", "out/fl"])
    return tmp_path / "out/fl"


def block(lang, i):
    return "\n".join(WORDS[lang].format(i=k) for k in range(8 * i, 8 * i + 8))


def test_build_writes_one_pack_per_language_in_h3s_raw_layout(tmp_path, monkeypatch):
    out = build(tmp_path, monkeypatch)
    en_held = pq.read_table(out / "inputs/flores-en/Heldout/part-00000.parquet").to_pylist()
    en_train = pq.read_table(out / "inputs/flores-en/Part_1/part-00000.parquet").to_pylist()
    assert [x["doc_id"] for x in en_held] == ["block-001"] and len(en_train) == 3
    assert en_held[0]["text"] == block("en", 0) and en_held[0]["pack_id"] == "flores-en"
    sa = pq.read_table(out / "inputs/flores-sa/Part_1/part-00000.parquet").to_pylist()
    assert [x["doc_id"] for x in sa] == ["block-001", "block-002", "block-003", "block-004"]
    assert sa[2]["text"] == block("sa", 2) and not (out / "inputs/flores-sa/Heldout").exists()
    summary = json.loads((out / "flores_build.json").read_text())
    assert summary["blocks"] == 4 and summary["packs"]["flores-en"] == {"train": 3, "heldout": 1}
    assert "English line" not in json.dumps(summary)


def test_controls_pair_each_block_with_another(tmp_path, monkeypatch):
    out = build(tmp_path, monkeypatch)
    rows = pq.read_table(out / "controls.parquet").to_pylist()
    assert len(rows) == 4 * len(flores.PAIRS)
    sa_en = [x for x in rows if x["pair"] == "sa-en"]
    assert [x["text_a"] for x in sa_en] == [block("sa", i) for i in range(4)]
    assert [x["text_b"] for x in sa_en] == [block("en", (i + 2) % 4) for i in range(4)]
    assert {x["expected"] for x in rows} == {"no"}


def test_files_of_unequal_length_are_refused(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="same number of lines"):
        build(tmp_path, monkeypatch, short="or")


def test_build_reads_flores_plus_jsonl_in_id_order(tmp_path, monkeypatch):
    monkeypatch.setattr(flores, "REPO", tmp_path)
    d = tmp_path / "flores_plus" / "devtest"
    d.mkdir(parents=True)
    order = list(range(LINES))[::-1]                              # records out of id order, extra fields ignored
    for lang, code in flores.LANGS.items():
        (d / f"{code}.jsonl").write_text("".join(
            json.dumps({"id": i, "iso_639_3": code[:3], "text": WORDS[lang].format(i=i), "url": "https://x.org/"},
                       ensure_ascii=False) + "\n" for i in order), encoding="utf-8")
    flores.main(["build", "--flores-dir", str(tmp_path / "flores_plus"), "--out", "out/fl"])
    sa = pq.read_table(tmp_path / "out/fl/inputs/flores-sa/Part_1/part-00000.parquet").to_pylist()
    assert [x["text"] for x in sa] == [block("sa", i) for i in range(4)]
    summary = json.loads((tmp_path / "out/fl/flores_build.json").read_text())
    assert set(summary["flores_sha256"]) == {f"{c}.jsonl" for c in flores.LANGS.values()}


def test_a_missing_language_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(flores, "REPO", tmp_path)
    d = flores_dir(tmp_path)
    (d / "ory_Orya.txt").unlink()
    with pytest.raises(SystemExit, match="neither ory_Orya.txt nor devtest/ory_Orya.jsonl"):
        flores.main(["build", "--flores-dir", str(d), "--out", "out/fl"])


def write_sheets(root, key, sheet_rows, columns=None):
    (root / "key").mkdir(parents=True)
    (root / "sheets").mkdir(parents=True)
    pacsv.write_csv(pa.table(key), root / "key/sa-en_key.csv")
    for r in (1, 2):
        t = pa.table(sheet_rows) if columns is None else pa.table(columns)
        pacsv.write_csv(t, root / "sheets" / f"sa-en_reader{r}.csv")


KEY = {"item": ["sa-en-001", "sa-en-002", "sa-en-003", "sa-en-004"],
       "source": ["candidate", "candidate", "candidate", "control"],
       "band": ["0.75-1.00", "0.30-0.45", "0.60-0.75", "control"],
       "drawn_for": ["labse", "labse", "labse", None], "expected": [None, None, None, "no"],
       "doc_id_a": ["block-001", "block-002", "block-003", None],
       "doc_id_b": ["block-001", "block-002", "block-004", None],
       "coverage_labse": [0.8, 0.4, 0.7, None]}
SHEET = {"item": ["sa-en-003", "sa-en-001", "sa-en-004", "sa-en-002"], "text_1": ["a\nb", "c", "d", "e"],
         "text_2": ["f", "g", "h", "i"], "translation": [""] * 4, "note": [""] * 4}


def test_check_counts_misses_and_false_matches(tmp_path, monkeypatch):
    monkeypatch.setattr(flores, "REPO", tmp_path)
    write_sheets(tmp_path / "out/s", KEY, SHEET)
    assert flores.main(["check", "--sheets", "out/s", "--out", "out/fl"]) == 0
    result = json.loads((tmp_path / "out/fl/flores_check.json").read_text())
    p = result["pairs"]["sa-en"]
    assert result["status"] == "ok" and p["both_sides_of_threshold"]
    assert (p["candidates"], p["translations"], p["controls"]) == (3, 2, 1)
    assert p["translations_below_threshold"] == 1 and p["non_translations_at_or_above_threshold"] == 1
    truth = pacsv.read_csv(tmp_path / "out/fl/flores_truth.csv").to_pylist()
    assert {x["item"]: x["translation"] for x in truth} == {"sa-en-001": "yes", "sa-en-002": "yes",
                                                             "sa-en-003": "no", "sa-en-004": "no"}


@pytest.mark.parametrize("sheet, columns, message", [
    ({**SHEET, "text_1": ["block-002 leaked", "c", "d", "e"]}, None, "holds a doc_id"),
    (None, {**SHEET, "coverage": [0.1] * 4}, "columns"),
    ({**SHEET, "item": ["sa-en-003", "sa-en-001", "sa-en-004", "sa-en-009"]}, None, "items differ")])
def test_check_fails_on_a_sheet_that_is_not_blind_or_not_the_keys(tmp_path, monkeypatch, sheet, columns, message):
    monkeypatch.setattr(flores, "REPO", tmp_path)
    write_sheets(tmp_path / "out/s", KEY, sheet, columns)
    assert flores.main(["check", "--sheets", "out/s", "--out", "out/fl"]) == 1
    result = json.loads((tmp_path / "out/fl/flores_check.json").read_text())
    assert result["status"] == "fail" and any(message in f for f in result["failures"])


def test_end_to_end_with_the_sheet_generator(tmp_path, monkeypatch):
    pytest.importorskip("torch")   # h3_e5d_sheets.py reads documents with h3.py's reader
    import h3
    import h3_e5d_sheets as sheets
    out = build(tmp_path, monkeypatch)
    monkeypatch.setattr(sheets, "REPO", tmp_path)
    docs = []
    for path in sorted((out / "inputs").rglob("*.parquet")):
        t = pq.read_table(path).to_pylist()
        rel = path.relative_to(out / "inputs").as_posix()
        for r, x in enumerate(t):
            docs.append({"pack": x["pack_id"], "doc_id": x["doc_id"], "lang": x["pack_id"][len("flores-"):],
                         "split": "heldout" if "/Heldout/" in rel else "train", "part": rel, "row_in_part": r,
                         "chars": len(x["text"])})
    row = {(x["lang"], x["doc_id"]): i for i, x in enumerate(docs)}
    run = tmp_path / "out/fl/h3_fake"
    run.mkdir()
    pq.write_table(pa.table({"row": list(range(len(docs))), "id": [f"{x['pack']}-{x['doc_id']}" for x in docs],
                             **{c: [x[c] for x in docs] for c in ("doc_id", "pack", "lang", "split", "part",
                                                                   "row_in_part", "chars")}}),
                   run / "h3_docs.parquet")
    ids = [f"block-{i:03d}" for i in range(1, 5)]
    pairs = [(x, a, y, b, cov) for x, y in flores.PAIRS for i, a in enumerate(ids)
             for b, cov in ((a, 0.9 - 0.1 * i), (ids[(i + 1) % 4], 0.35 + 0.05 * i))]
    pick = lambda p, s: docs[row[(p[0], p[1])] if s == "a" else row[(p[2], p[3])]]
    cols = {"row_a": [row[(p[0], p[1])] for p in pairs], "row_b": [row[(p[2], p[3])] for p in pairs]}
    for s in "ab":
        cols[f"id_{s}"] = [f"{pick(p, s)['pack']}-{pick(p, s)['doc_id']}" for p in pairs]
        cols[f"pack_{s}"] = [pick(p, s)["pack"] for p in pairs]
        cols[f"lang_{s}"] = [pick(p, s)["lang"] for p in pairs]
        cols[f"split_{s}"] = [pick(p, s)["split"] for p in pairs]
    n = len(pairs)
    h3.write_csv(run / "h3_candidates.csv", {
        **cols, "found_by": ["embedding"] * n, "doc_cosine": [0.7] * n, "length_ratio": [1.0] * n,
        "numbers_jaccard": [None] * n, "latin_share": [None] * n, "sentences_a": [8] * n, "sentences_b": [8] * n,
        "aligned": [round(8 * p[4]) for p in pairs], "coverage": [p[4] for p in pairs],
        "mean_sentence_cosine": [0.8] * n, "qualifies": [p[4] >= 0.6 for p in pairs]})
    (run / "h3_summary.json").write_text(json.dumps({"status": "complete"}))
    cfg = tmp_path / "sheets.json"
    cfg.write_text(json.dumps({"runs": {"labse": "out/fl/h3_fake"}, "inputs": "out/fl/inputs",
                               "controls": "out/fl/controls.parquet", "out": "out/fl/sheets",
                               "pairs": [list(p) for p in flores.PAIRS], "per_band": 4, "n_controls": 2,
                               "readers": 2, "seed": 3}))
    sheets.main(["--config", str(cfg)])
    assert flores.main(["check", "--sheets", "out/fl/sheets", "--out", "out/fl"]) == 0
    result = json.loads((out / "flores_check.json").read_text())
    for name in ("sa-en", "sa-hi", "hi-en", "or-en"):
        p = result["pairs"][name]
        assert p["candidates"] == 8 and p["translations"] == 4 and p["controls"] == 2
        assert p["both_sides_of_threshold"]
