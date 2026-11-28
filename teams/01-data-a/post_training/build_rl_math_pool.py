"""Build Team 10's RL math prompt pool v1 (Team 1's reply to the data request in #882) from a pinned Hub revision.

  python teams/01-data-a/post_training/build_rl_math_pool.py --out <dir> [--jsonl <train.jsonl>] [--drop-list <ids.json>]

Source: nvidia/Nemotron-RL-math-OpenMathReasoning, train.jsonl at revision 219bf017 (AoPS forum problems with an
extracted answer; CC BY 4.0). The validation file of that repository is AIME 2024 and is never read.
Without --jsonl the file is downloaded at the pinned revision; with it, its sha256 must equal the pinned one.

Steps, in order (each row is kept or dropped by the first step that drops it; summary.json counts every step):
  1. clean: NFC (the lab rule; never NFKC, TSAI 28 Nov), then Team 10's contract: strip U+200B and U+FEFF and the chat
     ghost markers ([INST], [/INST], <think>, </think>, "### Assistant:"); ZWJ / ZWNJ kept. A row whose question is empty after cleaning is dropped.
  2. exact duplicate: question lowercased, whitespace collapsed; the first line keeps it.
  3. F2: Team 9's fingerprints v2, full set (set_sha256 checked), on question + "\\n\\n" + answer, min_hits 1.
  4. drop list: doc_ids from the Kaggle check against MATH (train and test), MATH-500, GSM8K and Omni-MATH
     (math_overlap.json: those benchmarks are not in fingerprints v2, and TSAI's 21 Nov rule keeps benchmark data out).
  5. answer type, with Team 10's rl/math/math_verifier.py unchanged: "number" (parse_number reads an exact
     fraction), "guessable" (one letter A-E, yes/no, true/false), "too_long" (over MAX_ANSWER_CHARS), else "symbolic".
     Only "number" and "symbolic" rows are written; the pool's "number" rows are what the current verifier can score.

Output (--out): rl_math_pool_v1.parquet (doc_id, pack_id, question, answer, answer_type, q_tokens, source_line),
summary.json (counts per step, token totals on frozen p1536), pack_table_row.json (Team 10's contract fields + the
shard pack table fields), and the parquet's sha256 in both. Two runs on the same input give byte-identical files.
"""
import argparse, hashlib, importlib.util, json, re, sys, unicodedata
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DECONTAM = REPO / "teams" / "09-evaluation" / "decontam"
VERIFIER = REPO / "teams" / "10-post-training" / "rl" / "math" / "math_verifier.py"

SOURCE = {
    "repo": "nvidia/Nemotron-RL-math-OpenMathReasoning",
    "revision": "219bf0170cd87cd5db2bbf33715ce9ea43a2c59c",
    "file": "train.jsonl",
    "sha256": "cdcf89edb4c9f3047687d0272f70b96cf84bb74dcd7966dad0cd7c721bd91823",  # train.jsonl at that revision
    "license": "cc-by-4.0",
    "license_source": "Hugging Face card at revision 219bf017 (license: cc-by-4.0; \"ready for commercial use\")",
    "generator": "none for the problem text (AoPS forum posts); problems refined and answers extracted with "
                 "Qwen2.5-32B-Instruct per the OpenMathReasoning card (arXiv 2504.16891)",
    "generator_license": "Apache-2.0 (Qwen2.5-32B-Instruct)",
}
PACK_ID = "rl-math-omr-aops-v1"
TOKENIZER = {"path": "tokenizers/p1536-sample-v0/tokenizer.json",
             "sha256": "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"}
STRIP = {0x200B: None, 0xFEFF: None}
GHOSTS = ("[INST]", "[/INST]", "<think>", "</think>", "### Assistant:")
GUESS = re.compile(r"^\(?[a-e]\)?$|^(yes|no|true|false)$")
KEEP_TYPES = ("number", "symbolic")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clean(s):
    """NFC (lab rule, never NFKC), then Team 10's contract: strip U+200B / U+FEFF and the ghost markers; nothing else."""
    s = unicodedata.normalize("NFC", s).translate(STRIP)
    for g in GHOSTS:
        s = s.replace(g, "")
    return s.strip()


def norm_key(s):
    return " ".join(re.sub(r"\s+", " ", s.lower()).split())


def answer_type(answer, mv):
    if len(answer) > mv.MAX_ANSWER_CHARS:
        return "too_long"
    if mv.parse_number(answer) is not None:
        return "number"
    if GUESS.match(mv.normalise(mv._unwrap(answer))):
        return "guessable"
    return "symbolic"


def read_rows(jsonl_path):
    with open(jsonl_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            r = json.loads(line)
            yield i, r["question"], r["expected_answer"]


def build(rows, f2_check, drop_ids, mv, count_tokens):
    """rows: (line, question, answer). f2_check(text) -> bool. drop_ids: set of doc_ids. Returns (kept, counts)."""
    counts = {"read": 0, "cleaned_changed": 0, "empty_after_clean": 0, "duplicate": 0, "f2": 0, "drop_list": 0,
              "guessable": 0, "too_long": 0, "kept_number": 0, "kept_symbolic": 0}
    seen, kept = set(), []
    for line, q_raw, a_raw in rows:
        counts["read"] += 1
        q, a = clean(q_raw), clean(a_raw)
        counts["cleaned_changed"] += (q != q_raw.strip()) or (a != a_raw.strip())
        doc_id = f"omr_rl:{line}"
        if not q or not a:
            counts["empty_after_clean"] += 1
            continue
        k = norm_key(q)
        if k in seen:
            counts["duplicate"] += 1
            continue
        seen.add(k)
        if f2_check(q + "\n\n" + a):
            counts["f2"] += 1
            continue
        if doc_id in drop_ids:
            counts["drop_list"] += 1
            continue
        t = answer_type(a, mv)
        if t not in KEEP_TYPES:
            counts[t] += 1
            continue
        counts["kept_" + t] += 1
        kept.append({"doc_id": doc_id, "pack_id": PACK_ID, "question": q, "answer": a, "answer_type": t,
                     "source_line": line})
    toks = count_tokens([r["question"] for r in kept])
    for r, n in zip(kept, toks):
        r["q_tokens"] = n
    return kept, counts


def write(kept, counts, out, source, extra):
    out.mkdir(parents=True, exist_ok=True)
    cols = ["doc_id", "pack_id", "question", "answer", "answer_type", "q_tokens", "source_line"]
    table = pa.table({c: [r[c] for r in kept] for c in cols},
                     schema=pa.schema([("doc_id", pa.string()), ("pack_id", pa.string()), ("question", pa.string()),
                                       ("answer", pa.string()), ("answer_type", pa.string()), ("q_tokens", pa.int64()),
                                       ("source_line", pa.int64())]))
    path = out / "rl_math_pool_v1.parquet"
    pq.write_table(table, path, compression="zstd", write_statistics=False)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    n_num = sum(r["answer_type"] == "number" for r in kept)
    summary = {"pack_id": PACK_ID, "source": source, "counts": counts, "rows": len(kept), "rows_number": n_num,
               "rows_symbolic": len(kept) - n_num, "q_tokens_p1536": sum(r["q_tokens"] for r in kept),
               "q_tokens_p1536_number_rows": sum(r["q_tokens"] for r in kept if r["answer_type"] == "number"),
               "tokenizer": TOKENIZER, "parquet_sha256": sha, **extra}
    row = {"pack_id": PACK_ID, "language": "en", "script": "Latn", "domain": "math", "lane": "math",
           "license": source["license"], "license_source": source["license_source"],
           "hf_repo": source["repo"], "hf_revision": source["revision"], "rows": len(kept),
           "rows_number_answers": n_num, "p1536_tokens_prompts": summary["q_tokens_p1536"],
           "generator": source["generator"], "generator_license": source["generator_license"],
           "sha256": sha, "f2_set_sha256": extra.get("f2_set_sha256"), "f2_flagged_after_build": 0}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    (out / "pack_table_row.json").write_text(json.dumps(row, indent=1, sort_keys=True) + "\n")
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--jsonl", type=Path, help="local copy of train.jsonl (its sha256 must be the pinned one)")
    ap.add_argument("--drop-list", type=Path, help="math_overlap.json from the Kaggle check (doc_ids only)")
    ap.add_argument("--tokenizer", type=Path, default=Path.home() / "Workspace" / "era-v5-data" / TOKENIZER["path"])
    ap.add_argument("--print-sha", action="store_true", help="print the input's sha256 and stop")
    a = ap.parse_args(argv)

    if a.jsonl is None:
        from huggingface_hub import hf_hub_download
        a.jsonl = Path(hf_hub_download(SOURCE["repo"], SOURCE["file"], repo_type="dataset", revision=SOURCE["revision"]))
    sha = hashlib.sha256(a.jsonl.read_bytes()).hexdigest()
    if a.print_sha:
        print(sha)
        return 0
    if sha != SOURCE["sha256"]:
        sys.exit(f"{a.jsonl}: sha256 {sha} is not the pinned {SOURCE['sha256']}")

    from tokenizers import Tokenizer
    if hashlib.sha256(a.tokenizer.read_bytes()).hexdigest() != TOKENIZER["sha256"]:
        sys.exit(f"{a.tokenizer} is not the frozen p1536 tokenizer")
    tok = Tokenizer.from_file(str(a.tokenizer))

    sys.path.insert(0, str(DECONTAM))
    fpset = load_module("fpset", DECONTAM / "fpset.py")
    fp = fpset.Fingerprints(str(REPO / "teams" / "09-evaluation" / "fingerprints" / "v2"), None)
    mv = load_module("math_verifier", VERIFIER)

    drop = set()
    if a.drop_list:
        d = json.loads(a.drop_list.read_text())
        for sp, v in d["pools"]["omr_rl"]["by_benchmark"].items():
            drop |= set(v["doc_ids"])

    kept, counts = build(read_rows(a.jsonl), lambda t: fp.check(t, 1)[0], drop, mv,
                         lambda qs: [len(e.ids) for e in tok.encode_batch(qs, add_special_tokens=False)])
    s = write(kept, counts, a.out, {**SOURCE, "input_sha256": sha},
              {"f2_set_sha256": fp.set_sha256, "drop_list_ids": len(drop),
               "drop_list_sha256": hashlib.sha256(a.drop_list.read_bytes()).hexdigest() if a.drop_list else None})
    print(json.dumps({k: s[k] for k in ("rows", "rows_number", "rows_symbolic", "q_tokens_p1536", "parquet_sha256")}))
    print(json.dumps(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
