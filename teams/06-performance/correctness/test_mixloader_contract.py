"""Acceptance tests for the agreed W5 loader (``dataio.mixloader``, PR-A).

This file targets the interface in ``G6_W5_plan_p0_v2.md`` S3:

    make_loader(rank, world) -> loader
    state_dict / load_state_dict / next_batch_id / next / next_batch_full / add_skip
    next() -> ONE tensor (T+1 rows), so the contract hashes rows, not a tuple

The loader implementation is owned elsewhere; these tests only consume it. Until S3
lands, the tests skip. ``test_loader_contract.py`` keeps the checker honest in the
meantime with a synthetic fixture.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "07-infrastructure" / "ckpt" / "loader_contract.py"
WORLDS = (1, 2, 4)


def _load_contract():
    spec = importlib.util.spec_from_file_location("g6_loader_contract_mix", CONTRACT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract = _load_contract()


def _mixloader():
    module = pytest.importorskip("dataio.mixloader", reason="S3 (dataio/mixloader.py) has not landed")
    factory = getattr(module, "make_loader", None)
    if factory is None:
        pytest.skip("dataio.mixloader has no make_loader yet")
    return factory


@pytest.mark.parametrize("world", WORLDS)
def test_mixloader_passes_contract_at_world_1_2_4(world):
    factory = _mixloader()
    problems = contract.check(factory, steps=20, cut=7, world=world)
    assert problems == [], f"world={world}: {problems}"


def test_mixloader_next_returns_one_tensor():
    """A tuple would be hashed as one opaque row by the contract."""
    batch = _mixloader()(0, 1).next()
    assert hasattr(batch, "numpy"), "next() must return one tensor (S3)"
    assert batch.dim() == 2, f"next() must return [rows, T+1], got shape {tuple(batch.shape)}"


def test_mixloader_exposes_next_batch_full():
    loader = _mixloader()(0, 1)
    assert callable(getattr(loader, "next_batch_full", None)), "S3 requires next_batch_full()"
