"""The lab canary (G9): the string, the stamp, the benchmark canary files and the search.

There is one lab-wide canary string, recorded once in ../CANARY.md (TSAI, G9 chat, 2 Nov).
This module reads it from there. Every eval file that Team 9 publishes carries the canary line,
so canary_scan.py (and decontam_check.py, through fpset.Fingerprints) can tell when eval data
reached training data.

The canary is plain ASCII text, not a special token (TSAI, G10 chat, 29 Oct): a special token
never comes out of normal tokenization, so leaked text would not contain it.
"""

import json
import re
from pathlib import Path

CANARY_FILE = Path(__file__).resolve().parent.parent / "CANARY.md"
_LINE = re.compile(r"^(ERA V5 LAB EVALUATION DATA\. .* canary GUID (era-v5-lab:eval:[0-9a-f-]{36}))$", re.M)


def _read_record(path=CANARY_FILE):
    """(line, GUID) from CANARY.md. Exactly one distinct canary line must be recorded there."""
    found = set(_LINE.findall(Path(path).read_text(encoding="utf-8")))
    if len(found) != 1:
        raise ValueError(f"{path}: expected one recorded canary line, found {len(found)}")
    return found.pop()


LAB_CANARY_LINE, LAB_CANARY = _read_record()  # the line written into eval files; the searched-for GUID
LAB_CANARY_ID = "era-v5-lab"
MARKDOWN_LINE = f"<!-- {LAB_CANARY_LINE} -->"


def stamp(record):
    """Return a copy of a dict with the canary line as its first key."""
    return {"canary": LAB_CANARY_LINE, **{k: v for k, v in record.items() if k != "canary"}}


def read_canary_file(path):
    """The canary strings in one canaries.txt: one per line, stripped, blank lines skipped."""
    return [s for s in (line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()) if s]


def load_canaries(fingerprint_dir=None):
    """Canary string -> source ID: the lab canary, plus the benchmark canaries of a fingerprint set
    (the benchmarks whose entry in the set's MANIFEST.json has canaries, for example GPQA and HLE).
    fingerprint_dir=None gives the lab canary only. A folder without MANIFEST.json is an error,
    so a wrong path cannot quietly drop the benchmark canaries."""
    canaries = {LAB_CANARY: LAB_CANARY_ID}
    if fingerprint_dir is None:
        return canaries
    d = Path(fingerprint_dir)
    manifest = d / "MANIFEST.json"
    if not manifest.is_file():
        raise FileNotFoundError(f"{manifest} not found: not a fingerprint set folder")
    for bid, bm in sorted(json.loads(manifest.read_text(encoding="utf-8"))["benchmarks"].items()):
        if bm.get("canaries"):
            for c in read_canary_file(d / bid / "canaries.txt"):
                canaries.setdefault(c, bid)
    return canaries


def find(text, canaries):
    """Every occurrence of every canary in text, as (offset, canary), by offset."""
    out = []
    for c in canaries:
        if not c:
            raise ValueError("empty canary string")
        i = text.find(c)
        while i != -1:
            out.append((i, c))
            i = text.find(c, i + 1)
    return sorted(out)
