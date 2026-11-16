"""Equivalence tests for the speed-ups of four code rules in clean.py (results/spec_v1/speed_v1_code_rules.md). Each rule is checked
against a frozen copy of the rule as it was before the change (a4_reference, a6_reference, e2_reference and e3_reference, below): the
same text goes through both and the results must be equal, on hand-written cases at the edge of each guard and on random documents.
Every text here is made up; none comes from a pack.

  python -m pytest tests/spec_v1/test_speed_equivalence_code_rules.py

  DA-A4-002  replacement-character comment lines (six code packs): a text with no U+FFFD is kept without running LOST
  DA-A6-001  Cyrillic look-alike letters (six code packs): a text with no Cyrillic character (U+0400 to U+04FF) is kept without
             running MIXED
  DA-E2-001  byte-array and base64 drop (six code packs): the byte-array regex runs only when the text holds 24 or more "0x"
  DA-E3-003  known keys and base32 seeds (six code packs): each KEYS pattern runs only when a literal it needs is in the text, and
             SEED runs only when the text has "=", a quote and one of its words (tested on the casefolded text)

The rules in the sheet are read from specv1_1.md (the namespace of each card is run on its own). The speed-up tests of the code
rules DA-E3-004 and the shared F1 are in test_speed_equivalence_code.py. If a rule's behaviour is ever changed on purpose, update
or delete its frozen copy.
"""
import random
import re
import sys
import textwrap
from pathlib import Path

import pytest

SPEC = Path(__file__).resolve().parents[2] / "spec_v1"
SHEET = Path(__file__).resolve().parents[2] / "spec_v1_1" / "sheets" / "specv1_1.md"
sys.path.insert(0, str(SPEC))
import clean as c

CODE_PACKS = ("code-cpp", "code-go", "code-java", "code-js-ts", "code-python", "code-rust")


def doc(text, pack="code-go", lang="go"):
    return {"doc_id": "x", "text": text, "url": "", "lang_label": lang, "pack_id": pack}


def namespace(rule_id, family="code"):
    """The card of one rule in specv1_1.md run on its own: a fresh copy each time, so a test can wrap its regexes."""
    text = SHEET.read_text(encoding="utf-8")
    body = re.search(r"^## Medicine \d+ — " + family + r" / \w+ / `" + rule_id + r"`\n(.*?)(?=^## Medicine |\Z)", text, re.S | re.M).group(1)
    ns = {"__name__": "rules"}
    exec(textwrap.dedent(re.search(r"^```python\n(.*?)^```", body, re.S | re.M).group(1)), ns)
    return ns


class Spy:
    """A regex that counts the calls of one method and gives the real answer."""
    def __init__(self, real, method):
        self.real, self.method, self.calls = real, method, 0

    def __getattr__(self, name):
        if name == self.method:
            def call(*a, **k):
                self.calls += 1
                return getattr(self.real, name)(*a, **k)
            return call
        return getattr(self.real, name)


# =====================================================================================================================
# DA-A4-002: comment lines that hold a replacement character
# =====================================================================================================================

def a4_reference():
    """DA-A4-002 as it was before its speed-up (clean.py 716c9a90093f, specv1_1.md medicine 4): LOST is run on every text."""
    LOST = re.compile(r"[ \t]*//[^\n\w]*" + chr(0xFFFD) + r"[^\nA-Za-z0-9]*$", re.M)

    def medicine_a4(doc):
        t = LOST.sub("", doc["text"])
        return ("fix" if t != doc["text"] else "keep", t)

    return {"medicine_a4": medicine_a4, "LOST": LOST}


A4_OLD, A4_NEW = a4_reference(), namespace("DA-A4-002")


def test_a4_the_pattern_is_the_old_one():
    assert A4_NEW["LOST"].pattern == A4_OLD["LOST"].pattern and A4_NEW["LOST"].flags == A4_OLD["LOST"].flags


def test_a4_every_match_holds_a_replacement_character():
    for t in ("// �", "x\n  //��?\n", "\t// ?�.,;"):
        m = A4_OLD["LOST"].search(t)
        assert m and "�" in m.group()


FFFD = "�"
A4_TEXTS = {
    "empty": "",
    "no replacement character": "// a comment\nint x = 1; // 2\n",
    "only the character": FFFD,
    "the character in a string": 'a = "' + FFFD + '"\n',
    "the character in a comment with words": "// " + FFFD + " is a bad byte\n",
    "comment with the character only": "x\n// " + FFFD + FFFD + "\ny\n",
    "comment with the character and a digit": "// " + FFFD + "1\n",
    "comment with a letter before": "// ab" + FFFD + "\n",
    "comment with an underscore before": "//_" + FFFD + "\n",
    "comment with punctuation before": "// !?" + FFFD + "\n",
    "comment with indentation": "\t \t// " + FFFD + "\nnext\n",
    "comment at the end, no newline": "code\n// " + FFFD,
    "comment with trailing punctuation": "// " + FFFD + " ...;\n",
    "comment with trailing letter": "// " + FFFD + " z\n",
    "comment with the character twice": "// " + FFFD + " , " + FFFD + "\n",
    "two lines": "// " + FFFD + "\n// " + FFFD + FFFD + "\n",
    "slash-star comment": "/* " + FFFD + " */\n",
    "carriage return": "// " + FFFD + "\r\nx\r\n",
    "non-ascii letters around": "// éé" + FFFD + "é\n",
    "the character a long way down": "x = 1\n" * 3000 + "// " + FFFD + "\n",
}


@pytest.mark.parametrize("name", list(A4_TEXTS))
def test_a4_hand_cases_match_old_rule(name):
    text = A4_TEXTS[name]
    assert A4_NEW["medicine_a4"](doc(text)) == A4_OLD["medicine_a4"](doc(text))


def test_a4_the_hand_cases_reach_every_branch():
    results = [A4_NEW["medicine_a4"](doc(t)) for t in A4_TEXTS.values()]
    assert any(a == "fix" for a, _ in results)
    assert any(a == "keep" and FFFD in t for (a, t) in results)         # the character is there and nothing is changed
    assert any(a == "keep" and FFFD not in t for (a, t) in results)


def test_a4_a_text_without_the_character_does_not_run_lost_and_one_with_it_does():
    ns = namespace("DA-A4-002")
    ns["LOST"] = spy = Spy(ns["LOST"], "sub")
    ns["medicine_a4"](doc("// plain comment\nx = 1\n" * 100))
    assert spy.calls == 0
    ns["medicine_a4"](doc("// " + FFFD + "\n"))
    assert spy.calls == 1


A4_PIECES = ["// " + FFFD, "//" + FFFD + FFFD, "  // " + FFFD + " ...", "\t// ab" + FFFD, "// " + FFFD + "1", "// plain comment",
             "int x = 1;", 'p("' + FFFD + '")', "x = " + FFFD, "// é" + FFFD, "//", "// …" + FFFD + "?", "", "// _" + FFFD,
             "/* " + FFFD + " */", "code(); // " + FFFD, "y; //" + FFFD + "z", "// " + FFFD + FFFD + FFFD + ";;"]


def random_a4_text(rng):
    lines = [rng.choice(A4_PIECES) for _ in range(rng.randint(0, 30))]
    return rng.choice(["\n", "\n", "\r\n"]).join(lines) + rng.choice(["", "\n"])


def test_a4_random_texts_match_old_rule_and_cover_every_branch():
    rng = random.Random(41)
    seen = {"fix": 0, "has_char_kept": 0, "no_char": 0}
    for _ in range(10000):
        t = random_a4_text(rng)
        old, new = A4_OLD["medicine_a4"](doc(t)), A4_NEW["medicine_a4"](doc(t))
        assert new == old, repr(t)
        seen["fix"] += new[0] == "fix"
        seen["has_char_kept"] += new[0] == "keep" and FFFD in t
        seen["no_char"] += FFFD not in t
    assert all(v > 300 for v in seen.values()), seen


def test_a4_the_rule_in_clean_py_acts_only_on_the_code_packs_and_equals_the_old_rule():
    rule = c._RULE["DA-A4-002"]()
    for text in (A4_TEXTS["comment with the character only"], A4_TEXTS["empty"], A4_TEXTS["two lines"]):
        for pack in CODE_PACKS:
            assert rule(doc(text, pack)) == A4_OLD["medicine_a4"](doc(text))
        for pack in ("en-dclm", "math-finemath", "sci-finepdfs", None):
            assert rule(doc(text, pack, lang="en")) == ("keep", text)


# =====================================================================================================================
# DA-A6-001: Cyrillic look-alike letters
# =====================================================================================================================

def a6_reference():
    """DA-A6-001 as it was before its speed-up (clean.py 716c9a90093f, specv1_1.md medicine 3): MIXED is run on every text."""
    HOMO = str.maketrans("аеорсухіјѕАВЕКМНОРСТХІЈЅ",
                         "aeopcyxijsABEKMHOPCTXIJS")
    MIXED = re.compile(r"\b(?=\w*[A-Za-z])(?=\w*[Ѐ-ӿ])\w+\b")

    def medicine_a6(doc):
        t = MIXED.sub(lambda m: m.group().translate(HOMO), doc["text"])
        return ("fix" if t != doc["text"] else "keep", t)

    return {"medicine_a6": medicine_a6, "MIXED": MIXED, "HOMO": HOMO}


A6_OLD, A6_NEW = a6_reference(), namespace("DA-A6-001")


def test_a6_the_patterns_are_the_old_ones():
    assert A6_NEW["MIXED"].pattern == A6_OLD["MIXED"].pattern and A6_NEW["MIXED"].flags == A6_OLD["MIXED"].flags
    assert A6_NEW["HOMO"] == A6_OLD["HOMO"]


def test_a6_the_guard_range_is_the_range_of_mixed_and_every_match_holds_one():
    assert A6_NEW["CYRILLIC"].pattern == "[Ѐ-ӿ]"
    assert "[Ѐ-ӿ]" in A6_OLD["MIXED"].pattern
    for t in ("pаss", "Ѐa", "aӿ", "x_і_y", "abас"):
        m = A6_OLD["MIXED"].search(t)
        assert m and A6_NEW["CYRILLIC"].search(m.group())


CY = "а"                         # Cyrillic a, a look-alike of the Latin a
A6_TEXTS = {
    "empty": "",
    "latin only": "def pass_through(x): return x\n",
    "mixed word": "p" + CY + "ss = 1\n",
    "pure cyrillic word": "привет мир\n",
    "pure cyrillic look-alikes only": "аеорсух\n",
    "cyrillic next to a latin word": "abc привет\n",
    "mixed with underscore": "a_" + CY + "_b\n",
    "mixed with digit": "x1" + CY + "\n",
    "first edge of the range": "aЀ\n",
    "last edge of the range": "aӿ bӾ\n",
    "just below the range": "aϿ\n",
    "just above the range": "aԀԁ\n",
    "cyrillic supplement look-alike": "aԁ\n",
    "greek and latin": "aαβ\n",
    "a hundred mixed words": " ".join("w" + CY + str(i) for i in range(100)),
    "upper-case look-alikes": "HАНОР CATС\n",
    "cyrillic in a comment": "// комментарий about p" + CY + "ss\n",
    "cyrillic a long way down": "x = 1\n" * 3000 + "p" + CY + "ss\n",
    "no cyrillic a long way down": "x = 1\n" * 3000 + "pass\n",
    "non-ascii latin": "café über ça\n",
}


@pytest.mark.parametrize("name", list(A6_TEXTS))
def test_a6_hand_cases_match_old_rule(name):
    text = A6_TEXTS[name]
    assert A6_NEW["medicine_a6"](doc(text)) == A6_OLD["medicine_a6"](doc(text))


def test_a6_the_hand_cases_reach_every_branch():
    results = [(A6_NEW["medicine_a6"](doc(t)), t) for t in A6_TEXTS.values()]
    assert any(r[0] == "fix" for r, _ in results)
    assert any(r[0] == "keep" and A6_NEW["CYRILLIC"].search(t) for r, t in results)          # Cyrillic there, nothing to fix
    assert any(r[0] == "keep" and not A6_NEW["CYRILLIC"].search(t) for r, t in results)


def test_a6_a_text_without_cyrillic_does_not_run_mixed_and_one_with_it_does():
    ns = namespace("DA-A6-001")
    ns["MIXED"] = spy = Spy(ns["MIXED"], "sub")
    ns["medicine_a6"](doc("def f(x): return x + 1\n" * 100))
    assert spy.calls == 0
    ns["medicine_a6"](doc("p" + CY + "ss"))
    assert spy.calls == 1


A6_LATIN = ["pass", "return", "x1", "foo_bar", "caf\u00e9", "_", "9", "\u03b1\u03b2", "ab\u0501", "//", "(", ")", "=", "\u2013", "ABC", "value"]
A6_PURE = ["\u043f\u0440\u0438\u0432\u0435\u0442", "\u0430\u0435\u043e", "\u0400", "\u04ff", "\u0410\u0412\u0415"]
A6_MIXED = ["p" + CY + "ss", "a\u0400b", "\u04ffz", "\u0410BC", "H\u0410\u041d", "\u0455cript", "j\u0430v\u0430", "\u0406d", "x_\u0430"]


def random_a6_text(rng):
    """Latin pieces with, in some texts only, a few pure-Cyrillic and a few mixed-script pieces."""
    p_pure, p_mixed = rng.choice([0, 0, 0, 0.03, 0.2]), rng.choice([0, 0, 0, 0.03, 0.2])
    out = []
    for _ in range(rng.randint(0, 80)):
        r = rng.random()
        pool = A6_PURE if r < p_pure else A6_MIXED if r < p_pure + p_mixed else A6_LATIN
        out.append(rng.choice(pool) + rng.choice([" ", " ", "\n", "", "_", "."]))
    return "".join(out)


def test_a6_random_texts_match_old_rule_and_cover_every_branch():
    rng = random.Random(43)
    seen = {"fix": 0, "cyrillic_kept": 0, "none": 0}
    for _ in range(10000):
        t = random_a6_text(rng)
        old, new = A6_OLD["medicine_a6"](doc(t)), A6_NEW["medicine_a6"](doc(t))
        assert new == old, repr(t)
        has = bool(A6_NEW["CYRILLIC"].search(t))
        seen["fix"] += new[0] == "fix"
        seen["cyrillic_kept"] += new[0] == "keep" and has
        seen["none"] += not has
    assert all(v > 300 for v in seen.values()), seen


def test_a6_the_rule_in_clean_py_acts_only_on_the_code_packs_and_equals_the_old_rule():
    rule = c._RULE["DA-A6-001"]()
    for text in (A6_TEXTS["mixed word"], A6_TEXTS["empty"], A6_TEXTS["pure cyrillic word"]):
        for pack in CODE_PACKS:
            assert rule(doc(text, pack)) == A6_OLD["medicine_a6"](doc(text))
        for pack in ("en-dclm", "math-finemath", "sci-finepdfs", None):
            assert rule(doc(text, pack, lang="en")) == ("keep", text)


# =====================================================================================================================
# DA-E2-001: byte arrays and base64 blobs
# =====================================================================================================================

def e2_reference():
    """DA-E2-001 as it was before its speed-up (clean.py 716c9a90093f, specv1_1.md medicine 13): _BYTES is run on every text."""
    _BYTES = re.compile(r"(?:0x[0-9a-fA-F]{2},\s*){24,}(?:0x[0-9a-fA-F]{2},?)?")
    _B64 = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")

    def drop_blob(text: str, share: float = 0.10, b64_share: float = 0.4):
        if not text:
            return "keep", text
        n = len(text)
        if sum(len(m.group()) for m in _BYTES.finditer(text)) / n >= share:
            return "drop", text
        if sum(len(m.group()) for m in _B64.finditer(text)) / n >= b64_share:
            return "drop", text
        return "keep", text

    return {"drop_blob": drop_blob, "_BYTES": _BYTES, "_B64": _B64}


E2_OLD, E2_NEW = e2_reference(), namespace("DA-E2-001")


def test_e2_the_patterns_are_the_old_ones():
    for name in ("_BYTES", "_B64"):
        assert E2_NEW[name].pattern == E2_OLD[name].pattern and E2_NEW[name].flags == E2_OLD[name].flags, name


def test_e2_the_shortest_match_of_bytes_holds_24_groups_that_start_with_0x():
    for k in (23, 24, 25):
        t = "0x00, " * k
        m = E2_OLD["_BYTES"].search(t)
        assert (m is not None) == (k >= 24)
        if m:
            assert m.group().count("0x") >= 24 and t.count("0x") >= 24


def b64(n, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"):
    return "".join(alphabet[(i * 7 + 3) % len(alphabet)] for i in range(n))


def hexes(k, sep=", ", fmt="0x%02x"):
    return sep.join(fmt % (i % 256) for i in range(k))


def same_e2(text):
    assert E2_NEW["drop_blob"](text) == E2_OLD["drop_blob"](text), repr(text[:80])
    return E2_NEW["drop_blob"](text)[0]


E2_TEXTS = {
    "empty": "",
    "plain code": "int main() { return 0; }\n" * 50,
    "23 groups only": hexes(23) + ",",
    "24 groups only": hexes(24) + ",",
    "25 groups only": hexes(25) + ",",
    "24 groups, no trailing comma": hexes(24),
    "24 groups, newlines between": ",\n\t".join("0x%02X" % i for i in range(24)) + ",",
    "100 groups": "var data = []byte{" + hexes(100) + "}\n",
    "24 groups in a long file": "x = 1\n" * 1000 + hexes(24) + ",\n",
    "24 groups, bad hex": ", ".join("0x%02x" % i if i != 5 else "0xzz" for i in range(24)),
    "24 groups, one digit": ", ".join("0x%02x" % i if i != 5 else "0x7" for i in range(24)),
    "24 groups, upper-case x": ", ".join("0X%02x" % i for i in range(24)),
    "23 and 23 groups apart": hexes(23) + " ;\n" + hexes(23),
    "24 0x with no commas": "0x00 " * 24,
    "30 0x in prose": "the value 0x1f is common; " * 30,
    "base64 199": b64(199),
    "base64 200": b64(200),
    "base64 only, long": b64(5000),
    "base64 below the share": "x = 1\n" * 1000 + b64(300),
    "base64 with padding": b64(300) + "==",
    "base64 and fewer than 24 groups": b64(1000) + "\n" + hexes(10),
    "base64 and bytes": hexes(30) + "\n" + b64(1000),
    "many short base64": (b64(150) + " ") * 40,
}


@pytest.mark.parametrize("name", list(E2_TEXTS))
def test_e2_hand_cases_match_old_rule(name):
    same_e2(E2_TEXTS[name])


def test_e2_the_hand_cases_reach_every_branch():
    verdicts = {n: same_e2(t) for n, t in E2_TEXTS.items()}
    assert verdicts["24 groups only"] == "drop"                      # bytes half
    assert verdicts["base64 only, long"] == "drop"                   # base64 half
    assert verdicts["24 groups in a long file"] == "keep"            # 24 or more "0x", under the share
    assert verdicts["23 groups only"] == "keep"                      # under 24 "0x"
    assert verdicts["30 0x in prose"] == "keep"                      # 24 or more "0x", no byte array


@pytest.mark.parametrize("n", range(1420, 1441))
def test_e2_share_threshold_sweep(n):
    """The array is 24 groups, 143 characters: it is 10% of a text of 1430 characters, and the text is dropped up to that length. The
    filler is not base64 characters, so only the byte-array half can drop it."""
    array = hexes(24) + ","
    assert len(array) == 143
    text = array + "." * (n - len(array))
    assert same_e2(text) == ("drop" if n <= 1430 else "keep")


def test_e2_a_text_with_fewer_than_24_groups_does_not_run_bytes_and_one_with_24_does():
    ns = namespace("DA-E2-001")
    ns["_BYTES"] = spy = Spy(ns["_BYTES"], "finditer")
    ns["drop_blob"](hexes(23) + " " + "x" * 100)
    assert spy.calls == 0
    ns["drop_blob"]("x" * 100)
    assert spy.calls == 0
    ns["drop_blob"](hexes(24) + " " + "x" * 100)
    assert spy.calls == 1


def random_e2_text(rng):
    parts = []
    for _ in range(rng.randint(0, 6)):
        kind = rng.choice(["code", "code", "hex", "hex_bad", "b64", "prose0x", "pad"])
        if kind == "code":
            parts.append("func f() { return 1 }\n" * rng.randint(1, 40))
        elif kind == "hex":
            parts.append(hexes(rng.choice([1, 10, 22, 23, 24, 25, 26, 40, 90]), rng.choice([", ", ",", ",\n\t", ",  "])) + rng.choice(["", ",", ", "]))
        elif kind == "hex_bad":
            parts.append(", ".join(rng.choice(["0x%02x", "0X%02x", "0x%x", "0xg%x", "%02x"]) % (i % 16) for i in range(rng.randint(20, 40))))
        elif kind == "b64":
            parts.append(b64(rng.choice([150, 199, 200, 201, 400, 1500, 4000])) + rng.choice(["", "=", "=="]))
        elif kind == "prose0x":
            parts.append("see 0x1f and 0x2a; " * rng.randint(1, 40))
        else:
            parts.append("a" * rng.choice([10, 100, 500, 3000]))
        parts.append(rng.choice(["\n", " ", ""]))
    return "".join(parts)


def test_e2_random_texts_match_old_rule_and_cover_every_branch():
    rng = random.Random(47)
    seen = {"bytes_drop": 0, "b64_drop": 0, "keep_with_24": 0, "keep_below_24": 0}
    for _ in range(6000):
        t = random_e2_text(rng)
        new = same_e2(t)
        bytes_hit = sum(len(m.group()) for m in E2_OLD["_BYTES"].finditer(t)) / max(len(t), 1) >= 0.10
        seen["bytes_drop"] += new == "drop" and bytes_hit
        seen["b64_drop"] += new == "drop" and not bytes_hit
        seen["keep_with_24"] += new == "keep" and t.count("0x") >= 24
        seen["keep_below_24"] += new == "keep" and t.count("0x") < 24
    assert all(v > 150 for v in seen.values()), seen


def test_e2_the_rule_in_clean_py_acts_only_on_the_code_packs_and_equals_the_old_rule():
    rule = c._RULE["DA-E2-001"]()
    for text in (E2_TEXTS["24 groups only"], E2_TEXTS["plain code"], E2_TEXTS["empty"], E2_TEXTS["base64 only, long"]):
        for pack in CODE_PACKS:
            old = E2_OLD["drop_blob"](text)
            assert rule(doc(text, pack)) == old
        for pack in ("en-dclm", "math-finemath", "sci-finepdfs", None):
            assert rule(doc(text, pack, lang="en")) == ("keep", text)


# =====================================================================================================================
# DA-E3-003: known keys and base32 seeds
# =====================================================================================================================

def e3_reference():
    """DA-E3-003 as it was before its speed-up (clean.py 716c9a90093f, specv1_1.md medicine 23): all five KEYS patterns and SEED
    are run on every text."""
    KEYS = [re.compile(p) for p in (r"AKIA[0-9A-Z]{16}", r"gh[pousr]_[A-Za-z0-9]{30,}", r"\bsk-[A-Za-z0-9_-]{20,}",
            r"xox[baprs]-[A-Za-z0-9-]{10,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")]
    SEED = re.compile(r'(?i)((?:secret|seed|totp|otp)\w*\s*:?=\s*")[A-Z2-7]{16,}(")')

    def medicine_e3(doc):
        t = doc["text"]
        for rx in KEYS:
            t = rx.sub("EXAMPLE_SECRET", t)
        t = SEED.sub(r"\1EXAMPLE_SECRET\2", t)
        return ("fix" if t != doc["text"] else "keep", t)

    return {"medicine_e3": medicine_e3, "KEYS": KEYS, "SEED": SEED}


E3_OLD, E3_NEW = e3_reference(), namespace("DA-E3-003")


def test_e3_the_patterns_are_the_old_ones():
    assert [(r.pattern, r.flags) for r in E3_NEW["KEYS"]] == [(r.pattern, r.flags) for r in E3_OLD["KEYS"]]
    assert (E3_NEW["SEED"].pattern, E3_NEW["SEED"].flags) == (E3_OLD["SEED"].pattern, E3_OLD["SEED"].flags)
    assert len(E3_NEW["KEY_HINTS"]) == len(E3_NEW["KEYS"])


AKIA = "AKIA" + "ABCDEFGH12345678"
GH = {l: "gh" + l + "_" + "a1B2" * 8 for l in "pousr"}
SK = "sk-" + "abc_DEF-123" * 3
XOX = {l: "xox" + l + "-" + "1234567890ab" for l in "baprs"}
PEM = "-----BEGIN RSA " + "PRIVATE KEY-----\nMIIabc\n-----END RSA PRIVATE KEY-----"  # joined at run time, so pr-guard does not read it as a key
SEEDV = "ABCDEFGHIJKLMNOP"
KEY_SAMPLES = [AKIA, *GH.values(), SK, *XOX.values(), PEM]


def test_e3_every_text_a_keys_pattern_matches_holds_one_of_its_literals():
    """The hints are necessary: a sample of every shape of every pattern holds a hint of its pattern, and no other pattern's match is lost."""
    for rx, hints in zip(E3_OLD["KEYS"], E3_NEW["KEY_HINTS"]):
        samples = [s for s in KEY_SAMPLES if rx.search(s)]
        assert samples, rx.pattern
        for s in samples:
            m = rx.search(s)
            assert any(h in m.group() for h in hints), (rx.pattern, m.group())
    # the five gh shapes and the five xox shapes are all matched (so every letter of the class is covered by a hint)
    for s in (*GH.values(), *XOX.values()):
        assert any(rx.search(s) for rx in E3_OLD["KEYS"]), s


def test_e3_the_seed_words_catch_every_character_the_unicode_flag_lets_match_a_letter_of_them():
    """SEED is (?i): a character that matches a letter of secret, seed or totp under it must keep its letter after casefold()."""
    letters = sorted(set("secrettotpseedotp"))
    res = {ch: re.compile("(?i)" + ch) for ch in letters}
    for cp in range(0x20000):
        ch = chr(cp)
        for letter, rx in res.items():
            if rx.fullmatch(ch):
                assert letter in ch.casefold(), (hex(cp), letter)


def test_e3_the_seed_words_cover_the_words_of_the_pattern():
    assert set(E3_NEW["SEED_WORDS"]) <= {"secret", "seed", "totp", "otp"} and "otp" in E3_NEW["SEED_WORDS"]
    for w in ("secret", "seed", "totp", "otp"):
        assert any(s in w for s in E3_NEW["SEED_WORDS"]), w


def seeds(word, sep='=', quote='"', value=SEEDV):
    return word + sep + quote + value + quote


E3_TEXTS = {
    "empty": "",
    "plain code": "x = 1\nprint('hello')\n" * 30,
    "aws key": "key = '" + AKIA + "'\n",
    "aws key too short": "AKIA" + "A" * 15,
    "aws key lower case": "akia" + "A" * 16,
    "github token each letter": "\n".join(GH.values()),
    "github token too short": "ghp_" + "a" * 29,
    "github look-alike": "ghx_" + "a" * 40,
    "github token inside a word": "xgho_" + "a" * 30,
    "sk key": "t = " + SK,
    "sk key inside a word": "ask-" + "a" * 25,
    "sk key too short": "sk-" + "a" * 19,
    "slack tokens": "\n".join(XOX.values()),
    "slack token too short": "xoxb-123456789",
    "pem block": "a\n" + PEM + "\nb\n",
    "pem block no end": "-----BEGIN " + "PRIVATE KEY-----\nabc\n",
    "pem begin, wrong spacing": "-----BEGIN" + "PRIVATE KEY-----\n-----END PRIVATE KEY-----",
    "all five": "\n".join([AKIA, GH["p"], SK, XOX["b"], PEM]),
    "keys back to back": AKIA + GH["p"] + SK,
    "seed assignment": seeds("secret") + "\n",
    "seed assignment, upper case word": seeds("SECRET_KEY") + "\n",
    "seed assignment, mixed case": seeds("TotpSeed") + "\n",
    "seed assignment, otp": seeds("otp") + "\n",
    "seed assignment, seed": seeds("seed") + "\n",
    "seed assignment, totp": seeds("totp") + "\n",
    "seed assignment, long dotless s": seeds("ſecret") + "\n",
    "seed assignment, dotless s in seed": seeds("ſeed") + "\n",
    "seed assignment, colon equals": seeds("secret", sep=" := ") + "\n",
    "seed assignment, spaces": 'secret  =  "' + SEEDV + '"\n',
    "seed assignment, word suffix": seeds("secret_value_2") + "\n",
    "seed value too short": seeds("secret", value="ABCDEFGHIJKLMNO"),
    "seed value with lower case": seeds("secret", value="abcdefghijklmnop"),
    "seed value digits 2 to 7 only": seeds("secret", value="2345672345672345"),
    "seed value with a 1": seeds("secret", value="ABCDEFGHIJKLMNO1"),
    "seed with single quote": seeds("secret", quote="'"),
    "seed without a quote": "secret = " + SEEDV,
    "seed without an equals": 'secret "' + SEEDV + '"',
    "word without equals or quote": "secret seed otp totp " * 20,
    "equals and quote without a word": 'name = "' + SEEDV + '"',
    "word, equals and quote apart": 'seed\n=\n"' + SEEDV + '"',
    "word after the assignment": 'name = "' + SEEDV + '" # secret',
    "seed and keys": AKIA + "\n" + seeds("secret") + "\n" + PEM,
    "key replaced then seed": "secret=\"" + SEEDV + "\" " + AKIA,
    "cascade: replacement text next to a seed": "secret=\"" + "EXAMPLE_SECRET" + "\"",
    "non-ascii around": "éé " + seeds("secret") + " 中文",
    "key a long way down": "x = 1\n" * 3000 + AKIA,
    "seed a long way down": "x = 1\n" * 3000 + seeds("secret"),
}


def same_e3(text, pack="code-go", lang="go"):
    new, old = E3_NEW["medicine_e3"](doc(text, pack, lang)), E3_OLD["medicine_e3"](doc(text, pack, lang))
    assert new == old, repr(text[:100])
    return new


@pytest.mark.parametrize("name", list(E3_TEXTS))
def test_e3_hand_cases_match_old_rule(name):
    same_e3(E3_TEXTS[name])


def test_e3_the_hand_cases_reach_every_branch():
    results = {n: same_e3(t) for n, t in E3_TEXTS.items()}
    assert all(results[n][0] == "fix" for n in ("aws key", "github token each letter", "sk key", "slack tokens", "pem block", "all five",
                                                "seed assignment", "seed assignment, long dotless s", "seed and keys"))
    assert all(results[n][0] == "keep" for n in ("plain code", "aws key too short", "seed value too short", "word without equals or quote",
                                                 "equals and quote without a word", "seed without a quote"))


def test_e3_the_dotless_s_seed_is_replaced_and_found_only_by_the_casefold():
    text = seeds("ſecret")
    assert E3_NEW["medicine_e3"](doc(text))[0] == "fix"
    assert "secret" not in text.lower() and "secret" in text.casefold()


def test_e3_a_key_pattern_runs_only_when_a_literal_it_needs_is_in_the_text():
    expected_runs = [AKIA, GH["s"], SK, XOX["r"], PEM]
    for i, sample in enumerate(expected_runs):
        ns = namespace("DA-E3-003")
        spies = [Spy(rx, "sub") for rx in ns["KEYS"]]
        ns["KEYS"] = spies
        ns["medicine_e3"](doc("plain text\n"))
        assert [s.calls for s in spies] == [0] * 5
        ns["medicine_e3"](doc(sample))
        assert spies[i].calls == 1, i
        assert sum(s.calls for s in spies) == 1 + sum(1 for j, h in enumerate(ns["KEY_HINTS"]) if j != i and any(x in sample for x in h)), i


def test_e3_seed_runs_only_for_a_text_with_equals_quote_and_a_word():
    def calls(text):
        ns = namespace("DA-E3-003")
        ns["SEED"] = spy = Spy(ns["SEED"], "sub")
        ns["medicine_e3"](doc(text))
        return spy.calls
    assert calls("x = 1\n" * 50) == 0
    assert calls('secret "no equals"') == 0
    assert calls("secret = no_quote") == 0
    assert calls('name = "no word"') == 0
    assert calls(seeds("secret")) == 1
    assert calls(seeds("ſeed")) == 1
    assert calls(seeds("OTP")) == 1


E3_PIECES = [AKIA, GH["p"], GH["o"], SK, XOX["b"], PEM, "AKIA" + "A" * 10, "ghp_short", "sk-short", "xoxb-1", "-----BEGIN X-----",
             seeds("secret"), seeds("SEED_KEY"), seeds("totp"), seeds("otp"), seeds("ſecret"), seeds("secret", value="SHORT"),
             seeds("password"), seeds("name"), 'secret = "', 'seed = x', "secret", "seed", "otp", "totp", "x = 1", "print(1)", "=", '"',
             "A" * 16, "ghx_" + "a" * 30, "EXAMPLE_SECRET", "// secret key", "token = 'abc'", "é中"]


def random_e3_text(rng):
    return "".join(rng.choice(E3_PIECES) + rng.choice([" ", "\n", "", "\n\n", ";", "\t"]) for _ in range(rng.randint(0, 25)))


def test_e3_random_texts_match_old_rule_and_cover_every_branch():
    rng = random.Random(53)
    seen = {"fix": 0, "keep_with_word": 0, "keep_plain": 0, "key_fix": 0, "seed_fix": 0}
    for _ in range(12000):
        t = random_e3_text(rng)
        new = same_e3(t)
        seen["fix"] += new[0] == "fix"
        seen["keep_with_word"] += new[0] == "keep" and any(w in t.casefold() for w in ("secret", "seed", "otp"))
        seen["keep_plain"] += new[0] == "keep" and not any(w in t.casefold() for w in ("secret", "seed", "otp"))
        t2 = t
        for rx in E3_OLD["KEYS"]:
            t2 = rx.sub("EXAMPLE_SECRET", t2)
        seen["key_fix"] += t2 != t
        seen["seed_fix"] += E3_OLD["SEED"].sub(r"\1EXAMPLE_SECRET\2", t2) != t2
    assert all(v > 200 for v in seen.values()), seen


def test_e3_the_rule_in_clean_py_acts_only_on_the_code_packs_and_equals_the_old_rule():
    rule = c._RULE["DA-E3-003"]()
    for text in (E3_TEXTS["all five"], E3_TEXTS["seed assignment"], E3_TEXTS["plain code"], E3_TEXTS["empty"]):
        for pack in CODE_PACKS:
            assert rule(doc(text, pack)) == E3_OLD["medicine_e3"](doc(text))
        for pack in ("en-dclm", "math-finemath", "sci-finepdfs", None):
            assert rule(doc(text, pack, lang="en")) == ("keep", text)
