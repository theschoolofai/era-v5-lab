# Medicine sheet: ind-te-sangraha-v (oddjoker91)

## Medicine 1: C6 — proposed code; punctuation and formatting candidates

1. **Disease:** C6, **proposed code**. The instructor permits retaining C6 labels; final code adoption is a Gate 2 decision. There are 113 C6-labelled documents in the prepared 500-row export (three legacy I1 punctuation labels were renamed to C6).

   Examples of repeated dots: `2a0cfe90fd36e4ed` has `. .`; `11960d16258cd4b5` has `..`; `05fa567dfc849e6b` has `. . .`.

   Decimal examples: `f157a5cbd2fa544a` has `3. 28`; `6f4cb20218d172f1` has `7. 5`; `aab312911c6dde7b` has `6. 1`.

2. **Medicine:** Two candidate steps, in this order:
   - Join digits separated by a single full stop followed by horizontal spaces: `3. 67` → `3.67`. Do not cross line breaks or modify a single full stop without digits on both sides. This may also repair a spaced version number; it cannot determine whether a numeric sequence is a decimal or a numbered-list item.
   - Normalize two or more ASCII dots, including horizontal whitespace between dots, to exactly `...`. Existing `...`, single dots and Unicode `…` remain unchanged; do not join dots across line breaks.

   ```python
   import re
   _DOT_RUN = re.compile(r'\.(?:[^\S\r\n]*\.)+')
   _DECIMAL = re.compile(r'(?<![\d.])(\d+)\.[ \t]+(\d+)(?![\d.])')
   def _dots(text):
       return _DOT_RUN.sub('...', text)
   def _decimals(text):
       return _DECIMAL.sub(r'\1.\2', text)
   def medicine_c6(text):
       return _dots(_decimals(text))
   ```

3. **Action:** Fix text only; never drop a document. **The combined candidate currently fails the gold test and is not ready for deployment.** No cleaned source text has been written back. The full-pack checks below measured in-memory transformations only.

4. **Harm test:** Tested on the current upstream `ind-te-sangraha-v_gold.csv`, all 18 documents, using Data B's official `harm_test_indic.py` on 2026-11-04. The limit is max(1 document, 1%): one document here. Each variant was run in isolation, and the combined function above was also tested.

   | Candidate | Changed | Dropped | Result |
   | --- | ---: | ---: | --- |
   | Dots only | 1/18 (5.56%) | 0 | PASS |
   | Decimal spacing only | 1/18 (5.56%) | 0 | PASS |
   | Both C6 steps, combined | 2/18 (11.11%) | 0 | **FAIL** |

   All variants had zero execution errors and passed the ZWJ/ZWNJ and NFC/compatibility-character audits. Dots change gold ID `85644a4840025b6f`; decimal spacing changes a different gold ID, `d0919ae0e6249f93`. Separate passes do not establish that their combination passes. Keep the gold set fixed; narrow the candidate on linguistic grounds or retain it for later review.

   On the full 500-document diagnosis pack, dots affect 241 documents and decimal spacing affects 29; both steps together affect 251. These are in-memory measurements, not edits written to the source. This medicine does not resolve every C6 issue. English-prefix removal is a separate D3 medicine below.

   Reproduce the combined test using the original pack (or its lossless doc_id/text JSONL export):

   ```sh
   python3 teams/02-data-b/tools/harm_test_indic.py \
     --medicine diagnosis/submissions/ind-te-sangraha-v/oddjoker91/medicine.md \
     --pack /private/path/ind-te-sangraha-v.jsonl \
     --gold-dir teams/02-data-b/gold --rule all --show 20
   ```

   Gold CSV Git blob: `e56a1e80788f5879d669f139eef8b1be64661129`. Harness Git blob: `5164392c541c4ef7b2516d5ca512fe263592e813`. No pooled language set or private replacement gold was used.

5. **Side effects:** Repeated dots can be intentional style, including four dots for a full stop plus ellipsis; structured text can contain meaningful repeated dots. Numeric sequences can be list numbering rather than decimals. This proposal does not fix unmatched quotes, word segmentation, missing unit spaces, excessive line breaks or unrelated trailing content. Review those separately; do not infer that a changed document is now clean.

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

4. **Harm test:** **PASS.** Official Data B harness on the current real 18-document gold set: changed 0/18 (0%), dropped 0/18, errors 0; ZWJ/ZWNJ and NFC/compatibility-character audits PASS. Gold and harness Git blobs are the same as reported for C6 above. Use the reproduction command above with `--rule C1`. Full-pack in-memory check: 20/500 documents change, including 17 C1-labelled documents and three additional candidates requiring review. Eight synthetic scope tests pass (marker variants, mixed-language lines, Telugu-led bullets, line-window limit, empty-output guard and CRLF preservation). This standalone pass does not change the failing C6 or combined-pipeline result.

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

## Other frequent diseases: current disposition

These remain diagnosed in labels.csv; no automatic cleaning rule is asserted here yet.

- **C2 (24):** exact repeated sentences/paragraphs can sometimes be deduplicated safely; semantic repetition requires review. Candidate not implemented or harm-tested.
- **C3 (60):** truncated text cannot be reconstructed reliably by a regex. Human review is needed to choose retaining a useful fragment versus dropping the document. No automatic candidate.
- **C4 (27):** multiple articles can potentially be split only where reliable boundaries and retained context are available. No automatic candidate.
- **D4 (44):** bad translation needs native review or a validated quality filter; do not invent a corrected translation or a broad keyword drop rule. No automatic candidate.
- **F3 (64):** retain the reviewed drop decisions in labels.csv. A general content detector needs its own validation; this sheet does not claim a new automatic detector or a harm-test pass for one.

These dispositions document limits; they do not satisfy a request for executable, passing medicines for all frequent diseases. Raise the non-automatable cases with the reviewer rather than fabricate rules or results.
