"""Does a stuck rank turn into a fast, clean failure? (ADR 0003 §2) GPU + NCCL only.

In simple words: if one GPU stops answering, the others wait for it inside a collective. Without a timeout
they would wait forever, and we would pay for a frozen cluster. With the settings from ADR 0003
(TORCH_NCCL_ASYNC_ERROR_HANDLING=1, a collective timeout, the flight recorder) the waiting ranks must stop
by themselves soon after the timeout, and leave a trace that shows which rank was stuck.

Rank 1 sleeps instead of joining an all-reduce. Rank 0 must fail within timeout + margin.

    torchrun --nproc_per_node=2 health/nccl_timeout_test.py --timeout-s 20 --out nccl_timeout.json
"""
import argparse
import datetime
import glob
import json
import os
import sys
import time

import torch
import torch.distributed as dist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout-s", type=float, default=20)
    ap.add_argument("--stuck-s", type=float, default=90)
    ap.add_argument("--out")
    a = ap.parse_args()
    os.environ.setdefault("TORCH_NCCL_ASYNC_ERROR_HANDLING", "1")
    os.environ.setdefault("TORCH_NCCL_TRACE_BUFFER_SIZE", "2000")
    os.environ.setdefault("TORCH_NCCL_DUMP_ON_TIMEOUT", "1")
    trace_prefix = os.environ.setdefault("TORCH_NCCL_DEBUG_INFO_TEMP_FILE", "/tmp/v5_nccl_trace_")
    lr = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(lr)
    dist.init_process_group("nccl", timeout=datetime.timedelta(seconds=a.timeout_s))
    r = dist.get_rank()
    x = torch.ones(1 << 20, device="cuda")
    dist.all_reduce(x)                      # warm-up: everyone joins
    torch.cuda.synchronize()
    t0 = time.time()
    if r == 1:
        time.sleep(a.stuck_s)               # the stuck rank
        os._exit(0)
    err = None
    try:
        dist.all_reduce(x)
        torch.cuda.synchronize()
    except Exception as e:  # noqa: BLE001 - the point of the test is which error arrives, and when
        err = f"{type(e).__name__}: {str(e)[:300]}"
    waited = time.time() - t0
    traces = sorted(glob.glob(trace_prefix + "*"))
    ok = err is not None and waited <= a.timeout_s + 60
    out = {"name": "nccl_timeout", "status": "pass" if ok else "fail", "timeout_s": a.timeout_s,
           "seconds_to_failure": round(waited, 2), "error": err, "flight_recorder_files": traces}
    print(json.dumps(out), flush=True)
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f, indent=1)
    sys.stdout.flush()
    os._exit(0 if ok else 4)


if __name__ == "__main__":
    main()
