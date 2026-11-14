"""Rebuild source overlap shares from returned TSAI artifacts, without reading document text.

python teams/01-data-a/dedup/overlap_report.py --results teams/01-data-a/jobs/results/2026-11-04-overlap

Writes only to out/. The input must contain overlap_docs.parquet and overlap_matches.csv from overlap.py.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[3]


def write_matrix(out, documents, pairs):
    """Count distinct source document rows, once per target pack, with no self-matches.

    documents maps run-local integer row IDs to pack IDs. pairs yields qualifying (row_a, row_b).
    A repeated doc_id is deliberately irrelevant: rows denote distinct input occurrences.
    """
    totals = Counter(documents.values())
    hits = defaultdict(set)
    for a, b in pairs:
        if a not in documents or b not in documents:
            raise ValueError(f"pair references unknown document rows: {a}, {b}")
        if a == b:
            continue
        pa, pb = documents[a], documents[b]
        hits[pa, pb].add(a)
        hits[pb, pa].add(b)
    packs = sorted(totals)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "overlap_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", *packs])
        for a in packs:
            writer.writerow([a, *(f"{len(hits[a, b]) / totals[a]:.10f}" for b in packs)])
    with (out / "overlap_matrix_counts.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source_a", "source_b", "matched_documents", "total_documents"])
        for a in packs:
            for b in packs:
                writer.writerow([a, b, len(hits[a, b]), totals[a]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--out", default="out/overlap_returned", type=Path)
    args = parser.parse_args()
    out = (REPO / args.out).resolve()
    if not out.is_relative_to((REPO / "out").resolve()):
        parser.error("out must be inside out/ in the repository root")
    summary = json.loads((args.results / "overlap_summary.json").read_text(encoding="utf-8"))
    if summary.get("status") != "complete":
        parser.error("returned overlap job did not complete successfully")
    for name in ("overlap_docs.parquet", "overlap_matches.csv"):
        expected = summary["outputs"][name]["sha256"]
        digest = hashlib.sha256()
        with (args.results / name).open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            parser.error(f"returned artifact checksum mismatch: {name}")
    import pyarrow.parquet as pq
    docs = pq.read_table(args.results / "overlap_docs.parquet", columns=["row", "pack"]).to_pylist()
    documents = {d["row"]: d["pack"] for d in docs}
    if len(documents) != len(docs) or len(docs) != summary["documents_all"]:
        parser.error("duplicate row IDs or wrong document count in overlap_docs.parquet")
    with (args.results / "overlap_matches.csv").open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not {"row_a", "row_b", "rule"} <= set(reader.fieldnames or []):
            parser.error("overlap_matches.csv needs row_a, row_b and rule columns")
        write_matrix(out, documents, ((int(p["row_a"]), int(p["row_b"]))
                                     for p in reader))
    print(f"Wrote overlap_matrix.csv and overlap_matrix_counts.csv to {out}")


if __name__ == "__main__":
    main()
