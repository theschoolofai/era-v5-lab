"""The vector steps of H3: nearest neighbours across two languages, and the sentence alignment that confirms a pair.
numpy only; the encoder is in h3.py. Every vector is a unit row, so a dot product is a cosine.

    python3 -B -m pytest dedup/tests/test_h3_align.py
"""
import numpy as np


def unit(m):
    """Rows scaled to length 1, as float32; a zero row stays zero."""
    m = np.asarray(m, dtype=np.float32)
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


def cross_topk(A, B, k, block=128, check=None):
    """Nearest neighbours across two sets of unit rows, by exact cosine.

    Returns (i, j, cosine, side) for every pair in the union of each A row's k best B rows and each B row's k best A
    rows, sorted by (i, j). side is 1 when the pair is only in A's list, 2 when only in B's, 3 when in both (mutual).
    One pass over A in blocks of rows: A's lists come from each block, B's are kept as running lists and merged block
    by block, so the full A x B matrix is never held. check() is called before each block (the time limit)."""
    A, B = np.asarray(A, dtype=np.float32), np.asarray(B, dtype=np.float32)
    nA, nB = len(A), len(B)
    if nA == 0 or nB == 0:
        e = np.zeros(0, np.int64)
        return e, e, np.zeros(0, np.float32), np.zeros(0, np.int8)
    kA, kB = min(k, nB), min(k, nA)
    BT = np.ascontiguousarray(B.T)
    best_val = np.full((nB, kB), -np.inf, np.float32)
    best_idx = np.full((nB, kB), -1, np.int64)
    ai, aj, av = [], [], []
    for lo in range(0, nA, block):
        if check:
            check()
        hi = min(lo + block, nA)
        S = A[lo:hi] @ BT                                         # (rows of the block) x nB
        idx = np.argpartition(S, nB - kA, axis=1)[:, nB - kA:]   # each row's kA largest
        ai.append(np.repeat(np.arange(lo, hi), kA))
        aj.append(idx.ravel())
        av.append(np.take_along_axis(S, idx, 1).ravel())
        kb = min(kB, hi - lo)
        cidx = np.argpartition(S, (hi - lo) - kb, axis=0)[(hi - lo) - kb:, :]   # each column's kb largest in the block
        vals = np.concatenate([best_val, np.take_along_axis(S, cidx, 0).T], axis=1)
        rows = np.concatenate([best_idx, (cidx + lo).T], axis=1)
        sel = np.argpartition(vals, vals.shape[1] - kB, axis=1)[:, vals.shape[1] - kB:]
        best_val, best_idx = np.take_along_axis(vals, sel, 1), np.take_along_axis(rows, sel, 1)
    a_i, a_j, a_v = np.concatenate(ai), np.concatenate(aj), np.concatenate(av)
    b_j, b_i, b_v = np.repeat(np.arange(nB), kB), best_idx.ravel(), best_val.ravel()
    key = np.concatenate([a_i * nB + a_j, b_i * nB + b_j])
    cos = np.concatenate([a_v, b_v])
    side = np.concatenate([np.full(len(a_i), 1, np.int8), np.full(len(b_i), 2, np.int8)])
    order = np.argsort(key, kind="stable")
    key, cos, side = key[order], cos[order], side[order]
    uniq, start = np.unique(key, return_index=True)
    return uniq // nB, uniq % nB, cos[start], np.bitwise_or.reduceat(side, start)


def align(SA, SB, threshold):
    """Sentence alignment of two documents from their sentence vectors: the sentence pairs that are each other's best
    match (mutual best, so one to one) with cosine >= threshold. Returns (aligned pairs, their mean cosine)."""
    if len(SA) == 0 or len(SB) == 0:
        return 0, 0.0
    S = np.asarray(SA, dtype=np.float32) @ np.asarray(SB, dtype=np.float32).T
    best_b, best_a = S.argmax(axis=1), S.argmax(axis=0)
    rows = np.arange(len(S))
    cos = S[rows, best_b]
    ok = (best_a[best_b] == rows) & (cos >= threshold)
    n = int(ok.sum())
    return n, (float(cos[ok].mean()) if n else 0.0)
