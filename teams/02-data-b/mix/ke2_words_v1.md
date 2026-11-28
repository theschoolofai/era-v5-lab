# KE2 data request (R1, R5): Indic word list from Data B

Reply to KE2's Lab 5 request (design task 00) for R1 (word frequency table) and R5 (rare and long Indic words, Sanskrit compounds). File: `ke2_words_v1.csv`.

## What is in the file

- Columns: `word,count,lang,lane,bytes,kind` (KE2 asked for word, count, lang, lane; `bytes` is the UTF-8 length, `kind` says which list the row is from).
- `kind=top3000`: the 3,000 most frequent words per language (R1, trimmed so it fits in the repo).
- `kind=rare_1_10`: 200 words per language with count 1 to 10, a seeded random sample (R5).
- `kind=long_gt32`: the 200 most frequent words per language over 32 bytes with count at least 2 (R5). For `sa` these are mostly compounds and sandhi forms.
- Languages: hi, mr, bn, ta, sa. 17,000 rows, 849,208 bytes, sha256 `be36f6e6bdb5a1ee2d5c966bd7496cb9776eb321e6d2177c59e13ae701e10497`.

## Source and lane

- Text: public FineWeb-2, the same run as `word_cost_v1.md` (first 100,000 train docs per language, Sanskrit all 21,453). This is the source of our fw2 packs, but it is NOT the training shards themselves, so `lane` is `fw2-public`. A rerun on the shards needs only `docs_for` in `word_cost.py` changed.
- Licence: FineWeb-2 is ODC-By 1.0; these are word counts only, no documents.

## Word rule

Same as `word_cost_v1.md`: split on whitespace, Unicode punctuation (P*) and symbols (S*); ZWJ/ZWNJ stay inside a word; a hyphen splits; keep a word only if every letter is in the language's script block.

## How it was built

From the `out/word_freq_<lang>.csv` files that `word_cost.py` writes (full tables: hi 457k, mr 1.32M, bn 764k, ta 2.21M, sa 3.01M distinct words):

```python
import csv, random
L = ['hi', 'mr', 'bn', 'ta', 'sa']; LANE = 'fw2-public'; R = []
for g in L:
    rows = [(r['word'], int(r['count']), int(r['bytes']))
            for r in csv.DictReader(open(f'out/word_freq_{g}.csv', encoding='utf-8'))]
    R += [[a, c, g, LANE, b, 'top3000'] for a, c, b in rows[:3000]]
    rare = [r for r in rows if 1 <= r[1] <= 10]
    R += [[a, c, g, LANE, b, 'rare_1_10'] for a, c, b in random.Random(0).sample(rare, 300)[:200]]
    R += [[a, c, g, LANE, b, 'long_gt32'] for a, c, b in [r for r in rows if r[2] > 32 and r[1] >= 2][:200]]
```

## Not covered here

- R2 (held-out text with verified labels), R3 (code, Team 1), R4 (names with Indic and Latin spellings), R6 (misspellings).
- Full-size tables are not committed (up to 160 MB per language); ask if you want them.
