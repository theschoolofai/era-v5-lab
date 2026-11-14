# Matrix confirmation: TSAI's 38-pack overlap run

**Date:** Tuesday 10 November 2026. **By:** Aneesha Das (aneeshads).
**Run confirmed:** job `jobs/2026-11-04-overlap.md`, run by TSAI on 5 Nov 2026 at commit `86ecdd4`, results in
`teams/01-data-a/jobs/results/2026-11-04-overlap/`.
**Superseded (12 Nov):** TSAI reruns the cleaning with #244 and then the overlap measurement, and the 5 Nov results
are not used. This confirmation is repeated on the rerun's results (`jobs/2026-11-12-overlap-rerun.md`), and
`overlap_matrix.csv` is replaced by the rerun's matrix.

## Result

- **Confirmed, three ways.** The source-by-source matrix rebuilt from TSAI's `overlap_matches.csv` is
  **byte-identical** to the returned `overlap_matrix.csv` and `overlap_matrix_counts.csv`:
  - with the row → pack map rebuilt from the part order in the summary: **20 of 20 checks passed**;
  - with the map read from TSAI's `overlap_docs.parquet` (`--docs`): **22 of 22 checks passed**;
  - with the job request's own command, `overlap_report.py --results`: both files byte-identical.
- All 9 of the run's outputs, including `overlap_docs.parquet` and `overlap_pairs.csv`, equal the SHA-256 and size the
  run recorded in `overlap_summary.json`.
- The map rebuilt from the part order equals `overlap_docs.parquet` on **all 1,416,236 rows** (pack and split).
- **One caveat for the reviewed matrix:** 8 cells (code-cpp, code-java, code-js-ts) are inflated by 7 documents that
  are empty after normalisation (0 words, 0 shingles in `overlap_docs.parquet`) and therefore match each other. The
  cells are correct for what `overlap.py` measures, but these are not real duplicates (see "The empty-document group").

## What the matrix is

`overlap_matrix.csv` is a 38 × 38 table. Row pack A, column pack B: the share of A's documents that have at least one
qualifying H1 or H2 match in B. A document counts once per column, however many copies it has. The diagonal is
within-pack and excludes a document matching itself. The matrix is directional: A→B and B→A have different
denominators. `overlap_matrix_counts.csv` holds each cell's numerator (`matched_documents`) and denominator
(`total_documents`).

## Inputs

Downloaded on 10 Nov 2026 from `aneeshads/era-v5-lab`, branch `main`,
`teams/01-data-a/jobs/results/2026-11-04-overlap/`, into `out/overlap_tsai/` (git-ignored; no file is committed).

| File | Bytes | SHA-256 | Equals the summary |
|---|---:|---|---|
| `overlap_matches.csv` | 205,749 | `a3ecfba78e450e60488b5f82d2b562e4fc1cef08012ad100469ae2efb4e18c1b` | yes |
| `overlap_matrix.csv` | 19,866 | `2a049f187456278d9ebab5839fb351efaecc9c16bdae852bc4048aed9b7295bd` | yes |
| `overlap_matrix_counts.csv` | 52,511 | `cef888f81439bd0a943bed83ed7ec25d7b68e808702286f8bea066bbb060b523` | yes |
| `overlap_by_pack.csv` | 238,212 | `1a1b409c122d57083a87ade36a534a7483a0d1e76f74e58a0ecf0db0e03b0a89` | yes |
| `overlap_histogram.csv` | 1,694 | `e2558a34aa961528a4f6e945afc987b5dc8839b3b3f220cd512a59dfa2be342b` | yes |
| `overlap_summary.json` | 272,880 | `a1dec3f4e07153f02979ad92dc017c8c2a3df6458d9f8064817915b0d0b30cb0` | not recorded by the run |
| `overlap_docs.parquet` | 34,454,169 | `15ed5627f10fe220623275331eeb0701186f57c4c694a1496f736f0593d67c9c` | yes |
| `overlap_pairs.csv` | 6,739,846 | `699f2a87bd5f90f4b2d8110c6e0f8b49405f9ccdf363336acc9ace3696230f60` | yes |

`overlap_docs.parquet` and `overlap_pairs.csv` are too large for the repository. They were received separately on
10 Nov 2026, placed in `out/overlap_tsai/` and accepted only because their SHA-256 and size equal the summary's.
`overlap_matrix.npz` (4,407,894 bytes) was not needed.

The run itself: 1,416,236 documents in 38 packs and 86 parts (48 train, 38 held-out); 2,711 qualifying pairs
(98 H1, 2,613 H2; 2,661 within a pack, 50 across packs); 7 empty documents.

## Steps

**1. Stage the returned files** (from the repository root):

```sh
mkdir -p out/overlap_tsai && cd out/overlap_tsai
B=https://raw.githubusercontent.com/aneeshads/era-v5-lab/main/teams/01-data-a/jobs/results/2026-11-04-overlap
for f in overlap_summary.json overlap_matches.csv overlap_matrix.csv overlap_matrix_counts.csv overlap_by_pack.csv overlap_histogram.csv run.log; do curl -sSfL -o "$f" "$B/$f"; done
cd ../..
```

**2. Run the confirmation with the map rebuilt from the part order:**

```sh
python3 teams/01-data-a/dedup/confirm_matrix.py --results out/overlap_tsai
```

`confirm_matrix.py` (new, in this folder) reads no document text and writes only to `out/matrix_confirmation/`. It
uses `overlap_report.write_matrix`, the same function `overlap.py` used to write the returned matrix. It does this:

1. Checks the run: `status` is `complete`, and the 38 packs equal the config's `expected_packs`.
2. Hashes every returned output and compares its SHA-256 and size with `overlap_summary.json`.
3. Builds the row → pack map and checks it against the matches (see "Row → pack map" below).
4. Rebuilds `overlap_matrix.csv` and `overlap_matrix_counts.csv` from `overlap_matches.csv` and compares them with the
   returned files byte for byte.
5. Checks the content: 38 × 38 with packs in sorted order, every denominator equal to the pack's document count, every
   share equal to matched ÷ total to 10 decimals.
6. Finds the group of empty documents (the H1 group whose size equals `empty_documents`) and rebuilds the matrix
   without the pairs inside it, for review.

Run on macOS (arm64), Python 3.12.10: 0.46 s, peak memory 228 MiB (239,271,936 bytes). Exit 0.

**Row → pack map.** `overlap_report.py --results` reads this map from `overlap_docs.parquet`, which TSAI did not put in
the repository. `overlap.py` numbers documents 0 to N−1 in the order it reads the parts, and that order is the part
list in `overlap_summary.json` (`inputs.parts`), so step 2 rebuilds the map from that list. It is accepted only because:
- the 86 parts add up to 1,416,236 documents, equal to `documents_all`;
- the per-pack train and held-out counts from the parts equal the summary's, which `overlap.py` counted from each row's
  `pack_id` (38 packs × 2 splits);
- all 2,436 distinct rows in the 2,711 matches fall in the pack `overlap_matches.csv` names for them (0 mismatches).

Step 5 then compared this rebuilt map with `overlap_docs.parquet` row by row: it is exact.

**3. Run the confirmation with `overlap_docs.parquet`** (after placing it in `out/overlap_tsai/`):

```sh
python3 teams/01-data-a/dedup/confirm_matrix.py --results out/overlap_tsai --docs out/overlap_tsai/overlap_docs.parquet
```

The map is read from the parquet after its SHA-256 is checked against the summary. 22 of 22 checks passed; 3.80 s, peak
memory 634 MiB (665,042,944 bytes). Exit 0.

**4. Run the job request's own command** (`jobs/2026-11-04-overlap.md`) and compare its output with TSAI's files:

```sh
python3 teams/01-data-a/dedup/overlap_report.py --results out/overlap_tsai
cmp out/overlap_returned/overlap_matrix.csv out/overlap_tsai/overlap_matrix.csv
cmp out/overlap_returned/overlap_matrix_counts.csv out/overlap_tsai/overlap_matrix_counts.csv
```

`overlap_report.py` checked the summary's status and the SHA-256 of `overlap_docs.parquet` and `overlap_matches.csv`, and
wrote `out/overlap_returned/`. Exit 0; both `cmp` commands found no difference (SHA-256 `2a049f18…7295bd` and
`cef888f8…60b523`).

**5. Read `overlap_docs.parquet` directly** to list the documents with no shingles and to compare the step-2 map with it
for every row:

```sh
python3 -c "import pyarrow.parquet as pq; [print(d) for d in pq.read_table('out/overlap_tsai/overlap_docs.parquet', columns=['row','pack','split','part','doc_id','words','shingles']).to_pylist() if d['shingles'] == 0]"
python3 -c "import json, pyarrow.parquet as pq; t=pq.read_table('out/overlap_tsai/overlap_docs.parquet', columns=['pack','split']).to_pydict(); s=json.load(open('out/overlap_tsai/overlap_summary.json')); m=[(p['part'].split('/')[1], p['part'].split('/')[0]) for p in s['inputs']['parts'] for _ in range(p['documents'])]; print(len(m), len(t['pack']), sum(a != (b, c) for a, b, c in zip(m, t['pack'], t['split'])))"
```

The second command prints `1416236 1416236 0`: rows in the rebuilt map, rows in the parquet, rows that differ.

Results:
- the parquet has 1,416,236 rows, numbered 0 to N−1 in order;
- **exactly 7 documents have 0 words and 0 shingles**, the same 7 rows as the H1 group of 7 (see "The empty-document
  group");
- the map rebuilt from the part order differs from the parquet on **0 of 1,416,236 rows** for the pack and **0** for
  the split, and every row's part path equals the summary's part.

## Checks

### Map rebuilt from the part order (step 2): 20 of 20 passed

| # | Check | Result | Detail |
|---:|---|---|---|
| 1 | Overlap run status is `complete` | PASS | `complete` |
| 2 | The packs equal the config's `expected_packs` | PASS | 38 packs |
| 3 | `overlap_by_pack.csv` SHA-256 and size equal the summary | PASS | 238,212 bytes |
| 4 | `overlap_histogram.csv` SHA-256 and size equal the summary | PASS | 1,694 bytes |
| 5 | `overlap_matches.csv` SHA-256 and size equal the summary | PASS | 205,749 bytes |
| 6 | `overlap_matrix.csv` SHA-256 and size equal the summary | PASS | 19,866 bytes |
| 7 | `overlap_matrix_counts.csv` SHA-256 and size equal the summary | PASS | 52,511 bytes |
| 8 | The parts add up to `documents_all` | PASS | 86 parts, 1,416,236 documents |
| 9 | Per-pack train / held-out counts from the parts equal the summary | PASS | 38 packs × 2 splits agree |
| 10 | Every matched row is in the pack `overlap_matches.csv` names | PASS | 2,711 matches, 2,436 rows, 0 mismatches |
| 11 | Every `stage` label agrees with its packs | PASS | 0 disagree |
| 12 | No document is matched with itself | PASS | |
| 13 | Rule counts equal `qualifying_pairs_by_rule` | PASS | H1 98, H2 2,613 |
| 14 | Rebuilt `overlap_matrix.csv` is byte-identical to the returned file | PASS | SHA-256 `2a049f18…7295bd` |
| 15 | Rebuilt `overlap_matrix_counts.csv` is byte-identical to the returned file | PASS | SHA-256 `cef888f8…60b523` |
| 16 | `overlap_matrix.csv` is packs × packs, in sorted order | PASS | 38 rows × 38 columns |
| 17 | `overlap_matrix_counts.csv` has one cell per pair of packs | PASS | 1,444 cells (38 × 38) |
| 18 | Every denominator equals its pack's document count | PASS | 0 differ |
| 19 | Every share equals matched ÷ total (10 decimals) | PASS | 0 differ |
| 20 | The empty documents form exactly one H1 group | PASS | 7 empty documents, 1 group of 7 |

### Map read from `overlap_docs.parquet` (step 3): 22 of 22 passed

The same checks, except that checks 8 and 9 (the part list) are replaced by checks on the parquet, and the two large
files are hashed as well:

| Check | Result | Detail |
|---|---|---|
| `overlap_pairs.csv` SHA-256 and size equal the summary | PASS | 6,739,846 bytes |
| `overlap_docs.parquet` SHA-256 and size equal the summary | PASS | 34,454,169 bytes |
| `overlap_docs.parquet` SHA-256 equals the summary (before its map is used) | PASS | `15ed5627…593d67c9c` |
| `overlap_docs.parquet` has one entry per document | PASS | 1,416,236 rows |
| The other 18 checks (1–7, 10–20 above) | PASS | same details as above, including both byte-identical rebuilds |

## What the matrix shows

- **1,444 cells, 60 non-zero:** 20 on the diagonal (within a pack) and 40 off it (across packs).
- **2,436 documents (0.172%)** have at least one qualifying match: 2,363 matched within their own pack (the diagonal
  numerators added up) and 79 (0.0056%) with a copy in another pack. A document can count in both.
- **7 packs have no match at all:** `ind-gu-fw2`, `ind-hi-hplt`, `ind-kn-sangraha-s`, `ind-ml-fw2`, `ind-or-fw2`,
  `ind-te-sangraha-s`, `sci-finepdfs`.
- **The largest cross-pack share is 0.044%** (`ind-mr-fw2` → `ind-mr-sangraha-v`); every off-diagonal cell is below
  0.05%.
- **Directional counts:** every cross-pack pair of packs has the same number of matched documents in both directions,
  except three code pairs (code-cpp ↔ code-java, code-cpp ↔ code-js-ts, code-java ↔ code-js-ts). All three come from
  the empty-document group.
- **Train ↔ held-out pairs among the matches: 63**, as TSAI's README states.

### Per pack (diagonal and cross-pack documents)

"Own pack" is the diagonal cell; "other packs" is the number of distinct documents with a copy in any other pack.

| Pack | Documents | Matched, own pack | Share, own pack | Matched, other packs | Other packs reached |
|---|---:|---:|---:|---:|---:|
| `cadj-commits` | 75,579 | 1,664 | 2.2017% | 9 | 4 |
| `cadj-stackexchange` | 41,805 | 384 | 0.9186% | 0 | 0 |
| `ind-hi-sangraha-s` | 8,368 | 37 | 0.4422% | 0 | 0 |
| `ind-sa-fw2` | 5,721 | 23 | 0.4020% | 0 | 0 |
| `cadj-notebooks` | 15,732 | 27 | 0.1716% | 0 | 0 |
| `ind-hi-sangraha-v` | 14,831 | 18 | 0.1214% | 2 | 2 |
| `math-megamath` | 17,803 | 20 | 0.1123% | 1 | 1 |
| `code-rust` | 58,795 | 66 | 0.1123% | 3 | 1 |
| `ind-ta-sangraha-s` | 4,372 | 2 | 0.0457% | 0 | 0 |
| `en-dclm` | 60,802 | 19 | 0.0312% | 5 | 2 |
| `en-nemotroncc` | 89,183 | 27 | 0.0303% | 6 | 2 |
| `math-finemath` | 28,830 | 6 | 0.0208% | 2 | 2 |
| `en-fineweb-edu` | 72,100 | 14 | 0.0194% | 11 | 4 |
| `code-cpp` | 55,195 | 10 | 0.0181% | 2 | 3 |
| `code-python` | 73,305 | 13 | 0.0177% | 4 | 1 |
| `code-go` | 77,765 | 12 | 0.0154% | 0 | 0 |
| `code-java` | 85,518 | 10 | 0.0117% | 5 | 3 |
| `ind-hi-indiccorp` | 111,851 | 7 | 0.0063% | 1 | 1 |
| `code-js-ts` | 117,208 | 2 | 0.0017% | 2 | 2 |
| `en-nemotroncc-synth` | 198,877 | 2 | 0.0010% | 1 | 1 |
| `ind-bn-fw2` | 10,750 | 0 | 0 | 1 | 1 |
| `ind-bn-sangraha-v` | 10,213 | 0 | 0 | 1 | 1 |
| `ind-hi-fw2` | 14,257 | 0 | 0 | 1 | 1 |
| `ind-kn-fw2` | 7,764 | 0 | 0 | 3 | 1 |
| `ind-kn-sangraha-v` | 8,448 | 0 | 0 | 3 | 1 |
| `ind-mr-fw2` | 11,365 | 0 | 0 | 5 | 1 |
| `ind-mr-sangraha-v` | 12,299 | 0 | 0 | 5 | 1 |
| `ind-ta-fw2` | 6,824 | 0 | 0 | 1 | 1 |
| `ind-ta-sangraha-v` | 6,826 | 0 | 0 | 1 | 1 |
| `ind-te-fw2` | 5,009 | 0 | 0 | 2 | 1 |
| `ind-te-sangraha-v` | 8,174 | 0 | 0 | 2 | 1 |
| `ind-gu-fw2` | 23,011 | 0 | 0 | 0 | 0 |
| `ind-hi-hplt` | 8,719 | 0 | 0 | 0 | 0 |
| `ind-kn-sangraha-s` | 5,222 | 0 | 0 | 0 | 0 |
| `ind-ml-fw2` | 19,161 | 0 | 0 | 0 | 0 |
| `ind-or-fw2` | 34,012 | 0 | 0 | 0 | 0 |
| `ind-te-sangraha-s` | 4,468 | 0 | 0 | 0 | 0 |
| `sci-finepdfs` | 6,074 | 0 | 0 | 0 | 0 |
| **All 38** | **1,416,236** | **2,363** | | **79** | |

### Cross-pack cells (40 cells, 20 pairs of packs)

Matched documents of A with a copy in B, and the share of A; then the same for B → A.

| Pack A | Pack B | A → B | Share of A | B → A | Share of B |
|---|---|---:|---:|---:|---:|
| `en-fineweb-edu` | `en-nemotroncc` | 5 | 0.0069% | 5 | 0.0056% |
| `ind-mr-fw2` | `ind-mr-sangraha-v` | 5 | 0.0440% | 5 | 0.0407% |
| `cadj-commits` | `code-python` | 4 | 0.0053% | 4 | 0.0055% |
| `en-dclm` | `en-fineweb-edu` | 4 | 0.0066% | 4 | 0.0055% |
| `code-java` | `code-cpp` | 4 | 0.0047% | 1 | 0.0018% |
| `code-java` | `code-js-ts` | 4 | 0.0047% | 2 | 0.0017% |
| `cadj-commits` | `code-rust` | 3 | 0.0040% | 3 | 0.0051% |
| `ind-kn-fw2` | `ind-kn-sangraha-v` | 3 | 0.0386% | 3 | 0.0355% |
| `code-js-ts` | `code-cpp` | 2 | 0.0017% | 1 | 0.0018% |
| `ind-te-fw2` | `ind-te-sangraha-v` | 2 | 0.0399% | 2 | 0.0245% |
| `cadj-commits` | `code-cpp` | 1 | 0.0013% | 1 | 0.0018% |
| `cadj-commits` | `code-java` | 1 | 0.0013% | 1 | 0.0012% |
| `en-dclm` | `en-nemotroncc` | 1 | 0.0016% | 1 | 0.0011% |
| `en-fineweb-edu` | `en-nemotroncc-synth` | 1 | 0.0014% | 1 | 0.0005% |
| `en-fineweb-edu` | `math-finemath` | 1 | 0.0014% | 1 | 0.0035% |
| `ind-bn-fw2` | `ind-bn-sangraha-v` | 1 | 0.0093% | 1 | 0.0098% |
| `ind-hi-fw2` | `ind-hi-sangraha-v` | 1 | 0.0070% | 1 | 0.0067% |
| `ind-hi-indiccorp` | `ind-hi-sangraha-v` | 1 | 0.0009% | 1 | 0.0067% |
| `ind-ta-fw2` | `ind-ta-sangraha-v` | 1 | 0.0147% | 1 | 0.0146% |
| `math-finemath` | `math-megamath` | 1 | 0.0035% | 1 | 0.0056% |

## The empty-document group

The summary reports 7 empty documents (no word left after normalisation). Empty documents all have the same H1 key, so
they always form one complete H1 group. Exactly one H1 group has 7 members, and `overlap_docs.parquet` confirms that
these 7 rows, and no others, have 0 words and 0 shingles:

| Row | Pack | Split | Part | Row in part | `doc_id` | Words | Shingles |
|---:|---|---|---|---:|---|---:|---:|
| 173629 | `code-cpp` | train | `code-cpp/part-00001.parquet` | 1,499 | `79fa36f8339f9ebd` | 0 | 0 |
| 305920 | `code-java` | train | `code-java/part-00000.parquet` | 42,665 | `d5d0b4192775579c` | 0 | 0 |
| 309041 | `code-java` | train | `code-java/part-00000.parquet` | 45,786 | `4a67489226159c57` | 0 | 0 |
| 331691 | `code-java` | train | `code-java/part-00001.parquet` | 5,993 | `8a07c8e5f95eee27` | 0 | 0 |
| 347544 | `code-java` | train | `code-java/part-00001.parquet` | 21,846 | `91f4b8de1c11bf4b` | 0 | 0 |
| 360063 | `code-js-ts` | train | `code-js-ts/part-00000.parquet` | 12,129 | `a2ffa5d828d9e9ab` | 0 | 0 |
| 404794 | `code-js-ts` | train | `code-js-ts/part-00000.parquet` | 56,860 | `fff1410ec5527f29` | 0 | 0 |

`doc_id` is set before cleaning and never changed, so these IDs find each document's raw text in sample v0, to see which
cleaning rule emptied it.

They make **21 of the 98 H1 pairs** and **14 of the 50 cross-pack pairs**. These are files that cleaning emptied but did
not drop, not real duplicates. Without the pairs inside the group, 8 cells change:

| From | To | Matched now | Matched without the group | Documents of A |
|---|---|---:|---:|---:|
| `code-cpp` | `code-java` | 1 | 0 | 55,195 |
| `code-cpp` | `code-js-ts` | 1 | 0 | 55,195 |
| `code-java` | `code-cpp` | 4 | 0 | 85,518 |
| `code-java` | `code-java` | 10 | 6 | 85,518 |
| `code-java` | `code-js-ts` | 4 | 0 | 85,518 |
| `code-js-ts` | `code-cpp` | 2 | 0 | 117,208 |
| `code-js-ts` | `code-java` | 2 | 0 | 117,208 |
| `code-js-ts` | `code-js-ts` | 2 | 0 | 117,208 |

Without the group the matrix has 53 non-zero cells (19 diagonal, 34 cross-pack), 72 documents have a cross-pack copy
instead of 79, and every cross-pack pair of packs has equal counts in both directions. The rebuilt files without the
group are in `out/matrix_confirmation/without_empty_documents/`, for review only.

**Recommendation:** commit TSAI's matrix unchanged as the reviewed matrix, since it is exactly what the job measured,
with this note. Fix the cause upstream: cleaning should drop documents it empties, and `dedup.py` should leave
documents with no shingles out of duplicate groups.

## Tests

`tests/test_confirm_matrix.py` runs `confirm_matrix.py` on small made-up overlap runs, with no real data:

```sh
python3 -B -m pytest teams/01-data-a/dedup/tests/test_confirm_matrix.py -q -p no:cacheprovider
```

Result on 10 Nov 2026 (macOS arm64, Python 3.12.10, pytest 9.1.1): **11 passed in 2.27 s.** The confirmation was then rerun
with the final script: 20 of 20 checks passed, and both rebuilt files have the SHA-256 values above.

**The made-up run.** Every test builds it in a temporary folder, so nothing in the real repository is touched:
- **Documents:** 9 in 2 packs. `en-a` has train rows 0–3 and held-out row 7; `en-b` has train rows 4–6 and held-out
  row 8.
- **Matches:** 4 qualifying pairs: one within `en-a`, one exact pair across the two packs, and two train ↔ held-out
  pairs.
- **Matrix files:** written with `overlap_report.write_matrix`, the function `overlap.py` uses.
- **Summary:** records each file's SHA-256 and size, as TSAI's does.

Each test then changes one thing and checks that the script reacts correctly.

| # | Test | What it changes | What it proves |
|---:|---|---|---|
| 1 | `test_matching_run_is_confirmed` | Nothing; the run is consistent | All checks pass, exit 0, and the rebuilt files are identical. The counts come out right: 8 documents with a match, 2 with a cross-pack copy, 2 train ↔ held-out pairs, 2 non-zero cross-pack cells. |
| 2 | `test_changed_matrix_is_not_byte_identical` | One share in the matrix becomes 0.5000000001 instead of 0.5000000000, and the summary's hash is updated to hide it | Exactly two checks fail: "byte-identical" and "share = matched ÷ total". The rebuild catches an error that a hash check alone would miss. |
| 3 | `test_file_that_differs_from_the_summary_fails` | An extra row is added to the matches file | The SHA-256 check fails. A file that is not the run's own is refused. |
| 4 | `test_wrong_part_order_is_caught_by_the_matches` | The summary lists the parts in a different order | The per-pack counts still agree, but rows land in the wrong packs, and the matches check catches it. This is the key safeguard for building the map without `overlap_docs.parquet`. |
| 5 | `test_part_counts_that_disagree_with_the_summary_fail` | The part list says `en-a` has 5 train documents instead of 4 | The per-pack count check fails. |
| 6 | `test_empty_document_group_is_reported_and_removed_for_review` | 3 "empty" documents (rows 0 and 1 in `en-a`, row 4 in `en-b`) form one exact group, plus one real pair | The group is found, with 3 pairs inside it, 2 of them cross-pack. The changed cells are exact: `en-a→en-a` 4→2, `en-a→en-b` 2→0, `en-b→en-a` 1→0. The review copy is written, and the group is reported, not failed. |
| 7 | `test_empty_documents_without_one_group_fail` | The summary says 3 empty documents, but no exact group has 3 members | The check fails, so the script never guesses which documents are empty. |
| 8 | `test_docs_parquet_route` | `--docs` with an `overlap_docs.parquet` | The row → pack map is read from the parquet after its hash is checked, and everything passes. This is the route for when TSAI sends the file. |
| 9 | `test_docs_parquet_with_another_hash_fails` | The summary records a different hash for the parquet | The parquet is refused. |
| 10 | `test_missing_input_returns_2` | The counts file is deleted | The run stops with exit code 2 before any check. |
| 11 | `test_out_must_be_inside_out` | `--out elsewhere` | Writing outside `out/` is refused, as `JOB_REQUEST.md` requires. |

## Limits

- This confirms that the matrix follows exactly from the qualifying matches. It does not check whether each match is a
  true duplicate; that is the hand review (prose, code, `cadj-commits`) and E4.
- `overlap.py` does not record the summary's own SHA-256. The returned summary and `run.log` were edited after the run
  (the `platform` entry is missing from both, and the log's printed JSON has a trailing comma left behind). The output
  hashes inside the summary still match the returned files.

## Next steps

1. **Done:** the reviewed matrix is placed at `teams/01-data-a/dedup/overlap_matrix.csv`, copied from the rebuilt file
   (19,866 bytes, SHA-256 `2a049f187456278d9ebab5839fb351efaecc9c16bdae852bc4048aed9b7295bd`, byte-identical to TSAI's):
   ```sh
   cp out/matrix_confirmation/rebuilt/overlap_matrix.csv teams/01-data-a/dedup/overlap_matrix.csv
   ```
2. **Done:** the confirmation was rerun with `overlap_docs.parquet` (22 of 22) and with `overlap_report.py --results`
   (byte-identical), and the 7 empty documents were identified by `doc_id`.
3. **Done:** the decision log in `dedup_design_v1.md` records the matrix confirmation and the empty-document decision
   (both 10 Nov 2026).
4. **Done:** `dedup.py` sets aside the matches between documents with no shingles, removes none of them and lists them in
   `empty_documents.csv` (`README_dedup.md`, "Empty documents"). **Open:** which cleaning rule emptied the 7 documents
   is not yet recorded. They pass `clean.py`'s empty-output check (`out.strip()`) but have no words after
   normalisation, probably only invisible characters (`results_v1.md`, observation 6); their raw text can be found by
   `doc_id`. Dropping them is a cleaning change for spec v1.1.

## Files

| File | What it is | In git |
|---|---|---|
| `teams/01-data-a/dedup/confirm_matrix.py` | The confirmation script | yes (new) |
| `teams/01-data-a/dedup/tests/test_confirm_matrix.py` | Its tests: 11 cases on made-up runs (see "Tests") | yes (new) |
| `teams/01-data-a/dedup/matrix_confirmation.md` | This report | yes (new) |
| `teams/01-data-a/dedup/overlap_matrix.csv` | The reviewed matrix, byte-identical to TSAI's | yes (new) |
| `out/overlap_tsai/` | TSAI's returned files, plus `overlap_docs.parquet` and `overlap_pairs.csv` | no (`out/` is ignored) |
| `out/overlap_returned/` | The matrix written by `overlap_report.py --results` | no |
| `out/matrix_confirmation/confirmation.json` | Every check and number above | no |
| `out/matrix_confirmation/rebuilt/` | The rebuilt matrix files | no |
| `out/matrix_confirmation/without_empty_documents/` | The matrix without the empty-document group | no |
