#!/usr/bin/env python3
"""Stage the inputs of the wide-pass job once, WITH network, so run_job.py can run with none.

    HF_TOKEN=<read token with MILU access> python prepare_inputs.py --hf-home ./inputs/hf_home \
        --model-dir ./inputs/sarvam-1 --model sarvamai/sarvam-1 --revision e9607337286ddf496d4a2562b194e489dcf3feea

1. the model snapshot at the pinned revision (safetensors, config, tokenizer files) into --model-dir;
2. every dataset of run_wide_gguf.WIDE, loaded through lm_eval's own task loader into the cache at --hf-home,
   so the offline job reads exactly what an online run would (same dataset ids, configs and splits);
3. then the same tasks again with HF_HUB_OFFLINE=1 and HF_DATASETS_OFFLINE=1, to prove the cache is complete.

The token is read from the environment for staging only. It is not written anywhere, and the job does not need it.
"""
from __future__ import annotations

import argparse, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

LOAD = """
import sys
sys.path.insert(0, {here!r})
from run_wide_gguf import WIDE
from lm_eval.tasks import TaskManager, get_task_dict
tm = TaskManager(include_path={tasks!r})

def leaves(d):
    for v in d.values():
        yield from (leaves(v) if isinstance(v, dict) else [v])

total = 0
for t in leaves(get_task_dict(list(WIDE), tm)):   # building a task loads its dataset (into HF_HOME)
    n = len(t.eval_docs); total += n
    print(f"{{t.config.task}}: {{n}} items", flush=True)
print(f"total: {{total}} items")
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hf-home", required=True, type=Path)
    ap.add_argument("--model-dir", required=True, type=Path)
    ap.add_argument("--model", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--g9-dir", type=Path, default=HERE.parents[1] / "09-evaluation" / "harness_code_indic")
    args = ap.parse_args()
    if not os.environ.get("HF_TOKEN"):
        sys.exit("set HF_TOKEN (read token of an account that accepted ai4bharat/MILU and the model's terms)")
    os.environ["HF_HOME"] = str(args.hf_home.resolve())

    from huggingface_hub import snapshot_download
    snapshot_download(args.model, revision=args.revision, local_dir=str(args.model_dir),
                      allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt"])
    print("model:", args.model_dir, flush=True)

    code = LOAD.format(here=str(HERE), tasks=str(args.g9_dir / "tasks"))
    subprocess.run([sys.executable, "-c", code], check=True, env=os.environ)
    offline = {**os.environ, "HF_HUB_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1"}
    offline.pop("HF_TOKEN")
    print("offline check:", flush=True)
    subprocess.run([sys.executable, "-c", code], check=True, env=offline)
    print("staged:", args.hf_home, args.model_dir)


if __name__ == "__main__":
    main()
