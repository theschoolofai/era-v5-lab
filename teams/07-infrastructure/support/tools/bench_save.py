"""Measure what one checkpoint save costs on this machine (ADR 0001 §2, ADR 0004 §1).

In simple words: the cost model assumes how fast a GPU can copy its state to host memory (the "stall",
when training waits) and how fast it can be written to disk. This script measures both, so the cost
model can use real numbers instead of guesses.

For each size it measures:
  d2h_gbytes_s     GPU -> pinned host RAM copy speed (the stall, per GPU)
  sync_save_s      dcp.save to local disk, blocking (what training would wait without async)
  async_stall_s    dcp.async_save: time until training may continue
  async_total_s    async_save: time until the write is finished

    python ckpt/bench_save.py --sizes-gb 0.5 1 2 --out bench.json     (one GPU; --device cpu also works)
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time
import warnings

import torch
import torch.distributed as dist
import torch.distributed.checkpoint as dcp

warnings.filterwarnings("ignore", category=UserWarning, module=r"torch\.distributed\.checkpoint")


def sync(dev):
    if dev.type == "cuda":
        torch.cuda.synchronize(dev)


def state_of(size_gb: float, dev) -> dict:
    """fp32 tensors of 64 MB each, like a model's weights and optimizer moments."""
    n = int(size_gb * 2 ** 30 / 4)
    chunk = 16 * 2 ** 20
    out, i = {}, 0
    while n > 0:
        k = min(chunk, n)
        out[f"t{i:04d}"] = torch.randn(k, device=dev)
        n -= k
        i += 1
    return out


def bench(size_gb, dev, root) -> dict:
    st = state_of(size_gb, dev)
    nbytes = sum(t.numel() * 4 for t in st.values())
    pinned = {k: torch.empty(t.shape, dtype=t.dtype, pin_memory=dev.type == "cuda") for k, t in st.items()}
    sync(dev)
    t0 = time.perf_counter()
    for k, t in st.items():
        pinned[k].copy_(t, non_blocking=True)
    sync(dev)
    d2h = time.perf_counter() - t0

    d = tempfile.mkdtemp(dir=root)
    t0 = time.perf_counter()
    dcp.save(st, checkpoint_id=os.path.join(d, "sync"))
    sync_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    fut = dcp.async_save(st, checkpoint_id=os.path.join(d, "async"))
    stall = time.perf_counter() - t0
    fut.result()
    total = time.perf_counter() - t0
    shutil.rmtree(d, ignore_errors=True)
    return {"size_gb": round(nbytes / 1e9, 3), "d2h_s": round(d2h, 4), "d2h_gbytes_s": round(nbytes / 1e9 / d2h, 2),
            "sync_save_s": round(sync_s, 3), "disk_gbytes_s": round(nbytes / 1e9 / sync_s, 2),
            "async_stall_s": round(stall, 4), "async_total_s": round(total, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes-gb", type=float, nargs="+", default=[0.5, 1, 2])
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--dir", default=tempfile.gettempdir(), help="local disk to write to (NVMe on cloud nodes)")
    ap.add_argument("--out")
    a = ap.parse_args()
    dev = torch.device(a.device, 0) if a.device == "cuda" else torch.device("cpu")
    if not dist.is_initialized():  # async_save needs a process group; one rank, gloo
        os.environ.setdefault("MASTER_ADDR", "127.0.0.1")
        os.environ.setdefault("MASTER_PORT", "29599")
        dist.init_process_group("gloo", rank=0, world_size=1)
    res = {"device": torch.cuda.get_device_name(dev) if dev.type == "cuda" else "cpu",
           "torch": torch.__version__, "results": []}
    for g in a.sizes_gb:
        r = bench(g, dev, a.dir)
        res["results"].append(r)
        print(json.dumps(r), flush=True)
        if dev.type == "cuda":
            torch.cuda.empty_cache()
    if a.out:
        with open(a.out, "w") as f:
            json.dump(res, f, indent=1)
    dist.destroy_process_group()
    return 0


if __name__ == "__main__":
    sys.exit(main())
