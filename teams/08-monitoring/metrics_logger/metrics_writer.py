"""Buffered JSONL metrics writer for the training loop.

One row per completed optimizer step is appended to metrics.jsonl. Rows are held in memory and
written to disk whenever `step % flush_every == 0` (default 10), so a crash loses at most the last 9 steps.
A row with a non-finite value (stored as "nan", "inf" or "-inf") is flushed at once, because that is
the row you want to see after a crash.

Only metrics from the metric list are written; an unknown name (a typo, or a dropped metric such as
`loss` or `loss_by_lane`) is skipped with one warning per name. `gpu_alloc_gb` (the name train.py uses; the value is GiB) is
mapped to `gpu_alloc_gib`. The 10-second system metrics from G6 (`gpu_utilization`,
`gpu_memory_used`) have no step, so they are not written here.

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
    "update_weight_ratio", "expert_load",
    "model_flops_utilization", "loader_wait_time",
})

# Names used by train.py that are written under a different name.
ALIASES = {"gpu_alloc_gb": "gpu_alloc_gib"}


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
        # Names outside the metric list are skipped, not written.
        for name in metrics:
            if name not in METRICS and name not in self._warned:
                self._warned.add(name)
                print(f"metrics_writer: skipping unknown metric {name!r}", file=sys.stderr)
        metrics = {name: value for name, value in metrics.items() if name in METRICS}
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
