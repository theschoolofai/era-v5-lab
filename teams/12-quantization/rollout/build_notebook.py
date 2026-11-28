#!/usr/bin/env python3
"""Build rollout_mismatch.ipynb (Kaggle) from quant_rollout_mismatch.py and ../eval_mini's setup cells.

    python build_notebook.py

Reuses eval_mini's environment, llama-cpp-python (CUDA) build, evaluation venv and bf16 conversion cells (read from
../eval_mini/build_notebook.py, as eval_wide does), then runs quant_rollout_mismatch.py once per format, writing one
JSON per format so a session that stops resumes where it left off. The notebook embeds its own copy of the code and of
the 100 fixed prompts, so it runs without a branch being pushed.
"""
import hashlib, importlib.util, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MINI = HERE.parent / "eval_mini"
SOURCES = {"quant_rollout_mismatch.py": HERE / "quant_rollout_mismatch.py",
           "fixed_100.jsonl": HERE.parent / "prompts" / "fixed_100.jsonl"}

_spec = importlib.util.spec_from_file_location("mini_build", MINI / "build_notebook.py")
mini = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(mini)


def pick(marker: str) -> dict:
    hits = [c for c in mini.CELLS if isinstance(c, dict) and c["cell_type"] == "code" and marker in "".join(c["source"])]
    assert len(hits) == 1, (marker, len(hits))
    return hits[0]


md, code = mini.md, mini.code

CELLS = [
md("""
# G12: quantized policy for GRPO rollouts (Kaggle)

For each bit-width: the quantized model draws completions at temperature 1; the bf16 model scores the same tokens.
Reported per format: rollout tokens/s, the share of tokens outside objective_v1's trust region [1-eps, 1+eps],
|log-ratio|, k3, mean KL(bf16 || quant) and top-1 agreement (same fields as G10's `rl-loop/mismatch_probe.py`).
This is the quantization gap only: bf16 here is llama.cpp's bf16, not G10's torch trainer.

**Smoke run first:** keep `N = 4`, `K = 2`, `MAX_NEW = 32` and `FORMATS = ["Q8_0"]`; check that a `tok/s` line and an
`outside` value print for it. Then set the real values. The first run builds llama-cpp-python with CUDA (~15-30 min).

Kaggle: Accelerator **GPU T4 x2**, Internet **on**. Use **Save Version, Save & Run All (Commit)**. No token is needed
(both models are not gated).
"""),
code("""
# --- settings -----------------------------------------------------------------------------------------------
FORMATS   = ["Q8_0"]           # <-- quantized samplers to test: Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M (bf16 is the reference)
RUN_BY    = ""                 # <-- your GitHub handle, recorded with the results
N         = 4                  # prompts (of the 100 fixed prompts)           real run: 48
K         = 2                  # completions per prompt                       real run: 8
MAX_NEW   = 32                 # new tokens per completion                    real run: 256
EPS       = 0.2                # objective_v1's trust region (grpo.TR_EPSILON)
SEED      = 1234
N_CTX     = 2048
BASE      = "bf16"
MODEL, REVISION = "sarvamai/sarvam-1", "e9607337286ddf496d4a2562b194e489dcf3feea"
# or Granite: MODEL, REVISION = "ibm-granite/granite-3.0-3b-a800m-base", "142d2c8e3f7fb8844011cfa5565f0e520f0824b9"
LLAMA_TAG = "b11669"
LLAMA_CPP_PYTHON = "0.3.36"
DRIVE_DIR = "/content/drive/MyDrive/era-v5-g12/rollout_mismatch"
BF16_FALLBACK_GPU_LAYERS = 12  # reference GPU layers, only if bf16 does not fit next to the sampler on the GPUs
LIMIT = None                   # unused here; kept because the shared setup cells record it
NOTEBOOK_VERSION = "__NOTEBOOK_VERSION__"
assert FORMATS and all(f in {"Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M", "Q3_K_M"} for f in FORMATS), FORMATS
"""),
pick("LOCAL_TEST = bool(os.environ"),          # environment, folders, sh()
"__SOURCE_CELL__",
pick("llama-cpp-python with CUDA"),            # CUDA wheel + evaluation venv
pick("bf16 GGUF: the llama.cpp converter"),    # llama-quantize build + bf16 conversion
code("""
# every format: quantize (output layer Q8_0 below 8 bits, as quantize_eval.py), rollouts + scoring, one JSON per format
RUNS = f"{OUT}/rollout_{NAME}_n{N}_k{K}_t{MAX_NEW}"
os.makedirs(RUNS, exist_ok=True)

def run_format(fmt, gguf, ref_layers):
    out = f"{RUNS}/{fmt}.json"
    sh(f"cd {CODE} && {EVAL_PY} quant_rollout_mismatch.py --ref {BF16} --quant {fmt}={gguf} --prompts {CODE}/fixed_100.jsonl "
       f"--out {out} --n {N} --k {K} --max-new {MAX_NEW} --n-ctx {N_CTX} --eps {EPS} --seed {SEED} "
       f"--ref-n-gpu-layers {ref_layers}", log=f"{OUT}/logs/rollout_{fmt}.log")

for fmt in FORMATS:
    t0 = time.time()
    if os.path.exists(f"{RUNS}/{fmt}.json"):
        print(fmt, "already done, skipping"); continue
    gguf = f"{WORK}/{NAME}-{fmt}.gguf"
    made_here = not os.path.exists(gguf)
    if made_here:
        extra = "" if fmt == "Q8_0" else "--output-tensor-type q8_0"
        sh(f"{QUANTIZE} {extra} {BF16} {gguf} {fmt}", log=f"{OUT}/logs/quantize_{fmt}.log")
    ref_layers = -1
    try:
        run_format(fmt, gguf, ref_layers)
    except RuntimeError:
        tail = open(f"{OUT}/logs/rollout_{fmt}.log").read()[-20000:].lower()
        if not any(k in tail for k in ("out of memory", "failed to allocate", "cudamalloc")):
            raise
        ref_layers = BF16_FALLBACK_GPU_LAYERS
        print(f"out of GPU memory; retrying with the bf16 reference on {ref_layers} GPU layers")
        run_format(fmt, gguf, ref_layers)
    ENV["formats"][fmt] = {"ref_gpu_layers": ref_layers, "gguf_bytes": os.path.getsize(gguf),
                           "wall_clock_s": round(time.time() - t0), "finished": datetime.datetime.now().isoformat(timespec="seconds")}
    save_env()
    if made_here:
        os.remove(gguf)
"""),
code("""
# results: one table over the formats, a zip of everything
import pandas as pd
rows = []
for p in sorted(glob.glob(f"{RUNS}/*.json")):
    d = json.load(open(p))
    for f in d["formats"]:
        rows.append({"format": f["format"], "rollouts": f["rollouts"], "new_tokens": f["new_tokens"],
                     "rollout_tok_s": f["rollout_tokens_per_s"], "outside": round(f.get("outside", float("nan")), 4),
                     "below": round(f.get("below", float("nan")), 4), "above": round(f.get("above", float("nan")), 4),
                     "mean_abs_logratio": round(f.get("mean_abs_logratio", float("nan")), 4),
                     "k3": round(f.get("k3", float("nan")), 5), "kl_bf16_to_quant": round(f.get("mean_kl_ref_to_quant", float("nan")), 5),
                     "top1_agree": round(f.get("top1_agreement", float("nan")), 4)})
table = pd.DataFrame(rows); table.to_csv(f"{RUNS}/table.csv", index=False)
print(table.to_string(index=False))
ENV["finished"] = datetime.datetime.now().isoformat(timespec="seconds"); save_env()
shutil.copy(f"{OUT}/environment.json", f"{RUNS}/environment.json")
shutil.copytree(f"{OUT}/logs", f"{RUNS}/logs", dirs_exist_ok=True)
zip_path = shutil.make_archive(RUNS, "zip", RUNS)
print("\\nEverything is in", RUNS, "and", zip_path, "(Kaggle: the version's Output tab)")
"""),
]


def build() -> Path:
    src = {name: path.read_text() for name, path in SOURCES.items()}
    writer = ["# the code and the 100 fixed prompts, embedded by build_notebook.py",
              "SOURCES = " + json.dumps(src, ensure_ascii=True, indent=0),
              "for _name, _text in SOURCES.items():",
              "    open(f\"{CODE}/{_name}\", \"w\").write(_text)",
              "print(\"wrote\", sorted(SOURCES), \"to\", CODE)"]
    version = hashlib.sha256("".join(src[k] for k in sorted(src)).encode()).hexdigest()[:12]
    cells = [code("\n".join(writer)) if c == "__SOURCE_CELL__" else c for c in CELLS]
    for c in cells:
        c["source"] = [line.replace("__NOTEBOOK_VERSION__", version) for line in c["source"]]
    nb = {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                       "language_info": {"name": "python"}, "accelerator": "GPU"}}
    out = HERE / "rollout_mismatch.ipynb"
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=True) + "\n")
    return out


if __name__ == "__main__":
    print("wrote", build())
