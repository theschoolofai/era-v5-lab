#!/usr/bin/env python3
"""Recover the results zip that eval_mini.ipynb's last cell prints as base64.

    python extract_results.py eval_mini.ipynb [--out DIR]

With a Colab kernel attached from VS Code, the notebook's files stay on Google's VM; the last cell prints the
results zip between EVAL_MINI_ZIP_BEGIN / EVAL_MINI_ZIP_END, and saving the notebook keeps that output locally.
"""
import argparse, base64, json, zipfile
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("notebook", type=Path)
ap.add_argument("--out", type=Path, help="directory for the zip (default: next to the notebook)")
args = ap.parse_args()

text = "".join("".join(o.get("text", "")) for c in json.loads(args.notebook.read_text())["cells"]
               for o in c.get("outputs", []) if o.get("output_type") == "stream")
start = text.rfind("EVAL_MINI_ZIP_BEGIN")
if start < 0:
    raise SystemExit("no results in this notebook: run all cells to the end, then save it in VS Code")
header, rest = text[start:].split("\n", 1)
_, name, size = header.split()
blob = "".join(rest.split("EVAL_MINI_ZIP_END", 1)[0].split())
if len(blob) != int(size):
    raise SystemExit(f"output is incomplete ({len(blob)} of {size} characters): was the cell output truncated?")
out = (args.out or args.notebook.parent) / name
out.write_bytes(base64.b64decode(blob))
with zipfile.ZipFile(out) as z:
    bad = z.testzip()
    if bad:
        raise SystemExit(f"{out}: corrupt member {bad}")
    print(f"wrote {out}: {len(z.namelist())} files, {out.stat().st_size} bytes")
