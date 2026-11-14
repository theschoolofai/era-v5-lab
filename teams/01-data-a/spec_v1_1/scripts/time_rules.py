#!/usr/bin/env python3
"""Time every rule of a medicine sheet on every document of whole packs (TSAI speed rule, 14 Nov 2026).

For each pack it prints:
  - each rule alone, on every doc: seconds, docs/s, the slowest doc (id and ms), and its fixes, drops, errors and timeouts;
  - the whole sheet in order, as clean.py runs it (a fix carries into the next rule, a drop stops): the wall time.
The sheet is loaded with teams/01-data-a/harmtest/harm_test.py's load_rules. The pack's sha256 is compared with
results/sheets/<pack>_harm.json when there is one, so the timed file is the file the harm test used.
Prints doc_ids and numbers only, never text. Exits 1 if a rule raised or ran over the time limit on any doc.

From teams/01-data-a:
  python3 -I spec_v1_1/scripts/time_rules.py --sheet spec_v1_1/sheets/specv1_1.md --pack <pack>.parquet [...]
                                             [--timeout 5] [--json <file>]
"""
import argparse
import hashlib
import json
import signal
import sys
import time
from pathlib import Path

DATA_A = Path(__file__).resolve().parents[2]  # teams/01-data-a
HARM_REPORTS = DATA_A / "spec_v1_1" / "results" / "sheets"
HAS_ALARM = hasattr(signal, "setitimer")  # no per-doc limit on Windows


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_pack(path):
    """Every doc of a Parquet pack, as harm_test.py's documents: doc_id, text, and url, lang_label, pack_id if present.
    A file without a pack_id column gets its file name, as harm_test.py expects."""
    import pyarrow.parquet as pq
    names = pq.read_schema(path).names
    cols = ["doc_id", "text"] + [c for c in ("url", "lang_label", "pack_id") if c in names]
    rows = pq.read_table(path, columns=cols).to_pylist()
    for r in rows:
        r.setdefault("pack_id", Path(path).stem)
    return rows


def call(rule, doc, timeout):
    """(verdict, new text, seconds). verdict is keep, fix, drop, error or timeout. A fix that changes nothing is keep."""
    if HAS_ALARM:
        signal.setitimer(signal.ITIMER_REAL, timeout)
    start = time.perf_counter()
    try:
        out = rule(dict(doc))
        if isinstance(out, tuple):
            verdict, new = out[0], (out[1] if out[0] == "fix" else doc["text"])
        else:
            verdict, new = ("drop" if out is True else "keep"), doc["text"]
        if verdict == "fix" and new == doc["text"]:
            verdict = "keep"
    except Timeout:
        verdict, new = "timeout", doc["text"]
    except Exception:
        verdict, new = "error", doc["text"]
    finally:
        if HAS_ALARM:
            signal.setitimer(signal.ITIMER_REAL, 0)
    return verdict, new, time.perf_counter() - start


def time_rule(rule, docs, timeout):
    total, worst, worst_id = 0.0, 0.0, "-"
    counts = {"keep": 0, "fix": 0, "drop": 0, "error": 0, "timeout": 0}
    for d in docs:
        verdict, _, s = call(rule, d, timeout)
        total += s
        counts[verdict] += 1
        if s > worst:
            worst, worst_id = s, d["doc_id"]
    return {"seconds": round(total, 4), "docs_per_s": round(len(docs) / max(total, 1e-9)),
            "slowest_doc": worst_id, "slowest_ms": round(worst * 1000, 2), **counts}


def time_in_order(rules, docs, timeout):
    """(wall seconds, dropped, errors) for the whole sheet in order."""
    start, dropped, errors = time.perf_counter(), 0, 0
    for d in docs:
        doc = dict(d)
        for rule in rules.values():
            verdict, new, _ = call(rule, doc, timeout)
            if verdict in ("error", "timeout"):
                errors += 1
            if verdict == "drop":
                dropped += 1
                break
            doc["text"] = new
    return time.perf_counter() - start, dropped, errors


def harm_check(pack, sha):
    report = HARM_REPORTS / f"{Path(pack).stem}_harm.json"
    if not report.exists():
        return "no harm report to compare"
    same = json.loads(report.read_text(encoding="utf-8")).get("pack_sha256") == sha
    return "same file as the harm run" if same else "DIFFERENT file from the harm run"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sheet", required=True, type=Path)
    ap.add_argument("--pack", required=True, nargs="+", type=Path)
    ap.add_argument("--timeout", type=float, default=5.0, help="seconds for one rule on one doc (default 5)")
    ap.add_argument("--json", type=Path, help="also write the numbers to this file")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(DATA_A / "harmtest"))
    import harm_test  # only its loader is used; the file is not changed
    rules = harm_test.load_rules(a.sheet)[0]["RULES_BY_ID"]
    if HAS_ALARM:
        signal.signal(signal.SIGALRM, _alarm)
    report = {"sheet": a.sheet.name, "rules": len(rules), "timeout": a.timeout, "packs": {}}
    print(f"sheet {a.sheet.name}: {len(rules)} rules")
    started, bad = time.perf_counter(), 0
    for pack in a.pack:
        sha = sha256(pack)
        t0 = time.perf_counter()
        docs = read_pack(pack)
        read_s = time.perf_counter() - t0
        print(f"\n== {pack.stem}: {len(docs)} docs, sha256 {sha[:12]}… ({harm_check(pack, sha)}), read in {read_s:.2f} s")
        print(f"   {'rule':10} {'seconds':>8} {'docs/s':>9} {'slowest doc':>18} {'ms':>8} {'fix':>5} {'drop':>5} {'err':>4} {'t/o':>4}")
        per = {}
        for rid, rule in rules.items():
            r = per[rid] = time_rule(rule, docs, a.timeout)
            bad += r["error"] + r["timeout"]
            print(f"   {rid:10} {r['seconds']:8.3f} {r['docs_per_s']:9} {r['slowest_doc']:>18} {r['slowest_ms']:8.2f} "
                  f"{r['fix']:5} {r['drop']:5} {r['error']:4} {r['timeout']:4}")
        wall, dropped, errors = time_in_order(rules, docs, a.timeout)
        print(f"   ALL IN ORDER: {wall:.3f} s wall for {len(docs)} docs ({len(docs) / max(wall, 1e-9):.0f} docs/s), "
              f"{dropped} dropped")
        report["packs"][pack.stem] = {"docs": len(docs), "sha256": sha, "harm_report": harm_check(pack, sha),
                                      "read_seconds": round(read_s, 3), "rules": per,
                                      "in_order_seconds": round(wall, 3), "in_order_dropped": dropped,
                                      "in_order_errors": errors}
    total = time.perf_counter() - started
    report["wall_seconds"] = round(total, 2)
    print(f"\nall packs: {total:.1f} s wall; rule errors or timeouts: {bad}")
    if a.json:
        a.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
