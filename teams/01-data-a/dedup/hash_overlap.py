r"""Cross-pack exact copies from the clean job's text_hash column: rule H1, without reading any document text.

A drop-in "script" for the pipeline's overlap stage, like minhash_overlap.py. It writes the three files dedup.py and
run_pipeline.py read -- overlap_summary.json, overlap_matches.csv (same columns) and overlap_docs.parquet (same columns,
same row order) -- so dedup, apply, F2, the ledger and the reconciliation do not change. It finds exact copies only (rule
H1, "method": "exact_hash" in the summary); near copies (rule H2) are not looked for, so the remove list dedup.py makes
from it is the H1 part of what minhash_overlap.py's would be.

HOW IT WORKS
============
1. The cleaned parts must hold the text_hash and key_words columns: the clean job writes them with "text_hash": true in
   pipeline/clean.json (sha256 of each document's H1 key, and the key's number of words). The clean job's
   job_summary.json in the inputs folder records that, and its normalize_id must be h1_sha256.py's. Only doc_id,
   pack_id, text_hash and key_words are read, never text. Parts are read by `workers` threads at once, and each part's
   sha256 is recorded, as the other overlap stages do.
2. One pass over every hash at once: Arrow's dictionary encoding numbers the distinct hashes, and every group of two or
   more rows is written as star edges (each member with the group's first row), exactly as minhash_overlap.py writes
   its H1 edges. Rows are numbered as overlap.py numbers them (parts in sorted order, rows in file order), so for the
   same parts overlap_docs.parquet has the same rows and overlap_matches.csv the same H1 rows as minhash_overlap.py's.
3. overlap_docs.parquet's shingles column is the number of word 5-gram positions of the key (words - 4, at least 1; 0
   for an empty key), not the number of distinct shingles the other stages count, which needs the text. It is 0 exactly
   when the key is empty, the one thing dedup.py reads it for (an empty document is set aside, never removed). It is never
   null: dedup.py combines it with other conditions in Arrow, where a null would drop the row.

Memory: the table of all documents (IDs, the 64-character hash, row numbers), about 150 bytes per document.

HOW TO RUN IT
=============
    python teams/01-data-a/dedup/hash_overlap.py --config teams/01-data-a/dedup/hash_overlap.json

In the pipeline: "overlap": {"script": "teams/01-data-a/dedup/hash_overlap.py", "settings": "<this config>"}.

CONFIG (JSON; keys starting with "_" are comments)
  inputs, out          cleaned parts (train/ and heldout/) and the output folder, relative to the repository root;
                       out must be inside out/
  splits               ["train", "heldout"] (default)
  expected_packs       the pack IDs the parts must hold; [] checks nothing                       (default [])
  max_output_mb        limit for the files returned to the repository                           (default 50)
  workers              threads reading parts; 0 = all cores                                     (default 0)

WHAT IT WRITES (in out)
=======================
  overlap_docs.parquet   row -> document, as minhash_overlap.py (job storage; one row per document)
  overlap_matches.csv    the H1 edges: row_a, row_b, rule, stage, pack_a, pack_b, word_jaccard, code_jaccard
  overlap_summary.json   counts, inputs and their sha256, the key definition, stage times, peak RSS, versions, outputs
"""
import sys
sys.dont_write_bytecode = True

import argparse, hashlib, json, os, platform, time  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from h1_sha256 import NORMALIZE_ID  # noqa: E402
from minhash_overlap import find_parts, peak_rss_mb, sha256_file  # noqa: E402

REPO = HERE.parents[2]
DEFAULTS = {"inputs": "out/tokenizer_sample_v0_clean", "splits": ["train", "heldout"], "out": "out/overlap",
            "expected_packs": [], "max_output_mb": 50, "workers": 0}
COLUMNS = ["doc_id", "pack_id", "text_hash", "key_words"]
RETURNED = ("overlap_matches.csv",)
JOB_STORAGE = ("overlap_docs.parquet",)
EMPTY = hashlib.sha256(b"").hexdigest()   # the hash of an empty H1 key


def fail(message):
    sys.exit(f"ERROR: {message}")


def load_config(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    unknown = sorted(k for k in raw if not k.startswith("_") and k not in DEFAULTS)
    if unknown:
        fail(f"unknown keys in {path}: {unknown}")
    cfg = {**DEFAULTS, **{k: v for k, v in raw.items() if not k.startswith("_")}}
    for key in ("inputs", "out"):
        if Path(cfg[key]).is_absolute():
            fail("inputs and out must be relative to the repository root")
    if not (REPO / cfg["out"]).resolve().is_relative_to((REPO / "out").resolve()):
        fail(f"out must be inside out/ in the repository root, not {cfg['out']}")
    if (not isinstance(cfg["splits"], list) or not cfg["splits"]
            or any(s not in ("train", "heldout") for s in cfg["splits"]) or len(set(cfg["splits"])) != len(cfg["splits"])):
        fail(f"splits must be train and/or heldout, not {cfg['splits']}")
    if type(cfg["workers"]) is not int or cfg["workers"] < 0:
        fail("workers must be a whole number, 0 or more (0 = all cores)")
    if isinstance(cfg["max_output_mb"], bool) or not isinstance(cfg["max_output_mb"], (int, float)) \
            or not 0 < cfg["max_output_mb"] <= 50:
        fail("max_output_mb must be above 0 and at most 50 (JOB_REQUEST.md)")
    exp = cfg["expected_packs"]
    if not isinstance(exp, list) or any(not isinstance(p, str) or not p.strip() for p in exp) or len(set(exp)) != len(exp):
        fail("expected_packs must be a list of distinct nonempty pack IDs")
    return cfg


def clean_spec(inputs):
    """The text_hash record of the clean job that wrote the inputs (its job_summary.json), once it is h1_sha256.py's key."""
    path = inputs / "job_summary.json"
    try:
        spec = json.loads(path.read_text(encoding="utf-8")).get("text_hash")
    except (OSError, ValueError):
        fail(f"{path} cannot be read: the inputs must be a clean job's output folder")
    if not isinstance(spec, dict):
        fail(f"{path} records no text_hash: clean with \"text_hash\": true in pipeline/clean.json")
    if spec.get("normalize_id") != NORMALIZE_ID:
        fail(f"the clean job hashed keys of normalize {spec.get('normalize_id')!r}, h1_sha256.py builds {NORMALIZE_ID!r}")
    return spec


def read_part(item):
    """(split, part, table of COLUMNS, sha256) of one cleaned part, its columns checked with Arrow compute (no row loop)."""
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    split, part, path = item
    pf = pq.ParquetFile(path)
    missing = sorted(set(COLUMNS) - set(pf.schema_arrow.names))
    if missing:
        raise ValueError(f"{path} has no {', '.join(missing)} column: clean with \"text_hash\": true in pipeline/clean.json")
    t = pf.read(columns=COLUMNS)
    if t.num_rows:
        for name in ("doc_id", "pack_id"):
            c = t[name]
            if c.null_count or not pc.all(pc.greater(pc.utf8_length(pc.utf8_trim_whitespace(c)), 0)).as_py():
                raise ValueError(f"{path} has a missing or empty {name}")
        h, w = t["text_hash"], t["key_words"]
        if h.null_count or not pc.all(pc.match_substring_regex(h, r"^[0-9a-f]{64}$")).as_py():
            raise ValueError(f"{path}: text_hash must be 64 lowercase hex characters on every row")
        if w.null_count or pc.min(w).as_py() < 0:
            raise ValueError(f"{path}: key_words must be a whole number, 0 or more, on every row")
        if pc.any(pc.xor(pc.equal(w, 0), pc.equal(h, EMPTY))).as_py():
            raise ValueError(f"{path}: key_words is 0 exactly when the key is empty, and the text_hash of an empty key is "
                             f"{EMPTY[:12]}…; a row breaks that, so the columns do not come from one key")
    return split, part, t, sha256_file(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    cfg = load_config(ap.parse_args().config)
    import numpy as np
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.csv as pacsv
    import pyarrow.parquet as pq

    t0 = time.time()
    times = {}
    inputs, out = REPO / cfg["inputs"], REPO / cfg["out"]
    spec = clean_spec(inputs)
    parts = find_parts(inputs, cfg["splits"])
    workers = cfg["workers"] or os.cpu_count() or 1
    print(f"{len(parts)} cleaned parts, {workers} reading threads", flush=True)

    # 1. Read the hash columns of every part (threads: Arrow and hashlib release the GIL).
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            read = list(pool.map(read_part, parts))
    except ValueError as e:
        fail(e)
    tables, part_docs, digests = [], [], []
    for split, part, t, digest in read:
        n = t.num_rows
        tables.append(pa.table({"doc_id": t["doc_id"].cast(pa.string()), "pack": t["pack_id"].cast(pa.string()),
                                "split": pa.repeat(split, n).cast(pa.string()),
                                "part": pa.repeat(part, n).cast(pa.string()),
                                "row_in_part": pa.array(np.arange(n, dtype=np.int64)),
                                "text_hash": t["text_hash"].cast(pa.large_string()),
                                "words": t["key_words"].cast(pa.int64())}))
        part_docs.append(n)
        digests.append(digest)
    T = pa.concat_tables(tables)
    N = T.num_rows
    if N < 2:
        fail(f"{N} document(s); nothing to compare")
    packs = sorted(pc.unique(T["pack"]).to_pylist())
    if cfg["expected_packs"] and set(packs) != set(cfg["expected_packs"]):
        fail(f"pack inventory mismatch: missing={sorted(set(cfg['expected_packs']) - set(packs))}, "
             f"unexpected={sorted(set(packs) - set(cfg['expected_packs']))}")
    times["read"] = round(time.time() - t0, 1)

    # 2. H1: rows with the same hash. Star edges per group, from the group's first row (as minhash_overlap.py).
    t = time.time()
    codes = pc.dictionary_encode(T["text_hash"].combine_chunks()).indices.to_numpy().astype(np.int64)
    counts = np.bincount(codes)
    order = np.argsort(codes, kind="stable")          # rows grouped by hash, each group in row order
    first = order[np.r_[0, np.cumsum(counts)[:-1]]]   # smallest row of each group
    head = first[codes]
    rows = np.arange(N)
    edge = (counts[codes] > 1) & (rows != head)
    a, b = head[edge], rows[edge]
    empty = pc.sum(pc.equal(T["words"], 0)).as_py() or 0
    times["h1"] = round(time.time() - t, 1)

    # 3. Outputs.
    t = time.time()
    out.mkdir(parents=True, exist_ok=True)
    positions = pc.max_element_wise(pc.subtract(T["words"], 4), pa.scalar(1, pa.int64()))   # word 5-gram positions
    shingles = pc.if_else(pc.equal(T["words"], 0), pa.scalar(0, pa.int64()), positions)
    pq.write_table(pa.table({"row": pa.array(rows), "id": pc.binary_join_element_wise(T["pack"], T["doc_id"], "-"),
                             "doc_id": T["doc_id"], "pack": T["pack"], "split": T["split"], "part": T["part"],
                             "row_in_part": T["row_in_part"], "words": T["words"], "shingles": shingles}),
                   out / "overlap_docs.parquet", compression="zstd")
    # The edges stay in Arrow: the packs come by take(), and one write_csv call writes every row (no Python per pair).
    row_a, row_b = pa.array(a, pa.int64()), pa.array(b, pa.int64())
    pack_a, pack_b = T["pack"].take(row_a), T["pack"].take(row_b)
    edges = len(a)
    pacsv.write_csv(pa.table({"row_a": row_a, "row_b": row_b, "rule": pa.repeat("H1", edges),
                              "stage": pc.if_else(pc.equal(pack_a, pack_b), "within_pack", "cross_pack"),
                              "pack_a": pack_a, "pack_b": pack_b, "word_jaccard": pa.repeat("1.0", edges),
                              "code_jaccard": pa.repeat("", edges)}),
                    out / "overlap_matches.csv", write_options=pacsv.WriteOptions(quoting_style="none"))
    times["outputs"] = round(time.time() - t, 1)

    files = {f: {"bytes": (out / f).stat().st_size, "sha256": sha256_file(out / f)} for f in (*RETURNED, *JOB_STORAGE)}
    per = T.group_by(["pack", "split"]).aggregate([("row_in_part", "count")])   # one row per (pack, split)
    per_split = dict(zip(zip(per["pack"].to_pylist(), per["split"].to_pylist()), per["row_in_part_count"].to_pylist()))
    groups = counts[counts > 1]
    summary = {
        "status": "complete",
        "method": "exact_hash",
        "config": cfg,
        "normalize_id": spec["normalize_id"],
        "key": spec.get("key"),
        "text_hash": spec,
        "inputs": {"root": cfg["inputs"], "checksum_verification": "sha256",
                   "parts": [{"part": f"{sp}/{pt}", "documents": n, "sha256": dg}
                             for (sp, pt, _), n, dg in zip(parts, part_docs, digests)]},
        "documents": {p: {**{sp: per_split.get((p, sp), 0) for sp in cfg["splits"]},
                          "all": sum(per_split.get((p, sp), 0) for sp in cfg["splits"])} for p in packs},
        "documents_all": N,
        "distinct_hashes": int(len(counts)),
        "h1_exact_groups": int(len(groups)),
        "documents_in_h1_exact_groups": int(groups.sum()),
        "empty_documents": empty,
        "qualifying_pairs_by_rule": {"H1": int(len(a))},
        "h1_edges": "star: each member of an H1 group paired with the group's first row",
        "duplicate_rules": {"h1": "same sha256 of the H1 key (the clean job's text_hash)",
                            "h2": "not looked for: exact copies only", "translations": "not detected"},
        "shingles": "word 5-gram positions of the key (words - 4, at least 1; 0 for an empty key), not distinct shingles",
        "stage_seconds": times,
        "wall_seconds": round(time.time() - t0, 1),
        "workers": workers,
        "peak_rss_mb": peak_rss_mb(),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pyarrow": pa.__version__,
                     "platform": platform.platform()},
        "outputs": files,
        "returned_files": list(RETURNED) + ["overlap_summary.json"],
        "job_storage_files": list(JOB_STORAGE),
    }
    (out / "overlap_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    returned = sum(files[f]["bytes"] for f in RETURNED) + (out / "overlap_summary.json").stat().st_size
    summary["returned_mb"] = round(returned / (1 << 20), 2)
    (out / "overlap_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("documents_all", "h1_exact_groups", "documents_in_h1_exact_groups",
                                               "qualifying_pairs_by_rule", "stage_seconds", "wall_seconds", "peak_rss_mb",
                                               "returned_mb")}, indent=1))
    if returned > cfg["max_output_mb"] * (1 << 20):
        summary["status"] = "failed_output_limit"
        (out / "overlap_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        fail(f"returned files are {summary['returned_mb']} MB, over max_output_mb {cfg['max_output_mb']}")


if __name__ == "__main__":
    main()
