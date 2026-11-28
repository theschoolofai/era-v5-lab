#!/usr/bin/env python3
"""bn_sample_check.py - Bengali post-training candidates: tokens on p1536 and a language check on a sample.

Data B Lab 5 task 8 / Team 10's #882 (Bengali line). For each sample file (JSON lines, one candidate row per line,
any schema: every string value in the row is joined, so a `messages` list or `instruction`/`output` fields both work;
keys starting with "_", such as the sampler's `_row`, and id fields (ID_KEYS) are skipped)
it reports:
  rows, p1536 tokens (sum, mean, median, p95), bytes per token,
  Bengali share   = Bengali letters / all letters (letters and combining signs, as D1 and lang_id.py count them),
  bn_purity       = share of rows with Bengali share >= --min-share (default 0.8),
  latin_heavy     = share of rows whose letters are at least half Latin (English or romanised),
  as_marked       = share of rows where Assamese marker hits exceed Bengali marker hits (lang_label_config.json),
  nfc_unstable    = share of rows that change under NFC, and counts of ZWJ / ZWNJ kept,
  junk            = rows holding U+200B / U+FEFF or chat ghost markers ([INST], [/INST], <think>, ### Assistant:),
                    the strip list of teams/10-post-training/docs/data_request_teams1_2_v1.md.
Only counts leave this script; no text is written.

Usage
  python bn_sample_check.py --tokenizer tokenizer.json --samples dir/*.jsonl --out bn_sample_check_v1.json
"""
import argparse
import hashlib
import json
import math
import statistics
import sys
import unicodedata
from pathlib import Path

from tokenizers import Tokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "audit"))
import lang_id  # noqa: E402  (letter_counts, markers, the bn / as marker lists)

FROZEN_SHA256 = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"
ID_KEYS = {"id", "doc_id", "data_id", "ID"}
GHOSTS = ("[INST]", "[/INST]", "<think>", "### Assistant:")
JUNK_CHARS = ("\u200b", "\ufeff")


def strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for k, v in x.items():
            if not str(k).startswith("_") and k not in ID_KEYS:   # ids and sampler metadata are not text
                yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)


def row_text(row):
    return "\n".join(s for s in strings(row) if s)


def latin_letters(text):
    return sum(1 for ch in text if unicodedata.category(ch)[0] == "L" and "LATIN" in unicodedata.name(ch, ""))


def check_file(path, tok, cfg, min_share):
    n = 0
    tokens, shares = [], []
    pure = latin_heavy = as_marked = unstable = junk = zwj = zwnj = nbytes = 0
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        if not line.strip():
            continue
        text = row_text(json.loads(line))
        n += 1
        nbytes += len(text.encode("utf-8"))
        tokens.append(len(tok.encode(text, add_special_tokens=False).ids))
        own, total = lang_id.letter_counts(text, "Bengali")
        share = own / total if total else 0.0
        shares.append(share)
        pure += share >= min_share
        latin_heavy += bool(total) and latin_letters(text) * 2 >= total
        hits = lang_id.markers(text, ["bn", "as"], cfg)
        as_marked += hits["as"] > hits["bn"]
        unstable += unicodedata.normalize("NFC", text) != text
        junk += any(c in text for c in JUNK_CHARS) or any(g in text for g in GHOSTS)
        zwj += text.count("\u200d")
        zwnj += text.count("\u200c")
    if not n:
        return {"rows": 0}
    ts = sorted(tokens)
    return {
        "rows": n, "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "tokens_sum": sum(ts), "tokens_mean": round(sum(ts) / n, 1), "tokens_median": statistics.median(ts),
        "tokens_p95": ts[math.ceil(0.95 * n) - 1],   # nearest rank "bytes_per_token": round(nbytes / max(1, sum(ts)), 3),
        "bengali_share_median": round(statistics.median(shares), 4),
        "bn_purity": round(pure / n, 4), "latin_heavy": round(latin_heavy / n, 4), "as_marked": round(as_marked / n, 4),
        "nfc_unstable": round(unstable / n, 4), "junk_rows": junk, "zwj": zwj, "zwnj": zwnj,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--samples", nargs="+", required=True)
    ap.add_argument("--min-share", type=float, default=0.8)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    sha = hashlib.sha256(Path(a.tokenizer).read_bytes()).hexdigest()
    if sha != FROZEN_SHA256:
        sys.exit(f"tokenizer sha256 {sha} is not the frozen p1536 {FROZEN_SHA256}")
    tok = Tokenizer.from_file(a.tokenizer)
    cfg = lang_id.load_config()
    res = {"tokenizer_sha256": sha, "min_share": a.min_share,
           "files": {Path(p).stem: check_file(p, tok, cfg, a.min_share) for p in sorted(a.samples)}}
    a.out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for k, v in res["files"].items():
        print(k, json.dumps(v, ensure_ascii=False))


if __name__ == "__main__":
    main()
