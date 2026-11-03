"""Script classes of token bytes, used to break collision counts down by writing system.

Partial-UTF-8 tokens can be tagged with the block their lead byte points at (``detail=True``).
"""

from __future__ import annotations

import unicodedata

from .tokenizer import TokenizerBundle, raw_bytes_for_id

BRAHMIC_BLOCKS: dict[str, tuple[int, int]] = {
    "Devanagari": (0x0900, 0x097F),
    "Bengali": (0x0980, 0x09FF),
    "Gurmukhi": (0x0A00, 0x0A7F),
    "Gujarati": (0x0A80, 0x0AFF),
    "Oriya": (0x0B00, 0x0B7F),
    "Tamil": (0x0B80, 0x0BFF),
    "Telugu": (0x0C00, 0x0C7F),
    "Kannada": (0x0C80, 0x0CFF),
    "Malayalam": (0x0D00, 0x0D7F),
}
# Vedic Extensions / Devanagari Extended are used by Devanagari text too.
BRAHMIC_EXTRA = {"Devanagari": [(0x1CD0, 0x1CFF), (0xA8E0, 0xA8FF)]}

SPECIAL_CLASS = "Special/Control"
PARTIAL_CLASS = "Partial-UTF8"
CODE_CLASS = "Code/Structure"
DIGIT_CLASS = "Digits"
LATIN_CLASS = "Latin"
MIXED_CLASS = "Mixed"
OTHER_CLASS = "Other"


def _char_class(ch: str) -> str | None:
    """Class of one code point, or None for ignorable (space/newline/ZW*)."""
    cp = ord(ch)
    if ch in " \t\r\n\x0b\x0c" or cp in (0x200B, 0x200C, 0x200D, 0xFEFF):
        return None  # layout / joiner: ignored for classification
    for name, (lo, hi) in BRAHMIC_BLOCKS.items():
        if lo <= cp <= hi:
            return name
    for name, ranges in BRAHMIC_EXTRA.items():
        if any(lo <= cp <= hi for lo, hi in ranges):
            return name
    cat = unicodedata.category(ch)
    if cat.startswith("N"):
        return DIGIT_CLASS
    if cp < 0x80:
        return CODE_CLASS if not ch.isalpha() else LATIN_CLASS
    if cat.startswith("L") or cat.startswith("M"):
        try:
            if unicodedata.name(ch).startswith("LATIN"):
                return LATIN_CLASS
        except ValueError:
            pass
        return OTHER_CLASS
    # Non-ASCII punctuation/symbols (curly quotes, U+FFFD, box drawing, ...)
    return OTHER_CLASS


def _lead_byte_hint(raw: bytes) -> str:
    """Which script a UTF-8 fragment most likely belongs to, from its lead byte(s)."""
    # 3-byte lead E0 + second byte selects the Brahmic block (U+0900..U+0DFF).
    for i, b in enumerate(raw):
        if 0xE0 <= b <= 0xEF:
            if b == 0xE0 and i + 1 < len(raw):
                b2 = raw[i + 1]
                cp_hi = ((b & 0x0F) << 12) | ((b2 & 0x3F) << 6)
                for name, (lo, hi) in BRAHMIC_BLOCKS.items():
                    if lo <= cp_hi <= hi or lo <= cp_hi + 63 <= hi:
                        return name
                return "3-byte(E0: Sinhala/Thai/Tibetan remnant)"
            if b == 0xE0:
                return "3-byte(E0: Brahmic, block unknown)"
            if b == 0xE1:
                return "3-byte(E1: Georgian/Cherokee/ext)"
            if b == 0xE2:
                return "3-byte(E2: punctuation/math symbols)"
            if b == 0xE3:
                return "3-byte(E3: Kana/CJK punct)"
            if 0xE4 <= b <= 0xE9:
                return "3-byte(CJK remnant)"
            if 0xEA <= b <= 0xED:
                return "3-byte(Hangul remnant)"
            if b == 0xEE:
                return "3-byte(EE: private use)"
            return "3-byte(EF: fullwidth/specials)"
        if 0xC2 <= b <= 0xDF:
            return "2-byte(Latin-ext/Greek/Cyrillic)"
        if 0xF0 <= b <= 0xF4:
            return "4-byte(emoji/supp)"
    return "continuation-only"


def script_class(raw: bytes, *, is_special: bool = False, detail: bool = False) -> str:
    """Map a token's exact bytes to one script class (string).

    With ``detail=True`` partial-UTF-8 tokens get a sub-tag naming the script
    block their lead bytes point at, e.g. ``Partial-UTF8[Devanagari]``.
    """
    if is_special:
        return SPECIAL_CLASS
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return f"{PARTIAL_CLASS}[{_lead_byte_hint(raw)}]" if detail else PARTIAL_CLASS
    classes = {c for ch in text if (c := _char_class(ch)) is not None}
    if not classes:
        return CODE_CLASS  # pure whitespace / newline runs: structure tokens
    if len(classes) == 1:
        return classes.pop()
    # Latin + punctuation (e.g. "'s", "(x") is still "Latin"; digits + punct is Digits.
    if classes == {LATIN_CLASS, CODE_CLASS}:
        return LATIN_CLASS
    if classes == {DIGIT_CLASS, CODE_CLASS}:
        return DIGIT_CLASS
    brahmic = classes & set(BRAHMIC_BLOCKS)
    if len(brahmic) == 1 and classes - brahmic <= {CODE_CLASS, DIGIT_CLASS}:
        return brahmic.pop()  # Indic word with a trailing danda/punct/digit
    return MIXED_CLASS


def classify_vocab(tb: TokenizerBundle, detail: bool = False) -> list[str]:
    return [
        script_class(raw_bytes_for_id(tb, i), is_special=i in tb.special_ids, detail=detail)
        for i in range(tb.vocab_size)
    ]
