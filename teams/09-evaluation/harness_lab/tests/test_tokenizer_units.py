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
    spacey = toy(r"\S+|\s")                   # every space and newline its own token: worse on many short words
    short_words, long_words = "a b c d e f g h\n" * 3, "extraordinarily unbelievably\n" * 3
    assert tu.ntokens(spacey, short_words) > tu.ntokens(SHORT, short_words)
    assert tu.ntokens(SHORT, long_words) > tu.ntokens(spacey, long_words)
    # on each part, fitting to both gives the cuts of the tokenizer that binds there
    assert tu.fitted_segments(short_words, [spacey, SHORT], 20) == tu.fitted_segments(short_words, [spacey], 20)
    assert tu.fitted_segments(long_words, [spacey, SHORT], 20) == tu.fitted_segments(long_words, [SHORT], 20)
    both = tu.fitted_segments(short_words + long_words, [spacey, SHORT], 20)
    assert all(tu.ntokens(t, p) <= 20 for p in both for t in (spacey, SHORT))


def test_fitted_refuses_a_character_over_the_budget():
    with pytest.raises(ValueError):
        tu.fitted_segments("ab", [CHARS], budget=0)


def test_offsets_round_trip():
    pieces = tu.fitted_segments(TEXT, [WORDS], budget=6)
    assert tu.pieces_at(TEXT, tu.offsets_of(pieces)) == pieces


def test_token_window_resets_match_document_windows():
    # Mirrors Team 5's DocumentWindows (data.py: `for start in range(0, len(ids), seq_len)`), which needs torch and the
    # model artifacts to import: windows start at 0, seq_len, 2 seq_len, ..., so resets = windows - 1.
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


def test_check_segmentation_window_fails_budget_warns(tmp_path):
    docs = [{"id": "d1", "text": TEXT}]
    pieces = tu.fitted_segments(TEXT, [WORDS], budget=6)
    rows = [{"id": "d1", "text_sha256": hashlib.sha256(TEXT.encode()).hexdigest(), "offsets": tu.offsets_of(pieces)}]
    path = tmp_path / "seg.jsonl"
    header = {"kind": tu.SEGMENTATION_KIND, "window": 12, "budget": 6, "cuts_sha256": tu.cuts_sha256(rows)}
    path.write_text("".join(json.dumps(r) + "\n" for r in [header, *rows]))
    _, fail, warn = tu.check_segmentation(path, docs, {"S": SHORT})  # SHORT needs up to 10 tokens per piece
    assert fail == [] and warn
    _, fail, _ = tu.check_segmentation(path, docs, {"C": CHARS})     # one token per character: over the window
    assert fail


def write_seg(tmp_path, header, rows):
    path = tmp_path / "seg.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in [header, *rows]))
    return path


@pytest.mark.parametrize("problem", ["missing row", "unknown id", "eval sha", "bad offset", "cuts sha", "not a file"])
def test_check_segmentation_refuses_a_broken_file(tmp_path, problem):
    docs = [{"id": "d1", "text": "क ख ग"}, {"id": "d2", "text": TEXT}]
    rows = [{"id": d["id"], "text_sha256": hashlib.sha256(d["text"].encode()).hexdigest(), "offsets": []} for d in docs]
    header = {"kind": tu.SEGMENTATION_KIND, "window": 99, "budget": 99, "eval_file_sha256": "a" * 64}
    if problem == "missing row":
        rows = rows[1:]
    elif problem == "unknown id":
        rows.append({"id": "d9", "text_sha256": "0", "offsets": []})
    elif problem == "bad offset":
        rows[0]["offsets"] = [1]  # inside the 3-byte character क
    elif problem == "cuts sha":
        header["cuts_sha256"] = "0" * 64
    elif problem == "not a file":
        header["kind"] = "something-else"
    with pytest.raises(ValueError):
        tu.check_segmentation(write_seg(tmp_path, header, rows), docs, {"W": WORDS},
                              eval_file_sha256="b" * 64 if problem == "eval sha" else None)


def test_conservation_with_a_normalizing_tokenizer():
    from tokenizers import normalizers

    tok = toy(r" ?\S+")
    tok.normalizer = normalizers.Replace("\u09a1\u09bc", "\u09dc")  # Bengali DDA + NUKTA to RRA, as in p1536
    text = "\u09a1\u09bc\u09be " * 30
    rows, _ = tu.measure([text], ["bn"], {"N": tok}, window=8, limit=64, budget=8)
    r = rows[("bn", "N")]
    assert r["normalized_bytes"] < r["raw_bytes"] and r["docs_changed_by_normalizer"] == 1
    assert r["fitted_byte_conservation_failures"] == 0


def make_cli_inputs(tmp_path):
    texts = {"d1": TEXT, "d2": "short text", "d3": " ".join(["word"] * 40)}
    heldout, sources = tmp_path / "heldout.jsonl", tmp_path / "sources.jsonl"
    heldout.write_text("".join(json.dumps({"id": i, "text": t}) + "\n" for i, t in texts.items()))
    sources.write_text("".join(
        json.dumps({"id": i, "slice": "s", "text_sha256": hashlib.sha256(t.encode()).hexdigest()}) + "\n"
        for i, t in texts.items()))
    tok_path = tmp_path / "words" / "tokenizer.json"
    tok_path.parent.mkdir()
    WORDS.save(str(tok_path))
    chars_path = tmp_path / "chars.json"
    CHARS.save(str(chars_path))
    return heldout, sources, tok_path, chars_path


def test_cli_writes_counts_and_a_segmentation_file_that_checks(tmp_path):
    heldout, sources, tok_path, chars_path = make_cli_inputs(tmp_path)
    out, seg = tmp_path / "out.json", tmp_path / "seg.jsonl"
    base = ["--heldout", str(heldout), "--sources", str(sources), "--window", "10"]
    assert tu.main([*base, "--tokenizer", f"W={tok_path}", "--out", str(out), "--write-segmentation", str(seg)]) == 0
    counts = json.loads(out.read_text())
    assert str(tmp_path) not in counts["command"] and "W=<words>/tokenizer.json" in counts["command"]
    assert counts["budget"] == 8 and counts["totals"]["W"]["docs"] == 3
    header = json.loads(seg.read_text().splitlines()[0])
    assert header["window"] == 10 and header["budget"] == 8 and header["cuts_sha256"] == counts["cuts_sha256"]
    assert header["fitted_to"]["W"] == tu.sha256(tok_path)
    assert tu.main([*base, "--tokenizer", f"W={tok_path}", "--check-segmentation", str(seg)]) == 0
    assert tu.main([*base, "--tokenizer", f"C={chars_path}", "--check-segmentation", str(seg)]) == 1


@pytest.mark.parametrize("bad", [["--margin", "0"], ["--margin", "1.5"], ["--tokenizer", "no-equals-sign"]])
def test_cli_refuses_bad_arguments(tmp_path, bad):
    heldout, sources, tok_path, _ = make_cli_inputs(tmp_path)
    with pytest.raises(SystemExit):
        tu.main(["--heldout", str(heldout), "--sources", str(sources), "--tokenizer", f"W={tok_path}", *bad])


def test_cli_refuses_sources_that_do_not_match(tmp_path):
    heldout, sources, tok_path, _ = make_cli_inputs(tmp_path)
    lines = sources.read_text().splitlines()
    sources.write_text("\n".join(reversed(lines)) + "\n")
    with pytest.raises(ValueError):
        tu.main(["--heldout", str(heldout), "--sources", str(sources), "--tokenizer", f"W={tok_path}"])
