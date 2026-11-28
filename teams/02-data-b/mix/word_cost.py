"""Data B design task 2: what does a word cost (bytes per word) for hi, mr, bn, ta, sa.

Input: public FineWeb-2 (HuggingFaceFW/fineweb-2), the source of the fw2 packs.
Reads the first --docs documents of the first train parquet file of each language
(files sorted by name), so the run is repeatable.

Word = a run of characters between whitespace / Unicode punctuation (P*) / symbols (S*).
ZWJ/ZWNJ stay inside words. A hyphen splits a word (hyphenated compounds count as parts).
"Native" word = every letter is in the language's script block (digits-only words dropped).

Run:  pip install -q regex pyarrow huggingface_hub
      python word_cost.py --docs 100000 --out out/
"""
import argparse, collections, csv, json, os, sys, time
import regex
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem

LANGS = {  # lang: (fineweb-2 config, script block lo, hi)
    "hi": ("hin_Deva", 0x0900, 0x097F),
    "mr": ("mar_Deva", 0x0900, 0x097F),
    "sa": ("san_Deva", 0x0900, 0x097F),
    "bn": ("ben_Beng", 0x0980, 0x09FF),
    "ta": ("tam_Taml", 0x0B80, 0x0BFF),
}
SPLIT = regex.compile(r"[\s\p{P}\p{S}]+")
LETTER = regex.compile(r"\p{L}|\p{M}")
EDGES = [8, 16, 24, 32, 48, 64, 96, 128]

def is_native(w, lo, hi):
    has = False
    for ch in w:
        o = ord(ch)
        if lo <= o <= hi:
            has = True
        elif ch in "‌‍":
            continue
        elif LETTER.match(ch):
            return False  # letter from another script
        # digits outside block: allowed
    return has

def docs_for(cfg, n):
    fs = HfFileSystem()
    files = sorted(fs.ls(f"datasets/HuggingFaceFW/fineweb-2/data/{cfg}/train", detail=False))
    got = 0
    for f in files:
        with fs.open(f, "rb") as fh:
            pf = pq.ParquetFile(fh)
            for rg in range(pf.num_row_groups):
                for t in pf.read_row_group(rg, columns=["text"]).column("text").to_pylist():
                    yield t
                    got += 1
                    if got >= n:
                        return

def q(sorted_counts, total, p):
    # sorted_counts: list of (len, count) ascending; weighted quantile
    k, acc = p * total, 0
    for L, c in sorted_counts:
        acc += c
        if acc >= k:
            return L
    return sorted_counts[-1][0]

def run(lang, n, out):
    cfg, lo, hi = LANGS[lang]
    t0 = time.time()
    freq = collections.Counter()
    ndocs = nbytes = other = 0
    for text in docs_for(cfg, n):
        ndocs += 1
        nbytes += len(text.encode("utf-8"))
        for w in SPLIT.split(text):
            if not w:
                continue
            if is_native(w, lo, hi):
                freq[w] += 1
            elif LETTER.search(w):
                other += 1
    blen = collections.Counter()      # byte length -> token count
    for w, c in freq.items():
        blen[len(w.encode("utf-8"))] += c
    sc = sorted(blen.items())
    ntok = sum(blen.values())
    wbytes = sum(L * c for L, c in sc)
    def share_tok(th): return sum(c for L, c in sc if L > th) / ntok
    def share_byt(th): return sum(L * c for L, c in sc if L > th) / wbytes
    def share_typ(th):
        ws = [w for w in freq if len(w.encode()) > th]
        return len(ws) / len(freq), (sum(1 for w in ws if freq[w] == 1) / len(ws) if ws else 0)
    hist, prev = [], 0
    for e in EDGES + [10**9]:
        c = sum(cc for L, cc in sc if prev < L <= e)
        hist.append([f"{prev+1}-{e}" if e < 10**9 else f">{prev}", c, round(100 * c / ntok, 3)])
        prev = e
    t32, h32 = share_typ(32); t64, h64 = share_typ(64)
    chars = sum(len(w) * c for w, c in freq.items())
    row = dict(lang=lang, config=cfg, docs=ndocs, text_MB=round(nbytes / 1e6, 1),
               native_words=ntok, distinct=len(freq), other_script_words=other,
               bytes_per_char=round(wbytes / chars, 3),
               mean_bytes=round(wbytes / ntok, 2), median=q(sc, ntok, .5), p90=q(sc, ntok, .9),
               p99=q(sc, ntok, .99), p999=q(sc, ntok, .999), max=sc[-1][0],
               pct_words_gt16=round(100 * share_tok(16), 3),
               pct_words_gt32=round(100 * share_tok(32), 3),
               pct_words_gt64=round(100 * share_tok(64), 4),
               pct_wordbytes_gt32=round(100 * share_byt(32), 3),
               pct_wordbytes_gt64=round(100 * share_byt(64), 4),
               pct_types_gt32=round(100 * t32, 2), pct_hapax_among_types_gt32=round(100 * h32, 1),
               pct_types_gt64=round(100 * t64, 3), pct_hapax_among_types_gt64=round(100 * h64, 1),
               seconds=round(time.time() - t0))
    longest = sorted((w for w in freq if freq[w] >= 3), key=lambda w: -len(w.encode()))[:15]
    row["long_frequent"] = [[w, len(w.encode()), freq[w]] for w in longest]
    row["hist"] = hist
    with open(os.path.join(out, f"word_freq_{lang}.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh); wr.writerow(["word", "count", "lang", "bytes"])
        for w, c in freq.most_common():
            wr.writerow([w, c, lang, len(w.encode())])
    return row

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=int, default=100000)
    ap.add_argument("--langs", default="hi,mr,bn,ta,sa")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for lang in a.langs.split(","):
        r = run(lang, a.docs, a.out); rows.append(r)
        print(json.dumps({k: v for k, v in r.items() if k not in ("hist", "long_frequent")}, ensure_ascii=False), flush=True)
    json.dump(rows, open(os.path.join(a.out, "word_cost.json"), "w"), ensure_ascii=False, indent=1)
