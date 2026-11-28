"""Lab rule 6 (TSAI, 28 Nov): gradient coverage for model.head_mode=kas_v2 vs dense.

After one forward and backward, list every trainable parameter whose gradient is None or all zero, for each head
mode, with torch.compile off and on (rule 6: "fast path on and off"), and compare the lists. Real p1536 byte
table and prior; random tokens.

  PYTHONPATH=. python correctness/kas_grad_coverage.py --out kas_grad_coverage.json
"""
from __future__ import annotations

import argparse
import json

import torch

from models.config import ModelConfig
from models.gpt import GPT


def coverage(head: str, device: str, compiled: bool = False, d: int = 256, layers: int = 2, t: int = 64) -> dict:
    torch.manual_seed(0)
    cfg = ModelConfig(vocab_size=131072, block_size=t, n_layer=layers, n_head=4, n_embd=d, attn_impl="eager",
                      head_mode=head, tie_embeddings=False, reversible=False)
    model = GPT(cfg).to(device).train()
    ids = torch.randint(0, cfg.vocab_size, (2, t + 1), generator=torch.Generator().manual_seed(1)).to(device)
    run = torch.compile(model) if compiled else model
    _, loss = run(ids[:, :-1], ids[:, 1:])
    loss.backward()
    params = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    missing = [n for n, p in params if p.grad is None]
    zero = [n for n, p in params if p.grad is not None and not bool(p.grad.ne(0).any())]
    return {"head": head, "compiled": compiled, "trainable": len(params), "grad_none": missing, "grad_all_zero": zero,
            "loss": float(loss.detach())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    runs = {f"{h}{'_compiled' if c else ''}": coverage(h, a.device, c) for h in ("dense", "kas_v2") for c in (False, True)}
    result = {"check": "kas_grad_coverage", "device": a.device, "runs": runs,
              "passed": all(not r["grad_none"] and not r["grad_all_zero"] for r in runs.values()),
              "compile_lists_match": all(runs[h]["grad_none"] == runs[h + "_compiled"]["grad_none"] and
                                         runs[h]["grad_all_zero"] == runs[h + "_compiled"]["grad_all_zero"]
                                         for h in ("dense", "kas_v2"))}
    text = json.dumps(result, indent=2)
    print(text)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
