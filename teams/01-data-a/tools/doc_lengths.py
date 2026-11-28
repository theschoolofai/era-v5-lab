"""Long documents in the packs (D8): p1536 token length of every document, counted per pack and split.

  python -I teams/01-data-a/tools/doc_lengths.py <packs_root> <p1536 tokenizer.json> <out.json>

<packs_root> holds <pack>/<part folder>/part-*.parquet (the 38 sample packs as downloaded; every part, held-out too).
Per pack: documents, tokens, and for each threshold (8,192; 32,768; 131,072 tokens) the documents at or above it and
their tokens; also the p50 / p90 / p99 / max document length. Frozen p1536, add_special_tokens=False, no text printed.
"""
import hashlib, json, sys, time
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq
from tokenizers import Tokenizer

P1536 = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"
THRESHOLDS = (8192, 32768, 131072)


def pct(xs, q):
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def main(root, tok_path, out):
    assert hashlib.sha256(Path(tok_path).read_bytes()).hexdigest() == P1536, "not the frozen p1536"
    tok = Tokenizer.from_file(str(tok_path))
    lens = defaultdict(list)
    t0 = time.time()
    for f in sorted(Path(root).glob("*/*/*.parquet")):
        pack, folder = f.parent.parent.name, f.parent.name
        split = "heldout" if folder.lower().startswith("held") else "train"
        texts = pq.read_table(f, columns=["text"]).column(0).to_pylist()
        lens[(pack, split)] += [len(e.ids) for e in tok.encode_batch(texts, add_special_tokens=False)]
    rows = {}
    for (pack, split), xs in sorted(lens.items()):
        xs.sort()
        r = {"docs": len(xs), "tokens": sum(xs), "p50": pct(xs, .5), "p90": pct(xs, .9), "p99": pct(xs, .99), "max": xs[-1]}
        for t in THRESHOLDS:
            big = [x for x in xs if x >= t]
            r[f"docs_ge_{t}"] = len(big); r[f"tokens_ge_{t}"] = sum(big)
        rows[f"{pack}/{split}"] = r
    json.dump({"tokenizer_sha256": P1536, "thresholds": THRESHOLDS, "seconds": round(time.time() - t0, 1), "packs": rows},
              open(out, "w"), indent=1)
    tot = {k: sum(r[k] for r in rows.values()) for k in ("docs", "tokens", *[f"docs_ge_{t}" for t in THRESHOLDS], *[f"tokens_ge_{t}" for t in THRESHOLDS])}
    print(json.dumps(tot))


if __name__ == "__main__":
    main(*sys.argv[1:4])
