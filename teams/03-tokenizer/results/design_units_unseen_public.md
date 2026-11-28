# Design task 2: held-out units and words never seen in training

Made by `harness/design_units_unseen.py`; numbers in `design_units_unseen_public.json`. **Not sample v0.** Training and held-out text are a public stand-in built by `build_public_sample.py`: FineWeb-2 (11 Indic languages and Sanskrit) and FineWeb-Edu (English), en-fineweb-edu 345 MB, ind-hi-fw2 173 MB, ind-mr-fw2 58 MB, ind-bn-fw2 58 MB, ind-as-fw2 58 MB, ind-ta-fw2 58 MB, ind-te-fw2 58 MB, ind-kn-fw2 58 MB, ind-ml-fw2 58 MB, ind-gu-fw2 58 MB, ind-pa-fw2 58 MB, ind-or-fw2 58 MB, ind-sa-fw2 58 MB. No code, math or science text, so only the domains below are measured. The method and training settings are those of `design_units.py` (its prep, train_plain, train_super and one_file, unchanged), but the lists differ from the ones in `design_units.md`, and these numbers are not comparable with it one to one.

- **Unseen unit:** a unit that the list's own training text (100 MB or 1 GB) never produces when encoded with that list.
- **Unseen word:** a held-out word (maximal non-whitespace run) that never occurs in the training text.
- **Byte piece:** a token that is only part of one character's UTF-8 bytes.
- **p1536** is measured against our 1 GB set for reference only: it was trained on corpus60 (#414), not on this text.
- **Mean:** plain average over the 6 domains measured.

## Headline

| Unit list | Ids | Trained on | Ids never produced on training text | Held-out tokens that are unseen units | Held-out words unseen | Tokens/word seen → unseen | Byte pieces seen → unseen | Mean bytes/token (check) |
|---|---:|---|---:|---:|---:|---|---|---:|
| p1536 (frozen) | 131,072 | 1GB | 10.3% | 0.003% | 14.8% | 1.86 → 4.49 | 0.4% → 0.7% | 7.847 |
| plain 100MB 100k | 100,256 | 100MB | 0.5% | 0.004% | 25.0% | 1.48 → 3.60 | 0.1% → 0.6% | 8.661 |
| plain 1GB 100k | 100,256 | 1GB | 0.1% | 0.000% | 14.8% | 1.63 → 4.07 | 0.2% → 0.7% | 8.771 |
| SuperBPE 100MB t80k→100k | 100,256 | 100MB | 0.4% | 0.003% | 25.0% | 1.50 → 3.65 | 0.2% → 0.7% | 9.082 |
| SuperBPE 100MB t180k→200k | 200,256 | 100MB | 1.1% | 0.016% | 25.0% | 1.32 → 3.26 | 0.1% → 0.4% | 10.275 |

Check column: mean bytes/token on the held-out text.

## Held-out tokens that are unseen units, by domain

| Unit list | en-web | hi-mr | bn-or-gu | ta-ml | te-kn | sanskrit |
|---|---:|---:|---:|---:|---:|---:|
| p1536 (frozen) | 0.009% | 0.001% | 0.000% | 0.000% | 0.001% | 0.001% |
| plain 100MB 100k | 0.006% | 0.002% | 0.006% | 0.001% | 0.001% | 0.003% |
| plain 1GB 100k | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% | 0.000% |
| SuperBPE 100MB t80k→100k | 0.006% | 0.000% | 0.006% | 0.000% | 0.001% | 0.004% |
| SuperBPE 100MB t180k→200k | 0.023% | 0.009% | 0.014% | 0.012% | 0.021% | 0.014% |

## Held-out words never seen in training, by domain (share of word occurrences)

| Unit list | en-web | hi-mr | bn-or-gu | ta-ml | te-kn | sanskrit |
|---|---:|---:|---:|---:|---:|---:|
| p1536 (frozen) | 2.8% | 4.9% | 6.5% | 20.4% | 21.3% | 33.1% |
| plain 100MB 100k | 5.8% | 10.4% | 15.0% | 37.3% | 36.1% | 45.7% |
| plain 1GB 100k | 2.8% | 4.9% | 6.5% | 20.4% | 21.3% | 33.1% |
| SuperBPE 100MB t80k→100k | 5.8% | 10.4% | 15.0% | 37.3% | 36.1% | 45.7% |
| SuperBPE 100MB t180k→200k | 5.8% | 10.4% | 15.0% | 37.3% | 36.1% | 45.7% |

## What happens to unseen words: tokens per word, seen / unseen

| Unit list | en-web | hi-mr | bn-or-gu | ta-ml | te-kn | sanskrit |
|---|---:|---:|---:|---:|---:|---:|
| p1536 (frozen) | 1.23 / 3.73 | 1.55 / 3.83 | 1.75 / 4.08 | 2.07 / 4.22 | 2.03 / 4.21 | 2.54 / 6.88 |
| plain 100MB 100k | 1.21 / 3.50 | 1.30 / 3.06 | 1.43 / 3.31 | 1.73 / 3.60 | 1.67 / 3.62 | 1.57 / 4.49 |
| plain 1GB 100k | 1.25 / 4.13 | 1.38 / 3.46 | 1.54 / 3.75 | 1.97 / 4.07 | 1.89 / 4.03 | 1.76 / 4.99 |
| SuperBPE 100MB t80k→100k | 1.19 / 3.49 | 1.29 / 3.11 | 1.45 / 3.39 | 1.77 / 3.64 | 1.71 / 3.66 | 1.60 / 4.59 |
| SuperBPE 100MB t180k→200k | 1.15 / 3.24 | 1.17 / 2.79 | 1.24 / 3.00 | 1.48 / 3.18 | 1.43 / 3.24 | 1.43 / 4.11 |

## What happens to unseen words: byte-piece share of their tokens, seen / unseen

| Unit list | en-web | hi-mr | bn-or-gu | ta-ml | te-kn | sanskrit |
|---|---:|---:|---:|---:|---:|---:|
| p1536 (frozen) | 0.0% / 0.4% | 0.1% / 0.4% | 0.7% / 1.6% | 0.1% / 0.4% | 0.4% / 0.5% | 1.0% / 1.0% |
| plain 100MB 100k | 0.0% / 0.9% | 0.0% / 0.5% | 0.4% / 1.0% | 0.2% / 0.6% | 0.2% / 0.4% | 0.1% / 0.2% |
| plain 1GB 100k | 0.0% / 1.5% | 0.1% / 0.6% | 0.4% / 1.1% | 0.2% / 0.7% | 0.2% / 0.3% | 0.1% / 0.1% |
| SuperBPE 100MB t80k→100k | 0.0% / 1.0% | 0.1% / 0.5% | 0.5% / 1.2% | 0.2% / 0.7% | 0.3% / 0.6% | 0.2% / 0.2% |
| SuperBPE 100MB t180k→200k | 0.0% / 0.8% | 0.0% / 0.3% | 0.2% / 0.7% | 0.1% / 0.4% | 0.1% / 0.3% | 0.1% / 0.1% |

## Most frequent unseen units on held-out text

- **p1536 (frozen):** `.Created` (1), `=response` (1), ` 검색` (1), `.tf` (1), ` integra` (1), `abilirsiniz` (1), ` schade` (1), `(template` (1), ` gord` (1), ` Leute` (1)
- **plain 100MB 100k:** ` stim` (9), ` ହାଇକ` (3), ` श्रीमन` (2), ` आकडेव` (1), `વ્યાસ` (1), `uque` (1), ` चेय` (1), `దేహ` (1), ` গোস্ব` (1), ` ଚଳଚ୍ଚ` (1)
- **plain 1GB 100k:** none
- **SuperBPE 100MB t80k→100k:** ` stim` (9), ` ହାଇକ` (3), ` श्रीमन` (2), `దేహ` (1), ` चेय` (1), `વ્યાસ` (1), `अध्यायः` (1), `uque` (1), ` ଚଳଚ୍ଚ` (1), ` आदिव` (1)
- **SuperBPE 100MB t180k→200k:** ` stim` (9), ` ഇറക്കുമ` (5), `dard` (4), `ినియోగ` (4), ` perenn` (3), ` ହାଇକ` (3), ` ಇದ್ದಕ್ಕಿದ್ದ` (2), `igler` (2), `asg` (2), ` Duch` (2)

## Files

| Unit list | tokenizer.json sha256 |
|---|---|
| p1536 (frozen) | `e6b93a93a60520d7…` |
| plain 100MB 100k | `411995293fe6863e…` |
| plain 1GB 100k | `f5844f608bd2ac21…` |
| SuperBPE 100MB t80k→100k | `cfa9d27f3474d109…` |
| SuperBPE 100MB t180k→200k | `f9cbfd81a4f8912a…` |

Environment: Python 3.13.18, tokenizers 0.23.3, x86_64, 2 CPUs.
