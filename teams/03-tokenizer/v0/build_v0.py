"""Build tokenizer v0 from BrahmicTokenizer-131K.

v0 = BrahmicTokenizer-131K with its 250 generic reserved slots (ids 130822-131071)
split into named blocks. Vocab size, merges, normal tokens and every token id stay the
same. Only the strings of 128 reserved specials change. See special_slots.md.

Usage:
    python build_v0.py <path/to/BrahmicTokenizer-131K/tokenizer.json> <out/tokenizer.json>
"""
import hashlib
import json
import sys

BASELINE_SHA256 = "01d968a7970b029c071b29f060abf6104b66168dedf2ff3b1a0290a545739fff"
FIRST_RESERVED_ID = 130822  # id of <|reserved_0|>

# (prefix, count). Blocks are laid out in order from FIRST_RESERVED_ID.
BLOCKS = [
    ("g10_slot", 64),   # 130822-130885: G10 special-token list (31 Oct)
    ("lang_slot", 32),  # 130886-130917: language / script tags
    ("ctrl_slot", 32),  # 130918-130949: data, eval and training control
]
# The last 122 slots (130950-131071) keep their names <|reserved_128|> .. <|reserved_249|>.


def slot_map():
    m, i = {}, 0
    for prefix, count in BLOCKS:
        for k in range(count):
            m[f"<|reserved_{i}|>"] = f"<|{prefix}_{k:02d}|>"
            i += 1
    return m


def main(src, dst):
    raw = open(src, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != BASELINE_SHA256:
        sys.exit(f"baseline sha256 mismatch: {sha}")
    t = json.loads(raw.decode("utf-8"))
    m = slot_map()

    renamed = 0
    for a in t["added_tokens"]:
        if a["content"] in m:
            old = a["content"]
            assert a["id"] == FIRST_RESERVED_ID + int(old[len("<|reserved_"):-2]), old
            assert a["special"], old
            a["content"] = m[old]
            renamed += 1
    assert renamed == len(m), renamed

    vocab = t["model"]["vocab"]
    t["model"]["vocab"] = {m.get(k, k): v for k, v in vocab.items()}
    assert len(t["model"]["vocab"]) == len(vocab) == 131072
    assert len({a["content"] for a in t["added_tokens"]}) == len(t["added_tokens"]) == 356

    # Same serialisation as the baseline file (json.dumps defaults, ensure_ascii=False).
    out = json.dumps(t, ensure_ascii=False).encode("utf-8")
    open(dst, "wb").write(out)
    print(f"renamed {renamed} reserved slots")
    print(f"sha256 {hashlib.sha256(out).hexdigest()}  {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
