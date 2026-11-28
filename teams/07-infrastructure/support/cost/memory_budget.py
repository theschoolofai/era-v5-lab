"""Memory budget per GPU for one node of 8 GPUs (Lab 5, design task 1).

In simple words: for a model of a given total size, how many GB does each GPU need for the weights, the fp32
master copy, the gradients, the optimizer state (Adam or Muon) and the activations, and does it fit?
Every number in docs/memory_budget_lab5.md comes from this script.

    python support/cost/memory_budget.py [--gpus 8] [--gb-per-gpu 80] [--reserve-gb 6]

Assumptions (planning assumptions, not decisions):
- Mixed precision: bf16 weights (2 B), fp32 master copy (4 B), bf16 gradients (2 B) per parameter.
- Adam keeps two fp32 moments (8 B). Muon keeps one fp32 momentum buffer (4 B). The small 1D AdamW group under
  TSAI's hybrid rule (norm gains, gates, biases) is far below 1% of the parameters and is left out.
- Activations: Korthikanti et al. 2022 ("Reducing Activation Recomputation in Large Transformer Models"),
  34*s*b*h bytes per layer in bf16 with flash attention (no s^2 term). Full recompute keeps each layer's
  input (2*s*b*h) plus one layer being recomputed. One sequence per GPU (b = 1), plus fp32 logits for the loss.
- Shapes are dense-equivalent (12*L*h^2 ~ total parameters). An MoE of the same total size has a smaller h and L,
  so its activations are smaller: these activation rows are an upper bound. The states rows do not change,
  because every expert's weights, gradients and optimizer state are kept whatever the routing.
"""
import argparse

GB = 1e9
VOCAB = 131072
SIZES_B = (25, 50, 100, 150)
SHAPES = {25: (5120, 80), 50: (7168, 80), 100: (8192, 124), 150: (10240, 120)}  # (hidden h, layers L)
SEQS = ((4096, False), (4096, True), (8192, False), (8192, True))
W, MASTER, GRAD = 2, 4, 2
OPT = {"Adam": 8, "Muon": 4}
SHARDING = ("none", "zero1", "zero2", "zero3")
SHARD_TEXT = {"none": "none (every GPU holds everything)", "zero1": "ZeRO-1 (optimizer state + master sharded)",
              "zero2": "ZeRO-2 (+ gradients sharded)", "zero3": "ZeRO-3 / FSDP (everything sharded)"}


def activations_gb(h, layers, seq, recompute, batch=1):
    per_layer = 34 * seq * batch * h
    body = (2 * seq * batch * h * layers + per_layer) if recompute else per_layer * layers
    return (body + seq * batch * VOCAB * 4) / GB


def per_param_bytes(opt, shard, n):
    """Bytes per parameter on one GPU, for the four kinds of state."""
    o = OPT[opt]
    return {"none": W + MASTER + GRAD + o,
            "zero1": W + GRAD + (MASTER + o) / n,
            "zero2": W + (GRAD + MASTER + o) / n,
            "zero3": (W + GRAD + MASTER + o) / n}[shard]


def fmt(total, usable):
    return f"{total:.1f} {'fits' if total <= usable else '**no**'}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpus", type=int, default=8)
    ap.add_argument("--gb-per-gpu", type=float, default=80.0)
    ap.add_argument("--reserve-gb", type=float, default=6.0,
                    help="kept free per GPU for the CUDA context, NCCL buffers and fragmentation")
    a = ap.parse_args()
    n, usable = a.gpus, a.gb_per_gpu - a.reserve_gb
    out = [f"Node: {n} GPUs x {a.gb_per_gpu:.0f} GB = {n * a.gb_per_gpu:.0f} GB. "
           f"Usable per GPU: {usable:.0f} GB ({a.gb_per_gpu:.0f} - {a.reserve_gb:.0f} reserve).", ""]

    out += ["### A. Model states for the whole model, GB (before any sharding)", "",
            "| Total params | bf16 weights | fp32 master | bf16 gradients | Adam state | Muon state | "
            "Total, Adam (16 B/param) | Total, Muon (12 B/param) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for p in SIZES_B:
        x = p * 1e9 / GB
        out.append(f"| {p}B | {W*x:.0f} | {MASTER*x:.0f} | {GRAD*x:.0f} | {8*x:.0f} | {4*x:.0f} | "
                   f"{(W+MASTER+GRAD+8)*x:.0f} | {(W+MASTER+GRAD+4)*x:.0f} |")

    out += ["", "### B. Activations per GPU, one sequence (b = 1), GB", "",
            "| Total params | Shape (h, L) | 4k | 4k, recompute | 8k | 8k, recompute |", "|---|---|---:|---:|---:|---:|"]
    for p in SIZES_B:
        h, L = SHAPES[p]
        out.append(f"| {p}B | {h}, {L} | " + " | ".join(f"{activations_gb(h, L, s, r):.1f}" for s, r in SEQS) + " |")

    for opt in OPT:
        out += ["", f"### C. Per GPU with {opt}: states + activations (b = 1), GB, against {usable:.0f} GB", "",
                "| Total params | Sharding | States | + 4k | + 4k, recompute | + 8k | + 8k, recompute |",
                "|---|---|---:|---:|---:|---:|---:|"]
        for p in SIZES_B:
            h, L = SHAPES[p]
            for shard in SHARDING:
                st = p * per_param_bytes(opt, shard, n)
                out.append(f"| {p}B | {SHARD_TEXT[shard]} | {st:.0f} | "
                           + " | ".join(fmt(st + activations_gb(h, L, s, r), usable) for s, r in SEQS) + " |")

    out += ["", "### D. Largest total size whose states fit, before activations, B params", "",
            "| Optimizer | " + " | ".join(SHARD_TEXT[s] for s in SHARDING) + " |", "|---|" + "---:|" * len(SHARDING)]
    for opt in OPT:
        out.append(f"| {opt} | " + " | ".join(f"{usable / per_param_bytes(opt, s, n):.1f}" for s in SHARDING) + " |")

    # E. The same node with one memory-saving change at a time, all on ZeRO-3 + full recompute, 4k and 8k.
    scen = [("Muon, ZeRO-3 (reference)", W + MASTER + GRAD + 4, 0),
            ("+ no fp32 master (bf16 weights, stochastic rounding)", W + GRAD + 4, 0),
            ("+ no fp32 master, 8-bit Muon momentum", W + GRAD + 1, 0),
            ("+ master and momentum offloaded to CPU RAM", W + GRAD, MASTER + 4),
            ("Adam, master and moments offloaded to CPU RAM", W + GRAD, MASTER + 8)]
    out += ["", "### E. Fit more: one change at a time, ZeRO-3 + full recompute, per GPU GB "
            f"(CPU RAM column: per node)", "",
            "| Setting | GPU B/param | " + " | ".join(f"{p}B 4k | {p}B 8k" for p in SIZES_B) + " | CPU RAM, 25 / 50 / 100 / 150B |",
            "|---|---:|" + "---:|---:|" * len(SIZES_B) + "---|"]
    for name, gpu_b, cpu_b in scen:
        cells = []
        for p in SIZES_B:
            h, L = SHAPES[p]
            st = p * gpu_b / n
            cells += [fmt(st + activations_gb(h, L, 4096, True), usable), fmt(st + activations_gb(h, L, 8192, True), usable)]
        cpu = " / ".join(f"{p * cpu_b:.0f}" for p in SIZES_B) if cpu_b else "-"
        out.append(f"| {name} | {gpu_b / n:.2f} | " + " | ".join(cells) + f" | {cpu} GB |")
    print("\n".join(out))


if __name__ == "__main__":
    main()
