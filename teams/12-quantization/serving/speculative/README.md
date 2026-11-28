# Speculative decoding on a laptop (G12 lead item 8, with Team 6)

Lead item 8: *a draft head or small draft model for faster generation*. Team 6's lead item 7 asks for the same with a
multi-token-prediction (MTP) head. Dry run 2 was trained without one (`teams/05-architecture/configs/arms/t2.yaml`:
`mtp: false`), so this folder measures what a laptop gets today from the two kinds of speculation llama.cpp b11669 can
run without changing the model: a **small draft model** of the same family, and **n-gram drafting** from the text
already in the context. The memory part of lead item 8 (8k, 32k and 128k context) is in
[`../kv_cache/llamacpp/`](../kv_cache/llamacpp/README.md).

**In one minute** (Apple M6 32 GB, llama.cpp b11669 llama-server, Metal, greedy, 30 prompts)

- **On Llama-3.1-8B at Q8_0, a 1B draft makes generation 2.3 times faster.** It generates 18.2 tokens per second alone
  and 42.6 with Llama-3.2-1B-Instruct at Q4_0 drafting 8 tokens at a time (59% of drafted tokens accepted): 2.78× on code
  edits, 2.75× on reasoning answers, 1.68× on chat. Counting prompt time too, it is 17.7 against 39.3 tokens per second
  (2.22×).
- **The gain shrinks as the target gets cheaper.** On the same 8B at Q4_K_M (27.7 tokens per second alone) the best
  draft gives 1.22×, and on Llama-3.2-3B at Q8_0 (42.0 alone) 1.43×. On chat prompts a draft can make it slower (0.76 to
  0.87× with 8-token drafts, 0.53× with 16). Drafting 16 tokens at a time is slower than the 3B alone (0.82×); 4 beats 8 there (1.20× against 1.14×).
- **Which draft is best depends on the target.** The Q4_0 draft beats the Q8_0 draft on the 8B Q8_0 (2.34× against
  2.03×) and on the 3B (1.43× against 1.14×), but not on the 8B Q4_K_M (1.09× against 1.22×), although its acceptance is
  similar everywhere (58 to 59% against 63%). The time a draft step takes was not measured, so the cause is not shown here.
- **A draft costs 1.1 GiB (Q4_0) or 1.6 GiB (Q8_0) at 8k context**, the same on every target (its weights, its own
  cache and compute buffers), so the 8B at Q8_0 with the Q4_0 draft needs 10.2 GiB in all, and the 8B at Q4_K_M with it
  6.8 GiB.
- **N-gram drafting needs no second model and helps where the answer copies the prompt.** `ngram-simple` gives 1.67×
  on code edits on the 3B and changes nothing on chat or reasoning (0.99 to 1.00×); `ngram-mod` gives 1.34 to 1.37× on
  code edits.
- **Greedy outputs mostly match the target alone, but not always.** Speculative decoding should return the target's own
  greedy text. Here 30 of 30 matched for the 8B Q8_0 in every mode and 29 or 30 of 30 for the 3B (one code edit in three
  modes, one of them the draft-free `ngram-mod`), but 24 of 30 for the 8B Q4_K_M with either draft. I think the
  verification step, which runs several tokens at once with other kernels than one-token decoding, flips near-tied
  tokens; that is not checked, and run-to-run variation of the target alone is not ruled out either (no repeat of the
  base run was made; only hashes of the outputs are kept).

## Setup

- llama.cpp b11669 (commit 620d222) `llama-server`, Metal, Apple M6 32 GB; one request at a time (`-np 1`), greedy
  (temperature 0, seed 0), up to 192 generated tokens, prompt cache off, flash attention on, 8,192-token context.
- Targets: Llama-3.2-3B-Instruct (`unsloth/Llama-3.2-3B-Instruct` @ 006f5dcd) and Llama-3.1-8B-Instruct
  (`unsloth/Llama-3.1-8B-Instruct` @ 4699cc75); draft: Llama-3.2-1B-Instruct (`unsloth/Llama-3.2-1B-Instruct` @
  5a8abab4), all the same tokenizer. The revisions are those in each download's Hugging Face metadata; converted with
  b11669's `convert_hf_to_gguf.py` and quantized with b11669's `llama-quantize` (sha256 of every GGUF in the results).
- Prompts (30): the first 10 chat and 10 reason rows of Team 12's `serving/prompts_v1.jsonl`, and 10 code-edit rows
  ("add a docstring to every function, return the whole code"; 760 to 2,097 characters of code) whose code is from the
  train split of the cleaned
  tokenizer sample v0 (`spec_bench.py make-prompts --per-category 10`, sha256 88dc8c33...). The code text stays on the
  machine; the results hold numbers only.
- Speed: the server reports `predicted_per_second` per prompt (generation only; it times the tokens after the first);
  per mode and category, total tokens / the sum of tokens / `predicted_per_second`. `wall_s` (with prompt time) is
  also recorded.
  Acceptance is `draft_n_accepted / draft_n`. Greedy speculative decoding must return the target's own text, so every
  mode's output is compared with the baseline's, prompt by prompt.

## 1 · Speed per target and mode

Tokens per second over all generated tokens (speed-up against the target alone in brackets), by prompt category;
acceptance is draft tokens accepted over draft tokens proposed.

**3B** (llama-3.2-3b-instruct-Q8_0.gguf), 30 prompts, up to 192 tokens each:

| mode | all prompts | chat | code_edit | reason | acceptance | same text as alone |
|:--|--:|--:|--:|--:|--:|--:|
| base | 42.0 | 42.2 | 41.8 | 42.5 |  |  |
| draft llama-3.2-1b-instruct-Q4_0 n8 | 60.2 (1.43×) | 45.3 (1.07×) | 69.3 (1.66×) | 71.4 (1.68×) | 58% | 30/30 |
| draft llama-3.2-1b-instruct-Q8_0 n16 | 34.6 (0.82×) | 22.3 (0.53×) | 46.3 (1.11×) | 41.8 (0.98×) | 45% | 29/30 |
| draft llama-3.2-1b-instruct-Q8_0 n4 | 50.6 (1.20×) | 42.9 (1.02×) | 55.2 (1.32×) | 53.2 (1.25×) | 77% | 29/30 |
| draft llama-3.2-1b-instruct-Q8_0 n8 | 48.0 (1.14×) | 36.6 (0.87×) | 56.1 (1.34×) | 53.3 (1.25×) | 63% | 30/30 |
| ngram:ngram-mod | 48.7 (1.16×) | 41.9 (0.99×) | 57.4 (1.37×) | 42.1 (0.99×) | 53% | 29/30 |
| ngram:ngram-simple | 53.0 (1.26×) | 42.1 (1.00×) | 70.0 (1.67×) | 42.3 (0.99×) | 62% | 30/30 |

**8B Q8_0** (llama-3.1-8b-instruct-Q8_0.gguf), 30 prompts, up to 192 tokens each:

| mode | all prompts | chat | code_edit | reason | acceptance | same text as alone |
|:--|--:|--:|--:|--:|--:|--:|
| base | 18.2 | 18.4 | 18.0 | 18.4 |  |  |
| draft llama-3.2-1b-instruct-Q4_0 n8 | 42.6 (2.34×) | 31.0 (1.68×) | 50.0 (2.78×) | 50.7 (2.75×) | 59% | 30/30 |
| draft llama-3.2-1b-instruct-Q8_0 n8 | 37.0 (2.03×) | 27.4 (1.49×) | 43.3 (2.41×) | 42.8 (2.32×) | 63% | 30/30 |
| ngram:ngram-mod | 20.4 (1.12×) | 17.6 (0.96×) | 24.1 (1.34×) | 18.0 (0.98×) | 48% | 30/30 |

**8B Q4_K_M** (llama-3.1-8b-instruct-Q4_K_M.gguf), 30 prompts, up to 192 tokens each:

| mode | all prompts | chat | code_edit | reason | acceptance | same text as alone |
|:--|--:|--:|--:|--:|--:|--:|
| base | 27.7 | 29.6 | 26.3 | 29.1 |  |  |
| draft llama-3.2-1b-instruct-Q4_0 n8 | 30.1 (1.09×) | 22.5 (0.76×) | 34.3 (1.31×) | 38.2 (1.31×) | 58% | 24/30 |
| draft llama-3.2-1b-instruct-Q8_0 n8 | 33.8 (1.22×) | 25.5 (0.86×) | 38.5 (1.47×) | 42.3 (1.45×) | 63% | 24/30 |

## 2 · Memory

llama.cpp's buffers at 8,192-token context, MiB (weights are memory-mapped from the GGUF; KV and compute are allocated):

| target | mode | weights (GGUF sizes) | KV cache | compute | total | added by the draft |
|:--|:--|--:|--:|--:|--:|--:|
| 3b | base | 3,263 | 896 | 116 | 4,276 |  |
| 3b | draft llama-3.2-1b-instruct-Q8_0 n8 | 4,523 | 1,152 | 212 | 5,888 | 1,612 |
| 3b | draft llama-3.2-1b-instruct-Q4_0 n8 | 3,999 | 1,152 | 212 | 5,363 | 1,087 |
| 8b-Q8_0 | base | 8,145 | 1,024 | 164 | 9,333 |  |
| 8b-Q8_0 | draft llama-3.2-1b-instruct-Q8_0 n8 | 9,405 | 1,280 | 260 | 10,945 | 1,612 |
| 8b-Q8_0 | draft llama-3.2-1b-instruct-Q4_0 n8 | 8,880 | 1,280 | 260 | 10,420 | 1,087 |
| 8b-Q4_K_M | base | 4,693 | 1,024 | 164 | 5,881 |  |
| 8b-Q4_K_M | draft llama-3.2-1b-instruct-Q8_0 n8 | 5,953 | 1,280 | 260 | 7,493 | 1,612 |
| 8b-Q4_K_M | draft llama-3.2-1b-instruct-Q4_0 n8 | 5,428 | 1,280 | 260 | 6,968 | 1,087 |

- Weights are each GGUF's size: llama.cpp maps them from the file, and maps a tied embedding twice (`CPU_Mapped` for the
  lookup, and again inside the Metal range for the output), so summing its model buffers would count it twice. KV and
  compute are llama.cpp's own report at `-lv 4` (`spec_bench.py memory`).
- A draft adds the same memory to every target: 1,087 MiB for the 1B at Q4_0 and 1,612 MiB at Q8_0, its weights plus its
  own 8,192-token cache (256 MiB) and compute buffers (96 MiB).
- The 16 GB rows of #904's table measure what fits a 16 GB Mac; at 6.8 GiB the 8B Q4_K_M with the Q4_0 draft is a
  candidate to try there.

## What an MTP test on our model would need

Team 6's lead item 7 asks for speculative decoding with a multi-token-prediction head. For our model that needs:

1. **A checkpoint trained with `mtp: true`.** Dry run 2 has none (`teams/05-architecture/configs/arms/t2.yaml` and the
   run record in #869: `mtp: false`).
2. **A runtime that can use the head.** Team 5's MTP head is one extra `Linear(n_embd, vocab)` on the last hidden state,
   trained on token t+2 (`harness/week2/model.py:319`). llama.cpp b11669's `--spec-type draft-mtp` reads DeepSeek-style
   "nextn" layers (a whole extra transformer block), and neither of our export routes has them: `src/models/ernie4-5-moe.cpp`
   and the Granite MoE graph (`src/models/granite-moe.cpp`, and `granite.cpp`, which it builds on) have no nextn
   code; 28 other model files do. So a t+2 head would need a
   small runtime change, or a first test in PyTorch: how often the head's t+2 guess equals the model's own next-but-one
   greedy token, which bounds the speed-up before any runtime work.
3. Until then, a small draft model of the same tokenizer (section 1) or n-gram drafting are what a laptop can use with
   stock llama.cpp. For our model a draft would need the same p1536 tokenizer, so it would be a smaller model of our own.

## Not measured

- Our own model: there is no draft model with our tokenizer, and no MTP head (above).
- Sampling at temperature above 0, batches above 1, long prompts (the code edits are 760 to 2,097 characters of
  code), and the time a draft step takes.
- Why some outputs differ from the target alone (only hashes of the outputs are kept).
- The 16 GB and 64 GB Macs: these are one 32 GB machine's numbers.
- A repeat of the base runs (run-to-run variation of the target alone).

## Files and rerun

| file | what |
|:--|:--|
| [`spec_bench.py`](spec_bench.py) | `make-prompts`, `run` (one llama-server per target and mode), `memory` (llama.cpp's buffer report per target and mode) and `report` |
| [`test_spec_bench.py`](test_spec_bench.py) | server arguments per mode, the summary arithmetic, the report table, the buffer parser (CPU) |
| `results/` | numbers only: per prompt tokens, speed, draft counts and the sha256 of the output text |

<details>
<summary><b>Rerun</b></summary>
<br>

With `B` = llama.cpp b11669's `bin` folder (`llama-server`), the models from the `unsloth` mirrors at the revisions in
the results files, converted with b11669's `convert_hf_to_gguf.py` and quantized with b11669's `llama-quantize`
(sha256 of every GGUF in the results files), and `D8` / `D4` = the 1B draft at Q8_0 / Q4_0:

```
python spec_bench.py make-prompts --base ../prompts_v1.jsonl --data <tokenizer_sample_v0_clean> --code 20 \
    --per-category 10 --out prompts.jsonl                      # sha256 88dc8c33... for the set used here
python spec_bench.py run --bin $B --target 3b=<3B Q8_0> --prompts prompts.jsonl --n-predict 192 --out results/spec_3b.json \
    --modes base draft:$D8:8 draft:$D8:4 draft:$D8:16 draft:$D4:8 ngram:ngram-mod ngram:ngram-simple
python spec_bench.py run --bin $B --target 8b-Q8_0=<8B Q8_0> --prompts prompts.jsonl --n-predict 192 \
    --modes base draft:$D8:8 draft:$D4:8 ngram:ngram-mod --out results/spec_8b_q8.json
python spec_bench.py run --bin $B --target 8b-Q4_K_M=<8B Q4_K_M> --prompts prompts.jsonl --n-predict 192 \
    --modes base draft:$D8:8 draft:$D4:8 --out results/spec_8b_q4km.json
python spec_bench.py memory --bin $B --target 3b=<3B Q8_0> 8b-Q8_0=<8B Q8_0> 8b-Q4_K_M=<8B Q4_K_M> \
    --modes base draft:$D8:8 draft:$D4:8 --out results/spec_memory.json
python spec_bench.py report results/spec_*.json
python -m pytest test_spec_bench.py -q
```

Speed runs need a quiet machine.
</details>
