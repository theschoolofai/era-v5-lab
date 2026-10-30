#!/usr/bin/env python3
"""fetch_sheets.py - download the labels.csv of every reader of some packs from the lab's pull requests.

It reads public files with the gh command (run `gh auth login` once). Nothing is posted or changed on GitHub, and no
token is printed or saved by this script.

Usage
  python3 fetch_sheets.py --packs ind-te-fw2 ind-te-sangraha-v --out SHEETS_DIR [--repo theschoolofai/era-v5-lab]
Writes SHEETS_DIR/<pack_id>/<handle>.csv (the layout gold_indic.py reads) and lists what it found. A pull request
that was closed without merging is a withdrawn reader and is skipped. A folder that is not the author's own GitHub
handle is skipped (pr-guard rejects it too). If one reader has several pull requests, the newest one is used.
Exit codes: 0 done, 2 could not run.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PACK = re.compile(r"^[a-z0-9][a-z0-9-]{1,60}$")
HANDLE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$")


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip()[-300:] or f"gh exit {r.returncode}")
    return r.stdout


def jq_filter(packs):
    """The jq program that keeps only the labels.csv of these packs. Pack ids are checked first (a-z, 0-9, '-'), so no
    regex escaping is needed: re.escape would write '\\-', which jq does not accept."""
    keep = "|".join(packs)
    return ('[.[] | .files = [(.files // [])[] | select(.path | test("^diagnosis/submissions/(' + keep + ')/[^/]+/labels\\\\.csv$"))]'
            " | select(.files | length > 0) | {number, state, author: .author.login, files: [.files[].path]}]")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Download readers' labels.csv from the lab's pull requests.")
    ap.add_argument("--packs", required=True, nargs="+")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--repo", default="theschoolofai/era-v5-lab")
    a = ap.parse_args(argv)
    if not all(PACK.match(p) for p in a.packs) or not re.match(r"^[\w.-]+/[\w.-]+$", a.repo):
        print("error: a pack id or the repo name is not valid", file=sys.stderr)
        return 2
    jq = jq_filter(a.packs)  # gh filters the list itself: the whole list of pull requests is too long to read in one piece
    try:
        prs = json.loads(gh("pr", "list", "-R", a.repo, "--state", "all", "--limit", "1000",
                            "--json", "number,state,author,files", "--jq", jq) or b"[]")
    except (RuntimeError, ValueError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"error: could not list the pull requests ({e}). Is gh installed and logged in?", file=sys.stderr)
        return 2
    newest = {}  # (pack, handle) -> (pr number, path)
    for pr in sorted(prs, key=lambda p: p["number"]):
        for path in pr["files"]:
            _, _, pack, handle, _ = path.split("/")
            if pr["state"] == "CLOSED":
                print(f"skip  PR #{pr['number']} {pack}/{handle}: closed without merge")
            elif handle.lower() != pr["author"].lower() or not HANDLE.match(handle):
                print(f"skip  PR #{pr['number']} {pack}/{handle}: the folder is not the author's own handle")
            else:
                newest[(pack, handle.lower())] = (pr["number"], path)
    if not newest:
        print("nothing found for those packs", file=sys.stderr)
        return 2
    for (pack, handle), (number, path) in sorted(newest.items()):
        try:
            raw = gh("api", "-H", "Accept: application/vnd.github.raw", f"repos/{a.repo}/contents/{path}?ref=refs/pull/{number}/head")
            raw.decode("utf-8-sig")
        except (RuntimeError, UnicodeDecodeError, subprocess.TimeoutExpired) as e:
            print(f"FAIL  PR #{number} {pack}/{handle}: {str(e)[:100]}")
            continue
        dest = a.out / pack / f"{handle}.csv"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        lines = raw.count(b"\n")  # not inside the f-string: a backslash there is a syntax error before Python 3.12
        print(f"saved PR #{number:<4} {pack}/{handle}.csv  {len(raw)} bytes, {lines} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
