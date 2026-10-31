"""Predict each part's time from FLOPs and bytes (roofline).  [STUB, Extra: after the MVP]

For each region: t_compute = flops / peak, t_memory = bytes / bandwidth, t_launch = kernels * launch_us.
A group of regions: GPU time = sum over leaves of max(t_compute, t_memory); predicted = max(GPU time, launch time).
`bound` = which term wins. measured >> predicted means time lost to syncs, launch gaps or a poor kernel.
Offline use (no GPU): python -m perfkit.roofline --config configs/lab_small.yaml --gpu H100-SXM
"""
from __future__ import annotations


def forward_costs(mcfg: dict, B: int, T: int, dtype: str) -> dict:
    raise NotImplementedError("forward_costs")
