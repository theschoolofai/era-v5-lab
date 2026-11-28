"""Generate code samples the way evalplus did in December 2023 (codegen/model.py at commit 7d3a585).

Used for the protocol check on issues #334 and #335: the EvalPlus leaderboard's phi-2 scores come from that code.
Differences from evalplus 0.3.1's HF backend, which run_codegen.py uses:

  prompt        task["prompt"] as it is (0.3.1 strips it and adds one newline)
  stop strings  only <|endoftext|>, <|endofmask|>, </s> (0.3.1 adds "\\ndef ", "\\nassert", "\\nprint(" and more)
  max tokens    512 (0.3.1: 768)
  output        prompt + completion, to be cleaned by the sanitizer of that time (score_2023_protocol.py)

Usage:
  python fetch_weights.py --model phi-2
  python codegen_2023_protocol.py --weights <weights dir> --dataset mbpp --version v0.1.0 --dtype float16 \
      --out runs/protocol_2023/phi-2__mbpp.jsonl

Stopping and starting again continues from the samples already written.
"""
import argparse
import json
import os
import time
from pathlib import Path

# On Apple GPUs phi-2 can take tens of GB of swap in seconds without a cap. These must be set before torch loads.
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.5")
os.environ.setdefault("PYTORCH_MPS_LOW_WATERMARK_RATIO", "0.4")

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

EOS = ["<|endoftext|>", "<|endofmask|>", "</s>"]
MAX_NEW_TOKENS = 512
PROGRESS_EVERY = 20
ROUND_TRIP_PROBE = "def f(x):\n    return x + 1  # ok\n"


def load_tasks(dataset, version):
    if dataset == "humaneval":
        from evalplus.data import get_human_eval_plus
        return get_human_eval_plus(version=version)
    from evalplus.data import get_mbpp_plus
    return get_mbpp_plus(version=version)


def pick_device():
    if torch.cuda.is_available():
        return "cuda"
    return "mps" if torch.backends.mps.is_available() else "cpu"


def read_done(out):
    if not out.exists():
        return set()
    return {json.loads(line)["task_id"] for line in out.read_text(encoding="utf-8").splitlines() if line.strip()}


def complete(model, tok, prompt, device, max_new_tokens):
    ids = tok.encode(prompt, return_tensors="pt").to(device)
    gen = model.generate(ids, max_new_tokens=max_new_tokens, do_sample=False, pad_token_id=tok.eos_token_id)
    text = tok.decode(gen[0, ids.size(-1):], skip_special_tokens=True)
    cut = min([text.index(e) for e in EOS if e in text] or [len(text)])
    return text[:cut].replace("\t", "    ")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weights", required=True, help="folder with the model weights (see fetch_weights.py)")
    ap.add_argument("--dataset", required=True, choices=["humaneval", "mbpp"])
    ap.add_argument("--version", default="default", help='dataset version for the prompts, for example "v0.1.0"')
    ap.add_argument("--dtype", default="float16", choices=["float16", "bfloat16", "float32"])
    ap.add_argument("--max-new-tokens", type=int, default=MAX_NEW_TOKENS)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    device = pick_device()
    tok = AutoTokenizer.from_pretrained(args.weights)
    if tok.decode(tok.encode(ROUND_TRIP_PROBE, add_special_tokens=False)) != ROUND_TRIP_PROBE:
        raise SystemExit("the tokenizer does not round-trip spaces and newlines; samples would be broken")
    model = AutoModelForCausalLM.from_pretrained(args.weights, dtype=getattr(torch, args.dtype)).to(device).eval()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = read_done(out)
    tasks = load_tasks(args.dataset, args.version)
    start = time.time()
    with out.open("a", encoding="utf-8") as f, torch.inference_mode():
        for i, (task_id, task) in enumerate(tasks.items()):
            if task_id in done:
                continue
            impl = complete(model, tok, task["prompt"], device, args.max_new_tokens)
            f.write(json.dumps({"task_id": task_id, "solution": task["prompt"] + impl}) + "\n")
            f.flush()
            if i % PROGRESS_EVERY == 0:
                print(f"{i}/{len(tasks)} {time.time() - start:.0f}s", flush=True)
    print(f"done {len(tasks)} tasks, device {device}, dtype {args.dtype}, {time.time() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
