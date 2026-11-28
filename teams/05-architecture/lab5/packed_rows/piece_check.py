"""Pieces of a shard document, as the packed-rows format defines them, and a field-by-field check (#890).

A piece is one window of one document: at most L targets. The format, per piece:

    targets       the document's tokens as the shard stores them (the last piece ends with EOS, 130822)
    input_ids     the token before each target: BOS (130725) first, then targets[:-1]
                  (a later piece of a long document starts with the last target of the piece before)
    byte_lengths  UTF-8 bytes of each target from the raw byte table; 0 for EOS (it stands for no text)
    pos_ids       0, 1, 2, ... restarting in every piece

Rows are not compared: Team 6's loader mixes datasets, so different pieces sit side by side.

Write our pieces for some documents of a shard (Team 6 can diff theirs against this file):

    python teams/05-architecture/lab5/packed_rows/piece_check.py --shard <dir>/en-fineweb-edu-train-000000.bin \
        --byte-table teams/04-ke2/results/tables/p1536-s0/raw_table_P32.npz --docs 0 1 2 --out ours.json

Check a file of pieces from another loader (JSON: a list of {doc, piece, input_ids, targets, byte_lengths,
pos_ids}) against the format; exit code 1 and the first difference if anything differs:

    python teams/05-architecture/lab5/packed_rows/piece_check.py --shard ... --byte-table ... --check theirs.json

Check Team 5's own reader (week2/data.py, run.pack) against the format on real shard documents: the
documents are rebuilt as text from the byte table and read the way the trainer reads training text:

    python teams/05-architecture/lab5/packed_rows/piece_check.py --shard ... --byte-table ... \
        --tokenizer <p1536 tokenizer.json> --docs 0 1 2 --against-reader
"""

import argparse
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

BOS, EOS = 130725, 130822
HEADER = 1024          # G1 shard: 256 little-endian int32 (magic 20261025, version 2, token count, zeros)
FIELDS = ("input_ids", "targets", "byte_lengths", "pos_ids")


def shard_documents(bin_path):
    """(tokens, offsets) of a G1 shard; document i is tokens[offsets[i]:offsets[i + 1]], ending with EOS."""
    bin_path = Path(bin_path)
    meta = json.loads(bin_path.with_suffix(".json").read_text(encoding="utf8"))
    header = np.fromfile(bin_path, dtype="<i4", count=256)
    if header[:3].tolist() != [20261025, 2, meta["token_count"]] or header[3:].any():
        raise SystemExit(f"{bin_path}: not a G1 shard (header)")
    tokens = np.memmap(bin_path, dtype="<u4", mode="r", offset=HEADER)
    offsets = np.load(bin_path.with_name(bin_path.name[:-4] + ".idx.npy"), allow_pickle=False)
    if int(meta.get("eos_token_id", EOS)) != EOS:
        raise SystemExit(f"{bin_path}: EOS is {meta.get('eos_token_id')}, the format expects {EOS}")
    return tokens, offsets


def format_pieces(doc_tokens, seq_len, lengths, bos=BOS, eos=EOS):
    """The format's pieces of one stored document (its tokens end with EOS), computed from the shard alone."""
    doc = [int(t) for t in doc_tokens]
    if not doc or doc[-1] != eos:
        raise ValueError("A stored document ends with EOS")
    pieces = []
    for start in range(0, len(doc), seq_len):
        targets = doc[start:start + seq_len]
        pieces.append(dict(
            input_ids=[bos if start == 0 else doc[start - 1]] + targets[:-1],
            targets=targets,
            byte_lengths=[0 if t == eos else int(lengths[t]) for t in targets],
            pos_ids=list(range(len(targets)))))
    return pieces


def compare(expected, actual):
    """The first difference between two lists of pieces, or None."""
    if len(expected) != len(actual):
        return f"{len(actual)} pieces, the format gives {len(expected)}"
    for n, (e, a) in enumerate(zip(expected, actual)):
        for field in FIELDS:
            ev, av = [int(v) for v in e[field]], [int(v) for v in a[field]]
            if ev != av:
                at = next((i for i, (x, y) in enumerate(zip(ev, av)) if x != y), min(len(ev), len(av)))
                return (f"piece {n}, {field}: differs at position {at} "
                        f"(format {ev[at] if at < len(ev) else 'end'}, other {av[at] if at < len(av) else 'end'}; "
                        f"lengths {len(ev)} and {len(av)})")
    return None


def document_text(doc_tokens, table_bytes, lengths):
    """The document's text, rebuilt exactly from the raw byte table (without its EOS)."""
    raw = b"".join(table_bytes[t, :int(lengths[t])].tobytes() for t in doc_tokens[:-1])
    return raw.decode("utf8")


def reader_pieces(texts, artifacts, seq_len):
    """Team 5's reader (week2/data.py) on these texts, as the trainer reads packed training text."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness"))
    from week2.data import DocumentWindows
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "docs.jsonl"
        path.write_text("".join(json.dumps({"text": t}) + "\n" for t in texts), encoding="utf8")
        windows = DocumentWindows(path, artifacts, seq_len, eos_id=artifacts.eos_id).windows
    return [dict(input_ids=a, targets=b, byte_lengths=c, pos_ids=list(range(len(b)))) for a, b, c in windows]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--shard", required=True, help="a G1 shard .bin (its .json and .idx.npy beside it)")
    ap.add_argument("--byte-table", required=True, help="Team 4's raw byte table (format v2) for the tokenizer")
    ap.add_argument("--seq-len", type=int, default=2048)
    ap.add_argument("--docs", type=int, nargs="+", default=[0, 1, 2], help="document numbers in the shard")
    ap.add_argument("--out", help="write the format's pieces of --docs to this JSON file")
    ap.add_argument("--check", help="JSON file of pieces from another loader, checked against the format")
    ap.add_argument("--against-reader", action="store_true", help="check Team 5's reader on --docs")
    ap.add_argument("--tokenizer", help="tokenizer JSON (frozen p1536), for --against-reader")
    a = ap.parse_args()

    tokens, offsets = shard_documents(a.shard)
    with np.load(a.byte_table, allow_pickle=False) as z:
        table_bytes, lengths = z["bytes"], z["lengths"]
    doc = lambda i: tokens[int(offsets[i]):int(offsets[i + 1])]
    if a.check:
        theirs = json.loads(Path(a.check).read_text(encoding="utf8"))
        bad = 0
        for i in sorted({int(p["doc"]) for p in theirs}):
            got = sorted((p for p in theirs if int(p["doc"]) == i), key=lambda p: int(p["piece"]))
            diff = compare(format_pieces(doc(i), a.seq_len, lengths), got)
            print(f"document {i}: {'matches' if diff is None else diff}")
            bad += diff is not None
        raise SystemExit(1 if bad else 0)
    if a.against_reader:
        if not a.tokenizer:
            raise SystemExit("--against-reader needs --tokenizer")
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness"))
        from week2.artifacts import Artifacts, P1536_SHA256
        artifacts = Artifacts(a.tokenizer, a.byte_table, expected_tokenizer_sha=P1536_SHA256)
        bad = 0
        for i in a.docs:
            ours = reader_pieces([document_text(doc(i), table_bytes, lengths)], artifacts, a.seq_len)
            diff = compare(format_pieces(doc(i), a.seq_len, lengths), ours)
            print(f"document {i} ({len(doc(i))} tokens with EOS, {len(ours)} pieces): "
                  f"{'matches' if diff is None else diff}")
            bad += diff is not None
        raise SystemExit(1 if bad else 0)
    pieces = [dict(doc=i, piece=n, **p) for i in a.docs for n, p in enumerate(format_pieces(doc(i), a.seq_len, lengths))]
    text = json.dumps(pieces)
    if a.out:
        Path(a.out).write_text(text, encoding="utf8")
        print(f"{len(pieces)} pieces of documents {a.docs} written to {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
