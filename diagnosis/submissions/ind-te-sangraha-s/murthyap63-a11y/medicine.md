# Telugu medicine functions — reviewer-ready handoff

This delivery fixes the interface issues in the existing `medicine.md` without modifying the original 500-row labels or Parquet pack.

## Files

- `medicine_ind_te_sangraha_s.py` — **actual importable Python module** containing all eight medicine functions: A3, A6, B2, B4, C2, C3, D4, D5.
- `test_medicine_ind_te_sangraha_s.py` — 13 offline interface/behavior tests (Python standard library only).
- `medicine.md` — updated medicine report(appended) with corrected function signatures and return values.

## Requirements and usage

The module uses the Python standard library (Python 3.10+). It does not edit files, start training, or need a GPU.

From the directory containing both `.py` files:

```bash
python3 -m unittest -v test_medicine_ind_te_sangraha_s.py
python3 - <<'PY'
from medicine_ind_te_sangraha_s import medicine_a3, medicine_c3, medicine_d4
text = "ఉదాహరణ Â"
print(medicine_a3(text) == text)  # True: no approved repair supplied
print(medicine_c3(text) == text)  # True: no verified ending supplied
print(medicine_d4(text) == text)  # True: no verified translation supplied
PY
```

## Function interface

Every function accepts **only the document text** when called by the harm tester:

```python
result = medicine_a3(text)
result = medicine_a6(text)
result = medicine_b4(text)
result = medicine_c3(text)
result = medicine_d5(text)
result = medicine_c2(text)
result = medicine_b2(text)
```

Return values satisfy the reviewer contract: `str` for text (possibly unchanged), `True` for an explicitly approved drop. No `(action, text)` tuples. The six review-dependent rules have safe optional defaults, and can receive reviewer-verified corrections through optional parameters. D4's first argument is `text`, not `doc_id`; an approved mapping can still be passed by keyword with `doc_id=...`.

**Critical distinction:** A gold-set test with no optional reviewer corrections will produce no changes from the six reviewer-dependent rules. That demonstrates *interface compatibility only*, not cleaning efficacy or harmlessness of later reviewer-approved patches. The two automatic rules (`C2`, `B2`) must still be tested on the official gold set.

## Repository / PR steps

## test_medicine_ind_te_sangraha_s.py

### Offline interface/behavior checks; NOT the Data A/B Telugu gold-set harm test.

import inspect
import unittest

import medicine_ind_te_sangraha_s as med


class MedicineInterfaceTests(unittest.TestCase):
    def test_eight_functions_accept_single_text_argument(self):
        sample = "ఇది తెలుగు వాక్యం."
        for name in med.__all__:
            with self.subTest(medicine=name):
                fn = getattr(med, name)
                self.assertEqual(next(iter(inspect.signature(fn).parameters)), "text")
                result = fn(sample)
                self.assertTrue(isinstance(result, (str, bool)), (name, type(result)))
                self.assertNotIsInstance(result, tuple)
                self.assertEqual(result, sample)

    def test_six_review_dependent_rules_default_to_no_change(self):
        sample = "Â <ఐ. డి. 1> λαki తెలుగు"
        for name in ["medicine_a3", "medicine_a6", "medicine_b4", "medicine_c3", "medicine_d4", "medicine_d5"]:
            with self.subTest(medicine=name):
                self.assertEqual(getattr(med, name)(sample), sample)

    def test_verified_unicode_patch_a3(self):
        self.assertEqual(med.medicine_a3("ఒక Â సమస్య", [(3, "Â", "")]), "ఒక  సమస్య")

    def test_a6_patch(self):
        self.assertEqual(med.medicine_a6("a λαki b", [(2, "λαki", "లాకి")]), "a లాకి b")

    def test_b4_patch(self):
        self.assertEqual(med.medicine_b4("ID1 ఉంది", [(0, "ID1", "నిజమైన పేరు")]), "నిజమైన పేరు ఉంది")

    def test_d5_patch(self):
        self.assertEqual(med.medicine_d5("విచిత్ర వాక్యం", [(0, "విచిత్ర", "సహజ")]), "సహజ వాక్యం")

    def test_non_overlapping_patches_use_original_offsets(self):
        self.assertEqual(med.medicine_b4("ID1 and ID2", [(0, "ID1", "X"), (8, "ID2", "Y")]), "X and Y")

    def test_mismatched_patch_fails_instead_of_guessing(self):
        with self.assertRaises(ValueError):
            med.medicine_a3("తెలుగు", [(0, "wrong", "fixed")])

    def test_overlapping_patches_are_rejected(self):
        with self.assertRaises(ValueError):
            med.medicine_b4("ABCDEF", [(0, "ABC", "X"), (2, "CD", "Y")])

    def test_c3_review_path(self):
        self.assertEqual(med.medicine_c3("మొదటి ", "మొదటి పూర్తి"), "మొదటి పూర్తి")
        self.assertEqual(med.medicine_c3("మొదటి", "ఇతర పూర్తి"), "మొదటి")
        self.assertIs(med.medicine_c3("మొదటి", confirmed_drop=True), True)

    def test_d4_review_path_and_legacy_mapping(self):
        self.assertEqual(med.medicine_d4("bad", approved_text="good"), "good")
        self.assertEqual(
            med.medicine_d4("bad", doc_id="doc7", approved_text_by_id={"doc7": "good"}), "good"
        )
        self.assertIs(
            med.medicine_d4("bad", doc_id="doc7", confirmed_drop_ids={"doc7"}), True
        )
        self.assertIs(med.medicine_d4("bad", confirmed_drop=True), True)
        self.assertEqual(med.medicine_d4("bad", approved_text=""), "bad")

    def test_c2_collapses_only_five_or_more_identical_words(self):
        self.assertEqual(med.medicine_c2("పెద్ద పెద్ద పెద్ద పెద్ద పెద్ద"), "పెద్ద")
        self.assertEqual(med.medicine_c2("పెద్ద పెద్ద పెద్ద పెద్ద"), "పెద్ద పెద్ద పెద్ద పెద్ద")

    def test_b2_converts_only_confirmed_break_tags(self):
        self.assertEqual(med.medicine_b2("ఒక<br/>రెండు<బిఆర్>మూడు"), "ఒక\nరెండు\nమూడు")
        self.assertEqual(med.medicine_b2("<div>టెక్స్ట్</div>"), "<div>టెక్స్ట్</div>")


if __name__ == "__main__":
    unittest.main()
	
# Medicine sheet: ind-te-sangraha-s (GitHub: @YOUR_GITHUB_HANDLE)

**Source pack:** 500 Telugu `ind-te-sangraha-s` documents. **Label source:** `labels 1(1).csv` (user-provided diagnosis).
**Status:** Reviewer-compatible executable functions provided in `medicine_ind_te_sangraha_s.py`; **not gold-set validated**. **No edits or drops have been applied to the source dataset.**

## Scope and evidence

- Disease definitions and medicine requirements follow the `DISEASES(1).md` and `medicine_TEMPLATE(1).md`.
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
def medicine_d4(text, approved_text=None, confirmed_drop=False, *,
                doc_id=None, approved_text_by_id=None, confirmed_drop_ids=()):
    if confirmed_drop or (doc_id is not None and doc_id in confirmed_drop_ids):
        return True  # reviewer-approved drop
    corrected = approved_text
    if corrected is None and doc_id is not None and approved_text_by_id is not None:
        corrected = approved_text_by_id.get(doc_id)
    if isinstance(corrected, str) and corrected.strip():
        return corrected  # source-verified full Telugu replacement
    return text  # safe default: unchanged text
```

3. **Action:** **Fix** only with a source-checked, Telugu-reviewed rewrite. **Drop** a document when extensive mistranslation cannot be reliably repaired. A flagged document without a verified correction stays **pending**; do not treat it as corrected.

4. **Harm test:** **NOT RUN — ** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

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
def medicine_c3(text, verified_complete_text=None, confirmed_drop=False):
    if confirmed_drop:
        return True  # reviewer-approved drop
    if verified_complete_text is None:
        return text
    if not verified_complete_text.startswith(text):
        return text  # unverified/mismatched restoration: abstain
    return verified_complete_text
```

3. **Action:** **Fix** by restoring verified missing content. **Drop** if the missing source cannot be recovered and the remaining document is unusably incomplete. Do not invent omitted lists, dates or names.

4. **Harm test:** **NOT RUN.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

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
# _apply_verified_patches is defined in medicine_ind_te_sangraha_s.py.
def medicine_b4(text, verified_patches=()):
    return _apply_verified_patches(text, verified_patches)
```

3. **Action:** **Fix** confirmed placeholder spans using the original data, or **drop** a document if essential missing information makes it unrecoverable. Never replace an unknown ID with an invented value.

4. **Harm test:** **NOT RUN .** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

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
# _apply_verified_patches is defined in medicine_ind_te_sangraha_s.py.
def medicine_a6(text, verified_patches=()):
    return _apply_verified_patches(text, verified_patches)
```

3. **Action:** **Fix** a confirmed corrupted name or token using source-verified spelling; **drop** only if the document is broadly unrecoverable. Keep unresolved cases pending human review.

4. **Harm test:** **NOT RUN .** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

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

4. **Harm test:** **NOT RUN .** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

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
# _apply_verified_patches is defined in medicine_ind_te_sangraha_s.py.
def medicine_d5(text, reviewed_phrases=()):
    return _apply_verified_patches(text, reviewed_phrases)
```

3. **Action:** **Fix** after a native-quality language edit; **drop** only if the meaning cannot be established. Do not automatically rewrite or claim the original meaning has been preserved.

4. **Harm test:** **NOT RUN.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

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

4. **Harm test:** **NOT RUN.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

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
# _apply_verified_patches is defined in medicine_ind_te_sangraha_s.py.
def medicine_a3(text, verified_patches=()):
    return _apply_verified_patches(text, verified_patches)
```

3. **Action:** **Fix** an individually verified mojibake sequence using the original encoding/source. If the intended text cannot be recovered, mark it for review (or **drop** if the document is unusable).

4. **Harm test:** **NOT RUN.** Gold documents changed: **unknown**. Gold documents dropped: **unknown**. Result: **UNVERIFIED; do not deploy.** Before approval, run this medicine on the Data A/B clean Telugu gold set, count unique changed/dropped documents, and reject the medicine if more than 1% is affected.

5. **Side effects:** The character `Â` can be legitimate in quotations, language examples, or names; some damaged byte sequences are not uniquely recoverable. A4 replacement characters are different and cannot be repaired by this rule.

---

## Reviewer-compatible Python implementation (4 Nov 2026)

- Executable code is in `medicine_ind_te_sangraha_s.py`; this Markdown sheet is documentation.
- Each of the eight rules can be called with a single `text` argument and returns `str` (possibly unchanged) or `True` for an explicitly approved drop. No rule returns `('review', text)`.
- `A3`, `A6`, `B4`, `C3`, `D4`, and `D5` default to returning the input unchanged until verified reviewer inputs are passed. This enables the one-argument harm-test interface, but is **not proof that the eventual corrections are safe or effective**.
- For `D4`, `text` is now the first argument; optional `doc_id` and the approved-text mapping are keyword-only inputs.
- Verified patch validation, overlap checks, and all exact implementations are in the `.py` file. The accompanying unittest module contains 13 offline interface/behavior checks.
- The Data A/B-approved Telugu gold-set harm tests have **not** been run here.

## Gold-set harm test procedure (pending)

For each proposed medicine:

1. Do **not** treat the 48 `clean` labels from this same sample pack as the approved gold set.
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
