"""Buffered JSONL metrics writer for the training loop.

One row per completed optimizer step is appended to metrics.jsonl. Rows are held in memory and
written to disk whenever `step % flush_every == 0` (default 10), so a crash loses at most the last 9 steps.
A row with a non-finite value (stored as "nan", "inf" or "-inf") is flushed at once, because that is
the row you want to see after a crash.

Only metrics from the metric list are written; an unknown name (a typo, or a dropped metric such as
`loss` or `loss_by_lane`) is skipped with one warning per name. `gpu_alloc_gb` (the name train.py uses; the value is GiB) is
mapped to `gpu_alloc_gib`, and `temp_c` (the G6 sampler's name) to `gpu_temp_c`. The 10-second system metrics from G6 (`gpu_utilization`,
`gpu_memory_used`) have no step, so they are not written here.

Three MoE metrics are worked out from `expert_load` when the trainer does not pass them. An expert's utilization is
its share of its layer's picks divided by the uniform share (1 / number of experts): 1.0 is a fair share, 0 is never picked.
- `dead_experts_count`: routed experts, over all MoE layers, with utilization below 0.1.
- `dead_experts_by_layer`: the same count for each MoE layer, in layer order, to show where routing collapses.
- `expert_utilization_min`: the lowest utilization of any routed expert. It falls before an expert is counted as dead,
  so it warns early; below 0.1 the expert is dead.
`expert_load` is one layer (a list of per-expert picks or shares), several layers (a list of lists, or {layer: list}), or a
2-D array or tensor. Counts and shares give the same answer, since each layer is divided by its own total. Pass the
picks of the whole optimizer step, summed over micro-batches and data-parallel ranks: one micro-batch is too small to
call an expert dead.

When `expert_load` is logged, `router_max_vio` (DeepSeek MaxVio, the largest over MoE layers) is
computed from it and written in the same row, unless the caller passed it explicitly.

    with MetricsWriter("metrics.jsonl") as writer:
        for step in range(n):
            ...
            writer.write(step, loss_ntp=1.2, loss_mtp=1.4, lr=3e-4)
"""

import json
import math
import os
import sys
import time

FLUSH_EVERY = 10

# Metric list, per-step metrics only. Per-layer / per-expert metrics take a list or a dict.
METRICS = frozenset({
    "loss_ntp", "loss_mtp", "lr", "tokens_per_second", "gpu_alloc_gib",
    "gradient_norm", "gradient_clipping_applied", "validation_loss",
    "update_weight_ratio", "expert_load", "router_max_vio",
    "dead_experts_count", "dead_experts_by_layer", "expert_utilization_min",
    "model_flops_utilization", "loader_wait_time",
    "gpu_temp_c", "gpu_thermal_throttle",
    "tokens_per_byte", "tokens_per_byte_by_lang",
})

# Names used by train.py that are written under a different name.
ALIASES = {"gpu_alloc_gb": "gpu_alloc_gib", "temp_c": "gpu_temp_c"}


def _max_vio(loads):
    """DeepSeek MaxVio for one MoE layer: (max load - mean load) / mean load.

    0.0 means every expert gets the same share; 1.0 means the busiest expert gets twice the
    average. Returns NaN if any load is not finite or the mean is not positive.
    """
    loads = [float(x) for x in loads]
    if not all(math.isfinite(x) for x in loads):
        return float("nan")
    mean = sum(loads) / len(loads)
    if mean <= 0:
        return float("nan")
    return (max(loads) - mean) / mean


def _layers(expert_load):
    """Split expert_load into one list of loads per layer.

    Accepts a flat list (one layer), a list of lists, or a dict {layer: list}, as plain Python,
    NumPy or torch values. Empty layers are dropped.
    """
    if hasattr(expert_load, "tolist"):  # numpy array, torch tensor
        expert_load = expert_load.tolist()
    if isinstance(expert_load, dict):
        layers = list(expert_load.values())
    elif expert_load and all(isinstance(x, (list, tuple)) or getattr(x, "ndim", 0) >= 1 for x in expert_load):
        layers = list(expert_load)
    else:
        layers = [expert_load]
    layers = [x.tolist() if hasattr(x, "tolist") else x for x in layers]
    return [list(x) for x in layers if len(x) > 0]


def router_max_vio_per_layer(expert_load):
    """MaxVio for each MoE layer in expert_load (see `_layers` for accepted shapes)."""
    return [_max_vio(loads) for loads in _layers(expert_load)]


def router_max_vio(expert_load):
    """Routing imbalance for one step: the worst (largest) MaxVio over all MoE layers.

    Returns None if expert_load has no layers. NaN in any layer makes the result NaN, so a
    broken router is never hidden behind a healthy one.
    """
    per_layer = router_max_vio_per_layer(expert_load)
    if not per_layer:
        return None
    if any(math.isnan(v) for v in per_layer):
        return float("nan")
    return max(per_layer)

# An expert is dead below this fraction of the uniform share of its layer's picks.
DEAD_EXPERT_SHARE = 0.1


def _number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def expert_load_stats(expert_load, share=DEAD_EXPERT_SHARE):
    """{dead_experts_count, dead_experts_by_layer, expert_utilization_min} from expert_load.

    None when it cannot be told: no layers, an empty layer, a layer with no picks, or a negative or non-finite value.
    """
    if hasattr(expert_load, "tolist"):
        expert_load = expert_load.tolist()
    if isinstance(expert_load, dict):
        expert_load = list(expert_load.values())
    if not isinstance(expert_load, (list, tuple)) or not expert_load:
        return None
    layers = [expert_load] if all(_number(x) for x in expert_load) else expert_load
    by_layer, lowest = [], math.inf
    for layer in layers:
        if hasattr(layer, "tolist"):
            layer = layer.tolist()
        if not isinstance(layer, (list, tuple)) or not layer or not all(_number(x) and math.isfinite(x) and x >= 0 for x in layer):
            return None
        total = sum(layer)
        if total <= 0:
            return None
        # utilization = load / (total / n); dead below `share`, written without division
        by_layer.append(sum(1 for x in layer if x * len(layer) < share * total))
        lowest = min(lowest, min(layer) * len(layer) / total)
    return {"dead_experts_count": sum(by_layer), "dead_experts_by_layer": by_layer, "expert_utilization_min": lowest}


def dead_experts_count(expert_load, share=DEAD_EXPERT_SHARE):
    """Routed experts below `share` x the uniform share, summed over MoE layers; None when it cannot be told."""
    stats = expert_load_stats(expert_load, share)
    return None if stats is None else stats["dead_experts_count"]


def _clean(value):
    """Return (JSON-safe value, whether any non-finite number was found).

    NumPy and torch scalars become Python numbers. NaN and Inf are stored as the strings
    "nan", "inf" and "-inf", so the monitor can tell a NaN loss from an overflow.
    """
    if hasattr(value, "tolist"):  # numpy scalar/array, torch tensor
        value = value.tolist()
    if isinstance(value, float):
        return (value, False) if math.isfinite(value) else (str(value), True)
    if isinstance(value, (list, tuple)):
        pairs = [_clean(v) for v in value]
        return [v for v, _ in pairs], any(bad for _, bad in pairs)
    if isinstance(value, dict):
        pairs = {k: _clean(v) for k, v in value.items()}
        return {k: v for k, (v, _) in pairs.items()}, any(bad for _, bad in pairs.values())
    return value, False


class MetricsWriter:
    def __init__(self, path, flush_every=FLUSH_EVERY):
        if flush_every < 1:
            raise ValueError("flush_every must be >= 1")
        self.path = path
        self.flush_every = flush_every
        self._buffer = []
        self._warned = set()
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        self._file = open(path, "a", encoding="utf-8")

    def write(self, step, **metrics):
        """Buffer one row; flush when step is a multiple of `flush_every`."""
        if self._file is None:
            raise ValueError("write() on a closed MetricsWriter")
        metrics = {ALIASES.get(name, name): value for name, value in metrics.items()}
        # The MoE metrics are worked out from expert_load; a value passed by the trainer wins.
        if metrics.get("expert_load") is not None:
            for name, value in (expert_load_stats(metrics["expert_load"]) or {}).items():
                if metrics.get(name) is None:
                    metrics[name] = value
        # Names outside the metric list are skipped, not written.
        for name in metrics:
            if name not in METRICS and name not in self._warned:
                self._warned.add(name)
                print(f"metrics_writer: skipping unknown metric {name!r}", file=sys.stderr)
        metrics = {name: value for name, value in metrics.items() if name in METRICS}
        # router_max_vio is derived from expert_load unless the caller passed it.
        if metrics.get("expert_load") is not None and "router_max_vio" not in metrics:
            vio = router_max_vio(metrics["expert_load"])
            if vio is not None:
                metrics["router_max_vio"] = vio
        row = {"step": step, "time": time.time()}
        nonfinite = False
        for name, value in metrics.items():
            # Plain JSON has no NaN/Infinity; store null and flush now.
            row[name], bad = _clean(value)
            nonfinite = nonfinite or bad
        self._buffer.append(json.dumps(row, allow_nan=False))
        if nonfinite or step % self.flush_every == 0:
            self.flush()

    def flush(self):
        """Write buffered rows to disk."""
        if self._file is None or not self._buffer:
            return
        self._file.write("\n".join(self._buffer) + "\n")
        self._file.flush()
        os.fsync(self._file.fileno())
        self._buffer.clear()

    def close(self):
        """Flush the remaining rows and close the file. Safe to call twice."""
        if self._file is None:
            return
        self.flush()
        self._file.close()
        self._file = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
