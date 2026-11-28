# Lead addition 8: missing kinds of data, v1

Sourav Dhar · GitHub: sourav-dhar · Team 1 (Data A)

The brief's lead addition 8: "Long documents (for long context), reasoning traces, tool-call and function-call data,
code with execution results. Say which exist, their licences and sizes." The team doc adds a question: "Need a Data
Type classifier? Then we run that on all the packs?" This note answers both, from two sources:
- **the 38 sample packs**, measured here: document lengths in frozen p1536 tokens (`tools/doc_lengths.py`) and
  markers of the other kinds (`tools/kind_markers.py`);
- **sources outside them**, pinned at a Hub revision with licence, size and generator: from the survey for Team 10 in
  #914 (`post_training/data_request_reply_v1.md`, §3 and §4), from Team 10's licence table where #914 does not have the
  cell (said so in each table), and pre-training corpora read from their cards here.

Licence rule (TSAI, 28 Nov): NC, ND and unstated licences are allowed; the licence, its source and, for model-made
data, the generator and its licence are recorded. Team 10's generator rule (no text from closed or Llama models) is
noted where it bites; it is Team 10's and TSAI's call.

## Summary

| Kind | In the 38 packs | Outside them (examples, all pinned below) | Classifier needed? |
|---|---|---|---|
| Long documents | 14,329 of 1,444,766 documents (1.0%) have 8,192 p1536 tokens or more, holding 232.5 M of 1,262.8 M tokens; 628 have 32k or more, 71 have 128k or more | FinePDFs (ODC-By; English 206.9 M documents, 1.19 T tokens by its card), peS2o (ODC-BY; 8.29 M full-text papers), PG-19 (books; Apache-2.0); for SFT, about 1.1 M OpenThoughts3 rows in 8k-32k (#914 §4) | No: length is a token count |
| Reasoning traces | no marker found: 0 documents with `<think>` or `<\|im_start\|>` (the packs are web, code, math, PDF, model-rephrased English and Indic text) | OpenCodeReasoning-2 (2,572,641 rows), OpenThoughts3 (1.2 M), Nemotron-SFT-Math-v4 (545,431), Nemotron-Pretraining-SFT-v1 (gated; about 160 B tokens written by DeepSeek-R1 and R1-0528, among other generators) | No: these come as their own datasets |
| Tool and function calls | no marker found: 0 documents with `<tool_call>` or `"tool_calls"`; 4 code files mention `"function_call"` (API client code) | Nemotron-Agentic-v1 `tool_calling` (316,094), Nemotron-SFT-Agentic-v2 `tool_calling` (707,052), xlam-function-calling-60k (gated) | No |
| Code with execution results | 698 documents carry some execution output: 187 notebooks with cell outputs (`<jupyter_output>`, cadj-notebooks), 207 with IPython `Out[n]:` and 315 with a Python traceback, mostly pasted into cadj-stackexchange (349 documents) and code-python (63); few and untagged | OpenCodeInstruct (5,000,000 rows, each with its unit tests, a pass / fail per test and the average score), OpenCodeReasoning-2 (pass rate per row), SWE and terminal agent trajectories (#914) | No |

So the four kinds exist, in large amounts, outside the packs; inside the packs only long documents are there in any
number. The marker scan finds almost nothing of the other three in the packs, so a document-type classifier over the
packs looks unlikely to pay for D8 (an inference: no classifier was run). Classifying documents is D5's question
(quality).

## 1. Long documents

**In the 38 packs** (every part, held-out too; p1536 tokens per document, `add_special_tokens=False`):

| Pack | Documents | ≥ 8,192 tokens: docs (tokens) | ≥ 32,768 | ≥ 131,072 | Longest |
|---|---:|---:|---:|---:|---:|
| code-cpp | 56,158 | 2,167 (30.5 M) | 39 | 0 | 69,557 |
| code-go | 84,139 | 1,574 (23.3 M) | 39 | 0 | 63,530 |
| code-rust | 60,738 | 1,500 (19.3 M) | 7 | 0 | 40,362 |
| code-python | 75,661 | 1,078 (13.7 M) | 6 | 0 | 54,775 |
| en-dclm | 61,975 | 983 (15.0 M) | 49 | 0 | 113,314 |
| sci-finepdfs | 6,074 | 889 (32.4 M) | 181 | 42 | 1,122,845 |
| code-java | 86,060 | 875 (11.3 M) | 3 | 0 | 39,407 |
| code-js-ts | 123,172 | 860 (11.8 M) | 12 | 0 | 42,590 |
| math-megamath | 17,816 | 786 (17.3 M) | 70 | 17 | 518,495 |
| en-fineweb-edu | 72,665 | 621 (9.1 M) | 28 | 0 | 94,366 |
| en-nemotroncc | 92,774 | 612 (10.3 M) | 46 | 1 | 131,844 |
| math-finemath | 29,434 | 527 (8.4 M) | 25 | 3 | 277,236 |
| cadj-notebooks | 15,732 | 495 (6.3 M) | 9 | 0 | 102,360 |
| ind-sa-fw2 | 5,963 | 307 (8.2 M) | 64 | 7 | 160,009 |
| ind-hi-sangraha-s | 8,368 | 203 (3.2 M) | 12 | 0 | 119,594 |
| ind-hi-hplt | 8,840 | 116 (1.9 M) | 5 | 0 | 103,542 |
| 22 other packs (Indic, cadj-stackexchange, cadj-commits, en-nemotroncc-synth) | 639,197 | 736 (10.7 M) | 33 | 1 | 192,313 |
| **all 38** | 1,444,766 | 14,329 (232.5 M) | 628 (49.3 M) | 71 (18.0 M) | 1,122,845 |

These are the raw packs, before cleaning, dedup and F2 (sample v0: 1,444,766 documents, 1,262,827,283 p1536
tokens). Documents of 8,192 tokens or more are 1.0% of the documents and
18.4% of the tokens. By count they are mostly code; the longest are PDFs
(`sci-finepdfs`: 889 of its 6,074 documents are 8k or longer, 42 are 128k or longer) and math
(`math-megamath`). Only `cadj-commits` has none. Per pack and split: `jobs/logs/2026-11-28-d8-doc-lengths/doc_lengths_38packs.json`.

**Outside the packs** (pre-training; read from the cards, not tokenized here):

| Source @revision | Licence | Size (from the card) | What it is |
|---|---|---|---|
| `HuggingFaceFW/finepdfs` @220bac3a | ODC-By 1.0 | about 3 T tokens, 475 M documents, 1,733 language-script pairs; English (`eng_Latn`) 206,917,556 documents, 1,190.65 B tokens, 1.71 TB | text extracted from PDFs; the source of our `sci-finepdfs` pack |
| `allenai/peS2o` @636a503e | ODC-BY | v2: 38.97 M documents, 42.01 B whitespace-separated words; of them 8,293,485 full-text papers (`s2orc`, 36.34 B words) and 30.68 M titles and abstracts (`s2ag`) | open-access academic papers; only the `s2orc` part is long |
| `deepmind/pg19` @4d28bd77 | Apache-2.0 (Hub tag and card) | 11.51 GB | books from Project Gutenberg published before 1919; the repository holds a loading script and three small text files, so the books are fetched from elsewhere (not checked here) |

**For SFT** (Team 10's long-context row, measured on samples in #914 §4): rows of 8,192 to 32,768 p1536 tokens after
F2, estimated: OpenThoughts3 about 1.14 M, OpenCodeReasoning-2 about 1.02 M, Nemotron-SFT-OpenCode about 349 k,
Nemotron-Terminal about 304 k, SWE-Zero about 225 k.

## 2. Reasoning traces

Rows, licence and generator: OpenCodeReasoning-2 and OpenThoughts3 from #914 §3; Nemotron-SFT-Math-v4's rows from
#914 §1.3 and the rest of its row, and OpenMathReasoning's, from Team 10's licence table; OpenMathReasoning's row count
from the dataset viewer (its `cot` split).

| Source @revision | Rows | Licence | Generator | Team 10 decision |
|---|---:|---|---|---|
| `nvidia/OpenCodeReasoning-2` @eadf5359 | 2,572,641 | cc-by-4.0 | DeepSeek-R1 (MIT), QwQ-32B (Apache-2.0) | allowed (TSAI 11 Nov); question text must be rebuilt (#565) |
| `open-thoughts/OpenThoughts3-1.2M` @61bcf9d4 | 1,200,000 | apache-2.0 | QwQ-32B (Apache-2.0) | TSAI reserves |
| `nvidia/Nemotron-SFT-Math-v4` @84d42ad0 | 545,431 | cc-by-4.0 (AoPS) / cc-by-sa-4.0 (Math StackExchange) | DeepSeek-V4-Pro (MIT) | allowed |
| `nvidia/OpenMathReasoning` @d3d08664 | 3,201,061 (CoT split) | cc-by-4.0 | DeepSeek-R1 (MIT), QwQ-32B (Apache-2.0) | TSAI reserves |

At pre-training scale: `nvidia/Nemotron-Pretraining-SFT-v1` @3f1a5b88 (gated, manual approval; licence "other":
NVIDIA's data agreement, "for model training purposes ONLY"). Its card lists this set's generators by tokens, led by
DeepSeek-R1-0528 (100.8 B) and DeepSeek-R1 (59.8 B), with Qwen models, and also Mixtral-8x22B (17.6 B) and Nemotron
340B (about 4 B); it does not say how much of the R1 text is reasoning traces. The card also says a model trained on it
may be subject to the Qwen and DeepSeek licence terms. The card's category table is for NVIDIA's whole pre-training collection (6,585.8 B tokens), whose
SFT-style parts are Math SFT 190.6 B, Code SFT 58.5 B and General SFT 87.5 B tokens. The Nemotron 340B part would need
Team 10's generator check; the set is not in Team 10's licence table yet.

## 3. Tool and function calls

| Source @revision | Rows | Licence | Generator (Team 10 table) | Team 10 decision |
|---|---:|---|---|---|
| `nvidia/Nemotron-Agentic-v1` `tool_calling` @650d5909 | 316,094 (card) | cc-by-4.0 | Qwen3-235B-A22B, Qwen3-32B (Apache-2.0), gpt-oss-120b | TSAI reserves |
| `nvidia/Nemotron-SFT-Agentic-v2` `tool_calling` @7c804833 | 707,052 (card) | cc-by-4.0, apache-2.0, mit | DeepSeek-V3.2 (MIT), GLM-4.6 (MIT) | TSAI reserves |
| `Salesforce/xlam-function-calling-60k` @26d14ebf | 60,000 (name; not sampled) | cc-by-4.0 | Mixtral-8x22B-Instruct (Apache-2.0) and DeepSeek-V2-Chat (DeepSeek licence; Team 10's table: keep only the Mixtral rows if they can be split), via APIGen | TSAI reserves; gated: our Hub account must accept its terms first |

In the samples of #914, 87% (Agentic-v1) and 95% (Agentic-v2) of the rows carry tool calls.

## 4. Code with execution results

- **In the packs** (`tools/kind_markers.py`): 698 of the 1,444,766 documents carry a marker of execution output.
  `cadj-notebooks` (from `HuggingFaceTB/issues-kaggle-notebooks`) keeps cell outputs (`<jupyter_output>`) in 187 of
  its 15,732 documents (1.2%); the rest of it is code and text without results. Elsewhere the output is pasted by
  hand: IPython `Out[n]:` in 207 documents and Python tracebacks in 315, mostly in `cadj-stackexchange` (349
  documents with either), `code-python` (63), `math-megamath` (36) and `math-finemath` (29). A marker can also sit
  inside code (for example a traceback string in a test), so these are upper bounds.
- **`nvidia/OpenCodeInstruct` @8f3ba5ba** (5,000,000 rows, parquet footers; cc-by-4.0; Qwen2.5-32B-Instruct and
  Qwen2.5-Coder-32B-Instruct, Apache-2.0; TSAI reserves): every row has `unit_tests`, `tests_execution_status` (pass or
  fail per test) and `average_test_score`. In the first 2,000 rows, 954 (47.7%) score 1.0 and 253 (12.7%) score 0.
- **`nvidia/OpenCodeReasoning-2`** has a pass rate per row; **SWE and terminal trajectories** (SWE-Zero, SWE-rebench-
  openhands, Nemotron-Terminal-Corpus, in #914) hold the tool outputs of commands and test runs inside each trajectory.
- For RL, Team 10's own code pool (`deepmind/code_contests`, #564: 3,251 train and 255 held-out tasks with tests).

## How to reproduce

```bash
python -I teams/01-data-a/tools/doc_lengths.py <38 packs root> <p1536 tokenizer.json> <out.json>
```

```bash
python -I teams/01-data-a/tools/kind_markers.py <38 packs root>
```

Both outputs are in `jobs/logs/2026-11-28-d8-doc-lengths/`. The OpenCodeInstruct figures read the first row group of
`data/train-00000-of-00050.parquet` at the pinned revision. Everything in §2 and
§3 and the SFT rows of §1 come from #914 and its commands.

## Not measured

- Lengths of FinePDFs, peS2o and PG-19 documents in p1536 tokens (their sizes above are the cards').
- F2 on any of the outside sources beyond the #914 samples.
- The licence terms of `Nemotron-Pretraining-SFT-v1`'s agreement beyond the card's summary.
