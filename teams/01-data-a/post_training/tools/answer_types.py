"""Share of each pool's answers that Team 10's math_verifier.parse_number reads as an exact number (answer_type
"number"), guessable answers (one letter A-E, yes/no/true/false), answers > MAX_ANSWER_CHARS, and the rest (symbolic:
string match only). Imports Team 10's math_verifier.py (g10-week5-post-training @ 72128349) unchanged."""
import sys, json, re, importlib.util
from pathlib import Path
import pyarrow.parquet as pq
spec = importlib.util.spec_from_file_location("mv", sys.argv[1]); mv = importlib.util.module_from_spec(spec); spec.loader.exec_module(mv)
GUESS = re.compile(r"^\(?[a-e]\)?$|^(yes|no|true|false)$")
for pool in sys.argv[2:]:
    P = Path.home() / "Workspace/era-v5-data/g1-pt/pools" / pool
    t = pq.read_table(P / "docs.parquet", columns=["doc_id", "answer", "first_of_dup"]).to_pylist()
    fl = {json.loads(l)["doc_id"] for l in open(P / "f2_flagged.jsonl")}
    c = {"rows": 0, "number": 0, "guessable": 0, "too_long": 0, "symbolic": 0, "empty": 0}
    keep = dict(c)
    for r in t:
        a = r["answer"] or ""
        if not a.strip(): k = "empty"
        elif len(a) > mv.MAX_ANSWER_CHARS: k = "too_long"
        elif mv.parse_number(a) is not None: k = "number"
        elif GUESS.match(mv.normalise(mv._unwrap(a))): k = "guessable"
        else: k = "symbolic"
        c["rows"] += 1; c[k] += 1
        if r["first_of_dup"] and r["doc_id"] not in fl:
            keep["rows"] += 1; keep[k] += 1
    print(json.dumps({"pool": pool, "all": c, "unique_and_f2_clean": keep}))
