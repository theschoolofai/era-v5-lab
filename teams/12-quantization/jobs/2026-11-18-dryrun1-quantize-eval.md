# Dry run 1 checkpoint: quantize and score (Gate 3 evidence)

DRAFT. The lines marked TBD are filled in when Team 7's dry run 1 checkpoint arrives (due Wed 18 Nov).

```
Team:            12-quantization
Owner:           Rahul Bhati (therahulbhati)
Lead approval:   SreekanthZipsy
Question:        Does the G12 flow take the dry run 1 checkpoint to bf16, Q8_0 and Q4_K_M GGUF files and scores with no manual step, and how much does each format lose against bf16?
Script:          teams/12-quantization/scripts/quantize_eval.py   (with export_hf.py, check_gguf_logits.py, tokenizer/gguf_roundtrip.py)
Command:         python teams/12-quantization/scripts/quantize_eval.py --checkpoint inputs/dryrun1 --tokenizer inputs/tokenizer.json --tokenizer-sha256 e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b --formats bf16,Q8_0,Q4_K_M --roundtrip --work out/work --runs-csv out/runs.csv --scores-out out/scores.json --cleanup
Config:          none (every setting is on the command line)
Inputs:          dry run 1 checkpoint from Team 7 (TBD: path and sha256); frozen p1536 tokenizer.json (sha256 e6b93a93…, Kaggle sohiyiy/p1536-sample-v0, released 16 Nov in #504); llama.cpp b11669 binaries
Hardware:        1 GPU
Max time:        TBD (random 10M-parameter test: 6.5 min on an Apple M1, most of it package installs)
Precision:       bf16 (baseline), Q8_0 and Q4_K_M weights; router F32, output Q8_0
Measures:        A1 (export logits vs G5's model), A3 (llama.cpp vs G5), round-trip exit code, per format: size, bpw, router/output type, score, eval time, tok/s
Expected result: A1 and A3 PASS; round trip exit 1 or 2 (known limits of the GGUF tokenizer, #467); Q8_0 within noise of bf16, Q4_K_M within about 2 points
Outputs:         out/runs.csv, out/scores.json, out/work/*-roundtrip/*.md, out/work/*.json, logs (GGUF files deleted by --cleanup)
Test log:        teams/12-quantization/jobs/2026-11-15-flow-random-checkpoint.log (own machine, random G5 checkpoint, public BrahmicTokenizer-131K)
```

## Test run (15 Nov, Apple M1 8 GB, Metal, llama.cpp b11669)

Random G5 checkpoint from `scripts/make_random_checkpoint.py` (2 layers, width 64, 16 + 1 experts, 131,072 ids,
9.8M parameters), public BrahmicTokenizer-131K (`01d968a7…`), stand-in eval limited to 20 items. Exit 0.

| Step | Result |
|---|---|
| A1 export | max logit difference 1.67e-06, same top-1 on 4,096 of 4,096 positions: PASS |
| A3 llama.cpp vs G5 | same top-1 on 16 of 16 prompts, max log-probability difference 0.0076: PASS |
| Round trip | 0 lines with different ids; 16 single tokens wrong in the whole-vocabulary check: exit 1 |
| bf16 / Q8_0 / Q4_K_M | built, router F32 and output Q8_0 checked, scored (score 0: random weights) |

## Open before sending

1. **No network in a job (JOB_REQUEST.md rule 1).** The flow downloads at run time: the llama.cpp checkout, the
   converter venv (`uv pip install`), llama-cpp-python and `datasets` for the round trip, the held-out text for the
   round trip and the stand-in eval. Either TSAI's machine has these, or `inputs/` carries them (a prepared
   `--work` folder with `llama.cpp-b11669/`, `heldout/lines.json` and the eval file) and the flow gets an offline
   switch. To agree with TSAI.
2. **Eval set.** The flow scores its own items file (default: the 25 Oct stand-in). Decide whether to pass G9's
   eval-mini items with `--eval` instead, so the numbers can be compared with week 2.
3. **Checkpoint format.** The export reads G5's harness model. If dry run 1 is Team 7's bare `state_dict`, add
   `--spec` with `n_head`, `rope_theta`, `norm_eps` and `moe.top_k`.
