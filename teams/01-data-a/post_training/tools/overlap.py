"""Pairwise exact overlap of normalised questions (lowercase, whitespace collapsed; sha1 of it) between pools."""
import sys, itertools
from pathlib import Path
import pyarrow.parquet as pq
P = Path.home() / "Workspace/era-v5-data/g1-pt/pools"
sets = {k: set(pq.read_table(P / k / "docs.parquet", columns=["norm_key_sha1"]).column(0).to_pylist()) for k in sys.argv[1:]}
print("unique questions:", {k: len(v) for k, v in sets.items()})
for a, b in itertools.combinations(sets, 2):
    n = len(sets[a] & sets[b])
    if n: print(f"  {a:11} & {b:11}: {n:6}  ({n/len(sets[a]):.1%} of {a}, {n/len(sets[b]):.1%} of {b})")
