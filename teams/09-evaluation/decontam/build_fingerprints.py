"""Build the benchmark fingerprints (G9).

A fingerprint is the set of hashes of all 13-word runs (13-grams) of a benchmark item.
decontam_check.py looks for these hashes in training documents.

    python build_fingerprints.py --data-dir ~/bench-cache                       # all active benchmarks
    python build_fingerprints.py --data-dir ~/bench-cache --only swe_bench_verified
    python build_fingerprints.py --list                                         # show the registry

The benchmarks are in benchmarks.toml. Each file is downloaded at a pinned revision and
checked against its pinned sha256. Downloads stay in --data-dir, outside the repo.
"""

import argparse
import shutil
import sys
from pathlib import Path

import fpset
import registry

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "fingerprints" / fpset.VERSION
META_KEYS = ("name", "tags", "licence", "note", "source", "repo", "revision", "files", "split", "texts",
             "code", "mixed", "canaries", "dedupe", "gated")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", help="cache folder for the benchmark files (outside the repo)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--registry", default=str(registry.REGISTRY))
    ap.add_argument("--only", nargs="+", metavar="ID", help="rebuild only these benchmarks, keep the others")
    ap.add_argument("--list", action="store_true", help="print the registry and stop")
    args = ap.parse_args()

    reg = registry.load(args.registry)
    if args.list:
        for bid, b in reg.items():
            print(f"{b['status']:8s} {bid:20s} {b['name']:28s} {b.get('reason', '')}")
        return
    if not args.data_dir:
        ap.error("--data-dir is required to build")

    active = [bid for bid, b in reg.items() if b["status"] == "active"]
    todo = args.only or active
    bad = [bid for bid in todo if bid not in active]
    if bad:
        ap.error(f"not active in the registry: {bad}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if not args.only:  # a full build removes folders of benchmarks that are no longer active
        for d in out.iterdir():
            if d.is_dir() and d.name not in active:
                shutil.rmtree(d)
    boilerplate = fpset.Boilerplate()
    for bid in todo:
        b = reg[bid]
        meta = {k: b[k] for k in META_KEYS if k in b}
        canaries = set()
        m = fpset.write_benchmark(out, bid, registry.items(bid, b, args.data_dir, canaries),
                                  registry.run_lengths(b), meta,
                                  b.get("gram_filters", fpset.DEFAULT_GRAM_FILTERS), canaries, boilerplate,
                                  b.get("short_min", fpset.SHORT_MIN))
        print(f"{bid:20s} items {m['items']:>6}  without n-gram {m['items_without_ngram']:>4}  "
              f"n-grams {m['item_grams']:>9}  shards {sum(map(len, m['shards'].values()))}", file=sys.stderr)

    not_covered = {bid: {"status": b["status"], "reason": b["reason"]}
                   for bid, b in reg.items() if b["status"] != "active"}
    print(f"set_sha256 {fpset.write_index(out, not_covered)}")


if __name__ == "__main__":
    main()
