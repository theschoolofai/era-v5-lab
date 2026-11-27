# quant_error: where does quantization error come from?

One offline command that compares quantized GGUF files with their bf16 reference on the same held-out text, and writes small numbers-only files. It answers "which tensors, layers and slices lose the most" instead of one KL number per file.

```bash
python teams/12-quantization/quant_error/quant_error.py all \
  --hf-config  <hf dir with config.json>   --tokenizer <tokenizer.json> \
  --ref        <model-bf16.gguf> \
  --quant      Q8_0=<model-q8_0.gguf>  --quant Q4_K_M=<model-q4_k_m.gguf> \
  --heldout    teams/05-architecture/heldout_v1/data/heldout_v1.jsonl \
  --llama-bin  <llama.cpp>/build/bin       --out <out dir> \
  [--tokens-per-slice 1024] [--seq-len 512] [--kl-chunks 8] [--device cpu|mps|cuda] \
  [--normalize] [--export-report <export_report.json>] [--work <scratch dir>]
```

Exit 0 on success; exit 1 if `--out` is over 5 MB. Progress goes to stderr.

## Inputs

| Input | What it is |
|---|---|
| `--ref` | The bf16 GGUF of the model, made with the same export and the same llama.cpp build as the quantized files. |
| `--quant NAME=FILE` | One quantized GGUF per format (made with `llama-quantize`, router tensors stay F32, output layer `--output-tensor-type q8_0`). `NAME` labels the rows. |
| `--hf-config` | A Hugging Face folder of the same model. Only `config.json` is read; weights come from the GGUFs. olmoe and ernie4_5_moe are supported. |
| `--tokenizer` | The model's `tokenizer.json`. Used for the twin forward and to count tokens for llama.cpp. |
| `--heldout` | `heldout_v1.jsonl` (20 slices: English, 11 Indic languages, math, science, 6 code languages). Its sha256 is checked against `SHA256SUMS` beside it. |
| `--llama-bin` | `<llama.cpp>/build/bin` (needs `llama-perplexity`). The llama.cpp version is read from git in `<llama.cpp>` (else `$LLAMA_CPP_DIR`): `git describe --tags --match 'b[0-9]*'` and the short commit, e.g. `b12359 (b1b770d)`. The binary's own build number is not used: a shallow clone says "build 1". |
| `--normalize` | Pass each slice's text through the tokenizer's normalizer before llama.cpp, which cannot apply it itself (needed for p1536). The twin forward always gets the tokenizer's own normalization. |
| `--export-report` | `export_report.json` of the export; `verify.head_bias_effect` is copied to `summary.json` as `export_gap`. Nothing else is measured about the export gap here. |

## Outputs (all in `--out`; numbers only, no text, no token ids)

`format` is the `NAME` of `--quant`. An empty field is "not applicable"; `inf` is an exact match (no error).

| File | One row per | Columns |
|---|---|---|
| `tensors.csv` | tensor of each format (per expert for expert tensors) | `tensor, layer, kind, expert, ggml_type, bits_per_weight, numel, rel_err, sqnr_db, max_abs_err`. Error of the dequantized tensor against the reference: `rel_err` = ‖Ŵ-W‖/‖W‖. |
| `layers.csv` | format, slice, layer | `hidden_rel_err` = ‖h_q-h_ref‖/‖h_ref‖ of the layer's output (the quantized track runs on its own hidden states, so errors accumulate); `router_agree` = share of tokens whose top-k expert set is unchanged (empty for a dense layer). |
| `linears.csv` | format, nn.Linear (each expert; `lm_head` has an empty layer) | `rows`, `act_rel_err` = ‖X(W-Ŵ)ᵀ‖/‖XWᵀ‖ on up to 256 sampled real inputs X (an expert's: tokens routed to it). Empty `act_rel_err` when `rows` is 0 (no token reached that expert). |
| `tokens.csv` | format, slice | `n_tokens, kl_mean, kl_p99, same_top1`: KL(ref‖quant) in nats and top-1 agreement of the twin forward, in fp32 on `--device`. |
| `kl.csv` | slice, format | `chunks, tokens_scored, ppl_ratio, ppl_ratio_unc, kld_mean, kld_mean_unc, kld_99, same_top_p, time_s` from `llama-perplexity` (what users get from llama.cpp). `chunks` is 0, and the numbers are empty, for a slice under 1024 tokens (llama-perplexity refuses it). |
| `summary.json` | run | python, torch, transformers, gguf and llama.cpp versions; sha256 of the reference, every quantized file, the held-out file and the tokenizer; all settings; per-step and total wall time; `export_gap`. |

The twin forward (`tokens.csv`, `layers.csv`, `linears.csv`) uses the first `--tokens-per-slice` tokens of every slice, cut into sequences of `min(--seq-len, --tokens-per-slice)` (a last partial sequence is dropped). llama.cpp (`kl.csv`) scores up to `--kl-chunks` chunks of 512 tokens of each slice.

The slice texts and llama.cpp's scratch files (the base logits, about 260 KB per scored token at a 131k vocabulary) go to `--work`, a temporary folder removed at the end unless `--work` is given. They are never in `--out`.

## As a job on TSAI's machine

```text
Team:            12-quantization
Script:          teams/12-quantization/quant_error/quant_error.py
Command:         python teams/12-quantization/quant_error/quant_error.py all --hf-config ./inputs/<model>-hf --tokenizer ./inputs/tokenizer.json --ref ./work/<model>-bf16.gguf --quant Q8_0=./work/<model>-q8_0.gguf --quant Q4_K_M=./work/<model>-q4_k_m.gguf --heldout teams/05-architecture/heldout_v1/data/heldout_v1.jsonl --llama-bin ./work/llama.cpp/build/bin --out ./out/quant-error-<model> --device cuda [--normalize]
Config:          none; every setting is on the command line
Inputs:          the model's Hugging Face folder (config.json only is read), its tokenizer.json, the bf16 GGUF and one GGUF per format, all made beforehand; heldout_v1.jsonl and SHA256SUMS from this repository; llama.cpp b12359 built with the GPU backend (the same build made the GGUFs)
Hardware:        1 GPU; a CPU also works for the twin forward (slower); RAM for one decoder layer of the model in fp32 plus the sampled activations; the base logits of one slice on disk (about 260 KB per scored token at a 131k vocabulary: 8 chunks = about 0.5 GB)
Max time:        set from the rehearsal in REHEARSAL.md and the Task 7 pilot (see "Time" below)
Precision:       bf16 reference, the quantized files as given; the twin forward in fp32
Measures:        see "Outputs"
Outputs:         ./out/quant-error-<model>/{summary.json, tensors.csv, layers.csv, linears.csv, tokens.csv, kl.csv}; under 5 MB; no text, no token ids
```

Python environment: Python 3.12, torch, transformers 4.57, gguf (llama.cpp's gguf-py), tokenizers, numpy. No network is used. The command exits 1 when the output is over 5 MB and 0 otherwise; any error stops the run with a message and a non-zero exit code.

### Time

Rehearsal (`REHEARSAL.md`: 300 M parameters, 8 layers, 16 experts, 2 formats, 20 slices, Apple M6, Metal): about 90 s in total, of which tensors 9 s, twin forward 35 s and llama.cpp KL 42 s. The tensor step scales with the file size and the format count, the twin forward with layers x experts x formats and `--tokens-per-slice`, the KL step with the model's speed in llama.cpp x slices x formats x `--kl-chunks`. A 7 B model is not a simple multiple of this: it is measured in the OLMoE pilot (Task 7), and the job's `Max time` is set from that.

## Tests

`python teams/12-quantization/quant_error/test_cli.py` (the end-to-end test needs `LLAMA_CPP_DIR`, a built llama.cpp b12359 checkout, and the p1536 tokenizer; it is skipped with a message without them). The other modules have their own `test_*.py` in this folder.
