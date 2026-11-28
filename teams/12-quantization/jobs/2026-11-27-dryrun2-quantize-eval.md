# Dry run 2 checkpoint: quantize, score and 100 fixed prompts (Gate 4 evidence)

REQUEST FOR TSAI REVIEW. No approval and no run result is claimed. The authors are the G12 owners below. SreekanthZipsy, the lead, asked for this request (G12 channel, 27 Nov); TSAI runs it.

```text
Team:            12-quantization
Owner:           therahulbhati, s9k96
Lead approval:   SreekanthZipsy
Question:        Does the G12 flow take the dry run 2 checkpoint (KAS V2 head, loss-free router bias) to bf16, Q8_0, Q6_K, Q5_K_M and Q4_K_M GGUF files with no manual step, is the export wired exactly once the two biases Granite cannot hold are set aside, and how far does each format move from bf16 in score and on 100 fixed prompts?
Script:          teams/12-quantization/scripts/run_flow.py (it runs quantize_eval.py, then flow_fixed_prompts.py), with export_hf.py, check_gguf_logits.py, tokenizer/convert_frozen.py and Team 10's eval/effort_suite.py
Command:         python teams/12-quantization/scripts/run_flow.py --checkpoint ./inputs/dryrun2-1234/model.safetensors --tokenizer ./inputs/tokenizer.json --eval teams/12-quantization/prompts/eval_own_20.json --work ./work --out ./out/dryrun2-g12 --formats bf16,Q8_0,Q6_K,Q5_K_M,Q4_K_M --manifest teams/10-post-training/eval/effort_manifest.json --source-dir code_contests=./inputs/code_contests --source-dir hendrycks_math=./inputs/hendrycks_math --qe-args --spec ./inputs/dryrun2-1234/manifest.json --verify 16 --drop-router-bias --drop-head-bias
Config:          none. Every setting is on the command line or is a default of the scripts.
Inputs:          the dry run 2 model at step 1,221 as model.safetensors, its manifest.json, the frozen p1536 tokenizer (sha256 e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b), the two Team 10 parquet sets (25 `code_contests` and 6 `hendrycks_math` files, as `effort_manifest.json` names them), and a prepared work folder. See "Source and staging".
Hardware:        1 GPU
Max time:        90 minutes (ESTIMATE, see "What I ran before filing")
Precision:       bf16 baseline; Q8_0, Q6_K, Q5_K_M and Q4_K_M weights, router F32, output layer Q8_0
Measures:        Export test A1 twice: against G5's model as trained (shows how far routing moves without the router bias) and against G5 with router_bias set to zero (the wiring alone; must pass). The KAS head bias's effect on the same prompts (verify.head_bias_effect). Test A3 (llama.cpp against G5 with router_bias zeroed and the folded head without its output bias). Per format: size, bits per weight, score on 20 items, eval time, tokens per second. On the 100 prompts per format: finish reasons, tokens per second, outputs identical to bf16 and mean shared prefix with bf16, reported separately for Team 10's 55 slots and our 45 fill slots.
Expected result: A1 with router_bias zeroed PASS. A3 is reported: its 0.05 limit is not calibrated on a trained checkpoint, and on the full-shape stand-in below it was over the limit on both routes, so its top-1 count is the useful part. A1 against the trained routing FAILS by design; the size of the miss is the result. Q8_0 close to bf16 on the prompts and the score, Q6_K close, Q4_K_M further away. No score level is assumed: the model saw one English shard for 1,221 steps (TSAI's result note).
Outputs:         ./out/dryrun2-g12/{runs.csv,scores.json,manifest_<date>.json,prompts/summary.json,prompts/prompts_<format>.jsonl}, 50 MB or less (the dry run 1 smoke wrote 0.7 MB). GGUF files are deleted at the end. scores.json carries both A1 results and the statistics of the two dropped biases (export_a1, export_a1_zero_router_bias, export_router_bias, export_head_bias).
Run 2 question:  The same for the ERNIE 4.5 MoE export (#838: export_hf.py --target ernie4_5_moe, through quantize_eval.py --target), which keeps G5's router selection bias: does it match G5's model as trained (A1), and how far does each format move from its own bf16?
Run 2 order:     after the command above has exited 0, in the same ./work (see "Two runs")
Run 2 command:   python teams/12-quantization/scripts/run_flow.py --checkpoint ./inputs/dryrun2-1234/model.safetensors --tokenizer ./inputs/tokenizer.json --eval teams/12-quantization/prompts/eval_own_20.json --work ./work --out ./out/dryrun2-g12-ernie --formats bf16,Q8_0,Q6_K,Q5_K_M,Q4_K_M --manifest teams/10-post-training/eval/effort_manifest.json --source-dir code_contests=./inputs/code_contests --source-dir hendrycks_math=./inputs/hendrycks_math --qe-args --spec ./inputs/dryrun2-1234/manifest.json --verify 16 --target ernie4_5_moe --drop-head-bias
Run 2 time:      about as long as run 1 (ESTIMATE: one A1, not two, and the same llama.cpp steps)
Run 2 measures:  as run 1, with A1 once: against G5's model as trained, with the head bias left out (must pass, or the export exits 1). A3 compares llama.cpp with G5's model as trained (router bias kept, and the folded head without its output bias).
Run 2 expected:  A1 PASS. A3 is reported, as in run 1. Per format, as in run 1.
Run 2 outputs:   the files of run 1 in ./out/dryrun2-g12-ernie/, with export_target ernie4_5_moe in scores.json, export=ernie4_5_moe in the runs.csv notes, an export_router_bias action that starts with "kept", and export_a1_zero_router_bias null.
Test log:        "What I ran before filing" below
```

## Two runs

| Model | Formats | Prompts | Output directory |
|---|---|---:|---|
| dry run 2, dryrun2.yaml (KAS V2 head, bias_gamma 0.001), frozen p1536, seed 1234, step 1,221 | bf16, Q8_0, Q6_K, Q5_K_M, Q4_K_M | 100 | ./out/dryrun2-g12/ |

| Run | Command | Export | Router bias | KAS head bias | Formats | Output directory |
|---|---|---|---|---|---|---|
| 1 | `Command` | Granite MoE Shared | dropped (`--drop-router-bias`) | dropped (`--drop-head-bias`) | as in the table above | ./out/dryrun2-g12/ |
| 2 | `Run 2 command` | ERNIE 4.5 MoE (`--target ernie4_5_moe`) | kept | dropped (`--drop-head-bias`) | bf16, Q8_0, Q6_K, Q5_K_M, Q4_K_M | ./out/dryrun2-g12-ernie/ |

One job, two commands in this order, no shell pipe. `run_flow.py` runs `quantize_eval.py` and then `flow_fixed_prompts.py` and stops at the first non-zero exit code. Everything after `--qe-args` goes to `quantize_eval.py`. Run 2 uses the same `./work` after run 1, and only after run 1 exits 0: run 1 deletes its GGUF files as its last step, and run 2's files are named `<name>-ernie-*`, so nothing of run 1 is reused and the prompt step of run 2 finds only its own files. If run 1 stopped, delete `./work/*.gguf` before run 2 (otherwise run 2's prompt step refuses, finding two `*-bf16.gguf`). `quantize_eval.py` also refuses an export of the other route found under its name (only possible if one was put there by hand).

## Where each setting comes from

| Setting | Value in this job | Source |
|---|---|---|
| Checkpoint | `./inputs/dryrun2-1234/model.safetensors`, step 1,221 | TSAI's dry run 2 result (G12 channel, 27 Nov): job `dryrun2-1234`, final_model_sha256 `8d1600b278a3d8e15c3d7af408a86e7c47acd987a899bf5eeee6b2c72192eb47`. The checkpoint is in Team 7's store, `/shared/ckpt/dryrun2-1234`. ASSUMPTION on the staging, see below. |
| Model settings | `./inputs/dryrun2-1234/manifest.json` (`config.model`), passed with `--spec` | the run's `./out/dryrun2-1234/manifest.json`. A bare state_dict has no settings beside it, so `export_hf.py` needs the file. |
| Router bias | run 1: dropped (`--drop-router-bias`); A3 and the second A1 compare with G5 at router_bias zero. Run 2: kept; A1 and A3 compare with G5 as trained | Run 1: GraniteMoeShared has no selection bias (#762). The exact route is the patched llama.cpp, not ready yet. Run 2: `Ernie4_5_MoeForCausalLM` has a selection-only bias (`mlp.moe_statics.e_score_correction_bias`) that routes as G5 does, and stock llama.cpp b11669 (`ernie4_5-moe`) applies it (#838; stand-in results in the #862 comments). |
| KAS head bias | dropped (`--drop-head-bias`); A1 and A3 compare with the folded head without it, and its effect is measured | GraniteMoeShared has no output bias (#780). |
| Formats | bf16, Q8_0, Q6_K, Q5_K_M, Q4_K_M | `docs/bitwidth_proposal.md` v2 (#853): serve Q8_0, Q6_K the candidate "confirm on the lab's own model", Q4_K_M the format that failed on all four public models. Q5_K_M is added because the week 5 brief (design task 1) asks for 16, 8, 6, 5 and 4 bits: it gives the gap to bf16 one more point between Q6_K and Q4_K_M (still not a candidate to ship). |
| A1 prompts | 16 per A1 (two A1 runs) | `--verify 16`. The default 64 would take twice as long on CPU for a 300M model with two A1 runs; 16 prompts x 64 tokens is 1,024 positions each. |
| Run 2 | `--target ernie4_5_moe --drop-head-bias`, one A1, formats bf16, Q8_0, Q6_K, Q5_K_M, Q4_K_M | therahulbhati's ask on #862: an ERNIE run next to the Granite one, same formats, `--drop-head-bias` only. The formats are run 1's with Q5_K_M, which #885 adds to run 1, so the two exports compare format by format. llama.cpp's `ernie4_5-moe` has no output bias either, so the KAS head bias is dropped in run 2 too (#838). |
| Router and output layer | router F32, output layer Q8_0 | `quantize_eval.py` defaults. |
| Items for the score | `prompts/eval_own_20.json`, sha256 `5d4fec16221c3d2dd1aa2695f6f6ded97d5a493afd460bf7f927e19e36fbb069` | same as dry run 1, so the two runs compare. |
| 100 prompts | Team 10's `eval/effort_manifest.json` (30 code and 25 math slots) plus 45 of ours | as in dry run 1. |
| Decoding | greedy (temperature 0, top_k 1), seed 0, 128 new tokens, context 2,048 | `flow_fixed_prompts.py` defaults. |
| llama.cpp | b11669 binaries and checkout | #467, as in dry run 1. |

## Source and staging

- Start from `theschoolofai/era-v5-lab` main with #862 and the follow-up that adds run 2 merged. #862 adds `--formats` to `run_flow.py`, the second A1 to `export_hf.py`, and both A1 results and the bias statistics to `quantize_eval.py`'s scores.json. The follow-up adds `--target` to `quantize_eval.py` (run 2; it is passed on to `export_hf.py`).
- Checkpoint: the model weights at step 1,221 from `/shared/ckpt/dryrun2-1234`, written as `./inputs/dryrun2-1234/model.safetensors` with Team 7's `ckpt.export_safetensors` (the same call Team 9's `harness_lab/run_lab_ckpt.py` makes; it checks every key). A `checkpoint.pt` with `{"model": state_dict}` works too: then pass `--checkpoint ./inputs/dryrun2-1234/checkpoint.pt`. Copy `./out/dryrun2-1234/manifest.json` beside it.
- Tokenizer, Python, llama.cpp binaries, the `./work/` folder (`llama.cpp-b11669/`, `.venv-convert/`) and Team 10's parquet files: as in `2026-11-18-dryrun1-quantize-eval.md`, "Source and staging". The dry run 1 staging can be reused as it is. Please start from a `./work/` without dry run 1's `*-bf16.gguf` or `*-scores.json`, so the prompt step finds only this run's files.
- With these in place the run makes no network call.

## How the run is scored and reported

- As in dry run 1: 20 own items for the score (a check that the files work and move little from bf16, not a benchmark), and Team 10's 55 slots and our 45 reported apart, with no prompt or output text for Team 10's slots.
- Run 1 sets the two biases aside in every GGUF and run 2 the head bias only, so every format is compared with bf16 of the same export. The bf16 number is not the checkpoint's own quality: the first A1 and `head_bias_effect` say how far the export is from it on random prompts. What the biases cost on real text comes from two other reports, attached next to this result, not from this job: Team 10's `router_bias_reach.py` in the dry run 2 chain and G12's `ollama/measure_export_gaps.py` (#834).
- One checkpoint, one seed, greedy decoding. No winner is named and no setting is changed.

## What I ran before filing

On an Apple laptop (CPU), with a random-weight model in dry run 2's shape from `make_random_checkpoint.py --head-mode kas_v2 --bias-gamma 0.001 --router-bias-std 0.01` (2 layers, width 128, 10.8M parameters, vocabulary 131,072), saved as a bare `model.safetensors` with its `manifest.json` beside it, as the staging above:

| Step | Result |
|---|---|
| `export_hf.py` without the two flags | refused: `blocks.1.moe.router_bias is not zero (largest absolute value 0.0236, bias_gamma 0.001)` |
| `export_hf.py --verify 16 --drop-router-bias --drop-head-bias` | exit 0. The export itself takes 7 s; the two A1 runs take the rest (95 s in all with `--verify 2`, 15.7 min with `--verify 16` on a busy laptop) |
| A1 against G5 as trained | max logit difference 6.3, same top-1 on 864 of 1,024 positions: FAIL, as expected with the router bias dropped |
| A1 against G5 with router_bias zeroed | max logit difference 2.1e-05 (limit 1e-3), same top-1 on 1,024 of 1,024: PASS |
| `test_export_hf.py`, `test_run_flow.py` | 40 and 5 tests pass |

Not run here: the llama.cpp steps (A3, quantize, scores, prompts). They are the dry run 1 flow, unchanged, which ran end to end in that smoke (`evidence/2026-11-18-dryrun1-quantize-eval/smoke.md`), and A3 on a dropped-both KAS V2 GGUF passed in #780's smoke (16 of 16 prompts, 0.017). The random weights make every A1 number a wiring check, not a prediction for the trained model. I could not test the real checkpoint, a GPU, or the p1536 tokenizer on this machine.

### Both runs end to end (sourav-dhar, 28 Nov)

On an Apple laptop (export, A1 and A3 on CPU; scores and prompts on Metal), llama.cpp b11669 (`620d222`: `llama-server`, and `llama-quantize` built from the same checkout), the converter venv as `quantize_eval.py` builds it (torch 2.11.0, transformers 4.57.6), the frozen p1536 tokenizer, and a random-weight model in dry run 2's full shape: `make_random_checkpoint.py --d-model 512 --n-layer 8 --n-head 8 --n-kv-head 2 --d-ff 768 --n-expert 16 --n-shared 1 --top-k 2 --seq-len 2048 --pos-dim 32 --std 0.05 --head-mode kas_v2 --bias-gamma 0.001 --router-bias-std 0.01` (176,398,881 parameters), saved as a bare `model.safetensors` with its `manifest.json`. At width 512 the K-quants are real (at width 128 `llama-quantize` falls back to q8_0 for them). `Command` (with #885's Q5_K_M, as `Run 2 command` has it) and `Run 2 command` ran in this order in one `./work`, without `--manifest`/`--source-dir` (Team 10's parquet files are not on this machine) and with `--llama-bin`:

| Step | Run 1 (Granite) | Run 2 (ERNIE) |
|---|---|---|
| Exit code, wall time | 0, 211 s | 0, 270 s (its eval steps took up to twice as long as in the four-format run below, so the wall times are noisy) |
| A1 against G5 as trained (head bias left out) | 437 of 1,024 same top-1, max 7.48: FAIL, as expected | 1,024 of 1,024, max 3.7e-05 (limit 1e-3): PASS |
| A1 with router_bias zeroed | 1,024 of 1,024, max 3.8e-05: PASS | not run (the bias is kept) |
| A3, 16 prompts | 14 of 16 same top-1, max 1.04 (against G5 at router_bias zero) | 16 of 16, max 0.50 (against G5 as trained) |
| GGUF | `granitemoe`, pre-tokenizer granite-embed-multi-97m, 131,072 ids, eos 130822 | `ernie4_5-moe`, the same pre-tokenizer, ids and eos |
| Files | bf16, Q8_0, Q6_K, Q5_K_M, Q4_K_M at 16.0, 8.58, 7.09, 6.37, 5.69 bits per weight; router F32; output layer Q8_0 in the four quantized formats (BF16 in bf16) | the same bits per weight, router and output layer types |
| Prompts | 100 prompts x 5 formats | 100 prompts x 5 formats |
| `./work` after the run | no GGUF file; the exported folder `hf/<name>`, the `.quant_time` files, the A3 result, `llama-server.log` and `quantize-<format>.log` stay | the same, with `-ernie` names beside run 1's (run 1's export was not reused); `quantize-<format>.log` has no name in it, so run 2 overwrites run 1's |

With four formats (`Command` as on main, and `Run 2 command` without Q5_K_M) both runs exit 0 (148 s and 145 s) with the same A1 and A3 numbers, and the four GGUF files of each run have the same sha256 as in the five-format run.

A3 is over its 0.05 limit on both routes with random weights. With 64 prompts (`check_gguf_logits.py --prompts 64`) the bf16 ERNIE GGUF had the same top-1 as G5 as trained on 52 of 64 prompts and the Granite GGUF on 16; against G5 with router_bias zeroed it is 21 against 51 (27 Nov, same stand-in, in the #862 comments, with the check that the router bias is stored bit for bit in every format). `test_quantize_eval.py` 13 tests pass (8 new: `--target` reaches `export_hf.py`; ERNIE files are named `-ernie` and Granite names are unchanged; a resumed run refuses an export of the other route; an export report from before #838 is reused by a Granite run and refused by an ERNIE run; the runs.csv note comes from the export report; `--target ernie4_5_moe` stops before any work with `--drop-router-bias`, without `--drop-head-bias`, or on a Hugging Face folder). Taking out any one part of the change makes a new test fail (checked one by one), except the two lines of `main()` that write the runs.csv note and `export_target`: the run above checks those (`export=ernie4_5_moe` in run 2's runs.csv notes, `export_target` in both scores.json). `test_run_flow.py` 5 and `test_export_hf.py` 40 pass. Not run here: Team 10's 55 slots, the real checkpoint and a CUDA GPU. The random weights make these a wiring check, not a prediction for the trained model.

## Open items for TSAI

1. **Checkpoint.** Can the step 1,221 weights be staged as `model.safetensors` (Team 7's `export_safetensors`) or as a `checkpoint.pt` with a `model` key, plus `manifest.json`? If the path differs, I change `--checkpoint` and `--spec`.
2. **Time.** The two A1 runs are on CPU and take most of the export time (see the smoke). 90 minutes is an estimate for a model about 30 times the stand-in's size. If it runs long, `--verify 8` halves the A1 time.
3. **Work folder.** As in dry run 1, `./work/` sits outside `./out/` (llama.cpp checkout, converter venv, the exported model, the GGUFs). Nothing in it needs copying: `scores.json` has the export results.
4. **Dry run 1.** The dry run 1 job (22 Nov, "running it now") has not posted results yet. If it finished, its `runs.csv` and `scores.json` let us put the two runs side by side.
5. **Run 2.** It needs no extra staging: the same inputs and the same `./work`. If time is short, run 1 alone is the job TSAI approved on #862.
