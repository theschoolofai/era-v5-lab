"""Design task 5. One residual stream against several mixed streams.

The one-stream arm is the block on main. The mixed arm lives only in this
file. The first block reads the embedding twice and writes an attention
stream and an MoE stream. Every later block mixes those streams with a
learned 2 by 2, initialized to an equal mix. The mix is not in the trainer.

Train sequences and held-out sequences are disjoint. The score is
cross-entropy on the held-out sequences. Those tokens are synthetic. This is
not held-out bits per byte on heldout_v1, and it is not a 49M to 100M run.

Rates are the dry-run rates, not retuned for this net.

Command, from the repository root:

    python teams/05-architecture/lab5/design_5_6/residual_stream.py
"""

import json
import platform
import resource
import sys
import time
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "teams" / "05-architecture" / "harness"))

from week2.model import LanguageModel  # noqa: E402
from week2.optim import Muon  # noqa: E402

MUON_LR = 0.006
ADAMW_LR = 1e-3
SEEDS = (1234, 1235, 1236)
STEPS = 240
BATCH = 8
SEQ = 32
TRAIN_N = 128
HELD_N = 32
LAYERS = 8
WIDTH = 64
VOCAB = 64
POS = 8
STREAMS = 2


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


def new_mixes():
    """A 2 by 2 mix for every block after the split, plus one for the read.

    Zeros softmax to an equal mix. The first block has no mix: both streams
    are still the embedding, so a mix there cannot move.
    """
    return [nn.Parameter(torch.zeros(STREAMS, STREAMS)) for _ in range(LAYERS)]


def mix_streams(streams, logit):
    weight = logit.softmax(dim=-1)
    return torch.einsum("ij,jbtc->ibtc", weight, streams)


def two_stream_logits(model, ids, valid, mixes):
    hidden = model.embedding(ids)
    first = model.blocks[0]
    streams = torch.stack(
        [
            hidden + first.attn(first.n1(hidden), residual=hidden),
            hidden + first.moe(first.n2(hidden), valid),
        ],
        dim=0,
    )
    for block, logit in zip(model.blocks[1:], mixes[:-1]):
        mixed = mix_streams(streams, logit)
        attn = block.attn(block.n1(mixed[0]), residual=mixed[0])
        moe = block.moe(block.n2(mixed[1]), valid)
        streams = torch.stack([streams[0] + attn, streams[1] + moe], dim=0)
    read = mix_streams(streams, mixes[-1]).mean(0)
    return model.head(model.norm(read))


def sequences(seed, n):
    """Each later token is the sum of the two before it. The rule is shared.

    Train and held-out differ in the first two tokens. A model that learns the
    rule can score the held-out rows. Uniform noise cannot.
    """
    generator = torch.Generator()
    generator.manual_seed(seed)
    out = torch.empty(n, SEQ, dtype=torch.long)
    out[:, 0] = torch.randint(0, VOCAB, (n,), generator=generator)
    out[:, 1] = torch.randint(0, VOCAB, (n,), generator=generator)
    for t in range(2, SEQ):
        out[:, t] = (out[:, t - 2] + out[:, t - 1]) % VOCAB
    return out


def split_data(seed):
    """Distinct sequences from the same rule. The held-out rows are never updated on."""
    pool = sequences(seed, TRAIN_N + HELD_N + 64)
    unique = []
    seen = set()
    for row in pool:
        key = tuple(row.tolist())
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    if len(unique) < TRAIN_N + HELD_N:
        raise RuntimeError("not enough distinct sequences")
    train = torch.stack(unique[:TRAIN_N])
    held = torch.stack(unique[TRAIN_N : TRAIN_N + HELD_N])
    return train, held


def cross_entropy(logits, ids):
    return F.cross_entropy(logits[:, :-1].reshape(-1, VOCAB), ids[:, 1:].reshape(-1))


def optimizers(model, mixes):
    named = list(model.named_parameters())
    muon = [p for _, p in named if p.ndim == 2]
    adam = [p for _, p in named if p.ndim != 2]
    if mixes is not None:
        muon = muon + list(mixes)
    if any(p.ndim > 2 for p in muon):
        raise RuntimeError("a parameter above 2D is not in this test")
    return (
        Muon(muon, lr=MUON_LR, momentum=0.95, nesterov=True, ns_steps=5, weight_decay=0.0),
        torch.optim.AdamW(adam, lr=ADAMW_LR, weight_decay=0.0),
    )


def grad_coverage(model, mixes):
    none_grad = []
    zero_grad = []
    pairs = list(model.named_parameters())
    if mixes is not None:
        pairs = pairs + [(f"mix.{i}", p) for i, p in enumerate(mixes)]
    for name, param in pairs:
        if param.grad is None:
            none_grad.append(name)
        elif float(param.grad.detach().norm()) == 0.0:
            zero_grad.append(name)
    return {"grad_none": none_grad, "grad_zero": zero_grad}


def held_out_loss(model, mixes, held, forward):
    was_training = model.training
    model.eval()
    total = 0.0
    count = 0
    with torch.no_grad():
        for start in range(0, len(held), BATCH):
            ids = held[start : start + BATCH]
            valid = torch.ones_like(ids, dtype=torch.bool)
            loss = cross_entropy(forward(model, ids, valid, mixes), ids)
            total += float(loss) * len(ids)
            count += len(ids)
    model.train(was_training)
    return total / count


def run_arm(model, train, held, forward, mixes):
    muon, adam = optimizers(model, mixes)
    coverage = None
    order = torch.arange(len(train))
    started = time.perf_counter()
    before = held_out_loss(model, mixes, held, forward)
    train_before = held_out_loss(model, mixes, train, forward)
    for step in range(STEPS):
        pick = order[torch.randint(0, len(order), (BATCH,))]
        ids = train[pick]
        valid = torch.ones_like(ids, dtype=torch.bool)
        muon.zero_grad(set_to_none=True)
        adam.zero_grad(set_to_none=True)
        loss = cross_entropy(forward(model, ids, valid, mixes), ids)
        loss.backward()
        if step == 0:
            coverage = grad_coverage(model, mixes)
        muon.step()
        adam.step()
    elapsed = time.perf_counter() - started
    after = held_out_loss(model, mixes, held, forward)
    train_after = held_out_loss(model, mixes, train, forward)
    tokens = BATCH * SEQ * STEPS
    return {
        "train_before": train_before,
        "train_after": train_after,
        "held_out_before": before,
        "held_out_after": after,
        "seconds": round(elapsed, 4),
        "synthetic_tokens_per_second": round(tokens / elapsed, 2),
        "grad_coverage_after_first_backward": coverage,
    }


def one_forward(model, ids, valid, mixes):
    return model(ids, valid)


def one_seed(seed):
    train, held = split_data(seed)
    model = build(seed)
    start = {k: v.detach().clone() for k, v in model.state_dict().items()}
    one = run_arm(model, train, held, one_forward, None)
    model.load_state_dict(start)
    mixes = new_mixes()
    two = run_arm(model, train, held, two_stream_logits, mixes)
    mix_rows = []
    with torch.no_grad():
        for logit in mixes:
            mix_rows.append([[round(x, 4) for x in row] for row in logit.softmax(-1).tolist()])
    return {
        "seed": seed,
        "train_sequences": len(train),
        "held_out_sequences": len(held),
        "one_stream": one,
        "mixed_streams": two,
        "mix_after_training": mix_rows,
    }


def main():
    rows = [one_seed(seed) for seed in SEEDS]
    model = build(SEEDS[0])
    record = {
        "what": "design task 5, one stream against a learned mix of two streams",
        "one_stream": "teams/05-architecture/harness/week2/model.py Block.forward",
        "mixed_streams": "first block splits the embedding, later blocks use a learned 2 by 2 mix, this file only",
        "score": "cross-entropy on held-out sequences from the same two-token sum rule. Not heldout_v1 bits per byte.",
        "depth": LAYERS,
        "width": WIDTH,
        "steps": STEPS,
        "batch": BATCH,
        "seq": SEQ,
        "train_sequences": TRAIN_N,
        "held_out_sequences": HELD_N,
        "seeds": list(SEEDS),
        "muon_lr": MUON_LR,
        "adamw_lr": ADAMW_LR,
        "rates_are": "dry-run rates, not retuned for this net",
        "one_stream_parameters": sum(p.numel() for p in model.parameters()),
        "mix_parameters": LAYERS * STREAMS * STREAMS,
        "what_this_cannot_tell_you": "a 49M to 100M model, the real data mix, and heldout_v1 bits per byte",
        "torch": torch.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "command": "python teams/05-architecture/lab5/design_5_6/residual_stream.py",
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "seeds_ran": rows,
    }
    out = HERE / "residual_stream_result.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(out)
    for row in rows:
        print(
            row["seed"],
            "one",
            round(row["one_stream"]["held_out_before"], 4),
            "->",
            round(row["one_stream"]["held_out_after"], 4),
            "mixed",
            round(row["mixed_streams"]["held_out_before"], 4),
            "->",
            round(row["mixed_streams"]["held_out_after"], 4),
        )


if __name__ == "__main__":
    main()
