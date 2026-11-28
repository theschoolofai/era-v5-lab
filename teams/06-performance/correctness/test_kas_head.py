"""model.head_mode = "kas_v2" (models/kas_v2.py): Team 6's copy of Team 5's KAS V2 head, wired into GPT.

Parity: the copy gives the same logits and gradients as teams/05-architecture/harness/week2/kas_v2.py for the same
weights, and initialize_prior gives the same head.unigram. GPT: default head_mode stays dense; kas_v2 returns
contiguous fp32 [B, T, V] logits, gradients reach every KAS parameter, chunked CE equals the plain loss, and the
config refuses settings the head cannot serve (tied weight, padded vocab, fused CE).
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
import torch
import torch.nn.functional as F

from models.config import ModelConfig
from models.gpt import GPT
from models.kas_v2 import KASCodec, KASHead, initialize_prior, load_kas_table

TEAM5 = Path(__file__).resolve().parents[2] / "05-architecture"
VOCAB = 512
SMALL = dict(vocab_size=VOCAB, block_size=16, n_layer=2, n_head=4, n_embd=64, attn_impl="eager",
             head_mode="kas_v2", kas_prior=False)
HEAD_PARAMS = ("W_out", "beta", "unigram", "tok_u", "tok_c")


def team5():
    """Team 5's original module (teams/05-architecture/harness/week2/kas_v2.py), imported read-only."""
    if str(TEAM5) not in sys.path:
        sys.path.insert(0, str(TEAM5))
    return importlib.import_module("harness.week2.kas_v2")


def random_table(vocab=VOCAB):
    """Random bytes with lengths 1..8, like real BPE tokens."""
    g = torch.Generator().manual_seed(0)
    return (torch.randint(0, 256, (vocab, 32), generator=g, dtype=torch.uint8),
            torch.randint(1, 9, (vocab,), generator=g))


def small_gpt(**over):
    torch.manual_seed(0)
    return GPT(ModelConfig(**{**SMALL, **over}), head_bytes=random_table())


@pytest.mark.parametrize("training", [False, True])
def test_copy_matches_team5_head(training):
    ref_mod = team5()
    rows, lengths = random_table()
    ours = KASHead(rows, lengths, 64, KASCodec()).train(training)
    ref = ref_mod.KASHead(rows, lengths, 64, ref_mod.KASCodec()).train(training)
    ref.load_state_dict(ours.state_dict())
    x = torch.randn(3, 5, 64)
    torch.manual_seed(7)
    a = ours(x)
    torch.manual_seed(7)                     # same row-dropout mask in training mode
    b = ref(x)
    assert torch.equal(a, b)
    grad = torch.randn_like(a)
    a.backward(grad)
    b.backward(grad)
    for name in HEAD_PARAMS:
        assert torch.equal(getattr(ours, name).grad, getattr(ref, name).grad), name


def test_prior_matches_team5_on_the_real_table():
    ref_mod = team5()
    rows, lengths = load_kas_table(131072)
    assert rows.shape == (131072, 32) and int(lengths.min()) >= 1 and int(lengths.max()) <= 32
    ours = KASHead(rows, lengths, 8, KASCodec())
    ref = ref_mod.KASHead(rows, lengths, 8, ref_mod.KASCodec())
    ident = initialize_prior(ours, {})
    ref_ident = ref_mod.initialize_prior(ref, {})
    assert ident == ref_ident
    assert torch.equal(ours.unigram, ref.unigram)
    assert ours.unigram.abs().sum() > 0 and abs(float(ours.unigram.detach().double().mean())) < 1e-5


def test_default_head_is_dense():
    cfg = ModelConfig(**{**SMALL, "head_mode": "dense"})
    assert ModelConfig().head_mode == "dense"
    assert isinstance(GPT(cfg).head, torch.nn.Linear)


def test_gpt_kas_logits_and_grads():
    model = small_gpt().train()
    idx = torch.randint(0, VOCAB, (2, 16))
    logits, loss = model(idx, idx)
    assert logits.shape == (2, 16, VOCAB) and logits.dtype == torch.float32 and logits.is_contiguous()
    assert torch.isfinite(logits).all() and torch.isfinite(loss)
    loss.backward()
    for name in HEAD_PARAMS:
        g = getattr(model.head, name).grad
        assert g is not None and torch.isfinite(g).all() and g.abs().sum() > 0, name
    assert model.kas_codec.G.dtype == torch.float64          # the codec is a submodule: it moves with .to()


def test_chunked_ce_matches_plain_loss():
    idx = torch.randint(0, VOCAB, (2, 16))
    plain = small_gpt(ce_impl="torch").eval()
    chunked = small_gpt(ce_impl="chunked", ce_chunks=4).eval()
    chunked.load_state_dict(plain.state_dict())
    _, a = plain(idx, idx)
    _, b = chunked(idx, idx)
    torch.testing.assert_close(a, b)
    ref = F.cross_entropy(plain.head(plain.ln_f(plain.blocks[1](plain.blocks[0](plain.embed(idx))))).reshape(-1, VOCAB),
                          idx.reshape(-1))
    torch.testing.assert_close(a, ref)


def test_kas_active_head_params():
    """KAS head = d x 2048 + 64 x d + V x 64; dense = V x d. tok_u is V x 64 at any width, so KAS is smaller only
    when d > ~66: at d=64 it is larger, at d=256 about 3.8x smaller."""
    for width, smaller in ((64, False), (256, True)):
        over = dict(vocab_size=131072, n_embd=width, n_layer=1)
        dense = GPT(ModelConfig(**{**SMALL, **over, "head_mode": "dense", "tie_embeddings": False}))
        kas = GPT(ModelConfig(**{**SMALL, **over}), head_bytes=random_table(131072))
        head = 131072 * 64 + width * 2048 + 64 * width
        assert kas.param_counts()[1] - dense.param_counts()[1] == head - 131072 * width
        assert (kas.param_counts()[1] < dense.param_counts()[1]) is smaller


@pytest.mark.parametrize("bad", [dict(tie_embeddings=True), dict(vocab_pad_multiple=128), dict(ce_impl="fused"),
                                 dict(head_mode="kas")])
def test_config_refuses(bad):
    with pytest.raises(AssertionError):
        ModelConfig(**{**SMALL, **bad})


def test_chunked_ce_train_mode_recompute_reuses_each_chunks_mask():
    """In training mode tok_u row dropout is drawn once per head call, so ce_impl=chunked draws one mask per chunk
    (Team 5's correction_row_dropout: "the caller owns invocation timing"). The checkpointed backward recomputes each
    chunk; it must reuse that chunk's mask, i.e. give the same gradients as the same chunks computed without
    checkpointing from the same RNG state."""
    idx = torch.randint(0, VOCAB, (2, 16))
    model = small_gpt(ce_impl="chunked", ce_chunks=4).train()

    torch.manual_seed(11)
    _, loss = model(idx, idx)
    loss.backward()
    ckpt = {n: p.grad.clone() for n, p in model.named_parameters()}

    model.zero_grad(set_to_none=True)
    torch.manual_seed(11)
    x = model.ln_f(model.blocks[1](model.blocks[0](model.embed(idx)))).reshape(32, -1)
    y = idx.reshape(32)
    total = sum(F.cross_entropy(model.head(xc), yc, reduction="sum") for xc, yc in zip(x.chunk(4), y.chunk(4)))
    ref = total / 32
    ref.backward()
    torch.testing.assert_close(loss, ref)
    for n, p in model.named_parameters():
        torch.testing.assert_close(ckpt[n], p.grad, msg=n)


def test_reversible_stack_with_kas_head_trains():
    """Team 6 runs a reversible stack; the KAS head sits after it (after ln_f), so it is never recomputed by the
    reversible backward. Every parameter, head included, gets a finite non-zero gradient with reversible on."""
    idx = torch.randint(0, VOCAB, (2, 16))
    for impl in ("two_pass", "one_pass"):
        model = small_gpt(reversible=True, rev_impl=impl).train()
        _, loss = model(idx, idx)
        loss.backward()
        for n, p in model.named_parameters():
            assert p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0, (impl, n)
