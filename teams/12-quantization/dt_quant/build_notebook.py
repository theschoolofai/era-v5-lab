#!/usr/bin/env python3
"""Build dt_on_quantized.ipynb (Kaggle) from dt_on_quantized.py and G10's dt/mask.py.

    python build_notebook.py

The notebook embeds its own copy of both files (mask.py is G10's, unchanged), makes a venv with pinned torch,
transformers and pyarrow (Kaggle's preinstalled torch has failed to import before: undefined symbol ncclCommShrink),
runs the arms one at a time and keeps one result file, so a stopped session resumes where it left off.
"""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = {"dt_on_quantized.py": HERE / "dt_on_quantized.py", "mask.py": HERE.parents[1] / "10-post-training" / "dt" / "mask.py"}


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(True)}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.strip("\n").splitlines(True)}


CELLS = [
md("""
# G12: Deletion Tuning on a quantized base (Kaggle)

Does G10's Deletion Tuning (mask over `gate_proj` weights, official recipe defaults) work on a Q8_0 or Q4_0 base as well
as on the unquantized model, and what does the quantized base save in memory? Arms: `base`, `base_q8_0`, `base_q4_0`
(no DT), `dt`, `dt_q8_0`, `dt_q4_0`, and `dt_then_q8_0` / `dt_then_q4_0` (DT first, quantize the baked weights after;
computed inside the `dt` run). Metric: held-out wikitext-2 NLL per token, with paired intervals over windows.
Details: `teams/12-quantization/dt_quant/dt_on_quantized.py` docstring.

**Smoke run first:** keep `STEPS = 4`, `TRAIN_WINDOWS = 16`, `TEST_WINDOWS = 8` and `ARMS = ["base", "dt_q8_0"]`; check that
both arms print an NLL. Then set the real values. Kaggle: Accelerator **GPU T4 x2**, Internet **on**. No token needed.
"""),
code("""
# --- settings -----------------------------------------------------------------------------------------------
RUN_BY        = ""                      # <-- your GitHub handle, recorded with the results
MODEL         = "Qwen/Qwen3-0.6B-Base"
REVISION      = None                    # <-- pin a commit of the model before the real run and write it in the report
ARMS          = ["base", "dt_q8_0"]     # real run: ["base","base_q8_0","base_q4_0","dt","dt_q8_0","dt_q4_0","dt_then_q8_0","dt_then_q4_0"]
STEPS         = 4                       # real run: 400
TRAIN_WINDOWS = 16                      # real run: 2000 (windows of LENGTH tokens)
TEST_WINDOWS  = 8                       # real run: 200
LENGTH        = 512
BATCH, MICRO  = 8, 2                    # rows per step, rows per forward (lower MICRO if out of memory)
SEED          = 1
TORCH         = "torch==2.11.0"         # CUDA 12.6 build, from the PyTorch index below
TORCH_INDEX   = "https://download.pytorch.org/whl/cu126"
NOTEBOOK_VERSION = "__NOTEBOOK_VERSION__"
"""),
code("""
import datetime, glob, json, os, shutil, subprocess, time
OUT = "/kaggle/working/dt_quant_out"; WORK = "/kaggle/tmp/dt_quant_work"; CODE = f"{WORK}/code"
for d in (OUT, f"{OUT}/logs", WORK, CODE):
    os.makedirs(d, exist_ok=True)

def sh(cmd, log=None):
    print("$", cmd, flush=True)
    full = f"set -o pipefail; ( {cmd} ) 2>&1" + (f" | tee -a {log}" if log else "")
    rc = subprocess.run(full, shell=True, executable="/bin/bash").returncode
    if rc != 0:
        raise RuntimeError(f"command failed (exit {rc}): {cmd}" + (f"; see {log}" if log else ""))

sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader")
sh("curl -fsS -o /dev/null https://huggingface.co || (echo 'NO INTERNET: turn it on in the notebook settings' && false)")
ENV = {"started": datetime.datetime.now().isoformat(timespec="seconds"), "run_by": RUN_BY, "notebook_version": NOTEBOOK_VERSION,
       "model": MODEL, "revision": REVISION}
"""),
"__SOURCE_CELL__",
code("""
# a venv with pinned packages (Kaggle's own torch can fail to import); GPU must be visible to it
VENV = f"{WORK}/venv"; PY = f"env -u PYTHONPATH {VENV}/bin/python"
if not os.path.exists(f"{VENV}/.ready"):
    sh(f"rm -rf {VENV} && pip install -q uv==0.13.6 && uv venv -q --python python3 {VENV} && "
       f"uv pip install -q --python {VENV}/bin/python {TORCH} --index-url {TORCH_INDEX} && "
       f"uv pip install -q --python {VENV}/bin/python transformers==4.57.6 pyarrow numpy accelerate && touch {VENV}/.ready",
       log=f"{OUT}/logs/venv.log")
probe = subprocess.run(f"{PY} -c \\"import torch, transformers, pyarrow, json; print(json.dumps(dict(torch=torch.__version__, "
                       f"cuda=torch.cuda.is_available(), transformers=transformers.__version__, pyarrow=pyarrow.__version__)))\\"",
                       shell=True, capture_output=True, text=True)
if probe.returncode != 0:
    raise RuntimeError("the venv does not work: " + probe.stderr[-3000:])
ENV["packages"] = json.loads(probe.stdout.strip().splitlines()[-1]); print(ENV["packages"])
if not ENV["packages"]["cuda"]:
    raise RuntimeError("torch cannot see the GPU: set TORCH_INDEX to https://download.pytorch.org/whl/cu128 and delete "
                       f"{VENV}, then rerun")
json.dump(ENV, open(f"{OUT}/environment.json", "w"), indent=1)
"""),
code("""
# the run: one result file; arms already in it are skipped, so a stopped session resumes
RUN = f"{OUT}/dt_quant_{MODEL.split('/')[-1]}_s{STEPS}_w{TRAIN_WINDOWS}"
os.makedirs(RUN, exist_ok=True)
RES = f"{RUN}/results.json"
rev = f"--revision {REVISION} " if REVISION else ""
sh(f"cd {CODE} && env HF_HOME={WORK}/hf {PY} -u dt_on_quantized.py --model {MODEL} {rev}--out {RES} --arms {','.join(ARMS)} "
   f"--steps {STEPS} --batch {BATCH} --micro {MICRO} --length {LENGTH} --train-windows {TRAIN_WINDOWS} "
   f"--test-windows {TEST_WINDOWS} --seed {SEED} --device cuda", log=f"{OUT}/logs/run.log")
"""),
code("""
# results: one table, a zip of everything
import pandas as pd
d = json.load(open(RES))
rows = []
for name, r in d["arms"].items():
    m = r["memory"]
    rows.append({"arm": name, "nll": round(r["test_nll_mean"], 4), "deleted_%": round(100 * r["deletion_final"], 3) if "deletion_final" in r else None,
                 "train_s": r.get("train_seconds"), "peak_cuda_GB": r.get("peak_cuda_gb"),
                 "decoder_weights_GB": round(m["weights_bytes"] / 1e9, 3), "dt_state_GB": round(m["dt_state_bytes"] / 1e9, 3),
                 "packed_GB_targeted": round(r["packed_bytes_targeted"] / 1e9, 3) if "packed_bytes_targeted" in r else None})
table = pd.DataFrame(rows); table.to_csv(f"{RUN}/table.csv", index=False)
print(table.to_string(index=False))
print("\\npaired NLL differences (mean over windows, 95% interval):")
for k, v in d.get("paired", {}).items():
    print(f"  {k}: {v['mean_diff']:+.4f}  [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]  ({v['windows']} windows)")
ENV["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
json.dump(ENV, open(f"{OUT}/environment.json", "w"), indent=1)
shutil.copy(f"{OUT}/environment.json", f"{RUN}/environment.json"); shutil.copytree(f"{OUT}/logs", f"{RUN}/logs", dirs_exist_ok=True)
zip_path = shutil.make_archive(RUN, "zip", RUN)
print("\\nEverything is in", RUN, "and", zip_path, "(Kaggle: the version's Output tab)")
"""),
]


def build() -> Path:
    src = {name: path.read_text() for name, path in SOURCES.items()}
    writer = ["# the code, embedded by build_notebook.py (mask.py is G10's dt/mask.py, unchanged)",
              "SOURCES = " + json.dumps(src, ensure_ascii=True, indent=0),
              "# dt_on_quantized.py reads ../10-post-training/dt/mask.py: recreate that layout",
              "os.makedirs(f\"{WORK}/teams/12-quantization/dt_quant\", exist_ok=True); os.makedirs(f\"{WORK}/teams/10-post-training/dt\", exist_ok=True)",
              "open(f\"{WORK}/teams/12-quantization/dt_quant/dt_on_quantized.py\", \"w\").write(SOURCES[\"dt_on_quantized.py\"])",
              "open(f\"{WORK}/teams/10-post-training/dt/mask.py\", \"w\").write(SOURCES[\"mask.py\"])",
              "CODE = f\"{WORK}/teams/12-quantization/dt_quant\"",
              "print(\"wrote\", sorted(SOURCES), \"under\", WORK)"]
    version = hashlib.sha256("".join(src[k] for k in sorted(src)).encode()).hexdigest()[:12]
    cells = [code("\n".join(writer)) if c == "__SOURCE_CELL__" else c for c in CELLS]
    for c in cells:
        c["source"] = [line.replace("__NOTEBOOK_VERSION__", version) for line in c["source"]]
    nb = {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python"}, "accelerator": "GPU"}}
    out = HERE / "dt_on_quantized.ipynb"
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    return out


if __name__ == "__main__":
    print("wrote", build())
