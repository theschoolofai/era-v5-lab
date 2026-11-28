# What does a word cost? (Data B Lab 5 design task 2)

Word lengths in UTF-8 bytes for Hindi, Marathi, Bengali, Tamil and Sanskrit.

## Data and method

- Input: public FineWeb-2 (`HuggingFaceFW/fineweb-2`, the source of our fw2 packs), configs hin_Deva, mar_Deva, ben_Beng, tam_Taml, san_Deva. First 100,000 documents of the train split per language, reading parquet files in name order, so the run repeats exactly. Sanskrit has only 21,453 train documents in FineWeb-2, so sa uses all of them. This is NOT the Data B shards; rerun with the shard text when needed (one function, `docs_for`).
- Word: text between whitespace, Unicode punctuation (P*) and symbols (S*). ZWJ/ZWNJ stay inside a word. A hyphen splits (hyphenated compounds count as parts, so long-word shares are a lower bound).
- Native word: every letter is in the language's script block. Latin and other-script words are counted separately and left out of the tables.
- Shares are by running words (tokens) unless named "bytes" (share of word bytes) or "types" (distinct words).

Command (Google Colab, CPU, Python 3):

```
pip install -q regex pyarrow huggingface_hub
python word_cost.py --docs 100000 --out out
```

Outputs: `out/word_cost.json` (all numbers below, committed here as `word_cost_v1.json`) and `out/word_freq_<lang>.csv` (word, count, lang, bytes; not committed, size).

## Headline

| lang | docs | text MB | native words | distinct | mean B | median B | p90 | p99 | p99.9 | max | % words >16 B | % words >32 B | % words >64 B | % word bytes >32 B | % word bytes >64 B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hi | 100,000 | 654.8 | 49,563,554 | 457,310 | 11.76 | 12 | 21 | 30 | 39 | 327 | 18.728 | 0.791 | 0.0013 | 2.389 | 0.0094 |
| mr | 100,000 | 745.2 | 40,665,127 | 1,323,829 | 16.94 | 15 | 27 | 42 | 51 | 405 | 45.233 | 5.755 | 0.0069 | 12.584 | 0.0304 |
| bn | 100,000 | 690.5 | 39,785,672 | 763,636 | 15.91 | 15 | 27 | 39 | 48 | 378 | 40.247 | 3.696 | 0.0022 | 8.472 | 0.0113 |
| ta | 100,000 | 940.6 | 37,355,167 | 2,207,739 | 23.64 | 21 | 39 | 57 | 72 | 1686 | 72.871 | 20.461 | 0.2874 | 34.7 | 0.8675 |
| sa | 21,453 | 350.8 | 13,426,760 | 3,006,013 | 24.14 | 21 | 45 | 93 | 153 | 4005 | 61.766 | 23.428 | 3.5776 | 48.105 | 12.9909 |

The max column is noise: the 4,005 B (sa) and 1,686 B (ta) "words" are runs of text with no spaces, not real words. The percentiles are stable.

All five scripts cost 3 bytes per character here (bytes per char: hi 3.0, mr 3.0, bn 3.0, ta 2.999, sa 3.0), so 32 bytes is about 10 to 11 characters and 64 bytes about 21.

## Distribution (% of running words per byte-length bucket)

| lang | 1-8 | 9-16 | 17-24 | 25-32 | 33-48 | 49-64 | 65-96 | 97-128 | >128 |
|---|---|---|---|---|---|---|---|---|---|
| hi | 31.346 | 49.926 | 15.697 | 2.24 | 0.783 | 0.007 | 0.001 | 0.0 | 0.0 |
| mr | 8.656 | 46.111 | 30.941 | 8.537 | 5.595 | 0.153 | 0.007 | 0.0 | 0.0 |
| bn | 9.141 | 50.612 | 29.835 | 6.716 | 3.633 | 0.061 | 0.002 | 0.0 | 0.0 |
| ta | 1.746 | 25.383 | 36.537 | 15.874 | 18.109 | 2.064 | 0.285 | 0.002 | 0.001 |
| sa | 12.272 | 25.962 | 26.947 | 11.391 | 15.295 | 4.555 | 2.76 | 0.565 | 0.253 |

## Long words are mostly one-offs

| lang | % distinct words >32 B | of those, % seen once | % distinct words >64 B | of those, % seen once |
|---|---|---|---|---|
| hi | 9.98 | 67.4 | 0.11 | 94.4 |
| mr | 33.39 | 66.8 | 0.162 | 90.4 |
| bn | 22.42 | 64.0 | 0.078 | 88.5 |
| ta | 63.06 | 67.3 | 2.81 | 83.7 |
| sa | 65.96 | 80.1 | 13.337 | 88.5 |

## What a Sanskrit compound does to the counts

- Sanskrit writes compounds and sandhi as one word, so its words are the longest: mean 24.14 B vs 11.76 B for Hindi on the same script, p99 93 B vs 30 B, p99.9 153 B vs 39 B.
- 23.428% of Sanskrit running words are over 32 B, and they hold 48.105% of all Sanskrit word bytes; over 64 B: 3.5776% of words, 12.9909% of bytes. Hindi: 0.791% of words over 32 B.
- Sanskrit has the most distinct words (3,006,013 in 13,426,760 running words), and 80.1% of its distinct words over 32 B appear once: compounds are built fresh, not repeated, so a word list or a fixed-size word unit cannot cover them.
- Effect on any per-word unit: a share counted in words under-weights Sanskrit and Tamil bytes, and a 32-byte unit cap cuts about a fifth of Sanskrit and Tamil words, while for Hindi it cuts under 1%. Splitting compounds (sandhi splitting) would move these counts toward Hindi's; not done here.

Two long Sanskrit compounds that repeat in the sample (word, bytes, count):

- नानाभिनिर्हारनिर्देशविविधहेतुकारणनिदर्शनारम्बणनिरुक्त्युपायकौशल्यैर्नानाधिमुक्तानां (249 B, 4x)
- ताश्चातुर्महाराजिकांस्त्रयस्त्रिंशान्यामांस्तुषितान्निर्माणरतीन्परनिर्मितवशवर्तिनो (246 B, 12x)

Tamil is close behind Sanskrit for a different reason: agglutinative suffixes (case, plural, clitics) stack on one stem.

## Not done

- Not run on the Data B shards (used the public FineWeb-2 source text).
- No sandhi or compound splitting; no per-pack breakdown.
- KE2's word frequency table (word, count, lang, lane) comes out of the same run (`word_freq_<lang>.csv`) but is not committed here; lane is not filled.
