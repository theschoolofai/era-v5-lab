"""Equivalence tests for the speed-up of the math rule DA-C1-001 in clean.py (results/spec_v1/speed_v1_math.md): site boilerplate
on math-finemath. The 120-character test runs before the slow C1_SITE search, and on a pure-ASCII line the search uses the
lower-cased pattern on the lower-cased line instead of the (?i) pattern. The rule is checked against a frozen copy of the rule
as it was before (c1_reference, below): the same text goes through both and the results must be equal, on hand-written
cases at the edges of the fast path and on random documents. Every text here is made up; none comes from a pack.

  python -m pytest tests/spec_v1/test_speed_equivalence_math.py

The speed-up tests of the English rules are in test_speed_equivalence.py, those of the code rules in
test_speed_equivalence_code.py and those of the F1 rule in test_speed_equivalence_f1*.py. If the rule's behaviour is ever
changed on purpose, update or delete its frozen copy.
"""
import random
import re
import sys
from pathlib import Path

import pytest

SPEC = Path(__file__).resolve().parents[2] / "spec_v1"
sys.path.insert(0, str(SPEC))
import clean as c


def c1_reference():
    """DA-C1-001 as it was before its speed-up (clean.py 9a4e3a87f124, specv1_1.md medicine 58): the old medicine_c1 and its three
    regexes. Returns the namespace so tests can reach C1_LINE and C1_SITE."""
    # a whole line that is generic site chrome
    C1_LINE = re.compile(
        r"(?i)\s*(?:More Similar Questions|Similar Questions|Related (?:Questions|Posts|Articles)|Share (?:this|on \w+)|"
        r"Sign ?up|Log ?in|Subscribe|Cookie|Accept (?:all )?cookies|Privacy Policy|Terms of (?:Use|Service)|"
        r"All rights reserved|\u00a9.*|&copy;.*|Follow us|Skip to (?:main )?content|Show Tags|Replies|Views|"
        r"Contact - Home.*|Report (?:abuse|post)|Upvote|Downvote|Like this:|Loading\.\.\.|Previous Post|Next Post|"
        r"Recommended|Back to top|Quick Reply|Click here.*|Leave a (?:Reply|Comment)|Your email address will not be published.*|"
        r"Posted by.*|Tags?:.*|Categories?:.*|Hide Tags|Join (?:now|us)|Download (?:the )?App.*|Course Hero.*)\s*")
    # site chrome seen in this pack (forums, homework sites, document hosts, OEIS, GMAT Club ...); only on lines <= 120 chars
    C1_SITE = re.compile(
        r"(?i)Check GMAT Club Decision Tracker|It is currently \d+ \w+ \d{4}|GMAT Club Daily Prep|Display posts from previous|"
        r"GMAT\u00ae test is a registered trademark|\[#permalink\]|Kudos \[\?\]|This preview shows page|Sign up to view the full|"
        r"View Full Document|Ask a homework question|intentionally blurred sections|My Personal Notes arrow_drop_up|"
        r"^Open in App$|^Last Updated :|All times are GMT|The time now is \d{1,2}:\d{2}|Privacy Statement|"
        r"Remember Me\? Password|having trouble loading external resources|analy[sz]e our traffic|Want to see this answer and more|"
        r"^See Solution$|^Subscribe now$|Upcoming SlideShare|Are you sure you want to|Report Content as Inappropriate|"
        r"Open this post in threaded view|^Loading content$|The OEIS Community \| Maintained by|supported by donations|"
        r"You are Here: Home|Registered Office:|CYBER MONDAY|^Wiki User$|^Buscar$|^Uncategorized$|Created with Sketch|"
        r"best freelance writing portal|Comment sent successfully|Choose the classification system|Read More \u00bb|"
        r"TUTORIALS HOME|Top of Page|Our sister site|Everything was clear\?|Hello Guest!|Free\s+Algebra Tutorials!|"
        r"Teach yourself statistics|^Home >>|\u200e > \u200e|claim an answer you\u2019ll have 24 hours|Search Our Content Library|"
        r"filtered results|^Sort by$|tutors are online|snackBarMessage|Go To Main Page|^Show/hide solution$|"
        r"Correct! Wrong!|Tutorial is loading|^Filed Under:|^Exam Prep:|^Asked in:|Verified Answer \| Published|"
        r"^Guided Lessons$|^Course Content$|Doorsteptutor|Mark Forums Read|^Recommended$|DocShare\.tips|^Hide$|"
        r"Not now$|Write an Interview Experience|Your message has been successfully submitted|has the best spam protection|"
        r"posting guide http|Questions are from the workbook|^Share$|^Children$|Go back to editing|try BYJU|We\u2018ve got your back")
    # phpBB "Replies / <n> / Views / <n>" block, one value per line
    C1_REPLIES = re.compile(r"(?m)^Replies\n\d+\nViews\n[\d.]+K?\n?")

    def medicine_c1(text):
        keep = [l for l in text.split("\n")
                if not (C1_LINE.fullmatch(l) or (C1_SITE.search(l) and len(l) <= 120))]
        return C1_REPLIES.sub("", "\n".join(keep))

    return {"medicine_c1": medicine_c1, "C1_LINE": C1_LINE, "C1_SITE": C1_SITE, "C1_REPLIES": C1_REPLIES}


REF = c1_reference()
OLD_C1 = REF["medicine_c1"]
NEW_C1 = c._RULE["DA-C1-001"]()


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
