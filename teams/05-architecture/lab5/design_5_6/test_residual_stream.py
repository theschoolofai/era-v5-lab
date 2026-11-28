"""The one-stream arm matches the model. The two-stream arm adds no parameters."""

import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "teams" / "05-architecture" / "harness"))

from residual_stream import build, two_stream_logits  # noqa: E402


def test_one_stream_is_the_block_forward():
    """The one-stream arm is the block on main, not a second implementation."""
    model = build(0)
    model.eval()
    ids = torch.randint(0, 64, (2, 16))
    valid = torch.ones(2, 16, dtype=torch.bool)
    with torch.no_grad():
        x = model.embedding(ids)
        for block in model.blocks:
            x = block(x, valid)
        manual = model.head(model.norm(x))
        full = model(ids, valid)
    assert torch.equal(manual, full)


def test_two_stream_matches_shape_and_adds_no_parameters():
    model = build(1)
    before = sum(p.numel() for p in model.parameters())
    ids = torch.randint(0, 64, (2, 16))
    valid = torch.ones(2, 16, dtype=torch.bool)
    with torch.no_grad():
        logits = two_stream_logits(model, ids, valid)
    assert logits.shape == (2, 16, 64)
    assert sum(p.numel() for p in model.parameters()) == before


def test_two_stream_is_not_the_same_function_on_a_deeper_stack():
    """Four layers. A fixed mean of two streams is a different forward."""
    torch.manual_seed(2)
    model = build(2)
    model.eval()
    ids = torch.randint(0, 64, (2, 16))
    valid = torch.ones(2, 16, dtype=torch.bool)
    with torch.no_grad():
        one = model(ids, valid)
        two = two_stream_logits(model, ids, valid)
    assert one.shape == two.shape
    assert not torch.allclose(one, two)
