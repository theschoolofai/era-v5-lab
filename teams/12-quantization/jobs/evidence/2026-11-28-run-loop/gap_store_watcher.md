# Gap table

weights sha256 `2ec503310da0c920c0bfffd5600160fd367d4d416e5ae49ee040db3488b27655` (stages/strip.json)
guards: strict: nothing set aside
items: `<repo>/teams/12-quantization/prompts/eval_own_20.json` sha256 `5d4fec16221c3d2d`; score = fraction correct, gap = format minus bf16 GGUF, from each q/<format>/scores.json

| format | size GB | bpw | n | score | gap |  | tok/s | A1 as trained | A1 router_bias zeroed | A3 |
|---|---|---|---|---|---|---|---|---|---|

Full copy (Team 9 scorer, score_full.v1.json): {'lab_smoke_next_token/acc/none': 100.0}
Watcher: match {'lab_smoke_next_token/acc/none': (100.0, 100.0)}

Commands:
