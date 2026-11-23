# Sanskrit reader audit, day D4 (first reader)

Refs #711. Documents drawn with `random.Random(4).sample(range(n), 25)` from `ind-sa-fw2-train-000000` (n = 5667), decoded with the frozen tokenizer p1536 (sha256 `e6b93a93…`). Codes from `diagnosis/DISEASES.md`; `offset` is the character offset in the decoded text. `OCR` is not a DISEASES code: it marks scanned-book text with misread letters, written down as #527 says for codes outside the list. Source or cleaning: pending the raw part `ind-sa-fw2_part-00000.parquet`.

| doc_id | shard | verdict | code | offset | note |
|---|---|---|---|---|---|
| `75423f9e4d47b94e` | `ind-sa-fw2-train-000000` | finding | G3 | 466 | blank lines, quoted verse kept only its first line |
| `75423f9e4d47b94e` | `ind-sa-fw2-train-000000` | finding | C3 | 872 | ends mid-sentence |
| `4a0d46c68a0ec578` | `ind-sa-fw2-train-000000` | ok |  |  | stotra, complete |
| `bd181980f5d209a9` | `ind-sa-fw2-train-000000` | ok |  |  |  |
| `b7c7d966b6019d97` | `ind-sa-fw2-train-000000` | finding | G3 | 912 | blank lines, quoted verse kept only its first half |
| `b7c7d966b6019d97` | `ind-sa-fw2-train-000000` | finding | C3 | 1136 | ends mid-word |
| `738dca7eb9deb0bb` | `ind-sa-fw2-train-000000` | ok |  |  | news |
| `d6049ed74b2695f9` | `ind-sa-fw2-train-000000` | ok |  |  | colon at 95 is a dateline, not a visarga |
| `bd4759d1fb5e05ad` | `ind-sa-fw2-train-000000` | ok |  |  | Rigveda sukta, complete |
| `0fe8486c2bb9e0c4` | `ind-sa-fw2-train-000000` | ok |  |  | news |
| `68c788acd9ae8594` | `ind-sa-fw2-train-000000` | finding | D3 | 1444 | one Hindi sentence inside Sanskrit news |
| `37d6294642ac041a` | `ind-sa-fw2-train-000000` | ok |  |  | Samhita text; avagraha after a space is normal |
| `9f60e07096013f17` | `ind-sa-fw2-train-000000` | ok |  |  | Purana chapter, complete |
| `e4e5b4944e701553` | `ind-sa-fw2-train-000000` | ok |  |  | essay; spelling slips are the author's |
| `1e92b88cfec3f31a` | `ind-sa-fw2-train-000000` | ok |  |  | news |
| `ec09cf84f27662b9` | `ind-sa-fw2-train-000000` | ok |  |  | kavya canto, complete; title line twice at top |
| `4d8f70ef5085c008` | `ind-sa-fw2-train-000000` | finding | G3 | 0 | starts mid-word, opening cut |
| `4d8f70ef5085c008` | `ind-sa-fw2-train-000000` | finding | OCR | 53 | scanned commentary, misread letters and split words throughout |
| `cd67620279a32c81` | `ind-sa-fw2-train-000000` | finding | A6 | 71 | Latin capital I used as danda |
| `cd67620279a32c81` | `ind-sa-fw2-train-000000` | finding | A6 | 445 | Latin capital I used as danda |
| `185387955f0849d5` | `ind-sa-fw2-train-000000` | ok |  |  | news |
| `832cf7bbd1a72622` | `ind-sa-fw2-train-000000` | finding | C2 | 87 | first verse repeated |
| `832cf7bbd1a72622` | `ind-sa-fw2-train-000000` | finding | G4 | 2401 | ASCII colon for visarga, 7 times from here to 3164 |
| `4f7a6a85a601d7bf` | `ind-sa-fw2-train-000000` | finding | A6 | 4366 | OM sign in place of a vowel sign, also at 5172; `---` gaps are the edition's |
| `7bd8a8fa5e6288c7` | `ind-sa-fw2-train-000000` | finding | A1 | 104314 | VARIATION SELECTOR-15 U+FE0E, 211 times, ends of apparatus lines |
| `7bd8a8fa5e6288c7` | `ind-sa-fw2-train-000000` | finding | C1 | 104174 | 8.6k chars of manuscript variant notes after the text |
| `51e19714fc999a42` | `ind-sa-fw2-train-000000` | finding | C2 | 68 | first line repeated |
| `51e19714fc999a42` | `ind-sa-fw2-train-000000` | finding | G3 | 7034 | spaces between words lost in many verses |
| `c1a3da3a70d87d45` | `ind-sa-fw2-train-000000` | ok |  |  | Rigveda with svara marks and padapatha |
| `46f9b9113237390c` | `ind-sa-fw2-train-000000` | finding | C1 | 0 | wiki user-page header with Latin user name |
| `46f9b9113237390c` | `ind-sa-fw2-train-000000` | finding | B2 | 194 | `<poem>` tag left in |
| `07aafc1c903649cd` | `ind-sa-fw2-train-000000` | ok |  |  | Rigveda with bhashya; hyphen line breaks at 744 are the scan's |
| `7d742912c34be333` | `ind-sa-fw2-train-000000` | finding | G3 | 0 | starts mid-word, opening cut |
| `7d742912c34be333` | `ind-sa-fw2-train-000000` | finding | OCR | 52 | scanned commentary, misread letters and split words throughout |

## Summary

- Documents read: 25
- ok: 14
- with a finding: 11
- codes found: G3 (5), A6 (3), C1 (2), C2 (2), C3 (2), A1 (1), B2 (1), D3 (1), G4 (1), OCR (2, not a DISEASES code)
- G1 0, G2 0. The one G4 row (ASCII colon for visarga, `832cf7bbd1a72622`) is the case #576 asked to hear about; whether it is in the raw text is pending the raw part.
