# Dedup results v1

The measurements behind `dedup_design_v1.md`, for discussion. The design states the decisions; this file holds the numbers, and grows as new runs come in.

**How to read it**
- **Final** means measured by TSAI on the approved input with committed code. It changes only if the rules change.
- **Estimate** means computed by us from TSAI's files without `dedup.py`. Removal counts from `dedup.py` itself are given separately; they are local (no urls) until TSAI runs `jobs/2026-11-10-dedup.md`.
- **Local** means a test run on raw (not cleaned) sample v0 parts. It shows the code works and gives findings for the hand review; the TSAI run supersedes its counts.
- Every number is for the Week-2 tokenizer sample v0 (1.4 million documents). Applied to the full data, the counts will differ.

**12 Nov 2026: the 5 Nov run is superseded.** TSAI answered in G1 on 12 Nov that #244 changes the cleaner, so the cleaned sample of 3 Nov is out of date. After #244 merges, TSAI reruns the cleaning on sample v0, the overlap measurement is run again on the new cleaned output, and the `dedup.py` job runs on that output. The 5 Nov results are not used for the remove list. Section 1 and the E4 part of section 3 come from the 5 Nov run; they stay here as the record until the rerun's numbers replace them.

**Licence (TSAI, 12 Nov).** These runs treat all 38 packs as usable (`default_licence_usable: true` and an empty `licence_usable` in `dedup.json`). This holds for this experiment only. The licences of `code-js-ts` and `ind-hi-hplt` are **not verified**: G10's licence table leaves both open (`code-js-ts`: training-use rights need further verification; `ind-hi-hplt`: CC0 covers the packaging only, and the text keeps its web terms). G10 owns the final licence decision.

## 1. TSAI 38-pack run of 5 Nov (superseded; see the top)

Job `jobs/2026-11-04-overlap.md`, approved by the Data A lead; run by TSAI on a CPU host on 5 Nov 2026 at commit `86ecdd4`. Results: `jobs/results/2026-11-04-overlap/` (merged to `main` in PR #307). Input: the 38 cleaned sample v0 packs, 86 parts, train + held-out.

| | |
|---|---|
| Documents | 1,416,236 (7 empty) |
| Wall time, peak memory | 3,351 s (56 min), 9.6 GiB (9,835.6 MiB); requested 60 min, 32 GiB |
| Pairs that share a shingle | 2,347,235,732 |
| Pairs stored (word Jaccard ≥ 0.50) | 32,738 |
| Pairs by word Jaccard ≥ 0.70 / 0.75 / 0.80 / 0.85 / 0.90 / 0.95 | 4,620 / 3,396 / 2,407 / 1,576 / 860 / 314 |
| Qualifying pairs (after the family rules) | **2,711**: 98 H1 (71 exact groups, 150 documents) + 2,613 H2. One H1 group is the 7 empty documents (21 pairs; observation 6) |
| Within pack / cross pack | 2,661 / **50** |
| Train ↔ held-out pairs among the qualifying pairs | 63 |
| `doc_id`s used by two or more documents | 0 |

The word-Jaccard counts cover every pair, before the family rules; the qualifying pairs are what dedup acts on.

*Source:* `overlap_summary.json` (documents, time, memory, pairs at each threshold, H1 groups, qualifying pairs by rule); `overlap_matches.csv` (within / cross pack). The train ↔ held-out count (63) is confirmed from `overlap_docs.parquet` (`matrix_confirmation.md`).

### Per pack

Where each column comes from (all files in `jobs/results/2026-11-04-overlap/`):

| Column | Source |
|---|---|
| Documents | `overlap_summary.json`, `documents` |
| Pairs ≥ 0.80 | `overlap_by_pack.csv`, level `0.80`, same pack on both sides (raw word score, before the family rules) |
| Qualifying | `overlap_matches.csv`, `stage = within_pack` (pairs that pass the family rules) |
| Docs matched, own pack | `overlap_matrix_counts.csv`, the diagonal (`source_a = source_b`) |
| Docs matched, other packs | `overlap_matches.csv`, `stage = cross_pack`: distinct documents per pack |
| Est. removed, Est. % | **Our estimate**, computed from `overlap_matches.csv`: within-pack matches joined into union-find clusters, one survivor per cluster. Rule 0 is not applied, because `overlap_matches.csv` has no split column; held-out survivors can shift a few |

TSAI kept the large files (`overlap_docs.parquet`, `overlap_pairs.csv`) out of the repo. This table was computed before they arrived. They were received separately on 10 Nov, match the summary's SHA-256, and were used for the matrix confirmation (`matrix_confirmation.md`) and the `dedup.py` run below.

| Pack | Documents (train + held-out) | Pairs ≥ 0.80 | Qualifying | Docs matched, own pack | Docs matched, other packs | Est. removed | Est. % |
|---|---:|---:|---:|---:|---:|---:|---:|
| `cadj-commits` | 75,579 | 1,094 | 1,094 | 1,664 | 9 | 895 | 1.18% |
| `cadj-notebooks` | 15,732 | 15 | 15 | 27 | 0 | 14 | 0.09% |
| `cadj-stackexchange` | 41,805 | 208 | 208 | 384 | 0 | 199 | 0.48% |
| `code-cpp` | 55,195 | 6 | 5 | 10 | 2 | 5 | 0.01% |
| `code-go` | 77,765 | 8 | 6 | 12 | 0 | 6 | 0.01% |
| `code-java` | 85,518 | 8 | 9 | 10 | 5 | 6 | 0.01% |
| `code-js-ts` | 117,208 | 1 | 1 | 2 | 2 | 1 | 0.00% |
| `code-python` | 73,305 | 1 | 24 | 13 | 4 | 9 | 0.01% |
| `code-rust` | 58,795 | 3 | 530 | 66 | 3 | 58 | 0.10% |
| `en-dclm` | 60,802 | 14 | 14 | 19 | 5 | 11 | 0.02% |
| `en-fineweb-edu` | 72,100 | 7 | 7 | 14 | 11 | 7 | 0.01% |
| `en-nemotroncc` | 89,183 | 23 | 19 | 27 | 6 | 15 | 0.02% |
| `en-nemotroncc-synth` | 198,877 | 1 | 1 | 2 | 1 | 1 | 0.00% |
| `ind-bn-fw2` | 10,750 | 0 | 0 | 0 | 1 | 0 | 0 |
| `ind-bn-sangraha-v` | 10,213 | 0 | 0 | 0 | 1 | 0 | 0 |
| `ind-gu-fw2` | 23,011 | 0 | 0 | 0 | 0 | 0 | 0 |
| `ind-hi-fw2` | 14,257 | 0 | 0 | 0 | 1 | 0 | 0 |
| `ind-hi-hplt` | 8,719 | 0 | 0 | 0 | 0 | 0 | 0 |
| `ind-hi-indiccorp` | 111,851 | 29 | 5 | 7 | 1 | 4 | 0.00% |
| `ind-hi-sangraha-s` | 8,368 | 545 | 540 | 37 | 0 | 35 | 0.42% |
| `ind-hi-sangraha-v` | 14,831 | 134 | 134 | 18 | 2 | 17 | 0.11% |
| `ind-kn-fw2` | 7,764 | 0 | 0 | 0 | 3 | 0 | 0 |
| `ind-kn-sangraha-s` | 5,222 | 20 | 0 | 0 | 0 | 0 | 0 |
| `ind-kn-sangraha-v` | 8,448 | 0 | 0 | 0 | 3 | 0 | 0 |
| `ind-ml-fw2` | 19,161 | 0 | 0 | 0 | 0 | 0 | 0 |
| `ind-mr-fw2` | 11,365 | 0 | 0 | 0 | 5 | 0 | 0 |
| `ind-mr-sangraha-v` | 12,299 | 0 | 0 | 0 | 5 | 0 | 0 |
| `ind-or-fw2` | 34,012 | 0 | 0 | 0 | 0 | 0 | 0 |
| `ind-sa-fw2` | 5,721 | 13 | 13 | 23 | 0 | 12 | 0.21% |
| `ind-ta-fw2` | 6,824 | 0 | 0 | 0 | 1 | 0 | 0 |
| `ind-ta-sangraha-s` | 4,372 | 55 | 1 | 2 | 0 | 1 | 0.02% |
| `ind-ta-sangraha-v` | 6,826 | 0 | 0 | 0 | 1 | 0 | 0 |
| `ind-te-fw2` | 5,009 | 0 | 0 | 0 | 2 | 0 | 0 |
| `ind-te-sangraha-s` | 4,468 | 32 | 0 | 0 | 0 | 0 | 0 |
| `ind-te-sangraha-v` | 8,174 | 0 | 0 | 0 | 2 | 0 | 0 |
| `math-finemath` | 28,830 | 18 | 3 | 6 | 2 | 3 | 0.01% |
| `math-megamath` | 17,803 | 100 | 32 | 20 | 1 | 14 | 0.08% |
| `sci-finepdfs` | 6,074 | 0 | 0 | 0 | 0 | 0 | 0 |
| **All** | **1,416,236** | **2,335** | **2,661** | **2,363** | **79** | **1,313** | **0.09%** |

**Estimate, with the cross-pack pass:** 1,351 documents removed (0.095%); the cross-pack pass adds 38. *Source:* our union-find estimate over all of `overlap_matches.csv`.

**`dedup.py` (local, 10 Nov, no urls):** 1,345 documents removed (0.095%): 1,289 H2 and 56 H1; 1,309 within a pack and 36 across packs; 0 held-out removed; 63 train copies removed by rule 0. The 6 fewer than the estimate are empty documents: `dedup.py` sets aside the matches between the 7 empty documents and lists them in `empty_documents.csv` (observation 6). *Source:* `jobs/logs/2026-11-10-dedup-local.txt`, section 4. TSAI's run with urls can change which copy survives, not how many are removed.

**By family (estimate, within-pack):** code-adjacent 1,108 of 133,116 (0.83%); code 85 of 467,786 (0.02%); Indic 69 of 341,665 (0.02%); English 34 of 420,962 (0.01%); math 17 of 46,633 (0.04%); science 0 of 6,074. *Source:* the per-pack table, summed by the pack name's prefix.

### Cross-pack pairs (50)

| Packs | Qualifying pairs |
|---|---:|
| `code-java` × `code-js-ts` | 8 |
| `en-fineweb-edu` × `en-nemotroncc` | 5 |
| `ind-mr-fw2` × `ind-mr-sangraha-v` | 5 |
| `code-cpp` × `code-java` | 4 |
| `en-dclm` × `en-fineweb-edu` | 4 |
| `cadj-commits` × `code-python` | 4 |
| `ind-kn-fw2` × `ind-kn-sangraha-v` | 3 |
| `cadj-commits` × `code-rust` | 3 |
| `code-cpp` × `code-js-ts` | 2 |
| `ind-te-fw2` × `ind-te-sangraha-v` | 2 |
| Other pack pairs (1 each) | 10 |

*Source:* `overlap_matches.csv`, `stage = cross_pack`, counted by pack pair.

**14 of these 50 are between empty documents:** all 8 `code-java` × `code-js-ts`, all 4 `code-cpp` × `code-java` and both `code-cpp` × `code-js-ts` pairs (observation 6). The real cross-pack pairs number 36.

**Pairs affected by the Data B pack order** (`source_priority_v1.md`, rule 4): **23 of the 50** have a Data B pack on at least one side. 14 are between two Data B packs, mostly the same Indic language in `fw2` and `sangraha-v` (`ind-mr` 5, `ind-kn` 3, `ind-te` 2; `ind-hi`, `ind-bn`, `ind-ta` 1 each; `ind-hi-indiccorp` × `ind-hi-sangraha-v` 1). 9 are between `cadj-commits` and a code pack (`code-python` 4, `code-rust` 3, `code-cpp` 1, `code-java` 1). The other 27 are between two Data A packs (14 of them between empty documents). Rule 4 decides a pair only if the copies are still tied after rules 0–3. TSAI approved this order in G1 on 10 Nov 2026. *Source:* `overlap_matches.csv`, by each side's pack.

### Observations for discussion

1. **`cadj-commits` holds two-fifths of all qualifying pairs** (1,094 of 2,711) and 45 of the 98 exact pairs; by our estimate it would lose 1.18% of its documents, the only pack above 1%. A sample should be read to confirm they are true copies (for example repeated commit messages) before they are removed.
2. **The code token pass finds what word scores miss.** `code-rust` has 3 pairs at word Jaccard ≥ 0.80 but 530 qualifying pairs; `code-python` has 1 and 24. These come from the token pass, which ignores comments and licence headers. The code hand review (0.85) should look at these.
3. **E4 signal: the Indic `sangraha-s` packs.** `ind-kn-sangraha-s` (20 pairs ≥ 0.80), `ind-te-sangraha-s` (32) and `ind-ta-sangraha-s` (55) end with 0, 0 and 1 qualifying pairs. The likely cause is the 50-word minimum, since Indic words are longer and fewer (Risk 2). In contrast, `ind-hi-sangraha-s` keeps 540 of 545, all among only 37 documents, so a few near-identical documents form large clusters. These packs are the first place to run E4.
4. **Cross-pack overlap is small and mostly expected:** English web crawls, the `fw2` and `sangraha-v` versions of the same Indic language, and `cadj-commits` with code packs. The pairs between code languages (Java, JS/TS, C++) are not shared files: all 14 are between empty documents (observation 6).
5. **Cleaning changed the math counts slightly:** `math-finemath` has 28,830 documents after cleaning against 29,434 raw; `math-megamath` 17,803 against 17,816.
6. **7 documents are empty after cleaning:** 1 `code-cpp`, 4 `code-java`, 2 `code-js-ts`, all train (0 words and 0 shingles in `overlap_docs.parquet`; their `doc_id`s are in `matrix_confirmation.md`). They pass `clean.py`'s empty-output check (`out.strip()`) but have no words after normalisation, probably only invisible characters, so cleaning kept them. They share one H1 key, so `overlap.py` counts them as one exact group: 21 of the 98 H1 pairs and 14 of the 50 cross-pack pairs, inflating 8 code cells of the source matrix. `dedup.py` sets their matches aside and lists them in `empty_documents.csv`; they stay in the data. Dropping them is a cleaning rule change for spec v1.1, separate from the speed fix, which must keep `clean.py`'s output byte-identical; `empty_documents.csv` gives their IDs to whoever owns that change.

## 2. Local runs (raw sample v0 parts)

### English packs (Aneesha Das, 4 Nov)

`en-dclm`, `en-fineweb-edu`, `en-nemotroncc`, `en-nemotroncc-synth`; 426,508 documents; 845 s, 3.4 GB. Raw word scores, before the family rules. *Source:* the run log, `jobs/logs/2026-11-04-overlap-en-local.txt`.

| | Within pack | Cross pack | All |
|---|---:|---:|---:|
| Exact (H1) pairs | 16 | 0 | 16 |
| Pairs at word Jaccard ≥ 0.80 | 44 | 11 | 55 |

- H1: 9 groups, 21 documents, all in `en-nemotroncc`.
- Pairs at ≥ 0.70 / 0.75 / 0.80 / 0.85 / 0.90 / 0.95: 135 / 90 / 55 / 43 / 33 / 25.
- **Finding:** short template pages that differ only in a name or date score 0.82–0.85; this is why H2 has a minimum length.

### Five packs (Vijay Patil, 4 Nov)

`code-rust`, `en-fineweb-edu`, `ind-hi-hplt`, `ind-mr-sangraha-v`, `math-finemath`; 183,976 documents; 571 s, 2.76 GiB. With the family rules. *Source:* the run's transcript and result snapshots in `jobs/logs/2026-11-04-overlap-local/`.

- 0 H1 groups; 372 qualifying H2 pairs: 371 within packs, 1 cross-pack (`en-fineweb-edu` × `math-finemath`).
- Largest share: `code-rust`, 57 of 60,738 documents with a match in their own pack (0.09%).

### Math packs, E1 (Kunal Sinha, 4 Nov)

`math-finemath`, `math-megamath`; 47,250 documents; 97 s, 1.0 GB. Config `overlap_math.json`, log `jobs/logs/2026-11-04-overlap-math-local.txt`. *Source:* that run's `overlap_summary.json`, `overlap_pairs.csv`, `overlap_matches.csv` and `overlap_docs.parquet` (local, in `out/overlap_math/`, not in the repo); the hand review also read the document text from the input parts. Gold IDs were checked against `teams/01-data-a/gold/math-*_gold.csv`.

| | |
|---|---|
| H1 exact groups | 0 |
| Pairs by word Jaccard ≥ 0.70 / 0.75 / 0.80 / 0.85 / 0.90 / 0.95 | 369 / 243 / 131 / 68 / 46 / 18 |
| Of the 46 at ≥ 0.90: qualify / rejected by the numbers rule | 36 / 10 |
| Qualifying: within `megamath` / within `finemath` / cross-pack | 32 / 3 / 1 |
| Train ↔ held-out qualifying pairs | 1 |
| Gold IDs present in this input | 0 of 112 |

**Hand review** (all 10 rejected pairs and the lowest-scoring kept pairs):
1. **The numbers rule rejects true copies with a different header.** Two pairs are the same page saved twice (Jaccard 0.987 and 0.972), differing only in a date line ("Dec 10, 2015 · 15 minute read") or a number in the title ("UVa 11357"), plus Markdown formatting. Both pairs share their URL.
2. **Template pages pass 0.90.** The largest cluster (7 documents) is slideserve.com pages: different presentations ("projectile motion", "the preprocessor", …) inside about 117 words of identical site boilerplate. Only the title differs, so they are not copies of one document.
3. **The rule works where it should:** two chemistry textbook chapters with different worked values are kept apart.
4. **A same-URL copy is missed just below 0.90:** reference.com's "examples of quadrilaterals" is in `finemath` train and `megamath` held-out with the identical URL, at 0.894.
5. **The gold harm check cannot run on the sample:** none of the 112 math gold IDs are in it.

Per-pack `jaccard_matrix.py` outputs for the two math packs (histogram, matrix, pairs with shingle counts) are in `out/jaccard_math/` on the local machine; they match the within-pack counts above.

## 3. Checks on the week-1 diagnosis packs and E4 (11 Nov)

### Harm check (pass)

The gold sets come from the week-1 diagnosis packs, not from sample v0, so the harm check on the 38-pack run was `not_testable`. It was run on the 4 diagnosis packs on hand, through the production order: `clean.py` (main, SHA-256 `d3464bda…`), then `overlap.py`, then `dedup.py` with `gold_dirs` set. It was run twice on the same overlap output: run 1 with the gold files in this branch, run 2 adding the `cadj-commits` gold file from `main`. Log: `jobs/logs/2026-11-11-dedup-harm-diag-local.txt` (counts and hashes only).

| | |
|---|---|
| Packs | `math-finemath`, `math-megamath`, `sci-finepdfs` (cleaned), `cadj-commits` (raw: `clean.py` has no rules for it) |
| Documents after cleaning | 1,964 |
| Gold IDs present, run 1 | **314**: `math-finemath` 86, `math-megamath` 26, `sci-finepdfs` 202 (this branch has no `cadj-commits` gold file) |
| Gold IDs present, run 2 | **727**: the 314 above plus `cadj-commits` 413 (all 413 IDs in its gold file) |
| Qualifying duplicate pairs | 0 |
| Documents removed / gold removed | 0 / **0** in both runs |
| Gold dropped by `clean.py` | 0 |

The result is a pass, but a check where nothing is removed is weak on its own. The stronger evidence is the margin: **only one pair in the 1,964 documents reaches word Jaccard ≥ 0.50**: two `cadj-commits` documents at 0.716. Both are `cadj-commits` gold documents (run 2), and both are kept, because 0.716 is below the 0.80 prose threshold. No math or science gold document is in any pair at ≥ 0.50, so none came near the 0.80 or 0.90 thresholds. Limits: 4 of the 13 Data A packs have gold here, and each pack is checked on its own.

**The `cadj-commits` gold file (run 2)** is `teams/02-data-b/gold/cadj-commits_gold.csv` on `main` (added in commit `6b09da4`, 2 Nov; SHA-256 `ba4da5c2…`). It is not in this branch, which has not been synced with `main`, and it was not added here because it is a Data B file. When this PR merges, `main` already has it.

**To reproduce run 2** from the repo root, after the clean and overlap steps in the log:

```bash
git fetch upstream
mkdir -p out/gold_main
git show 6b09da4:teams/02-data-b/gold/cadj-commits_gold.csv > out/gold_main/cadj-commits_gold.csv
sha256sum out/gold_main/cadj-commits_gold.csv     # ba4da5c2…
# config: copy out/dedup_diag.json to out/dedup_diag2.json, set
#   "gold_dirs": ["teams/01-data-a/gold", "teams/02-data-b/gold", "out/gold_main"], "out": "out/dedup_diag2"
python teams/01-data-a/dedup/dedup.py --config out/dedup_diag2.json   # harm check: pass
```

### E4, measured part: the 50-word minimum and Indic text

**Source:** TSAI's 38-pack run of sample v0 (all 1,416,236 documents, Data B's Indic packs included), not the gold sets or the week-1 diagnosis packs. No document text was read.

**Method:**
1. From `overlap_pairs.csv` (every pair at word Jaccard ≥ 0.50), keep the pairs inside each `sangraha-s` pack with word Jaccard ≥ 0.80.
2. Check each pair against `overlap_matches.csv`: did it qualify under the family rules?
3. For each pair that did not qualify, look up both documents' `words` in `overlap_docs.parquet`, the same count `overlap_rules.py` uses for the 50-word minimum.

For prose (which includes Indic), a pair qualifies only if its word Jaccard is ≥ 0.80 and both documents have ≥ 50 words. Every pair kept in step 1 already passes the score, so the length rule is the only possible reason for a rejection; the "Rejected: other" column below is 0, which confirms it. The shares of documents under 50 words come from the same `words` column, over every document of each pack.

Every near-identical pair (word Jaccard ≥ 0.80) that was rejected in the three `sangraha-s` packs was rejected because a document has fewer than 50 words:

| Pack | Pairs ≥ 0.80 | Qualify | Rejected: a document < 50 words | Rejected: other |
|---|---:|---:|---:|---:|
| `ind-kn-sangraha-s` | 20 | 0 | 20 | 0 |
| `ind-te-sangraha-s` | 32 | 0 | 32 | 0 |
| `ind-ta-sangraha-s` | 55 | 1 | 54 | 0 |
| `ind-hi-sangraha-s` (for comparison) | 545 | 540 | 5 | 0 |

Share of documents under 50 words, by family: **Indic 19.9%**, code 14.1% (code uses a 20-line minimum, not words), science 2.8%, English 1.7%, math 1.4%, code-adjacent 1.2%. Among the Indic packs it is concentrated in `ind-hi-indiccorp` (56.3%, median 42 words) and the `sangraha-s` packs (14.5–17.1%); the `fw2` and `sangraha-v` packs are 0–3%.

So the 50-word minimum, set on English, leaves about a fifth of Indic documents to H1 only (Risk 2). Still open: a reader to judge whether the 106 rejected `sangraha-s` pairs are true copies. If they are, a lower word minimum for Indic is the fix (a minimum in characters would not separate these pairs; see the rebuild below); it changes `overlap_rules.py` and needs an overlap rerun.

### E4, rebuilt from the raw text (11 Nov)

**Source:** the same 106 pairs, from TSAI's `overlap_pairs.csv`, `overlap_matches.csv` and `overlap_docs.parquet`, with each document's text taken from the raw sample-v0 parts of the three packs (all 6 match `inputs/sample_v0/SHA256SUMS`). `e4_review.py` rebuilds each document's H1 key and 5-grams as `overlap.py` does. Document text stays in the git-ignored `out/e4/`; only counts are given here.

**Raw text versus what TSAI scored.** TSAI scored the cleaned parts, and cleaning changed two of the three packs:

| Pack | Documents, raw → cleaned | Cleaned documents whose raw text gives TSAI's word and 5-gram counts | Rejected pairs whose raw text gives TSAI's score |
|---|---:|---:|---:|
| `ind-kn-sangraha-s` | 5,244 → 5,222 | 4,615 (88.4%) | 20 of 20 |
| `ind-te-sangraha-s` | 4,829 → 4,468 | 4,275 (95.7%) | 32 of 32 |
| `ind-ta-sangraha-s` | 4,372 → 4,372 | 4,372 (100%) | 54 of 54 |

Every rejected pair gives TSAI's score from the raw text (to its 6 decimals), so all 106 were rebuilt from the text TSAI scored, even in the two packs that cleaning changed.

**What the pairs are, by the numbers** (no reading needed):

| Pack | Rejected pairs | Distinct documents | Clusters (sizes) | Shorter document of each pair | Words that differ, each side | Would qualify with a minimum of 40 / 30 / 20 / 10 words |
|---|---:|---:|---|---|---|---|
| `ind-kn-sangraha-s` | 20 | 10 | 2 (8, 2) | 17 words (1 pair), 30–39 (19) | 1–4 | 0 / 19 / 19 / 20 |
| `ind-te-sangraha-s` | 32 | 9 | 1 (9) | 30–39 (29), 40–49 (3) | 1–5 | 3 / 32 / 32 / 32 |
| `ind-ta-sangraha-s` | 54 | 16 | 1 (16) | 30–39 (54) | 1–4 | 0 / 54 / 54 / 54 |

- The 106 pairs come from only **35 documents in 4 clusters**. Every pair is within the train split, and the two documents differ by only 1–5 words per side. That fits either short copies or one fixed text with a word changed; only a reader can say which.
- A character minimum would not separate them either: their H1 keys have 148–366 characters.
- **What is at stake:** with one document kept per cluster, a 30-word minimum would remove 30 documents of the 14,062 in the three packs (31 with a 10-word minimum).

**Across all `ind-*` packs** (TSAI's outputs only): the 50-word minimum rejects 135 prose pairs ≥ 0.80 with an `ind-*` side, among 69 documents, and no other rule rejects any. A minimum of 40 / 30 / 20 / 10 words would admit 3 / 106 / 111 / 135 of them (3 / 35 / 42 / 69 documents). So although 19.9% of Indic documents are under 50 words, few of them are in near-identical pairs: lowering the minimum affects at most 69 documents across the 22 Indic packs.

**Still open: the reading.** The blind review sheets are ready in `out/e4/review/<pack>/`, on the local machine and not in the repo. Each sheet shows the two texts of every pair side by side, in random order, without scores, lengths or IDs, and comes with a `labels.csv` to fill in (copy, template, different or unsure). The labels must come from a human reader of the language, and theirs are the E4 result.

To repeat this, run `python3 -B teams/01-data-a/dedup/e4_review.py` from the repo root. It needs the raw parts in `inputs/sample_v0/packs` and TSAI's outputs in `out/overlap_tsai`; its tests are in `tests/test_e4_review.py`.

## 4. Still to come

In the order TSAI set on 12 Nov. Updated 13 Nov: TSAI confirmed the #244 cleaning rerun is complete
(86 parts, 1,414,996 cleaned documents). The overlap request now pins merged speed commit `7526194`, with a fresh
115-test log and synthetic 38-pack hand-off validation. Those smoke results do not replace the real-data results
still needed below; see `jobs/2026-11-12-overlap-rerun.md` for the input provenance and execution requirements.

| Result | From | Needs |
|---|---|---|
| The cleaned sample with the #244 cleaner | TSAI's cleaning job on sample v0 | Complete: 86/86 parts, 0 errors, 1,414,996 rows; provenance in the overlap rerun request |
| Overlap measurement on the new cleaned sample | TSAI's rerun of `overlap.py` (`jobs/2026-11-12-overlap-rerun.md`) | The cleaned sample above; lead approval |
| Reviewed source matrix from the rerun | `confirm_matrix.py` on the returned files → `dedup/overlap_matrix.csv` | The rerun's results. The matrix there now is from 5 Nov |
| Final removal counts and remove list, with urls | TSAI's run of `jobs/2026-11-10-dedup.md` on the rerun's output | The rerun's results, then lead approval. Licence: all 38 packs usable for this experiment only (see the top). On the 5 Nov run, without urls: 1,345 |
| Groups whose survivor F2 removes: count and list | The F2 step, after dedup (Clean → Dedup → F2) | F2's removals and the new dedup run's `dedup_groups.csv`; the export is implemented, but the F2 count/list remains downstream work |
| Harm check with the #244 cleaner | Local, on the 4 diagnosis packs | Still needs to run with the merged cleaner; sample-v0 and synthetic `not_testable` checks do not replace it |
| Hand review: prose 0.80, code 0.85, `cadj-commits` sample | Pairs from the TSAI rerun | `overlap_pairs.csv` and text |
| E4: are the rejected `sangraha-s` pairs true copies? | A human reader of Kannada, Telugu and Tamil | `e4_review.py` run again on the rerun's outputs, since the #244 cleaner can change these pairs; then the reader's labels on the new blind sheets |

**Done on 10 Nov, on the 5 Nov run:** the reviewed source matrix, `dedup/overlap_matrix.csv`, byte-identical to TSAI's (`matrix_confirmation.md`); `dedup.py` written and run locally on TSAI's outputs (1,345 removed, above). Both are redone on the rerun.
