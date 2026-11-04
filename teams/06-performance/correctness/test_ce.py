"""Chunked cross-entropy against the plain path, and against a definition written here.

GPT(ce_impl="chunked") must give the same loss and the same gradients as ce_impl="torch" for every target pattern the
trainer can send: all positions counted, some positions masked with IGNORE_INDEX (SFT loss masks), a masked row, one
position left, none left, and token counts that ce_chunks does not divide. A masked position counts in neither the sum nor
the divisor. No tokenizer is needed: the model is tiny and uses a plain embedding table.
"""
from __future__ import annotations

import pytest
import torch
import torch.nn.functional as F

from models.config import ModelConfig
from models.gpt import GPT, IGNORE_INDEX

VOCAB = 97
BLOCK = 16


def _models(device, chunks):
    cfg = dict(vocab_size=VOCAB, block_size=BLOCK, n_layer=1, n_head=2, n_embd=32)
    torch.manual_seed(0)
    plain = GPT(ModelConfig(**cfg, ce_impl="torch")).to(device).train()
    chunked = GPT(ModelConfig(**cfg, ce_impl="chunked", ce_chunks=chunks)).to(device).train()
    chunked.load_state_dict(plain.state_dict())
    return plain, chunked


def _data(device, B, T, masked=()):
    g = torch.Generator().manual_seed(1)
    idx = torch.randint(0, VOCAB, (B, T), generator=g).to(device)
    y = torch.randint(0, VOCAB, (B, T), generator=g).to(device)
    for b, t in masked:
        y[b, t] = IGNORE_INDEX
    return idx, y


def _mean_ce(logits, y):
    """Mean of -log p(target) over the non-ignored positions, from the definition, in fp64."""
    lp = torch.log_softmax(logits.double().reshape(-1, logits.shape[-1]), dim=-1)
    y = y.reshape(-1)
    keep = y != IGNORE_INDEX
    return -lp[keep, y[keep]].mean()


def _grads(model):
    return {n: p.grad.clone() for n, p in model.named_parameters() if p.grad is not None}


def _loss_and_grads(model, idx, y):
    model.zero_grad(set_to_none=True)
    loss = model(idx, y)[1]
    loss.backward()
    return loss.detach(), _grads(model)


def _same(a, b, what):
    torch.testing.assert_close(a, b, rtol=1e-5, atol=1e-6, msg=lambda m: f"{what}: {m}")


MASKS = {
    "none": (),
    "scattered": ((0, 0), (0, 5), (1, 3), (1, 15)),
    "half": tuple((b, t) for b in range(2) for t in range(8)),
    "one_row": tuple((0, t) for t in range(16)),
    "one_left": tuple((b, t) for b in range(2) for t in range(16) if (b, t) != (1, 7)),
}


@pytest.mark.parametrize("mask", MASKS)
def test_chunked_matches_plain_and_definition(device, mask):
    plain, chunked = _models(device, chunks=4)
    idx, y = _data(device, 2, 16, MASKS[mask])
    with torch.no_grad():
        reference = _mean_ce(plain(idx)[0], y)         # logits of the plain model, loss from the definition
    lp, gp = _loss_and_grads(plain, idx, y)
    lc, gc = _loss_and_grads(chunked, idx, y)
    _same(lp.double(), reference, f"plain vs definition ({mask})")
    _same(lc.double(), reference, f"chunked vs definition ({mask})")
    assert gp.keys() == gc.keys()
    for name in gp:
        _same(gc[name], gp[name], f"gradient of {name} ({mask})")


@pytest.mark.parametrize("B, T, chunks", [(3, 7, 4), (1, 5, 8), (2, 16, 3), (2, 16, 32)])
def test_chunked_when_chunks_do_not_divide_the_token_count(device, B, T, chunks):
    plain, chunked = _models(device, chunks=chunks)
    idx, y = _data(device, B, T, masked=((0, 1), (B - 1, T - 1)))
    lp, gp = _loss_and_grads(plain, idx, y)
    lc, gc = _loss_and_grads(chunked, idx, y)
    _same(lc, lp, f"loss B={B} T={T} chunks={chunks}")
    for name in gp:
        _same(gc[name], gp[name], f"gradient of {name} B={B} T={T} chunks={chunks}")


def test_chunked_loss_is_zero_when_every_target_is_ignored(device):
    _, chunked = _models(device, chunks=4)
    idx, _ = _data(device, 2, 16)
    y = torch.full((2, 16), IGNORE_INDEX, device=device)
    loss, grads = _loss_and_grads(chunked, idx, y)
    assert loss.item() == 0.0, "no target counts, so the loss is 0 (the plain path gives NaN here)"
    assert all(torch.isfinite(g).all() and not g.any() for g in grads.values()), "no target, so no gradient"
