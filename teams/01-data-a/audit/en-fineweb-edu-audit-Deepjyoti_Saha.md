# en-fineweb-edu audit: issues and proposals

Week 3 (22 to 23 Nov 2026). Reviewer: Deepjyoti Saha (rotation, Team 1). Pack: `en-fineweb-edu`, 35 documents: 25 from Part_1 (`part-00000`) and 10 from Part_2 (`part-00001`). Taken over from the unsubmitted assignment, as agreed in "01 Data A" on 22 Nov.

Each document was compared raw (`Cap1-packs/`) against cleaned (`tokenizer_sample_v0_clean/train/`), matched by `doc_id`. Disease codes follow [DISEASES.md](../../../diagnosis/DISEASES.md). The labels are in `en-fineweb-edu-Part_1-Deepjyoti_Saha.csv` and `en-fineweb-edu-Part_2-Deepjyoti_Saha.csv` (the viewer's seven columns; `evidence` and `hex` left empty). A dropped document has no verdict; its note says whether the drop looks right or wrong, as in the en-dclm audit.

## Inputs and method

| Input | File | sha256 |
|---|---|---|
| Raw Part_1 | `Cap1-packs/en-fineweb-edu/Part_1/part-00000.parquet` | `53cbbf7a77b84e46…` |
| Raw Part_2 | `Cap1-packs/en-fineweb-edu/Part_2/part-00001.parquet` | `bdd5d5b4f7aa8ec0…` |
| Cleaned Part_1 | `tokenizer_sample_v0_clean/train/en-fineweb-edu/part-00000.parquet` | `2d0ac7331258ba29…` |
| Cleaned Part_2 | `tokenizer_sample_v0_clean/train/en-fineweb-edu/part-00001.parquet` | `f2f89744215cf72c…` |

- **Selection:** only changed documents, as with the viewer's "Only changed" default (`diagnosis/tools/view_packs_hub.py`, branch `g1-web-viewer-pre-post` at `be1571f8`). A document counts as changed if its text differs after cleaning or it is missing after cleaning. Part_1 has 1,428 changed documents of 54,004 (406 dropped); Part_2 has 514 of 17,929 (153 dropped). The 35 are a random sample of the changed ones (`random.Random(20261122).sample`, Part_1 first).
- **Which rule did it:** every sampled document was run again through `teams/01-data-a/spec_v1/clean.py` (English pipeline, then the shared F1 rule), one rule at a time. The rerun gives exactly the published cleaned text for all 35, so each change in the CSV notes names the rule that made it.
- **Labels:** first drafted from that rerun, then checked by the reviewer reading each raw and cleaned pair in full in the viewer (`read` = full 35); the reviewer's changes are in the CSVs.
- **Pack-wide counts:** the same rerun over every dropped document in both parts (559 drops), to size each finding beyond the sample.
- Not done: decoding the sampled documents from the corpus shards.

## Summary

| Verdict | Docs |
|---|---:|
| clean | 14 |
| fix | 9 |
| drop | 0 |
| Dropped by cleaning: drop looks right or acceptable | 6 |
| Dropped by cleaning: drop looks wrong | 6 |
| **Total** | **35** |

Mojibake, stray tags, foreign-language title lines, "Skip to main content" lines and real email addresses are handled well. The problems are in the drops (6 of 12 sampled drops look wrong), in the phone mask (numbers masked that are not phones, and phones left unmasked), and in boilerplate left behind (4 kept documents).

## 1. Good documents dropped as "truncated" (DA-C3-003) (4 in the sample)

**What it is.** DA-C3-003 drops the whole document when its last word is a "dangling" word (a, the, on, of, that ...) and it does not end in `. ! ? " ' ) :`. In this pack that hits complete articles for three reasons:
- a footer line at the end ("Share this page on"): the article is complete; only the last line is boilerplate;
- one cut-off last sentence after pages of good text ("... prior to seed germination. A");
- a curly closing quote: `worked on.”` does not count as an ending, because the rule lists only the straight quotes `"` and `'`.

**How big it is.** DA-C3-003 makes 392 of the 559 drops in the two parts. 268 of those documents are 2,000 characters or longer; 28 end in a curly closing quote (’ or ”); 32 end in the "[…]" marker, which is the case the rule is right about.

**What to do.**
1. Add `”` and `’` to the end punctuation (a clear false positive, small enough for the freeze).
2. For v1.1: when the document is long, cut the last line or partial sentence instead of dropping the document; keep the drop for short fragments and for the "[…]" marker.

| Part | doc_id |
|---|---|
| Part_1 | `40fb0256c0b2c8fe` |
| Part_1 | `eeadc959d809b46e` |
| Part_1 | `0309ba9879105216` |
| Part_2 | `5716019c1d54b86c` |

## 2. A long article dropped for one ad line (DA-D4-001) (1)

**What it is.** DA-D4-001 drops any document that contains "essay writing service" (or spintax). On ukessays.com a 21,000-character anatomy lab write-up has one inline ad ("... using our Essay Writing Service!"), so the whole write-up was dropped.

**How big it is.** DA-D4-001 makes 60 drops in the two parts; 30 of them are 5,000 characters or longer, which is unusual for an essay-mill page.

**What to do.** For v1.1: when the phrase sits in a short line inside a long document, remove that line (C1) instead of dropping; keep the drop for short pages.

| Part | doc_id |
|---|---|
| Part_1 | `bdacc614dc1007a6` |

## 3. Table or code output read as a keyword line (DA-C5-002) (1)

**What it is.** DA-C5-002 drops a document with any line of 7 or more `|`-separated fields. A Raspberry Pi tutorial prints SQLite query output (`1|22.1|2013-10-08 2|...`), which matched.

**How big it is.** DA-C5-002 makes 56 drops in the two parts.

**What to do.** Do not count lines with digits in most fields, or lines inside code, as keyword lines.

| Part | doc_id |
|---|---|
| Part_1 | `1781746e90858653` |

## 4. The phone mask: wrong numbers masked, real phones missed (DA-F1-005) (4)

**What it is.** Two opposite errors.
- **Masked, but not a phone (2).** The pattern (2 to 4 digits, a separator, 3 to 4 digits, a separator, 3 to 4 digits) also matches parts of journal DOIs (`10.1034/j.1399-3054.1998...`) and runs of years (`1933 1934 1935`). Both became `<PHONE>`, which corrupts citations and tables.
- **A phone, but not masked (2).** International numbers with more groups than the pattern allows were masked only in part, leaving the last digits, or not at all. In a contact block, two staff phone numbers written without separators or in 4-2-4 groups were left as they are, next to the staff names (F1). The values are not copied here.

**How big it is.** 139 kept documents in the two parts gained a `<PHONE>` mask; in 25 of them the mask sits inside a DOI. The missed numbers were found by reading; they are not counted pack-wide.

**What to do.** Skip matches inside a DOI (after `10.NNNN/`) and runs of 4-digit years (now). For v1.1, also match whole international numbers (`00` or `+` and the country code, then several groups) and 10 to 11 digit numbers next to "Tel" or "Phone".

| Part | doc_id |
|---|---|
| Part_1 | `c28d662ea8889277` |
| Part_2 | `5fbc8b949d34abb0` |
| Part_1 | `5f7d6fc8766a9c26` |
| Part_1 | `78ad531b7e9e702f` |

## 4a. Boilerplate left after cleaning (C1) (4)

**What it is.** The cleaner removes some page furniture ("Skip to main content", "You May Also Like") but leaves the rest:
- a block of site links in the first lines of a page;
- a "Get the latest version of the Adobe Acrobat reader" footer;
- the related-article titles that followed a removed "You May Also Like" heading;
- a stray "- freely available" label at the top of a paper.

**What to do.** For v1.1: when a C1 rule removes a heading such as "You May Also Like" or "Related", also remove the short title lines that follow it. Add the Acrobat-reader line to the footer patterns.

| Part | doc_id |
|---|---|
| Part_1 | `7bdfe8559c7f7634` |
| Part_1 | `d8ee293d6c80f4cd` |
| Part_1 | `32118f1f0794bd21` |
| Part_1 | `c28d662ea8889277` |

## 5. Repeated section headings removed (DA-C2-003) (2)

**What it is.** Repeated-line removal also removes headings that legitimately repeat, once per section: "Geology and landforms" in a proposal with several wilderness units, "Demand of the question:" before each answer on a UPSC page. Only the first section keeps its heading.

**What to do.** Keep short heading-like lines (no end punctuation, under about 60 characters) when the lines between the repeats differ.

| Part | doc_id |
|---|---|
| Part_2 | `ffe9a2072a43aa0e` |
| Part_2 | `97cc11bc7799273a` |

## Smaller notes

- DA-B4-007 deleted an author's own sentence, "The text does not say.", from a Bible commentary: its pattern for rewriter meta-comments also matches ordinary prose. Small loss.
- DA-C5-005 removes "Keywords:" lines from papers and abstracts. Harmless, though they are metadata rather than SEO.

## Proposals, in order

| # | Rule | Change | When |
|---|---|---|---|
| 1 | DA-C3-003 | Count `”` and `’` as end punctuation | now (clear false positive) |
| 2 | DA-F1-005 | Do not mask inside DOIs or runs of years | now (clear false positive) |
| 3 | DA-C5-002 | Exempt numeric table or code-output lines | now (clear false positive) |
| 4 | DA-C3-003 | Trim the last line of a long document instead of dropping it | v1.1 |
| 5 | DA-D4-001 | Remove a short ad line inside a long document instead of dropping it | v1.1 |
| 6 | DA-C2-003 | Keep repeated section headings | v1.1 |
| 7 | DA-F1-005 | Mask whole international numbers and 10 to 11 digit numbers after "Tel" | v1.1 |
| 8 | C1 rules | Remove the title lines after a removed "Related" heading; add the Acrobat-reader footer | v1.1 |
