#!/usr/bin/env python3
"""Build rollout_vllm.ipynb (Kaggle or Colab): vLLM as the rollout sampler, W4A16 GPTQ against the vLLM baseline, scored by PyTorch.

    python build_vllm_notebook.py

Team 10 asked for the path they would run on a GPU: vLLM sampling a W4A16 (GPTQ) copy, scored against the PyTorch bf16
reference. The recipe is Team 12's week-2 GPU path (gpu_path/): llm-compressor 0.15.0 GPTQ W4A16 (group 128, lm_head kept
in bf16) and vLLM 0.33.0, each in its own environment. New here: the sampler stage (quant_rollout_vllm.py, same dump as the
llama.cpp stage), a check for a dense model's packed layers, and the PyTorch scoring stage (score_with_torch.py).
The notebook embeds its own copy of the code, so it runs without a branch being pushed.
"""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = {"quant_rollout_vllm.py": HERE / "quant_rollout_vllm.py", "quant_rollout_mismatch.py": HERE / "quant_rollout_mismatch.py",
           "score_with_torch.py": HERE / "score_with_torch.py", "check_dense_w4a16.py": HERE / "check_dense_w4a16.py",
           "quantize_w4a16.py": HERE.parent / "gpu_path" / "quantize_w4a16.py", "fixed_100.jsonl": HERE.parent / "prompts" / "fixed_100.jsonl"}


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n").splitlines(True)}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.strip("\n").splitlines(True)}


CELLS = [
md("""
# G12: vLLM W4A16 rollouts against a PyTorch bf16 reference

Team 10's question for the live GRPO run: how far is a vLLM sampler on a W4A16 (GPTQ) copy of the policy from the PyTorch bf16
model that trains it? Formats: the vLLM baseline (`vllm_fp16` on a T4, `vllm_bf16` on an L4 or A100) and `vllm_W4A16`; both are
sampled at temperature 1 and scored by the same PyTorch bf16 reference. The llama.cpp Q8_0 row comes from `rollout_mismatch.ipynb`
(same model, same prompts); the note generator puts them side by side.

**Read first**
- vLLM decodes all prompts and samples at once, so tokens/s is a **batched throughput**, not the single-stream speed of the llama.cpp rows.
- A **T4 has no bf16 compute**, so vLLM runs fp16 there; the reference is bf16, so the baseline row includes the fp16-against-bf16 gap.
  For the exact bf16 GPU path use an L4 or A100 (Colab) with `VLLM_DTYPE = "bfloat16"`.
- vLLM's W4A16 kernels may not load on a T4 (week 2 found Marlin MoE needs compute capability 8.0). If W4A16 fails to load, rerun on an L4 or A100.
- GPTQ is calibrated on web text (fineweb-edu), as in week 2, not on code: the quantization of a code model may suffer for that reason.

**Smoke first:** keep `SMOKE = True`, `N = 5`, `K = 2`, `MAX_NEW = 32`. Kaggle: Accelerator **GPU T4 x2**, Internet **on**. Then set `SMOKE = False`,
`N = 50`, `K = 8`, `MAX_NEW = 256`. No token is needed (the model is public, Apache-2.0).
"""),
code("""
# --- settings -----------------------------------------------------------------------------------------------
RUN_BY        = ""                    # <-- your GitHub handle, recorded with the results
MODEL, REVISION = "Qwen/Qwen2.5-Coder-1.5B", "df3ce67c0e24480f20468b6ef2894622d69eb73b"
LAYERS        = 28                    # decoder layers of this model; the packed-linear check expects 7 x LAYERS
PROMPTS       = "balanced"            # "balanced" = N prompts round-robin over english / indic / code / tool_call / reasoning; "first" = the first N
N, K, MAX_NEW = 5, 2, 32              # smoke; real run: 50, 8, 256
EPS, SEED     = 0.2, 1234
SMOKE         = True                  # GPTQ calibration: True = 32 samples x 512 tokens (tests the pipeline); False = 256 x 1024
METHOD        = "gptq"                # or "rtn" (no calibration) if GPTQ fails
FORMATS       = ["base", "W4A16"]     # base = the unquantized model in vLLM
VLLM_DTYPE    = "half"                # T4 has no bf16 compute: "half". On an L4 or A100: "bfloat16"
VLLM_UTIL     = 0.80                  # share of GPU memory vLLM may take
# pinned to the versions of week 2 (gpu_path/results/environment.json)
QUANT_PKGS    = ["llmcompressor==0.15.0", "compressed-tensors==0.20.1", "datasets==5.1.0"]
VLLM_PKGS     = ["vllm==0.33.0"]
TORCH_REFERENCE = True                # stage 2: score the same tokens with the HF model in PyTorch
TORCH_DTYPE   = "bfloat16"
TORCH         = "torch==2.11.0"
TORCH_INDEX   = "https://download.pytorch.org/whl/cu126"
NOTEBOOK_VERSION = "__NOTEBOOK_VERSION__"
assert PROMPTS in ("balanced", "first") and all(f in ("base", "W4A16") for f in FORMATS), (PROMPTS, FORMATS)
"""),
code("""
import datetime, glob, json, os, shutil, subprocess, sys, time
from pathlib import Path
KAGGLE = Path("/kaggle").exists()
WORK = Path("/kaggle/working" if KAGGLE else "/content"); TMP = Path("/kaggle/tmp" if KAGGLE else "/content/tmp")
OUT = WORK / "rollout_vllm_out"; CODE = TMP / "code"
for d in (OUT, OUT / "logs", TMP, CODE):
    d.mkdir(parents=True, exist_ok=True)

def sh(cmd, log=None):
    print("$", cmd, flush=True)
    full = f"set -o pipefail; ( {cmd} ) 2>&1" + (f" | tee -a {log}" if log else "")
    rc = subprocess.run(full, shell=True, executable="/bin/bash").returncode
    if rc != 0:
        raise RuntimeError(f"command failed (exit {rc}): {cmd}" + (f"; see {log}" if log else ""))

GPUS = subprocess.run("nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader", shell=True, capture_output=True, text=True).stdout.strip()
print(GPUS)
sh("curl -fsS -o /dev/null https://huggingface.co || (echo 'NO INTERNET: turn it on in the notebook settings' && false)")
ENV = {"started": datetime.datetime.now().isoformat(timespec="seconds"), "platform": "kaggle" if KAGGLE else "colab", "run_by": RUN_BY,
       "notebook_version": NOTEBOOK_VERSION, "gpu": GPUS,
       "settings": {k: globals()[k] for k in ("MODEL", "REVISION", "PROMPTS", "N", "K", "MAX_NEW", "SMOKE", "METHOD", "FORMATS", "VLLM_DTYPE", "VLLM_UTIL",
                                              "QUANT_PKGS", "VLLM_PKGS", "TORCH_DTYPE")}, "formats": {}}
def save_env():
    json.dump(ENV, open(f"{OUT}/environment.json", "w"), indent=1)
save_env()
"""),
"__SOURCE_CELL__",
code("""
# three environments: llm-compressor, vLLM and the PyTorch scorer pin different torch and transformers versions
sh("pip -q install uv==0.13.6")
for name, pkgs in (("quant", QUANT_PKGS), ("vllm", VLLM_PKGS)):
    venv = TMP / f"venv-{name}"
    if not (venv / "bin/python").exists():
        sh(f"uv venv -q --python 3.12 {venv} && uv pip install -q --python {venv}/bin/python " + " ".join(f"'{p}'" for p in pkgs), log=f"{OUT}/logs/venv_{name}.log")
TVENV = TMP / "venv-torch"
if TORCH_REFERENCE and not (TVENV / ".ready").exists():
    sh(f"rm -rf {TVENV} && uv venv -q --python python3 {TVENV} && uv pip install -q --python {TVENV}/bin/python {TORCH} --index-url {TORCH_INDEX} && "
       f"uv pip install -q --python {TVENV}/bin/python transformers==4.57.6 numpy accelerate && touch {TVENV}/.ready", log=f"{OUT}/logs/venv_torch.log")
QPY, VPY, TPY = (f"env -u PYTHONPATH {TMP}/venv-quant/bin/python", f"env -u PYTHONPATH {TMP}/venv-vllm/bin/python", f"env -u PYTHONPATH {TVENV}/bin/python")
probe = {}
for name, py, mods in (("quant", QPY, "llmcompressor compressed_tensors transformers torch"), ("vllm", VPY, "vllm transformers torch")):
    c = "import importlib.metadata as m; print({k: m.version(k.replace('_','-')) for k in '%s'.split()})" % mods
    probe[name] = subprocess.run(f"{py} -c \\"{c}\\"", shell=True, capture_output=True, text=True, check=True).stdout.strip()
    print(name, probe[name])
ENV["packages"] = probe; save_env()
"""),
code("""
# the bf16 model at the pinned revision, then W4A16 (GPTQ, group 128, lm_head kept in bf16): the week-2 recipe
BF16 = TMP / "model-bf16"
if not (BF16 / "config.json").exists():
    sh(f"{QPY} -c \\"from huggingface_hub import snapshot_download as s; s('{MODEL}', revision='{REVISION}', local_dir='{BF16}', "
       f"allow_patterns=['*.json','*.safetensors','*.txt'])\\"")
W4 = TMP / (f"model-W4A16-{METHOD}" + ("-smoke" if SMOKE else ""))        # a smoke model is never reused for the real run
if "W4A16" in FORMATS:
    if not (W4 / "quantize_meta.json").exists():
        samples = "--samples 32 --seq-len 512" if SMOKE else "--samples 256 --seq-len 1024"
        t = time.time()
        sh(f"{QPY} {CODE}/quantize_w4a16.py --model-dir {BF16} --out {W4} --method {METHOD} --model {MODEL} --revision {REVISION} {samples}",
           log=f"{OUT}/logs/quantize.log")
        ENV["quantize_s"] = round(time.time() - t)
    # fails unless every decoder linear is stored packed (llm-compressor can skip layers silently)
    sh(f"python3 {CODE}/check_dense_w4a16.py {W4} --layers {LAYERS} --base {BF16} --out {OUT}/check_W4A16.json")
    shutil.copy(W4 / "quantize_meta.json", OUT / "quantize_meta.json")
save_env()
"""),
code("""
# the sampler: vLLM, one process per format (the GPU memory is freed between them), same prompts and seed for both
BASE = "vllm_" + ("bf16" if VLLM_DTYPE in ("bfloat16", "bf16") else "fp16")
NAMES = {"base": BASE, "W4A16": "vllm_W4A16"}; DIRS = {"base": BF16, "W4A16": W4}
RUNS = f"{OUT}/rollout_{MODEL.split('/')[-1]}_vllm_n{N}_k{K}_t{MAX_NEW}" + ("_balanced" if PROMPTS == "balanced" else "") + ("_smoke" if SMOKE else "")
os.makedirs(RUNS, exist_ok=True)
for fmt in FORMATS:
    name, js = NAMES[fmt], f"{RUNS}/{NAMES[fmt]}.json"
    if os.path.exists(js):
        print(name, "already done, skipping"); continue
    t0 = time.time()
    sh(f"cd {CODE} && {VPY} quant_rollout_vllm.py --model-dir {DIRS[fmt]} --name {name} --dtype {VLLM_DTYPE} --prompts {CODE}/fixed_100.jsonl "
       f"--n {N} --k {K} --max-new {MAX_NEW} --seed {SEED} --eps {EPS} --gpu-memory-utilization {VLLM_UTIL} --out {js} --dump-dir {RUNS}/dump"
       + (" --balanced" if PROMPTS == "balanced" else ""), log=f"{OUT}/logs/sample_{name}.log")
    ENV["formats"][name] = {"wall_clock_s": round(time.time() - t0), "dtype": VLLM_DTYPE}; save_env()
"""),
code("""
# stage 2: the same sampled tokens through the Hugging Face model in PyTorch (Team 10's trainer setup)
TORCH_JSON = f"{RUNS}/torch_reference.json"
if TORCH_REFERENCE and not os.path.exists(TORCH_JSON):
    pr = subprocess.run(f"{TPY} -c \\"import torch, json; print(json.dumps(dict(torch=torch.__version__, cuda=torch.cuda.is_available())))\\"",
                        shell=True, capture_output=True, text=True)
    if pr.returncode != 0 or not json.loads(pr.stdout.strip().splitlines()[-1])["cuda"]:
        raise RuntimeError("the torch venv cannot see the GPU: set TORCH_INDEX to https://download.pytorch.org/whl/cu128, delete " + str(TVENV) + " and rerun")
    ENV["torch_venv"] = json.loads(pr.stdout.strip().splitlines()[-1]); save_env()
    dumps = " ".join(f"--dump {RUNS}/dump/{NAMES[f]}_rollouts.jsonl" for f in FORMATS if os.path.exists(f"{RUNS}/dump/{NAMES[f]}_rollouts.jsonl"))
    sh(f"cd {CODE} && env HF_HOME={TMP}/hf {TPY} -u score_with_torch.py {dumps} --model {MODEL} --revision {REVISION} --out {TORCH_JSON} "
       f"--dtype {TORCH_DTYPE} --eps {EPS} --per-rollout --device cuda", log=f"{OUT}/logs/score_with_torch.log")
"""),
code("""
# results: speed per format, the PyTorch table with intervals, a zip of everything
import pandas as pd
rows = []
for p in sorted(glob.glob(f"{RUNS}/vllm_*.json")):
    if os.path.basename(p) == "torch_reference.json":
        continue
    f = json.load(open(p))["formats"][0]
    rows.append({"format": f["format"], "dtype": f["dtype"], "vllm": f["vllm"], "rollouts": f["rollouts"], "new_tokens": f["new_tokens"],
                 "batched_tok_s": f["rollout_tokens_per_s"], "finish": f["finish_reasons"]})
speed = pd.DataFrame(rows)
if (speed["format"] == BASE).any():
    speed["tok_s_vs_" + BASE] = (speed["batched_tok_s"] / float(speed.loc[speed["format"] == BASE, "batched_tok_s"].iloc[0])).round(2)
speed.to_csv(f"{RUNS}/table_speed.csv", index=False)
print("vLLM batched generation throughput (not single-stream decode speed)"); print(speed.to_string(index=False))
if os.path.exists(TORCH_JSON):
    tj = json.load(open(TORCH_JSON))
    trows = [{"format": f["format"], "outside": round(f["outside"], 4), "outside_ci95": f["ci95_by_prompt"]["outside"], "mean_abs_logratio": round(f["mean_abs_logratio"], 4),
              "k3": round(f["k3"], 5), "k3_ci95": f["ci95_by_prompt"]["k3"], "top1_agree": round(f["top1_agreement"], 4), "top1_ci95": f["ci95_by_prompt"]["top1_agreement"]}
             for f in tj["formats"]]
    tt = pd.DataFrame(trows); tt.to_csv(f"{RUNS}/table_torch.csv", index=False)
    print(f"\\nreference = PyTorch {tj['dtype']} ({tj['reference']}); intervals resample prompts"); print(tt.to_string(index=False))
ENV["finished"] = datetime.datetime.now().isoformat(timespec="seconds"); save_env()
shutil.copy(f"{OUT}/environment.json", f"{RUNS}/environment.json"); shutil.copytree(f"{OUT}/logs", f"{RUNS}/logs", dirs_exist_ok=True)
for extra in ("quantize_meta.json", "check_W4A16.json"):
    if os.path.exists(f"{OUT}/{extra}"):
        shutil.copy(f"{OUT}/{extra}", f"{RUNS}/{extra}")
zip_path = shutil.make_archive(RUNS, "zip", RUNS)      # the dump (token ids) is inside: do not commit it
print("\\nEverything is in", RUNS, "and", zip_path, "(Kaggle: the version's Output tab)")
"""),
]


def build() -> Path:
    src = {name: path.read_text() for name, path in SOURCES.items()}
    writer = ["# the code and the 100 fixed prompts, embedded by build_vllm_notebook.py",
              "SOURCES = " + json.dumps(src, ensure_ascii=True, indent=0),
              "for _name, _text in SOURCES.items():",
              "    open(f\"{CODE}/{_name}\", \"w\").write(_text)",
              "print(\"wrote\", sorted(SOURCES), \"to\", CODE)"]
    version = hashlib.sha256(("".join(src[k] for k in sorted(src)) + Path(__file__).read_text()).encode()).hexdigest()[:12]
    cells = [code("\n".join(writer)) if c == "__SOURCE_CELL__" else c for c in CELLS]
    for c in cells:
        c["source"] = [line.replace("__NOTEBOOK_VERSION__", version) for line in c["source"]]
    nb = {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}, "accelerator": "GPU"}}
    out = HERE / "rollout_vllm.ipynb"
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    return out


if __name__ == "__main__":
    print("wrote", build())
