# Phi-3-mini-4k-instruct, bf16 vs Q4_K_M (eval_mini)

Run by shishir13 on Kaggle 2xT4, 2 Nov 2026, with `eval_mini.ipynb` (settings cell only: `MODEL`, `REVISION`, `FORMATS`, `RUN_BY`,
`LIMIT = None`), llama.cpp b11669, llama-cpp-python 0.3.36. Model `microsoft/Phi-3-mini-4k-instruct`, revision `f39ac1d28e92`.

Two differences from the OLMoE runs:
- `TOL` in check 3 of `test_llamacpp_lm.py` is 0.10, not 0.05: Q4_K_M had a cache-vs-fresh difference of 0.0786. Checks 1 and 2 passed
  (`log p(' Paris')` -0.095 = generation -0.095). So `NOTEBOOK_VERSION` is `ec7db60966d6+phi3tol0.10` and these runs must not be combined with the OLMoE ones.
- `run_meta.model` and `run_meta.model_revision` in the two `summary.json` files say OLMoE: `run_mini_gguf.py` writes the OLMoE default.
  The model that ran is in `environment.json` (`settings.MODEL`) and in `run_meta.gguf`.

The per-item `*.samples.jsonl` files are not committed (about 1.6 MB zipped); they are in the Kaggle version's Output.
