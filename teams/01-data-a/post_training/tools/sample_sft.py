"""Sample SFT candidates at pinned revisions; p1536 length profile + docs.parquet for F2.

  python -I sample_sft.py <key> [<key> ...]        (needs HF_TOKEN in the environment)

Sampling (seed 0): parquet -> random row groups of random files; jsonl -> random byte windows of random files (size-
weighted), whole lines after the first newline. Up to N rows per key. Window sampling slightly favours rows that follow
long rows; the numbers are a sample profile, not a census.
Rendering: every message content (+ reasoning, tool-call arguments) and the tool schemas, joined by newlines. ChatML
special tokens are NOT included (a few per turn). p1536, add_special_tokens=False.
Writes ~/Workspace/era-v5-data/g1-pt/sft/<key>/{docs.parquet, stats.json}. Never prints row text.
"""
import hashlib, json, os, random, sys, time, unicodedata
from pathlib import Path
import pyarrow as pa, pyarrow.parquet as pq
from pyarrow.fs import PyFileSystem, FSSpecHandler
from huggingface_hub import HfApi, HfFileSystem
from tokenizers import Tokenizer

DATA = Path.home() / "Workspace/era-v5-data"
OUT = DATA / "g1-pt/sft"
TOK_PATH = DATA / "tokenizers/p1536-sample-v0/tokenizer.json"
TOK_SHA = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"
GHOSTS = ["[INST]", "[/INST]", "<think>", "</think>", "### Assistant:"]
N = int(os.environ.get("SAMPLE_N", "500"))
WINDOW = 16 << 20

SPECS = {  # key: (repo, revision, file filter prefixes, notes)
    "ocr2":          ("nvidia/OpenCodeReasoning-2", "eadf535931451525f3e5621d0f960c240bc62fd9", ["train/python/", "train/cpp/"]),
    "cf_cots":       ("open-r1/codeforces-cots", "39ac85c150806230473c70ad72c31f6232fe3f41", ["solutions_decontaminated/"]),
    "oci":           ("nvidia/OpenCodeInstruct", "8f3ba5bafe4d6e8db46082cf7ae6741bc370604d", ["data/"]),
    "opencode":      ("nvidia/Nemotron-SFT-OpenCode-v1", "556d5237acff203f3e1a0be49428634c3606cda2", ["agent_skills/", "agent_skills_question_tool/", "bash_only_tool/", "bash_only_tool_skills/", "general/"]),
    "compprog_v2":   ("nvidia/Nemotron-SFT-Competitive-Programming-v2", "778afc98a9e027e10b3cd78020c120e93e142ef2", ["data/"]),
    "commitpackft":  ("bigcode/commitpackft", "fc56fe33c030c6daa414c2b112c932b8eed085e6", ["data/python/", "data/javascript/", "data/typescript/", "data/java/", "data/c++/", "data/go/", "data/rust/"]),
    "agentic_v1_tool": ("nvidia/Nemotron-Agentic-v1", "650d590978ca35c8f1ecea2faf136e5fac421b62", ["data/tool_calling.jsonl"]),
    "agentic_v1_inter": ("nvidia/Nemotron-Agentic-v1", "650d590978ca35c8f1ecea2faf136e5fac421b62", ["data/interactive_agent.jsonl"]),
    "agentic_v2_tool": ("nvidia/Nemotron-SFT-Agentic-v2", "7c804833427f633ccd53b582dbf02525fd680f78", ["data/tool_calling.jsonl"]),
    "ot3":           ("open-thoughts/OpenThoughts3-1.2M", "61bcf9d4eb38b30295efc2021227a63cc5bb34c8", ["data/"]),
    "science_v1":    ("nvidia/Nemotron-Science-v1", "82e1af468197076b4f0f392c239274eac032adc7", ["data/RQA.jsonl", "data/MCQ.jsonl"]),
    "dolly":         ("databricks/databricks-dolly-15k", "bdd27f4d94b9c1f951818a7da7fd7aeea5dbff1a", ["databricks-dolly-15k.jsonl"]),
    "swe_rebench_oh": ("nebius/SWE-rebench-openhands-trajectories", "35455389ab51bf5e2306bfd436ef72d0f98bf882", ["trajectories.parquet"]),
    "cascade_swe":   ("nvidia/Nemotron-Cascade-SFT-SWE", "b4ef73ff9bbcfc33d1ec7a48e53017f9ce7af7a3", ["swe_"]),
    "swe_zero":      ("nvidia/SWE-Zero-openhands-trajectories", "7b3cd106d00f60918e722d33a1d74bc67072a7ea", ["data/"]),
    "terminal":      ("nvidia/Nemotron-Terminal-Corpus", "67a3e039a1b07079c04dcf9d0d03fc5798e24fd9", ["dataset_adapters/", "synthetic_tasks/"]),
}
MSG_KEYS = ("messages", "conversations", "trajectory")
FLAT_KEYS = [("question", "r1_generation"), ("input", "output"), ("subject", "old_contents", "new_contents"),
             ("instruction", "context", "response")]


def render(row):
    """(full text, assistant-only text, n_turns, has_tool_calls)."""
    parts, asst, turns, tc = [], [], 0, False
    for k in MSG_KEYS:
        msgs = row.get(k)
        if isinstance(msgs, str):
            try: msgs = json.loads(msgs)
            except Exception: msgs = None
        if isinstance(msgs, list) and msgs:
            for m in msgs:
                if not isinstance(m, dict): continue
                turns += 1
                role = (m.get("role") or m.get("from") or "").lower()
                seg = [m.get("content") or m.get("value") or ""]
                for rk in ("reasoning_content", "reasoning", "thinking"):
                    if isinstance(m.get(rk), str): seg.append(m[rk])
                if m.get("tool_calls"):
                    tc = True; seg.append(json.dumps(m["tool_calls"], ensure_ascii=False))
                seg = [s if isinstance(s, str) else json.dumps(s, ensure_ascii=False) for s in seg]
                parts += seg
                if role in ("assistant", "gpt"): asst += seg
            break
    else:
        for keys in FLAT_KEYS:
            if all(k in row for k in keys):
                vals = [row[k] or "" for k in keys]; parts += vals; asst.append(vals[-1]); turns = 2
                break
    if row.get("tools"):
        t = row["tools"]; parts.append(t if isinstance(t, str) else json.dumps(t, ensure_ascii=False))
    return "\n".join(parts), "\n".join(asst), turns, tc


def list_files(api, repo, rev, prefixes):
    info = api.dataset_info(repo, revision=rev, files_metadata=True)
    return [(s.rfilename, s.size) for s in info.siblings
            if s.rfilename.endswith((".parquet", ".jsonl")) and any(s.rfilename.startswith(p) for p in prefixes)]


COLS = {  # parquet: read only these columns (the rest are not rendered)
    "ocr2": ["question", "r1_generation", "license", "dataset", "source", "pass_rate"],
    "cf_cots": ["messages", "contest_start_year"],
    "oci": ["input", "output", "domain", "generation_algorithm", "average_test_score"],
    "ot3": ["conversations", "source", "domain"],
    "swe_zero": ["trajectory", "license", "dataset", "repo"],
}
PER_FILE = int(os.environ.get("PER_FILE_DIV", "2"))


def sample_parquet(pfs, base, files, rng, n, cols=None):
    rows = []
    order = files[:]; rng.shuffle(order)
    for f, _ in order:
        pf = pq.ParquetFile(f"{base}/{f}", filesystem=pfs)
        rg = rng.randrange(pf.metadata.num_row_groups)
        have = [c for c in cols if c in pf.schema_arrow.names] if cols else None
        t = pf.read_row_group(rg, columns=have).to_pylist()
        pick = rng.sample(range(len(t)), min(len(t), max(1, n // PER_FILE), n - len(rows)))
        rows += [(f"{f}#rg{rg}:{i}", t[i]) for i in pick]
        if len(rows) >= n: break
    return rows


def sample_jsonl(fs, base, files, rng, n):
    rows = []; total = sum(s for _, s in files); tries = 0
    while len(rows) < n and tries < 40:
        tries += 1
        r = rng.random() * total
        for f, s in files:
            if r < s: break
            r -= s
        if s <= WINDOW:  # small file: read it once, take random lines, drop it from the draw
            with fs.open(f"{base}/{f}", "rb") as fh:
                lines = [ln for ln in fh.read().split(b"\n") if ln.strip()]
            idx = sorted(rng.sample(range(len(lines)), min(len(lines), n - len(rows))))
            for j in idx:
                try: rows.append((f"{f}:line{j}", json.loads(lines[j])))
                except Exception: pass
            files = [(g, z) for g, z in files if g != f]; total -= s
            if not files: break
            continue
        off = rng.randrange(0, s - WINDOW)
        with fs.open(f"{base}/{f}", "rb", block_size=WINDOW) as fh:
            fh.seek(off); buf = fh.read(WINDOW)
        lines = buf.split(b"\n")
        if off > 0: lines = lines[1:]
        lines = lines[:-1] if not buf.endswith(b"\n") else lines
        take = lines[: max(1, n // 8)]
        for j, ln in enumerate(take):
            if not ln.strip(): continue
            try: rows.append((f"{f}@{off}:{j}", json.loads(ln)))
            except Exception: pass
            if len(rows) >= n: break
    return rows, tries


def pct(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None


def main():
    assert hashlib.sha256(TOK_PATH.read_bytes()).hexdigest() == TOK_SHA
    tok = Tokenizer.from_file(str(TOK_PATH))
    api = HfApi(); fs = HfFileSystem(token=os.environ.get("HF_TOKEN"), block_size=1 << 20); pfs = PyFileSystem(FSSpecHandler(fs))
    for key in sys.argv[1:]:
        t0 = time.time(); rng = random.Random(0)
        repo, rev, prefixes = SPECS[key]
        files = list_files(api, repo, rev, prefixes)
        base = f"datasets/{repo}@{rev}"
        if files[0][0].endswith(".parquet"):
            rows = sample_parquet(pfs, base, files, rng, N, COLS.get(key)); windows = None
        else:
            rows, windows = sample_jsonl(fs, base, files, rng, N)
        texts, assts, turns, tcs, ids, line_bytes, extra = [], [], [], [], [], [], {}
        for rid, r in rows:
            full, a, nt, tc = render(r)
            texts.append(full); assts.append(a); turns.append(nt); tcs.append(tc); ids.append(rid)
            line_bytes.append(len(json.dumps(r, ensure_ascii=False, default=str).encode()))
            if key == "ocr2": extra["question_placeholder_dash"] = extra.get("question_placeholder_dash", 0) + (r.get("question", "") .strip() == "-")
            for fld in ("license", "generator", "model", "source", "dataset", "domain", "category", "lang", "generation_algorithm"):
                v = r.get(fld)
                if isinstance(v, str) and len(v) < 60:
                    extra.setdefault("field_" + fld, {}); extra["field_" + fld][v] = extra["field_" + fld].get(v, 0) + 1
        tk = [len(e.ids) for e in tok.encode_batch(texts, add_special_tokens=False)]
        ta = [len(e.ids) for e in tok.encode_batch(assts, add_special_tokens=False)]
        n = len(tk)
        clean = {"u200b": sum("​" in t for t in texts), "ufeff": sum("﻿" in t for t in texts),
                 "ghost_marker": sum(any(g in t for g in GHOSTS) for t in texts),
                 "nfkc_changes": sum(unicodedata.normalize("NFKC", t) != t for t in texts)}
        total_bytes = sum(s for _, s in files)
        stats = {"key": key, "repo": repo, "revision": rev, "files": len(files), "bytes": total_bytes, "sampled_rows": n,
                 "jsonl_windows": windows,
                 "tokens": {"mean": round(sum(tk) / n, 1) if n else None, "p50": pct(tk, .5), "p90": pct(tk, .9), "p99": pct(tk, .99), "max": max(tk, default=0),
                            "assistant_mean": round(sum(ta) / n, 1) if n else None},
                 "share_8k_32k": round(sum(8192 <= x <= 32768 for x in tk) / n, 4) if n else None,
                 "share_over_32k": round(sum(x > 32768 for x in tk) / n, 4) if n else None,
                 "share_with_tool_calls": round(sum(tcs) / n, 4) if n else None,
                 "turns_mean": round(sum(turns) / n, 1) if n else None,
                 "mean_row_bytes": round(sum(line_bytes) / n) if n else None,
                 "clean_contract_counts": clean, "fields": extra, "seconds": round(time.time() - t0, 1)}
        o = OUT / key; o.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.table({"doc_id": [f"{key}:{i}" for i in ids], "pack_id": [key] * n, "text": texts,
                                 "tokens": tk, "assistant_tokens": ta}), o / "docs.parquet", compression="zstd")
        (o / "stats.json").write_text(json.dumps(stats, indent=1))
        print(json.dumps({k: v for k, v in stats.items() if k != "fields"}), flush=True)


if __name__ == "__main__":
    main()
