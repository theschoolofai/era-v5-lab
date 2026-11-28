# Week 5: FLORES on our own unit lists, unseen held-out units, the 1 GB run: findings (G3)

Numbers: `design_units_unseen_public.md` / `.json` and `flores_task5_ours_public.md` / `.json`, made by
`harness/design_units_unseen.py` and `harness/flores_ours.py`. Covers three open items of the 28 Nov brief: Task 5 on
our own unit list, design task 2 (unseen units) and design task 3 (the 1 GB run).

**Data: not sample v0.** Sample v0 was not available to us, so `harness/build_public_sample.py` builds a public stand-in
in the same folder layout: FineWeb-2 for the 11 Indic languages and Sanskrit (58 MB each, Hindi 173 MB) and FineWeb-Edu
for English (345 MB), 1.15 GB in all, with held-out docs that never appear in training. There is no code, math or
science text. Training and evaluation use `design_units.py` unchanged (prep, train_plain, train_super, one_file,
eval_text), so with sample v0 the same commands give sample-v0 numbers. The lists are rebuilt here and are not the files
behind `design_units.md`; compare trends, not exact values. Run on Google Colab (2 CPUs, 12 GB RAM), tokenizers 0.23.3.

## Headline

| | p1536 (frozen) | plain 100MB 100k | plain 1GB 100k | SuperBPE 100MB t80k→100k | SuperBPE 100MB t180k→200k |
|---|---:|---:|---:|---:|---:|
| Ids | 131,072 | 100,256 | 100,256 | 100,256 | 200,256 |
| FLORES Indic mean tokens/word (11 languages) | 2.139 | 1.971 | 1.952 | 1.938 | 1.680 |
| FLORES Indic tokens vs p1536 | – | −8.2% | −9.1% | −10.5% | −22.1% |
| FLORES English tokens vs p1536 | – | +3.3% | +2.6% | −15.9% | −20.9% |
| FLORES Fr / De / Es tokens vs p1536 | – | +40 to +53% | +40 to +51% | +40 to +52% | +29 to +41% |
| Held-out tokens that are unseen units | 0.003%* | 0.004% | 0.000% | 0.003% | 0.016% |
| Held-out words never seen in training | 14.8%* | 25.0% | 14.8% | 25.0% | 25.0% |
| Tokens per word, seen → unseen words | 1.86 → 4.49 | 1.48 → 3.60 | 1.63 → 4.07 | 1.50 → 3.65 | 1.32 → 3.26 |

\* p1536 against our 1 GB set; it was trained on corpus60 (#414), not on this text.

## Design task 2: unseen units, and what happens to them

1. **Almost no held-out token is a unit the training text never produced:** 0.000–0.004% at 100k ids, 0.016% at 200k.
   A BPE unit is learned from training text, so nearly every unit is produced on it: only 0.1–1.1% of our ids are never
   produced on their own training text. The few unseen ones are mid-merge pieces of rare words (` stim`, ` ହାଇକ`,
   ` श्रीमन`) that training text always merged further. This is a different measure from the "unused units" of
   `design_units_findings.md` (ids never produced on the eval text: 16–20%).
2. **Unseen words are the real effect.** 25% of held-out word occurrences never occur in 100 MB of training text, and
   14.8% never occur in 1 GB. They are much commoner in Tamil/Malayalam and Telugu/Kannada (20–37%) and Sanskrit
   (33–46%) than in English (3–6%) and Hindi/Marathi (5–10%).
3. **What happens to them:** they are split into about 2.5× more tokens than seen words (plain 1 GB: 1.63 → 4.07
   tokens per word; Sanskrit 1.76 → 4.99), and they stay lossless. They fall back to subword pieces, not raw bytes: at
   most 0.7% of their tokens are byte pieces (part of one character's UTF-8 bytes).
4. **More training text halves the unseen-word share** (25.0% → 14.8% from 100 MB to 1 GB) and adds 1.3% mean bytes per
   token (8.661 → 8.771 on the held-out text).

## Task 5: FLORES on our own unit lists

1. **On Indic, every one of our lists needs fewer tokens than p1536**: −8 to −10.5% at 100k ids (with fewer ids than
   p1536's 131,072) and −22% at 200k. SuperBPE's gain is biggest in Hindi (−27% at 100k) and Punjabi (−18%), smallest
   in the Dravidian languages (−2 to −4%), as in `design_units_findings.md` finding 1.
2. **Outside English and the Indic languages they are much worse**: +40 to +53% on French, German and Spanish, and +65 to
   +150% on Russian, Chinese, Japanese and Korean, because the stand-in has no text in those languages. p1536 keeps
   o200k's coverage there.
3. **All 20 languages are lossless** with every list.
4. FLORES is near our training domain (web text), and our lists have no code ids, so these gains are an upper bound for
   a list that must also cover code. FLORES reports here; it does not choose.

## Design task 3: the 1 GB run

- `design_units.py train_plain` holds the whole set as one Python list; on 12 GB of RAM the 1 GB run was **killed (out of
  memory)**. `design_units_unseen.py train` streams the training text from `train_text.parquet` in batches instead.
  With that, **plain BPE on 1 GB finished: 300,000 merges in 685 s on 2 CPUs**. 100 MB: 85 s.
- Only the first 100k merges (plain) or 180k (SuperBPE stage 1) are used, so training stops at 300k merges
  (`--max-merges`); a prefix of a BPE is a BPE.
- SuperBPE on 1 GB (stage 2) is not in these tables: `train_super` slices a list and stage 2 needs more memory still.

## Proposed unit dictionary to name as frozen (for TSAI to decide)

- **Keep p1536 as the frozen tokenizer of the run.** None of these lists can replace it: they have no code or
  non-Indic, non-English text, and they would change the token ids.
- **For the design track and Task 00 with Team 4, name one unit dictionary: SuperBPE, marks rule, t80k→100k, trained on
  1 GB of sample v0** (`super_1GB_t80k_100k_marks`, already built in `design_units.md`, 6.60 mean bytes/token). It keeps
  the 100k id budget, beats plain BPE on both sample v0 and here (FLORES Indic −10.5% vs −9.1% for plain on 1 GB), and
  needs only the marks fix to the released split rule. Its file should be published with its sha256 before it is named.
- Reasons not to pick the 200k list yet: twice the embedding rows for −12 more points on FLORES, and 1.1% of its ids are
  never produced on its own training text.
