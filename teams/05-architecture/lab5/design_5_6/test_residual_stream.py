"""The one-stream arm matches the model. The mixed arm adds only the 2 by 2 mixes."""

import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "teams" / "05-architecture" / "harness"))

from residual_stream import (  # noqa: E402
    LAYERS,
    STREAMS,
    build,
    new_mixes,
    split_data,
    two_stream_logits,
)


def test_one_stream_is_the_block_forward():
    model = build(0)
    model.eval()
    ids = torch.randint(0, 64, (2, 32))
    valid = torch.ones(2, 32, dtype=torch.bool)
    with torch.no_grad():
        hidden = model.embedding(ids)
        for block in model.blocks:
            hidden = block(hidden, valid)
        manual = model.head(model.norm(hidden))
        full = model(ids, valid)
    assert torch.equal(manual, full)


def test_held_out_sequences_are_disjoint():
    train, held = split_data(7)
    train_set = {tuple(row.tolist()) for row in train}
    assert all(tuple(row.tolist()) not in train_set for row in held)


def test_mix_starts_equal_and_adds_only_those_parameters():
    model = build(1)
    before = sum(p.numel() for p in model.parameters())
    mixes = new_mixes()
    assert len(mixes) == LAYERS
    for logit in mixes:
        weight = logit.softmax(-1)
        assert torch.allclose(weight, torch.full_like(weight, 1 / STREAMS))
    ids = torch.randint(0, 64, (2, 32))
    valid = torch.ones(2, 32, dtype=torch.bool)
    with torch.no_grad():
        logits = two_stream_logits(model, ids, valid, mixes)
    assert logits.shape == (2, 32, 64)
    assert sum(p.numel() for p in model.parameters()) == before
    assert sum(p.numel() for p in mixes) == LAYERS * STREAMS * STREAMS


def test_mixed_streams_are_not_the_same_forward():
    torch.manual_seed(2)
    model = build(2)
    model.eval()
    ids = torch.randint(0, 64, (2, 32))
    valid = torch.ones(2, 32, dtype=torch.bool)
    with torch.no_grad():
        one = model(ids, valid)
        two = two_stream_logits(model, ids, valid, new_mixes())
    assert one.shape == two.shape
    assert not torch.allclose(one, two)
