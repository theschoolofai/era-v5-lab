# KE2 data request R4, Bengali: names with Bengali and Latin spellings

Data B's reply to KE2's Lab 5 request (design task 00), item R4, for Bengali. File: `ke2_names_bn_v1.csv`.
The Hindi, Tamil and other languages are answered by their own readers (G2 chat, 28 Nov).

## What is in the file

16,000 rows, 1,325,535 bytes, sha256 `1f062843d07b173dfbd6c69f9f68a4f8c4ecdf4cb5550a414bdc7124e10428ff`.
Every entity or pair has two rows, one per spelling, linked by `id`.

| Columns | Meaning |
|---|---|
| `name,lang,script,type,source,licence` | KE2's six columns |
| `id` | Wikidata QID, or `<split>:<unique_identifier>` for Aksharantar; links the two spellings |
| `sitelinks` | Wikidata sitelink count: a rough measure of how well known the entity is (blank for Aksharantar) |
| `region` | `in_bd` when the item's citizenship (P27) or country (P17) is India, Bangladesh or British Raj, else `other` (blank for Aksharantar) |
| `count_bn_sample` | whole-word occurrences of the Bengali form in our two bn packs of sample v0 (`ind-bn-fw2`, `ind-bn-sangraha-v`, 21,533 documents); blank on Latin rows |

| Part | Rows | `type` | Bengali form | Latin form | Licence |
|---|---:|---|---|---|---|
| Wikidata entities | 10,000 | `person` 2,000 · `place` 2,000 · `org` 1,000 (entities) | Bengali label (`bn`, `Beng`) | English label (`en`, `Latn`) | CC0-1.0 (Wikidata data) |
| Aksharantar word pairs | 6,000 | `name_word` 3,000 (pairs) | Bengali word (`bn`, `Beng`) | Latin spelling (`bn`, `Latn`) | CC0-1.0 (see the licence note) |

### Seen and unseen in our Bengali text

6,226 of the 8,000 Bengali forms never occur as whole words in the two bn packs (`count_bn_sample = 0`), so KE2 can
draw unseen names and seen names from one file. 3,849 of the 8,000 Bengali forms are longer than 32 bytes.

| type | region | unseen | seen | median words | median bytes |
|---|---|---:|---:|---:|---:|
| person | in_bd | 764 | 236 | 2 | 38 |
| person | other | 945 | 55 | 2 | 40 |
| place | in_bd | 818 | 182 | 2 | 46 |
| place | other | 918 | 82 | 2 | 40 |
| org | in_bd | 412 | 88 | 3 | 71 |
| org | other | 461 | 39 | 3 | 55 |
| name_word | | 1,908 | 1,092 | 1 | 18 |

## Sources

1. **Wikidata** (query service, read 28 Nov 2026): items with a Bengali Wikipedia article, a Bengali label and an
   English label. `person` = instance of human (Q5), 61,524 in the pool after the filters. `org` = instance of one of
   21 organisation classes (university, political party, company, newspaper, ...; list in `ORG_CLASSES`), 7,502 in
   the pool, one query per class (a single query timed out). `place` = has coordinates (P625) and is neither a person
   nor an org, 29,274 in the pool. Seeded sample: half `in_bd`, half `other` per type.
2. **Aksharantar** (`ai4bharat/Aksharantar` at `e418c1fc928d9f5393af33268472cf20c1891be8`, `ben.zip` sha256
   `4ab6edcc6ab556040d8f43ee75eec73cc25af0cf72d09e4650dab26b196d5fe7`): the word pairs whose `source` is `Wikidata`
   in the train and valid splits (18,596 distinct pairs after the filters), seeded sample of 3,000. Examples in the
   file: ক্লডিয়া / claudia, প্রাণকৃষ্ণ / prankrishna, রত্নায়েকে / ratnayeke.

**Filters.** Labels are NFC with single spaces. A Bengali form is kept only if every letter is in the Bengali block,
with no ৰ / ৱ (Assamese letters), no digit and no "(...)" disambiguator; a Latin form only if its letters are Latin
(the modifier letters ʻ ʼ ʾ ʿ allowed) with no "(...)". The pool counts above are after the filters, which dropped
4,266 Wikidata items for their Bengali label (mostly a disambiguator or a digit) and 171 for their English label.
Aksharantar pairs also need at least 2 Bengali letters and 2 Latin characters, which drops misaligned pairs such as
ব / b.

**Not used:** Aksharantar's `AK-NEI` and `AK-NEF` named-entity pairs (2,699 for Bengali). They sit only in the
test split, which is Aksharantar's transliteration benchmark, and a read of 25 found ordinary words among them
(স্পেশাল / special, অথোরিটি / authority).

**Licence note.** Wikidata's data is CC0. The Aksharantar card gives CC-BY for manually collected data and CC0 for
"mined dataset (from Samanantar and IndicCorp)" and existing sources; it does not name its Wikidata-mined pairs. We
record them as CC0 because they are mined (not manually collected) from Wikidata labels, which are CC0 themselves:
that is our reading, not a statement on the card.

## Read before use

- **The English label is the entity's English name, not always a spelling of the Bengali form.** For people it
  usually is one, sometimes with other name parts (এডগার কড / Edgar F. Codd) or as a translation (চতুর্দশ লুই /
  Louis XIV of France). For orgs and places it is often a translation (যুক্তরাজ্য স্বাধীনতা দল / UK Independence
  Party; জাতিসংঘ সদর দপ্তর / Headquarters of the United Nations). Use the `name_word` rows when a true spelling pair
  is needed.
- **`place` is approximate.** "Has coordinates" also catches events and institutions whose class is not in
  `ORG_CLASSES`. A rough search of the English labels finds about 20 wars and battles (Falklands War) and about 100
  universities, colleges, schools, banks or clubs (Purdue University) among the 2,000 place rows; the search also
  catches a few true places (Dogger Bank).
- 49 Bengali forms occur more than once (50 extra rows): 46 are one Bengali word with two Latin spellings in
  Aksharantar, 1 is two entities with the same Bengali label, and 2 are a word pair that is also an entity's label.
- **Wikidata changes daily.** The 25 query answers used here are kept outside the repo (about 60 MB, in Sourav's
  data folder; sha256 of each in `ke2_names_bn_v1.json`). With those answers the script rebuilds this file byte for
  byte; a fresh query gives a newer snapshot with different rows. The CSV is the deliverable.
- `count_bn_sample` word rule: the split regex of `word_cost.py` in #923 (whitespace, Unicode punctuation and
  symbols; ZWJ/ZWNJ kept), after NFC. Whole words only: কলকাতার does not count as কলকাতা. A multi-word name also
  matches across punctuation (এম এ মান্নান matches এম. এ. মান্নান).

## Commands

```bash
cd teams/02-data-b/mix
# inputs: Aksharantar ben.zip at the pinned revision, and the two bn raw parts of sample v0
hf download ai4bharat/Aksharantar ben.zip --repo-type dataset \
    --revision e418c1fc928d9f5393af33268472cf20c1891be8 --local-dir dl_aksharantar
python ke2_names_bn.py --cache <wikidata answers folder> --aksharantar-zip dl_aksharantar/ben.zip \
    --bn-parts <raw>/train/ind-bn-fw2/part-00000.parquet <raw>/train/ind-bn-sangraha-v/part-00000.parquet \
    --out ke2_names_bn_v1.csv --summary ke2_names_bn_v1.json
python -m unittest test_ke2_names_bn        # 13 tests, made-up data, no network
```

An empty `--cache` folder makes the script query Wikidata (about 4 minutes: 25 queries, 1 to 37 s each); with the
saved answers it takes about 6 seconds. The raw parts are `ind-bn-fw2` sha256 `fda2605f…` (11,205 docs) and
`ind-bn-sangraha-v` sha256 `84a59d86…` (10,328 docs).

## Checks

An independent recheck (its own code, not this script's) found one bug, fixed in this version: a name that ends a
document was counted more than once. After the fix, `count_bn_sample` was recounted for all 8,000 Bengali forms
(0 differences) and, with a separate regex method, for a seeded 150 (0 differences). Rerun on this version, the
recheck's row checks match all 3,000 Aksharantar pairs to the zip (source Wikidata, right split) and 4,998 of the
5,000 Wikidata entities to the saved answers; the other 2 differ only by the filter fixes above (a double space
collapsed in one English label, and Ḥabīb al-Raḥmān al-Aʻẓamī kept under the ʻ ʼ rule).

## Not covered here

- R6 (misspellings, wrong/right pairs): candidates are mined from the same two packs with `bn_word_sheets.py`
  (one common Bengali spelling confusion apart, the wrong form at most a tenth as common). A Bengali reader is
  marking them; only the pairs marked as misspellings will go in `ke2_misspell_bn_v1.csv`.
