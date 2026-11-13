# Reading audit: en-dclm

Reader: smita. Docs picked by `pick_docs.py` (seed 20261101, rows 1-50 of the shuffled list). The findings are in `reading_en-dclm_smita.csv`: one row per finding, 22 rows in 19 docs. `#N` below is the position of a doc in the reading order (the list at the end).

## How it was read

- **Pack files:** tokenizer sample v0-clean, `train/en-dclm/part-00000.parquet` (45,369 docs, sha256 `34fdfc28…`) and `part-00001.parquet` (14,843 docs, sha256 `0674a7af…`): 60,212 docs in all, Part 1 then Part 2.
- **Seed and pick:** 20261101, the `pick_docs.py` method, rows 1-50. The list is at the end of this file. Checked: it is exactly what `pick_docs.py` returns for the two parts in that order.
- **Cleaner:** spec v1 as run by TSAI on #244: `clean.py` sha256 `97c1a55b…` at `8da2ac4`. Re-running that `clean.py` on the raw text of the 50 docs reproduces all 50 cleaned texts exactly: 45 unchanged, 5 fixed.
- **Docs read:** 50. The cleaner changed 5 of them: `DA-C2-003` 2, `DA-A1-004` 1 (a BOM), `DA-B1-002` 1, `DA-C5-005` 1 and `DA-F1-005` 1 (an email). Only the `DA-C2-003` change in `21866f62a874ae46` is recorded as harm: the other four removed page chrome, a tag line, a stray `amp;`, a BOM or an email, as intended.
- **Method:** read by the reader in `view_reading.py`, a local reading page that writes this CSV (built with Claude, Anthropic). 7 rows are `manual`: the first four findings (C2 harm, two F1 phones, the BibTeX record), which the reader found and then assessed with Claude's help, and three C1 widget rows (#18, #32, #44) found and added by the reader. After the first read, Claude made a second pass over the 47 docs with no finding and suggested 21 rows (20 C1, 1 C5). The reader checked each one in the cleaned text: 15 were confirmed and are in the CSV with `source` = `ai` (15 rows); 6 were true but too site-specific to be useful as a general rule and were left out. <!-- TODO: confirm this AI-use wording -->
- **Offsets:** code points in the cleaned text, end exclusive. A harm row can give a point. For F1 rows `quote` is empty and `why` gives the type and offset only. Other quotes are short snippets of page chrome (the BibTeX row quotes only the opening token, not the author names).

## Findings table

22 findings in 19 docs; the other 31 docs were read and have no finding. Kinds: missed 20, new 1, harm 1.

| code | kind | docs affected | % of docs read |
|---|---|---:|---:|
| C1 | missed | 16 | 32% |
| F1 | missed | 1 | 2% |
| NEW-bibtex-record | new | 1 | 2% |
| DA-C2-003 | harm | 1 | 2% |

Where the existing rules miss:

- **C1 (16 docs, 32%):** page chrome left at the end or start of the text. `DA-C1-006` deletes a line only when the whole line is a label from a fixed list (`Share this:`, `Read more`, `Related posts` and a few more), and none of the phrases below are on it.
  - **Comment-login widgets** at the end of blog posts: the WordPress block (`Leave a Reply`, a login prompt, `Twitter picture`, `Facebook photo`, `Google+ photo`, `Connecting to %s`, `%d bloggers like this:`) in #6, #32 and #44, and the LiveJournal block in #18.
  - **Comment and answer forms:** `Leave a Reply` in #8, #9 and #25; `Your Answer` in #12 and #48; `Comments are closed.` in #38.
  - **Site navigation and headers:** a Wikipedia header (#15), a StackExchange tour banner (#48), a category crumb (#8), `• Close Menu` (#16), a site menu row (#17), an author box (#21), a newsletter widget (#30), a page footer template (#40).
- **F1 (1 doc):** `DA-F1-005` replaced the email in a business contact block in #35 but left both phone numbers. Its PHONE pattern needs separators between digit groups and at most 4 digits in the last group, so a country code followed by 11 digits in one block, and a 4-4-7 group number, both pass through.

## New diseases

| name | what it is | docs |
|---|---|---|
| NEW-bibtex-record | the whole doc is one BibTeX citation record on a single line (`@inbook {...}` with author, title, booktitle, publisher, msc2010 and identifier fields); only the abstract, about 66% of the text, is prose | 1 (#47) |

One doc is below the 2-doc bar for this read; it counts toward the combined total.

## Harm

| rule | what it deleted | docs |
|---|---|---|
| `DA-C2-003` | repeated comment-header lines in `21866f62a874ae46` (#11): 9 later copies of `<name> said...` (7 of 8 `Anonymous said...` headers and 2 of 3 for one named commenter). The comments lose who is speaking, and later replies point back at the speaker ("anon says ..."). | 1 |

`DA-C2-003` also removed 2 copies of a repeated `Download the original file` line in `b8060931cadbc90f`. That one is page chrome and the removal is fine.

## Open questions for the lead

1. **C1 labels:** can the phrases in the appendix below be added to the `DA-C1-006` line list? Most sit on a line of their own, so a whole-line match works. `You may also like...` in #9 is already on the list but is not removed, because the pattern allows no dots after `like`.
2. **Widget blocks:** the WordPress comment-login block repeats in 3 of 50 docs (6%). Should it be removed as one block from `Leave a Reply`, rather than label by label?
3. **Format placeholders:** that block also carries unfilled `%s` and `%d` (`Connecting to %s`, `%d bloggers like this:`) in #6, #32 and #44. The English B4 rules do not cover them. Is that B4, or handled with C1?
4. **Site-specific footers:** 6 C1/C5 findings were left out as too specific (a byline, a newsletter promo, an archive link row, a Spanish course footer, a dictionary word list, `Pages: 1 2`). Should those count as missed C1/C5?
5. **DA-C2-003:** limit it so that comment-header lines (`<name> said...`) are kept?
6. **DA-F1-005 PHONE pattern:** accept long unbroken mobile numbers and a 7-digit last group?
7. **No-break spaces:** U+00A0 is in 24 of 50 docs (251 occurrences, none removed). It is not in the A1 list or in `DA-A1-004`, and `DA-B1-002` maps the `&nbsp;` entity to a plain space but not the literal character. Is it a disease for the tokenizer, or left as is? (The week-1 labels for cadj-stackexchange marked it A1.)

## Appendix: C1 phrases left in the cleaned text

Phrases found left over in the cleaned text, with the number of the 50 docs that contain them. The doc numbers are reading-order positions; `(CSV)` means the doc is in the findings CSV for it. A rule that removes a whole line equal to one of these would not touch running text.

| phrase (own line unless noted) | docs | where |
|---|---:|---|
| `Leave a Reply` / `Leave a reply` | 6: #6, #8, #9, #25, #32, #44 (CSV, all) | end of post |
| `Log Out / Change )` with `You are commenting using your account.` | 2: #6, #32 (CSV, both) | end |
| `Twitter picture`, `Facebook photo`, `Google+ photo` / `Google photo` | 3: #6, #32, #44 (CSV) | end |
| `Connecting to %s` | 3: #6, #32, #44 (CSV) | end |
| `%d bloggers like this:` | 2: #32, #44 (CSV) | end |
| `WordPress.com Logo`, `Get every new post delivered to your Inbox.` | 1: #44 (CSV) | end |
| `Post a new comment`, `Comments allowed for members only`, `Anonymous comments are disabled in this journal`, `default userpic`, `Your IP address will be recorded` | 1: #18 (CSV) | end (LiveJournal) |
| `Your Answer` | 2: #12, #48 (CSV) | end |
| `share|improve this answer add comment Your Answer`, `Take the 2-minute tour ×` | 1: #48 (CSV) | end, start (StackExchange) |
| `Comments are closed.` | 2: #38 (CSV), #50 | end |
| `You may also like...` | 1: #9 (CSV) | end |
| `• Close Menu` | 1: #16 (CSV) | end |
| `Top Back Home Web Statistics` | 1: #17 (CSV) | end |
| `About the Author Photo Credits` | 1: #21 (CSV) | end |
| `Sign up to our newsletter Newsletter Preferences` | 1: #30 (CSV) | end |
| `From Wikipedia, the free encyclopedia Jump to: navigation, search` | 1: #15 (CSV) | start |

Found but not in the CSV: `Comments are closed.` in #50 (end of the text), and the 6 site-specific items from question 4.

## Doc IDs read (reading order)

```
7e7f285784a8f6cb a08dc72d2c17181f b8060931cadbc90f 9f9fea0d4c9a59c4 521be92d60c7d8b6
0b9075e915ffceac a50456e30ae6668d dec657da5609fd56 c2a7eaeb2b784189 709ce270bd1f6b04
21866f62a874ae46 13eaa07ada811509 3be5e12aa5059557 19018bd2e2055b79 2287fd9e465fdbef
19557aba45b99172 c6565d3fa99ecdf4 b30b6cbd053b962e 430f380475e09005 f901e751f10ddabc
cd61bed30779f726 93e6bff9aae918d0 e466807c9b4b211f 49199ad150ffaf5c 18ee2d2741be1cdb
fa9d2322f3e9167d 0b9bc040037e2ef6 606c63ca57e354dc 30397f0912751606 8a44dc21a6065507
72e7cf6f1feed2bd c5a8f9d8fc3ac30f e28e9df5648fab30 a623cfa6b5c434a3 6b35cf6dc52ed772
0f84775543b81ee3 9fc9481b12978ce6 7559294831c4ff58 d6eaec7b52e8cc14 6ad54ee8d7a97abe
0dd6028065f67d5e 0fb9e5978f437c7e 7425ae309f3fee04 ca99e6d44576a2c2 26686651c1faf11b
59c1fd082f2ad0d7 f0bdeaae299d2822 6ea66e2255976696 43540eb19f496f8f d7289ffe9209e8f8
```

Docs with no finding (no rows), 31: `7e7f285784a8f6cb`, `a08dc72d2c17181f`, `b8060931cadbc90f`, `9f9fea0d4c9a59c4`, `521be92d60c7d8b6`, `a50456e30ae6668d`, `709ce270bd1f6b04`, `3be5e12aa5059557`, `19018bd2e2055b79`, `430f380475e09005`, `f901e751f10ddabc`, `93e6bff9aae918d0`, `e466807c9b4b211f`, `49199ad150ffaf5c`, `fa9d2322f3e9167d`, `0b9bc040037e2ef6`, `606c63ca57e354dc`, `30397f0912751606`, `72e7cf6f1feed2bd`, `e28e9df5648fab30`, `a623cfa6b5c434a3`, `0f84775543b81ee3`, `9fc9481b12978ce6`, `d6eaec7b52e8cc14`, `0dd6028065f67d5e`, `0fb9e5978f437c7e`, `7425ae309f3fee04`, `26686651c1faf11b`, `59c1fd082f2ad0d7`, `43540eb19f496f8f`, `d7289ffe9209e8f8`.
