"""Packed rows: eager attention against SDPA with the document mask (TSAI's review of #890, steps P10 and P17).

Four arms on the same documents, the same model and the same seed:

    eager_packed    packed rows, eager attention with the document mask
    sdpa_packed     packed rows, SDPA with the document mask passed as attn_mask
    eager_unpacked  one window per row with padding (today's loader), eager attention
    sdpa_unpacked   one window per row with padding, SDPA causal only

For each arm: real (non-padding) tokens per second over forward plus backward, peak GPU memory,
and the gradient-coverage list TSAI's lab rule asks for (parameters whose gradient is None or all
zero). Document lengths come from shard .idx.npy files when given, so rows look like real data;
token ids are random (speed does not depend on them). The model is the T2 arm (8 layers, width
512, 16 experts) with a smaller vocabulary by default, so the output head does not swamp the
attention cost; every number is for the machine it ran on.

    python teams/05-architecture/lab5/packed_rows/measure_attention.py \
        --index <shards>/en-fineweb-edu-train-000000.idx.npy --steps 20 --batch 2 --dtype fp16
"""

import argparse
from pathlib import Path
import sys
import time

import numpy as np
import torch

TEAM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TEAM / "harness"))
from week2.config import load_runtime  # noqa: E402
from week2.model import LanguageModel  # noqa: E402


def gradient_gaps(model):
    """Names of parameters whose gradient is None or all zero, sorted."""
    return sorted(
        name for name, p in model.named_parameters()
        if p.requires_grad and (p.grad is None or not torch.any(p.grad != 0))
    )


def document_windows(index_files, L, rng, count):
    """Window sizes (at most L) from real document lengths, or a fixed mix when no index is given."""
    if index_files:
        sys.path.insert(0, str(TEAM / "harness"))
        from packing_fill import document_lengths
        lengths = document_lengths([Path(x) for x in index_files])
    else:
        lengths = rng.integers(50, 6000, 5000)
    sizes = []
    for n in rng.permutation(lengths)[:count]:
        n = int(n)
        sizes += [L] * (n // L) + ([n % L] if n % L else [])
    return sizes


def packed_rows(sizes, L, pool=16):
    """Best fit from the next `pool` windows (the loader's rule, BatchStream.next_packed)."""
    upcoming, held, rows = iter(sizes), [], []
    while True:
        while len(held) < pool:
            n = next(upcoming, None)
            if n is None:
                break
            held.append(n)
        if not held:
            return rows
        row, left = [], L
        while True:
            fits = [i for i, n in enumerate(held) if n <= left]
            if not fits:
                break
            i = max(fits, key=lambda j: (held[j], -j))
            row.append(held.pop(i))
            left -= row[-1]
            while len(held) < pool:
                n = next(upcoming, None)
                if n is None:
                    break
                held.append(n)
        rows.append(row)


def make_batch(rows, L, vocab, gen):
    """ids, valid, doc_ids (int32), pos_ids (int32), targets for a list of rows of window sizes."""
    B = len(rows)
    ids = torch.randint(1, vocab, (B, L), generator=gen)
    doc = torch.zeros(B, L, dtype=torch.int32)
    pos = torch.zeros(B, L, dtype=torch.int32)
    for r, row in enumerate(rows):
        at = 0
        for k, n in enumerate(row, start=1):
            doc[r, at:at + n] = k
            pos[r, at:at + n] = torch.arange(n, dtype=torch.int32)
            at += n
    valid = doc != 0
    ids = ids.masked_fill(~valid, 0)
    targets = torch.randint(0, vocab, (B, L), generator=gen).masked_fill(~valid, -100)
    return ids, valid, doc, pos, targets


def build(arm, vocab, L, device):
    c = load_runtime(TEAM / "configs/arms/t2.yaml")
    m = dict(c["model"])
    m.update(vocab_size=vocab, block_size=L, attn_impl="eager" if arm.startswith("eager") else "sdpa")
    rng = np.random.default_rng(7)
    rows = rng.integers(0, 256, (vocab, 4), dtype=np.uint8)
    lengths = rng.integers(1, 5, vocab, dtype=np.int16)
    torch.manual_seed(1234)
    return LanguageModel(m, rows, lengths).to(device)


def run_arm(arm, batches, vocab, L, device, dtype, warmup):
    model = build(arm, vocab, L, device)
    model.train()
    packed = arm.endswith("_packed")
    cast = torch.autocast(device.type, dtype=dtype) if dtype != torch.float32 else torch.autocast(device.type, enabled=False)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    seconds, real, gaps = 0.0, 0, None
    for step, (ids, valid, doc, pos, targets) in enumerate(batches):
        ids, valid, doc, pos, targets = (t.to(device) for t in (ids, valid, doc, pos, targets))
        model.zero_grad(set_to_none=True)
        if device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        with cast:
            logits = model(ids, valid, segments=(doc, pos) if packed else None)
            loss = torch.nn.functional.cross_entropy(
                logits.float().view(-1, logits.shape[-1]), targets.view(-1), ignore_index=-100)
        loss.backward()
        if device.type == "cuda":
            torch.cuda.synchronize()
        dt = time.perf_counter() - t0
        if step == 0:
            gaps = gradient_gaps(model)
        if step >= warmup:
            seconds += dt
            real += int(valid.sum())
    peak = f"{torch.cuda.max_memory_allocated() / 2**30:.2f}" if device.type == "cuda" else "n/a"
    return real / seconds, peak, gaps


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--index", nargs="*", default=[], help="shard .idx.npy files for document lengths")
    p.add_argument("--window", type=int, default=2048)
    p.add_argument("--batch", type=int, default=2, help="rows per step")
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--warmup", type=int, default=3, help="steps left out of the timing")
    p.add_argument("--vocab", type=int, default=32768)
    p.add_argument("--dtype", choices=["fp32", "fp16", "bf16"], default="fp16")
    p.add_argument("--seed", type=int, default=1234)
    a = p.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}[a.dtype]
    rng = np.random.default_rng(a.seed)
    L, steps = a.window, a.steps
    sizes = document_windows(a.index, L, rng, count=20000)
    packed = packed_rows(sizes, L)
    single = [[n] for n in sizes]
    need = steps * a.batch
    if len(packed) < need:
        raise SystemExit(f"only {len(packed)} packed rows; lower --steps or --batch")

    def batches(rows):
        gen = torch.Generator().manual_seed(a.seed)
        return [make_batch(rows[i * a.batch:(i + 1) * a.batch], L, a.vocab, gen) for i in range(steps)]

    data = {"eager_packed": batches(packed), "sdpa_packed": batches(packed),
            "eager_unpacked": batches(single), "sdpa_unpacked": batches(single)}
    name = torch.cuda.get_device_name() if device.type == "cuda" else "CPU"
    print(f"Machine: {name}; torch {torch.__version__}; dtype {a.dtype}; window {L}; "
          f"{a.batch} rows per step; {steps} steps ({a.warmup} not timed); vocab {a.vocab}; seed {a.seed}")
    print("Index files: " + (", ".join(Path(x).name for x in a.index) if a.index else "none (synthetic lengths)"))
    print()
    print("| Arm | Rows | Fill | Real tokens/s | vs eager packed | Peak memory (GiB) | Gradient None or zero |")
    print("|---|---|---:|---:|---:|---:|---|")
    base, gaps_all = None, {}
    for arm, rows in data.items():
        fill = sum(int(b[1].sum()) for b in rows) / (steps * a.batch * L)
        tps, peak, gaps = run_arm(arm, rows, a.vocab, L, device, dtype, a.warmup)
        base = base or tps
        gaps_all[arm] = gaps
        print(f"| {arm} | {'packed' if arm.endswith('_packed') else 'one window'} | {fill:.1%} | "
              f"{tps:,.0f} | {tps / base:.2f}x | {peak} | {len(gaps)} |")
    print()
    same = gaps_all["eager_packed"] == gaps_all["sdpa_packed"]
    print(f"Gradient coverage, eager packed vs SDPA packed: {'same' if same else 'DIFFERENT'} "
          f"({len(gaps_all['eager_packed'])} parameters with no or zero gradient)")
    for arm, gaps in gaps_all.items():
        if gaps:
            print(f"  {arm}: " + ", ".join(gaps))


if __name__ == "__main__":
    main()
