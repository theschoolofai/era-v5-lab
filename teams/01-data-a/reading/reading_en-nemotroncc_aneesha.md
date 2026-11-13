# English reading audit (task 7): en-nemotroncc

Reader: Aneesha Das. Row 7 of the Week 2 assignments, en-nemotroncc (50 docs).
The findings are in `reading_en-nemotroncc_aneesha.csv`: 52 findings in 26 docs. The other 24 docs were read and had no finding, so they have no rows; all 50 doc_ids are listed at the end.

## How it was read

- **Pack files:** tokenizer sample v0-clean, `train/en-nemotroncc/part-00000.parquet` (Part 1, 35 of the 50 docs) and `train/en-nemotroncc/part-00001.parquet` (Part 2, 15 docs).
- **Cleaner:** spec v1 `clean.py` as run by TSAI on #244. The English family runs 20 rules (`DA-A1-004` to `DA-F1-005`).
- **Seed and pick:** <!-- TODO: how the 50 doc_ids were picked (pick_docs.py with seed 20261101 and --rows ..., or a list handed over) -->
- **Docs read:** 50, all in full.
- **AI used:** no. Every row was found and written by the reader (`source` is `manual` on all rows). A local browser app was used only to show the cleaned text and record the offsets.
- **Offsets:** code points in the cleaned text, end exclusive.
- **Private data:** no F1 or E3 row in this read.

## Method

Each doc was read in full in the cleaned text and every problem was logged as one row. Each row was checked against `specv1.md` and the English sheets (`medicine_english.md`, `decisions_english.md`): a disease an English rule covers is `missed`, one no English rule covers is `new`.

## Findings table

27 missed findings in 15 docs, 25 new in 15 docs, 0 harm. 24 docs had no finding.

| code | kind | docs affected | % of docs read |
|---|---|---|---|
| C1 | missed | 12 | 24% |
| C3 | missed | 6 | 12% |
| B1 | missed | 1 | 2% |
| D3 | missed | 1 | 2% |
| NEW-missing-spaces | new | 2 | 4% |
| NEW-abstract-with-no-paper-behind-it | new | 1 | 2% |
| NEW-ad-disguised-as-an-article | new | 1 | 2% |
| NEW-clickbait-and-promotional-tone | new | 1 | 2% |
| NEW-footnote-whose-main-content-is-missing | new | 1 | 2% |
| NEW-grammar-error | new | 1 | 2% |
| NEW-header-details-stripped | new | 1 | 2% |
| NEW-heading-stuck-to-the-paragraph | new | 1 | 2% |
| NEW-hyphen-split-words | new | 1 | 2% |
| NEW-leftover-hyphens-from-line-breaks | new | 1 | 2% |
| NEW-mismatched-quotation-marks | new | 1 | 2% |
| NEW-missing-space-after-a-full-stop | new | 1 | 2% |
| NEW-old-place-name-spelling | new | 1 | 2% |
| NEW-pronoun-slip | new | 1 | 2% |
| NEW-spliced-sentences | new | 1 | 2% |
| NEW-squashed-into-prose | new | 1 | 2% |
| NEW-text-describing-a-missing-video | new | 1 | 2% |
| NEW-text-with-the-link-gone | new | 1 | 2% |
| NEW-too-few-words | new | 1 | 2% |
| NEW-two-pieces-stuck-together-with-no-space | new | 1 | 2% |
| NEW-two-words-stuck-together | new | 1 | 2% |
| NEW-typos-and-grammar-errors | new | 1 | 2% |

## Top findings

- **C1 boilerplate kept (12 docs, 19 rows):** site navigation and labels ("Pages", "Categories", "Uncategorized", "Main menu", "Sermons", "Learn More", "read more..."), an advert line, a streaming promo line, a related-stories block, and in one doc six slide-viewer field labels ("Slide Title", "Photographer/Creator", "Preview", "Date", "Description"). `DA-C1-006` is the English C1 rule.
- **C3 truncated docs kept (6 docs):** the text stops in the middle of a sentence. `DA-C3-001` and `DA-C3-003` are the English C3 rules.
- **D3 and B1 (1 doc each):** Navajo words mixed into English text; a leftover "Coming up: ( - )" fragment logged as B1.
- **New candidates:** 22 names, each in 1 doc except `NEW-missing-spaces` (2 docs). Several names describe text run together with no space or line break (see open question 1).

## New diseases

| name | description | docs |
|---|---|---|
| `NEW-missing-spaces` | space missing between words or after a full stop | 2 |
| `NEW-two-words-stuck-together` | no space between two words | 1 |
| `NEW-two-pieces-stuck-together-with-no-space` | two pieces of text run together with no space | 1 |
| `NEW-missing-space-after-a-full-stop` | no space after a full stop | 1 |
| `NEW-heading-stuck-to-the-paragraph` | a heading run into its paragraph; the line break is missing | 1 |
| `NEW-squashed-into-prose` | an agenda whose line breaks and bullets were lost | 1 |
| `NEW-hyphen-split-words` | words split by a line-end hyphen | 1 |
| `NEW-leftover-hyphens-from-line-breaks` | a hyphen left from a line break inside a word | 1 |
| `NEW-spliced-sentences` | the start of one sentence glued onto another | 1 |
| `NEW-mismatched-quotation-marks` | a quote opened with one kind of mark and closed with another | 1 |
| `NEW-text-with-the-link-gone` | the text points to a link (a download) that is missing | 1 |
| `NEW-text-describing-a-missing-video` | the text introduces a video that is missing | 1 |
| `NEW-footnote-whose-main-content-is-missing` | a footnote kept, cut off from the main content it belongs to | 1 |
| `NEW-abstract-with-no-paper-behind-it` | the text refers to "this paper" but no paper is there | 1 |
| `NEW-header-details-stripped` | header details stripped from the text | 1 |
| `NEW-too-few-words` | the doc is a single word | 1 |
| `NEW-clickbait-and-promotional-tone` | clickbait wording | 1 |
| `NEW-ad-disguised-as-an-article` | a promotion inside an article | 1 |
| `NEW-typos-and-grammar-errors` | Iran called Iranian ("Iranian capitol") | 1 |
| `NEW-grammar-error` | wrong grammar | 1 |
| `NEW-pronoun-slip` | the person addressed is unclear | 1 |
| `NEW-old-place-name-spelling` | an old spelling of a place name (Kiev for Kyiv) | 1 |

Over the 1% line (2+ docs of 200 in the English domain): `NEW-missing-spaces` (2 docs). The other names are at 1 doc in this read and need a second doc from another English reader. `NEW-missing-spaces` and `NEW-hyphen-split-words` are names already used in the math and science audits (`spec_v1_1/sheets/NEW_DISEASES.md`).

## Harm

None found. No row in this read shows a spec v1 rule removing or damaging real content.

## Open questions for the lead

1. Several names describe the same kind of problem. If they are merged before counting, the counts change: text run together with no space (`NEW-missing-spaces`, `NEW-two-words-stuck-together`, `NEW-two-pieces-stuck-together-with-no-space`, `NEW-missing-space-after-a-full-stop`) is in 5 docs; line-break hyphens (`NEW-hyphen-split-words`, `NEW-leftover-hyphens-from-line-breaks`) in 1 doc; grammar (`NEW-grammar-error`, `NEW-typos-and-grammar-errors`) in 2 docs. Merge, or keep them apart?
2. <!-- TODO: your own questions, or delete this line -->

## Doc IDs read (reading order)

```
a5beaed27fce57f4
d3930e8efd7f2875
514f19df31264866
6a83fe15c96d7ef7
21b3a60a70d8e8e3
c2a1accfe1ee73c1
7e9b50b5ec7bae5e
1f9b5ac7201191fd
8e878c3f109876a1
6846c04d749df61b
e959f68211479a14
986032c30098ab9b
746c2f5a2d03df38
012f59fe9357a1d2
e956f775c244329d
c0141829a89b70e5
55c4e02d60b8025f
b24b48e571bb8579
c29476cba55fb465
31578015b87b9c76
a9ff7424b805a6b7
91ec00ec7f982d18
062af6dbb5c7bd1c
2feb05980d7d894a
d98136cee53ef137
c6b63cdcd44135d7
6c2d2df1767f0ff5
373cc7193cbdc3bd
d88d5ae0f0d8163e
ac425325b462b50e
da1284ff5b1a26e9
cfa8295d1ae741dd
bf517e0acba00792
49aa8d9c7242b94d
11878b0609eb47c3
4531052708320471
05a83252d55fc98d
be70a0b5686b443e
a466d07d4f672a69
8e521ac6452018d2
502ee3da08920d31
9a2b400c34a5802f
577564a4d05fe06d
1199766d07c144b5
eadb3c4ab96e8ea5
67deb54c4b6d0d75
005b6af570979c96
c816e82b9664794c
e66fcaa6e734db3a
8d8a59cfa7b6bf97
```
