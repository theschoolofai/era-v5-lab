"""Gold-set notes: a document leaves a gold set only when a second reader agrees that it was not clean.

Usage:
    python -I gold_notes.py                  check every <pack_id>_gold.csv in the gold folder
    python -I gold_notes.py --pack en-dclm   check one pack
    python -I gold_notes.py --record         add the documents that are new in the gold files to the manifest

    --gold-dir  the gold folder (default: ../gold)

Guideline 3: never remove a gold document to make a rule pass. Remove it only if a second reader agrees that it
was not clean, and write the reason in the gold-set notes. Two files in the gold folder hold this:

    gold_manifest.csv   pack_id, doc_id, added
                        every document that has ever been in a gold set. Rows are only added, never removed.
    gold_notes.csv      date, pack_id, doc_id, decision, code, raised_by, second_reader, rule_id, reason
                        one row for each gold document that someone said is not clean. decision is "removed"
                        (the second reader agrees, so the document leaves the gold set) or "kept" (the second
                        reader does not agree, so it stays). rule_id is the rule that touched it, if any.

The check: a document that is in the manifest but no longer in the gold file must have a "removed" note with a
reason and a second_reader who is not the person who raised it. Run it before a harm test: a gold file that fails
it must not be used.

Never write personal data or a secret in a note: for F1 and E3 give the type and the position only.
Exit code: 0 = every gold file passes, 1 = a problem was found, 2 = the files could not be read.
"""
import argparse
import csv
import datetime
import sys
from pathlib import Path

DEFAULT_GOLD_DIR = Path(__file__).resolve().parent.parent / "gold"
MANIFEST = "gold_manifest.csv"
NOTES = "gold_notes.csv"
MANIFEST_FIELDS = ["pack_id", "doc_id", "added"]
NOTE_FIELDS = ["date", "pack_id", "doc_id", "decision", "code", "raised_by", "second_reader", "rule_id", "reason"]
DECISIONS = ("removed", "kept")


class NotesError(Exception):
    """A notes or manifest file cannot be read."""


def pack_of(gold: Path) -> str:
    """en-dclm_gold.csv -> en-dclm."""
    return gold.stem[: -len("_gold")] if gold.stem.endswith("_gold") else gold.stem


def notes_dir(gold: Path) -> Path:
    """The folder whose manifest and notes cover this gold file: its own folder if it has a manifest, else ../gold.
    So a copy of a team gold file elsewhere is still checked against the team's manifest."""
    return gold.parent if (gold.parent / MANIFEST).exists() else DEFAULT_GOLD_DIR


def _read_csv(path: Path, fields):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            missing = [c for c in fields if c not in (reader.fieldnames or [])]
            if missing:
                raise NotesError(f"{path.name}: missing columns {', '.join(missing)}")
            return [{k: (v or "").strip() for k, v in r.items() if k} for r in reader]
    except OSError as e:
        raise NotesError(f"cannot read {path}: {e.strerror}")


def read_gold_ids(gold: Path) -> list:
    return list(dict.fromkeys(r["doc_id"] for r in _read_csv(gold, ["doc_id"]) if r["doc_id"]))


def read_manifest(folder: Path) -> dict:
    """{pack_id: [doc_id, ...]}, or {} if there is no manifest yet."""
    path = folder / MANIFEST
    if not path.exists():
        return {}
    out = {}
    for r in _read_csv(path, MANIFEST_FIELDS):
        out.setdefault(r["pack_id"], []).append(r["doc_id"])
    return out


def read_notes(folder: Path) -> list:
    path = folder / NOTES
    return _read_csv(path, NOTE_FIELDS) if path.exists() else []


def check(gold: Path, folder: Path = None):
    """Return (problems, warnings) for one gold file. A problem means the gold set must not be used."""
    folder = folder or notes_dir(gold)
    pack, ids = pack_of(gold), set(read_gold_ids(gold))
    manifest = read_manifest(folder)
    if not manifest:
        return [], [f"no {MANIFEST} in {folder}: removals from the gold set cannot be checked"]
    known = manifest.get(pack, [])
    if not known:
        return [], [f"{pack} is not in {MANIFEST}: run gold_notes.py --record after the gold file is built"]
    notes = [n for n in read_notes(folder) if n["pack_id"] == pack]
    problems, warnings = [], []
    for n in notes:
        if n["decision"] not in DECISIONS:
            problems.append(f"{NOTES}: {n['doc_id']}: decision must be removed or kept, not {n['decision']!r}")
    removed = {n["doc_id"]: n for n in notes if n["decision"] == "removed"}
    for doc_id in known:
        if doc_id in ids:
            if doc_id in removed:
                warnings.append(f"{doc_id}: {NOTES} says removed, but it is still in {gold.name}")
            continue
        n = removed.get(doc_id)
        if n is None:
            problems.append(f"{doc_id} left the gold set without a note in {NOTES}")
        elif not n["second_reader"]:
            problems.append(f"{doc_id}: the note has no second_reader")
        elif n["second_reader"].lower() == n["raised_by"].lower():
            problems.append(f"{doc_id}: the second_reader is the person who raised it ({n['raised_by']})")
        elif not n["reason"]:
            problems.append(f"{doc_id}: the note has no reason")
    new = len(ids - set(known))
    if new:
        warnings.append(f"{new} documents of {gold.name} are not in {MANIFEST} yet: run gold_notes.py --record")
    return problems, warnings


def record(golds, folder: Path) -> int:
    """Add the documents of the gold files that the manifest does not have yet. Return how many were added."""
    path = folder / MANIFEST
    manifest = read_manifest(folder)
    today = datetime.date.today().isoformat()
    rows = [(pack_of(g), d) for g in golds for d in read_gold_ids(g) if d not in set(manifest.get(pack_of(g), []))]
    if not rows:
        return 0
    new_file = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new_file:
            w.writerow(MANIFEST_FIELDS)
        w.writerows((p, d, today) for p, d in rows)
    if not (folder / NOTES).exists():
        (folder / NOTES).write_text(",".join(NOTE_FIELDS) + "\n", encoding="utf-8")
    return len(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check that gold documents leave a gold set only with a second reader's note.")
    ap.add_argument("--gold-dir", type=Path, default=DEFAULT_GOLD_DIR)
    ap.add_argument("--pack", help="only this pack, for example en-dclm")
    ap.add_argument("--record", action="store_true", help="add new gold documents to the manifest")
    args = ap.parse_args(argv)

    golds = sorted(args.gold_dir.glob(f"{args.pack or '*'}_gold.csv"))
    if not golds:
        print(f"error: no {args.pack or '<pack_id>'}_gold.csv in {args.gold_dir}", file=sys.stderr)
        return 2
    try:
        if args.record:
            print(f"{MANIFEST}: {record(golds, args.gold_dir)} documents added")
        bad = 0
        for g in golds:
            problems, warnings = check(g, args.gold_dir)
            print(f"{pack_of(g)}: " + ("OK" if not problems else f"{len(problems)} problems"))
            for p in problems:
                print(f"  problem: {p}")
            for w in warnings:
                print(f"  warning: {w}")
            bad += bool(problems)
    except NotesError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
