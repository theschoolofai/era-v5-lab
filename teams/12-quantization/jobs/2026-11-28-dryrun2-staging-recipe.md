# Dry run 2 quantize job: staging recipe (G12, 28 Nov 2026)

Unblocks `jobs/2026-11-27-dryrun2-quantize-eval.md` (#862). One command stages everything that job needs with network;
a second command checks it offline.

```bash
python teams/12-quantization/scripts/stage_dryrun_inputs.py all --inputs ./inputs --work ./work --cuda   # drop --cuda on CPU
python teams/12-quantization/scripts/stage_dryrun_inputs.py check --inputs ./inputs --work ./work \
    --tokenizer ./inputs/tokenizer.json --model ./inputs/dryrun2-1234/model.safetensors
```

Steps can be run alone: `sources`, `llama`, `venv`, `check`.

## What each step does

| Step | Result | Verified how |
|---|---|---|
| sources | 25 `code_contests` files (4.83 GB) and 6 `hendrycks_math` files (2.7 MB) under `inputs/<source>/`, at the manifest revision | sha256 of every file against `effort_manifest.json`; a mismatch deletes the file and fails |
| llama | llama.cpp `b11669` (`620d2225cc43...`) in `work/llama.cpp-b11669`, binaries in `build/bin` | HEAD read from `.git/HEAD` must equal the pinned commit; `check` runs `llama-server --version` and needs build 11669 |
| venv | `work/.venv-convert`: Python 3.12, b11669's convert requirements (transformers 4.57.6), gguf-py, `pyarrow<19` | `check` imports the package versions |
| check | PASS/FAIL per item, no network, exit 1 on any FAIL | |

## Why the build flags matter

The build passes `-DLLAMA_BUILD_NUMBER=11669 -DLLAMA_BUILD_COMMIT=620d222`. A shallow clone has no tag history, so without them
the binaries report build 1. `quantize_eval.py` then cannot match `work/llama.cpp-b11669` by build number and falls back to
`git ls-remote`, which needs network and fails on an offline node.

## Corrections to the job file

- `2026-11-18-dryrun1-quantize-eval.md` (which the dry run 2 job points to for staging) lists 24 `code_contests` and 7 `hendrycks_math` files. The manifest resolves **25 and 6** (4.83 GB for the 25 `code_contests` files; the job says about 4.6 GB); the counts are corrected in #885.
- Files sit under `data/` for `code_contests` and at the dataset root for `hendrycks_math`; the script tries both.

## Evidence

- Sources, 28 Nov: all 6 `hendrycks_math` files and 1 `code_contests` file (205 MB) downloaded and matched their pinned
  sha256; the other 24 `code_contests` files were checked reachable, not downloaded in full.
- Script tests: `scripts/test_stage_dryrun_inputs.py`, 6 pass.
- Not yet run end to end by me: the `llama` build and `venv` steps (the b11669 sources are on disk, the build is not done).
  Whoever stages the node should paste the `check` output into the job's evidence.
