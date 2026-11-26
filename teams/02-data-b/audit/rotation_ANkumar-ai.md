# Data B rotation, week 4: R1 and R2 on ind-te-fw2 (ANkumar-ai)

Refs #ISSUE. Rotation member: ANkumar-ai (Ajay). Language: Telugu (I read Telugu; I did the week-1 diagnosis of ind-te-fw2).

## What was checked

| Item | Value |
|---|---|
| Shard | `ind-te-fw2-train-000000` (5,670 documents) |
| Sample | DAY 4: `random.Random(4).sample(range(5670), 50)`, the same draw as #560 and #618 |
| Input | the 50 documents decoded from the p1536 shard, with their raw sample-v0 text (`ind-te-fw2_part-00000.parquet`), shared by @shankarpandala on 25 Nov |
| Integrity | sha256 of all 50 decoded texts matches `documents.tsv` (50/50) |
| Raw text | NFC applied before comparing (p1536's normalizer), as asked |
| Checks | G1, G2, A1, A2, A3, A4, A6 by code point (DISEASES.md), plus VV (two dependent vowel signs in a row, or virama + vowel sign) and NFC |
| Source or cleaning | each finding's context is looked up in the NFC raw text; every raw/shard difference is listed below |
| Wall time | 0.54 s for all checks (one process) |

Reader check: I read 15 of the 50 documents on screen (including all 7 with a finding or a cleaning change) and agree with every code-point result. The other 35 were checked by code point only.

Document text is not reproduced here: only IDs, codes, offsets and code points.

<details><summary>Documents checked (50)</summary>

- `fab5d5dde67ea6b9`
- `8a73eb6aa6810afc`
- `a5958f84af8dae22`
- `153285e2e7adbd34`
- `4f377b8c28b09590`
- `94b6adae3ce872a2`
- `dc37923ec8efe6da`
- `476ebc3ae4e21d16`
- `2e80a0142cf0918e`
- `0ed57d6658a51ed0`
- `6330519780b7aa36`
- `47f871f9e869f3d8`
- `7ce18abfa9c69925`
- `0d09d4224ede9b6b`
- `cec6c45042d50bda`
- `c7a54a063e9947ce`
- `a08e03399539c434`
- `f59b120ab1a2e489`
- `df42ebcb389501e6`
- `8a7eaf8a1412fd68`
- `f70e8ed9dba39ac0`
- `384dd45efa1911d5`
- `694770ec83673a12`
- `59f8801218e49ffb`
- `08dc9def41ac6446`
- `99cdebc47b2fcb2f`
- `fcc0aecb824819f1`
- `d41a4bb7fc118194`
- `95b19837e2ea70ca`
- `bfff9a6443986da2`
- `d6841884649df818`
- `05f83c01e05b331d`
- `ba9b167682a81787`
- `b61e8536329d1633`
- `a8762b315778c377`
- `4d435c20d5b35bec`
- `bcdfa1cfefd91326`
- `c2eed4440108a471`
- `c6e9721d15003693`
- `31d1cd5b66c17e97`
- `bf835796442d692a`
- `63ba64d7f4e621dd`
- `5483e9f8d926829f`
- `08cee316836fa8ae`
- `e644436b7317c4ef`
- `2ba4c51be095637b`
- `6262990a082abb4d`
- `3ee9b20efa12e014`
- `a08f70f11604a08d`
- `2bd3b501d2526294`

</details>

## R1: results on 50 documents

| Code | Findings | Documents |
|---|---|---|
| G1 vowel sign or virama not attached to a Telugu letter | 0 | 0 |
| G2 ZWJ/ZWNJ at word edge or doubled | 0 | 0 |
| A1 invisible characters | 0 | 0 |
| A2 control characters | 0 | 0 |
| A3 mojibake | 0 | 0 |
| A4 U+FFFD | 0 | 0 |
| A6 Latin or other script inside a Telugu word | 1 | 1 |
| VV two vowel signs in a row (extra) | 1 | 1 |

- ZWJ (U+200D) and ZWNJ (U+200C): 0 in the raw text and 0 in the shard, for all 50 documents. Counts match, so no joiner was lost.
- NFC: all 50 shard documents are already NFC.
- 45 of 50 shard documents are identical to their NFC raw text. The other 5 were changed by cleaning (table below).
- Both findings are identical in the raw text: they come from the source, not from clean.py or p1536.

## R2: findings with doc ID and hex dump

Offsets are zero-based code points in the decoded shard document. The hex dump is the finding (bold) plus three code points on each side.

| doc_id | code | offset | hex dump | origin | note |
|---|---|---|---|---|---|
| 59f8801218e49ffb | VV | 59 | U+0054 U+000A U+0C15 **U+0C46** **U+0C46** U+0C0E U+0C32 | source | vowel sign E typed twice in a name; reader check: should be KA + U+0C47 (long E) |
| 6330519780b7aa36 | A6 | 2353 | U+0C3F U+0C27 U+0C3F **U+00C5** U+0C32 U+0C4B U+0020 | source | Latin U+00C5 inside a Telugu word; reader check: the word is correct without it (legacy font or typing error) |

Not counted: `a08e03399539c434` offset 1933 has U+2764 U+FE0F (heart emoji with variation selector 16). FE0F is the normal emoji-presentation selector, not listed under A1, so I left it as a note.

## Changes made by cleaning (raw NFC vs shard)

All 5 changed documents were checked at each edit boundary: no word is cut, no vowel sign is left detached, and joiner counts are 0 before and after.

| doc_id | raw offset | removed (code points) | what was removed |
|---|---:|---:|---|
| 476ebc3ae4e21d16 | 2807 | 11 | phone number, replaced by the 7-character placeholder U+003C U+0050 U+0048 U+004F U+004E U+0045 U+003E (F1 masking; digits not shown) |
| 0ed57d6658a51ed0 | 1408 | 88 | "read this too" related-news line (C1) |
| 0ed57d6658a51ed0 | 2055 | 114 | "read this too" related-news line (C1) |
| 0ed57d6658a51ed0 | 2807 | 54 | English "Tags:" line (C1) |
| cec6c45042d50bda | 1582 | 28 | "View this post on Instagram" embed text (C1) |
| a08e03399539c434 | 0 | 20 | "Just In / Don't Miss!" sidebar header (C1) |
| a08e03399539c434 | 1700 | 28 | "View this post on Instagram" embed text (C1) |
| 8a7eaf8a1412fd68 | 0 | 13 | "latest news" header line (C1) |
| 8a7eaf8a1412fd68 | 1269 | 13 | "read these too" trailer line (C1) |

Note for Data A (not script damage): in `a08e03399539c434` the Instagram rule removed only the "View this post on Instagram" line. The rest of the embed (English caption, handles, "A post shared by ...") stays in the shard, from offset 1680.

## Summary

Documents checked: 50 (DAY 4). Findings: G1 0, G2 0, A1 0, A4 0, A6 1 (plus VV 1). Documents with a finding: 2 of 50. ZWJ/ZWNJ: 0 before and 0 after cleaning, so none lost. Cleaning touched 5 documents and only removed boilerplate or masked a phone number, with no script damage. Both findings come from the source text.

## Command

```
python3 -I rotation_ANkumar-ai.py <folder with documents.tsv, shard_D4/, raw_D4/> findings.json
docs 50, sha_ok 50, nfc_bad [], identical_to_raw 45, zwj [0, 0], zwnj [0, 0]
counts {"A6": 1, "A1": 1, "VV": 1}, docs_with_finding 3, origin {"source": 3, "cleaning": 0, "source?": 0}, wall_s 0.54
```

The script's A1 count includes the FE0F after the heart emoji; it is reported above as a note, not as a disease.
