# Medicine sheet: ind-kn-fw2 (LokeshJatangi)

I labelled **500 documents**, all `full`: **239 clean, 231 fix and 30 drop**.
Disease counts below are document counts; a document can have more than one label.
I propose **three reusable coded medicines** for unattended use: C5, C1 and C2.
A6 and G1 can be identified with generic detectors, but no reliable generic repair is proposed.
They remain under rejected generic repair proposals.
Their rules use text structure and metadata syntax, without document IDs, stored offsets,
word-replacement tables or publisher-specific exceptions. The examples below are evidence,
not lookup keys. F1 is listed last as a rejected proposal.

For the harm test, I used the **45-document Kannada gold set**
[ind-kn-fw2_gold.csv](https://github.com/theschoolofai/era-v5-lab/blob/fdb5eae12bafb32b0bcfa45f2ac0e6e059f22baf/teams/02-data-b/gold/ind-kn-fw2_gold.csv),
and the [Indic harm-test reference](https://github.com/theschoolofai/era-v5-lab/blob/692efe961a8073f414346a6dcd789c19647a6c93/teams/02-data-b/tools/harm_test_indic.py).

The unchanged C5 and C2 rules each changed **0/45** and dropped **0/45** gold documents
in the recorded tests.
C1 has been revised to remove publisher-specific rules. Its previous result does not validate
the revised snippet; the revised C1 and three-rule combination need a new run.
Clean-gold harm results do not measure repair coverage on damaged documents.

The reference allows one changed/dropped document on this small gold set; the template's
**at most 1%** limit allows zero out of 45.

The medicines return repaired text without dropping documents, normalizing Unicode or converting
Kannada digits. Structural deletions preserve joiners and compatibility characters.
The unattended pipeline contains no privacy redaction or automatic document-drop rule.

## Combined medicines

Load all Python snippets in document order to use the combined function. The text-only reference
uses the same three-rule order. No rule needs URL provenance or approved spans.
A6, G1 and F1 are excluded from automatic repair.

```python
def _rules():
    return {"C5": medicine_c5, "C1": medicine_c1, "C2": medicine_c2}

def repair_all(text, url=""):
    for function in (medicine_c5, medicine_c1, medicine_c2):
        text = function(text, url)
    return text
```

## Medicine 1

1. **Disease:** C5 — keyword/link lists; **47 labelled documents**. Three recorded examples:

| doc_id | Exact evidence excerpt / position |
|---|---|
| `d78b35287b746574` | `- News ಸರ್ಕಾರದಿಂದ 84 ಸಾವಿರ ರೆಮಿಡಿಸ್ವಿರ್ ಖರೀದಿ: ಸುಧಾಕರ್` at 12 |
| `4f6fb355e6e5e1bd` | `- News ನಾಲ್ಕು ರಾಜ್ಯಗಳ ಮುಖ್ಯಮಂತ್ರಿಗಳ ಜತೆ ಪ್ರಧಾನಿ ಮೋದಿ ಮಾತುಕತೆ` at 12 |
| `ad31bf1d2b690c09` | `#BJP4Belagavi #BJP4Maski #BJP4Basavakalyana` at 1451 |

2. **Medicine:** Remove at least two consecutive English-led teaser bullets immediately under
`Don't Miss!`, optionally preceded by `Just In`. C1 removes the remaining header. Remove a whole line only
when it consists entirely of two or more hashtag tokens. Accept spaces after `#` and adjacent hashtags.
Preserve inline tags in article sentences, isolated hashtags, ordinary Markdown headings and unheaded lists.

```python
import re
import unicodedata

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    out = list(text)
    for a, b in spans:
        if not protected(text[a:b]):
            out[a:b] = [""] * (b - a)  # Keep source indices stable, even for overlaps.
    return "".join(out)

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

3. **Action:** Fix text by removing only matched teaser links and hashtag-only lines. No automatic document drop.

4. **Harm test:** pinned **45-document** `ind-kn-fw2_gold.csv`, using the referenced Indic harness.
   - Reference CLI: **changed 0/45; dropped 0/45; harm 0.00%; PASS**.
   - Full-context run: **changed 0/45; dropped 0/45; harm 0.00%; PASS** under both reference and strict-template limits.
   - Scope: the same text transformation was assessed individually in both runs.

5. **Side effects:** a legitimate standalone social-tag list can be removed. A multiword tag such as
`#sachin tendulkar`, comma-separated tags, blank lines inside teaser lists, or a single teaser is outside
this narrow rule. No document is dropped just because much of it is a list.

## Medicine 2

1. **Disease:** C1 — boilerplate; **180 labelled documents**. Three recorded examples:

| doc_id | Exact evidence excerpt / position |
|---|---|
| `a7746a3981e58f31` | `Last Updated Mar 27, 2019, 3:47 PM IST` at 1257 |
| `bfe4d0c9f43dc03b` | `‘ವಾರ್ತಾ ಭಾರತಿ’ ನಿಮಗೆ ಆಪ್ತವೇ ?` at 1947; outside this generic rule |
| `d78b35287b746574` | `Don't Miss!` at 0 |

2. **Medicine:** Remove standalone publication/update metadata lines matching a date/time
format, the standalone social-follow prompt, and recognized navigation headers. The formats
accept variable dates, times and time zones; they contain no observed article text, publisher
names or host allowlist. Preserve inline date mentions, arbitrary bylines, publisher appeals,
image credits and unrecognized footer text. This is a narrow boilerplate repair, not a rule
for deleting every English line or every date.

```python
import re
import unicodedata

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    out = list(text)
    for a, b in spans:
        if not protected(text[a:b]):
            out[a:b] = [""] * (b - a)  # Keep source indices stable, even for overlaps.
    return "".join(out)

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
FOLLOW = re.compile(r"Please\s+follow\s+and\s+like\s+us\s*:?", re.I)

def medicine_c1(text, url=""):
    rows, spans, offset = text.splitlines(keepends=True), [], 0
    for i, line in enumerate(rows):
        body, label = line.strip(), line.strip().casefold()
        pair = (label == "just in" and i + 1 < len(rows)
                and rows[i + 1].strip().casefold() in {"don't miss!", "don’t miss!"})
        if (STAMP.fullmatch(body) or KANNADA_STAMP.fullmatch(body) or FOLLOW.fullmatch(body)
                or label in {"don't miss!", "don’t miss!"} or pair):
            spans.append((offset, offset + len(line)))
        offset += len(line)
    return remove_spans(text, spans)
```

3. **Action:** Fix text by removing only the recognized standalone metadata and headers. No automatic document drop.

4. **Harm test:** The revised generic rule has not yet been run on the **45-document**
   `ind-kn-fw2_gold.csv`. Changed and dropped counts are pending. The earlier publisher-aware
   rule changed/dropped 0/45; that result is not assigned to this revised snippet.

5. **Side effects:** a quoted metadata line or an article genuinely titled `Don't Miss!` can match.
Date syntax does not prove calendar validity or boilerplate intent. Altered or wrapped metadata,
publisher-specific bylines and donation footers remain unchanged. The rule does not repair all C1 cases.

## Medicine 3

1. **Disease:** C2 — repetition; **17 labelled documents**. Three recorded examples:

| doc_id | Evidence |
|---|---|
| `c69e1a6483bd6ac2` | `ಚಿಕ್ಕಮಗಳೂರು : ಆತ್ಮೋದ್ಧಾರಕ್ಕೆ ಸೇವೆ` begins the repeated line at 0 and 3385 |
| `0f52e8c63e977510` | `ಎಲ್ಲ ಶೋಷಣೆಗಳೂ ಸುಳ್ಳುಗಳೂ ಅಗತ್ಯಸೇವೆಯೇ ಆಗುತ್ತಿರುವಾಗ,` begins a 249-character repeat at 23 and 7915 |
| `39d902703f233992` | `ಬೆಂಗಳೂರು: ಬೋಯಿಂಗ್ ಇಂಡಿಯಾ ಹಾಗೂ ಸೆಲ್ಕೊ ಅನುದಾನದಲ್ಲಿ ಬೆಂಗಳೂರಲ್ಲಿ` begins the repeated lead at 0 |

2. **Medicine:** Keep the first exact long prose sentence/line and remove later non-overlapping
copies, including copies inside paragraphs. Require at least 80 code points, eight words and terminal
`.`, `!` or `?`. Skip fenced-code documents, verse-like layouts, quotation-led units and protected characters.
Do not treat author attributions with different dates as identical. Short repeated titles/credits and paraphrases also stay manual.

```python
import re
import unicodedata

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    out = list(text)
    for a, b in spans:
        if not protected(text[a:b]):
            out[a:b] = [""] * (b - a)  # Keep source indices stable, even for overlaps.
    return "".join(out)

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

3. **Action:** Fix text by retaining the first exact long prose passage and removing later copies. No automatic document drop.

4. **Harm test:** pinned **45-document** `ind-kn-fw2_gold.csv`, using the referenced Indic harness.
   - Reference CLI: **changed 0/45; dropped 0/45; harm 0.00%; PASS**.
   - Full-context run: **changed 0/45; dropped 0/45; harm 0.00%; PASS** under both reference and strict-template limits.
   - Scope: the same text transformation was assessed individually in both runs.

5. **Side effects:** intentionally restated long prose can still lose a later copy. Verse/layout detection is
a protective heuristic, not a genre classifier. Different internal whitespace, line wrapping, joiners,
capitalization or punctuation can prevent a match. Deleting a sentence can leave surrounding blank space;
that whitespace is deliberately not rewritten.

## Medicine 4 — F1 (rejected for unattended use)

1. **Disease:** F1 — private-data candidates; **11 labelled documents**. Three recorded examples:

| doc_id | Type and original offset |
|---|---|
| `634f9d4743893171` | phone-number-like token at 20403 |
| `c472a3db00395ba6` | phone-number-like token at 3081 |
| `76fdbcb28c49fc27` | phone-number-like token at 4853 |

2. **Medicine:** Rejected. The previous function only redacted externally approved spans.
Without human supervision it leaves every candidate unchanged. A phone/email pattern alone cannot
establish private ownership; no validated automatic replacement is proposed. The previous code is
retained in the rough notes and excluded from the executable snippets and combined pipeline.

3. **Action:** No automatic F1 fix or drop is submitted.

4. **Harm test:** The previous function changed **0/45** and dropped **0/45** gold documents
because no spans were supplied. That result does not validate unattended F1 repair. There is no
accepted F1 medicine to test in this submission.

5. **Side effects:** Automatic redaction of all numeric or email-like candidates can remove public
contacts and valid article content. The previous default leaves private data unredacted. Neither
behavior establishes a reliable unattended medicine.

## Harm-test results

The recorded results apply only to unchanged snippets:

| Rule / run | Gold docs | Changed | Dropped | Harm | Result |
|---|---:|---:|---:|---:|---|
| C5 | 45 | 0 | 0 | 0.00% | PASS |
| C1, revised generic rule | 45 | — | — | — | Not yet run |
| C2 | 45 | 0 | 0 | 0.00% | PASS |

The revised three-rule combination has not yet been run. Earlier combined results included
rules that are no longer submitted and are retained only in the rough notes.

## Rejected medicine proposals

I excluded the following repair proposals from generic unattended execution. A6 mixed-script
issues and G1 dangling vowel signs or viramas can be identified generically, but detection alone
does not establish the intended characters or word boundaries. No reliable generic repair is
submitted for either. The disease labels remain valid observations.

| Code | Disease / proposed repair | Labelled documents | Reason for rejection |
|---|---|---:|---|
| A6 | Script/font corruption — exact-word substitutions | 21 | The replacement table contains observed words from this pack. Mixed-script issues can be identified generically, but the intended replacement spelling cannot be reliably inferred. |
| G1 | Spacing / broken words — exact-word joins | 18 | The replacement table contains observed word pairs. Dangling vowel signs, halants and viramas can be identified generically, but removing spaces or reconstructing missing letters is not reliably correct in every context. |
| D3 | Mixed language — language-based deletion | 74 | Natural language mixing can be valid content. Language alone does not establish which text to remove; structural boilerplate is handled by C1/C5. |
| D4 | Bad machine translation — automatic rewriting | 23 | A reliable correction requires meaning and source context. No generic coded rewrite or drop rule is established. |
| G2 | Suspected lost ZWJ/ZWNJ — automatic joiner insertion | 21 | Missing joiners cannot be inferred from every conjunct or loanword. A blanket insertion rule can change valid Kannada text. |
| C3 | Truncation — reconstruction or automatic drop | 10 | An ellipsis, colon or missing final punctuation does not establish missing content or justify dropping a document. |
| F1 | Private-data candidates — approved-span redaction | 11 | The previous function requires human-approved spans. Without supervision it does no redaction; blanket numeric/email redaction can remove public contacts and valid content. |

Publisher-specific C1 bylines and donation-footer matches were also removed from the retained C1
medicine. They depend on named hosts and exact publisher text rather than a reusable metadata rule.
All rejected code, earlier results and removed working material are retained in the rough notes.

Labels below the more-than-five threshold: C4 (3), B3 (2), F3 (2), D5 (2), A3 (1), H2 (1), H3 (1).
I have not proposed general repair rules for these few cases.
