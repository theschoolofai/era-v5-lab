"""G1 (Team 1) check for Team 10's RL math pool: which candidate rows share text with MATH / MATH-500 / GSM8K / Omni-MATH.

Runs on Kaggle (eval firewall: benchmark text never goes to the dev machine). CPU only.
Method = Team 10's math500_guard.py: question lowercased and whitespace collapsed; a row is flagged for a benchmark
split if it equals an item exactly or shares any 13-word run with one. Output (/kaggle/working/math_overlap.json) holds
only counts, candidate doc_ids (the same ids as the local docs.parquet) and benchmark item ids. No text.
"""
import json, re, time, os, glob
from pathlib import Path
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

T0 = time.time()
api = HfApi()
TMP = Path("/tmp/g1"); TMP.mkdir(exist_ok=True)


def norm(s):
    return " ".join(re.sub(r"\s+", " ", (s or "").lower()).split())


def grams(s, n=13):
    w = norm(s).split()
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def dl(repo, f, rev):
    return hf_hub_download(repo, f, repo_type="dataset", revision=rev, cache_dir=str(TMP / "hf"))


def files_of(repo, rev, pred):
    return sorted(s.rfilename for s in api.dataset_info(repo, revision=rev).siblings if pred(s.rfilename))


# ---- benchmarks (pinned where Team 10 pinned; else the current sha, recorded) ----
bench = {}   # split name -> list of (item_id, text)
pins = {}
rev = "21a5633873b6a120296cce3e2df9d5550074f4a3"; pins["EleutherAI/hendrycks_math"] = rev
for f in files_of("EleutherAI/hendrycks_math", rev, lambda x: x.endswith(".parquet")):
    split = "math_train" if "/train" in f else "math_test" if "/test" in f else None
    if not split: continue
    subj = f.split("/")[0]
    for i, r in enumerate(pq.read_table(dl("EleutherAI/hendrycks_math", f, rev), columns=["problem"]).to_pylist()):
        bench.setdefault(split, []).append((f"{split}:{subj}:{i}", r["problem"]))
for repo, pred, split, col, idcol in [
        ("HuggingFaceH4/MATH-500", lambda x: x.endswith(".jsonl"), "math500", "problem", "unique_id"),
        ("openai/gsm8k", lambda x: x.startswith("main/") and x.endswith(".parquet"), None, "question", None),
        ("KbsdJames/Omni-MATH", lambda x: x.endswith(".jsonl"), "omni_math", "problem", None)]:
    r_ = api.dataset_info(repo).sha; pins[repo] = r_
    for f in files_of(repo, r_, pred):
        p = dl(repo, f, r_)
        rows = pq.read_table(p).to_pylist() if f.endswith(".parquet") else [json.loads(l) for l in open(p, encoding="utf-8")]
        sp = split or ("gsm8k_train" if "train" in f else "gsm8k_test")
        for i, r in enumerate(rows):
            bench.setdefault(sp, []).append((f"{sp}:{r.get(idcol) if idcol else i}", r[col]))
exact, gram_ix = {}, {}
for sp, items in bench.items():
    exact[sp] = {norm(t): iid for iid, t in items}
    gi = {}
    for iid, t in items:
        for g in grams(t):
            gi.setdefault(g, set()).add(iid)
    gram_ix[sp] = gi
print("benchmarks", {k: len(v) for k, v in bench.items()}, round(time.time() - T0), "s", flush=True)


# ---- candidate pools at the pinned revisions; ids = the local docs.parquet ids ----
def jsonl_pool(key, repo, rev_, f, idf):
    for i, line in enumerate(open(dl(repo, f, rev_), encoding="utf-8")):
        r = json.loads(line)
        yield f"{key}:{idf(i, r)}", r.get("question") or ""


def parquet_pool(key, repo, rev_, prefix, col):
    for f in files_of(repo, rev_, lambda x: x.startswith(prefix) and x.endswith(".parquet")):
        stem = f.rsplit("/", 1)[-1].split(".")[0]
        p = dl(repo, f, rev_)
        for i, q in enumerate(pq.read_table(p, columns=[col]).column(0).to_pylist()):
            yield f"{key}:{stem}:{i}", q or ""
        os.remove(p)


POOLS = {
    "omr_rl": lambda: jsonl_pool("omr_rl", "nvidia/Nemotron-RL-math-OpenMathReasoning", "219bf0170cd87cd5db2bbf33715ce9ea43a2c59c", "train.jsonl", lambda i, r: i),
    "so_rl": lambda: jsonl_pool("so_rl", "nvidia/Nemotron-RL-math-stack_overflow", "81ee859274bd8294ed270511c9fc688f60bd2492", "train.jsonl", lambda i, r: i),
    "rlmath_v2": lambda: jsonl_pool("rlmath_v2", "nvidia/Nemotron-RL-Math-v2", "804418c1d4eceeaa453d895954887c0975e79121", "data/train.jsonl", lambda i, r: r["uuid"]),
    "deepmath": lambda: parquet_pool("deepmath", "zwhe99/DeepMath-103K", "5cf055d1fe3d7a2eb19719ac020211469736ae44", "data/train-", "question"),
    "openr1": lambda: parquet_pool("openr1", "open-r1/OpenR1-Math-220k", "e4e141ec9dea9f8326f4d347be56105859b2bd68", "data/train-", "problem"),
    "sftmath_v4": lambda: parquet_pool("sftmath_v4", "nvidia/Nemotron-SFT-Math-v4", "84d42ad0cb960f07f951b9baa9ed2b46a5a18c66", "data/train-", "problem"),
}
out = {"method": "exact normalised match or any shared 13-word run (Team 10 math500_guard.py normaliser)",
       "benchmark_items": {k: len(v) for k, v in bench.items()}, "benchmark_pins": pins, "pools": {}}
for key, gen in POOLS.items():
    t = time.time(); n = 0
    res = {sp: {"exact": 0, "gram": 0, "doc_ids": [], "items": set()} for sp in bench}
    for did, q in gen():
        n += 1
        nq = norm(q); gq = grams(q)
        for sp in bench:
            hit_items = set()
            if nq and nq in exact[sp]:
                res[sp]["exact"] += 1; hit_items.add(exact[sp][nq])
            gi = gram_ix[sp]
            gh = set().union(*(gi[g] for g in gq if g in gi)) if gq else set()
            if gh:
                res[sp]["gram"] += 1; hit_items |= gh
            if hit_items:
                res[sp]["doc_ids"].append(did); res[sp]["items"] |= hit_items
    for sp in res:
        res[sp]["flagged_rows"] = len(res[sp]["doc_ids"]); res[sp]["distinct_items"] = len(res[sp].pop("items"))
    out["pools"][key] = {"rows": n, "by_benchmark": res, "seconds": round(time.time() - t)}
    print(key, n, {sp: (v["exact"], v["gram"], v["flagged_rows"]) for sp, v in res.items()}, round(time.time() - t), "s", flush=True)
out["seconds"] = round(time.time() - T0)
Path("/kaggle/working/math_overlap.json").write_text(json.dumps(out))
print("done", out["seconds"], "s")
