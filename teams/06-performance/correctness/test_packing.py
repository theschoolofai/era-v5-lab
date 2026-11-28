"""perfkit/packing.py (Lab 5 design 3): the three row builders score the same targets, and the packed rows carry the
document ids the mask needs."""
from collections import Counter

import numpy as np

from models.gpt import IGNORE_INDEX
from perfkit.packing import packed_rows, window_rows

T = 8
DOCS = [np.arange(100, 105), np.arange(200, 219), np.arange(300, 303), np.arange(400, 412)]   # 5, 19, 3, 12 tokens


def _scored(rows):
    """Counter of (input token, target) pairs over all rows: every next-token prediction the arm scores."""
    c = Counter()
    for x, y, _ in rows:
        for a, b in zip(x, y):
            if b != IGNORE_INDEX:
                c[(int(a), int(b))] += 1
    return c


def test_every_arm_scores_each_in_document_next_token_once():
    want = Counter((int(d[i]), int(d[i + 1])) for d in DOCS for i in range(len(d) - 1))
    assert _scored(window_rows(DOCS, T, pad=0)) == want
    owner = np.concatenate([np.full(len(d), k) for k, d in enumerate(DOCS)])
    got = _scored(packed_rows(DOCS, T))
    covered = (len(owner) - 1) // T * T               # the packed stream drops the tail that does not fill a row
    assert sum(got.values()) == int((owner[1:covered + 1] == owner[:covered]).sum())
    assert not (got - want)                           # nothing scored across a document boundary


def test_window_rows_pad_and_fill():
    rows = list(window_rows(DOCS, T, pad=0))
    assert len(rows) == 1 + 3 + 1 + 2                 # ceil((n - 1) / T) windows per document
    x, y, d = rows[0]
    assert d is None and list(x[:4]) == list(range(100, 104)) and list(x[4:]) == [0, 0, 0, 0]   # last token: no target
    assert list(y[:4]) == list(range(101, 105)) and all(v == IGNORE_INDEX for v in y[4:])


def test_packed_rows_doc_ids_and_boundary_targets():
    x, y, d = next(packed_rows(DOCS, T))
    assert list(x) == [100, 101, 102, 103, 104, 200, 201, 202]
    assert list(d) == [0, 0, 0, 0, 0, 1, 1, 1]
    assert y[4] == IGNORE_INDEX and y[3] == 104 and y[5] == 201
    x2, _, d2 = list(packed_rows(DOCS, T))[1]
    assert x2[0] == 203 and d2[0] == 0                # the next row starts at token T and renumbers from 0
