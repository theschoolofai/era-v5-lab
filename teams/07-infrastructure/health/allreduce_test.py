"""Collective test: correctness and bus bandwidth of the four collectives training uses (ADR 0003 §1).

In simple words: every GPU exchanges known numbers with every other GPU, in the four patterns training
uses. If an answer is wrong, the hardware or network is broken. If it is slow, the node would slow down the
whole training run (and every slow minute is paid for), so it fails the check.

    all_reduce      data-parallel gradients (DDP, ZeRO-1)
    reduce_scatter  ZeRO-2/3 and FSDP gradients
    all_gather      ZeRO-3 and FSDP weights
    all_to_all      MoE expert dispatch and combine

Every value is a small whole number, exact in fp32 in any reduction order, so a wrong value is a fault, not
rounding. Bus bandwidth follows the nccl-tests convention. The four collectives and their checks come from
millermuttu's `health/allreduce.py` (team 07); here they share one JSON report with the rest of the health check.

Run:  torchrun --nproc_per_node=<gpus> health/allreduce_test.py [--max-mb 1024] [--ops all_reduce,all_to_all]
      without GPUs it uses gloo on CPU and says so (backend: gloo); bandwidth then means nothing.
"""
import argparse
import json
import os
import sys
import time

import torch
import torch.distributed as dist

OPS = ("all_reduce", "reduce_scatter", "all_gather", "all_to_all")


def err(y, want) -> float:
    """Largest difference from the exact answer (0.0 when every value is right)."""
    return float((y - want).abs().max())


def make(op, size, r, n, dev):
    """(run, error, busbw factor, bytes) for one collective on a message of `size` bytes."""
    m = max(n, (size // 4) // n * n)              # elements, a multiple of the world size
    k = m // n
    ranks = torch.arange(n, dtype=torch.float32, device=dev).repeat_interleave(k)
    if op == "all_reduce":
        x = torch.full((m,), float(r + 1), device=dev)
        y = torch.empty_like(x)

        def run():
            y.copy_(x)
            dist.all_reduce(y)
        return run, lambda: err(y, n * (n + 1) / 2), 2 * (n - 1) / n, m * 4
    if op == "reduce_scatter":
        x = torch.full((m,), float(r + 1), device=dev)
        y = torch.empty(k, device=dev)
        return (lambda: dist.reduce_scatter_tensor(y, x)), lambda: err(y, n * (n + 1) / 2), \
            (n - 1) / n, m * 4
    if op == "all_gather":
        x = torch.full((k,), float(r), device=dev)
        y = torch.empty(m, device=dev)
        return (lambda: dist.all_gather_into_tensor(y, x)), lambda: err(y, ranks), (n - 1) / n, m * 4
    # all_to_all: chunk j of rank r holds r*n+j; after the exchange, chunk s of rank r holds s*n+r
    x = (r * n + torch.arange(n, dtype=torch.float32, device=dev)).repeat_interleave(k)
    y = torch.empty(m, device=dev)
    return (lambda: dist.all_to_all_single(y, x)), lambda: err(y, ranks * n + r), (n - 1) / n, m * 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-mb", type=float, default=1)
    ap.add_argument("--max-mb", type=float, default=1024)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--iters", type=int, default=20)
    ap.add_argument("--ops", default=",".join(OPS), help="comma list of: " + ", ".join(OPS))
    ap.add_argument("--floor-gbps", type=float, default=0.0, help="fail an op if busbw is below this at the largest size")
    ap.add_argument("--out", help="write the JSON result here (rank 0)")
    a = ap.parse_args()
    ops = [o for o in a.ops.split(",") if o]
    bad_ops = [o for o in ops if o not in OPS]
    if bad_ops:
        sys.exit(f"unknown op(s) {bad_ops}; choose from {OPS}")
    corrupt = os.environ.get("V5_COLL_CORRUPT")   # test only: this op reports a wrong value on rank 0

    cuda = torch.cuda.is_available()
    dist.init_process_group("nccl" if cuda else "gloo")
    r, n = dist.get_rank(), dist.get_world_size()
    dev = torch.device("cuda", int(os.environ.get("LOCAL_RANK", 0))) if cuda else torch.device("cpu")
    if cuda:
        torch.cuda.set_device(dev)
    sync = torch.cuda.synchronize if cuda else (lambda: None)

    reports = []
    for op in ops:
        results, wrong = [], []
        size = int(a.min_mb * 2 ** 20)
        while size <= a.max_mb * 2 ** 20:
            run, error, factor, nbytes = make(op, size, r, n, dev)
            for _ in range(a.warmup):
                run()
            times = []
            for _ in range(a.iters):
                sync()
                t0 = time.perf_counter()
                run()
                sync()
                times.append(time.perf_counter() - t0)
            e = 1.0 if corrupt == op and r == 0 else error()
            if e:
                wrong.append(nbytes)
            worst = torch.tensor([e], device=dev)
            dist.all_reduce(worst, op=dist.ReduceOp.MAX)     # the largest error on any rank
            t = sorted(times)[len(times) // 2]
            algbw = nbytes / t / 1e9
            # seconds / max_error / all_ranks_correct: Team 08's g7-collective/1 fields; time_s kept for our tools
            results.append({"bytes": nbytes, "time_s": round(t, 6), "seconds": round(t, 6),
                            "algbw_gbps": round(algbw, 3), "busbw_gbps": round(algbw * factor, 3),
                            "max_error": worst.item(), "all_ranks_correct": worst.item() == 0})
            size *= 2
        flag = torch.tensor([1 if wrong else 0], device=dev)
        dist.all_reduce(flag)
        status, detail = "pass", "exact values"
        if flag.item():
            status, detail = "fail", f"wrong values on {int(flag.item())} rank(s)" + (f", sizes {wrong} here" if wrong else "")
        elif a.floor_gbps and results and results[-1]["busbw_gbps"] < a.floor_gbps:
            status, detail = "fail", f"busbw {results[-1]['busbw_gbps']} < floor {a.floor_gbps}"
        reports.append({"name": f"nccl_{op}", "op": op, "status": status, "detail": detail,
                        "metrics": {"sizes": results}})

    status = "fail" if any(x["status"] == "fail" for x in reports) else "pass"
    out = {"name": "nccl_collectives", "status": status, "backend": "nccl" if cuda else "gloo", "ranks": n,
           "ops": reports}
    if r == 0:
        print(json.dumps(out))
        if a.out:
            with open(a.out, "w") as f:
                json.dump(out, f)
    dist.destroy_process_group()
    return 0 if status == "pass" else 4


if __name__ == "__main__":
    sys.exit(main())
