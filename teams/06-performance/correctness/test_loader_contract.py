"""Independent tests of the Team 7 loader contract (ADR 0001 section 7).

The subject is ``teams/07-infrastructure/ckpt/loader_contract.py`` and the deterministic
synthetic factory in ``dataio/synthetic_loader.py``. The production loader
(``dataio/loader.py``) is not modified or reimplemented here.

What is proven:
  * the exact contract checker passes at world sizes 1, 2 and 4;
  * row k of batch N depends only on (seed, N), never on rank, world or restart;
  * ``next_batch_id()`` does not consume and hashes the rows ``next()`` returns;
  * every rank saves the same JSON-serialisable global state;
  * a JSON round-trip resumes exactly, and ``add_skip(2)`` skips two batches;
  * a state from another manifest is rejected;
  * the reshard continuation at 4 -> 2 is the same global batch;
  * the checker itself rejects a per-rank offset and a consuming peek, so a green
    result is not vacuous.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import torch

from dataio.synthetic_loader import SyntheticContractLoader, global_batch, make_loader

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "07-infrastructure" / "ckpt" / "loader_contract.py"


def _load_contract():
    spec = importlib.util.spec_from_file_location("g6_loader_contract", CONTRACT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract = _load_contract()


def _row_bytes(batch: torch.Tensor) -> list:
    return [row.numpy().tobytes() for row in batch]


@pytest.mark.parametrize("world", [1, 2, 4])
def test_contract_checker_passes_at_world_1_2_4(world):
    problems = contract.check(make_loader, steps=10, cut=3, world=world)
    assert problems == [], f"world={world}: {problems}"


def test_rows_depend_only_on_seed_and_global_batch():
    """World size and rank select a slice; they do not change the rows in that slice."""
    one = make_loader(0, 1)
    four = make_loader(2, 4)
    for _ in range(3):
        one.next()
        four.next()

    whole = one.next()
    local = four.next()

    assert torch.equal(local, whole[4:6]), "rank 2 of 4 must be rows [4, 6) of the same global batch"
    assert torch.equal(torch.cat([make_loader(r, 4).next() for r in range(4)]), global_batch(0))


def test_next_returns_one_tensor_not_a_tuple():
    """The contract hashes batch content; a tuple would be hashed as one opaque row."""
    batch = make_loader(0, 1).next()
    assert hasattr(batch, "numpy"), "next() must return one tensor (the contract's row hashing)"
    assert batch.dim() == 2


def test_next_batch_id_does_not_consume_and_hashes_the_next_rows():
    loader = make_loader(1, 2)

    peek = loader.next_batch_id()
    assert loader.next_batch_id() == peek, "a second peek must return the same value"
    assert peek["position"] == 0
    assert isinstance(peek["sha256"], str) and len(peek["sha256"]) == 64

    batch = loader.next()
    assert hashlib.sha256(batch.numpy().tobytes()).hexdigest() == peek["sha256"]
    assert loader.next_batch_id()["position"] == 1


def test_every_rank_saves_the_same_json_state():
    states = []
    for rank in range(4):
        loader = make_loader(rank, 4)
        for _ in range(5):
            loader.next()
        state = json.loads(json.dumps(loader.state_dict()))
        states.append(json.dumps(state, sort_keys=True))

    assert len(set(states)) == 1, "one global ledger offset means one state, not a per-rank position"
    state = json.loads(states[0])
    assert state["offset"] == 5
    assert state["skip"] == 0
    assert len(state["manifest"]) == 64


def test_json_round_trip_resumes_the_uninterrupted_run():
    straight = make_loader(0, 2)
    rows = [straight.next().clone() for _ in range(8)]

    cut = 3
    loader = make_loader(0, 2)
    for _ in range(cut):
        loader.next()
    state = json.loads(json.dumps(loader.state_dict()))

    resumed = make_loader(0, 2)
    resumed.load_state_dict(state)
    for step in range(cut, len(rows)):
        assert torch.equal(resumed.next(), rows[step]), f"batch {step} differs after resume"


def test_add_skip_skips_exactly_two_batches():
    straight = make_loader(0, 1)
    rows = [straight.next().clone() for _ in range(8)]

    loader = make_loader(0, 1)
    for _ in range(3):
        loader.next()
    loader.add_skip(2)

    assert loader.next_batch_id()["position"] == 5
    for step in range(5, 8):
        assert torch.equal(loader.next(), rows[step]), f"add_skip(2) must land on batch {step}"


def test_manifest_guard_rejects_another_shard_list():
    loader = make_loader(0, 2)
    state = loader.state_dict()
    with pytest.raises(ValueError, match="manifest"):
        loader.load_state_dict(dict(state, manifest="0" * 64))


def test_reshard_4_to_2_continues_with_the_same_global_batch():
    old = [make_loader(rank, 4) for rank in range(4)]
    for loader in old:
        for _ in range(4):
            loader.next()
    state = json.loads(json.dumps(old[0].state_dict()))
    want = sorted(row for loader in old for row in _row_bytes(loader.next()))

    got = []
    for rank in range(2):
        loader = make_loader(rank, 2)
        loader.load_state_dict(state)
        got += _row_bytes(loader.next())

    assert sorted(got) == want, "the next global batch must be the same after resharding 4 -> 2"


def test_checker_rejects_per_rank_state():
    class PerRankState(SyntheticContractLoader):
        def state_dict(self):
            state = super().state_dict()
            state["offset"] += self.rank
            return state

    problems = contract.check(lambda rank, world: PerRankState(rank, world), steps=6, cut=2, world=2)
    assert any("differs between ranks" in problem for problem in problems), problems


def test_checker_rejects_a_consuming_peek():
    class ConsumingPeek(SyntheticContractLoader):
        def next_batch_id(self):
            batch_id = super().next_batch_id()
            self.offset += 1
            return batch_id

    problems = contract.check(lambda rank, world: ConsumingPeek(rank, world), steps=6, cut=2, world=2)
    assert any("changes when called twice" in problem for problem in problems), problems
