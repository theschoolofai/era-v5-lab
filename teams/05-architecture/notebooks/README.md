# Attention smoke lab

A readable marimo notebook that checks the existing G5 attention implementations
with the actual Week-2 training program. It changes no model or trainer source.

## Open the notebook

From a configured marimo/PyTorch environment, run from this directory:

```bash
marimo edit attention_smoke.py
```

The notebook opens without starting training. Use **Run verification and smoke
tests** to queue the existing verification suite and the selected smoke checks.
Jobs run one at a time to avoid loading five large models into RAM together.
Use **Refresh completed results** to update the view. Matching completed results
are validated and reused; incomplete output is preserved for inspection.

The default workspace is `attention-smoke-lab/` beneath the process working
directory. To keep it elsewhere, set `ATTENTION_SMOKE_DIR` before launching.
The nested workspace is ignored by this folder's `.gitignore`.

## What it checks

The reference plus four alternatives are loaded from the existing configuration
files: more key/value sharing, windowed attention with a learned sink, half-RoPE,
and an attention output gate. The notebook explains those labels and draws the
eight-layer attention patterns.

The model width, depth, experts, vocabulary, and attention choices remain those
of the reviewed T2 configurations. Supported smoke flags reduce only context,
batch, steps, and CPU precision:

| Check | Steps | Context | Batch | Format | Seed |
|---|---:|---:|---:|---|---:|
| CPU launch check | 6 | 160 | 1 | fp32 | 1234 |
| Optional GPU launch check | 8 | 160 | 1 | bf16 | 1234 |

A context of 160 is deliberate: it exceeds the unchanged local window of 128.
At least one synthetic document is verified to contain more than 128 tokens.
The real artifact loader validates the tokenizer and every byte-table row.
Nothing patches the identity checks or grants quality-run approval.

## Inputs and reproducibility

- Source is pinned to `c9cac5a0d5811e712212a37a01d6c540346ff1a1`.
- The published course tokenizer v0 is rebuilt from its pinned public baseline.
  Its expected SHA-256 is checked before use.
- The existing G4 builder generates the matching format-v2 raw P32 byte table.
- Only synthetic English, code, and Hindi documents are used for smoke data.
- Input hashes, commands, resolved model settings, versions, and original trainer
  manifests/metrics/summaries are retained in the workspace.
- Initial evaluation at step zero is excluded from training-loss plots.

The evidence download contains launch evidence, not official evaluation results.
The trainer's `smoke` and `eligible_for_quality_comparison` fields are checked.
Cached evidence must match the current source, artifacts, data, configuration,
and PyTorch runtime. Choose a fresh workspace when changing those inputs.

## Observed validation: 10 November 2026

The user-provided Linux notebook completed all 102 existing Week-2 tests and all
five CPU plus five GPU smoke checks. All runs had finite losses and gradients;
the final training loss was lower than the first in each observed run.
The notebook passed `marimo check`.

Observed runtime: Python 3.13.11, PyTorch 2.11.0, CUDA 13.0,
NumPy 2.4.6, tokenizers 0.22.2, PyYAML 6.0.3, marimo 0.25.2.
GPU: RTX PRO 6000 Blackwell Server Edition, approximately 95 GiB visible memory.
These are the tested installed versions; the harness's older requirements file
is unchanged. Wall times are diagnostic, not comparative speed benchmarks.

## Full-quality runs

The course permits an owner's machine when it meets the run budget. A full
comparison is a separate operation: approved real training/evaluation inputs,
source sidecars/checksums/decontamination report, approved runtime resolution,
context 2048, global batch 8, 1221 steps within 90 minutes, and all three seeds.
The short checks here do not establish full-budget memory or runtime, and no
quality run is automatically launched.

Keep tokenizer/table downloads, run outputs, model checkpoints, archives, HTML,
and PDF exports outside Git. The notebook contains no kernel URL or credential.
Notebook setup/orchestration is AI-assisted; model code is the upstream code.
