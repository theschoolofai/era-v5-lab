"""Fill revision and stored_bytes in dataset_list.csv from Hugging Face metadata. No data is downloaded.

Usage: python hub_meta.py dataset_list.csv
Rows need hub_id and hub_paths (folders in the repo, ';'-separated). Other rows are left as they are.
"""
import csv, sys
from huggingface_hub import HfApi

api = HfApi()


def folder_bytes(repo, rev, path):
    files = api.list_repo_tree(repo, repo_type="dataset", path_in_repo=None if path == "." else path, revision=rev, recursive=True)
    sizes = [getattr(f, "size", 0) or 0 for f in files if getattr(f, "size", None) is not None]
    return sum(sizes), len(sizes)


def main(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    shas = {}
    for r in rows:
        if not (r["hub_id"] and r["hub_paths"]) or r["stored_bytes"]:
            continue  # ponytail: rows already sized are skipped; blank stored_bytes to re-pull
        repo = r["hub_id"]
        if repo not in shas:
            shas[repo] = api.dataset_info(repo).sha
        total, n = 0, 0
        for p in r["hub_paths"].split(";"):
            b, k = folder_bytes(repo, shas[repo], p)
            total, n = total + b, n + k
        r["revision"], r["stored_bytes"] = shas[repo], str(total)
        print(f"{r['pack_id'] or r['dataset']:22} {repo:42} {total / 1e9:10.1f} GB  {n} files", flush=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1])
