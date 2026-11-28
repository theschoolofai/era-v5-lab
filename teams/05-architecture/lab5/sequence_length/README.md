# Sequence-length strategy and a review of pre-training speed-ups: approach

**Brief item (Team 5, Tasks):** "Write a sequence-length strategy: the length at each stage of training, the batch size at each, and what changes when the length changes (memory, loader, evaluation). Also review published methods that speed up pre-training (for example Token Superposition Training, arXiv 2605.06546). Say which one you would test first, what it costs, and what it needs from the loader."
**Owner:** Deepjyoti Saha. **Builds on:** Revant's context-length recommendation (#825, `docs/long_context_plan.md`) and the packing plan (#831).

## What it delivers

`docs/sequence_length_plan.md` (this note grows into it), with:

1. A stage table: the training length at each stage, the batch size in rows and in tokens, and the share of the token budget.
2. For each change of length: what changes in memory, in the loader and in evaluation.
3. A review of speed-up methods, TST first, ending with the one to test first, its cost and what it needs from the loader.

## Starting point

- #825 recommends `data.seq_len = 2048` to start and 4,096 as the first extension candidate, and defers 8,192 until a 4K checkpoint shows useful long-range behaviour.
- With today's one-window-per-row loader, 4,096 needs 1.81 times the positions of 2,048 and about 3.62 times the dense attention pairs per pass (#825). Packing removes the padding part of that difference: both lengths need about 1.01B positions per pass on the 41 shards (#831), so the cost of 4,096 becomes the attention per row only.
- On the 41 shards, 28.4% of content tokens lie past the first 2,048 tokens of their document and 16.8% past 4,096; for science documents it is 80.8% and 71.1% (#825).

## Approach

1. **Inputs.** The numbers above; dry run 2's step time and memory (#869); the planning assumption of one node with 8 GPUs of 80 GB; Team 7's memory budget and the model designs (design task 2) when they are posted.
2. **Stage table.** Draft: most of the budget at 2,048, a later stage at 4,096, and the long-context step (position-free recalibration, design task 5b, or a longer stage) at the end. Keep tokens per step the same across a length change (half the rows at twice the length), so the step-indexed WSD schedule (#713) is unaffected.
3. **What changes at a switch.**
   - Memory: in the eager path the attention scores grow with the square of the length per row; packing changes the number of rows, not this.
   - Loader: re-pack at the new length; the packed format (packed_rows/) carries `pos_ids`, so positions stay per document.
   - Evaluation: score held-out bits per byte at both lengths around each switch, so the switch is visible. #825 notes that the frozen held-out set has few full-length 4K documents; long held-out examples are a Team 9 question.
4. **Speed-up review.** For each method: what it changes, its reported gain and the conditions, the cost (compute, code, risk), what it needs from the loader and from the KAS input, and the smallest test at 49M to 100M that would decide it.
   - **TST (arXiv 2605.06546)** first: the G5 trainer already has a TST switch (`harness/week2/tst.py`, #713, #773), off in dry run 2, so a test costs little code.
   - Then one or two others, for example starting with shorter sequences and lengthening them during training.
5. **Recommendation.** The method to test first and the test; a GPU run is optional this week.

## Checks

- Every number in the stage table is derived from a file or command in the note.
- The tokens-per-step rule holds at every switch.
- Each claim about a method cites the paper's own numbers and conditions, not a summary.

## What it needs from others

Team 7 (memory budget), design task 2 (model sizes), Team 9 (long held-out examples), Team 6 (loader limits).

## What it cannot tell

The final lengths depend on the model size and the corpus-v1 mix, which are not settled; the plan gives the rule and the numbers to recompute it.

## Plan and dates

| Step | What | By |
|---|---|---|
| 1 | Stage table and switch effects (draft) | Mon 30 Nov |
| 2 | TST and one other method reviewed | Tue 1 Dec |
| 3 | Final note and recommendation | Wed 2 Dec, 07:00 |
