"""Fill text_bytes and tokens_p1536 in dataset_list.csv without downloading data.

text_bytes: reads only the Parquet footers of up to 3 files per row (column sizes are in the footer), takes
  ratio = uncompressed size of the text column(s) / file size, then text_bytes = stored_bytes x ratio.
tokens_p1536 = text_bytes / p1536 bytes per token, from G3's measurement on the held-out part of each
  Stage 1 pack (teams/03-tokenizer/results/fertility_domains.json). In-38 rows use their own pack's rate;
  new rows use the mean rate of their part's packs.

Usage: python text_bytes.py dataset_list.csv fertility_domains.json
"""
import csv, json, sys
from statistics import mean
import pyarrow.parquet as pq
from huggingface_hub import HfApi, HfFileSystem

api, fs = HfApi(), HfFileSystem()
TEXT_COLS = ["text", "content"]
PART_PACKS = {
    "code": ["code-cpp", "code-go", "code-java", "code-js-ts", "code-python", "code-rust"],
    "synthetic code": ["code-cpp", "code-go", "code-java", "code-js-ts", "code-python", "code-rust"],
    "code-adjacent": ["cadj-commits", "cadj-notebooks", "cadj-stackexchange"],
    "English real": ["en-dclm", "en-fineweb-edu", "en-nemotroncc"],
    "English synthetic": ["en-nemotroncc-synth"],
    "math": ["math-finemath", "math-megamath"],
    "science": ["sci-finepdfs"],
}


def text_ratio(repo, rev, paths):
    files = []
    for p in paths.split(";"):
        for f in api.list_repo_tree(repo, repo_type="dataset", path_in_repo=None if p == "." else p, revision=rev, recursive=True):
            if getattr(f, "size", None) and f.path.endswith(".parquet"):
                files.append(f)
    if not files:
        return None, "no parquet files (jsonl or ids only)"
    pick = [files[i * (len(files) - 1) // 2] for i in range(3)] if len(files) >= 3 else files
    text = size = 0
    cols_used = set()
    for f in {x.path: x for x in pick}.values():
        md = pq.ParquetFile(fs.open(f"datasets/{repo}@{rev}/{f.path}", block_size=256 * 1024)).metadata
        names = [md.schema.column(i).path for i in range(md.num_columns)]
        want = [n for n in names if n in TEXT_COLS] or [md.schema.column(i).path for i in range(md.num_columns)
                                                         if md.schema.column(i).physical_type == "BYTE_ARRAY"]
        cols_used.update(want)
        for g in range(md.num_row_groups):
            rg = md.row_group(g)
            for c in range(rg.num_columns):
                if rg.column(c).path_in_schema in want:
                    text += rg.column(c).total_uncompressed_size
        size += f.size
    return text / size, "footer of %d files; columns: %s" % (len(pick), ",".join(sorted(cols_used)))


def main(csv_path, fert_path):
    packs = json.load(open(fert_path, encoding="utf-8"))["packs"]
    rate = {k: v["p1536_bytes_per_token"] for k, v in packs.items()}
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    cols = list(rows[0].keys())
    for c in ["p1536_bytes_per_token", "rate_source", "text_source"]:
        if c not in cols:
            cols.insert(cols.index("tokens_p1536") + 1, c)
    for r in rows:
        if r.get("pack_id") in rate:
            r["p1536_bytes_per_token"], r["rate_source"] = str(rate[r["pack_id"]]), f"G3 fertility_domains, {r['pack_id']}"
        elif r["part"] in PART_PACKS:
            r["p1536_bytes_per_token"] = "%.3f" % mean(rate[p] for p in PART_PACKS[r["part"]])
            r["rate_source"] = "G3 fertility_domains, mean of " + "+".join(PART_PACKS[r["part"]])
        if r.get("text_bytes") or not (r["hub_paths"] and r["stored_bytes"]):
            continue
        try:
            ratio, how = text_ratio(r["hub_id"], r["revision"], r["hub_paths"])
        except Exception as e:  # gated without access, or unreadable footer
            ratio, how = None, f"not read: {type(e).__name__}"
        r["text_source"] = how
        if ratio:
            r["text_bytes"] = str(int(int(r["stored_bytes"]) * ratio))
            r["tokens_p1536"] = str(int(int(r["text_bytes"]) / float(r["p1536_bytes_per_token"])))
        print(f"{r['dataset'][:38]:38} ratio={ratio and round(ratio, 2)}  tokens={int(r['tokens_p1536'] or 0) / 1e9:9.1f}B  {how}", flush=True)
    w = csv.DictWriter(open(csv_path, "w", newline="", encoding="utf-8"), fieldnames=cols)
    w.writeheader()
    w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
