#!/usr/bin/env python3
"""Second reference for the quantized-rollout mismatch: score the same sampled tokens with PyTorch (Team 10's setup).

    python score_with_torch.py --dump out/dump/Q8_0_rollouts.jsonl [--dump ...] --model sarvamai/sarvam-1 \\
        --revision <commit> --out torch_reference.json [--dtype bfloat16] [--device cuda] [--eps 0.2]

Stage 1 (`quant_rollout_mismatch.py --dump-dir`, llama.cpp) samples with a quantized GGUF and writes, per rollout, the token
ids, the quantized model's log-probability of every sampled token and its top-1 token per position. This stage loads the
Hugging Face model, runs the same ids through it, and reports what Team 10's trainer would see: log_ratio =
log p_torch - log p_sampler for every sampled token, the share outside [1 - eps, 1 + eps], |log-ratio| quantiles, k3 (the
fields of rl-loop/mismatch_probe.py), top-1 agreement, with 95% intervals that resample prompts (the rollouts of a prompt
are not independent).

Team 10's trainer (rl-loop/policy.py) keeps frozen weights in bf16, runs bf16 autocast, takes the logits in fp32 and
applies log_softmax: that is `--dtype bfloat16` here. `--dtype float32` runs the whole model in fp32 (as mismatch_probe.py
--hf-dtype float32). On a T4 (no native bf16) check `torch_bf16_supported` in the output and prefer float32 if bf16 is slow.

Mean KL(torch || quant) is not reported: it needs the quantized model's full distribution, which the dump does not keep
(the llama.cpp reference mode of quant_rollout_mismatch.py reports it). The dump holds token ids of model-generated
completions: keep it out of the repository; only the aggregate output of this script is committed.
"""
from __future__ import annotations

import argparse, json, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import quant_rollout_mismatch as qrm  # noqa: E402


def load_dump(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def score_records(model, records: list[dict], device, dtype_name: str) -> tuple[dict, np.ndarray, np.ndarray]:
    """Run every rollout's ids through `model`; returns per-token arrays (lp_ref, lp_q, agree), positions, clusters."""
    import torch
    lp_ref, lp_q, agree, positions, clusters = [], [], [], [], []
    vocab = None
    model.eval()
    with torch.no_grad():
        for rec in records:
            if max(rec["ids"]) >= model.config.vocab_size:
                raise ValueError(f"id {max(rec['ids'])} is outside the model's vocabulary ({model.config.vocab_size}): "
                                 "wrong model or revision for this dump?")
            ids = torch.tensor([rec["ids"]], device=device)
            plen = rec["prompt_len"]
            logits = model(input_ids=ids).logits[0, plen - 1:len(rec["ids"]) - 1].float()
            vocab = logits.shape[-1]
            comp = ids[0, plen:]
            if int(comp.max()) >= vocab:
                raise ValueError(f"a sampled id is outside the output width ({vocab}): wrong model for this dump?")
            logp = torch.log_softmax(logits, -1)
            lp_ref.append(logp.gather(-1, comp[:, None]).squeeze(-1).cpu().numpy().astype(np.float64))
            agree.append((logp.argmax(-1).cpu().numpy() == np.asarray(rec["top1_q"])))
            lp_q.append(np.asarray(rec["lp_q"], dtype=np.float64))
            positions.append(np.arange(len(comp)))
            clusters.append(np.full(len(comp), rec["prompt_idx"]))
    per_pos = {"lp_ref": np.concatenate(lp_ref), "lp_q": np.concatenate(lp_q), "agree": np.concatenate(agree)}
    return per_pos, np.concatenate(positions), np.concatenate(clusters)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dump", action="append", required=True, type=Path, help="<format>_rollouts.jsonl; repeat per format")
    ap.add_argument("--model", required=True); ap.add_argument("--revision", default=None)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32", "float16"])
    ap.add_argument("--device", default=None)
    ap.add_argument("--eps", type=float, default=qrm.EPS)
    a = ap.parse_args()
    import torch
    from transformers import AutoModelForCausalLM
    device = torch.device(a.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(a.model, revision=a.revision, dtype=getattr(torch, a.dtype)).to(device)
    out = {"reference": f"{a.model}@{a.revision}", "dtype": a.dtype, "device": str(device), "torch": torch.__version__,
           "torch_bf16_supported": bool(device.type == "cuda" and torch.cuda.is_bf16_supported()), "eps": a.eps, "formats": []}
    for path in a.dump:
        records = load_dump(path)
        if not records:
            continue
        name = records[0]["format"]
        per_pos, positions, clusters = score_records(model, records, device, a.dtype)
        res = {"format": name, "rollouts": len(records), "new_tokens": int(len(per_pos["lp_ref"]))}
        res.update(qrm.aggregate(per_pos, positions, a.eps, clusters))
        out["formats"].append(res)
        ci = res["ci95_by_prompt"]
        print(f"{name}: outside {res['outside']:.4f} {ci['outside']}, top-1 {res['top1_agreement']:.4f} {ci['top1_agreement']}, "
              f"k3 {res['k3']:.5f}, {time.time() - t0:.0f}s", flush=True)
    a.out.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
