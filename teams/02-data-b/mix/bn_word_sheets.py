#!/usr/bin/env python3
"""bn_word_sheets.py - two reading sheets for a Bengali reader, built from the bn packs' word counts.

1. Stop-word candidates (Data B task 0 (b), the stop-word check): the TOP most common Bengali words by document share,
   with the share in each pack, whether the word is already a bn marker in audit/lang_label_config.json, and whether
   it holds র (Bengali ra), which Assamese writes as ৰ, so a word with র cannot be Assamese. The reader marks which
   words are Bengali function words that are good markers.
2. Misspelling candidates (KE2's R6, wrong/right pairs): a frequent word W and a much rarer form V of it that differs
   by one common Bengali spelling confusion (RULES). Both forms occur in the packs, so every pair is real text, but a
   pair can also be two valid words (দিন "day" / দীন "poor"): the reader marks each pair.

Word rule (as mix/word_cost.py in #923): NFC, split on whitespace, Unicode punctuation (P*) and symbols (S*); ZWJ/ZWNJ
stay in a word; keep a word only if every letter is in the Bengali block.

Usage
  python bn_word_sheets.py --parts ind-bn-fw2/part-00000.parquet ind-bn-sangraha-v/part-00000.parquet \
      --config ../audit/lang_label_config.json --stopwords out/bn_stopword_candidates.csv \
      --misspell out/bn_misspell_candidates.csv
"""
import argparse
import collections
import csv
import json
import unicodedata
from pathlib import Path

import pyarrow.parquet as pq
import regex

SPLIT = regex.compile(r"[\s\p{P}\p{S}]+")
LETTER = regex.compile(r"[\p{L}\p{M}]")
LO, HI = 0x0980, 0x09FF
ZW = {"\u200c", "\u200d"}
NUKTA = "\u09bc"
TOP = 200
MIN_RIGHT = 30          # W must occur at least this often
MAX_RATIO = 0.1         # V must be at most this share of W's count
PER_RULE = 50
# One substitution at one position. Bengali letters with a nukta are two code points after NFC (ড + ়).
RULES = {
    "i/ii (ি ী)": [("ি", "ী"), ("ী", "ি")],
    "u/uu (ু ূ)": [("ু", "ূ"), ("ূ", "ু")],
    "sibilants (শ ষ স)": [("শ", "ষ"), ("শ", "স"), ("ষ", "শ"), ("ষ", "স"), ("স", "শ"), ("স", "ষ")],
    "n/nn (ন ণ)": [("ন", "ণ"), ("ণ", "ন")],
    "ja/ya (জ য)": [("জ", "য"), ("য", "জ")],
    "ra/rra (র ড়)": [("র", "ড" + NUKTA), ("ড" + NUKTA, "র")],
    "chandrabindu dropped or added (ঁ)": [("ঁ", "")],
}


def native(w):
    has = False
    for ch in w:
        o = ord(ch)
        if LO <= o <= HI:
            has = True
        elif ch in ZW:
            continue
        elif LETTER.match(ch):
            return False
    return has and not any(ch.isdigit() for ch in w)


def words(text):
    return [w for w in SPLIT.split(unicodedata.normalize("NFC", text or "")) if w and native(w)]


def count(parts):
    tok, docs, ndocs = collections.Counter(), {}, {}
    for p in parts:
        name = Path(p).parent.name
        d = collections.Counter()
        texts = pq.read_table(p, columns=["text"]).column("text").to_pylist()
        for t in texts:
            ws = words(t)
            tok.update(ws)
            d.update(set(ws))
        docs[name], ndocs[name] = d, len(texts)
    return tok, docs, ndocs


def variants(w, pairs):
    for a, b in pairs:
        start = 0
        while True:
            i = w.find(a, start)
            if i < 0:
                break
            if not (a == "ড" and w[i + 1:i + 2] == NUKTA) and not (a == "য" and w[i + 1:i + 2] == NUKTA):
                yield w[:i] + b + w[i + len(a):]
            start = i + 1
    if pairs == RULES["chandrabindu dropped or added (ঁ)"]:
        for i in range(1, len(w) + 1):              # add ঁ after a vowel sign or independent vowel
            if unicodedata.category(w[i - 1]) in ("Mc", "Mn", "Lo") and w[i:i + 1] != "ঁ":
                yield w[:i] + "ঁ" + w[i:]


def misspell_rows(tok):
    out = []
    for rule, pairs in RULES.items():
        found = {}
        for w, cw in tok.most_common():
            if cw < MIN_RIGHT:
                break
            for v in variants(w, pairs):
                cv = tok.get(v, 0)
                if v != w and 1 <= cv <= cw * MAX_RATIO and v not in found:
                    found[v] = (w, cv, cw)
        ranked = sorted(found.items(), key=lambda kv: (-kv[1][2], kv[0]))[:PER_RULE]
        out += [[v, w, rule, cv, cw, round(cv / cw, 4), ""] for v, (w, cv, cw) in ranked]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--parts", nargs="+", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--stopwords", required=True, type=Path)
    ap.add_argument("--misspell", required=True, type=Path)
    a = ap.parse_args()

    tok, docs, ndocs = count(a.parts)
    with open(a.config, encoding="utf-8") as f:
        markers = set(json.load(f)["markers"]["bn"]["words"])
    packs = sorted(docs)
    share = {w: sum(docs[p][w] / ndocs[p] for p in packs) / len(packs) for w in tok}
    top = sorted(share, key=lambda w: (-share[w], w))[:TOP]

    a.stopwords.parent.mkdir(parents=True, exist_ok=True)
    with open(a.stopwords, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(["rank", "word", "count", *[f"doc_share_{p}" for p in packs], "in_current_markers", "has_ra",
                     "reader_mark"])
        for i, w in enumerate(top, 1):
            wr.writerow([i, w, tok[w], *[round(docs[p][w] / ndocs[p], 4) for p in packs],
                         "yes" if w in markers else "", "yes" if "র" in w else "", ""])
    rows = misspell_rows(tok)
    with open(a.misspell, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(["wrong", "right", "rule", "count_wrong", "count_right", "ratio", "reader_mark"])
        wr.writerows(rows)
    print(json.dumps({"docs": ndocs, "distinct_words": len(tok), "tokens": sum(tok.values()),
                      "stopword_rows": len(top), "misspell_rows": len(rows),
                      "misspell_per_rule": collections.Counter(r[2] for r in rows),
                      "markers_in_top": sum(1 for w in top if w in markers), "markers": len(markers)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
