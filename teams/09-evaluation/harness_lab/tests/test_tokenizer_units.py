"""Tests for tokenizer_units.py (metric_v1, Lab 5 design 4).

    pytest teams/09-evaluation/harness_lab/tests/test_tokenizer_units.py -q

Toy word-level tokenizers stand in for p1536 and C3, so no tokenizer file is needed.
"""

import sys
from pathlib import Path

import pytest

tokenizers = pytest.importorskip("tokenizers")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tokenizer_units as tu  # noqa: E402


def word_tokenizer(split_long=False):
    """One token per word; with split_long, a word of 4+ letters is two tokens (a 'worse' tokenizer)."""
    from tokenizers import Regex, Tokenizer, models, pre_tokenizers

    tok = Tokenizer(models.WordLevel({"[UNK]": 0}, unk_token="[UNK]"))
    pattern = r"\S{1,3}" if split_long else r"\S+"
    tok.pre_tokenizer = pre_tokenizers.Split(Regex(pattern), behavior="isolated", invert=False)
    return tok


def ntok(tok, text):
    return len(tok.encode(text, add_special_tokens=False).ids)


TEXT = "alpha beta\ngamma delta epsilon\nzeta eta theta iota kappa\nlambda mu"


def test_byte_segments_rebuild_the_text_and_respect_the_limit():
    pieces = tu.byte_segments(TEXT, limit=24)
    assert "".join(pieces) == TEXT
    assert all(len(p.encode("utf-8")) <= 24 for p in pieces)
    assert all(p.endswith(("\n", " ")) for p in pieces[:-1])  # cut after a newline or space


def test_byte_segments_never_split_a_character():
    text = "क" * 50  # 3 bytes per character, no spaces
    pieces = tu.byte_segments(text, limit=10)
    assert "".join(pieces) == text
    assert all(len(p.encode("utf-8")) <= 10 and len(p.encode("utf-8")) % 3 == 0 for p in pieces)


def test_fitted_segments_fit_every_tokenizer_and_rebuild_the_text():
    a, b = word_tokenizer(), word_tokenizer(split_long=True)
    pieces = tu.fitted_segments(TEXT, [a, b], window=5)
    assert "".join(pieces) == TEXT
    assert all(ntok(a, p) <= 5 and ntok(b, p) <= 5 for p in pieces)
    assert len(pieces) > 1
    assert all(p.endswith(("\n", " ")) for p in pieces[:-1])


def test_fitted_segments_keep_a_short_text_whole():
    assert tu.fitted_segments("one two", [word_tokenizer()], window=5) == ["one two"]


def test_measure_counts_tokens_resets_and_segments():
    a, b = word_tokenizer(), word_tokenizer(split_long=True)
    rows = tu.measure([TEXT, "short"], ["s1", "s1"], {"A": a, "B": b}, window=5, limit=24)
    ra, rb = rows[("s1", "A")], rows[("s1", "B")]
    assert ra["docs"] == rb["docs"] == 2
    assert ra["raw_bytes"] == rb["raw_bytes"] == len(TEXT.encode()) + 5
    assert ra["tokens"] == ntok(a, TEXT) + ntok(a, "short") and rb["tokens"] == ntok(b, TEXT) + ntok(b, "short")
    assert rb["tokens"] > ra["tokens"]
    # token windows: resets depend on the tokenizer; fitted segments: the same for both
    assert rb["context_resets"] > ra["context_resets"]
    assert ra["fitted_resets"] == rb["fitted_resets"]
    assert ra["segments"] == rb["segments"]
