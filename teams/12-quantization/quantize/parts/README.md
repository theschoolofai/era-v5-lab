# Which parts stay at higher precision, and why (G12 design task 1, second question)

TSAI's task 1 asks, besides the size, memory, speed and quality per bit-width: *which parts stay at higher precision
(router, output layer, embeddings) and why?* Team 12's files keep the router (`ffn_gate_inp`) at F32 and the output
layer at Q8_0 (`scripts/quantize_eval.py`, `docs/bitwidth_proposal.md`). This folder measures what each part costs and
buys on a public MoE, OLMoE-1B-7B, and gives the sizes of the same variants on our dry run 2 shape.

**In one minute** (OLMoE-1B-7B, KL against the bf16 model at 4k context in llama.cpp b11669, six packs; the base mix is
Q4_K_M, the 4-bit format in Team 12's ladder)

- **Router: keep it at F32; it costs almost nothing, and at 4 bits it is the most sensitive part per byte.** It is 2.1M of OLMoE's
  6.9B parameters (8 MiB at F32, 0.2% of the Q4_K_M file). With only the router rounded to Q8_0 and everything else at
  bf16, KL is 0.00051, 70% of what quantizing every other weight to Q8_0 costs (0.00073); at Q4_0 it is 0.0056. Inside
  Team 12's Q4_K_M file a Q8_0 router is not measurable (0.01677 against 0.01674, s.e. 0.0002), but a Q4_0 router adds
  19% (0.0200): per MiB saved that is 8 times the KL of the next part (output Q8_0 to Q4_K). A Q8_0 router would save
  5.9 MiB.
- **The router changes which experts run.** In PyTorch (router computed in fp32), a Q8_0 router changes the set of 8
  experts for 3.1% of tokens in layer 0, where only the rounding acts, and for 6.6% over all layers; a changed set
  differs by one expert (1.01 on average). A Q4_0 router changes 37% in layer 0.
- **Attention: the largest cut of the one-part changes run here.** Attention at Q8_0 on top of Team 12's mix lowers KL
  from 0.0167 to 0.0107 (36% on average, 27 to 46% per pack, lower on all six packs) for +3% file size. On our dry run 2
  shape attention is 2.9 MiB at Q4_K_M, so the same change costs +2.4 MiB (+1.2%).
- **Output layer:** Team 12's Q8_0 output has 1.4% less KL than llama.cpp's default Q6_K (0.0167 against 0.0170), bf16
  no less than Q8_0 (0.0167), and Q4_K 17.5% more (0.0197). On our shape the output is the largest tensor (52.5 MiB at Q6_K,
  68 MiB at Q8_0), so Q8_0 instead of Q6_K costs 15.5 MiB, 7.5% of the file.
- **Embedding:** Q8_0 instead of Q4_K lowers KL by 6% (0.0157) for +1.2% on OLMoE; on our shape, where the 131,072-token
  table is 36 MiB at Q4_K, it would add 32 MiB (+16%).
- **Bits outside the experts buy more than bits inside them.** llama.cpp's Q4_K_M mix puts 8 of OLMoE's 16 expert
  down-projections at Q6_K (264 MiB more than Q4_K). Putting all experts at Q4_K and everything else at Q8_0
  (`experts-q4`) spends 193 MiB on the other parts, gives a file 71 MiB smaller (3,947 against 4,018 MiB) and 27% less
  KL (0.0124 against 0.0170). On our shape the same recipe is larger (237.8 against 190.0 MiB), because the embedding and
  output are 45% of our exported parameters (3% on OLMoE).

Team 12's proposal (`docs/bitwidth_proposal.md` v2) serves Q8_0, where attention, output and embedding are already Q8_0
and only the router question is left; the rest matters for a smaller file (Q6_K, Q4_K_M). From these numbers, for our
model I would keep the router at F32 (as now) and, in a file below 8 bits, attention at Q8_0 (cheap at our size), output
at Q8_0 (as now) or Q6_K, embedding and experts at the file's bit-width. These are proxy results: our own checkpoint is
not measured.

## How

- **Model:** OLMoE-1B-7B-0924 (`allenai/OLMoE-1B-7B-0924` @ 6d84c485): 16 layers, 64 experts with 8 active, untied
  embedding and output layer like ours; unlike ours it has no shared expert and no router selection bias. Converted to
  a bf16 GGUF with llama.cpp b11669's `convert_hf_to_gguf.py`.
- **Variants** (`parts_llamacpp.py quantize`, b11669's `llama-quantize`; the types of each part are in
  `results/kl_olmoe.json`, the per-tensor types in the quantize logs, which stay on the machine):

  | variant | what changes |
  |:--|:--|
  | `llama-default` | llama.cpp's own Q4_K_M mix (output Q6_K, 8 of 16 expert down-projections Q6_K) |
  | `g12` | Team 12's rule: output at Q8_0 (`--output-tensor-type q8_0`) |
  | `out-q4_K` / `out-bf16` | output at Q4_K / left at bf16 (only `output.weight` changes) |
  | `embd-q8_0` | `g12` + token embedding at Q8_0 (only `token_embd` changes) |
  | `attn-q8_0` | `g12` + the 64 attention q/k/v/output matrices at Q8_0 |
  | `experts-q4` | everything at Q8_0 except the 48 routed-expert tensors (`ffn_*_exps`) at Q4_K (several parts change) |
  | `pure-q4_K` | `--pure`: every quantizable matrix at Q4_K, output and embedding included |
  | `q8_0` | Q8_0, output Q8_0 |
  | `router-q8_0` / `router-q4_0` | the bf16 model with its 16 routers rounded to Q8_0 / Q4_0 values, stored as F32 |
  | `g12+router-q8_0` / `g12+router-q4_0` | `g12` with its routers rounded the same way |

- **The router.** The standard tools never write a quantized router: `tensor_allows_quantization` in
  `src/llama-quant.cpp` skips every name containing `ffn_gate_inp.weight` before any `--tensor-type` override, and
  `convert_hf_to_gguf.py` writes it as F32. `parts_llamacpp.py router` therefore clones a GGUF and overwrites each F32
  router in place with its values rounded to Q8_0 or Q4_0 blocks (bit-exact against gguf-py, including ties;
  `test_parts.py`), still stored as F32. llama.cpp then computes exactly the router a quantized one would give, scored
  like every other variant. `router_emul.py` adds what llama.cpp does not report: how many expert choices change.
- **Quality:** `llama-perplexity --kl-divergence` against the bf16 GGUF (`parts_llamacpp.py kl`), 4,096-token chunks
  (OLMoE's limit), 4 per pack, the second half of each chunk scored, six packs (English, Python, Hindi, Bengali, Tamil,
  Kannada) of the train split of the cleaned tokenizer sample v0; no benchmark item. Metal, Apple M6.

## 1 · The variants (OLMoE-1B-7B, llama.cpp b11669)

<!-- version: 0.7.0-dev (build 1, commit 620d222); n_ctx 4096; 4 chunks per pack -->
| variant | size MiB | output | embedding | attention | experts | mean KLD (s.e.) | same top-1 | worst pack |
|:--|--:|:--|:--|:--|:--|--:|--:|:--|
| llama-default | 4018.3 | Q6_K | Q4_K | Q4_K/Q6_K | Q4_K/Q6_K | 0.01697 (0.00020) | 94.18% | en-fineweb-edu |
| g12 | 4042.1 | Q8_0 | Q4_K | Q4_K/Q6_K | Q4_K/Q6_K | 0.01674 (0.00020) | 94.26% | en-fineweb-edu |
| out-q4_K | 3993.0 | Q4_K | Q4_K | Q4_K/Q6_K | Q4_K/Q6_K | 0.01967 (0.00020) | 93.47% | en-fineweb-edu |
| out-bf16 | 4134.2 | BF16 | Q4_K | Q4_K/Q6_K | Q4_K/Q6_K | 0.01672 (0.00020) | 94.26% | en-fineweb-edu |
| embd-q8_0 | 4091.2 | Q8_0 | Q8_0 | Q4_K/Q6_K | Q4_K/Q6_K | 0.01568 (0.00019) | 94.36% | en-fineweb-edu |
| attn-q8_0 | 4161.9 | Q8_0 | Q4_K | Q8_0 | Q4_K/Q6_K | 0.01069 (0.00014) | 95.52% | ind-hi-fw2 |
| experts-q4 | 3947.0 | Q8_0 | Q8_0 | Q8_0 | Q4_K | 0.01237 (0.00021) | 95.19% | ind-kn-fw2 |
| pure-q4_K | 3720.7 | Q4_K | Q4_K | Q4_K | Q4_K | 0.02475 (0.00027) | 92.79% | en-fineweb-edu |
| q8_0 | 7019.0 | Q8_0 | Q8_0 | Q8_0 | Q8_0 | 0.00073 (0.00001) | 98.82% | en-fineweb-edu |
| router-q8_0 | 13203.2 | BF16 | BF16 | BF16 | BF16 | 0.00051 (0.00001) | 99.08% | en-fineweb-edu |
| router-q4_0 | 13203.2 | BF16 | BF16 | BF16 | BF16 | 0.00561 (0.00006) | 96.70% | en-fineweb-edu |
| g12+router-q8_0 | 4042.1 | Q8_0 | Q4_K | Q4_K/Q6_K | Q4_K/Q6_K | 0.01677 (0.00021) | 94.21% | en-fineweb-edu |
| g12+router-q4_0 | 4042.1 | Q8_0 | Q4_K | Q4_K/Q6_K | Q4_K/Q6_K | 0.01995 (0.00023) | 93.69% | en-fineweb-edu |

The router variants keep F32 storage, so their size is the base file's.

Per pack: `attn-q8_0` is the lowest of the Q4_K-based variants on all six packs (27 to 46% below `g12`), `out-q4_K` the
highest of the one-part changes after `pure-q4_K` on all six (`g12+router-q4_0` is higher on four), `g12` below
`llama-default` on all six (0.8 to 2.8%), and `out-bf16` within 0.5% of `g12` (`results/kl_olmoe.json`).

## 2 · The router's expert choices (OLMoE-1B-7B, PyTorch on MPS)

The router weights rounded to the format and kept in fp32, the router computed in fp32 as llama.cpp computes its F32
router (the 8 chosen experts' mixing weights then go to bf16 for the bf16 expert layers, which does not change which
experts are chosen), every other weight at bf16; 24 windows of 1,024 tokens (4 per pack, six packs), all positions; k = 8.

| router weights | relative L2 error of the weights | same set of 8 experts, all layers | layer 0 only | experts changed per changed set | mean KL | same top-1 |
|:--|--:|--:|--:|--:|--:|--:|
| unchanged (control) | 0 | 100% | 100% | 0 | 0 | 100% |
| Q8_0 | 0.81% | 93.4% | 96.9% | 1.01 | 0.00106 | 98.4% |
| Q4_0 | 12.7% | 64.5% | 63.0% | 1.07 | 0.00584 | 96.3% |

The control runs in the same windows and is bit-identical, so every difference comes from the router weights. Layer 0's
input does not depend on any router, so its rate is the rounding's direct effect. Later layers add the effect of earlier
changes and their own router margins, which this run does not separate: at Q8_0 the share of changed sets rises from 3.1%
in layer 0 to 8 to 9% in layers 5 to 7 and is 6 to 8% after that; at Q4_0 it peaks at 44% in layer 5 and falls to 30 to
34% in layers 8 to 15, below layer 0's 37% (`same_topk_set_by_layer`). The
KL here is not on the same footing as section 1 (other windows, every position scored, another runtime); section 1's
`router-*` rows are the numbers to compare with the other parts.

## 3 · Our dry run 2 shape (sizes only, random weights)

The same variants built from the dry run 2 stand-in's bf16 GGUF (sha256 31aca821..., the file of #928's rows: the
stand-in in dry run 2's full shape, exported by `quantize_eval.py` with #862's run 1 settings; the command is in the
rerun below), MiB per part (`results/variants_t2_standin.json`):

| variant | file | output | embedding | attention | experts | shared expert | router |
|:--|--:|--:|--:|--:|--:|--:|--:|
| llama-default | 190.0 | 52.5 | 36.0 | 2.9 | 87.2 | 5.4 | 0.25 |
| g12 | 205.5 | 68.0 | 36.0 | 2.9 | 87.2 | 5.4 | 0.25 |
| out-q4_K | 173.5 | 36.0 | 36.0 | 2.9 | 87.2 | 5.4 | 0.25 |
| out-bf16 | 265.5 | 128.0 | 36.0 | 2.9 | 87.2 | 5.4 | 0.25 |
| embd-q8_0 | 237.5 | 68.0 | 68.0 | 2.9 | 87.2 | 5.4 | 0.25 |
| attn-q8_0 | 207.9 | 68.0 | 36.0 | 5.3 | 87.2 | 5.4 | 0.25 |
| experts-q4 | 237.8 | 68.0 | 68.0 | 5.3 | 81.0 | 9.6 | 0.25 |
| pure-q4_K | 166.8 | 36.0 | 36.0 | 2.8 | 81.0 | 5.1 | 0.25 |
| q8_0 | 309.8 | 68.0 | 68.0 | 5.3 | 153.0 | 9.6 | 0.25 |

## Not measured

- Our own checkpoint: quality per part is on OLMoE as a proxy. Our model has a 131,072-token vocabulary (embedding and
  output are 45% of its exported parameters, against 3% on OLMoE), 16 experts with a shared one, and a router selection
  bias, so the sizes in section 3 are ours but the quality numbers are not.
- Task scores (benchmarks run only under the eval firewall): next-token KL only.
- Other base mixes than Q4_K_M and Q8_0, and upgrading the experts alone inside the Q4_K_M mix (outside it, from
  `experts-q4` to `q8_0` all of the change is in the experts: KL 0.0124 to 0.0007 for 3,072 MiB).
- Whether the near-tied experts that swap carry small gate weights (the small KL suggests so, but it is not measured).

## Files and rerun

| file | what |
|:--|:--|
| [`parts_llamacpp.py`](parts_llamacpp.py) | `quantize` (the variants), `router` (router variants), `kl` (KL against bf16 per pack), `table` |
| [`router_emul.py`](router_emul.py) | the router in Q8_0 / Q4_0 in PyTorch (fp32): expert choices, KL, top-1, NLL |
| [`test_parts.py`](test_parts.py) | part names, the variants' flags and regexes against real tensor names, the KL log parser, the Q8_0 / Q4_0 rounding against gguf-py (ties included), the router metrics, the fp32 router, the in-place router rewrite |
| `results/` | numbers only |

<details>
<summary><b>Rerun</b></summary>
<br>

With `B` = llama.cpp b11669's `bin` folder (`llama-quantize`, `llama-perplexity`), `M` = OLMoE-1B-7B-0924 @ 6d84c485
converted to bf16 with the same build, `<texts>` from `kv_llamacpp.py text` (`serving/kv_cache/llamacpp/`, #910), and
Python with gguf-py and torch (transformers 5.x for `router_emul.py`):

```
python parts_llamacpp.py quantize --bin $B --bf16 $M --work <work>
python parts_llamacpp.py router --work <work> --from bf16=$M g12=<work>/<name>-g12.gguf
python parts_llamacpp.py kl --bin $B --bf16 $M --work <work> --texts <texts> --ctx 4096 --chunks 4 --out results/kl_olmoe.json
python parts_llamacpp.py table results/kl_olmoe.json
python parts_llamacpp.py quantize --bin $B --bf16 <stand-in bf16 GGUF> --work <work2>   # -> variants.json, copied to
#   results/variants_t2_standin.json; the stand-in: make_random_checkpoint.py --d-model 512 --n-layer 8 --n-head 8
#   --n-kv-head 2 --d-ff 768 --n-expert 16 --n-shared 1 --top-k 2 --seq-len 2048 --pos-dim 32 --std 0.05
#   --head-mode kas_v2 --bias-gamma 0.001 --router-bias-std 0.01, then quantize_eval.py --drop-router-bias --drop-head-bias
python router_emul.py --model allenai/OLMoE-1B-7B-0924 --revision 6d84c48581ece794365f2b8e9cfb043c68ade9c5 --local <folder> \
    --texts <texts> --windows 4 --tokens 1024 --formats q8_0 q4_0 none --out results/router_olmoe.json
python -m pytest test_parts.py -q
```
</details>
