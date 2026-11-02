#!/usr/bin/env python3
"""
mix_search.py
=============
Chooses the training-text mix for C1-C3 on the week-2 sample v0, one script block at a time, and writes it as a
train_bpe.py --mix file. No mix may make any language worse than the committed builds (trained on corpus60).

Each script block learns its merges only from its own languages' words, so each block can be tuned on its own. For
every block and every mix below this learns the block's merges exactly as train_bpe.py does (mixed_counts, then
learn_merges, with no normalizer and with the v1 normalizer). It then measures the block's languages (tokens per word)
for C1 (slots_c1.json), C2 (slots_v2.json) and C3 (slots_v2.json + normalizer v1).

Rule:
  1. Choose on FineWeb-2 dev + sample held-out half a. A mix is eligible when, for C1, C2 and C3, no language of the
     block is worse than with the committed mix (corpus60 as is). Take the eligible mix with the lowest mean change.
  2. Confirm on FineWeb-2 check + sample held-out half b, by the same rule. If it fails, the block keeps corpus60.
A block that keeps corpus60 gets no --mix entry, so train_bpe.py builds it exactly as the committed builds.

Mixes ("share" = the language's or source's part of the block's text by bytes; "raw" = the files as they are):
  Devanagari (Hi, Mr), Bengali (Bn, As): corpus60 raw; sample raw; sample with equal shares per language; the smaller
    language at 60%; corpus60 + sample with equal shares per language and per source; the same with the smaller
    language at 60%. As has no sample pack, so it is always corpus60.
  Single-language blocks: corpus60 raw; sample raw; corpus60 + sample at 50/50; corpus60 + sample at 70/30.
  Gurmukhi (Pa has no sample pack): corpus60 only.

Usage
-----
    python mix_search.py --c60 corpus60 --s0 corpus_s0 --heldout <fetch_heldout.py out> --heldout-s0 heldout_s0 \\
        --work <dir> --out mix_s0.json
(--heldout-s0 is sample_to_corpus.py --heldout-out. Paths in the --mix file are written as given, so pass relative
--c60 / --s0 paths to get a portable file.) About 25 minutes on 3 processes; word counts are cached in --work.
"""
import argparse
import json
import pickle
import sys
import time
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import train_bpe as tb  # noqa: E402
from slot_search import Builder, measure  # noqa: E402

CANDS = {"C1": ("none", "slots_c1.json"), "C2": ("none", "slots_v2.json"), "C3": ("v1", "slots_v2.json")}
SELECT, CONFIRM = ("dev", "s0a"), ("check", "s0b")
A = None  # parsed arguments; set in main and, in each worker process, by init()


def init(args):
    global A
    A = argparse.Namespace(**args)


def path(unit):
    src, lang = unit
    return Path(A.c60 if src == "c60" else A.s0) / f"{lang}.txt"


def share_mix(shares):
    """{(src, lang): share} -> [(unit, factor)]: factors from file bytes so each unit gets its share; smallest is 1."""
    k = max(path(u).stat().st_size / s for u, s in shares.items())
    return [(u, s * k / path(u).stat().st_size) for u, s in shares.items()]


def raw(*units):
    return [(u, 1.0) for u in units]


def mixes(langs):
    if len(langs) == 2:
        big, small = langs                                   # Hi/Mr, Bn/As: the second is the smaller language
        s_small = "c60" if small == "As" else "s0"           # As has no sample pack
        return {"committed": raw(("c60", big), ("c60", small)),
                "s0raw": raw(("s0", big), (s_small, small)),
                "s0eq": share_mix({("s0", big): .5, (s_small, small): .5}),
                "s0small60": share_mix({("s0", big): .4, (s_small, small): .6}),
                "uni_eq": share_mix({("c60", big): .25, ("s0", big): .25,
                                     **({("c60", small): .5} if small == "As" else
                                        {("c60", small): .25, ("s0", small): .25})}),
                "uni_small60": share_mix({("c60", big): .2, ("s0", big): .2,
                                          **({("c60", small): .6} if small == "As" else
                                             {("c60", small): .3, ("s0", small): .3})})}
    (lang,) = langs
    if not (Path(A.s0) / f"{lang}.txt").exists() or lang in ("Pa", "As"):
        return {"committed": raw(("c60", lang))}
    return {"committed": raw(("c60", lang)), "s0raw": raw(("s0", lang)),
            "uni_eq": share_mix({("c60", lang): .5, ("s0", lang): .5}),
            "uni_c60_70": share_mix({("c60", lang): .7, ("s0", lang): .3})}


def counts(unit, script, nk, pattern, norm):
    f = Path(A.work) / f"{unit[0]}_{unit[1]}_{script}_{nk}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    c = tb.word_counts([path(unit)], script, pattern, norm)
    f.write_bytes(pickle.dumps(c))
    return c


def run_block(script):
    import tiktoken
    t0 = time.time()
    sets = {"dev": Path(A.heldout) / "dev", "check": Path(A.heldout) / "check",
            "s0a": Path(A.heldout_s0) / "a", "s0b": Path(A.heldout_s0) / "b"}
    slots = {name: json.loads((HERE / name).read_text())["scripts"] for _, name in CANDS.values()}
    pattern = tiktoken.get_encoding("o200k_base")._pat_str
    ext = json.loads((HERE / "o200k_v2.json").read_text())
    norms = {"none": None, "v1": tb.load_normalizer("v1")}
    bs = {k: Builder(n, pattern, ext["prune"]) for k, n in norms.items()}
    id_bytes0, merges0 = bs["none"].core(ext["tokens"])
    seg = bs["none"].tokenizer(id_bytes0, merges0, normalize=False)
    langs = slots["slots_v2.json"][script]["langs"]
    n_max = max(s[script]["slots"] for s in slots.values())
    out = {}
    for name, mix in mixes(langs).items():
        out[name] = {"mix": [[u[0], u[1], f] for u, f in mix]}
        for nk in ("none", "v1"):
            total = defaultdict(float)                       # = train_bpe.mixed_counts
            for u, f in mix:
                for piece, c in counts(u, script, nk, pattern, norms[nk]).items():
                    total[piece] += c * f
            items = sorted((p, n) for p, c in total.items() if (n := round(c)) > 0)
            words = [e.ids for e in seg.encode_batch([w.decode("utf-8") for w, _ in items], add_special_tokens=False)]
            id_bytes, vocab_bytes = dict(id_bytes0), set(id_bytes0.values())
            learned = tb.learn_merges(words, [c for _, c in items], id_bytes, vocab_bytes, script, n_max,
                                      len(id_bytes0))
            for cand, (cnk, slots_name) in CANDS.items():
                if cnk != nk:
                    continue
                n = slots[slots_name][script]["slots"]
                ids = dict(id_bytes0)
                ids.update({nid: id_bytes[nid] for _, _, nid, _ in learned[:n]})
                tok = bs[nk].tokenizer(ids, merges0 + [(id_bytes[a], id_bytes[b]) for a, b, _, _ in learned[:n]],
                                       normalize=nk == "v1")
                out[name][cand] = {k: {lang: measure(tok, d / f"{lang}.txt") for lang in langs
                                       if (d / f"{lang}.txt").exists()}
                                   for k, d in sets.items()}
        print(f"{script} {name} ({time.time() - t0:.0f}s)", flush=True)
    return script, out


def choose(res):
    def rel(r, base, sets):
        return [r[c][sp][lang] / base[c][sp][lang] - 1 for c in CANDS for sp in sets for lang in r[c][sp]]

    chosen, mix = {}, {}
    for script, recipes in sorted(res.items()):
        base = recipes["committed"]
        rows = {}
        for name, r in recipes.items():
            sel, conf = rel(r, base, SELECT), rel(r, base, CONFIRM)
            rows[name] = (all(x <= 0 for x in sel), sum(sel) / len(sel),
                          all(x <= 0 for x in conf), sum(conf) / len(conf))
            print(f"  {script:10s} {name:12s} choose {'ok  ' if rows[name][0] else 'fail'} {rows[name][1]:+.2%}  "
                  f"confirm {'ok  ' if rows[name][2] else 'fail'} {rows[name][3]:+.2%}")
        pick = min((n for n in rows if rows[n][0]), key=lambda n: rows[n][1])
        if not rows[pick][2]:
            pick = "committed"
        chosen[script] = pick
        if pick != "committed":
            for src, lang, f in recipes[pick]["mix"]:
                mix.setdefault(lang, []).append([str(Path(A.c60 if src == "c60" else A.s0) / f"{lang}.txt"), f])
    return chosen, mix


def main():
    global A
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--c60", required=True, help="the committed training corpus (fetch_corpus.py, corpus60)")
    ap.add_argument("--s0", required=True, help="sample v0 corpus (sample_to_corpus.py --out)")
    ap.add_argument("--heldout", required=True, help="fetch_heldout.py output (dev/ and check/)")
    ap.add_argument("--heldout-s0", required=True, help="sample_to_corpus.py --heldout-out (a/ and b/)")
    ap.add_argument("--work", required=True, help="cache and results directory (outside the repo)")
    ap.add_argument("--out", required=True, help="the --mix file to write")
    ap.add_argument("--procs", type=int, default=3)
    A = ap.parse_args()
    Path(A.work).mkdir(parents=True, exist_ok=True)
    blocks = list(json.loads((HERE / "slots_v2.json").read_text())["scripts"])
    with Pool(A.procs, initializer=init, initargs=(vars(A),)) as pool:
        res = dict(pool.imap_unordered(run_block, blocks))
    (Path(A.work) / "mix_search.json").write_text(json.dumps(res, indent=1))
    chosen, mix = choose(res)
    Path(A.out).write_text(json.dumps({"_comment": f"mix_search.py: {chosen}", **mix}, indent=1) + "\n")
    print(f"chosen: {chosen}\nwrote {A.out}")


if __name__ == "__main__":
    main()
