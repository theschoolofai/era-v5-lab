"""Language-neutral signals for H3, the same content in another language: sentences, numbers, Latin-script tokens, a
language-neutral URL key and the length ratio. Pure Python, no model; used by h3.py.

None of these decides H3 on its own. The sentences feed the encoder. The URL key finds sites that publish one page in
several languages (hi.example.org, /hi/, ?lang=hi). Numbers, Latin-script tokens and the length ratio are reported for
each candidate pair, for the hand review.

    python3 -B -m pytest dedup/tests/test_h3_signals.py
"""
import re
import unicodedata
from collections import Counter
from urllib.parse import parse_qsl, urlencode, urlsplit

# A sentence ends at . ! ? or the Devanagari danda or double danda followed by whitespace, or at a line break.
_SENTENCE_END = re.compile(r"(?<=[.!?।॥])\s+|\s*\n\s*")
# \d matches every Unicode decimal digit (Devanagari, Bengali, Tamil, ...), so Indic and ASCII numbers are both found.
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
# Names, acronyms and URLs that stay in Latin letters inside Indic text; three letters or more.
_LATIN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z0-9]{2,}")
_LOCALE = re.compile(r"^([a-z]{2})(?:[-_][a-z]{2})?$")

LANG_CODES = frozenset("en hi sa mr bn gu kn ml or ta te pa ur as ne".split())
LANG_NAMES = {"english": "en", "hindi": "hi", "sanskrit": "sa", "marathi": "mr", "bengali": "bn", "bangla": "bn",
              "gujarati": "gu", "kannada": "kn", "malayalam": "ml", "odia": "or", "oriya": "or", "tamil": "ta",
              "telugu": "te", "punjabi": "pa", "urdu": "ur", "assamese": "as", "nepali": "ne"}
LANG_PARAMS = frozenset({"lang", "language", "hl", "lng", "locale"})
_HOST_PREFIXES = ("www", "m")


def split_sentences(text, min_chars=20, max_sentences=None):
    """The document's sentences, whitespace collapsed, each at least min_chars long (shorter ones, such as menu items
    and headings, are dropped); at most max_sentences, from the start."""
    out = []
    for s in _SENTENCE_END.split(text or ""):
        s = " ".join(s.split())
        if len(s) >= min_chars:
            out.append(s)
            if max_sentences and len(out) >= max_sentences:
                break
    return out


def numbers(text):
    """The multiset of numbers, with every script's digits as ASCII and the thousands commas removed, so that
    "२०२४" and "2024" match, and "1,00,000" and "100000" too."""
    found = Counter()
    for m in _NUMBER.finditer(text or ""):
        s = "".join(str(unicodedata.decimal(ch)) if ch.isdecimal() else ch for ch in m.group()).replace(",", "")
        found[s if "." in s else str(int(s))] += 1
    return found


def multiset_jaccard(a, b):
    """Shared / all counts of two Counters; None when both are empty (no evidence either way)."""
    if not a and not b:
        return None
    return sum((a & b).values()) / sum((a | b).values())


def latin_tokens(text):
    """The set of Latin-script words of three letters or more, lowercased."""
    return {t.lower() for t in _LATIN.findall(text or "")}


def latin_share(a, b):
    """The share of the smaller token set found in the other; None when either is empty. For an Indic and an English
    document this is the share of the Indic document's Latin words (names, acronyms) that the English one has."""
    if not a or not b:
        return None
    return len(a & b) / min(len(a), len(b))


def _language(token):
    t = token.lower()
    if t in LANG_NAMES:
        return LANG_NAMES[t]
    m = _LOCALE.match(t)
    return m.group(1) if m and m.group(1) in LANG_CODES else None


def url_key(url):
    """(key, language): the URL with one language marker removed, and the language that marker named.

    The marker is a language subdomain (hi.wikipedia.org), a path segment (/hi/, /en-us/, /hindi/) or a query
    parameter (?lang=hi). www. and m. are dropped, the path is lowercased and the other query parameters are sorted.
    So https://example.org/hi/news/7 and https://example.org/news/7 share a key. The key is None for a site's home
    page (no path left), whose language versions are not one document."""
    if not url:
        return None, None
    try:
        parts = urlsplit(url.strip())
        host = (parts.hostname or "").lower()
    except ValueError:
        return None, None
    if not host:
        return None, None
    labels = host.split(".")
    while len(labels) > 2 and labels[0] in _HOST_PREFIXES:
        labels.pop(0)
    lang = None
    if len(labels) > 2 and _language(labels[0]):
        lang = _language(labels.pop(0))
        while len(labels) > 2 and labels[0] in _HOST_PREFIXES:
            labels.pop(0)
    segments = [s for s in parts.path.split("/") if s]
    if lang is None:
        for k, segment in enumerate(segments):
            if _language(segment):
                lang = _language(segment)
                del segments[k]
                break
    query = []
    for name, value in parse_qsl(parts.query, keep_blank_values=True):
        if name.lower() in LANG_PARAMS:
            lang = lang or _language(value)
            continue
        query.append((name, value))
    if not segments and not query:
        return None, lang
    key = ".".join(labels) + "/" + "/".join(segments).lower()
    return (key + "?" + urlencode(sorted(query)) if query else key), lang


def length_ratio(a, b):
    """Longer / shorter character count; infinite when either is 0."""
    lo, hi = min(a, b), max(a, b)
    return hi / lo if lo > 0 else float("inf")
