"""Lemma 1: the codec is injective on byte strings of length at most P (proof.md)."""

import math
import random

import torch

from forward import code_digest, codes, expected_values, read_support

PS = (32, 64)
DTYPES = (torch.float32, torch.bfloat16)


def rand_bytes(rng, L):
    return bytes(rng.randrange(256) for _ in range(L))


def test_code_has_exactly_two_values_in_fp32_and_bf16():
    rng = random.Random(0)
    for P in PS:
        for L in range(1, P + 1):
            for _ in range(3):
                s = rand_bytes(rng, L)
                for dtype in DTYPES:
                    z = codes([s], P, dtype)[0]
                    assert len(torch.unique(z)) == 2, (P, L, dtype)


def test_two_values_match_the_closed_form():
    rng = random.Random(1)
    for P in PS:
        for L in range(1, P + 1):
            z = codes([rand_bytes(rng, L)], P)[0]
            hi, lo = expected_values(L, P)
            assert math.isclose(float(z.max()), hi, rel_tol=1e-3), (P, L)
            assert math.isclose(float(z.min()), lo, rel_tol=1e-3), (P, L)


def test_gap_between_lit_and_unlit_survives_bf16():
    rng = random.Random(2)
    for P in PS:
        for L in range(1, P + 1):
            z = codes([rand_bytes(rng, L)], P, torch.bfloat16)[0].float()
            assert float(z.max() - z.min()) > 8.0, (P, L)


def test_bytes_read_back_from_the_code_edge_strings_and_random():
    rng = random.Random(3)
    for P in PS:
        strings = [b"\x00", b"\xff", b"a", b"\x00\x00", b"\x00" * P, b"\xff" * P, b"a" * P, bytes(range(P))]
        strings += [rand_bytes(rng, rng.randrange(1, P + 1)) for _ in range(3000)]
        for dtype in DTYPES:
            batch = codes(strings, P, dtype)
            for s, z in zip(strings, batch, strict=True):
                assert read_support(z, P) == s, (P, dtype, s)


def test_empty_string_is_the_zero_code_and_no_other_string_is():
    rng = random.Random(4)
    for P in PS:
        zero = codes([b""], P)[0]
        assert float(zero.abs().max()) == 0.0
        assert read_support(zero, P) == b""
        nonempty = codes([rand_bytes(rng, rng.randrange(1, P + 1)) for _ in range(200)], P)
        assert bool((nonempty.abs().amax(dim=1) > 0).all())


def test_distinct_strings_give_distinct_codes():
    rng = random.Random(5)
    for P in PS:
        pool = set()
        while len(pool) < 20000:
            L = rng.randrange(1, P + 1)
            s = rand_bytes(rng, L)
            pool.add(s)
            if len(s) >= 2:  # near neighbours: one byte changed, two bytes swapped, one byte added
                i = rng.randrange(len(s))
                pool.add(s[:i] + bytes([(s[i] + 1) % 256]) + s[i + 1 :])
                j = rng.randrange(len(s) - 1)
                pool.add(s[:j] + s[j + 1 : j + 2] + s[j : j + 1] + s[j + 2 :])
            if len(s) < P:
                pool.add(s + bytes([rng.randrange(256)]))
        strings = sorted(pool)
        for dtype in DTYPES:
            digests = set()
            for i in range(0, len(strings), 1000):
                digests.update(code_digest(z) for z in codes(strings[i : i + 1000], P, dtype))
            assert len(digests) == len(strings), (P, dtype, len(digests), len(strings))
