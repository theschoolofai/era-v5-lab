#!/usr/bin/env python3
"""aya_benchmark_overlap.py - are two "permissive" aya_collection subsets benchmark items?

`teams/10-post-training/licences/licence_table.md` (`sft-indic-aya-collection`) lists `templated_indic_sentiment` and
`templated_indic_paraphrase` among the 10 aya_collection subsets to consider for SFT. Their sources are IndicSentiment
and IndicXParaphrase, two IndicXTREME benchmarks. This script counts, for one language, how many benchmark items
appear verbatim (NFC, whitespace collapsed) in the aya rows:
  IndicSentiment (validation, test): the ENGLISH REVIEW in aya `inputs`, the INDIC REVIEW in aya `targets`
                                     (aya turns each review into an English-to-Indic translation task), also
                                     counted with quote marks removed (aya drops a review's own quote marks);
                                     and the English side for every language of the subset;
  IndicXParaphrase (one test file):  each Indic sentence (sentence1, sentence2) longer than 20 characters, in aya
                                     `inputs` or `targets`.
Only counts are written.

Usage
  python aya_benchmark_overlap.py --lang ben --aya-sentiment templated_indic_sentiment/train-00000-of-00001.parquet \
      --aya-paraphrase templated_indic_paraphrase/train-00000-of-00001.parquet \
      --indicsentiment IndicSentiment/data --indicxparaphrase IndicXParaphrase/data/bn.tsv --out overlap.json
"""
import argparse
import json
import unicodedata
from pathlib import Path

import pyarrow.parquet as pq

ISO = {"ben": "bn"}


QUOTES = str.maketrans("", "", "'\"\u2018\u2019\u201c\u201d")


def norm(s):
    return " ".join(unicodedata.normalize("NFC", s or "").split())


def unquote(s):
    """norm() without quote marks: aya drops the review's own quote marks when it wraps it in a template."""
    return " ".join(norm(s).translate(QUOTES).split())


def load_json_rows(path):
    text = Path(path).read_text(encoding="utf-8").strip()
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def aya_rows(path, lang=None):
    rows = pq.read_table(path, columns=["inputs", "targets", "language"]).to_pylist()
    return [r for r in rows if lang is None or r["language"] == lang]


def sentiment(aya, bench_dir, code):
    inputs = " \n ".join({norm(r["inputs"]) for r in aya})
    targets = {norm(r["targets"]) for r in aya}
    targets_blob = " \n ".join(targets)
    targets_unq = " \n ".join(unquote(r["targets"]) for r in aya)
    out = {"aya_rows": len(aya)}
    for split in ("validation", "test"):
        rows = load_json_rows(Path(bench_dir) / split / f"{code}.json")
        en = [norm(r["ENGLISH REVIEW"]) for r in rows if r.get("ENGLISH REVIEW")]
        ind = [norm(r["INDIC REVIEW"]) for r in rows if r.get("INDIC REVIEW")]
        out[split] = {"items": len(rows), "distinct_english_reviews": len(set(en)),
                      "english_review_in_aya_inputs": sum(1 for v in en if v in inputs),
                      "indic_review_in_aya_targets": sum(1 for v in ind if v in targets or v in targets_blob),
                      "indic_review_in_aya_targets_without_quote_marks":
                          sum(1 for v in ind if unquote(v) in targets_unq)}
    return out


def english_side_all_languages(aya_all, bench_dir, code):
    """For every language of the aya subset: how many of the benchmark's distinct English reviews (validation + test,
    taken from one language file: the English side is shared) appear in that language's aya inputs."""
    en = set()
    for split in ("validation", "test"):
        en |= {norm(r["ENGLISH REVIEW"]) for r in load_json_rows(Path(bench_dir) / split / f"{code}.json")
               if r.get("ENGLISH REVIEW")}
    by_lang = {}
    for r in aya_all:
        by_lang.setdefault(r["language"], []).append(norm(r["inputs"]))
    return {"distinct_english_reviews": len(en),
            "found_per_language": {lang: sum(1 for v in en if v in " \n ".join(ins))
                                   for lang, ins in sorted(by_lang.items())},
            "aya_rows_per_language": {lang: len(ins) for lang, ins in sorted(by_lang.items())}}


def paraphrase(aya, tsv):
    blob = " \n ".join(norm(r["inputs"]) + " " + norm(r["targets"]) for r in aya)
    with open(tsv, encoding="utf-8") as f:
        lines = [line.rstrip("\n").split("\t") for line in f]
    cols = [lines[0].index(c) for c in ("sentence1", "sentence2")]      # the Indic pair; `en` is English
    sents = {norm(row[i]) for row in lines[1:] for i in cols if i < len(row) and len(norm(row[i])) > 20}
    return {"aya_rows": len(aya), "tsv_rows": len(lines) - 1, "sentences": len(sents),
            "sentences_in_aya": sum(1 for s in sents if s in blob)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lang", default="ben")
    ap.add_argument("--aya-sentiment", required=True)
    ap.add_argument("--aya-paraphrase", required=True)
    ap.add_argument("--indicsentiment", required=True, help="folder with validation/<code>.json and test/<code>.json")
    ap.add_argument("--indicxparaphrase", required=True, help="the language's .tsv file")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    code = ISO.get(a.lang, a.lang)
    res = {"lang": a.lang,
           "indic_sentiment": sentiment(aya_rows(a.aya_sentiment, a.lang), a.indicsentiment, code),
           "indic_sentiment_english_all_languages":
               english_side_all_languages(aya_rows(a.aya_sentiment), a.indicsentiment, code),
           "indic_xparaphrase": paraphrase(aya_rows(a.aya_paraphrase, a.lang), a.indicxparaphrase)}
    a.out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res))


if __name__ == "__main__":
    main()
