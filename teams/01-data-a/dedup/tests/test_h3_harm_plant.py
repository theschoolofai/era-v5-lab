"""Unit tests for h3_harm_plant.py, the planted cases of H3's harm check: which pairs each layout gets, where their
documents go, and the checks on its inputs.

The "FLORES+" files and the same-page pairs here are made up; none is real text. The script runs in-process with its
repository root pointed at a temporary folder.

  python3 -B -m pytest dedup/tests/test_h3_harm_plant.py
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
import h3_harm_plant as plant  # noqa: E402

LINES = 80   # 10 blocks of 8; the plants use 8
WORDS = {"en": "English line {i} is long enough to keep.", "hi": "हिंदी पंक्ति {i} रखने के लिए काफी लंबी है।",
         "sa": "संस्कृतवाक्यम् {i} रक्षितुं पर्याप्तं दीर्घम् अस्ति।"}
P1_PAIRS = {"sa": {"sa-en", "sa-hi"}, "hi": {"sa-hi", "hi-en"}, "en": {"sa-en", "hi-en"}}
P3_PAIR = {"sa": "hi-en", "hi": "sa-en", "en": "sa-hi"}


def block(lang, b):
    """Block number b (from 1) of the made-up FLORES+ file of lang."""
    return "\n".join(WORDS[lang].format(i=k) for k in range((b - 1) * 8, b * 8))


def setup(root, monkeypatch, layouts=plant.HELD, shift_hi=False, real_ids=("d1", "d2")):
    monkeypatch.setattr(plant, "REPO", root)
    for held in layouts:
        for lang, pack in plant.PACK.items():
            split = "heldout" if lang == held else "train"
            (root / "out/h3harm" / f"{held}-held" / "inputs" / split / pack).mkdir(parents=True, exist_ok=True)
    d = root / "flores_plus" / "devtest"
    d.mkdir(parents=True)
    for lang in ("en", "hi", "sa"):
        ids = range(1, LINES + 1) if (shift_hi and lang == "hi") else range(LINES)
        (d / f"{plant.flores.LANGS[lang]}.jsonl").write_text("".join(
            json.dumps({"id": i, "text": WORDS[lang].format(i=i - (lang == "hi" and shift_hi))}, ensure_ascii=False)
            + "\n" for i in ids), encoding="utf-8")
    pq.write_table(pa.table({"doc_id": ["d1", "d2", "d3"],
                             "sa_text": ["संस्कृतपाठः प्रथमः अत्र अस्ति।\n" * 4, "संस्कृतपाठः द्वितीयः अत्र अस्ति।\n" * 4,
                                         "संस्कृतपाठः तृतीयः।"],
                             "tr_text": ["The first translation is here.\n" * 4, "दूसरा अनुवाद यहाँ है।\n" * 4, "x"],
                             "tr_lang": ["en", "hi", "en"], "kind": ["block", "interleaved", "block"]}),
                   root / "known_pairs.parquet")
    (root / "real.csv").write_text("doc_id,kind,tr_lang,found_by\n" + "".join(f"{d},,,test\n" for d in real_ids),
                                   encoding="utf-8")


def run(root):
    plant.main(["--out", "out/h3harm", "--flores-dir", str(root / "flores_plus"), "--known-pairs",
                str(root / "known_pairs.parquet"), "--real", str(root / "real.csv")])
    return pacsv.read_csv(root / "out/h3harm/plants.csv",
                          convert_options=pacsv.ConvertOptions(strings_can_be_null=True)).to_pylist()


def part(root, held, split, pack):
    return pq.read_table(root / "out/h3harm" / f"{held}-held" / "inputs" / split / pack / plant.PLANT_PART).to_pylist()


def test_each_layout_gets_its_cases(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    rows = run(tmp_path)
    for held in plant.HELD:
        mine = [r for r in rows if r["layout"] == held]
        p1 = [r for r in mine if r["case"] == "p1_heldout_train"]
        p3 = [r for r in mine if r["case"] == "p3_train_train"]
        p2 = [r for r in mine if r["case"] == "p2_real_web"]
        assert {r["language_pair"] for r in p1} == P1_PAIRS[held] and len(p1) == 6
        assert {r["language_pair"] for r in p3} == {P3_PAIR[held]} and len(p3) == 2
        assert all(r["a_split"] == "heldout" and r["a_lang"] == held and r["b_split"] == "train" for r in p1)
        assert all(r["a_split"] == r["b_split"] == "train" and held not in (r["a_lang"], r["b_lang"]) for r in p3)
        assert {r["expected"] for r in p1} == {"removed_if_qualifying"}
        assert {r["expected"] for r in p3} == {"never_removed"}
        assert len(p2) == (2 if held == "sa" else 0)


def test_the_real_web_pairs_put_the_sanskrit_half_in_held_out(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    rows = [r for r in run(tmp_path) if r["case"] == "p2_real_web"]
    assert {(r["source_doc_id"], r["language_pair"], r["b_pack"]) for r in rows} == {
        ("d1", "sa-en", "en-fineweb-edu"), ("d2", "sa-hi", "ind-hi-fw2")}
    held = {r["doc_id"]: r["text"] for r in part(tmp_path, "sa", "heldout", "ind-sa-fw2")}
    en = {r["doc_id"]: r["text"] for r in part(tmp_path, "sa", "train", "en-fineweb-edu")}
    assert held["plant-p2-sa-d1-sa"].startswith("संस्कृतपाठः प्रथमः")
    assert en["plant-p2-sa-d1-en"].startswith("The first translation")


def test_planted_documents_are_the_flores_blocks_in_their_packs(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    rows = run(tmp_path)
    for r in (r for r in rows if r["case"] != "p2_real_web"):
        for s in "ab":
            docs = {d["doc_id"]: d for d in part(tmp_path, r["layout"], r[f"{s}_split"], r[f"{s}_pack"])}
            d = docs[r[f"{s}_doc_id"]]
            assert d["text"] == block(r[f"{s}_lang"], r["block"])
            assert d["pack_id"] == r[f"{s}_pack"] and d["lang_label"] == r[f"{s}_lang"]


def test_blocks_are_distinct_within_a_layout_and_ids_are_marked(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    rows = run(tmp_path)
    for held in plant.HELD:
        blocks = [r["block"] for r in rows if r["layout"] == held and r["block"] is not None]
        assert len(blocks) == len(set(blocks)) == 8
        for split in ("train", "heldout"):
            for pack in plant.PACK.values():
                f = tmp_path / "out/h3harm" / f"{held}-held" / "inputs" / split / pack / plant.PLANT_PART
                if f.is_file():
                    ids = [d["doc_id"] for d in pq.read_table(f).to_pylist()]
                    assert len(ids) == len(set(ids)) and all(i.startswith("plant-") for i in ids)


def test_the_summary_holds_counts_and_hashes_only(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    run(tmp_path)
    raw = (tmp_path / "out/h3harm/plants.json").read_text(encoding="utf-8")
    assert "English line" not in raw and "translation is here" not in raw
    summary = json.loads(raw)
    assert summary["pairs"]["sa-held"] == {"p1_heldout_train": 6, "p2_real_web": 2, "p3_train_train": 2}
    assert set(summary["inputs_sha256"]) == {"eng_Latn.jsonl", "hin_Deva.jsonl", "san_Deva.jsonl",
                                             "known_pairs.parquet", "real.csv"}


def test_a_real_translation_missing_from_the_known_pairs_is_refused(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, real_ids=("d1", "d9"))
    with pytest.raises(SystemExit, match="names 1 doc_ids that"):
        run(tmp_path)


def test_flores_with_different_sentence_ids_is_refused(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, shift_hi=True)
    with pytest.raises(SystemExit, match="hin_Deva and eng_Latn hold different sentence ids"):
        run(tmp_path)


def test_a_missing_layout_is_refused(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, layouts=("sa", "hi"))
    with pytest.raises(SystemExit, match="run run_h3_harm.sh's layout step first"):
        run(tmp_path)


def test_out_must_be_inside_out(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="--out must be inside out/"):
        plant.main(["--out", "elsewhere", "--flores-dir", str(tmp_path / "flores_plus"), "--known-pairs",
                    str(tmp_path / "known_pairs.parquet"), "--real", str(tmp_path / "real.csv")])
