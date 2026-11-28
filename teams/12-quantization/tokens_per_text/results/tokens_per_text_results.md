# Fewer positions per text, fewer decode steps (G12 with G6, lead item 7, third part), 28 Nov 2026

**Question (Lab 5, G6 lead item 7):** fewer positions per text means fewer decode steps; measure it.

**What was measured.** For five tokenizers on the same excerpts of 10 languages: tokens per 1,000 characters (= decode steps
to write that text); then the real decode time per token of a GGUF at four context lengths; then both combined into decode
seconds and KV-cache memory per 1,000 characters. Full tables: `tokens_per_text_tables.md`; raw aggregates: `counts.json`,
`speed.json`. Script: `tokens_per_text.py` (tests: `test_tokens_per_text.py`).

| Item | Value |
|---|---|
| Tokenizers | p1536 (frozen, sha256 `e6b93a93a60520d7…`), BrahmicTokenizer-131K @ `93df154c`, sarvam-1 @ `e9607337`, Granite 3.0 3B-A800M @ `142d2c8e`, Qwen3-0.6B-Base @ `da87bfb6` |
| Texts | Wikipedia excerpts, 10 languages, 3 articles each (`texts_sources.json`: titles, revisions, sha256); about 1,000-character excerpts, at most 30 per language (17 for Gujarati: 20,710 characters; 35,000 to 49,000 for the others) |
| Model for speed | the dry-run-2-shaped stand-in GGUF (8 layers, width 512, 2 KV heads, head dim 64), random weights, llama.cpp b11669 build via llama-cpp-python 0.3.36, CPU, Apple M3 Max |
| KV cache | 4,096 bytes per token (2 x 8 layers x 2 KV heads x 64 x 2 bytes, f16), read from the GGUF metadata |

## Result

**Decode steps per 1,000 characters, mean over the nine Indic languages (p1536 = 1.00; p1536 averages 300 tokens per 1,000 characters):**

| Tokenizer | Indic mean | Range over languages | English |
|---|---:|---:|---:|
| p1536 | 1.00 | | 1.00 |
| BrahmicTokenizer-131K (the baseline) | 1.26 | 1.07 to 1.50 | 1.00 |
| sarvam-1 | 1.02 | 0.92 to 1.15 | 1.22 |
| Qwen3 | 4.12 | 3.17 to 4.63 | 1.04 |
| Granite 3.0 | 5.14 | 3.33 to 7.94 | 1.33 |

- **p1536 against the baseline:** the baseline needs 7% to 50% more decode steps for the same Indic text (mean 26%; Punjabi 1.50x,
  Kannada 1.29x, Telugu 1.29x), and the same for English.
- **p1536 against sarvam-1:** nearly level. sarvam-1 needs fewer tokens in Bengali, Hindi, Marathi and Tamil (0.92x to 0.99x of
  p1536's) and more in Gujarati, Kannada, Malayalam, Punjabi and Telugu (1.02x to 1.15x); in English it needs 22% more.
- **Tokenizers without Indic merges** (Granite 3.0, Qwen3) take 3.2 to 7.9 times the steps for the same text: Gujarati with
  Granite is 2,622 tokens per 1,000 characters, over two per character.
- **Time follows steps almost one to one.** On the Q8_0 stand-in a decode step costs 1.59 ms at empty context and 2.06 ms at
  4,096 tokens of context (fit: 1.59 ms + 0.117 microseconds per context token), so the projected decode time per 1,000
  characters tracks the step ratio (for example Punjabi with the baseline: 1.51x the time for 1.50x the steps). At this model
  size the context term is small. Per 1,000 characters with p1536: 0.33 s in English and 0.41 to 0.54 s in the Indic languages.
- **KV-cache memory follows the token count exactly:** 836 KB per 1,000 English characters and 1.0 to 1.4 MB per 1,000 Indic
  characters with p1536 (the baseline: up to 2.1 MB for Punjabi).

## Limits

- **One model for every tokenizer.** A tokenizer with another vocabulary size would change the embedding and head cost a little;
  not modelled. The speed numbers come from the same stand-in whatever the tokenizer.
- **Random-weight stand-in, CPU, one Mac (M3 Max, 64 GB).** Decode speed here says nothing about a 16 GB or 32 GB laptop or a
  GPU. bf16 decodes at 8.7 ms per token on this CPU build (no fast bf16 kernel) against 1.6 ms for Q8_0, so Q8_0 is the
  meaningful row; the bf16 section of the tables is a build artifact, not a result.
- **The 4,096-token context point is above the stand-in's training context (2,048)**; it measures speed, not quality.
- **Small, narrow text sample.** At most 30 excerpts per language from three Wikipedia articles each, so the numbers show the
  tokenizers' behaviour on this text, not on a general corpus. p1536 may have seen Wikipedia-like text in training; this was not
  checked, and would favour it. Team 3's FLORES fertility table (`teams/03-tokenizer/COMPARE.md`) is the larger comparison
  of tokenizers; this measurement adds what the counts mean at inference.
- **No speculative decoding or MTP here:** the dry run 2 model has no MTP head (Sourav's note on t2.yaml). This covers the third
  part of the G6 item only.
- Counts only, no text is written; Wikipedia text is CC BY-SA and is not committed.

## Reproduce

```bash
python tokens_per_text.py count --texts <dir of <lang>.txt> --tokenizer p1536=teams/03-tokenizer/release/tokenizer.json \
  --tokenizer brahmic-131k=theschoolofai/BrahmicTokenizer-131K@93df154cbc9dbf038a222c010d9b43906a8a72c3 \
  --tokenizer sarvam-1=sarvamai/sarvam-1@e9607337286ddf496d4a2562b194e489dcf3feea \
  --tokenizer granite-3.0=ibm-granite/granite-3.0-3b-a800m-base@142d2c8e3f7fb8844011cfa5565f0e520f0824b9 \
  --tokenizer qwen3=Qwen/Qwen3-0.6B-Base@da87bfb608c14b7cf20ba1ce41287e8de496c0cd --out counts.json
python tokens_per_text.py speed --gguf model-Q8_0.gguf --out speed.json
python tokens_per_text.py combine --counts counts.json --speed speed.json --base p1536 --out tokens_per_text_tables.md
```
The texts come from `teams/12-quantization/ollama/stage_texts.py` (needs network once).
