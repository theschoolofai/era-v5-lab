"""R1/R2 code-point audit for a Telugu shard sample (Data B week-4 rotation).

Usage: python3 -I r1_te.py <folder with documents.tsv, shard_D4/, raw_D4/> [out.json]

Checks each decoded shard document by code point, and tags every finding as
"source" (the same context exists in the NFC raw text) or "cleaning".
Prints counts only; findings (ids, offsets, hex) go to out.json.
"""
import hashlib
import json
import re
import sys
import time
import unicodedata as ud
from difflib import SequenceMatcher
from pathlib import Path

ZWJ, ZWNJ = "‍", "‌"
VIRAMA = "్"
A1_CHARS = set("​﻿­⁠‎‏") | {chr(c) for c in range(0x202A, 0x202F)} | {
    chr(c) for c in range(0x2066, 0x206A)} | {"︎", "️"}
MOJIBAKE = re.compile(r"Ã.|à[°±¤¥¦§¨©ª«¬®¯]|â€")


def is_te(ch):
    return "ఀ" <= ch <= "౿"


def is_te_mark(ch):
    return is_te(ch) and ud.category(ch).startswith("M")


def is_vowel_sign(ch):
    return is_te_mark(ch) and ch != VIRAMA and ud.category(ch) in ("Mc", "Mn") and (
        "ా" <= ch <= "ౌ" or ch in "ౕౖౢౣ")


def script_of(ch):
    if not ch.isalpha() and not ud.category(ch).startswith("M"):
        return None
    try:
        name = ud.name(ch)
    except ValueError:
        return "UNKNOWN"
    return name.split()[0]


def hexdump(text, i, width=1):
    lo, hi = max(0, i - 3), min(len(text), i + width + 3)
    parts = []
    for j in range(lo, hi):
        cp = f"U+{ord(text[j]):04X}"
        parts.append(f"**{cp}**" if i <= j < i + width else cp)
    return " ".join(parts)


def scan(text):
    out = []

    def add(code, i, what, width=1):
        out.append({"code": code, "offset": i, "what": what, "hex": hexdump(text, i, width),
                    "ctx": text[max(0, i - 3):i + width + 3]})

    for i, ch in enumerate(text):
        prev = text[i - 1] if i else ""
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if is_te_mark(ch) and not (is_te(prev) and ud.category(prev).startswith("L") or is_te_mark(prev)):
            add("G1", i, f"{ud.name(ch)} not attached to a Telugu letter (after U+{ord(prev):04X})" if prev
                else f"{ud.name(ch)} at document start")
        if is_vowel_sign(ch) and is_vowel_sign(prev):
            add("VV", i - 1, "two dependent vowel signs in a row", 2)
        if ch == VIRAMA and (nxt == VIRAMA or is_vowel_sign(nxt)):
            add("VV", i, "virama followed by a vowel sign or second virama", 2)
        if ch in (ZWJ, ZWNJ):
            name = "ZWJ" if ch == ZWJ else "ZWNJ"
            if not is_te(prev) or not is_te(nxt):
                add("G2", i, f"{name} at a word edge")
            elif nxt in (ZWJ, ZWNJ):
                add("G2", i, f"{name} doubled")
        if ch in A1_CHARS:
            add("A1", i, ud.name(ch, "invisible"))
        cat = ud.category(ch)
        if cat == "Cc" and ch not in "\n\t\r":
            add("A2", i, f"control U+{ord(ch):04X}")
        if ch == "�":
            add("A4", i, "replacement character")
    for m in MOJIBAKE.finditer(text):
        add("A3", m.start(), "mojibake pattern", len(m.group()))
    # A6: a run of letters/marks with no space that mixes Telugu with another script
    for m in re.finditer(r"[^\W\d_]+|[ఀ-౿‌‍]+", text):
        word = m.group()
        scripts = {script_of(c) for c in word} - {None}
        if "TELUGU" in scripts and len(scripts) > 1:
            j = next(k for k, c in enumerate(word) if script_of(c) not in (None, "TELUGU"))
            add("A6", m.start() + j, f"{sorted(scripts - {'TELUGU'})} letter inside a Telugu word")
    return out


def tag_source(f, raw_nfc, shard, sm_ops):
    ctx = f["ctx"]
    if ctx and ctx in raw_nfc:
        return "source"
    for tag, i1, i2, j1, j2 in sm_ops:
        if tag != "equal" and j1 - 3 <= f["offset"] <= j2 + 3:
            return "cleaning"
    return "source?"


def main(folder, out_path=None):
    t0 = time.time()
    folder = Path(folder)
    rows = [line.split("\t") for line in (folder / "documents.tsv").read_text().splitlines()[1:]]
    all_findings, summary = [], {"docs": 0, "sha_ok": 0, "nfc_bad": [], "identical_to_raw": 0,
                                 "changed_by_cleaning": [], "zwj": [0, 0], "zwnj": [0, 0]}
    for doc_id, n_shard, n_raw, sha in rows:
        shard = (folder / "shard_D4" / f"{doc_id}.txt").read_text(encoding="utf-8")
        raw = (folder / "raw_D4" / f"{doc_id}.txt").read_text(encoding="utf-8")
        raw_nfc = ud.normalize("NFC", raw)
        summary["docs"] += 1
        summary["sha_ok"] += hashlib.sha256(shard.encode()).hexdigest() == sha.strip()
        if ud.normalize("NFC", shard) != shard:
            summary["nfc_bad"].append(doc_id)
        summary["zwj"][0] += raw_nfc.count(ZWJ); summary["zwj"][1] += shard.count(ZWJ)
        summary["zwnj"][0] += raw_nfc.count(ZWNJ); summary["zwnj"][1] += shard.count(ZWNJ)
        ops = []
        if shard == raw_nfc:
            summary["identical_to_raw"] += 1
        else:
            ops = SequenceMatcher(None, raw_nfc, shard, autojunk=False).get_opcodes()
            changes = [(t, i1, i2, j1, j2) for t, i1, i2, j1, j2 in ops if t != "equal"]
            summary["changed_by_cleaning"].append({
                "doc_id": doc_id, "raw_len": len(raw_nfc), "shard_len": len(shard),
                "zwj": [raw_nfc.count(ZWJ), shard.count(ZWJ)], "zwnj": [raw_nfc.count(ZWNJ), shard.count(ZWNJ)],
                "edits": [{"op": t, "raw_off": i1, "shard_off": j1,
                           "removed_hex": " ".join(f"U+{ord(c):04X}" for c in raw_nfc[i1:i2][:12]),
                           "added_hex": " ".join(f"U+{ord(c):04X}" for c in shard[j1:j2][:12]),
                           "removed_len": i2 - i1, "added_len": j2 - j1} for t, i1, i2, j1, j2 in changes]})
        for f in scan(shard):
            f["doc_id"] = doc_id
            f["origin"] = tag_source(f, raw_nfc, shard, ops)
            all_findings.append(f)
    counts = {}
    for f in all_findings:
        counts[f["code"]] = counts.get(f["code"], 0) + 1
    summary["counts"] = counts
    summary["docs_with_finding"] = len({f["doc_id"] for f in all_findings})
    summary["origin"] = {o: sum(f["origin"] == o for f in all_findings) for o in ("source", "cleaning", "source?")}
    summary["wall_s"] = round(time.time() - t0, 2)
    if out_path:
        Path(out_path).write_text(json.dumps({"summary": summary, "findings": all_findings},
                                             ensure_ascii=False, indent=1), encoding="utf-8")
    s = dict(summary)
    s["changed_by_cleaning"] = [c["doc_id"] for c in summary["changed_by_cleaning"]]
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
