# Task 00: extreme compression, joint with Team 4 (G3 side)

Status: G3's half, for Team 4 to review. Numbers: [`task00_units.md`](task00_units.md), made by
[`../harness/task00_units.py`](../harness/task00_units.py). Builds on #887 (design tasks 1–4).

**Data caveat:** public text, not sample v0 (FineWeb-Edu English, FineMath, codeparrot Python, FineWeb-2 hi/mr/bn/ta/te/sa).
Per domain: 1 MB held-out (C), 5 MB standing in for the model's training text (B), 8 MB to learn the units (A), all
disjoint, exact duplicates removed. Absolute unseen shares depend on B's size (they fall as B grows; the table shows B/5
against B), so read them as a trend, not a 10T-token value.

## 1. Proposal: the unit list and how the model handles new units

1. **Keep p1536 as stage 1.** Ids 0–131,071 keep their meaning, sha `e6b93a93…a64b` stays the base. New units are
   SuperBPE stage-2 merges over p1536 ids (arXiv 2503.13423), appended from id 131,072. Every new unit has a fixed
   p1536 spelling, so nothing already built on p1536 (special tokens, counts #719, KE2 tables) changes.
2. **32-byte cap.** KE2's codec is `L_max = 32` and no p1536 token is longer than 32 bytes, so a 32-byte cap needs no
   codec change. The 64-byte cap buys almost nothing (row "cap64" below; #887 found ≤0.02%).
3. **Split rule:** #887's "marks" rule (Indic vowel signs and virama stay with letters; the released SuperBPE rule breaks
   Indic words). Units may cross spaces, never newlines or punctuation runs; digits stay in groups of up to 3.
4. **Unseen units, training (proposal for Team 4 to test):**
   - Input: every unit gets its KE2 vector from its bytes, so an unseen unit has an embedding.
   - Target: the KAS head also scores a unit from its bytes, plus a per-unit row (`tok_u`) and a log-unigram prior.
     For a unit seen fewer than *m* times in the training stream, use no `tok_u` row (bytes only) and a smoothed prior
     from its p1536 spelling.
   - Backoff at tokenizing time: units seen fewer than *m* times in the training stream are written as their p1536
     spelling. Then the model is never asked to predict a unit it never saw. The cost in compression is measured below.
   - Unit dropout: in training, spell a small share of new units in p1536 ids (like KAS `--tok-dropout`), so the model
     learns both forms.
   - Fair loss: report bits per byte, which does not depend on how the text is cut into units.
5. **Unseen units, inference:** p1536 is the escape. The model may emit a new unit or the p1536 ids for the same bytes;
   both decode to the same text (lossless check below). No escape token is needed.
6. **Freeze once.** Learn the unit list on a deduplicated sample, set *m* and the size, freeze, then tokenize the 10T
   corpus once.

## 2. Measured scoring cost (G3 numbers)

Held-out text, 9 domains (en-web, math, Python, hi, mr, bn, ta, te, sa), 1 MB each. Full tables: `task00_units.md`.

| Unit list | Ids N | Times fewer tokens than p1536 (mean) | Bytes/token (mean) | Unseen units (pooled, B = 45 MB) | Logits per byte vs p1536 | Top-131k units cover |
|---|---:|---:|---:|---:|---:|---:|
| p1536 | 131,072 | 1.00 | 7.09 | 0.5% | 1.00x | 99.5% |
| +SuperBPE, cap 32 | 262,144 | 1.37 | 9.67 | 1.1% | 1.48x | 95.0% |
| +SuperBPE, cap 32 | 524,288 | 1.49 | 10.61 | 2.8% | 2.75x | 86.9% |
| +SuperBPE, cap 32 (all merges) | 846,794 | 1.55 | 11.01 | 4.1% | 4.30x | 83.7% |
| +SuperBPE, cap 64 (all merges) | 966,672 | 1.58 | 11.32 | 4.5% | 4.83x | 82.6% |

1. **Merges alone do not reach 2–3x on this data.** SuperBPE on top of p1536 gives 1.37x fewer tokens at 262k ids,
   1.49x at 524k and 1.55x with every merge seen twice in 72 MB (847k). Sanskrit gains most (1.69x to 1.94x), Python least
   (1.18x to 1.25x). Going further needs much more unit-training text than 72 MB (#887: 1 GB helped Indic most) and/or
   model-side gains (Team 4's merged-unit training, multi-token prediction).
2. **The head pays more than the sequence saves above ~262k.** Logits per byte (head size times positions per byte) is
   1.48x p1536 at 262k, 2.75x at 524k, 4.30x at 847k, if every position is scored against the full list. So a full
   softmax only makes sense near 262k; bigger lists need a shortlist or a byte-built head (KAS).
3. **Unseen units grow with the list.** Share of held-out positions whose unit never occurs in the model's 45 MB text:
   1.1% (262k), 2.8% (524k), 4.1% (847k); with a fifth of that text 8.0% / 13.4% / 16.1%. At 847k, 469k of the ids never
   occur in B at all. More model text lowers it, so the 10T-token value will be much lower, but not zero.
4. **Backoff keeps most of the gain at m = 1, little at m = 10.** Writing new units never seen in B as their p1536 spelling
   gives 1.35x / 1.42x / 1.44x (262k / 524k / 847k) and needs 236k / 359k / 428k ids. Requiring 10 sightings drops it to
   1.17x–1.21x with ~172k ids. So the threshold must be set on the full training stream, not a sample.
5. **32 vs 64 bytes:** 64 adds 0.03x (1.55 to 1.58) with 120k more ids, gains only in Indic (ta +0.09x). With KE2's
   `L_max = 32`, 32 bytes is the better choice.
6. **Lossless:** decode(encode(x)) equals the normalized text on every held-out document, every list, including backoff
   (the p1536 spelling decodes to the same bytes).

## 3. Shared table (draft; Team 4 columns blank)

One row per unit list. G3 columns are measured (public text, above). Team 4 columns are for Team 4 to fill
(49M model, their protocol). Proposed by G3; Team 4 can add or change columns.

| Unit list | Ids N | Cap (bytes) | Tokens vs p1536: mean / Python / Indic (hi–te) / sa | Unseen units (B 45 MB) | Backoff m=1: times fewer / ids | Logits per byte vs p1536 | Lossless | T4: bits per byte (49M) | T4: tokens/s (training) | T4: top-10 on unseen units | T4: head time per step | T4: head memory | T4: verdict |
|---|---:|---:|---|---:|---|---:|---|---|---|---|---|---|---|
| p1536 (frozen) | 131,072 | 32 | 1.00 / 1.00 / 1.00 / 1.00 | 0.5% | – | 1.00x | yes | | | | | | |
| p1536 + SuperBPE | 262,144 | 32 | 1.37 / 1.18 / 1.34 / 1.69 | 1.1% | 1.35x / 235,698 | 1.48x | yes | | | | | | |
| p1536 + SuperBPE | 524,288 | 32 | 1.49 / 1.23 / 1.49 / 1.86 | 2.8% | 1.42x / 358,964 | 2.75x | yes | | | | | | |
| p1536 + SuperBPE | 846,794 | 32 | 1.55 / 1.25 / 1.54 / 1.94 | 4.1% | 1.44x / 428,468 | 4.30x | yes | | | | | | |
| p1536 + SuperBPE | 966,672 | 64 | 1.58 / 1.25 / 1.60 / 1.97 | 4.5% | 1.45x / 448,666 | 4.83x | yes | | | | | | |

**G3 suggestion for Team 4 to test first:** 262k (1.37x fewer tokens, head 1.48x per byte, 1.1% unseen) with KAS's byte
path for rare units, against 524k with a shortlist. The unit-list files are rebuilt by the script in about 17 minutes on
a free Colab CPU; G3 can hand Team 4 any row as `tokenizer` files on request.

## Not done / open

- Sample v0 and the 1 GB point: this run uses public text and 8 MB per domain for the units.
- Unseen share at 10T scale: only the trend (B/5 vs B) is measured.
- Team 4 columns: bits per byte at 49M, tokens per second, top-10 on unseen units, head time and memory (Team 4 design
  tasks 1–3, Avnish has the head scoring test).
- Which size and *m* to freeze: Team 3 + Team 4 propose, TSAI decides.
