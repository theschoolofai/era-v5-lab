"""Inspect a parquet sample pack one document at a time without altering Indic text.

The raw document is always printed unchanged. Diagnostic views are separate so that
ZWJ/ZWNJ and other shaping characters do not get replaced inside the text being read.

Usage:
    python view_pack.py <pack.parquet>
    python view_pack.py <pack.parquet> --row 53
    python view_pack.py <pack.parquet> --start 52
    python view_pack.py <pack.parquet> --audit
    python view_pack.py <pack.parquet> --unicode 2400 2460
Navigation:
    Enter       next document
    b           previous document
    h           toggle audit diagnostics
    u A B       print every Unicode code point in text[A:B]
    q           quit

Notes:
- --row is 1-based and recommended for humans.
- --start is retained for backward compatibility and is 0-based.
- Terminal glyph shaping is NOT evidence of G1/G2. Use the Unicode view to verify
  the actual code points and offsets.
"""

from __future__ import annotations
import argparse
import re
import unicodedata
from collections import Counter

# C0/C1 control names that unicodedata.name() does not reliably expose.
CONTROL_NAMES = {
    0x0000: "NULL",
    0x0001: "START OF HEADING",
    0x0002: "START OF TEXT",
    0x0003: "END OF TEXT",
    0x0004: "END OF TRANSMISSION",
    0x0005: "ENQUIRY",
    0x0006: "ACKNOWLEDGE",
    0x0007: "BELL",
    0x0008: "BACKSPACE",
    0x0009: "CHARACTER TABULATION",
    0x000A: "LINE FEED",
    0x000B: "LINE TABULATION",
    0x000C: "FORM FEED",
    0x000D: "CARRIAGE RETURN",
    0x000E: "SHIFT OUT",
    0x000F: "SHIFT IN",
    0x0010: "DATA LINK ESCAPE",
    0x0011: "DEVICE CONTROL ONE",
    0x0012: "DEVICE CONTROL TWO",
    0x0013: "DEVICE CONTROL THREE",
    0x0014: "DEVICE CONTROL FOUR",
    0x0015: "NEGATIVE ACKNOWLEDGE",
    0x0016: "SYNCHRONOUS IDLE",
    0x0017: "END OF TRANSMISSION BLOCK",
    0x0018: "CANCEL",
    0x0019: "END OF MEDIUM",
    0x001A: "SUBSTITUTE",
    0x001B: "ESCAPE",
    0x001C: "INFORMATION SEPARATOR FOUR",
    0x001D: "INFORMATION SEPARATOR THREE",
    0x001E: "INFORMATION SEPARATOR TWO",
    0x001F: "INFORMATION SEPARATOR ONE",
    0x007F: "DELETE",
    0x0085: "NEXT LINE",
}

# Characters worth reporting separately. They are NOT substituted into raw text.
SPECIAL_NAMES = {
    0x00A0: "NO-BREAK SPACE",
    0x00AD: "SOFT HYPHEN",
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x2060: "WORD JOINER",
    0x202A: "LEFT-TO-RIGHT EMBEDDING",
    0x202B: "RIGHT-TO-LEFT EMBEDDING",
    0x202C: "POP DIRECTIONAL FORMATTING",
    0x202D: "LEFT-TO-RIGHT OVERRIDE",
    0x202E: "RIGHT-TO-LEFT OVERRIDE",
    0x2066: "LEFT-TO-RIGHT ISOLATE",
    0x2067: "RIGHT-TO-LEFT ISOLATE",
    0x2068: "FIRST STRONG ISOLATE",
    0x2069: "POP DIRECTIONAL ISOLATE",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE / BOM",
    0xFFFD: "REPLACEMENT CHARACTER",
}

# Dependent Devanagari marks that should normally be attached to a Devanagari base
# or another valid mark. We report suspicious placements as G1 *candidates* only.
DEVANAGARI_DEPENDENT_MARKS = (
    set(range(0x0900, 0x0904))  # candrabindu/anusvara/visarga and U+0900
    | set(range(0x093A, 0x094E))
    | set(range(0x094E, 0x0950))
    | set(range(0x0951, 0x0958))
    | set(range(0x0962, 0x0964))
) - {0x093D}  # DEVANAGARI SIGN AVAGRAHA is a letter, not a dependent mark.


def unicode_name(ch: str) -> str:
    """Return a useful Unicode name, including common names for controls."""
    cp = ord(ch)
    if cp in CONTROL_NAMES:
        return CONTROL_NAMES[cp]
    if cp in SPECIAL_NAMES:
        return SPECIAL_NAMES[cp]
    return unicodedata.name(ch, "UNKNOWN")


def char_repr(ch: str) -> str:
    """Readable one-character representation that never relies on glyph shaping."""
    if ch == "\n":
        return r"'\n'"
    if ch == "\r":
        return r"'\r'"
    if ch == "\t":
        return r"'\t'"
    if ch == " ":
        return "' '"
    return repr(ch)


def format_codepoint(offset: int, ch: str) -> str:
    return (
        f"{offset:6d}  {char_repr(ch):10}  U+{ord(ch):04X}  "
        f"{unicode_name(ch)}  [{unicodedata.category(ch)}]"
    )


def unicode_range(text: str, start: int, end: int) -> str:
    """Print EVERY character in text[start:end], including ordinary ASCII."""
    start = max(0, start)
    end = min(len(text), end)
    if start >= end:
        return f"(empty range {start}:{end}; text length={len(text)})"
    rows = [f"Unicode range {start}:{end} (text length={len(text)})"]
    rows.extend(format_codepoint(i, text[i]) for i in range(start, end))
    return "\n".join(rows)


def hidden_characters(text: str) -> list[tuple[int, str]]:
    """Return hidden/control/special characters without modifying the source text."""
    out = []
    for i, ch in enumerate(text):
        cp = ord(ch)
        cat = unicodedata.category(ch)
        if cp in SPECIAL_NAMES or (cat in {"Cc", "Cf", "Zl", "Zp"} and ch != "\n"):
            out.append((i, ch))
    return out


def _nfc_cluster(text: str, mark_index: int) -> tuple[int, int, str]:
    """Return a starter+combining-marks cluster around a candidate character."""
    start = mark_index
    while start > 0 and unicodedata.combining(text[start]) != 0:
        start -= 1
    end = mark_index + 1
    while end < len(text) and unicodedata.combining(text[end]) != 0:
        end += 1
    return start, end, text[start:end]


def nfc_candidates(text: str) -> list[tuple[int, str, str]]:
    """Return source offsets/clusters whose canonical form changes under NFC.

    Also detect standalone NFC-changing characters (including nukta letters)
    and adjacent composing code points with combining class 0 (split vowel signs).
    """
    seen = set()
    out = []
    for i, ch in enumerate(text):
        # Check for a genuine interaction between adjacent code points, not
        # merely NFC changes that already occur in either character alone.
        pair_composes = (
            i > 0
            and unicodedata.normalize("NFC", text[i - 1:i + 1])
            != (unicodedata.normalize("NFC", text[i - 1])
                + unicodedata.normalize("NFC", ch))
        )
        if (unicodedata.combining(ch) == 0
                and unicodedata.normalize("NFC", ch) == ch
                and not pair_composes):
            continue
        start, end, cluster = _nfc_cluster(text, i)
        if pair_composes:
            start = min(start, i - 1)
            cluster = text[start:end]
        if (start, end) in seen:
            continue
        seen.add((start, end))
        normalized = unicodedata.normalize("NFC", cluster)
        if cluster != normalized:
            out.append((start, cluster, normalized))
    return out


def is_devanagari(ch: str) -> bool:
    return 0x0900 <= ord(ch) <= 0x097F


def g1_candidates(text: str) -> list[tuple[int, str, str | None]]:
    """Find suspicious Devanagari dependent marks cut from a Devanagari context.
    This is intentionally a candidate detector, not an automatic diagnosis. A mark is
    suspicious when its immediate predecessor is whitespace or outside Devanagari
    (except ZWJ/ZWNJ). This catches e.g. `क ि`, `कs्`, and mojibake before a matra.
    """
    out = []
    for i, ch in enumerate(text):
        if ord(ch) not in DEVANAGARI_DEPENDENT_MARKS:
            continue
        prev = text[i - 1] if i else None
        if prev is None:
            out.append((i, ch, prev))
            continue
        if prev in {"\u200c", "\u200d"}:  # joiners can legitimately participate in clusters
            continue
        if prev.isspace() or not is_devanagari(prev):
            out.append((i, ch, prev))
    return out


def mixed_digit_candidates(text: str) -> list[tuple[int, str]]:
    """Find numeric tokens mixing ASCII and Devanagari digits, e.g. १0७."""
    out = []
    for m in re.finditer(r"[०-९0-9]+", text):
        token = m.group()
        if re.search(r"[०-९]", token) and re.search(r"[0-9]", token):
            out.append((m.start(), token))
    return out


def audit_report(text: str) -> str:
    """Compact whole-document diagnostic report with no silent 2,000-char cutoff."""
    sections = []
    hidden = hidden_characters(text)
    if hidden:
        counts = Counter(ord(ch) for _, ch in hidden)
        rows = ["Hidden/control characters:"]
        first_offset = {}
        for i, ch in hidden:
            first_offset.setdefault(ord(ch), i)
        for cp, count in sorted(counts.items(), key=lambda kv: first_offset[kv[0]]):
            suffix = f" ({count}x)" if count > 1 else ""
            rows.append(
                f"  {first_offset[cp]} U+{cp:04X} {unicode_name(chr(cp))}{suffix}"
            )
        sections.append("\n".join(rows))
    nfc = nfc_candidates(text)
    if nfc:
        rows = ["A5/NFC candidates:"]
        for offset, src, dst in nfc:
            src_desc = " + ".join(f"U+{ord(c):04X} {unicode_name(c)}" for c in src)
            dst_desc = " + ".join(f"U+{ord(c):04X} {unicode_name(c)}" for c in dst)
            rows.append(f"  {offset} {src_desc}  ->  {dst_desc}")
        sections.append("\n".join(rows))
    g1 = g1_candidates(text)
    if g1:
        rows = ["G1 candidates (verify in context):"]
        for offset, mark, prev in g1:
            if prev is None:
                prev_desc = "START OF TEXT"
            else:
                prev_desc = f"U+{ord(prev):04X} {unicode_name(prev)}"
            rows.append(
                f"  {offset} {prev_desc} + U+{ord(mark):04X} {unicode_name(mark)}"
            )
        sections.append("\n".join(rows))
    mixed = mixed_digit_candidates(text)
    if mixed:
        rows = ["Mixed Devanagari/ASCII digit candidates:"]
        for offset, token in mixed:
            cps = " + ".join(f"U+{ord(c):04X}" for c in token)
            rows.append(f"  {offset} {token!r}: {cps}")
        sections.append("\n".join(rows))

    if not sections:
        return "(no audit candidates found)"
    return "\n\n".join(sections)


def validate_row(d: dict, index: int) -> None:
    required = ("doc_id", "source", "lang_label", "text")
    missing = [k for k in required if k not in d]
    if missing:
        raise ValueError(f"row {index + 1}: missing required columns: {', '.join(missing)}")
    if d["text"] is None:
        raise ValueError(f"row {index + 1} doc_id={d.get('doc_id')!r}: text is null")
    if not isinstance(d["text"], str):
        raise TypeError(
            f"row {index + 1} doc_id={d.get('doc_id')!r}: text must be str, "
            f"got {type(d['text']).__name__}"
        )


def load_pack(path: str) -> list[dict]:
    """Load parquet with a helpful dependency error."""
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise SystemExit(
            "pyarrow is required to read parquet files. Install it with:\n"
            "    python -m pip install pyarrow"
        ) from exc

    rows = pq.read_table(path).to_pylist()
    for i, row in enumerate(rows):
        validate_row(row, i)
    return rows


def print_document(d: dict, i: int, total: int, audit: bool = False) -> None:
    text = d["text"]
    print("\n" + "=" * 100)
    print(
        f"[{i + 1}/{total}] doc_id={d['doc_id']}  source={d['source']}  "
        f"lang_label={d['lang_label']}  chars={len(text)}"
    )
    if d.get("url"):
        print("url:", d["url"])
    print("-" * 100)
    print(text)  # RAW TEXT: never substitute ZWJ/ZWNJ or other characters here.
    print("-" * 100)
    print(
        "NOTE: terminal glyph shaping is not evidence of G1/G2. "
        "Use `u START END` to inspect source code points."
    )
    if audit:
        print("-" * 100)
        print(audit_report(text))


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pack")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--start", type=int, default=None, help="0-based row index (legacy)")
    group.add_argument("--row", type=int, default=None, help="1-based row number")
    ap.add_argument(
        "--hex", "--audit", dest="audit", action="store_true",
        help="show whole-document audit diagnostics (legacy --hex alias retained)",
    )
    ap.add_argument(
        "--unicode", nargs=2, type=int, metavar=("START", "END"),
        help="print every code point in this zero-based character range for the first shown document",
    )
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    rows = load_pack(a.pack)
    if not rows:
        raise SystemExit("pack contains no rows")

    if a.row is not None:
        if not 1 <= a.row <= len(rows):
            raise SystemExit(f"--row must be between 1 and {len(rows)}")
        i = a.row - 1
    else:
        i = 0 if a.start is None else a.start
        if not 0 <= i < len(rows):
            raise SystemExit(f"--start must be between 0 and {len(rows) - 1}")
    audit = a.audit
    first = True
    while 0 <= i < len(rows):
        d = rows[i]
        print_document(d, i, len(rows), audit=audit)

        if first and a.unicode:
            print("-" * 100)
            print(unicode_range(d["text"], *a.unicode))
        first = False

        try:
            raw = input(
                "\n[Enter]=next  b=back  h=audit  u START END=unicode  q=quit > "
            ).strip()
        except EOFError:
            break  # Piped stdin may terminate before an interactive quit command.
        low = raw.lower()
        if low == "q":
            break
        if low == "b":
            i = max(0, i - 1)  # do not exit when backing up from row 1
            continue
        if low == "h":
            audit = not audit
            continue  # redisplay same document with/without diagnostics
        if low.startswith("u "):
            parts = raw.split()
            if len(parts) != 3:
                print("Usage: u START END")
                continue
            try:
                start, end = int(parts[1]), int(parts[2])
            except ValueError:
                print("START and END must be integers")
                continue
            print("-" * 100)
            print(unicode_range(d["text"], start, end))
            continue
        if raw == "":
            i += 1
            continue
        print("Unknown command. Use Enter, b, h, u START END, or q.")


if __name__ == "__main__":
    main()
