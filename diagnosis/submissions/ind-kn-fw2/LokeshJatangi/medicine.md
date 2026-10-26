# Medicine sheet: ind-kn-fw2 (LokeshJatangi)

## Medicine 1: C1 — Website boilerplate

### Disease and evidence

C1 is website furniture mixed into the article: navigation headings and category links. A line beginning with
English alone does not establish C1. The proposed detector covers these structures:

1. A contiguous block at the **first nonblank line of the document**, where each nonblank line starts with a
   literal hyphen, horizontal whitespace, then an ASCII letter: `- News …`, `- Finance …`, or another English-led
   bullet. The line pattern is `[ \t]*-[ \t]+[A-Za-z].*`.
2. `Just In` followed by `Don't Miss!` (also accepting a curly apostrophe), then at least one such bullet. This
   paired navigation header can identify an embedded block too. Heading comparison ignores case and outer whitespace.
3. Standalone `Trending` and `Title` lines, including `Title⟦LF⟧`, are website labels. Only the standalone word is matched; the following article title is preserved.
4. Lines ending in `N day ago` or `N days ago`, such as `ರಾಜಕೀಯ7 days ago` and `ರಾಜಕೀಯ6 days ago`, are topic/age metadata. No space is required between the topic and number. ASCII and Kannada digits are supported; trailing spaces after `ago` are allowed. A bare `-` between recognized widget lines is included in the same block.

5. Complete publication/update timestamp lines are metadata too. Examples are `Team Udayavani, Feb 11, 2021, 3:27 PM IST` and `Last Modified ಶನಿವಾರ, 5 ಸೆಪ್ಟಂಬರ್ 2020 (10:08 IST)`. English-date formats support optional First Published/Published/Updated/Last Modified markers and bylines, an English month/date/year and a 12- or 24-hour time with timezone. The exact reader example `First Published Jan 20, 2021, 2:58 PM IST` is included in the regression tests. The second supports First Published/Published, Last Modified/Updated or Updated markers, a localized date and a parenthesized time/timezone. The whole line must match; ordinary year/date mentions and narrative sentences are preserved. These examples were supplied by the reader; their document IDs and offsets must be recorded during review.
6. A leading `ಮುಖಪುಟ` homepage label at the first nonblank document line is C1. A standalone label line is removed; when it is an inline breadcrumb, only the label token is matched and removed. Later mentions and longer words such as `ಮುಖಪುಟದ` are preserved. Top English navigation bullets can follow the standalone homepage label.
7. Pipe-terminated city/navigation labels are C1 only when the whole label line ends in `|` followed only by whitespace and a real LF/CRLF. This covers `ಬೆಂಗಳೂರು|`, repeated `ಬೆಂಗಳೂರು| ಬೆಂಗಳೂರು|`, and `ಮುಖಪುಟ | ಕರ್ನಾಟಕ | ಬೆಂಗಳೂರು |` when followed by that newline. Remove the complete matching label line. Preserve inline related links such as `ಇದನ್ನೂ ಓದಿ | ಲೇಖನದ ಶೀರ್ಷಿಕೆ`, `ಬೆಂಗಳೂರು| article text`, and a final bare `ಬೆಂಗಳೂರು|` with no LF. Match Unicode letter/mark-based labels across scripts without a fixed city list; this is structural, not semantic city recognition. Ordinary unpiped city mentions remain content.
8. The exact standalone slogan `ಜೀವ ರಕ್ಷಣೆಗಾಗಿ ಸಂಚಾರ ನಿಯಮ ಪಾಲಿಸಿ`, including a line enclosed in quotation marks, is C1. Remove just that matching line; preserve longer sentences discussing the phrase.

This is a general suffix rule, not a topic-name whitelist. It also covers `ಅಂತರಂಗ5 days ago`,
`ದಿನದ ಸುದ್ದಿ5 days ago`, `ಲೈಫ್ ಸ್ಟೈಲ್4 days ago`, `ಕ್ರೀಡೆ4 days ago`, and ` ಭಾವ ಭೈರಾಗಿ5 days ago`.
Topic names may contain spaces, the number may touch the topic, and a leading space remains in the original
source range. In `Trending\n-\nಅಂತರಂಗ5 days ago`, the topic line starts at original offset 11.

Blank lines may separate headers or entries. The block ends at the first nonblank line that does not match.
A heading pair without any matching bullet is not removed. English sentences and bullets below an ordinary
article heading are preserved. The eight category names in the reported example are News, Finance, Sports,
Automobiles, Lifestyle, Education, Technology and Travel; the top-bullet rule also covers other English names.

**Count snapshot (25 October 2026):** 8 saved review rows carry C1, meeting the disease's more-than-five threshold.
A separate literal search found 11 documents containing the exact `Just In` / `Don't Miss!` header. None of those
11 overlaps the 8 saved C1 reviews. The 11 header matches are candidate evidence for this narrower pattern,
not confirmed C1 labels or a measured count for the full, extended detector. The full detector count and human
confirmation of these candidates remain pending.

Three source-header examples for follow-up (all at original code-point offset 0):

| doc_id | Exact header representation | Review status for this pattern |
|---|---|---|
| `95fcd3a60a26a368` | `Just In\nDon't Miss!` | Candidate; not yet saved as C1 |
| `10c1bbd17380fb15` | `Just In\nDon't Miss!` | Candidate; not yet saved as C1 |
| `352f61da6247acd6` | `Just In\nDon't Miss!` | Candidate; not yet saved as C1 |

Here `\n` represents the source newline. Source offsets count Unicode code points, beginning at 0. For the
reported LF-separated example, the first category bullet begins at offset **20**. With CRLF it begins at 22;
the implementation calculates offsets from the original text and does not hard-code them.

The requested single-line evidence format is:

```text
C1: "Just In Don't Miss!" at offset 0 | C1: "- News ಕರ್ನಾಟಕದಲ್ಲಿ 573 ಕೊರೊನಾ ಸೋಂಕಿತರು ಪತ್ತೆ" at offset 20
```

For readability, whitespace inside the header quote is collapsed; its exact source span is `[0, 19)` and contains
an LF between the two headings. All stored offsets and match ranges still refer to the original source. The
viewer action appends one entry for the header and one for every matching bullet, keeps existing evidence,
adds the C1 checkbox and stores the result as a browser draft. It changes an empty/clean verdict to `fix` and
preserves an existing `fix`/`drop` verdict. Clicking it again does not duplicate the same evidence entries.
It does not submit a review until **Save my label** is used.

For F1/E3-selected documents or detected sensitive patterns, the viewer adds only the type and offset, for
example `C1: navigation category link at offset 20`; it does not quote the source values. F1/E3 evidence must
remain type-and-position only, and its hex field must remain empty.

### Medicine and action

**Action: fix the text** by removing the complete matched navigation block, including the line endings of its
headers and bullets, and the matched widget labels/topic-age lines. Keep every character outside those ranges exactly, including article whitespace, Indic vowel
signs and joiners. The function never drops a document. If the result is empty, it remains an empty text result
for manual review; this proposal does not silently add an empty-document drop rule.

The executable implementation is `teams/08-monitoring/diagnosis-viewer/c1_navigation.py`. Its exact code follows;
a test checks that this copy and the executable stay identical.

```python
"""C1 website-boilerplate medicine. Import for inspection; CLI reports gold harm only."""
import argparse
import json
import re
import unicodedata

LINE_ENDINGS = "\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029"
ENGLISH_BULLET = re.compile(r"[ \t]*-[ \t]+[A-Za-z].*")
AGE_SUFFIX = re.compile(r"(?<!\d)\d+[ \t]+days?[ \t]+ago[ \t]*$", re.IGNORECASE)
HOME_PREFIX = re.compile(r"\s*(?P<label>ಮುಖಪುಟ)(?=$|[\s/|»›:>])")
TRAFFIC_SLOGAN = "ಜೀವ ರಕ್ಷಣೆಗಾಗಿ ಸಂಚಾರ ನಿಯಮ ಪಾಲಿಸಿ"
MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DAY = r"(?:0?[1-9]|[12][0-9]|3[01])"
CLOCK_24 = r"(?:[01]?[0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?"
CLOCK_12 = r"(?:0?[1-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?[ \t]+(?:AM|PM)"
CLOCK = rf"(?:{CLOCK_12}|{CLOCK_24})"
ZONE = r"(?:[A-Z]{2,5}|[+-](?:[01][0-9]|2[0-3]):?[0-5][0-9])"
PUBLICATION_MARKER = r"(?:First[ \t]+Published|Last[ \t]+(?:Modified|Updated)|Published|Updated)"
BYLINE_TIMESTAMP = re.compile(
    rf"[ \t]*(?:{PUBLICATION_MARKER}[ \t]*:?[ \t]+)?(?:[^,\r\n]{{1,120}},[ \t]*)?"
    rf"{MONTH}\.?[ \t]+{DAY},[ \t]*[0-9]{{4}},[ \t]*{CLOCK}[ \t]+{ZONE}[ \t]*",
    re.IGNORECASE,
)
UPDATE_TIMESTAMP = re.compile(
    rf"[ \t]*{PUBLICATION_MARKER}[ \t]*:?[ \t]+"
    rf"(?:[^,\r\n()]+,[ \t]*)?\d{{1,2}}[ \t]+[^\d\r\n()]+[ \t]+\d{{4}}[ \t]*"
    rf"\([ \t]*{CLOCK}[ \t]+{ZONE}[ \t]*\)[ \t]*",
    re.IGNORECASE,
)


def pipe_navigation_matches(line):
    """Recognize complete navigation-label lines ending in a pipe and real LF.

    Only whitespace may follow the last pipe before LF/CRLF. Inline related
    links, unpiped trailing text, and EOF without LF are not this C1 pattern.
    This checks syntax, not a city dictionary; Indic marks remain in labels.
    """
    if not line.endswith("\n"):
        return []
    body = line.rstrip(LINE_ENDINGS)
    if not body.rstrip().endswith("|"):
        return []
    matches, cursor = [], 0
    while True:
        pipe = body.find("|", cursor)
        if pipe < 0:
            break
        segment = body[cursor:pipe]
        label = segment.strip()
        if (not label or unicodedata.category(label[0])[0] not in "LN"
                or not any(unicodedata.category(ch).startswith("L") for ch in label)
                or any(not (unicodedata.category(ch)[0] in "LMN" or ch.isspace()
                            or ch in "-'’.,()/\u200c\u200d") for ch in label)):
            return []
        start = cursor + len(segment) - len(segment.lstrip())
        matches.append({"start": start, "end": pipe + 1, "detail": "pipe-terminated city/navigation label"})
        cursor = pipe + 1
    return matches if not body[cursor:].strip() else []


def find_c1_blocks(text):
    """Match navigation, widget labels, relative ages and publication timestamps.

    All offsets are zero-based original Unicode code-point offsets. Blank lines
    may separate entries. A nonblank, nonmatching line ends the block. Unheaded
    English-led bullets match only at the first nonblank line of the document.
    Trending, Title and lines ending in N day(s) ago also match elsewhere. A bare '-'
    joins widget entries only when another recognized widget line follows it.
    Publication timestamps match complete byline/date/time/timezone lines, or
    marked update lines with a localized date and parenthesized time/timezone.
    A leading ಮುಖಪುಟ navigation label matches only at the first nonblank line.
    Pipe-label lines require a final pipe followed only by whitespace and LF/CRLF.
    Inline related-link text is preserved. The traffic-safety slogan is line-level.
    """
    lines = text.splitlines(keepends=True)
    starts, offset = [], 0
    for line in lines:
        starts.append(offset)
        offset += len(line)
    bodies = [line.rstrip(LINE_ENDINGS) for line in lines]
    first = next((j for j, body in enumerate(bodies) if body.strip()), len(lines))
    blocks, i = [], 0
    navigation_first = first
    pipe_rows, whole_pipe_rows = set(), set()
    for j, body in enumerate(bodies):
        matches = pipe_navigation_matches(lines[j])
        if matches:
            pipe_rows.add(j)
            whole_pipe_rows.add(j)
            blocks.append({"start": starts[j], "end": starts[j] + len(lines[j]), "matches": [
                {**match, "start": starts[j] + match["start"], "end": starts[j] + match["end"]}
                for match in matches
            ]})
            if j == first:
                navigation_first = next((k for k in range(j + 1, len(lines)) if bodies[k].strip()), len(lines))
    home = HOME_PREFIX.match(bodies[first]) if first < len(lines) and first not in pipe_rows else None
    if home:
        whole_line = not bodies[first][home.end("label"):].strip()
        end = starts[first] + (len(lines[first]) if whole_line else home.end("label"))
        blocks.append({"start": starts[first], "end": end, "matches": [{
            "start": starts[first] + home.start("label"), "end": starts[first] + home.end("label"),
            "detail": "homepage navigation label",
        }]})
        if whole_line:
            navigation_first = next((j for j in range(first + 1, len(lines)) if bodies[j].strip()), len(lines))
    while navigation_first in whole_pipe_rows:
        navigation_first = next((j for j in range(navigation_first + 1, len(lines)) if bodies[j].strip()), len(lines))
    while i < len(lines):
        if i in pipe_rows:
            i += 1
            continue
        second = None
        if bodies[i].strip().casefold() == "just in":
            second = i + 1
            while second < len(lines) and not bodies[second].strip():
                second += 1
            if second == len(lines) or bodies[second].strip().casefold() not in {"don't miss!", "don’t miss!"}:
                i += 1
                continue
            cursor = second + 1
        elif i == navigation_first and ENGLISH_BULLET.fullmatch(bodies[i]):
            cursor = i
        else:
            i += 1
            continue
        categories = []
        while cursor < len(lines):
            if not bodies[cursor].strip():
                cursor += 1
                continue
            if not ENGLISH_BULLET.fullmatch(bodies[cursor]):
                break
            categories.append(cursor)
            cursor += 1
        if not categories:
            i += 1
            continue
        matches = [] if second is None else [
            {"start": starts[i], "end": starts[second] + len(bodies[second]), "detail": "navigation header"}
        ]
        matches.extend({"start": starts[j], "end": starts[j] + len(bodies[j]),
                        "detail": "navigation category link"} for j in categories)
        last = categories[-1]
        blocks.append({"start": starts[i], "end": starts[last] + len(lines[last]), "matches": matches})
        i = cursor
    def widget_kind(body):
        if body.strip().strip("\"'‘’“”") == TRAFFIC_SLOGAN:
            return "traffic-safety slogan"
        if body.strip().casefold() == "trending":
            return "trending widget heading"
        if body.strip().casefold() == "title":
            return "website title label"
        if AGE_SUFFIX.search(body):
            return "topic or relative-age metadata"
        if BYLINE_TIMESTAMP.fullmatch(body) or UPDATE_TIMESTAMP.fullmatch(body):
            return "publication or update timestamp"
        return None

    navigation_blocks = tuple(blocks)
    i = 0
    while i < len(lines):
        if not widget_kind(bodies[i]) or any(b["start"] <= starts[i] < b["end"] for b in navigation_blocks):
            i += 1
            continue
        start, last, matches = i, i, []
        while i < len(lines):
            body = bodies[i]
            kind = widget_kind(body)
            if not body.strip():
                i += 1
                continue
            if body.strip() == "-":
                next_line = i + 1
                while next_line < len(lines) and not bodies[next_line].strip():
                    next_line += 1
                if next_line < len(lines) and widget_kind(bodies[next_line]):
                    kind = "widget separator"
            if not kind or any(b["start"] <= starts[i] < b["end"] for b in navigation_blocks):
                break
            matches.append({"start": starts[i], "end": starts[i] + len(body), "detail": kind})
            last = i
            i += 1
        blocks.append({"start": starts[start], "end": starts[last] + len(lines[last]), "matches": matches})
    return sorted(blocks, key=lambda block: block["start"])


def find_c1_matches(text):
    return [match for block in find_c1_blocks(text) for match in block["matches"]]


def c1_evidence(text, matches, redact=False):
    """Single-line evidence; header whitespace is collapsed for readability.

    Set redact=True for F1/E3 documents or overlapping sensitive matches.
    Exact source ranges remain in matches; offsets always refer to the source.
    """
    entries = []
    for match in matches:
        value = match["detail"] if redact else json.dumps(
            " ".join(text[match["start"]:match["end"]].split()), ensure_ascii=False
        )
        entries.append(f'C1: {value} at offset {match["start"]}')
    return " | ".join(entries)


def fix_c1_navigation(text):
    """Remove complete matched blocks; preserve all text outside them exactly."""
    pieces, previous = [], 0
    for block in find_c1_blocks(text):
        pieces.append(text[previous:block["start"]])
        previous = block["end"]
    pieces.append(text[previous:])
    return "".join(pieces)


def harm_test(gold_rows):
    """Count every changed gold document as harm, even if the edit looks useful."""
    total = changed = 0
    for row in gold_rows:
        text = row["text"]
        if not isinstance(text, str):
            raise ValueError("Every gold document must have a string text field")
        total += 1
        changed += fix_c1_navigation(text) != text
    if not total:
        raise ValueError("The gold set must not be empty")
    # This medicine fixes text and never drops a document, including empty output.
    return {"gold_documents": total, "changed_documents": changed, "dropped_documents": 0,
            "changed_or_dropped_documents": changed, "harm_percent": 100 * changed / total,
            "passes_harm_test": changed * 100 <= total}


def main():
    parser = argparse.ArgumentParser(description="Read a gold Parquet and report C1 harm counts; writes no dataset.")
    parser.add_argument("--gold", required=True, help="Kannada gold set marked clean by two readers")
    args = parser.parse_args()
    import pyarrow.parquet as pq
    print(json.dumps(harm_test(pq.read_table(args.gold, columns=["text"]).to_pylist()), indent=2))


if __name__ == "__main__":
    main()
```

### Functional tests

Tests are defined in `teams/08-monitoring/diagnosis-viewer/test_c1_navigation.py`; viewer action and local-draft
behavior are covered by `test_drafts.js`, invoked from the Python frontend suite. **Result: pending user execution.**

| Scenario | Required result |
|---|---|
| Reported heading and eight category lines | Nine evidence ranges: one header plus eight bullets; first offsets 0 and 20. |
| A document starting with `- ` plus an English letter | Flag/remove the contiguous leading block; stop at the first body line. |
| Ordinary English prose, Kannada bullets, `-News` without a space, or an en dash | Preserve the text. |
| An English-led list below an ordinary article heading | Preserve the text. |
| A heading pair without an English-led bullet | Preserve the text. |
| Standalone Trending and Title labels | Remove just those label lines, preserving the article title/body that follows. |
| Reported Team Udayavani timestamp and Kannada Last Modified line | Mark each full metadata line as C1, preserve exact original offsets and the following article title/body. |
| Exact First Published Jan 20, 2021, 2:58 PM IST example | One C1 timestamp range, offset 0 when it starts the document; keep the following article unchanged. |
| Leading ಮುಖಪುಟ label | Match only at the first nonblank line, preserving the following article or inline breadcrumb remainder; preserve later mentions and longer words. |
| Pipe-terminated city labels, repetitions and breadcrumbs | Require a final pipe, optional trailing whitespace and real LF/CRLF; preserve inline article/related-link text, EOF without LF and ordinary city mentions. |
| Exact standalone traffic-safety slogan | Remove its standalone/quoted line; preserve longer prose discussing the phrase. |
| Timestamp variants and negative controls | Accept supported full byline/update formats; preserve bare dates/years, invalid clock times, and narrative sentences. |
| Kannada topic attached to a numeric age ending in day(s) ago | Flag/remove the line; preserve lines with additional words after ago. |
| Reported ಅಂತರಂಗ / ದಿನದ ಸುದ್ದಿ / ಲೈಫ್ ಸ್ಟೈಲ್ / ಕ್ರೀಡೆ / ಭಾವ ಭೈರಾಗಿ widget | Seven evidence ranges: Trending, the separator and five topic lines; handle leading/trailing spaces and keep the following article unchanged. |
| Bare hyphen between widget entries | Include it; preserve unrelated hyphen lines. |
| A navigation bullet also ending in an age marker | Count/remove its range once. |
| CRLF and a prefix containing an emoji | Calculate original code-point offsets; preserve all unrelated characters and line endings. |
| Reapplying the repair | Produce no additional change. |
| Multiple matched blocks | Remove each block and preserve the intervening article text. |
| Sensitive evidence mode | Emit descriptions and offsets without source values. |
| Viewer evidence action | Preserve existing evidence/codes, append C1 once, save locally, and send no review automatically. |
| Synthetic gold boundary | 1/100 or 2/200 changed passes; 2/100 or 3/200 changed fails. |
| Empty or invalid gold input | Raise an error; do not report a passing result. |

From the repository root, run the complete synthetic suite and retain the terminal output:

```bash
python3 -m unittest discover -s teams/08-monitoring/diagnosis-viewer -p 'test_*.py' -v
```

### Gold-set harm test

**Status: NOT RUN. No Kannada gold-set file was found in this repository. This medicine is not yet approved for
scale use.** The 500-document diagnosis pack is not a clean gold set. Synthetic threshold tests check the counting
logic; they are not a substitute for the language gold set.

Use the Kannada gold Parquet supplied by the gold-set owners, whose documents two readers marked clean. Replace
the path below with that real file, run the command, and record the complete JSON output:

```bash
python3 teams/08-monitoring/diagnosis-viewer/c1_navigation.py --gold /absolute/path/to/kannada_gold.parquet
```

The command reads the gold set and reports counts; it writes no repaired dataset. Count every document whose text
changes as harm, even if a removed block looks like boilerplate. Dropped documents are 0 for this fix-only
medicine. The pass rule is `100 * changed_or_dropped_documents <= gold_documents`, so **exactly 1% passes and more
than 1% fails**. For a 200-document gold set, at most 2 documents may change; 3 changes fail.

| Required measurement | Current result |
|---|---|
| Gold-set identity/version | Pending |
| Total gold documents | Pending |
| Documents changed | Pending |
| Documents dropped | Pending execution; implementation has no drop action |
| Documents changed or dropped, counted once | Pending |
| Harm percentage | Pending |
| Pass/fail at ≤1% | Undetermined |

Keep the gold file identity and actual totals with the final report. Re-run the harm test after any rule change.
Do not run cleaning scripts over the full training data as part of this diagnosis task.

### Side effects and limits

- A legitimate article may begin with an English-led bullet list. The top-of-document heuristic can remove it;
  fluent review and the gold harm test are required before adopting this medicine.
- An article quoting the exact `Just In` / `Don't Miss!` menu can match even when it is meaningful content.
- A genuine heading named `Title` or `Trending`, or a narrative line ending in `7 days ago`, can match the widget rules. These are additional false-positive cases that must count as gold harm.
- An article genuinely beginning with the standalone word `ಮುಖಪುಟ` can be mistaken for navigation. Removing only an inline homepage token may leave other breadcrumb text for manual review.
- Pipe-delimited tables, code expressions or meaningful labels that end in a pipe and real LF/CRLF can match the city/navigation syntax. Inline related links with content after the last pipe are excluded by this rule. Labels are not validated against a city dictionary; count every resulting change to clean gold text as harm.
- A genuine headline or quotation identical to `ಜೀವ ರಕ್ಷಣೆಗಾಗಿ ಸಂಚಾರ ನಿಯಮ ಪಾಲಿಸಿ` can match the slogan rule. The standalone-line constraint preserves longer prose but does not establish whether an isolated phrase is website furniture.
- A legitimate standalone date/time reference formatted like a full publication byline can match. Calendar validity and timezone semantics are not established by this structural detector. Timestamp additions must be included in the gold harm run; no passing result has been measured.
- Mixed Kannada/English is not itself C1. Ordinary English-led sentences remain valid; D3 can be labeled separately
  and can accompany `clean` in this review workflow.
- Localised headers, other bullet symbols, missing spaces after the hyphen, wrapped link titles, and menus outside
  the supported structures may be missed. Unmatched menus, cookie notices and footers still need manual reading.
- The function identifies structure, not intent or private ownership. Sensitive values must not be copied into
  evidence or this public medicine sheet.
- An all-navigation document becomes empty text. Decide any later document drop separately and harm-test that
  combined action; the zero-drop result here would no longer describe the combined medicine.


### Site-specific C1 addendum: Vartha Bharati and News18

**Disease:** C1 website boilerplate. In the 500-document Kannada diagnosis pack, the specified Vartha Bharati
footer occurs in all 8 documents from that site; the requested News18 metadata occurs in 2 of 3 News18
news documents. These are 10 distinct documents changed by this site-specific medicine. The C1 frequency
exceeds five; these measured matches are separate from the earlier saved-label snapshot.

**Rule — Vartha Bharati:** require an HTTP(S) URL whose parsed hostname is exactly `varthabharati.in` or a
subdomain. Match the exact two-line appeal below at a line boundary and document end, allowing LF/CRLF
between its lines and optional trailing spaces/tabs/newlines. Remove only the appeal itself; preserve the
newline before it and any trailing whitespace. Do not match a phrase inside a sentence, a partial appeal,
a following non-whitespace article paragraph, or the same text on another host.

```text
‘ವಾರ್ತಾ ಭಾರತಿ’ ನಿಮಗೆ ಆಪ್ತವೇ ? ಇದರ ಸುದ್ದಿಗಳು ಮತ್ತು ವಿಚಾರಗಳು ಎಲ್ಲರಿಗೆ ಉಚಿತವಾಗಿ ತಲುಪುತ್ತಿರಬೇಕೇ?
ಬೆಂಬಲಿಸಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ
```

The reported example URL is `https://m.varthabharati.in/article/2021_04_07/285999`. It is index 146,
**row 147**, doc_id `c640c89d2ca2413a`. Its 120-code-point footer is `[1588, 1708)`: the reader's final
position 1707 is inclusive. Offsets below are zero-based original Unicode code points, with end excluded.

**Rule — News18:** require an HTTP(S) URL with exact hostname `kannada.news18.com` and path `/news` or
beginning `/news/`. Remove a complete `news18-kannada Updated:` line (allow horizontal edge whitespace),
a supported English month/day/year/time/timezone line immediately following that label, and complete
standalone `India` lines. Remove the line endings belonging to these lines. Preserve the following title
and article; do not remove inline `India` mentions or a timestamp merely because it appears without the
publisher label. The broader existing viewer can still flag standalone timestamps separately; duplicate
ranges from its generic and site-specific C1 checks are counted once.

```text
news18-kannada Updated:
February 14, 2021, 6:22 PM IST
India
```

**Action:** fix text; never drop a document. Apply only the site rules in `c1_site_boilerplate.py` when
producing this cleaned copy. The broader navigation heuristics in `c1_navigation.py` are not applied to it.
Every character outside the specified removals stays unchanged. Keep all 500 rows in their original order,
with the same doc_ids, schema/metadata and non-text columns. No review JSON or label CSV is rewritten.

**Source examples and observed ranges (26 October 2026):**

| Site | doc_id | Index / row | Original evidence ranges | Characters removed |
|---|---|---|---|---|
| varthabharati | `bfe4d0c9f43dc03b` | 13 / 14 | [1947, 2067) | 120 |
| varthabharati | `f8ebdf3dd24db84a` | 14 / 15 | [4541, 4661) | 120 |
| varthabharati | `450d74fdc31034db` | 55 / 56 | [2602, 2722) | 120 |
| varthabharati | `c640c89d2ca2413a` | 146 / 147 | [1588, 1708) | 120 |
| news18-kannada | `316edbe5fbc2fa0c` | 160 / 161 | [0, 23), [24, 54), [55, 60) | 61 |
| varthabharati | `2b009789877f7fa1` | 225 / 226 | [886, 1006) | 120 |
| news18-kannada | `8c9ce90a54c1de92` | 297 / 298 | [0, 23), [24, 51) | 52 |
| varthabharati | `0f52e8c63e977510` | 413 / 414 | [8467, 8587) | 120 |
| varthabharati | `605d66bd451a0aee` | 442 / 443 | [7025, 7145) | 120 |
| varthabharati | `949f9bf8f6ae18c9` | 463 / 464 | [861, 981) | 120 |

The Vartha Bharati spans all contain the exact appeal quoted above. News18 doc_id `316edbe5fbc2fa0c`
has publisher `[0,23)`, timestamp `[24,54)` and India `[55,60)`; with their newlines, 61 characters are
removed. Doc_id `8c9ce90a54c1de92` has publisher `[0,23)` and timestamp `[24,51)`, removing 52 characters
including newlines. The third News18 document, `bf96c0d9ae768e5d`, has no requested marker and is unchanged.
The eight footer removals remove 960 characters; the two News18 removals remove 113, totaling **1,073**.

The generated review artifacts are `ind-kn-fw2.c1-sites.parquet` and `ind-kn-fw2.c1-sites.changes.json`.
The manifest contains IDs, offsets and counts, without article excerpts. The input pack remains intact.
Run the viewer on the original pack to inspect original offsets/C1 evidence. The cleaned copy has its own
path and shifted text offsets; its browser draft namespace and default reviews path are separate.

**Executable code:** `teams/08-monitoring/diagnosis-viewer/c1_site_boilerplate.py` (exact copy below).

```python
"""Site-specific C1 medicines for Vartha Bharati and News18; new Parquet copy only."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from c1_navigation import MONTH, DAY, CLOCK, ZONE


FOOTER_LINES = (
    "‘ವಾರ್ತಾ ಭಾರತಿ’ ನಿಮಗೆ ಆಪ್ತವೇ ? ಇದರ ಸುದ್ದಿಗಳು ಮತ್ತು ವಿಚಾರಗಳು ಎಲ್ಲರಿಗೆ ಉಚಿತವಾಗಿ ತಲುಪುತ್ತಿರಬೇಕೇ?",
    "ಬೆಂಬಲಿಸಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ",
)
FOOTER = "\n".join(FOOTER_LINES)
FOOTER_PATTERN = re.compile(
    r"(?m)^" + re.escape(FOOTER_LINES[0]) + r"\r?\n"
    + re.escape(FOOTER_LINES[1]) + r"(?=[ \t\r\n]*\Z)"
)
NEWS18_HEADER = re.compile(r"[ \t]*news18-kannada[ \t]+Updated:[ \t]*")
NEWS18_TIMESTAMP = re.compile(
    rf"[ \t]*{MONTH}\.?[ \t]+{DAY},[ \t]*[0-9]{{4}},[ \t]*{CLOCK}[ \t]+{ZONE}[ \t]*",
    re.IGNORECASE,
)


def is_varthabharati_url(url):
    try:
        parsed = urlsplit(url or "")
        host = (parsed.hostname or "").lower()
        return parsed.scheme in {"http", "https"} and (
            host == "varthabharati.in" or host.endswith(".varthabharati.in")
        )
    except (TypeError, ValueError, AttributeError):
        return False


def find_varthabharati_footer(text, url=None):
    """Exact two-line appeal at document end; original code-point offsets.

    Accept LF/CRLF between the two lines and optional trailing whitespace.
    Preserve that trailing whitespace and the newline before the appeal.
    A URL mention inside article text or a look-alike hostname is insufficient.
    """
    if not is_varthabharati_url(url):
        return []
    return [{"start": m.start(), "end": m.end(),
             "detail": "Vartha Bharati donation/support footer"}
            for m in FOOTER_PATTERN.finditer(text)]


def fix_varthabharati_footer(text, url=None):
    pieces, previous = [], 0
    for match in find_varthabharati_footer(text, url):
        pieces.append(text[previous:match["start"]])
        previous = match["end"]
    pieces.append(text[previous:])
    return "".join(pieces)


def is_news18_news_url(url):
    try:
        parsed = urlsplit(url or "")
        return (parsed.scheme in {"http", "https"} and parsed.hostname == "kannada.news18.com"
                and (parsed.path == "/news" or parsed.path.startswith("/news/")))
    except (TypeError, ValueError, AttributeError):
        return False


def news18_blocks(text, url=None):
    """Complete publisher/category lines, with timestamp only after publisher.

    Original source offsets are code points. Never remove an inline India
    mention or consume a following headline that is not a supported timestamp.
    """
    if not is_news18_news_url(url):
        return []
    lines = text.splitlines(keepends=True)
    starts, offset = [], 0
    for line in lines:
        starts.append(offset)
        offset += len(line)
    blocks, i = [], 0
    while i < len(lines):
        body = lines[i].rstrip("\r\n")
        header = NEWS18_HEADER.fullmatch(body)
        if not header and body.strip(" \t") != "India":
            i += 1
            continue
        matches = [{"start": starts[i], "end": starts[i] + len(body),
                    "detail": "News18 publisher/update label" if header else "News18 standalone India category"}]
        first, last = i, i
        if header and i + 1 < len(lines):
            timestamp = lines[i + 1].rstrip("\r\n")
            if NEWS18_TIMESTAMP.fullmatch(timestamp):
                last = i + 1
                matches.append({"start": starts[last], "end": starts[last] + len(timestamp),
                                "detail": "News18 timestamp following update label"})
        blocks.append({"start": starts[first], "end": starts[last] + len(lines[last]),
                       "matches": matches})
        i = last + 1
    return blocks


def find_news18_boilerplate(text, url=None):
    return [match for block in news18_blocks(text, url) for match in block["matches"]]


def fix_news18_boilerplate(text, url=None):
    pieces, previous = [], 0
    for block in news18_blocks(text, url):
        pieces.append(text[previous:block["start"]])
        previous = block["end"]
    pieces.append(text[previous:])
    return "".join(pieces)


def site_name(url):
    if is_varthabharati_url(url):
        return "varthabharati"
    if is_news18_news_url(url):
        return "news18-kannada"
    return None


def find_site_boilerplate(text, url=None):
    return find_varthabharati_footer(text, url) + find_news18_boilerplate(text, url)


def fix_site_boilerplate(text, url=None):
    if is_varthabharati_url(url):
        return fix_varthabharati_footer(text, url)
    return fix_news18_boilerplate(text, url)


def harm_test(gold_rows):
    total = changed = 0
    for row in gold_rows:
        if not isinstance(row.get("text"), str):
            raise ValueError("Gold rows require non-null string text")
        # Missing URLs must not produce an artificial zero-harm pass.
        if not isinstance(row.get("url"), str) or not row["url"].strip():
            raise ValueError("Gold rows require URL provenance for this site-specific medicine")
        total += 1
        changed += fix_site_boilerplate(row["text"], row["url"]) != row["text"]
    if not total:
        raise ValueError("Gold set must not be empty")
    return {"gold_documents": total, "changed_documents": changed,
            "dropped_documents": 0, "changed_or_dropped_documents": changed,
            "harm_percent": 100 * changed / total,
            "passes_harm_test": changed * 100 <= total}


def clean_table(table):
    """Keep row order, IDs, schema/metadata and every non-text column intact."""
    import pyarrow as pa

    for name in ("doc_id", "url", "text"):
        if name not in table.column_names:
            raise ValueError(f"Pack requires {name} column")
    texts, records, site_documents = [], [], 0
    site_counts, changed_counts = {}, {}
    for i, row in enumerate(table.select(["doc_id", "url", "text"]).to_pylist()):
        text, url = row["text"], row["url"]
        if not isinstance(text, str):
            raise ValueError(f"Row {i + 1}: text must be a non-null string")
        site = site_name(url)
        if site:
            site_documents += 1
            site_counts[site] = site_counts.get(site, 0) + 1
        matches = find_site_boilerplate(text, url)
        fixed = fix_site_boilerplate(text, url)
        texts.append(fixed)
        if matches:
            changed_counts[site] = changed_counts.get(site, 0) + 1
            records.append({"index": i, "row": i + 1, "doc_id": row["doc_id"],
                            "disease": "C1", "site": site, "original_characters": len(text),
                            "cleaned_characters": len(fixed),
                            "removed_characters": len(text) - len(fixed), "matches": matches})
    index = table.schema.get_field_index("text")
    cleaned = table.set_column(index, table.schema.field(index),
                               pa.array(texts, type=table.schema.field(index).type))
    report = {"medicine": "C1 site boilerplate (Vartha Bharati / News18)", "documents": table.num_rows,
              "site_documents": site_documents, "changed_documents": len(records),
              "dropped_documents": 0,
              "site_documents_by_site": site_counts, "changed_documents_by_site": changed_counts,
              "removed_characters": sum(r["removed_characters"] for r in records),
              "gold_harm_test": "NOT RUN", "changes": records}
    return cleaned, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pack", type=Path)
    mode.add_argument("--gold", type=Path, help="report gold harm; URLs required")
    parser.add_argument("--output", type=Path, help="new cleaned Parquet; input is preserved")
    parser.add_argument("--report", type=Path, help="new JSON manifest, offsets/counts only")
    args = parser.parse_args()
    if args.gold and (args.output or args.report):
        parser.error("--gold reports harm only; use --pack for output/report")
    if args.report and not args.output:
        parser.error("--report requires --output")
    import pyarrow.parquet as pq

    if args.gold:
        print(json.dumps(harm_test(pq.read_table(args.gold).to_pylist()), indent=2))
        return
    paths = [path for path in (args.output, args.report) if path is not None]
    if len({path.resolve() for path in paths}) != len(paths):
        parser.error("Output and report must be different paths")
    for path in paths:
        if path.resolve() == args.pack.resolve() or path.exists():
            parser.error(f"Refusing to replace an existing file: {path}")
    cleaned, report = clean_table(pq.read_table(args.pack))
    report["input"] = str(args.pack)
    report["output"] = str(args.output) if args.output else None
    if args.output:
        with args.output.open("xb") as stream:
            pq.write_table(cleaned, stream)
    if args.report:
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

**Commands:** run from the repository root. Existing output paths are refused; choose fresh names for a
repeat run. Omitting `--output` reports matches/counts without writing a pack.

```bash
python3 teams/08-monitoring/diagnosis-viewer/c1_site_boilerplate.py --pack ind-kn-fw2.parquet
python3 teams/08-monitoring/diagnosis-viewer/c1_site_boilerplate.py --pack ind-kn-fw2.parquet --output ind-kn-fw2.c1-sites.parquet --report ind-kn-fw2.c1-sites.changes.json
python3 -m unittest discover -s teams/08-monitoring/diagnosis-viewer -p 'test_*.py' -v
python3 teams/08-monitoring/diagnosis-viewer/c1_site_boilerplate.py --gold /absolute/path/to/kannada_gold_with_urls.parquet
```

**Tests added; execution pending:**

| Check | Acceptance evidence |
|---|---|
| Exact donation footer / offsets | 120 source code points; correct offsets even after an emoji. |
| URL and suffix guards | Other hosts, look-alike domains, partial appeals, prose and nonterminal copies preserved. |
| LF/CRLF and surrounding whitespace | Only matched footer characters removed; other whitespace exact. |
| News18 publisher/date/India | Complete lines removed; following article retained; inline India and unsupported dates preserved. |
| News18 timestamp overlap | Generic and site-specific C1 produce one candidate/evidence entry per identical range. |
| Table and repeat application | Row order, IDs, schema/metadata and other columns preserved; second pass makes no changes. |
| Viewer endpoint/evidence action | URL guards reach `/inspect`; both sites append C1 evidence to a local draft without submitting labels. |
| Output paths | Source pack and existing output files cannot be overwritten by the CLI. |
| Harm boundary / provenance | 1/100 changed passes, 2/100 fails; empty gold or missing URL provenance raises an error. |

**Gold harm test: NOT RUN.** A cleaned diagnosis copy is not a gold set. Require the actual Kannada clean
gold set with URL provenance; missing URLs must not yield a misleading zero-harm pass. Report its identity,
total document count, changed count, zero drops and harm percentage. Exactly 1% or less changes/drops passes;
more than 1% fails. The CLI's `--gold` evaluates the combined two site rules, counting each changed document
once. It does not claim a passing result for these rules or for their union with the earlier general C1 medicine.
If both medicines are later combined, evaluate that complete action against gold again.

**Side effects and limits:** an article genuinely reproducing the exact terminal appeal on Vartha Bharati
can be removed accidentally. A meaningful standalone `India` heading on a News18 news page also matches.
Any such change to clean gold counts as harm. A changed appeal, alternate quotation marks, wrapped lines,
URL aliases or different host/path may be missed. The News18 rule checks timestamp structure, not calendar
validity. A metadata-only document may become empty but remains a row; no automatic drop rule is added.
