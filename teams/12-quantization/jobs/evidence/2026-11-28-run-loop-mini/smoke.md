# run_loop.py eval-mini stage smoke, 28 Nov 2026 (Apple M5 16 GB, CPU, llama.cpp b11669, llama-cpp-python 0.3.36, lm_eval 0.4.13)

Not a result: Udit's synthetic 3-step bundle (weights sha256 `464011f3...`), random-like weights, trained context 32 tokens. Every score is near
chance and every gap is about zero; this shows that the stage runs, resumes and reports. Firewall: the files here hold scores, task names,
counts and hashes only (no item text, no item ids; the per-item `*.samples.jsonl` files stay in the scratch folder). Paths are
placeholders: `<repo>`, `<scratch>`, `<bundle-scratch>`, `~`.

## Command (`<scratch>/mini/run.sh`)

```
HF_HOME=<scratch>/mini/hf python teams/12-quantization/scripts/run_loop.py --weights <bundle>/model.safetensors --manifest <bundle>/manifest.json \
    --tokenizer ~/Downloads/tokenizer_p1536.json --out <scratch>/mini/out --work <scratch>/stage/work --formats bf16,Q8_0 \
    --drop-router-bias --drop-head-bias --verify 4 --mini-python <scratch>/mini/evalvenv/bin/python --model-note "Synthetic 3-step ..." --qe-args --no-record
```
Mini defaults: `--mini-tasks mmlu,arc_challenge` (G9's mini profile limits: mmlu 10 items per subject = 570, arc_challenge 500), CPU (`--mini-ngl 0`).
The eval venv: `uv venv --python 3.12`, then `uv pip install llama-cpp-python==0.3.36 lm_eval==0.4.13 datasets==5.1.0` (the pins of eval_mini.ipynb).

## What `loop_log.jsonl` shows (times from its own `ts`)

| Time | Event |
|---|---|
| 12:14:58 | `mini_bf16` starts, crashes at once: `NameError: shutil` (my import was missing). Fixed; the unit tests did not cover it because the first version of the test had no mini stage |
| 12:15:55 | rerun: strip and q_bf16 skipped, `mini_bf16` starts; `bf16/mmlu` done (acc 0.2614, n=570, 538 s) |
| ~12:25:41 | `kill -9` on the process group while `arc_challenge` was running (no `mini_bf16` marker; `mini/bf16/summary.json` holds mmlu) |
| 12:25:45 | rerun: `bf16/mmlu: already done, skipped`, `arc_challenge` runs (151 s), `mini_bf16` done 12:28:17 |
| 12:28:17 to 12:28:24 | `q_Q8_0` (the bf16 GGUF is reused) |
| 12:28:24 to 12:31:41 | `mini_Q8_0` (mmlu 134 s, arc ~63 s); the Q8_0 GGUF is deleted after it, bf16 stays |
| 12:31:55 | full rerun: strip, q_*, mini_* all skipped; report rebuilt |

## Result (`gap.md`, `gap.json`)

| task | metric | bf16 | Q8_0 | gap | gap se (unpaired) |
|---|---|---|---|---|---|
| mmlu (n=570) | acc | 0.2614 +/- 0.0185 | 0.2614 +/- 0.0185 | 0.0 | 0.0261 |
| arc_challenge (n=500) | acc_norm | 0.2500 +/- 0.0194 | 0.2480 +/- 0.0193 | -0.002 | 0.0274 |

Chance is 0.25 for both. The own-20-item column of the gap table is kept and labelled "own 20 items (G12 own, through llama-server; NOT eval-mini)".
`test_llamacpp_lm.py` (the shifted-logprob guard) runs before each format and its exit code is in the table and in `stages/mini_*.json`
(`guard_exit` 1: the random model does not rank " Paris" in its top 5, which that guard's check 1 needs; it is reported, not fatal. Its
checks 1 and 2 need a model that knows the answer, so they cannot judge this checkpoint.)

## Cost

Time: `mini_bf16` 538 s + 151 s (two runs, one kill), `mini_Q8_0` 197 s (timestamps above). Disk: eval venv 559 MB, HF datasets cache 17 MB
(network, once: the datasets, the pip wheels, nothing else), `out/` 264 KB; the bf16 GGUF 0.61 GB stays, one quantized GGUF at a time
(0.32 GB for Q8_0) is held until its mini stage ends. The whole flow for a 300M-parameter model needs about 1.3 GB beyond the HF export (0.6 GB) at its peak.

## Tests and limits

`python teams/12-quantization/scripts/test_run_loop.py`: 7 tests OK (fake eval-mini runner): a mini stage per format, the gap and its se, the
label and the model note (printed only with `--model-note`), a GGUF kept for its mini stage then deleted, a killed mini stage resumes with its GGUF,
a changed task list reruns the mini stages only (and rebuilds the deleted quantized GGUFs from bf16, not re-making bf16).
Not run: Q6_K, Q5_K_M, Q4_K_M mini stages (two formats only), GPU/Metal, the real dry run 2 checkpoint, hellaswag / gsm8k / truthfulqa_mc2
(in G9's mini profile, not in the v2 evidence; use `--mini-tasks`), Belebele and MILU (not in the mini profile; `eval_wide/run_wide_gguf.py` has them).
No change was made to eval_mini code or G9's harness.
