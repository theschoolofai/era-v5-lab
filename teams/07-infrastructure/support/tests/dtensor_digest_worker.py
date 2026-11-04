"""Run by test T17 with torchrun: the digest of DTensor shards (FSDP rows, tensor-parallel columns, a replicated
scalar) on N ranks must equal the digest of the same full tensors in one process (ADR 0001 §8)."""
import json
import os
import sys

import torch
import torch.distributed as dist

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from ckpt.ckpt import state_digest  # noqa: E402

try:
    from torch.distributed.tensor import Replicate, Shard, distribute_tensor
except ImportError:  # torch < 2.5
    from torch.distributed._tensor import Replicate, Shard, distribute_tensor
from torch.distributed.device_mesh import init_device_mesh  # noqa: E402


def full_state():
    g = torch.Generator().manual_seed(7)
    return {"model": {"rows": torch.randn(13, 6, generator=g), "cols": torch.randn(5, 9, generator=g)},
            "optim": {"step": torch.tensor(42.0), "m": torch.randn(11, generator=g).to(torch.bfloat16)}}


if __name__ == "__main__":
    out = sys.argv[1]
    if "RANK" not in os.environ:
        json.dump({"digest": state_digest(full_state())}, open(out, "w"))
        sys.exit(0)
    dist.init_process_group("gloo")
    mesh = init_device_mesh("cpu", (dist.get_world_size(),))
    f = full_state()
    sharded = {"model": {"rows": distribute_tensor(f["model"]["rows"], mesh, [Shard(0)]),      # FSDP, uneven
                         "cols": distribute_tensor(f["model"]["cols"], mesh, [Shard(1)])},     # tensor parallel
               "optim": {"step": distribute_tensor(f["optim"]["step"], mesh, [Replicate()]),
                         "m": distribute_tensor(f["optim"]["m"], mesh, [Shard(0)])}}
    d = state_digest(sharded)
    if dist.get_rank() == 0:
        json.dump({"digest": d, "world": dist.get_world_size()}, open(out, "w"))
    dist.destroy_process_group()
