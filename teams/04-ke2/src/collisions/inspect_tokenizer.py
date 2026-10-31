#!/usr/bin/env python
"""KE2 collisions, step 1: tokenizer census.

Facts we need before grouping collisions:
  1. vocab size, added/special tokens, ID gaps, model-vocab vs added-ID overlap
  2. raw bytes per ID (byte-level map for normal tokens, UTF-8 literal for added)
  3. byte-length histogram, counts > 32 and > 64
  4. UTF-8 fragments (raw bytes not valid UTF-8 on their own)
  5. size of the decode([id]) bug (U+FFFD collapse) and of the library's
     token_id_to_bytes / build_byte_buffer path vs the raw table
  6. exact duplicate raw byte strings (untruncated)
  7. single-byte coverage (can every byte 0..255 be produced by one token?)
  8. codec smoke test: encode_single at P=32/64 vs the closed form

Usage:
  python inspect_tokenizer.py [--tokenizer PATH_OR_HF_ID]
Writes teams/04-ke2/results/inspect_<name>.json (override with --out).
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import sys
import time
from pathlib import Path

FFFD = "�".encode()  # EF BF BD


# ---------------------------------------------------------------- byte map
def gpt2_bytes_to_unicode() -> dict[int, str]:
    """GPT-2 / o200k ByteLevel table: byte value -> printable unicode char."""
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return {b: chr(c) for b, c in zip(bs, cs, strict=True)}


BYTE_DECODER = {c: b for b, c in gpt2_bytes_to_unicode().items()}


def piece_to_bytes(piece: str) -> bytes | None:
    """Byte-level piece -> raw bytes. None if any char is outside the map."""
    try:
        return bytes(BYTE_DECODER[ch] for ch in piece)
    except KeyError:
        return None


# ---------------------------------------------------------------- loading
def load_tokenizer(name: str):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(name)


def tokenizer_json_sha256(name: str) -> str | None:
    p = Path(name) / "tokenizer.json"
    if not p.is_file():
        try:
            from huggingface_hub import hf_hub_download

            p = Path(hf_hub_download(name, "tokenizer.json"))
        except Exception:
            return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------- census
def build_raw_table(tok):
    """Return (V, raw[list[bytes|None]], kind[list[str]], info dict).

    kind: normal | special | added | unmapped | gap
    """
    bt = tok.backend_tokenizer
    model_vocab = bt.get_vocab(with_added_tokens=False)  # piece -> id
    added = bt.get_added_tokens_decoder()  # id -> AddedToken
    all_ids = set(model_vocab.values()) | set(added)
    V = max(all_ids) + 1

    raw: list[bytes | None] = [None] * V
    kind: list[str] = ["gap"] * V
    unmapped_examples = []

    for i in range(V):
        if i in added:
            a = added[i]
            raw[i] = a.content.encode("utf-8")
            kind[i] = "special" if a.special else "added"
            continue
        piece = bt.id_to_token(i)
        if piece is None:
            continue
        b = piece_to_bytes(piece)
        if b is None:
            kind[i] = "unmapped"
            if len(unmapped_examples) < 10:
                unmapped_examples.append({"id": i, "piece": piece})
        else:
            raw[i] = b
            kind[i] = "normal"

    overlap = sorted(set(model_vocab.values()) & set(added))
    info = {
        "V": V,
        "len_tok": len(tok),
        "model_vocab_size": len(model_vocab),
        "n_added": len(added),
        "n_added_special": sum(a.special for a in added.values()),
        "added_id_ranges": id_ranges(sorted(added)),
        "model_vs_added_id_overlap": {
            "count": len(overlap),
            "examples": [{"id": i, "added": added[i].content, "model_piece": bt.id_to_token(i)} for i in overlap[:10]],
        },
        "named_specials": {
            k: [getattr(tok, k, None), getattr(tok, k + "_id", None)]
            for k in ("bos_token", "eos_token", "pad_token", "unk_token")
        },
        "all_special_ids_count": len(set(tok.all_special_ids or [])),
        "unmapped_examples": unmapped_examples,
    }
    return V, raw, kind, info


def id_ranges(ids: list[int]) -> list[list[int]]:
    out = []
    for i in ids:
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return out


def is_valid_utf8(b: bytes) -> bool:
    try:
        b.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def length_stats(raw, kind, which: str) -> dict:
    lens = [len(b) for b, k in zip(raw, kind, strict=True) if k == which and b is not None]
    if not lens:
        return {"n": 0}
    hist = collections.Counter(lens)
    longest = max(range(len(raw)), key=lambda i: len(raw[i]) if kind[i] == which and raw[i] is not None else -1)
    return {
        "n": len(lens),
        "max": max(lens),
        "mean": round(sum(lens) / len(lens), 3),
        "n_empty": hist.get(0, 0),
        "n_gt_32": sum(v for k, v in hist.items() if k > 32),
        "n_gt_64": sum(v for k, v in hist.items() if k > 64),
        "longest_example": {"id": longest, "len": len(raw[longest]), "hex": raw[longest].hex()},
        "hist": dict(sorted(hist.items())),
    }


def decode_bug(tok, raw, kind, V) -> dict:
    """decode([id]) vs raw table; and the library's token_id_to_bytes path."""
    ids = [i for i in range(V) if kind[i] in ("normal", "special", "added")]
    t0 = time.time()
    dec = tok.batch_decode([[i] for i in ids], skip_special_tokens=False, clean_up_tokenization_spaces=False)
    dec_b = {i: d.encode("utf-8") for i, d in zip(ids, dec, strict=True)}
    t_dec = time.time() - t0

    differ = [i for i in ids if dec_b[i] != raw[i]]
    with_fffd = [i for i in ids if FFFD in dec_b[i]]
    groups = collections.defaultdict(list)
    for i in ids:
        groups[dec_b[i]].append(i)
    raw_groups = collections.Counter(raw[i] for i in ids)
    # IDs that are unique in the raw table but share a decode([id]) output
    collapsed = [i for i in ids if len(groups[dec_b[i]]) > 1 and raw_groups[raw[i]] == 1]
    biggest = max(groups.items(), key=lambda kv: len(kv[1]))

    out = {
        "seconds": round(t_dec, 2),
        "n_checked": len(ids),
        "n_decode_differs_from_raw": len(differ),
        "n_decode_contains_fffd": len(with_fffd),
        "n_raw_unique_but_decode_shared": len(collapsed),
        "largest_decode_group": {"n": len(biggest[1]), "hex": biggest[0].hex(), "ids_head": biggest[1][:10]},
        "differ_examples": [{"id": i, "raw_hex": raw[i].hex(), "decode_hex": dec_b[i].hex()} for i in differ[:10]],
    }

    # library path (kronecker_embeddings.token_id_to_bytes) — what build_byte_buffer uses
    try:
        from kronecker_embeddings import token_id_to_bytes

        special_ids = set(tok.all_special_ids or [])
        lib_diff = []
        for i in ids:
            if token_id_to_bytes(tok, i, special_ids) != raw[i]:
                lib_diff.append(i)
        out["library_token_id_to_bytes"] = {
            "n_differs_from_raw": len(lib_diff),
            "examples": [
                {"id": i, "raw_hex": raw[i].hex(), "lib_hex": token_id_to_bytes(tok, i, special_ids).hex()}
                for i in lib_diff[:10]
            ],
        }
    except Exception as e:
        out["library_token_id_to_bytes"] = {"error": repr(e)}
    return out


def duplicates(raw, kind, V) -> dict:
    groups = collections.defaultdict(list)
    for i in range(V):
        if raw[i] is not None:
            groups[raw[i]].append(i)
    dup = [ids for ids in groups.values() if len(ids) > 1]
    split = collections.Counter()
    for ids in dup:
        ks = {"special" if kind[i] in ("special", "added") else "normal" for i in ids}
        split["+".join(sorted(ks))] += 1
    return {
        "n_groups": len(dup),
        "n_tokens_in_groups": sum(len(g) for g in dup),
        "by_kind": dict(split),
        "examples": [
            {"ids": ids[:10], "hex": raw[ids[0]].hex(), "kinds": [kind[i] for i in ids[:10]]} for ids in dup[:20]
        ],
    }


def single_byte_coverage(raw, kind) -> dict:
    have = {raw[i][0] for i in range(len(raw)) if kind[i] == "normal" and raw[i] is not None and len(raw[i]) == 1}
    missing = sorted(set(range(256)) - have)
    return {"n_covered": len(have), "missing_hex": [f"{b:02x}" for b in missing]}


def codec_smoke(raw, kind) -> dict:
    """encode_single at P=32/64 vs closed form. Picks a few representative IDs."""
    try:
        import torch
        from kronecker_embeddings import encode_single
    except Exception as e:
        return {"error": repr(e)}

    normal = [i for i in range(len(raw)) if kind[i] == "normal" and raw[i]]
    picks = {
        "shortest": min(normal, key=lambda i: len(raw[i])),
        "longest": max(normal, key=lambda i: len(raw[i])),
        "fragment": next((i for i in normal if not is_valid_utf8(raw[i])), None),
        "devanagari": next(
            (i for i in normal if is_valid_utf8(raw[i]) and any("ऀ" <= c <= "ॿ" for c in raw[i].decode())), None
        ),
        "special": next((i for i in range(len(raw)) if kind[i] == "special"), None),
    }
    eps = 1e-6
    rows = []
    for label, i in picks.items():
        if i is None:
            rows.append({"label": label, "id": None})
            continue
        for P in (32, 64):
            b = raw[i]
            L = min(len(b), P)
            D = 256 * P
            z = encode_single(b, pos_dim=P)
            x = encode_single(b, pos_dim=P, z_normalize=False)
            nz = int((x != 0).sum())
            # closed form (ddof=1 std, plus eps as in the library)
            mu = math.sqrt(L) / D
            sd = math.sqrt((1 - L / D) / (D - 1))
            hi = (1 / math.sqrt(L) - mu) / (sd + eps)
            lo = (0 - mu) / (sd + eps)
            expect = torch.where(x != 0, torch.tensor(hi), torch.tensor(lo))
            rows.append(
                {
                    "label": label,
                    "id": i,
                    "P": P,
                    "L": L,
                    "shape": list(z.shape),
                    "shape_ok": list(z.shape) == [D],
                    "nonzero_raw": nz,
                    "nonzero_ok": nz == L,
                    "max_abs_err_vs_closed_form": float((z.double() - expect.double()).abs().max()),
                    "z_mean": float(z.double().mean()),
                    "z_std_ddof1": float(z.double().std()),
                }
            )
    return {"rows": rows}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--tokenizer",
        default=None,
        help="tokenizer folder / HF id (default: the pinned BrahmicTokenizer-131K, found locally)",
    )
    ap.add_argument("--out", default=None, help="output JSON path")
    args = ap.parse_args()

    t0 = time.time()
    if args.tokenizer is None:  # same lookup as the ke2 package: env vars, then the HF cache
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from ke2.tokenizer import resolve_tokenizer_path

        args.tokenizer = str(resolve_tokenizer_path().parent)
        label = "theschoolofai/BrahmicTokenizer-131K"
    elif Path(args.tokenizer).exists():
        label = Path(args.tokenizer).name  # a local folder: record its name, never the full path
    else:
        label = args.tokenizer  # an HF id
    name = label.rstrip("/").split("/")[-1]
    tok = load_tokenizer(args.tokenizer)
    V, raw, kind, info = build_raw_table(tok)

    report = {
        "tokenizer": label,
        "tokenizer_json_sha256": tokenizer_json_sha256(args.tokenizer),
        "tokenizer_class": type(tok).__name__,
        "versions": versions(),
        "kind_counts": dict(collections.Counter(kind)),
        **info,
        "length_normal": length_stats(raw, kind, "normal"),
        "length_special": length_stats(raw, kind, "special"),
        "length_added_nonspecial": length_stats(raw, kind, "added"),
        "n_utf8_fragments_normal": sum(
            1 for b, k in zip(raw, kind, strict=True) if k == "normal" and not is_valid_utf8(b)
        ),
        "single_byte_coverage": single_byte_coverage(raw, kind),
        "exact_duplicates": duplicates(raw, kind, V),
        "decode_bug": decode_bug(tok, raw, kind, V),
        "codec_smoke": codec_smoke(raw, kind),
    }
    report["seconds_total"] = round(time.time() - t0, 2)

    out = Path(args.out) if args.out else Path(__file__).resolve().parents[2] / "results" / f"inspect_{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=True))
    print_summary(report)
    print(f"\nwrote {out}")


def versions() -> dict:
    v = {}
    for m in ("transformers", "tokenizers", "kronecker_embeddings", "torch"):
        try:
            v[m] = __import__(m).__version__
        except Exception:
            v[m] = None
    return v


def print_summary(r: dict):
    ln, ls = r["length_normal"], r["length_special"]
    db, dup = r["decode_bug"], r["exact_duplicates"]
    lib = db.get("library_token_id_to_bytes", {})
    print(f"tokenizer        {r['tokenizer']}  ({r['tokenizer_class']})")
    print(f"sha256           {r['tokenizer_json_sha256']}")
    print(f"versions         {r['versions']}")
    print(f"V / len(tok)     {r['V']} / {r['len_tok']}")
    print(f"kinds            {r['kind_counts']}")
    print(f"added / special  {r['n_added']} / {r['n_added_special']}   ranges {r['added_id_ranges'][:6]}")
    print(
        f"model∩added IDs  {r['model_vs_added_id_overlap']['count']}  {r['model_vs_added_id_overlap']['examples'][:3]}"
    )
    print(f"named specials   {r['named_specials']}")
    print(
        f"normal lengths   max {ln.get('max')}  mean {ln.get('mean')}  "
        f"empty {ln.get('n_empty')}  >32 {ln.get('n_gt_32')}  >64 {ln.get('n_gt_64')}"
    )
    print(f"special lengths  max {ls.get('max')}  >32 {ls.get('n_gt_32')}  >64 {ls.get('n_gt_64')}")
    print(f"utf8 fragments   {r['n_utf8_fragments_normal']}")
    print(
        f"single bytes     {r['single_byte_coverage']['n_covered']}/256  "
        f"missing {r['single_byte_coverage']['missing_hex']}"
    )
    print(f"exact dups       groups {dup['n_groups']}  tokens {dup['n_tokens_in_groups']}  {dup['by_kind']}")
    print(
        f"decode([id])     differs {db['n_decode_differs_from_raw']}  "
        f"has FFFD {db['n_decode_contains_fffd']}  "
        f"unique→shared {db['n_raw_unique_but_decode_shared']}  "
        f"largest group {db['largest_decode_group']['n']}"
    )
    print(f"library bytes    differs {lib.get('n_differs_from_raw', lib.get('error'))}")
    cs = r["codec_smoke"]
    if "error" in cs:
        print(f"codec smoke      ERROR {cs['error']}")
    else:
        for row in cs["rows"]:
            if row.get("id") is None:
                print(f"codec smoke      {row['label']:<10} (none found)")
                continue
            print(
                f"codec smoke      {row['label']:<10} id {row['id']:>6} P {row['P']:>2} L {row['L']:>2} "
                f"shape_ok {row['shape_ok']} nonzero_ok {row['nonzero_ok']} "
                f"err {row['max_abs_err_vs_closed_form']:.2e} std {row['z_std_ddof1']:.6f}"
            )
    print(f"seconds          {r['seconds_total']}")


if __name__ == "__main__":
    main()
