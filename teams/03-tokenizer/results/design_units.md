# Design tasks 1-4: our own unit lists vs p1536, o200k and released SuperBPE

Made by `harness/design_units.py` (`prep`, `train`, `eval`). Numbers in `design_units.json`.

- **Training text:** sample v0 `train/` (6.0 GB, 38 packs at the Stage 1 group shares), exact duplicates removed, fixed random order (seed 20261128), nested sets: 10MB = 2,438 docs, 100MB = 23,843 docs, 1GB = 239,774 docs.
- **Evaluation text:** the `heldout/` parts of the same packs (never trained on), up to 1 MB per domain:

| Domain | Packs | Docs | Bytes |
|---|---|---:|---:|
| en-web | en-dclm, en-fineweb-edu, en-nemotroncc | 220 | 1,000,413 |
| en-synthetic | en-nemotroncc-synth | 620 | 1,000,402 |
| code-python | code-python | 228 | 1,030,829 |
| code-other | code-cpp, code-go, code-java, code-js-ts, code-rust | 191 | 1,002,549 |
| code-adjacent | cadj-commits, cadj-notebooks, cadj-stackexchange | 230 | 1,002,890 |
| math | math-finemath, math-megamath | 177 | 1,008,185 |
| science-pdf | sci-finepdfs | 63 | 851,970 |
| hi-mr (Devanagari) | ind-hi-fw2, ind-hi-hplt, ind-hi-indiccorp, ind-hi-sangraha-s, ind-hi-sangraha-v, ind-mr-fw2, ind-mr-sangraha-v | 193 | 1,008,495 |
| bn-or-gu | ind-bn-fw2, ind-bn-sangraha-v, ind-or-fw2, ind-gu-fw2 | 162 | 1,003,228 |
| ta-ml | ind-ta-fw2, ind-ta-sangraha-s, ind-ta-sangraha-v, ind-ml-fw2 | 119 | 1,022,545 |
| te-kn | ind-te-fw2, ind-te-sangraha-s, ind-te-sangraha-v, ind-kn-fw2, ind-kn-sangraha-s, ind-kn-sangraha-v | 146 | 1,002,690 |
| sanskrit | ind-sa-fw2 | 55 | 766,547 |

- **Word rule:** maximal non-whitespace runs (`str.split()`), the same for every domain. For code, tokens per word is only a relative measure; bytes per token is the comparable one.
- **Mean:** the plain average over the 12 domains, so each domain counts the same.

## Task 1: tokens per word by domain (lower is better)

| Tokenizer | Ids | en-web | en-synthetic | code-python | code-other | code-adjacent | math | science-pdf | hi-mr | bn-or-gu | ta-ml | te-kn | sanskrit | **Mean** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| p1536 (frozen) | 131,072 | 1.285 | 1.319 | 2.938 | 2.733 | 2.241 | 1.526 | 1.468 | 1.622 | 1.951 | 2.418 | 2.401 | 3.454 | **2.113** |
| o200k_base | 200,019 | 1.273 | 1.305 | 2.861 | 2.627 | 2.196 | 1.503 | 1.448 | 1.802 | 2.900 | 3.197 | 3.134 | 3.727 | **2.331** |
| o200k first 100k | 100,256 | 1.319 | 1.365 | 2.973 | 2.721 | 2.280 | 1.555 | 1.503 | 2.070 | 3.467 | 3.805 | 3.745 | 4.028 | **2.569** |
| plain 10MB 100k | 100,256 | 1.341 | 1.374 | 3.024 | 2.741 | 2.253 | 1.544 | 1.540 | 1.593 | 2.109 | 2.689 | 2.816 | 3.200 | **2.185** |
| plain 100MB 100k | 100,256 | 1.317 | 1.347 | 2.931 | 2.671 | 2.202 | 1.509 | 1.504 | 1.536 | 1.926 | 2.573 | 2.489 | 2.920 | **2.077** |
| plain 1GB 100k | 100,256 | 1.310 | 1.338 | 2.895 | 2.650 | 2.189 | 1.498 | 1.492 | 1.510 | 1.930 | 2.477 | 2.434 | 2.766 | **2.041** |
| SuperBPE 100MB t180k→200k | 200,256 | 1.018 | 1.058 | 2.548 | 2.208 | 1.774 | 1.208 | 1.208 | 1.271 | 1.657 | 2.205 | 2.140 | 2.607 | **1.742** |
| SuperBPE 100MB t80k→100k | 100,256 | 1.073 | 1.121 | 2.654 | 2.288 | 1.849 | 1.253 | 1.270 | 1.421 | 1.964 | 2.637 | 2.563 | 2.940 | **1.919** |
| SuperBPE 100MB t80k→100k upstream rule | 100,256 | 1.074 | 1.121 | 2.655 | 2.290 | 1.851 | 1.254 | 1.270 | 1.573 | 2.034 | 2.740 | 2.754 | 2.992 | **1.967** |
| SuperBPE 1GB t80k→100k | 100,256 | 1.062 | 1.104 | 2.612 | 2.259 | 1.822 | 1.234 | 1.249 | 1.386 | 1.970 | 2.541 | 2.495 | 2.792 | **1.877** |
| UW/OLMo2-8B-SuperBPE-t180k | 200,005 | 0.941 | 1.015 | 2.964 | 2.639 | 2.131 | 1.208 | 1.152 | 4.164 | 7.527 | 9.087 | 9.701 | 6.608 | **4.095** |
| UW/OLMo2-8B-SuperBPE-t80k | 200,005 | 0.865 | 0.932 | 2.717 | 2.462 | 1.958 | 1.132 | 1.086 | 4.101 | 9.286 | 10.230 | 13.779 | 6.131 | **4.557** |
| alisawuffles/superbpe-tokenizer-128k | 128,001 | 0.942 | 1.014 | 2.993 | 2.679 | 2.130 | 1.223 | 1.182 | 4.157 | 9.309 | 10.810 | 12.542 | 6.154 | **4.595** |
| SuperBPE 100MB t180k→200k (one file) | 200,229 | 1.018 | 1.058 | 2.548 | 2.210 | 1.774 | 1.208 | 1.208 | 1.271 | 1.657 | 2.205 | 2.140 | 2.607 | **1.742** |
| SuperBPE 100MB t80k→100k (one file) | 100,221 | 1.073 | 1.121 | 2.654 | 2.290 | 1.849 | 1.253 | 1.270 | 1.421 | 1.964 | 2.637 | 2.563 | 2.940 | **1.920** |
| SuperBPE 100MB t80k→100k upstream rule (one file) | 100,222 | 1.074 | 1.121 | 2.655 | 2.292 | 1.851 | 1.254 | 1.270 | 1.573 | 2.034 | 2.740 | 2.754 | 2.992 | **1.967** |
| SuperBPE 1GB t80k→100k (one file) | 100,211 | 1.062 | 1.104 | 2.612 | 2.261 | 1.821 | 1.234 | 1.249 | 1.386 | 1.970 | 2.541 | 2.495 | 2.792 | **1.877** |

## Task 1: bytes per token by domain (higher is better)

| Tokenizer | Ids | en-web | en-synthetic | code-python | code-other | code-adjacent | math | science-pdf | hi-mr | bn-or-gu | ta-ml | te-kn | sanskrit | **Mean** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| p1536 (frozen) | 131,072 | 4.65 | 4.97 | 3.94 | 3.77 | 3.81 | 3.88 | 4.23 | 8.52 | 8.55 | 10.15 | 8.91 | 6.04 | **5.95** |
| o200k_base | 200,019 | 4.70 | 5.03 | 4.05 | 3.92 | 3.89 | 3.94 | 4.29 | 7.67 | 5.75 | 7.67 | 6.83 | 5.60 | **5.28** |
| o200k first 100k | 100,256 | 4.53 | 4.81 | 3.90 | 3.79 | 3.74 | 3.81 | 4.13 | 6.68 | 4.81 | 6.45 | 5.71 | 5.18 | **4.79** |
| plain 10MB 100k | 100,256 | 4.46 | 4.77 | 3.83 | 3.76 | 3.79 | 3.83 | 4.03 | 8.68 | 7.91 | 9.12 | 7.60 | 6.52 | **5.69** |
| plain 100MB 100k | 100,256 | 4.54 | 4.87 | 3.95 | 3.86 | 3.88 | 3.92 | 4.13 | 9.00 | 8.67 | 9.54 | 8.60 | 7.14 | **6.01** |
| plain 1GB 100k | 100,256 | 4.56 | 4.90 | 4.00 | 3.89 | 3.90 | 3.95 | 4.16 | 9.15 | 8.65 | 9.90 | 8.79 | 7.54 | **6.12** |
| SuperBPE 100MB t180k→200k | 200,256 | 5.87 | 6.20 | 4.54 | 4.67 | 4.81 | 4.90 | 5.14 | 10.88 | 10.07 | 11.12 | 10.00 | 8.00 | **7.19** |
| SuperBPE 100MB t80k→100k | 100,256 | 5.57 | 5.86 | 4.36 | 4.50 | 4.61 | 4.72 | 4.89 | 9.73 | 8.50 | 9.30 | 8.35 | 7.09 | **6.46** |
| SuperBPE 100MB t80k→100k upstream rule | 100,256 | 5.57 | 5.85 | 4.36 | 4.50 | 4.61 | 4.72 | 4.89 | 8.79 | 8.21 | 8.95 | 7.77 | 6.97 | **6.27** |
| SuperBPE 1GB t80k→100k | 100,256 | 5.63 | 5.94 | 4.43 | 4.56 | 4.68 | 4.80 | 4.97 | 9.97 | 8.47 | 9.65 | 8.58 | 7.47 | **6.60** |
| UW/OLMo2-8B-SuperBPE-t180k | 200,005 | 6.35 | 6.47 | 3.91 | 3.90 | 4.00 | 4.90 | 5.39 | 3.32 | 2.22 | 2.70 | 2.21 | 3.16 | **4.04** |
| UW/OLMo2-8B-SuperBPE-t80k | 200,005 | 6.92 | 7.04 | 4.26 | 4.19 | 4.36 | 5.23 | 5.71 | 3.37 | 1.80 | 2.40 | 1.55 | 3.40 | **4.18** |
| alisawuffles/superbpe-tokenizer-128k | 128,001 | 6.35 | 6.47 | 3.87 | 3.85 | 4.01 | 4.84 | 5.25 | 3.33 | 1.79 | 2.27 | 1.71 | 3.39 | **3.93** |
| SuperBPE 100MB t180k→200k (one file) | 200,229 | 5.87 | 6.20 | 4.54 | 4.66 | 4.81 | 4.90 | 5.14 | 10.88 | 10.07 | 11.12 | 10.00 | 8.00 | **7.18** |
| SuperBPE 100MB t80k→100k (one file) | 100,221 | 5.57 | 5.86 | 4.36 | 4.50 | 4.61 | 4.72 | 4.89 | 9.73 | 8.50 | 9.30 | 8.35 | 7.09 | **6.46** |
| SuperBPE 100MB t80k→100k upstream rule (one file) | 100,222 | 5.57 | 5.85 | 4.36 | 4.50 | 4.61 | 4.72 | 4.89 | 8.79 | 8.21 | 8.95 | 7.77 | 6.97 | **6.27** |
| SuperBPE 1GB t80k→100k (one file) | 100,211 | 5.63 | 5.94 | 4.43 | 4.56 | 4.68 | 4.80 | 4.97 | 9.97 | 8.47 | 9.65 | 8.58 | 7.47 | **6.60** |

## Task 1: merge curves (mean bytes per token over the 12 domains)

Each column is one unit list cut to its first k merges. A dash: training stopped before k merges (no pair seen twice).

| Merges | plain 10MB | plain 100MB | plain 1GB | o200k cut |
|---:|---:|---:|---:|---:|
| 1,000 | 2.491 | 2.484 | 2.489 | 2.059 |
| 10,000 | 3.955 | 4.009 | 4.047 | 3.260 |
| 100,000 | 5.693 | 6.008 | 6.117 | 4.794 |
| 1,000,000 | – | – | 7.854 | – |

Mean bytes per token at each size, by domain, plain BPE on 1 GB:

| Merges | en-web | en-synthetic | code-python | code-other | code-adjacent | math | science-pdf | hi-mr | bn-or-gu | ta-ml | te-kn | sanskrit |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1,000 | 2.29 | 2.28 | 2.15 | 2.14 | 2.04 | 2.15 | 2.16 | 3.51 | 2.62 | 2.74 | 2.56 | 3.25 |
| 10,000 | 3.50 | 3.58 | 3.17 | 3.19 | 3.10 | 3.17 | 3.19 | 5.74 | 4.69 | 5.38 | 4.79 | 5.07 |
| 100,000 | 4.56 | 4.90 | 4.00 | 3.89 | 3.90 | 3.95 | 4.16 | 9.15 | 8.65 | 9.90 | 8.79 | 7.54 |
| 1,000,000 | 4.92 | 5.30 | 4.29 | 4.12 | 4.14 | 4.16 | 4.51 | 11.02 | 12.48 | 15.18 | 13.48 | 10.64 |

## Task 1: unit caps of 32 and 64 bytes

Merges whose unit is longer than the cap are removed. Plain BPE on 100 MB at every size, and the SuperBPE lists. `Longest` is the longest unit kept.

| Unit list | Cap | Longest | Mean bytes/token | en-web | en-synthetic | code-python | code-other | code-adjacent | math | science-pdf | hi-mr | bn-or-gu | ta-ml | te-kn | sanskrit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| plain 100MB 1k | none | 19 | 2.484 | 2.31 | 2.29 | 2.15 | 2.14 | 2.04 | 2.15 | 2.16 | 3.49 | 2.67 | 2.62 | 2.51 | 3.28 |
| plain 100MB 1k | 32 | 19 | 2.484 | 2.31 | 2.29 | 2.15 | 2.14 | 2.04 | 2.15 | 2.16 | 3.49 | 2.67 | 2.62 | 2.51 | 3.28 |
| plain 100MB 1k | 64 | 19 | 2.484 | 2.31 | 2.29 | 2.15 | 2.14 | 2.04 | 2.15 | 2.16 | 3.49 | 2.67 | 2.62 | 2.51 | 3.28 |
| plain 100MB 10k | none | 64 | 4.009 | 3.50 | 3.58 | 3.16 | 3.18 | 3.10 | 3.17 | 3.19 | 5.66 | 4.79 | 5.23 | 4.75 | 4.80 |
| plain 100MB 10k | 32 | 32 | 4.009 | 3.50 | 3.58 | 3.16 | 3.18 | 3.10 | 3.17 | 3.19 | 5.66 | 4.79 | 5.23 | 4.75 | 4.80 |
| plain 100MB 10k | 64 | 64 | 4.009 | 3.50 | 3.58 | 3.16 | 3.18 | 3.10 | 3.17 | 3.19 | 5.66 | 4.79 | 5.23 | 4.75 | 4.80 |
| plain 100MB 100k | none | 232 | 6.008 | 4.54 | 4.87 | 3.95 | 3.86 | 3.88 | 3.92 | 4.13 | 9.00 | 8.67 | 9.54 | 8.60 | 7.14 |
| plain 100MB 100k | 32 | 32 | 6.000 | 4.54 | 4.87 | 3.95 | 3.86 | 3.88 | 3.92 | 4.13 | 8.99 | 8.65 | 9.49 | 8.58 | 7.14 |
| plain 100MB 100k | 64 | 64 | 6.008 | 4.54 | 4.87 | 3.95 | 3.86 | 3.88 | 3.92 | 4.13 | 9.00 | 8.67 | 9.54 | 8.60 | 7.14 |
| SuperBPE 100MB t180k→200k | none | 325 | 7.185 | 5.87 | 6.20 | 4.54 | 4.67 | 4.81 | 4.90 | 5.14 | 10.88 | 10.07 | 11.12 | 10.00 | 8.00 |
| SuperBPE 100MB t180k→200k | 32 | 32 | 7.180 | 5.87 | 6.20 | 4.54 | 4.66 | 4.79 | 4.90 | 5.14 | 10.86 | 10.07 | 11.12 | 10.00 | 8.00 |
| SuperBPE 100MB t180k→200k | 64 | 64 | 7.184 | 5.87 | 6.20 | 4.54 | 4.67 | 4.80 | 4.90 | 5.14 | 10.88 | 10.07 | 11.12 | 10.00 | 8.00 |
| SuperBPE 100MB t80k→100k | none | 325 | 6.458 | 5.57 | 5.86 | 4.36 | 4.50 | 4.61 | 4.72 | 4.89 | 9.73 | 8.50 | 9.30 | 8.35 | 7.09 |
| SuperBPE 100MB t80k→100k | 32 | 32 | 6.454 | 5.57 | 5.86 | 4.36 | 4.49 | 4.60 | 4.72 | 4.89 | 9.71 | 8.50 | 9.30 | 8.35 | 7.09 |
| SuperBPE 100MB t80k→100k | 64 | 64 | 6.458 | 5.57 | 5.86 | 4.36 | 4.50 | 4.61 | 4.72 | 4.89 | 9.73 | 8.50 | 9.30 | 8.35 | 7.09 |
| SuperBPE 1GB t80k→100k | none | 325 | 6.597 | 5.63 | 5.94 | 4.43 | 4.56 | 4.68 | 4.80 | 4.97 | 9.97 | 8.47 | 9.65 | 8.58 | 7.47 |
| SuperBPE 1GB t80k→100k | 32 | 32 | 6.592 | 5.63 | 5.94 | 4.43 | 4.55 | 4.67 | 4.80 | 4.97 | 9.95 | 8.47 | 9.65 | 8.58 | 7.47 |
| SuperBPE 1GB t80k→100k | 64 | 64 | 6.596 | 5.63 | 5.94 | 4.43 | 4.56 | 4.68 | 4.80 | 4.97 | 9.97 | 8.47 | 9.65 | 8.58 | 7.47 |

## Task 2: lossless, unused units, encoder rate

Lossless: share of eval docs where decode(encode(x)) equals the normalizer's output. Unused units: ids never produced on all 12 MB of eval text. Rate: tokens per second on one core over all eval text (Apple arm64, RAYON_NUM_THREADS=1).

| Tokenizer | Ids | Lossless (min over domains) | Unused units | Unused share | Tokens/s/core |
|---|---:|---:|---:|---:|---:|
| p1536 (frozen) | 131,072 | 1.0000 | 48,526 | 37.0% | 664,942 |
| o200k_base | 200,019 | 1.0000 | 127,374 | 63.7% | 3,024,099 |
| o200k first 1k | 1,256 | 1.0000 | 114 | 9.1% | 6,752,886 |
| o200k first 10k | 10,256 | 1.0000 | 1,497 | 14.6% | 4,545,636 |
| o200k first 100k | 100,256 | 1.0000 | 48,976 | 48.9% | 3,254,578 |
| plain 10MB 1k | 1,256 | 1.0000 | 62 | 4.9% | 1,366,318 |
| plain 10MB 10k | 10,256 | 1.0000 | 202 | 2.0% | 940,297 |
| plain 10MB 100k | 100,256 | 1.0000 | 32,776 | 32.7% | 645,945 |
| plain 10MB 100k ≤32B | 100,256 | 1.0000 | 32,748 | 32.7% | 716,868 |
| plain 10MB 100k ≤64B | 100,256 | 1.0000 | 32,758 | 32.7% | 733,054 |
| plain 100MB 1k | 1,256 | 1.0000 | 61 | 4.9% | 1,415,897 |
| plain 100MB 1k ≤32B | 1,256 | 1.0000 | 61 | 4.9% | 1,398,724 |
| plain 100MB 1k ≤64B | 1,256 | 1.0000 | 61 | 4.9% | 1,386,963 |
| plain 100MB 10k | 10,256 | 1.0000 | 117 | 1.1% | 909,731 |
| plain 100MB 10k ≤32B | 10,256 | 1.0000 | 117 | 1.1% | 906,833 |
| plain 100MB 10k ≤64B | 10,256 | 1.0000 | 117 | 1.1% | 932,861 |
| plain 100MB 100k | 100,256 | 1.0000 | 23,907 | 23.8% | 530,253 |
| plain 100MB 100k ≤32B | 100,256 | 1.0000 | 23,989 | 23.9% | 675,059 |
| plain 100MB 100k ≤64B | 100,256 | 1.0000 | 23,919 | 23.9% | 707,836 |
| plain 1GB 1k | 1,256 | 1.0000 | 61 | 4.9% | 1,393,432 |
| plain 1GB 10k | 10,256 | 1.0000 | 104 | 1.0% | 928,917 |
| plain 1GB 100k | 100,256 | 1.0000 | 20,234 | 20.2% | 702,517 |
| plain 1GB 100k ≤32B | 100,256 | 1.0000 | 20,288 | 20.2% | 707,613 |
| plain 1GB 100k ≤64B | 100,256 | 1.0000 | 20,224 | 20.2% | 693,457 |
| plain 1GB 1000k | 1,000,256 | 1.0000 | 829,275 | 82.9% | 612,035 |
| SuperBPE 100MB t180k→200k | 200,256 | 1.0000 | 81,597 | 40.8% | 194,627 |
| SuperBPE 100MB t180k→200k ≤32B | 199,818 | 1.0000 | 81,222 | 40.6% | 194,673 |
| SuperBPE 100MB t180k→200k ≤64B | 200,163 | 1.0000 | 81,517 | 40.7% | 196,099 |
| SuperBPE 100MB t180k→200k (one file) | 200,229 | 1.0000 | 81,629 | 40.8% | 533,823 |
| SuperBPE 100MB t80k→100k | 100,256 | 1.0000 | 20,121 | 20.1% | 210,168 |
| SuperBPE 100MB t80k→100k ≤32B | 99,850 | 1.0000 | 19,775 | 19.8% | 209,222 |
| SuperBPE 100MB t80k→100k ≤64B | 100,170 | 1.0000 | 20,047 | 20.0% | 209,234 |
| SuperBPE 100MB t80k→100k (one file) | 100,221 | 1.0000 | 20,145 | 20.1% | 580,515 |
| SuperBPE 100MB t80k→100k upstream rule | 100,256 | 1.0000 | 21,142 | 21.1% | 193,243 |
| SuperBPE 100MB t80k→100k upstream rule (one file) | 100,222 | 1.0000 | 21,167 | 21.1% | 584,741 |
| SuperBPE 1GB t80k→100k | 100,256 | 1.0000 | 15,611 | 15.6% | 199,382 |
| SuperBPE 1GB t80k→100k ≤32B | 99,914 | 1.0000 | 15,357 | 15.4% | 199,278 |
| SuperBPE 1GB t80k→100k ≤64B | 100,166 | 1.0000 | 15,532 | 15.5% | 201,294 |
| SuperBPE 1GB t80k→100k (one file) | 100,211 | 1.0000 | 15,629 | 15.6% | 576,053 |
| UW/OLMo2-8B-SuperBPE-t180k | 200,005 | 1.0000 | 119,014 | 59.5% | 1,124,332 |
| UW/OLMo2-8B-SuperBPE-t80k | 200,005 | 1.0000 | 91,536 | 45.8% | 1,187,673 |
| alisawuffles/superbpe-tokenizer-128k | 128,001 | 1.0000 | 49,175 | 38.4% | 1,269,912 |

## Task 2: numbers

Each string encoded alone; pieces joined with `·`; `�` is a piece that is part of one character's UTF-8 bytes.

| Tokenizer | `7` | `42` | `1999` | `2026` | `12345` | `1234567` | `3.14159` | `-0.0001` | `1,50,000` | `1,000,000` |
|---|---|---|---|---|---|---|---|---|---|---|
| p1536 (frozen) | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| o200k_base | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| o200k first 100k | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| plain 10MB 100k | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| plain 100MB 100k | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| plain 1GB 100k | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| SuperBPE 100MB t180k→200k | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| SuperBPE 100MB t80k→100k | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| SuperBPE 100MB t80k→100k upstream rule | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| SuperBPE 1GB t80k→100k | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| UW/OLMo2-8B-SuperBPE-t180k | 7 | 42 | 1·999 | 2·026 | 12·345 | 1·234·567 | 3·.·14·159 | -·0·.·0·001 | 1·,·50·,·000 | 1·,·000·,·000 |
| UW/OLMo2-8B-SuperBPE-t80k | 7 | 42 | 1·999 | 2·026 | 12·345 | 1·234·567 | 3·.·14·159 | -·0·.·0·001 | 1·,·50·,·000 | 1·,·000·,·000 |
| alisawuffles/superbpe-tokenizer-128k | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| SuperBPE 100MB t180k→200k (one file) | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| SuperBPE 100MB t80k→100k (one file) | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| SuperBPE 100MB t80k→100k upstream rule (one file) | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |
| SuperBPE 1GB t80k→100k (one file) | 7 | 42 | 199·9 | 202·6 | 123·45 | 123·456·7 | 3·.·141·59 | -·0·.·000·1 | 1·,·50·,·000 | 1·,·000·,·000 |

| Tokenizer | `1e-9` | `0x7fff` | `2026-11-28` | `10:45` | `₹2,499` | `99.9%` | `१२३४५` | `৩৬৫` | `௨௦௨௬` |
|---|---|---|---|---|---|---|---|---|---|
| p1536 (frozen) | 1·e·-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | ₹·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| o200k_base | 1·e·-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | ₹·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| o200k first 100k | 1·e·-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | ₹·2·,·499 | 99·.·9·% | १·२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| plain 10MB 100k | 1·e·-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | �·�·�·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| plain 100MB 100k | 1·e·-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | ₹·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| plain 1GB 100k | 1·e·-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | �·��·2·,·499 | 99·.·9·% | १२·३·४५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| SuperBPE 100MB t180k→200k | 1·e-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | ₹·2·,·499 | 99·.·9·% | १२·३·४५ | ৩৬·৫ | �·�·�·�·�·�·�·� |
| SuperBPE 100MB t80k→100k | 1·e-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | �·��·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| SuperBPE 100MB t80k→100k upstream rule | 1·e-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | �·��·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| SuperBPE 1GB t80k→100k | 1·e-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | �·��·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| UW/OLMo2-8B-SuperBPE-t180k | 1·e-·9 | 0·x·7·fff | 2·026·-·11·-·28 | 10·:·45 | ₹·2·,·499 | 99·.·9·% | १·२·�·�·�·�·�·� | �·�·�·�·�·� | �·�·�·�·�·�·�·� |
| UW/OLMo2-8B-SuperBPE-t80k | 1·e-·9 | 0·x·7·fff | 2·026·-·11·-·28 | 10·:·45 | �·�·2·,·499 | 99·.·9·% | �·�·�·�·�·�·�·�·�·� | �·�·�·�·�·� | �·�·�·�·�·�·�·� |
| alisawuffles/superbpe-tokenizer-128k | 1·e-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | �·�·2·,·499 | 99·.·9·% | �·�·�·�·�·�·�·�·�·� | �·�·�·�·�·� | �·�·�·�·�·�·�·� |
| SuperBPE 100MB t180k→200k (one file) | 1·e-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | ₹·2·,·499 | 99·.·9·% | १२·३·४५ | ৩৬·৫ | �·�·�·�·�·�·�·� |
| SuperBPE 100MB t80k→100k (one file) | 1·e-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | �·��·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| SuperBPE 100MB t80k→100k upstream rule (one file) | 1·e-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | �·��·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |
| SuperBPE 1GB t80k→100k (one file) | 1·e-·9 | 0·x·7·fff | 202·6·-·11·-·28 | 10·:·45 | �·��·2·,·499 | 99·.·9·% | १२·३·४·५ | ৩·৬·৫ | �·�·�·�·�·�·�·� |

## Task 3: training-text size (10 MB, 100 MB, 1 GB)

| Set | Docs | Merges learned (stop: no pair seen twice) | Train seconds (10 threads) | Mean bytes/token at 100k merges | en-web | en-synthetic | code-python | code-other | code-adjacent | math | science-pdf | hi-mr | bn-or-gu | ta-ml | te-kn | sanskrit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10MB | 2,438 | 114,809 | 3.5 | 5.693 | 4.46 | 4.77 | 3.83 | 3.76 | 3.79 | 3.83 | 4.03 | 8.68 | 7.91 | 9.12 | 7.60 | 6.52 |
| 100MB | 23,843 | 488,541 | 31.8 | 6.008 | 4.54 | 4.87 | 3.95 | 3.86 | 3.88 | 3.92 | 4.13 | 9.00 | 8.67 | 9.54 | 8.60 | 7.14 |
| 1GB | 239,774 | 1,000,000 | 378.4 | 6.117 | 4.56 | 4.90 | 4.00 | 3.89 | 3.90 | 3.95 | 4.16 | 9.15 | 8.65 | 9.90 | 8.79 | 7.54 |

## Tokenizers

| Tokenizer | Group | Source |
|---|---|---|
| p1536 (frozen) | reference | `e6b93a93a60520d7…` |
| o200k_base | reference | this script |
| o200k first 1k | o200k cut | this script |
| o200k first 10k | o200k cut | this script |
| o200k first 100k | o200k cut | this script |
| plain 10MB 1k | plain BPE | this script |
| plain 10MB 10k | plain BPE | this script |
| plain 10MB 100k | plain BPE | this script |
| plain 10MB 100k ≤32B | plain BPE | this script |
| plain 10MB 100k ≤64B | plain BPE | this script |
| plain 100MB 1k | plain BPE | this script |
| plain 100MB 1k ≤32B | plain BPE | this script |
| plain 100MB 1k ≤64B | plain BPE | this script |
| plain 100MB 10k | plain BPE | this script |
| plain 100MB 10k ≤32B | plain BPE | this script |
| plain 100MB 10k ≤64B | plain BPE | this script |
| plain 100MB 100k | plain BPE | this script |
| plain 100MB 100k ≤32B | plain BPE | this script |
| plain 100MB 100k ≤64B | plain BPE | this script |
| plain 1GB 1k | plain BPE | this script |
| plain 1GB 10k | plain BPE | this script |
| plain 1GB 100k | plain BPE | this script |
| plain 1GB 100k ≤32B | plain BPE | this script |
| plain 1GB 100k ≤64B | plain BPE | this script |
| plain 1GB 1000k | plain BPE | this script |
| SuperBPE 100MB t180k→200k | SuperBPE (ours) | this script |
| SuperBPE 100MB t180k→200k ≤32B | SuperBPE (ours) | this script |
| SuperBPE 100MB t180k→200k ≤64B | SuperBPE (ours) | this script |
| SuperBPE 100MB t180k→200k (one file) | SuperBPE (ours, one file) | this script |
| SuperBPE 100MB t80k→100k | SuperBPE (ours) | this script |
| SuperBPE 100MB t80k→100k ≤32B | SuperBPE (ours) | this script |
| SuperBPE 100MB t80k→100k ≤64B | SuperBPE (ours) | this script |
| SuperBPE 100MB t80k→100k (one file) | SuperBPE (ours, one file) | this script |
| SuperBPE 100MB t80k→100k upstream rule | SuperBPE (ours) | this script |
| SuperBPE 100MB t80k→100k upstream rule (one file) | SuperBPE (ours, one file) | this script |
| SuperBPE 1GB t80k→100k | SuperBPE (ours) | this script |
| SuperBPE 1GB t80k→100k ≤32B | SuperBPE (ours) | this script |
| SuperBPE 1GB t80k→100k ≤64B | SuperBPE (ours) | this script |
| SuperBPE 1GB t80k→100k (one file) | SuperBPE (ours, one file) | this script |
| UW/OLMo2-8B-SuperBPE-t180k | SuperBPE (released) | `c59b266e1dc9a768…` @ `695ddc45fcb4` |
| UW/OLMo2-8B-SuperBPE-t80k | SuperBPE (released) | `0a9b5dda03c25cd1…` @ `aee0ef4c2415` |
| alisawuffles/superbpe-tokenizer-128k | SuperBPE (released) | `669e1f163c577f71…` @ `fdccc3c5d682` |
