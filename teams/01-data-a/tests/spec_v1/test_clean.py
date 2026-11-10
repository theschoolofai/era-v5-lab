"""Unit tests for clean.py, the Spec v1 cleaner: its one function per disease code, the scope table at its top, and the
build that writes it from specv1.md. Every text here is made up; none comes from a pack. Some science rules act only on
documents the reviewers named, so those cases use the doc_id the rule lists in specv1.md (an ID, never the document's text).

  python -m pytest tests/spec_v1

  1  every disease-code function, on every family that has a rule for it
  2  the scope table and the build
  3  the code family: licences, generated files, the shared F1
  4  the English family: look-alikes, ZWJ and ZWNJ, DA-F1-005, clean() equal to the sheet
  5  the math family
  6  the shared F1 on the math and science packs: the prose path of spec_v1/build/f1_rule.py (TSAI, 1 Nov)
"""
import random
import re
import subprocess
import sys
import textwrap
import unicodedata
from functools import cache
from pathlib import Path

import pytest

SPEC = Path(__file__).resolve().parents[2] / "spec_v1"
BUILD = SPEC / "build" / "build_clean.py"
sys.path.insert(0, str(SPEC))
import clean as c

AT = "@"  # the secret and email scans read added lines, so made-up values are joined at run time
ZWJ, ZWNJ = chr(0x200D), chr(0x200C)  # written as numbers: a raw joiner in code is invisible
FAMILIES = {"code": {"code-cpp", "code-go", "code-java", "code-js-ts", "code-python", "code-rust"},
            "english": {"en-dclm", "en-fineweb-edu", "en-nemotroncc", "en-nemotroncc-synth"},
            "math": {"math-finemath", "math-megamath"}, "sci": {"sci-finepdfs"},
            "indic": {"ind-bn-fw2", "ind-gu-fw2", "ind-hi-fw2", "ind-hi-hplt", "ind-kn-fw2",
                      "ind-kn-sangraha-s", "ind-kn-sangraha-v", "ind-mr-fw2", "ind-mr-sangraha-v",
                      "ind-sa-fw2", "ind-ta-sangraha-v", "ind-te-fw2", "ind-te-sangraha-s",
                      "ind-bn-sangraha-v", "ind-hi-indiccorp", "ind-hi-sangraha-s", "ind-te-sangraha-v"}}
PACKS = sorted(set().union(*FAMILIES.values()))
SHEET = (SPEC / "sheets" / "specv1.md").read_text(encoding="utf-8")
SECTIONS = [(family, rid) for family, rid, body in re.findall(
    r"^## Medicine \d+ — (\w+) / \w+ / `(D[AB]-[A-H]\d-\d{3})`\n(.*?)(?=^## Medicine |\Z)", SHEET, re.S | re.M)
    if '```python deferred\n' not in body]

GO_CODE = 'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("hi")\n}\n'
JAVA_CODE = "class A {\n    int x = 1;\n}\n"
LICENCE = ("// Licensed under the Apache License, Version 2.0 (the License);\n// you may not use this file except in compliance with the License.\n"
           "// You may obtain a copy of the License at\n//     the licence site\n// Unless required by applicable law or agreed to in writing, software\n"
           "// distributed under the License is distributed on an AS IS BASIS,\n// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.\n")
EN_TEXT = "The river rises in the hills and runs south to the sea.\nFarmers along its banks grow rice and wheat.\n"
PARA = ("The river rises in the hills and runs south to the sea. "
        "Farmers along its banks grow rice and wheat in the dry months.")
RUSSIAN = "Это строка на русском языке."
HINDI_ZWJ = "क्\u200dष"   # half ka + ssa: the joiner asks for the half form
HINDI_ZWNJ = "क्\u200cष"  # ka + virama + ssa: the joiner stops the conjunct
OTHER_LANGS = ("hi", "mr", "fr", None)  # not English and not a code language: every rule keeps
BODY = "Let x be a real number. Then x squared is never negative, so the sum of two squares is at least zero.\n"
SCI = "We measured the reaction rate at 300 K. The rate constant was 2.5 per second, as Table 1 shows.\n"
OPENING = ("Background. " + SCI + "The second sentence of the abstract explains the sample, the method and the error bars.\n"
           "A third line names the funding body and the year of the survey, which was 2019.\n")  # 200+ characters, no repeat inside


def doc(pack, text, lang): return {"doc_id": "x", "text": text, "url": "http://a/b", "lang_label": lang, "pack_id": pack}
def code(text, lang="go", pack="code-go"): return {"doc_id": "x", "text": text, "url": "a/b", "lang_label": lang, "pack_id": pack}
def maths(text, pack="math-finemath"): return doc(pack, text, "en")
def sci(text, doc_id="x"): return dict(doc("sci-finepdfs", text, "eng_Latn"), doc_id=doc_id)  # the science pack's tag


def en(text, lang="en"):
    """A document of an English pack: en-dclm is tagged en, en-nemotroncc is tagged eng."""
    return doc("en-nemotroncc" if lang == "eng" else "en-dclm", text, lang)


def joiners(s):
    return s.count(ZWJ), s.count(ZWNJ)


# DA-F1-005 asks whether an organisation word sits in the 13 lines around a contact line (6 each way), and whether a
# public role (reporter, editor ...) sits in the line or the 2 lines above an email. These lines hold no digit, no
# at-sign and none of those words, and each differs from the others, so no other rule sees a repeat.
FILL = ["The river rises in the hills.", "It runs south to the sea.", "Growers plant rice and wheat.", "The dry months are long.",
        "Rain returns in June.", "Boats cross the bend at dawn.", "Fish are sold at noon.", "Evenings are quiet and cool.",
        "Children swim near the sandbar."]
ORG_LINE, ORG_LINE_2 = "The library is on the corner.", "The museum opens at nine."
PHONE_LINE, PHONE_MASKED = "Call 555-867-5309 now.", "Call <PHONE> now."
EMAIL_LINE, EMAIL_MASKED = "Write to ravi.kumar" + AT + "brightwave.net today.", "Write to <EMAIL> today."
ROLE_LINE, REACH_LINE = "The reporter wrote this story.", "Reach jane.doe" + AT + "newsdesk.net today."
ORG_VOICE_LINE = "Please call us any time."  # one phrase like this makes the whole page an organisation's


def gap(n):
    """n different lines with nothing in them, as a block of text."""
    return "\n".join(FILL[:n])


# 1. Every disease-code function, on every family that has a rule for it

# (family, function, document, what the function does, the text after a fix: None checks only that the text changed)
SICK = [
    ("code", "A1", code("\ufeff" + GO_CODE), "fix", None),
    ("code", "A2", code(GO_CODE.replace("\n", "\r\n")), "fix", None),
    ("code", "A6", code("package main // pаssword\n"), "fix", None),  # a Cyrillic a inside a Latin word
    ("code", "A4", code("package main\n// ��\n"), "fix", None),
    ("code", "B3", code("<reponame>a/b\n" + GO_CODE), "fix", None),
    ("code", "E1", code("// Code generated by protoc-gen-go. DO NOT EDIT.\n" + GO_CODE), "drop", None),
    ("code", "E2", code(GO_CODE + "var blob = []byte{" + "0x00, " * 40 + "}\n"), "drop", None),
    ("code", "C3", code('package main\n\nfunc main() {\n\tfmt.Println("hi\n'), "drop", None),
    ("code", "C4", code(JAVA_CODE + "_" * 25 + "\n" + JAVA_CODE, "java", "code-java"), "drop", None),  # two files joined
    ("code", "E4", code(LICENCE + "\n" + GO_CODE), "fix", None),
    ("code", "C1", code("package v1\n\n// EDIT THIS FILE!  THIS IS SCAFFOLDING FOR YOU TO OWN!\ntype A struct{}\n"), "fix", None),
    ("code", "B4", code('package main\nconst a = "<NAME>"\n'), "fix", None),
    ("code", "E3", code('package main\nconst k = "AKIA' + "ABCDEFGHIJKLMNOP" + '"\n'), "fix", None),
    ("code", "F1", code("package main // by a" + AT + "mail.io\n"), "fix", None),  # the shared F1, build/f1_rule.py

    ("english", "A1", en("Hello\u200bworld\ufeff and more."), "fix", "Helloworld and more."),
    ("english", "A2", en("Bell\x07 here\r\nnext line"), "fix", "Bell here\nnext line"),
    ("english", "A3", en("The cafÃ© didnâ€™t open on Monday. " + PARA), "fix", "The café didn't open on Monday. " + PARA),  # mojibake
    ("english", "A5", en("Café au lait"), "fix", "Café au lait"),  # a decomposed accent
    ("english", "B1", en("Fish &amp; chips&nbsp;today &mdash; fresh."), "fix", "Fish & chips today — fresh."),
    ("english", "B2", en("<p>First paragraph.</p><div>Second paragraph.</div>"), "fix", " First paragraph. Second paragraph. "),
    ("english", "C3", en("The council will meet on Monday to discuss the"), "drop", None),
    ("english", "C3", en("Short teaser ending here [...]"), "drop", None),
    ("english", "C5", en("Buy cheap nfl jerseys today and ray ban sunglasses outlet deals. " + PARA), "drop", None),
    ("english", "C5", en(PARA + "\nTags: river, farming, rice"), "fix", PARA),
    ("english", "D4", en("{Hello|Hi} there, {friend|buddy}. " + PARA), "drop", None),
    ("english", "C1", en(PARA + "\nShare this:\n" + PARA), "fix", PARA + "\n" + PARA),
    ("english", "C2", en("Subscribe to our newsletter\n" + PARA + "\nSubscribe to our newsletter\nMore text.\nSubscribe to our newsletter"),
     "fix", "Subscribe to our newsletter\n" + PARA + "\n\nMore text.\n"),
    ("english", "D3", en(PARA + "\n" + RUSSIAN + "\n" + PARA), "fix", PARA + "\n" + PARA),
    ("english", "B4", en("Welcome {{ user.name }} to the shop. " + PARA), "fix", "Welcome  to the shop. " + PARA),
    ("english", "B4", en("Total Due After -DATE-: 40 dollars. " + PARA), "fix", "Total Due After the Due Date: 40 dollars. " + PARA),
    ("english", "B4", en("Price: NaN\n" + PARA), "fix", "Price:\n" + PARA),
    ("english", "B4", en("She called it'smart work' today. " + PARA), "fix", "She called it 'smart work' today. " + PARA),
    ("english", "B4", en(PARA + " The text does not mention the price. " + PARA), "fix", PARA + " " + PARA),
    ("english", "F1", en(PARA + "\nCall me on 555-867-5309 or write to ravi.kumar" + AT + "gmail.com."), "fix",
     PARA + "\nCall me on <PHONE> or write to <EMAIL>."),  # DA-F1-005
    ("english", "F1", en(PARA + "\nI live at 42 Elm Street, Springfield, IL 62704."), "fix", PARA + "\nI live at <ADDRESS>."),
    # DA-F1-005, the 13-line window: an organisation word 6 lines away keeps the contact, one 7 lines away does not
    ("english", "F1", en(ORG_LINE + "\n" + gap(5) + "\n" + PHONE_LINE), "keep", None),
    ("english", "F1", en(ORG_LINE + "\n" + gap(6) + "\n" + PHONE_LINE), "fix",
     ORG_LINE + "\n" + gap(6) + "\n" + PHONE_MASKED),
    ("english", "F1", en(EMAIL_LINE + "\n" + gap(5) + "\n" + ORG_LINE), "keep", None),  # the same below the contact line
    ("english", "F1", en(EMAIL_LINE + "\n" + gap(6) + "\n" + ORG_LINE), "fix",
     EMAIL_MASKED + "\n" + gap(6) + "\n" + ORG_LINE),
    ("english", "F1", en(FILL[0] + "\n" + PHONE_LINE + "\n" + ORG_LINE_2), "keep", None),  # an organisation on the next line
    ("english", "F1", en(ORG_VOICE_LINE + "\n" + gap(9) + "\n" + PHONE_LINE), "keep", None),  # an organisation's page, far away
    ("english", "F1", en("Email me at ravi dot kumar at brightwave dot net.\nPhone: five five five, eight six seven.\n" + ORG_LINE),
     "keep", None),  # no digit and no at-sign on any line
    ("english", "F1", en(FILL[0] + "\n\n" + PHONE_LINE + "\n\n" + FILL[1] + "\n"), "fix",
     FILL[0] + "\n\n" + PHONE_MASKED + "\n\n" + FILL[1] + "\n"),  # only the contact line changes: blank lines and the last newline stay
    # a public role in the email line or the 2 lines above it keeps an email at an organisation's domain; 3 lines above does not
    ("english", "F1", en(ROLE_LINE + "\n" + FILL[1] + "\n" + REACH_LINE), "keep", None),
    ("english", "F1", en(ROLE_LINE + "\n" + FILL[1] + "\n" + FILL[2] + "\n" + REACH_LINE), "fix",
     ROLE_LINE + "\n" + FILL[1] + "\n" + FILL[2] + "\nReach <EMAIL> today."),

    ("math", "A3", maths("Hereâ€™s the proof.\n" + BODY), "fix", None),  # mojibake of a right single quote
    ("math", "A1", maths("Area\u200b of a circle is pi r squared.\n" + BODY), "fix", None),
    ("math", "A5", maths("the ﬁrst term\n" + BODY), "fix", None),  # the fi ligature
    ("math", "B2", maths("x<br>y and <strong>z</strong>\n" + BODY), "fix", None),
    ("math", "B4", maths("{{ 'course-label' | message }}\n" + BODY), "fix", None),
    ("math", "B5", maths("$$$x^2$$\n" + BODY), "fix", None),
    ("math", "C5", maths(BODY + "See more: Ten Fun Facts About Algebra\n"), "fix", None),
    ("math", "C5", maths("Study guides\n\nQ: What is 3 divided by 4?\n\nWrite your answer...\n\nSubmit\n\nRelated questions\n\nIt is 0.75.\n",
                         "math-megamath"), "drop", None),
    ("math", "C3", maths("This preview shows page 1 - 2 out of 4 pages.\n" + BODY), "drop", None),
    ("math", "C1", maths(BODY + "Share\nWrite a comment\n"), "fix", None),
    ("math", "C2", maths(BODY + "Introductory Physics Homework Help forum\n" * 6), "fix", None),
    ("math", "A6", maths("x \uf0c5 y is the exclusive or.\n" + BODY), "fix", None),  # a Symbol-font glyph in the private use area
    ("math", "D3", maths(BODY + "Дивитися фільми онлайн\n" + BODY), "fix", None),  # a foreign-script spam line
    ("math", "F1", maths(BODY + "Home: 217-555-0123\n"), "fix", None),  # the shared F1, prose path: a private label on a made-up number

    ("sci", "B4", sci("Call FUN and <function name> in the text.\n" + SCI), "fix", None),
    ("sci", "B2", sci("The area is 4 m<sup>2</sup> at the start.\n" + SCI, "7ea84af3398cb3ed"), "fix", None),  # a reviewed ID
    ("sci", "B5", sci("Rates rose\\footnote{See the appendix.} in May.\n" + SCI, "80c340aef304a24c"), "fix", None),  # a reviewed ID
    ("sci", "A1", sci("Rates\u200b rose.\n" + SCI), "fix", None),
    ("sci", "A6", sci("A smooth抽吸 surface.\n" + SCI, "12e943fb710cab5b"), "fix", None),  # the one reviewed intrusion
    ("sci", "C1", sci("A Study of Rates\nMPRA Paper No. 12345, posted 1 May 2020 10:00 UTC\n" + SCI * 12), "fix", None),  # an archive cover
    ("sci", "C2", sci(OPENING + OPENING + "The end of the paper.\n"), "fix", None),  # the opening passage twice
    ("sci", "C3", sci(SCI, "26a07693d706218f"), "drop", None),  # reviewed: cut off beyond repair
    ("sci", "C4", sci(SCI, "44f66c3734e3d5ca"), "drop", None),  # reviewed: two records joined
    ("sci", "D1", sci(SCI, "44f66c3734e3d5ca"), "drop", None),  # reviewed: wrong language label
    ("sci", "F1", sci(SCI, "b0d032fadb33dbf4"), "drop", None),  # DA-F1-006: a reviewed private-person record
    ("sci", "D3", sci(SCI + "Le taux est élevé.\n"), "keep", None),  # DA-D3-004 keeps mixed language: it has no sick case
]
ENGLISH_SICK = [(fn, d["text"], action, after) for fam, fn, d, action, after in SICK if fam == "english"]
CLEAN = {"code": code(GO_CODE), "english": en(PARA + "\n\n" + PARA), "english, tagged eng": en(PARA + "\n\n" + PARA, "eng"),
         "math": maths(BODY * 3), "math, display maths": maths(BODY + "Display: $$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$ and $$a$$$$b$$ are two blocks.\n"),
         "sci": sci(SCI * 2)}


def test_every_function_is_tested_on_every_family_it_has_a_rule_for():
    pairs = {(fam, c._ID[make].split("-")[1]) for fam, rules in c._PIPELINES.items() for make in rules}
    pairs |= {(fam, "F1") for fam, rules in c._PIPELINES.items() if c.SCOPE["f1_rule.py"] & {p for m in rules for p in c.SCOPE[c._ID[m]]}}  # the shared F1
    # Indic's source-equivalence, Unicode and pipeline checks are in test_indic_integration.py.
    assert {(fam, fn) for fam, fn, *_ in SICK} == {(fam, fn) for fam, fn in pairs if fam != "indic"}
    assert set(c.RULES) == {code for _, code in pairs}  # every registered disease has a pipeline rule
    assert all(c.RULES[k].__name__ == k.lower() for k in c.RULES)


@pytest.mark.parametrize("family, fn, row, action, after", SICK, ids=[f"{f}-{fn}-{i}" for i, (f, fn, *_) in enumerate(SICK)])
def test_a_function_treats_a_sick_document(family, fn, row, action, after):
    if (family, fn) == ("code", "F1"):
        pytest.importorskip("tree_sitter_language_pack")  # the shared F1 reads comments and strings in code with tree-sitter
    a, new = c.RULES[fn](row)
    assert a == action
    if action in ("drop", "keep"):
        assert new == row["text"]  # a drop hands back the document as it was
    elif after is not None:
        assert new == after
    else:
        assert new != row["text"]


@pytest.mark.parametrize("kind", CLEAN)
@pytest.mark.parametrize("fn", list(c.RULES))
def test_a_function_keeps_a_clean_document(kind, fn):
    assert c.RULES[fn](CLEAN[kind]) == ("keep", CLEAN[kind]["text"])


@pytest.mark.parametrize("kind", CLEAN)
def test_clean_keeps_a_clean_document(kind):
    assert c.clean(CLEAN[kind]) == ("keep", CLEAN[kind]["text"])


# 2. The scope table (SCOPE) and build/build_clean.py, which writes it from specv1.md

def test_every_rule_has_one_scope_entry_in_sheet_order():
    assert list(c.SCOPE) == list(c._RULE) == [rid for _, rid in SECTIONS] + ["f1_rule.py"]
    assert all(isinstance(packs, frozenset) and packs for packs in c.SCOPE.values())


def test_each_pack_is_in_exactly_one_family():
    assert {f: {p for p, g in c._FAMILY.items() if g == f} for f in FAMILIES} == FAMILIES
    for fam, rid in SECTIONS:
        assert c.SCOPE[rid] <= FAMILIES[fam]


def test_each_family_runs_its_rules_in_sheet_order():
    assert {f: [c._ID[make] for make in rules] for f, rules in c._PIPELINES.items()} == {f: [rid for g, rid in SECTIONS if g == f] for f in FAMILIES}


def test_the_f1_rules_cover_their_whole_family():
    assert c.SCOPE["DA-F1-005"] == FAMILIES["english"]  # the instructor's F1 rule, never left out
    assert c._PIPELINES["english"][-1] is c._english_f1_005  # and last in the English family
    assert 'RULE_ID = "DA-F1-005"' in (SPEC / "clean.py").read_text(encoding="utf-8")
    assert c.SCOPE["DA-F1-006"] == FAMILIES["sci"]
    assert c.SCOPE["f1_rule.py"] == FAMILIES["code"] | FAMILIES["math"] | FAMILIES["sci"] | FAMILIES["indic"]  # the shared F1
    assert not [rid for rid in c._RULE if rid.startswith("DB-F1-")]  # Indic's source F1 rules are deferred: the shared F1 replaces them
    assert not c.SCOPE["f1_rule.py"] & FAMILIES["english"]  # English keeps its own F1, DA-F1-005
    assert c.RULES["F1"] is c.f1


def test_a_math_rule_takes_the_packs_of_its_origin():
    assert c.SCOPE["DA-A1-005"] == {"math-finemath"} and c.SCOPE["DA-C5-001"] == {"math-megamath"}
    assert c.SCOPE["DA-A3-001"] == FAMILIES["math"]


@pytest.mark.parametrize("rid, text, lang", [
    ("DA-A1-001", "\ufeffpackage main\n", "go"),                           # code A1: a BOM
    ("DA-A1-004", "The river\u200b rises in the hills.\n", "en"),          # English A1: a zero-width space
    ("DA-A1-005", "Area\u200b of a circle is pi r squared.\n", "en"),       # math A1, finemath only
    ("DA-B4-013", "Call FUN and <function name> in the text.\n", "en"),    # science B4: a converter label
])
@pytest.mark.parametrize("pack", PACKS)
def test_a_rule_acts_only_on_the_packs_of_its_scope(rid, text, lang, pack):
    expect = "fix" if pack in c.SCOPE[rid] else "keep"
    assert c._RULE[rid]()(doc(pack, text, lang))[0] == expect  # the rule's own guard, which reads SCOPE
    assert c._run(doc(pack, text, lang), c._RULE[rid])[0] == expect  # and _run, which checks SCOPE before any rule


def test_the_scope_table_decides(monkeypatch):
    text = "\ufeffpackage main\n"
    assert c.a1(doc("code-go", text, "go"))[0] == "fix"
    monkeypatch.setitem(c.SCOPE, "DA-A1-001", frozenset({"code-cpp"}))
    assert c.a1(doc("code-go", text, "go")) == ("keep", text)


@pytest.mark.parametrize("pack", [None, "en-unknown"])
def test_no_rule_runs_without_a_known_pack(pack):
    row = {k: v for k, v in doc(pack, "\ufeffArea\u200b of <b>a</b> circle.\n", "en").items() if v is not None}
    assert c.clean(row) == ("keep", row["text"])
    assert all(c._run(row, make) == ("keep", row["text"]) for make in c._RULE.values())


def build(tmp_path, sheet=SHEET):
    (tmp_path / "specv1.md").write_text(sheet, encoding="utf-8", newline="\n")
    return subprocess.run([sys.executable, "-I", str(BUILD), "--sheet", str(tmp_path / "specv1.md"), "--out", str(tmp_path / "clean.py")],
                          capture_output=True, encoding="utf-8", errors="replace")  # the build prints UTF-8 (Indic letters), on Windows too


def with_packs(rid, packs):
    """specv1.md with the SPEC_PACKS line of one rule changed."""
    start = SHEET.index(f"/ `{rid}`")
    end = SHEET.index("\n## Medicine ", start)
    section = re.sub(r"^SPEC_PACKS = .*$", f"SPEC_PACKS = {packs!r}", SHEET[start:end], count=1, flags=re.M)
    return SHEET[:start] + section + SHEET[end:]


def test_the_build_writes_this_clean_py(tmp_path):
    r = build(tmp_path)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "clean.py").read_bytes() == (SPEC / "clean.py").read_bytes()


@pytest.mark.parametrize("rid, packs, error", [
    ("DA-A1-004", set(), "applies to no pack"),
    ("DA-A1-004", FAMILIES["english"] | {"math-finemath"}, "in two families"),
    ("DA-F1-005", {"en-dclm"}, "DA-F1-005 must be in the sheet"),
])
def test_the_build_stops_on_a_bad_scope(tmp_path, rid, packs, error):
    r = build(tmp_path, with_packs(rid, packs))
    assert r.returncode != 0 and error in r.stderr
    assert not (tmp_path / "clean.py").exists()


# 3. The code family

@pytest.fixture
def prose(monkeypatch):
    """The shared F1 (spec_v1/build/f1_rule.py) on prose. clean.py runs it on the code, math and sci packs; English has its own F1, DA-F1-005."""
    monkeypatch.setattr(c, "_F1_LANGS", c._F1_LANGS | {"en"})


def test_keeps_a_build_tag_when_a_licence_goes():
    text = "//go:build linux\n\n" + LICENCE + "\n" + GO_CODE
    a, new = c.clean(code(text))
    assert a == "fix" and new.count("go:build linux") == 1 and "Apache" not in new


def test_a_generated_file_with_its_banner_in_the_licence_is_dropped():
    assert c.clean(code(LICENCE + "// Code generated by mockgen. DO NOT EDIT.\n" + GO_CODE))[0] == "drop"


def test_code_language_guards_and_pack_scoped_bom_cleanup():
    row = code("\ufeff<reponame>a\n" + GO_CODE, lang="fra")
    # The existing A1 sheet uses a pack guard; B3 and E4 also guard the language.
    assert c.a1(row) == ("fix", row["text"].replace("\ufeff", ""))
    assert c.b3(row)[0] == c.e4(row)[0] == "keep"


@pytest.mark.parametrize("line, expect", [
    (f"Write to jane.doe{AT}acme.test today.", "Write to jane.doe" + AT + "acme.test today."),  # a test domain is never a real person
    (f"Write to jane.doe{AT}acme.io today.", "Write to <EMAIL> today."),
    (f"Write to support{AT}acme.io today.", f"Write to support{AT}acme.io today."),
    (f"Write to clerk{AT}city.gov today.", f"Write to clerk{AT}city.gov today."),
    ("Her mobile: 555-010-0199.", "Her mobile: <PHONE>."),
    ("Reach her on +91 98765 43210.", "Reach her on <PHONE>."),
    ("Her phone 98765 43210 works.", "Her phone <PHONE> works."),
    ("Her phone 9876543210 works.", "Her phone <PHONE> works."),
    ("She lives at 221B Baker Street now.", "She lives at <ADDRESS> now."),
    ("She lives at 18 MG Road now.", "She lives at <ADDRESS> now."),
    ("Reach her on +1 555 010 0199.", "Reach her on <PHONE>."),
    ("Call Acme Ltd on 555-010-0199.", "Call Acme Ltd on 555-010-0199."),
    ("She lives at 12 Elm Grove Road in the town.", "She lives at <ADDRESS> in the town."),
    ("The City Council is at 12 Elm Grove Road.", "The City Council is at 12 Elm Grove Road."),
])
def test_shared_f1_replaces_a_private_person_and_keeps_organisations(prose, line, expect):
    assert c._shared_f1(en(line))[1] == expect


@pytest.mark.parametrize("line", ["Released on 2021-03-14 at 10:30.", "Version 1.2.3.4 of the tool.", "Total 123 456 7890 units.", f"logo{AT}2x.png and {AT}types/node", 'x = [1000 2000 3000]'])
def test_shared_f1_leaves_numbers_and_code_that_look_alike(prose, line):
    assert c._shared_f1(en(line)) == ("keep", line)


def test_shared_f1_drops_a_personal_listing(prose):
    listing = "\n".join(f"person{i}{AT}mail.io" for i in range(6))
    assert c._shared_f1(en(listing))[0] == "drop"


def test_shared_f1_keeps_a_long_article_with_one_address(prose):
    text = EN_TEXT * 20 + f"Written by a{AT}mail.io\n"
    a, new = c._shared_f1(en(text))
    assert a == "fix" and "<EMAIL>" in new


def test_b4_leaves_the_email_tag_and_fixes_the_others():
    a, new = c.b4(code('package main\nconst a = "<EMAIL> <NAME> <KEY> <PASSWORD>"\n'))
    assert a == "fix" and "<EMAIL>" in new and not any(t in new for t in ("<NAME>", "<KEY>", "<PASSWORD>"))


@pytest.mark.parametrize("text, expect", [
    ("package main\n// by a" + AT + "mail.io\n", "package main\n// by <EMAIL>\n"),
    ('package main\nconst a = "mobile: 555-010-0199"\n', 'package main\nconst a = "mobile: <PHONE>"\n'),
    ("package main\nvar x = 555-010-0199\n", "package main\nvar x = 555-010-0199\n"),  # arithmetic in code
])
def test_f1_in_code_touches_only_comments_and_strings(text, expect):
    pytest.importorskip("tree_sitter_language_pack")
    assert c.f1(code(text))[1] == expect


def test_the_shared_f1_runs_on_code():
    row = code("package main\n")
    assert c.f1(row) == c._shared_f1(row)


@pytest.mark.parametrize("row", [code(LICENCE + GO_CODE), code("<reponame>a\n\ufeff" + GO_CODE), code(GO_CODE.replace("\n", "\r\n"))])
def test_clean_twice_is_clean_once_on_code(row):
    a, once = c.clean(row)
    assert a != "drop"
    assert c.clean(dict(row, text=once)) == ("keep", once)


def test_f1_tag_survives_a_second_clean():
    """This failed while B4 rewrote <EMAIL>: a second clean() turned the F1 tag into user@example.com."""
    pytest.importorskip("tree_sitter_language_pack")
    a, once = c.clean(code(f"package main // by a{AT}mail.io\n"))
    assert a == "fix" and "<EMAIL>" in once
    assert c.clean(code(once)) == ("keep", once)


# 4. The English family

# (code, a text that looks like the disease but is not: it must stay as it is)
LOOK_ALIKE = [
    ("A1", "A plain line with café and an em dash — here."),
    ("A1", "Hindi keeps its joiners: " + HINDI_ZWJ + " and " + HINDI_ZWNJ + "."),
    ("A2", "Tab\tseparated\nlines"),
    ("A3", "A café in São Paulo opens at nine. " + PARA),
    ("A5", "Café au lait"),
    ("B1", "AT&T and R&D work together."),
    ("B2", "Use the <p> tag to start a paragraph in HTML."),
    ("C3", PARA),
    ("C5", PARA + "\nThe tags on the bags were lost."),
    ("D4", "Pipes like a|b and braces {x} are fine. " + PARA),
    ("C1", PARA + "\nShare this story with your friends today.\n" + PARA),
    ("C2", "Subscribe to our newsletter\n" + PARA + "\nSubscribe to our newsletter"),
    ("D3", PARA + " He said спасибо to us."),
    ("B4", PARA + " Sets use { and } braces."),
    ("F1", PARA + "\nContact our office at info" + AT + "acme.com or call 1-800-555-0199."),
    ("F1", PARA + "\nThe years 1990 to 2005 saw 3,000 new farms."),
]

# joiners in every context a rule could touch; no line here is one a rule removes
JOINER_PROBES = dict(zip([
    "hindi-zwj", "hindi-zwnj", "malayalam-chillu", "persian-zwnj", "emoji-family", "emoji-flag", "beside-a1-junk",
    "crlf-and-control", "mojibake", "decomposed-accent", "html", "phone", "address", "long-paragraph", "joiner-in-tags"], [
    "The word " + HINDI_ZWJ + " is written with a half ka.",
    "The word " + HINDI_ZWNJ + " keeps the virama visible.",
    "Old Malayalam writes ന്\u200d for the chillu n.",
    "In Persian, می\u200cخواهم means I want.",
    "Our family \U0001F468\u200d\U0001F469\u200d\U0001F467 went on a trip.",
    "Pride month \U0001F3F3️\u200d\U0001F308 starts in June.",
    "Mixed\u200b\u200d\ufeff\u200c junk\u00ad and joiners here.",
    "Line one \u200d\r\nLine two\x07 \u200c here.\r\n",
    "The cafÃ© sells " + HINDI_ZWJ + " tea, didnâ€™t it?",
    "Café and " + HINDI_ZWNJ + " together.",
    "Entities &amp; joiners \u200d inside <b>bold \u200c</b> text.",
    "Call Ravi \u200d on 555-867-5309 tonight \u200c please.",
    "He lives at 42 Elm Street \u200d, Springfield, IL 62704 \u200c now.",
    ("Hindi text uses " + HINDI_ZWJ + " and " + HINDI_ZWNJ + ". ") * 30,
    PARA + "\n" + "Tags" + ZWJ + ": not a tag line, the joiner is inside the word\n" + PARA,
]))


@cache
def sheet():
    """The English blocks of specv1.md, in sheet order, each in its own namespace, as harm_test.py runs them."""
    out = []
    for rid, body in re.findall(r"^## Medicine \d+ — english / \w+ / `([^`]+)`\n(.*?)(?=^## Medicine |\Z)", SHEET, re.S | re.M):
        ns = {"__name__": "rules"}
        exec(textwrap.dedent(re.search(r"^```python\n(.*?)^```", body, re.S | re.M).group(1)), ns)
        assert ns["RULE_ID"] == rid
        out.append((rid, ns["medicine"]))
    return out


def run_sheet(row):
    d = dict(row)
    for _, m in sheet():
        a, t = m(d)
        if a == "drop":
            return ("drop", row["text"])
        d["text"] = t
    return ("fix" if d["text"] != row["text"] else "keep", d["text"])


@pytest.mark.parametrize("fn, text", LOOK_ALIKE, ids=[f"{x[0]}-{i}" for i, x in enumerate(LOOK_ALIKE)])
def test_leaves_a_look_alike(fn, text):
    assert c.RULES[fn](en(text)) == ("keep", text)


@pytest.mark.parametrize("text", [t for _, t, _, _ in ENGLISH_SICK], ids=[f"{x[0]}-{i}" for i, x in enumerate(ENGLISH_SICK)])
def test_a_row_of_another_language_passes_unchanged(text):
    for lang in OTHER_LANGS:
        row = en(text, lang)
        assert all(fn(row) == ("keep", text) for fn in c.RULES.values())
        assert c.clean(row) == ("keep", text)


@pytest.mark.parametrize("text", [t for _, t, a, _ in ENGLISH_SICK if a == "fix"] + [PARA],
                         ids=[f"{x[0]}-{i}" for i, x in enumerate(ENGLISH_SICK) if x[2] == "fix"] + ["plain"])
def test_clean_twice_is_clean_once(text):
    a, once = c.clean(en(text))
    if a != "drop":
        assert c.clean(en(once)) == ("keep", once)


# Keep ZWJ and ZWNJ in all text (DISEASES.md, A1: "ZWJ U+200D and ZWNJ U+200C are NOT diseases in Indic text").

@pytest.mark.parametrize("text", JOINER_PROBES.values(), ids=JOINER_PROBES.keys())
def test_no_function_and_not_clean_deletes_a_joiner(text):
    for fn in list(c.RULES.values()) + [c.clean]:
        a, new = fn(en(text))
        assert a != "drop", fn.__name__
        assert joiners(new) == joiners(text), fn.__name__


def test_a1_takes_the_junk_and_leaves_the_joiners_beside_it():
    a, new = c.a1(en("Mixed\u200b\u200d\ufeff\u200c junk\u00ad here."))
    assert (a, new) == ("fix", "Mixed\u200d\u200c junk here.")


def test_d3_takes_a_joiner_only_with_a_whole_foreign_line():
    """D3 deletes a line whose letters are mostly not Latin, so a Hindi line in an English document goes with its
    joiners. That removes the line, not the joiner: a joiner in a line that stays is kept."""
    hindi_line = "यह " + HINDI_ZWJ + "त्रिय है और " + HINDI_ZWNJ + " भी।"
    english_line = "The half form " + HINDI_ZWJ + " appears in this English line."
    a, new = c.d3(en(PARA + "\n" + hindi_line + "\n" + english_line))
    assert (a, new) == ("fix", PARA + "\n" + english_line)
    assert joiners(new) == joiners(english_line)


# DA-D3-003: a line goes when it has 3 or more letters and more than half of them are not Latin. The rule skips ASCII lines
# (an ASCII letter is always Latin) and looks each letter's script up once, so these cases pin what it still must do.

def d3_reference(text):
    """DA-D3-003 as it was before the ASCII skip and the cache: unicodedata.name on every letter of every line."""
    def foreign(line):
        letters = [ch for ch in line if ch.isalpha()]
        return len(letters) >= 3 and sum(unicodedata.name(ch, "").split(" ")[0] != "LATIN" for ch in letters) / len(letters) > 0.5
    return "\n".join(line for line in text.split("\n") if not foreign(line))


def d3_result(text):
    """What d3 gives for text, in the shared form, from the reference."""
    out = d3_reference(text)
    return ("drop", text) if not out.strip() else ("fix" if out != text else "keep", out)


# (the line, whether D3 deletes it). Each line sits between two English paragraphs.
D3_LINES = [
    ("Hello world, and more. It's 5 o'clock (almost)!", False),   # ASCII only
    ("12345 67890 -- ??", False),                                 # no letters at all
    ("Café naïve façade déjà vu Ångström", False),                # Latin letters outside ASCII
    ("Это строка на русском языке.", True),                       # Cyrillic
    ("日本語のテキストです", True),                                 # Han and Hiragana
    ("한국어 문장입니다", True),                                     # Hangul
    ("यह हिंदी की एक पंक्ति है", True),                           # Devanagari
    ("Ελληνικό κείμενο εδώ", True),                               # Greek
    ("Hello Привет мир", True),                                   # ASCII word and Cyrillic: 9 of 14 letters are not Latin
    ("The word привет means hello in Russian.", False),           # a foreign word inside an English sentence: 6 of 32
    ("12345 -- привет", True),                                    # digits and punctuation do not count as letters
    ("ab аб", False),                                             # exactly half non-Latin is not more than half
    ("ab абв", True),                                             # 3 of 5
    ("abc аб", False),                                            # 2 of 5
    ("аб", False),                                                # fewer than 3 letters: kept however foreign
    ("я", False),
    ("абв", True),                                                # exactly 3 letters
]


@pytest.mark.parametrize("line, goes", D3_LINES, ids=[f"d3-line-{i}" for i in range(len(D3_LINES))])
def test_d3_deletes_a_line_only_when_more_than_half_its_letters_are_not_latin(line, goes):
    text = PARA + "\n" + line + "\n" + EN_TEXT
    a, new = c.d3(en(text))
    assert (a, new) == (("fix", PARA + "\n" + EN_TEXT) if goes else ("keep", text))
    assert (a, new) == d3_result(text)  # and the reference agrees


def test_d3_cached_script_lookup_equals_unicodedata_name_for_every_letter():
    """A line of one repeated letter goes exactly when the reference says so, for every alphabetic code point. The same
    letters come up again and again, so this also reads the cache after it is filled."""
    for _ in range(2):
        for cp in range(0x110000):
            if chr(cp).isalpha():
                line = chr(cp) * 3
                text = PARA + "\n" + line
                a, new = c.d3(en(text))
                assert (a == "fix") == (unicodedata.name(chr(cp), "").split(" ")[0] != "LATIN"), hex(cp)
                assert new == d3_reference(text), hex(cp)


def test_every_ascii_letter_is_latin():
    """The reason D3 may skip an ASCII line."""
    assert all(unicodedata.name(chr(cp)).split(" ")[0] == "LATIN" for cp in range(128) if chr(cp).isalpha())


def test_d3_equals_the_unicodedata_reference_on_random_documents():
    """Random lines from scripts, digits, punctuation and spaces, so that ASCII, Latin, foreign and mixed lines all come up."""
    pools = ["abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789 .,;:!?'-()", "    ", "éèàüöñçøåßÿ", "абвгдежзийклмн", "ΑΒΓαβγδεζ",
             "日本語中文字漢", "한국어문장", "कखगघचछजझ्ािी", "ابتثجحخد", "😀🙂★☆"]
    rng = random.Random(11)
    docs = []
    for _ in range(3000):
        lines = []
        for _ in range(rng.randint(1, 8)):
            mix = rng.sample(pools, rng.randint(1, 3))
            lines.append("".join(rng.choice(rng.choice(mix)) for _ in range(rng.randint(0, 40))))
        docs.append("\n".join(lines))
    cut = [d for d in docs if d3_reference(d) != d]
    assert 300 < len(cut) < len(docs) - 300  # lines go in some documents and stay in others: the check is not vacuous
    for d in docs:
        assert c.d3(en(d)) == d3_result(d)


@pytest.mark.parametrize("lang", ["en", "eng"])
def test_f1_tags_survive_a_second_clean(lang):
    text = PARA + "\nCall me on 555-867-5309 or write to ravi.kumar" + AT + "gmail.com.\nI live at 42 Elm Street, Springfield, IL 62704."
    a, once = c.clean(en(text, lang))
    assert a == "fix" and all(t in once for t in ("<PHONE>", "<EMAIL>", "<ADDRESS>"))
    assert c.clean(en(once, lang)) == ("keep", once)


@cache
def f1_namespace():
    """The DA-F1-005 block of specv1.md run on its own, to reach its regexes and its medicine_f1."""
    body = re.search(r"^## Medicine \d+ — english / F1 / `DA-F1-005`\n(.*?)(?=^## Medicine |\Z)", SHEET, re.S | re.M).group(1)
    ns = {"__name__": "rules"}
    exec(textwrap.dedent(re.search(r"^```python\n(.*?)^```", body, re.S | re.M).group(1)), ns)
    return ns


def f1_joined_window(text):
    """DA-F1-005 as it was before the window was searched line by line: for every line, ORGANISATION runs on the joined
    13-line window. The reference that medicine_f1 must equal."""
    ns = f1_namespace()
    lines = text.split("\n")
    org_page = bool(ns["ORG_VOICE"].search(text))
    out = []
    for i, line in enumerate(lines):
        org = org_page or bool(ns["ORGANISATION"].search("\n".join(lines[max(0, i - 6):i + 7])))
        new = ns["EMAIL"].sub(lambda m: ns["_email"](m, org or bool(ns["PUBLIC_ROLE"].search(
            "\n".join(lines[max(0, i - 2):i + 1])))), line)
        if ns["PHONE"].search(new) or ns["ADDRESS"].search(new):
            if not org:
                new = ns["PHONE"].sub(lambda m: m.group() if ns["TOLL_FREE"].match(m.group()) else "<PHONE>", new)
                if len(line.strip()) <= ns["CONTACT_LINE"]:
                    new = ns["ADDRESS"].sub("<ADDRESS>", new)
        out.append(new)
    return "\n".join(out)


def test_f1_window_fixtures_hold_what_the_cases_assume():
    ns = f1_namespace()
    plain = FILL + [PHONE_LINE, EMAIL_LINE, REACH_LINE]
    assert not any(ns[name].search(x) for name in ("ORGANISATION", "ORG_VOICE", "PUBLIC_ROLE") for x in plain)
    assert all(ns["ORGANISATION"].search(x) for x in (ORG_LINE, ORG_LINE_2))
    assert ns["ORG_VOICE"].search(ORG_VOICE_LINE) and not ns["ORGANISATION"].search(ORG_VOICE_LINE)
    assert ns["PUBLIC_ROLE"].search(ROLE_LINE) and not ns["ORGANISATION"].search(ROLE_LINE)


def test_f1_searching_the_window_line_by_line_equals_searching_it_joined():
    """The optimisation must change nothing: random documents of contact lines, organisation words, roles and plain lines,
    most of them close enough together for the 13-line windows to overlap."""
    pieces = (FILL + [ORG_LINE, ORG_LINE_2, ORG_VOICE_LINE, ROLE_LINE, PHONE_LINE, EMAIL_LINE, REACH_LINE, "", " ", "123",
              "Open Mon-Fri, fax 020 7946 0958", "Toll free 1-800-555-0199", "Ring +1 (312) 555-0142 or 312 555 0142",
              "Home: 42 Elm Street, Springfield, IL 62704", "12 N. Oak Avenue", "He lived at No. 12 High Street.",
              "sam99" + AT + "uni.edu", "info" + AT + "brightwave.net", "ravi_k" + AT + "gmail.com", "a" + AT + "b", "ten at the real\nestate office"])
    rng = random.Random(5)
    docs = ["\n".join(" ".join(rng.choices(pieces, k=rng.randint(0, 2))) for _ in range(rng.randint(1, 40))) for _ in range(2000)]
    expected = [f1_joined_window(d) for d in docs]
    assert [f1_namespace()["medicine_f1"](d) for d in docs] == expected
    assert 200 < sum(a != d for a, d in zip(expected, docs)) < len(docs) - 200  # both outcomes are exercised, so the check is not vacuous
    for d, e in zip(docs[:200], expected):  # clean.py's own F1, through the shared form
        want = ("drop", d) if not e.strip() else ("fix" if e != d else "keep", e)
        assert c.RULES["F1"](en(d)) == want


# Two pages laid out like real ones in week1-packs: en-dclm 91baef5b95248038 (short contact lines beside organisation lines)
# and en-nemotroncc fab230d1a3b03a77 (one last line holding a webmail address and a phone). Only the layout is copied:
# which lines are blank, where the organisation words and the contacts sit, how long the page is. Every word is made up.
SHAPE_PROSE = ["Rivers carry silt to the delta each spring.", "Her grandfather kept bees on the hill.",
               "The trail follows a ridge above the valley.", "Snow arrived early and stayed until April.",
               "Children learned to swim in the lake.", "A narrow bridge crosses the stream near the mill.",
               "Lanterns were lit along the harbour wall.", "The orchard produces apples, pears and plums.",
               "Winter evenings were spent reading by the fire.", "Few visitors reach the northern cliffs.",
               "Wild herbs grow between the old stones.", "The ferry leaves at dawn and returns at dusk.",
               "Fog settled over the fields before sunrise.", "Songs drifted from the open windows.",
               "Maps of the coast were drawn by hand.", "A quiet road leads past the old windmill.",
               "Gulls circled the boats all afternoon.", "Rain fell softly on the slate roofs.",
               "The baker's cart rolled down the lane.", "Distant bells rang across the water."]
SHAPE_A_BLANK = {0, 1, 3, 5, 7, 9, 12, 14, 16, 18, 20, 22, 24, 28, 30}  # 33 lines
SHAPE_A_CONTACT = {4: "Tel: 555-867-5309", 6: "Our address: 1425 Willow Street", 26: "880 Rose Road"}
SHAPE_A_MASKED = {4: "Tel: <PHONE>", 6: "Our address: <ADDRESS>", 26: "<ADDRESS>"}
SHAPE_A_ORG = {2: "Free consultation for new clients.",
               17: "The clinic keeps long opening hours and offers health checks on most days of the week.",
               21: "A small auto workshop stands beside the river, and the owner knows every engine in town.",
               25: "Family law and wills."}
SHAPE_A_PLAIN = {2: "Welcome to the village page.", 17: "Snow lay thick on the fields all week.",
                 21: "Rain fell on the roofs of the old town.", 25: "Candles burned late in the hall."}


def shape_a(org):
    """The first page: contacts on lines 4, 6 and 26, organisation words only on the lines named in org."""
    prose = iter(SHAPE_PROSE)
    lines = []
    for i in range(33):
        if i in SHAPE_A_CONTACT:
            lines.append(SHAPE_A_CONTACT[i])
        elif i in SHAPE_A_ORG:
            lines.append(SHAPE_A_ORG[i] if i in org else SHAPE_A_PLAIN[i])
        elif i in SHAPE_A_BLANK:
            lines.append("")
        else:
            lines.append(next(prose))
    return lines


@pytest.mark.parametrize("org, masked", [
    ((2, 17, 21, 25), ()),            # as in the real page: every contact has an organisation within 6 lines, nothing changes
    ((17, 21, 25), (4, 6)),           # line 2 is the only organisation word near lines 4 and 6, and 24 lines from line 26
    ((2, 17), (26,)),                 # lines 21 and 25 are the organisation words near line 26; line 17 is 9 lines away
    ((), (4, 6, 26)),                 # no organisation word: the phone and both addresses go
], ids=["organisations-everywhere", "top-organisation-removed", "bottom-organisations-removed", "no-organisation"])
def test_f1_on_a_page_laid_out_like_a_real_one(org, masked):
    lines = shape_a(org)
    assert len(lines) == 33
    text = "\n".join(lines)
    want = "\n".join(SHAPE_A_MASKED[i] if i in masked else line for i, line in enumerate(lines))
    assert c.RULES["F1"](en(text)) == (("fix", want) if masked else ("keep", text))
    assert f1_joined_window(text) == want  # and the joined-window reference agrees


def test_f1_masks_the_webmail_address_and_keeps_the_phone_on_one_organisation_line():
    """The second page: 41 lines, text on the even ones, and a last line with both, beside an organisation word."""
    lines = [SHAPE_PROSE[i // 2] if i % 2 == 0 else "" for i in range(38)] + ["The university runs the survey.", "",
             "Further information: front desk (555) 867\u20105309 or sam.lee" + AT + "gmail.com"]
    assert len(lines) == 41
    text = "\n".join(lines)
    want = "\n".join(lines[:-1] + ["Further information: front desk (555) 867\u20105309 or <EMAIL>"])
    assert c.RULES["F1"](en(text)) == ("fix", want)  # the phone stays: the line belongs to an organisation; a webmail address is a person's


def test_f1_shaped_pages_hold_what_their_cases_assume():
    ns = f1_namespace()
    plain = SHAPE_PROSE + list(SHAPE_A_PLAIN.values()) + list(SHAPE_A_CONTACT.values())
    assert not any(ns[name].search(x) for name in ("ORGANISATION", "ORG_VOICE", "PUBLIC_ROLE") for x in plain)
    assert all(ns["ORGANISATION"].search(x) for x in SHAPE_A_ORG.values())
    assert not any(ns["ORG_VOICE"].search(x) or ns["PUBLIC_ROLE"].search(x) for x in SHAPE_A_ORG.values())


@pytest.mark.parametrize("text", [t for _, t, _, _ in ENGLISH_SICK] + [t for _, t in LOOK_ALIKE] + list(JOINER_PROBES.values()),
                         ids=[f"sick-{x[0]}-{i}" for i, x in enumerate(ENGLISH_SICK)] + [f"look-alike-{x[0]}-{i}" for i, x in enumerate(LOOK_ALIKE)]
                         + [f"joiner-{k}" for k in JOINER_PROBES])
def test_clean_gives_what_the_sheet_gives(text):
    assert c.clean(en(text)) == run_sheet(en(text))


# 5. The math family

def test_a_teaser_cut_is_trimmed_to_the_last_sentence():
    a, new = c.c3(maths(BODY + "The second claim follows from the first. A deeper unders..."))
    assert a == "fix" and new.rstrip().endswith("first.")


@pytest.mark.parametrize("row", [maths("Hereâ€™s a\u200b <br>proof.\nShare\n" + BODY),
                                 maths("the ﬁrst <b>term</b>\n" + BODY, "math-megamath")])
def test_clean_twice_is_clean_once_on_math(row):
    a, once = c.clean(row)
    assert a == "fix"
    assert c.clean(dict(row, text=once)) == ("keep", once)


# Math v1.1: SomaKorada07's functions (A6 and D3 are new; A3, B5 and C2 follow her rules more closely)

def test_a6_maps_a_symbol_font_glyph():
    a, new = c.a6(maths("x \uf0c5 y is the exclusive or.\n" + BODY))
    assert a == "fix" and "⊕" in new and "\uf0c5" not in new


def test_a3_repairs_utf8_read_as_cp866():
    a, new = c.a3(maths("ItтАЩs a proof.\n" + BODY))
    assert a == "fix" and "’" in new


def test_b5_converts_bbcode_in_any_case():
    a, new = c.b5(maths("[TEX]x^2[/TEX]\n" + BODY))
    assert a == "fix" and "[TEX]" not in new


def test_c2_keeps_repeated_answer_options():
    options = "".join(f"{k}. {n} apples and {n - 8} pears in the basket on the table\n" for k, n in zip("ABCD", (12, 14, 16, 18)))
    assert len(options) > 150  # long enough for the passage check
    text = BODY + ("Question one asks for the sum.\n\n" + options + "\n") + ("Question two asks for the sum again.\n\n" + options + "\n")
    assert c.c2(maths(text)) == ("keep", text)


def test_d3_removes_a_foreign_line_and_drops_a_mostly_foreign_page():
    line = "Дивитися фільми онлайн\n"
    a, new = c.d3(maths(BODY + line + BODY))
    assert a == "fix" and line.strip() not in new
    assert c.d3(maths(line * 20 + "Short note.\n"))[0] == "drop"


def test_greek_letters_are_maths_not_foreign():
    text = "Let α + β = π and λ > 0.\n" + BODY
    assert c.d3(maths(text)) == ("keep", text)


# 6. The shared F1 on the math and science packs: the prose path of spec_v1/build/f1_rule.py (TSAI, 1 Nov).
# Made-up values only: 555-01xx numbers, example names and domains.

def sci_prose(text): return dict(doc("sci-finepdfs", text, "eng_Latn"), url="http://a/b.pdf")


@pytest.mark.parametrize("text, expect", [
    ("Call me.\nHome: 312-555-0142\n", "Call me.\nHome: <PHONE>\n"),
    ("Reach Pat on 312-555-0177 (cell) after six.", "Reach Pat on <PHONE> (cell) after six."),
    (f"Written by jordan.sample{AT}mailhost.net; questions to info{AT}mailhost.net or someone{AT}example.org",
     f"Written by <EMAIL>; questions to info{AT}mailhost.net or someone{AT}example.org"),
])
def test_prose_f1_gives_private_values_their_tag(text, expect):
    assert c.f1(sci_prose(text)) == ("fix", expect)


def test_prose_f1_contact_card_phone_and_address():
    a, new = c.f1(sci_prose("Jordan Sample\n12 Maple Lane\nSpringfield, IL 62701\n217-555-0123\n"))
    assert a == "fix" and "<PHONE>" in new and "<ADDRESS>" in new and "555-0123" not in new and "Maple" not in new


def test_prose_f1_people_table():
    a, new = c.f1(sci_prose("| Name | Telephone | Fax |\n|---|---|---|\n| Jordan Sample | 44 20 5550 0123 | 44 20 5550 0124 |\n"))
    assert a == "fix" and new.count("<PHONE>") == 2 and "5550" not in new


def test_prose_f1_mailing_list_at_form_on_math():
    a, new = c.f1(maths("Re: patch\nJordan Sample\njsample at mail.example-uni.net\nThu Oct 1 2009\n", "math-megamath"))
    assert a == "fix" and "jsample at" not in new and "<EMAIL>" in new


def test_prose_f1_drops_a_listing_of_individuals():
    rows = "".join(f"SAMPLE, Jordan Lee, {30 + i}, {i} Maple Lane, Springfield, Clerk. Order made.\n" for i in range(8))
    assert c.f1(sci_prose(rows))[0] == "drop"


@pytest.mark.parametrize("text", [
    "County Clerk's Office\n100 Main Street\nPhone: 312-555-0100\n",                        # public office
    "Call 1-800-555-0199 for help.",                                                         # toll free
    "**Food Pantry Network**\n- Address: 22 Oak Street, Springfield, IL 62701\n- Phone: 217-555-0188\n"
    "- Website: https://pantry.example.org/\n",                                              # a directory of organisations
    f"Contact us\n\nsales.team.lead{AT}company-mail.net",                                    # an organisation's mailbox
    "The data set is available at data.example-archive.net under CC0.",                     # "at" in prose is not an email
    "We set $x = 312-555$ and n = 1.000.0000 in Table 3, page 555-0123 of the appendix.",  # numbers that look alike
])
def test_prose_f1_keeps_organisations_and_look_alikes(text):
    assert c.f1(sci_prose(text)) == ("keep", text)


@pytest.mark.parametrize("row", [
    {"doc_id": "x", "text": "Home: 312-555-0142", "lang_label": "en"},                                   # no pack_id
    {"doc_id": "x", "text": "Home: 312-555-0142", "lang_label": "en", "pack_id": "en-dclm"},            # English: has its own F1, DA-F1-005
    {"doc_id": "x", "text": "Home: 312-555-0142", "lang_label": "en", "pack_id": "sci-finepdfs"},       # wrong tag for that pack
])
def test_prose_path_runs_only_on_math_and_sci_packs(row):
    assert c._shared_f1(row) == ("keep", row["text"])  # the shared rule alone; SCOPE also keeps it off English


def test_clean_twice_is_clean_once_on_prose():
    row = sci_prose(f"Jordan Sample\n12 Maple Lane\nSpringfield, IL 62701\nHome: 217-555-0123\njordan.s{AT}mailhost.net\n")
    a, once = c.clean(row)
    assert a == "fix"
    assert c.clean(dict(row, text=once)) == ("keep", once)
