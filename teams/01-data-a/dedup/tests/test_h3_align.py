"""Unit tests for h3_align.py, the vector steps of H3: the cross-language nearest neighbours, checked against a brute
force of every pair, and the sentence alignment. Every vector here is random or made up.

  python3 -B -m pytest dedup/tests/test_h3_align.py
"""
import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from h3_align import align, cross_topk, unit  # noqa: E402


def random_unit(n, d, seed):
    return unit(np.random.default_rng(seed).standard_normal((n, d)))


def brute_force(A, B, k):
    """Each A row's k best B rows (side 1) and each B row's k best A rows (side 2), from the full matrix."""
    S = A @ B.T
    sides = {}
    for i in range(len(A)):
        for j in np.argsort(-S[i])[:min(k, len(B))]:
            sides[(i, int(j))] = sides.get((i, int(j)), 0) | 1
    for j in range(len(B)):
        for i in np.argsort(-S[:, j])[:min(k, len(A))]:
            sides[(int(i), j)] = sides.get((int(i), j), 0) | 2
    return sides, S


@pytest.mark.parametrize("nA,nB,k,block", [(7, 11, 3, 2), (7, 11, 3, 3), (7, 11, 3, 100), (12, 5, 2, 4),
                                           (2, 1, 3, 1), (1, 6, 4, 8)])
def test_cross_topk_matches_brute_force(nA, nB, k, block):
    A, B = random_unit(nA, 6, 1), random_unit(nB, 6, 2)
    expected, S = brute_force(A, B, k)
    i, j, cos, side = cross_topk(A, B, k, block)
    got = {(int(x), int(y)): int(s) for x, y, s in zip(i, j, side)}
    assert got == expected
    assert np.allclose(cos, S[i, j], atol=1e-6)
    assert list(zip(i.tolist(), j.tolist())) == sorted(got)


def test_cross_topk_checks_the_time_limit_before_each_block():
    calls = []
    cross_topk(random_unit(10, 4, 3), random_unit(5, 4, 4), 2, block=3, check=lambda: calls.append(1))
    assert len(calls) == 4                                   # blocks of rows 0-2, 3-5, 6-8, 9


def test_cross_topk_empty_side():
    i, j, cos, side = cross_topk(np.zeros((0, 4)), random_unit(3, 4, 5), 2)
    assert len(i) == len(j) == len(cos) == len(side) == 0


def test_align_counts_mutual_best_matches_above_the_threshold():
    SA = random_unit(4, 16, 6)
    SB = SA[[2, 0, 3, 1]]                                    # the same sentences in another order
    n, mean = align(SA, SB, 0.7)
    assert n == 4 and mean == pytest.approx(1.0)
    assert align(SA, SB, 1.01) == (0, 0.0)


def test_align_is_one_to_one():
    SA = random_unit(3, 16, 7)
    n, _ = align(SA, SA[[0, 0]], 0.7)                        # both B sentences are A's first sentence
    assert n == 1


def test_align_empty():
    assert align(np.zeros((0, 4)), random_unit(2, 4, 8), 0.5) == (0, 0.0)


def test_unit_rows():
    m = unit([[3.0, 4.0], [0.0, 0.0]])
    assert np.allclose(m, [[0.6, 0.8], [0.0, 0.0]]) and m.dtype == np.float32
