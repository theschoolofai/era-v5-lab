# Rehearsal at the dry-run-2 shape (28 Nov 2026)

Does `quant_error.py all` run end to end on a random model of the lab's dry-run-2 shape, on the Mac, and what does it cost? The weights are random, so the numbers in the output mean nothing (for example, top-1 agreement is chance); only the plumbing, time, memory and size are being checked.

Machine: Apple M6, 32 GB, macOS (Darwin 27.2). Python 3.12.16 (g12-spike/venv-tf457), torch 2.15.0, transformers 4.57.6, gguf 0.19.0. llama.cpp `b12359 (b1b770d)`, built with Metal. Everything below ran in `~/Workspace/quant-error-runs/rehearsal-t2/` (outside the repository); `$R` is `teams/12-quantization`, `$TOK` the frozen p1536 `tokenizer.json` (sha256 `e6b93a93…`), `$L` `~/Workspace/g12-spike/llama.cpp`.

## Commands

```bash
python $R/scripts/make_random_checkpoint.py --tokenizer $TOK --out run --d-model 512 --n-layer 8 --n-head 8 \
  --n-kv-head 2 --d-ff 768 --n-expert 16 --n-shared 1 --top-k 2 --seq-len 2048 --head-mode kas_v2 \
  --bias-gamma 0.001 --router-bias-std 0.01 --std 0.02
python $R/scripts/export_hf.py --checkpoint run --out hf --target ernie4_5_moe --dtype fp32 --drop-head-bias \
  --verify 4 --tokenizer $TOK                      # A1: max logit difference 4.05e-06, same top-1 on 256/256: PASS
python $R/tokenizer/convert_frozen.py --checkpoint hf --tokenizer $TOK --tokenizer-sha256 e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b \
  --llama-cpp $L --work convert-work --out convert-report --outtype bf16 --convert-python $(which python) --llama-tokenize $L/build/bin/llama-tokenize
for q in Q8_0 Q4_K_M; do $L/build/bin/llama-quantize --output-tensor-type q8_0 convert-work/frozen.gguf model-$q.gguf $q; done
LLAMA_CPP_DIR=$L /usr/bin/time -l python $R/quant_error/quant_error.py all --hf-config hf --tokenizer $TOK \
  --ref convert-work/frozen.gguf --quant Q8_0=model-Q8_0.gguf --quant Q4_K_M=model-Q4_K_M.gguf \
  --heldout teams/05-architecture/heldout_v1/data/heldout_v1.jsonl --llama-bin $L/build/bin --out out \
  --tokens-per-slice 1024 --kl-chunks 8 --device mps --normalize --export-report hf/export_report.json
```

`convert_frozen.py` wrote `frozen.gguf` (the bf16 reference, 606 MB) and then stopped in its own round-trip report step with `ModuleNotFoundError: No module named 'datasets'` (that step streams FineWeb-2 text, and the venv has no `datasets`; it is not part of the harness). Sizes: Q8_0 325 MB, Q4_K_M 215 MB.

## Result

| | |
|---|---|
| Model | 300 M parameters (8 layers, d 512, 16 experts + 1 shared, top-2, vocabulary 131k, untied KAS V2 head), 2 formats, 20 slices |
| Exit code | 0 |
| Wall time | 87.8 s (`/usr/bin/time -l` real); by step: tensors 8.9 s, twin forward 35.2 s (both formats, MPS), llama.cpp KL 42.4 s (40 slice-format passes at 8 chunks, plus 20 base passes) |
| Peak memory | 3.05 GB maximum resident set size; 4.24 GB peak memory footprint (includes the MPS buffers) |
| Output size | 208 KB (`out/`: tensors.csv 115 KB, linears.csv 72 KB, layers.csv 17 KB, kl.csv 3 KB, tokens.csv 3 KB, summary.json 2 KB), limit 5 MB |
| Scratch (not output) | the slice texts and the llama.cpp base logits in a temporary folder, removed at the end |

Checks on the output: `kl.csv` has 40 rows, every one with 8 chunks and 2040 scored tokens; `summary.json` records `llama_cpp: "b12359 (b1b770d)"`, the sha256 of the four input files, the settings and `export_gap` copied from `export_report.json`; no CSV has a text or token-id column; `inf` appears as `inf` in `tensors.csv` (66 exact matches: norms, router, router bias, F32 tensors) and None as an empty field.

Cross-check, twin forward (PyTorch, MPS, first 1024 tokens) against llama.cpp (Metal, 8 chunks of 512, second halves scored), both on the same random model: mean KL on `c4-val` is 0.000171 against 0.000166 for Q8_0 and 0.00575 against 0.00558 for Q4_K_M. Top-1 agreement is in line for Q8_0 (89.7% against 92.5%) but not for Q4_K_M (12.6% against 45.5%); with random weights the logits are almost flat, so the top-1 is probably near-arbitrary, and the two sets of positions differ; not investigated.

## What the rehearsal found

- `tensors.tensor_errors` refused the first real pair: the converter's bf16 file stores ERNIE's `blk.N.exp_probs_b.bias` with shape `[16, 1]` and `llama-quantize` rewrites it as `[16]` (`weights.py` already ignores size-1 axes for this tensor; `tensors.py` did not). `tensors.py` now ignores size-1 axes in that comparison, with a test (`test_tensors.py::test_size_one_axes_are_ignored`).
- `git describe --tags` on the llama.cpp checkout answers `v1.0.0` (the commit carries two tags), so the version is read with `--match 'b[0-9]*'`.
