"""Disk-backed rollout cache for GRPO / objective_v1 (Lab 5 Design Task 6: Waste).

Caches sampled completions, sampler log-probabilities, completion masks, and verifier rewards keyed by:
    (checkpoint_sha256, prompts_sha256, sampler_cfg_sha256)

When comparing learner changes on the same starting checkpoint and prompts (e.g. Full FT vs DT vs LoRA,
AdamW vs Hybrid Muon, objective_v1 vs GRPO+TIS), subsequent arms read exact cached rollouts instead of
re-running the expensive rollout sampler. Never mixes rollouts across different checkpoints or prompts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import torch


def _canonical_sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def cache_key(*, checkpoint_sha256: str, prompt_ids: list[str], sampler_cfg: dict) -> str:
    """Deterministic 24-hex key binding checkpoint, exact prompt order, and sampler settings."""
    if not checkpoint_sha256:
        raise ValueError("checkpoint_sha256 must be non-empty")
    return _canonical_sha256({
        "checkpoint_sha256": checkpoint_sha256,
        "prompts_sha256": _canonical_sha256(prompt_ids),
        "sampler_cfg": sampler_cfg,
    })[:24]


class RolloutCache:
    """Simple torch-serialized rollout cache with strict key verification and hit/miss counters."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def path_for(self, key: str) -> Path:
        return self.root / f"rollout_{key}.pt"

    def get(self, key: str) -> dict | None:
        p = self.path_for(key)
        if not p.is_file():
            self.misses += 1
            return None
        entry = torch.load(p, map_location="cpu", weights_only=False)
        if entry.get("key") != key:
            raise ValueError(f"Rollout cache key mismatch in {p}: {entry.get('key')} != {key}")
        self.hits += 1
        return entry["payload"]

    def put(self, key: str, payload: dict, meta: dict | None = None) -> Path:
        p = self.path_for(key)
        tmp = p.with_suffix(".pt.tmp")
        torch.save({"key": key, "meta": meta or {}, "payload": payload}, tmp)
        tmp.replace(p)
        return p

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "cache_dir": str(self.root),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total, 4) if total else 0.0,
        }
