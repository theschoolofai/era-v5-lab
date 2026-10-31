# Medicine sheet: ind-te-sangraha-s 

**Source pack:** 500 Telugu `ind-te-sangraha-s` documents. **Label source:** `labels.csv` (user-provided diagnosis).

## My opinion
Articles are good in content. correct to 98%. With the short Desk Top Publishing exposure i had in telugu these articles are to be corrected by a script editor. This will become a good dataset. This is also supported by the agent. Whose results are given below.

## Scope and evidence

- Disease definitions and medicine requirements follow the supplied `DISEASES(1).md` and `medicine_TEMPLATE(1).md`.
- Counts below are **documents carrying the code**, not separate occurrences; one document may have multiple diseases.
- Example quotations are exact Unicode substrings checked against the matching 500-document source-text export. Offsets are zero-based Python character offsets `[start,end)`.
- The label sheet records `read=full` for all documents, but this medicine proposal cannot independently certify translation quality or source fidelity.

| Code | Disease | Documents | Medicine required (>5)? |
|---|---|---:|:---:|
| D4 | Bad machine translation | 426 | Yes |
| C3 | Truncated documents | 32 | Yes |
| B4 | Template or code junk in prose | 10 | Yes |
| A6 | Wrong or mixed script | 9 | Yes |
| C2 | Repeated lines, phrases, or runaway word repetitions | 9 | Yes |
| D5 | Translationese | 8 | Yes |
| B2 | HTML/XML tag remnants | 8 | Yes |
| A3 | Mojibake / encoding residue | 6 | Yes |
| B3 | Ghost chat markers | 5 | No |
| G1 | Cut at vowel sign | 1 | No |
| F1 | Personal data | 1 | No |

**Required medicine entries: 8.** The template asks for one entry per disease found in more than five documents.

## Proposed medicines

### Medicine 1 — D4: Bad machine translation

1. **Disease:** `D4` — **426 of 500 documents**. Three verified examples:

   - `doc_id=c2926fcd7c9d9ef6`, offset `[1022,1091)`: `హైడ్ లెస్ పోయిడ్విన్ వికెట్ను 1/87 గణాంకాలతో ముగించడానికి ప్రకటించాడు`
   - `doc_id=1476d4874c81f2a1`, offset `[837,885)`: `శిఖరాలు ఏవీ ఎప్పుడూ శిఖరాగ్ర స్థాయికి చేరుకోలేదు`
   - `doc_id=e75cb610611b73de`, offset `[1018,1033)`: `గేదె బ్లేజర్లతో`

2. **Medicine (rule in words):** Compare the Telugu sentence with the original source, restore the intended meaning, preserve proper nouns/numbers/dates, and have a Telugu-fluent reviewer approve the complete corrected passage. **No global regex can reliably repair a wrong meaning.** Only apply verified replacements; if the passage cannot be recovered, drop the document after review.

   **Python rule / function:**

   ```python
   def medicine_d4(doc_id, text, approved_text_by_id, confirmed_drop_ids):
       if doc_id in confirmed_drop_ids:
           return 'drop', None
       corrected = approved_text_by_id.get(doc_id)
       if corrected and corrected.strip():
           return 'fix', corrected  # complete source-verified Telugu text
       return 'review', text       # abstain; do not fabricate a translation
   ```

3. **Action:** **Fix** only with a source-checked, Telugu-reviewed rewrite. **Drop** a document when extensive mistranslation cannot be reliably repaired. A flagged document without a verified correction stays **pending**; do not treat it as corrected.

4. **Harm test:** **NOT RUN — approved Telugu gold set unavailable.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

5. **Side effects:** An automated retranslation may change factual meaning, named entities, figures, gender, or terminology. Legitimate English names or technical terms may be mistakenly treated as errors. A language model alone cannot establish fidelity to an unavailable original source.

---

### Medicine 2 — C3: Truncated documents

1. **Disease:** `C3` — **32 of 500 documents**. Three verified examples:

   - `doc_id=e61e3982f326eb8b`, offset `[63115,63167)`: `కాన్స్టాన్స్ రాజు కోసం 6 మంది పిల్లలకు జన్మనిచ్చాడుః`
   - `doc_id=29196613cdcd085b`, offset `[1648,1697)`: `ఆల్ట్వీస్ ఈ క్రింది జాతీయ అలంకరణలను అందుకున్నారుః`
   - `doc_id=bae9636d02b0f6bb`, offset `[1985,2035)`: `గత yda జాతీయ సమావేశాలు ఈ క్రింది వేదికలలో జరిగాయిః`

2. **Medicine (rule in words):** Find a document that stops after a dangling heading, colon/visarga, or promised list. Retrieve the missing ending from the trustworthy original source. Append/replace only when the recovered text is verified as belonging to the document; otherwise consider dropping.

   **Python rule / function:**

   ```python
   def medicine_c3(text, verified_complete_text=None):
       if verified_complete_text is None:
           return 'review', text
       if not verified_complete_text.startswith(text):
           return 'review', text   # mismatched or edited source; compare manually
       return 'fix', verified_complete_text
   ```

3. **Action:** **Fix** by restoring verified missing content. **Drop** if the missing source cannot be recovered and the remaining document is unusably incomplete. Do not invent omitted lists, dates or names.

4. **Harm test:** **NOT RUN — approved Telugu gold set unavailable.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

5. **Side effects:** Some short encyclopaedia entries legitimately end after headings or Telugu visarga; a source may have been short originally. Blindly appending material may join unrelated documents. A partial source recovery can still leave a bad translation.

---

### Medicine 3 — B4: Template or code junk in prose

1. **Disease:** `B4` — **10 of 500 documents**. Three verified examples:

   - `doc_id=3dbf4ee7290f1569`, offset `[1129,1133)`: `ఐడి1`
   - `doc_id=976b619191078e2d`, offset `[611,621)`: `<ఐ. డి. 1>`
   - `doc_id=ece2c016b6dd2f17`, offset `[5511,5516)`: `(ID1)`

2. **Medicine (rule in words):** Detect unresolved placeholders (for example `ఐడి1`, `(ID1)`, `<ఐ. డి. 1>`) and malformed table/template remnants. Look up the original source field or table to recover the real value. Replace only individually verified spans; otherwise refer the record for manual review.

   **Python rule / function:**

   ```python
   import re
   B4_CANDIDATE = re.compile(
       r'(?:\(?ID[0-9]+\)?|ఐడి[0-9]+|<ఐ\.?\s*డి\.?\s*[0-9]+>|\{\{[^{}\n]{1,80}\}\}|!\s*కొల్న్\s*=)'
   )
   def medicine_b4(text, verified_patches):
       # verified_patches: list of (Unicode_start_offset, old_text, new_text)
       for offset, old, new in sorted(verified_patches, reverse=True):
           if text[offset:offset + len(old)] != old:
               raise ValueError('B4 patch does not match original span')
           text = text[:offset] + new + text[offset + len(old):]
       return text
   ```

3. **Action:** **Fix** confirmed placeholder spans using the original data, or **drop** a document if essential missing information makes it unrecoverable. Never replace an unknown ID with an invented value.

4. **Harm test:** **NOT RUN — approved Telugu gold set unavailable.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

5. **Side effects:** Strings such as `ID1` may be authentic identifiers, code examples, or meaningful notation. Removing table syntax can destroy the meaning of a scientific or statistical table. A missing source value cannot be reconstructed from the placeholder alone.

---

### Medicine 4 — A6: Wrong or mixed script

1. **Disease:** `A6` — **9 of 500 documents**. Three verified examples:

   - `doc_id=d7d13ed37c277bea`, offset `[26,30)`: `λαki`
   - `doc_id=fbc06e41a24bff00`, offset `[112,138)`: `сесссссссече оталооvá liga`
   - `doc_id=d4492131f05d9697`, offset `[85,106)`: `Кугер момаланга итеро`

2. **Medicine (rule in words):** Flag suspicious Greek/Cyrillic substitutions and mixed-script proper names in this Telugu pack. Check the original name and language before rewriting. Apply only confirmed character/word corrections at verified offsets; do not transliterate every foreign character.

   **Python rule / function:**

   ```python
   import re
   FOREIGN_SCRIPT_CANDIDATE = re.compile(r'[\u0370-\u03FF\u0400-\u052F]')
   def medicine_a6(text, verified_patches):
       # verified_patches: list of (Unicode_start_offset, old_text, new_text)
       for offset, old, new in sorted(verified_patches, reverse=True):
           if text[offset:offset + len(old)] != old:
               raise ValueError('A6 source text changed; verify again')
           text = text[:offset] + new + text[offset + len(old):]
       return text
   ```

3. **Action:** **Fix** a confirmed corrupted name or token using source-verified spelling; **drop** only if the document is broadly unrecoverable. Keep unresolved cases pending human review.

4. **Harm test:** **NOT RUN — approved Telugu gold set unavailable.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

5. **Side effects:** Scientific text, mathematics, or legitimate foreign-language names can correctly contain Greek or Cyrillic. Replacing visually similar letters by appearance alone may corrupt a proper noun or formula.

---

### Medicine 5 — C2: Repeated lines, phrases, or runaway word repetitions

1. **Disease:** `C2` — **9 of 500 documents**. Three verified examples:

   - `doc_id=1dfc15bd899c7864`, offset `[15652,15666)`: `శాతం శాతం శాతం`
   - `doc_id=30dba6607c964642`, offset `[11711,11742)`: `ఎనోవిడ్ ఇ, ఎనోవిడ్ ఇ, ఎనోవిడ్ ఇ`
   - `doc_id=e48ce213509a7e61`, offset `[17103,17132)`: `పెద్ద పెద్ద పెద్ద పెద్ద పెద్ద`

2. **Medicine (rule in words):** Automatically collapse an obvious run of **five or more** immediately repeated identical words to one word, while retaining any spacing outside the matched run. For duplicated sentences/clauses or table rows, compare context and require separate human approval before removing a repeated span.

   **Python rule / function:**

   ```python
   import re
   RUNAWAY_WORDS = re.compile(r'(?<!\S)(\S+)(?:[ \t]+\1(?=\s|$)){4,}')
   def medicine_c2(text):
       return RUNAWAY_WORDS.sub(lambda m: m.group(1), text)
   # For repeated whole sentences: review and remove only exact verified spans.
   ```

3. **Action:** **Fix** confirmed accidental repeats. **Drop** only when repetition makes a document unsalvageable and a reviewer approves that decision. The function below repairs word-runs only, not every C2 case.

4. **Harm test:** **NOT RUN — approved Telugu gold set unavailable.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

5. **Side effects:** Repeated words can be emphasis, a poem, quoted dialogue, or an accurate count of a repeated pattern. A single-word rule will not fix the duplicated whole sentences or phrases also present in these nine labels.

---

### Medicine 6 — D5: Translationese

1. **Disease:** `D5` — **8 of 500 documents**. Three verified examples:

   - `doc_id=7cec415bb4bdc235`, offset `[232,298)`: `ఒక దశాబ్దం కంటే ఎక్కువ కాలం గాటా యొక్క ఆర్చ్ బిషప్ గా గడిపిన ముందు`
   - `doc_id=77736f9e9be4c1ea`, offset `[57,82)`: `ఇప్పుడు ఎక్కువగా పాత వాదన`
   - `doc_id=b04d22c04ea47594`, offset `[300,343)`: `గేట్ గణనలు అత్యంత ముఖ్యమైన మొత్తం కారకాల్లో`

2. **Medicine (rule in words):** Rewrite unnaturally literal Telugu phrases into idiomatic Telugu without changing the factual meaning. This needs a Telugu-fluent reviewer and, when the interpretation is unclear, comparison to the source language. Use an approved, exact-location patch list rather than a global regex.

   **Python rule / function:**

   ```python
   def medicine_d5(text, reviewed_phrases):
       # reviewed_phrases: list of (Unicode_start_offset, old_text, idiomatic_text)
       for offset, old, new in sorted(reviewed_phrases, reverse=True):
           if text[offset:offset + len(old)] != old:
               raise ValueError('D5 phrase location mismatch')
           text = text[:offset] + new + text[offset + len(old):]
       return text
   ```

3. **Action:** **Fix** after a native-quality language edit; **drop** only if the meaning cannot be established. Do not automatically rewrite or claim the original meaning has been preserved.

4. **Harm test:** **NOT RUN — approved Telugu gold set unavailable.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

5. **Side effects:** Stylistic preferences differ by dialect, register, and domain. An apparently awkward phrasing may be valid formal Telugu; paraphrasing can accidentally change a technical distinction or the tone of a quotation.

---

### Medicine 7 — B2: HTML/XML tag remnants

1. **Disease:** `B2` — **8 of 500 documents**. Three verified examples:

   - `doc_id=d7d13ed37c277bea`, offset `[300,307)`: `<బిఆర్>`
   - `doc_id=79167d66fe9ef5eb`, offset `[1534,1539)`: `<</Â>`
   - `doc_id=3ca9fef936298941`, offset `[336,339)`: `<Â>`

2. **Medicine (rule in words):** Convert confirmed line-break tags (`<br>`, `<br/>`, and the translated artifact `<బిఆర్>`) to newlines where they are genuine markup. Other malformed tags such as `<</Â>` or `<Â>` require source inspection before removal; never strip all angle-bracket text indiscriminately.

   **Python rule / function:**

   ```python
   import re
   BR_TAG = re.compile(r'<br\s*/?>|<బిఆర్>', re.IGNORECASE)
   def medicine_b2(text):
       return BR_TAG.sub('\n', text)  # deliberately leaves other tags unchanged
   ```

3. **Action:** **Fix** verified markup artifacts while preserving nearby content. **Drop** only if the markup corruption makes the content irrecoverable.

4. **Harm test:** **NOT RUN — approved Telugu gold set unavailable.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

5. **Side effects:** An HTML tutorial may quote `<br>` literally, and a literal angle-bracket expression may be meaningful. Replacing tags with a newline can also alter tables, lists or code examples. Broken tags may overlap A3 encoding errors.

---

### Medicine 8 — A3: Mojibake / encoding residue

1. **Disease:** `A3` — **6 of 500 documents**. Three verified examples:

   - `doc_id=79167d66fe9ef5eb`, offset `[1537,1538)`: `Â`
   - `doc_id=5c1b142ee4cd51b6`, offset `[437,438)`: `Â`
   - `doc_id=3adf45c208031841`, offset `[1679,1680)`: `Â`

2. **Medicine (rule in words):** Identify suspicious UTF-8 decoding leftovers such as `Â`. Compare original source bytes and intended Unicode; then correct only the verified bad span. Do not simply delete every `Â` or use broad re-decoding without checks.

   **Python rule / function:**

   ```python
   import re
   MOJIBAKE_CANDIDATE = re.compile(r'Â|Ã.|â€™|â€œ|â€')
   def medicine_a3(text, verified_patches):
       # verified_patches: list of (Unicode_start_offset, bad_text, repaired_text)
       for offset, old, new in sorted(verified_patches, reverse=True):
           if text[offset:offset + len(old)] != old:
               raise ValueError('A3 patch is not at the recorded location')
           text = text[:offset] + new + text[offset + len(old):]
       return text
   ```

3. **Action:** **Fix** an individually verified mojibake sequence using the original encoding/source. If the intended text cannot be recovered, mark it for review (or **drop** if the document is unusable).

4. **Harm test:** **NOT RUN — approved Telugu gold set unavailable.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

5. **Side effects:** The character `Â` can be legitimate in quotations, language examples, or names; some damaged byte sequences are not uniquely recoverable. A4 replacement characters are different and cannot be repaired by this rule.

---

## Gold-set harm test procedure (pending)

The assignment states that Data A/B own the Telugu gold set (approximately 200 human-verified clean documents). The supplied files are the **sample pack, labels, disease list and blank medicine template**; they do not include that clean gold set. A sample-pack result is **not a substitute**.

For each proposed medicine:

1. Obtain the approved Telugu gold documents. Do **not** treat the 48 `clean` labels from this same sample pack as the approved gold set.
2. Run the medicine in a dry run on every gold document; count each changed or dropped document once. Count `review`/no-edit decisions as **neither changed nor dropped**, but do not approve a rule that is still missing the verification/rewrite inputs required to operate.
3. Report `changed`, `dropped`, `affected=changed+dropped`, and `affected / N × 100` for each individual medicine; reject if `affected > 0.01 * N`.
4. Review false positives and refine each rule. Re-run the full test before any approval; preserve the original dataset.

```python
def harm_summary(n_gold, changed_ids, dropped_ids):
    affected = len(set(changed_ids) | set(dropped_ids))
    return {
        "changed": len(set(changed_ids)),
        "dropped": len(set(dropped_ids)),
        "affected": affected,
        "percent": 100 * affected / n_gold,
        "passes_1_percent": affected <= 0.01 * n_gold,
    }
```

**Example threshold only (not a test result):** For exactly 200 gold documents, **at most 2** distinct gold documents can be changed or dropped by a medicine. Actual gold-set size and results are still required.

## Important below-threshold cases

- **B3 = 5 documents**: below the “more than five” medicine-entry cutoff, but dangerous special tokens (such as `<unk>`) should still be manually reviewed and handled before training.
- **G1 = 1 document**: review the split Telugu vowel sign; do not remove ZWJ/ZWNJ automatically (valid in Indic scripts).
- **F1 = 1 document**: may contain private information. Do **not** quote any personal identifier, its raw value, or hex dump in this public sheet. Follow the privacy redaction policy.

## Submission status

- [x] Used all 500 document IDs and the disease codes from the supplied label sheet.
- [x] Included one medicine for each code occurring **more than five times**.
- [x] Included three **source-verified exact character examples** with `doc_id` for every qualifying disease.
- [x] Included a rule in words, Python function, action and side effects for each.
- [ ] Replace `@YOUR_GITHUB_HANDLE` with your own GitHub handle.
- [ ] Obtain the Data A/B **approved Telugu gold set**, run each harm test and record the actual counts; do not submit this as harm-test validated before then.
- [ ] Obtain source/reviewer-approved corrections for D4/D5 and unrecoverable C3/B4/A6 cases; do not invent translation repairs.
- [ ] Complete the assignment’s independent second review of 10% of labeled documents, if not already performed.
