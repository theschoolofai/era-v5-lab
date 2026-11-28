"""F2 rates per lane from a finished f2_pool.py / run_f2.py output: rows, text bytes, p1536 tokens, worker seconds.

  python -I teams/01-data-a/tools/f2_rates.py <f2_out_dir> <input_root> <p1536 tokenizer.json> [--wall S --workers N]

<f2_out_dir> holds <rel>.f2.json for each input part <input_root>/<rel>; seconds are run_f2.py's per-part times.
Lane = the pack name before its first '-' (cadj, code, en, ind, math, sci). Prints a table and a JSON line.
"""
import argparse, glob, hashlib, json, os
from collections import defaultdict
import pyarrow.parquet as pq
from tokenizers import Tokenizer

P1536 = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"
ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("root"); ap.add_argument("tok")
ap.add_argument("--wall", type=float); ap.add_argument("--workers", type=int); a = ap.parse_args()
assert hashlib.sha256(open(a.tok, "rb").read()).hexdigest() == P1536, "not the frozen p1536"
tok = Tokenizer.from_file(a.tok)
agg = defaultdict(lambda: {"parts": 0, "rows": 0, "bytes": 0, "tokens": 0, "seconds": 0.0, "dropped": 0})
for f in sorted(glob.glob(os.path.join(a.out, "**", "*.f2.json"), recursive=True)):
    d = json.load(open(f)); rel = os.path.relpath(f, a.out)[:-len(".f2.json")]
    texts = pq.read_table(os.path.join(a.root, rel), columns=["text"]).column(0).to_pylist()
    n_tok = sum(len(e.ids) for e in tok.encode_batch(texts, add_special_tokens=False))
    for k in (rel.split("/")[0].split("-")[0], "ALL"):
        g = agg[k]; g["parts"] += 1; g["rows"] += d["rows"]; g["bytes"] += sum(len(t.encode()) for t in texts)
        g["tokens"] += n_tok; g["seconds"] += d["seconds"]; g["dropped"] += d["dropped_by_f2"]
print(f"{'lane':5} {'parts':>5} {'rows':>10} {'text MB':>9} {'tokens':>14} {'worker s':>9} {'MB/s/w':>7} {'tok/s/w':>9} {'dropped':>7}")
for k, g in sorted(agg.items(), key=lambda kv: (kv[0] == "ALL", kv[0])):
    print(f"{k:5} {g['parts']:5} {g['rows']:10,} {g['bytes']/1e6:9,.0f} {g['tokens']:14,} {g['seconds']:9,.0f} {g['bytes']/1e6/g['seconds']:7.2f} {g['tokens']/g['seconds']:9,.0f} {g['dropped']:7,}")
tot = agg["ALL"]
if a.wall and a.workers:
    print(f"wall {a.wall:.0f} s with {a.workers} workers: {tot['tokens']/a.wall:,.0f} tokens/s for the run, {tot['tokens']/a.wall/a.workers:,.0f} per worker")
print(json.dumps({k: v for k, v in agg.items()}))
