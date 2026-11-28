"""Turn one fetched RL-math candidate into docs.parquet (doc_id, pack_id, text, question, answer) + stats.json.

  python -I prepare_pool.py <key> [<key> ...]

Reads ~/Workspace/era-v5-data/g1-pt/raw/<key>/, writes ~/Workspace/era-v5-data/g1-pt/pools/<key>/.
text = question + "\n\n" + answer (what F2 checks). Nothing is cleaned or changed: the Team 10 cleaning contract is
only COUNTED here (U+200B, U+FEFF, chat ghost markers, rows NFKC would change, ZWJ/ZWNJ present).
Token counts: frozen p1536 tokenizer, add_special_tokens=False, question and answer counted separately.
Exact-duplicate key: question lowercased, whitespace collapsed (the same normaliser as Team 10's math500_guard.py).
"""
import hashlib, json, re, sys, time, unicodedata
from pathlib import Path
import pyarrow as pa, pyarrow.parquet as pq
from tokenizers import Tokenizer

DATA = Path.home() / "Workspace/era-v5-data"
RAW, POOLS = DATA / "g1-pt/raw", DATA / "g1-pt/pools"
TOK_PATH = DATA / "tokenizers/p1536-sample-v0/tokenizer.json"
TOK_SHA = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"
GHOSTS = ["[INST]", "[/INST]", "<think>", "</think>", "### Assistant:"]


def norm_key(s):
    return " ".join(re.sub(r"\s+", " ", s.lower()).split())


def jsonl(p):
    with open(p, encoding="utf-8") as f:
        for i, line in enumerate(f):
            yield i, json.loads(line)


def rows_for(key):
    """Yield (row_id, question, answer, meta dict). row_id is stable: the line or (file,row) at the pinned revision."""
    if key in ("omr_rl", "so_rl"):
        for i, r in jsonl(RAW / key / "train.jsonl"):
            yield f"{i}", r["question"], r["expected_answer"], {}
    elif key == "rlmath_v2":
        for i, r in jsonl(RAW / key / "data/train.jsonl"):
            yield r["uuid"], r["question"], r["expected_answer"], {
                "placeholder": bool(r.get("_hf_question_placeholder")), "verifier_type": r.get("verifier_type")}
    else:
        t = pq.read_table(next((RAW / key).glob("*.cols.parquet"))).to_pylist()
        qcol, acol = {"deepmath": ("question", "final_answer"), "openr1": ("problem", "answer"),
                      "sftmath_v4": ("problem", "expected_answer"), "omr_cot": ("problem", "expected_answer")}[key]
        for r in t:
            meta = {k: r[k] for k in r if k not in (qcol, acol, "src_file", "src_row")}
            yield f'{r["src_file"].rsplit("/", 1)[-1].split(".")[0]}:{r["src_row"]}', r[qcol] or "", r[acol] or "", meta


def pct(xs, q):
    if not xs: return None
    xs = sorted(xs); return xs[min(len(xs) - 1, int(q * len(xs)))]


def main():
    assert hashlib.sha256(TOK_PATH.read_bytes()).hexdigest() == TOK_SHA, "tokenizer is not the frozen p1536"
    tok = Tokenizer.from_file(str(TOK_PATH))
    for key in sys.argv[1:]:
        t0 = time.time()
        out = POOLS / key; out.mkdir(parents=True, exist_ok=True)
        ids, qs, ans, metas = [], [], [], []
        for rid, q, a, m in rows_for(key):
            ids.append(rid); qs.append(q); ans.append(a if isinstance(a, str) else json.dumps(a)); metas.append(m)
        n = len(ids)
        keys = [norm_key(q) for q in qs]
        first = {}
        for i, k in enumerate(keys):
            first.setdefault(k, i)
        dup_rows = n - len(first)
        empty_q = sum(1 for q in qs if not q.strip())
        empty_a = sum(1 for a in ans if not a.strip())
        clean = {"u200b": 0, "ufeff": 0, "ghost_marker": 0, "nfkc_changes": 0, "zwj_or_zwnj": 0}
        for q, a in zip(qs, ans):
            s = q + "\n" + a
            clean["u200b"] += "​" in s
            clean["ufeff"] += "﻿" in s
            clean["ghost_marker"] += any(g in s for g in GHOSTS)
            clean["nfkc_changes"] += unicodedata.normalize("NFKC", s) != s
            clean["zwj_or_zwnj"] += ("‍" in s) or ("‌" in s)
        tq = [len(e.ids) for e in tok.encode_batch(qs, add_special_tokens=False)]
        ta = [len(e.ids) for e in tok.encode_batch(ans, add_special_tokens=False)]
        text = [q + "\n\n" + a for q, a in zip(qs, ans)]
        cols = {"doc_id": [f"{key}:{r}" for r in ids], "pack_id": [key] * n, "text": text, "question": qs, "answer": ans,
                "q_tokens": tq, "a_tokens": ta, "norm_key_sha1": [hashlib.sha1(k.encode()).hexdigest() for k in keys],
                "first_of_dup": [first[k] == i for i, k in enumerate(keys)]}
        if any(metas):
            mk = sorted({k for m in metas for k in m})
            for k in mk:
                cols["meta_" + k] = [None if m.get(k) is None else str(m.get(k)) for m in metas]
        pq.write_table(pa.table(cols), out / "docs.parquet", compression="zstd")
        stats = {"pool": key, "rows": n, "unique_questions": len(first), "duplicate_rows": dup_rows,
                 "empty_question": empty_q, "empty_answer": empty_a, "clean_contract_counts": clean,
                 "p1536_tokens": {"question_total": sum(tq), "answer_total": sum(ta),
                                  "question_mean": round(sum(tq) / n, 1) if n else None,
                                  "question_p50": pct(tq, .5), "question_p95": pct(tq, .95), "question_max": max(tq, default=0),
                                  "answer_p50": pct(ta, .5), "answer_p95": pct(ta, .95)},
                 "tokenizer_sha256": TOK_SHA, "seconds": round(time.time() - t0, 1)}
        (out / "stats.json").write_text(json.dumps(stats, indent=1))
        print(json.dumps(stats), flush=True)


if __name__ == "__main__":
    main()
