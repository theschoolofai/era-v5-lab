"""Tests for tokenizer_units.py (metric_v1, Lab 5 design 4).

    pytest teams/09-evaluation/harness_lab/tests/test_tokenizer_units.py -q

Toy tokenizers stand in for p1536 and C3, so no tokenizer file is needed.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("tokenizers")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tokenizer_units as tu  # noqa: E402


def toy(pattern):
    """A tokenizer whose tokens are the regex matches (and the gaps between them)."""
    from tokenizers import Regex, Tokenizer, models, pre_tokenizers

    tok = Tokenizer(models.WordLevel({"[UNK]": 0}, unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.Split(Regex(pattern), behavior="isolated", invert=False)
    return tok


WORDS = toy(r" ?\S+")        # one token per word, a space joined to the word after it (as in p1536)
SHORT = toy(r" ?\S{1,3}")    # long words split in pieces of 3: more tokens
CHARS = toy(r".")            # one token per character
TEXT = "alpha beta\ngamma delta epsilon\nzeta eta theta iota kappa\nlambda mu"


def test_byte_segments_rebuild_the_text_and_respect_the_limit():
    pieces = tu.byte_segments(TEXT, limit=24)
    assert "".join(pieces) == TEXT
    assert all(len(p.encode()) <= 24 for p in pieces)
    assert pieces[0].endswith("\n")


def test_byte_segments_never_split_a_character_and_refuse_tiny_limits():
    text = "क" * 50  # 3 bytes per character, nothing to cut at
    pieces = tu.byte_segments(text, limit=10)
    assert "".join(pieces) == text
    assert all(len(p.encode()) <= 10 and len(p.encode()) % 3 == 0 for p in pieces)
    with pytest.raises(ValueError):
        tu.byte_segments(text, limit=2)


def test_fitted_pieces_fit_every_tokenizer_and_cut_after_newlines():
    # line tokens (WORDS, SHORT): (3, 5), (4, 8), (6, 10), (2, 3); a budget of 12 fits every line
    pieces = tu.fitted_segments(TEXT, [WORDS, SHORT], budget=12)
    assert "".join(pieces) == TEXT
    assert len(pieces) > 1
    assert all(tu.ntokens(t, p) <= 12 for p in pieces for t in (WORDS, SHORT))
    assert all(p.endswith("\n") for p in pieces[:-1])


def test_fitted_cut_without_newlines_falls_before_a_space():
    text = " ".join(["word"] * 40)
    pieces = tu.fitted_segments(text, [WORDS], budget=7)
    assert "".join(pieces) == text
    assert all(p[0] == " " for p in pieces[1:])  # the space stays with the word after it
    # cutting before a space adds no tokens: the pieces hold exactly the tokens of the whole text
    assert sum(tu.ntokens(WORDS, p) for p in pieces) == tu.ntokens(WORDS, text)


def test_fitted_falls_back_to_characters_in_text_without_spaces():
    text = "क" * 25
    pieces = tu.fitted_segments(text, [CHARS], budget=10)
    assert "".join(pieces) == text
    assert [len(p) for p in pieces] == [10, 10, 5]  # as long as possible


def test_fitted_pieces_are_as_long_as_possible():
    pieces = tu.fitted_segments(TEXT, [WORDS], budget=6)
    lines = TEXT.splitlines(keepends=True)
    for piece, rest in zip(pieces, pieces[1:]):
        next_line = next(line for line in lines if rest.startswith(line))
        assert tu.ntokens(WORDS, piece + next_line) > 6  # adding the next line would not fit


def test_each_tokenizer_can_be_the_binding_one():
    # WORDS binds on the many-short-words line, SHORT on the long-words line
    text = "a b c d e f g h\nextraordinarily unbelievable\n"
    pieces = tu.fitted_segments(text, [WORDS, SHORT], budget=6)
    assert all(tu.ntokens(t, p) <= 6 for p in pieces for t in (WORDS, SHORT))
    alone = tu.fitted_segments(text, [WORDS], budget=6)
    assert len(pieces) > len(alone)


def test_fitted_refuses_a_character_over_the_budget():
    with pytest.raises(ValueError):
        tu.fitted_segments("ab", [CHARS], budget=0)


def test_offsets_round_trip():
    pieces = tu.fitted_segments(TEXT, [WORDS], budget=6)
    assert tu.pieces_at(TEXT, tu.offsets_of(pieces)) == pieces


def test_token_window_resets_match_document_windows():
    # Team 5's DocumentWindows starts a window at 0, seq_len, 2 seq_len, ...: resets = windows - 1
    rows, _ = tu.measure([" ".join(["w"] * 10)], ["s"], {"W": WORDS}, window=4, limit=64, budget=4)
    assert rows[("s", "W")]["tokens"] == 10
    assert rows[("s", "W")]["context_resets"] == 2  # windows at 0, 4, 8
    assert rows[("s", "W")]["fitted_resets"] == 2


def test_measure_counts_and_conservation():
    rows, fitted = tu.measure([TEXT, "short"], ["s1", "s1"], {"A": WORDS, "B": SHORT}, window=6, limit=24)
    ra, rb = rows[("s1", "A")], rows[("s1", "B")]
    assert ra["docs"] == rb["docs"] == 2
    assert ra["raw_bytes"] == len(TEXT.encode()) + 5
    assert rb["tokens"] > ra["tokens"]
    assert rb["context_resets"] > ra["context_resets"]  # token windows depend on the tokenizer
    assert ra["fitted_tokens"] == ra["tokens"] and rb["fitted_tokens"] == rb["tokens"]
    assert ra["fitted_byte_conservation_failures"] == rb["fitted_byte_conservation_failures"] == 0
    assert len(fitted) == 2


def test_check_segmentation_catches_a_tokenizer_that_does_not_fit(tmp_path):
    docs = [{"id": "d1", "text": TEXT}]
    pieces = tu.fitted_segments(TEXT, [WORDS], budget=6)
    path = tmp_path / "seg.jsonl"
    rows = [{"kind": tu.SEGMENTATION_KIND, "budget": 6},
            {"id": "d1", "text_sha256": hashlib.sha256(TEXT.encode()).hexdigest(), "offsets": tu.offsets_of(pieces)}]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert tu.check_segmentation(path, docs, {"A": WORDS})[1] == []
    assert tu.check_segmentation(path, docs, {"C": CHARS})[1]  # one token per character does not fit
