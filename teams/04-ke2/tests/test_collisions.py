"""Collision audit: every collision group is real, counted right, and has a known cause.

Exact counts are pinned only for BrahmicTokenizer-131K (BRAHMIC_SHA256 below);
everything else is a property that must hold for any byte-level tokenizer.
"""

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "collisions"))

import build_collisions as bc

import build_tables as bt
from ke2.script_class import BRAHMIC_BLOCKS

# Aliases: pr-guard's email check misreads dotted pytest decorators as addresses.
fixture = pytest.fixture
parametrize = pytest.mark.parametrize

# Counts below are pinned to this exact tokenizer.json; on any other tokenizer they are skipped.
BRAHMIC_SHA256 = "01d968a7970b029c071b29f060abf6104b66168dedf2ff3b1a0290a545739fff"


@fixture(scope="session")
def is_brahmic(tb):
    return tb.sha256 == BRAHMIC_SHA256


@fixture(scope="module")
def audit(tb, tables):
    return bc.audit(tb, tables)


def _groups(audit, kind, P):
    return [g for g in audit.groups if g.extraction == kind and g.P == P]


# --------------------------------------------------------------------------- #
# label_cause: pure-function cases (no tokenizer needed)
# --------------------------------------------------------------------------- #
FFFD = bt.U_FFFD


@parametrize(
    "true, untrunc, row, special, expected",
    [
        ([b"", b""], [b"", b""], b"", [False, False], "empty"),
        ([b"ab", b"ab"], [b"ab", b"ab"], b"ab", [False, False], "duplicate_vocab"),
        ([b"<s>", b"<s>"], [b"<s>", b"<s>"], b"<s>", [True, False], "special_literal"),
        ([b"\xe0\xa4", b"\xe0\xa5"], [FFFD, FFFD], FFFD, [False, False], "decode_collapse"),
        ([b"\xe0\xa4", FFFD], [FFFD, FFFD], FFFD, [False, False], "decode_collapse"),
        (
            [b"x" * 40 + b"1", b"x" * 40 + b"2"],
            [b"x" * 40 + b"1", b"x" * 40 + b"2"],
            b"x" * 32,
            [False, False],
            "truncation",
        ),
        ([b"a", b"b"], [b"z", b"z"], b"z", [False, False], "other"),
    ],
)
def test_label_cause(true, untrunc, row, special, expected):
    assert bc.label_cause(true, untrunc, row, special) == expected


# --------------------------------------------------------------------------- #
# Properties on the real tables
# --------------------------------------------------------------------------- #
def test_gate_zero_other(audit):
    others = [(g.extraction, g.P, g.ids[:5]) for g in audit.groups if g.cause == "other"]
    assert not others, f"groups with no known cause: {others}"


def test_every_group_is_a_real_collision(audit, tables):
    for g in audit.groups:
        t = tables[g.extraction, g.P]
        assert len(g.ids) >= 2
        assert all(t.row(i) == g.row for i in g.ids)


def test_groups_cover_exactly_the_non_unique_rows(audit, tables):
    """Independent recount: tokens whose row appears more than once == tokens in groups."""
    for (kind, P), t in tables.items():
        rows = [t.row(i) for i in range(t.vocab_size)]
        counts = {}
        for r in rows:
            counts[r] = counts.get(r, 0) + 1
        expected = {i for i, r in enumerate(rows) if counts[r] > 1}
        got = {i for g in _groups(audit, kind, P) for i in g.ids}
        assert got == expected, (kind, P)
        # no token in two groups
        assert sum(len(g.ids) for g in _groups(audit, kind, P)) == len(got)


@parametrize("P", bt.POS_DIMS)
def test_raw_table_collides_only_by_truncation(audit, tb, P):
    """Raw extraction is exact, so the only way two rows can match is cutting to P."""
    gs = _groups(audit, "raw", P)
    assert {g.cause for g in gs} <= {"truncation"}
    max_len = max(len(bt.raw_bytes_for_id(tb, i)) for i in range(tb.vocab_size))
    if max_len <= P:
        assert gs == [], "no token exceeds P, so the raw table must be collision-free"


def test_decode_groups_have_expected_causes(audit):
    for P in bt.POS_DIMS:
        causes = {g.cause for g in _groups(audit, "decode", P)}
        assert causes <= {"decode_collapse", "truncation"}, causes


def test_summary_matches_groups(audit):
    for P in bt.POS_DIMS:
        for kind in ("raw", "decode"):
            rows = [r for r in audit.summary if r["extraction"] == kind and r["P"] == P]
            gs = _groups(audit, kind, P)
            assert sum(r["n_tokens"] for r in rows) == audit.vocab_size
            assert sum(r["n_colliding_tokens"] for r in rows) == sum(len(g.ids) for g in gs)
            assert sum(r["n_excess_tokens"] for r in rows) == sum(len(g.ids) - 1 for g in gs)


def test_pinned_counts_brahmic(audit, is_brahmic):
    if not is_brahmic:
        pytest.skip("counts pinned for BrahmicTokenizer-131K only")
    for P in bt.POS_DIMS:
        assert _groups(audit, "raw", P) == []
        gs = _groups(audit, "decode", P)
        assert len(gs) == 10
        assert sum(len(g.ids) for g in gs) == 1151
        assert sum(len(g.ids) - 1 for g in gs) == 1141  # == test_tables' V - unique
        assert max(len(g.ids) for g in gs) == 658
        assert {g.cause for g in gs} == {"decode_collapse"}


_NEUTRAL_LETTER_PREFIXES = ("MODIFIER", "COMBINING", "MASCULINE", "FEMININE")


def _letter_scripts(text: str) -> set:
    """Writing systems of the *letters* in text. Digits, punctuation, symbols,
    modifier letters (e.g. Hawaiian okina), ordinal indicators and combining
    marks are script-neutral (Unicode Common/Inherited) and ignored."""
    import unicodedata

    out = set()
    for ch in text:
        if unicodedata.category(ch)[0] not in "LM":
            continue
        cp = ord(ch)
        brahmic = next((n for n, (lo, hi) in BRAHMIC_BLOCKS.items() if lo <= cp <= hi), None)
        if brahmic:
            out.add(brahmic)
            continue
        name = unicodedata.name(ch, "")
        if not name or name.startswith(_NEUTRAL_LETTER_PREFIXES):
            continue
        out.add(name.split()[0])
    return out


def test_no_cross_script_tokens_brahmic(tb, is_brahmic):
    """Model card: zero tokens spanning two writing systems.

    Note: build_tables' "Mixed" class is broader (any two character classes,
    e.g. Latin + digits "2nd"), so it is NOT used for this check.
    """
    if not is_brahmic:
        pytest.skip("model-card claim is about BrahmicTokenizer-131K")
    cross = []
    for i in range(tb.vocab_size):
        b = bt.raw_bytes_for_id(tb, i)
        try:
            s = b.decode("utf-8")
        except UnicodeDecodeError:
            continue  # fragments carry part of one character: cannot span two scripts
        if len(_letter_scripts(s)) > 1:
            cross.append((i, s))
    assert cross == [], f"{len(cross)} cross-script tokens, e.g. {cross[:10]}"


def test_letter_scripts_helper():
    assert _letter_scripts("ʻole") == {"LATIN"}
    assert _letter_scripts(" Nº") == {"LATIN"}
    assert _letter_scripts("भारत।") == {"Devanagari"}
    assert _letter_scripts("2nd") == {"LATIN"}
    assert _letter_scripts("abc भारत") == {"LATIN", "Devanagari"}


# --------------------------------------------------------------------------- #
# Output files
# --------------------------------------------------------------------------- #
def test_csv_roundtrip(tmp_path, audit, tb):
    meta = bc.write_outputs(audit, tb, tmp_path)
    with open(tmp_path / "collisions.csv") as f:
        r = csv.DictReader(f)
        assert r.fieldnames == bc.GROUP_COLUMNS
        rows = list(r)
    assert len(rows) == len(audit.groups)
    for row, g in zip(rows, audit.groups, strict=True):
        assert [int(x) for x in row["token_ids"].split(";")] == g.ids
        assert bytes.fromhex(row["bytes_hex"]) == g.row
        assert row["cause"] in bc.CAUSES
    with open(tmp_path / "collisions_summary.csv") as f:
        r = csv.DictReader(f)
        assert r.fieldnames == bc.SUMMARY_COLUMNS
        assert len(list(r)) == len(audit.summary)
    assert meta["gate_zero_other"] is True
    assert meta["tokenizer_sha256"] == tb.sha256


def test_committed_csv_is_current(audit, tb):
    """If results are committed, they must match a fresh recompute for this tokenizer."""
    p = bc.RESULTS / "collisions.csv"
    meta_p = bc.RESULTS / "collisions_meta.json"
    if not p.exists() or not meta_p.exists():
        pytest.skip("no committed results")
    import json

    if json.loads(meta_p.read_text())["tokenizer_sha256"] != tb.sha256:
        pytest.skip("committed results are for a different tokenizer")
    with open(p) as f:
        committed = list(csv.DictReader(f))
    fresh = [{k: str(v) for k, v in r.items()} for r in bc.group_rows(audit, tb)]
    assert committed == fresh


# --------------------------------------------------------------------------- #
# Cross-checks
# --------------------------------------------------------------------------- #
def test_inspect_tokenizer_agrees_with_build_tables(tb):
    """Two independent byte extractions must give identical bytes for every ID."""
    transformers = pytest.importorskip("transformers")
    import inspect_tokenizer as it

    hf = transformers.PreTrainedTokenizerFast(tokenizer_file=str(tb.path))
    V, raw, _kind, _ = it.build_raw_table(hf)
    assert tb.vocab_size == V
    diff = [i for i in range(V) if raw[i] != bt.raw_bytes_for_id(tb, i)]
    assert diff == [], f"{len(diff)} IDs differ, e.g. {diff[:10]}"


SAMPLES = [
    "भारत एक देश है",  # Hindi (model-card example)
    "আমি বাংলায় গান গাই",  # Bengali
    "தமிழ் ஒரு மொழி",  # Tamil
    "తెలుగు భాష",  # Telugu
    "ಕನ್ನಡ ನಾಡು",  # Kannada
    "മലയാളം",  # Malayalam
    "ਪੰਜਾਬੀ ਬੋਲੀ",  # Gurmukhi
    "ગુજરાતી ભાષા",  # Gujarati
    "ଓଡ଼ିଆ ଭାଷା",  # Oriya
    "The quick brown fox, 1234567890.",
    "def f(x):\n    return x + 1  # ok\n",
    "naïve café — “quotes” …",
    "emoji 🙂👍🏽 and 漢字 kept as bytes",
    "मिश्रित text with English और हिन्दी",
]


@parametrize("text", SAMPLES)
def test_raw_rows_concatenate_back_to_text(tb, raw32, text):
    """Brief: token bytes must concatenate back to the original text."""
    ids = tb.tok.encode(text, add_special_tokens=False).ids
    assert b"".join(raw32.row(i) for i in ids) == text.encode("utf-8")
