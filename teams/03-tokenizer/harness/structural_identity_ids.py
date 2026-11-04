#!/usr/bin/env python3
"""
structural_identity_ids.py
==========================

Companion to BrahmicTokenizer-131K/verify_sarvam_m_structural_identity.py.

That script compares two tokenizer.json files as *sets* (vocab strings, merge
pairs, added-token strings). It does not look at token ids. This script adds
the id-level view and an encode check, so we can say exactly when two
tokenizers give the same ids for the same text:

  1. token string -> id agreement for the normal vocab
  2. every id whose string differs between A and B
  3. pre_tokenizer / decoder / normalizer equality
  4. encode equality on a fixed multi-script sample (needs `pip install tokenizers`;
     skipped with a note if it is missing)

Usage
-----
    python structural_identity_ids.py A/tokenizer.json B/tokenizer.json

Exit code 0 always when both files parse (like the script it extends: it
reports, it does not judge). Exit code 2 if a file cannot be read.
"""
import json
import sys

SAMPLES = {
    "en": "The quick brown fox jumps over the lazy dog.",
    "hi": "भारत एक विशाल देश है और यहाँ कई भाषाएँ बोली जाती हैं।",
    "bn": "বাংলা ভাষা বিশ্বের অন্যতম সমৃদ্ধ ভাষা।",
    "ta": "தமிழ் மிகவும் பழமையான மொழிகளில் ஒன்றாகும்.",
    "te": "తెలుగు భాష చాలా మధురమైనది.",
    "or": "ଓଡ଼ିଆ ଭାଷା ଭାରତର ଏକ ପ୍ରାଚୀନ ଭାଷା।",
    "code": 'public static void main(String[] args) {\n    System.out.println("hi");\n}',
    "mixed": "Hello नमस्ते 123 😀",
}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} A/tokenizer.json B/tokenizer.json", file=sys.stderr)
        sys.exit(2)
    pa, pb = sys.argv[1], sys.argv[2]
    try:
        A, B = load(pa), load(pb)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    va, vb = A["model"]["vocab"], B["model"]["vocab"]
    same_id = sum(1 for k, v in va.items() if vb.get(k) == v)
    same_str = len(set(va) & set(vb))
    print(f"A: {pa}\nB: {pb}\n")
    print("--- token string -> id ---")
    print(f"  |A| {len(va):,}   |B| {len(vb):,}")
    print(f"  same string in both:        {same_str:,}")
    print(f"  same string AND same id:    {same_id:,}")
    print(f"  same string, different id:  {same_str - same_id:,}")

    ia = {v: k for k, v in va.items()}
    ib = {v: k for k, v in vb.items()}
    diff = [(i, ia.get(i), ib.get(i)) for i in sorted(set(ia) | set(ib)) if ia.get(i) != ib.get(i)]
    print(f"\n--- ids whose string differs: {len(diff)} ---")
    if diff:
        print(f"  lowest id {diff[0][0]}, highest id {diff[-1][0]}")
    for i, a, b in diff[:40]:
        print(f"  id {i:>6}:  A={a!r:<22} B={b!r}")

    print("\n--- pipeline pieces ---")
    for k in ("normalizer", "pre_tokenizer", "decoder", "post_processor"):
        print(f"  {k:<14} identical: {A.get(k) == B.get(k)}")

    print("\n--- encode check ---")
    try:
        from tokenizers import Tokenizer
    except ImportError:
        print("  skipped: pip install tokenizers")
        return
    ta, tb = Tokenizer.from_file(pa), Tokenizer.from_file(pb)
    allsame = True
    for name, s in SAMPLES.items():
        x, y = ta.encode(s).ids, tb.encode(s).ids
        allsame &= x == y
        print(f"  {name:<6} {len(x):>3} tokens   identical ids: {x == y}")
    print(f"  all samples identical: {allsame}")


if __name__ == "__main__":
    main()
