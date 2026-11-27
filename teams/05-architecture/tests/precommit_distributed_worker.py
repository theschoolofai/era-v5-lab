"""Two actual ranks exercise the G5 initialization adapter and G7 step-zero commit.

This validates the checkpoint boundary, not distributed G5 training support.
"""
from datetime import timedelta
import json
import os
from pathlib import Path
import sys

import torch
import torch.distributed as dist

TEAM = Path(__file__).resolve().parents[1]
G7 = TEAM.parent / "07-infrastructure"
sys.path[:0] = [str(TEAM / "harness"), str(G7), str(G7 / "support" / "simulation")]
from ckpt.ckpt import Checkpointer
from trainer.tiny import TinyLM, SyntheticLoader, make_probe_fn
from week2.precommit import claim_for_start


def main():
    root, rank = Path(sys.argv[1]), int(sys.argv[2])
    os.environ["LOCAL_RANK"] = str(rank)
    torch.set_num_threads(1)
    store = dist.FileStore(str(root / "rendezvous"), 2)
    dist.init_process_group("gloo", store=store, rank=rank, world_size=2, timeout=timedelta(seconds=60))
    try:
        torch.manual_seed(1234)
        model = TinyLM(1234)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        loader = SyntheticLoader(1234, 8, rank, 2)
        checkpointer = Checkpointer("run", str(root / f"rank-cache-{rank}"), str(root / "store"))
        epoch = claim_for_start(checkpointer)
        assert checkpointer.save(0, model, optimizer, loader, make_probe_fn(1234), reason="start")
        assert checkpointer.wait() and not checkpointer.any_fenced()
        dist.barrier()
        pointer = checkpointer.store.get_json("latest.json")
        assert pointer["step"] == 0
        (root / f"rank-{rank}.json").write_text(json.dumps({"epoch": epoch, "step": pointer["step"], "world": dist.get_world_size()}))
    finally:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
