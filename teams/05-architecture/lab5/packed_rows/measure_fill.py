"""Rows and fill per pass: today's one window per row against the packed loader (run.pack).

Reads only shard .idx.npy document offsets (no token ids, no text). Windows are cut exactly as
week2/data.py cuts them (at most L targets per window): today without EOS (the unpacked trainer does
not train on it); packed with each document's EOS as its last target (#890, D3: A), so a packed
document is one token longer and its EOS counts as a scored token. Windows are shuffled with a fixed
seed, then placed into rows. Packed (the loader's rule, BatchStream.next_packed): each row takes the
largest of the next 16 windows that still fits, until none fits; no window is cut. The strict-order
column places windows only in order (a window that does not fit opens a new row) and shows why the
pool is there.

    python teams/05-architecture/lab5/packed_rows/measure_fill.py \
        --index code-python-train-000000.idx.npy en-fineweb-edu-train-000000.idx.npy --windows 2048 4096
"""

import argparse
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness"))
from packing_fill import document_lengths  # noqa: E402


def windows(lengths, L):
    """Window sizes for every document, as week2/data.py cuts them."""
    full = lengths // L
    rest = lengths % L
    sizes = np.repeat(np.full(len(lengths), L), full)
    return np.concatenate([sizes, rest[rest > 0]])


def in_order_rows(sizes, L):
    """Rows needed when windows are placed strictly in order (a window that does not fit opens a row)."""
    rows, used = 0, L  # start "full" so the first window opens row 1
    for n in sizes.tolist():
        if used + n > L:
            rows += 1
            used = 0
        used += n
    return rows


def packed_rows(sizes, L, pool=16):
    """Rows needed with the loader's rule (BatchStream.next_packed): best fit from the next `pool` windows."""
    upcoming = iter(sizes.tolist())
    held, rows = [], 0

    def refill():
        while len(held) < pool:
            n = next(upcoming, None)
            if n is None:
                return
            held.append(n)

    refill()
    while held:
        rows += 1
        left = L
        while True:
            fits = [i for i, n in enumerate(held) if n <= left]
            if not fits:
                break
            i = max(fits, key=lambda j: (held[j], -j))
            left -= held.pop(i)
            refill()
    return rows


def pool_sweep(lengths, Ls, seed, pools):
    """Fill packed for each pool size (run.pack_pool); a pool of 1 is strict order."""
    stored = lengths + 1                      # packed documents end with EOS (#890, D3: A)
    content = int(stored.sum())
    rng = np.random.default_rng(seed)
    head = "| Pool | " + " | ".join(f"Fill at {L:,}" for L in Ls) + " |"
    lines = [head, "|---:|" + "---:|" * len(Ls)]
    orders = {L: rng.permutation(windows(stored, L)) for L in Ls}
    for pool in pools:
        cells = [f"{content / (packed_rows(orders[L], L, pool) * L):.1%}" for L in Ls]
        lines.append(f"| {pool} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def report(lengths, Ls, seed):
    content = int(lengths.sum())
    stored = lengths + 1                      # packed documents end with EOS (#890, D3: A)
    packed_content = int(stored.sum())
    rng = np.random.default_rng(seed)
    lines = ["| Window | Rows today | Rows packed (loader) | Fill today | Fill in strict order | Fill packed (loader) | Packed / today |",
             "|---:|---:|---:|---:|---:|---:|---:|"]
    for L in Ls:
        today = len(windows(lengths, L))
        order = rng.permutation(windows(stored, L))
        strict = in_order_rows(order, L)
        packed = packed_rows(order, L)
        lines.append(
            f"| {L:,} | {today:,} | {packed:,} | {content / (today * L):.1%} | "
            f"{packed_content / (strict * L):.1%} | {packed_content / (packed * L):.1%} | {packed / today:.2f}x |"
        )
    return (f"Documents: {len(lengths):,}; content tokens: {content:,} (packed, with each document's EOS: "
            f"{packed_content:,}); window order shuffled with seed {seed}.\n\n"
            + "\n".join(lines))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--index", nargs="+", required=True, help="shard .idx.npy files")
    p.add_argument("--windows", nargs="+", type=int, default=[2048, 4096])
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--pool", nargs="*", type=int, default=[],
                   help="also print fill for these pool sizes (run.pack_pool), e.g. 1 4 8 16 32 64")
    a = p.parse_args()
    lengths = document_lengths([Path(x) for x in a.index])
    print(report(lengths, a.windows, a.seed))
    if a.pool:
        print()
        print(pool_sweep(lengths, a.windows, a.seed, a.pool))


if __name__ == "__main__":
    main()
