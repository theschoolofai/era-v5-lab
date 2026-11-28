# Protocol check for the two code known failures (#334, #335)

Both code FAILs in [`compare_v0_code_indic.md`](compare_v0_code_indic.md) disappear when the samples are generated
with the EvalPlus protocol of December 2023 instead of evalplus 0.3.1. This file records the evidence. It changes
no verdict: the rows in the comparison report and in [`known_failures.md`](known_failures.md) stand until the
G9 lead decides how to record this.

## Results

All runs: M2 Pro, Apple GPU (MPS), greedy, scored with `evalplus.evaluate` 0.3.1 in `python:3.12-slim`, 0 timeouts.

| Model, benchmark | Published | Our harness (0.3.1) | Dec 2023 protocol | Δ to published |
|---|---|---|---|---|
| phi-2, MBPP | 64.0 | 62.43 | 64.02 (242/378) | +0.02 |
| phi-2, MBPP+ ([#335](https://github.com/theschoolofai/era-v5-lab/issues/335)) | 54.2 | 51.32 (194/378), FAIL | 54.23 (205/378) | +0.03 |
| Qwen2.5-1.5B, HumanEval | 37.2 | 35.37 (58/164) | 37.20 (61/164) | 0.00 |
| Qwen2.5-1.5B, HumanEval+ ([#334](https://github.com/theschoolofai/era-v5-lab/issues/334)) | 32.9 | 30.49 (50/164), FAIL | 31.10 (51/164) | −1.80 |

- **phi-2:** float16, prompts from MBPP+ v0.1.0, scored on MBPP+ v0.2.0 (hash `ee43ecabebf20deef4bb776a405ac5b1`).
- **Qwen2.5-1.5B:** bfloat16, HumanEval+ v0.1.10 (hash `fe585eb4df8c88d844eeb463ea4d0302`). Scoring the same samples
  on HumanEval+ v0.1.9 (hash `84f4b93a1270b492e4c54d5212da7a5b`) gives the same 61 and 51.
- **Qwen, base pass and plus fail:** HumanEval/22, 25, 46, 55, 60, 63, 76, 122, 151, 154.

## The December 2023 protocol

Taken from evalplus/evalplus at commit `7d3a585` (30 Dec 2023), the day phi-2 was run for the leaderboard.

| Setting | Dec 2023 | evalplus 0.3.1 (our harness) |
|---|---|---|
| Prompt | `task["prompt"]` unchanged | stripped, plus one newline |
| Stop strings | `<\|endoftext\|>`, `<\|endofmask\|>`, `</s>` | those, plus `\nif __name__`, `\ndef main(`, `\nprint(` and per-dataset strings such as `\ndef `, `\nassert` |
| New tokens | 512 | 768 |
| Output | prompt + completion | completion through the built-in sanitizer |
| Clean-up | `tools/sanitize.py` at `d48a1e4` | built-in sanitizer |

## How the phi-2 leaderboard number was made (#335)

Read from the git history of evalplus/evalplus and of the leaderboard's `results.json`.

1. **29–30 Dec 2023:** phi-2 was added (`4f9d3dc`) and moved to vLLM with float16 (`7d3a585`). MBPP+ was v0.1.0, 399 tasks.
2. **Leaderboard values for phi-2 MBPP+:** 52.9 (23 Mar 2024), 52.4 (12 Apr), then 54.2 on 21 Apr 2024 in the commit
   "Update mbpp v0.2.0" (`65db7ff`). MBPP went from 62.9 to 64.0 in the same commit.
3. **The prompt handling changed later**, on 29 Apr 2024 (`31389be`). So the December samples were re-scored on
   v0.2.0; they were not regenerated.

Our rerun follows the same three steps and gives the leaderboard's two numbers. This is the publisher's protocol.

## What is and is not shown for Qwen (#334)

- **Not stated by Qwen.** The Qwen2.5 blog and paper (arXiv 2412.15115, Table 5) say only "0-shot" and cite
  Liu et al. 2023. They give no harness version, prompt, stop strings, token limit or dataset version.
- **Inferred.** The December 2023 protocol gives exactly the published HumanEval score, 61/164. That is good
  evidence for the older prompt and stop-string handling, but it is not Qwen's stated protocol.
- **HumanEval+ is within 2.0** (−1.80) under that protocol. The published 32.9 is 54/164; we get 51.

## Limits

- **Different generation backend.** The leaderboard used vLLM on CUDA; these runs used transformers on MPS.
- **Old prompt text.** 18 of the 378 MBPP+ prompts differ between v0.1.0 and v0.2.0. The samples use the old
  text, as the leaderboard's did.
- **One machine.** Each row is one run on one machine.
- **A timing-sensitive test.** HumanEval/15 has an input of n = 999991. A correct solution failed it once, in a
  scoring run made while the disk was full; four clean reruns passed. Score on an idle machine.
- **Other models.** deepseek-coder-1.3b came from the same 2023 code and passes all four rows with 0.3.1, so the
  effect of the stricter stop strings depends on the model.

## Reproduce

In `../harness_code_indic/` (Docker needed for scoring):

```
python fetch_weights.py --model phi-2
python codegen_2023_protocol.py --weights <weights dir> --dataset mbpp --version v0.1.0 --dtype float16 --out runs/protocol_2023/phi-2__mbpp.jsonl
python score_2023_protocol.py --samples runs/protocol_2023/phi-2__mbpp.jsonl --dataset mbpp

python fetch_weights.py --model qwen2.5-1.5b
python codegen_2023_protocol.py --weights <weights dir> --dataset humaneval --dtype bfloat16 --out runs/protocol_2023/qwen2.5-1.5b__humaneval.jsonl
python score_2023_protocol.py --samples runs/protocol_2023/qwen2.5-1.5b__humaneval.jsonl --dataset humaneval
```

Generation took 111 minutes for phi-2 (399 tasks) and 22 minutes for Qwen2.5-1.5B (164 tasks) on the M2 Pro.
Samples and result files stay in `runs/`, which is gitignored.
