"""Compare how tokenizers cut the same held-out bytes, and build the fixed segmentation (Lab 5 design 4, metric_v1.md).

    # measure p1536 and C3 on heldout_v1, and write the segmentation file fitted to both
    python teams/09-evaluation/harness_lab/tokenizer_units.py \
        --tokenizer p1536=<p1536>/tokenizer.json --tokenizer C3=<c3>/tokenizer.json \
        --out teams/09-evaluation/results/metric_v1/tokenizer_units.json \
        --write-segmentation teams/09-evaluation/results/metric_v1/segmentation_heldout_v1.jsonl

    # check that a (new) tokenizer fits an existing segmentation file; exit 1 if any piece does not fit
    python teams/09-evaluation/harness_lab/tokenizer_units.py --tokenizer new=<new>/tokenizer.json \
        --check-segmentation teams/09-evaluation/results/metric_v1/segmentation_heldout_v1.jsonl

Reads Team 5's heldout_v1 (text + sources; ids, order and text_sha256 are checked) and reports, per slice and per
tokenizer: documents, stored UTF-8 bytes, bytes after the tokenizer's normalizer, tokens, bytes per token, context
resets under Team 5's token windows, and the pieces of two byte segmentations (fixed size, and fitted: section 2).
It checks that decode(encode(text)) gives the normalized text and that the normalized bytes of the fitted pieces add
up to those of the whole text. It prints counts only, never document text. Needs `tokenizers`.
"""

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

from tokenizers import Tokenizer

HERE = Path(__file__).resolve().parent
HELDOUT = HERE.parents[1] / "05-architecture" / "heldout_v1" / "data"
SEGMENTATION_KIND = "metric_v1-segmentation"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ntokens(tok, text):
    return len(tok.encode(text, add_special_tokens=False).ids)


def _char_boundary(data, cut):
    """Move `cut` back to the start of a UTF-8 character."""
    while 0 < cut < len(data) and (data[cut] & 0xC0) == 0x80:
        cut -= 1
    return cut


def _cut_in(head):
    """Where to end a piece inside `head`: after its last newline, else before its last space (the pre-tokenizer
    joins a space to the word after it), else at its end. Returns 0 if `head` holds nothing to cut at."""
    newline = head.rfind(b"\n")
    if newline >= 0:
        return newline + 1
    space = head.rfind(b" ")
    return space if space > 0 else len(head)


def byte_segments(text, limit=4096):
    """Fixed-size pieces of at most `limit` UTF-8 bytes (the rejected rule in metric_v1 section 2). Joined, the
    pieces give the text back."""
    if limit < 4:
        raise ValueError("limit must hold at least one UTF-8 character (4 bytes)")
    pieces, data = [], text.encode("utf-8")
    while len(data) > limit:
        cut = _char_boundary(data, _cut_in(data[:limit])) or _char_boundary(data, limit)
        pieces.append(data[:cut].decode("utf-8"))
        data = data[cut:]
    pieces.append(data.decode("utf-8"))
    return pieces


def fitted_segments(text, tokenizers, budget):
    """The proposed rule (metric_v1 section 2): the longest pieces that are at most `budget` tokens for every tokenizer,
    each ending after a newline, else before a space, else at a character boundary. Joined, the pieces give the text
    back. Raises ValueError if a single character is over the budget or a piece cannot be made to fit."""
    def fits(piece):
        return all(ntokens(t, piece) <= budget for t in tokenizers)

    pieces, data = [], text.encode("utf-8")
    while not fits(data.decode("utf-8")):
        # Largest prefix that fits, by bisection on bytes. A token holds far fewer than 64 bytes, so the search is
        # capped at 64 bytes per budget token instead of the whole remaining text.
        lo, hi = 0, min(len(data), 64 * budget)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if fits(data[:_char_boundary(data, mid)].decode("utf-8")):
                lo = mid
            else:
                hi = mid - 1
        lo = _char_boundary(data, lo)
        if lo == 0:
            raise ValueError(f"one character is over the budget of {budget} tokens")
        cut = _char_boundary(data, _cut_in(data[:lo])) or lo
        if not fits(data[:cut].decode("utf-8")):  # token counts are not always monotone in length
            cut = lo
            if not fits(data[:cut].decode("utf-8")):
                raise ValueError("no prefix fits the budget")
        pieces.append(data[:cut].decode("utf-8"))
        data = data[cut:]
    pieces.append(data.decode("utf-8"))
    return pieces


def offsets_of(pieces):
    """Byte offsets where each piece after the first starts."""
    out, pos = [], 0
    for piece in pieces[:-1]:
        pos += len(piece.encode("utf-8"))
        out.append(pos)
    return out


def pieces_at(text, offsets):
    data = text.encode("utf-8")
    bounds = [0, *offsets, len(data)]
    return [data[a:b].decode("utf-8") for a, b in zip(bounds, bounds[1:])]


def normalized_bytes(tok, text):
    return len((tok.normalizer.normalize_str(text) if tok.normalizer else text).encode("utf-8"))


def measure(texts, slices, tokenizers, window, limit=4096, budget=None):
    """Counts per (slice, tokenizer), and the fitted pieces of each text."""
    budget = window if budget is None else budget
    rows, fitted_all = collections.defaultdict(collections.Counter), []
    for text, name in zip(texts, slices):
        raw = len(text.encode("utf-8"))
        fixed = byte_segments(text, limit)
        fitted = fitted_segments(text, list(tokenizers.values()), budget)
        fitted_all.append(fitted)
        for label, tok in tokenizers.items():
            r = rows[(name, label)]
            norm = tok.normalizer.normalize_str(text) if tok.normalizer else text
            ids = tok.encode(text, add_special_tokens=False).ids
            windows = len(range(0, len(ids), window))  # as Team 5's DocumentWindows
            fitted_tokens = [ntokens(tok, p) for p in fitted]
            r.update(docs=1, raw_bytes=raw, normalized_bytes=len(norm.encode("utf-8")),
                     docs_changed_by_normalizer=int(norm != text), tokens=len(ids),
                     docs_over_window=int(len(ids) > window), context_resets=max(windows - 1, 0),
                     round_trip_failures=int(tok.decode(ids) != norm),
                     fixed_pieces=len(fixed), fixed_pieces_over_window=sum(ntokens(tok, p) > window for p in fixed),
                     fitted_pieces=len(fitted), fitted_resets=len(fitted) - 1, fitted_tokens=sum(fitted_tokens),
                     fitted_byte_conservation_failures=int(
                         sum(normalized_bytes(tok, p) for p in fitted) != len(norm.encode("utf-8"))))
            r["fixed_max_piece_tokens"] = max(r["fixed_max_piece_tokens"], max(ntokens(tok, p) for p in fixed))
            r["fitted_max_piece_tokens"] = max(r["fitted_max_piece_tokens"], max(fitted_tokens))
    return rows, fitted_all


def read_heldout(heldout, sources):
    """Documents with their slices; ids, order and text_sha256 must match the sources file (as Team 5 checks)."""
    docs = [json.loads(line) for line in heldout.read_text("utf-8").splitlines()]
    meta = [json.loads(line) for line in sources.read_text("utf-8").splitlines()]
    if [d["id"] for d in docs] != [m["id"] for m in meta]:
        raise ValueError("heldout and sources ids differ or are out of order")
    for d, m in zip(docs, meta):
        if hashlib.sha256(d["text"].encode("utf-8")).hexdigest() != m["text_sha256"]:
            raise ValueError(f"{d['id']}: text_sha256 does not match the sources file")
    return docs, [m["slice"] for m in meta]


def check_segmentation(path, docs, tokenizers):
    """Every piece of the segmentation file must fit its budget for every given tokenizer. Returns the failures."""
    lines = [json.loads(line) for line in Path(path).read_text("utf-8").splitlines()]
    header, rows = lines[0], lines[1:]
    if header.get("kind") != SEGMENTATION_KIND:
        raise ValueError(f"{path}: not a {SEGMENTATION_KIND} file")
    by_id = {d["id"]: d["text"] for d in docs}
    failures = []
    for row in rows:
        text = by_id[row["id"]]
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != row["text_sha256"]:
            raise ValueError(f"{row['id']}: text_sha256 differs from the segmentation file")
        for i, piece in enumerate(pieces_at(text, row["offsets"])):
            for label, tok in tokenizers.items():
                n = ntokens(tok, piece)
                if n > header["budget"]:
                    failures.append((row["id"], i, label, n))
    return header, failures


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer", action="append", required=True, metavar="NAME=PATH")
    ap.add_argument("--heldout", type=Path, default=HELDOUT / "heldout_v1.jsonl")
    ap.add_argument("--sources", type=Path, default=HELDOUT / "heldout_v1_sources.jsonl")
    ap.add_argument("--window", type=int, default=2048, help="token window (dry run 2 block_size)")
    ap.add_argument("--margin", type=float, default=0.8,
                    help="fitted pieces hold at most margin x window tokens, so a later tokenizer up to 1/margin times "
                         "less efficient still fits (metric_v1 section 2)")
    ap.add_argument("--segment-bytes", type=int, default=4096, help="size of the rejected fixed-size rule")
    ap.add_argument("--out", type=Path, help="counts as JSON")
    ap.add_argument("--write-segmentation", type=Path, help="write the fitted segmentation file (JSONL)")
    ap.add_argument("--check-segmentation", type=Path, help="check the tokenizers against a segmentation file")
    a = ap.parse_args(argv)

    tokenizers, tok_sha = {}, {}
    for spec in a.tokenizer:
        name, path = spec.split("=", 1)
        tokenizers[name], tok_sha[name] = Tokenizer.from_file(path), sha256(path)
    docs, slices = read_heldout(a.heldout, a.sources)

    if a.check_segmentation:
        header, failures = check_segmentation(a.check_segmentation, docs, tokenizers)
        for doc_id, i, label, n in failures[:20]:
            print(f"{doc_id} piece {i}: {label} has {n} tokens, budget {header['budget']}", file=sys.stderr)
        print(f"{a.check_segmentation.name} (budget {header['budget']}): {len(failures)} piece(s) over the budget",
              file=sys.stderr)
        return 1 if failures else 0

    budget = int(a.window * a.margin)
    rows, fitted = measure([d["text"] for d in docs], slices, tokenizers, a.window, a.segment_bytes, budget)

    if a.write_segmentation:
        header = {"kind": SEGMENTATION_KIND, "eval_file_sha256": sha256(a.heldout), "window": a.window,
                  "margin": a.margin, "budget": budget, "fitted_to": tok_sha,
                  "rule": "longest pieces <= budget tokens for every tokenizer in fitted_to; end after a newline, "
                          "else before a space, else at a character boundary; offsets are UTF-8 byte offsets"}
        lines = [header] + [{"id": d["id"], "text_sha256": hashlib.sha256(d["text"].encode("utf-8")).hexdigest(),
                             "offsets": offsets_of(p)} for d, p in zip(docs, fitted)]
        a.write_segmentation.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")

    out = {"command": "tokenizer_units.py " + " ".join(argv if argv is not None else sys.argv[1:]),
           "heldout_sha256": sha256(a.heldout), "sources_sha256": sha256(a.sources), "window": a.window,
           "margin": a.margin, "budget": budget, "segment_bytes": a.segment_bytes, "tokenizer_sha256": tok_sha,
           "segmentation_sha256": sha256(a.write_segmentation) if a.write_segmentation else None, "rows": []}
    for (name, label), r in sorted(rows.items()):
        out["rows"].append({"slice": name, "tokenizer": label, **r,
                            "bytes_per_token": round(r["raw_bytes"] / r["tokens"], 4)})
    totals = collections.defaultdict(collections.Counter)
    for (_, label), r in rows.items():
        for key, value in r.items():
            totals[label][key] = max(totals[label][key], value) if key.endswith("max_piece_tokens") else \
                totals[label][key] + value
    out["totals"] = {k: dict(v) for k, v in totals.items()}

    names = list(tokenizers)
    print(f"{'slice':6}{'docs':>6}{'raw bytes':>11}{'norm Δ':>8}" + "".join(f"{n + ' B/tok':>12}" for n in names)
          + "".join(f"{n + ' resets':>13}" for n in names) + f"{'fitted resets':>15}")
    for name in sorted({k[0] for k in rows}):
        first = rows[(name, names[0])]
        print(f"{name:6}{first['docs']:>6}{first['raw_bytes']:>11}{first['normalized_bytes'] - first['raw_bytes']:>8}"
              + "".join(f"{rows[(name, n)]['raw_bytes'] / rows[(name, n)]['tokens']:>12.3f}" for n in names)
              + "".join(f"{rows[(name, n)]['context_resets']:>13}" for n in names) + f"{first['fitted_resets']:>15}")
    for n in names:
        t = totals[n]
        print(f"{n}: {t['docs']} docs, {t['raw_bytes']} raw bytes, {t['normalized_bytes']} normalized, "
              f"{t['tokens']} tokens, {t['context_resets']} token-window resets, {t['round_trip_failures']} round-trip "
              f"failures; fixed {a.segment_bytes}-byte pieces {t['fixed_pieces']} "
              f"(largest {t['fixed_max_piece_tokens']} tokens, {t['fixed_pieces_over_window']} over the window); "
              f"fitted (budget {budget}) pieces "
              f"{t['fitted_pieces']}, {t['fitted_resets']} resets, largest {t['fitted_max_piece_tokens']} tokens, "
              f"{t['fitted_tokens']} tokens in pieces, {t['fitted_byte_conservation_failures']} byte-conservation "
              f"failures", file=sys.stderr)
    if a.out:
        a.out.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
