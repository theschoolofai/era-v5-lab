"""Tests for the rules in sheets/medicine_english.md, loaded the way harmtest/harm_test.py loads them. All text is made up.

  python3 -m unittest discover -s spec_v1_1/tests      (from teams/01-data-a)
"""
import sys
import unittest
from pathlib import Path

SPEC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPEC.parent / "harmtest"))  # harm_test.py moved here from tools/ (theschoolofai/era-v5-lab#244)
import harm_test  # noqa: E402  (only its loader is used; the file is not changed)

SHEET = SPEC / "sheets" / "medicine_english.md"
RULES, _ = harm_test.load_rules(SHEET)
RULES = RULES["RULES_BY_ID"]

PASSAGE = ("The letters show that the two ministers were watched closely in the months after the rising. "
           "Several reports name them, and the council asked for more evidence before it acted on any of them. "
           "Their names appear again in a later list of the parish.")  # 246 characters, over the 200 the rule needs


def doc(text, pack, doc_id="0" * 16):
    return {"doc_id": doc_id, "text": text, "url": "", "lang_label": "en", "pack_id": pack}


def run(rule_id, text, pack, **kw):
    return RULES[rule_id](doc(text, pack, **kw))


class Sheet(unittest.TestCase):
    def test_one_rule_for_each_new_english_disease(self):
        # DA-D6-002 (appended Q&A) was withdrawn on 13 Nov: 32 of 326 gold docs have the same Q&A
        self.assertEqual(sorted(RULES), ["DA-A8-003", "DA-D7-001"])

    def test_every_rule_is_off_on_other_packs(self):
        text = PASSAGE + "\n\nQuestion: Who? Answer: Them.\nas you choose.Compose a paper"
        for rid in RULES:
            for pack in ("en-dclm", "en-fineweb-edu", "math-finemath", None):
                self.assertEqual(run(rid, text, pack, doc_id="0f7b90400c1362df"), ("keep", text), (rid, pack))

    def test_each_rule_runs_only_on_its_pack(self):
        self.assertEqual(run("DA-D7-001", PASSAGE, "en-nemotroncc", doc_id="0f7b90400c1362df"), ("keep", PASSAGE))
        self.assertEqual(run("DA-A8-003", "choose.Compose a", "en-nemotroncc-synth"), ("keep", "choose.Compose a"))

    def test_appended_questions_and_answers_are_left_alone(self):
        # no rule removes them: the gold set has them in 32 of 326 en-nemotroncc-synth docs
        text = PASSAGE + "\n\nQuestion: Who were the two ministers? Answer: Two local ministers."
        for rid in RULES:
            self.assertEqual(run(rid, text, "en-nemotroncc-synth"), ("keep", text), rid)


class A8(unittest.TestCase):
    R, P = "DA-A8-003", "en-nemotroncc"

    def test_a_missing_space_after_a_full_stop_is_put_back(self):
        self.assertEqual(run(self.R, "as you choose.Compose a 500-word paper", self.P),
                         ("fix", "as you choose. Compose a 500-word paper"))
        self.assertEqual(run(self.R, "It ended there.Then, later", self.P), ("fix", "It ended there. Then, later"))

    def test_urls_abbreviations_names_and_code_stay(self):
        for text in ("Visit www.Google.com today", "See e.g.The list", "Ask Mr.Smith now", "Use Node.Js here",
                     "Every once in awhile", "x = obj.Value; return x", "```\nfoo.Bar baz\n```",
                     "mail me at user@example.Com now", "https://site.org/path.Name more"):
            self.assertEqual(run(self.R, text, self.P), ("keep", text), text)

    def test_idempotent(self):
        once = run(self.R, "as you choose.Compose it.Then go", self.P)[1]
        self.assertEqual(run(self.R, once, self.P), ("keep", once))


class D7(unittest.TestCase):
    R, P = "DA-D7-001", "en-nemotroncc-synth"

    def test_the_six_confirmed_docs_are_dropped(self):
        for did in ("0f7b90400c1362df", "0f7240ba1fdd3411", "52bd1da881ee0592", "f2a8b2cc25bb5c7a",
                    "5aeafd200220c080", "c3d88009d8a459e9"):
            self.assertEqual(run(self.R, PASSAGE, self.P, doc_id=did)[0], "drop", did)

    def test_the_appended_qa_doc_with_a_correct_answer_is_kept(self):
        self.assertEqual(run(self.R, PASSAGE, self.P, doc_id="ffaad5c6d3dde332"), ("keep", PASSAGE))

    def test_any_other_doc_is_kept(self):
        self.assertEqual(run(self.R, PASSAGE, self.P, doc_id="1" * 16), ("keep", PASSAGE))


if __name__ == "__main__":
    unittest.main()
