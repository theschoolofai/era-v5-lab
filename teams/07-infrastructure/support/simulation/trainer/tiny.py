"""Tiny model and synthetic data loader for testing the checkpoint, queue and health code.

In simple words: a toy language model small enough to train on a laptop CPU in seconds. It has the same
kinds of state as the real model (trainable weights, a frozen table like KE2's, optimizer state, a data
position), so the checkpoint code is tested on everything it has to save.

The real sizes in config_v0.yaml are still empty (TSAI fills them on 31 Oct); this file does not use them.
"""
import hashlib

import torch
import torch.nn as nn
import torch.nn.functional as F

VOCAB, SEQ, DIM = 256, 32, 64


class TinyLM(nn.Module):
    def __init__(self, seed: int = 1234):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        self.embed = nn.Embedding(VOCAB, DIM)
        # Frozen, non-trained table, standing in for the Kronecker (KE2) tables: hashed in the manifest.
        self.register_buffer("ke2_table", torch.randn(VOCAB, DIM, generator=g) * 0.02)
        self.ff1 = nn.Linear(DIM, 4 * DIM)
        self.ff2 = nn.Linear(4 * DIM, DIM)
        self.norm = nn.LayerNorm(DIM)
        self.head = nn.Linear(DIM, VOCAB, bias=False)
        self.head_mtp = nn.Linear(DIM, VOCAB, bias=False)  # t+2 head (config: loss.train_on=ntp, loss_mtp logged)

    def forward(self, x):
        h = self.embed(x) + self.ke2_table[x]
        h = h + self.ff2(F.gelu(self.ff1(self.norm(h))))
        return self.head(h), self.head_mtp(h)


FROZEN_KEYS = ("ke2_table",)


def lm_loss(model, batch):
    logits, logits_mtp = model(batch[:, :-1])
    ntp = F.cross_entropy(logits.reshape(-1, VOCAB), batch[:, 1:].reshape(-1))
    mtp = F.cross_entropy(logits_mtp[:, :-1].reshape(-1, VOCAB), batch[:, 2:].reshape(-1))
    return ntp, mtp


class SyntheticLoader:
    """Deterministic data: global batch number p is always the same tokens, on any world size.

    `position` is the ledger offset: the authority on where we are in the data (ADR 0001 §7),
    not the step counter. `skip` holds batch numbers a rollback chose to skip.
    """

    def __init__(self, seed: int, global_batch: int, rank: int, world: int):
        assert global_batch % world == 0, "global batch must divide by world size"
        self.seed, self.global_batch, self.rank, self.world = seed, global_batch, rank, world
        self.position = 0
        self.skip = set()
        # Which data this is: the real loader hashes its shard list; ours is generated from the seed. A state
        # saved on other data must be refused, not resumed (Mallik's manifest field, team 07).
        self.manifest = hashlib.sha256(f"synthetic:{seed}:{VOCAB}:{SEQ}".encode()).hexdigest()

    def _global(self, p: int) -> torch.Tensor:
        g = torch.Generator().manual_seed(self.seed * 1_000_003 + p)
        return torch.randint(0, VOCAB, (self.global_batch, SEQ + 1), generator=g)

    def _next_pos(self, p: int) -> int:
        while p in self.skip:
            p += 1
        return p

    def next(self) -> torch.Tensor:
        self.position = self._next_pos(self.position)
        b = self._global(self.position)[self.rank::self.world]
        self.position += 1
        return b

    def next_batch_id(self) -> dict:
        p = self._next_pos(self.position)
        return {"position": p, "sha256": hashlib.sha256(self._global(p).numpy().tobytes()).hexdigest()}

    def add_skip(self, n: int):
        p = self.position
        for _ in range(n):
            p = self._next_pos(p)
            self.skip.add(p)
            p += 1

    def state_dict(self) -> dict:
        return {"position": self.position, "skip": sorted(self.skip), "manifest": self.manifest}

    def load_state_dict(self, d: dict):
        if d.get("manifest", self.manifest) != self.manifest:
            raise ValueError(f"saved on data manifest {d['manifest'][:12]}, this loader reads {self.manifest[:12]}")
        self.position = d["position"]
        self.skip = set(d["skip"])


def probe_batch(seed: int) -> torch.Tensor:
    """A fixed held-out batch, never used for training."""
    g = torch.Generator().manual_seed(seed + 999_983)
    return torch.randint(0, VOCAB, (8, SEQ + 1), generator=g)


def make_probe_fn(seed: int):
    pb = probe_batch(seed)

    def probe(model) -> float:
        m = getattr(model, "module", model)
        was = m.training
        m.eval()
        with torch.no_grad():
            ntp, _ = lm_loss(m, pb.to(next(m.parameters()).device))
        m.train(was)
        return ntp.item()

    return probe
