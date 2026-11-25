"""Unit tests for h3_harm_check.py, the H3 harm check with planted cases: a layout that passes, and each way it must fail.

Each test writes one layout's outputs by hand, as run_h3_harm.sh's h3.py and dedup.py runs would leave them
(h3_summary.json, h3_docs.parquet, h3_matches.csv, h3_candidates.csv, and per dedup.py mode dedup_summary.json,
remove_list.csv, dedup_log.jsonl and h3_pairs.csv), with a plants.csv and a gold folder. Every ID is made up. The script
runs in-process with its repository root pointed at a temporary folder.

  python3 -B -m pytest dedup/tests/test_h3_harm_check.py
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
import h3_harm_check as check  # noqa: E402

SA, HI, EN = "ind-sa-fw2", "ind-hi-fw2", "en-fineweb-edu"
# (pack, split, doc_id, lang): the planted documents of the sa-held layout, and three real ones
DOCS = [(SA, "heldout", "plant-p1-sa-b001-sa", "sa"), (EN, "train", "plant-p1-sa-b001-en", "en"),
        (SA, "heldout", "plant-p1-sa-b002-sa", "sa"), (EN, "train", "plant-p1-sa-b002-en", "en"),
        (HI, "train", "plant-p3-sa-b007-hi", "hi"), (EN, "train", "plant-p3-sa-b007-en", "en"),
        (SA, "heldout", "plant-p2-sa-d1-sa", "sa"), (EN, "train", "plant-p2-sa-d1-en", "en"),
        (SA, "heldout", "d1", "sa"), (EN, "train", "g1", "en"), (HI, "train", "r2", "hi")]
ROW = {d[2]: i for i, d in enumerate(DOCS)}
PLANTS = [("p1_heldout_train", "sa-en", 1, "", 0, 1), ("p1_heldout_train", "sa-en", 2, "", 2, 3),
          ("p3_train_train", "hi-en", 7, "", 4, 5), ("p2_real_web", "sa-en", None, "d1", 6, 7)]
H3_LOG = {"removed_pack_id": EN, "removed_split": "train", "removed_id": "plant-p1-sa-b001-en", "rule": "H3"}


def side(doc):
    pack, split, doc_id, lang = DOCS[ROW[doc]]
    return {"pack": pack, "split": split, "part": "x/part-plant.parquet", "row_in_part": ROW[doc], "doc_id": doc_id,
            "lang": lang}


def write_matches(path, pairs):
    """h3_matches.csv rows for [(doc a, doc b, coverage)], in MATCHES_HEADER's columns."""
    cols = {k: [] for k in ("pack_id_a", "split_a", "part_a", "row_in_part_a", "doc_id_a", "pack_id_b", "split_b",
                            "part_b", "row_in_part_b", "doc_id_b", "lang_a", "lang_b", "coverage")}
    for a, b, cov in pairs:
        for s, d in (("a", side(a)), ("b", side(b))):
            for k in ("pack", "split", "part", "row_in_part", "doc_id", "lang"):
                cols[f"{'pack_id' if k == 'pack' else k}_{s}"].append(d[k])
        cols["coverage"].append(cov)
    pacsv.write_csv(pa.table(cols), path)


def write_pairs(path, pairs):
    """dedup.py's h3_pairs.csv rows for [(doc a, doc b, coverage, outcome)]."""
    cols = {k: [] for k in ("pack_id_a", "split_a", "doc_id_a", "pack_id_b", "split_b", "doc_id_b", "coverage",
                            "outcome")}
    for a, b, cov, outcome in pairs:
        for s, d in (("a", side(a)), ("b", side(b))):
            cols[f"pack_id_{s}"].append(d["pack"])
            cols[f"split_{s}"].append(d["split"])
            cols[f"doc_id_{s}"].append(d["doc_id"])
        cols["coverage"].append(cov)
        cols["outcome"].append(outcome)
    pacsv.write_csv(pa.table(cols), path)


def build(root, monkeypatch, log=(H3_LOG,), harm="pass", report_list=None, not_verified=0, matches=None):
    """One sa-held layout that passes unless an argument changes it."""
    monkeypatch.setattr(check, "REPO", root)
    out = root / "out/h3harm"
    run = out / "sa-held"
    for d in ("h3", "dedup_noh3", "dedup_report", "dedup_remove"):
        (run / d).mkdir(parents=True)
    pacsv.write_csv(pa.table({
        "layout": ["sa"] * 4, "case": [p[0] for p in PLANTS], "language_pair": [p[1] for p in PLANTS],
        "block": pa.array([p[2] for p in PLANTS], pa.int64()), "source_doc_id": [p[3] for p in PLANTS],
        **{f"{s}_{k}": [DOCS[p[4 if s == "a" else 5]][i] for p in PLANTS]
           for s in "ab" for k, i in (("pack", 0), ("split", 1), ("doc_id", 2), ("lang", 3))},
        "expected": ["removed_if_qualifying", "removed_if_qualifying", "never_removed", "removed_if_qualifying"]}),
        out / "plants.csv")
    (run / "h3/h3_summary.json").write_text(json.dumps({"status": "complete", "verified": 6, "qualifying": 2,
                                                        "not_verified_over_max_verify": not_verified}))
    pq.write_table(pa.table({"row": list(range(len(DOCS))), "doc_id": [d[2] for d in DOCS],
                             "pack": [d[0] for d in DOCS]}), run / "h3/h3_docs.parquet")
    qualifying = [("plant-p1-sa-b001-sa", "plant-p1-sa-b001-en", 0.95), ("plant-p3-sa-b007-hi", "plant-p3-sa-b007-en",
                                                                         0.9)]
    write_matches(run / "h3/h3_matches.csv", qualifying + list(matches or []))
    cand = qualifying + [("plant-p1-sa-b002-sa", "plant-p1-sa-b002-en", 0.4), ("d1", "g1", 0.2),
                         ("plant-p2-sa-d1-sa", "plant-p2-sa-d1-en", 0.3)] + list(matches or [])
    pacsv.write_csv(pa.table({"row_a": [ROW[a] for a, _, _ in cand], "row_b": [ROW[b] for _, b, _ in cand],
                              "lang_a": [side(a)["lang"] for a, _, _ in cand],
                              "lang_b": [side(b)["lang"] for _, b, _ in cand],
                              "coverage": [c for _, _, c in cand], "qualifies": [c >= 0.6 for _, _, c in cand]}),
                    run / "h3/h3_candidates.csv")
    header = "pack_id,split,part,row_in_part,doc_id\n"
    (run / "dedup_noh3/remove_list.csv").write_text(header)
    (run / "dedup_report/remove_list.csv").write_text(report_list if report_list is not None else header)
    (run / "dedup_remove/remove_list.csv").write_text(header)
    (run / "dedup_remove/dedup_log.jsonl").write_text("".join(json.dumps(e) + "\n" for e in log))
    write_pairs(run / "dedup_remove/h3_pairs.csv", [("plant-p1-sa-b001-sa", "plant-p1-sa-b001-en", 0.95, "removed"),
                                                     ("plant-p3-sa-b007-hi", "plant-p3-sa-b007-en", 0.9,
                                                      "reported_train_train")])
    for m in check.MODES:
        (run / f"dedup_{m}/dedup_summary.json").write_text(json.dumps({"harm_check": {
            "status": harm, "gold_ids_in_input": 1, "gold_removed": 0 if harm == "pass" else 1,
            "gold_removed_ids": [] if harm == "pass" else [f"{EN}:g1"]}}))
    (root / "gold").mkdir()
    (root / "gold" / f"{EN}_gold.csv").write_text("doc_id,reader_1,reader_2\ng1,x,y\n")


def run_check(root):
    code = check.main(["--out", "out/h3harm", "--gold", "gold"])
    return code, json.loads((root / "out/h3harm/harm_cases.json").read_text())


def test_a_layout_that_removes_the_qualifying_plant_passes(tmp_path, monkeypatch):
    build(tmp_path, monkeypatch)
    code, result = run_check(tmp_path)
    r = result["layouts"]["sa-held"]
    assert code == 0 and result["status"] == "pass" and r["failures"] == []
    assert r["removal_tested"] == {"sa-en": {"planted": 2, "removed": 1}}
    assert r["cases"]["p1_heldout_train"] == {"planted": 2, "qualifying": 1, "removed_by_h3": 1, "ok": 2}
    assert r["cases"]["p3_train_train"] == {"planted": 1, "qualifying": 1, "removed_by_h3": 0, "ok": 1}
    pairs = {p["b"]: p for p in r["planted_pairs"]}
    assert pairs[f"{EN}:plant-p1-sa-b001-en"]["outcome"] == "removed"
    assert pairs[f"{EN}:plant-p3-sa-b007-en"]["outcome"] == "reported_train_train"
    assert pairs[f"{EN}:plant-p1-sa-b002-en"]["coverage"] == 0.4                  # verified, below the cut
    assert pairs[f"{EN}:plant-p1-sa-b001-en"]["coverage"] == 0.95
    assert r["margin"]["sa-en"] == {"verified": 1, "qualifying": 0, "highest_coverage": 0.2, "highest_with_gold": 0.2}


def test_a_web_pair_removed_through_its_original_page_passes(tmp_path, monkeypatch):
    via_page = ("d1", "plant-p2-sa-d1-en", 0.7)                    # the held-out page qualifies with the train half
    build(tmp_path, monkeypatch, matches=[via_page],
          log=(H3_LOG, {**H3_LOG, "removed_id": "plant-p2-sa-d1-en"}))
    code, result = run_check(tmp_path)
    p2 = next(p for p in result["layouts"]["sa-held"]["planted_pairs"] if p["case"] == "p2_real_web")
    assert code == 0 and p2["qualifies"] is False and p2["train_side_targeted"] and p2["removed_by_h3"]


def test_a_real_h3_removal_is_listed(tmp_path, monkeypatch):
    build(tmp_path, monkeypatch, log=(H3_LOG, {**H3_LOG, "removed_pack_id": HI, "removed_id": "r2"}))
    code, result = run_check(tmp_path)
    assert code == 0 and result["layouts"]["sa-held"]["h3_removed_real_documents"] == [f"{HI}:r2"]


@pytest.mark.parametrize("change, message", [
    ({"log": ()}, "sa-en: no p1 pair removed"),                                       # the qualifying plant stays
    ({"log": ()}, "1 planted pairs not as expected"),
    ({"log": (H3_LOG, {**H3_LOG, "removed_id": "plant-p1-sa-b002-en"})}, "1 planted pairs not as expected"),
    ({"log": (H3_LOG, {**H3_LOG, "removed_id": "plant-p3-sa-b007-en"})}, "1 planted pairs not as expected"),
    ({"log": (H3_LOG, {**H3_LOG, "removed_pack_id": SA, "removed_split": "heldout",
                       "removed_id": "plant-p1-sa-b001-sa"})}, "H3 removed 1 held-out documents"),
    ({"harm": "fail"}, "harm check 'fail': 1 gold documents removed"),
    ({"report_list": "pack_id,split,part,row_in_part,doc_id\nx,train,p,0,y\n"}, "h3.remove false changed"),
    ({"not_verified": 5}, "left 5 candidates unverified")])
def test_each_failure_fails_the_check(tmp_path, monkeypatch, change, message):
    build(tmp_path, monkeypatch, **change)
    code, result = run_check(tmp_path)
    r = result["layouts"]["sa-held"]
    assert code == 1 and result["status"] == "fail" and any(message in f for f in r["failures"])


def test_out_must_be_inside_out(tmp_path, monkeypatch):
    build(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="--out must be inside out/"):
        check.main(["--out", "elsewhere"])
