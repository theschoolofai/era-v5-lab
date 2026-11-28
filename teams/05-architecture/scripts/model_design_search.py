"""G5 design task 2: size the two sparse models, with memory feasibility on 8x80 GB.

Run:  python teams/05-architecture/scripts/model_design_search.py
      (stdlib only, no input files)

Shapes follow the G5 implementation, not a textbook transformer:

  head_dim    derived as `n_embd // n_head`       (model.py, GQA.__init__: self.d = w // self.nh)
  embedding   KAS V2: KASInput.projection = Linear(2048, n_embd) and
  + head      KASHead.W_out = (n_embd, 2048)      (kas_v2.py)
              so the term is 2 * n_embd * 2048, NOT vocab * n_embd.

Memory is reported three ways because the trainer keeps FP32 parameters and gradients and autocasts the
computation, which is the case that decides whether a design is buildable:

  fp32 resident   FP32 weights + grads + Muon state (4 B/param) on the GPU
  fp32 offload    FP32 weights + grads on the GPU, optimizer state in host RAM
  bf16 offload    bf16 weights + grads, optimizer in host RAM

Optimizer state is Muon's single buffer (4 B/param). AdamW's two moments (8 B/param) make every case worse.
"""
import math

NGPU, GPU_GB, GB = 8, 80, 1e9
KAS_WIDTH = 2048          # the fixed KAS V2 codec width


def params(d, L, E, k, d_ex, n_head, n_kv):
    """(total, active, two_d) for one design. head_dim is derived, as model.py does."""
    hd = d // n_head
    emb_head = 2 * d * KAS_WIDTH                     # KAS input projection + head
    attn = d * hd * n_head * 2 + d * hd * n_kv * 2   # q,o at n_head; k,v at n_kv
    per_expert = 3 * d * d_ex
    total = emb_head + L * attn + L * E * per_expert
    active = emb_head + L * attn + L * k * per_expert
    return total, active, total - emb_head


def mem_per_gpu(total, act_gb=20, param_bytes=4, opt_bytes=4, offload=False):
    wg = total * param_bytes * 2
    opt = 0 if offload else total * opt_bytes
    return (wg + opt) / NGPU / GB + act_gb


def dcrit(w):
    return w ** 0.44


# Both designs use head dim 128: A1 is 3072/24, B3 is 4096/32. Head dim is derived as d // n_head
# (model.py), so n_head is the knob. B3 at n_head=64 would give head dim 64; it is 98.16B/3.79B instead of
# 98.33B/3.96B -- a 0.2% difference that does not change any conclusion.
DESIGNS = [
    ("A1", dict(d=3072, L=32, E=128, k=8,  d_ex=768, n_head=24, n_kv=4)),
    ("B3", dict(d=4096, L=40, E=256, k=6,  d_ex=768, n_head=32, n_kv=8)),  # head dim 128
    ("A2", dict(d=3072, L=32, E=64,  k=4,  d_ex=1536, n_head=24, n_kv=4)),
    ("A3", dict(d=2560, L=40, E=128, k=8,  d_ex=768, n_head=20, n_kv=4)),
]

hdr = (f"{'design':6s} {'d':>5s} {'L':>3s} {'E':>4s} {'k':>3s} {'d_ex':>5s} {'hd':>3s} "
       f"{'total':>8s} {'active':>7s} {'act%':>5s} {'Dcrit':>5s} {'L/Dc':>5s} "
       f"{'fp32 res':>9s} {'fp32 off':>9s} {'bf16 off':>9s}")
print(hdr)
print("-" * len(hdr))
for name, kw in DESIGNS:
    total, active, _ = params(**kw)
    hd = kw["d"] // kw["n_head"]
    res = mem_per_gpu(total)
    off = mem_per_gpu(total, offload=True)
    boff = mem_per_gpu(total, param_bytes=2, offload=True)
    dc = dcrit(kw["d"])
    flag = lambda m: f"{m:5.1f}G{'' if m <= GPU_GB else '!'}"
    print(f"{name:6s} {kw['d']:5d} {kw['L']:3d} {kw['E']:4d} {kw['k']:3d} {kw['d_ex']:5d} {hd:3d} "
          f"{total/1e9:7.2f}B {active/1e9:6.2f}B {100*active/total:5.1f} {dc:5.0f} {kw['L']/dc:5.2f} "
          f"{flag(res):>9s} {flag(off):>9s} {flag(boff):>9s}")

print("\n! = does not fit 80 GB. 20 GB activation reserve assumed in every column.")
print("Optimizer is Muon (4 B/param). AdamW (8 B/param) is worse in every row.")
print()
print("Max total parameters that fit 8x80 GB, FP32 weights+grads, Muon resident:")
for t in (20, 25, 30, 35, 40, 45, 50):
    m = mem_per_gpu(t * 1e9)
    print(f"  {t:3d}B -> {m:5.1f} G  {'fits' if m <= GPU_GB else 'does not fit'}")
print()
print("CPU RAM needed for the optimizer state when offloaded:")
for name, kw in DESIGNS:
    total, _, _ = params(**kw)
    print(f"  {name}: {total*4/1e9:5.0f} GB (Muon) | {total*8/1e9:5.0f} GB (AdamW)")
