"""Profile decontam_check output (no text): per benchmark, flagged docs, distinct items, and docs by max coverage band."""
import json, sys, collections
for p in sys.argv[1:]:
    per = collections.defaultdict(lambda: {"docs": 0, "items": set(), "bands": collections.Counter()})
    docs_band = collections.Counter(); n = 0
    for line in open(p):
        r = json.loads(line); n += 1
        best = 0
        for h in r["hits"]:
            b = h["item"].split(":")[0]
            cov = 1.0 if "canary" in h else h.get("coverage", 0)
            per[b]["items"].add(h["item"]); best = max(best, cov)
        for b in {h["item"].split(":")[0] for h in r["hits"]}:
            cb = max((1.0 if "canary" in h else h.get("coverage", 0)) for h in r["hits"] if h["item"].startswith(b + ":"))
            per[b]["docs"] += 1
            per[b]["bands"]["<0.1" if cb < .1 else "0.1-0.5" if cb < .5 else ">=0.5"] += 1
        docs_band["<0.1" if best < .1 else "0.1-0.5" if best < .5 else ">=0.5"] += 1
    print(f"== {p.split('/')[-2]}: flagged {n}; by max coverage {dict(docs_band)}")
    for b, v in sorted(per.items(), key=lambda kv: -kv[1]["docs"]):
        print(f"   {b:16} docs {v['docs']:5}  distinct items {len(v['items']):5}  bands {dict(v['bands'])}")
