# G12 week 3 rotation — jssunil

**Status: plan; run NOT RUN. Checkpoint: open-source stand-in, as the lead answered (G12, 16 Nov 19:56).** Updated 16 November 2026.
R1: run the quantize-and-evaluate flow on **one checkpoint** (due Wed 18 Nov). R2: record the time and the cost
(due Thu 19 Nov). Both come from the G12 week 3 work order, §4. The flow on the dry run 1 checkpoint is core task 5
(Member B, D6), filed as theschoolofai/era-v5-lab#508; this rotation run does not duplicate it.

## 1. Which checkpoint (lead's answer, 16 Nov 19:56: "some open source model checkpoint", refer #18)

| Option | What it proves | Status |
|---|---|---|
| A. Labelled stand-in public model (not Qwen2.5-0.5B or 1.5B, already used in #13 / #18) | The flow runs end to end on trained weights; drift numbers for one architecture | **Chosen:** `ibm-granite/granite-3.0-1b-a400m-base`, pinned revision: a small MoE (router to check), Granite MoE family like our export target |
| B. Dry run 1 checkpoint (#475, p1536 tokenizer) | The V5 path itself | Not for rotation (task 5, #508) |

The result is labelled with the checkpoint actually used. A stand-in result is not presented as dry run 1 or
Gate 3 evidence.

## 2. Quality: four measures on the same checkpoint

A 1,221-step T2 model, or a small stand-in, scores near zero on exact-match benchmarks, so a benchmark delta of 0
says nothing. The run reports each quantized format's drift from bf16 first and the benchmark last.

| # | Measure | Tool | Why |
|---|---|---|---|
| 1 | KL divergence to bf16 (mean, median, 99th percentile, max), top-1 agreement (`same_top_p`), perplexity ratio | `quality/kl_eval.py` (llama.cpp `llama-perplexity`) | Compares the full next-token distribution on every scored token; the tail (p99, max) catches rare bad tokens that a mean hides |
| 2 | Output agreement on 100 fixed prompts: identical outputs, mean shared prefix | `scripts/flow_fixed_prompts.py` (theschoolofai/era-v5-lab#478) with the 100 fixed prompts the lead named: G10's `teams/10-post-training/eval/effort_manifest.json` (manifest sha256 `d6190b2d…9226`; pointers to rows of pinned upstream files, texts fetched by hash). #478's own `prompts/fixed_100.jsonl` (`da3f6851…4919`) only if the lead prefers it | The team's task 5 check (Sreekanth on #478, 15 Nov, and G12 chat, 16 Nov 16:48); fetching the texts needs the network, so do it before an offline run |
| 3 | Bits per byte on the same text as (1) | derived from (1): tokens scored × ln(PPL) ÷ ln 2 ÷ UTF-8 bytes of the scored text | Does not depend on the tokenizer, so it stays valid if GGUF and HF token IDs differ (Indic lines, #467) |
| 4 | MMLU / GSM8K exact match | `scripts/quantize_eval.py` (#14 path) | Reference only; expected near chance. Run locally where downloads are allowed, never in an offline TSAI job |

Text for (1) and (3): WikiText-2 test as pinned in `kl_eval.py` for a stand-in; for dry run 1, G3/G9 held-out text
with the p1536 tokenizer, if the lead approves its use.

**Basis:** Session 18: keep the router unquantised and compare formats on the same evaluation
[N `local:sessions/session_18_preference_alignment_and_inference_serving.md#0013`, `#0046`]. KL between the
full-precision and reduced-precision output distributions as a quantization error measure [P 2610.38277#0022].
Llama 3: benchmarks looked fine under FP8 while the model "occasionally produces corrupted responses"
[P 2407.21783#0136]. BPB is independent of the tokenizer
[N `local:sessions/session_16_scaling_laws_and_compute_planning.md#0003`]. An "acceptable" KL threshold:
**Basis: none in index**; this run reports numbers and proposes no threshold.

## 3. Checks before any number is read

| Check | Evidence kept | Result |
|---|---|---|
| Input identity | checkpoint, tokenizer, text and prompt-file sha256 | NOT RUN |
| Tokenizer | stand-in: its own tokenizer; dry run 1: p1536, sha256 `e6b93a93…a64b` (TSAI Gate 3 notice), **not** the C3 default `15468e66…` in #14 | NOT RUN |
| Export checks A1 / A3 (#14 path only) | reports, with pass/fail written here even when the process exits 0 | NOT RUN |
| Tokenizer round trip | exit code and mismatch counts. On p1536, exit 1 from 6 vocabulary tokens and one Cyrillic line is the known state (#467); anything beyond that is a failure | NOT RUN |
| Router and output tensor types | `gguf-dump` of every GGUF: the router must be F32 (the #14 guard also accepts Q8_0, which would break the Session 18 rule) | NOT RUN |

## 4. R1 results

| Format | Size | KL mean / p99 / max | Top-1 agree | PPL ratio | BPB | fixed_100 identical / shared prefix | Benchmark (ref.) |
|---|---|---|---|---|---|---|---|
| bf16 | NOT RUN | — | — | 1.000 | NOT RUN | — | NOT RUN |
| Q8_0 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| Q4_K_M | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |

## 5. R2: time and cost, measured per stage on the machine that ran it

TSAI keeps raw timing private, so R2 uses this run's own machine. Each stage is timed separately; set-up (clone,
build, downloads) is listed but kept out of the pipeline total.

| Stage | Seconds | Notes |
|---|---|---|
| Set-up: llama.cpp build, downloads | NOT RUN | not part of the pipeline total |
| Convert to bf16 GGUF | NOT RUN | |
| Quantize, per format | NOT RUN | fresh files only; a reused GGUF's `.quant_time` is the old value |
| KL pass, per format | NOT RUN | |
| fixed_100 run, per format | NOT RUN | also records decode tokens/s |
| Pipeline total (excluding set-up) | NOT RUN | |
| Peak memory and decode tokens/s, per format | NOT RUN | the numbers a serving choice uses |

**Cost:** on a local machine, "none (local)" with the machine named; on Modal, billed GPU-hours × the published
rate, with the rate and its date. No rate is assumed. Serving cost per million tokens = price per hour ÷
(tokens/s × 3,600) × 10⁶ [N `local:sessions/session_18_preference_alignment_and_inference_serving.md#0013`,
`#0045`]. Reporting time alone when there is no billed rate: **Basis: none in index** (team practice in #13).

## 6. Checklist

- [x] Read the work order, #13, #14, #18, #478 (and the lead's comment there), #508, G10's `effort_manifest.json` and the team's `kl_eval.py`.
- [x] Lead confirms the checkpoint: open-source model (16 Nov 19:56).
- [ ] Confirm llama.cpp converts the chosen model before the run.
- [ ] Pin inputs and hashes; run the checks in §3.
- [ ] Fill §4 and §5 from this run's own logs; attach a gist with the logs.
- [ ] Take the PR out of draft and link it in the G12 group.
