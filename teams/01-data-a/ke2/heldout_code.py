r"""KE2's request R3 (Team 4, Lab 5): held-out code with identifiers (Python, JS/TS, C++), cleaned and through F2.

    python -I teams/01-data-a/ke2/heldout_code.py --packs <folder with the raw sample-v0 packs> --out out/ke2_r3

What it takes. The held-out part of code-python, code-js-ts and code-cpp that the sample-v0 manifest lists (one part per
pack), found under --packs by size and sha256 and checked against the manifest's row count. These are the docs that no
train part holds (the sample's held-out split); train parts are read only to check that.

What it does to each held-out doc, in order (each step's counts go to r3_summary.json):
  1. Exact match with train: a doc whose text is byte-for-byte the text of a doc in the same pack's train parts is
     left out, so nothing KE2 gets is in training.
  2. Clean: the pipeline's pinned cleaner (pipeline/clean.json: "clean" and "clean_sha256"), clean.clean(doc), unchanged.
     A doc it drops is left out; a fixed doc keeps the fixed text. So the text looks like the training text (StarCoder's
     <reponame>/<filename>/<gh_stars> lines and the other code rules applied). On a Windows checkout the cleaner has CRLF
     line endings; if its bytes miss the pin but its LF form hits it, the LF form is what runs (logged as crlf_to_lf).
  3. F2: spec_v1/run_f2.py's run_file() with G9's pinned fingerprint set (v2), unchanged: a doc sharing a run of
     20 code tokens with a benchmark item, or holding a canary string, is left out. F2 is G9's decontam check
     (decontam/fpset.py) and canary strings; there is no other check to run.

What it writes, in --out (inside the repository's out/, which is not committed; it holds document text):
  code__<lang>/docs.parquet  doc_id, text, url, lang, lane, pack_id, source, license, license_source; sorted by doc_id.
                             url is StarCoder's repo/path of the file: the attribution its licence asks for.
  r3_summary.json            inputs (path, rows, sha256), the cleaner, run_f2.py and set sha256, per language the counts
                             of every step, the doc_ids F2 dropped with their benchmark items, bytes of text, identifier
                             counts and each docs.parquet's sha256. No document text.
  work/                      the cleaned parts and F2's own outputs and .f2.json reports (intermediate).

Identifiers (for the summary only). A run [A-Za-z_][A-Za-z0-9_]* that has an inner '_' (x_velocity) or a lower-to-upper
step (xVelocity) counts as a compound identifier; distinct and total counts per language.
Needs pyarrow and regex (the cleaner's and F2's imports).
"""
import sys
sys.dont_write_bytecode = True

import argparse, hashlib, importlib.util, json, platform, re, time, types  # noqa: E402
from collections import defaultdict  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
from word_freq import sha256, train_parts  # noqa: E402  (finds a manifest part by size and sha256)

APPROVED = REPO / "teams/01-data-a/jobs/2026-11-19-first-training/approved_inputs.json"
MANIFEST = REPO / "teams/01-data-a/jobs/2026-11-02-tokenizer-sample-v0-clean/tokenizer_sample_v0_manifest.json"
CLEAN_SETTINGS = REPO / "teams/01-data-a/pipeline/clean.json"
RUN_F2 = REPO / "teams/01-data-a/spec_v1/run_f2.py"
PACKS = ("code-python", "code-js-ts", "code-cpp")
COLUMNS = ("doc_id", "text", "url", "lang", "lane", "pack_id", "source", "license", "license_source")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
COMPOUND = re.compile(r"[A-Za-z0-9]_[A-Za-z0-9]|[a-z][A-Z]")


def text_key(text):
    return hashlib.blake2b((text or "").encode("utf-8"), digest_size=16).digest()


def load_cleaner(path, pin):
    """The cleaner as a module once its sha256 is the pin (as clean_job.load_clean), or its LF form's on a CRLF checkout.
    The bytes that are hashed are the bytes that run."""
    source = Path(path).read_bytes()
    crlf_to_lf = False
    if hashlib.sha256(source).hexdigest() != pin:
        lf = source.replace(b"\r\n", b"\n")
        if hashlib.sha256(lf).hexdigest() != pin:
            raise SystemExit(f"ERROR: {path} differs from the pin {pin[:12]}... (also with LF line endings)")
        source, crlf_to_lf = lf, True
    module = types.ModuleType("clean")
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module, crlf_to_lf


def load_run_f2(path=RUN_F2):
    spec = importlib.util.spec_from_file_location("run_f2", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def identifiers(texts):
    distinct, total = set(), 0
    for t in texts:
        for w in IDENT.findall(t):
            if COMPOUND.search(w):
                distinct.add(w)
                total += 1
    return {"compound_distinct": len(distinct), "compound_total": total}


def main(argv=None):
    import pyarrow as pa
    import pyarrow.parquet as pq
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--packs", required=True, help="folder with the raw sample-v0 packs (<pack>/... or train|heldout/<pack>/)")
    ap.add_argument("--out", default="out/ke2_r3", help="output folder inside the repository's out/")
    ap.add_argument("--approved", default=str(APPROVED))
    ap.add_argument("--manifest", default=str(MANIFEST))
    ap.add_argument("--clean-settings", default=str(CLEAN_SETTINGS))
    a = ap.parse_args(argv)
    out = (REPO / a.out).resolve() if not Path(a.out).is_absolute() else Path(a.out).resolve()
    if (REPO / "out").resolve() not in out.parents:
        raise SystemExit("ERROR: --out must be inside the repository's out/ folder (not committed)")
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"ERROR: {out} is not empty")

    t0 = time.time()
    approved = {p["pack_id"]: p for p in json.loads(Path(a.approved).read_text(encoding="utf-8"))["packs"]}
    listed = defaultdict(list)
    for part in json.loads(Path(a.manifest).read_text(encoding="utf-8"))["shards"]:
        listed[(part["pack_id"], part["split"])].append(part)
    settings = json.loads(Path(a.clean_settings).read_text(encoding="utf-8"))
    cleaner_path = REPO / settings["clean"]
    cleaner, crlf_to_lf = load_cleaner(cleaner_path, settings["clean_sha256"])
    f2 = load_run_f2()
    fp = f2.fingerprints()  # the pinned set, checked before anything is written
    f2_sha = sha256(RUN_F2)
    out.mkdir(parents=True, exist_ok=True)

    inputs, langs = [], {}
    for pid in PACKS:
        meta = approved[pid]
        held = listed[(pid, "heldout")]
        if len(held) != 1:
            raise SystemExit(f"ERROR: the manifest lists {len(held)} held-out parts for {pid}, not 1")
        (src, part), = train_parts(a.packs, pid, held)
        train = train_parts(a.packs, pid, listed[(pid, "train")])
        in_train = set()
        for p, tpart in train:
            for batch in pq.ParquetFile(p).iter_batches(batch_size=2000, columns=["text"]):
                in_train.update(text_key(t) for t in batch.column(0).to_pylist())
        inputs.append(dict(part, pack_id=pid))
        inputs.extend(dict(tpart, pack_id=pid) for _, tpart in train)

        table = pq.read_table(src)
        if table.num_rows != part["rows"]:
            raise SystemExit(f"ERROR: {src} has {table.num_rows} rows, the manifest lists {part['rows']}")
        rows = table.to_pylist()
        counts = {"rows": len(rows), "in_train_exact": 0, "clean_dropped": 0, "clean_fixed": 0}
        kept = []
        for doc in rows:
            if text_key(doc["text"]) in in_train:
                counts["in_train_exact"] += 1
                continue
            action, text = cleaner.clean(doc)
            if action == "drop":
                counts["clean_dropped"] += 1
                continue
            if action == "fix":
                counts["clean_fixed"] += 1
            kept.append(dict(doc, text=text))
        clean_part = out / "work" / "clean" / pid / "part-00000.parquet"
        clean_part.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pylist(kept, schema=table.schema), clean_part)
        f2_part = out / "work" / "f2" / pid / "part-00000.parquet"
        report = f2.run_file(clean_part, f2_part, fp, f2_sha)
        if report["errors"]:
            raise SystemExit(f"ERROR: F2 could not check {len(report['errors'])} docs of {pid}")

        docs = sorted(pq.read_table(f2_part).to_pylist(), key=lambda d: d["doc_id"])
        final = [{"doc_id": d["doc_id"], "text": d["text"], "url": d.get("url"), "lang": meta["language"],
                  "lane": meta["lane"], "pack_id": pid, "source": d.get("source") or meta["source"],
                  "license": meta["license"], "license_source": meta["license_source"]} for d in docs]
        name = f"{meta['lane']}__{meta['language']}"
        dst = out / name / "docs.parquet"
        dst.parent.mkdir(parents=True, exist_ok=True)
        schema = pa.schema([(c, pa.string()) for c in COLUMNS])
        pq.write_table(pa.Table.from_pylist(final, schema=schema), dst, compression="zstd")
        texts = [d["text"] for d in final]
        langs[name] = {
            "pack_id": pid, "lang": meta["language"], "lane": meta["lane"], **counts,
            "f2_dropped": report["dropped_by_f2"],
            "f2_dropped_docs": [{"doc_id": d["doc_id"], "items": d["items"]} for d in report["dropped"]],
            "docs": len(final), "text_bytes": sum(len(t.encode("utf-8")) for t in texts),
            "identifiers": identifiers(texts),
            "license": meta["license"], "license_source": meta["license_source"],
            "file": f"{name}/docs.parquet", "file_bytes": dst.stat().st_size, "sha256": sha256(dst),
        }
        if counts["rows"] - counts["in_train_exact"] - counts["clean_dropped"] - report["dropped_by_f2"] != len(final):
            raise SystemExit(f"ERROR: {pid}: the step counts do not add up")
        print(f"{name}: {counts['rows']} held-out docs -> {len(final)} ({langs[name]['text_bytes'] / 1e6:.2f} MB): "
              f"{counts['in_train_exact']} in train, {counts['clean_dropped']} dropped and {counts['clean_fixed']} "
              f"fixed by the cleaner, {report['dropped_by_f2']} dropped by F2", flush=True)

    import pyarrow, regex
    summary = {
        "request": "KE2 (Team 4) R3: held-out code with identifiers (Python, JS/TS, C++), through the F2 check",
        "split": "heldout", "steps": ["exact match with the pack's train text", "pinned cleaner", "F2 (fingerprints v2)"],
        "cleaner": {"path": settings["clean"], "sha256": settings["clean_sha256"], "crlf_to_lf": crlf_to_lf},
        "run_f2_py_sha256": f2_sha, "set_sha256": fp.set_sha256,
        "approved_inputs_sha256": sha256(a.approved), "manifest_sha256": sha256(a.manifest),
        "languages": langs, "docs": sum(v["docs"] for v in langs.values()),
        "text_bytes": sum(v["text_bytes"] for v in langs.values()), "inputs": inputs,
        "seconds": round(time.time() - t0, 1),
        "versions": {"python": platform.python_version(), "pyarrow": pyarrow.__version__, "regex": regex.__version__},
    }
    (out / "r3_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                                         newline="\n")
    print(f"{summary['docs']:,} docs, {summary['text_bytes'] / 1e6:.2f} MB, {summary['seconds']} s -> {out}")


if __name__ == "__main__":
    main()
