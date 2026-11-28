#!/usr/bin/env python3
"""Build rollout_mismatch.ipynb (Kaggle) from quant_rollout_mismatch.py and ../eval_mini's setup cells.

    python build_notebook.py

Reuses eval_mini's environment, llama-cpp-python (CUDA) build, evaluation venv and bf16 conversion cells (read from
../eval_mini/build_notebook.py, as eval_wide does), then runs quant_rollout_mismatch.py once per format, writing one
JSON per format so a session that stops resumes where it left off. The notebook embeds its own copy of the code and of
the 100 fixed prompts, so it runs without a branch being pushed.

Stage 1 samples with each quantized GGUF and scores with the bf16 GGUF (llama.cpp), and dumps the token ids. Stage 2
(`TORCH_REFERENCE`) scores the same ids with the Hugging Face model in PyTorch, Team 10's trainer setup, in a pinned venv.
"""
import hashlib, importlib.util, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MINI = HERE.parent / "eval_mini"
SOURCES = {"quant_rollout_mismatch.py": HERE / "quant_rollout_mismatch.py", "score_with_torch.py": HERE / "score_with_torch.py",
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
Stage 1 is the quantization gap against llama.cpp's bf16; stage 2 (PyTorch) is the gap G10's trainer sees. `bf16` in `FORMATS`
adds a bf16 sampler row: its decode tok/s is the baseline of `tok_s_vs_bf16`, and in stage 2 its mismatch is the
llama.cpp-versus-PyTorch gap with no quantization in it. Compare tok/s only inside one session (the GPU varies between sessions).

**Smoke run first:** keep `N = 4`, `K = 2`, `MAX_NEW = 32` and `FORMATS = ["Q8_0"]`; check that a `tok/s` line and an
`outside` value print for it. Then set the real values. The first run builds llama-cpp-python with CUDA (~15-30 min).

Kaggle: Accelerator **GPU T4 x2**, Internet **on**. Use **Save Version, Save & Run All (Commit)**. No token is needed
(both models are not gated).
"""),
code("""
# --- settings -----------------------------------------------------------------------------------------------
FORMATS   = ["Q8_0"]           # <-- samplers to test: bf16, Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M. bf16 as a sampler is the decode-speed
                               #     baseline (tok/s) and, in stage 2, the llama.cpp-versus-PyTorch gap; always scored against the bf16 reference
RUN_BY    = ""                 # <-- your GitHub handle, recorded with the results
PROMPTS   = "first"            # "first" = the first N of the 100 fixed prompts (the first 48 are 40 English + 8 Indic, no code);
                               # "balanced" = N taken round-robin over english / indic / code / tool_call / reasoning (10 each at N = 50)
N         = 4                  # prompts (of the 100 fixed prompts)           real run: 48
K         = 2                  # completions per prompt                       real run: 8
MAX_NEW   = 32                 # new tokens per completion                    real run: 256
EPS       = 0.2                # objective_v1's trust region (grpo.TR_EPSILON)
SEED      = 1234
N_CTX     = 2048
BASE      = "bf16"
MODEL, REVISION = "sarvamai/sarvam-1", "e9607337286ddf496d4a2562b194e489dcf3feea"
# or Granite: MODEL, REVISION = "ibm-granite/granite-3.0-3b-a800m-base", "142d2c8e3f7fb8844011cfa5565f0e520f0824b9"
# second models Team 10 suggested (pin a revision before the real run): "Qwen/Qwen2.5-Coder-1.5B", "HuggingFaceTB/SmolLM2-1.7B"
TORCH_REFERENCE = True         # stage 2: score the same tokens with the HF model in PyTorch (Team 10's trainer setup)
TORCH_DTYPE = "bfloat16"       # Team 10's trainer: bf16 weights and autocast, fp32 logits. T4 has no native bf16: if stage 2 is slow, "float32"
TORCH = "torch==2.11.0"        # CUDA 12.6 build, from the PyTorch index below
TORCH_INDEX = "https://download.pytorch.org/whl/cu126"
LLAMA_TAG = "b11669"
LLAMA_CPP_PYTHON = "0.3.36"
DRIVE_DIR = "/content/drive/MyDrive/era-v5-g12/rollout_mismatch"
BF16_FALLBACK_GPU_LAYERS = 12  # reference GPU layers, only if bf16 does not fit next to the sampler on the GPUs
LIMIT = None                   # unused here; kept because the shared setup cells record it
NOTEBOOK_VERSION = "__NOTEBOOK_VERSION__"
assert FORMATS and all(f in {"bf16", "Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M", "Q3_K_M"} for f in FORMATS), FORMATS
assert PROMPTS in ("first", "balanced"), PROMPTS
"""),
pick("LOCAL_TEST = bool(os.environ"),          # environment, folders, sh()
"__SOURCE_CELL__",
pick("llama-cpp-python with CUDA"),            # CUDA wheel + evaluation venv
pick("bf16 GGUF: the llama.cpp converter"),    # llama-quantize build + bf16 conversion
code("""
# every format: quantize (output layer Q8_0 below 8 bits, as quantize_eval.py), rollouts + scoring, one JSON per format
RUNS = f"{OUT}/rollout_{NAME}_n{N}_k{K}_t{MAX_NEW}" + ("_balanced" if PROMPTS == "balanced" else "")
os.makedirs(RUNS, exist_ok=True)

def run_format(fmt, gguf, ref_layers):
    out = f"{RUNS}/{fmt}.json"
    sh(f"cd {CODE} && {EVAL_PY} quant_rollout_mismatch.py --ref {BF16} --quant {fmt}={gguf} --prompts {CODE}/fixed_100.jsonl "
       f"--out {out} --n {N} --k {K} --max-new {MAX_NEW} --n-ctx {N_CTX} --eps {EPS} --seed {SEED} "
       f"--ref-n-gpu-layers {ref_layers} --dump-dir {RUNS}/dump" + (" --balanced" if PROMPTS == "balanced" else ""), log=f"{OUT}/logs/rollout_{fmt}.log")

for fmt in FORMATS:
    t0 = time.time()
    if os.path.exists(f"{RUNS}/{fmt}.json"):
        print(fmt, "already done, skipping"); continue
    gguf = BF16 if fmt == "bf16" else f"{WORK}/{NAME}-{fmt}.gguf"
    made_here = fmt != "bf16" and not os.path.exists(gguf)       # the bf16 file is the reference: never made or deleted here
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
# stage 2: the same sampled tokens scored by the Hugging Face model in PyTorch (Team 10's setup); pinned venv, GPU must be visible
TORCH_JSON = f"{RUNS}/torch_reference.json"
if TORCH_REFERENCE and not os.path.exists(TORCH_JSON):
    TVENV = f"{WORK}/torch-venv"; TPY = f"env -u PYTHONPATH {TVENV}/bin/python"
    if not os.path.exists(f"{TVENV}/.ready"):
        sh(f"rm -rf {TVENV} && pip install -q uv==0.13.6 && uv venv -q --python python3 {TVENV} && "
           f"uv pip install -q --python {TVENV}/bin/python {TORCH} --index-url {TORCH_INDEX} && "
           f"uv pip install -q --python {TVENV}/bin/python transformers==4.57.6 numpy accelerate && touch {TVENV}/.ready",
           log=f"{OUT}/logs/torch_venv.log")
    pr = subprocess.run(f"{TPY} -c \\"import torch, json; print(json.dumps(dict(torch=torch.__version__, cuda=torch.cuda.is_available())))\\"",
                        shell=True, capture_output=True, text=True)
    if pr.returncode != 0 or not json.loads(pr.stdout.strip().splitlines()[-1])["cuda"]:
        raise RuntimeError("the torch venv cannot see the GPU (" + (pr.stderr[-500:] or pr.stdout) + "): set TORCH_INDEX to "
                           "https://download.pytorch.org/whl/cu128, delete " + TVENV + " and rerun")
    ENV["torch_venv"] = json.loads(pr.stdout.strip().splitlines()[-1]); save_env()
    dumps = " ".join(f"--dump {RUNS}/dump/{f}_rollouts.jsonl" for f in FORMATS if os.path.exists(f"{RUNS}/dump/{f}_rollouts.jsonl"))
    rev = f"--revision {REVISION} " if REVISION else ""
    sh(f"cd {CODE} && env HF_HOME={WORK}/hf {TPY} -u score_with_torch.py {dumps} --model {MODEL} {rev}--out {TORCH_JSON} "
       f"--dtype {TORCH_DTYPE} --eps {EPS} --device cuda", log=f"{OUT}/logs/score_with_torch.log")
"""),
code("""
# results: one table over the formats, a zip of everything
import pandas as pd
rows = []
for p in sorted(glob.glob(f"{RUNS}/*.json")):
    if os.path.basename(p) in ("torch_reference.json", "environment.json"):   # not per-format llama.cpp results
        continue
    d = json.load(open(p))
    for f in d["formats"]:
        rows.append({"format": f["format"], "rollouts": f["rollouts"], "new_tokens": f["new_tokens"],
                     "rollout_tok_s": f["rollout_tokens_per_s"], "outside": round(f.get("outside", float("nan")), 4),
                     "below": round(f.get("below", float("nan")), 4), "above": round(f.get("above", float("nan")), 4),
                     "mean_abs_logratio": round(f.get("mean_abs_logratio", float("nan")), 4),
                     "k3": round(f.get("k3", float("nan")), 5), "kl_bf16_to_quant": round(f.get("mean_kl_ref_to_quant", float("nan")), 5),
                     "top1_agree": round(f.get("top1_agreement", float("nan")), 4)})
table = pd.DataFrame(rows)
if (table["format"] == "bf16").any():       # the real speed ratio: this sampler against the bf16 sampler, same prompts, same session
    base_speed = float(table.loc[table["format"] == "bf16", "rollout_tok_s"].iloc[0])
    table["tok_s_vs_bf16"] = (table["rollout_tok_s"] / base_speed).round(2)
table.to_csv(f"{RUNS}/table.csv", index=False)
print("reference = llama.cpp bf16 GGUF"); print(table.to_string(index=False))
if os.path.exists(f"{RUNS}/torch_reference.json"):
    tj = json.load(open(f"{RUNS}/torch_reference.json"))
    trows = [{"format": f["format"], "outside": round(f["outside"], 4), "outside_ci95": f["ci95_by_prompt"]["outside"],
              "mean_abs_logratio": round(f["mean_abs_logratio"], 4), "k3": round(f["k3"], 5), "k3_ci95": f["ci95_by_prompt"]["k3"],
              "top1_agree": round(f["top1_agreement"], 4), "top1_ci95": f["ci95_by_prompt"]["top1_agreement"]} for f in tj["formats"]]
    ttable = pd.DataFrame(trows); ttable.to_csv(f"{RUNS}/table_torch.csv", index=False)
    print(f"\\nreference = PyTorch {tj['dtype']} ({tj['reference']}); intervals resample prompts"); print(ttable.to_string(index=False))
ENV["finished"] = datetime.datetime.now().isoformat(timespec="seconds"); save_env()
shutil.copy(f"{OUT}/environment.json", f"{RUNS}/environment.json")
shutil.copytree(f"{OUT}/logs", f"{RUNS}/logs", dirs_exist_ok=True)
zip_path = shutil.make_archive(RUNS, "zip", RUNS)   # the dump (token ids) is inside: do not commit it
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
    # the version covers the embedded code and this builder (its cells), so two different notebooks never share one
    version = hashlib.sha256(("".join(src[k] for k in sorted(src)) + Path(__file__).read_text()).encode()).hexdigest()[:12]
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
