"""Small pyarrow helpers shared by the pipeline's scripts: whole columns at a time, never a Python loop over rows.

  const(value, n, type)              n copies of a value
  arange(n, start=0)                 start, start+1, ..., start+n-1 (int64)
  count(mask)                        how many True
  flat(arr)                          one Array from an Array or a ChunkedArray
  as_str(arr)                        the array as pa.string() (from large_string, dictionary, ...)
  opened(path, buffer_size=0)        a ParquetFile that is closed on leaving the with-block
  iter_sized(pf, target, most, cols)  the file's rows in batches of about `target` decoded bytes, sized as it reads
  batch_rows(pf, target, most, cols)  rows that hold about `target` bytes by the footer (an estimate only)
  read_columns(path, cols, error)    those columns of a Parquet file; `error` is raised when one is missing
  read_csv(path, header, types, error)   a CSV whose first line must be exactly `header`, typed as given
  posix(table, col)                  the column with \\ turned into /
  by_part(table, keys, count_col)    {key values: the rows of the table with them}, in key order
"""
import contextlib

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pcsv
import pyarrow.parquet as pq


def const(value, n, typ):
    """An array of n copies of value (no Python list of n items)."""
    return pa.repeat(pa.scalar(value, typ), n)


def arange(n, start=0):
    """start, start+1, ..., start+n-1 as int64."""
    if n == 0:
        return pa.array([], pa.int64())
    a = pc.subtract(pc.cumulative_sum(const(1, n, pa.int64())), 1)
    return pc.add(a, start) if start else a


def count(mask):
    """How many True in a boolean array (nulls count as False)."""
    return pc.sum(mask).as_py() or 0


def flat(arr):
    """One contiguous Array from an Array or a ChunkedArray (some compute functions take no ChunkedArray)."""
    if isinstance(arr, pa.ChunkedArray):
        return pa.concat_arrays(arr.chunks) if arr.num_chunks else pa.array([], arr.type)
    return arr


def as_str(arr):
    """The array as pa.string(): one type for joins and comparisons, whatever a file stored."""
    if pa.types.is_dictionary(arr.type):
        arr = arr.cast(arr.type.value_type)
    return arr.cast(pa.string()) if arr.type != pa.string() else arr


def opened(path, buffer_size=0):
    """A ParquetFile closed on leaving the with-block. Windows will not rename a hard link while another name of the same
    file is still open, and ParquetFile otherwise keeps its handle until garbage collection. buffer_size > 0 reads each
    column chunk through a buffer of that size instead of whole, so a part written as one huge row group is streamed."""
    pf = pq.ParquetFile(path, buffer_size=buffer_size)
    return contextlib.closing(pf) if hasattr(pf, "close") else contextlib.nullcontext(pf)


def _column_indices(md, columns):
    """The Parquet column indices of `columns` (all columns: None)."""
    if columns is None:
        return None
    wanted = set(columns)
    return [j for j in range(md.num_columns) if md.schema.column(j).path.split(".")[0] in wanted]


def _stored_per_row(rg, idx):
    """A row group's uncompressed stored bytes per row (of the columns idx, or of all): what the footer says."""
    size = rg.total_byte_size if idx is None else sum(rg.column(j).total_uncompressed_size for j in idx)
    return size / rg.num_rows if rg.num_rows else 0.0


def batch_rows(pf, target_bytes, most, columns=None):
    """Rows that hold about target_bytes by the footer: target_bytes over the widest row group's stored bytes per row,
    at least 1 and at most `most`. Only an estimate, for the writer's page size: dictionary-encoded repeated text
    decodes far larger than it is stored. Reads size their batches with iter_sized."""
    md = pf.metadata
    idx = _column_indices(md, columns)
    widest = max((_stored_per_row(md.row_group(i), idx) for i in range(md.num_row_groups)), default=0.0)
    return most if widest <= 0 else int(max(1, min(most, target_bytes // widest)))


def iter_sized(pf, target_bytes, most, columns=None, first=16):
    """pf's rows in file order, in batches of about target_bytes of decoded data, at most `most` rows each.

    The footer alone cannot size a read: a dictionary-encoded column of repeated text decodes far larger than it is
    stored (600 copies of one 200 KB text are stored in about 1.5 KB a row). So the first read is `first` rows, and
    every later one is sized from the most decoded bytes per row seen so far (or the footer's, if larger). One reader
    runs across row groups, and is replaced only when that size changes by more than half: after the first read, and
    when rows grow (the rest is then read from the row group it reached, skipping what was already given out). So a
    jump in row size costs at most one oversized read (at most `most` rows) before reads shrink."""
    import bisect
    md = pf.metadata
    n_groups = md.num_row_groups
    idx = _column_indices(md, columns)
    starts, total = [], 0
    for i in range(n_groups):
        starts.append(total)
        total += md.row_group(i).num_rows
    stored = max((_stored_per_row(md.row_group(i), idx) for i in range(n_groups)), default=0.0)
    pos, seen = 0, 0.0  # rows given out; the most decoded bytes per row so far

    def size(per_row):
        return most if per_row <= 0 else int(max(1, min(most, target_bytes // per_row)))

    while pos < total:
        b = min(size(max(seen, stored)), first) if seen == 0 else size(max(seen, stored))
        g = bisect.bisect_right(starts, pos) - 1
        skip, cut = pos - starts[g], False
        for batch in pf.iter_batches(batch_size=b, row_groups=list(range(g, n_groups)), columns=columns):
            if skip:  # rows of this row group already given out before the reader was replaced
                if skip >= batch.num_rows:
                    skip -= batch.num_rows
                    continue
                batch, skip = batch.slice(skip), 0
            if not batch.num_rows:
                continue
            seen = max(seen, batch.nbytes / batch.num_rows)
            pos += batch.num_rows
            yield batch
            want = size(max(seen, stored))
            if want < b / 2 or want > 2 * b:
                cut = True  # read the rest at the size the data showed
                break
        if not cut:
            break


def read_columns(path, columns, error=ValueError):
    """Only these columns of a Parquet file; `error(message)` is raised when one is missing."""
    with opened(path) as pf:
        missing = set(columns) - set(pf.schema_arrow.names)
        if missing:
            raise error(f"{path}: no {', '.join(sorted(missing))} column")
        return pf.read(columns=list(columns))


def read_csv(path, header, types, error=ValueError):
    """A CSV whose first line is exactly `header` (a list of names), with the given {name: pyarrow type} (others: string).
    No value is read as null; a quoted value may hold a newline. A wrong header or a malformed line raises `error`."""
    with open(path, encoding="utf-8", newline="") as f:
        first = f.readline().rstrip("\r\n")
    got = [c.strip('"') for c in first.split(",")] if first else None
    if got != header:
        raise error(f"{path}: header is {got}, expected {header}")
    convert = pcsv.ConvertOptions(column_types={c: types.get(c, pa.string()) for c in header},
                                  strings_can_be_null=False, quoted_strings_can_be_null=False, null_values=[])
    try:
        return pcsv.read_csv(path, read_options=pcsv.ReadOptions(block_size=1 << 24),
                             parse_options=pcsv.ParseOptions(newlines_in_values=True), convert_options=convert)
    except (pa.ArrowInvalid, pa.ArrowTypeError) as e:
        raise error(f"{path}: {e}") from None


def posix(table, col="part"):
    """The table with \\ replaced by / in column `col`, so a list written on Windows matches files on Linux and back."""
    i = table.schema.get_field_index(col)
    return table.set_column(i, col, pc.replace_substring(table.column(col), "\\", "/"))


def by_part(table, keys=("split", "part")):
    """{tuple of key values: the table's rows with those values}, in sorted key order. Sorts once, then cuts the sorted
    table where any key column changes value; the loop is over distinct keys (parts), never over rows. (Group order is
    taken from the sort, not from group_by, whose output order is not the order of first appearance.)"""
    n = table.num_rows
    if n == 0:
        return {}
    t = table.sort_by([(k, "ascending") for k in keys])
    if n == 1:
        starts = [0]
    else:
        change = None
        for k in keys:
            col = t.column(k)
            diff = pc.fill_null(pc.not_equal(col.slice(1), col.slice(0, n - 1)), False)  # two nulls: one group
            nulls = pc.xor(pc.is_null(col.slice(1)), pc.is_null(col.slice(0, n - 1)))  # null next to a value: a cut
            diff = pc.or_(diff, nulls)
            change = diff if change is None else pc.or_(change, diff)
        starts = [0] + [i + 1 for i in pc.indices_nonzero(change).to_pylist()]
    ends = starts[1:] + [n]
    heads = t.select(list(keys)).take(pa.array(starts, pa.int64())).to_pylist()
    return {tuple(h[k] for k in keys): t.slice(a, b - a) for h, a, b in zip(heads, starts, ends)}
