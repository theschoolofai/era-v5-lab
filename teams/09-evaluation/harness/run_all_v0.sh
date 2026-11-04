#!/usr/bin/env bash
# The exact command sequence behind eval_mini_v0 (24-25 Oct 2026, Apple M2 Pro 32 GB, MPS, bf16).
# Run from the repository root after the set-up in README.md:
#   caffeinate -i bash teams/09-evaluation/harness/run_all_v0.sh 2>&1 | tee -a teams/09-evaluation/harness/runs/run_all_v0.log
#   .venv/bin/python teams/09-evaluation/harness/build_results.py
# Stages are ordered so the most useful results land first; stop after any stage and rebuild.
# Wall clock on the M2 Pro: stage 1 ~55 min, stage 2 ~85 min, stage 3 ~2.5 h, stage 4 ~70 min, stage 5 ~100 min.
set -euo pipefail
PY=${PY:-.venv/bin/python}
RUN="$PY teams/09-evaluation/harness/run_eval_mini.py"
MODELS=("Qwen/Qwen2.5-0.5B" "Qwen/Qwen2.5-1.5B" "HuggingFaceTB/SmolLM2-1.7B")

echo "== stage 1: profile mini on every model (the uniform baseline other teams diff against)"
for m in "${MODELS[@]}"; do $RUN --model "$m" --profile mini; done

echo "== stage 2: full TruthfulQA (0-shot) and full ARC Easy + Challenge (0-shot) in the publishers' settings"
for m in "${MODELS[@]}"; do $RUN --model "$m" --profile check --tasks truthfulqa_mc2 arc_easy arc_challenge; done

echo "== stage 3: full GSM8K 5-shot (SmolLM2 card's setting; lm_eval default)"
for m in "${MODELS[@]}"; do $RUN --model "$m" --profile check --tasks gsm8k; done

echo "== stage 4: full GSM8K 4-shot, the Qwen2.5 report's setting, for the two Qwen models"
for m in "Qwen/Qwen2.5-0.5B" "Qwen/Qwen2.5-1.5B"; do $RUN --model "$m" --profile check --tasks gsm8k --num-fewshot 4; done

echo "== stage 5: full ARC-Challenge 25-shot, the Qwen2.5 report's setting, for the two Qwen models (~26 min and ~1 h on MPS)"
for m in "Qwen/Qwen2.5-0.5B" "Qwen/Qwen2.5-1.5B"; do $RUN --model "$m" --profile check --tasks arc_challenge --num-fewshot 25; done

echo "== done"
