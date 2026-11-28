# run_loop.py smoke, 28 Nov 2026 (Apple laptop, CPU, llama.cpp b11669)

Not a result: random-weight models, so every score is 0.0 and every gap is 0.0. The smoke shows that the stages run, that a kill is
survived, and that a rerun skips what is finished. Each file here is the output of the command above it. Paths are those of the
scratchpad of the run. Python: a venv with torch 2.15.0 (`run_lab_ckpt.py` needs 2.14.1 or newer) and `kronecker-embeddings`
at the commit `teams/04-ke2/src/requirements.txt` pins (the restore test imports it).

## 1. Team 7's restore-test store, Team 9's smoke scorer (strip + score_full + report)

```
python teams/07-infrastructure/jobs/restore_test/restore_test.py          # PASS restore_test nproc=1 cpu
python teams/09-evaluation/harness_lab/eval_watcher.py --run-dir <out>/ckpt_store/restore-b --once --no-load   # the "watcher" file
python teams/12-quantization/scripts/run_loop.py --run-dir <out>/ckpt_store/restore-b --tokenizer ~/Downloads/tokenizer_p1536.json \
    --out /tmp/loop2 --stages strip,score_full,report --watcher-json <watcher out>/main__step_00000100-e1.json
```

`gap_store_watcher.md`: weights sha256 `2ec50331...`, full copy `lab_smoke_next_token/acc/none` 100.0 = watcher 100.0 (match). The tiny
MoE has no G5 layout and no p1536 vocabulary, so the quantize stages cannot run on it (that is why `--stages` exists); the store
path is tested up to the weights and Team 9's score.

## 2. Udit's synthetic KAS V2 bundle (`kas-export-rehearsal-2026-11-24/model.safetensors`, sha256 `464011f3...`)

```
python teams/12-quantization/scripts/run_loop.py --weights <bundle>/model.safetensors --manifest <bundle>/manifest.json \
    --tokenizer ~/Downloads/tokenizer_p1536.json --out <scratch>/loop/out --work ~/.cache/era-v5-quant \
    --drop-router-bias --drop-head-bias --verify 4 --qe-args --no-record
```

Run 1 was killed with `kill -9` on its process group while `q_Q6_K` was running (`loop_log.jsonl` lines 1-7: strip, q_bf16, q_Q8_0 done,
q_Q6_K started, nothing after). Run 2 (same command): `strip`, `q_bf16`, `q_Q8_0` skipped ("marker has the same version and key"),
`q_Q6_K` redone, then `q_Q5_K_M`, `q_Q4_K_M`, report (lines 8-17). Run 3: everything skipped, report rebuilt (lines 18-26).
`gap.md`, `gap.json`, `loop_log.jsonl`, `stage_strip.json` are the files of that run.

| Test (from `q/bf16/scores.json`) | Result |
|---|---|
| A1 against G5 as trained | FAIL by design: max logit difference 0.48, same top-1 on 123/128 (router_bias dropped) |
| A1 with router_bias zeroed | PASS: 2.19e-05, 128/128 |
| A3 | PASS: 16/16 prompts, max log-probability difference 0.0172 |

Gap table (`gap.md`): bf16, Q8_0, Q6_K, Q5_K_M, Q4_K_M at 0.61, 0.32, 0.27, 0.24, 0.22 GB (16.0, 8.58, 7.09, 6.37, 5.69 bpw); score 0.0 on
the 20 own items in every format, so every gap is +0.0. The table says `RELAXED: --drop-router-bias --drop-head-bias`.

## 3. Tests

`python teams/12-quantization/scripts/test_run_loop.py`: 4 tests OK (fake quantize_eval): rerun skips; a bumped stage version reruns
that stage and never `strip`; a killed stage leaves no marker and the rerun resumes there; gap and label; a new checkpoint reruns all.

## Not tested

A real checkpoint (dry run 2 step 1,221 is not here), a GPU, Team 9's watcher on a real store, `lm_eval_lab:team5` as `--scorer`, and
eval-mini on the GGUFs (`eval_mini/run_mini_gguf.py` needs G9's harness, llama-cpp-python and the datasets): the loop scores the
quantized copies on `--eval` items through llama-server, as `quantize_eval.py` does.

Note: the local absolute paths in the files of this folder (repo, scratch folder, Python of the venv, home folder) were replaced by `<repo>`, `<scratch>`, `python` and `~` before the commit. Nothing else was changed.
