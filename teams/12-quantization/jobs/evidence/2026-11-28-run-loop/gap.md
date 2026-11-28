# Gap table

weights sha256 `464011f3cbec0f528af3cbc5392776c1e95c324563aa176b8d0f937745b389e0` (stages/strip.json)
guards: RELAXED: --drop-router-bias --drop-head-bias (the GGUF is not the checkpoint as trained; every gap is against the bf16 GGUF of the same export)
items: `<repo>/teams/12-quantization/prompts/eval_own_20.json` sha256 `5d4fec16221c3d2d`; score = fraction correct, gap = format minus bf16 GGUF, from each q/<format>/scores.json

| format | size GB | bpw | n | score | gap | mcq gap | numeric gap | tok/s | A1 as trained | A1 router_bias zeroed | A3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bf16 | 0.61 | 16.0 | 20 | 0.0 | +0.0 | +0.0 | +0.0 | 0 | False | True | True |
| Q8_0 | 0.32 | 8.58 | 20 | 0.0 | +0.0 | +0.0 | +0.0 | 0 | False | True | True |
| Q6_K | 0.27 | 7.09 | 20 | 0.0 | +0.0 | +0.0 | +0.0 | 0 | False | True | True |
| Q5_K_M | 0.24 | 6.37 | 20 | 0.0 | +0.0 | +0.0 | +0.0 | 0 | False | True | True |
| Q4_K_M | 0.22 | 5.69 | 20 | 0.0 | +0.0 | +0.0 | +0.0 | 0 | False | True | True |

Full copy (Team 9 scorer, score_full.v1.json): not scored (needs a store input)
Watcher: no watcher score given (--watcher-json): not compared

Commands:
- bf16: `python <repo>/teams/12-quantization/scripts/quantize_eval.py --checkpoint <scratch>/loop/out/weights/model.safetensors --tokenizer ~/Downloads/tokenizer_p1536.json --eval <repo>/teams/12-quantization/prompts/eval_own_20.json --formats bf16 --work ~/.cache/era-v5-quant --runs-csv <scratch>/loop/out/runs.csv --scores-out <scratch>/loop/out/q/bf16/scores.json --verify 4 --name loop --cleanup --spec <scratch>/loop/out/weights/manifest.json --drop-router-bias --drop-head-bias --no-record`
- Q8_0: `python <repo>/teams/12-quantization/scripts/quantize_eval.py --checkpoint <scratch>/loop/out/weights/model.safetensors --tokenizer ~/Downloads/tokenizer_p1536.json --eval <repo>/teams/12-quantization/prompts/eval_own_20.json --formats Q8_0 --work ~/.cache/era-v5-quant --runs-csv <scratch>/loop/out/runs.csv --scores-out <scratch>/loop/out/q/Q8_0/scores.json --verify 4 --name loop --cleanup --spec <scratch>/loop/out/weights/manifest.json --drop-router-bias --drop-head-bias --no-record`
- Q6_K: `python <repo>/teams/12-quantization/scripts/quantize_eval.py --checkpoint <scratch>/loop/out/weights/model.safetensors --tokenizer ~/Downloads/tokenizer_p1536.json --eval <repo>/teams/12-quantization/prompts/eval_own_20.json --formats Q6_K --work ~/.cache/era-v5-quant --runs-csv <scratch>/loop/out/runs.csv --scores-out <scratch>/loop/out/q/Q6_K/scores.json --verify 4 --name loop --cleanup --spec <scratch>/loop/out/weights/manifest.json --drop-router-bias --drop-head-bias --no-record`
- Q5_K_M: `python <repo>/teams/12-quantization/scripts/quantize_eval.py --checkpoint <scratch>/loop/out/weights/model.safetensors --tokenizer ~/Downloads/tokenizer_p1536.json --eval <repo>/teams/12-quantization/prompts/eval_own_20.json --formats Q5_K_M --work ~/.cache/era-v5-quant --runs-csv <scratch>/loop/out/runs.csv --scores-out <scratch>/loop/out/q/Q5_K_M/scores.json --verify 4 --name loop --cleanup --spec <scratch>/loop/out/weights/manifest.json --drop-router-bias --drop-head-bias --no-record`
- Q4_K_M: `python <repo>/teams/12-quantization/scripts/quantize_eval.py --checkpoint <scratch>/loop/out/weights/model.safetensors --tokenizer ~/Downloads/tokenizer_p1536.json --eval <repo>/teams/12-quantization/prompts/eval_own_20.json --formats Q4_K_M --work ~/.cache/era-v5-quant --runs-csv <scratch>/loop/out/runs.csv --scores-out <scratch>/loop/out/q/Q4_K_M/scores.json --verify 4 --name loop --cleanup --spec <scratch>/loop/out/weights/manifest.json --drop-router-bias --drop-head-bias --no-record`
