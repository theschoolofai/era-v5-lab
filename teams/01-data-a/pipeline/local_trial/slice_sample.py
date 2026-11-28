r"""A fixed-seed slice of the tokenizer sample: the same 86 parts, each cut to a share of its rows, with its own manifest.

    python -I teams/01-data-a/pipeline/local_trial/slice_sample.py \
        --manifest teams/01-data-a/jobs/2026-11-02-tokenizer-sample-v0-clean/tokenizer_sample_v0_manifest.json \
        --sample <folder with the 86 raw parts> --out inputs/sample_1pct --share 0.01 --seed 20261128

For the 1% sample run of D2 (rows read, rows dropped by each stage, seconds per stage): the whole pipeline runs on it as on
the full sample, with every pack and both splits, at about a hundredth of the work.

Which rows. For each part of the manifest, k = max(1, round(rows x share)) rows are taken, chosen by NumPy's generator seeded
with (seed, crc32 of the part path): the same rows for the same seed, share and part, whatever the order the parts are read
in. The rows keep their file order and every column (doc_id, text, url, lang_label, pack_id, source), byte for byte.

Where the parts are. --sample may hold the official layout (<split>/<pack>/<file>) or a pack-first copy (<pack>/<split>/...,
or <pack>/Part_N/ and <pack>/Heldout/ as in the course download). A part is the file under the pack's folder with the
manifest's size and sha256 (the clean job finds its inputs the same way), so file names and folder names do not matter.

What it writes, in --out (inside the repository, which the pipeline needs; not committed):
  <split>/<pack>/<file>     the sliced parts, in the official layout
  sample_manifest.json      the manifest of the slice, in the sample manifest's format: name, seed, share, the source
                            manifest's sha256, total_docs, and one entry per part (path, split, pack_id, rows, bytes,
                            sha256, text_bytes, source_rows, source_sha256). Its sha256 is the stages.clean.manifest_sha256
                            of a run on the slice; the last line printed gives it.
It refuses an --out that is not empty.
"""
import sys
sys.dont_write_bytecode = True

import argparse, hashlib, json, zlib  # noqa: E402
from pathlib import Path  # noqa: E402


class SliceError(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def find_part(sample, shard, hashed):
    """The file under `sample` with the shard's size and sha256: in <split>/<pack>/ or anywhere under <pack>/."""
    split, pack = shard["split"], shard["pack_id"]
    folders = [sample / split / pack, sample / pack]
    candidates = [p for f in folders if f.is_dir() for p in sorted(f.rglob("*.parquet"))]
    for p in dict.fromkeys(candidates):
        if p.stat().st_size != shard["bytes"]:
            continue
        if p not in hashed:
            hashed[p] = sha256(p)
        if hashed[p] == shard["sha256"]:
            return p
    raise SliceError(f"no file with the size and sha256 of {shard['path']} under {sample / pack} or {sample / split / pack}")


def rows_to_keep(n, share, seed, path):
    """Sorted row numbers: k = max(1, round(n * share)) of n, from a generator seeded with (seed, crc32(path))."""
    import numpy as np
    if n == 0:
        return np.zeros(0, dtype=np.int64)
    k = min(n, max(1, round(n * share)))
    rng = np.random.default_rng([seed, zlib.crc32(path.encode("utf-8"))])
    return np.sort(rng.choice(n, size=k, replace=False))


def slice_sample(manifest, sample, out, share, seed):
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    if not 0 < share <= 1:
        raise SliceError("--share must be above 0 and at most 1")
    if out.exists() and any(out.iterdir()):
        raise SliceError(f"{out} is not empty: choose a fresh folder")
    source = json.loads(manifest.read_text(encoding="utf-8"))
    entries, hashed = [], {}
    for shard in source["shards"]:
        path = find_part(sample, shard, hashed)
        table = pq.read_table(path)
        if table.num_rows != shard["rows"]:
            raise SliceError(f"{path} has {table.num_rows} rows, the manifest says {shard['rows']} for {shard['path']}")
        cut = table.take(rows_to_keep(table.num_rows, share, seed, shard["path"]))
        target = out / shard["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(cut, target)
        entries.append({"path": shard["path"], "split": shard["split"], "pack_id": shard["pack_id"], "rows": cut.num_rows,
                        "bytes": target.stat().st_size, "sha256": sha256(target),
                        "text_bytes": int(pc.sum(pc.binary_length(cut["text"])).as_py() or 0),
                        "source_rows": shard["rows"], "source_sha256": shard["sha256"]})
    data = {"name": f"{source.get('name', 'sample')}, slice of {share:g} (seed {seed})", "seed": seed, "share": share,
            "source_manifest_sha256": sha256(manifest), "total_docs": sum(e["rows"] for e in entries),
            "total_text_bytes": sum(e["text_bytes"] for e in entries), "shards": entries}
    path = out / "sample_manifest.json"
    path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8", newline="\n")
    return path, data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True, help="the sample's manifest (86 parts)")
    ap.add_argument("--sample", type=Path, required=True, help="the folder holding the sample's raw parts")
    ap.add_argument("--out", type=Path, required=True, help="an empty or new folder for the slice")
    ap.add_argument("--share", type=float, default=0.01, help="share of each part's rows to keep (default 0.01)")
    ap.add_argument("--seed", type=int, default=20261128)
    a = ap.parse_args(argv)
    try:
        path, data = slice_sample(a.manifest, a.sample, a.out, a.share, a.seed)
    except SliceError as e:
        sys.exit(f"slice_sample: {e}")
    splits = {s: sum(1 for e in data["shards"] if e["split"] == s) for s in ("train", "heldout")}
    print(f"{len(data['shards'])} parts {splits}, {data['total_docs']:,} rows of "
          f"{sum(e['source_rows'] for e in data['shards']):,}, {data['total_text_bytes']:,} text bytes")
    print(f"manifest {path} sha256 {sha256(path)}")


if __name__ == "__main__":
    main()
