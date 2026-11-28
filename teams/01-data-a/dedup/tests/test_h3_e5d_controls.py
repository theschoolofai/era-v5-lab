"""Unit tests for h3_e5d_controls.py, the controls of E5d's Sanskrit reader sheets: which same-page pairs it takes, how
many, and the checks on its inputs.

The pairs, their texts and their scores are made up. The script runs in-process with its repository root pointed at a
temporary folder.

  python3 -B -m pytest dedup/tests/test_h3_e5d_controls.py
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
import h3_e5d_controls as controls  # noqa: E402

# (doc_id, kind, tr_lang, LaBSE coverage_0.5, BGE-M3 coverage_0.5)
EN = ([("e00", "block", "en", 0.8, 1.0), ("e01", "interleaved", "en", 0.6, 0.6)]          # real; read, not
      + [(f"e{i:02d}", "block", "en", 0.2, 0.7) for i in range(2, 10)]                   # BGE-M3 too high
      + [(f"e{i:02d}", "block", "en", 0.1, 0.2) for i in range(10, 40)])                 # low on both: the pool
HI = ([("h00", "interleaved", "hi", 0.9, 1.0), ("h01", "block", "hi", 0.6, 0.6)]
      + [(f"h{i:02d}", "block", "hi", 0.35, 0.3) for i in range(2, 6)]                   # LaBSE too high
      + [(f"h{i:02d}", "block", "hi", 0.0, 0.5) for i in range(6, 20)])                  # low on both: the pool
ROWS = EN + HI + [("n0", "not_sanskrit", "hi", 0.0, 0.0), ("n1", "not_sanskrit", "hi", 0.0, 0.0)]
REAL = ["e00", "h00"]
READ_NO = ["e01", "h01"]


def write_scores(path, rows, which):
    path.parent.mkdir(parents=True, exist_ok=True)
    pacsv.write_csv(pa.table({"doc_id": [r[0] for r in rows], "kind": [r[1] for r in rows],
                              "tr_lang": [r[2] for r in rows], "head_cosine": [0.5] * len(rows),
                              "coverage_0.5": [r[which] for r in rows], "coverage_0.6": [0.0] * len(rows)}), path)


def setup(root, monkeypatch, labse_rows=ROWS, bge_rows=ROWS, known_rows=ROWS):
    monkeypatch.setattr(controls, "REPO", root)
    pq.write_table(pa.table({"doc_id": [r[0] for r in known_rows],
                             "sa_text": [f"संस्कृतपाठः {r[0]}" for r in known_rows],
                             "tr_text": [f"translation half {r[0]}" for r in known_rows],
                             "tr_lang": [r[2] for r in known_rows], "kind": [r[1] for r in known_rows]}),
                   root / "known_pairs.parquet")
    (root / "real.csv").write_text("doc_id,kind,tr_lang,found_by\n" + "".join(f"{d},,,x\n" for d in REAL))
    write_scores(root / "scores/labse/pair_scores.csv", labse_rows, 3)
    write_scores(root / "scores/bge/pair_scores.csv", bge_rows, 4)


def run(root, *extra, read_no=READ_NO):
    controls.main(["--out", "out/c", "--known-pairs", str(root / "known_pairs.parquet"), "--real",
                   str(root / "real.csv"), "--labse", str(root / "scores/labse/pair_scores.csv"), "--bge",
                   str(root / "scores/bge/pair_scores.csv"), "--not-translations", *read_no, *extra])
    return (pq.read_table(root / "out/c/controls.parquet").to_pylist(),
            json.loads((root / "out/c/controls.json").read_text(encoding="utf-8")))


def test_controls_are_the_read_non_translations_then_pairs_low_on_both(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    rows, summary = run(tmp_path)
    for pair, read, pool in (("sa-en", "e01", {f"e{i:02d}" for i in range(10, 40)}),
                             ("sa-hi", "h01", {f"h{i:02d}" for i in range(6, 20)})):
        mine = [r for r in rows if r["pair"] == pair]
        assert len(mine) == 10 and {r["expected"] for r in mine} == {"no"}
        assert [r["doc_id"] for r in mine if r["source"].startswith("read_not_translation:")] == [read]
        drawn = {r["doc_id"] for r in mine if r["source"].startswith("low_both_encoders:")}
        assert len(drawn) == 9 and drawn <= pool
        assert all(r["source"].endswith(":" + r["doc_id"]) for r in mine)
        assert all(r["text_a"] == f"संस्कृतपाठः {r['doc_id']}" and r["text_b"] == f"translation half {r['doc_id']}"
                   for r in mine)
        assert sorted(summary["pairs"][pair]["unread_doc_ids_to_check"]) == sorted(drawn)
    assert not {"e00", "h00", "n0", "n1"} & {r["doc_id"] for r in rows}


def test_positives_add_the_read_translations_as_yes(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    rows, summary = run(tmp_path, "--positives")
    yes = {(r["pair"], r["doc_id"]) for r in rows if r["expected"] == "yes"}
    assert yes == {("sa-en", "e00"), ("sa-hi", "h00")}
    assert summary["pairs"]["sa-en"]["read_translation"] == 1 and len(rows) == 22


def test_the_seed_fixes_the_draw(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    first = [r["doc_id"] for r in run(tmp_path)[0]]
    assert first == [r["doc_id"] for r in run(tmp_path)[0]]
    assert first != [r["doc_id"] for r in run(tmp_path, "--seed", "5")[0]]


def test_a_short_pool_is_reported(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    rows, summary = run(tmp_path, "--per-pair", "20")
    assert summary["pairs"]["sa-hi"] | {"unread_doc_ids_to_check": None} == {
        "read_not_translation": 1, "low_both_encoders_pool": 14, "low_both_encoders_drawn": 14, "read_translation": 0,
        "shortfall": 5, "unread_doc_ids_to_check": None}
    assert summary["pairs"]["sa-en"]["shortfall"] == 0 and sum(r["pair"] == "sa-hi" for r in rows) == 15


def test_the_summary_holds_ids_and_counts_only(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    run(tmp_path)
    raw = (tmp_path / "out/c/controls.json").read_text(encoding="utf-8")
    assert "translation half" not in raw and "संस्कृत" not in raw
    s = json.loads(raw)
    assert s["rule"]["max_bge"] == 0.5 and s["rule"]["max_labse_below"] == 0.3
    assert set(s["inputs_sha256"]) == {"known_pairs.parquet", "real.csv", "labse/pair_scores.csv",
                                       "bge_m3/pair_scores.csv"}


@pytest.mark.parametrize("change, message", [
    ({"bge_rows": ROWS[:-1]}, "must score the same pairs"),
    ({"known_rows": ROWS[1:]}, "the scores name pairs that"),
    ({"read_no": ["e00"]}, "listed both as a real translation and as read not a translation"),
    ({"read_no": ["zz"]}, "a read non-translation is not among the scored pairs")])
def test_bad_inputs_are_refused(tmp_path, monkeypatch, change, message):
    read_no = change.pop("read_no", READ_NO)
    setup(tmp_path, monkeypatch, **change)
    with pytest.raises(SystemExit, match=message):
        run(tmp_path, read_no=read_no)


def test_out_must_be_inside_out(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="--out must be inside out/"):
        controls.main(["--out", "elsewhere", "--known-pairs", str(tmp_path / "known_pairs.parquet"), "--real",
                       str(tmp_path / "real.csv"), "--labse", str(tmp_path / "scores/labse/pair_scores.csv"),
                       "--bge", str(tmp_path / "scores/bge/pair_scores.csv")])


def test_the_sheet_generator_can_read_the_file(tmp_path, monkeypatch):
    pytest.importorskip("torch")   # h3_e5d_sheets.py imports h3.py
    import h3_e5d_sheets as sheets
    setup(tmp_path, monkeypatch)
    run(tmp_path)
    t = pq.read_table(tmp_path / "out/c/controls.parquet")
    assert set(sheets.CONTROL_COLUMNS) <= set(t.column_names)
    assert set(t.column("pair").to_pylist()) == {"sa-en", "sa-hi"}
