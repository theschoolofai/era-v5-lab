# Medicine sheet: ind-mr-sangraha-v (patilvijay23)

**Source:** `labels.csv` (final reviewed Marathi pack, rows 1–500), **500 distinct documents; all 500 marked `full`**. Verdicts: **99 `clean`, 362 `fix`, 39 `drop`**. This supersedes the earlier medicine sheet based on 252 documents. Disease counts are *distinct document counts*, not the number of occurrences; documents can have multiple diseases. A medicine section is included for every disease present in **more than five** reviewed documents.

**Status:** **LABEL REVIEW COMPLETE — DATA B INDIC GOLD-SET HARM TEST PASS (7 executable rules plus combined run).** All 500 source-document diagnoses have been reviewed. The user-supplied `harm_test_indic.py` console output and `ind_mr_harm_results.md` report confirm **0 changed and 0 dropped** among **88 Marathi gold documents** for each of the seven executable rules and `ALL IN ORDER` (**0.00%, PASS**). Both additional Indic safety checks — **ZWJ/ZWNJ preservation** and **normal-form/compatibility-character preservation** — report **PASS** for every executable rule and the combined run. The four context-dependent medicines (C3, D4, F1 and C4) have no executable rule and were not tested. A `fix` verdict identifies a cleaning requirement, not proof of an applied correction. Gold-set safety PASS does not establish effectiveness on disease-positive documents.

## Data B Indic gold-set harm test — reported results

These results supersede the earlier Data A `harm_test.py` results in this medicine. They are transcribed from the supplied **`harm_test_indic.py` console output** and **`ind_mr_harm_results.md`**; no new harm-test execution is claimed in this documentation update.

**Reproducible command** (run from the repository root with `harm_test_indic.py` downloaded there; adjust paths to match your local checkout):

```bash
python -I teams/02-data-b/tools/harm_test_indic.py \
  --medicine diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md \
  --pack /path/to/packs/ind-mr-sangraha-v.parquet \
  --gold-dir teams/01-data-a/gold \
  --rule all --show 10 \
  --md-out ind_mr_harm_results.md
```

**Run inputs and provenance:**

- **Harness:** `teams/02-data-b/tools/harm_test_indic.py` from TSAI (Data B), downloaded and run locally.
- **Pack:** `ind-mr-sangraha-v.parquet` (1 pack).
- **Gold CSV:** `ind-mr-sangraha-v_gold.csv`, in the directory supplied via `--gold-dir` (**88 gold documents**).
- **Medicine:** `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`.
- **Medicine SHA-256 prefix reported by the Indic runner:** `d657d7ff45e5` (**12-character prefix of the tested medicine file's SHA-256**, not Data A's rule-code hash).
- **Executable rules:** A5, D3, C1, C2, A6, B4, C5 (**7**).
- **Limit:** at most **1** gold document changed or dropped for 88 gold documents, under the TSAI rule: maximum of 1% or 1 document.
- **Indic checks:** unchanged ZWJ/ZWNJ counts; NFC and compatibility-character preservation in changed gold documents.

| Rule | Changed | Dropped | Percent | ZWJ/ZWNJ audit | Normal-form audit | Result |
| --- | ---: | ---: | ---: | --- | --- | --- |
| A5 | 0 | 0 | 0.00% | PASS | PASS | **PASS** |
| D3 | 0 | 0 | 0.00% | PASS | PASS | **PASS** |
| C1 | 0 | 0 | 0.00% | PASS | PASS | **PASS** |
| C2 | 0 | 0 | 0.00% | PASS | PASS | **PASS** |
| A6 | 0 | 0 | 0.00% | PASS | PASS | **PASS** |
| B4 | 0 | 0 | 0.00% | PASS | PASS | **PASS** |
| C5 | 0 | 0 | 0.00% | PASS | PASS | **PASS** |
| **ALL IN ORDER** | **0** | **0** | **0.00%** | **PASS** | **PASS** | **PASS** |

**Reported final result:** `result: PASS`.

**Untested manual medicines:** The Indic runner printed `note: C3 has no rule in code, so nothing to test`, and the same note for **D4, F1 and C4**. These sections intentionally specify context-dependent repair, exclusion or privacy handling without a callable `cure_<code>` function. Their absence must **not** be reported as a harm-test PASS for those operations.

**Interpretation:** The seven executable rules, both Indic-specific audits, and their combined application caused **zero measured gold-set changes or drops** across 88 documents. Because no gold documents changed, the joiner/form audits had no modified gold outputs to stress-test; they do not prove these rules preserve Indic shaping and normal form on changed, disease-positive documents. Positive-case repair effectiveness, coverage of non-executable medicines, and safe release of F1 documents require separate validation.

**Hash provenance:** The `d657d7ff45e5` prefix identifies the **original medicine file used in the supplied Indic run**. Updating the explanatory harm-test text in this Markdown file necessarily changes its raw-file SHA-256, even though the fenced cleaning-rule code is unchanged. Re-running the same command on this updated file will therefore print a different medicine-file SHA prefix; that difference alone does not indicate changed rule behavior.

## Disease coverage in the final 500 labels

| Disease | Documents | `fix` | `drop` | Proposed handling |
| --- | ---: | ---: | ---: | --- |
| A5 | 221 | 208 | 13 | Executable NFC normalization candidate |
| D3 | 148 | 129 | 19 | Preserve natural code-mixing; explicit no-op |
| C2 | 100 | 95 | 5 | Conservative exact repeated-prefix removal |
| C1 | 97 | 84 | 13 | Narrow publisher/related-content boilerplate removal |
| A6 | 45 | 42 | 3 | Automate mixed-script numeric tokens only; contextual handling for other A6 forms |
| C5 | 23 | 13 | 10 | Remove high-confidence standalone tag-list lines; separately handle headline-only documents |
| D4 | 21 | 1 | 20 | No generic rewriting; 20 drop and 1 targeted fix in reviewed labels |
| B4 | 19 | 19 | 0 | Convert literal `\n` sequences in prose (narrow gate) |
| C3 | 13 | 11 | 2 | Source/boundary-specific repair or exclude; no universal rewrite |
| F1 | 12 | 11 | 1 | Privacy-preserving redaction or exclusion; never print sensitive values |
| C4 | 11 | 7 | 4 | Traceable split/remove at verified boundaries or exclude |

**Below medicine threshold:** G1 (**4 documents**; detached Indic combining marks, context-specific repair only) and B5 (**1 document**; broken markup marker). These five diagnoses are fully labelled, but no generic executable medicine is justified by their limited evidence.

**Suggested cleaning order:** B4 → A5 → narrowly scoped A6 → C1 → C5 → C2. D3 is an explicit no-op; C3, C4, D4 and F1 are context-dependent cleaning/privacy gates, **not** executable general medicines. The supplied Data B `--rule all` Indic run reported a **PASS** for the existing file-order `ALL IN ORDER` sequence, including both Indic-specific audits. The suggested cleaning order here is descriptive and may differ from the sequence actually run by the harness. Verify positive-document effectiveness and combined-rule interactions before deployment.

**Long-context preservation:** **12 documents** are tagged `Long-context candidate — use for long context` in the reviewed labels' `note` column, including both clean documents and documents with fixable defects. Do not impose a blanket short-length cap or drop them merely because they are long; preserve the coherent long-form text after authorized fixes. No long-context candidate has a `drop` verdict.

---

## Medicine 1 — A5: wrong Unicode normal form

1. **Disease:** A5, **221 documents**. Decomposed Devanagari forms whose NFC normalization changes the code-point sequence. Examples from the labels:
   - `4884f7c293a7beab`: `ऱ` at offset 2437 → NFC `ऱ`.
   - `47594b68339a08b9`: `ऴ` → NFC `ऴ`.
   - `038ffeeda8d9dca7`: `ऱ` at offset 68 (5 occurrences) → NFC `ऱ`.
   - **Additional reviewed example (rows 351–500 unless noted):** `2fcf621e5200ec99`: non-NFC `ऱ` at offset 171.

2. **Medicine:** Normalize the text to NFC. Do **not** use NFKC or change Indic digits, ZWJ or ZWNJ.

   ```python
   import unicodedata

   def cure_a5(text):
       return unicodedata.normalize("NFC", text)
   ```

3. **Action:** Fix by NFC normalization only; it does not override a document-level `drop` decision for other diseases.

4. **Harm test (Data B Indic `harm_test_indic.py`): PASS** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). This demonstrates no measured gold harm; it does not establish NFC-repair effectiveness on A5-positive documents.

5. **Side effects:** NFC changes code-point sequences and may invalidate offsets; NFC does **not** reconnect a detached matra/virama, repair OCR errors, or fix severe structural corruption. Count actual changes in the harm test rather than presuming they are harmless.

## Medicine 2 — D3: natural mixed-language content

1. **Disease:** D3, **148 documents**. Natural Marathi mixed with English names, titles, technical words, or Sanskrit quotations. Examples:
   - `870f3c12624cc486`: `UPSC` near offset 1172.
   - `31e2deeb3fd7a6f3`: `Karjat Nagar Panchayat Election` near offset 200.
   - `8344f9091076fadd`: English phrase `The question is will he get` near offset 866.
   - **Additional reviewed example (rows 351–500 unless noted):** `bfd0e9032a359e9b`: natural Marathi–English code-mixing near offset 0; co-occurring C1/C2 require separate attention.

2. **Medicine:** Preserve the text. Mixed language alone is **not** evidence that the document is damaged.

   ```python
   def cure_d3(text):
       return text
   ```

3. **Action:** Keep unchanged for D3. Apply separate, independently tested medicines if the same document also has another disease. **28 reviewed D3-only documents** have a `fix` verdict in the source labels. Preserve those verdicts as submitted, but do not treat this no-op as a text correction or report 28 documents changed. Any separate transformation must be justified by another disease or a specifically documented operation.

4. **Harm test (Data B Indic `harm_test_indic.py`): PASS** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Because this is an intentional no-op, its PASS does not show that any D3-only `fix` records were corrected.

5. **Side effects:** No direct mutation. The risk is *over-cleaning by other medicines*: an English name, English headline, or Sanskrit quotation is not necessarily C1/C5 boilerplate or A6 corruption.

## Medicine 3 — C1: publisher/navigation boilerplate

1. **Disease:** C1, **97 documents**. Publisher promotions, unrelated navigation, login/footer prompts and related-story notices. Examples:
   - `2c66d24bfd6db2ef`: related-story marker `हे ही वाचाः` near offset 1082.
   - `e14f9a0e6e8d1d9b`: English publisher promotion near offset 741 and Marathi follow prompt near offset 972.
   - `038ffeeda8d9dca7`: social-media/source navigation near offset 1312 (`साम आता सर्व सोशल मीडिया`).
   - **Additional reviewed example (rows 351–500 unless noted):** `983103a12fa7a78f`: publisher/navigation boilerplate near offset 1926.

2. **Medicine:** Remove only full lines starting with clearly identified navigation/related-story/promo phrases; do not delete text just because it is in English. Keep line endings stable and avoid deleting partial sentence matches.

   ```python
   import re

   _C1_LINE = re.compile(
       r"^\s*(?:"
       r"हे\s*ही\s*वाचा\s*[:ः]?.*"
       r"|हेही\s*वाचा\s*[:ः]?.*"
       r"|हे\s*देखील\s*वाचा\s*[:ः]?.*"
       r"|Read\s+Also\s*[:\-]?.*"
       r"|Keep\s+Reading\s*[:\-]?.*"
       r"|Forgot\s+your\s+password\??\s*.*"
       r"|Home\s*/\s*Marathi\s*"
       r"|Get\s+Latest\s+Marathi\s+News.*"
       r"|साम\s+आता\s+सर्व\s+सोशल\s+मीडिया.*"
       r")\s*$",
       flags=re.IGNORECASE,
   )

   def cure_c1(text):
       lines = text.splitlines(keepends=True)
       return "".join(
           line for line in lines
           if not _C1_LINE.fullmatch(line.rstrip("\r\n"))
       )
   ```

3. **Action:** Fix only matching boilerplate lines. A `drop` verdict remains if no coherent article survives.

4. **Harm test (Data B Indic `harm_test_indic.py`): PASS** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Verify independently that the narrow matcher removes actual C1 boilerplate without deleting article content.

5. **Side effects:** Some genuine article text could begin with one of the listed phrases, and boilerplate embedded mid-paragraph is intentionally not removed. This rule is conservative; context-specific cleanup is needed for more complex cases.

## Medicine 4 — C2: exact repeated lead/content

1. **Disease:** C2, **100 documents**. Duplicate titles, lead paragraphs, or repeated article snippets. Examples:
   - `4884f7c293a7beab`: opening paragraph repeats at offsets 0 and 316.
   - `948113e0495d4af9`: opening text repeats at offsets 0 and 122.
   - `9532c5c8c0d27ac4`: lead/title repeats at offsets 0 and 114.
   - **Additional reviewed example (rows 351–500 unless noted):** `f8666e415e416667`: repeated lead/text near offsets 104 and 344.

2. **Medicine:** Remove only a **long, exact** second copy of the document's opening content if it occurs near the beginning; do not perform global line deduplication, fuzzy matching, or removal of legitimate refrains.

   ```python
   def cure_c2(text):
       seed_len, min_repeat, search_limit = 48, 80, 1600
       if len(text) < min_repeat * 2:
           return text
       seed = text[:seed_len]
       second = text.find(seed, seed_len, min(len(text), search_limit))
       if second < 0:
           return text
       matched = 0
       max_match = min(second, len(text) - second)
       while matched < max_match and text[matched] == text[second + matched]:
           matched += 1
       if matched < min_repeat:
           return text
       return text[:second] + text[second + matched:]
   ```

3. **Action:** Fix only verified exact repeated prefixes, keeping the first occurrence. Review other C2 variants manually.

4. **Harm test (Data B Indic `harm_test_indic.py`): PASS** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Verify on C2-positive documents that intended duplicates are removed with valid joins.

5. **Side effects:** Repeated opening text may be intentional (poetry, quotations, structured articles). The strict rule misses shorter duplicates and OCR-altered copies, which is preferable to deleting uncertain content. Check the resulting join around the removed span.

## Medicine 5 — A6: wrong or mixed script

1. **Disease:** A6, **45 documents**. A heterogeneous collection including corrupted mixed digits, hyphenated Marathi words, intruding Latin characters, and a stray non-Devanagari symbol. Examples:
   - `4884f7c293a7beab`: mixed digits `१0७`, `१0`, `३0` (ASCII zero positions recorded at offsets 1901, 1910 and 1952 in the final labels).
   - `e71787a3124f9007`: Marathi word fragments `चेह-याच्या` and `ब-याच` (hyphen positions at offsets 509 and 834 in the final labels).
   - `208b033cb8584898`: stray `U+00BA` inside a Marathi word near offset 787 (2 occurrences).
   - **Additional reviewed example (rows 351–500 unless noted):** `7d5867bf37cf6900`: stray `U+00BA` in a word near offset 885 (also F1; handle privacy separately).

2. **Medicine:** **Automate only one narrow subtype:** replace ASCII digits inside a contiguous token containing both ASCII and Devanagari digits. Hyphen, stray `U+00BA`, Latin-character intrusion, standalone ASCII digits, and other A6 cases need separate context-aware decisions.

   ```python
   import re

   _A6_MIXED_DIGITS = re.compile(r"[०-९0-9]+")
   _A6_DIGIT_MAP = str.maketrans("0123456789", "०१२३४५६७८९")

   def cure_a6(text):
       def convert(match):
           token = match.group()
           if re.search(r"[०-९]", token) and re.search(r"[0-9]", token):
               return token.translate(_A6_DIGIT_MAP)
           return token
       return _A6_MIXED_DIGITS.sub(convert, text)
   ```

3. **Action:** Fix the mixed-digit subtype only; handle remaining A6 occurrences through verified context-specific repairs or separately tested medicines; do not pretend that the mixed-digit rule covers all 45 A6 documents.

4. **Harm test (Data B Indic `harm_test_indic.py`): PASS** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Only mixed-digit conversion is covered; other A6 subtypes require separate source-aware tests.

5. **Side effects:** Even mixed-script digits can occasionally be deliberate; global Latin removal, blanket hyphen replacement, or indiscriminate `U+00BA` substitution would risk damaging legitimate names and D3 code-mixing.

## Medicine 6 — B4: literal escaped newline in prose

1. **Disease:** B4, **19 documents**. A literal backslash followed by `n` occurs where a line boundary is intended. Examples:
   - `5cd1cc2146075a9f`: literal `\n` near offset 81 (3 occurrences).
   - `09f78635c7686fd8`: literal `\n` near offset 14 (11 occurrences).
   - `8f3c76c4c4ad8584`: literal `\n` near offset 109 (13 occurrences).
   - **Additional reviewed example (rows 351–500 unless noted):** `3561e05403291f93`: literal `\n` near offset 42 (99 occurrences).

2. **Medicine:** Convert the literal two-character sequence `\n` to a newline **only for this identified prose subtype**. Run before line-based C1/C5/C2 cleaning.

   ```python
   def cure_b4(text):
       # Conservative gate for recurring escaped newlines in the Marathi prose pack.
       if text.count("\\n") < 3:
           return text
       return text.replace("\\n", "\n")
   ```

3. **Action:** Fix escaped newlines when they recur as prose formatting artifacts.

4. **Harm test (Data B Indic `harm_test_indic.py`): PASS** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Check B4-positive prose separately so valid technical escape sequences remain intact.

5. **Side effects:** Technical quotations can legitimately include `\n`. The recurrence threshold reduces but does not eliminate that risk. Other escaped control sequences are left untouched.

## Medicine 7 — C3: incomplete or truncated document

1. **Disease:** C3, **13 documents**. Text starts or stops mid-sentence, or page-continuation artifacts interrupt it. Examples:
   - `7ac16bc32542abcd`: incomplete ending near offset 1203.
   - `8acc240b173977d0`: incomplete beginning at offset 0 and page-continuation artifacts.
   - `177179a646864418`: incomplete ending near offset 824 (`चांगले निर्णय`).
   - **Additional reviewed example (rows 351–500 unless noted):** `31dcd9c6ce0f3808`: incomplete document boundary near offset 31221; long-context candidate.

2. **Medicine:** **Context-specific operation; not an unreviewed label.** Verify the source boundary and either restore the missing text, trim the demonstrably incomplete fragment while preserving a coherent document, or exclude the document. A universal regex cannot reliably infer the original sentence or detect all truncated Marathi prose. **No executable Python medicine is proposed.**

3. **Action:** Fix only with verified source/boundary; **drop** when no coherent content remains (as in `0ad004d5deb1e7fe`, labelled `drop`).

4. **Harm test (Data B Indic `harm_test_indic.py`): NOT EXECUTED.** The runner reported `note: C3 has no rule in code, so nothing to test`. This medicine is context-dependent and has no executable `cure_c3`; neither the gold-set PASS nor the ZWJ/ZWNJ and normal-form audit results cover this manual operation. Any future automated cure must be evaluated separately for effectiveness and harm.

5. **Side effects:** Trimming near punctuation can remove legitimate text; generating a missing ending would invent content. Some incomplete-looking passages are intentional excerpts.

## Medicine 8 — D4: severely unnatural machine translation

1. **Disease:** D4, **21 documents**. Broken literal translation, unnatural Marathi grammar, or extensive semantically corrupted wording. Examples:
   - `61b2c25e9513730b`: broken translated phrasing near offset 2793 (`काय माजी कर्मचारी किराणा दुकान...`).
   - `866b1853d8a9d95a`: severely unnatural text from offset 0.
   - `43785419033933e9`: severely unnatural translated phrasing from offset 0.
   - **Additional example from reviewed row 291:** `cc36761de1d96f0f`: localized awkward translated wording near offset 981, labelled `fix` rather than `drop`.
   - **New example from rows 351–500:** `816e770dc45f85c5`: pervasive machine-translation grammar corruption from offset 0; labelled `drop`.

2. **Medicine:** **Source-aware intervention only.** Of the 21 reviewed D4 documents, **20 carry `drop` and 1 carries `fix`** (`cc36761de1d96f0f`, a localized wording defect). Do not attempt word-by-word regex "repair" or machine-generate a replacement training document. The single `fix` case needs an evidence-preserving local correction, not a global language rewrite. **No executable Python medicine is proposed.**

3. **Action:** **Drop the 20 documents marked `drop`**, including `9e41a5d56ac92089` and `f94044ff48697280` (both now labelled `full`); retain the single `fix` document for a limited, source-faithful wording repair. All 21 diagnoses are final reviewed labels.

4. **Harm test (Data B Indic `harm_test_indic.py`): NOT EXECUTED.** The runner reported `note: D4 has no rule in code, so nothing to test`. This medicine is context-dependent and has no executable `cure_d4`; neither the gold-set PASS nor the ZWJ/ZWNJ and normal-form audit results cover this manual operation. Any future automated cure must be evaluated separately for effectiveness and harm.

5. **Side effects:** Unusual idioms, literary style and natural code-mixing could be mistaken for bad translation. Avoid applying a broad language-quality classifier without validation.

## Medicine 9 — F1: private-person information

1. **Disease:** F1, **12 documents**. Private residential locations, personally linked addresses or contact details. Examples **without revealing any private values**:
   - `fab4928039a870ab`: private-person-linked street-level location near offset 9.
   - `727a8a3d9a6f4fd4`: phone number near offset 2095.
   - `d2dbdd1f87b6a3e1`: private residential location near offset 278.
   - **Additional reviewed example (rows 351–500 unless noted):** `b5776aacf45b7cac`: private-person identity/location at offset 256 (private values intentionally omitted).

2. **Medicine:** **Context-specific privacy gate.** Identify and redact the exact private span with surrounding context, or exclude the document if the sensitive material cannot be safely removed. Names of public figures and public institutions are not automatically private data. **Do not embed any private values in rule code, examples, logs, PRs or JSON reports. No executable redaction rule is proposed until a safe detector is tested.**

3. **Action:** Fix by verified, privacy-preserving redaction; otherwise **drop**. Do not release an unredacted F1 record.

4. **Harm test (Data B Indic `harm_test_indic.py`): NOT EXECUTED.** The runner reported `note: F1 has no rule in code, so nothing to test`. This medicine is context-dependent and has no executable `cure_f1`; neither the gold-set PASS nor the ZWJ/ZWNJ and normal-form audit results cover this manual operation. Any future automated cure must be evaluated separately for effectiveness and harm.

5. **Side effects:** A broad name/address detector can erase legitimate public references; a narrow detector can miss sensitive data. The label's `hex` and evidence should never reproduce private values.

## Medicine 10 — C4: unrelated documents joined

1. **Disease:** C4, **11 documents**. Two unrelated articles or passages concatenated without a reliable document boundary. Examples:
   - `eca53051bfdab52d`: a new document begins near offset 1975.
   - `815eb112e94faf6e`: unrelated second text begins near offset 115.
   - `f2b8c25ffbcc196c`: unrelated standalone passage begins near offset 555 (`रशियातल्या फिफा`).
   - **Additional reviewed example (rows 351–500 unless noted):** `f1b6e560a1351d1c`: unrelated joined passage starts near offset 1716.

2. **Medicine:** **Context-specific operation; not an unreviewed label.** Inspect the boundary and split into separately traceable documents, or retain just the verified coherent span if provenance permits. Do not create duplicate `doc_id`s or guess split locations from language switches alone. **No executable Python medicine is proposed.**

3. **Action:** Fix by a provenance-preserving split/removal when possible; **drop** when the surviving text is not coherent (`d89a364142de1d38` and `9910e11f3461f5d0` are labelled `drop`).

4. **Harm test (Data B Indic `harm_test_indic.py`): NOT EXECUTED.** The runner reported `note: C4 has no rule in code, so nothing to test`. This medicine is context-dependent and has no executable `cure_c4`; neither the gold-set PASS nor the ZWJ/ZWNJ and normal-form audit results cover this manual operation. Any future automated cure must be evaluated separately for effectiveness and harm.

5. **Side effects:** Legitimate bilingual quotations, interviews, and multi-section articles may look like joined documents; blind splitting can corrupt source context.

## Medicine 11 — C5: tag/keyword/headline-list contamination

1. **Disease:** C5, **23 documents**. Navigation headlines, SEO tags, related-article lists, and keyword blocks mixed with prose. Examples:
   - `4dea645e7a66adbb`: headline/keyword list begins near offset 2520.
   - `5c0626f06c750fcf`: navigation headline/tag-list starts at offset 0 (`लाईव्ह न्यूज`); the record is labelled `drop`.
   - `9532c5c8c0d27ac4`: standalone `Tags: Sleeping habits` near offset 320.
   - **Additional reviewed example (rows 351–500 unless noted):** `0c7931b66f6e2ea5`: unrelated headline/link list near offset 4702 (also C1/B4).

2. **Medicine:** Remove only clearly standalone tag/keyword lines, not legitimate lists that are part of article content. Whole navigation-only documents retain their reviewed `drop` action; generic text segmentation is not safe here.

   ```python
   import re

   _C5_TAG_LINE = re.compile(
       r"^\s*(?:Tags?|Keywords?|कीवर्ड)\s*[:：]\s*\S.*$",
       flags=re.IGNORECASE,
   )

   def cure_c5(text):
       return "".join(
           line for line in text.splitlines(keepends=True)
           if not _C5_TAG_LINE.fullmatch(line.rstrip("\r\n"))
       )
   ```

3. **Action:** Fix standalone matched tag lines; remove other verified contamination with a context-specific operation. **Drop** documents composed almost entirely of navigation/headline lists (e.g., `5c0626f06c750fcf`), consistent with their labels.

4. **Harm test (Data B Indic `harm_test_indic.py`): PASS** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). The narrow tag-line rule does not cover every C5 headline-list subtype; test positive-case coverage separately.

5. **Side effects:** Metadata examples and instructional prose can contain genuine `Tags:` or `Keywords:` lines. Broadly deleting any list or headline would destroy real content. Some C5 overlaps C1, so combined-rule effects must be assessed separately.

---

## Review and release checklist

- **Reviewed label input:** All **500** source records are `full`. Preserve the submitted **99 clean / 362 fix / 39 drop** verdicts, the reviewed evidence/offsets and the 12 long-context tags. No 252-row totals or `partial`-read labels remain.
- **D3 semantics:** The labels contain **28 D3-only `fix` documents** even though the D3 medicine deliberately leaves text unchanged. These reviewed labels are preserved. Do not claim a D3 cleaning change or invent a mutation to make a `fix` label match the no-op.
- **D4 outcomes:** Apply the reviewed outcome, **20 `drop` and 1 `fix`**, rather than the earlier all-drop assumption. Do not rewrite heavily corrupted content just to retain it.
- **Rule extraction:** Only the sections with `cure_<code>` functions are *executable candidates*: A5, D3 (no-op), C1, C2, A6 (mixed numerals only), B4 and C5. C3, C4, D4 and F1 are intentionally non-executable source/context/privacy gates. Below-threshold G1 and B5 have no general medicine.
- **Gold harm tests:** **Completed in the supplied Data B `harm_test_indic.py` console output and `ind_mr_harm_results.md`** for **88 Marathi gold documents**: seven executable rules and `ALL IN ORDER` each reported **0 changed, 0 dropped, 0.00%, PASS**. All eight runs also reported **PASS** for ZWJ/ZWNJ preservation and normal-form/compatibility-character checks. The limit was **1 changed/dropped gold document**. The tested medicine SHA-256 prefix was `d657d7ff45e5` (the updated Markdown file will have a different full-file hash). C3, D4, F1 and C4 were not executed because they have no callable rules. These are user-supplied results, not a re-run for this document update.
- **Effectiveness and clashes:** The reported individual and combined **gold-harm PASS** does not prove positive-label cleaning coverage, especially because all seven rules changed zero gold documents. Measure recall and actual changes on reviewed, disease-positive pack documents. Check overlaps (especially C1/C5, A5/A6, B4/C1/C2), verify the actual harness execution order, and separately evaluate any revised combined pipeline.
- **Long context:** Preserve all 12 flagged long-context candidates. If a candidate also has C3 or other fixable defects, apply the documented cleanup while retaining the coherent long-form span; do not globally truncate.
- **Privacy:** For F1, publish **type and offset**, never private values in examples, logs, rule code, diffs or reports. Redact or exclude affected source text before release.
- **Indic text safety:** Keep ZWJ and ZWNJ, avoid NFKC and global deletion of spaces around matras/viramas. G1 repairs require precise contextual evidence; do not derive a generic rule from four documents.

**Interpretation:** Label diagnosis is complete. The supplied **Data B Indic** gold-set harm run **passed** for all seven executable rules and `ALL IN ORDER` (88 gold documents; 0 changed, 0 dropped), with **PASS** on the ZWJ/ZWNJ and normal-form audits. These additional audits provide no evidence about behavior on changed gold documents because no gold documents were modified; the safety result does **not** establish positive-document cleaning effectiveness or cover the four non-executable manual gates.
