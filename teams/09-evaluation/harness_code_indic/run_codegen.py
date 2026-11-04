"""Generate HumanEval+ / MBPP+ solutions locally with evalplus (greedy, base prompt, bf16, pinned revision).

Executing the solutions needs Linux, so that step runs in code_eval_colab.ipynb. This script writes the files to upload:
    runs/<model>/evalplus/<model>__humaneval.jsonl
    runs/<model>/evalplus/<model>__mbpp.jsonl

Usage (from this folder):
    python -u run_codegen.py --model qwen2.5-1.5b
"""
import argparse
import json
import os
import shutil
import time
from pathlib import Path
from importlib import metadata

from fetch_weights import local_dir
from run_lm_eval import HERE, RUNS, cap_vram, gpu_state, keep_awake


def fix_stacked_stop_criteria():
    """evalplus 0.3.1's HF decoder wraps model._get_stopping_criteria on every call, and each wrap captures the previous one,
    so problem n runs n stop criteria. The stale ones use earlier prompt lengths and can find a stop string inside the current
    prompt, ending generation after one token. Measured 25 Oct: HumanEval/32 and /38 kept 1 token in a long run, but 768 and
    101 tokens when generated fresh, and the time per problem grew linearly. Dropping the leftover patch before each call
    restores evalplus's intended behaviour: one stop criterion per problem."""
    from evalplus.provider.hf import HuggingFaceDecoder
    original = HuggingFaceDecoder.codegen

    def codegen(self, prompt, do_sample=True, num_samples=200):
        self.model.__dict__.pop("_get_stopping_criteria", None)
        return original(self, prompt, do_sample=do_sample, num_samples=num_samples)

    HuggingFaceDecoder.codegen = codegen


def fix_shared_eos_list():
    """evalplus 0.3.1: DecoderBase sets `self.eos = EOS` (the module-level list, not a copy) and the HF decoder then does
    `self.eos += extra_eos(dataset)`, which grows the shared list. Running HumanEval then MBPP in one process gave MBPP
    HumanEval's stop strings ('\\ndef ', '\\nclass ', '\\nimport ', '\\nfrom '), cutting MBPP answers at their first or
    second function (phi-2: 346/378 empty). Each decoder now gets its own copy."""
    from evalplus.provider.base import DecoderBase
    original = DecoderBase.__init__

    def __init__(self, *args, **kwargs):
        original(self, *args, **kwargs)
        self.eos = list(self.eos)

    DecoderBase.__init__ = __init__


PROBE = "def f(x):\n    return x + 1  # ok\n\tif a == b:\n        print('हिन्दी తెలుగు')\n"


def fix_tokenizer_rebuild():
    """transformers 5 rebuilds some tokenizers from their config class instead of using tokenizer.json. For
    deepseek-coder-1.3b-base (config says LlamaTokenizerFast, tokenizer.json is byte-level BPE) this drops every space
    and newline when encoding: 'def f(x):\\n    return x + 1' -> 'deff(x):returnx+1'. The loader below checks a
    round trip and falls back to the repo's own tokenizer.json; if that also fails, the run stops."""
    import json as _json
    import evalplus.provider.hf as hf
    from transformers import AutoTokenizer, PreTrainedTokenizerFast

    class CheckedAutoTokenizer:
        @staticmethod
        def from_pretrained(name, *args, **kwargs):
            tok = AutoTokenizer.from_pretrained(name, *args, **kwargs)
            if tok.decode(tok.encode(PROBE, add_special_tokens=False)) == PROBE:
                return tok
            cfg = _json.loads((Path(name) / "tokenizer_config.json").read_text(encoding="utf-8"))
            special = {k: (v["content"] if isinstance(v, dict) else v) for k, v in cfg.items()
                       if k in ("bos_token", "eos_token", "pad_token", "unk_token") and v}
            tok = PreTrainedTokenizerFast(tokenizer_file=str(Path(name) / "tokenizer.json"), **special)
            if tok.decode(tok.encode(PROBE, add_special_tokens=False)) != PROBE:
                raise RuntimeError(f"{name}: tokenizer does not round-trip even from tokenizer.json")
            print(f"tokenizer: {name} rebuilt by transformers did not round-trip; using its tokenizer.json", flush=True)
            return tok

    hf.AutoTokenizer = CheckedAutoTokenizer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="key in published_scores.json 'models'")
    ap.add_argument("--datasets", default="humaneval,mbpp")
    a = ap.parse_args()

    m = json.loads((HERE / "published_scores.json").read_text(encoding="utf-8"))["models"][a.model]
    weights = local_dir(m["hf_id"], m["revision"])
    assert (weights / "SOURCE.json").exists(), f"run fetch_weights.py --model {a.model} first"
    out = RUNS / a.model / "evalplus"
    raw_root = out / "raw"
    out.mkdir(parents=True, exist_ok=True)
    keep_awake()
    fraction = cap_vram()

    from evalplus.codegen import run_codegen
    fix_stacked_stop_criteria()
    fix_shared_eos_list()
    fix_tokenizer_rebuild()

    meta = {"model": a.model, "hf_id": m["hf_id"], "revision": m["revision"], "vram_fraction_cap": fraction,
            "settings": {"backend": "hf", "greedy": True, "force_base_prompt": True, "dtype": "bfloat16", "attn_implementation": "eager",
                         "fix": "evalplus stacked stop-criteria bug patched (one criterion per problem); see fix_stacked_stop_criteria",
                         "fix2": "evalplus shared EOS list patched (per-decoder copy); see fix_shared_eos_list",
                         "fix3": "tokenizer round-trip guard with tokenizer.json fallback; see fix_tokenizer_rebuild"},
            "versions": {p: metadata.version(p) for p in ("evalplus", "torch", "transformers")}, "gpu_before": gpu_state(), "runs": {}}
    cwd = os.getcwd()
    for dataset in [d.strip() for d in a.datasets.split(",") if d.strip()]:
        t0 = time.time()
        os.chdir(weights.parent)  # evalplus names its output after the model path; a bare folder name avoids the 'C:' colon on Windows
        try:
            path = run_codegen(model=weights.name, dataset=dataset, root=str(raw_root), greedy=True, backend="hf",
                               force_base_prompt=True, dtype="bfloat16", attn_implementation="eager", resume=True)
        finally:
            os.chdir(cwd)
        upload = out / f"{a.model}__{dataset}.jsonl"
        shutil.copyfile(path, upload)
        n = sum(1 for _ in open(upload, encoding="utf-8"))
        meta["runs"][dataset] = {"samples": str(upload), "n": n, "wall_seconds": round(time.time() - t0, 1)}
        print(f"{dataset}: {n} solutions -> {upload} ({(time.time() - t0) / 60:.1f} min)", flush=True)
    meta["gpu_after"] = gpu_state()
    meta_path = out / "codegen_meta.json"
    if meta_path.exists():  # a rerun of one dataset keeps the record of the others
        old = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["runs"] = {**{k: {**v, "settings_at_run": old.get("settings")} for k, v in old.get("runs", {}).items()}, **meta["runs"]}
    meta_path.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
