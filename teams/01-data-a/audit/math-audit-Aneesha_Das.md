# Math packs audit: math-finemath and math-megamath

Reviewer: Aneesha Das (`aneeshads`). Date: 20 Nov 2026. Assignment 11: 22 docs from math-finemath Part_1 and 13 docs from math-megamath Part_1.

Each doc was read side by side in the pack viewer: the raw text (`Cap1-packs`) and the cleaned text (`tokenizer_sample_v0_clean/train`). Each doc is labelled `clean`, `fix` or `drop`, with disease codes from [DISEASES.md](../../../diagnosis/DISEASES.md) and a note. The labels are in this folder:

- [`math-finemath-Part_1-Aneesha_Das.csv`](math-finemath-Part_1-Aneesha_Das.csv) (22 rows)
- [`math-megamath-Part_1-Aneesha_Das.csv`](math-megamath-Part_1-Aneesha_Das.csv) (13 rows)

The cleaner did many things right (email masking, `[math]` to `$`, ligatures, mojibake, HTML line breaks). But only 4 of the 35 docs are clean after cleaning. The main problems, most serious first:

1. **Cleaning removed real content.** In megamath, reference entries with six or more authors are deleted, leaving empty numbered slots: 421 lines in 70 docs across the pack. In finemath, the rule that removes repeated lines also removes repeated formula lines from worked solutions.
2. **Personal data left in.** Emails written as `name (at) gmail (dot) com` or `name at domain dot com` are not masked: 840 in 37 megamath docs. Phone numbers and an office address are also left.
3. **Boilerplate left in (C1), in 26 of 35 docs.** When a junk line repeats, the cleaner often removes every copy but the first. Junk that appears once (footers, signatures, site buttons) is not touched.
4. **Spam and non-math pages kept.** 7 docs the cleaner kept should be dropped.

## Inputs and method

| Input | File | SHA-256 |
|---|---|---|
| Raw finemath | `Cap1-packs/math-finemath/Part_1/part-00000.parquet` | `a5dbb4da6d0c2e890901aecb10b5c2bd71378d8e66e5975adc0d7d98592f51b2` |
| Cleaned finemath | `tokenizer_sample_v0_clean/train/math-finemath/part-00000.parquet` | `7b3366baf9b8b756eb8b8579940918cbc4cd5eac7b54394e639a722ce117d339` |
| Raw megamath | `Cap1-packs/math-megamath/Part_1/part-00000.parquet` | `e8c53baf0e1c842d303199b93cc36768199edbc64a142925df890915c4cb7d91` |
| Cleaned megamath | `tokenizer_sample_v0_clean/train/math-megamath/part-00000.parquet` | `152c811a29bdd254f4c8778553222b6dcc5df04081267bba69d82345c3c87715` |

- **Viewer:** `diagnosis/tools/view_packs_hub.py` on branch `g1-web-viewer-pre-post` of `patilvijay23/era-v5-lab`, commit `be1571f`, with "Only changed" and "Random next" on.
- **Sample:** only docs the cleaner changed or dropped. One finemath doc was picked in the viewer. The other 34 were drawn at random, with a fixed seed, from the changed or dropped docs of each pack.

  | Pack | Docs | Changed | Dropped by cleaner | Reviewed |
  |---|---:|---:|---:|---:|
  | math-finemath | 29,122 | 8,361 | 600 | 22 |
  | math-megamath | 17,647 | 1,739 | 13 | 13 |

- **Reading:** 34 docs read in full. One doc (`01cbee543c7751fd`, 31,000 characters of SEO spam) was read at the start, middle and end, and is marked `partial`.
- **Labels:** `read`, `verdict`, `diseases` and `note` are filled in. `evidence` and `hex` are left empty, as the audit instructions ask. Offsets in the notes are character positions in the cleaned text ("post offset").
- **How the labels were made:** drafted with an AI assistant (Claude) from the full raw and cleaned text, then checked by the reviewer.
- **Whole-pack counts:** the "How big it is" numbers below come from a short script that compares the raw and cleaned text of every doc in the pack, line by line. They are pattern counts, not hand-checked labels.
- **Personal data:** no email address, phone number or address is copied into this report or the label files. Only the position is given.

This audits the `tokenizer_sample_v0_clean` copy named in the audit instructions. The [D3 report](https://github.com/theschoolofai/era-v5-lab/blob/main/teams/01-data-a/audit/day_D3.md) notes that this older copy can differ from the frozen p1536 shard output, so these findings have not been checked against the shards. 35 docs is a small sample, not a quality estimate for the whole pack.

## Summary

| Pack | Reviewed | Dropped by cleaner | clean | fix | drop |
|---|---:|---:|---:|---:|---:|
| math-finemath | 22 | 3 | 4 | 12 | 6 |
| math-megamath | 13 | 0 | 0 | 9 | 4 |
| **Total** | **35** | **3** | **4** | **21** | **10** |

`drop` includes the 3 docs the cleaner already dropped (the reviewer agrees). The other 7 `drop` docs were kept by the cleaner and should be dropped.

| Disease | finemath | megamath | Docs |
|---|---:|---:|---:|
| C1 boilerplate | 16 | 10 | 26 |
| C2 repeated lines | 1 | 5 | 6 |
| C5 keyword lists, SEO spam | 3 | 2 | 5 |
| C3 truncated (all three dropped Course Hero previews) | 3 | 0 | 3 |
| C4 several documents joined | 1 | 2 | 3 |
| A3 mojibake | 1 | 2 | 3 |
| F1 personal data | 0 | 3 | 3 |
| A4 replacement character U+FFFD | 1 | 1 | 2 |
| B2 markup tags | 1 | 1 | 2 |
| B5 broken LaTeX | 0 | 2 | 2 |
| E2 data blob (raw PDF bytes) | 0 | 1 | 1 |
| Content removed by cleaning (no code fits; in the note) | 1 | 3 | 4 |

A doc can have several diseases, so the counts overlap. C1 and C2 are each found more than five times, so they need a medicine sheet (DISEASES.md section 4).

## Content removed by cleaning (4 docs)

**What it is.** Cleaning deleted real content. No disease code fits damage done by cleaning to English text (the G codes are for Indic), so these rows describe it in the note.

**Reference entries with six or more authors are deleted.** The entry is removed but its number stays, so the reference list has empty slots. In `f079a0d75820b184`, 12 entries are gone (slots 3–8, 10–11, 13–15 and 19), including reference 4, which the Methods section points to for the growth details. In `0cb915d7762c2e45`, the one deleted entry is the paper's own method, cited 4 times in the text. In `27c5838098758c5b`, two article entries lost their author lines.

**How big it is.** Across math-megamath, 421 reference lines with six or more authors were removed, in 70 docs. In math-finemath, 1 line.

**Repeated formula lines are deleted.** In `89dc8e7278ce1f4b`, the formula line `P(E) = n(E)/ n(S)` starts each worked probability solution. The rule that removes repeated lines kept the first copy and deleted the other 4, so solutions Q12 to Q15 now go from `n(E)` straight to the answer.

**How big it is.** Across math-finemath, 755 docs had a repeated line containing `=`, `^`, `$` or a LaTeX command deleted while one copy was kept (5,412 lines). Not all of these are formulas, so this is an upper bound that needs a spot-check. In math-megamath, the repeated-line rule changed only 3 docs.

**Email masking also removes nearby words.** In `0ef68457f8488afa`, the mask swallowed the last word of many comments together with the commenter name (`way better <EMAIL>`). The doc is a drop anyway, but the same rule runs on every doc.

**What to do.** Run the current `clean.py` on these docs to find the rule that deleted each line. Then:
- Exempt reference lists from the rule that removes author lists.
- Limit the repeated-line rule to boilerplate-like lines (short, no math symbols), or to lines repeated next to each other.
- Make the email pattern stop at word boundaries.

## Personal data left in (F1) (3 docs)

**What it is.** Plain emails were masked to `<EMAIL>` correctly in every doc where they appeared. But emails written in a disguised form were not, and phone numbers were not masked at all.

- `4258f5c9fbf14805`: 73 emails written as `(at) … (dot) com` or `at … dot com`, first at post offset 3070, with commenters' full names and social-media links.
- `31c47797e0ec552c`: a 1996 mailing-list signature with a name, an office address and a phone number (post offset 1669).
- `27c5838098758c5b`: a research group's office phone number (post offset 390). This is a judgement call: it is a work number on a public page.

**How big it is.** Across math-megamath, 840 disguised emails are left in 37 docs. Across math-finemath, 7 in 6 docs.

**What to do.** Extend the F1 rule to the `(at)`/`(dot)` and `at … dot` forms and to phone numbers. Check it against the gold set for harm before adopting it.

## Boilerplate left in (C1) (26 docs)

**What it is.** Site chrome is left in the cleaned text: forum badges, sign-in prompts, Q&A site buttons, archive headers and footers, empty page labels from journal sites, and signatures.

**Pattern.** In 5 docs, the cleaner removed every copy of a repeated junk line except the first:

| doc_id | Junk line | Removed |
|---|---|---|
| `03adce6b428657cc` | `Quick Reference:` | 5 of 6 |
| `b1efb7907a0c8cbb` | `Please Log in or Create an account to join the conversation.` | 9 of 10 |
| `caec68d5a4dc4373` | `Homework Helper` | 10 of 11 |
| `e45925da5672827e` | `Standard: MATH 1` | 5 of 6 |
| `73670428f7373dee` | `by Subhotosh Khan` | 4 of 5 |

Junk that appears only once is not touched: `Join BYJU'S Learning Program`, `Post a followup to this message`, `Moderators: …`, wiki `[edit]` labels, and journal labels such as `Received / Accepted / Published`.

**What to do.** When a line is judged boilerplate, remove every copy, not all but one. Add patterns for the site chrome above. Since C1 is found in 26 docs, write a medicine sheet for it.

## Spam and non-math pages kept (7 docs)

**What it is.** The cleaner kept these docs and made only small fixes. They should be dropped.

| Pack | doc_id | Why drop |
|---|---|---|
| math-finemath | `73670428f7373dee` | Forum search results: thread titles, views and last-post dates, no math (C5) |
| math-finemath | `e45925da5672827e` | Worksheet catalogue, almost no math; 2 U+FFFD (C5, A4) |
| math-finemath | `01cbee543c7751fd` | SEO spam stitched from many sites; ends with a clothing ad (C5, C4) |
| math-megamath | `41f03ba56962c1e9` | SEO sentence soup, 51,000 characters in 2 lines (C5, C4, C2) |
| math-megamath | `9cb311703c53c1e0` | SEO spam mixed with raw PDF bytes; 179 U+FFFD (C5, C4, E2, A4) |
| math-megamath | `4258f5c9fbf14805` | Kids' film giveaway, not math; 73 unmasked emails (F1) |
| math-megamath | `0ef68457f8488afa` | Raw Blogger feed of a parent discussion on school placement |

**What to do.** These need a doc-level rule (keyword density, share of PDF syntax or U+FFFD, topic). Check any new drop rule against the gold set.

## Characters and markup left in (8 docs)

- **A3 mojibake:**
  - `94c0014436db12b5`: one mojibake was fixed, but the broken emoji `đź™‚` is left at post offset 9633.
  - `9cb311703c53c1e0`: `FØlix Muæoz-García`.
  - `41f03ba56962c1e9`: `ááá`, `¥` and `آ` from PDF fonts.
- **A4 U+FFFD:**
  - `e45925da5672827e`: 2.
  - `9cb311703c53c1e0`: 179.
- **B2 markup:**
  - `caec68d5a4dc4373`: a BBCode `[ATTACH]` tag.
  - `32d96679ed59c9d5`: a MediaWiki diff header with raw `<math>` tags, `'''bold'''` markup and 44 lines of `− | |||`.
- **B5 broken LaTeX:**
  - `0cb915d7762c2e45`: `\left{c}_{\ell}\right}` lost its `|`.
  - `31c47797e0ec552c`: a broken TeX accent `Riec\u can`.
- **E2:** `9cb311703c53c1e0` contains raw PDF object syntax and bytes.

## Dropped by cleaning (3 docs, finemath)

All three are Course Hero paywall previews. The drop is right. They are labelled `drop` with C1 and C3, and their notes start "No matching doc_id".

| doc_id | Verdict | Note |
|---|---|---|
| `b5b886b63aeb9e2e` | drop | Signals homework preview; formulas garbled in extraction; cut off after page 5 |
| `67f407a0ccd09d74` | drop | Finance lecture problems; `{[ promptMessage ]}` template junk and paywall text. Borderline: the worked solutions were usable |
| `6df989a2bcd44389` | drop | Fluids textbook preview; equations lost their symbols; testimonials |

## What the cleaner did right

- Plain emails masked to `<EMAIL>` (megamath), including in C code headers.
- `[math]…[/math]` converted to `$…$` (179 pairs in `32d96679ed59c9d5`).
- Ligatures `ﬁ`, `ﬀ` and `ﬂ` replaced with `fi`, `ff` and `fl`.
- Mojibake `â€™` fixed to `’`.
- `<br />` turned into line breaks and `<i>` removed.
- Zero-width spaces removed.
- Jiskha `posted by .` lines removed.
- A paragraph repeated inside a forum quote removed, which does no harm (`11c56a701b6c6f82`, `c87c76a202bf9370`).

## Per-doc findings

### math-finemath (22)

| doc_id | Cleaner | Verdict | Diseases | Finding |
|---|---|---|---|---|
| `caec68d5a4dc4373` | changed | fix | C1;B2 | Physics forum. Badges left (`Gold Member` x20, `2022 Award` x7), BBCode tag |
| `6df989a2bcd44389` | dropped | drop | C1;C3 | Course Hero preview. Drop right |
| `4376102f99b2fdfd` | changed | fix | C1 | Jiskha. `Answer This Question` footer left |
| `1fbf0a290e52e534` | changed | clean | — | Mojibake fixed, breadcrumb removed. Source flattens exponents (`x2 = 4`) |
| `1e700ddf3f3e4e0d` | changed | clean | — | `posted by on .` removed correctly |
| `73670428f7373dee` | changed | drop | C5;C1 | Forum search results, no math |
| `c87c76a202bf9370` | changed | fix | C1 | Forum signature left |
| `94c0014436db12b5` | changed | fix | A3 | Broken emoji left at post offset 9633 |
| `4dd13476a6af3f3f` | changed | clean | — | `posted by .` removed correctly |
| `b5b886b63aeb9e2e` | dropped | drop | C1;C3 | Course Hero preview. Drop right |
| `411aeec06d260b92` | changed | fix | C1 | Game buttons and Twitter testimonials left |
| `fd90a7692cbe0dda` | changed | fix | C1 | BYJU'S UI left |
| `67f407a0ccd09d74` | dropped | drop | C1;C3 | Course Hero preview. Borderline |
| `a878064814cc3108` | changed | fix | C1 | `Similar Questions` link list left |
| `e45925da5672827e` | changed | drop | C1;C5;A4 | Worksheet catalogue; 2 U+FFFD |
| `21bfa34841bcc936` | changed | fix | C2 | Three figure lines still doubled; OCR errors in source |
| `01cbee543c7751fd` | changed | drop | C5;C4;C1 | SEO spam. Read `partial` |
| `89dc8e7278ce1f4b` | changed | fix | C1 | Formula line deleted from 4 of 5 solutions; `darkmode` left |
| `03adce6b428657cc` | changed | fix | C1 | `Quick Reference:` removed 5 of 6 times; page UI left |
| `b1efb7907a0c8cbb` | changed | fix | C1 | Sign-in prompt removed 9 of 10 times; forum footer left |
| `11c56a701b6c6f82` | changed | clean | — | Repeated paragraph in a quote removed; harmless |
| `76718c4a528f2cee` | changed | fix | C1 | answers.com UI left; low value |

### math-megamath (13)

| doc_id | Cleaner | Verdict | Diseases | Finding |
|---|---|---|---|---|
| `32ce96905cc39b34` | changed | fix | C1 | Good GLPK page with C code; emails masked; 9 `[edit]` labels left |
| `0ef68457f8488afa` | changed | drop | C1;C2 | Raw Blogger feed; masking ate nearby words |
| `4258f5c9fbf14805` | changed | drop | F1;C2;C1 | Giveaway, not math; 73 unmasked emails |
| `c2014b24148deb41` | changed | fix | C2;C1 | Good thread, but every post appears twice; one list repeated 8 times |
| `9cb311703c53c1e0` | changed | drop | A4;A3;E2;C4;C5 | SEO spam with raw PDF bytes |
| `31c47797e0ec552c` | changed | fix | F1;C1;B5 | Email masked, but phone and office address left in signature |
| `0cb915d7762c2e45` | changed | fix | C1;B5 | Key reference deleted; broken LaTeX |
| `32d96679ed59c9d5` | changed | fix | C1;C2;B2 | Good Polymath math; wiki diff header left |
| `f079a0d75820b184` | changed | fix | C1 | 12 reference entries deleted |
| `27c5838098758c5b` | changed | fix | F1 | Office phone left; 2 author lines deleted |
| `41f03ba56962c1e9` | changed | drop | C5;C4;C2;A3 | SEO sentence soup |
| `edfafeaa35e38bc9` | changed | fix | C1 | Good Usenet post; archive header and footer left |
| `ca8e91121e85235c` | changed | fix | C1 | Good Usenet post; archive header and footer left |

The full note for each doc is in the label CSVs.

## Follow-up

1. Run the current `clean.py` on the 4 over-cleaned docs and name the rule behind each deletion (author-list removal, repeated-line removal, email masking).
2. Spot-check the 755 finemath docs where a repeated formula-like line was deleted, to see how many lost real math.
3. Check the F1, C1 and over-cleaning findings against the p1536 shard output before proposing changes to the frozen spec.
4. Write medicine sheets for C1 (26 docs) and C2 (6 docs), with the gold-set harm test. A medicine that changes or drops more than 1% of the gold set fails.
5. Arrange the second-reader check of 10% of these docs (4 of 35).
