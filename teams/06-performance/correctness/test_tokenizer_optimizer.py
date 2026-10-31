"""Integration coverage for real Brahmic token bytes, KE, and optimizer updates.

The focused tokenizer and optimizer contracts live in test_tokenizer.py and
test_optimizer.py. This module keeps the cross-component path covered without
duplicating those unit tests.
"""
import os

import pytest
import torch
from torch import nn

from dataio.tokenizer import BrahmicTokenizer
from models.ke1 import KroneckerEmbedding
from models.optim import Muon, build_optimizer

fixture = pytest.fixture


@fixture(scope="module")
def tokenizer():
    return BrahmicTokenizer(os.environ.get("BRAHMIC_TOKENIZER_PATH"))


class _TinyKeModel(nn.Module):
    def __init__(self, token_bytes):
        super().__init__()
        self.embedding = KroneckerEmbedding(token_bytes, d_model=8)
        self.blocks = nn.ModuleList([nn.Linear(8, 8, bias=False)])
        self.norm = nn.LayerNorm(8)
        self.head = nn.Linear(8, 1)

    def forward(self, token_ids):
        x = self.embedding(token_ids)
        x = torch.tanh(self.blocks[0](x))
        return self.head(self.norm(x))


def test_real_tokenizer_ke_model_takes_optimizer_step(tokenizer):
    token_ids = tokenizer.encode("\u092d\u093e\u0930\u0924 \u090f\u0915 \u0926\u0947\u0936 \u0939\u0948")
    assert token_ids == [66526, 2420, 13092, 732]

    model = _TinyKeModel(tokenizer.token_bytes())
    opt = build_optimizer(model, {
        "name": "muon", "lr": 0.001, "muon_lr": 0.02, "weight_decay": 0.01,
    })
    optimizers = dict(opt.named)
    assert isinstance(optimizers["opt.muon"], Muon)
    assert isinstance(optimizers["opt.adamw"], torch.optim.AdamW)

    ids = torch.tensor([token_ids], dtype=torch.long)
    before = model.embedding.proj.weight.detach().clone()
    loss = model(ids).square().mean()
    loss.backward()
    opt.step()

    assert torch.isfinite(loss)
    assert model.embedding.proj.weight.grad is not None
    assert not torch.equal(model.embedding.proj.weight, before)
    assert all(torch.isfinite(parameter).all() for parameter in model.parameters())
