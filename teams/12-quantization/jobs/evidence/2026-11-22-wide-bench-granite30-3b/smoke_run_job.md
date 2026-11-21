# Smoke: prepare_inputs.py --tasks and run_job.py --tasks, offline (TO RUN BEFORE FILING)

Not run yet. Covers the `--tasks` option (new since the sarvam-1 smoke) and Granite's conversion through `run_job.py`.

## Kaggle cells (T4 x2, Internet on; no HF_TOKEN needed), after eval_wide.ipynb's setup cells

```python
# 1. fresh code (with --tasks) and staging, with network
LAB = f"{WORK}/lab"
sh(f"rm -rf {LAB} && git clone -q --depth 1 --branch g12-week4-wide-bench https://github.com/SomaKorada07/era-v5-lab {LAB}")
sh(f"cd {LAB} && env -u HF_TOKEN {EVAL_PY} teams/12-quantization/eval_wide/prepare_inputs.py --tasks mmlu arc_challenge "
   f"--hf-home {WORK}/inputs/hf_home_g --model-dir {WORK}/inputs/granite-3.0-3b-a800m-base "
   f"--model ibm-granite/granite-3.0-3b-a800m-base --revision 142d2c8e3f7fb8844011cfa5565f0e520f0824b9",
   log=f"{OUT}/logs/smoke_g_prepare.log")
```

```python
# 2. the job command in the background (Kaggle's display can stop refreshing), empty work folder: convert runs
import subprocess, os
os.makedirs(f"{WORK}/job_g", exist_ok=True)
log = open(f"{OUT}/logs/smoke_g_run_job.log", "w")
env = {k: v for k, v in os.environ.items() if k not in ("HF_TOKEN", "PYTHONPATH")}
JOB = subprocess.Popen([
    f"{WORK}/eval-venv/bin/python", "teams/12-quantization/eval_wide/run_job.py",
    "--model-dir", f"{WORK}/inputs/granite-3.0-3b-a800m-base", "--hf-home", f"{WORK}/inputs/hf_home_g",
    "--llama-dir", f"{WORK}/llama.cpp", "--convert-python", f"{WORK}/convert-venv/bin/python", "--quantize", QUANTIZE,
    "--formats", "bf16", "Q4_K_M", "--tasks", "mmlu", "arc_challenge", "--cap", "2",
    "--work", f"{WORK}/job_g", "--out", f"{OUT}/smoke_g_out",
    "--model", "ibm-granite/granite-3.0-3b-a800m-base", "--revision", "142d2c8e3f7fb8844011cfa5565f0e520f0824b9"],
    cwd=LAB, env=env, stdout=log, stderr=subprocess.STDOUT)
print("started, pid", JOB.pid)
```

```python
# 3. check (repeat until exit code 0)
print("exit code:", JOB.poll())
!tail -3 {OUT}/logs/smoke_g_run_job.log
!cat {OUT}/smoke_g_out/job.json
```

## Result

- prepare_inputs.py, online pass (items per task):
- prepare_inputs.py, offline check: PASS / FAIL
- run_job.py exit code, steps (`job.json`):
- GGUF sha256 (bf16, Q4_K_M):
- paired.md:
