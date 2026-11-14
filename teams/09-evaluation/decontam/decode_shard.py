"""Decode training shards (Data A shard format v1) back to text for the decontamination check (G9).

    python decode_shard.py <shard.bin | folder> --tokenizer <c3>/tokenizer.json --out <dir>
    python decontam_check.py <dir>/<shard_id>.text.parquet          # full set: no --benchmarks, --tags or --exclude

A shard (teams/01-data-a/shards/shard_format_v1.md) holds token IDs, not text:
  <shard_id>.bin           1,024-byte header (256 little-endian int32: magic 20261025, version 2, token count), then uint32 ids
  <shard_id>.idx.npy       int64 start of each document, then the token count
  <shard_id>.docs.parquet  doc_id per document, in shard order (IDs and counts only)
  <shard_id>.json          the manifest (sha256 of each file, counts, EOS id, tokenizer sha256)

This script checks a shard against its manifest, then writes <out>/<shard_id>.text.parquet with the columns
doc_id, text, shard_id, n_tokens. decontam_check.py and canary_scan.py read that file as it is (doc_id and text columns).
Each document is its tokens minus the final EOS (<|endoftext|> id 130822), decoded with the frozen C3 tokenizer
(sha256 C3_SHA256; TSAI allowed it for decoding in week 3). The text is the tokenizer-normalized text the model trains on.

Checks (a shard that fails one is reported and skipped, with nothing written for it; the other shards still run, and the
exit code is 1 if any shard failed):
  - header magic and version, and file size = 1,024 + 4 x token count;
  - .idx.npy starts at 0, rises, and ends at the token count; one docs.parquet row per document;
  - manifest: payload, index and docs sha256, doc_count, token_count, eos_token_id and tokenizer_sha256 all match;
  - every document ends with EOS, and no other special id occurs inside a document.
With --check-text <clean.parquet> (the run_clean.py output the shard was written from), each decoded document must equal
the tokenizer-normalized source text of the same doc_id: a round-trip test of the decoder.

The output holds document text. Do not commit it or paste it anywhere (pr-guard refuses .parquet anyway); the report gives
only IDs, items, coverage and offsets. Needs numpy, pyarrow and tokenizers (no torch).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from tokenizers import Tokenizer

C3_SHA256 = "15468e66457b43af79f695cbe585c0d03e3cfe7a4a5d04d189dd3c6b9f02ddc3"  # G3 freeze, #340
MAGIC, VERSION, HEADER_BYTES = 20261025, 2, 1024
EOS_ID = 130_822
SPECIAL_FROM = 130_725  # G3: named specials and reserved slots run from here to the end of the vocab
BATCH = 256


class ShardError(ValueError):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_tokenizer(path, any_tokenizer=False):
    """(tokenizer, sha256). Only the frozen C3 tokenizer, unless any_tokenizer (tests)."""
    got = sha256(path)
    if not any_tokenizer and got != C3_SHA256:
        raise ShardError(f"{path}: sha256 {got}, not the frozen C3 {C3_SHA256}")
    return Tokenizer.from_file(str(path)), got


def shard_files(bin_path):
    bin_path = Path(bin_path)
    stem = bin_path.name[: -len(".bin")]
    base = bin_path.with_name(stem)
    return {"bin": bin_path, "idx": Path(f"{base}.idx.npy"), "docs": Path(f"{base}.docs.parquet"),
            "manifest": Path(f"{base}.json"), "shard_id": stem}


def read_shard(bin_path, tokenizer_sha, eos_id=None, special_from=None):
    """Check one shard against its manifest. Return (shard_id, tokens, starts, doc_ids)."""
    eos_id = EOS_ID if eos_id is None else eos_id
    special_from = SPECIAL_FROM if special_from is None else special_from
    f = shard_files(bin_path)
    for key in ("bin", "idx", "docs", "manifest"):
        if not f[key].exists():
            raise ShardError(f"{f['shard_id']}: missing {f[key].name}")
    m = json.loads(f["manifest"].read_text(encoding="utf-8"))

    header = np.fromfile(f["bin"], dtype="<i4", count=256)
    if len(header) != 256 or header[0] != MAGIC or header[1] != VERSION or header[2] <= 0:
        raise ShardError(f"{f['bin'].name}: bad header (want magic {MAGIC}, version {VERSION})")
    n_tok = int(header[2])
    if f["bin"].stat().st_size != HEADER_BYTES + 4 * n_tok:
        raise ShardError(f"{f['bin'].name}: size {f['bin'].stat().st_size}, header says {HEADER_BYTES + 4 * n_tok}")
    tokens = np.fromfile(f["bin"], dtype="<u4", offset=HEADER_BYTES)

    starts = np.load(f["idx"], allow_pickle=False)
    if starts.dtype != np.int64 or starts.ndim != 1 or len(starts) < 2:
        raise ShardError(f"{f['idx'].name}: want a 1-D int64 array of doc starts plus the token count")
    if starts[0] != 0 or starts[-1] != n_tok or np.any(np.diff(starts) <= 0):
        raise ShardError(f"{f['idx'].name}: starts must begin at 0, rise, and end at the token count {n_tok}")
    n_docs = len(starts) - 1

    doc_ids = pq.read_table(f["docs"], columns=["doc_id"]).column("doc_id").to_pylist()
    if len(doc_ids) != n_docs:
        raise ShardError(f"{f['docs'].name}: {len(doc_ids)} rows, index has {n_docs} documents")

    want = {"payload_sha256": sha256(f["bin"]), "index_sha256": sha256(f["idx"]),
            "sample_metadata_sha256": sha256(f["docs"]), "doc_count": n_docs, "token_count": n_tok,
            "eos_token_id": eos_id, "tokenizer_sha256": tokenizer_sha}
    for key, value in want.items():
        if m.get(key) != value:
            raise ShardError(f"{f['manifest'].name}: {key} is {m.get(key)!r}, the shard gives {value!r}")

    ends = starts[1:] - 1
    if np.any(tokens[ends] != eos_id):
        bad = int(np.flatnonzero(tokens[ends] != eos_id)[0])
        raise ShardError(f"{f['shard_id']}: document {doc_ids[bad]} does not end with EOS {eos_id}")
    inner = np.ones(n_tok, dtype=bool)
    inner[ends] = False
    if np.any(tokens[inner] >= special_from):
        pos = int(np.flatnonzero(inner & (tokens >= special_from))[0])
        doc = int(np.searchsorted(starts, pos, side="right") - 1)
        raise ShardError(f"{f['shard_id']}: special id {int(tokens[pos])} inside document {doc_ids[doc]}")
    return f["shard_id"], tokens, starts, doc_ids


def decode_shard(bin_path, tok, tokenizer_sha, eos_id=None, special_from=None):
    """Return a pyarrow table: doc_id, text, shard_id, n_tokens (n_tokens includes the final EOS)."""
    shard_id, tokens, starts, doc_ids = read_shard(bin_path, tokenizer_sha, eos_id, special_from)
    texts = []
    for i in range(0, len(doc_ids), BATCH):
        seqs = [tokens[starts[j]:starts[j + 1] - 1].tolist() for j in range(i, min(i + BATCH, len(doc_ids)))]
        texts.extend(tok.decode_batch(seqs, skip_special_tokens=False))
    return pa.table({"doc_id": [str(d) for d in doc_ids], "text": texts,
                     "shard_id": [shard_id] * len(doc_ids),
                     "n_tokens": np.diff(starts).astype(np.int64)})


def check_text(table, clean_parquet, tok):
    """Round trip: each decoded doc equals the tokenizer-normalized source text. Return (checked, mismatches)."""
    src = pq.read_table(clean_parquet, columns=["doc_id", "text"])
    source = dict(zip((str(d) for d in src.column("doc_id").to_pylist()), src.column("text").to_pylist()))
    norm = tok.normalizer.normalize_str if tok.normalizer is not None else (lambda s: s)
    bad = []
    for doc_id, text in zip(table.column("doc_id").to_pylist(), table.column("text").to_pylist()):
        if doc_id not in source:
            bad.append((doc_id, "not in source"))
        elif text != norm(source[doc_id] or ""):
            bad.append((doc_id, "text differs"))
    return table.num_rows, bad


def find_shards(path):
    path = Path(path)
    if path.is_dir():
        return sorted(path.rglob("*.bin"))
    if path.suffix == ".bin":
        return [path]
    raise ShardError(f"{path}: give a .bin file or a folder of shards")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shards", help="a <shard_id>.bin file or a folder searched for *.bin")
    ap.add_argument("--tokenizer", type=Path, required=True, help="the frozen C3 tokenizer.json (sha256 C3_SHA256)")
    ap.add_argument("--out", type=Path, required=True, help="folder for <shard_id>.text.parquet (holds text: never commit)")
    ap.add_argument("--check-text", type=Path, help="run_clean.py *_clean.parquet the shard came from: round-trip test")
    ap.add_argument("--any-tokenizer", action="store_true", help="tests only: accept a tokenizer other than C3")
    a = ap.parse_args(argv)

    try:
        tok, tok_sha = load_tokenizer(a.tokenizer, a.any_tokenizer)
        shards = find_shards(a.shards)
    except ShardError as e:
        print(f"decode_shard: {e}", file=sys.stderr)
        return 1
    if not shards:
        print(f"decode_shard: no .bin shards under {a.shards}", file=sys.stderr)
        return 1
    a.out.mkdir(parents=True, exist_ok=True)
    failed = 0
    for path in shards:
        try:
            table = decode_shard(path, tok, tok_sha)
            summary = {"shard_id": table.column("shard_id")[0].as_py(), "docs": table.num_rows,
                       "tokens": int(sum(table.column("n_tokens").to_pylist())), "tokenizer": tok_sha[:12]}
            if a.check_text:
                checked, bad = check_text(table, a.check_text, tok)
                summary["round_trip"] = f"{checked - len(bad)}/{checked} match"
                if bad:
                    summary["round_trip_fail"] = [d for d, _ in bad[:5]]
                    raise ShardError(f"{path.name}: {len(bad)} of {checked} documents do not round-trip")
            out = a.out / f"{summary['shard_id']}.text.parquet"
            pq.write_table(table, out)
            summary["out"] = str(out)
            print(json.dumps(summary))
        except ShardError as e:
            failed += 1
            print(f"decode_shard: {e}", file=sys.stderr)
    print(f"decoded {len(shards) - failed} of {len(shards)} shard(s)", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
