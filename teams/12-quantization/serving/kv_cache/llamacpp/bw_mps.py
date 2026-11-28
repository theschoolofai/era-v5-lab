"""Unified-memory bandwidth on Apple silicon through PyTorch MPS, for the speed table's bandwidth limit.

    python bw_mps.py --repeat 5 --out results/bandwidth_mps.json      # on a quiet machine

Each repeat times, over a 1 GiB float32 tensor, `x.sum()` (reads it once) and `y.copy_(x)` (reads and writes it),
20 runs each after a warm-up, and keeps the median run. The file holds every repeat and the median over repeats. This
is what one PyTorch kernel reaches, not a hardware bound: llama.cpp's own kernels may read faster or slower.
"""
import argparse, json, statistics, time

import torch


def once(n=2 ** 28, reps=20):
    dev = torch.device('mps')
    x = torch.ones(n, device=dev); y = torch.empty_like(x)

    def t(f):
        f(); torch.mps.synchronize()
        ts = []
        for _ in range(reps):
            a = time.perf_counter(); f(); torch.mps.synchronize(); ts.append(time.perf_counter() - a)
        return statistics.median(ts)

    gb = n * 4 / 1e9
    return {'read_GBps': gb / t(lambda: x.sum()), 'copy_GBps': 2 * gb / t(lambda: y.copy_(x))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repeat', type=int, default=1)
    ap.add_argument('--out')
    a = ap.parse_args()
    rows = []
    for _ in range(a.repeat):
        rows.append(once()); print(json.dumps(rows[-1]), flush=True)
    out = {'method': 'torch MPS: median of 20 timed runs each of x.sum() (read) and y.copy_(x) (read+write) over 1 GiB '
                     'float32, per repeat', 'torch': torch.__version__, 'repeats': len(rows),
           'read_GBps': [r['read_GBps'] for r in rows], 'copy_GBps': [r['copy_GBps'] for r in rows],
           'read_GBps_median': statistics.median(r['read_GBps'] for r in rows),
           'copy_GBps_median': statistics.median(r['copy_GBps'] for r in rows)}
    if a.out:
        with open(a.out, 'w') as f: f.write(json.dumps(out, indent=1) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k.endswith('median')}))


if __name__ == '__main__':
    main()
