"""perfkit/packing.py (Lab 5 design 3): the row builders of every arm score the same targets, and the packed rows
carry the document ids and positions the mask needs, in both row formats (#890 and the bring-up stream)."""
from collections import Counter

import numpy as np
import pytest

from models.gpt import IGNORE_INDEX
from perfkit.packing import (arm_rows, doc_windows, one_window_rows, packed_rows, pool_rows, window_fill,
                             window_rows)

T = 8
BOS = 999
DOCS = [np.arange(100, 105), np.arange(200, 219), np.arange(300, 303), np.arange(400, 412)]   # 5, 19, 3, 12 tokens


def _scored(rows):
    """Counter of (input token, target) pairs over all rows: every next-token prediction the arm scores."""
    c = Counter()
    for x, y, *_ in rows:
        for a, b in zip(x, y):
            if b != IGNORE_INDEX:
                c[(int(a), int(b))] += 1
    return c


# ------------------------------------------------------------------------------ #890 format
def test_doc_windows_follow_the_g5_rule():
    w = doc_windows(DOCS, T, BOS)
    assert len(w) == 1 + 3 + 1 + 2                    # ceil(n / T) windows per document
    assert list(w[0][0]) == [BOS, 100, 101, 102, 103] and list(w[0][1]) == [100, 101, 102, 103, 104]
    assert w[2][0][0] == 207 and w[2][1][0] == 208    # a later window starts from the token before it
    assert sum(len(t) for _, t in w) == sum(len(d) for d in DOCS)   # every token a target once


def test_890_arms_score_the_same_targets():
    fmt = {"rows": "890", "bos": BOS, "data_seed": 3, "pool": 4}
    want = _scored(arm_rows("window", fmt, DOCS, T))
    assert sum(want.values()) == sum(len(d) for d in DOCS)
    assert _scored(arm_rows("packed_mask", fmt, DOCS, T)) == want
    assert _scored(arm_rows("packed_nomask", fmt, DOCS, T)) == want


def test_pool_rows_format_and_best_fit():
    # windows w0..w6, target sizes 5, 8, 8, 3, 3, 8, 4 (doc 1 is w1-w3, doc 3 is w5-w6). Pool of 4, hand-traced:
    # row 0: pool [w0 w1 w2 w3] -> w1 (largest, earliest of the two 8s); row 1: [w0 w2 w3 w4] -> w2;
    # row 2: [w0 w3 w4 w5] -> w5; row 3: [w0 w3 w4 w6] -> w0, then w3 (3 left, earliest 3); row 4: [w4 w6] -> w6, w4.
    w = doc_windows(DOCS, T, BOS)
    rows = list(pool_rows(w, range(len(w)), T, pad=0, pool=4))
    assert len(rows) == 5 and sum(int(d.max()) for _, _, d, _ in rows) == len(w)   # one pass: each window once
    assert [list(y[:2]) for _, y, _, _ in rows[:3]] == [[200, 201], [208, 209], [400, 401]]
    x, y, d, p = rows[3]
    assert d.dtype == np.int32 and p.dtype == np.int32
    assert list(x) == [BOS, 100, 101, 102, 103, 215, 216, 217]
    assert list(y) == [100, 101, 102, 103, 104, 216, 217, 218]
    assert list(d) == [1] * 5 + [2] * 3 and list(p) == [0, 1, 2, 3, 4, 0, 1, 2]
    x, y, d, p = rows[4]                              # padding only at the end: doc id 0, target IGNORE
    assert list(x[:7]) == [407, 408, 409, 410, BOS, 300, 301] and list(y[:7]) == [408, 409, 410, 411, 300, 301, 302]
    assert list(d) == [1, 1, 1, 1, 2, 2, 2, 0] and list(p) == [0, 1, 2, 3, 0, 1, 2, 0] and y[7] == IGNORE_INDEX


def test_pool_of_one_is_strict_order():
    w = doc_windows(DOCS, T, BOS)
    rows = list(pool_rows(w, range(len(w)), T, pad=0, pool=1))
    got = [list(y[y != IGNORE_INDEX]) for _, y, _, _ in rows]
    flat = [int(v) for r in got for v in r]
    assert flat == [int(v) for _, t in w for v in t]   # the windows in order, none skipped or reordered


def test_window_fill_formats():
    n = np.array([len(d) for d in DOCS])
    assert window_fill(DOCS, T, bos=True) == pytest.approx(n.sum() / (np.ceil(n / T).sum() * T))
    assert window_fill(DOCS, T, bos=False) == pytest.approx((n - 1).sum() / (np.ceil((n - 1) / T).sum() * T))


# ------------------------------------------------------------------------------ bring-up (stream) format
def test_stream_every_arm_scores_each_in_document_next_token_once():
    want = Counter((int(d[i]), int(d[i + 1])) for d in DOCS for i in range(len(d) - 1))
    assert _scored(window_rows(DOCS, T, pad=0)) == want
    owner = np.concatenate([np.full(len(d), k) for k, d in enumerate(DOCS)])
    got = _scored(packed_rows(DOCS, T))
    covered = (len(owner) - 1) // T * T               # the packed stream drops the tail that does not fill a row
    assert sum(got.values()) == int((owner[1:covered + 1] == owner[:covered]).sum())
    assert not (got - want)                           # nothing scored across a document boundary


def test_stream_window_rows_pad_and_fill():
    rows = list(window_rows(DOCS, T, pad=0))
    assert len(rows) == 1 + 3 + 1 + 2                 # ceil((n - 1) / T) windows per document
    x, y, d, p = rows[0]
    assert d is None and p is None and list(x[:4]) == list(range(100, 104)) and list(x[4:]) == [0, 0, 0, 0]
    assert list(y[:4]) == list(range(101, 105)) and all(v == IGNORE_INDEX for v in y[4:])


def test_stream_packed_rows_doc_ids_and_boundary_targets():
    x, y, d, p = next(packed_rows(DOCS, T))
    assert list(x) == [100, 101, 102, 103, 104, 200, 201, 202]
    assert list(d) == [0, 0, 0, 0, 0, 1, 1, 1] and p is None
    assert y[4] == IGNORE_INDEX and y[3] == 104 and y[5] == 201
    x2, _, d2, _ = list(packed_rows(DOCS, T))[1]
    assert x2[0] == 203 and d2[0] == 0                # the next row starts at token T and renumbers from 0


def test_one_window_rows_padding():
    w = doc_windows(DOCS, T, BOS)
    x, y, d, p = next(one_window_rows(w, [0], T, pad=0))
    assert d is None and p is None and list(x[5:]) == [0, 0, 0] and all(v == IGNORE_INDEX for v in y[5:])
