# code-go audit: issues to fix

This file lists the problems found while auditing the code-go pack.

45 docs were read side by side: the text before cleaning (`Cap1-packs/`) and after cleaning (`tokenizer_sample_v0_clean/train/`). Part_1 has 35 docs and Part_2 has 10. Only docs that cleaning changed or dropped were sampled (the viewer's default), so unchanged docs are not covered. Each doc was labelled in `audit_labels/code-go_<part>.csv` (copies in `teams/01-data-a/audit/code-go_<part>-smitasasindran.csv`). The verdict answers "was the cleaner's output right?": `clean` (yes), `fix` (no, something is wrong in the output), or `drop` (the doc was removed, and that was right). Disease codes follow `era-v5-lab/diagnosis/DISEASES.md`.

Docs labelled `clean` are left out: 33 docs. What remains is 12 docs: 4 marked `fix` and 8 marked `drop`. The 8 dropped docs need no action; they are listed so a second reader can check them.

Every one of the 45 docs also lost a dataset header line (`<gh_stars>…`, `<reponame>…` or `<filename>…`) at the top. That was done correctly in every doc and is not an issue.

## Summary

| Issue | Docs |
|---|---:|
| Cyrillic letter replaced with a Latin one in a test fixture (G4) | 1 |
| Short licence header left at the top (E4) | 3 |
| Dropped by cleaning, correctly (E1, E2) | 8 |
| **Total** | **12** |

The first issue is the smallest group in the sample and it changes what the code means, so it is the one to look at first. The second is minor and affects many docs across the pack.

## Cyrillic letter replaced with a Latin one in a test fixture (G4) (1)

**What it is.** `dabdf7ec` is a test fixture for a Go linter that flags non-ASCII identifiers. Before cleaning it declares `type TеstStruct struct{}` with a Cyrillic `е` (U+0435). Cleaning changed it to a Latin `e`. The comment on the same line still says the identifier "contain non-ASCII character: U+0435", so the cleaned file now contradicts itself, and the test no longer tests anything. This is damage from cleaning: G4, over-normalised.

**How big it is.** The rule is DA-A6-001 in `spec_v1/clean.py`. It rewrites any word that mixes Latin and Cyrillic letters, in code, strings and comments alike. Across the whole code-go pack (83,267 docs before cleaning) it changed 11 docs. 9 of them look like accidental look-alike letters in ordinary code (for example `retriеve`, `AcсBandwidth`, `PVСReport`), where the change is right. The other 2 are test files with deliberate Cyrillic: this doc and `c95ad16bf96bf0d6` (Part_2, a test of a symbol-cleaning function whose input `оjо` is Cyrillic on purpose). The second one was found by searching the pack and is not in the audit sample.

**What to do.** Skip DA-A6-001 for files that are tests or test data (a `testdata/` folder or a `_test.go` name; the path is in the `url` column). Check that the 9 good changes still happen and that the gold set still changes under 1%.

| Pack | doc_id | Verdict |
|---|---|---|
| code-go / Part_1 | `dabdf7ecc74cd614` | fix |

## Short licence header left at the top (E4) (3)

**What it is.** The file still starts with a 3-line copyright and licence comment after cleaning, for example "Copyright 2014 … / Use of this source code is governed by a MIT-style / license that can be found in the LICENSE file." The same wording repeats across thousands of Go files. This is disease E4, repeated licence headers.

**Where.** The licence rule for code-go, DA-E4-005, only removes a comment block that has licence words and at least 4 lines (`block.count("\n") >= 4` in `_is_licence`). Longer Apache and MIT blocks were removed in this sample (seven docs). The 3-line form passes through. In `05809df4` the header also shows `Copyright 2018 AUTHOR`, where the original had a `<NAME>` placeholder.

**How big it is.** In the cleaned pack, 2,260 of 76,955 docs (2.9%) still start with a `//` comment block of fewer than 4 lines that contains licence words. Each is about 150 characters of boilerplate, so the harm per doc is small.

**What to do.** Lower the line limit for the Go forms of the short header ("Use of this source code is governed by … LICENSE file"), or decide that 3-line notices are acceptable and record that. Either way, re-run the gold-set harm test, because a short block is easier to confuse with a real comment. `88d0c261` was labelled `fix` without the E4 code; it now has it.

| Pack | doc_id | Verdict |
|---|---|---|
| code-go / Part_1 | `4a379ae4228af6e2` | fix |
| code-go / Part_1 | `88d0c26177f7877c` | fix |
| code-go / Part_1 | `05809df4f85761c5` | fix |

## Dropped by cleaning, correctly (E1, E2) (8)

**What it is.** Cleaning removed these docs completely. Each starts with a `Code generated … DO NOT EDIT` header, so they are generated code (E1). Two of them (`d0b99f0f8a8caaeb` and `12450bcb472f6610`, both `.pb.go` files) also end in a large gzipped descriptor as a byte array (E2). The notes in the label files say "Correctly dropped by cleaning". The viewer shows "No matching doc_id" for any dropped doc, which is not a reason and is not used in the notes.

**What to do.** Nothing. If a second reader disagrees with any row, change its verdict to `fix` and say what was good about the doc.

| Pack | doc_id | Verdict |
|---|---|---|
| code-go / Part_1 | `7643d5cdbac0d774` | drop |
| code-go / Part_1 | `9506fec46784a06e` | drop |
| code-go / Part_1 | `fe6a2b7719890828` | drop |
| code-go / Part_1 | `95e214af76eb5d16` | drop |
| code-go / Part_1 | `b86a73c3741ef72f` | drop |
| code-go / Part_1 | `d0b99f0f8a8caaeb` | drop |
| code-go / Part_2 | `12450bcb472f6610` | drop |
| code-go / Part_2 | `87e58585404b217d` | drop |

## Other notes

- **Withdrawn labels.** Two docs (`0be515fddd3bb1cc`, `dbbb98d4c8762c0c`) were first labelled A6 for "CJK and Latin in one word". They are Chinese comments next to ASCII code (`//构造url`), which is normal, so they are now `clean`.
- **Placeholders are replaced in different ways.** The dataset's `<PASSWORD>` became `EXAMPLE_PASSWORD`, `<KEY>` became `EXAMPLE_KEY`, and `<NAME>` became `AUTHOR`. None of these changes broke the sampled code, but the rule is worth a line in the medicine sheet.
- **CRLF.** `a310b1f78ba5bb79` had 121 carriage returns removed and nothing else changed. That is fine.
