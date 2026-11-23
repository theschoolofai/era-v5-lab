# MinHash + LSH overlap stage (`minhash_overlap.py`)

TSAI ruled on 23 Nov 2026 that the exact all-pairs overlap (`overlap.py`) is not to be run at corpus-v1 scale and set a
minimum bar for its replacement. This stage is that replacement. It is a drop-in for `overlap.py`: it writes the three
files `dedup.py` and `run_pipeline.py` read (`overlap_summary.json`, `overlap_matches.csv` with the same columns,
`overlap_docs.parquet` with the same rows in the same order), so dedup, apply, F2, the ledger and the reconciliation do
not change.

## How it works

1. **Per part, in parallel, resumable.** `workers` processes each read one cleaned part and compute, per document, the
   H1 key and its sha256 (`h1_sha256.py`), the word 5-gram shingles (`jaccard_matrix.shingles`, exactly `overlap.py`'s)
   and a 128-value MinHash signature; for code packs also the code-token shingles (`overlap_rules.code_shingles`) and
   their signature. Each part's result goes to `work/` with the part's input sha256 and the settings; a rerun reuses
   every unchanged part, so a stopped job continues where it stopped.
2. **H1 first.** Documents with the same H1 sha256 are exact copies (rule H1), written as star edges to the group's first
   row. `dedup.py` forms groups by connected components, so the groups are the same as with all pairs.
3. **LSH across all packs and both splits.** 32 bands of 4 values. Two documents agreeing in any band are a candidate.
   Bands are processed one at a time from memory-mapped signature files, so memory is about the band table, not the
   signatures. A bucket larger than `max_bucket` (2,000) gives star edges to its first member and is counted in the
   summary. Code documents with at least 20 nonblank lines are banded on their code signatures the same way.
4. **Exact decision.** Every candidate is scored with the exact Jaccard of its shingle sets (only candidate documents
   are re-read), and `overlap.py`'s rules decide: prose >= 0.80 and both >= 50 words; math >= 0.90 and identical
   numbers; code >= 0.85 token Jaccard and both >= 20 lines; mixed domains pass both. MinHash only picks candidates.

## Against TSAI's bar (23 Nov)

| Bar | How it is met |
|---|---|
| 1. MinHash + LSH, parameters justified by agreement with the exact method; exact-hash first; per shard, parallel | 128 hashes, 32 × 4 bands; H1 by sha256 first; step 1 per part in `workers` processes. Agreement: below |
| 2. No N × N matrix, no all-pairs histogram; outputs candidate pairs or cluster IDs; fix the 50 MB cap at 1.15× | Neither is written. `overlap_pairs.csv` holds verified candidates only. `max_output_mb` counts only the files returned to the repository (CSVs + summary); `overlap_docs.parquet`, `overlap_pairs.csv` and `work/` stay in job storage |
| 3. Cross-pack dedup on signatures or cluster IDs, resumable per stage | LSH runs over all packs and both splits together; step 1 resumes per part; the runner's `"from": "overlap"` resumes at the stage |
| 4. Measured time and RAM at 1×, 2×, 4× on the staged data, inside 64 GiB / 720 min | 1× measured on the sample (below). `minhash_sizing.py` runs 1×, 2× and 4× on the staged data and writes `sizing.csv` |
| 5. A partial-scope config for the 33 staged packs | `minhash_overlap_partial.json`: `expected_packs` empty, so it reads the packs present |

## Agreement with the exact method

On slices of five packs (prose, Indic, math, code, held-out), `overlap.py` and this stage give the same document table,
the same duplicate groups and a byte-identical `dedup.py` `remove_list.csv`. `tests/test_minhash_overlap.py` checks the
same on made-up data with planted H1, prose, math and code copies.

The earlier agreement test (dedup v2 item 11, 11 packs, ground truth TSAI's 5 Nov exact run): 32 × 4 found every one of
the 1,974 word and 560 code qualifying pairs. The chance a pair at Jaccard s is not a candidate is (1 − s⁴)³²:
4.6 × 10⁻⁸ at 0.80, 6 × 10⁻¹¹ at 0.85.

**Full sample, 23 Nov 2026** (`jobs/logs/2026-11-23-minhash-overlap-sample/`): all 47 train parts of the cleaned sample
(1,395,320 documents, 37 packs; the local copy has no `ind-ta-sangraha-v` train part), against TSAI's 5 Nov exact run
on the same files (every document's shingle count identical):

| | Exact (5 Nov) | MinHash + LSH |
|---|---:|---:|
| H2 qualifying pairs | 2,550 | **2,550 found, 0 missed, 0 added** |
| Duplicate groups (dedup.py's connected components) | 1,060 | **1,060, identical** |
| `dedup.py` `remove_list.csv` | 1,317 rows | **1,317 rows, byte-identical** (sha256 `8461bf1b…`) |
| H1 rows in `overlap_matches.csv` | 97 (all pairs) | 78 (star edges; same groups) |

Measured on a 2-core, 7 GB cloud workspace, `workers` 2:

| Stage | Seconds |
|---|---:|
| Per-part signatures (read, H1 key, shingles, MinHash; Pygments for 463k code documents) | 2,324 |
| H1 | 0.9 |
| LSH, 32 bands (646,651 word and 27,352 code candidates; largest bucket 509; no star buckets) | 15.5 |
| Exact Jaccard of the word candidates | 23.1 |
| Rules | 4.9 |
| Outputs | 2.1 |
| **Wall** | **2,375 (39.6 min)** |

Peak RSS 4.2 GB in the main process and 3.2 GB in the largest worker (exact overlap on the 38-pack rehearsal: 14.0 GB,
84 min). Returned files 0.49 MB (exact: 43.6 MB). The signature step is per part and CPU-bound (about 16 ms per code
document, mostly Pygments), so it divides by the workers: at 30 workers it is about 2 minutes for the sample.

## Running it

    python teams/01-data-a/dedup/minhash_overlap.py --config teams/01-data-a/dedup/minhash_overlap.json

In the pipeline, the overlap stage takes a `script` key, so no runner change is needed:

    "overlap": {"mode": "run", "script": "teams/01-data-a/dedup/minhash_overlap.py",
                "settings": "teams/01-data-a/dedup/minhash_overlap_partial.json"}

Sizing on the staged data (bar 4):

    python teams/01-data-a/dedup/minhash_sizing.py --inputs <staged cleaned folder under the repo> --factors 1 2 4 --workers 0

Needs the same packages as `overlap.py` (`requirements_overlap.txt`). Runs on Linux, macOS and Windows (on Windows the
peak RSS of the workers is not recorded).

## Limits

- LSH is tuned for the removal thresholds (>= 0.80). `overlap_pairs.csv` and `pairs_at_or_above` below 0.70 are a sample
  of the pairs, not all of them.
- A bucket above `max_bucket` gives star edges: a document in it that is a duplicate of another member but not of the
  first is not found through that bucket (other bands usually still find it). The summary counts such buckets.
- Pygments lexing of code (about 16 ms a document here) is the slowest part; it runs in parallel per part, so the
  largest code part sets the floor for the signature step.
- Peak RSS was measured at 1× only; 2× and 4× are for `minhash_sizing.py` on the staged data.
