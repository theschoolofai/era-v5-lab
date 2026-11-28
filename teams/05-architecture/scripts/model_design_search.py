"""G5 design task 2: size the two sparse models, with training-memory feasibility on 8x80 GB.

Run:  python teams/05-architecture/scripts/model_design_search.py
      (stdlib only, no input files)

Constraints from the Lab 5 brief:
  - planning assumption: one node, 8 GPUs x 80 GB
  - expert counts must divide evenly across 8 GPUs
  - design (a) ~30B total at 8-10% active
  - design (b) ~100B total at 2-3% active
  - our tokenizer is p1536: vocab 131,072

Memory model (per GPU, fully sharded over 8 ranks):
  weights   : params * bytes_per_param            (bf16 = 2)
  gradients : params * 2
  optimizer : Muon 1 buffer 4 B for 2D weights, AdamW 2 moments 8 B for 1D weights
  total     : (w + g + opt) / 8 + activation reserve
Activation reserve is a rough function of batch x seq x d x L; kept explicit so it can be argued.
"""
import itertools
import math

V = 131072          # p1536 vocab
NGPU = 8
GPU_GB = 80
GB = 1e9


def params(d, L, E, k, d_ex, n_heads, n_kv, head_dim, d_ff=None, dense_layers=0, d_shared=0):
    emb = V * d
    attn = d * head_dim * n_heads * 2 + d * head_dim * n_kv * 2
    dense_ffn = dense_layers * 3 * d * (d_ff or 4 * d)
    moe_layers = L - dense_layers
    per_expert = 3 * d * d_ex
    total = emb + L * attn + dense_ffn + moe_layers * E * per_expert + moe_layers * d_shared * 3 * d
    active = emb + L * attn + dense_ffn + moe_layers * k * per_expert + moe_layers * d_shared * 3 * d
    # split by ndim for the optimizer: all matmuls are 2D, norms/biases 1D (small, ignored here)
    two_d = total - emb          # embedding is 2D too, but usually in the AdamW group by convention
    return total, active, two_d


def mem_per_gpu(total, two_d, act_gb):
    w = total * 2
    g = total * 2
    opt = two_d * 4 + (total - two_d) * 8
    return (w + g + opt) / NGPU / GB + act_gb


def report(label, **kw):
    total, active, two_d = params(**kw)
    act = 100 * active / total
    D = kw["L"]
    W = kw["d"]
    dcrit_pow = W ** 0.44
    mem = mem_per_gpu(total, two_d, kw.pop("act_gb", 20))
    return dict(label=label, total=total / 1e9, active=active / 1e9, ratio=act,
                L=D, W=W, E=kw["E"], k=kw["k"], d_ex=kw["d_ex"],
                dcrit=dcrit_pow, mem=mem, **{kk: vv for kk, vv in kw.items() if kk in ("n_heads", "n_kv", "head_dim")})


CANDIDATES_A = []
# 30B, 8-10% active. Sweep d, L, E, k with expert count divisible by 8.
for d, L, n_heads, n_kv, hd in [
    (2048, 48, 32, 4, 128),
    (2048, 56, 32, 4, 128),
    (2304, 48, 36, 4, 128),
    (2560, 48, 40, 4, 128),
]:
    for E, k in [(128, 8), (128, 12), (256, 16), (256, 24), (192, 12)]:
        for d_ex in (768, 896, 1024):
            total, active, two_d = params(d, L, E, k, d_ex, n_heads, n_kv, hd)
            ratio = 100 * active / total
            if 27e9 <= total <= 33e9 and 8.0 <= ratio <= 10.0 and E % NGPU == 0:
                CANDIDATES_A.append((total / 1e9, ratio, d, L, E, k, d_ex, n_heads, n_kv))

CANDIDATES_B = []
# 100B, 2-3% active.
for d, L, n_heads, n_kv, hd in [
    (3072, 48, 48, 8, 128),
    (3584, 48, 56, 8, 128),
    (4096, 40, 64, 8, 128),
    (4096, 48, 64, 8, 128),
]:
    for E, k in [(256, 8), (256, 12), (512, 12), (512, 16), (384, 12)]:
        for d_ex in (1024, 1280, 1536):
            total, active, two_d = params(d, L, E, k, d_ex, n_heads, n_kv, hd)
            ratio = 100 * active / total
            if 90e9 <= total <= 115e9 and 2.0 <= ratio <= 3.5 and E % NGPU == 0:
                CANDIDATES_B.append((total / 1e9, ratio, d, L, E, k, d_ex, n_heads, n_kv))


def show(name, rows):
    print(f"\n=== {name}: {len(rows)} feasible parameter combinations ===")
    print(f"{'total':>7s} {'act%':>5s} {'d':>5s} {'L':>3s} {'E':>4s} {'k':>3s} {'d_ex':>5s} {'heads/kv':>9s} {'Dcrit':>6s} {'mem/GPU':>8s}")
    for t, r, d, L, E, k, d_ex, nh, nkv in sorted(rows, key=lambda x: abs(x[0] - (30 if name.startswith('30') else 100))):
        total, active, two_d = params(d, L, E, k, d_ex, nh, nkv, 128)
        m = mem_per_gpu(total, two_d, 20)
        print(f"{t:7.2f} {r:5.2f} {d:5d} {L:3d} {E:4d} {k:3d} {d_ex:5d} {nh:5d}/{nkv:<3d} {d**0.44:6.0f} {m:7.1f}G")


show("30B", CANDIDATES_A)
show("100B", CANDIDATES_B)
print("\nmem/GPU assumes full ZeRO-3 sharding of weights+grads+optimizer and a 20 GB activation reserve.")
print("Above 80 GB the design does not train on the stated single node.")
