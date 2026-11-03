# MILU task configs (vendored)

These files are copied unchanged from `lm_eval/tasks/milu/` in https://github.com/AI4Bharat/MILU (branch `master`, fetched 25 Oct 2026).
That repository is a fork of EleutherAI's lm-evaluation-harness (version 0.4.4) and is under the MIT License, Copyright (c) 2020 EleutherAI.

They are loaded into lm-evaluation-harness 0.4.13 with `--include_path tasks`.

The dataset `ai4bharat/MILU` is gated on Hugging Face (CC BY 4.0). Accept its terms and log in with `hf auth login` before running these tasks.
The published scores we compare against (MILU paper, arXiv 2411.02538, Table 3) are 5-shot: pass `--num_fewshot 5`.
