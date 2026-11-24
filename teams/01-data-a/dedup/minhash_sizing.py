r"""Sizing check for minhash_overlap.py: measured time and RAM at 1x, 2x and 4x the sample on the staged data.

TSAI's bar (23 Nov 2026): measured time and RAM at 1x, 2x, 4x on the staged data, inside the job's 64 GiB / 720-minute
envelope. For each factor it takes whole staged parts, in a fixed order that interleaves the packs, until their rows
reach factor x the sample's cleaned documents (1,410,230, the 38-pack rehearsal #599), links them into a folder under
out/, runs minhash_overlap.py on them in a fresh output folder, and records wall time, peak RSS of the main process and
the largest worker, the peak of the summed RSS of the main process and every worker running at the same time
(peak_rss_total_gb: sampled every 0.5 s from /proc, Linux only), and the stage times. No document text is written.

    python teams/01-data-a/dedup/minhash_sizing.py --inputs out/<staged cleaned folder> --factors 1 2 4

Writes out/minhash_sizing/sizing.csv and sizing.json, and prints the extrapolated hours and GB for the whole staged
inputs (linear in documents, from the largest measured factor).
"""
import sys
sys.dont_write_bytecode = True

import argparse, csv, json, os, subprocess, time  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SAMPLE_DOCS = int(os.environ.get("MH_SAMPLE_DOCS", 1_410_230))


def tree_rss_bytes(pid):
    """Resident memory of a process and all its descendants, summed (Linux /proc; None elsewhere)."""
    proc = Path("/proc")
    if not proc.is_dir():
        return None
    children, rss = {}, {}
    for d in proc.iterdir():
        if not d.name.isdigit():
            continue
        try:
            st = (d / "stat").read_text().rsplit(")", 1)[1].split()
            children.setdefault(int(st[1]), []).append(int(d.name))      # ppid -> pids
            rss[int(d.name)] = int(st[21]) * os.sysconf("SC_PAGE_SIZE")    # resident pages
        except (OSError, IndexError, ValueError):
            continue
    total, todo = 0, [pid]
    while todo:
        p = todo.pop()
        total += rss.get(p, 0)
        todo.extend(children.get(p, ()))
    return total


def run_measured(cmd, cwd, every=0.5):
    """Run cmd and sample the summed RSS of its whole process tree (the main process plus every worker running at
    that moment) every `every` seconds. Returns (exit code, peak total RSS in bytes, or None off Linux)."""
    import threading
    proc = subprocess.Popen(cmd, cwd=cwd)
    peak, stop = [None], threading.Event()
    def sample():
        while not stop.is_set():
            v = tree_rss_bytes(proc.pid)
            if v is not None:
                peak[0] = max(peak[0] or 0, v)
            stop.wait(every)
    t = threading.Thread(target=sample, daemon=True)
    t.start()
    code = proc.wait()
    stop.set(); t.join()
    return code, peak[0]


def part_rows(path):
    import pyarrow.parquet as pq
    return pq.ParquetFile(path).metadata.num_rows


def pick(parts, target):
    """Whole parts, round-robin over packs so every factor mixes the packs, until the rows reach target."""
    by_pack = {}
    for split, rel, path, rows in parts:
        by_pack.setdefault(rel.split("/")[0], []).append((split, rel, path, rows))
    chosen, total = [], 0
    while total < target and any(by_pack.values()):
        for pack in sorted(by_pack):
            if by_pack[pack] and total < target:
                p = by_pack[pack].pop(0)
                chosen.append(p); total += p[3]
    return chosen, total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", required=True, help="staged cleaned folder with train/ and heldout/, relative to the repo")
    ap.add_argument("--factors", type=float, nargs="+", default=[1, 2, 4])
    ap.add_argument("--workers", type=int, default=None, help="override the settings' workers (default: keep them)")
    ap.add_argument("--settings", default="teams/01-data-a/dedup/minhash_overlap_partial.json")
    a = ap.parse_args()
    inputs = REPO / a.inputs
    parts = [(split, p.relative_to(inputs / split).as_posix(), p, part_rows(p))
             for split in ("train", "heldout") if (inputs / split).is_dir()
             for p in sorted((inputs / split).rglob("*.parquet"))]
    staged = sum(p[3] for p in parts)
    base = json.loads((REPO / a.settings).read_text(encoding="utf-8"))
    root = REPO / "out" / "minhash_sizing"
    results = []
    for f in a.factors:
        chosen, rows = pick(parts, f * SAMPLE_DOCS)
        name = f"x{f:g}"
        folder = root / name / "inputs"
        for split, rel, path, _ in chosen:
            link = folder / split / rel
            link.parent.mkdir(parents=True, exist_ok=True)
            if not link.exists():
                try:
                    os.symlink(path.resolve(), link)
                except OSError:          # Windows without symlink rights: hard link, then copy
                    try:
                        os.link(path.resolve(), link)
                    except OSError:
                        import shutil; shutil.copy2(path, link)
        cfg = {**{k: v for k, v in base.items() if not k.startswith("_")}, "inputs": (folder).relative_to(REPO).as_posix(),
               "out": (root / name / "overlap").relative_to(REPO).as_posix(), "workers": base.get("workers", 0) if a.workers is None else a.workers, "expected_packs": [],
               "splits": sorted({c[0] for c in chosen})}
        cfg_path = root / name / "config.json"
        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        t = time.time()
        code, total = run_measured([sys.executable, str(HERE / "minhash_overlap.py"), "--config", str(cfg_path)], REPO)
        s = json.loads((root / name / "overlap" / "overlap_summary.json").read_text(encoding="utf-8")) if code == 0 else {}
        rss = s.get("peak_rss_mb", {})
        results.append({"factor": f, "parts": len(chosen), "documents": rows, "status": s.get("status", "failed"),
                        "wall_minutes": round((time.time() - t) / 60, 1),
                        "peak_rss_main_gb": round((rss.get("main") or 0) / 1024, 2),
                        "peak_rss_worker_gb": round((rss.get("largest_worker") or 0) / 1024, 2),
                        "peak_rss_total_gb": round(total / (1 << 30), 2) if total else None,
                        "workers": s.get("workers"), "candidates": s.get("pairs_verified"),
                        "qualifying": s.get("qualifying_pairs_by_rule"), "stage_seconds": s.get("stage_seconds")})
        print(json.dumps(results[-1]), flush=True)
    root.mkdir(parents=True, exist_ok=True)
    with open(root / "sizing.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, ["factor", "parts", "documents", "status", "wall_minutes", "peak_rss_main_gb",
                                "peak_rss_worker_gb", "peak_rss_total_gb", "workers", "candidates"], extrasaction="ignore")
        w.writeheader(); w.writerows(results)
    ok = [r for r in results if r["status"] == "complete"]
    proj = {}
    if ok:
        big = max(ok, key=lambda r: r["documents"])
        k = staged / big["documents"]
        proj = {"staged_documents": staged, "from_factor": big["factor"],
                "hours_linear": round(big["wall_minutes"] * k / 60, 2),
                "peak_rss_main_gb_linear": round(big["peak_rss_main_gb"] * k, 1),
                "peak_rss_total_gb_at_largest_factor": big["peak_rss_total_gb"],
                "note": "each factor's row is measured; this projection to all staged documents is linear, not measured"}
    (root / "sizing.json").write_text(json.dumps({"results": results, "projection_whole_staged_inputs": proj}, indent=2),
                                      encoding="utf-8")
    print(json.dumps(proj))


if __name__ == "__main__":
    main()
