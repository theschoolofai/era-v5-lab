"""Text normalize for decontamination. The same function runs on benchmark items and on documents.

Week 2: replace this module with the spec v1 normalize function of Team 1 and change NORMALIZE_ID.
A fingerprint set records NORMALIZE_ID, and decontam_check.py refuses a set with a different ID.
"""

import re
import sys
import unicodedata

NORMALIZE_ID = "g9-v1"
DESCRIPTION = ("words = runs of Unicode L/M/N characters; each word NFKC then lower(); "
               "everything else separates words")


def _mark_ranges():
    # Python \w does not match combining marks (Unicode M*), so Indic vowel signs
    # would split words. Add all M* characters to the word class.
    ranges, start, prev = [], None, None
    for cp in range(sys.maxunicode + 1):
        if unicodedata.category(chr(cp))[0] == "M":
            if start is None:
                start = cp
            prev = cp
        elif start is not None:
            ranges.append((start, prev))
            start = None
    if start is not None:
        ranges.append((start, prev))
    return "".join(f"\\U{a:08x}-\\U{b:08x}" for a, b in ranges)


# A word is a run of Unicode letters (L*), marks (M*) and numbers (N*).
# Everything else (spaces, punctuation, symbols, underscore) separates words.
WORD_RE = re.compile(f"(?:[^\\W_]|[{_mark_ranges()}])+")


def words_with_offsets(text):
    """Return [(word, char_offset)] for text. Offsets point into the original text."""
    out = []
    for m in WORD_RE.finditer(text):
        tok = unicodedata.normalize("NFKC", m.group()).lower()
        # NFKC can add separators (for example "½" -> "1⁄2"), so split again.
        for w in WORD_RE.findall(tok):
            out.append((w, m.start()))
    return out


def normalize(text):
    """Text -> list of normalized words."""
    return [w for w, _ in words_with_offsets(text)]
