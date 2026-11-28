#!/usr/bin/env python3
"""Unit tests of bn_sample_check.py and aya_benchmark_overlap.py, on made-up data only (no network, no model).
The frozen tokenizer is replaced by a stub that gives one token per character.
Run: python -m unittest test_bn_post_training (from teams/02-data-b/post_training)."""
import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

import aya_benchmark_overlap as ov
import bn_sample_check as chk

BN = "আমি আজ স্কুলে যাব এবং তারপর বাড়ি ফিরব। তিনি কিন্তু সেখান থেকে আমাদের জন্য এসেছিলেন।"
AS = "মই আজি বিদ্যালয়লৈ যাম আৰু তাৰ পিছত ঘৰলৈ উভতি আহিম। তেওঁ আৰু তেওঁৰ বাবে কৰা কাম।"


class StubTok:
    class Enc:
        def __init__(self, n):
            self.ids = list(range(n))

    def encode(self, text, add_special_tokens=False):
        return self.Enc(len(text))


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


class SampleCheck(unittest.TestCase):
    def run_rows(self, rows):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.jsonl"
            write_jsonl(p, rows)
            return chk.check_file(p, StubTok(), chk.lang_id.load_config(), 0.8)

    def test_ids_and_metadata_are_not_text(self):
        # A Latin id or _row must not lower the Bengali share or add tokens.
        a = self.run_rows([{"_row": "bangla_bd/NativQA_train.json#41", "doc_id": "acebdd66-1992-4906", "answer": BN}])
        b = self.run_rows([{"answer": BN}])
        self.assertEqual(a["bn_purity"], 1.0)
        self.assertEqual(a["tokens_sum"], b["tokens_sum"])

    def test_purity_latin_assamese_junk(self):
        r = self.run_rows([{"messages": [{"role": "user", "content": BN}, {"role": "assistant", "content": BN}]},
                           {"instruction": "Write a poem about rain", "output": "Rain falls softly."},
                           {"text": AS},
                           {"text": "[INST] " + BN + " [/INST]"},
                           {"text": BN + "​"}])
        self.assertEqual(r["rows"], 5)
        self.assertEqual(r["bn_purity"], 0.8)          # rows 1, 3 (same script), 4 (few Latin letters), 5
        self.assertEqual(r["latin_heavy"], 0.2)        # row 2
        self.assertEqual(r["as_marked"], 0.2)          # row 3
        self.assertEqual(r["junk_rows"], 2)            # rows 4 and 5

    def test_p95_is_nearest_rank(self):
        r = self.run_rows([{"t": "ক" * n} for n in range(1, 21)])   # 20 rows of 1..20 tokens
        self.assertEqual(r["tokens_p95"], 19)                       # rank ceil(0.95 * 20) = 19

    def test_nfc_unstable_counts_precomposed_nukta(self):
        r = self.run_rows([{"t": "বাড়ি"}, {"t": "বাড়ি"}])
        self.assertEqual(r["nfc_unstable"], 0.5)       # precomposed ড় (U+09DC) changes under NFC


def write_parquet(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)


class Overlap(unittest.TestCase):
    def test_counts(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            sent = d / "sent.parquet"
            write_parquet(sent, [
                {"inputs": 'Translate from English to Bengali: "Good  phone."', "targets": "ভালো ফোন।", "language": "ben"},
                {"inputs": 'Translate from English to Bengali: "Bad bag."', "targets": "অন্য কথা", "language": "ben"},
                {"inputs": 'Translate from English to Bengali: "Nice pen."', "targets": "ভালো কলম ও কালি।", "language": "ben"},
                {"inputs": 'Translate from English to Hindi: "Old fan."', "targets": "পুরনো পাখা।", "language": "hin"}])
            for split, rows in (("validation", [{"ENGLISH REVIEW": "Good phone.", "INDIC REVIEW": "ভালো ফোন।"}]),
                                ("test", [{"ENGLISH REVIEW": "Bad bag.", "INDIC REVIEW": "খারাপ ব্যাগ।"},
                                          {"ENGLISH REVIEW": "Old fan.", "INDIC REVIEW": "পুরনো পাখা।"},
                                          {"ENGLISH REVIEW": "Nice pen.", "INDIC REVIEW": "ভালো 'কলম' ও কালি।"}])):
                (d / "is" / split).mkdir(parents=True)
                write_jsonl(d / "is" / split / "bn.json", rows)
            para = d / "para.parquet"
            write_parquet(para, [{"inputs": "এই বাক্যটি একটু লম্বা করে লেখা হলো।", "targets": "হ্যাঁ", "language": "ben"}])
            tsv = d / "bn.tsv"
            tsv.write_text("en\tsentence1\tsentence2\tlabel\nAn English sentence that is long enough.\t"
                           "এই বাক্যটি একটু লম্বা করে লেখা হলো।\tএটা একেবারেই নতুন একটি বাক্য।\t1\n", encoding="utf-8")
            s = ov.sentiment(ov.aya_rows(sent, "ben"), d / "is", "bn")
            e = ov.english_side_all_languages(ov.aya_rows(sent), d / "is", "bn")
            p = ov.paraphrase(ov.aya_rows(para, "ben"), tsv)
        self.assertEqual(s["aya_rows"], 3)
        self.assertEqual(s["validation"], {"items": 1, "distinct_english_reviews": 1, "english_review_in_aya_inputs": 1,
                                           "indic_review_in_aya_targets": 1,
                                           "indic_review_in_aya_targets_without_quote_marks": 1})
        # "Nice pen." matches only once the review's own quote marks are dropped
        self.assertEqual(s["test"], {"items": 3, "distinct_english_reviews": 3, "english_review_in_aya_inputs": 2,
                                     "indic_review_in_aya_targets": 0,
                                     "indic_review_in_aya_targets_without_quote_marks": 1})
        self.assertEqual(e["distinct_english_reviews"], 4)
        self.assertEqual(e["found_per_language"], {"ben": 3, "hin": 1})
        self.assertEqual(e["aya_rows_per_language"], {"ben": 3, "hin": 1})
        self.assertEqual(p, {"aya_rows": 1, "tsv_rows": 1, "sentences": 2, "sentences_in_aya": 1})


if __name__ == "__main__":
    unittest.main()
