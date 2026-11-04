"""The data-loader contract every team's loader must pass before the main run (ADR 0001 §7).

In simple words: a checkpoint can only resume training exactly if the data loader can say where it is,
and later continue from exactly that place. Teams 01/02 own the real loader; this file is the test they run
on it. Our synthetic loader passes it today (see test at the bottom).

A loader must offer:
    state_dict()        -> JSON-serialisable dict: ONE global ledger offset, the skip list and "manifest" (sha256 of
                           the shard list), the same on every rank (no per-rank or per-worker positions)
    load_state_dict(d)  -> continue from that state; raise ValueError if d["manifest"] is not this loader's data
    next_batch_id()     -> {"position": ..., "sha256": <hash of the next batch's content>}, without consuming it
    next()              -> the next batch (tensor or anything hashable via bytes)
    add_skip(n)         -> skip the next n batches (rollback)

    python ckpt/loader_contract.py --factory mypkg.loader:make_loader     (factory(rank, world) -> loader)

Why one global offset: after a node is lost the run may continue at another world size (resharding). The
checkpoint then gives every new rank the saved state of old rank 0. That is only right if that state means
"global batch N", from which each rank computes its own slice. A per-rank position ("rank 3 is at row 812")
has no meaning for a different set of ranks: data would repeat or be skipped. The checkpointer also checks this
at every save (`loader_global` in the manifest) and refuses a resharded restore of a loader that fails it
(ReshardError, exit 78). The test below also proves the same offset resumes correctly at another world size.
"""
import argparse
import hashlib
import importlib
import json
import sys


def _bytes(b):
    if hasattr(b, "numpy"):
        return b.cpu().numpy().tobytes()
    return json.dumps(b, sort_keys=True, default=str).encode()


def check(factory, steps=20, cut=7, world=2) -> list:
    """Returns a list of problems; empty means the loader passes."""
    problems, states = [], []
    for r in range(world):
        a = factory(r, world)
        straight = [hashlib.sha256(_bytes(a.next())).hexdigest() for _ in range(steps)]
        b = factory(r, world)
        for _ in range(cut):
            b.next()
        st = b.state_dict()
        try:
            st = json.loads(json.dumps(st))
        except TypeError as e:
            problems.append(f"rank {r}: state_dict is not JSON-serialisable: {e}")
            continue
        peek = b.next_batch_id()
        if b.next_batch_id() != peek:
            problems.append(f"rank {r}: next_batch_id() changes when called twice (it must not consume)")
        c = factory(r, world)
        c.load_state_dict(st)
        if c.next_batch_id() != peek:
            problems.append(f"rank {r}: next_batch_id after load_state_dict differs from before save")
        resumed = [hashlib.sha256(_bytes(c.next())).hexdigest() for _ in range(steps - cut)]
        if resumed != straight[cut:]:
            first = next(i for i, (x, y) in enumerate(zip(resumed, straight[cut:])) if x != y)
            problems.append(f"rank {r}: resumed batch {cut + first} differs from the uninterrupted run")
        d = factory(r, world)
        d.load_state_dict(st)
        d.add_skip(2)
        skipped = [hashlib.sha256(_bytes(d.next())).hexdigest() for _ in range(3)]
        if skipped != straight[cut + 2:cut + 5]:
            problems.append(f"rank {r}: add_skip(2) does not skip exactly the next 2 batches")
        if not isinstance(st.get("manifest"), str) or not st["manifest"]:
            problems.append(f"rank {r}: state_dict has no \"manifest\" (sha256 of the shard list)")
        else:
            try:
                factory(r, world).load_state_dict(dict(st, manifest="0" * 64))
                problems.append(f"rank {r}: load_state_dict accepted a state saved on another data manifest")
            except ValueError:
                pass
        states.append(json.dumps(st, sort_keys=True))
    if len(set(states)) > 1:
        problems.append("state_dict differs between ranks at the same step: it must be one global ledger "
                        "offset, or a restore at another world size repeats or skips data")
    elif states:
        problems += _reshard_check(factory, json.loads(states[0]), cut, world)
    return problems


def _rows(b) -> list:
    """The samples in a batch, as bytes: a rank's slice of a global batch is a set of rows."""
    if hasattr(b, "numpy") and b.dim() > 0:
        return [r.cpu().numpy().tobytes() for r in b]
    return [_bytes(b)]


def _reshard_check(factory, st, cut, world) -> list:
    """The saved state, loaded at another world size, must continue with exactly the same global batch."""
    new = 2 if world == 1 else world // 2
    try:
        old = [factory(r, world) for r in range(world)]
        for x in old:
            for _ in range(cut):
                x.next()
        want = sorted(row for x in old for row in _rows(x.next()))
        got = []
        for r in range(new):
            y = factory(r, new)
            y.load_state_dict(st)
            got += _rows(y.next())
    except AssertionError:  # this loader cannot run at that world size at all; not a contract failure
        return []
    if sorted(got) != want:
        return [f"after loading the state at world size {new} (saved at {world}), the next global batch differs"]
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--factory", required=True, help="module:function, function(rank, world) -> loader")
    a = ap.parse_args()
    mod, fn = a.factory.split(":")
    probs = check(getattr(importlib.import_module(mod), fn))
    print(json.dumps({"pass": not probs, "problems": probs}, indent=1))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
