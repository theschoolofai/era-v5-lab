"""Unit tests for h3_e5d_pack.py, E5d's reader zips: what goes into each zip, what never does, and the inputs it
refuses.

The generator's folder here is made up in h3_e5d_sheets.py's layout: sheets/<pair>_reader<k>.csv (UTF-8 with a
byte-order mark), readers_guide.md, key/ and e5d_summary.json with each output's sha256.

  python3 -B -m pytest dedup/tests/test_h3_e5d_pack.py
"""
import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h3_e5d_pack as pack  # noqa: E402
import view_e5d_sheets as viewer  # noqa: E402

ROWS = {"sa-en": [("sa-en-001", "संस्कृतवाक्यम्।", "A Sanskrit sentence.", "", ""),
                  ("sa-en-002", "अन्यत् वाक्यम्।", "Another sentence.", "", "")],
        "sa-hi": [("sa-hi-001", "पाठः।", "पाठ।", "", "")],
        "hi-en": [("hi-en-001", "हिंदी वाक्य।", "A Hindi sentence.", "", "")]}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_sheet(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(viewer.SHEET_COLUMNS)
        w.writerows(rows)


def write_summary(folder, status="complete"):
    outputs = {str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob("*"))
               if p.is_file() and p.name != "e5d_summary.json"}
    (folder / "e5d_summary.json").write_text(json.dumps({"status": status, "outputs": outputs}), encoding="utf-8")


@pytest.fixture
def made(tmp_path):
    """A generator folder with two readers' copies of three language pairs."""
    folder = tmp_path / "e5d"
    (folder / "sheets").mkdir(parents=True)
    (folder / "key").mkdir()
    for pair, rows in ROWS.items():
        for k in (1, 2):
            write_sheet(folder / "sheets" / f"{pair}_reader{k}.csv", rows if k == 1 else rows[::-1])
        (folder / "key" / f"{pair}_key.csv").write_text("item,coverage\n", encoding="utf-8")
    (folder / "readers_guide.md").write_text("# E5d: what to answer\n", encoding="utf-8")
    write_summary(folder)
    return folder


def assign_file(tmp_path, assign):
    path = tmp_path / "assign.json"
    path.write_text(json.dumps(assign), encoding="utf-8")
    return path


ASSIGN = {"reader_a": ["sa-en_reader1"], "reader_b": ["sa-en_reader2", "sa-hi_reader1"]}


def test_each_reader_gets_guide_viewer_and_their_sheets(made, tmp_path):
    out = tmp_path / "zips"
    manifest = pack.pack(made, assign_file(tmp_path, ASSIGN), out)
    with zipfile.ZipFile(out / "e5d_reader_b.zip") as z:
        assert z.namelist() == ["e5d/README.md", "e5d/sheets/readers_guide.md", "e5d/sheets/sa-en_reader2.csv",
                                "e5d/sheets/sa-hi_reader1.csv", "e5d/view_e5d_sheets.py"]
        assert z.read("e5d/view_e5d_sheets.py") == pack.VIEWER.read_bytes()
        assert z.read("e5d/README.md") == pack.README.read_bytes()
        assert z.read("e5d/sheets/sa-en_reader2.csv") == (made / "sheets" / "sa-en_reader2.csv").read_bytes()
    assert manifest["readers"]["reader_a"]["sheets"] == ["sa-en_reader1"]
    assert json.loads((out / "manifest.json").read_text())["readers"]["reader_b"]["zip"] == "e5d_reader_b.zip"


def test_key_and_summary_never_leave(made, tmp_path):
    out = tmp_path / "zips"
    pack.pack(made, assign_file(tmp_path, ASSIGN), out)
    for z in out.glob("*.zip"):
        names = zipfile.ZipFile(z).namelist()
        assert not any("key" in n or "summary" in n or n.endswith(".parquet") for n in names)


def test_unassigned_sheets_are_listed_not_packed(made, tmp_path):
    manifest = pack.pack(made, assign_file(tmp_path, ASSIGN), tmp_path / "zips")
    assert manifest["unassigned"] == ["hi-en_reader1", "hi-en_reader2", "sa-hi_reader2"]
    assert sorted(p.name for p in (tmp_path / "zips").glob("*.zip")) == ["e5d_reader_a.zip", "e5d_reader_b.zip"]


def test_same_inputs_give_the_same_zip(made, tmp_path):
    a = pack.pack(made, assign_file(tmp_path, ASSIGN), tmp_path / "a")
    b = pack.pack(made, assign_file(tmp_path, ASSIGN), tmp_path / "b")
    assert [r["zip_sha256"] for r in a["readers"].values()] == [r["zip_sha256"] for r in b["readers"].values()]


def test_unzipped_sheets_open_in_the_viewer(made, tmp_path):
    out = tmp_path / "zips"
    pack.pack(made, assign_file(tmp_path, ASSIGN), out)
    zipfile.ZipFile(out / "e5d_reader_b.zip").extractall(tmp_path / "unzipped")
    root = tmp_path / "unzipped" / "e5d"
    sheets = viewer.discover(root / "sheets", root / "e5d_labels", "reader_b")
    assert [s["key"] for s in sheets] == ["sa-en_reader2", "sa-hi_reader1"]
    assert all(viewer.done(s) == 0 for s in sheets)


@pytest.mark.parametrize("assign, message", [
    ({"reader_a": ["sa-en_reader1"], "reader_b": ["sa-en_reader1"]}, "one reader per sheet"),
    ({"reader_a": ["sa-en_reader1", "sa-en_reader2"]}, "both copies of sa-en"),
    ({"reader_a": ["sa-en_reader1", "sa-en_reader1"]}, "one reader per sheet"),
    ({"reader_a": ["sa-en_reader9"]}, "no "),
    ({"reader_a": ["sa-en_key"]}, "not a sheet name"),
    ({"reader a": ["sa-en_reader1"]}, "no spaces"),
    ({"reader_a": []}, "nonempty list"),
    ([], "must be an object"),
])
def test_bad_assignments_are_refused(made, tmp_path, assign, message):
    with pytest.raises(pack.PackError, match=message):
        pack.pack(made, assign_file(tmp_path, assign), tmp_path / "zips")
    assert not (tmp_path / "zips").exists()          # every check runs before anything is written


def test_an_edited_sheet_is_refused(made, tmp_path):
    path = made / "sheets" / "sa-en_reader1.csv"
    path.write_bytes(path.read_bytes().replace("Another".encode(), b"Edited"))
    with pytest.raises(pack.PackError, match="was changed"):
        pack.pack(made, assign_file(tmp_path, ASSIGN), tmp_path / "zips")


@pytest.mark.parametrize("answer", [("yes", ""), ("", "a note")])
def test_an_answered_sheet_is_refused(made, tmp_path, answer):
    path = made / "sheets" / "sa-en_reader1.csv"
    write_sheet(path, [ROWS["sa-en"][0], ROWS["sa-en"][1][:3] + answer])
    assert pack.answered_items(path) == ["sa-en-002"]
    write_summary(made)                               # recorded as made, so only the answers are wrong
    with pytest.raises(pack.PackError, match="already answered"):
        pack.pack(made, assign_file(tmp_path, ASSIGN), tmp_path / "zips")


def test_an_incomplete_run_is_refused(made, tmp_path):
    write_summary(made, status="stopped_time_limit")
    with pytest.raises(pack.PackError, match="not complete"):
        pack.pack(made, assign_file(tmp_path, ASSIGN), tmp_path / "zips")


def test_main_writes_only_inside_out(made, tmp_path):
    with pytest.raises(SystemExit, match="inside out/"):
        pack.main(["--sheets-out", str(made), "--assign", str(assign_file(tmp_path, ASSIGN)),
                   "--out", "../elsewhere"])
