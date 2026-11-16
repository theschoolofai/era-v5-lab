# Tokenizer CPU speed benchmark v1 — p1536

Encode throughput for **p1536** on English, Code and Indic text. Median of three measured runs per domain.

## Tokenizer verification (p1536)

| Field | Value |
|---|---|
| Artifact | `$WEEK3DATA/archive/tokenizer.json` |
| Expected sha256 | `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b` |
| Observed sha256 | `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b` |
| Matches | `archive/SHA256SUMS`, `train/p1536_s0_manifest.json` |
| Checks | structure (BPE, vocab 131072, 130460 merges, 356 specials), roles, round trip, AutoTokenizer |
| EOS | `<\|endoftext\|>` **130822** |
| Result | **PASS** |

## Upstream sync

| Item | Value |
|---|---|
| Upstream `main` SHA | `ae4c03dbe69b9a46bfdd8a0922cf5d48118ab51f` |

## Machine and configuration

| Field | Value |
|---|---|
| Machine | Apple MacBook Pro, **Apple M2**, 8 logical CPUs |
| OS | macOS 15.1.1 (Darwin 24.1.0, arm64) |
| Python | 3.11.8 |
| `tokenizers` | 0.21.1 |
| Runs / domain | 3 measured + 1 warm-up |
| Encode API | `Tokenizer.encode(text, add_special_tokens=False)` |
| Parallelism | `TOKENIZERS_PARALLELISM=false`; BLAS/OpenMP threads = 1 |

### One-core affinity

**Not verified** on Darwin (no `os.sched_setaffinity`). Thread pools limited to 1; hard CPU pin not claimed.

## Dataset sizes

| Domain | Selected records | Input UTF-8 bytes | vs 1 GB target |
|---|---:|---:|---|
| English | 354 320 | 1 000 002 183 | reached target |
| Code | 233 254 | 1 000 000 966 | reached target |
| Indic | 42 260 | 309 018 421 | all available (0.309 GB) |

Selection: sorted parquet paths under `$WEEK3DATA/{english,code,indic}`, row order, stop at 1 000 000 000 UTF-8 bytes (or all available). Text column: `text`.

## Methodology

Load/decode Parquet before timing. Warm-up excluded. Timed window = encode loop only. Report **median** of three runs.  
`MB/s = (input_bytes / 1e6) / elapsed_s`, `tokens/s = total_tokens / elapsed_s`.

## p1536 results — three runs and medians

### English (~1.000 GB)

| Run | MB/s | tokens/s | elapsed_s | tokens |
|---:|---:|---:|---:|---:|
| 1 | 1.594 | 329 511 | 627.2 | 206 673 500 |
| 2 | 1.638 | 338 621 | 610.3 | 206 673 500 |
| 3 | 1.659 | 342 961 | 602.6 | 206 673 500 |
| **Median** | **1.638** | **338 621** | | tokens/byte **0.2067** |

### Code (~1.000 GB)

| Run | MB/s | tokens/s | elapsed_s | tokens |
|---:|---:|---:|---:|---:|
| 1 | 2.580 | 667 893 | 387.7 | 258 914 207 |
| 2 | 2.575 | 666 634 | 388.4 | 258 914 207 |
| 3 | 2.507 | 649 055 | 398.9 | 258 914 207 |
| **Median** | **2.575** | **666 634** | | tokens/byte **0.2589** |

### Indic (0.309 GB, all available)

| Run | MB/s | tokens/s | elapsed_s | tokens |
|---:|---:|---:|---:|---:|
| 1 | 3.178 | 376 891 | 97.2 | 36 646 601 |
| 2 | 3.245 | 384 880 | 95.2 | 36 646 601 |
| 3 | 3.213 | 381 047 | 96.2 | 36 646 601 |
| **Median** | **3.213** | **381 047** | | tokens/byte **0.1186** |

## Median summary (p1536)

| Domain | Median MB/s | Median tokens/s | tokens/byte |
|---|---:|---:|---:|
| English | **1.638** | **338 621** | 0.2067 |
| Code | **2.575** | **666 634** | 0.2589 |
| Indic | **3.213** | **381 047** | 0.1186 |

## Cross-check

Pending — no second machine available.

## Contributors

- [@nitinranjansharma](https://github.com/nitinranjansharma)
