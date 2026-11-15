# eval_v1: SFT evaluation (code and chat-format sections)

Status: draft from the WP3 bench, 14 Nov 2026. This file holds the **code** and **chat-format** scorers and their split rules.
Tool-call, Indic and safety sections are WP15. Implementation: [`bench/evaluate.py`](bench/evaluate.py) (a separate process:
the trainer never imports it or reads its inputs). Measured on SmolLM2-135M: [`../results/small_sft.md`](../results/small_sft.md).

## Splits (code)

- **Unit:** the near-duplicate cluster of the problem family key, never a row. An OCR-2 pack row's `source_id` is a
  completion id, and one problem has many completions. The family key (exact statement identity across TACO, APPS and
  code_contests) comes from the pack sidecar. Clusters come from the 10 Nov MinHash signatures (word 5-grams, LSH 32×4,
  estimated Jaccard ≥ 0.8), rebuilt with the same code and checked for parity with `combine_dedup.py`.
- **Assignment:** salted sha256 of the cluster id (salt `g10-bench-slice-v1`) against cumulative fractions. The WP3 bench
  uses 0.70/0.10/0.20, because only 747 families in shards 0-3 fit 2,048 surrogate tokens. Zero overlap is checked at
  cluster, family, question-hash and OCR question-id level, and the build stops otherwise.
- **Held-out guard:** a training-pack row whose cluster contains a WP1 `heldout_eval_v1` family is dropped. A row whose family
  is itself held out stops the build. The WP1 held-out file is never opened; only its id list is read.
- **Dev for decisions, test sealed:** learning rates and any config choice use dev. Test is uploaded or read only after the
  config is frozen.

## Scorers

| Scorer | Definition | Notes |
|---|---|---|
| Target bits per byte | Σ NLL (nats) over masked target tokens, teacher forced / ln 2 / target UTF-8 bytes | Targets are the `convert.py` mask (assistant body + its `<\|im_end\|>`; never the final `<\|endoftext\|>`). Bytes = UTF-8 bytes of the G10-surface assistant spans, each byte once, recomputed from `surrogate_text` at evaluation time (never per-token offsets: byte-fallback tokens share offsets). Loss code is the trainer's. |
| Format validity | Share of prompts (one per cluster, greedy, total ≤ 2,048 tokens) whose generation stops on `<\|im_end\|>`, has no foreign special token, and whose prompt + generation + `\n<\|endoftext\|>` is accepted by `chat-format/render.py` `parse()` with exactly one new non-empty assistant turn | Sub-rates reported: closed, hit budget, has think, valid with a code block, reason counts. Generation ids are decoded per segment, so a marker typed as plain text cannot pass as a marker. |
| Execution pass@1 | Greedy completion's last python block through `rl-data/stdio_check.score` (Docker `python:3.12-slim`, no network, 512 MB, expected outputs never enter the sandbox), up to 100 problems | Tests come from the pinned sources (TACO/APPS `input_output`, code_contests public + private + generated), at most 20 per problem, accepted only when the source row's family hash equals the slice row's. Call-based (`fn_name`) and file-I/O problems are skipped. Scorer ceiling measured with dev reference solutions: 17/24. |
| Forgetting | Bits per byte on G5 `heldout_v1.jsonl` (sha256 `21c6e4b2…12bb`) with the model's tokenizer, G5 protocol: each document alone, BOS before the first window, non-overlapping 2,048-token windows with the previous token as context; per-slice Σ nats / ln 2 / Σ bytes via G5 `scoring.source_slices`, groups via `scoring.group_metrics` | Report Δ versus the untrained base on the same backend. |
| Eval-mini | Team 9 `harness/run_eval_mini.py --profile mini --tasks arc_challenge hellaswag`, primary metric with stderr | Black box in its own virtualenv. Only scores are read. |

## Chat format for a surrogate tokenizer

A surrogate maps every G10 marker to one existing special token (no new embedding rows); see [`bench/retok.py`](bench/retok.py)
and the table in [`bench/README.md`](bench/README.md). Rows containing an unmapped marker or a surrogate special surface in
content are rejected and counted. Caveat measured on SmolLM2-135M base: its chat specials have near-identical untrained
embeddings, and a LoRA run with frozen embeddings produced 0% format validity (cause not established by a control). Report
format validity per method, never only the bpb.

## Every SFT run reports
Untrained base on the same table and backend; target bpb; format validity with reason counts; exec pass@1; forgetting Δ by
group; eval-mini; seeds and spread; hardware, dtype, batch, sequence cap, seconds per 100 steps, peak memory; slice and model sha256.
