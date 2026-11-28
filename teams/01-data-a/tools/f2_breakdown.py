"""Where F2's time goes on one part (B7): set load, parquet read, the check, and the write of the kept docs.

  python -s teams/01-data-a/tools/f2_breakdown.py <part.parquet> <out.parquet> [--profile]

Uses run_f2.py's own fingerprints() (the pinned set) and G9's Fingerprints.check, unchanged, one process, one thread.
Without --profile the times are plain wall times. With --profile the check also runs under cProfile and the top
functions by own time are printed (cProfile makes the check about 2.5 times slower; use its shares, not its seconds).
"""
import argparse, cProfile, importlib.util, io, pstats, time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("run_f2", REPO / "teams/01-data-a/spec_v1/run_f2.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

ap = argparse.ArgumentParser()
ap.add_argument("part", type=Path); ap.add_argument("out", type=Path); ap.add_argument("--profile", action="store_true")
a = ap.parse_args()
t0 = time.time(); fp = F.fingerprints(); t_load = time.time() - t0
t0 = time.time(); tab = pq.read_table(a.part); t_read = time.time() - t0
texts = tab.column("text").to_pylist()
nbytes = sum(len(t.encode()) for t in texts)
pr = cProfile.Profile() if a.profile else None
t0 = time.time()
if pr: pr.enable()
keep = [not fp.check(t, 1)[0] for t in texts]
if pr: pr.disable()
t_check = time.time() - t0
t0 = time.time(); pq.write_table(tab.filter(pa.array(keep)), a.out); t_write = time.time() - t0
total = t_read + t_check + t_write
print(f"part {a.part.parent.parent.name}/{a.part.parent.name}/{a.part.name}: docs {len(texts):,}, text {nbytes/1e6:.0f} MB, "
      f"kept {sum(keep):,}")
print(f"set load {t_load:.1f} s | read {t_read:.2f} s | check {t_check:.1f} s ({nbytes/1e6/t_check:.2f} MB/s) | "
      f"write {t_write:.2f} s | read + write = {100*(t_read+t_write)/total:.2f}% of read + check + write"
      + (" (check under cProfile)" if pr else ""))
if pr:
    s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(8)
    print("\n".join(s.getvalue().splitlines()[:20]))
