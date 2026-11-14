"""Equivalence tests for the speed-ups of the math rules in clean.py (results/spec_v1/speed_v1_math.md). Each rule that was
made faster is checked against a frozen copy of the rule as it was before the change (math_speed_reference.py): the same
text goes through both and the results must be equal, on hand-written cases at the edges of the fast path and on random
documents. Every text here is made up; none comes from a pack.

  python -m pytest tests/spec_v1/test_speed_equivalence_math.py

  DA-C1-001  site boilerplate (math-finemath): the 120-character test runs before the slow C1_SITE search, and on a pure-ASCII
             line the search uses the lower-cased pattern on the lower-cased line instead of the (?i) pattern
  DA-D3-005  foreign-script lines (math-finemath, math-megamath): letters are counted only for lines that hold a foreign
             character, and the whole text is returned as it is when it holds none

The speed-up tests of the English rules are in test_speed_equivalence.py and those of the code rules in
test_speed_equivalence_code.py. If a rule's behaviour is ever changed on purpose, update or delete its frozen copy.
"""
import random
import re
import sys
from pathlib import Path

import pytest

SPEC = Path(__file__).resolve().parents[2] / "spec_v1"
sys.path.insert(0, str(SPEC))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import clean as c
from math_speed_reference import c1_reference, d3_reference

REF = c1_reference()
OLD_C1 = REF["medicine_c1"]
NEW_C1 = c._RULE["DA-C1-001"]()
D3_REF = d3_reference()
OLD_D3 = D3_REF["medicine_d3"]
NEW_D3 = c._RULE["DA-D3-005"]()


def doc(text, pack="math-finemath", lang="en"):
    return {"doc_id": "x", "text": text, "url": "http://a/b", "lang_label": lang, "pack_id": pack}


def expected(text):
    """What the old rule gives for a math-finemath document, in the shared (action, text) form."""
    out = OLD_C1(text)
    return ("fix" if out != text else "keep", out)


def same(text):
    assert NEW_C1(doc(text)) == expected(text), repr(text)


# ---- one made-up line for each alternative of C1_SITE (and of C1_LINE), built from the regex source itself ----------

def alternatives(pattern):
    """The top-level alternatives of a regex source (split on | outside brackets, groups and escapes)."""
    out, depth, cur, i = [], 0, "", 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\":
            cur += pattern[i:i + 2]; i += 2; continue
        if ch in "([": depth += 1
        elif ch in ")]": depth -= 1
        if ch == "|" and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
        i += 1
    return out + [cur]


SUBS = [(r"\d{4}", "2024"), (r"\d{2}", "30"), (r"\d{1,2}", "10"), (r"\d+", "12"), (r"\w+", "Mon"), (r"\s+", " "),
        (r"[sz]", "s"), ("^", ""), ("$", ""), (r"\[", "["), (r"\]", "]"), (r"\?", "?"), (r"\|", "|"), (r"\.", ".")]


def sample(alt):
    s = alt
    for a, b in SUBS:
        s = s.replace(a, b)
    return re.sub(r"\\u([0-9a-f]{4})", lambda m: chr(int(m.group(1), 16)), s)


SITE_ALTS = alternatives(REF["C1_SITE"].pattern[4:])
SITE_SAMPLES = [sample(a) for a in SITE_ALTS]
LINE_ALTS = alternatives(REF["C1_LINE"].pattern[4:].strip())
LINE_SAMPLES = [sample(re.sub(r"\.\*|\\s\*", "", a)) for a in LINE_ALTS]


def test_every_site_alternative_has_a_sample_the_old_regex_matches():
    # guards the sample builder: a sample that does not match would make the cases below test nothing
    assert len(SITE_ALTS) > 80
    bad = [s for s in SITE_SAMPLES if not REF["C1_SITE"].search(s)]
    assert bad == []


def test_the_pattern_can_be_lowered_safely():
    # the fast path lower-cases C1_SITE: that only works if every escape is lower-case and no character is non-ASCII
    p = REF["C1_SITE"].pattern
    assert p.startswith("(?i)") and p.isascii()
    assert not any(e[1].isupper() for e in re.findall(r"\\.", p))      # no \D \W \S \U: lower() would change them


def variants(s):
    return [s, s.upper(), s.lower(), s.swapcase(), "x " + s, s + " x", "  " + s + "  ", s + "\r", "\t" + s]


@pytest.mark.parametrize("sample_line", SITE_SAMPLES)
def test_site_phrase_in_every_case_and_position_matches_old_rule(sample_line):
    for line in variants(sample_line):
        same("Solve for x.\n" + line + "\nThe answer is 4.")


@pytest.mark.parametrize("sample_line", [s for s in LINE_SAMPLES if s.strip()])
def test_whole_line_chrome_matches_old_rule(sample_line):
    for line in variants(sample_line) + [sample_line + " more words here"]:
        same("Find x.\n" + line + "\nx = 2")


# ---- the 120-character limit -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("phrase", ["View Full Document", "[#permalink]", "Kudos [?]", "^Home >>"[1:], "Share", "Hide",
                                    "My Personal Notes arrow_drop_up", "The time now is 10:30"])
def test_length_limit_sweep(phrase):
    for n in range(max(1, len(phrase)), 125):
        for left in (0, n - len(phrase)):
            line = "a" * left + phrase + "a" * (n - len(phrase) - left)
            assert len(line) == n
            same("Intro.\n" + line + "\nOutro.")


def test_site_phrase_on_a_line_of_120_is_dropped_and_121_is_kept():
    phrase = "View Full Document"
    for n, dropped in ((120, True), (121, False)):
        line = phrase + " " + "a" * (n - len(phrase) - 1)
        assert len(line) == n
        got = NEW_C1(doc("Intro.\n" + line + "\nOutro."))
        assert got == expected("Intro.\n" + line + "\nOutro.")
        assert (got[0] == "fix") == dropped


def test_anchored_phrase_only_matches_the_whole_line_or_its_end():
    for text in ("Open in App", "open in app", "Please Open in App", "Open in App now", "x Hide", "Hide x", "HIDE"):
        same("a\n" + text + "\nb")


# ---- non-ASCII lines keep the original (?i) regex ---------------------------------------------------------------------

KELVIN, LONG_S, DOTTED_I, DOTLESS_I = "K", "ſ", "İ", "ı"
UNICODE_LINES = [
    KELVIN + "udos [?]", "Kudos [?] " + KELVIN, "Check GMAT Club Decision Tracker " + LONG_S, LONG_S + "hare",
    "Sign" + LONG_S + "up", "Privacy Statement é", "GMAT® test is a registered trademark",
    "GMAT® TEST IS A REGISTERED TRADEMARK", "Read More »", "READ MORE »", "We‘ve got your back",
    "WE‘VE GOT YOUR BACK", "claim an answer you’ll have 24 hours", DOTTED_I + "ntentionally blurred sections",
    "intentionally blurred sections " + DOTLESS_I, "Free Algebra Tutorials!", "Free Algebra Tutorials!",
    "Home \u200E > \u200E Algebra", "© 2024 Example", "It is currently 12 Mon 2024 é",
    "١٢ It is currently ١٢ Mon ٢٠٢٤", "The time now is ١٠:٣٠",
    "Solve α + β = 10 View Full Document", "é", "中文 Share",
]


@pytest.mark.parametrize("line", UNICODE_LINES)
def test_non_ascii_lines_match_old_rule(line):
    for text in (line, line.upper(), line.lower(), "x " + line, line + " x"):
        same("a\n" + text + "\nb")


def test_the_unicode_cases_include_lines_that_only_the_unicode_regex_matches():
    # these are lines where lower-casing the line would give a different answer than (?i); the fast path must not touch them
    site = REF["C1_SITE"]
    assert site.search(KELVIN + "udos [?]") and not site.search(("Kudos [?]").replace("K", "x"))
    assert expected("a\n" + KELVIN + "udos [?]\nb")[0] == "fix"


def test_other_packs_languages_and_scope_are_unchanged():
    text = "Find x.\nView Full Document\nShare\nx = 2"
    assert NEW_C1(doc(text, pack="math-megamath")) == ("keep", text)       # the rule runs on finemath only
    for pack in ("en-dclm", "code-python", "sci-finepdfs"):
        assert NEW_C1(doc(text, pack=pack)) == ("keep", text)
    assert NEW_C1(doc("")) == ("keep", "")


def test_edge_documents():
    for text in ("", "\n", "\n\n\n", "   ", "Share", "Share\n", "\nShare", "Views", "Replies\n12\nViews\n3.4K\nrest",
                 "Replies\n12\nViews\n3.4K", "x\nReplies\n12\nViews\n3\n", "Replies\n12\nViews\n", "a\r\nShare\r\nb",
                 "a\rView Full Document\rb", "one line that is fine", "$x^2 + y^2 = z^2$\n\n$\\frac{a}{b}$"):
        same(text)


# ---- random documents -------------------------------------------------------------------------------------------------

MATH = ["Solve for x: 2x + 3 = 11.", "x = 4", "$\\int_0^1 x^2 dx = \\frac{1}{3}$", "", "", "The perimeter is 24 cm.",
        "Step 1: subtract 3 from both sides.", "  indented line  ", "A" * 119, "b" * 120, "c" * 121, "α + β = γ",
        "Therefore the sum of the angles is 180 degrees, as the figure above shows.", "Tags", "Home", "views and replies"]


def random_line(rng):
    k = rng.random()
    if k < 0.45:
        return rng.choice(MATH)
    if k < 0.75:
        phrase = rng.choice(SITE_SAMPLES)
    elif k < 0.85:
        phrase = rng.choice([s for s in LINE_SAMPLES if s.strip()])
    else:
        phrase = rng.choice(UNICODE_LINES)
    phrase = rng.choice([phrase, phrase.upper(), phrase.lower(), phrase.swapcase()])
    pad = rng.choice(["", "", " ", "x" * rng.randint(1, 130), "word " * rng.randint(1, 30)])
    return rng.choice([phrase, pad + phrase, phrase + pad, pad + " " + phrase + " " + pad])


def random_doc(rng):
    lines = [random_line(rng) for _ in range(rng.randint(0, 25))]
    if rng.random() < 0.1:
        lines.insert(rng.randint(0, len(lines)), f"Replies\n{rng.randint(0, 99)}\nViews\n{rng.choice(['5', '3.4K', '10', ''])}")
    return rng.choice(["\n", "\n", "\n", "\r\n", "\n\n"]).join(lines)


def test_random_documents_match_old_rule_and_cover_both_outcomes():
    rng = random.Random(1)
    fixes = keeps = 0
    long_kept = 0
    for _ in range(4000):
        text = random_doc(rng)
        want = expected(text)
        assert NEW_C1(doc(text)) == want, repr(text)
        fixes += want[0] == "fix"
        keeps += want[0] == "keep"
        long_kept += any(len(l) > 120 and REF["C1_SITE"].search(l) for l in text.split("\n"))
    assert fixes > 1500 and keeps > 100       # the draw hits both: a test that never fires proves nothing
    assert long_kept > 300                    # lines over 120 characters that hold a site phrase and must stay


def test_random_ascii_lines_match_the_old_regex_directly():
    # the fast path replaces C1_SITE.search on ASCII lines: compare the old regex with the lowered one on random strings
    rng = random.Random(2)
    lowered = re.compile(REF["C1_SITE"].pattern[4:].lower())
    pieces = [s for s in SITE_SAMPLES if s.isascii()] + list("abcxyz 0123456789.-:[]?|>$^\t")
    hits = 0
    for _ in range(20000):
        s = "".join(rng.choice(pieces) if rng.random() < 0.5 else rng.choice("abKkSs 1[]?>") for _ in range(rng.randint(0, 6)))
        s = "".join(ch.swapcase() if rng.random() < 0.3 else ch for ch in s)
        assert s.isascii()
        old, new = REF["C1_SITE"].search(s), lowered.search(s.lower())
        assert bool(old) == bool(new), repr(s)
        hits += bool(old)
    assert hits > 2000


# =====================================================================================================================
# DA-D3-005: lines in a foreign script
# =====================================================================================================================

def expected_d3(text):
    """What the old rule gives, in the shared (action, text) form."""
    out = OLD_D3(text)
    if isinstance(out, tuple):
        return ("drop", text)
    return ("fix" if out != text else "keep", out)


def same_d3(text, pack="math-finemath"):
    got = NEW_D3(doc(text, pack=pack))
    assert got == expected_d3(text), repr(text)
    return got[0]


EN = "The perimeter of the square is four times its side."
SCRIPTS = {"cyrillic": "Привет мир это тест", "devanagari": "नमस्ते दुनिया यह एक परीक्षा है", "kana": "こんにちは世界のテスト",
           "cjk": "你好世界这是一个测试", "hangul": "안녕하세요 세계 테스트", "arabic": "مرحبا بالعالم هذا اختبار"}
# first and last character of each range of D3_FOREIGN, and the characters just outside it
EDGES = ["\u0400", "\u04ff", "\u0900", "\u0dff", "\u3040", "\u30ff", "\u4e00", "\u9fff", "\uac00", "\ud7af", "\u0600", "\u06ff"]
OUTSIDE = ["\u03ff", "\u0500", "\u08ff", "\u0e00", "\u303f", "\u3100", "\u4dff", "\ua000", "\uabff", "\ud7b0", "\u05ff", "\u0700",
           "\u03b1", "\u03a9", "\u00e9", "\u2211", "\u221e"]
# characters inside the ranges that are not letters: the line's letter count then differs from its foreign count
NOT_LETTERS = ["\u0964", "\u0966", "\u093e", "\u094d", "\u0660", "\u060c", "\u0483", "\u0488", "\u0e50", "\u30fb", "\u3099"]


def test_the_foreign_ranges_used_below_are_what_the_regex_matches():
    regex = D3_REF["D3_FOREIGN"]
    assert all(regex.search(ch) for ch in EDGES)
    assert not any(regex.search(ch) for ch in OUTSIDE)
    assert any(regex.search(ch) and not ch.isalpha() for ch in NOT_LETTERS)      # the cases below do cover non-letters


@pytest.mark.parametrize("name", sorted(SCRIPTS))
def test_each_script_alone_in_a_line_or_inline(name):
    line = SCRIPTS[name]
    assert same_d3(EN + "\n" + line + "\n" + EN + " " + EN) == "fix"              # a whole foreign line is deleted
    assert same_d3(EN + " " + line + " " + EN) == "keep"                            # a few foreign letters in an English line stay
    assert same_d3(line) == "drop"                                                 # all foreign: drop
    assert same_d3("\n".join([line] * 3)) == "drop"
    for pack in ("math-finemath", "math-megamath"):
        same_d3(EN + "\n" + line + "\n" + EN, pack)


@pytest.mark.parametrize("ch", EDGES + OUTSIDE + NOT_LETTERS)
def test_range_edges_and_non_letter_characters(ch):
    for text in (ch, ch * 5, EN + "\n" + ch * 7 + "\n" + EN, EN + ch, ch + "a", "a" + ch * 3 + "b\n" + EN, ch + "1" + ch + "\n",
                 "\n".join([ch + "ab", ch * 4, "ab" + ch + "cd"]), "a" * 40 + "\n" + ch * 60, "1 2 3 " + ch):
        same_d3(text)


def test_greek_is_left_alone():
    assert same_d3("Let \u03b1 + \u03b2 = \u03b3.\n\u03b1\u03b2\u03b3\u03b4\u03b5\u03b6 \u03b7\u03b8\u03b9\u03ba") == "keep"


def line_with(foreign, letters, foreign_char="ж"):
    return "a" * (letters - foreign) + foreign_char * foreign


@pytest.mark.parametrize("foreign_char", ["ж", "你", "ह", "ع"])
def test_line_threshold_sweep(foreign_char):
    # a line goes when MORE than half of its letters are foreign: 5 of 10 stays, 6 of 10 goes
    for n in (1, 2, 3, 10, 11, 40):
        for k in range(0, n + 1):
            same_d3(EN + " " + EN + "\n" + line_with(k, n, foreign_char) + "\n" + EN)
    assert same_d3(EN * 3 + "\n" + line_with(5, 10) + "\n" + EN * 3) == "keep"
    assert same_d3(EN * 3 + "\n" + line_with(6, 10) + "\n" + EN * 3) == "fix"


def test_document_threshold_sweep():
    # the document goes when the removed lines hold MORE than 30% of all its letters: 30 of 100 is a fix, 31 of 101 a drop
    for total in (10, 100, 101, 1000):
        for foreign in range(1, total):
            text = "x" * (total - foreign) + "\n" + "ж" * foreign
            same_d3(text)
    assert same_d3("a" * 70 + "\n" + "ж" * 30) == "fix"
    assert same_d3("a" * 70 + "\n" + "ж" * 31) == "drop"
    assert same_d3("a" * 70 + "\n" + "ж" * 29) == "fix"


def test_foreign_characters_that_are_kept_never_drop_the_document():
    # foreign letters in lines that are not removed do not count towards the drop test
    for k in (1, 3, 9):
        text = "\n".join([("a" * 20 + "ж" * k)] * 5)
        assert same_d3(text) == "keep"
    assert same_d3("\u0964\n\u0964\u0964\n" + EN) == "keep"        # lines of marks only: no letters, so kept


def test_edge_documents_d3():
    for text in ("", "\n", "\n\n\n", " ", "123 456", "\u0964", "ж", "ж\n", "\nж", "a\r\nж\r\nb", "ж\r\nж", "a\nж ж ж\nb\n",
                 "a\n\nж ж ж\n\nb", EN + "\n", "\n" + EN, "ж" * 1000, ("a" * 50 + "\n") * 50 + "ж" * 5000):
        same_d3(text)


def test_other_packs_and_languages_are_unchanged_d3():
    text = EN + "\n" + SCRIPTS["cyrillic"] + "\n" + EN
    for pack in ("en-dclm", "code-python", "sci-finepdfs", "ind-hi-fw2"):
        assert NEW_D3(doc(text, pack=pack)) == ("keep", text)
    assert NEW_D3(doc(text, lang="hi")) == ("keep", text)
    assert NEW_D3(doc(text, pack="math-megamath"))[0] == "fix"


def foreign_run(rng, n):
    return "".join(rng.choice(rng.choice(list(SCRIPTS.values())).replace(" ", "") + "".join(NOT_LETTERS + EDGES)) for _ in range(n))


def random_d3_line(rng):
    k = rng.random()
    if k < 0.40:
        return rng.choice([EN, "x = 4", "$\\int_0^1 x^2 dx$", "", "", "Step 1: add 3.", "Let \u03b1 + \u03b2 = \u03b3", " ", "12 + 7 = 19", "\u00e9\u00e8 ok"])
    if k < 0.60:
        return foreign_run(rng, rng.randint(1, 60))                                                  # a foreign line
    if k < 0.85:
        n = rng.randint(1, 40)
        f = rng.randint(0, n)
        letters = list("a" * (n - f)) + list(foreign_run(rng, f))
        rng.shuffle(letters)
        return "".join(letters)                                                                      # mixed line
    return EN + " " + foreign_run(rng, rng.randint(1, 4)) + " " + EN                                 # a few inline


def random_d3_doc(rng):
    mode = rng.random()
    if mode < 0.3:
        lines = [rng.choice([EN, "x = 4", "", "Step 1."]) for _ in range(rng.randint(0, 20))]       # no foreign character at all
    else:
        lines = [random_d3_line(rng) for _ in range(rng.randint(1, 20))]
    return rng.choice(["\n", "\n", "\r\n", "\n\n"]).join(lines)


def test_random_documents_match_old_rule_and_cover_all_outcomes():
    rng = random.Random(3)
    seen = {"keep": 0, "fix": 0, "drop": 0}
    foreign_kept = 0
    for i in range(4000):
        text = random_d3_doc(rng)
        action = same_d3(text, "math-finemath" if i % 2 else "math-megamath")
        seen[action] += 1
        foreign_kept += action == "keep" and bool(D3_REF["D3_FOREIGN"].search(text))
    assert seen["keep"] > 800 and seen["fix"] > 400 and seen["drop"] > 100, seen    # the draw hits all three outcomes
    assert foreign_kept > 50       # documents with a foreign character that nothing removes: they take the slow path and are kept
