r"""KE2's request R1 (Team 4, Lab 5): a word-frequency table of the 38 sample packs, per language and lane.

    python -I teams/01-data-a/ke2/word_freq.py --packs <folder with the 38 raw packs> --out out/ke2_r1

What it counts. The train split of every pack in approved_inputs.json (the 38 sample-v0 packs): every train part that
the sample-v0 manifest lists (48 parts), each checked against the manifest's sha256 and row count, every document's text,
word by word. Held-out parts are not read (they are KE2's R2, text no training shard holds).

The word rule.
  1. The text is put in NFC, the lab's only normalization (no NFKC, no case folding).
  2. A word is a maximal run of letters and combining marks (Unicode categories L* and M*), so Indic vowel signs,
     viramas and nuktas stay inside the word. ZWJ (U+200D) and ZWNJ (U+200C) are part of a word when letters or marks
     stand on both sides of them; at a word's edge they are dropped.
  3. Everything else ends a word: digits, '_', apostrophes, hyphens, punctuation, symbols and spaces. So "don't" is
     "don" + "t", "x_velocity" is "x" + "velocity" (identifiers as written are R3's), and "COVID-19" is "COVID".
  4. Case is kept as written: "The" and "the" are counted apart; fold them if your test needs that.

Language and lane. Each pack's "language" and "lane" from approved_inputs.json, as on the shard manifests: for code
packs the language is the programming language (cpp, go, java, js-ts, python, rust) and the lane is code; for the
code-adjacent packs it is "code" or "en". One file per (lane, language): words of all the packs in that pair, summed.

What it writes, in --out (inside the repository's out/, which is not committed):
  <lane>__<language>.csv   word,count,lang,lane, sorted by count (descending) then word; UTF-8, no BOM
  packs.csv                pack_id,lang,lane,source,license,license_source,docs,words,distinct_words,file:
                           which packs went into which file, with each pack's licence (KE2's licence column)
  r1_summary.json          the rule, the inputs (path, rows, sha256 of every part read), per file its words, distinct
                           words and sha256, and the versions

Only words and counts leave the packs: no document, sentence or doc_id is written.
Needs pyarrow and regex.
"""
import sys
sys.dont_write_bytecode = True

import argparse, csv, hashlib, json, platform, time, unicodedata  # noqa: E402
from collections import Counter, defaultdict  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
APPROVED = REPO / "teams/01-data-a/jobs/2026-11-19-first-training/approved_inputs.json"
MANIFEST = REPO / "teams/01-data-a/jobs/2026-11-02-tokenizer-sample-v0-clean/tokenizer_sample_v0_manifest.json"
WORD = r"[\p{L}\p{M}]+(?:[‌‍]+[\p{L}\p{M}]+)*"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def words(text):
    import regex
    return regex.findall(WORD, unicodedata.normalize("NFC", text))


def train_parts(packs_root, pack_id, listed):
    """The pack's train parts that the sample manifest lists, found by size and sha256 under <root>/train/<pack>/ or
    <root>/<pack>/ (the course download's Part_N folders), in the manifest's order. Stops if any listed part is missing."""
    root = Path(packs_root)
    files = sorted((root / "train" / pack_id).glob("*.parquet")) + sorted((root / pack_id).rglob("*.parquet"))
    by_size = defaultdict(list)
    for f in dict.fromkeys(files):
        by_size[f.stat().st_size].append(f)
    found = []
    for part in listed:
        match = [f for f in by_size.get(part["bytes"], []) if sha256(f) == part["sha256"]]
        if not match:
            raise SystemExit(f"ERROR: {pack_id}: no file under {root} has the sha256 of {part['path']} ({part['sha256'][:12]}...)")
        found.append((match[0], part))
    return found


def count_pack(job):
    """Count one pack's train parts. Returns (pack_id, Counter, docs, parts info)."""
    import pyarrow.parquet as pq
    pack_id, found = job
    counts, docs, parts = Counter(), 0, []
    for p, listed in found:
        pf = pq.ParquetFile(p)
        if pf.metadata.num_rows != listed["rows"]:
            raise SystemExit(f"ERROR: {p} has {pf.metadata.num_rows} rows, the manifest lists {listed['rows']}")
        if "text" not in pf.schema_arrow.names:
            raise SystemExit(f"ERROR: {p} has no text column")
        for batch in pf.iter_batches(batch_size=2000, columns=["text"]):
            for text in batch.column(0).to_pylist():
                docs += 1
                if text:
                    counts.update(words(text))
        parts.append({"path": listed["path"], "rows": listed["rows"], "sha256": listed["sha256"]})
    return pack_id, counts, docs, parts


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--packs", required=True, help="folder with the 38 raw packs (<pack>/Part_*/ or train/<pack>/)")
    ap.add_argument("--out", default="out/ke2_r1", help="output folder inside the repository's out/")
    ap.add_argument("--approved", default=str(APPROVED), help="approved_inputs.json (packs, language, lane, licence)")
    ap.add_argument("--manifest", default=str(MANIFEST), help="sample-v0 manifest: every train part, its rows and sha256")
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    out = (REPO / a.out).resolve() if not Path(a.out).is_absolute() else Path(a.out).resolve()
    if (REPO / "out").resolve() not in out.parents:
        raise SystemExit("ERROR: --out must be inside the repository's out/ folder (not committed)")
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"ERROR: {out} is not empty")
    out.mkdir(parents=True, exist_ok=True)

    approved = json.loads(Path(a.approved).read_text(encoding="utf-8"))
    packs = {p["pack_id"]: p for p in approved["packs"]}
    t0 = time.time()
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    listed = defaultdict(list)
    for part in manifest["shards"]:
        if part["split"] == "train":
            listed[part["pack_id"]].append(part)
    missing = sorted(set(packs) - set(listed))
    if missing:
        raise SystemExit(f"ERROR: the manifest lists no train part for {missing}")
    jobs = [(pid, train_parts(a.packs, pid, listed[pid])) for pid in sorted(packs)]
    groups, pack_rows, inputs = defaultdict(Counter), [], []
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for pid, counts, docs, parts in pool.map(count_pack, jobs):
            p = packs[pid]
            key = (p["lane"], p["language"])
            groups[key].update(counts)
            pack_rows.append({"pack_id": pid, "lang": p["language"], "lane": p["lane"], "source": p.get("source"),
                              "license": p.get("license"), "license_source": p.get("license_source"), "docs": docs,
                              "words": sum(counts.values()), "distinct_words": len(counts),
                              "file": f"{key[0]}__{key[1]}.csv"})
            inputs.extend(dict(part, pack_id=pid) for part in parts)
            print(f"{pid}: {docs:,} docs, {sum(counts.values()):,} words, {len(counts):,} distinct", flush=True)

    files = {}
    for (lane, lang), counts in sorted(groups.items()):
        name = f"{lane}__{lang}.csv"
        with open(out / name, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["word", "count", "lang", "lane"])
            for word, n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
                w.writerow([word, n, lang, lane])
        files[name] = {"lang": lang, "lane": lane, "words": sum(counts.values()), "distinct_words": len(counts),
                       "bytes": (out / name).stat().st_size, "sha256": sha256(out / name)}
    with open(out / "packs.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pack_rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(pack_rows, key=lambda r: (r["file"], r["pack_id"])))
    import pyarrow, regex
    summary = {
        "request": "KE2 (Team 4) R1: word frequency table of the 38 sample packs, per language and lane",
        "word_rule": {"normalization": "NFC", "pattern": WORD, "case": "kept as written",
                      "separators": "everything that is not a letter or a mark (digits, _, ', -, punctuation, spaces)",
                      "joiners": "ZWJ/ZWNJ kept inside a word, dropped at its edges"},
        "split": "train", "approved_inputs_sha256": sha256(a.approved), "manifest_sha256": sha256(a.manifest),
        "packs": len(pack_rows), "parts": len(inputs),
        "docs": sum(r["docs"] for r in pack_rows), "files": files, "inputs": inputs,
        "seconds": round(time.time() - t0, 1),
        "versions": {"python": platform.python_version(), "pyarrow": pyarrow.__version__, "regex": regex.__version__,
                     "unicodedata": unicodedata.unidata_version},
    }
    (out / "r1_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(files)} files, {summary['docs']:,} docs, {summary['seconds']} s -> {out}")


if __name__ == "__main__":
    main()
