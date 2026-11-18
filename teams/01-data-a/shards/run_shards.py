"""Write a shard for every part in a pipeline run's final folder: shard_writer.py once per part.

  python -I teams/01-data-a/shards/run_shards.py --input <run>/final --manifest <run>/pipeline_manifest.json \
      --tokenizer <p1536>/tokenizer.json --dataset-version corpus-v1 --out <dir> [--pack code-go ...] [--tokens N]
      [--any-tokenizer]

--input is the run's final folder: <input>/<split>/<pack>/<part>.parquet, the layout run_pipeline.py gives it. Every part
found is handed to shard_writer.py (the split comes from the folder name), except a part in a folder named in
NOT_SHARDED (heldout, validation, val): it is reported as "not_sharded", which is not an error, because what a held-out
part becomes is for G3 and G9 to say. Language, script, domain and lane come from the pack's row in pack_table.json (--pack-table
for another table, such as a job's; one that also gives "license" and "license_source" has both written into every manifest); a pack that is not in the
table, or has a null field, is not sharded (status "skipped").

Shard numbers run across the parts of a pack and split, in part order: the writer fills a shard up to --tokens and rolls
over into the next number, so a part gets one shard or several, and the next part starts at the number after its last.
Without a rollover, part-00000 gets <pack>-<split>-000000, part-00001 gets 000001, and so on.

Before anything is written it checks that --out holds no shard of a pack it would write, and stops if it does.
A part the writer stops on (a broken link in its chain, ...) is recorded as "failed" and the run goes on.
It exits 1 unless every part was written or not_sharded.

Writes <out>/shards_summary.json: for each part its status; for a written part its shards (the part-to-shards map: each
shard_id with its docs, tokens and the rows first_row..rows_read-1 of the part it covers), the docs, tokens and rows read
summed over them, rows_in_part, "truncated" (rows_read < rows_in_part: never, now that the writer rolls over; kept as a
check) and the docs left out per reason, with the run_id and the sha256 of cleaning_pipeline.json. A second run into the same --out
with --pack adds to the summary; one made for another run_id is refused, and the writer refuses other processing part by part.
Needs what shard_writer.py needs.
"""
import sys
sys.dont_write_bytecode = True

import argparse, contextlib, hashlib, io, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pack_table  # noqa: E402
import shard_writer  # noqa: E402

SUMMARY = "shards_summary.json"
NOT_SHARDED = ("heldout", "validation", "val")  # split folders that are left alone (shard_writer.py also refuses a non-train part)


def find_parts(final, packs=()):
    """[(split, pack, part file)] of <final>/<split>/<pack>/*.parquet, sorted; only `packs` if given."""
    found = []
    for path in sorted(Path(final).glob("*/*/*.parquet")):
        split, pack = path.parent.parent.name, path.parent.name
        if not packs or pack in packs:
            found.append((split, pack, path))
    return found


def shards_of(out, split, pack):
    """The manifests <pack>-<split>-<6 digits>.json already in out."""
    return sorted(p.name for p in Path(out).glob(f"{pack}-{split}-*.json")
                  if re.fullmatch(rf"{re.escape(pack)}-{re.escape(split)}-\d{{6}}\.json", p.name))


def write_one(path, a, row, index):
    """Run shard_writer on one part, its first shard numbered index. Returns ([manifest, ...], None) or (None, why it stopped)."""
    argv = ["--input", str(path), "--manifest", str(a.manifest), "--tokenizer", str(a.tokenizer), "--out", str(a.out),
            "--language", row["language"], "--script", row["script"], "--domain", row["domain"], "--lane", row["lane"],
            "--index", str(index)]
    if "license" in row:  # a table with licences (pack_table.LICENCE): both go into the manifest
        argv += ["--license", row["license"], "--license-source", row["license_source"]]
    if a.tokens:
        argv += ["--tokens", str(a.tokens)]
    if a.any_tokenizer:
        argv.append("--any-tokenizer")
    if a.dataset_version:
        argv += ["--dataset-version", a.dataset_version]
    try:
        with contextlib.redirect_stdout(io.StringIO()):  # the writer prints a JSON line per shard; the summary has it
            return shard_writer.main(argv), None
    except SystemExit as e:
        return None, str(e.code)
    except Exception as e:  # one bad part must not stop the others
        return None, f"{type(e).__name__}: {e}"


def entry_of(manifests, out):
    """The summary entry of a written part, from its shards' manifests and quality reports."""
    shards, left_out = [], {k: 0 for k in shard_writer.LEFT_OUT}
    for m in manifests:
        report = json.loads((out / f"{m['shard_id']}.quality_report.json").read_text(encoding="utf-8"))
        shards.append({"shard_id": m["shard_id"], "docs": m["doc_count"], "tokens": m["token_count"],
                       "first_row": report["first_row"], "rows_read": report["rows_read"]})
        for k, v in report["left_out"].items():
            left_out[k] += v
    rows_in_part = report["upstream"]["counts"]["final"]
    return {"status": "written", "shards": shards, "docs": sum(x["docs"] for x in shards), "tokens": sum(x["tokens"] for x in shards),
            "rows_read": shards[-1]["rows_read"], "rows_in_part": rows_in_part, "truncated": shards[-1]["rows_read"] < rows_in_part,
            "left_out": left_out}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, required=True, help="the run's final folder: <input>/<split>/<pack>/<part>.parquet")
    ap.add_argument("--manifest", type=Path, required=True, help="the run's pipeline_manifest.json")
    ap.add_argument("--tokenizer", type=Path, required=True, help="G3's frozen p1536 tokenizer.json")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pack", action="append", default=[], help="only this pack (repeatable)")
    ap.add_argument("--tokens", type=int, help="fill each shard up to this many tokens (shard_writer's default: 2^26)")
    ap.add_argument("--any-tokenizer", action="store_true", help="tests only: accept a tokenizer other than p1536")
    ap.add_argument("--dataset-version", help="every manifest's dataset_version (e.g. sample, corpus-v1); required unless --any-tokenizer")
    ap.add_argument("--pack-table", type=Path, default=pack_table.TABLE)
    a = ap.parse_args(argv)
    problem = shard_writer.dataset_version_problem(a.dataset_version, a.any_tokenizer)
    if problem:  # before anything is read or written: every part would fail on it
        sys.exit(f"run_shards: {problem}")

    table = pack_table.load(a.pack_table)
    parts = find_parts(a.input, a.pack)
    if not parts:
        sys.exit(f"run_shards: no <split>/<pack>/<part>.parquet in {a.input}" + (f" for {a.pack}" if a.pack else ""))
    run_id = json.loads(a.manifest.read_text(encoding="utf-8")).get("run_id")
    summary_path = a.out / SUMMARY
    summary = {"parts": {}}
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary["run_id"] != run_id:
            sys.exit(f"run_shards: {summary_path} is from another pipeline run ({summary['run_id']}) than {a.manifest} ({run_id}); use a new --out")
    taken = [n for split, pack in sorted({(s, p) for s, p, _ in parts if s not in NOT_SHARDED}) for n in shards_of(a.out, split, pack)]
    if taken:
        sys.exit(f"run_shards: already in {a.out}: {', '.join(taken[:5])}{' ...' if len(taken) > 5 else ''}. Nothing was written; "
                 "use a new --out, or --pack for the other packs")

    this_run, next_index = [], {}  # (split, pack) -> the number of its next shard
    for split, pack, path in parts:
        name = f"{split}/{pack}/{path.name}"
        if split in NOT_SHARDED:
            entry = {"pack_id": pack, "status": "not_sharded", "reason": f"{split} is not sharded (held-out data: G3 and G9 decide)"}
        else:
            entry = {"pack_id": pack}
            try:
                row = pack_table.row(pack, table)
            except pack_table.PackTableError as e:
                entry.update(status="skipped", reason=str(e))
            else:
                index = next_index.get((split, pack), 0)
                manifests, why = write_one(path, a, row, index)
                if why:
                    entry.update(status="failed", reason=why)
                else:
                    entry.update(entry_of(manifests, a.out))
                    next_index[(split, pack)] = index + len(manifests)
        summary["parts"][name] = entry
        this_run.append(entry["status"])
        note = f"{len(entry['shards'])} shard(s), {entry['docs']} docs, {entry['tokens']} tokens" + (" TRUNCATED" if entry["truncated"] else "") \
            if entry["status"] == "written" else entry["reason"]
        print(f"{entry['status']:8} {name}: {note}", file=sys.stderr if entry["status"] in ("failed", "skipped") else sys.stdout)

    pipeline = a.out / "cleaning_pipeline.json"  # written by the writer with the run's first shard
    summary = {"run_id": run_id, "cleaning_pipeline_sha256": hashlib.sha256(pipeline.read_bytes()).hexdigest() if pipeline.is_file() else None,
               "parts": summary["parts"]}
    entries = summary["parts"].values()
    summary["counts"] = {s: sum(e["status"] == s for e in entries) for s in ("written", "failed", "skipped", "not_sharded")}
    summary["counts"]["truncated"] = sum(bool(e.get("truncated")) for e in entries)
    summary["counts"]["shards"] = sum(len(e.get("shards", [])) for e in entries)
    a.out.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summary["counts"]))
    return 0 if set(this_run) <= {"written", "not_sharded"} else 1  # this run's parts, not those an earlier run left in the summary


if __name__ == "__main__":
    sys.exit(main())
