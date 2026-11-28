# Design tasks 1-4: findings (G3, 28 Nov brief; for Team 4, task 00 SuperBPE)

Numbers: `design_units.md` / `.json`, made by `harness/design_units.py`. Training text: sample v0 `train/`, duplicates
removed, nested 10 MB / 100 MB / 1 GB sets. Evaluation text: the `heldout/` parts of the same 38 packs, 12 domains, up
to 1 MB each. Mean = plain average over the 12 domains. Every unit list here is lossless on every eval doc.

**Caveat:** our lists are trained and tested on the same packs (train vs heldout split). p1536 was trained on a different
corpus (corpus60, #414), so the comparison flatters our lists somewhat. The o200k and released SuperBPE lists are
outside tokenizers for all domains.

## Headline (mean bytes per token over 12 domains; higher is better)

| Unit list | Ids | Mean bytes/token | Tokens/word en-web | hi-mr | ta-ml | sanskrit |
|---|---:|---:|---:|---:|---:|---:|
| p1536 (frozen) | 131,072 | 5.95 | 1.285 | 1.622 | 2.418 | 3.454 |
| o200k_base | 200,019 | 5.28 | | | | |
| o200k, first 100k | 100,256 | 4.79 | | | | |
| plain BPE, 1 GB, 100k | 100,256 | 6.12 | 1.310 | 1.510 | 2.477 | 2.766 |
| **SuperBPE (ours), 1 GB, t80k→100k** | 100,256 | **6.60** | 1.062 | 1.386 | 2.541 | 2.792 |
| **SuperBPE (ours), 100 MB, t180k→200k** | 200,256 | **7.19** | 1.018 | 1.271 | 2.205 | 2.607 |
| UW OLMo2 SuperBPE t180k (released) | 200,005 | 4.04 | 0.941 | 4.164 | 9.087 | 6.608 |

1. **SuperBPE gives 8% more bytes per token than plain BPE at the same 100k ids** (6.60 vs 6.12, 1 GB). The gain is
   biggest in English (+23%), code-adjacent text (+20%) and math (+22%), and 9% in Hindi and Marathi.
   **It is 2–3% worse than plain BPE on Tamil, Malayalam, Telugu, Kannada, Bengali, Odia and Gujarati** at 100k: the 20k stage-2
   merges go to multi-word English and code units, and those scripts lose the stage-1 merges they would have got.
   At 200k (t180k), every domain gains, Tamil and Malayalam included (+12% over plain 1 GB 100k).
2. **The released SuperBPE split rule breaks Indic words.** `superbpe/scripts/extend_tokenizer.sh` uses
   `[^\s\p{L}\p{N}]{2,}`, which counts combining marks (`\p{M}`: vowel signs, virama) as punctuation. So "है।" splits
   into "ह" + "ै।", and stage 2 can make an Indic word *worse* than stage 1. Keeping `\p{M}` with letters (our `marks`
   rule) gives +3% mean bytes/token at 100 MB, t80k→100k (6.46 vs 6.27): **Hindi/Marathi +11%, Telugu/Kannada +7%,
   Tamil/Malayalam +4%**, English and code unchanged. Anyone building SuperBPE for Indic needs this fix.
3. **The released SuperBPE tokenizers are English-only.** UW t180k needs 2.6× (hi-mr) to 3.8× (ta-ml) the tokens of
   p1536 on Indic. They are not usable for our mix, but they get 8–13% more bytes per token than our lists on English web text, because
   they were trained on 10 GB of English.
4. **Unit caps of 32 and 64 bytes cost almost nothing.** A 64-byte cap changes the mean by at most 0.02%, a 32-byte cap by
   at most 0.15% (it removes 342 to 438 SuperBPE units and touches long Indic words most: 32 bytes is about 10 Indic
   letters). The longest uncapped unit is 232 bytes (plain) and 325 bytes (SuperBPE): runs of code or table
   characters. **Recommendation: a 64-byte cap, free.**

## Task 1: merge curves (plain BPE, 1 GB, mean bytes per token)

| Merges | 1k | 10k | 100k | 1M |
|---|---:|---:|---:|---:|
| ours | 2.49 | 4.05 | 6.12 | 7.85 |
| o200k cut | 2.06 | 3.26 | 4.79 | – |

- English gains little after 100k: +8% for ten times the merges. The Indic scripts gain 20–53% from 100k to 1M
  (ta-ml 9.90 → 15.18 bytes/token): whole Indic words keep becoming units.
- **The 1M list wastes 83% of its ids** on our 12 MB of eval text (829,275 ids never used). At 100k, 20% are unused; at
  10k, 1%.

## Task 2: lossless, unseen units, numbers

- **Lossless:** every list, every eval doc (decode(encode(x)) == normalizer(x)), including both SuperBPE encoders.
- **Unused units** (ids never produced on 12 MB of eval text): p1536 37%, o200k 64%, ours 20% (plain 1 GB 100k) and
  16% (SuperBPE 1 GB). More training text means fewer dead units: 33% → 24% → 20% for 10 MB → 100 MB → 1 GB at 100k.
- **Numbers:** p1536, o200k and all our lists split digits left to right in groups of up to 3 (`1234567` →
  `123·456·7`). The UW OLMo2 SuperBPE groups from the right (`1·234·567`), which keeps place value. Tamil digits
  (`௨௦௨௬`) fall back to bytes in every tokenizer: 8 tokens for 4 digits in p1536. Devanagari and Bengali digits are
  one token each or less.

## Task 3: training-text size and encoder rate

| Set | Merges learned | Train time (10 threads) | Mean bytes/token at 100k |
|---|---:|---:|---:|
| 10 MB | 114,809 (no pair seen twice after that) | 3.5 s | 5.69 |
| 100 MB | 488,541 | 32 s | 6.01 |
| 1 GB | 1,000,000 (the limit) | 378 s | 6.12 |

- 10 MB → 100 MB gains 5.5% at 100k; 100 MB → 1 GB gains 1.8%, mostly in Indic and Sanskrit (Sanskrit +5.6%). Beyond 1 GB
  the gain at 100k is small; it matters more for big vocabularies (10 MB cannot even fill 115k merges).
- **SuperBPE stage 2 is the expensive part:** 108 s on 100 MB but 46 min on 1 GB in 16 GB of RAM (swapping). On a
  workstation with 64 GB+ it should scale near linearly.
- **Encoder rate, one core:** plain BPE 0.5–0.7M tokens/s at 100k (p1536: 0.66M), SuperBPE as one file 0.53–0.58M,
  o200k (tiktoken) 3.0M, released SuperBPE 1.1–1.3M. The two-stage Python encoder (0.2M) is for checking only; the
  one-file export gives the same counts (within 0.013%) at about 3× the rate.

## Task 4: against the released SuperBPE

See finding 3. For our mix, our SuperBPE beats every released one by 58–83% on the 12-domain mean. The method carries
over (finding 1); the released files and the released split rule do not (finding 2).

## Not done

- SuperBPE at 1 GB with t180k→200k (stage 2 needs more RAM than this laptop has).
- SuperBPE built on top of the frozen p1536 merges (superbpe's `extend_existing_tokenizer.sh`): this is the natural
  next step for task 00 with Team 4, and `train_super` takes any stage-1 merge list.
- Our unit lists on FLORES (Task 5's "your own unit list"): `flores_task5.py` takes any `tokenizer.json`, and the
  one-file exports are written to the work dir (`super_*.tokenizer.json`; 5–10 MB each, not committed).
