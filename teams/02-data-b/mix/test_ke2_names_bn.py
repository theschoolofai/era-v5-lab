#!/usr/bin/env python3
"""Unit tests of ke2_names_bn.py and bn_word_sheets.py, on made-up data only (no network: the Wikidata answers are
written into the cache folder first). Run: python -m unittest test_ke2_names_bn (from teams/02-data-b/mix)."""
import collections
import csv
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import pyarrow as pa
import pyarrow.parquet as pq

import bn_word_sheets as sheets
import ke2_names_bn as names


def write_parquet(path, texts):
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"doc_id": [str(i) for i in range(len(texts))], "text": texts}), path)


def binding(qid, bn, en, sl):
    return {"item": {"value": f"http://www.wikidata.org/entity/{qid}"}, "bn": {"value": bn},
            "en": {"value": en}, "sl": {"value": str(sl)}}


def write_cache(cache, answers):
    """answers: query name -> list of bindings; every other query gets an empty answer."""
    cache.mkdir(parents=True, exist_ok=True)
    for name in names.queries():
        rows = answers.get(name, [])
        (cache / f"{name}.json").write_text(json.dumps({"results": {"bindings": rows}}, ensure_ascii=False),
                                            encoding="utf-8")


def write_zip(path, train, valid):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("ben_train.json", "\n".join(json.dumps(r, ensure_ascii=False) for r in train) + "\n")
        z.writestr("ben_valid.json", "\n".join(json.dumps(r, ensure_ascii=False) for r in valid) + "\n")
        z.writestr("ben_test.json", "")


def ak(uid, bn, lat, source="Wikidata"):
    return {"unique_identifier": uid, "native word": bn, "english word": lat, "source": source}


class NameFilters(unittest.TestCase):
    def test_bengali_name(self):
        self.assertTrue(names.is_bengali_name("রবীন্দ্রনাথ ঠাকুর"))
        self.assertTrue(names.is_bengali_name("জাতিসংঘ সদর দপ্তর"))
        self.assertFalse(names.is_bengali_name("রবি Tagore"))          # Latin letters inside
        self.assertFalse(names.is_bengali_name("রবি ২"))                # a digit
        self.assertFalse(names.is_bengali_name("রবি (লেখক)"))          # a disambiguator
        self.assertFalse(names.is_bengali_name("आमि"))                 # another script
        self.assertFalse(names.is_bengali_name(""))
        self.assertFalse(names.is_bengali_name("রাষ্ট্ৰীয় সংস্থা"))     # Assamese ৰ
        self.assertEqual(names.clean("বাঁকুড়া  জেলা "), "বাঁকুড়া জেলা")

    def test_latin_name(self):
        self.assertTrue(names.is_latin_name("Rabindranath Tagore"))
        self.assertTrue(names.is_latin_name("Ōe Kenzaburō"))
        self.assertFalse(names.is_latin_name("রবি"))
        self.assertFalse(names.is_latin_name("Tagore (writer)"))
        self.assertFalse(names.is_latin_name("1984"))
        self.assertTrue(names.is_latin_name("Bah\u00e1\u02bcu'll\u00e1h"))     # modifier letter ʼ
        self.assertTrue(names.is_latin_name("\u02bbAl\u012b"))


class CountInParts(unittest.TestCase):
    def test_whole_words_only(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ind-bn-x" / "part-00000.parquet"
            write_parquet(p, ["আমি কলকাতা যাব। কলকাতা শহর সুন্দর।", "নিউ ইয়র্ক বড়। কলকাতার রাস্তা।", None])
            got = names.count_in_parts(["কলকাতা", "নিউ ইয়র্ক", "ঢাকা", "ইয়র্ক"], [p])
        self.assertEqual(got, {"কলকাতা": 2, "নিউ ইয়র্ক": 1, "ঢাকা": 0, "ইয়র্ক": 1})

    def test_name_at_document_end_counts_once(self):
        # A longer name in the list must not make a name that ends a document count more than once.
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ind-bn-x" / "part-00000.parquet"
            write_parquet(p, ["আমি কলকাতা যাব", "আমি যাব কলকাতা"])
            got = names.count_in_parts(["কলকাতা", "ক খ গ ঘ ঙ"], [p])
        self.assertEqual(got, {"কলকাতা": 2, "ক খ গ ঘ ঙ": 0})


class Aksharantar(unittest.TestCase):
    def test_wikidata_pairs_only_dedup_and_filter(self):
        with tempfile.TemporaryDirectory() as d:
            z = Path(d) / "ben.zip"
            write_zip(z, [ak("ben1", "ভরদ্বাজ", "bhardwaj"), ak("ben2", "ভরদ্বাজ", "bhardwaj"),
                          ak("ben3", "কলম", "kalam", source="IndicCorp"), ak("ben4", "রবি2", "robi"),
                          ak("ben5", "ব", "b"), ak("ben6", "হিউস", "c")],                  # misaligned: dropped
                      [ak("ben1", "গগৈ", "gogoi")])
            pairs, pool = names.aksharantar_pairs(z)
        self.assertEqual(pool, 2)
        self.assertEqual(sorted(p[1:] for p in pairs), [("গগৈ", "gogoi"), ("ভরদ্বাজ", "bhardwaj")])
        self.assertIn(("train:ben1", "ভরদ্বাজ", "bhardwaj"), pairs)      # first id wins for a duplicate
        self.assertIn(("valid:ben1", "গগৈ", "gogoi"), pairs)             # ids keep their split


class Sampling(unittest.TestCase):
    def test_half_from_region_and_repeatable(self):
        pool = {f"Q{i}": ("ক", "Ka", 1) for i in range(1, 41)}
        region = {f"Q{i}" for i in range(1, 11)}
        with mock.patch.dict(names.SAMPLE, {"person": 8}, clear=True):
            a = names.sample_entities({"person": pool}, region)
            b = names.sample_entities({"person": pool}, region)
        self.assertEqual(a, b)
        self.assertEqual(len(a["person"]), 8)
        self.assertEqual(sum(q in region for q in a["person"]), 4)

    def test_small_region_fills_from_the_rest(self):
        pool = {f"Q{i}": ("ক", "Ka", 1) for i in range(1, 11)}
        with mock.patch.dict(names.SAMPLE, {"person": 6}, clear=True):
            got = names.sample_entities({"person": pool}, {"Q1"})
        self.assertEqual(len(got["person"]), 6)
        self.assertIn("Q1", got["person"])


ANSWERS = {
    "region_P27": [{"item": {"value": "http://www.wikidata.org/entity/Q1"}}],
    "region_P17": [{"item": {"value": "http://www.wikidata.org/entity/Q20"}}],
    "person": [binding("Q1", "রবীন্দ্রনাথ ঠাকুর", "Rabindranath Tagore", 200),
               binding("Q2", "ল্যারি হাগমেন", "Larry Hagman", 60),
               binding("Q3", "রবি (লেখক)", "Robi", 2)],                           # dropped: disambiguator
    "org_Q3918": [binding("Q20", "ঢাকা বিশ্ববিদ্যালয়", "University of Dhaka", 50),
                  binding("Q2", "ল্যারি হাগমেন", "Larry Hagman", 60)],             # a person: stays a person
    "place": [binding("Q30", "কলকাতা", "Kolkata", 300),
              binding("Q20", "ঢাকা বিশ্ববিদ্যালয়", "University of Dhaka", 50)],    # an org: stays an org
}


class WikidataAndMain(unittest.TestCase):
    def test_types_are_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            write_cache(Path(d), ANSWERS)
            by_type, region, shas, drops = names.wikidata_entities(Path(d))
        self.assertEqual(sorted(by_type["person"]), ["Q1", "Q2"])
        self.assertEqual(sorted(by_type["org"]), ["Q20"])
        self.assertEqual(sorted(by_type["place"]), ["Q30"])
        self.assertEqual(region, {"Q1", "Q20"})
        self.assertEqual(set(shas), set(names.queries()))
        self.assertEqual(drops, {"bengali label": 1})                     # Q3, the disambiguator

    def run_main(self, d):
        cache, z, part = d / "cache", d / "ben.zip", d / "ind-bn-x" / "part-00000.parquet"
        write_cache(cache, ANSWERS)
        write_zip(z, [ak("ben1", "গগৈ", "gogoi")], [])
        write_parquet(part, ["কলকাতা শহরে রবীন্দ্রনাথ ঠাকুর থাকতেন। কলকাতা বড়।"])
        out, summ = d / "names.csv", d / "summary.json"
        argv = ["ke2_names_bn.py", "--cache", str(cache), "--aksharantar-zip", str(z), "--bn-parts", str(part),
                "--out", str(out), "--summary", str(summ)]
        with mock.patch.object(sys, "argv", argv), mock.patch("sys.stdout", new=io.StringIO()):
            names.main()
        return out.read_bytes(), json.loads(summ.read_text(encoding="utf-8"))

    def test_main_rows_and_repeatable(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            a, summary = self.run_main(Path(d1))
            b, _ = self.run_main(Path(d2))
        self.assertEqual(a, b)
        rows = list(csv.DictReader(io.StringIO(a.decode("utf-8"))))
        self.assertEqual(list(rows[0])[:6], ["name", "lang", "script", "type", "source", "licence"])
        self.assertEqual(len(rows), 2 * (2 + 1 + 1 + 1))                # 4 entities + 1 pair, two spellings each
        by = {(r["id"], r["script"]): r for r in rows}
        self.assertEqual(by[("Q1", "Beng")]["count_bn_sample"], "1")
        self.assertEqual(by[("Q30", "Beng")]["count_bn_sample"], "2")
        self.assertEqual(by[("Q30", "Latn")]["count_bn_sample"], "")
        self.assertEqual(by[("Q1", "Beng")]["region"], "in_bd")
        self.assertEqual(by[("Q2", "Beng")]["region"], "other")
        self.assertEqual(by[("Q1", "Latn")]["lang"], "en")
        self.assertEqual(by[("train:ben1", "Latn")]["lang"], "bn")
        self.assertEqual(by[("train:ben1", "Beng")]["licence"], "CC0-1.0")
        self.assertEqual(summary["rows"], len(rows))
        self.assertEqual(summary["bengali_forms_seen_in_sample"], 2)


class WordSheets(unittest.TestCase):
    def test_words_rule(self):
        self.assertEqual(sheets.words("আমি ভাত খাই। Rice 2 খাই২ কি\u200cন্তু-না"),
                         ["আমি", "ভাত", "খাই", "কি\u200cন্তু", "না"])

    def test_variants_keep_nukta_letters_whole(self):
        ra = sheets.RULES["ra/rra (র ড়)"]
        self.assertIn("বাড়ি", set(sheets.variants("বারি", ra)))
        self.assertIn("বারি", set(sheets.variants("বাড়ি", ra)))
        ja = sheets.RULES["ja/ya (জ য)"]
        self.assertEqual(set(sheets.variants("হয়", ja)), set())          # য় is not য: never turned into জ়
        self.assertIn("যাওয়া", set(sheets.variants("জাওয়া", ja)))

    def test_misspell_thresholds(self):
        tok = collections.Counter({"একটি": 1000, "একটী": 5, "দিন": 1000, "দীন": 300, "বিল": 10, "বীল": 1})
        rows = sheets.misspell_rows(tok)
        pairs = {(r[0], r[1]) for r in rows}
        self.assertIn(("একটী", "একটি"), pairs)
        self.assertNotIn(("দীন", "দিন"), pairs)                          # ratio 0.3 > MAX_RATIO
        self.assertNotIn(("বীল", "বিল"), pairs)                          # right word too rare
        self.assertTrue(all(r[6] == "" for r in rows))

    def test_main_sheets(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            part = d / "ind-bn-x" / "part-00000.parquet"
            write_parquet(part, ["এবং আমি একটি বই পড়ি।"] * 40 + ["এবং একটী বই।"])
            cfg = d / "cfg.json"
            cfg.write_text(json.dumps({"markers": {"bn": {"words": ["এবং"]}}}, ensure_ascii=False), encoding="utf-8")
            sw, ms = d / "sw.csv", d / "ms.csv"
            argv = ["x", "--parts", str(part), "--config", str(cfg), "--stopwords", str(sw), "--misspell", str(ms)]
            with mock.patch.object(sys, "argv", argv), mock.patch("sys.stdout", new=io.StringIO()):
                sheets.main()
            with open(sw, encoding="utf-8") as f:
                top = list(csv.DictReader(f))
            with open(ms, encoding="utf-8") as f:
                miss = list(csv.DictReader(f))
        self.assertEqual(top[0]["word"], "এবং")
        self.assertEqual(top[0]["in_current_markers"], "yes")
        self.assertEqual(top[0]["doc_share_ind-bn-x"], "1.0")
        self.assertEqual([(m["wrong"], m["right"]) for m in miss], [("একটী", "একটি")])


if __name__ == "__main__":
    unittest.main()
