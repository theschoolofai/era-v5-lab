"""Compute total/active parameters and critical depth for the Lab 5 study table (G5 design task 1).

Formulas
--------
Dense FFN block: 3 * d * d_ff          (gate, up, down)
Expert FFN block: 3 * d * d_expert     (same shape per expert)
Attention (GQA, no bias): d*kv_head_dim*n_kv*2 (k,v) + d*n_head*head_dim (q) + n_head*head_dim*d (o)
Embedding: vocab * d  (tied or untied both count once for total; head adds another vocab*d if untied)

Critical depth (Depth Delusion, arXiv 2601.20994, eq. 4):
    D_crit ~ W^0.44     and  D_crit ~= 2.43 * ln(W) in the paper's fitted range (W in [256,1536])
The paper's constant is fitted on W<=1536, so extrapolation to W~2048-7168 is *outside* the fitted range.
Both numbers are reported so the extrapolation is visible rather than hidden.
"""
import json
import math
import sys
from pathlib import Path

CFGS = Path(sys.argv[1] if len(sys.argv) > 1 else "configs-cache")
# Fetch the configs first:
#   for m in Qwen/Qwen3-30B-A3B Qwen/Qwen3-235B-A22B ...; do
#     curl -sL "https://huggingface.co/$m/raw/main/config.json" -o "configs-cache/$(echo $m | tr / _).json"; done


def load(name):
    d = json.load(open(CFGS / f"{name}.json"))
    for sub in ("text_config", "llm_config", "language_config"):
        if sub in d and isinstance(d[sub], dict):
            for k, v in d[sub].items():
                d.setdefault(k, v)
    return d


def experts(d):
    return d.get("num_experts") or d.get("n_routed_experts") or d.get("num_local_experts") or 0


def shared(d):
    return d.get("n_shared_experts") or 0


def analyse(name, label):
    d = load(name)
    L = d["num_hidden_layers"]
    h = d["hidden_size"]
    nh = d.get("num_attention_heads", 0)
    nkv = d.get("num_key_value_heads", nh)
    hd = d.get("head_dim") or (h // nh if nh else 0)
    V = d["vocab_size"]
    E = experts(d)
    k = d.get("num_experts_per_tok", 0)
    d_ff = d.get("intermediate_size", 0)
    d_ex = d.get("moe_intermediate_size") or d.get("intermediate_size", 0)
    d_sh = d.get("shared_expert_intermediate_size") or d.get("shared_intermediate_size") or 0
    dense_layers = d.get("first_k_dense_replace", 0)

    emb = V * h
    # attention per layer
    attn = h * hd * nh + h * hd * nkv * 2 + hd * nh * h
    # dense FFN layers (first_k are dense in DeepSeek-style)
    dense_ffn = dense_layers * 3 * h * d_ff
    moe_layers = L - dense_layers
    # expert params
    per_expert = 3 * h * d_ex
    all_experts = moe_layers * E * per_expert
    shared_par = moe_layers * shared(d) * 3 * h * (d_sh or d_ex)
    total = emb + L * attn + dense_ffn + all_experts + shared_par
    active = (emb + L * attn + dense_ffn
              + moe_layers * k * per_expert + shared_par)
    W = h
    dcrit_pow = W ** 0.44
    dcrit_log = 2.43 * math.log(W)
    return dict(label=label, L=L, d=h, heads=nh, kv=nkv, head_dim=hd, V=V, E=E, k=k,
                d_ex=d_ex, d_shared=d_sh, d_ff=d_ff, dense_layers=dense_layers,
                total=total, active=active, ratio=100 * active / total,
                W=W, dcrit_pow=dcrit_pow, dcrit_log=dcrit_log)


MODELS = [
    ("Qwen_Qwen3-30B-A3B", "Qwen3-30B-A3B"),
    ("Qwen_Qwen3-235B-A22B", "Qwen3-235B-A22B"),
    ("Qwen_Qwen3-Next-80B-A3B-Thinking", "Qwen3-Next-80B-A3B-Thinking"),
    ("deepseek-ai_DeepSeek-V3", "DeepSeek-V3"),
    ("deepseek-ai_DeepSeek-V3.2", "DeepSeek-V3.2"),
    ("zai-org_GLM-4.5", "GLM-4.5"),
    ("MiniMaxAI_MiniMax-M2", "MiniMax-M2"),
    ("moonshotai_Kimi-K2-Instruct", "Kimi-K2-Instruct"),
]

rows = [analyse(n, l) for n, l in MODELS]
hdr = f"{'model':26s} {'L':>3s} {'d':>5s} {'heads':>5s} {'kv':>3s} {'E':>4s} {'topk':>4s} {'d_exp':>6s} {'d_sh':>5s} {'V':>6s} {'total':>8s} {'active':>8s} {'act%':>6s} {'Dcrit':>6s} {'2.43lnW':>7s}"
print(hdr)
print("-" * len(hdr))
for r in rows:
    print(f"{r['label']:26s} {r['L']:3d} {r['d']:5d} {r['heads']:5d} {r['kv']:3d} {r['E']:4d} {r['k']:4d} "
          f"{r['d_ex']:6d} {r['d_shared']:5d} {r['V']:6d} {r['total']/1e9:8.2f} {r['active']/1e9:8.2f} "
          f"{r['ratio']:6.1f} {r['dcrit_pow']:6.0f} {r['dcrit_log']:7.0f}")
print()
print("total/active in billions. Dcrit = W^0.44 (power form). 2.43lnW = the paper's practical fit (valid W<=1536).")
print()
print("=== how far outside the fit are we? ===")
for r in rows:
    over = r['L'] - r['dcrit_pow']
    print(f"{r['label']:26s} L={r['L']:3d}  Dcrit(pow)={r['dcrit_pow']:5.0f}  ->  {over:+5.0f} layers vs critical")
