# metric_v1: the main metric across tokenizers (Lab 5, design 4)

Draft for review. Owner: `raghavTayal`. Task 2 (validation shards, bits per byte per pack and lane) uses this definition.

The brief: define the main metric so two tokenizers compare (bits per byte on fixed held-out bytes), with one fixed
segmentation per text, and list the downstream tasks beside it, including code and arithmetic.

All numbers below come from [`harness_lab/tokenizer_units.py`](harness_lab/tokenizer_units.py) on Team 5's
`heldout_v1` (1,059 documents, 15 slices), output in [`results/metric_v1/`](results/metric_v1/). They match dry run 2
exactly: p1536 gives 549,042 tokens and 3,775,551 UTF-8 bytes, and every slice's token and byte counts equal the
run's `val/slices/<slice>/scored_tokens` and `utf8_bytes` at step 1,221 (#869).

## 1. Definition

```text
bpb(S) = sum over scored tokens in S of  -log2 p(token | context)   /   sum over texts in S of  UTF-8 bytes(text)
```

- **Numerator:** the summed negative log-likelihood of every scored token, in bits (nats / ln 2). Sum first, divide
  once. Never average per-batch, per-window or per-document bpb.
- **Denominator:** the UTF-8 byte count of each text exactly as stored in the evaluation file, before the tokenizer's
  normalizer. It is fixed per text and does not depend on the tokenizer (section 3).
- **Scored tokens:** each segment starts with BOS as input only. Every text token is scored. EOS is not scored: it
  has no bytes. This is Team 5's `bos_then_all_text_tokens_document_isolated` rule. No context crosses documents.
- **Aggregation:** a slice or pack score is pooled bits / pooled bytes. A lane score is pooled bits / pooled bytes over
  its packs (main), with the unweighted mean of its pack scores beside it.
- **Reported with every score:** total bits (or nats), UTF-8 bytes, scored tokens, tokenizer sha256, evaluation-file
  sha256 and segmentation sha256. Without the counts, two scores cannot be pooled or checked.

## 2. One fixed segmentation per text

**When it matters.** With one tokenizer, today's token windows already cut each text at the same places every time, so
the dry run trend and task 2's reference check (TSAI's 2.0561 on `heldout_v1`) are unaffected and keep token windows.
The rule below is for comparing two tokenizers or two unit lists.

**Finding.** `DocumentWindows` cuts a document every `seq_len` tokens, and each later window starts with only the one
preceding token as context. Where the cuts fall depends on the tokenizer. On `heldout_v1` at 2,048 tokens, p1536
(549,042 tokens) has 66 context resets and C3 (579,522 tokens) has 77. They differ in 8 slices: as 6 / 7, bn 6 / 7,
kn 3 / 4, ml 2 / 3, mr 3 / 4, or 1 / 2, pa 7 / 10, te 8 / 10. So the tokenizer with fewer tokens also gets more
context per scored token, and part of its bpb gain is context, not the tokenizer. The effect is small here, but it grows
with longer documents and shorter windows, and it favours the tokenizer with more bytes per token.

**Rule (proposed).** Cut each text once into the longest pieces that fit the window for **every** tokenizer being
compared, each ending at the last newline (else space, else character boundary) that fits. Store the cuts as byte
offsets of the stored text in a segmentation file with its sha256, and score every tokenizer on those pieces, each
with BOS, like a document. A later tokenizer must fit the same pieces; if one does not, the scorer stops with an error
and the file is rebuilt for all tokenizers. It never re-windows silently.

Measured on `heldout_v1` (`fitted_segments` in the script):

| Segmentation | Pieces, p1536 / C3 (1,059 documents) | Context resets, p1536 / C3 | Same cuts for both |
|---|---:|---:|---|
| Token windows of 2,048 (today) | 1,125 / 1,136 | 66 / 77 | no |
| Fitted to both tokenizers (proposed) | 1,138 / 1,138 | 79 / 79 | yes |
| Fixed 4,096-byte pieces | 1,709 / 1,709 | 650 / 650 | yes |
| Fixed 5,632-byte pieces (largest size tried with no piece over 2,048 tokens) | 1,464 / 1,464 | 405 / 405 | yes |

A fixed byte size is rejected: dense text (math, 3.63 bytes per token) sets the size, so long Indic documents are cut
far more often than needed, with 5 to 8 times the resets of the fitted rule. The fitted rule gives both tokenizers the
same cuts at a cost of 2 resets more than C3's own windows. Compare only scores with the same segmentation sha256.
The quick profile of the mini-benchmark (#929) already uses fixed prefixes of at most 1,024 bytes, so it needs no
change.

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

Dividing by the normalized bytes would raise the bpb of these slices by 1.2–2.2%, about 0.03–0.05 at today's
2.0–2.3. That is a third of the change between nearby checkpoints on an Indic slice (0.12–0.17, #929). Team 5's
`evaluate()` already divides by the stored bytes and checks byte conservation against the normalized ones. Keep it.

**For task 2.** A shard's `docs.parquet` has `n_tokens` and `n_chars` but no byte count, and decoding a shard
(`decode_shard.py`) gives the normalized text. Bytes counted from decoded shards are therefore wrong for as, bn and pa.
The byte field Team 1 adds to the validation shards must count the UTF-8 bytes of the text before the tokenizer.
Until it lands, count bytes from the cleaned text the shard was built from, not from the decoded shard.

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
tokens per second do not compare across tokenizers. Convert them to bytes: bits per byte, bytes per second. For the
same reason, a tokenizer comparison trains each model on the same number of **bytes**, not tokens, and states long
context lengths in bytes beside tokens.

## 5. Downstream tasks beside bpb, and why

Pooled bpb averages over all bytes. A change of units moves the hard decisions (where a number splits, how an Indic
word breaks, how code indentation is cut), and those show in task scores more than in pooled bpb. Each task below is
scored so that its own unit does not depend on the tokenizer.

| Task (from #929, #931) | Scored as | Unit question | Meaningful from |
|---|---|---|---|
| Held-out bpb per slice | section 1 | none: bytes | the first checkpoints (#929: the first signal at 100M–1B tokens) |
| Multiple choice: MMLU, MILU (hi, te, ta, bn), ARC-Easy, ARC-Challenge, Belebele, HellaSwag (internal only, #909) | rank options by log-likelihood / continuation **bytes**, as #929 | per-token length normalization would change with the tokenizer, so it is not used | above chance; SE at chance is 3.3–6.1 points on full (#929) |
| Arithmetic (5 small sets, one in Devanagari) | exact match on generated answers; also gold-answer bpb | digits: both tokenizers group ASCII digits in runs of 1–3 (pre-tokenizer `\p{N}{1,3}`, 0.4 tokens per digit), but 10 Devanagari digits take 9 tokens, so the same sum is cut differently by script. A unit list with single digits changes arithmetic far more than bpb | gold bpb now; exact match later |
| Code: HumanEval, MBPP | pass@1 on generations; reference-code bpb now | indentation: 8 spaces are one token in both. Joint encoding of prompt and code moves the prompt's token boundary (#929: 50 of 50 HumanEval items), so continuations are scored by bytes or by explicit token pairs | code bpb now; pass@1 when the model writes code |
| Indic generation: IN22, FLORES | chrF (characters, no tokenizer) | none | late checkpoints |
| Long context (RULER-style) | accuracy at fixed lengths | a length in tokens holds different text per tokenizer: set lengths in bytes | after the long-context stage |

## 6. A tokenizer comparison, step by step

1. Same model shape and the same training **bytes** for each tokenizer.
2. Score both on the same evaluation file and the same segmentation file (section 2), with the definition in section 1.
3. Report per slice and pooled: bits, bytes, tokens, bpb, bytes per token; then the tasks in section 5.
4. A difference smaller than the checkpoint-to-checkpoint change of that slice (#929) is noise.

## 7. Open points

- **Effect on the score.** Once the step 1,221 weights are shared, score `heldout_v1` with token windows and with the
  fitted pieces, and report the difference per slice (expected small: 79 against 66 resets).
- **Who builds the segmentation file.** Proposal: Team 9 builds it once per evaluation file and records its sha256 in
  that file's manifest.
- **Validation shards.** Team 1's byte-count field (section 3).

## Reproduce

```bash
python teams/09-evaluation/harness_lab/tokenizer_units.py \
  --tokenizer p1536=<p1536>/tokenizer.json --tokenizer C3=<c3>/tokenizer.json \
  --out teams/09-evaluation/results/metric_v1/tokenizer_units.json
```

p1536 sha256 `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`, C3 sha256
`15468e66457b43af79f695cbe585c0d03e3cfe7a4a5d04d189dd3c6b9f02ddc3`. The script prints counts only, never text.
