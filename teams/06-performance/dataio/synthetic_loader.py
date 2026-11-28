"""Deterministic synthetic factory for the Team 7 loader contract.

This is a test fixture, not the training loader. ``dataio/loader.py`` is owned by the
loader implementation and stays untouched; this factory exists so the contract in
``teams/07-infrastructure/ckpt/loader_contract.py`` can be exercised before the real
shards, tokenizer and packing format arrive.

The batch is a fixed global ledger row:

    global batch N = rows [0, GLOBAL_ROWS) of a deterministic token block
    rank r, world W -> rows [r * GLOBAL_ROWS / W, (r + 1) * GLOBAL_ROWS / W)

Rows depend only on ``(seed, N)``, so every rank and every world size sees the same
global batch. That is what lets one saved state resume at another world size.

Run the contract directly from ``teams/06-performance`` (the script's own directory,
not the cwd, is on ``sys.path``, so put the cwd on ``PYTHONPATH``):

    PYTHONPATH=. python ../07-infrastructure/ckpt/loader_contract.py \
        --factory dataio.synthetic_loader:make_loader

PowerShell:

    $env:PYTHONPATH=(Get-Location).Path
    python ../07-infrastructure/ckpt/loader_contract.py --factory dataio.synthetic_loader:make_loader
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import torch

GLOBAL_ROWS = 8          # fixed global batch; divisible by the tested world sizes 1, 2, 4
ROW_TOKENS = 5           # block size 4 plus the next-token target
VOCAB_SIZE = 131072
DEFAULT_SEED = 20261128


def manifest(seed: int = DEFAULT_SEED) -> str:
    """SHA-256 of the shard-list description, as the contract requires."""
    spec = {
        "source": "synthetic-contract",
        "seed": seed,
        "global_rows": GLOBAL_ROWS,
        "row_tokens": ROW_TOKENS,
        "vocab_size": VOCAB_SIZE,
    }
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def global_batch(position: int, seed: int = DEFAULT_SEED) -> torch.Tensor:
    """[GLOBAL_ROWS, ROW_TOKENS] int64 rows of global batch ``position``.

    The generator is seeded from ``(seed, position)``; it never depends on rank,
    world size or a process-local RNG state.
    """
    if position < 0:
        raise ValueError(f"position must be non-negative, got {position}")
    rng = np.random.default_rng([seed, position])
    return torch.from_numpy(rng.integers(0, VOCAB_SIZE, (GLOBAL_ROWS, ROW_TOKENS), dtype=np.int64))


class SyntheticContractLoader:
    """One rank's view of a fixed global row ledger."""

    def __init__(self, rank: int, world: int, seed: int = DEFAULT_SEED):
        if world < 1 or GLOBAL_ROWS % world:
            # The contract's reshard check treats AssertionError as "this world size
            # cannot run", not as a loader failure.
            raise AssertionError(f"world={world} must divide the fixed global batch of {GLOBAL_ROWS} rows")
        if not 0 <= rank < world:
            raise ValueError(f"rank={rank} is outside world={world}")
        self.rank, self.world, self.seed = rank, world, seed
        self.offset = 0      # next global batch to emit, after pending skips
        self.skip = 0        # batches still to skip
        self._manifest = manifest(seed)

    @property
    def rows_per_rank(self) -> int:
        return GLOBAL_ROWS // self.world

    def _position(self) -> int:
        return self.offset + self.skip

    def _local_batch(self, position: int) -> torch.Tensor:
        rows = global_batch(position, self.seed)
        start = self.rank * self.rows_per_rank
        return rows[start:start + self.rows_per_rank].clone()

    def next(self) -> torch.Tensor:
        """This rank's rows of the next global batch."""
        position = self._position()
        batch = self._local_batch(position)
        self.offset = position + 1
        self.skip = 0
        return batch

    def next_batch_id(self) -> dict:
        """{"position": global batch, "sha256": hash of this rank's next rows}; no consume."""
        position = self._position()
        batch = self._local_batch(position)
        return {
            "position": position,
            "sha256": hashlib.sha256(batch.numpy().tobytes()).hexdigest(),
        }

    def add_skip(self, n: int) -> None:
        """Skip exactly the next ``n`` global batches."""
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            raise ValueError(f"n must be a non-negative int, got {n!r}")
        self.skip += n

    def state_dict(self) -> dict:
        """One global ledger offset, the pending skip count and the data manifest."""
        return {"offset": self.offset, "skip": self.skip, "manifest": self._manifest}

    def load_state_dict(self, state: dict) -> None:
        if state.get("manifest") != self._manifest:
            raise ValueError("state was saved on another data manifest")
        offset, skip = state.get("offset"), state.get("skip", 0)
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise ValueError(f"offset must be a non-negative int, got {offset!r}")
        if not isinstance(skip, int) or isinstance(skip, bool) or skip < 0:
            raise ValueError(f"skip must be a non-negative int, got {skip!r}")
        self.offset, self.skip = offset, skip


def make_loader(rank: int, world: int) -> SyntheticContractLoader:
    """Factory signature expected by ``loader_contract.py --factory module:function``."""
    return SyntheticContractLoader(rank, world)
