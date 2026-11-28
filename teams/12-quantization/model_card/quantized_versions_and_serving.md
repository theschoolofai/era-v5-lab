# Model card text: Quantized versions and Serving, Quantization part

Date: 28 Nov 2026

Sections "Quantized versions" and "Serving" of `teams/11-release/model_card/model_card_outline.md`. Owner team:
Quantization. This file fills the two `[text: waiting for Quantization]` placeholders in `model_card_v0.md`. Release
edits it into the model card and TSAI approves it. It describes the path as tested so far. The text for the lab's own
model waits for the export of a trained checkpoint, and every number waits for TSAI.

## Quantized versions

A quantized version stores each weight in fewer bits. The file is smaller and runs faster on a laptop, and it loses
some quality. The Quantization team makes these versions in GGUF, the file format that llama.cpp and Ollama run.

The full-precision reference is bf16, which stores 16 bits per weight. The Quantization team proposes Q8_0, about 8
bits per weight, as the default version. Q6_K, about 6 bits per weight, is the candidate for a smaller file. TSAI
decides which versions the lab releases. [text: waiting for TSAI, the formats chosen at Gate 4]

Each quantized file keeps two parts at higher precision. The router, which picks the experts for each token, stays
at 32 bits. The output layer, which scores each token as the next token, stays at 8 bits.

The team scores each quantized version against the bf16 version of the same file. It compares the scores on a fixed
set of test items, and the greedy outputs on a fixed set of prompts. A version that has not been scored against its
own bf16 is not released.

| Version | Bits per weight | File size | Memory at 8,192 tokens | Speed on a laptop | Change in score against bf16 |
|---|---|---|---|---|---|
| bf16 | [number: waiting for TSAI] | [number: waiting for TSAI] | [number: waiting for TSAI] | [number: waiting for TSAI] | reference |
| Q8_0 | [number: waiting for TSAI] | [number: waiting for TSAI] | [number: waiting for TSAI] | [number: waiting for TSAI] | [number: waiting for TSAI] |
| Q6_K | [number: waiting for TSAI] | [number: waiting for TSAI] | [number: waiting for TSAI] | [number: waiting for TSAI] | [number: waiting for TSAI] |

What every GGUF version loses, at every bit width:

- The model has a bias that helps the router pick experts. The standard format has no place for it, so the export
  drops it. Some tokens then go to different experts. [number: waiting for TSAI]
- The output head adds a bias for each token. The standard format has no place for it either, so the export drops it.
  [number: waiting for TSAI]
- The lab's tokenizer changes some letters before it splits a text. A GGUF file carries only part of that step. For
  Gurmukhi, the Punjabi script, the export changes how the token strings are written. The token ids stay the same.
  Bengali and Malayalam text typed in some forms gives other token ids. [number: waiting for TSAI]

## Serving

You can run the quantized versions with llama.cpp or with Ollama on a laptop. [text: waiting for Quantization, the
steps from download to chat after the export of the lab's model]

The Quantization team checks each file in three steps before release:

1. The exported model must give the same next-token scores as the lab's model, with the two biases above set to zero.
   This check finds a wiring error in the export.
2. The bf16 GGUF file, run in llama.cpp, must give next-token scores close to the lab's model, with the two biases
   set to zero.
3. Each Ollama file must give the same greedy text in Ollama as in llama.cpp, on a fixed set of prompts.

The team ran these steps on a random model with the shape of the second dry run. They have not yet run on a trained
checkpoint. [text: waiting for Quantization, the results on the lab's model]

## Where each statement comes from (for the review, not for the model card)

| Statement | Source |
|---|---|
| Q8_0 the default, Q6_K the candidate, TSAI decides | `teams/12-quantization/docs/bitwidth_proposal.md` v2 (#853) |
| Router at F32, output layer at Q8_0 | `quantize_eval.py` defaults; bitwidth proposal v2 |
| Each format scored against its own bf16 on 20 items and 100 prompts | `jobs/2026-11-27-dryrun2-quantize-eval.md` (#862, #885) |
| The table columns | `bitwidth_table/` (#904); Lab 5 brief, task 1 |
| Router bias and head bias dropped | `ollama/README.md`, "What the GGUF version cannot carry"; `export_hf.py` `--drop-router-bias`, `--drop-head-bias` (#762, #780) |
| Gurmukhi remap, ids unchanged; Bengali and Malayalam limit | `ollama/README.md`, "Tokenizer: the normalizer in llama.cpp"; `ollama/remap_vocab.py` |
| Check 1 | `export_hf.py`, A1 with router_bias zeroed (#862) |
| Check 2 | `check_gguf_logits.py`, A3 |
| Check 3 | `ollama/package_ollama.py --smoke` (#834) |
| Tested on a random model only | `jobs/2026-11-27-dryrun2-quantize-eval.md`, "What I ran before filing"; `ollama/smoke_standin.md` |

Open for TSAI and the Quantization lead: the router bias may be kept with the ERNIE export (#838), which stock
llama.cpp and Ollama run. If TSAI chooses that route, the first bullet under "What every GGUF version loses" goes.
