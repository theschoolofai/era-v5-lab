# Task 00, G3 side: SuperBPE units on top of frozen p1536 (public text)

Stage 2 learned 859,747 merges in 541 s. Data per domain (MB): en-web C 1.0 / B 5.0 / A 8.0; math C 1.0 / B 5.0 / A 8.0; code-python C 1.0 / B 5.0 / A 8.1; hi C 1.0 / B 5.0 / A 8.0; mr C 1.0 / B 5.1 / A 8.0; bn C 1.0 / B 5.0 / A 8.0; ta C 1.0 / B 5.0 / A 8.0; te C 1.0 / B 5.0 / A 8.0; sa C 1.0 / B 5.0 / A 8.0

## Tokens vs p1536 (times fewer tokens on held-out C; higher is better)

| Unit list | Ids | en-web | math | code-python | hi | mr | bn | ta | te | sa | **Mean** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| p1536 | 131,072 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **1.00** |
| p1536+SuperBPE 262k cap32 | 262,144 | 1.33 | 1.39 | 1.18 | 1.43 | 1.32 | 1.40 | 1.26 | 1.30 | 1.69 | **1.37** |
| p1536+SuperBPE 524k cap32 | 524,288 | 1.42 | 1.47 | 1.23 | 1.57 | 1.46 | 1.56 | 1.39 | 1.45 | 1.86 | **1.49** |
| p1536+SuperBPE 846k cap32 | 846,794 | 1.47 | 1.52 | 1.25 | 1.63 | 1.51 | 1.62 | 1.44 | 1.52 | 1.94 | **1.55** |
| p1536+SuperBPE 966k cap64 | 966,672 | 1.47 | 1.52 | 1.25 | 1.69 | 1.56 | 1.67 | 1.53 | 1.55 | 1.97 | **1.58** |

## Bytes per token

| Unit list | en-web | math | code-python | hi | mr | bn | ta | te | sa | Mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| p1536 | 4.71 | 3.69 | 4.22 | 8.55 | 9.15 | 8.48 | 10.54 | 8.18 | 6.25 | 7.09 |
| p1536+SuperBPE 262k cap32 | 6.24 | 5.11 | 4.99 | 12.22 | 12.11 | 11.87 | 13.27 | 10.63 | 10.58 | 9.67 |
| p1536+SuperBPE 524k cap32 | 6.69 | 5.45 | 5.18 | 13.46 | 13.34 | 13.21 | 14.65 | 11.89 | 11.65 | 10.61 |
| p1536+SuperBPE 846k cap32 | 6.93 | 5.60 | 5.27 | 13.97 | 13.85 | 13.76 | 15.18 | 12.40 | 12.15 | 11.01 |
| p1536+SuperBPE 966k cap64 | 6.93 | 5.62 | 5.30 | 14.46 | 14.29 | 14.16 | 16.12 | 12.69 | 12.33 | 11.32 |

## Unseen units: share of held-out positions whose unit never occurs in the model text B

| Unit list | en-web | math | code-python | hi | mr | bn | ta | te | sa | Pooled (B/5) | Pooled (B) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| p1536 | 1.9% | 1.9% | 3.6% | 0.6% | 1.9% | 1.1% | 0.7% | 1.4% | 1.5% | 2.7% | 0.5% |
| p1536+SuperBPE 262k cap32 | 3.4% | 4.0% | 5.4% | 2.3% | 4.4% | 2.1% | 1.5% | 2.7% | 4.1% | 8.0% | 1.1% |
| p1536+SuperBPE 524k cap32 | 5.9% | 6.6% | 7.2% | 4.8% | 7.0% | 4.2% | 3.3% | 4.9% | 6.4% | 13.4% | 2.8% |
| p1536+SuperBPE 846k cap32 | 8.0% | 8.3% | 8.4% | 6.4% | 8.8% | 5.8% | 4.7% | 6.6% | 8.1% | 16.1% | 4.1% |
| p1536+SuperBPE 966k cap64 | 8.0% | 8.3% | 8.4% | 7.3% | 9.7% | 6.7% | 6.2% | 7.3% | 8.4% | 17.0% | 4.5% |

## Backoff: new units seen < m times in B written as their p1536 spelling (times fewer than p1536)

| Unit list | m | en-web | math | code-python | hi | mr | bn | ta | te | sa | Mean | Ids still needed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| p1536+SuperBPE 262k cap32 | 1 | 1.31 | 1.36 | 1.16 | 1.41 | 1.29 | 1.39 | 1.25 | 1.29 | 1.66 | 1.35 | 235,698 |
| p1536+SuperBPE 262k cap32 | 10 | 1.19 | 1.22 | 1.11 | 1.23 | 1.14 | 1.22 | 1.14 | 1.16 | 1.46 | 1.21 | 171,573 |
| p1536+SuperBPE 524k cap32 | 1 | 1.36 | 1.39 | 1.18 | 1.49 | 1.37 | 1.50 | 1.35 | 1.40 | 1.76 | 1.42 | 358,964 |
| p1536+SuperBPE 524k cap32 | 10 | 1.16 | 1.19 | 1.10 | 1.21 | 1.12 | 1.19 | 1.13 | 1.15 | 1.40 | 1.18 | 172,991 |
| p1536+SuperBPE 846k cap32 | 1 | 1.37 | 1.39 | 1.19 | 1.51 | 1.38 | 1.52 | 1.37 | 1.42 | 1.78 | 1.44 | 428,468 |
| p1536+SuperBPE 846k cap32 | 10 | 1.15 | 1.18 | 1.09 | 1.20 | 1.12 | 1.18 | 1.12 | 1.14 | 1.36 | 1.17 | 172,031 |
| p1536+SuperBPE 966k cap64 | 1 | 1.37 | 1.39 | 1.19 | 1.53 | 1.41 | 1.53 | 1.42 | 1.44 | 1.79 | 1.45 | 448,666 |
| p1536+SuperBPE 966k cap64 | 10 | 1.15 | 1.17 | 1.09 | 1.18 | 1.11 | 1.16 | 1.11 | 1.13 | 1.34 | 1.16 | 171,418 |

## Output scoring cost

| Unit list | Head size N | Lossless | Logits per byte vs p1536 | Ids used on C | Ids never in B | Shortlist K for 99% | for 99.9% | Top-131k coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| p1536 | 131,072 | yes, every doc | 1.00x | 55,948 | 48,884 | 69,976 | not reachable | 99.5% |
| p1536+SuperBPE 262k cap32 | 262,144 | yes, every doc | 1.48x | 121,123 | 75,880 | not reachable | not reachable | 95.0% |
| p1536+SuperBPE 524k cap32 | 524,288 | yes, every doc | 2.75x | 161,862 | 215,798 | not reachable | not reachable | 86.9% |
| p1536+SuperBPE 846k cap32 | 846,794 | yes, every doc | 4.30x | 179,069 | 469,481 | not reachable | not reachable | 83.7% |
| p1536+SuperBPE 966k cap64 | 966,672 | yes, every doc | 4.83x | 184,653 | 569,200 | not reachable | not reachable | 82.6% |

Notes (added by hand after the run; the table numbers are the run's output, only the list labels were renamed to their
real id counts, which the script now prints itself):

- The trainer asked for 1,000,000 stage-2 merges but found only 859,747 pairs seen at least twice in 72 MB, so the
  largest lists hold every merge learned: 846,794 ids with the 32-byte cap, 966,672 with the 64-byte cap (so the cap64
  row is a bigger list, not the same size).
- "Unseen" per domain is against that domain's B; "Pooled" is against all of B (45 MB) and against its first fifth.
- Shortlist K "not reachable": more than 1% (0.1%) of held-out positions are units never seen in B, so no shortlist
  ranked by B counts can cover 99% (99.9%) of them. Those positions need the byte path (KE2/KAS) or a backoff.
- Command (Colab CPU, 2 cores, 12 GB): `python task00_units.py --p1536 tokenizer.json --out full/`, about 17 minutes.
  p1536 sha256 checked: e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b.
