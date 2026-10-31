"""Lemma 2: the cut to P bytes (repository rule and our proposed variant) is a prefix, is bounded, and keeps whole UTF-8 letters (proof.md)."""

import random

from kronecker_embeddings.tokenizer_utils import utf8_safe_truncate

from forward import proposed_truncate, repo_truncate, truncate

PS = (32, 64)
CHARS = [*"aZ5-_ ", "é", "ñ", "ß", "ಕ", "ನ", "್", "ಡ", "ಾ", "ಿ", "ि", "र", "ा", "日", "本", "😀", "—", "‍"]


def is_valid(b: bytes) -> bool:
    try:
        b.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def random_valid(rng, max_chars=40):
    return "".join(rng.choice(CHARS) for _ in range(rng.randrange(1, max_chars))).encode("utf-8")


def random_raw(rng):
    """Arbitrary bytes, with many continuation bytes (0x80-0xBF) to stress the rule."""
    n = rng.randrange(0, 200)
    return bytes(rng.randrange(0x80, 0xC0) if rng.random() < 0.5 else rng.randrange(256) for _ in range(n))


def test_both_rules_prefix_identity_length_bounds_and_idempotence_on_raw_bytes():
    rng = random.Random(0)
    for P in PS:
        for _ in range(5000):
            raw = random_raw(rng)
            for rule in ("repo", "proposed"):
                t = truncate(raw, P, rule)
                assert raw.startswith(t)  # (a) prefix
                if len(raw) <= P:
                    assert t == raw  # (b) unchanged if it fits
                elif rule == "proposed" or t:
                    assert P - 3 <= len(t) <= P  # (c) loses at most 3 bytes
                assert truncate(t, P, rule) == t  # (e) idempotent


def test_valid_utf8_stays_valid_and_both_rules_agree():
    rng = random.Random(1)
    for P in PS:
        long_seen = 0
        for _ in range(5000):
            raw = random_valid(rng)
            t = repo_truncate(raw, P)
            assert is_valid(t)  # (d) no letter split
            assert t and t == proposed_truncate(raw, P) == utf8_safe_truncate(raw, P)
            long_seen += len(raw) > P
        assert long_seen > 500  # the test really exercises the cut


def test_repo_rule_cut_token_is_empty_or_valid_and_proposed_never_empties():
    rng = random.Random(2)
    for P in PS:
        emptied = 0
        for _ in range(5000):
            raw = random_raw(rng)
            t = repo_truncate(raw, P)
            if len(raw) > P:
                assert t == b"" or is_valid(t)  # a cut token is empty or valid UTF-8
            if raw:
                assert proposed_truncate(raw, P)  # Lemma 2 (c), proposed rule
                emptied += bool(t == b"") and len(raw) > P
        assert emptied > 500  # random bytes that are not UTF-8 really hit the repository's empty case


def test_example_stray_tail_byte_token_of_36_bytes():
    # 95 is the tail byte of some earlier letter, so no prefix is valid UTF-8.
    raw = b"\x95" + b"a" * 20 + "ಕನ್ನಡ".encode()
    assert len(raw) == 36
    assert repo_truncate(raw, 32) == b""  # all-zero code; such tokens collide
    t = proposed_truncate(raw, 32)
    assert len(t) == 30 and raw.startswith(t) and t.endswith("ಕನ್".encode())
    # If the first assertion fails one day, upstream changed the rule: update proof.md.
