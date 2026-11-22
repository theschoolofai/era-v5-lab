# Audit collation: every finding, the rule behind it and its proposal

Week 4, tasks 4.4 and 5.1. 22 Nov 2026. Collected by `TEJASKUMAR-REDDY-J` from `day_D3.md` and the audit PRs #68, #71, #72, #76, #78 and #79 of patilvijay23/era-v5-lab. No cleaner rule is changed here.

The audits read different cleaned outputs. So every labelled document was run again through the current `spec_v1_1/clean.py`, rule by rule, to see which findings are still there and which rule causes each.

| File | What it holds |
|---|---|
| [`collation_findings.csv`](collation_findings.csv) | 29 findings: audit, documents, disease, current rule, whether it is still there, proposal, next step |
| [`collation_docs.csv`](collation_docs.csv) | 313 labelled documents: label, what the current cleaner does, the rules that acted in order |
| [`collation_scope.csv`](collation_scope.csv) | Documents each rule fixes and drops on the English and math train parts |
| [`collation_replay.py`](collation_replay.py) | The script that writes the last two |

The files hold ids, rule ids and counts only: no document text and no personal data.

## Coverage

| Audit | Pack | Labels | Current cleaner: fix / keep / drop |
|---|---|---:|---|
| `day_D3.md` | 29 label files | 71 | 10 / 17 / 44 |
| #68 | en-dclm | 35 | 28 / 0 / 7 |
| #71 | math-finemath, math-megamath | 35 | 28 / 0 / 7 |
| #72 | code-go | 45 | 37 / 0 / 8 |
| #76 | en-nemotroncc-synth | 76 | 75 / 0 / 1 |
| #78 | code-js-ts | 45 | 41 / 0 / 4 |
| #79 | sci-finepdfs | 6 of 35 | 6 / 0 / 0 |
| **Total** | | **313** | **225 / 17 / 71** |

- **#79:** its label CSV is not in the PR yet, so only the 6 `fix` and `drop` documents named in the report are here.
- **Not here:** the Gujarati and Marathi supplement of `day_D3.md`, and the packs with no audit PR on 22 Nov: code-cpp, code-java, code-python, code-rust, en-fineweb-edu and en-nemotroncc.
- **#68 tally:** the report and the CSVs agree: 25 `fix`, 2 `clean`, 1 `drop`, and 7 dropped by the cleaner (2 right, 3 acceptable, 2 wrong).

## Main findings

1. **`DA-C3-003` drops good documents, and only one pack has a proposal.** It drops a document whose last word is a word like `this`, `at` or `by`. On the four English packs it drops 3,019 documents, 1,959 of them over 2,000 characters. It is 707 of the 1,155 drops on en-dclm, and 14 of the 22 English drops in `day_D3.md`. Both wrong drops of #68 and the one of #76 come from it.
   - The endings of 40 of the 707 en-dclm drops were read (one reader, endings only). About 32 end in site chrome or in a link or contact that was already removed (`Share This`, `find us at`), about 6 are cut off, one is a finished sentence that ends in a curly quote, and one is a raw feed.
   - #76's `DA-C3-008` withdraws the rule on en-nemotroncc-synth, which has 63 of the 3,019. Withdrawing it on en-dclm also brings back #68's documents whose drop was right or acceptable, so it needs a narrower test.
2. **`DA-C7-002` drops 1,498 of 17,647 megamath documents (8.5%)** because the text mentions figures. Two of them are labelled `fix` in #71, one as good content.
3. **#71 read an older output.** In it the cleaner had dropped 13 megamath documents; the current cleaner drops 2,550. On finemath it is 600 and 2,609. Its labels hold for the documents still kept.
4. **The rules #71 could not name:** the deleted reference and author lines are `DA-C5-006`, and the deleted formula lines are `DA-C2-001`. `DA-C5-006` removes 690 comma-list lines in 199 megamath documents; about 607 of them look like reference entries (a rough pattern, not read).
5. **`day_D3.md` is partly out of date.** Of its 56 dropped documents, 12 (all Indic) are kept now and 44 are still dropped; `collation_docs.csv` names the rule for each. All 6 visarga documents come through unchanged. The 9 licence-header documents still have licence text at the top.
6. **Cleaner damage with no proposal:** `DA-A6-001` changes the Cyrillic letters of two Go test fixtures (#72).

## Conflicts to settle before any of these rules is adopted

- **#75 and #76 replace the same rules** (`DA-C2-003` and `DA-F1-005`) on en-nemotroncc-synth. With each PR's cards in place of the rules they replace, three audited documents differ:

  | doc_id | phone masks now | with #75 | with #76 |
  |---|---:|---:|---:|
  | `8aecb4bed3222e59` | 1 | 2 | 0 |
  | `417036b98dd9380a` | 1 | 2 | 0 |
  | `d6e8da1b50823198` | 1 | 2 | 1 |

  #76 judges the first two as public contacts and marks the third for review. #75 masks every copy of a number that is masked once. One policy is needed for a number that looks public in one place and private in another.
- **Rule IDs of #75:** `DA-A2-009`, `DA-B3-002`, `DA-B4-014` and `DA-C2-005` are already in `rules/registry.json`, and `DA-C2-005` was also an English rule dropped in `decisions_english.md`. The next free numbers on 22 Nov, counting #71 and #76, are `DA-A2-010`, `DA-B3-012`, `DA-B4-016` and `DA-C2-009`. `DA-F1-007` is free.

## #68: each finding and its medicine

| Finding in #68 | Current rule | Medicine |
|---|---|---|
| cp1252 quotes deleted | `DA-A2-008` | #75 `DA-A2-009` |
| Lines cut inside code | `DA-C2-003` | #75 `DA-C2-005`; record fields and formula lines are still cut |
| Math removed inside dollar signs | `DA-B4-010` | #75 `DA-B4-014`; sets that start with a letter, minus or bracket are still cut (2 en-dclm documents, up to 3 synth) |
| Phone masked once | `DA-F1-005` | #75 `DA-F1-007`; a `+44` copy of the number is not matched; conflict above |
| `<s>` and `</s>` kept | none | #75 `DA-B3-002`; also strips literal examples and code fences |
| Two wrong drops | `DA-C3-003` | **None for this pack** |
| Wrong language, gutted | `DA-D3-003` | **None** |
| Boilerplate (C1), 25 documents | `DA-C1-006`, `DA-C2-003` | **None for this pack** (#76 `DA-C1-013` is synth only, #71 `DA-C1-012` math only) |
| Joined pages (C4), PDF bullets (A3), SEO line (C5) | none | **None** |

The five cards of #75 were checked again on its branch (`2ecacf5f`): gold harm 0 changed and 0 dropped on the four English packs, and `clean()` at 0.97x of spec v1.1's speed on 2,000 documents (the earlier run was 1.02x; runs vary by about 5%).

## How to reproduce

From the repository root, with the raw sample train parts in `<raw>`:

```bash
python -I teams/01-data-a/audit/collation_replay.py docs --raw <raw> --labels teams/01-data-a/audit/collation_docs.csv --out collation_docs.csv
python -I teams/01-data-a/audit/collation_replay.py scope --raw <raw> --out collation_scope.csv
```

`docs` takes its labels from the committed CSV and writes the same file again. Each replay is compared with `clean()` and the script stops on a difference. `clean.py` sha256 `6a57276c0e83312b…`, the same as in #76.

## Limits

- The replay uses the raw tokenizer sample v0 train parts, not corpus-v1 and not the token shards.
- A finding marked "still there" means the same characters or the same drop are in the current output. It does not say how common the problem is. Audited documents were mostly picked from the ones the cleaner changed.
- The 40 endings were read by one person, and the wrong and right drops of `DA-C3-003` are not labelled.
- Not submitted here: new medicines. The ones marked **None** still need a card and a harm test.
