# Exotic heads and dictionaries, and export checks (G12 design tasks 5 and 6, 28 Nov 2026)

TSAI's questions, Lab 5 brief:
- **5.** A head that scores candidates built from bytes, or a very large dictionary: what must change in the exporter and runtime? What cannot be exported to a standard format and needs our own runtime?
- **6.** Which export check must pass and which is expected to fail, and why?

Everything below is read from `scripts/export_hf.py`, `docs/unsupported_parts.md` and the measured files named in each row.
Numbers from a random stand-in checkpoint say whether the wiring is right, not how good the model is; each row says which it is.

## 5. Exotic heads and dictionaries

### 5.1 Why a byte-built head exports at all

The KAS V2 head builds each token's output vector from its bytes (`head.W_out`, `head.beta`, `head.tok_u`, `head.tok_c`).
`export_hf.py` (`fold_kas_head`) evaluates it once for every id and writes a normal `lm_head.weight [V, d]`:

```
lm_head[v] = beta[L_v] * (positions_v @ W_out.T) + tok_u[v] @ tok_c        (float64, exact)
```

This is exact only because **the candidate set is the fixed vocabulary of V ids**, and each candidate's vector depends
on nothing but its id. The input side (KE2/KAS codes times the projection) folds the same way (`fold_kas_input`).
Runtime and file format see an ordinary untied head.

### 5.2 What changes in the exporter

| Part | Standard format can carry it? | What the exporter does |
|---|---|---|
| Input codes times projection | yes, folded to `embed_tokens [V, d]` | exact fold, runs the harness module itself |
| Head weights from bytes | yes, folded to `lm_head [V, d]` | exact fold |
| Head output bias `head.unigram` (one value per token) | **no**: `GraniteMoeShared` has no output bias; llama.cpp, Ollama and vLLM have none for `ernie4_5_moe` | export stops unless `--drop-head-bias`; the statistics and measured effect go to `export_report.json`. `--target ernie4_5_moe` carries it in `lm_head.bias` in transformers only |
| Router selection bias (`router_bias`, `bias_gamma`) | **no** on Granite; yes on ERNIE in transformers | stops unless all zero or `bias_gamma` is 0; `--drop-router-bias` exports anyway and records the largest bias |
| MTP head | no | dropped |
| Attention gate (attn-4) | no, in either runtime | export stops; needs new runtime code (`unsupported_parts.md` §10) |

### 5.3 What needs our own runtime

1. **Candidates not in a fixed table.** If a head scores arbitrary byte strings (an open candidate set built at run time),
   there is no `[V, d]` matrix to write. Both runtimes expect one `output.weight` / `lm_head`. This needs a custom
   architecture in llama.cpp and a custom model class in vLLM. Nothing in our current heads is like this.
2. **The unigram bias, exactly.** The bias is a per-token log prior added to every logit. Without it the exported model
   scores every token without its prior. An exact route is a patched llama.cpp and a vLLM model class (Shubham, #780);
   stock Ollama cannot run a patched llama.cpp. `granite_fold` approximates it inside stock Granite (below).
3. **The router selection bias exactly** is a patched runtime as well; ERNIE carries it in transformers only.

### 5.4 Measured cost of the drops (random stand-in in the shape of dry run 2, `ollama/smoke_standin.md`)

| Variant | Same top-1 as the checkpoint (Bengali / Punjabi) | Mean KL, nats |
|---|---|---|
| both biases dropped (`granite`) | 22.3% / 26.5% | 1.345 / 1.165 |
| `granite_fold` (constant-direction head fit plus a router logit shift) | 42.8% / 46.6% | 0.637 / 0.537 |

Stand-in weights are random with a std-1 unigram bias, so only the direction counts: the fold halves KL. The cost on
the real dry run 2 checkpoint needs its weights (job `dryrun2-1234`).

### 5.5 A very large dictionary

Folding turns a small trained part into two dense tables, so the dictionary size sets the exported size:

```
exported embed + head parameters = 2 * V * d_model
```

| Case | Trained parameters | Exported parameters | Embed + head share |
|---|---:|---:|---:|
| DR2 stand-in: V 131,072, d 512 | 176,398,881 | 299,966,976 | 134,217,728 = 44.7% |

The fold gives up the saving of the byte-built input and head. Memory at serve time grows linearly with V; doubling V
at d 512 adds 134,217,728 parameters. The tables quantize like any other tensor, but the output layer stays Q8_0 below
8 bits, and the embedding is then a separate measured choice (`--token-embedding-type`). Other effects of a large V:
the tokenizer's pre-tokenizer must be recognised by llama.cpp (a hash in `get_vocab_base_pre`, or the name written into
the GGUF), and a normalizer cannot live in a GGUF (below). Neither is solved by a bigger dictionary.

## 6. Export checks: which must pass, which is expected to fail

| Check | Command | Must pass? | Result and reason |
|---|---|---|---|
| A1 against G5 with router_bias zeroed | `export_hf.py --verify N` (second A1) | **must pass** | wiring of the rewrites (KAS fold, q/k reorder, shared-expert merge). Stand-in: max diff 2.1e-05 (limit 1e-3), top-1 same on 1,024/1,024 |
| A1 against G5 as trained | `export_hf.py --verify N` | **expected to fail** | Granite cannot route with the selection bias. Stand-in: max diff 6.3, top-1 same on 864/1,024. The size of the miss is the result, not a bug |
| A3 llama.cpp bf16 against G5 | `scripts/check_gguf_logits.py` | **must pass** | proves llama.cpp runs the architecture as exported. Limit 0.05 is not calibrated on a trained model. #780 smoke: 16/16 prompts, 0.017 |
| Router kept F32 in every GGUF | inspect tensors of each output file | **must pass** | a quantized router flips top-k choices |
| Tokenizer ids, text as it is | `tokenizer/gguf_roundtrip.py` | **expected to fail** | GGUF has no normalizer; p1536's NFC and replacements are not applied. `granite-embed-multi-97m`: 3,075 of 20,400 lines differ, 3,074 of them lines the normalizer changes |
| Tokenizer ids, text normalized first | same script, normalized pass | must pass | proves the rest of the pre-tokenizer matches; remaining diffs are 1 line and 6 vocabulary tokens (accented capitals) |
| EOS and EOT ids, specials | round trip: specials 356/356 | must pass | generation does not stop otherwise |
| Q8_0 and below against bf16 of the same export | wide pass, `eval_wide/paired.py` | measured, not pass or fail | the biases are dropped in every format, so the comparison is with bf16 of the same export |

Two rules for reading a failure:
- A1 against G5-as-trained and the raw tokenizer pass fail for a **known, named cause**. They stay in the table as
  expected failures with that cause; they must not be silenced by loosening a limit.
- A3 at `--std 0.05` looks the same for a correct and a broken export, because attention is nearly uniform. A clear
  FAIL is a wiring error; a near miss needs a look (`check_gguf_logits.py`, how to read it).

## Evidence and what is not measured

- `scripts/export_hf.py` (header, `fold_kas_head`), `docs/unsupported_parts.md` §8-12, `ollama/smoke_standin.md`,
  `results/gguf_roundtrip_p1536.md`, `jobs/2026-11-27-dryrun2-quantize-eval.md` (the numbers above come from these files).
- **Not measured:** the cost of the drops on the real dry run 2 weights; anything about a dictionary above V = 131,072
  (the size row is arithmetic, no model was exported); an exact patched-llama.cpp path (Shubham's, not mine).
