"""Turn the week-2 tokenizer sample v0 (raw parquet) into the <lang>.txt corpus that train_bpe.py reads.

Only train/ parts go into the corpus. Each part is checked against the sample's SHA256SUMS first, so renamed downloads
(e.g. "part-00000 (12).parquet") are found by hash. Documents are written in pack-name order, then row order, as
text.strip() + "\\n" (the fetch_corpus.py format). A language with no pack in the sample can be copied from another
corpus directory with --fallback (its manifest entry is copied too and marked as such).

--heldout-out writes the sample's heldout/ parts as evaluation text, never as training text: <dir>/all/<lang>.txt
(Indic languages, En = en-* packs, Code = code-* packs) and two document halves, <dir>/a (even documents, used by
mix_search.py to choose) and <dir>/b (odd documents, used to confirm).

    python sample_to_corpus.py --sample <dir with SHA256SUMS and the parquet files> --out <corpus dir> \\
        --fallback <corpus60 dir> --fallback-langs Pa,As --heldout-out <heldout_s0 dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

# Paper label -> sample pack language code (pack ids are ind-<code>-<source>). Same 11 languages as fetch_corpus.py.
LANGS = {"Hi": "hi", "Bn": "bn", "Ta": "ta", "Te": "te", "Kn": "kn", "Ml": "ml", "Mr": "mr", "Gu": "gu",
         "Pa": "pa", "Or": "or", "As": "as"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sample_parts(sample: Path, split: str) -> dict[str, Path]:
    """SHA256SUMS path (<split>/<pack>/part-*.parquet) -> local file with that sha256."""
    want = {}
    for line in (sample / "SHA256SUMS").read_text().splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            if name.startswith(f"{split}/") and name.endswith(".parquet"):
                want[digest] = name.strip()
    found = {}
    for f in sorted(sample.glob("*.parquet")) + sorted(sample.glob(f"{split}/*/*.parquet")):
        digest = sha256_file(f)
        if digest in want:
            found.setdefault(want[digest], f)
    missing = sorted(set(want.values()) - set(found))
    if missing:
        sys.exit(f"ERROR: {split} parts in SHA256SUMS with no matching local file: {missing}")
    return found


def texts(pq, files):
    for f in files:
        for text in pq.read_table(f, columns=["text"]).column("text").to_pylist():
            text = (text or "").strip()
            if text:
                yield text


def write_heldout(pq, sample: Path, out: Path):
    parts = sample_parts(sample, "heldout")
    groups = {"En": "en-", "Code": "code-", **{lang: f"ind-{code}-" for lang, code in LANGS.items()}}
    for lang, prefix in groups.items():
        names = sorted(n for n in parts if n.split("/")[1].startswith(prefix))
        if not names:
            continue
        docs = list(texts(pq, [parts[n] for n in names]))
        for sub, chosen in (("all", docs), ("a", docs[0::2]), ("b", docs[1::2])):
            (out / sub).mkdir(parents=True, exist_ok=True)
            (out / sub / f"{lang}.txt").write_text("".join(d + "\n" for d in chosen), encoding="utf-8")
        print(f"heldout {lang}: {len(names)} packs, {len(docs)} docs", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sample", required=True, help="directory with SHA256SUMS and the downloaded parquet files")
    ap.add_argument("--out", required=True, help="output corpus directory (outside the repo)")
    ap.add_argument("--fallback", help="corpus directory (fetch_corpus.py output) for languages not in the sample")
    ap.add_argument("--fallback-langs", default="", help='comma list, e.g. "Pa,As"')
    ap.add_argument("--heldout-out", help="also write the heldout/ parts as evaluation text here (all/, a/, b/)")
    args = ap.parse_args()

    import pyarrow.parquet as pq

    sample, out = Path(args.sample), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    parts = sample_parts(sample, "train")
    fallback = [x for x in args.fallback_langs.split(",") if x]
    manifest = {}
    for lang, code in LANGS.items():
        if lang in fallback:
            if not args.fallback:
                sys.exit("ERROR: --fallback-langs needs --fallback.")
            src = Path(args.fallback)
            shutil.copyfile(src / f"{lang}.txt", out / f"{lang}.txt")
            entry = json.loads((src / "corpus_manifest.json").read_text())[lang]
            manifest[lang] = {**entry, "from": f"fallback: {src.name} (not in sample v0)"}
            print(f"{lang}: copied from {src.name}, {entry['bytes'] / 1e6:.1f} MB", flush=True)
            continue
        names = sorted(n for n in parts if n.split("/")[1].startswith(f"ind-{code}-"))
        if not names:
            sys.exit(f"ERROR: no train pack for {lang} (ind-{code}-*) in the sample; add it to --fallback-langs.")
        h = hashlib.sha256()
        n_docs = n_bytes = 0
        with (out / f"{lang}.txt").open("w", encoding="utf-8") as f:
            for text in texts(pq, [parts[n] for n in names]):
                chunk = text + "\n"
                f.write(chunk)
                b = chunk.encode("utf-8")
                h.update(b)
                n_docs += 1
                n_bytes += len(b)
        manifest[lang] = {"packs": [n.split("/")[1] for n in names],
                          "parts": {n: sha256_file(parts[n]) for n in names},
                          "file": f"{lang}.txt", "docs": n_docs, "bytes": n_bytes, "sha256": h.hexdigest(),
                          "from": "sample v0 train/"}
        print(f"{lang}: {len(names)} packs, {n_docs} docs, {n_bytes / 1e6:.1f} MB, sha256 {h.hexdigest()[:12]}",
              flush=True)
    (out / "corpus_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"wrote {out / 'corpus_manifest.json'}")
    if args.heldout_out:
        write_heldout(pq, sample, Path(args.heldout_out))


if __name__ == "__main__":
    main()
