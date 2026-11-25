r"""E5d's reader zips: one zip per bilingual reader, with that reader's sheets from h3_e5d_sheets.py, the viewer
(view_e5d_sheets.py) and the readers' guide (README_e5d_readers.md). Nothing else leaves out/: the key, the
sentences and the generator's summary stay with us.

HOW TO RUN IT
=============
From the repository root, after h3_e5d_sheets.py has written its folder:

    python3 -I teams/01-data-a/dedup/h3_e5d_pack.py --sheets-out out/e5d_e5c \
        --assign teams/01-data-a/dedup/h3_e5d_readers.json --out out/e5d_zips

  --sheets-out  h3_e5d_sheets.py's --out folder: sheets/, readers_guide.md and e5d_summary.json (status complete)
  --assign      a JSON object, reader -> the sheets they read, by name without .csv:
                {"keshavamurali": ["sa-en_reader1"], "riteshverma": ["sa-en_reader2", "sa-hi_reader1"]}
                A reader name is a GitHub handle or a name (letters, digits, '.', '_', '-')
  --out         the folder for the zips, inside out/

CHECKS (any failure stops the run, and no zip is written)
=========================================================
  - the generator's run is complete, and every packed file (each sheet, readers_guide.md) has the sha256 its
    e5d_summary.json records, so no sheet was edited after it was made;
  - each sheet is one the viewer opens (its columns, distinct item IDs) and is blind and unanswered: the translation
    and note columns are empty;
  - a sheet goes to one reader only, and no reader gets both readers' copies of one language pair;
  - each zip, once written, holds exactly the expected files, and the viewer opens its sheets with no answers yet.
Sheets that no reader is assigned are listed (not packed), so sheets can go out in stages.

WHAT IT WRITES (in --out, inside out/)
======================================
  e5d_<reader>.zip   e5d/README.md (the readers' guide), e5d/view_e5d_sheets.py, e5d/sheets/readers_guide.md and
                     e5d/sheets/<pair>_reader<k>.csv for each of the reader's sheets. The sheets hold page text: the
                     zips are sent privately and never committed. Entries are sorted, with a fixed date, so the same
                     inputs give the same bytes
  manifest.json      the inputs' sha256, each reader's sheets, each zip's sha256 and file list, and the unassigned
                     sheets: names and hashes only, no text

Python 3 with pyarrow, as the other E5d scripts; a reader needs only Python 3. Its loops run over the readers and their
few files, never over sheet rows: a sheet's answer cells are checked with pyarrow compute. The viewer's own read_sheet
and discover read each sheet as the reader's viewer will.
"""
import sys
sys.dont_write_bytecode = True

import argparse, hashlib, json, tempfile, zipfile  # noqa: E401,E402
from pathlib import Path  # noqa: E402

import pyarrow as pa  # noqa: E402
import pyarrow.compute as pc  # noqa: E402
import pyarrow.csv as pacsv  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import view_e5d_sheets as viewer  # noqa: E402

REPO = Path(__file__).resolve().parents[3]   # teams/01-data-a/dedup/h3_e5d_pack.py -> the repository root
HERE = Path(__file__).resolve().parent
VIEWER = HERE / "view_e5d_sheets.py"
README = HERE / "README_e5d_readers.md"
ROOT = "e5d"                                  # the folder a reader gets when unzipping
DATE = (2026, 1, 1, 0, 0, 0)                  # every zip entry's date, so that the same inputs give the same zip


class PackError(ValueError):
    """An input that cannot be packed."""


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def answered_items(path):
    """The items of a sheet whose translation or note cell is not empty (h3_e5d_sheets.py leaves both empty)."""
    data = Path(path).read_bytes()
    data = data[3:] if data.startswith(b"\xef\xbb\xbf") else data
    table = pacsv.read_csv(pa.BufferReader(data), parse_options=pacsv.ParseOptions(newlines_in_values=True),
                           convert_options=pacsv.ConvertOptions(
                               column_types={c: pa.string() for c in viewer.SHEET_COLUMNS}))
    filled = [pc.greater(pc.utf8_length(pc.utf8_trim_whitespace(pc.fill_null(table[c], ""))), 0)
              for c in ("translation", "note")]
    return table["item"].filter(pc.or_(*filled)).to_pylist()


def read_assign(path):
    """{reader: [sheet name, ...]} from the --assign file, with each rule of the docstring's CHECKS on names."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise PackError(f"{path}: not a JSON file ({e})")
    if not isinstance(raw, dict) or not raw:
        raise PackError(f"{path}: must be an object, reader -> list of sheets")
    owner, assign = {}, {}
    for reader, sheets in raw.items():
        try:
            name = viewer.clean_name(reader)
        except viewer.SheetError as e:
            raise PackError(f"reader {reader!r}: {e}")
        if not name or name != reader:
            raise PackError(f"reader {reader!r}: use letters, digits, '.', '_' and '-' only, with no spaces")
        if not isinstance(sheets, list) or not sheets or not all(isinstance(s, str) for s in sheets):
            raise PackError(f"reader {reader}: give a nonempty list of sheet names")
        pairs = {}
        for s in sheets:
            m = viewer.SHEET_NAME.match(f"{s}.csv")
            if not m:
                raise PackError(f"reader {reader}: {s!r} is not a sheet name (<pair>_reader<k>)")
            if s in owner:
                raise PackError(f"sheet {s} is assigned to {owner[s]} and {reader}: one reader per sheet")
            if m["pair"] in pairs:
                raise PackError(f"reader {reader} has {pairs[m['pair']]} and {s}: both copies of {m['pair']}")
            owner[s], pairs[m["pair"]] = reader, s
        assign[reader] = sorted(sheets)
    return assign


def check_sheets(sheets_out, assign):
    """The generator's summary, and the checked path of every assigned sheet; the unassigned sheets."""
    sheets_out = Path(sheets_out)
    summary_path = sheets_out / "e5d_summary.json"
    if not summary_path.is_file():
        raise PackError(f"no {summary_path}: run h3_e5d_sheets.py first")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("status") != "complete":
        raise PackError(f"{summary_path}: status {summary.get('status')!r}, not complete")
    recorded = summary.get("outputs") or {}

    def checked(rel):
        path = sheets_out / rel
        if not path.is_file():
            raise PackError(f"no {path}")
        if rel not in recorded:
            raise PackError(f"{rel} is not among the outputs in {summary_path.name}")
        if sha256(path) != recorded[rel]:
            raise PackError(f"{rel} differs from the file h3_e5d_sheets.py wrote (sha256): it was changed")
        return path

    guide = checked("readers_guide.md")
    paths = {}
    for reader, sheets in assign.items():
        for s in sheets:
            path = checked(f"sheets/{s}.csv")
            try:
                viewer.read_sheet(path)                          # as the reader's viewer reads it
            except viewer.SheetError as e:
                raise PackError(str(e))
            answered = answered_items(path)
            if answered:
                raise PackError(f"{s}: items already answered ({answered[:3]}): a sheet goes out unanswered")
            paths[s] = path
    made = sorted(Path(k).stem for k in recorded if k.startswith("sheets/") and k.endswith(".csv"))
    unassigned = [s for s in made if s not in paths]
    return summary_path, guide, paths, unassigned


def entries(guide, sheet_paths):
    """[(name in the zip, source file)], sorted: the guide, the viewer and the reader's sheets."""
    files = [(f"{ROOT}/README.md", README), (f"{ROOT}/view_e5d_sheets.py", VIEWER),
             (f"{ROOT}/sheets/readers_guide.md", guide)]
    files += [(f"{ROOT}/sheets/{p.name}", p) for p in sheet_paths]
    return sorted(files)


def write_zip(path, files):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, src in files:
            info = zipfile.ZipInfo(name, date_time=DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, Path(src).read_bytes())


def verify_zip(path, files, reader, n_sheets):
    """The zip holds exactly files, byte for byte, and the viewer opens its sheets with no answers."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if names != [n for n, _ in files]:
            raise PackError(f"{path.name}: holds {names}, not the expected files")
        for name, src in files:
            if z.read(name) != Path(src).read_bytes():
                raise PackError(f"{path.name}: {name} differs from {src}")
        with tempfile.TemporaryDirectory() as tmp:
            z.extractall(tmp)
            root = Path(tmp) / ROOT
            try:
                opened = viewer.discover(root / "sheets", root / "e5d_labels", reader)
            except viewer.SheetError as e:
                raise PackError(f"{path.name}: the viewer cannot open it: {e}")
    if len(opened) != n_sheets or any(viewer.done(s) for s in opened):
        raise PackError(f"{path.name}: the viewer opens {len(opened)} sheets, not {n_sheets} unanswered ones")


def pack(sheets_out, assign_path, out):
    """Check everything, then write one zip per reader and manifest.json in out. Returns the manifest."""
    assign = read_assign(assign_path)
    summary_path, guide, paths, unassigned = check_sheets(sheets_out, assign)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    readers = {}
    for reader, sheets in assign.items():
        files = entries(guide, [paths[s] for s in sheets])
        zip_path = out / f"e5d_{reader}.zip"
        write_zip(zip_path, files)
        verify_zip(zip_path, files, reader, len(sheets))
        readers[reader] = {"sheets": sheets, "zip": zip_path.name, "zip_sha256": sha256(zip_path),
                           "files": {name: sha256(src) for name, src in files}}
    manifest = {"sheets_out": str(Path(sheets_out)), "e5d_summary_sha256": sha256(summary_path),
                "assign_sha256": sha256(assign_path), "viewer_sha256": sha256(VIEWER),
                "readme_sha256": sha256(README), "readers": readers, "unassigned": unassigned}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheets-out", required=True, type=Path, help="h3_e5d_sheets.py's output folder")
    ap.add_argument("--assign", required=True, type=Path, help="JSON: reader -> list of sheet names")
    ap.add_argument("--out", required=True, help="the folder for the zips, inside out/")
    args = ap.parse_args(argv)
    out = REPO / args.out
    if Path(args.out).is_absolute() or not out.resolve().is_relative_to((REPO / "out").resolve()):
        sys.exit(f"ERROR: --out must be inside out/ in the repository root, not {args.out!r}")
    try:
        manifest = pack(args.sheets_out, args.assign, out)
    except PackError as e:
        sys.exit(f"ERROR: {e}")
    for reader, r in manifest["readers"].items():
        print(f"{r['zip']}: {', '.join(r['sheets'])}  sha256 {r['zip_sha256'][:16]}")
    print("not packed (no reader yet): " + (", ".join(manifest["unassigned"]) or "none"))
    print(f"manifest: {(out / 'manifest.json').resolve().relative_to(REPO.resolve())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
