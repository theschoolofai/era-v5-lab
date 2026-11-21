# Smoke: run_job.py and prepare_inputs.py, offline (TO RUN BEFORE FILING)

Not run yet. Fill in after the Kaggle smoke below; TSAI does not run a script with no test log.

## Kaggle cell (T4 x2, Internet on, HF_TOKEN secret), after eval_wide.ipynb's setup cells

```python
import os
from kaggle_secrets import UserSecretsClient
LAB = f"{WORK}/lab"   # full clone of the branch with eval_wide/
sh(f"git clone -q --depth 1 --branch g12-week4-wide-bench https://github.com/SomaKorada07/era-v5-lab {LAB}")
os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")   # via the environment: sh() echoes commands
# 1. staging, with network and the token
sh(f"cd {LAB} && {EVAL_PY} teams/12-quantization/eval_wide/prepare_inputs.py "
   f"--hf-home {WORK}/inputs/hf_home --model-dir {WORK}/inputs/sarvam-1 "
   f"--model sarvamai/sarvam-1 --revision e9607337286ddf496d4a2562b194e489dcf3feea", log=f"{OUT}/logs/smoke_prepare.log")
# 2. the job command, no token, offline env set by run_job.py, 2 items per task, two formats
sh(f"cd {LAB} && env -u HF_TOKEN {EVAL_PY} teams/12-quantization/eval_wide/run_job.py "
   f"--model-dir {WORK}/inputs/sarvam-1 --hf-home {WORK}/inputs/hf_home --llama-dir {WORK}/llama.cpp "
   f"--convert-python {WORK}/convert-venv/bin/python --quantize {QUANTIZE} --formats bf16 Q4_K_M "
   f"--work {WORK}/job_work --out {OUT}/smoke_out --cap 2 "
   f"--model sarvamai/sarvam-1 --revision e9607337286ddf496d4a2562b194e489dcf3feea", log=f"{OUT}/logs/smoke_run_job.log")
```

## Result

- prepare_inputs.py, online pass: (items per task)
- prepare_inputs.py, offline check: PASS / FAIL
- run_job.py exit code, time:
- job.json steps:
- paired.md:
