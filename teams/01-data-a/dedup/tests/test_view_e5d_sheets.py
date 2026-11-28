"""Unit tests for view_e5d_sheets.py, E5d's reader viewer: which sheets it finds, how answers are checked and saved,
and what its local server serves and refuses.

The sheets here are made up, in h3_e5d_sheets.py's format (UTF-8 with a byte-order mark, a sentence per line). The
server tests start the viewer on a free port of 127.0.0.1 in a thread.

  python3 -B -m pytest dedup/tests/test_view_e5d_sheets.py
"""
import csv
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import view_e5d_sheets as viewer  # noqa: E402

ROWS = [("sa-en-001", "संस्कृतवाक्यम् प्रथमम्।\nद्वितीयं वाक्यम्।", "The first sentence.\nThe second one.", "", ""),
        ("sa-en-002", "अन्यत् वाक्यम्।", "Another sentence, with a comma.", "", ""),
        ("sa-en-003", "तृतीयम्।", "The third.", "", "")]


def write_sheet(folder, name, rows=ROWS, header=viewer.SHEET_COLUMNS):
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / name, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(header)
        w.writerows(rows)


def read_answers(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture
def sheets(tmp_path):
    folder = tmp_path / "sheets"
    write_sheet(folder, "sa-en_reader1.csv")
    write_sheet(folder, "sa-hi_reader1.csv", [("sa-hi-001", "पाठः।", "पाठ।", "", "")])
    write_sheet(folder, "notes.csv", [("x", "y", "z", "", "")])          # not a sheet name: ignored
    (folder / "readers_guide.md").write_text("# guide\nyes / no / unsure", encoding="utf-8")
    return folder


def test_it_finds_the_readers_sheets_and_names_the_answer_files(sheets, tmp_path):
    found = viewer.discover(sheets, tmp_path / "labels", viewer.clean_name("Ritesh Verma"))
    assert [(s["key"], s["pair"], s["reader"]) for s in found] == [("sa-en_reader1", "sa-en", 1),
                                                                   ("sa-hi_reader1", "sa-hi", 1)]
    assert found[0]["out"] == tmp_path / "labels" / "sa-en-reader1-Ritesh_Verma.csv"
    assert found[0]["items"][0] == {"item": "sa-en-001", "text_1": ROWS[0][1], "text_2": ROWS[0][2]}
    assert viewer.labels_path(tmp_path, "hi-en", 2, "").name == "hi-en-reader2.csv"


def test_save_writes_every_item_in_the_sheets_order(sheets, tmp_path):
    s = viewer.discover(sheets, tmp_path / "labels", "R")[0]
    assert viewer.save(s, {"sa-en-002": {"translation": "Yes", "note": "line one\r\nline two, with a comma"}}) == 1
    assert viewer.save(s, {"sa-en-003": {"translation": "no", "note": ""}}) == 2
    rows = read_answers(s["out"])
    assert list(rows[0]) == viewer.LABEL_COLUMNS
    assert [(r["item"], r["translation"], r["note"]) for r in rows] == [
        ("sa-en-001", "", ""), ("sa-en-002", "yes", "line one\nline two, with a comma"), ("sa-en-003", "no", "")]
    assert not [p for p in s["out"].parent.iterdir() if p.name.endswith(".tmp")]


def test_answer_files_hold_no_document_text(sheets, tmp_path):
    s = viewer.discover(sheets, tmp_path / "labels", "R")[0]
    viewer.save(s, {"sa-en-001": {"translation": "unsure", "note": ""}})
    raw = s["out"].read_text(encoding="utf-8")
    assert "संस्कृत" not in raw and "first sentence" not in raw


@pytest.mark.parametrize("answers, message", [
    ({"sa-en-001": {"translation": "maybe", "note": ""}}, "must be yes, no or unsure"),
    ({"sa-en-009": {"translation": "yes", "note": ""}}, "not in this sheet"),
    ({"sa-en-001": {"translation": "yes", "note": "x" * (viewer.MAX_NOTE + 1)}}, "at most"),
    ({"sa-en-001": "yes"}, "must be an object"),
    (["yes"], "answers must be an object")])
def test_bad_answers_are_refused(sheets, tmp_path, answers, message):
    s = viewer.discover(sheets, tmp_path / "labels", "R")[0]
    with pytest.raises(viewer.SheetError, match=message):
        viewer.save(s, answers)
    assert not s["out"].exists()


def test_answers_typed_into_the_sheet_count_until_the_first_save(tmp_path):
    folder = tmp_path / "sheets"
    write_sheet(folder, "sa-en_reader2.csv", [ROWS[0][:3] + ("Yes", "typed"), ROWS[1][:3] + ("", "")])
    s = viewer.discover(folder, tmp_path / "labels", "")[0]
    assert s["answers"]["sa-en-001"] == {"translation": "yes", "note": "typed"} and viewer.done(s) == 1
    viewer.save(s, {"sa-en-001": {"translation": "no", "note": ""}})
    again = viewer.discover(folder, tmp_path / "labels", "")[0]               # the answer file wins from now on
    assert again["answers"]["sa-en-001"] == {"translation": "no", "note": ""}


@pytest.mark.parametrize("rows, header, message", [
    (ROWS, ["item", "text_1", "text_2"], "columns"),
    (ROWS + [ROWS[0]], viewer.SHEET_COLUMNS, "distinct, nonempty"),
    ([("", "a", "b", "", "")], viewer.SHEET_COLUMNS, "distinct, nonempty")])
def test_bad_sheets_are_refused(tmp_path, rows, header, message):
    write_sheet(tmp_path / "sheets", "sa-en_reader1.csv", rows, header)
    with pytest.raises(viewer.SheetError, match=message):
        viewer.discover(tmp_path / "sheets", tmp_path / "labels", "")


def test_a_folder_without_sheets_is_refused(tmp_path):
    (tmp_path / "sheets").mkdir()
    with pytest.raises(viewer.SheetError, match="no sheets"):
        viewer.discover(tmp_path / "sheets", tmp_path / "labels", "")


def test_names_are_checked():
    assert viewer.clean_name("  Ritesh   Verma ") == "Ritesh_Verma"
    with pytest.raises(viewer.SheetError, match="--name may hold"):
        viewer.clean_name("a/b")


@pytest.fixture
def served(sheets, tmp_path):
    app = viewer.App(viewer.discover(sheets, tmp_path / "labels", "Tester"), "the guide")
    srv = viewer.make_server(app, "127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield app, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def call(url, data=None, headers=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def test_the_server_serves_the_page_and_the_sheets(served):
    app, base = served
    code, page = call(base + "/")
    assert code == 200 and app.token in page and "E5d reader sheets" in page
    code, body = call(base + "/api/sheets")
    j = json.loads(body)
    assert code == 200 and j["guide"] == "the guide"
    assert [(s["key"], s["total"], s["done"]) for s in j["sheets"]] == [("sa-en_reader1", 3, 0), ("sa-hi_reader1", 1, 0)]
    code, body = call(base + "/api/sheet?key=sa-en_reader1")
    items = json.loads(body)["items"]
    assert code == 200 and all(set(i) == {"item", "text_1", "text_2"} for i in items)   # blind: text only
    assert call(base + "/api/sheet?key=nope")[0] == 404


def test_the_server_saves_only_with_the_pages_token(served):
    app, base = served
    payload = {"key": "sa-en_reader1", "answers": {"sa-en-001": {"translation": "yes", "note": ""}}}
    assert call(base + "/api/save", payload)[0] == 403                                  # another page cannot save
    code, body = call(base + "/api/save", payload, {"X-E5d-Token": app.token})
    assert code == 200 and json.loads(body) == {"file": "sa-en-reader1-Tester.csv", "done": 1, "total": 3}
    bad = {"key": "sa-en_reader1", "answers": {"sa-en-001": {"translation": "maybe"}}}
    code, body = call(base + "/api/save", bad, {"X-E5d-Token": app.token})
    assert code == 400 and "yes, no or unsure" in json.loads(body)["error"]
    assert read_answers(app.by_key["sa-en_reader1"]["out"])[0]["translation"] == "yes"


def test_the_server_answers_local_hosts_only(served):
    _, base = served
    assert call(base + "/api/sheets", headers={"Host": "evil.example"})[0] == 403
