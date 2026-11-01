# Medicine sheet: ind-kn-fw2 (LokeshJatangi)

**Gold set used for the harm test: TBD**

Pack: **500 documents**, all labelled `full`: **239 clean, 231 fix, 30 drop**.
Counts below are documents carrying each saved label; codes overlap. They are **not measured repair coverage**.
Snapshot: `labels.csv`

**Gold validation: PENDING for every medicine and their combination.** No independent two-reader Kannada
gold set was supplied. Our 239 single-reader clean labels are not substituted for gold. No passing harm
result or claim of corpus-scale safety is made. Functional tests also require the recorded terminal output.

The six repair snippets below are intentionally narrower than the viewer's candidate checks. They cover
specific structures, not every document bearing a code. No rule changes the source pack, invents missing
text, drops a document, performs NFC/NFKC normalization, or converts Kannada digits. Empty results remain
empty strings for manual review. Structural deletions containing ZWJ/ZWNJ or compatibility characters are
skipped. F1 deliberately redacts only explicitly confirmed private-data spans, including their contents.

## Shared helpers

Run the Python snippets in document order in one namespace; they need only Python's standard library.
`remove_spans` preserves every character outside selected source ranges, including whitespace.

```python
import re
import unicodedata
from urllib.parse import urlsplit

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    merged = []
    for a, b in sorted(set(spans)):
        if protected(text[a:b]):
            continue
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    out, cursor = [], 0
    for a, b in merged:
        out.append(text[cursor:a])
        cursor = b
    return "".join(out) + text[cursor:]

def source_parts(url):
    try:
        p = urlsplit(url or "")
        return ((p.hostname or "").lower(), p.path) if p.scheme in {"http", "https"} else ("", "")
    except (ValueError, TypeError, AttributeError):
        return "", ""
```

## Medicine 1 — C1: boilerplate (180 documents)

**Examples:**

| doc_id | Exact evidence excerpt / position |
|---|---|
| `a7746a3981e58f31` | `Last Updated Mar 27, 2019, 3:47 PM IST` at 1257 |
| `bfe4d0c9f43dc03b` | `‘ವಾರ್ತಾ ಭಾರತಿ’ ನಿಮಗೆ ಆಪ್ತವೇ ?` at 1947; the complete two-line donation footer is required |
| `d78b35287b746574` | `Don't Miss!` at 0 |

**Rule / action: fix text.** Remove complete publication/update metadata lines, the exact social-follow
prompt, and the recognized navigation headers. Remove the exact terminal Vartha Bharati appeal only on
that host/subdomains. On News18 news URLs, remove the publisher/update label and its immediately following
supported timestamp. A Team Udayavani byline requires that publisher's host. Keep inline date mentions,
arbitrary bylines, standalone `India`, city names, `Title`, `Trending`, image credits and slogans outside
these precise rules; the broader viewer can suggest them for manual C1 review.

```python
MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DAY = r"(?:0?[1-9]|[12][0-9]|3[01])"
TIME = r"(?:(?:0?[1-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?\s+(?:AM|PM)|(?:[01]?[0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?)"
ZONE = r"(?:IST|UTC|GMT|[+-](?:[01][0-9]|2[0-3]):?[0-5][0-9])"
WEEKDAY = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
DATE = rf"(?:{WEEKDAY},\s*)?{MONTH}\.?\s+{DAY},\s*[0-9]{{4}},\s*{TIME}\s+(?:{ZONE}|\[{ZONE}\])"
MARKER = r"(?:First\s+Published|Last\s+(?:Modified|Updated)|Published|Updated)"
LOCAL_DATE = rf"(?:[\u0c80-\u0cff]+,\s*)?\d{{1,2}}\s+[\u0c80-\u0cff]+\s+\d{{4}}\s*\({TIME}\s+{ZONE}\)"
STAMP = re.compile(rf"{MARKER}(?:\s*:\s*|\s+)(?:{DATE}|{LOCAL_DATE})", re.I)
KANNADA_STAMP = re.compile(rf"(?:ಭಾನುವಾರ|ಸೋಮವಾರ|ಮಂಗಳವಾರ|ಬುಧವಾರ|ಗುರುವಾರ|ಶುಕ್ರವಾರ|ಶನಿವಾರ),\s*\d{{1,2}}\s+[\u0c80-\u0cff]+\s+\d{{4}}\s*\({TIME}\s+IST\)", re.I)
BARE_DATE = re.compile(DATE, re.I)
FOLLOW = re.compile(r"Please\s+follow\s+and\s+like\s+us\s*:?", re.I)
APPEAL = re.compile(r"(?m)^‘ವಾರ್ತಾ ಭಾರತಿ’ ನಿಮಗೆ ಆಪ್ತವೇ \? ಇದರ ಸುದ್ದಿಗಳು ಮತ್ತು ವಿಚಾರಗಳು ಎಲ್ಲರಿಗೆ ಉಚಿತವಾಗಿ ತಲುಪುತ್ತಿರಬೇಕೇ\?\r?\nಬೆಂಬಲಿಸಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ(?=[ \t\r\n]*\Z)")

def medicine_c1(text, url=""):
    host, path = source_parts(url)
    news18 = host == "kannada.news18.com" and (path == "/news" or path.startswith("/news/"))
    udayavani = host == "udayavani.com" or host.endswith(".udayavani.com")
    rows, spans, offset, previous_header = text.splitlines(keepends=True), [], 0, False
    for i, line in enumerate(rows):
        body, label = line.strip(), line.strip().casefold()
        header = news18 and label == "news18-kannada updated:"
        pair = label == "just in" and i + 1 < len(rows) and rows[i + 1].strip().casefold() in {"don't miss!", "don’t miss!"}
        byline = udayavani and body.startswith("Team Udayavani,") and BARE_DATE.fullmatch(body[len("Team Udayavani,"):].strip())
        if (STAMP.fullmatch(body) or KANNADA_STAMP.fullmatch(body) or FOLLOW.fullmatch(body)
                or label in {"don't miss!", "don’t miss!"} or pair or byline or header
                or (previous_header and BARE_DATE.fullmatch(body))):
            spans.append((offset, offset + len(line)))
        previous_header, offset = header, offset + len(line)
    if host == "varthabharati.in" or host.endswith(".varthabharati.in"):
        spans.extend((m.start(), m.end()) for m in APPEAL.finditer(text))
    return remove_spans(text, spans)
```

**Harm test:** pending; changed/dropped counts and percentage are not measured.
**Side effects:** a quoted metadata line or an article genuinely titled `Don't Miss!` can match. Date syntax
does not prove calendar validity or boilerplate intent. Altered/wrapped site footers and unfamiliar metadata
are missed. Missing URL provenance disables the site-specific branches rather than guessing a publisher.

## Medicine 2 — C5: keyword/link lists (47 documents)

**Examples:**

| doc_id | Exact evidence excerpt / position |
|---|---|
| `d78b35287b746574` | `- News ಸರ್ಕಾರದಿಂದ 84 ಸಾವಿರ ರೆಮಿಡಿಸ್ವಿರ್ ಖರೀದಿ: ಸುಧಾಕರ್` at 12 |
| `4f6fb355e6e5e1bd` | `- News ನಾಲ್ಕು ರಾಜ್ಯಗಳ ಮುಖ್ಯಮಂತ್ರಿಗಳ ಜತೆ ಪ್ರಧಾನಿ ಮೋದಿ ಮಾತುಕತೆ` at 12 |
| `ad31bf1d2b690c09` | `#BJP4Belagavi #BJP4Maski #BJP4Basavakalyana` at 1451 |

**Rule / action: fix text.** Remove at least two consecutive English-led teaser bullets immediately under
`Don't Miss!`, optionally preceded by `Just In`. C1 removes the remaining header. Remove a whole line only
when it consists entirely of two or more hashtag tokens. Accept spaces after `#` and adjacent hashtags.
Preserve inline tags in article sentences, isolated hashtags, ordinary Markdown headings and unheaded lists.

```python
NAV = re.compile(r"(?mi)^[ \t]*(?:Just In[ \t]*\r?\n)?[ \t]*Don['’]t Miss![ \t]*\r?\n(?P<links>(?:[ \t]*-[ \t]+[A-Za-z][^\r\n]*(?:\r?\n|$)){2,})")
TAG = r"#[ \t]*[^\W\d_][\w\u0c80-\u0cff\u200c\u200d]*"
TAG_CLOUD = re.compile(rf"[ \t]*(?:{TAG}[ \t]*){{2,}}")

def medicine_c5(text, url=""):
    spans = [(m.start("links"), m.end("links")) for m in NAV.finditer(text)]
    offset = 0
    for line in text.splitlines(keepends=True):
        if TAG_CLOUD.fullmatch(line.rstrip("\r\n")):
            spans.append((offset, offset + len(line)))
        offset += len(line)
    return remove_spans(text, spans)
```

**Harm test:** pending; no measured pass.
**Side effects:** a legitimate standalone social-tag list can be removed. A multiword tag such as
`#sachin tendulkar`, comma-separated tags, blank lines inside teaser lists, or a single teaser is outside
this narrow rule. No document is dropped just because much of it is a list.

## Medicine 3 — C2: repetition (17 documents)

**Examples:** exact excerpts; the repeated source spans may be longer.

| doc_id | Evidence |
|---|---|
| `c69e1a6483bd6ac2` | `ಚಿಕ್ಕಮಗಳೂರು : ಆತ್ಮೋದ್ಧಾರಕ್ಕೆ ಸೇವೆ` begins the repeated line at 0 and 3385 |
| `0f52e8c63e977510` | `ಎಲ್ಲ ಶೋಷಣೆಗಳೂ ಸುಳ್ಳುಗಳೂ ಅಗತ್ಯಸೇವೆಯೇ ಆಗುತ್ತಿರುವಾಗ,` begins a 249-character repeat at 23 and 7915 |
| `39d902703f233992` | `ಬೆಂಗಳೂರು: ಬೋಯಿಂಗ್ ಇಂಡಿಯಾ ಹಾಗೂ ಸೆಲ್ಕೊ ಅನುದಾನದಲ್ಲಿ ಬೆಂಗಳೂರಲ್ಲಿ` begins the repeated lead at 0 |

**Rule / action: fix text.** Keep the first exact long prose sentence/line and remove later non-overlapping
copies, including copies inside paragraphs. Require at least 80 code points, eight words and terminal
`.`, `!` or `?`. Skip fenced-code documents, verse-like layouts, quotation-led units and protected characters.
Do not treat different dated author attributions as identical: the Parveen Kaswan example remains a review
candidate, not a deletion rule. Short repeated titles/credits and paraphrases also stay manual.

```python
def medicine_c2(text, url=""):
    if "```" in text or "~~~" in text:
        return text
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    if len(lines) >= 6 and sum(len(s) < 60 and not s.endswith((".", "!", "?")) for s in lines) * 2 > len(lines):
        return text
    units = set(lines)
    units.update(m.group().strip() for m in re.finditer(r"[^.!?\r\n]+(?:[.!?]+|(?=[\r\n]|$))", text))
    units = [s for s in units if len(s) >= 80 and len(s.split()) >= 8 and s.endswith((".", "!", "?"))
             and not s.startswith(('"', "'", "‘", "“", ">")) and not protected(s)
             and not re.match(r"[—–-]\s+.*\(@[A-Za-z0-9_]+\)", s)]
    spans = []
    for unit in sorted(units, key=lambda s: (-len(s), s)):
        cursor = text.find(unit) + len(unit)
        while (a := text.find(unit, cursor)) >= 0:
            b = a + len(unit)
            if not (a and (text[a - 1].isalnum() or unicodedata.category(text[a - 1]).startswith("M"))):
                spans.append((a, b))
            cursor = b
    return remove_spans(text, spans)
```

**Harm test:** pending; no measured pass.
**Side effects:** intentionally restated long prose can still lose a later copy. Verse/layout detection is
a protective heuristic, not a genre classifier. Different internal whitespace, line wrapping, joiners,
capitalization or punctuation can prevent a match. Deleting a sentence can leave surrounding blank space;
that whitespace is deliberately not rewritten.

## Medicine 4 — G1: spacing / broken words (18 documents)

**Examples:**

| doc_id | Evidence |
|---|---|
| `7fd06bf25bcaa6d1` | `ಕೋಣೆ ಗಳ` at 137; also number–word spacing observations |
| `e5e0486d846b09a7` | `ಶೀಘ್ರ ದಲ್ಲೇ` at 107 |
| `2914f93d5aa778b8` | `ವಸಡಿನ ೊಂದನ್ನು` at 566; retained for manual linguistic repair |

**Rule / action: fix only the two explicit full-word spacing pairs below.** Local G1 labels include the
former spacing codes. A dangling virama/vowel sign does not establish which letters were lost; a generic
space-deletion regex cannot reliably reconstruct the word. Do not join all Kannada tokens or insert spaces
at every number–letter boundary. Preserve ordinals such as `10ನೇ`, valid loanword boundaries and joiners.

```python
G1_FIXES = {"ಕೋಣೆ ಗಳ": "ಕೋಣೆಗಳ", "ಶೀಘ್ರ ದಲ್ಲೇ": "ಶೀಘ್ರದಲ್ಲೇ"}
EDGE = r"[\w\u0c80-\u0cff\u200c\u200d]"
G1_PATTERN = re.compile(rf"(?<!{EDGE})(?:{'|'.join(map(re.escape, G1_FIXES))})(?!{EDGE})")

def medicine_g1(text, url=""):
    if "```" in text or "~~~" in text:
        return text
    return G1_PATTERN.sub(lambda m: G1_FIXES[m.group()], text)
```

**Harm test:** pending; no measured pass. Coverage is deliberately a subset of the 18 labelled documents.
**Side effects:** a lesson quoting either misspelling can be changed. Inflections and different whitespace
are not inferred. These mappings repair spacing, not other misspellings in the same document.

## Medicine 5 — A6: specific script/font corruption (21 documents)

**Examples:**

| doc_id | Exact evidence / position |
|---|---|
| `47424ea4989c5934` | `ಪೆÇಲೀಸರು` at 79 |
| `442de0ddbdf11639` | `ಪೆÇಲೀಸ್` at 69 |
| `244c2e3dd2f0c566` | `ಬ್ಯಾ0ಕ್` at 243; `ಸಿ0ಡಿಕೇಟ್` at 264 |

**Rule / action: fix only the listed complete words.** These are proposed exact corrections for recurring
legacy-font/character substitutions. Never replace every `Ç`, zero or avagraha globally, delete all Latin
letters, expand abbreviations, or reconstruct missing translated words. Other A6 cases remain manual.

```python
A6_FIXES = {"ಪೆÇಲೀಸ್": "ಪೊಲೀಸ್", "ಪೆÇಲೀಸರು": "ಪೊಲೀಸರು", "ಬ್ಯಾ0ಕ್": "ಬ್ಯಾಂಕ್",
            "ಸಿ0ಡಿಕೇಟ್": "ಸಿಂಡಿಕೇಟ್", "ಅಽಕಾರಿ": "ಅಧಿಕಾರಿ"}
A6_PATTERN = re.compile(rf"(?<!{EDGE})(?:{'|'.join(map(re.escape, sorted(A6_FIXES, key=len, reverse=True)))})(?!{EDGE})")

def medicine_a6(text, url=""):
    if "```" in text or "~~~" in text:
        return text
    return A6_PATTERN.sub(lambda m: A6_FIXES[m.group()], text)
```

**Harm test:** pending; this dictionary does not establish a general font map or cover all 21 documents.
**Side effects:** a lesson deliberately quoting an erroneous spelling can be changed. Inflections outside
the list are left untouched. Valid `CETಗೆ`, Sanskrit avagraha, personal-name spellings and incomplete
fragments such as `Home ತುವಿನಲ್ಲಿ` are not guessed or automatically removed.

## Medicine 6 — F1: confirmed private-data redaction (11 documents)

**Examples (values intentionally omitted):**

| doc_id | Type and original offset |
|---|---|
| `634f9d4743893171` | phone-number-like token at 20403 |
| `c472a3db00395ba6` | phone-number-like token at 3081 |
| `76fdbcb28c49fc27` | phone-number-like token at 4853 |

**Rule / action: fix by redacting reader-confirmed private spans.** Phone/email regexes only propose
candidates; they do not establish private ownership. Supply approved `[start, end)` code-point ranges in
`confirmed_spans`, measured on the unchanged source. The function merges overlaps, checks bounds and
replaces only those spans with ordinary text `[REDACTED]`. It returns no source values or evidence log.
No approved spans means no redaction. Do not pass every detected ten-digit number automatically.

```python
def medicine_f1(text, url="", *, confirmed_spans=()):
    merged = []
    for a, b in sorted(confirmed_spans):
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(text):
            raise ValueError("F1 needs valid original code-point spans")
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    out, cursor = [], 0
    for a, b in merged:
        out.extend((text[cursor:a], "[REDACTED]"))
        cursor = b
    return "".join(out) + text[cursor:]
```

**Harm test:** pending. Gold rows must explicitly carry `confirmed_private_spans` (an empty list if none),
so missing annotations cannot silently masquerade as a tested redaction pipeline. This evaluates span
replacement, not the accuracy of phone/email detection or private-ownership judgments.
**Side effects:** an incorrectly approved span can erase valid text. Offsets from a modified text can redact
the wrong characters, so F1 runs first and original ranges must never be reused after other transformations.
Public contacts and ordinary numeric values remain unless explicitly approved. Evidence stays type and
offset only; hex stays empty. Documents requiring a drop rather than redaction remain a reader decision.

## Recurring labels without a solid automatic medicine

Each of these exceeds five labelled documents. Three recorded examples are retained for traceability;
they do not establish a safe automatic replacement. **Action:** manual fix/drop after review, except D3
mixing itself is preserved. There is no executable repair or measured gold result for these codes.

### D3 — Mixed language: 74 documents

- `12d7d5e672b21506`: `News13 strives to publish and promote positive news` at 1052.
- `adb72bac01d7c42b`: `reporterkarnataka news` at 109.
- `95fcd3a60a26a368`: `Education NIT Recruitment 2021:` at 334.

**Decision:** keep natural mixing. Boilerplate can be removed by C1/C5 structure, not because it is English.
Seventeen D3-labelled documents are clean. A language-based deletion rule would discard valid content.

### D4 — Bad machine translation: 23 documents

- `740400a2326815d0`: `ಎಕ್ಷಾಮ್ನಲ್ಲಿ` at 1826.
- `fef7c1450fb4b473`: `ಭೇಟಿ ಮಾಡಬಹುದು ಒಂದು ಮನುಷ್ಯ ಮೂವತ್ತು ವರ್ಷಗಳ.` in the recorded evidence near 771.
- `da5e3fd306d82f8a`: `ಚಾರ್ಜ್ ಸಂಪೂರ್ಣವಾಗಿ ಉಚಿತನೀವು`.

**Decision:** fluent/source review, then rewrite or drop. English loanwords alone do not prove bad
translation. No keyword-based translation repair is justified; the same phrase can be valid in context.

### G2 — Suspected lost joiners: 21 documents

- `51fa1af6aa0279aa`: `ಒನ್ಪ್ಲಸ್` at 447.
- `e7b8bf9fcc02f67e`: `ಏರ್ಬ್ಯಾಗ್` at 2651.
- `0de20b851b0be1b0`: `ಲವ್ಸ್ಟೋರಿ` at 342.

**Decision:** compare the source or obtain a fluent orthographic correction. The pack has no ZWJ/ZWNJ,
but absence does not prove a joiner belongs in every conjunct. Preserve supplied joiners and their order;
ZWJ before Kannada RA's virama and the legacy virama-before-ZWJ order can look alike but differ as text.
Never strip `\u200b..\u200d` or insert joiners using a blanket loanword rule. No automatic restoration.

### C3 — Truncation: 10 documents

- `5324bc601e15d2a1`: `ಇದರಲ್ಲಿ ಇನ್ನಷ್ಟು ಓದಿ :` at the ending, recorded as cut after a colon.
- `0133d46ad029bd26`: `ಸಿಗಲು […]` at 786 in the recorded evidence.
- `9bbd16758b6866b9`: `ಇದು ಗೊತ್ತಾದ ವಿದ್ಯಾರ್ಥಿಗಳು ತಮ್ಮ ನೆಚ್ಚಿನ ಶಿಕ್ಷಕರ` at 0.

**Decision:** recover the original or make a manual keep/drop decision. A colon, ellipsis or missing final
full stop is insufficient to reconstruct missing text or justify dropping a document automatically.

## Combination and gold harm test

Run F1 first using original offsets. Run C5 before C1 because teaser removal needs the navigation header;
run A6/G1 before C2 so corrected text is considered during deduplication. Each medicine and the pipeline need a separate gold
measurement. These functions fix text only: they never return a drop decision.

```python
RULES = {"C1": medicine_c1, "C5": medicine_c5, "C2": medicine_c2, "G1": medicine_g1,
         "A6": medicine_a6, "F1": medicine_f1}

def repair_all(text, url="", *, confirmed_spans=()):
    text = medicine_f1(text, confirmed_spans=confirmed_spans)
    for function in (medicine_c5, medicine_c1, medicine_a6, medicine_g1, medicine_c2):
        text = function(text, url)
    return text

def harm_report(rows):
    rows = list(rows)
    if not rows or any(not isinstance(r.get("text"), str) for r in rows):
        raise ValueError("Nonempty clean gold with string text is required")
    if any(not source_parts(r.get("url"))[0] for r in rows):
        raise ValueError("URL provenance is required for the site-specific C1 branch")
    if any(not isinstance(r.get("confirmed_private_spans"), list) for r in rows):
        raise ValueError("Explicit confirmed_private_spans lists are required; use [] for none")
    report = {}
    for code, function in {**RULES, "combined": repair_all}.items():
        outputs = [function(r["text"], r["url"], confirmed_spans=r["confirmed_private_spans"])
                   if code in {"F1", "combined"} else function(r["text"], r["url"]) for r in rows]
        changed = sum(output != r["text"] for output, r in zip(outputs, rows))
        report[code] = {"gold_documents": len(rows), "changed_documents": changed,
                        "dropped_documents": 0, "harm_percent": 100 * changed / len(rows),
                        "passes_harm_test": changed * 100 <= len(rows)}
        if code == "F1":
            report[code]["scope"] = "confirmed-span replacement only; detector not evaluated"
    return report
```

The caller must supply genuinely independent two-reader clean gold; this function cannot verify reader
agreement. Count **every changed gold document as harm**, including an empty-text result. Exactly 1% passes;
more than 1% fails. Missing/invalid gold or missing URL provenance raises an error instead of manufacturing
a zero-harm pass. Call `harm_report(gold_rows)` after loading these snippets; record the gold identity and
its SHA-256 with the resulting counts. **Actual results remain PENDING.**

| Rule | Gold documents | Changed | Dropped | Harm | Result |
|---|---|---|---|---|---|
| C1 | Pending | Pending | Pending | Pending | Not run |
| C5 | Pending | Pending | Pending | Pending | Not run |
| C2 | Pending | Pending | Pending | Pending | Not run |
| G1 | Pending | Pending | Pending | Pending | Not run |
| A6 | Pending | Pending | Pending | Pending | Not run |
| F1 | Pending | Pending | Pending | Pending | Not run |
| Combined | Pending | Pending | Pending | Pending | Not run |

