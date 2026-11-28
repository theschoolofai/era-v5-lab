# Gap table

> Synthetic 3-step test checkpoint (Udit's bundle): its eval-mini scores are near chance and every gap is about zero. This run proves the wiring, not quantization quality (docs/bitwidth_proposal.md has the public-model evidence).

weights sha256 `464011f3cbec0f528af3cbc5392776c1e95c324563aa176b8d0f937745b389e0` (stages/strip.json)
guards: RELAXED: --drop-router-bias --drop-head-bias (the GGUF is not the checkpoint as trained; every gap is against the bf16 GGUF of the same export)
own 20 items (G12 own, through llama-server; NOT eval-mini): `<repo>/teams/12-quantization/prompts/eval_own_20.json` sha256 `5d4fec16221c3d2d`; score = fraction correct, gap = format minus bf16 GGUF, from each q/<format>/scores.json

| format | size GB | bpw | n | score | gap | mcq gap | numeric gap | tok/s | A1 as trained | A1 router_bias zeroed | A3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bf16 | 0.61 | 16.0 | 20 | 0.0 | +0.0 | +0.0 | +0.0 | 0 | False | True | True |
| Q8_0 | 0.32 | 8.58 | 20 | 0.0 | +0.0 | +0.0 | +0.0 | 0 | False | True | True |

## eval-mini (G9 mini profile via eval_mini/run_mini_gguf.py, llama-cpp-python, one runtime for every format; gap = format minus bf16 GGUF, se = the standard error eval-mini reports; the gap se is the unpaired sqrt(se_format^2 + se_bf16^2))

| task | metric | format | n | score | se | gap | gap se | guard exit |
|---|---|---|---|---|---|---|---|---|
| mmlu | acc | bf16 | 570 | 0.2614035087719298 | 0.01848360307518024 | - | - | 1 |
| mmlu | acc | Q8_0 | 570 | 0.2614035087719298 | 0.01848360307518024 | 0.0 | 0.0261 | 1 |
| arc_challenge | acc_norm | bf16 | 500 | 0.25 | 0.019384310743640384 | - | - | 1 |
| arc_challenge | acc_norm | Q8_0 | 500 | 0.248 | 0.019332342821239124 | -0.002 | 0.0274 | 1 |

Commands: `<scratch>/mini/evalvenv/bin/python <repo>/teams/12-quantization/eval_mini/run_mini_gguf.py --gguf <scratch>/stage/work/loop-464011f3-bf16.gguf --format bf16 --out <scratch>/mini/out/mini --g9-harness <repo>/teams/09-evaluation/harness/run_eval_mini.py --tasks mmlu arc_challenge --n-gpu-layers 0 --model lab:0158d87b --revision 0158d87b323075de3baaf599cc7a8d96b44904742bc1eba1b4434bfe67b38306`; `<scratch>/mini/evalvenv/bin/python <repo>/teams/12-quantization/eval_mini/run_mini_gguf.py --gguf <scratch>/stage/work/loop-464011f3-Q8_0.gguf --format Q8_0 --out <scratch>/mini/out/mini --g9-harness <repo>/teams/09-evaluation/harness/run_eval_mini.py --tasks mmlu arc_challenge --n-gpu-layers 0 --model lab:4ae26e11 --revision 4ae26e1106f687a52d09d9f3ebb2ced824f38298b22ea1d726066e4187e66271`

Full copy (Team 9 scorer, score_full.v1.json): not scored (needs a store input)
Watcher: no watcher score given (--watcher-json): not compared

Commands:
- bf16: `~/.cache/era-v5-quant/venv-loop/bin/python <repo>/teams/12-quantization/scripts/quantize_eval.py --checkpoint <scratch>/mini/out/weights/model.safetensors --tokenizer ~/Downloads/tokenizer_p1536.json --eval <repo>/teams/12-quantization/prompts/eval_own_20.json --formats bf16 --work <scratch>/stage/work --runs-csv <scratch>/mini/out/runs.csv --scores-out <scratch>/mini/out/q/bf16/scores.json --verify 4 --name loop --spec <scratch>/mini/out/weights/manifest.json --drop-router-bias --drop-head-bias --no-record`
- Q8_0: `~/.cache/era-v5-quant/venv-loop/bin/python <repo>/teams/12-quantization/scripts/quantize_eval.py --checkpoint <scratch>/mini/out/weights/model.safetensors --tokenizer ~/Downloads/tokenizer_p1536.json --eval <repo>/teams/12-quantization/prompts/eval_own_20.json --formats Q8_0 --work <scratch>/stage/work --runs-csv <scratch>/mini/out/runs.csv --scores-out <scratch>/mini/out/q/Q8_0/scores.json --verify 4 --name loop --spec <scratch>/mini/out/weights/manifest.json --drop-router-bias --drop-head-bias --no-record`
