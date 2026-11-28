# metric_v1: the main metric across tokenizers (Lab 5, design 4)

Draft for review. Owner: `raghavTayal`. Task 2 (validation shards, bits per byte per pack and lane) uses this definition.

The brief: define the main metric so two tokenizers compare (bits per byte on fixed held-out bytes), with one fixed
segmentation per text, and list the downstream tasks beside it, including code and arithmetic.

All numbers below come from [`harness_lab/tokenizer_units.py`](harness_lab/tokenizer_units.py) on Team 5's
`heldout_v1` (1,059 documents, 15 slices); its output and the segmentation file are in
[`results/metric_v1/`](results/metric_v1/). They match dry run 2 exactly: p1536 gives 549,042 tokens and 3,775,551
UTF-8 bytes, and every slice's token and byte counts equal the run's `val/slices/<slice>/scored_tokens` and
`utf8_bytes` at step 1,221 (#869).

## 1. Definition

```text
bpb(S) = sum over scored tokens in S of  -log2 p(token | context)   /   sum over texts in S of  UTF-8 bytes(text)
```

- **Numerator:** the summed negative log-likelihood of every scored token, in bits (nats / ln 2). Sum first, divide
  once. Never average per-batch, per-window or per-document bpb.
- **Denominator:** the UTF-8 byte count of each text exactly as stored in the evaluation file, before the tokenizer's
  normalizer. It is fixed per text and does not depend on the tokenizer (section 3).
- **Scored tokens (Team 5's rule today):** a document's first window starts with BOS as input; every text token is
  scored; EOS is never scored (it has no bytes); no context crosses documents. Later windows of a long document start
  with one preceding token as context (section 2).
- **Aggregation:** a slice or pack score is pooled bits / pooled bytes. A lane score is pooled bits / pooled bytes over
  its packs (main), with the unweighted mean of its pack scores beside it. Team 5's group numbers are unweighted means
  (`indic_mean_bpb`, `three_group_bpb`), so label which one a number is.
- **Reported with every score:** total bits (or nats), UTF-8 bytes, scored tokens, tokenizer sha256, evaluation-file
  sha256, and the segmentation: `bpb@tokwin` (Team 5's token windows, `seq_len`) or `bpb@seg:<cuts_sha256>`
  (section 2).
  Without the counts, two scores cannot be pooled or checked.

**Worked example, dry run 2 at step 1,221 (#869):**

| Score | Arithmetic | Result |
|---|---|---:|
| `as` (Assamese) slice | 391,888.16 nats / ln 2 / 253,230 bytes | 2.2327 |
| Indic lane, pooled (main) | 3,760,492.52 nats of the 11 Indic slices / ln 2 / their 2,768,074 bytes | 1.9599 |
| Indic lane, unweighted mean of slices (= Team 5's `indic_mean_bpb`) | mean of the 11 slice scores | 1.9573 |
| All bytes, pooled (= TSAI's val/bpb) | 5,380,804.25 nats / ln 2 / 3,775,551 bytes | 2.0561 |

## 2. One fixed segmentation per text

**When it matters.** With one tokenizer, Team 5's token windows cut each text at the same places every time, so the
dry run trend and task 2's reference check (TSAI's 2.0561) are unaffected and stay `bpb@tokwin`. The rule below is for
comparing two tokenizers or two unit lists, and those scores are `bpb@seg:<cuts_sha256>`.

**Finding.** `DocumentWindows` cuts a document every `seq_len` tokens, and each later window starts with only the one
preceding token as context. Where the cuts fall depends on the tokenizer. On `heldout_v1` at 2,048 tokens, p1536
(549,042 tokens) has 66 context resets and C3 (579,522 tokens) has 77. They differ in 8 slices: as 6 / 7, bn 6 / 7,
kn 3 / 4, ml 2 / 3, mr 3 / 4, or 1 / 2, pa 7 / 10, te 8 / 10. So the tokenizer with fewer tokens also gets more
context per scored token, and part of its bpb gain is context, not the tokenizer. The effect is small here, but it grows
with longer documents and shorter windows, and it favours the tokenizer with more bytes per token.

**Rule (proposed).**

1. Cut each text once: take the longest prefix that holds at most a **budget** of tokens for every tokenizer being
   compared, then cut it back to its last newline, else before its last space (the pre-tokenizer joins a space to the
   word after it), else at a character boundary. Repeat on the rest. Cutting back means a piece can be well under the
   budget (of the 124 cut pieces here, the smallest has 305 tokens and 40 have under 1,500).
2. Budget = margin × window, with **margin 0.8**: 1,638 tokens for a 2,048 window. Only the window is a hard limit, so
   a later tokenizer up to 25% less efficient on a piece still fits, and earlier scores stay valid.
3. Store the cuts in a segmentation file: per text its id, text sha256 and UTF-8 byte offsets, with a header naming
   the evaluation file sha256, window, margin, budget, the sha256 of every tokenizer it was fitted to, and
   `cuts_sha256` (a hash of the id and offsets rows only, so the same cuts keep the same name). `--write-segmentation`
   writes it. [`segmentation_heldout_v1.jsonl`](results/metric_v1/segmentation_heldout_v1.jsonl) is the one for p1536
   and C3: `cuts_sha256` `6ab99203995b65d47aa51d96134e0991614611da9daa1f3be7c1c5ccd00b3386`.
4. Score each piece on its own with BOS as input, like a document, so every tokenizer sees the same pieces and the
   same contexts. A new tokenizer is first checked with `--check-segmentation`: a piece over the **window** fails (exit
   1), and then the file must be rebuilt and every score in the comparison redone, which needs the old checkpoints. A
   piece over the budget but within the window is a warning: it fits, using part of the margin. Nothing re-windows
   silently.

Checked against the other G3 tokenizers: c2 has no piece over the budget; c1 has 5 pieces over the budget (largest
1,703 tokens) and none over the window, so it fits; BrahmicTokenizer-131K has 10 pieces over the window and would need
a rebuild.

Measured on `heldout_v1`:

| Segmentation | Pieces, p1536 / C3 (1,059 documents) | Resets, p1536 / C3 | Same cuts for both |
|---|---:|---:|---|
| Token windows of 2,048 (today) | 1,125 / 1,136 | 66 / 77 | no |
| Fitted, margin 1.0 (budget 2,048) | 1,138 / 1,138 | 79 / 79 | yes |
| **Fitted, margin 0.8 (budget 1,638), proposed** | 1,183 / 1,183 | 124 / 124 | yes |
| Fixed 4,096-byte pieces | 1,709 / 1,709 | 650 / 650 | yes |
| Fixed 5,632-byte pieces (largest size tried with no piece over 2,048 tokens) | 1,464 / 1,464 | 405 / 405 | yes |

- "Reset" means two things here: a token-window reset keeps one token of context; a piece starts from BOS with none.
- A fixed byte size is rejected: dense text (math, 3.63 bytes per token) sets the size, so long Indic documents are
  cut far more often than needed: 3 to 5 times the resets of the proposed rule (5 to 8 times those of margin 1.0).
- The cost of the proposed rule: 124 resets against p1536's own 66 (C3: 77), more in every slice with long documents
  (for example pa 15 against 7 / 10, math 27 against 16). Absolute `bpb@seg` is therefore a little higher than
  `bpb@tokwin`; only scores with the same segmentation sha256 compare. Margin 1.0 adds only 13 resets over p1536's
  own (the proposed margin adds 58) but leaves no room: there, both tokenizers already have a piece of exactly 2,048
  tokens.
- Measured on `heldout_v1`, the cuts add no tokens: the pieces hold exactly the tokens of the whole texts (549,042 for
  p1536, 579,522 for C3), and their normalized bytes add up to those of each whole text (0 failures). This is not
  guaranteed for every text (a cut at a character boundary or inside a run of spaces can change tokens), so the script
  counts both for every file.
- The file is fitted to one window. A model with a longer context needs its own file.
- The quick profile of the mini-benchmark (#929) uses fixed prefixes of at most 1,024 bytes, so it needs no change.

## 3. Bytes: as stored, not normalized, not decoded from shards

p1536 and C3 share one normalizer: NFC, then 15 rewrites to single letters (6 Malayalam chillu forms, 3 Bengali and
6 Gurmukhi nukta letters, e.g. Bengali DDA + NUKTA to RRA). Assamese is written in the Bengali script, so on
`heldout_v1` the normalizer changes every document in as, bn and pa, and nothing in the other 12 slices. NFC alone
changes no document: all of the change comes from the rewrites.

| Slice | Documents changed | UTF-8 bytes before | After the normalizer | Change |
|---|---:|---:|---:|---:|
| as | 20 of 20 | 253,230 | 249,282 | −3,948 (−1.6%) |
| bn | 27 of 27 | 265,042 | 259,303 | −5,739 (−2.2%) |
| pa | 27 of 27 | 254,686 | 251,575 | −3,111 (−1.2%) |

Within one run, the denominator is a constant factor per slice, so it cannot change a slice's trend. It matters in
three places: pooling slices into a lane (the normalized bytes would under-weight as, bn and pa), comparing slices,
and comparing tokenizers whose normalizers differ. In size: dividing by the normalized bytes would raise these slices
by 1.2–2.2% (0.035, 0.048 and 0.028 at dry run 2), about a sixth to a third of their late checkpoint variation in
#929. Team 5's `evaluate()` already divides by the stored bytes and checks byte conservation against the normalized
ones. Keep it.

**Condition for a comparison:** a normalizer that drops information (NFKC, lowercasing) makes its model predict a
simpler string, and stored bytes in the denominator do not correct that. So:

- Same normalizer (p1536 and C3): comparable on every slice.
- One side has a normalizer that only rewrites spellings, the other has none (p1536 against c1, c2 or
  BrahmicTokenizer-131K, which have no normalizer): comparable, but the slices the normalizer changes are flagged.
  Here that is as, bn and pa (74 documents, 1.2–2.2% of their bytes): the p1536 model never has to predict whether a
  nukta letter was stored composed or decomposed, the other model does.
- A normalizer that folds case or compatibility forms: not comparable on the slices it changes.

**For task 2 (validation shards).**

- A shard's `docs.parquet` has `n_tokens` and `n_chars` but no byte count, and decoding a shard (`decode_shard.py`)
  gives the normalized text. Bytes counted from decoded shards are therefore wrong for as, bn and pa. A byte field we
  ask Team 1 to add should count the UTF-8 bytes of the text before the tokenizer. Until then, count bytes from the
  cleaned text the shard was built from.
- Shard documents end with EOS (130822), and `n_tokens` counts it (`shard_writer.py`: `len(ids) + 1`). Scored tokens
  per document are `n_tokens − 1`; leave the EOS loss out of the numerator, and use the `.idx.npy` document starts so
  no context crosses documents.

Both tokenizers rebuild the normalized text exactly: `decode(encode(text))` equals it for all 1,059 documents, with
0 failures for p1536 and C3. So the scored tokens cover every normalized byte.

## 4. Per-token numbers do not compare across tokenizers

| Slice group | Bytes per token, p1536 | Bytes per token, C3 | p1536 tokens / C3 tokens |
|---|---|---|---|
| Indic (11 slices) | 7.88–10.53 | 6.76–9.52 | 0.844 (or) to 0.955 (hi) |
| code | 3.88 | 4.00 | 1.030 |
| en, math, sci | 4.67, 3.63, 5.05 | 4.68, 3.64, 5.06 | 1.000–1.002 |
| all 1,059 documents | 6.88 | 6.51 | 0.947 |

At the same bpb, the tokenizer with fewer tokens has a higher loss per token. So per-token loss, `val/perplexity` and
tokens per second do not compare across tokenizers. Convert them to bytes: bits per byte, bytes per second. A fair
comparison trains each model on the same number of **bytes**, with the same non-embedding parameters, and reports the
training FLOPs per byte beside the score: at the same bytes, the tokenizer with more bytes per token takes fewer steps,
and with a context window counted in tokens it also sees more bytes of context in training. Long-context lengths are
stated in bytes beside tokens.

## 5. Downstream tasks beside bpb, and why

Pooled bpb averages over all bytes. A change of units moves the hard decisions (where a number splits, how an Indic
word breaks, how code indentation is cut), and those show in task scores more than in pooled bpb. Each task is scored
so that its own unit does not depend on the tokenizer. Rows come from the mini-benchmark (#929), `benchmarks_v1.md`
(main) and the Lab 5 benchmark plan (#931); each row keeps its approval status from there.

| Task | Scored as | Unit question | Meaningful from |
|---|---|---|---|
| Held-out bpb per slice | section 1 | none: bytes | the first checkpoints (#929: the first signal at 100M–1B tokens) |
| Multiple choice: MMLU, MILU (hi, te, ta, bn); diagnostic: ARC-Challenge, Belebele, HellaSwag (internal only, #909); ARC-Easy awaiting approval (#929) | rank options by log-likelihood / continuation **bytes**, as #929 | per-token length normalization would change with the tokenizer, so it is not used | above chance; SE at chance is 3.3–6.1 points on full (#929) |
| Arithmetic (5 small sets, one in Devanagari) | exact match on generated answers; also gold-answer bpb | both tokenizers group ASCII digits in runs of 1–3 (pre-tokenizer `\p{N}{1,3}`; "0123456789" is 4 tokens), but 10 Devanagari digits take 9 tokens, so the same sum is cut differently by script. A unit list with single digits changes arithmetic far more than bpb | gold bpb now; exact match later |
| Code: HumanEval, MBPP | pass@1 on generations; reference-code bpb now | indentation: after a newline, an 8-space indent becomes the newline, 7 spaces and the next word with its space (same in both). Joint encoding of prompt and code moves the prompt's token boundary (#929: 50 of 50 HumanEval items), so continuations are scored by bytes or by explicit token pairs | code bpb now; pass@1 when the model writes code |
| Indic generation: IndicGenBench (Flores-IN), an evaluation set in `benchmarks_v1.md`. IN22 is pending approval (#931); FLORES+ is decontamination only | chrF on characters, after the tokenizer's normalizer (or NFC plus the 6 Malayalam chillu mappings) on both output and reference | p1536 and C3 decode to composed nukta letters (e.g. U+09DF), which NFC splits, and to atomic Malayalam chillus, which NFC leaves alone while references may use the ZWJ form. Without the same normalization on both sides, chrF marks correct output wrong | late checkpoints |
| Long context (RULER-style) | accuracy at fixed lengths | a length in tokens holds different text per tokenizer: set lengths in bytes | after the long-context stage |

## 6. A tokenizer comparison, step by step

1. Same model shape and non-embedding parameters, the same training **bytes**, the same data order, at least 2 to 3
   seeds per tokenizer. Report FLOPs per byte.
2. Check the normalizers (section 3). Build or check the segmentation file for both tokenizers (section 2).
3. Score both on the same evaluation file and segmentation file with the definition in section 1.
4. Report per slice and pooled: bits, bytes, tokens, bpb, bytes per token; then the tasks in section 5.
5. Noise: the spread across seeds (as Team 5's `compare_arms`), and a paired bootstrap over documents on the shared
   bytes. Not #929's checkpoint-to-checkpoint change, which is one run moving, not two models differing.

## 7. Open points

- **A scorer for `bpb@seg`.** Team 5's `DocumentWindows` works per document; scoring pieces needs a piece-level
  dataset that reads the segmentation file and runs each piece from BOS. Proposal: Team 9 (`raghavTayal`) adds it in
  `harness_lab`, reusing Team 5's model loading, with the same byte-conservation check.
- **Effect on the score.** With that scorer and the step 1,221 weights, score `heldout_v1` as `bpb@tokwin` and as
  `bpb@seg:6ab99203…`, and report the difference per slice.
- **Who builds the segmentation file.** Proposal: Team 9, once per evaluation file and window, with its sha256 in that
  file's manifest.
- **Packs and lanes.** `heldout_v1` has slices, not packs. Task 2 maps the validation shards' packs to the 6 lanes
  (`pack_table.json`) and reports both the pooled and the mean lane scores.
- **Validation shards.** Team 1's byte-count field (section 3).

## Reproduce

```bash
# counts, and the segmentation file fitted to p1536 and C3 (margin 0.8)
python teams/09-evaluation/harness_lab/tokenizer_units.py \
  --tokenizer p1536=<p1536>/tokenizer.json --tokenizer C3=<c3>/tokenizer.json \
  --out teams/09-evaluation/results/metric_v1/tokenizer_units.json \
  --write-segmentation teams/09-evaluation/results/metric_v1/segmentation_heldout_v1.jsonl
# other rows of the table in section 2
python teams/09-evaluation/harness_lab/tokenizer_units.py --tokenizer p1536=... --tokenizer C3=... --margin 1.0
python teams/09-evaluation/harness_lab/tokenizer_units.py --tokenizer p1536=... --tokenizer C3=... --segment-bytes 5632
# check a tokenizer against the file (exit 1 if a piece is over the window; pieces over the budget are warnings)
python teams/09-evaluation/harness_lab/tokenizer_units.py --tokenizer new=<new>/tokenizer.json \
  --check-segmentation teams/09-evaluation/results/metric_v1/segmentation_heldout_v1.jsonl
pytest teams/09-evaluation/harness_lab/tests/test_tokenizer_units.py -q
```

p1536 sha256 `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`, C3 sha256
`15468e66457b43af79f695cbe585c0d03e3cfe7a4a5d04d189dd3c6b9f02ddc3`. The script prints counts only, never text.
