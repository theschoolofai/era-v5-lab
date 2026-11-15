"""Tests for arrowtools.py: the shared pyarrow helpers by_part (cut a table by part) and batch_rows (rows per read
batch, from the footer).

  python -m pytest teams/01-data-a/pipeline/tests -q
"""
import random

import pyarrow as pa
import pyarrow.parquet as pq

import conftest  # noqa: F401  (the pipeline folder on sys.path)
import arrowtools as at


def test_by_part_cuts_at_every_key_change_in_sorted_order():
    rng = random.Random(1)
    rows = [(rng.choice(["train", "heldout"]), f"p{rng.randrange(300):03d}", i) for i in range(5000)]
    t = pa.table({"split": [r[0] for r in rows], "part": [r[1] for r in rows], "i": [r[2] for r in rows]})
    want = {}
    for split, part, i in rows:
        want.setdefault((split, part), []).append(i)
    got = at.by_part(t)
    assert list(got) == sorted(want) and {k: v["i"].to_pylist() for k, v in got.items()} == want


def test_by_part_keeps_rows_with_a_null_key_together():
    t = pa.table({"split": ["train"] * 5, "part": [None, "a", None, None, "b"], "v": [0, 1, 2, 3, 4]})
    got = {k: v["v"].to_pylist() for k, v in at.by_part(t).items()}
    assert got == {("train", "a"): [1], ("train", "b"): [4], ("train", None): [0, 2, 3]}


def test_batch_rows_is_sized_by_the_widest_row_group(tmp_path):
    f = tmp_path / "p.parquet"
    with pq.ParquetWriter(f, pa.schema([("id", pa.string()), ("text", pa.string())])) as w:
        w.write_table(pa.table({"id": [f"a{i}" for i in range(100)], "text": [f"{i:03d}" * 30 for i in range(100)]}))
        w.write_table(pa.table({"id": [f"b{i}" for i in range(10)], "text": [f"{i}" * 20_000 for i in range(10)]}))
    with at.opened(f) as pf:
        md = pf.metadata
        widest = max(md.row_group(i).total_byte_size / md.row_group(i).num_rows for i in range(md.num_row_groups))
        assert widest > 10_000  # the second group's 20 KB rows, not the average
        assert at.batch_rows(pf, 1 << 20, 8192) == int((1 << 20) // widest)
        assert at.batch_rows(pf, 1 << 40, 8192) == 8192 and at.batch_rows(pf, 1, 8192) == 1
        assert at.batch_rows(pf, 1 << 20, 8192, ["id"]) == 8192  # the ids alone are small
    e = tmp_path / "empty.parquet"
    pq.write_table(pa.table({"id": pa.array([], pa.string())}), e)
    with at.opened(e) as pf:
        assert at.batch_rows(pf, 1 << 20, 8192) == 8192


# --- Vijay's review of PR #46 (15 Nov) -------------------------------------------------------------------------------
def rows_of(batches):
    return [r for b in batches for r in b.column(0).to_pylist()]


def test_iter_sized_gives_every_row_once_in_order(tmp_path):
    """Small rows, then the same long text repeated (dictionary-encoded: tiny in the footer), then distinct long rows."""
    f = tmp_path / "p.parquet"
    small = [f"s{i}" for i in range(300)]
    same = ["x" * 50_000] * 200
    long_ = [f"{i:05d}" * 10_000 for i in range(50)]
    ids = list(range(550))
    with pq.ParquetWriter(f, pa.schema([("text", pa.string()), ("id", pa.int64())])) as w:
        for chunk, start in ((small, 0), (same, 300), (long_, 500)):
            w.write_table(pa.table({"text": chunk, "id": ids[start:start + len(chunk)]}), row_group_size=64)
    target = 256 << 10
    with at.opened(f) as pf:
        batches = list(at.iter_sized(pf, target, 1024))
    assert [i for b in batches for i in b.column(1).to_pylist()] == ids
    assert rows_of(batches) == small + same + long_
    over = [b.nbytes for b in batches if b.nbytes > 2 * target + 50_000]
    assert len(over) <= 1  # one read at the old size when the rows jump to 50 KB, then reads shrink
    with at.opened(f) as pf:
        assert [i for b in at.iter_sized(pf, target, 1024, ["id"]) for i in b.column(0).to_pylist()] == ids


def test_iter_sized_on_an_empty_file_and_a_single_row_group(tmp_path):
    e = tmp_path / "e.parquet"
    pq.write_table(pa.table({"text": pa.array([], pa.string())}), e)
    with at.opened(e) as pf:
        assert list(at.iter_sized(pf, 1 << 20, 1024)) == []
    one = tmp_path / "one.parquet"
    pq.write_table(pa.table({"text": [f"t{i}" for i in range(5000)]}), one, row_group_size=5000)
    with at.opened(one) as pf:
        batches = list(at.iter_sized(pf, 1 << 20, 1024))
    assert rows_of(batches) == [f"t{i}" for i in range(5000)] and max(b.num_rows for b in batches) <= 1024
    assert batches[0].num_rows == 16  # the first read is small: decoded sizes are not known before it
