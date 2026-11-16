"""Unit tests for h3_signals.py, the language-neutral signals of H3: sentences, numbers, Latin-script tokens, the URL key
and the length ratio. Every text and URL here is made up.

  python3 -B -m pytest dedup/tests/test_h3_signals.py
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from h3_signals import (latin_share, latin_tokens, length_ratio, multiset_jaccard, numbers,  # noqa: E402
                        split_sentences, url_key)


def test_sentences_split_at_end_marks_and_line_breaks():
    text = "First sentence here. Second one is here!\nThird line is also here।  Fourth"
    assert split_sentences(text, min_chars=10) == ["First sentence here.", "Second one is here!",
                                                   "Third line is also here।"]


def test_sentences_split_at_danda_and_double_danda():
    text = "यह पहला वाक्य है। यह दूसरा वाक्य है॥ यह तीसरा वाक्य है।"
    assert split_sentences(text, min_chars=5) == ["यह पहला वाक्य है।", "यह दूसरा वाक्य है॥", "यह तीसरा वाक्य है।"]


def test_sentences_short_ones_dropped_spaces_collapsed_and_capped():
    text = "Menu\nA   long enough sentence   here. Another long enough one here. A third long enough one."
    assert split_sentences(text, min_chars=10) == ["A long enough sentence here.", "Another long enough one here.",
                                                   "A third long enough one."]
    assert split_sentences(text, min_chars=10, max_sentences=2) == ["A long enough sentence here.",
                                                                    "Another long enough one here."]
    assert split_sentences("", 10) == [] and split_sentences(None, 10) == []


def test_numbers_match_across_scripts_and_grouping():
    assert numbers("वर्ष २०२४ में 1,00,000 लोग; 2024 और 007") == Counter({"2024": 2, "100000": 1, "7": 1})
    assert numbers("১২ জন") == Counter({"12": 1})          # Bengali digits
    assert numbers("pi is 3.14") == Counter({"3.14": 1})
    assert numbers("no digits") == Counter()


def test_multiset_jaccard():
    a, b = Counter({"1": 2, "2": 1}), Counter({"1": 1, "3": 1})
    assert multiset_jaccard(a, b) == 1 / 4                  # min counts 1 / max counts 2 + 1 + 1
    assert multiset_jaccard(a, a) == 1.0
    assert multiset_jaccard(Counter(), Counter()) is None
    assert multiset_jaccard(a, Counter()) == 0.0


def test_latin_tokens_and_share():
    hindi = latin_tokens("भारत में NASA और ISRO ने in 2024 में काम किया")
    assert hindi == {"nasa", "isro"}                        # "in" is too short; 2024 is not a word
    english = latin_tokens("NASA and ISRO worked together in 2024")
    assert latin_share(hindi, english) == 1.0
    assert latin_share(hindi, {"nasa", "other", "words"}) == 0.5
    assert latin_share(set(), english) is None


def test_url_key_language_subdomain():
    assert url_key("https://hi.wikipedia.org/wiki/Taj_Mahal") == ("wikipedia.org/wiki/taj_mahal", "hi")
    assert url_key("https://en.m.wikipedia.org/wiki/Taj_Mahal") == ("wikipedia.org/wiki/taj_mahal", "en")


def test_url_key_language_path_segment():
    assert url_key("https://www.example.com/hi/news/7") == ("example.com/news/7", "hi")
    assert url_key("https://example.com/news/7") == ("example.com/news/7", None)   # same key, no marker
    assert url_key("https://example.com/en-us/about") == ("example.com/about", "en")
    assert url_key("https://example.com/hindi/story") == ("example.com/story", "hi")


def test_url_key_language_query_parameter():
    assert url_key("https://example.com/news/7?lang=hi&id=3") == ("example.com/news/7?id=3", "hi")
    assert url_key("https://example.com/news/7?id=3") == ("example.com/news/7?id=3", None)


def test_url_key_none_for_home_pages_and_missing_urls():
    assert url_key("https://hi.example.com/") == (None, "hi")
    assert url_key("") == (None, None) and url_key(None) == (None, None)
    assert url_key("not a url") == (None, None)


def test_url_key_keeps_other_subdomains_and_short_hosts():
    assert url_key("https://blog.example.com/a") == ("blog.example.com/a", None)
    assert url_key("https://example.in/a") == ("example.in/a", None)


def test_length_ratio():
    assert length_ratio(100, 250) == 2.5 == length_ratio(250, 100)
    assert length_ratio(0, 10) == float("inf")
