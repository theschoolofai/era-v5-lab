"""Fetch the RL-math candidates at pinned revisions into ~/Workspace/era-v5-data/g1-pt/raw/<repo>/.
jsonl files: whole file (hf_hub_download). Big parquet sets: only the named columns (range reads via HfFileSystem)."""
import os, sys, time, json
from pathlib import Path
import pyarrow as pa, pyarrow.parquet as pq
from huggingface_hub import hf_hub_download, HfFileSystem
ROOT = Path.home() / "Workspace/era-v5-data/g1-pt/raw"
TOK = os.environ.get("HF_TOKEN")
JOBS = {
 "omr_rl":   ("nvidia/Nemotron-RL-math-OpenMathReasoning", "219bf0170cd87cd5db2bbf33715ce9ea43a2c59c", "jsonl", ["train.jsonl"], None),
 "so_rl":    ("nvidia/Nemotron-RL-math-stack_overflow", "81ee859274bd8294ed270511c9fc688f60bd2492", "jsonl", ["train.jsonl"], None),  # aime24_validation.jsonl NOT fetched (benchmark items)
 "rlmath_v2":("nvidia/Nemotron-RL-Math-v2", "804418c1d4eceeaa453d895954887c0975e79121", "jsonl", ["data/train.jsonl"], None),
 "deepmath": ("zwhe99/DeepMath-103K", "5cf055d1fe3d7a2eb19719ac020211469736ae44", "parquet", [f"data/train-{i:05d}-of-00010.parquet" for i in range(10)], ["question", "final_answer", "difficulty", "topic"]),
 "openr1":   ("open-r1/OpenR1-Math-220k", "e4e141ec9dea9f8326f4d347be56105859b2bd68", "parquet", [f"data/train-{i:05d}-of-00010.parquet" for i in range(10)], ["problem", "answer", "problem_type", "question_type", "source", "uuid", "correctness_math_verify", "is_reasoning_complete"]),
 "omr_cot":  ("nvidia/OpenMathReasoning", "d3d08664755704f422af97d43a7ff0ded4bd95df", "parquet", [f"data/cot-{i:05d}-of-00144.parquet" for i in range(144)], ["problem", "problem_source", "problem_type", "expected_answer", "pass_rate_72b_tir"]),
 "sftmath_v4":("nvidia/Nemotron-SFT-Math-v4", "84d42ad0cb960f07f951b9baa9ed2b46a5a18c66", "parquet", [f"data/train-{i:05d}-of-00012.parquet" for i in range(12)], ["uuid", "problem", "expected_answer", "license", "source", "dataset", "subset"]),
}
fs = HfFileSystem(token=TOK, block_size=1 << 20)
for key in sys.argv[1:]:
    rid, rev, kind, files, cols = JOBS[key]
    out = ROOT / key; out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if kind == "jsonl":
        for f in files:
            p = hf_hub_download(rid, f, repo_type="dataset", revision=rev, token=TOK, local_dir=out)
        print(json.dumps({"job": key, "repo": rid, "rev": rev, "files": files, "seconds": round(time.time()-t0, 1)}), flush=True)
    else:
        from concurrent.futures import ThreadPoolExecutor
        from pyarrow.fs import PyFileSystem, FSSpecHandler
        pfs = PyFileSystem(FSSpecHandler(fs))
        def one(f):
            path = f"datasets/{rid}@{rev}/{f}"
            names = pq.read_schema(path, filesystem=pfs).names
            t = pq.read_table(path, filesystem=pfs, columns=[c for c in cols if c in names], pre_buffer=True)
            t = t.append_column("src_file", pa.array([f] * t.num_rows))
            return t.append_column("src_row", pa.array(list(range(t.num_rows)), pa.int64()))
        with ThreadPoolExecutor(8) as ex:
            tabs = list(ex.map(one, files))
        print(json.dumps({"job": key, "files": len(files), "rows": sum(t.num_rows for t in tabs), "seconds": round(time.time()-t0, 1)}), flush=True)
        T = pa.concat_tables(tabs, promote_options="default")
        pq.write_table(T, out / f"{key}.cols.parquet", compression="zstd")
        (out / "SOURCE.json").write_text(json.dumps({"repo": rid, "revision": rev, "files": files, "columns": cols, "rows": T.num_rows}, indent=1))
        print(json.dumps({"job": key, "repo": rid, "rev": rev, "rows": T.num_rows, "seconds": round(time.time()-t0, 1)}), flush=True)
