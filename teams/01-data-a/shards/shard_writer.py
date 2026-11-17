"""Write one shard in the v1 format (shard_format_v1.md) from one cleaned pack part, check it, and describe it.

  python teams/01-data-a/shards/shard_writer.py --input <run>/final/train/code-go/part-00000.parquet \
      --manifest <run>/pipeline_manifest.json --tokenizer <c3>/tokenizer.json \
      --language go --script Latn --lane code --out <dir>

Input: one part of the pipeline's final folder (run_pipeline.py: clean, dedup, then F2), and the run's pipeline_manifest.json.
provenance.py checks the part's chain back to the raw sample part (F2 report, apply, remove list, clean job) and stops
when a link breaks; what it returns checks cleaning_pipeline.json and goes into the quality report. The split comes from the
part's folder: train. A held-out part is refused until G3 and G9 say what happens to it (the format has train and
validation only). --domain defaults to clean.py's family of the pack. Docs are taken in order until the next one would
pass --tokens; a doc is never split.

Tokenizer (G3): the frozen p1536 tokenizer.json (Gate 3, in place of C3), sha256 TOKENIZER_SHA256 below (G3 train/p1536_s0_manifest.json).
Any other file is refused, except with --any-tokenizer (tests only: the shard is marked dataset_version "test").
Docs are encoded with encode_batch(add_special_tokens=False); each doc ends with one EOS, <|endoftext|> id 130822 (G3, G10).
No BOS and no language tag. The normalizer is inside tokenizer.json, so no normalizer is applied here.

A doc is left out, counted, and listed by doc_id in the quality report when:
  - secret:     its text looks like it holds an email address or a secret (pr-guard's patterns);
  - empty:      it encodes to no tokens;
  - special:    a special id appears inside it (tokenizers turns a literal "<|im_start|>" in the text into a special id);
  - roundtrip:  decode(ids) is not the tokenizer-normalized text.
Checks after writing: G6's open_shard reads the .bin, sizes and index match the manifest, every id < 131,072, and the only
special ids in the shard are the EOS at the end of each doc.
Writes <dir>/<shard_id>.{bin,idx.npy,docs.parquet,json}, cleaning_pipeline.json, <shard_id>.quality_report.json and <shard_id>.dump.md
(IDs and counts only, never text). cleaning_pipeline.json describes the processing (clean.py, F2 set, remove list): run_pipeline.py's shard stage writes it
next to the manifest, and the writer checks it against what provenance.py derives and copies it, so every shard of one
run gets the same file; a --out that already holds one from other processing is refused. The quality report's
"upstream" block lists the doc_ids this part lost to dedup (with group and rule) and to F2 (with benchmark item IDs and
offsets). Needs numpy, pyarrow, tokenizers and torch (G6's dataio imports torch).
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from tokenizers import Tokenizer

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "teams" / "06-performance"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import provenance  # noqa: E402
from dataio.loader import HEADER_BYTES, open_shard  # noqa: E402
from dataio.prepare_fineweb import write_shard  # noqa: E402

TOKENIZER_SHA256 = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"  # G3 Gate 3 freeze, p1536 (was C3 15468e66..., #340)
VOCAB = 131_072
EOS_ID, EOS = 130_822, "<|endoftext|>"
SPECIAL_BLOCK = range(130_725, VOCAB)  # G3: named specials and reserved slots; plus every added token marked special
BATCH = 256
# pr-guard's secret and email patterns (.github/workflows/pr-guard.yml)
SECRET = re.compile("|".join([
    r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"gh[pousr]_[A-Za-z0-9]{30,}", r"\bsk-[A-Za-z0-9_-]{20,}",
    r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9][A-Za-z0-9._%+-]*@(?!users\.noreply\.github\.com\b|example\.(?:com|org)\b)"
    r"(?:[A-Za-z0-9-]+\.)+(?:com|org|net|edu|gov|mil|int|in|io|ai|co|uk|us|me|dev|app|info|biz|ac|ca|au|de|fr|jp|sg|ae)\b"]),
    re.IGNORECASE)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_tokenizer(path, any_tokenizer):
    """(tokenizer, sha256, special ids). Refuses anything but p1536 unless any_tokenizer."""
    got = sha(path)
    tok = Tokenizer.from_file(str(path))
    if not any_tokenizer:
        if got != TOKENIZER_SHA256:
            sys.exit(f"{path}: sha256 {got}, not the frozen p1536 {TOKENIZER_SHA256}. --any-tokenizer is for tests only.")
        if tok.id_to_token(EOS_ID) != EOS:
            sys.exit(f"{path}: id {EOS_ID} is {tok.id_to_token(EOS_ID)!r}, not {EOS}")
    if tok.get_vocab_size(with_added_tokens=True) != VOCAB:
        sys.exit(f"{path}: vocab {tok.get_vocab_size(with_added_tokens=True)}, not {VOCAB}")
    specials = {i for i, t in tok.get_added_tokens_decoder().items() if t.special} | set(SPECIAL_BLOCK)
    return tok, got, specials


def pack_family(pack_id):
    """clean.py's family of the pack (code, english, math, sci, indic), the shard's domain unless --domain says otherwise."""
    sys.path.insert(0, str(REPO / "teams" / "01-data-a" / "spec_v1"))
    try:
        import clean
    finally:
        sys.path.remove(str(REPO / "teams" / "01-data-a" / "spec_v1"))
    if pack_id not in clean._FAMILY:
        sys.exit(f"shard_writer: clean.py has no family for pack {pack_id!r}; give --domain")
    return clean._FAMILY[pack_id]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clean", type=Path, required=True, help="a *_clean.parquet from run_clean.py --f2")
    ap.add_argument("--summary", type=Path, required=True, help="its *_summary.json")
    ap.add_argument("--tokenizer", type=Path, required=True, help="G3's frozen p1536 tokenizer.json")
    ap.add_argument("--language", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--lane", required=True, help="capability_lane")
    ap.add_argument("--domain", help="default: the pack's family in clean.py")
    ap.add_argument("--index", type=int, default=0, help="shard number within the pack and split")
    ap.add_argument("--tokens", type=int, default=2 ** 26, help="fill the shard up to this many tokens")
    ap.add_argument("--any-tokenizer", action="store_true", help="tests only: accept a tokenizer other than p1536")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)

    try:
        info = provenance.load(a.input, a.manifest)
    except provenance.Stop as e:
        sys.exit(f"shard_writer: {e}")
    pack_id, part_path = info["part"]["pack_id"], f"{info['part']['split']}/{info['part']['part']}"
    if info["part"]["split"] != "train":
        sys.exit(f"shard_writer: {part_path} is a {info['part']['split']} part. Only train parts are sharded for now: the format "
                 "allows train and validation, and what a held-out part becomes is for G3 and G9 to say")
    split = "train"
    domain = a.domain or pack_family(pack_id)
    tok, tok_sha, specials = load_tokenizer(a.tokenizer, a.any_tokenizer)
    norm = tok.normalizer.normalize_str if tok.normalizer is not None else (lambda t: t)  # a Sequence normalizer has len 0, so it is falsy
    shard_id = f"{pack_id}-{split}-{a.index:06d}"
    pipeline = a.out / "cleaning_pipeline.json"
    run_file = a.manifest.resolve().parent / "cleaning_pipeline.json"  # written by run_pipeline.py's shard stage
    if not run_file.is_file():
        sys.exit(f"shard_writer: {run_file} not found: run_pipeline.py's shard stage writes it "
                 f"(or: python teams/01-data-a/shards/provenance.py --manifest {a.manifest} --write-record)")
    if json.loads(run_file.read_text(encoding="utf-8")) != info["record"]:
        sys.exit(f"shard_writer: {run_file} is not what {a.manifest} and its stage outputs give now; write it again "
                 "(provenance.py --write-record)")
    if pipeline.is_file() and pipeline.read_bytes() != run_file.read_bytes():
        sys.exit(f"shard_writer: {pipeline} describes other processing than {run_file} (another clean.py, F2 set or remove list); use a new --out")
    a.out.mkdir(parents=True, exist_ok=True)

    table = pq.read_table(a.input, columns=["doc_id", "text", "lang_label"])
    ids_col, text_col, lang_col = (table.column(c).to_pylist() for c in ("doc_id", "text", "lang_label"))
    docs, rows, total, full, seen = [], [], 0, False, len(text_col)
    left_out = {"secret": [], "empty": [], "special": [], "roundtrip": []}
    for b in range(0, len(text_col), BATCH):
        texts = text_col[b:b + BATCH]
        for k, enc in enumerate(tok.encode_batch(texts, add_special_tokens=False)):
            row, text, ids = b + k, texts[k], enc.ids
            doc_id = ids_col[row]
            if SECRET.search(text):
                left_out["secret"].append(doc_id)
                continue
            if not ids:
                left_out["empty"].append(doc_id)
                continue
            inside = sorted(set(ids) & specials)
            if inside:
                left_out["special"].append({"doc_id": doc_id, "ids": inside})
                continue
            if tok.decode(ids, skip_special_tokens=False) != norm(text):
                left_out["roundtrip"].append(doc_id)
                continue
            if total + len(ids) + 1 > a.tokens:
                full, seen = True, row  # rows read before the first doc that did not fit
                break
            docs.append(ids + [EOS_ID])
            rows.append({"doc_id": doc_id, "input_part": part_path, "input_row": row, "n_tokens": len(ids) + 1,
                         "n_chars": len(text), "lang_label": lang_col[row]})
            total += len(ids) + 1
        if full:
            break
    if not docs:
        sys.exit("no document fits in --tokens")

    starts = np.cumsum([0] + [r["n_tokens"] for r in rows]).astype("<i8")  # doc_count + 1 entries; the last is token_count
    bin_path, idx_path, meta_path = (a.out / f"{shard_id}{x}" for x in (".bin", ".idx.npy", ".docs.parquet"))
    write_shard(bin_path, [t for d in docs for t in d])
    np.save(idx_path, starts)
    pq.write_table(pa.Table.from_pylist(rows), meta_path)
    shutil.copyfile(run_file, pipeline)  # the run's file, byte for byte: its sha256 is the manifest's cleaning_pipeline_sha256
    tpc = np.array([r["n_tokens"] / max(r["n_chars"], 1) for r in rows])
    worst = sorted(rows, key=lambda r: -r["n_tokens"] / max(r["n_chars"], 1))[:5]
    report = a.out / f"{shard_id}.quality_report.json"
    report.write_text(json.dumps({
        "shard_id": shard_id, "rows_read": seen, "docs_in_shard": len(docs),
        "left_out": {k: len(v) for k, v in left_out.items()}, "left_out_docs": left_out,
        "tokens_per_char": {"min": round(float(tpc.min()), 3), "median": round(float(np.median(tpc)), 3),
                            "p99": round(float(np.percentile(tpc, 99)), 3), "max": round(float(tpc.max()), 3)},
        "most_tokens_per_char": [{"doc_id": r["doc_id"], "n_tokens": r["n_tokens"], "n_chars": r["n_chars"]} for r in worst],
        "upstream": {"input_part": part_path, "raw_input_sha256": info["raw_input"]["sha256"], "final_sha256": info["final"]["sha256"],
                     "run_id": info["pipeline"]["run_id"], "counts": info["counts"], "removed_by_dedup": info["dedup"]["removed"],
                     "dropped_by_f2": info["f2"]["dropped"]},  # the whole input part, whether or not all its rows fit in the shard
    }, indent=2) + "\n", encoding="utf-8", newline="\n")

    token_count = int(starts[-1])
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    manifest = {
        "schema_version": "shard-v1", "dataset_version": "test" if a.any_tokenizer else "sample", "shard_id": shard_id,
        "format": "brahmic_u32_v2+doc_index", "token_dtype": "uint32",
        "payload_uri": bin_path.name, "payload_sha256": sha(bin_path), "payload_bytes": bin_path.stat().st_size,
        "index_uri": idx_path.name, "index_sha256": sha(idx_path),
        "doc_count": len(docs), "token_count": token_count, "eos_token_id": EOS_ID,
        "tokenizer_sha256": tok_sha,
        "pack_id": pack_id, "language": a.language, "script": a.script, "domain": domain, "capability_lane": a.lane,
        "split": split,
        "inputs_sha256": hashlib.sha256(f"{info['raw_input']['sha256']} {info['raw_input']['part']}\n".encode("utf-8")).hexdigest(),
        "cleaning_pipeline_sha256": sha(pipeline), "decontam_set_sha256": info["f2"]["set_sha256"],
        "sample_metadata_uri": meta_path.name, "sample_metadata_sha256": sha(meta_path),
        "quality_report_uri": report.name, "quality_report_sha256": sha(report),
        "created_by": commit,
    }
    (a.out / f"{shard_id}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    # Check the shard against its manifest, reading the .bin the way G6's loader does.
    tokens = open_shard(bin_path)
    idx = np.load(idx_path)
    meta = pq.read_table(meta_path)
    assert manifest["payload_bytes"] == HEADER_BYTES + 4 * token_count and len(tokens) == token_count <= a.tokens
    assert idx[0] == 0 and idx[-1] == token_count and len(idx) == len(docs) + 1 == meta.num_rows + 1
    assert meta.column("n_tokens").to_pylist() == np.diff(idx).tolist()
    assert int(tokens.max()) < VOCAB
    special_at = np.flatnonzero(np.isin(tokens, sorted(specials)))
    assert special_at.tolist() == (idx[1:] - 1).tolist(), "a special id other than the final EOS of a doc"
    assert (tokens[idx[1:] - 1] == EOS_ID).all()
    for k, d in enumerate(docs):
        assert tokens[idx[k]:idx[k + 1]].tolist() == d

    header = np.fromfile(bin_path, dtype="<i4", count=3)
    n, lo = meta.num_rows, {k: len(v) for k, v in left_out.items()}
    lines = [f"# Shard `{shard_id}`\n\n",
             f"Written by `shard_writer.py` from `{s['pack']}` of `{pack_id}`, after `clean.py` and F2 (fingerprints "
             f"part's {info['counts']['cleaned']:,} docs removed) and F2 ({info['counts']['dropped_by_f2']:,} dropped; fingerprints "
             f"`{s['f2']['set_sha256'][:12]}`): the first {n:,} docs that fit in {a.tokens:,} tokens, of {seen:,} rows read.\n\n",
             f"Tokenizer `{tok_sha[:12]}`" + (" (**not p1536: test only**)" if tok_sha != TOKENIZER_SHA256 else " (p1536, frozen)") +
             f"; EOS `{EOS}` id {EOS_ID} after each doc; no BOS, no language tag.\n\n",
             f"Left out: {lo['secret']} secret-like, {lo['empty']} empty, {lo['special']} with a special id inside, "
             f"{lo['roundtrip']} not round-tripping (doc_ids in `{shard_id}.quality_report.json`).\n\n",
             "| file | bytes | sha256 |\n|---|---:|---|\n",
             *(f"| `{p.name}` | {p.stat().st_size:,} | `{sha(p)[:16]}…` |\n" for p in (bin_path, idx_path, meta_path, pipeline, report)),
             f"\n## `{bin_path.name}`\n\n- header, {HEADER_BYTES:,} bytes = 256 little-endian int32: `{header[0]}` (magic), "
             f"`{header[1]}` (version), `{header[2]:,}` (token count), then zeros\n"
             f"- then {token_count:,} little-endian uint32 token IDs; every doc ends with {EOS_ID}, and no other special id occurs\n"
             f"- tokens per character: median {np.median(tpc):.3f}, max {tpc.max():.3f}\n\n",
             f"## `{idx_path.name}`\n\nint64, {n + 1:,} entries (start of each doc, then token_count): "
             f"`{idx[:5].tolist()} … {idx[-2:].tolist()}`\n\n",
             f"## `{meta_path.name}`\n\nOne row per doc in shard order, IDs and counts only. First rows:\n\n"
             "| doc_id | input_part | input_row | n_tokens | n_chars | lang_label |\n|---|---|---:|---:|---:|---|\n",
             *(f"| `{r['doc_id']}` | `{r['input_part']}` | {r['input_row']:,} | {r['n_tokens']:,} | {r['n_chars']:,} | "
               f"{r['lang_label']} |\n" for r in rows[:5])]
    (a.out / f"{shard_id}.dump.md").write_text("".join(lines), encoding="utf-8", newline="\n")
    print(json.dumps({"shard_id": shard_id, "docs": n, "tokens": token_count, "rows_read": seen, "left_out": lo,
                      "tokens_per_char_median": round(float(np.median(tpc)), 3), "tokenizer": tok_sha[:12]}))
    return manifest


if __name__ == "__main__":
    main()
