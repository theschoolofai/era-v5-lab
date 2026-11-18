# Exploratory WikiText pilot log - not the class-corpus result

Executed 2026-11-17T19:29:18.881325+00:00

## Setup

GPU NVIDIA RTX PRO 6000 Blackwell Server Edition. Precision BF16 with SDPA. Fixed pretrained weights. Batch three independent test articles.
Model HuggingFaceTB/SmolLM-135M at `1d461723eec654e65efdc40cf49301c89c0c92f4`.
WikiText-103 raw test split at `b08601e04326c79dfdd32d625aee71d232d685c3`. First three complete articles with at least 4,096 tokens. Pretraining overlap is unknown.
The 2K input is the exact suffix of the 4K input. Every condition scores the same final 512 target IDs per document using next-token alignment. Each condition scores 1,536 tokens total.

## Measured BF16 quality

| Run | Context | Setting | Mean NLL | Perplexity |
|---|---:|---|---:|---:|
| A | 2048 | Original RoPE | 2.470164 | 11.824388 |
| B | 4096 | Original RoPE | 6.693264 | 806.952112 |
| C | 4096 | YaRN ×2 | 2.482160 | 11.967088 |
| D | 2048 | YaRN ×2 | 2.470355 | 11.826650 |

YaRN 4K minus original 4K is -4.211104 nats/token. YaRN 2K minus original 2K is +0.000191.
YaRN 4K minus native 2K is +0.011996 nats/token. The 4K setting largely restores native 2K loss, with no mean improvement over the native 2K context on this sample.

## FP32 sensitivity

| Run | Mean NLL | Perplexity |
|---|---:|---:|
| A | 2.468912 | 11.809586 |
| B | 6.697379 | 810.279388 |
| C | 2.482499 | 11.971137 |
| D | 2.469834 | 11.820482 |

## Correctness checks

- PASS Identical pretrained weights. 134,515,008 parameters per model
- PASS Identical scored targets. 3 × 512 target IDs in every condition
- PASS YaRN uses original 2K reference. Frequency-ramp bounds 8 and 21, extension factor 2
- PASS Configured rotary amplitude matches the expected scalar, 1.06931472. Historical manifest label: "YaRN attention scale applied once"; the assertion checks the scalar and is not an end-to-end application count. The notebook adds no manual multiplier.
- PASS Tail projection and next-token shift. Max loss difference 0
- PASS SDPA versus eager numerical drift. Max per-document mean NLL difference 0.002087 nats/token (BF16 screen <0.02)
- PASS All four real input lengths scored. 12 document-condition rows, 1,536 scored tokens per condition

## Efficiency

The vocabulary head projects 513 rows, then drops the final unscored row. A direct short-input comparison against full logits gave zero loss difference. All three documents are batched. Gradient recording and KV caching are disabled.
The batch-size sweep tested 3, 6, 12, 24, 48 with repeated fixtures and unchanged quality sample count. Fastest tested batch was 6, about 400,418 input tokens/second. Its peak allocated memory was 2475.6 MiB with both BF16 models resident.
GPU timings include forward execution and tail cross-entropy. They exclude model loading, data loading, warmup and finite-loss host checks. Each row has three measured repeats. These are evaluation timings, with no training or cached-generation benchmark.

## Scope of the conclusion

This is an inference-only positional retrofit evaluated on three older English Wikipedia articles. It supports a candidate extension proposal and a controlled follow-up on the team checkpoint. Retrieval, multilingual evaluation and any continued-training budget remain follow-up work. TSAI selects the production context schedule.

## Reproduce

The current submission provides `notebooks/context_extension.ipynb`, a standard
Jupyter conversion of the reviewed export. See `notebooks/README.md` for the
pinned core dependencies and CUDA Run All instructions. Fresh outputs are
written below the kernel working directory in `out/context_extension_pilot/`;
committed result files are not overwritten.

The conversion preserves the scoring and document-selection functions, model
and dataset revisions, four conditions, BF16/FP32 checks and timing calculations.
It replaces presentation widgets with ordinary notebook displays and static PNG
charts. The notebook includes a labelled historical snapshot; all code-cell
execution counts remain empty because the sandbox connection was unavailable
for a fresh GPU run during conversion. Schema, syntax, numerical snapshot and
source-preservation checks passed locally.

The exact originally executed source remains in Git commit
`9539c7be6263b3fe429a5096dac8c77ed1428f63` at
`teams/05-architecture/notebooks/context_extension.py`. Its recorded isolated
replay added a launcher dependency header only. Original primary/replay hashes
are retained in `source_provenance.json`; the original replay receipt's
`notebook_sha256` field identifies the primary source. The complete supporting
download retains historical replay logs, exact token IDs and per-token losses.

## Sources

- https://huggingface.co/HuggingFaceTB/SmolLM-135M
- https://huggingface.co/datasets/Salesforce/wikitext
- https://arxiv.org/abs/2309.00071
- https://huggingface.co/docs/transformers/main/en/internal/rope_utils

WikiText derives from Wikipedia. Preserve the dataset attribution and applicable Creative Commons Attribution ShareAlike terms with redistributed fixtures. Article titles and source revision are recorded in the fixture metadata.

## Fresh-environment verification

The original source was executed from scratch in an isolated sandbox before the Jupyter conversion. All four mean NLLs reproduced exactly. See the complete download under `supporting_evidence/Replay/` and `supporting_evidence/notebook_report.html`. Performance timings remain those of the primary run because replay timing is sensitive to concurrent GPU activity.

## Provenance and scope

The experiment was executed with assistant help in the authorized personal Molab session; the notebook was reviewed before this submission was prepared. This is a surrogate fixed-weight evaluation, not an official TSAI team-model run. The native-2K SDPA/eager check is a limited engineering screen. The signed baseline remains eager, and production sequence length remains open.

## Offline verification from the repository root

```bash
python teams/05-architecture/tests/verify_context_extension.py
```

This checks the current notebook and both saved measurement snapshots without
running a new GPU experiment. No team-code speed change is proposed here.
Any later speed-only integration must satisfy the Lab 3 requirement for
byte-identical output. The pilot's BF16 SDPA/eager tolerance check is not that proof.
