#!/usr/bin/env python3
"""A real trainer for watcher_restart_test.py --real: Team 5's tiny MoE, saved with Team 7's Checkpointer at the
steps of a recorded commits.jsonl, on its recorded times divided by --speed.

In simple words: this is restore_test.py's training loop (same config, model, loss, loader and probe), but it saves
at every step the recorded run committed (dry run 2: 0, 195, ..., 1,221), with the recorded reason ("start",
"interval", "final"), and waits so that each commit lands at its recorded time, scaled. So the eval watchers follow a
real Team 7 store that grows while they score it, and run_lab_ckpt.py --scorer smoke --steps <last step> exports and
scores each commit with the probe-loss check on.

    python teams/09-evaluation/harness_lab/tests/replay_trainer.py --commits <commits.jsonl> --store <dir> \\
        --run-id dryrun2-1234 --speed 40

Prints one "committed <step> <reason>" line per commit. Exit 0 when the last commit is in commits.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEAMS = HERE.parents[2]
RESTORE_TEST = TEAMS / "07-infrastructure" / "jobs" / "restore_test"
sys.path.insert(0, str(RESTORE_TEST))
import restore_test as rt  # noqa: E402  (puts Team 7 and Team 5's harness on sys.path)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--commits", type=Path, required=True, help="the recorded commits.jsonl (steps, times, reasons)")
    ap.add_argument("--store", type=Path, required=True, help="Team 7 remote root; the run is <store>/<run-id>")
    ap.add_argument("--local", type=Path, help="Team 7 local staging folder (default: <store>/../ckpt_local)")
    ap.add_argument("--run-id", default="dryrun2-1234")
    ap.add_argument("--speed", type=float, default=40.0, help="recorded seconds per wall second")
    ap.add_argument("--config", type=Path, default=rt.CONFIGS / "config_v0.yaml")
    ap.add_argument("--tiny", type=Path, default=rt.CONFIGS / "small" / "tiny_moe.yaml")
    a = ap.parse_args(argv)
    commits = [json.loads(x) for x in a.commits.read_text(encoding="utf-8").splitlines() if x.strip()]
    steps = [c["step"] for c in commits]
    if steps != sorted(set(steps)):
        raise SystemExit(f"{a.commits}: steps must rise (a restore is not replayed here): {steps}")

    import torch
    os.environ.setdefault("RANK", "0")
    os.environ.setdefault("WORLD_SIZE", "1")
    os.environ.setdefault("LOCAL_RANK", "0")
    os.environ["RUN_ID"] = a.run_id
    torch.use_deterministic_algorithms(True)  # the saved probe-loss bits are made with these two settings,
    torch.set_num_threads(1)                  # as in restore_test.py; run_lab_ckpt.py exports with the same ones

    cfg = rt.load_cfg(a.config.resolve(), a.tiny.resolve(), max(steps[-1], 1))
    seed = int(cfg["run.seed"])
    torch.manual_seed(seed)
    model = rt.TinyMoE(cfg)
    optim = torch.optim.AdamW(model.parameters(), lr=float(cfg["optim.lr"]))
    loader = rt.StreamLoader(cfg, seed, 0, 1)
    clip = float(cfg["run.grad_clip"])
    probe_batch = rt.stream_for(cfg, seed + 1)[:int(cfg["tiny.batch"])]

    def probe(m) -> float:
        m.eval()
        with torch.no_grad():
            ntp, _ = rt.losses(m, probe_batch)
        m.train()
        return ntp.item()

    local = a.local or a.store.parent / "ckpt_local"
    ck = rt.Checkpointer(a.run_id, str(local), str(a.store), config_path=str(a.tiny.resolve()), seed=seed,
                         code_paths=rt.CODE_PATHS)
    t0, wall0, step = commits[0]["time"], time.time(), 0
    for c in commits:
        while step < c["step"]:
            tokens = loader.next()
            optim.zero_grad(set_to_none=True)
            ntp, mtp = rt.losses(model, tokens)
            (ntp + mtp).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
            optim.step()
            step += 1
        late = time.time() - (wall0 + (c["time"] - t0) / a.speed)
        if late < 0:
            time.sleep(-late)
        if not (ck.save(step, model, optim, loader, probe, reason=c.get("reason") or "interval") and ck.wait()):
            print(f"replay_trainer: the commit of step {step} failed", file=sys.stderr)
            return 1
        print(f"committed {step} {c.get('reason')}" + (f" ({late:.1f} s late: training is slower than --speed)"
                                                       if late > 1 else ""), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
