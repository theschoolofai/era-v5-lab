# KE2 request R1: word-frequency tables of the 38 sample packs

**Answer.** 21 tables, one per language and lane, of every word in the train split of the 38 sample-v0 packs (all
1,430,307 train documents, 48 parts), as `word,count,lang,lane`. 488.6 MB as CSV, 82 MB gzipped; shared by link (below),
not committed, since they are over pr-guard's 5 MB limit. Their sha256 values are in `results/r1/r1_summary.json`.

Requested by Team 4 (KE2) for Lab 5 design task 00 (spelling, new words, rare words): R1 of
`teams/04-ke2/new-units/data_request_teams_1_2.md`, "word frequency table of the training shards (or the 38 sample
packs)". R5 (rare and long Indic words) is Team 2's; these tables already hold every count from 1 up.

## The word rule

1. The text is put in **NFC**, the lab's only normalization: no NFKC, no case folding.
2. A **word** is a maximal run of Unicode letters and combining marks (categories `L*` and `M*`), so Indic vowel signs,
   viramas and nuktas stay inside the word. ZWJ (U+200D) and ZWNJ (U+200C) belong to a word when letters or marks stand
   on both sides; at a word's edge they are dropped.
3. **Everything else separates words:** digits, `_`, apostrophes, hyphens, punctuation, symbols and spaces.
   `don't` is `don` + `t`, `x_velocity` is `x` + `velocity` (identifiers as written are R3's), `COVID-19` is `COVID`.
4. **Case is kept as written:** `The` and `the` are counted apart.

The pattern is `[\p{L}\p{M}]+(?:[‌‍]+[\p{L}\p{M}]+)*` (Python `regex`), after `unicodedata.normalize("NFC")`.

## What was counted

- **Input:** sample v0's raw train parts, the 38 packs of `approved_inputs.json`, **before cleaning, dedup and F2**.
  corpus-v1's shards are not out yet; `word_freq.py` reruns on its cleaned parts when they land (about 5 minutes for a
  sample-sized set on 2 cores). Every part is checked against the sample-v0 manifest's sha256 and row count, and a
  missing or changed part stops the run.
- **Held-out parts are not read:** they are text that no training shard holds (R2).
- **Language and lane** come from `approved_inputs.json`, as on the shard manifests. For code packs the language is the
  programming language and the lane `code`; the code-adjacent packs are `code` (commits, notebooks) or `en`
  (StackExchange).
- **Licence:** `results/r1/packs.csv` lists the packs behind each table with their source, licence and licence source
  (KE2's licence column, once per pack rather than on every word row).
- **Only words and counts** leave the packs: no document, sentence or doc_id is written.

## The tables

| Table | Packs | Words | Distinct | Count ≤ 10 | Over 32 bytes | sha256 |
|---|---:|---:|---:|---:|---:|---|
| `code__cpp.csv` | 1 | 37,878,730 | 1,119,226 | 969,547 | 16,703 | `9637665ca244…` |
| `code__go.csv` | 1 | 41,490,028 | 1,283,215 | 1,153,676 | 42,368 | `bfc2a887a002…` |
| `code__java.csv` | 1 | 32,999,450 | 1,386,815 | 1,249,194 | 43,116 | `7e33884a33ee…` |
| `code__js-ts.csv` | 1 | 32,104,998 | 1,287,004 | 1,175,057 | 21,698 | `310033352299…` |
| `code__python.csv` | 1 | 40,380,322 | 721,775 | 633,843 | 11,636 | `707a12c02086…` |
| `code__rust.csv` | 1 | 38,761,081 | 461,029 | 384,693 | 7,047 | `722405371172…` |
| `code-adjacent__code.csv` | 2 | 34,051,841 | 549,049 | 465,492 | 8,724 | `163c0e5a9341…` |
| `code-adjacent__en.csv` | 1 | 20,414,474 | 337,630 | 289,443 | 2,771 | `ab00d8562c92…` |
| `english__en.csv` | 4 | 221,772,370 | 1,337,346 | 1,146,048 | 4,698 | `2113f95391e8…` |
| `indic__bn.csv` | 2 | 7,850,485 | 386,786 | 344,131 | 72,355 | `b6c71859a5ed…` |
| `indic__gu.csv` | 1 | 9,046,237 | 384,509 | 337,516 | 46,826 | `af67410e36f9…` |
| `indic__hi.csv` | 5 | 31,608,737 | 520,766 | 458,835 | 50,455 | `50fbbd1ae59e…` |
| `indic__kn.csv` | 3 | 6,199,835 | 629,049 | 577,759 | 273,567 | `007f3582a10e…` |
| `indic__ml.csv` | 1 | 5,147,999 | 791,468 | 740,690 | 517,280 | `feccd3dfa79e…` |
| `indic__mr.csv` | 2 | 7,524,230 | 472,373 | 424,433 | 123,180 | `62b327fa4358…` |
| `indic__or.csv` | 1 | 7,624,556 | 318,462 | 280,610 | 52,286 | `5ba6adfe0f97…` |
| `indic__sa.csv` | 1 | 3,442,525 | 1,049,509 | 1,021,606 | 611,469 | `90757bb0b0e7…` |
| `indic__ta.csv` | 3 | 5,598,877 | 588,280 | 541,657 | 295,736 | `cf7c8f416719…` |
| `indic__te.csv` | 3 | 6,503,069 | 615,518 | 565,006 | 208,793 | `dd607e65ee29…` |
| `math__en.csv` | 2 | 46,348,147 | 552,782 | 483,768 | 8,909 | `51b2155bea55…` |
| `science__en.csv` | 1 | 23,927,115 | 388,183 | 319,580 | 1,418 | `7d6c12cffbbb…` |

"Over 32 bytes" counts distinct words longer than 32 bytes in UTF-8 (an Indic letter is 3 bytes), the length KE2's
R5 asks about. Sanskrit's compounds stand out: 58% of its distinct words are over 32 bytes, and 97% occur 10 times or
fewer; Malayalam is close behind.

## Getting the tables

- **Link:** <to be added>: `ke2_r1_tables.tar` holds the 21 tables gzipped (`<lane>__<lang>.csv.gz`), `packs.csv` and
  `r1_summary.json`.
- **Check:** the sha256 values in `r1_summary.json` are of the uncompressed CSV files: `gunzip` first, then compare.

## Reproduce

From the repository root, with `pyarrow` and `regex`:

```bash
python3 -I teams/01-data-a/ke2/word_freq.py --packs <the 38 raw sample-v0 packs> --out out/ke2_r1
python3 -m pytest -q teams/01-data-a/ke2/tests
```

`--packs` takes the course download's layout (`<pack>/Part_N/`, `<pack>/Heldout/`) or the pipeline's
(`train/<pack>/`); parts are found by size and sha256, so names do not matter. The run log is
`results/r1/run.log`: 21 tables, 1,430,307 documents, 335 s on 2 cores. An earlier run of the same script gave byte-identical tables
(21 of 21).
