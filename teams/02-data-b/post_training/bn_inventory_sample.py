"""bn_inventory_sample.py - seeded random samples (seed 1234, up to 300 rows) of the Bengali rows of six candidates.

Data B Lab 5 task 8 / Team 10's #882, Bengali line. The samples feed bn_sample_check.py (tokens on p1536, language
check). Every source is pinned to a revision. MultiNativQA and Bangla-Math are read from local downloads:
  hf download QCRI/MultiNativQA bangla_bd/NativQA_bn_scb_bd_train.json bangla_in/NativQA_bn_scb_in_train.json \
      --repo-type dataset --revision 018bd34d17d234b9ba1a134a6a4b437b4767c176 --local-dir <files_root>/QCRI__MultiNativQA
  hf download kawchar85/Bangla-Math BdMO.csv --repo-type dataset \
      --revision dd1e9f3bd7745bb97f34d938374c34422fefec6a --local-dir <files_root>/kawchar85__Bangla-Math

Usage: python -I bn_inventory_sample.py <out_dir> <files_root>
Remote parquet reads use row-group statistics so only row groups that can hold Bengali rows are fetched.
The samples hold dataset text, so they stay out of the repo; their sha256 are in bengali_inventory_v1.md.
"""
import csv
import json
import random
import sys
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem

SEED, N = 1234, 300
fs = HfFileSystem()
out_dir = Path(sys.argv[1])
files_root = Path(sys.argv[2])
csv.field_size_limit(1 << 30)


def write(name, rows, fields):
    rnd = random.Random(SEED)
    idx = sorted(rnd.sample(range(len(rows)), min(N, len(rows))))
    p = out_dir / f"{name}.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for i in idx:
            r = {"_row": rows[i]["_row"]}
            r.update({k: rows[i][k] for k in fields})
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, "population", len(rows), "written", len(idx))


def remote_filtered(path, fcol, fval, cols):
    """Rows where fcol == fval, reading only row groups whose min/max range can contain fval."""
    rows = []
    with fs.open(path, "rb", block_size=1 << 20) as f:
        pf = pq.ParquetFile(f)
        md = pf.metadata
        ci = pf.schema_arrow.names.index(fcol)
        base = 0
        for g in range(md.num_row_groups):
            rg = md.row_group(g)
            st = rg.column(ci).statistics
            mn = st.min if st is not None and st.has_min_max else None
            mx = st.max if st is not None and st.has_min_max else None
            ok = mn is None or (mn <= fval <= mx)
            if ok:
                t = pf.read_row_group(g, columns=[fcol] + cols).to_pylist()
                for j, r in enumerate(t):
                    if r[fcol] == fval:
                        r["_row"] = base + j
                        rows.append(r)
            base += rg.num_rows
    return rows


def remote_listcol(path, col):
    with fs.open(path, "rb", block_size=1 << 20) as f:
        pf = pq.ParquetFile(f)
        t = pf.read(columns=["doc_id", col]).to_pylist()
    rows = []
    for i, r in enumerate(t):
        # kept as published: a list of lists of strings, each inner list alternating user/assistant
        rows.append({"_row": i, "doc_id": r["doc_id"], "turns": r[col] or []})
    return rows


AYA_DS = "datasets/CohereLabs/aya_dataset@f9ea04583f02a8f86404ff6c58bf75fe637df8a2/data/train-00000-of-00001.parquet"
AYA_NEWS = ("datasets/CohereLabs/aya_collection@09069079fad96ad9c7f8781be8c1d70471dfa768/"
            "templated_bengali_news/train-00000-of-00001.parquet")
IA = "datasets/ai4bharat/indic-align@032b6a9070e7f85f1a38e0506419f4590a20455a/indicalign-instruct"

if __name__ == "__main__":
    rows = remote_filtered(AYA_DS, "language_code", "ben", ["inputs", "targets", "annotation_type"])
    write("aya_dataset_ben", rows, ["inputs", "targets"])

    rows = remote_filtered(AYA_NEWS, "language", "ben", ["inputs", "targets"])
    write("aya_collection_templated_bengali_news", rows, ["inputs", "targets"])

    rows = remote_listcol(f"{IA}/oasst/oasst.parquet", "ben_Beng")
    write("indic_align_oasst_t_ben_Beng", rows, ["doc_id", "turns"])

    rows = remote_listcol(f"{IA}/dolly/Dolly.parquet", "ben_Beng")
    write("indic_align_dolly_t_ben_Beng", rows, ["doc_id", "turns"])

    rows = []
    for fn in ["bangla_bd/NativQA_bn_scb_bd_train.json", "bangla_in/NativQA_bn_scb_in_train.json"]:
        for i, d in enumerate(json.load(open(files_root / "QCRI__MultiNativQA" / fn, encoding="utf-8"))):
            d["_row"] = f"{fn}#{i}"
            rows.append(d)
    write("multinativqa_bangla_train", rows, ["input_query", "question", "answer"])

    with open(files_root / "kawchar85__Bangla-Math/BdMO.csv", newline="", encoding="utf-8") as f:
        rows = [dict(r, _row=i) for i, r in enumerate(csv.DictReader(f))]
    write("bangla_math_bdmo_problems", rows, ["Problem", "Answer"])
