#!/usr/bin/env python3
"""ke2_names_bn.py - KE2 (Team 4) data request R4, Bengali: names with a Bengali-script and a Latin spelling.

Sources
  1. Wikidata (CC0 1.0): items that have a Bengali Wikipedia article, a Bengali label and an English label.
       person = P31 Q5
       org    = P31 is one of ORG_CLASSES (one query per class; one big query times out on the public endpoint)
       place  = has P625 (coordinates) and is neither a person nor an org
     The Latin spelling is the item's English label. region = "in_bd" when the item's P27 (citizenship) or P17
     (country) is India, Bangladesh or British Raj, else "other".
  2. Aksharantar (ai4bharat/Aksharantar @ AKSHARANTAR_REV, ben.zip): word-level spelling pairs that Aksharantar mined
     from Wikidata labels (source "Wikidata", train + valid splits), Bengali word + Latin spelling, e.g. a surname.
     A seeded sample of AK_SAMPLE pairs. Not used: the AK-NEI / AK-NEF named-entity pairs, which sit only in the TEST
     split (Aksharantar's transliteration benchmark) and include ordinary words.
  The Wikidata English label is the entity's name in English: for people it is usually a spelling of the Bengali
  form (sometimes with more name parts), for orgs and places it is often a translation. Use the Aksharantar rows when
  a true spelling pair is needed.

Output CSV columns: KE2's six (name,lang,script,type,source,licence), then
  id               links the spellings of one entity (Wikidata QID, or <split>:<Aksharantar unique_identifier>)
  sitelinks        Wikidata sitelink count (how well known the entity is); blank for Aksharantar
  region           in_bd / other (Wikidata); blank for Aksharantar
  count_bn_sample  how often the Bengali form occurs as whole words in the two bn raw packs of sample v0
                   (ind-bn-fw2, ind-bn-sangraha-v), so KE2 can pick seen and unseen names; blank on Latin rows
  lang/script: bn/Beng for the Bengali form, en/Latn for Wikidata's English label, bn/Latn for Aksharantar's
  Latin spelling. type: person / place / org (Wikidata), name_word (Aksharantar).

Filters: labels are NFC with single spaces. A Bengali form is kept only if every letter is in the Bengali block, it
has no ৰ / ৱ (Assamese letters), no digit and no "(...)" disambiguator; a Latin form only if its letters are Latin
(the modifier letters ʻ ʼ ʾ ʿ allowed) and it has no "(...)". Aksharantar pairs need at least 2 Bengali letters and
2 Latin characters (drops misaligned pairs such as ব / b).

Word rule for count_bn_sample: the split regex of teams/02-data-b/mix/word_cost.py in #923 (whitespace, Unicode
punctuation P* and symbols S*; ZWJ/ZWNJ stay inside a word), after NFC (never NFKC).

Wikidata is live, so the query results are cached as JSON under --cache (with their sha256 in the summary); a rerun
with the same cache rebuilds the same CSV byte for byte.

Usage
  python ke2_names_bn.py --cache out/ke2_names_bn --aksharantar-zip ben.zip \
      --bn-parts ind-bn-fw2/part-00000.parquet ind-bn-sangraha-v/part-00000.parquet \
      --out ke2_names_bn_v1.csv --summary ke2_names_bn_v1.json
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import random
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import pyarrow.parquet as pq
import regex

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "era-v5-lab-data-b/0.1 (course project; python urllib)"
AKSHARANTAR_REV = "e418c1fc928d9f5393af33268472cf20c1891be8"
BN_WIKI = "<https://bn.wikipedia.org/>"
REGION_QIDS = "wd:Q668 wd:Q902 wd:Q129286"          # India, Bangladesh, British Raj
ORG_CLASSES = {
    "Q43229": "organization", "Q4830453": "business", "Q3918": "university", "Q7278": "political party",
    "Q891723": "public company", "Q2385804": "educational institution", "Q875538": "public university",
    "Q902104": "private university", "Q327333": "government agency", "Q163740": "nonprofit organization",
    "Q476028": "association football club", "Q11032": "newspaper", "Q1110794": "daily newspaper",
    "Q783794": "company", "Q31855": "research institute", "Q1664720": "institute", "Q3914": "school",
    "Q9826": "high school", "Q46970": "airline", "Q215380": "musical group", "Q2001305": "television channel",
}
SAMPLE = {"person": 2000, "place": 2000, "org": 1000}   # entities per type; up to half from region in_bd
AK_SAMPLE = 3000                                        # Aksharantar Wikidata-mined pairs
SEED = 20261129

SPLIT = regex.compile(r"[\s\p{P}\p{S}]+")
LETTER = regex.compile(r"[\p{L}\p{M}]")
BENGALI_BLOCK = (0x0980, 0x09FF)
ASSAMESE_ONLY = {"\u09f0", "\u09f1"}                  # ৰ ৱ: in the Bengali block, but Assamese letters
ZW = {"\u200c", "\u200d"}
LATIN_MODIFIERS = {"\u02bb", "\u02bc", "\u02be", "\u02bf"}   # ʻ ʼ ʾ ʿ (transliterated Arabic, Hawaiian names)


def label_query(where):
    return f"""SELECT ?item ?bn ?en ?sl WHERE {{
 {where}
 ?a schema:about ?item; schema:isPartOf {BN_WIKI}.
 ?item wikibase:sitelinks ?sl; rdfs:label ?bn. FILTER(LANG(?bn) = "bn")
 ?item rdfs:label ?en. FILTER(LANG(?en) = "en")
}}"""


def region_query(prop):
    return f"""SELECT DISTINCT ?item WHERE {{
 VALUES ?c {{ {REGION_QIDS} }}
 ?item wdt:{prop} ?c.
 ?a schema:about ?item; schema:isPartOf {BN_WIKI}.
}}"""


def queries():
    q = {"person": label_query("?item wdt:P31 wd:Q5."),
         "place": label_query("?item wdt:P625 ?coord. FILTER NOT EXISTS { ?item wdt:P31 wd:Q5 }"),
         "region_P27": region_query("P27"),
         "region_P17": region_query("P17")}
    for qid in ORG_CLASSES:
        q[f"org_{qid}"] = label_query(f"?item wdt:P31 wd:{qid}.")
    return q


def run_query(text, tries=4):
    data = urllib.parse.urlencode({"query": text}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={
        "User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"})
    for k in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            if k == tries - 1:
                raise
            wait = 15 * (k + 1)
            print(f"  retry in {wait}s after {e}")
            time.sleep(wait)


def cached(cache, name, text):
    path = cache / f"{name}.json"
    if not path.exists():
        t = time.time()
        raw = run_query(text)
        path.write_bytes(raw)
        print(f"  {name}: fetched in {time.time() - t:.1f}s")
        time.sleep(2)                                   # be gentle with the public endpoint
    raw = path.read_bytes()
    return json.loads(raw)["results"]["bindings"], hashlib.sha256(raw).hexdigest()


def clean(s):
    """NFC and single spaces (some Wikidata labels hold a double space)."""
    return " ".join(unicodedata.normalize("NFC", s).split())


def is_bengali_name(s):
    if not s or "(" in s or any(c.isdigit() for c in s) or any(c in ASSAMESE_ONLY for c in s):
        return False
    has = False
    for ch in s:
        o = ord(ch)
        if BENGALI_BLOCK[0] <= o <= BENGALI_BLOCK[1]:
            has = True
        elif ch in ZW:
            continue
        elif LETTER.match(ch):
            return False                                # a letter from another script
    return has


def is_latin_name(s):
    if not s or "(" in s:
        return False
    letters = [c for c in s if LETTER.match(c) and c not in LATIN_MODIFIERS]
    return bool(letters) and all("LATIN" in unicodedata.name(c, "") for c in letters if c.isalpha())


def words(text):
    return [w for w in SPLIT.split(unicodedata.normalize("NFC", text)) if w]


def count_in_parts(names, parts):
    """Whole-word occurrences of each name (a word sequence) in the parquet parts' text column."""
    targets = collections.defaultdict(set)
    for n in names:
        w = tuple(words(n))
        if w:
            targets[w[0]].add(w)
    maxlen = max((len(w) for ws in targets.values() for w in ws), default=1)
    counts = collections.Counter()
    for p in parts:
        for text in pq.read_table(p, columns=["text"]).column("text").to_pylist():
            ws = words(text or "")
            for i, w in enumerate(ws):
                cands = targets.get(w)
                if not cands:
                    continue
                for L in range(1, min(maxlen, len(ws) - i) + 1):   # never read past the document's end
                    seq = tuple(ws[i:i + L])
                    if seq in cands:
                        counts[seq] += 1
    return {n: counts[tuple(words(n))] for n in names}


def wikidata_entities(cache):
    shas, by_type = {}, {}
    drops = collections.Counter()                       # distinct QIDs whose labels fail a filter, per reason
    q = queries()
    region = set()
    for name in ("region_P27", "region_P17"):
        rows, shas[name] = cached(cache, name, q[name])
        region |= {r["item"]["value"].rsplit("/", 1)[1] for r in rows}

    def collect(rows):
        out = {}
        for r in rows:
            qid = r["item"]["value"].rsplit("/", 1)[1]
            bn, en = clean(r["bn"]["value"]), clean(r["en"]["value"])
            if is_bengali_name(bn) and is_latin_name(en):
                out[qid] = (bn, en, int(r["sl"]["value"]))
            else:
                bad[qid] = "bengali label" if not is_bengali_name(bn) else "english label"
        return out

    bad = {}

    rows, shas["person"] = cached(cache, "person", q["person"])
    by_type["person"] = collect(rows)
    org = {}
    for qid in ORG_CLASSES:
        rows, shas[f"org_{qid}"] = cached(cache, f"org_{qid}", q[f"org_{qid}"])
        org.update(collect(rows))
    by_type["org"] = {k: v for k, v in org.items() if k not in by_type["person"]}
    rows, shas["place"] = cached(cache, "place", q["place"])
    by_type["place"] = {k: v for k, v in collect(rows).items() if k not in by_type["org"]}
    kept = set().union(*by_type.values())
    drops.update(reason for qid, reason in bad.items() if qid not in kept)
    return by_type, region, shas, dict(sorted(drops.items()))


def sample_entities(by_type, region):
    rng = random.Random(SEED)
    picked = {}
    for t, n in SAMPLE.items():
        pool = by_type[t]
        ids = sorted(pool)
        local = [i for i in ids if i in region]
        other = [i for i in ids if i not in region]
        k_local = min(len(local), n // 2)
        k_other = min(len(other), n - k_local)
        k_local = min(len(local), n - k_other)
        picked[t] = sorted(rng.sample(local, k_local) + rng.sample(other, k_other), key=lambda q: int(q[1:]))
    return picked


def aksharantar_pairs(zip_path):
    pairs = {}
    with zipfile.ZipFile(zip_path) as z:
        for split in ("train", "valid"):
            with z.open(f"ben_{split}.json") as f:
                for line in io.TextIOWrapper(f, encoding="utf-8"):
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    if r["source"] != "Wikidata":
                        continue
                    bn, lat = clean(r["native word"]), clean(r["english word"])
                    letters_bn = sum(1 for c in bn if unicodedata.category(c) == "Lo")
                    if is_bengali_name(bn) and is_latin_name(lat) and letters_bn >= 2 and len(lat) >= 2:
                        pairs.setdefault((bn, lat), f"{split}:{r['unique_identifier']}")
    keys = sorted(pairs)
    picked = random.Random(SEED).sample(keys, min(AK_SAMPLE, len(keys)))
    return [(pairs[k], k[0], k[1]) for k in sorted(picked)], len(keys)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache", required=True, type=Path)
    ap.add_argument("--aksharantar-zip", required=True, type=Path)
    ap.add_argument("--bn-parts", nargs="+", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--summary", required=True, type=Path)
    a = ap.parse_args()
    a.cache.mkdir(parents=True, exist_ok=True)

    by_type, region, shas, drops = wikidata_entities(a.cache)
    picked = sample_entities(by_type, region)
    ak, ak_pool = aksharantar_pairs(a.aksharantar_zip)

    bn_names = sorted({by_type[t][q][0] for t in picked for q in picked[t]} | {p[1] for p in ak})
    counts = count_in_parts(bn_names, a.bn_parts)

    rows = []
    for t in ("person", "place", "org"):
        for qid in picked[t]:
            bn, en, sl = by_type[t][qid]
            reg = "in_bd" if qid in region else "other"
            rows.append([bn, "bn", "Beng", t, "wikidata", "CC0-1.0", qid, sl, reg, counts[bn]])
            rows.append([en, "en", "Latn", t, "wikidata", "CC0-1.0", qid, sl, reg, ""])
    for uid, bn, lat in ak:
        rows.append([bn, "bn", "Beng", "name_word", "aksharantar:Wikidata", "CC0-1.0", uid, "", "", counts[bn]])
        rows.append([lat, "bn", "Latn", "name_word", "aksharantar:Wikidata", "CC0-1.0", uid, "", "", ""])

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["name", "lang", "script", "type", "source", "licence", "id", "sitelinks", "region", "count_bn_sample"])
    w.writerows(rows)
    data = buf.getvalue().encode("utf-8")
    a.out.write_bytes(data)

    def file_sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    beng = [r for r in rows if r[2] == "Beng"]
    summary = {
        "rows": len(rows), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "pool_entities": {t: len(v) for t, v in by_type.items()},
        "wikidata_dropped_by_filters": drops,
        "pool_in_bd": {t: sum(1 for q in v if q in region) for t, v in by_type.items()},
        "picked_entities": {t: len(v) for t, v in picked.items()},
        "picked_in_bd": {t: sum(1 for q in v if q in region) for t, v in picked.items()},
        "aksharantar_pairs": {"pool": ak_pool, "picked": len(ak)},
        "bengali_forms_seen_in_sample": sum(1 for r in beng if r[9] > 0),
        "bengali_forms_unseen_in_sample": sum(1 for r in beng if r[9] == 0),
        "seed": SEED,
        "inputs": {"aksharantar_zip_sha256": file_sha(a.aksharantar_zip), "aksharantar_rev": AKSHARANTAR_REV,
                   "bn_parts_sha256": {p.parent.name: file_sha(p) for p in a.bn_parts},
                   "wikidata_query_sha256": shas},
    }
    a.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in list(summary)[:10]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
