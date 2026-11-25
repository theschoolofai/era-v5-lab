"""Unit tests for h3_e5d_sheets.py, E5d's blind reader sheets: what a sheet shows and hides, how pairs are drawn on
both sides of the threshold, how two encoders' candidates are pooled, the controls, and the checks that stop a run.

Every text here is made up; none comes from a pack. Each test builds a small input folder in h3.py's raw layout and
two h3.py output folders by hand (h3_docs.parquet, h3_candidates.csv, h3_summary.json), so no model is needed. The
script runs in-process with its repository root pointed at a temporary folder, as in test_h3.py.

  python3 -B -m pytest dedup/tests/test_h3_e5d_sheets.py
"""
import json
import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pa = pytest.importorskip("pyarrow")
pytest.importorskip("torch")   # h3_e5d_sheets.py reads documents with h3.py's reader
import pyarrow.csv as pacsv  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h3  # noqa: E402
import h3_e5d_sheets as sheets  # noqa: E402
from h3_signals import split_sentences  # noqa: E402

DEVANAGARI = "कखगघचछजझटठडढतथदधनपफबभमयरलवशसह"
N = 12   # documents per language
PACKS = {"sa": "ind-sa-x", "hi": "ind-hi-x", "en": "en-x"}


def sentence(lang, d, k):
    if lang == "en":
        return f"English sentence {k} of document {d} says something new."
    w = DEVANAGARI[d % len(DEVANAGARI)] + "ा" + DEVANAGARI[k % len(DEVANAGARI)]
    return f"{w} {w}{w} {'वाक्य' if lang == 'hi' else 'वाक्यम्'} {k} लेख {d} अस्ति।"


def doc_text(lang, d):
    k = 20 if (lang, d) == ("en", 0) else 5                       # en document 0 is longer than max_sentences
    return "\n".join([sentence(lang, d, i) for i in range(k)] + ["Menu"])   # "Menu" is too short: never shown


def doc_id(lang, d):
    return f"{lang}-doc-{d:02d}"


def build_inputs(root):
    """inputs/<pack>/Part_1/ and, for English documents 0-2, inputs/en-x/Heldout/; returns the documents in order."""
    docs = []
    for lang, pack in PACKS.items():
        groups = [("Heldout", range(3)), ("Part_1", range(3, N))] if lang == "en" else [("Part_1", range(N))]
        for folder, ds in groups:
            part = f"{pack}/{folder}/part-00000.parquet"
            (root / "inputs" / pack / folder).mkdir(parents=True, exist_ok=True)
            texts = [doc_text(lang, d) for d in ds]
            pq.write_table(pa.table({"pack_id": [pack] * len(ds), "doc_id": [doc_id(lang, d) for d in ds],
                                     "text": texts}), root / "inputs" / part)
            for r, (d, t) in enumerate(zip(ds, texts)):
                docs.append({"lang": lang, "d": d, "pack": pack, "doc_id": doc_id(lang, d), "part": part,
                             "row_in_part": r, "chars": len(t), "split": "heldout" if folder == "Heldout" else "train",
                             "text": t})
    return docs


SCORED = {"sentence_min_chars": 20, "max_sentences": 16}   # h3.py's defaults


def write_run(root, name, docs, pairs, reverse_docs=False, status="complete", sentences=SCORED):
    """An h3.py output folder: docs (in reverse order if reverse_docs) and pairs [(lang_a, d_a, lang_b, d_b, cov)]."""
    folder = root / "out" / "runs" / name
    folder.mkdir(parents=True, exist_ok=True)
    order = docs[::-1] if reverse_docs else docs
    row = {(x["lang"], x["d"]): i for i, x in enumerate(order)}
    pq.write_table(pa.table({"row": list(range(len(order))), "id": [f"{x['pack']}-{x['doc_id']}" for x in order],
                             "doc_id": [x["doc_id"] for x in order], "pack": [x["pack"] for x in order],
                             "lang": [x["lang"] for x in order], "split": [x["split"] for x in order],
                             "part": [x["part"] for x in order], "row_in_part": [x["row_in_part"] for x in order],
                             "chars": [x["chars"] for x in order], "sentences": [5] * len(order)}),
                   folder / "h3_docs.parquet")
    side = lambda s: [order[row[(p[0], p[1])] if s == "a" else row[(p[2], p[3])]] for p in pairs]
    A, B = side("a"), side("b")
    cov = [p[4] for p in pairs]
    h3.write_csv(folder / "h3_candidates.csv", {
        "row_a": [row[(p[0], p[1])] for p in pairs], "row_b": [row[(p[2], p[3])] for p in pairs],
        "id_a": [f"{x['pack']}-{x['doc_id']}" for x in A], "id_b": [f"{x['pack']}-{x['doc_id']}" for x in B],
        "pack_a": [x["pack"] for x in A], "pack_b": [x["pack"] for x in B],
        "lang_a": [x["lang"] for x in A], "lang_b": [x["lang"] for x in B],
        "split_a": [x["split"] for x in A], "split_b": [x["split"] for x in B],
        "found_by": ["embedding"] * len(pairs), "doc_cosine": [0.5 + c / 2 for c in cov],
        "length_ratio": [1.1] * len(pairs), "numbers_jaccard": [0.5] * len(pairs), "latin_share": [None] * len(pairs),
        "sentences_a": [5] * len(pairs), "sentences_b": [5] * len(pairs), "aligned": [round(c * 5) for c in cov],
        "coverage": cov, "mean_sentence_cosine": [0.8] * len(pairs), "qualifies": [c >= 0.6 for c in cov]})
    summary = {"status": status, "config": {"top_k": 3, **sentences}} if sentences is not None else {"status": status}
    (folder / "h3_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return folder


COV = np.round(np.linspace(0.3, 1.0, N), 4).tolist()   # one sa-en and one hi-en pair per document, coverage rising


def setup(tmp_path, monkeypatch, **cfg):
    monkeypatch.setattr(sheets, "REPO", tmp_path)
    docs = build_inputs(tmp_path)
    labse = [("sa", d, "en", d, COV[d]) for d in range(N)] + [("en", d, "hi", d, COV[d]) for d in range(N)]
    labse.append(("sa", 0, "hi", 0, 0.9))                         # a language pair not configured: dropped
    bge = [("en", d, "sa", d, round(1.0 - COV[d] / 2, 4)) for d in range(N)]   # the other side first
    write_run(tmp_path, "labse", docs, labse)
    write_run(tmp_path, "bge", docs, bge, reverse_docs=True)
    pq.write_table(pa.table({"pair": ["sa-en"] * 4 + ["hi-en"] * 4,
                             "text_a": [f"नियन्त्रण वाक्यम् {i} अत्र अस्ति।" for i in range(8)],
                             "text_b": [f"Control sentence number {i} is here." for i in range(8)],
                             "expected": ["no"] * 8, "source": ["test-control"] * 8}), tmp_path / "controls.parquet")
    config = {"runs": {"labse": "out/runs/labse", "bge": "out/runs/bge"}, "inputs": "inputs",
              "controls": "controls.parquet", "out": "out/e5d", "pairs": [["sa", "en"], ["hi", "en"]],
              "per_band": 4, "n_controls": 3, "readers": 2, "seed": 7, **cfg}
    config = {k: v for k, v in config.items() if v is not None}     # a None override leaves the key out
    path = tmp_path / "e5d.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path, docs


def run(path):
    sheets.main(["--config", str(path)])


def read(path):
    data = path.read_bytes()
    data = data[3:] if data.startswith(sheets.BOM) else data
    return pacsv.read_csv(pa.BufferReader(data), parse_options=pacsv.ParseOptions(newlines_in_values=True),
                          convert_options=pacsv.ConvertOptions(column_types={
                              "item": pa.string(), "text_1": pa.string(), "text_2": pa.string(),
                              "translation": pa.string(), "note": pa.string()})).to_pylist()


def key_rows(tmp_path, name):
    return pacsv.read_csv(tmp_path / "out/e5d/key" / f"{name}_key.csv",
                          convert_options=pacsv.ConvertOptions(strings_can_be_null=True)).to_pylist()


def shown(text):
    return "\n".join(split_sentences(text, 20, 16))


def test_sheets_are_blind(tmp_path, monkeypatch):
    path, docs = setup(tmp_path, monkeypatch)
    run(path)
    raw = (tmp_path / "out/e5d/sheets/sa-en_reader1.csv").read_bytes()
    assert raw.startswith(sheets.BOM)
    for name in ("sa-en", "hi-en"):
        for r in (1, 2):
            rows = read(tmp_path / "out/e5d/sheets" / f"{name}_reader{r}.csv")
            assert list(rows[0]) == sheets.SHEET_COLUMNS
            assert all(x["translation"] == "" and x["note"] == "" for x in rows)
            cells = " ".join(x["text_1"] + x["text_2"] for x in rows)
            for x in docs:
                assert x["doc_id"] not in cells and x["pack"] not in cells
            assert "Menu" not in cells


def test_every_reader_gets_every_item_in_their_own_order(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, per_band=10)
    run(path)
    key = [x["item"] for x in key_rows(tmp_path, "sa-en")]
    assert len(key) == len(set(key))
    orders = [[x["item"] for x in read(tmp_path / "out/e5d/sheets" / f"sa-en_reader{r}.csv")] for r in (1, 2)]
    assert sorted(orders[0]) == sorted(orders[1]) == sorted(key)
    assert orders[0] != orders[1]


def test_both_sides_of_the_threshold_are_drawn(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, per_band=2)
    run(path)
    rows = [x for x in key_rows(tmp_path, "hi-en") if x["source"] == "candidate"]
    cov = [x["coverage_labse"] for x in rows]
    assert min(cov) < 0.6 <= max(cov)
    assert {x["band"] for x in rows} == {"0.30-0.45", "0.45-0.60", "0.60-0.75", "0.75-1.00"}
    summary = json.loads((tmp_path / "out/e5d/e5d_summary.json").read_text())
    hi = [s for s in summary["strata"] if s["pair"] == "hi-en"]
    assert all(s["encoder"] == "labse" and s["drawn"] <= s["wanted"] == 2 for s in hi)


def test_each_language_pair_can_have_its_own_sample_size(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, per_band={"en-sa": 4, "hi-en": 1}, n_controls={"sa-en": 2, "hi-en": 0})
    run(path)
    summary = json.loads((tmp_path / "out/e5d/e5d_summary.json").read_text())
    wanted = {(s["pair"], s["encoder"]): s["wanted"] for s in summary["strata"]}
    assert wanted == {("sa-en", "labse"): 2, ("sa-en", "bge"): 2, ("hi-en", "labse"): 1}   # 4 split between 2
    hi = [x for x in key_rows(tmp_path, "hi-en")]
    assert len(hi) == 4 and all(x["source"] == "candidate" for x in hi)                   # 1 per band, no controls
    assert sum(x["source"] == "control" for x in key_rows(tmp_path, "sa-en")) == 2
    assert summary["config"]["per_band"] == {"sa-en": 4, "hi-en": 1}                       # named in pairs' order


ABOVE, NEAR, BELOW = [[0.6, 1.0]], [[0.45, 0.6]], [[0.3, 0.45]]


def buckets(above, below, above_bands=ABOVE + NEAR):
    return {"per_band": None, "buckets": {"above": {"bands": above_bands, "n": above},
                                          "below": {"bands": BELOW, "n": below}}}


def doc_number(row):
    return int(row["doc_id_a"][-2:])


def test_buckets_take_every_qualifying_pair_then_fill_from_near_the_cut(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, n_controls=0,
                    **buckets(above={"sa-en": 12, "hi-en": 8}, below={"sa-en": 0, "hi-en": 2}))
    run(path)
    hi = key_rows(tmp_path, "hi-en")
    above = [r for r in hi if r["bucket"] == "above"]
    assert len(above) == 8 and len(hi) == 10
    assert {doc_number(r) for r in above if r["band"] == "0.60-1.00"} == set(range(5, 12))    # all 7 qualifying
    assert {doc_number(r) for r in above if r["band"] == "0.45-0.60"} <= {3, 4}
    assert sum(r["band"] == "0.45-0.60" for r in above) == 1
    below = [r for r in hi if r["bucket"] == "below"]
    assert len(below) == 2 and {doc_number(r) for r in below} <= {0, 1, 2}
    assert {r["band"] for r in below} == {"0.30-0.45"}
    sa = key_rows(tmp_path, "sa-en")                              # LaBSE qualifies 5-11, BGE-M3 0-7: all 12, once
    assert sorted(doc_number(r) for r in sa) == list(range(12))
    assert {doc_number(r) for r in sa if r["drawn_for"] == "labse"} == set(range(5, 12))
    assert {doc_number(r) for r in sa if r["drawn_for"] == "bge"} == set(range(0, 5))
    summary = json.loads((tmp_path / "out/e5d/e5d_summary.json").read_text())
    assert summary["shortfalls"] == []


def strata_by_bucket(tmp_path):
    strata = json.loads((tmp_path / "out/e5d/e5d_summary.json").read_text())["strata"]
    return {(s["pair"], s["bucket"]): s for s in strata}


def test_a_bucket_draw_is_split_between_the_encoders(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, n_controls=0,
                    **buckets(above={"sa-en": 4, "hi-en": 0}, below=0, above_bands=ABOVE))
    run(path)
    s = strata_by_bucket(tmp_path)[("sa-en", "above")]
    assert s["available"] == 12 and s["drawn_by_encoder"] == {"labse": 2, "bge": 2}
    rows = key_rows(tmp_path, "sa-en")
    assert len(rows) == 4 == len({doc_number(r) for r in rows})


def test_a_bucket_tops_up_from_the_encoder_that_has_pairs(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, n_controls=0, **buckets(above=0, below={"sa-en": 2, "hi-en": 0}))
    run(path)
    s = strata_by_bucket(tmp_path)[("sa-en", "below")]           # only LaBSE scores sa-en pairs in 0.30-0.45
    assert s["available"] == 3 and s["drawn_by_encoder"] == {"labse": 2, "bge": 0}
    assert {doc_number(r) for r in key_rows(tmp_path, "sa-en")} <= {0, 1, 2}


def test_a_short_bucket_is_reported(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, n_controls=0,
                    **buckets(above={"sa-en": 12, "hi-en": 10}, below=0))
    run(path)
    summary = json.loads((tmp_path / "out/e5d/e5d_summary.json").read_text())
    assert summary["shortfalls"] == [{"pair": "hi-en", "bucket": "above", "wanted": 10, "drawn": 9}]


def test_bucket_keys_label_the_controls_and_per_band_keys_stay_as_they_were(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, **buckets(above=4, below=2))
    run(path)
    rows = key_rows(tmp_path, "sa-en")
    assert {r["bucket"] for r in rows if r["source"] == "control"} == {"control"}
    assert {r["bucket"] for r in rows if r["source"] == "candidate"} <= {"above", "below"}
    path, _ = setup(tmp_path, monkeypatch)                        # bands and per_band: no bucket column
    run(path)
    assert "bucket" not in key_rows(tmp_path, "sa-en")[0]


def test_a_pair_both_encoders_listed_is_read_once_with_both_scores(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, per_band=50)
    run(path)
    rows = [x for x in key_rows(tmp_path, "sa-en") if x["source"] == "candidate"]
    assert len(rows) == N == len({(x["doc_id_a"], x["doc_id_b"]) for x in rows})
    for x in rows:
        d = int(x["doc_id_a"][-2:])
        assert x["lang_a"] == "sa" and x["lang_b"] == "en" and x["doc_id_b"] == doc_id("en", d)
        assert x["coverage_labse"] == pytest.approx(COV[d])
        assert x["coverage_bge"] == pytest.approx(round(1.0 - COV[d] / 2, 4))
    assert {x["drawn_for"] for x in rows} == {"labse", "bge"}


def test_only_hindi_pairs_have_one_encoder(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch, per_band=50)
    run(path)
    rows = [x for x in key_rows(tmp_path, "hi-en") if x["source"] == "candidate"]
    assert len(rows) == N and all(x["coverage_bge"] is None for x in rows)
    summary = json.loads((tmp_path / "out/e5d/e5d_summary.json").read_text())
    assert summary["runs"]["labse"]["other_language_pairs_dropped"] == 1
    assert summary["shortfalls"]


def test_texts_are_the_scored_sentences_on_the_right_sides(tmp_path, monkeypatch):
    path, docs = setup(tmp_path, monkeypatch, per_band=50)
    run(path)
    text = {x["doc_id"]: x["text"] for x in docs}
    key = {x["item"]: x for x in key_rows(tmp_path, "sa-en")}
    flips = set()
    for row in read(tmp_path / "out/e5d/sheets/sa-en_reader1.csv"):
        k = key[row["item"]]
        if k["source"] != "candidate":
            continue
        a, b = shown(text[k["doc_id_a"]]), shown(text[k["doc_id_b"]])
        first, second = (a, b) if k["text_1_side"] == "a" else (b, a)
        assert (row["text_1"], row["text_2"]) == (first, second)
        flips.add(k["text_1_side"])
    assert flips == {"a", "b"}
    en0 = shown(text[doc_id("en", 0)])
    assert en0.count("\n") == 15 and "Menu" not in en0


def test_controls_are_mixed_in(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch)
    run(path)
    for name in ("sa-en", "hi-en"):
        ctl = [x for x in key_rows(tmp_path, name) if x["source"] == "control"]
        assert len(ctl) == 3
        assert all(x["expected"] == "no" and x["band"] == "control" and x["drawn_for"] is None
                   and x["control_source"] == "test-control" for x in ctl)
    rows = read(tmp_path / "out/e5d/sheets/sa-en_reader2.csv")
    assert sum("Control sentence number" in (x["text_1"] + x["text_2"]) for x in rows) == 3


def test_the_seed_fixes_the_sheets(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch)
    run(path)
    first = {p.name: p.read_bytes() for p in (tmp_path / "out/e5d").rglob("*.csv")}
    run(path)
    assert first == {p.name: p.read_bytes() for p in (tmp_path / "out/e5d").rglob("*.csv")}
    cfg = json.loads(path.read_text())
    path.write_text(json.dumps({**cfg, "seed": 8}))
    run(path)
    assert first != {p.name: p.read_bytes() for p in (tmp_path / "out/e5d").rglob("*.csv")}


def test_summary_has_counts_and_no_text(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch)
    run(path)
    raw = (tmp_path / "out/e5d/e5d_summary.json").read_text(encoding="utf-8")
    assert "English sentence" not in raw and "वाक्य" not in raw
    summary = json.loads(raw)
    assert summary["status"] == "complete" and summary["items"]["sa-en"] > 0
    assert "sheets/sa-en_reader1.csv" in summary["outputs"]


def test_documents_that_changed_since_the_run_stop_it(tmp_path, monkeypatch):
    path, _ = setup(tmp_path, monkeypatch)
    docs_path = tmp_path / "out/runs/labse/h3_docs.parquet"
    t = pq.read_table(docs_path)
    pq.write_table(t.set_column(t.schema.get_field_index("chars"), "chars",
                                pa.array([c + 1 for c in t["chars"].to_pylist()])), docs_path)
    with pytest.raises(SystemExit, match="differ from what h3.py read"):
        run(path)


def test_sentences_are_split_as_the_runs_split_them(tmp_path, monkeypatch):
    path, docs = setup(tmp_path, monkeypatch, per_band=50)
    short = {"sentence_min_chars": 20, "max_sentences": 3}
    labse = [("sa", d, "en", d, COV[d]) for d in range(N)]
    write_run(tmp_path, "labse", docs, labse, sentences=short)
    write_run(tmp_path, "bge", docs, labse, reverse_docs=True, sentences=short)
    run(path)
    text = {x["doc_id"]: x["text"] for x in docs}
    key = {x["item"]: x for x in key_rows(tmp_path, "sa-en")}
    rows = [x for x in read(tmp_path / "out/e5d/sheets/sa-en_reader1.csv") if key[x["item"]]["source"] == "candidate"]
    assert rows
    for row in rows:
        k = key[row["item"]]
        a, b = (split_sentences(text[k[f"doc_id_{s}"]], 20, 3) for s in "ab")
        assert {row["text_1"], row["text_2"]} == {"\n".join(a), "\n".join(b)}
    summary = json.loads((tmp_path / "out/e5d/e5d_summary.json").read_text())
    assert summary["sentence_settings"] == short


def test_runs_that_split_sentences_differently_are_refused(tmp_path, monkeypatch):
    path, docs = setup(tmp_path, monkeypatch)
    write_run(tmp_path, "bge", docs, [("en", 0, "sa", 0, 0.9)], sentences={"sentence_min_chars": 20,
                                                                            "max_sentences": 8})
    with pytest.raises(SystemExit, match="split sentences differently"):
        run(path)


def test_a_run_without_its_sentence_settings_is_refused(tmp_path, monkeypatch):
    path, docs = setup(tmp_path, monkeypatch)
    write_run(tmp_path, "labse", docs, [("sa", 0, "en", 0, 0.9)], sentences=None)
    with pytest.raises(SystemExit, match="does not record h3.py's sentence_min_chars and max_sentences"):
        run(path)


def test_an_incomplete_run_is_refused(tmp_path, monkeypatch):
    path, docs = setup(tmp_path, monkeypatch)
    write_run(tmp_path, "labse", docs, [("sa", 0, "en", 0, 0.9)], status="stopped_time_limit")
    with pytest.raises(SystemExit, match="only a complete h3.py run"):
        run(path)


@pytest.mark.parametrize("change, message", [
    ({"out": "elsewhere"}, "out must be inside out/"),
    ({"bands": [0.6, 0.3]}, "bands must be"),
    ({"pairs": [["sa", "en"], ["en", "sa"]]}, "pairs must be distinct"),
    ({"runs": {}}, "runs must be"),
    ({"per_band": 0}, "per_band must be"),
    ({"per_band": {"sa-en": 4}}, "map must name each language pair"),
    ({"per_band": {"sa-en": 4, "hi-en": 2, "sa-hi": 1}}, "map must name each language pair"),
    ({"per_band": {"sa-en": 4, "en-sa": 4, "hi-en": 2}}, "map must name each language pair"),
    ({"per_band": {"sa-en": 4, "hi-en": 0}}, "per_band must be a positive integer, or a map"),
    ({"n_controls": {"sa-en": -1, "hi-en": 1}}, "n_controls must be a nonnegative integer, or a map"),
    ({"max_sentences": 16}, "unknown keys"),                     # taken from the runs, never the sheet config
    ({"buckets": {"above": {"bands": [[0.6, 1.0]], "n": 2}}}, "buckets replace bands and per_band"),
    ({"per_band": None, "buckets": {}}, "buckets must be a nonempty"),
    ({"per_band": None, "buckets": {"Above": {"bands": [[0.6, 1.0]], "n": 2}}}, "bucket names must be lowercase"),
    ({"per_band": None, "buckets": {"above": {"bands": [[0.6, 1.0]]}}}, 'needs exactly "bands" and "n"'),
    ({"per_band": None, "buckets": {"above": {"bands": [[0.6, 0.6]], "n": 2}}}, "bands must be \\[low, high\\]"),
    ({"per_band": None, "buckets": {"above": {"bands": [], "n": 2}}}, "bands must be \\[low, high\\]"),
    ({"per_band": None, "buckets": {"above": {"bands": [[0.6, 1.0]], "n": {"sa-en": 2}}}},
     "a bucket above n map must name each language pair"),
    ({"surprise": 1}, "unknown keys")])
def test_bad_configs_are_refused(tmp_path, monkeypatch, change, message):
    path, _ = setup(tmp_path, monkeypatch, **change)
    with pytest.raises(SystemExit, match=message):
        run(path)
