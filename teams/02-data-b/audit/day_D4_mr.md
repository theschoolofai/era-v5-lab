# Marathi reader audit, day D4

The two sections cover 25 documents per Marathi shard for #795.

## ind-mr-fw2

Refs #795. Reader: `patilvijay23`. Reviewed 25 decoded documents from
`ind-mr-fw2-train-000000`, using the issue's day-4 draw:
`random.Random(4).sample(range(11250), 25)`, in draw order.
This section covers the fw2 shard. The sangraha-v audit follows below.

Decoded with frozen p1536; tokenizer SHA-256:
`e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`.
Source shard payload SHA-256:
`c6aa0cf3adb8e3f01741ad41cab255d033ac47a802040bd6ce60fe5a61681be4`.

Codes follow `diagnosis/DISEASES.md`. Offsets are zero-based Unicode character
positions in the decoded shard text. Multiple findings have separate rows;
summary counts use unique documents. D3 annotations on `ok` rows describe natural
language mixing and do not call for removal.

### Reader findings

| doc_id | shard | verdict | code | offset | note |
|---|---|---|---|---|---|
| `19dc4537a81c3357` | `ind-mr-fw2-train-000000` | finding | G1 | 171 | duplicated vowel sign in source; unchanged by cleaning |
| `6e3adb2e9dd2db54` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `a6a30e47fe1ae415` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `8aba1558f9777ca0` | `ind-mr-fw2-train-000000` | ok | D3 | 14 | Natural language mixing: romanised place name in the opening line |
| `fedd3a53aec6a062` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `f9c3f45f756a0473` | `ind-mr-fw2-train-000000` | ok | D3 | 303 | Natural language mixing: Latin-script rendering of a person name |
| `4b6a5bb8591220cf` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `38b78b36215beef6` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `e18a114a936cc021` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `6b1c0cc656315927` | `ind-mr-fw2-train-000000` | finding | C1 | 4106 | Related-news footer |
| `6b1c0cc656315927` | `ind-mr-fw2-train-000000` | finding | C2 | 196 | Repeated English horoscope phrases: one occurs 3x and another 2x |
| `13b9567325470c42` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `7b81e07d7d9098e5` | `ind-mr-fw2-train-000000` | finding | C1 | 1050 | English boilerplate starts here until end of doc |
| `4a6f4022afc284fd` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `9e14cfb48c502dc7` | `ind-mr-fw2-train-000000` | ok |  |  | Cleaner replaced ASCII vertical bar with Devanagari danda |
| `a17353b196212210` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `d1eaa48f0c647291` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `00b8a065d445abcb` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `d4f50f7bd5a46bec` | `ind-mr-fw2-train-000000` | finding | C1 | 1084 | Trailing headline and page-number fragment; probable navigation link |
| `d872d6172ae9c7f2` | `ind-mr-fw2-train-000000` | finding | C1 | 929 | News article boilerplate from 929 to EOD |
| `efc6e13a34102a1b` | `ind-mr-fw2-train-000000` | finding | C1 | 0 | App-install promotional boilerplate at start. Source observation: Nonstandard adjacent vowel-sign sequences exist 42x (first offset 185), all identical in raw source |
| `c2e67c57aba8c085` | `ind-mr-fw2-train-000000` | finding | C1 | 184 | Residual table-of-contents navigation marker |
| `c2e67c57aba8c085` | `ind-mr-fw2-train-000000` | finding | C1 | 8492 | Dangling further-information and source headings |
| `a7d9c397fee12e11` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `f6e598a21b1e9128` | `ind-mr-fw2-train-000000` | ok |  |  |  |
| `48c41e2628c095bd` | `ind-mr-fw2-train-000000` | ok |  |  | Article-related image caption with news-agency attribution; natural language mixing |
| `3350cc5269689c9e` | `ind-mr-fw2-train-000000` | finding | C1 | 1438 | Publisher promotion for news coverage and mobile app |

### Source comparison

All 25 document IDs were matched to the raw sample-v0 Marathi fw2 part, whose SHA-256 matches `audit/raw_parts_SHA256SUMS`. For 24 documents, decoded shard text is identical to raw text after the frozen tokenizer's normalization. The remaining document, `9e14cfb48c502dc7`, differs only by an intentional vertical-bar-to-danda punctuation repair at offset 6 (`DB-G4-002`).

The G1-coded duplicated vowel sign in `19dc4537a81c3357` is already in the raw source, unchanged by cleaning; it is not evidence of damage introduced by the cleaner. Likewise, the 42 adjacent vowel-sign sequences noted for `efc6e13a34102a1b` are source observations, not 42 additional findings or confirmed word splits. No cleaning-induced G1–G4 damage or joiner loss was identified in this sample.

The local cleaned parquet differs from the decoded shard for `7b81e07d7d9098e5`; the decoded shard matches the raw source for that document. This audit uses the decoded shard text, including the publisher promotion at offset 1050, rather than that local cleaned copy.

### Summary

- Documents read: 25
- ok: 17
- With a finding: 8
- Finding rows: 10
- Codes found: C1 (8), C2 (1), G1 (1)
- Descriptive annotations: D3 in 2 otherwise okay documents.

## ind-mr-sangraha-v

Refs #795; follows the fw2 audit merged in #818. Reader: `patilvijay23`.
Reviewed all 25 decoded documents from `ind-mr-sangraha-v-train-000000`, drawn
with `random.Random(4).sample(range(12164), 25)`, in draw order. Shankar
confirmed this second-pack assignment on #795.

Decoded with frozen p1536; tokenizer SHA-256:
`e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`.
Source shard payload SHA-256:
`043e1ff61f9f7db24600f13e63c62605671925dbdebcbfa59984908e6e0b3742`.

All 25 supplied text files match their hashes and character counts in the
privately shared `documents.tsv`. The IDs, texts and draw order also match
the local decoded sample-v0 shard. The reviewed CSV is
[`day_D4_mr_sangraha_v.csv`](day_D4_mr_sangraha_v.csv); the table below has
exactly the same 29 rows. Offsets are zero-based Unicode character positions
in decoded shard text. Separate findings have separate rows; counts of
documents are unique. Notes contain no document text or personal data.

### Reader findings

| doc_id | shard | verdict | code | offset | note |
|---|---|---|---|---|---|
| `6565fb789e5493fe` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `426bc52019bc57b9` | `ind-mr-sangraha-v-train-000000` | finding | C1 | 2282 | Publisher promotional footer |
| `774962d40bb371c9` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `02d5de470abac897` | `ind-mr-sangraha-v-train-000000` | finding | C1 | 98 | keywords boilerplate |
| `45586958888201c8` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `0b4208a1a92712bb` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `44d30e24572c3f82` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `7025084d63149330` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `5a66daa5d4001dc4` | `ind-mr-sangraha-v-train-000000` | finding | C1 | 1904 | like/share/comment solicitation from this point to EOD |
| `523043de1db88e9c` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `13cf5acd515cb010` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `c9031283465dcdb8` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `39de1a9bc42b9646` | `ind-mr-sangraha-v-train-000000` | finding | C2 | 460 | Identical nonempty line repeated 10 times; reader recommends dropping this low-value document |
| `c3ab66f722edf270` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `f760f2c02f0786b7` | `ind-mr-sangraha-v-train-000000` | finding | C1 | 53 | site breadcrumb navigation |
| `f760f2c02f0786b7` | `ind-mr-sangraha-v-train-000000` | finding | C1 | 147 | publication/update metadata |
| `f760f2c02f0786b7` | `ind-mr-sangraha-v-train-000000` | finding | G1 | 1371 | Duplicated vowel sign U+0947 in source; unchanged by cleaning |
| `d598504f67f00598` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `4a9376090db4dda1` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `2501d0dffe8663fb` | `ind-mr-sangraha-v-train-000000` | finding | C1 | 66 | site breadcrumb navigation |
| `2501d0dffe8663fb` | `ind-mr-sangraha-v-train-000000` | finding | C1 | 2621 | publisher editorial footer |
| `2501d0dffe8663fb` | `ind-mr-sangraha-v-train-000000` | finding | C1 | 3018 | subscription/comment feed footer |
| `2889e69e622b6e75` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `4a8fef3d7758620f` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `56384c5ddc5d05f1` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `2bf9520141721a51` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `a545d8703095fba9` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `659eff05e6fa4e25` | `ind-mr-sangraha-v-train-000000` | ok |  |  |  |
| `e4279ffe79517148` | `ind-mr-sangraha-v-train-000000` | finding | C3 | 535 | ends with an introductory heading and no following body; possible missing embed or text |

### Source comparison

All 25 IDs were matched to the raw sample-v0 Marathi sangraha-v train part,
SHA-256 `85f3fe3355206939f4b483da0e7e0187aa3738067951a78ffcccfb097237b7cc`,
which matches `audit/raw_parts_SHA256SUMS`. Raw text was normalized with the
frozen p1536 tokenizer before comparison. Eighteen decoded documents are
identical to normalized raw; seven differ. Their differences consist of
removing duplicated text already retained elsewhere, decoding literal newline
escapes, and six ordinal-sign-to-Marathi-letter repairs across two documents.
The duplicated heading in one document is removed alongside newline decoding.

Every finding's local text is present in the raw source. In particular,
`f760f2c02f0786b7` has doubled U+0947 at offset 1371 in both raw and decoded
text. The G1 row records a source-existing duplicated vowel sign, as in #818,
not cleaning-induced damage. The C3 row describes a source-existing final
heading with no following body; it may be a missing embed rather than a cut
introduced by cleaning. No cleaning-induced G1–G4 damage or joiner loss was
identified in this sample.

The C2 document `39de1a9bc42b9646` has ten copies of the same nonempty line.
The reader recommends dropping it; its audit verdict remains `finding`, as
required by the reader-report format. This report changes no cleaning rules.

### Summary

- Documents read: 25
- ok: 18
- With a finding: 7
- Finding rows: 11
- Codes found: C1 (8), C2 (1), G1 (1), C3 (1)

## Combined Marathi summary

- Documents read: 50 (25 fw2, 25 sangraha-v)
- ok: 35
- With a finding: 15
- Finding rows: 21
- Codes found: C1 (16), C2 (2), G1 (2), C3 (1)
- The two G1 rows are source-existing; no cleaning-induced damage was identified.
- Descriptive D3 annotations in the fw2 section are unchanged.
