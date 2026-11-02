# Medicine sheet: ind-kn-fw2 (LokeshJatangi)

I labelled **500 documents**, all `full`: **239 clean, 231 fix and 30 drop**.
Disease counts below are document counts; a document can have more than one label.
I propose **three reusable coded medicines** for unattended use: C5, C1 and C2.
The rules use text structure and metadata syntax, without document IDs, stored offsets,
word-replacement tables or publisher-specific exceptions. The examples below are evidence,
not lookup keys. A6 and G1 can be identified generically but have no reliable generic repair;
they remain under rejected repair proposals. D3 can be detected, but the need for repair depends
on context. F1 is retained as the last medicine, tested separately from the C5/C1/C2 combination.
Its expanded phone/email rule passed the 175-document gold harm test and matched all **32 saved
evidence offsets across 11 F1-labelled documents**. Public-contact matches remain a side effect.

For the harm test, I used the **175-document combined Kannada gold set**,
[kannada_gold.csv](https://github.com/theschoolofai/era-v5-lab/blob/2e5bbc37f99313affe35bee66481b28d6d79af0e/teams/02-data-b/gold/kannada_gold.csv),
and the [Indic harm-test reference](https://github.com/theschoolofai/era-v5-lab/blob/2e5bbc37f99313affe35bee66481b28d6d79af0e/teams/02-data-b/tools/harm_test_indic.py).
All gold IDs were matched to original source text: **45 ind-kn-fw2, 27 ind-kn-sangraha-s
and 103 ind-kn-sangraha-v**.

C5, C1, C2 and their **three-rule combination** each changed **0/175** and dropped **0/175** documents:
**0.00% harm, PASS**. This includes the current generic C1 snippet and the current three-rule
combination. The result satisfies the template's **at most 1%** limit. Clean-gold harm results
do not measure repair coverage on damaged documents.

The medicines return repaired text without dropping documents, normalizing Unicode or converting
Kannada digits. Structural deletions preserve joiners and compatibility characters.
The C5/C1/C2 combination contains no privacy redaction or automatic document-drop rule. F1 redaction is available separately.

## Combined medicines

Load all Python snippets in document order to use the combined function. The text-only reference
uses the same three-rule order. No accepted rule needs URL provenance or approved spans.
A6 and G1 have no automatic repair. F1 is tested separately with `--rule F1` and is not in this
three-rule combination. The reference with `--rule all` also includes the F1 snippet.

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

4. **Harm test:** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness.
   **Changed 0/175; dropped 0/175; harm 0.00%; PASS** under the 1% limit.

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

4. **Harm test:** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness.
   **Changed 0/175; dropped 0/175; harm 0.00%; PASS** under the 1% limit.

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

4. **Harm test:** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness.
   **Changed 0/175; dropped 0/175; harm 0.00%; PASS** under the 1% limit.

5. **Side effects:** intentionally restated long prose can still lose a later copy. Verse/layout detection is
a protective heuristic, not a genre classifier. Different internal whitespace, line wrapping, joiners,
capitalization or punctuation can prevent a match. Deleting a sentence can leave surrounding blank space;
that whitespace is deliberately not rewritten.

## Medicine 4 — F1

1. **Disease:** F1 — private-data candidates; **11 labelled documents**. Three recorded examples:

| doc_id | Type and original offset |
|---|---|
| `634f9d4743893171` | phone-number-like token at 20403 |
| `c472a3db00395ba6` | phone-number-like token at 3081 |
| `76fdbcb28c49fc27` | phone-number-like token at 4853 |

2. **Medicine:** Replace ASCII email-address candidates
and phone-like numbers with `[REDACTED]`. Accept contiguous **10 or 11 digits**, two groups of
**5+5 digits**, or a **3+8-digit** city-code/landline grouping separated by spaces or tabs.
An optional `+` followed by one to three digits and spaces/tabs is consumed as a country prefix;
no particular country code is hard-coded or required. Never join numbers across line breaks.
The rule needs no approved spans, document IDs, saved offsets or observed private values.
This is a syntactic redaction hypothesis, not a private-ownership classifier. Other groupings,
hyphenated/parenthesized formats and internationalized email addresses are outside its scope.
Original packs remain unchanged in the harm test.

```python
import re

F1_EMAIL = r"(?<![\w.+-])[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}(?![\w-])"
F1_NUMBER = r"(?:[0-9]{10,11}|[0-9]{5}[ \t]+[0-9]{5}|[0-9]{3}[ \t]+[0-9]{8})"
F1_PHONE = rf"(?<!\w)(?:\+[0-9]{{1,3}}[ \t]+)?{F1_NUMBER}(?!\w)"
F1_CANDIDATE = re.compile(rf"(?:{F1_EMAIL})|(?:{F1_PHONE})")

def medicine_f1(text, url=""):
    return F1_CANDIDATE.sub("[REDACTED]", text)
```

3. **Action:** Fix text by replacing matched phone/email candidates with `[REDACTED]`; no document
drop. F1 is available separately from the C5/C1/C2 combination. The matcher does not establish
private ownership; public contact details can also match.

4. **Harm test:** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness
   with `--rule F1`: **changed 0/175; dropped 0/175; harm 0.00%; PASS** under the 1% limit.
   On the 500-document labelled pack, candidates were found in **11/11 F1-labelled documents**
   and **32/32 saved evidence offsets matched exactly**, with no missed saved offsets.
   This validates candidate coverage on those labels, not the private ownership of every match.

5. **Side effects:** Public contact addresses, publisher phone numbers and ordinary 10- or 11-digit
numeric values can be redacted. Regex matching does not prove personal ownership. Unsupported
number groupings, non-ASCII digits and internationalized addresses can be missed. A clean-gold
PASS would measure harm on this gold set, not establish complete privacy protection.

## Harm-test results

C5/C1/C2 were tested individually and together on all **175** gold documents. The expanded F1 rule was tested separately:

| Rule / run | Gold docs | Changed | Dropped | Harm | Result |
|---|---:|---:|---:|---:|---|
| C5 | 175 | 0 | 0 | 0.00% | PASS |
| C1 | 175 | 0 | 0 | 0.00% | PASS |
| C2 | 175 | 0 | 0 | 0.00% | PASS |
| C5 → C1 → C2, prior ALL IN ORDER | 175 | 0 | 0 | 0.00% | PASS |
| D3 | — | — | — | — | Detection can be tested; no context-free repair submitted |
| F1, expanded rule tested separately | 175 | 0 | 0 | 0.00% | PASS |

**D3 detection and harm-test status:** Mixed-language candidates can be identified and detector
accuracy can be tested. A detected language change is not automatically a defect: names, quotations,
technical terms and ordinary code-switching may be appropriate. Whether to keep, remove or rewrite
text depends on context. No unconditional D3 repair is submitted, so no repair harm-test PASS is
claimed. Structural boilerplate is handled by the separately tested C1/C5 rules.

**F1 harm-test and coverage status:** The expanded matcher passed on all **175 gold documents**,
changing 0 and dropping 0. On all 500 original pack documents, it found candidates in **11/11
F1-labelled documents** and matched **32/32 saved evidence offsets exactly**, with no saved
candidates missed. The saved offset in `10e60ad0965db2c1` was corrected from the space at 1013
to the number's actual start at **1014** before recording these coverage counts.

| Previously missed evidence, now matched | Original offset | Supported format |
|---|---:|---|
| `01889f08ad435afa` | 872 | Two groups of five digits separated by a space. |
| `ea24c30c80be30df` | 1399 | An optional country prefix followed by two five-digit groups. |

The scan also found **four candidates in two documents labelled clean**: `51f68b9da172f3ae`
at 509, and `99aef15a39ddc21c` at 446, 1276 and 1287. Their contexts advertise bank or hospital
contact numbers, so these are not established private-data omissions. Candidate coverage and
private ownership remain separate questions. No source contact values were printed in the
coverage report or rewritten in the packs.

## Rejected medicine proposals

I excluded the following repair proposals from generic unattended execution. A6 mixed-script
issues and G1 dangling vowel signs or viramas can be identified generically, but detection alone
does not establish the intended characters or word boundaries. No reliable generic repair is
submitted for either. The disease labels remain valid observations.

| Code | Disease / proposed repair | Labelled documents | Reason for rejection |
|---|---|---:|---|
| A6 | Script/font corruption — exact-word substitutions | 21 | The replacement table contains observed words from this pack. Mixed-script issues can be identified generically, but the intended replacement spelling cannot be reliably inferred. |
| G1 | Spacing / broken words — exact-word joins | 18 | The replacement table contains observed word pairs. Dangling vowel signs, halants and viramas can be identified generically, but removing spaces or reconstructing missing letters is not reliably correct in every context. |
| D3 | Mixed language — unconditional language-based deletion | 74 | Mixed-language candidates can be identified and detector accuracy can be tested. Repair is not always needed and depends on context; language alone does not establish which text to remove. |
| D4 | Bad machine translation — automatic rewriting | 23 | A reliable correction requires meaning and source context. No generic coded rewrite or drop rule is established. |
| G2 | Suspected lost ZWJ/ZWNJ — automatic joiner insertion | 21 | Missing joiners cannot be inferred from every conjunct or loanword. A blanket insertion rule can change valid Kannada text. |
| C3 | Truncation — reconstruction or automatic drop | 10 | An ellipsis, colon or missing final punctuation does not establish missing content or justify dropping a document. |
| F1 | Previous approved-span-only redaction | 11 | The previous function required human-approved spans and did nothing without them, so that version remains rejected. The current automatic rule is retained as Medicine 4 with a passing gold harm test and 32/32 saved offsets matched; public-contact matches remain a side effect. |

Publisher-specific C1 bylines and donation-footer matches were also removed from the retained C1
medicine. They depend on named hosts and exact publisher text rather than a reusable metadata rule.
All rejected code, earlier results and removed working material are retained in the rough notes.

Labels below the more-than-five threshold: C4 (3), B3 (2), F3 (2), D5 (2), A3 (1), H2 (1), H3 (1).
I have not proposed general repair rules for these few cases.
