# Medicine sheet: ind-te-sangraha-v (oddjoker91)

## Medicine 1: C6 — proposed code; repeated-dot normalization

1. **Disease:** C6, **proposed code**. The instructor permits retaining C6 labels; final code adoption is a Gate 2 decision. There are 113 C6-labelled documents in the 500-row export (three legacy I1 punctuation labels were renamed to C6). Examples: `2a0cfe90fd36e4ed` has `. .`; `11960d16258cd4b5` has `..`; `05fa567dfc849e6b` has `. . .`.

2. **Medicine:** Normalize two or more ASCII dots, including horizontal whitespace between dots, to exactly `...`. Existing `...`, single dots and Unicode `…` remain unchanged. Do not join dots across line breaks. Decimal normalization is a separate deferred candidate below and is not called by this medicine.

   ```python
   import re
   _DOT_RUN = re.compile(r'\.(?:[^\S\r\n]*\.)+')
   def medicine_c6(text):
       return _DOT_RUN.sub('...', text)
   ```

3. **Action:** Fix punctuation only; never drop a document. No cleaned text is written back to the source pack.

4. **Harm test:** **PASS** in isolation: 1/18 gold documents changed (5.56%), 0 dropped, zero errors; ZWJ/ZWNJ and NFC/compatibility-character audits PASS. The official limit is max(1 document, 1%): one document for this small set. This is a pass under that allowance, not a strict percentage-only 1% threshold. Changed gold ID: `85644a4840025b6f`. On the full diagnosis pack, 241 documents change in memory; 93 are C6-labelled. A match does not prove a defect.

   Reproduce the active C6/C1/D3 pipeline using the original pack or its lossless doc_id/text JSONL export:

   ```sh
   python3 teams/02-data-b/tools/harm_test_indic.py \
     --medicine diagnosis/submissions/ind-te-sangraha-v/oddjoker91/medicine.md \
     --pack /private/path/ind-te-sangraha-v.jsonl \
     --gold-dir teams/02-data-b/gold --rule all --show 20
   ```

   **Active pipeline result (C6 → C1 → D3): PASS**, changed 1/18 (5.56%), dropped 0, errors 0; joiner and normal-form audits PASS. The deferred decimal candidate is excluded.

   Tested on 2026-11-04. Gold CSV Git blob: `e56a1e80788f5879d669f139eef8b1be64661129` (18 documents, exact pack). Harness Git blob: `5164392c541c4ef7b2516d5ca512fe263592e813`. No pooled or replacement gold used.

5. **Side effects:** Repeated dots can be intentional writing style, including four dots representing a sentence-ending full stop plus ellipsis. Code, paths and other structured text may use dots meaningfully. This proposal does not fix every C6 issue or establish that affected documents become clean.

### Separate C6 candidate: decimal normalization — deferred, not active

- **Proposed action:** Join a single full stop and horizontal spaces between digits: `3. 67` → `3.67`, without crossing line breaks. Examples: `f157a5cbd2fa544a` (`3. 28`), `6f4cb20218d172f1` (`7. 5`), `aab312911c6dde7b` (`6. 1`).
- **Candidate expression:** `re.sub(r'(?<![\d.])(\d+)\.[ \t]+(\d+)(?![\d.])', r'\1.\2', text)`.
- **Standalone gold result:** 1/18 changed (5.56%), 0 dropped, zero errors; joiner and normal-form audits PASS under the same small-set allowance. Changed gold ID: `d0919ae0e6249f93`. Full-pack candidate affects 29 documents, 14 C6-labelled.
- **Why deferred:** dots plus decimals together change 2/18 gold documents (11.11%) and **FAIL**. The failure is retained here; splitting the description does not make that combination safe. The candidate is excluded from the executable Python blocks and from `--rule all`; do not deploy both together without a new passing joint test.
- **Side effects:** numeric sequences may be list numbering, times or versions rather than decimal quantities. Needs further review or a linguistically justified narrower condition. The gold set stays fixed.

## Medicine 2: C1 — remove marked English-led opening link lines

1. **Disease:** C1, 84 labelled documents. Source examples: `f6f4daa0825fdc8d` begins with `- #Jr Ntr`; `7d0eb95ce450da31` has `- Sports`; `ab303656e1bad234` has `- #Hyderabad`. The rest of each matched line can contain Telugu: remove the whole line, not just the English token.

2. **Medicine:** Inspect only the first five non-empty physical lines. If a line begins with optional horizontal indentation, then `-`, `-#`, `- #` or `#`, followed by an ASCII letter (spaces around the marker are allowed), remove that entire line including its line ending. Preserve other lines exactly. Do not scan later lines. Keep the original document if this would empty it. Five non-empty lines is the explicit interpretation of "first few"; it is a fixed scope, not a gold-ID exception.

   ```python
   import re
   _C1_PREFIX = re.compile(r'^[ \t]*(?:-[ \t]*#?[ \t]*|#[ \t]*)[A-Za-z]')
   def medicine_c1(text):
       lines = text.splitlines(keepends=True)
       kept = []
       nonempty = 0
       removed = False
       for line in lines:
           if line.strip():
               nonempty += 1
           if nonempty <= 5 and line.strip() and _C1_PREFIX.match(line):
               removed = True
               continue
           kept.append(line)
       out = ''.join(kept)
       # Do not empty a document consisting solely of such lines.
       return out if removed and out.strip() else text
   ```

3. **Action:** Fix text, never drop the document. This targets opening website-link/hashtag blocks identified in the C1 evidence. It does not establish that every English-led bullet or heading is boilerplate.

4. **Harm test:** **PASS.** Official Data B harness on the current real 18-document gold set: changed 0/18 (0%), dropped 0/18, errors 0; ZWJ/ZWNJ and NFC/compatibility-character audits PASS. Gold and harness Git blobs are the same as reported for C6 above. Use the reproduction command above with `--rule C1`. Full-pack in-memory check: 20/500 documents change, including 17 C1-labelled documents and three additional candidates requiring review. Eight synthetic scope tests pass (marker variants, mixed-language lines, Telugu-led bullets, line-window limit, empty-output guard and CRLF preservation). The active C6/C1/D3 pipeline is tested together; deferred candidates are excluded.

5. **Side effects:** Legitimate opening bullet points or Markdown headings can match, including meaningful mixed-language content. Unmarked boilerplate and marked lines after the fifth non-empty line remain. The empty-output guard deliberately keeps documents composed only of matching lines. Do not infer that a fixed document is fully clean, or deploy solely because gold passes.

## Medicine 3: D3 — remove an English headline prefix

1. **Disease:** D3, 17 labelled documents. Examples: `b0b57d21903011ff` begins `Kiwi fruit:`; `05a24f223d5af5c8` begins `Hair Bath :`; `572fd22e8ac6d98c` begins `Farmers worried:`. Their label evidence identifies English mixed into Telugu headlines. This narrow candidate does not treat all code-switching as a defect.

2. **Medicine:** Remove an English/ASCII prefix and colon only at the start of the document, when Telugu follows immediately. Allow horizontal spaces and a prefix of at most 80 characters. Preserve internal prefixes, URLs and other language mixtures.

   ```python
   import re
   _D3_PREFIX = re.compile(r"\A[ \t]*[A-Za-z][A-Za-z0-9 '&(),.\-]{0,79}[ \t]*:[ \t]*(?=[\u0c00-\u0c7f])")
   def medicine_d3(text):
       return _D3_PREFIX.sub('', text, count=1)
   ```

3. **Action:** Fix the prefix only, never drop the document.

4. **Harm test:** PASS in the isolated candidate test: 0/18 gold documents changed, 0 dropped, zero errors; joiner and normal-form audits PASS. Use the same gold/harness blobs and command above with `--rule D3`. Full-pack candidate matches 23 documents; matching is not proof that each removal is appropriate. Final-file verification is recorded in the preparation report.

5. **Side effects:** A location, person or subject in the prefix may not be repeated in Telugu. For example, `Delhi:` is present in a document labelled clean in this submission; the current gold sample does not cover all valid prefixes. C2 examples `822114ef3fae2236` (`Vizianagaram:`) and `ad15daf77d5f5dba` (`Sunil Deodhar:`) also match, but removing prefixes does not fix their repeated content. Human review of proposed removals remains necessary. Do not delete all English words from natural mixed-language text.

## Why I didn't write medicines for these codes

- **C2 — repeated content (24 documents):** I found repeated sentences and paragraphs. Some repeat the same idea in different words. I didn't write a medicine yet because I need to check what can be removed without losing useful information.
- **C3 — incomplete text (60 documents):** These documents stop in the middle of a sentence. I don't know what the missing text was, so I didn't try to fill it in with a rule.
- **C4 — multiple articles (27 documents):** These have more than one article in the same document. I didn't write a medicine because I couldn't find a reliable way to separate them without cutting an article in the wrong place.
- **D4 — bad translation (44 documents):** I could see problems with the translation, but fixing them needs a person to read and understand the text. I didn't write a rule to guess the correct translation.
- **F3 — unsuitable content (64 documents):** I marked all of these as `drop` in labels.csv. I didn't write a keyword-based medicine because the same words can also appear in normal news reports.

These are my reasons for not adding automatic medicines for these codes. Please let me know if you expect a different approach. I haven't claimed harm-test results for them.
