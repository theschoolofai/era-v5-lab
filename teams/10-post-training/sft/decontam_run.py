"""Decontamination run for one SFT set (G10).

    python decontam_run.py --set sft-code-codeforces-cots --input out/codeforces-cots.jsonl --out-dir decontam_out

For one set it does what the instruction asks and what the eval firewall requires:

1. Runs Team 9's `decontam_check.py` on the FULL fingerprint set (no --benchmarks, --tags or --exclude).
   The first stderr line of the checker gives the set_sha256 and the scope. A scope other than "full set",
   or a set_sha256 other than the pinned one (fingerprints v2, lab PR #280), is refused.
2. Runs Team 9's `canary_scan.py` on the same files. A canary is a leak, never a pass.
3. Writes the set without the flagged and canary documents (`<set>.clean.jsonl` or `.parquet`).
   A JSONL file is copied byte for byte, row by row.
4. Reconciles: rows in = rows kept + rows removed, ids are unique, every flagged id is an input id,
   no kept id is flagged. It then runs the checker again on the clean file, which must flag 0 documents.
5. Writes `<set>.record.json` with counts, ids, item ids, offsets, sha256 values, the hashes of the tools and
   the benchmarks of the fingerprint set. `decontam_report.py` turns the records into `sft/decontam_report.md`.

No document text is printed or written anywhere. Only counts, document ids, benchmark item ids and character
offsets leave this script (eval firewall, section 4). The input files are `convert.py` outputs
(`id` and `text`), or any JSONL or Parquet file with an id column and a text column.

Exit code: 0 = every check passed (flagged documents may exist: they are removed and recorded),
1 = a canary was found or a reconciliation check failed (stop using the file, post in G9: item or canary id,
document id and offset only), 2 = a tool could not run or its output could not be read.
Run it with plain `python`, not `python -I`: Team 9's scripts import their neighbours from their own folder.
Keep `--out-dir` out of Git: the clean files and the records hold training rows and document ids.
"""

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TEAMS = Path(__file__).resolve().parents[2]
DEFAULT_TOOLS = Path(os.environ.get("G10_DECONTAM_TOOLS", TEAMS / "09-evaluation" / "decontam"))
PINNED_SET_SHA256 = "2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a"  # fingerprints v2, lab PR #280
TOOL_FILES = ("decontam_check.py", "canary_scan.py", "fpset.py", "normalize.py", "lab_canary.py")
HEAD_RE = re.compile(r"^fingerprints (\S+) set_sha256 ([0-9a-f]{64}) \((.*)\)$")
SUM_RE = re.compile(r"^docs (\d+) flagged (\d+) \([^)]*\) by benchmark (\{.*\})$")
CANARY_SUM_RE = re.compile(r"^docs (\d+) with_canary (\d+) hits (\d+)(?: files_skipped (\d+))?$")


class RunError(Exception):
    """A tool could not run, or its output could not be read (exit code 2)."""


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_ids(path, id_field):
    """The document ids of one file, in order, as the checker reads them (str of the id)."""
    path = Path(path)
    if path.suffix == ".parquet":
        import pyarrow.parquet as pq
        try:
            col = pq.read_table(path, columns=[id_field]).column(id_field)
        except Exception as e:  # a missing column or a bad file
            raise RunError(f"{path.name}: cannot read column '{id_field}': {e}") from e
        return [str(i) for i in col.to_pylist()]
    if path.suffix != ".jsonl":
        raise RunError(f"{path.name}: only .jsonl and .parquet inputs are supported")
    ids = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            r = json.loads(line)
            if not isinstance(r, dict) or id_field not in r:
                raise RunError(f"{path.name} line {n}: no '{id_field}' field")
            ids.append(str(r[id_field]))
    return ids


def run_tool(tools, script, args):
    """Run one of Team 9's scripts. Paths in `args` must be absolute: the script runs in its own folder."""
    cmd = [sys.executable, str(Path(tools) / script), *map(str, args)]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(tools), env=env)
    return p.returncode, p.stdout, p.stderr


def parse_check(stdout, stderr):
    """Flagged documents, set_sha256, scope and the summary of one decontam_check.py run."""
    lines = [ln for ln in stderr.splitlines() if ln.strip()]
    heads = [m for m in map(HEAD_RE.match, lines) if m]
    sums = [m for m in map(SUM_RE.match, lines) if m]
    if len(heads) != 1 or len(sums) != 1:
        raise RunError("cannot read the summary lines of decontam_check.py (its output format changed?)")
    head, summ = heads[0], sums[0]
    flagged = {}
    for ln in stdout.splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        hits = r.get("hits", [])
        cov = [h["coverage"] for h in hits if "coverage" in h]
        flagged[str(r["doc_id"])] = {
            "n_items": r["n_items"],
            "benchmarks": sorted({h["item"].split(":")[0] for h in hits}),
            "hits": [{"item": h["item"], "grams": h.get("grams"), "item_grams": h.get("item_grams"),
                      "coverage": h.get("coverage"), "offset": h.get("offset")} for h in hits if "item" in h],
            "max_coverage": max(cov) if cov else None,
        }
    return {"version": head.group(1), "set_sha256": head.group(2), "scope": head.group(3),
            "docs": int(summ.group(1)), "flagged_count": int(summ.group(2)),
            "by_benchmark": ast.literal_eval(summ.group(3)), "flagged": flagged}


def parse_canary(rc, stdout, stderr):
    """Canary hits as (doc id, offset, short label); the canary string itself is never kept."""
    hits = []
    for ln in stdout.splitlines():
        if ln.strip():
            r = json.loads(ln)
            label = hashlib.sha256(r["canary"].encode("utf-8")).hexdigest()[:8]
            hits.append({"doc_id": str(r["doc_id"]), "offset": r["offset"], "canary_label": label})
    last = [ln for ln in stderr.splitlines() if ln.strip()]
    m = CANARY_SUM_RE.match(last[-1]) if last else None
    if rc not in (0, 1, 2) or not m:
        raise RunError("cannot read the summary line of canary_scan.py")
    return {"exit": rc, "docs": int(m.group(1)), "docs_with_canary": int(m.group(2)),
            "hits": hits, "files_skipped": int(m.group(4) or 0)}


def write_clean(path, out_path, id_field, drop):
    """Copy a file without the rows whose id is in `drop`. Returns the number of rows written."""
    path = Path(path)
    if path.suffix == ".parquet":
        import pyarrow as pa
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
        t = pq.read_table(path)
        ids = pc.cast(t.column(id_field), pa.string())
        mask = pc.invert(pc.is_in(ids, value_set=pa.array(sorted(drop), type=pa.string())))
        out = t.filter(mask)
        pq.write_table(out, out_path)
        return out.num_rows
    kept = 0
    with open(path, "rb") as src, open(out_path, "wb") as dst:  # bytes in, bytes out: rows are not re-encoded
        for line in src:
            if not line.strip():
                continue
            if str(json.loads(line)[id_field]) in drop:
                continue
            dst.write(line if line.endswith(b"\n") else line + b"\n")
            kept += 1
    return kept


def tool_info(tools):
    """sha256 of each Team 9 script that took part, and the git commit of the folder when it is a checkout."""
    info = {"files": {n: sha256_file(Path(tools) / n) for n in TOOL_FILES if (Path(tools) / n).is_file()}}
    try:
        p = subprocess.run(["git", "-C", str(tools), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
        info["git_commit"] = p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        info["git_commit"] = None
    return info


def fingerprint_benchmarks(folder):
    """The benchmark ids in the MANIFEST.json of the fingerprint set."""
    try:
        m = json.loads((Path(folder) / "MANIFEST.json").read_text(encoding="utf-8"))
        return sorted(m["benchmarks"])
    except (OSError, ValueError, KeyError) as e:
        raise RunError(f"cannot read the benchmark list in {folder}/MANIFEST.json: {e}") from e


def run_set(set_id, inputs, out_dir, tools=DEFAULT_TOOLS, id_field="id", text_field="text",
            fingerprints=None, expect_sha=PINNED_SET_SHA256, recheck=True):
    """Run, filter and reconcile one set. Returns the record (also written to <set>.record.json)."""
    tools = Path(tools).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = [Path(p).resolve() for p in inputs]  # the tools run in their own folder: paths must be absolute
    fingerprints = str(Path(fingerprints).resolve()) if fingerprints else None
    for need in ("decontam_check.py", "canary_scan.py"):
        if not (tools / need).is_file():
            raise RunError(f"{tools / need} not found: check out Team 9's decontam folder (lab main) "
                           "or set G10_DECONTAM_TOOLS")
    for p in inputs:
        if not p.is_file():
            raise RunError(f"{p} is not a file")
    suffixes = {p.suffix for p in inputs}
    if len(suffixes) != 1:
        raise RunError("give files of one kind (all .jsonl or all .parquet) for one set")
    ext = suffixes.pop()
    clean_files = ([out_dir / f"{set_id}.clean{ext}"] if len(inputs) == 1
                   else [out_dir / f"{set_id}.clean-{n:03d}{ext}" for n in range(len(inputs))])
    if set(clean_files) & set(inputs):
        raise RunError("an input file would be overwritten by its own clean file: use another --out-dir")

    ids = []
    for p in inputs:
        ids += read_ids(p, id_field)
    dup = [i for i, c in Counter(ids).items() if c > 1]

    fp_args = ["--fingerprints", fingerprints] if fingerprints else []
    common = [*inputs, "--id-field", id_field, "--text-field", text_field]
    # No --benchmarks, --tags or --exclude: only the full set is the formal check.
    rc, out, err = run_tool(tools, "decontam_check.py", [*common, *fp_args])
    if rc != 0:
        last = err.strip().splitlines()[-1] if err.strip() else ""
        raise RunError(f"decontam_check.py exited {rc}: {last}")
    check = parse_check(out, err)
    if check["scope"] != "full set":
        raise RunError(f"the checker ran a partial scope ({check['scope']}); only the full set counts")
    if expect_sha and check["set_sha256"] != expect_sha:
        raise RunError(f"set_sha256 {check['set_sha256']} is not the expected {expect_sha}")
    set_folder = fingerprints or str(tools.parent / "fingerprints" / check["version"])
    benchmarks = fingerprint_benchmarks(set_folder)

    crc, cout, cerr = run_tool(tools, "canary_scan.py", [*common, *fp_args])
    canary = parse_canary(crc, cout, cerr)

    id_set = set(ids)
    flagged_ids = set(check["flagged"])
    canary_ids = {h["doc_id"] for h in canary["hits"]}
    remove = flagged_ids | canary_ids
    kept = sum(write_clean(p, c, id_field, remove) for p, c in zip(inputs, clean_files))

    checks = {
        "ids_unique": not dup,
        "docs_match_checker": check["docs"] == len(ids) == canary["docs"],
        "flagged_ids_in_input": flagged_ids <= id_set,
        "canary_ids_in_input": canary_ids <= id_set,
        "flagged_count_matches": check["flagged_count"] == len(flagged_ids),
        "rows_in_eq_kept_plus_removed": len(ids) == kept + len(remove & id_set),
        "canary_scan_complete": canary["files_skipped"] == 0 and canary["exit"] in (0, 1),
    }
    recheck_res = None
    if recheck:
        rc2, out2, err2 = run_tool(tools, "decontam_check.py",
                                   [*clean_files, "--id-field", id_field, "--text-field", text_field, *fp_args])
        if rc2 != 0:
            raise RunError("decontam_check.py failed on the clean file")
        c2 = parse_check(out2, err2)
        recheck_res = {"docs": c2["docs"], "flagged": c2["flagged_count"], "set_sha256": c2["set_sha256"]}
        checks["clean_file_flags_0"] = (c2["flagged_count"] == 0 and c2["docs"] == kept
                                        and c2["set_sha256"] == check["set_sha256"])

    record = {
        "set": set_id,
        "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fingerprints": check["version"], "set_sha256": check["set_sha256"], "scope": check["scope"],
        "benchmarks": benchmarks,
        "tools": tool_info(tools),
        "inputs": [{"name": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in inputs],
        "rows_in": len(ids), "rows_flagged": len(flagged_ids), "rows_canary": len(canary_ids),
        "rows_removed": len(remove & id_set), "rows_kept": kept,
        "by_benchmark": check["by_benchmark"],
        "flagged": check["flagged"],
        "canary": {"exit": canary["exit"], "docs_with_canary": canary["docs_with_canary"],
                   "hits": canary["hits"], "files_skipped": canary["files_skipped"]},
        "clean": [{"name": p.name, "sha256": sha256_file(p)} for p in clean_files],
        "recheck_on_clean": recheck_res,
        "duplicate_ids": len(dup),
        "checks": checks, "ok": all(checks.values()) and not canary_ids,
    }
    (out_dir / f"{set_id}.record.json").write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
    return record


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", required=True, dest="set_id", help="set id from licences/licence_table.md")
    ap.add_argument("--input", required=True, nargs="+", help="JSONL or Parquet files of this set")
    ap.add_argument("--out-dir", required=True, help="where the clean file and the record go (keep it out of Git)")
    ap.add_argument("--tools", default=str(DEFAULT_TOOLS), help="Team 9's decontam folder")
    ap.add_argument("--id-field", default="id")
    ap.add_argument("--text-field", default="text")
    ap.add_argument("--fingerprints", help="TEST ONLY: another fingerprint set folder; use with --expect-sha ''")
    ap.add_argument("--expect-sha", default=PINNED_SET_SHA256, help="expected set_sha256 ('' to skip, test only)")
    ap.add_argument("--no-recheck", action="store_true",
                    help="skip the second pass over the clean file (decontam_report.py then refuses the record)")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.set_id):
        ap.error("--set must be a plain set id (letters, digits, '.', '_', '-')")
    try:
        rec = run_set(args.set_id, args.input, args.out_dir, args.tools, args.id_field, args.text_field,
                      args.fingerprints, args.expect_sha, not args.no_recheck)
    except (RunError, OSError, json.JSONDecodeError) as e:
        print(f"{args.set_id}: {e}", file=sys.stderr)
        return 2
    bad = [k for k, v in rec["checks"].items() if not v]
    status = "OK" if rec["ok"] else "FAILED: " + ", ".join(bad or ["canary found"])
    print(f"{rec['set']}: rows {rec['rows_in']} flagged {rec['rows_flagged']} canary {rec['rows_canary']} "
          f"kept {rec['rows_kept']} set_sha256 {rec['set_sha256'][:8]}... {status}")
    return 0 if rec["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
