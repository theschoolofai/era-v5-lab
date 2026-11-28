"""Design task 5 small test. One residual stream against a two-stream mix.

The one-stream arm is the block on main: pre-norm, then add the sublayer
back onto the same stream. The two-stream arm lives only in this file.
Attention writes one stream and the MoE writes the other. A fixed mean mixes
them. No new parameters.

Synthetic tokens. The loss is cross-entropy on those tokens. It is not
held-out bits per byte, and it is not a 49M to 100M run.

Command, from the repository root:

    python teams/05-architecture/lab5/design_5_6/residual_stream.py
"""

import json
import platform
import sys
import time
from pathlib import Path

import torch
from torch.nn import functional as F

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "teams" / "05-architecture" / "harness"))

from week2.model import LanguageModel  # noqa: E402
from week2.optim import Muon  # noqa: E402

# Smoke step sizes so the loss can move on this tiny net.
# Not a learning-rate recommendation. The Muon estimate on the dry run stays 0.006.
SMOKE_MUON_LR = 0.02
SMOKE_ADAMW_LR = 1e-3
SEEDS = (1234, 1235)
STEPS = 20
BATCH = 4
SEQ = 16
LAYERS = 4
WIDTH = 32
VOCAB = 64
POS = 8


def spec():
    return {
        "rope_theta": 10000.0,
        "rotary_fraction": 1.0,
        "norm_eps": 1e-5,
        "moe": {
            "num_experts": 4,
            "num_shared": 1,
            "top_k": 2,
            "ffn_hidden": WIDTH * 2,
            "bias": False,
            "bias_gamma": 0.0,
        },
        "attn_impl": "eager",
        "mtp": False,
        "vocab_size": VOCAB,
        "n_layer": LAYERS,
        "n_head": 4,
        "n_kv_head": 2,
        "n_embd": WIDTH,
        "head_mode": "dense",
    }


def byte_table(vocab, pos):
    rows = torch.arange(vocab * pos, dtype=torch.uint8).reshape(vocab, pos)
    lengths = torch.full((vocab,), pos, dtype=torch.long)
    return rows, lengths


def build(seed):
    torch.manual_seed(seed)
    rows, lengths = byte_table(VOCAB, POS)
    model = LanguageModel(spec(), rows, lengths)
    model.train()
    return model


def two_stream_logits(model, ids, valid):
    """Attention and the MoE keep separate streams. The read is their mean."""
    h = model.embedding(ids)
    u = h.clone()
    for block in model.blocks:
        mix = 0.5 * (h + u)
        h = h + block.attn(block.n1(mix), residual=mix)
        u = u + block.moe(block.n2(mix), valid)
    return model.head(model.norm(0.5 * (h + u)))


def batch(seed):
    g = torch.Generator()
    g.manual_seed(seed)
    ids = torch.randint(0, VOCAB, (BATCH, SEQ), generator=g)
    valid = torch.ones(BATCH, SEQ, dtype=torch.bool)
    return ids, valid


def cross_entropy(logits, ids):
    return F.cross_entropy(logits[:, :-1].reshape(-1, VOCAB), ids[:, 1:].reshape(-1))


def optimizers(model):
    named = list(model.named_parameters())
    muon = [p for _, p in named if p.ndim == 2]
    adam = [p for _, p in named if p.ndim != 2]
    if any(p.ndim > 2 for p in muon):
        raise RuntimeError("a parameter above 2D is not in this test")
    return (
        Muon(muon, lr=SMOKE_MUON_LR, momentum=0.95, nesterov=True, ns_steps=5, weight_decay=0.0),
        torch.optim.AdamW(adam, lr=SMOKE_ADAMW_LR, weight_decay=0.0),
    )


def grad_coverage(model):
    none_grad = []
    zero_grad = []
    for name, p in model.named_parameters():
        if p.grad is None:
            none_grad.append(name)
        elif float(p.grad.detach().norm()) == 0.0:
            zero_grad.append(name)
    return {"grad_none": none_grad, "grad_zero": zero_grad}


def run_arm(model, ids, valid, forward):
    muon, adam = optimizers(model)
    losses = []
    coverage = None
    started = time.perf_counter()
    for step in range(STEPS):
        muon.zero_grad(set_to_none=True)
        adam.zero_grad(set_to_none=True)
        loss = cross_entropy(forward(model, ids, valid), ids)
        loss.backward()
        if step == 0:
            coverage = grad_coverage(model)
        muon.step()
        adam.step()
        losses.append(float(loss.detach()))
    elapsed = time.perf_counter() - started
    tokens = BATCH * SEQ * STEPS
    return {
        "loss_first": losses[0],
        "loss_last": losses[-1],
        "seconds": round(elapsed, 4),
        "synthetic_tokens_per_second": round(tokens / elapsed, 2),
        "grad_coverage_after_first_backward": coverage,
    }


def one_seed(seed):
    ids, valid = batch(seed)
    model = build(seed)
    start = {k: v.detach().clone() for k, v in model.state_dict().items()}
    one = run_arm(model, ids, valid, lambda m, i, v: m(i, v))
    model.load_state_dict(start)
    two = run_arm(model, ids, valid, two_stream_logits)
    return {
        "seed": seed,
        "one_stream": one,
        "two_stream_fixed_mean": two,
    }


def main():
    rows = [one_seed(seed) for seed in SEEDS]
    model = build(SEEDS[0])
    record = {
        "what": "design task 5 small test",
        "one_stream": "teams/05-architecture/harness/week2/model.py Block.forward",
        "two_stream": "attention stream and MoE stream, fixed mean, no new parameters, this file only",
        "tokens": "synthetic. Not held-out bits per byte.",
        "depth": LAYERS,
        "width": WIDTH,
        "steps": STEPS,
        "batch": BATCH,
        "seq": SEQ,
        "seeds": list(SEEDS),
        "smoke_muon_lr": SMOKE_MUON_LR,
        "smoke_adamw_lr": SMOKE_ADAMW_LR,
        "rates_are": "smoke step sizes, not a learning-rate recommendation",
        "parameters": sum(p.numel() for p in model.parameters()),
        "torch": torch.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "command": "python teams/05-architecture/lab5/design_5_6/residual_stream.py",
        "what_this_cannot_tell_you": "depth at the real model, scale, and the data mix",
        "seeds_ran": rows,
    }
    out = HERE / "residual_stream_result.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(out)
    for row in rows:
        print(
            row["seed"],
            "one",
            round(row["one_stream"]["loss_first"], 4),
            "->",
            round(row["one_stream"]["loss_last"], 4),
            "two",
            round(row["two_stream_fixed_mean"]["loss_first"], 4),
            "->",
            round(row["two_stream_fixed_mean"]["loss_last"], 4),
        )


if __name__ == "__main__":
    main()
