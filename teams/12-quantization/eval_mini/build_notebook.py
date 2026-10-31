#!/usr/bin/env python3
"""Build eval_mini.ipynb (Kaggle or Colab) from the .py files next to it.

    python build_notebook.py

The notebook carries its own copy of llamacpp_lm.py, run_mini_gguf.py and paired.py (written to disk by its
first code cell), so it runs without this branch being pushed. The .py files stay the source of truth: edit
them, then rebuild. G9's run_eval_mini.py is still fetched from upstream main, where it is published.

Local test (same cells, no GPU box): EVAL_MINI_LOCAL_TEST=1 jupyter nbconvert --execute eval_mini.ipynb
uses the GGUFs in ~/.cache/era-v5-quant, two formats and a few items per task.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = ["llamacpp_lm.py", "run_mini_gguf.py", "paired.py", "test_llamacpp_lm.py"]


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(True)}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": s.strip("\n").splitlines(True)}


CELLS = [
md("""
# G12: G9's eval_mini on OLMoE GGUF files (Kaggle or Colab)

Runs G9's **mini** profile (ARC-C 500, HellaSwag 400, MMLU 570, GSM8K 200, TruthfulQA-mc2 200; G9's shots, limits
and seed) on **bf16 and six llama.cpp formats**, all through one backend (llama-cpp-python in-process; see
`llamacpp_lm.py` for why not llama-server), with **per-item logs**, then compares each format with bf16 item by
item (`paired.py`).

**Team run (G12):** bf16 is done (Kaggle, 28 Oct). Each member runs the formats assigned to them: set `FORMATS` and
`RUN_BY` in the settings cell, nothing else. Send the zip back; `combine.py` checks that every run used identical code
and settings (the `NOTEBOOK_VERSION` fingerprint, model revision, llama.cpp build, lm_eval, seed, item counts) and
compares every format with bf16 item by item.

Every step stops the run if it fails. The notebook detects where it runs:

- **Kaggle:** Settings → Accelerator **GPU T4 x2**, Internet **on**. For the full run use **Save Version → Save & Run
  All (Commit)**: it runs in the background (up to 12 h) and `/kaggle/working/eval_mini_out/` becomes the version's
  downloadable Output. Model files go to `/kaggle/tmp` (outside the 20 GB output limit).
- **Colab:** T4 runtime, Run all. Output to Google Drive if it mounts (then a second session reuses the compiled
  build and skips finished tasks), else to the runtime, with the zip also printed by the last cell.
- Time on Kaggle 2×T4: ~35 min to compile llama-cpp-python and convert the model, then ~25-45 min per format
  (bf16 took 45 min). Two formats ≈ 2 h. `LIMIT = 5` gives a quick end-to-end check first if you want one.
"""),
code("""
# --- settings -----------------------------------------------------------------------------------------------
FORMATS   = ["Q8_0", "Q6_K"]   # <-- YOUR assigned formats (bf16 is already done; see the team table in README.md)
RUN_BY    = ""                 # <-- your GitHub handle, recorded with the results
LIMIT     = None               # None = G9's full mini profile; 5 = quick end-to-end check (not combinable)
BASE      = "bf16"             # paired comparison is made against this when it is in the same run (combine.py otherwise)
MODEL, REVISION = "allenai/OLMoE-1B-7B-0924", "6d84c48581ece794365f2b8e9cfb043c68ade9c5"  # team pin
LLAMA_TAG = "b11669"           # llama.cpp build of the team's conversion/quantization
LLAMA_CPP_PYTHON = "0.3.36"    # in-process log-probabilities checked correct with this version
G9_RAW = "https://raw.githubusercontent.com/theschoolofai/era-v5-lab/main/teams/09-evaluation/harness/run_eval_mini.py"
DRIVE_DIR = "/content/drive/MyDrive/era-v5-g12/eval_mini"   # Colab, when Drive mounts
BF16_FALLBACK_GPU_LAYERS = 12  # of 16 layers, only if bf16 does not fit on the GPU(s)
NOTEBOOK_VERSION = "__NOTEBOOK_VERSION__"   # fingerprint of the embedded code: combine.py requires the same one
assert FORMATS and all(f in {"bf16", "Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M", "Q3_K_M", "Q2_K"} for f in FORMATS), FORMATS

import os
if os.environ.get("EVAL_MINI_LOCAL_TEST"):   # dry run of these same cells on a Mac (see build_notebook.py)
    LIMIT, FORMATS, BASE, RUN_BY = 2, ["Q8_0", "Q2_K"], "Q8_0", "local-test"
"""),
code("""
import datetime, glob, json, os, platform, shutil, subprocess, sys, time
LOCAL_TEST = bool(os.environ.get("EVAL_MINI_LOCAL_TEST"))
IN_KAGGLE = os.path.isdir("/kaggle/working")
try:
    import google.colab  # noqa: F401
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

if LOCAL_TEST:
    LOCAL_OUT, WORK = os.environ.get("EVAL_MINI_OUT", "/tmp/eval_mini_local"), os.path.expanduser("~/.cache/era-v5-quant")
elif IN_KAGGLE:
    LOCAL_OUT, WORK = "/kaggle/working/eval_mini_out", "/kaggle/tmp/eval_mini_work"   # output vs big files
else:
    LOCAL_OUT, WORK = "/content/eval_mini_out", "/content/work"
OUT = LOCAL_OUT
if IN_COLAB:
    try:
        from google.colab import drive
        drive.mount("/content/drive")
        OUT = DRIVE_DIR
    except Exception as e:  # e.g. not available from an editor-attached runtime
        print(f"Drive not mounted ({e!r}); output goes to {LOCAL_OUT}. DOWNLOAD THE ZIP AT THE END.")
for d in (OUT, f"{OUT}/logs", WORK):
    os.makedirs(d, exist_ok=True)
CODE = f"{WORK}/eval_mini_code"; os.makedirs(CODE, exist_ok=True)

def sh(cmd, log=None):
    \"\"\"Run a shell command; stream its output (and append it to a log); stop the notebook if it fails.\"\"\"
    print("$", cmd, flush=True)
    full = f"set -o pipefail; ( {cmd} ) 2>&1" + (f" | tee -a {log}" if log else "")
    rc = subprocess.run(full, shell=True, executable="/bin/bash").returncode
    if rc != 0:
        raise RuntimeError(f"command failed (exit {rc}): {cmd}" + (f"; see {log}" if log else ""))

PLATFORM = "local-test" if LOCAL_TEST else "kaggle" if IN_KAGGLE else "colab" if IN_COLAB else "other"
ENV = {"started": datetime.datetime.now().isoformat(timespec="seconds"), "platform": PLATFORM,
       "output_dir": OUT, "run_by": RUN_BY, "notebook_version": NOTEBOOK_VERSION,
       "settings": {k: globals()[k] for k in ("LIMIT", "FORMATS", "BASE", "MODEL", "REVISION",
       "LLAMA_TAG", "LLAMA_CPP_PYTHON", "BF16_FALLBACK_GPU_LAYERS")}, "python": platform.python_version(), "formats": {}}
def save_env():
    json.dump(ENV, open(f"{OUT}/environment.json", "w"), indent=1)
if shutil.which("nvidia-smi"):
    ENV["gpu"] = subprocess.run("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader",
                                shell=True, capture_output=True, text=True).stdout.strip()
    sh("nvidia-smi")
sh(f"df -h {WORK} | tail -1")
if not LOCAL_TEST:   # Kaggle needs Internet switched on in the notebook settings
    sh("curl -fsS -o /dev/null https://huggingface.co || (echo 'NO INTERNET: turn it on in the notebook settings' && false)")
save_env()
print("platform:", PLATFORM, "| output:", OUT, "| model files:", WORK)
"""),
"__SOURCE_CELL__",
code("""
# llama-cpp-python with CUDA (compiled here, ~10-25 min). The wheel is kept where it survives a new session
# (Colab: Drive), so a later session installs it in seconds.
# GGML_CUDA_NO_VMM: Kaggle's build image has no libcuda for CMake to link (found by therahulbhati, perplexity/README.md).
#
# The evaluation runs in its OWN venv (EVAL_PY) holding only llama-cpp-python, lm_eval and datasets at G9's pins.
# lm_eval imports torch and transformers whenever it finds them, and Kaggle's preinstalled ones fail to import
# (torch: undefined symbol ncclCommShrink; transformers: a dependency version check). This venv has neither.
if LOCAL_TEST:
    LLAMA_SPEC, UV_PYTHON = f"llama-cpp-python=={LLAMA_CPP_PYTHON}", "3.12"   # uv builds it (Metal on a Mac)
else:
    UV_PYTHON = "python3"   # the platform's python, the one the wheel is built for
    sh("pip install -q uv==0.13.6", log=f"{OUT}/logs/pip.log")
    WHEELS = f"{OUT}/wheels" if OUT == DRIVE_DIR else f"{WORK}/wheels"
    wheels = glob.glob(f"{WHEELS}/llama_cpp_python-{LLAMA_CPP_PYTHON}-*.whl")
    if not wheels:
        os.makedirs(WHEELS, exist_ok=True)
        caps = sorted({c.replace(".", "") for c in subprocess.run("nvidia-smi --query-gpu=compute_cap --format=csv,noheader",
                       shell=True, capture_output=True, text=True).stdout.split()}) or ["75"]
        ENV["cuda_arch"] = caps; save_env()
        # -v makes the build print ninja's [done/total] counter; the full output goes to the log, the counter here
        build_log = f"{OUT}/logs/build_llama_cpp_python.log"
        print("compiling llama-cpp-python with CUDA: ~15-30 min; progress every ~20 kernels below")
        sh(f'CMAKE_ARGS="-DGGML_CUDA=on -DGGML_CUDA_NO_VMM=ON -DCMAKE_CUDA_ARCHITECTURES={";".join(caps)}" '
           f'pip wheel -v --no-deps --no-cache-dir -w {WHEELS} llama-cpp-python=={LLAMA_CPP_PYTHON} 2>&1 '
           f'| tee {build_log} | grep --line-buffered -E "^ *[[][0-9]+/[0-9]+[]]" | awk "NR % 20 == 1 {{print; fflush()}}" ; '
           f'ls {WHEELS}/llama_cpp_python-*.whl >/dev/null || (tail -40 {build_log}; false)')
        wheels = glob.glob(f"{WHEELS}/llama_cpp_python-{LLAMA_CPP_PYTHON}-*.whl")
    LLAMA_SPEC = wheels[0]

EVAL_VENV = f"{WORK}/eval-venv"
EVAL_PY = f"env -u PYTHONPATH {EVAL_VENV}/bin/python"   # also without Kaggle's PYTHONPATH sitecustomize hook
if not os.path.exists(f"{EVAL_VENV}/.ready"):
    sh(f"rm -rf {EVAL_VENV} && uv venv -q --python {UV_PYTHON} {EVAL_VENV} && uv pip install -q --python {EVAL_VENV}/bin/python "
       f"{LLAMA_SPEC} lm_eval==0.4.13 datasets==5.1.0 && touch {EVAL_VENV}/.ready", log=f"{OUT}/logs/eval_venv.log")
probe = f"{CODE}/probe_env.py"
open(probe, "w").write(os.linesep.join([
    "import importlib.util, json, llama_cpp, lm_eval, datasets, platform",
    "print(json.dumps({'python': platform.python_version(), 'llama_cpp_python': llama_cpp.__version__,",
    "  'lm_eval': lm_eval.__version__, 'datasets': datasets.__version__,",
    "  'gpu_offload': bool(llama_cpp.llama_supports_gpu_offload()),",
    "  'torch_visible': importlib.util.find_spec('torch') is not None,",
    "  'transformers_visible': importlib.util.find_spec('transformers') is not None}))", ""]))
res = subprocess.run(f"{EVAL_PY} {probe}", shell=True, capture_output=True, text=True)
if res.returncode != 0:
    raise RuntimeError("the evaluation venv does not work: " + res.stderr[-3000:])
ENV["packages"] = json.loads(res.stdout.strip().splitlines()[-1])
if not LOCAL_TEST and not ENV["packages"]["gpu_offload"]:
    raise RuntimeError("llama-cpp-python has no GPU offload: delete the wheels folder and rerun to rebuild it with CUDA")
if ENV["packages"]["torch_visible"] or ENV["packages"]["transformers_visible"]:
    raise RuntimeError(f"torch/transformers visible in the evaluation venv: {ENV['packages']}")
save_env(); print(ENV["packages"])
"""),
code("""
# G9's runner (profile, task list, record format) from upstream main; its sha256 goes into every summary
sh(f"curl -fsSL {G9_RAW} -o {CODE}/run_eval_mini.py")
sys.path.insert(0, CODE)
"""),
code("""
# bf16 GGUF: the llama.cpp converter at the team's build, pinned checkpoint; llama-quantize built CPU-only (~5 min)
NAME = MODEL.split("/")[-1]
BF16 = f"{WORK}/{NAME}-bf16.gguf"
QUANTIZE = shutil.which("llama-quantize") if LOCAL_TEST else f"{WORK}/llama.cpp/build/bin/llama-quantize"
if not LOCAL_TEST and not os.path.exists(QUANTIZE):
    if not os.path.exists(f"{WORK}/llama.cpp"):
        sh(f"git clone -q --depth 1 --branch {LLAMA_TAG} https://github.com/ggml-org/llama.cpp {WORK}/llama.cpp")
    sh(f"cmake -S {WORK}/llama.cpp -B {WORK}/llama.cpp/build -DLLAMA_CURL=OFF -DGGML_CUDA=OFF "
       f"&& cmake --build {WORK}/llama.cpp/build -j --target llama-quantize", log=f"{OUT}/logs/build_llama_quantize.log")
if not os.path.exists(BF16):
    # the converter's own requirements (pinned torch, numpy, ...) go into a separate venv, so they cannot replace
    # packages this notebook has already imported
    CONV = f"{WORK}/convert-venv"
    if not os.path.exists(f"{CONV}/.ready"):   # uv: Kaggle's python has no ensurepip, so plain venv fails
        sh(f"rm -rf {CONV} && pip install -q uv==0.13.6 && uv venv -q --python python3 {CONV} "
           f"&& uv pip install -q --python {CONV}/bin/python --index-strategy unsafe-best-match "
           f"-r {WORK}/llama.cpp/requirements/requirements-convert_hf_to_gguf.txt {WORK}/llama.cpp/gguf-py "
           f"&& touch {CONV}/.ready", log=f"{OUT}/logs/convert_venv.log")
    from huggingface_hub import snapshot_download
    hf = snapshot_download(MODEL, revision=REVISION, local_dir=f"{WORK}/hf",
                           allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt"])
    # env -u PYTHONPATH: Kaggle injects a sitecustomize hook through PYTHONPATH that needs packages this venv lacks
    sh(f"env -u PYTHONPATH {CONV}/bin/python {WORK}/llama.cpp/convert_hf_to_gguf.py {hf} --outtype bf16 --outfile {BF16}",
       log=f"{OUT}/logs/convert.log")
    shutil.rmtree(f"{WORK}/hf", ignore_errors=True)
ENV["bf16_gguf_bytes"] = os.path.getsize(BF16); save_env()
print(BF16, round(os.path.getsize(BF16) / 1e9, 2), "GB")
"""),
code("""
# every format: quantize (same rule as scripts/quantize_eval.py: output layer Q8_0 below 8 bits), run G9's profile,
# save after each task. A format whose five tasks are all in its summary.json is skipped.
TASKS = ["arc_challenge", "hellaswag", "mmlu", "gsm8k", "truthfulqa_mc2"]
RUNS = f"{OUT}/runs_" + "-".join(FORMATS) + (f"_limit{LIMIT}" if LIMIT else "")   # unique per member; tests apart

def finished(fmt):
    p = f"{RUNS}/{fmt}/summary.json"
    return os.path.exists(p) and {r["task"] for r in json.load(open(p))["records"]} >= set(TASKS)

def run_format(fmt, gguf, gpu_layers):
    sh(f"cd {CODE} && {EVAL_PY} run_mini_gguf.py --gguf {gguf} --format {fmt} --out {RUNS} "
       f"--g9-harness {CODE}/run_eval_mini.py --n-gpu-layers {gpu_layers}" + (f" --limit {LIMIT}" if LIMIT else ""),
       log=f"{OUT}/logs/run_{fmt}.log")

for fmt in FORMATS:
    if finished(fmt):
        print(f"{fmt}: all tasks done, skipped"); continue
    t0 = time.time()
    gguf = BF16 if fmt == "bf16" else f"{WORK}/{NAME}-{fmt}.gguf"
    made_here = False
    if not os.path.exists(gguf):
        extra = "" if fmt == "Q8_0" else "--output-tensor-type q8_0"
        sh(f"{QUANTIZE} {extra} {BF16} {gguf} {fmt}", log=f"{OUT}/logs/quantize_{fmt}.log"); made_here = True
    # the shifted-logprob guard (instructor, 28 Oct): this file's scores must equal its own greedy generation's
    sh(f"cd {CODE} && {EVAL_PY} test_llamacpp_lm.py {gguf}", log=f"{OUT}/logs/test_llamacpp_lm_{fmt}.log")
    gpu_layers = -1
    try:
        run_format(fmt, gguf, gpu_layers)
    except RuntimeError:
        # retry with fewer GPU layers only for bf16 and only when the failure was GPU memory; anything else is a bug
        tail = open(f"{OUT}/logs/run_{fmt}.log").read()[-20000:].lower()
        if fmt != "bf16" or not any(k in tail for k in ("out of memory", "failed to allocate", "cudamalloc")):
            raise
        gpu_layers = BF16_FALLBACK_GPU_LAYERS
        print(f"bf16 ran out of GPU memory with all layers on the GPU; retrying with {gpu_layers} GPU layers")
        run_format(fmt, gguf, gpu_layers)
    ENV["formats"][fmt] = {"gpu_layers": gpu_layers, "gguf_bytes": os.path.getsize(gguf),
                           "wall_clock_s": round(time.time() - t0), "finished": datetime.datetime.now().isoformat(timespec="seconds")}
    save_env()
    if made_here and fmt != "bf16" and not LOCAL_TEST:
        os.remove(gguf)   # keep the local disk small
"""),
code("""
# results: G9-primary scores per format, the paired comparison with the base, a zip of everything
import pandas as pd
rows = []
for p in sorted(glob.glob(f"{RUNS}/*/summary.json")):
    s = json.load(open(p))
    for r in s["records"]:
        if r["primary"]:
            rows.append({"format": s["run_meta"]["format"], "task": r["task"], "points": round(100 * r["value"], 1),
                         "stderr": round(100 * (r["stderr"] or 0), 1), "n": r["n_items"], "seconds": r["wall_clock_s"]})
long = pd.DataFrame(rows)
long.to_csv(f"{RUNS}/scores_long.csv", index=False)
scores = long.pivot_table(index="format", columns="task", values="points").reindex([f for f in FORMATS if f in set(long.format)])
scores.to_csv(f"{RUNS}/scores.csv")
print(scores.to_string())
if os.path.exists(f"{RUNS}/{BASE}/summary.json"):
    sh(f"{EVAL_PY} {CODE}/paired.py {RUNS} --base {BASE} --out {RUNS}/paired.md")
else:
    print(f"{BASE} is not in this run: the paired comparison is made when the runs are combined (combine.py)")
ENV["finished"] = datetime.datetime.now().isoformat(timespec="seconds"); save_env()
shutil.copy(f"{OUT}/environment.json", f"{RUNS}/environment.json")
shutil.copytree(f"{OUT}/logs", f"{RUNS}/logs", dirs_exist_ok=True)
zip_path = shutil.make_archive(RUNS, "zip", RUNS)
print("\\nEverything is in", RUNS, "and", zip_path)
n_files = sum(len(f) for _, _, f in os.walk(RUNS)); print(n_files, "files:", sorted(os.listdir(RUNS)))
"""),
code("""
# Colab without Drive only: the zip as base64 text in this cell's output, so it survives the runtime (e.g. a
# Colab kernel attached from VS Code: files stay on Google's VM, cell outputs are saved with the notebook).
# Locally: python extract_results.py eval_mini.ipynb  -> writes the zip next to the notebook.
import base64
if IN_COLAB and OUT != DRIVE_DIR:
    blob = base64.b64encode(open(zip_path, "rb").read()).decode()
    print(f"EVAL_MINI_ZIP_BEGIN {os.path.basename(zip_path)} {len(blob)}")
    for i in range(0, len(blob), 4000):
        print(blob[i:i + 4000])
    print("EVAL_MINI_ZIP_END")
else:
    print("results:", zip_path, "(Kaggle: the version's Output tab; Colab with Drive: the Drive folder)")
"""),
md("""
## Send back

**Kaggle:** download `eval_mini_out/runs*.zip` from the version's Output tab. **Colab with Drive:** it is in the
Drive folder. **Colab without Drive:** save the notebook, then locally `python extract_results.py eval_mini.ipynb`.
The zip is named after your formats (e.g. `runs_Q8_0-Q6_K.zip`); send it to the person combining the results.
It holds per format a `summary.json`
(G9's record format) and one `*.samples.jsonl` per task; `scores.csv`, `scores_long.csv`, `paired.md`,
`environment.json` (GPU, versions, settings, per-format GPU layers and time) and `logs/`. From Drive, or if Drive
did not mount, download it from the runtime before the session ends.
"""),
]


def build() -> Path:
    src = {name: (HERE / name).read_text() for name in SOURCES}
    writer = ["# the evaluation code (llamacpp_lm.py, run_mini_gguf.py, paired.py), embedded by build_notebook.py",
              "SOURCES = " + json.dumps(src, ensure_ascii=True, indent=0),
              "for _name, _text in SOURCES.items():",
              "    open(f\"{CODE}/{_name}\", \"w\").write(_text)",
              "print(\"wrote\", sorted(SOURCES), \"to\", CODE)"]
    import hashlib
    version = hashlib.sha256(("".join(src[k] for k in sorted(src)) + Path(__file__).read_text()).encode()).hexdigest()[:12]
    cells = [code("\n".join(writer)) if c == "__SOURCE_CELL__" else c for c in CELLS]
    for c in cells:
        c["source"] = [line.replace("__NOTEBOOK_VERSION__", version) for line in c["source"]]
    nb = {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python"}, "accelerator": "GPU",
                       "colab": {"provenance": [], "gpuType": "T4"}}}
    out = HERE / "eval_mini.ipynb"
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    return out


if __name__ == "__main__":
    print("wrote", build())
