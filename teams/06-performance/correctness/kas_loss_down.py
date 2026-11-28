"""Lab 5 task 1(a) check: with model.head_mode=kas_v2 (frozen p1536 byte table, p1536 unigram prior) the loss goes down.

Synthetic, learnable data: a fixed bank of token sequences drawn from a Zipf-like distribution over the real 131,072
ids; each step trains on a random batch from the bank. Same seed, data and optimizer for --head dense and kas_v2.
Plain torch AdamW (not perfkit's Muon/AdamW split), so the head is the only difference between the two runs.

  PYTHONPATH=. python correctness/kas_loss_down.py --head kas_v2 --steps 200 --out kas_loss_down.json
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time

import torch

from models.config import ModelConfig
from models.gpt import GPT


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def git_dirty() -> bool:
    try:
        return bool(subprocess.check_output(["git", "status", "--porcelain", "--", "."], text=True).strip())
    except Exception:
        return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", choices=("dense", "kas_v2"), default="kas_v2")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--seq", type=int, default=64)
    ap.add_argument("--n-embd", type=int, default=256)
    ap.add_argument("--n-layer", type=int, default=2)
    ap.add_argument("--bank", type=int, default=32, help="number of fixed training sequences")
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    torch.manual_seed(a.seed)
    cfg = ModelConfig(vocab_size=131072, block_size=a.seq, n_layer=a.n_layer, n_head=4, n_embd=a.n_embd,
                      attn_impl="eager", head_mode=a.head, tie_embeddings=False, reversible=False)
    model = GPT(cfg).to(a.device).train()
    total, active = model.param_counts()

    g = torch.Generator().manual_seed(a.seed)
    weights = 1.0 / torch.arange(1, cfg.vocab_size + 1, dtype=torch.float64)       # Zipf over id rank
    perm = torch.randperm(cfg.vocab_size, generator=g)
    bank = perm[torch.multinomial(weights, a.bank * (a.seq + 1), replacement=True, generator=g)]
    bank = bank.view(a.bank, a.seq + 1)

    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, betas=(0.9, 0.95), weight_decay=0.0)
    losses, t0 = [], time.perf_counter()
    for step in range(a.steps):
        rows = bank[torch.randint(0, a.bank, (a.batch,), generator=g)].to(a.device)
        _, loss = model(rows[:, :-1], rows[:, 1:])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        losses.append(float(loss))
        if not torch.isfinite(loss):
            break
    seconds = time.perf_counter() - t0

    first, last = sum(losses[:10]) / min(10, len(losses)), sum(losses[-10:]) / min(10, len(losses))
    result = {
        "check": "kas_loss_down", "head_mode": a.head, "passed": bool(last < first and all(map(lambda v: v == v, losses))),
        "loss_first10_mean": first, "loss_last10_mean": last, "loss_step0": losses[0], "loss_final": losses[-1],
        "loss_every_25": {i: losses[i] for i in range(0, len(losses), 25)},
        "steps": len(losses), "seconds": round(seconds, 1),
        "params_total": total, "params_active": active,
        "prior_identity_counts_sha256": (model.prior_identity or {}).get("counts_verified_sha256"),
        "config": dict(batch=a.batch, seq=a.seq, n_embd=a.n_embd, n_layer=a.n_layer, bank=a.bank, lr=a.lr,
                       seed=a.seed, optimizer="torch.optim.AdamW(0.9, 0.95), wd 0", attn_impl="eager",
                       reversible=False, data="synthetic Zipf bank"),
        "device": a.device, "torch": torch.__version__, "python": platform.python_version(),
        "git_sha": git_sha(), "git_dirty": git_dirty(), "command": " ".join([sys.executable] + sys.argv),
    }
    text = json.dumps(result, indent=2)
    print(text)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
