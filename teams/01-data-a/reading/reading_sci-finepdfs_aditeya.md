# Science reading audit (task 10): sci-finepdfs, docs 101-200

Reader: Aditeya (AditeyaAItronics). Row 10 of the Week 2 assignments, rows 101-200 of the shuffled list; Utkarsh reads rows 1-100.
The findings are in `reading_sci-finepdfs_aditeya.csv`: one row per finding, 65 rows, positions only.

## How it was read

- **Pack file:** tokenizer sample v0-clean, `train/sci-finepdfs/part-00000.parquet` (Part 1; sci-finepdfs has no Part 2).
  6,011 docs, sha256 `db4736df225c8931…`, the same as `output_sha256` in `cleaned_manifest.json`.
- **Before-cleaning file:** tokenizer sample v0, `train/sci-finepdfs/part-00000.parquet`, sha256 `87dd59b9268bf578…`
  (the `input_sha256` of this part in `job_summary.json`), used only to compare text before and after cleaning.
- **Cleaner:** spec v1 as run by TSAI on #244: `clean.py` sha256 `97c1a55b…` (`clean_sha256` in `job_summary.json`).
  Rule IDs here are the ones that ran in that job (`DA-A1-006`, `DA-C1-007`, …).
- **Seed and pick:** 20261101 with `pick_docs.py --rows 101-200`. Rows 1-100 and 101-200 of the same shuffle share no doc.
  The list is at the end of this file. "Doc 165" below means row 165 of that list.
- **Docs read:** 100, 2.11 M characters (median 6.3 K, the longest 382 K).
- **What the cleaner did to these 100:** nothing. All 100 cleaned texts are identical to v0. On the whole pack the job changed
  52 of 6,011 docs (`DA-A1-006` 36, `DA-C2-004` 10, `DA-C1-007` 6) and dropped none. Most sci rules in spec v1 are scoped to
  doc_ids of the 500-doc diagnosis pack, so they cannot fire on the tokenizer sample. For that reason this file has
  **no harm rows**: no rule touched any doc read.
- **missed / new:** `missed` = spec v1 has a sci rule for that disease code (A1, A6, B2, B4, B5, C1, C2, C3, C4, D1, D3, F1)
  and the cleaned doc still has it. Everything else is `new`, including C5, which has no sci rule.
- **Method: AI-assisted.** Claude (Anthropic) did a first pass. A script scanned the full cleaned text of every doc for each
  disease (invisible characters, mojibake, tags, templates, ligatures, repeated lines and paragraphs, boilerplate words,
  dot leaders, emails and phones, generated-caption phrases). The opening and ending of every doc, and every flagged span,
  were read. Each row was then checked against the text. The five longest docs (court transcript 289 K, proxy statement
  382 K, newspaper 172 K, charity accounts 149 K, thesis 98 K) were read by flagged span, opening and ending, not every
  line. Every row has `source` = `ai`.
- **Offsets:** code points in the cleaned text, end exclusive. A whole-doc finding is `0-<length>`. The C3 row on doc 114 is
  `p-p`, the point where the text stops.
- **quote:** left empty in every row. The sample holds personal data, so no document text goes into the repo; `why`
  is in my own words.
- **Emails:** every email in these 100 docs had already been replaced upstream by `email@example.com` or
  `firstname.lastname@example.org`, so there is no email F1. Most phone numbers are business, school or government lines, and
  only private people's numbers are logged as F1.

## Findings table

65 findings in 49 docs; the other 51 docs have no finding. Kinds: missed 34, new 31, harm 0.

| code | kind | docs affected | % of docs read |
|---|---|---|---|
| C1 | missed | 18 | 18% |
| NEW-pdf-ligatures | new | 5 | 5% |
| C2 | missed | 4 | 4% |
| F1 | missed | 4 | 4% |
| C3 | missed | 3 | 3% |
| NEW-hyphen-split-words | new | 3 | 3% |
| NEW-merged-table-cells | new | 3 | 3% |
| NEW-missing-table-data | new | 3 | 3% |
| NEW-reading-order | new | 2 | 2% |
| NEW-seo-filler | new | 2 | 2% |
| NEW-toc-dot-leaders | new | 2 | 2% |
| NEW-underscore-blanks | new | 2 | 2% |
| A1 | missed | 1 | 1% |
| C5 | new | 1 | 1% |
| D1 | missed | 1 | 1% |
| NEW-detached-diacritics | new | 1 | 1% |
| NEW-figure-only-doc | new | 1 | 1% |
| NEW-generated-image-captions | new | 1 | 1% |
| NEW-missing-spaces | new | 1 | 1% |
| NEW-orphan-figure-labels | new | 1 | 1% |
| NEW-pdf-quote-glyphs | new | 1 | 1% |
| NEW-split-superscripts | new | 1 | 1% |
| NEW-spun-text | new | 1 | 1% |

Where the existing rules miss (from the `missed` rows):

- **C1 (18 docs):** running page headers and footers (journal name, ISSN, report date, company address, `Page n of m`,
  `REV 1.0`), sometimes inside a sentence (docs 165, 171). Also repository cover pages, publisher adverts, ebook-preview
  footers and print or PDF-creator stamps.
  - The repository covers are Scholarly Commons, New Prairie Press and Groningen. DA-C1-007 matches only four cover formats
    (HAL, White Rose-style eprints, MPRA), and its running-header part runs only on six diagnosis-pack ids.
  - The publisher adverts are BioMed Central. The stamps are `Powered by TCPDF`, `PDF4Free` and the ResearchGate
    "user has requested enhancement".
- **C2 (4 docs):** a thesis title page printed 4 times, a slide deck exported with every build step, a title printed twice,
  and a calendar listing printed twice. DA-C2-004 removes a repeated lead only within the first 2,500 characters, and the
  paragraph rule is ID-scoped.
- **F1 (4 docs):** phones of private individuals given as event contacts (newspaper calendar, parish newsletter), a
  parish prayer list with names and family relations, cadet profiles of minors (name, rank, school grade, sport), and a
  civil-court docket naming private claimants and defendants. DA-F1-006 drops only nine diagnosis-pack ids.
- **C3 (3 docs):** a title line with nothing after it, an accounts-payable list cut after one entry, and an ebook preview
  that stops mid-scene.
- **A1 (1 doc):** soft hyphens (U+00AD) followed by a space split words. DA-A1-006 removes only U+FEFF and U+200B.
- **D1 (1 doc):** a Japanese document labelled `en`.

## New diseases

| name | description | docs |
|---|---|---|
| NEW-pdf-ligatures | ligature code points (U+FB00-FB06: ﬁ ﬂ ﬀ ﬃ) inside words; NFC keeps them, so tokens differ from plain `fi` | 5 |
| NEW-hyphen-split-words | line-end hyphen kept with a space after it (`company- owned`, `stereo- scopic`) | 3 |
| NEW-merged-table-cells | table cells merged or shifted (count and percent in one cell, 6 cells under 5 headers) | 3 |
| NEW-missing-table-data | a table's headings survive but its body is gone, or a list is announced and missing | 3 |
| NEW-reading-order | numbered steps or a sentence extracted out of order | 2 |
| NEW-seo-filler | spun "download this ebook" SEO pages with no content | 2 |
| NEW-toc-dot-leaders | tables of contents with dot leaders and page numbers | 2 |
| NEW-underscore-blanks | blank fill-in forms where underscore runs make up much of the text | 2 |
| C5 (no sci rule) | search-snippet farm: one title repeated with dated snippets | 1 |
| NEW-generated-image-captions | English machine-written picture descriptions ("The image shows …") inserted into a Japanese document | 1 |
| NEW-spun-text | article run through a synonym spinner ("sun powered detached plan" for passive solar design) | 1 |
| NEW-detached-diacritics | accent extracted as a separate spacing character (`Mo´nica`) | 1 |
| NEW-figure-only-doc | supplementary file whose content was figures; only title, authors and licence left | 1 |
| NEW-missing-spaces | line break lost between two words (`dcpDivision`) | 1 |
| NEW-orphan-figure-labels | diagram callouts extracted as one-letter and number lines | 1 |
| NEW-pdf-quote-glyphs | quotation marks extracted as `―` and `‖` | 1 |
| NEW-split-superscripts | ordinal `th` moved onto its own line, away from the date | 1 |

Above 1% (2+ docs of 100): NEW-pdf-ligatures, NEW-hyphen-split-words, NEW-merged-table-cells, NEW-missing-table-data,
NEW-reading-order, NEW-seo-filler, NEW-toc-dot-leaders and NEW-underscore-blanks. Over the 200 science docs (with Utkarsh's
half) the 1% line is 2 docs; the combined count goes into `reading_check_v1.md`.

## Harm

None. The cleaner did not change any of the 100 docs (identical to v0), so no rule could remove real content here.
On the whole pack it changed 52 docs; none of them is in this half of the sample.

## Open questions for the lead

1. Most sci rules are scoped to doc_ids of the 500-doc diagnosis pack, so on the tokenizer sample spec v1 is nearly a no-op
   for science (52 of 6,011 changed). Should spec v1.1 turn the C1 running-header and repository-cover rules into
   content rules, with a harm test on the sci gold set?
2. Ligatures (NEW-pdf-ligatures, 5%): a narrow map of U+FB00-FB06 to plain letters, rather than full NFKC, looks safe.
   Is that a Data A rule or a tokenizer-side normalisation (Team 3)?
3. F1 on names alone: the civil docket (doc 180) and the cadet profiles of minors (doc 176) contain no phone or email, only
   names with context. Are names of private people in public records F1 for this corpus?
4. Doc 154 (196 characters) is an excerpt of a police-style statement with a threat of violence. It is not logged as F3.
   It is evidence text, not advocacy, but the lead may want to decide.
5. Doc 196 is a Japanese document with English captions generated by a vision model. Is it D1 (drop), or keep the Japanese
   for the Japanese route and strip the generated captions?

## Doc ids read (rows 101-200 of the shuffle, in order)

| | | | | |
|---|---|---|---|---|
| 101: `0b01d4e17931cdeb` | 102: `c0ad48e380e33628` | 103: `a286f7d691161a05` | 104: `77e7a26acc77fb9f` | 105: `d84b6b9fb2522239` |
| 106: `255f57592e1e996a` | 107: `650395fbfeab86c5` | 108: `0863ac75c9ec153e` | 109: `e60d167c8b3e9fbf` | 110: `75183caf56d8e54b` |
| 111: `5a201c19575522f9` | 112: `4a33733776358fac` | 113: `2995fee8d5d7a164` | 114: `00b17b2db8046697` | 115: `03f43ec094ecc97c` |
| 116: `25ef1f02c6f05f4c` | 117: `c0b8a3e02c4dee8b` | 118: `2f6267dcaf99d714` | 119: `3e22ff820f492fa2` | 120: `c7953f24786c4754` |
| 121: `ed5687cf6229b607` | 122: `ef812364b6cca7a0` | 123: `7231c6ce2c6e0e27` | 124: `91c24a54b1ea3ba6` | 125: `19a646db74a424fd` |
| 126: `980d490625a9634d` | 127: `5d09e35b94110374` | 128: `75768b1b6b165557` | 129: `f91ebf4b70622a3e` | 130: `d8a1ed9b1607a1dd` |
| 131: `732559ee8e39b4b7` | 132: `2660580f8f3302c8` | 133: `ed5c8ecd5da28c30` | 134: `4f6a45ad70006517` | 135: `868e726c95a5af11` |
| 136: `dc43735254d92153` | 137: `f82d23a50e08a31f` | 138: `687e6f4c567f4a39` | 139: `46e23697b7c66387` | 140: `c4ee2ebebd351b57` |
| 141: `8f4e65ba0fe04bd8` | 142: `5643f370f281448a` | 143: `6227972b3dbff1b2` | 144: `93412124dc441459` | 145: `abe178bd55d72a88` |
| 146: `a49b90427d078d3f` | 147: `3940f0cf1c1d7420` | 148: `ef116ab77fd97de3` | 149: `03158e08e24178f8` | 150: `680400a6c14bde86` |
| 151: `aedf621b192970d3` | 152: `a2138bc5d5b2b2a4` | 153: `6d7eff36938ef3e7` | 154: `2f73e3f7ed7bf88b` | 155: `1264a9ef9e046b8e` |
| 156: `f163172e98bdaa35` | 157: `6deaff0b02c57734` | 158: `b1857f12c0d28f07` | 159: `d8e3f724095e4aaa` | 160: `e46456a5002848ec` |
| 161: `7f398a48bb524bdc` | 162: `e4d1400f9236b8c9` | 163: `3b2c0420a33ccaab` | 164: `8f2471175b7ae2b9` | 165: `381b21b367f75de6` |
| 166: `76ca502a2a0e018e` | 167: `3c28ee502fc8b04e` | 168: `d91d02844c32e48f` | 169: `303f5b935bffde0e` | 170: `df489e9a2ad16513` |
| 171: `63f1b68a2107c1b6` | 172: `21f33206f24a2f0e` | 173: `30085cc779561511` | 174: `765f3f0bbe7e9a83` | 175: `cac6d71a34e4928f` |
| 176: `b3ae8754bf05c33f` | 177: `48f32aa6de53150f` | 178: `12709b4b0b432005` | 179: `f78bd7a1dd958131` | 180: `1a15c4ec5610cc58` |
| 181: `365b8539483e5a3f` | 182: `b843b3c34e476817` | 183: `3b17c7620d42f333` | 184: `59aef569bc52cdff` | 185: `39bb03a0df7d4af5` |
| 186: `2223dc794fb288a2` | 187: `44b00ca0070b587c` | 188: `5184f3e79af8cf94` | 189: `d0b3e2b9bcf8e4e0` | 190: `e21134212dd567ef` |
| 191: `507e3afaa15e2375` | 192: `6cdcf2807cbf5156` | 193: `b24435b65aee7da6` | 194: `31567d352efcd98e` | 195: `5ffff0464dd66f71` |
| 196: `79596acc4ee8648a` | 197: `fac0d63aba9fab0c` | 198: `35d51dcf919068f8` | 199: `db955ac64864c36c` | 200: `28889d207c496442` |
