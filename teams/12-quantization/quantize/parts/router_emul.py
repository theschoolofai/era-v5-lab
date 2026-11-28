"""G12 task 1, the router part: what an 8-bit or 4-bit router would do to the choice of experts.

llama-quantize never quantizes `ffn_gate_inp` (the router), so the standard tools never produce a GGUF with a quantized
router. Here the router weights of a public MoE (Hugging Face transformers 5.x, Apple MPS) are rounded to llama.cpp's
Q8_0 or Q4_0 blocks (32 weights along the input dimension, one fp16 scale; Q4_0 stores 0..15 with an offset of 8, as
ggml's quantize_row_q4_0_ref) and kept in fp32, and the router itself is computed in fp32 (as llama.cpp computes its
F32 router); every other weight runs in bf16 as loaded. Each text window runs once with the original router and once
per format, and the script reports, per format:
  - same top-k: the share of (token, layer) pairs whose set of k chosen experts is unchanged, over all layers and for
    layer 0 alone (layer 0's input does not depend on any router, so it shows the direct effect; later layers add the
    knock-on effect of earlier changes); the mean number of experts that change per pair;
  - the model's next-token output: mean KL(original || quantized-router), same top-1 and the NLL change.
The KL here is not on the same footing as llama-perplexity's (other windows, all positions scored, a different
runtime); parts_llamacpp.py's `router-*` variants measure the router in llama.cpp itself.

    python router_emul.py --model allenai/OLMoE-1B-7B-0924 --local <folder> --texts <texts> --out router.json

Text: the train split of the cleaned tokenizer sample v0 (never benchmark items), from kv_llamacpp.py's `text` step
(serving/kv_cache/llamacpp/, #910).
"""
import argparse, json, math, sys, time
from pathlib import Path

import torch
import torch.nn.functional as F

DEFAULT_PACKS = ['en-fineweb-edu', 'code-python', 'ind-hi-fw2', 'ind-bn-fw2', 'ind-ta-fw2', 'ind-kn-fw2']


def q8_0(w):
    """ggml quantize_row_q8_0_ref then dequantize: blocks of 32 along the last dim, d = amax / 127; the codes use the
    fp32 d and roundf (half away from zero), the stored scale is fp16."""
    x = w.float().reshape(-1, 32)
    d = x.abs().amax(dim=1, keepdim=True) / 127
    inv = torch.where(d > 0, 1 / torch.where(d > 0, d, torch.ones_like(d)), torch.zeros_like(d))
    v = x * inv
    q = torch.sign(v) * torch.floor(v.abs() + 0.5)
    return (q * d.half().float()).reshape(w.shape)


def q4_0(w):
    """ggml quantize_row_q4_0_ref then dequantize: d = max / -8 where max is the signed value of largest |x|;
    q = min(15, (int8)(x / d + 8.5)) with the fp32 d; x' = (q - 8) * d with the stored fp16 d."""
    x = w.float().reshape(-1, 32)
    idx = x.abs().argmax(dim=1, keepdim=True)
    d = torch.gather(x, 1, idx) / -8
    inv = torch.where(d != 0, 1 / torch.where(d != 0, d, torch.ones_like(d)), torch.zeros_like(d))
    q = torch.clamp(torch.trunc(x * inv + 8.5), 0, 15)
    return ((q - 8) * d.half().float()).reshape(w.shape)


FORMATS = {'q8_0': q8_0, 'q4_0': q4_0,
           'none': lambda w: w.float()}   # control: the router unchanged; must give KL 0 and 100% same experts


def routers(model):
    """[(name, module)] for every top-k router of the OLMoE / Qwen-MoE kind (transformers 5.x `*TopKRouter`)."""
    return [(name, m) for name, m in model.named_modules()
            if type(m).__name__.endswith('TopKRouter') and hasattr(m, 'weight') and hasattr(m, 'top_k')]


def fp32_router(m):
    """Replace the router's forward with the same computation in fp32 on an fp32 copy of the weights (`m.w32`).
    Returns the original bf16 weights as fp32 (exact)."""
    m.w32 = m.weight.detach().float().clone()

    def forward(hidden_states):
        h = hidden_states.reshape(-1, m.hidden_dim)
        logits = F.linear(h.float(), m.w32)
        probs = F.softmax(logits, dim=-1)
        top_v, top_i = torch.topk(probs, m.top_k, dim=-1)
        if m.norm_topk_prob:
            top_v = top_v / top_v.sum(dim=-1, keepdim=True)
        return logits, top_v.to(hidden_states.dtype), top_i
    m.forward = forward
    return m.w32.clone()


def compare(base_lp, base_sel, lp, sel, ids, k):
    """Metrics of one quantized run against the original run of the same window.
    base_lp / lp: (T, V) log-probs; base_sel / sel: per layer, (T, k) sorted expert ids; ids: the window's token ids."""
    same_set = torch.stack([(s == b).all(dim=-1).float().mean() for s, b in zip(sel, base_sel)])
    changed = torch.stack([(k - (s[:, :, None] == b[:, None, :]).any(-1).sum(-1)).float().mean() for s, b in zip(sel, base_sel)])
    kl = (base_lp.exp() * (base_lp - lp)).sum(-1)                       # KL(original || quantized), per position
    tgt = torch.tensor(ids[1:], device=lp.device)
    dnll = (-lp[:-1].gather(1, tgt[:, None]).squeeze(1)) - (-base_lp[:-1].gather(1, tgt[:, None]).squeeze(1))
    return {'tokens': len(ids), 'same_topk_set': same_set.mean().item(), 'same_topk_set_by_layer': same_set.tolist(),
            'same_topk_set_layer0': same_set[0].item(), 'same_topk_set_later': same_set[1:].mean().item(),
            'experts_changed': changed.mean().item(), 'kl': kl.mean().item(),
            'same_top1': (lp.argmax(-1) == base_lp.argmax(-1)).float().mean().item(), 'dnll': dnll.mean().item()}


def windows(tok, text_path, n, T):
    ids = tok(text_path.read_text(), add_special_tokens=False)['input_ids']
    if len(ids) < n * T: sys.exit(f'{text_path}: {len(ids)} tokens, need {n * T}')
    bos = [tok.bos_token_id] if tok.bos_token_id is not None else []
    return [bos + ids[i * T:(i + 1) * T - len(bos)] for i in range(n)]


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', required=True, help='Hub id (for the record)')
    ap.add_argument('--revision', default=None)
    ap.add_argument('--local', type=Path, required=True, help='downloaded model folder')
    ap.add_argument('--texts', type=Path, required=True)
    ap.add_argument('--packs', nargs='+', default=DEFAULT_PACKS)
    ap.add_argument('--windows', type=int, default=4, help='windows per pack')
    ap.add_argument('--tokens', type=int, default=1024)
    ap.add_argument('--formats', nargs='+', default=['q8_0', 'q4_0'], choices=list(FORMATS))
    ap.add_argument('--device', default='mps')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.local)
    model = AutoModelForCausalLM.from_pretrained(a.local, dtype=torch.bfloat16).to(a.device).eval()
    k = model.config.num_experts_per_tok
    rs = routers(model)
    if not rs: sys.exit('no top-k router modules found (this needs transformers 5.x and an OLMoE / Qwen-MoE model)')
    orig = [fp32_router(m) for _, m in rs]
    picked = []
    hooks = [m.register_forward_hook(lambda mod, i, o: picked.append(o[0])) for _, m in rs]

    def run(ids):
        picked.clear()
        logits = model(torch.tensor([ids], device=a.device)).logits[0].float()
        return F.log_softmax(logits, dim=-1), [torch.topk(l, k, dim=-1).indices.sort(dim=-1).values for l in picked]

    res = {'model': a.model, 'revision': a.revision, 'top_k': k, 'n_routers': len(rs),
           'router_params': sum(w.numel() for w in orig), 'model_params': sum(p.numel() for p in model.parameters()),
           'router_compute': 'fp32 (weights rounded to the format and kept in fp32)', 'windows_per_pack': a.windows,
           'tokens': a.tokens, 'device': a.device, 'torch': torch.__version__, 'transformers': transformers.__version__,
           'argv': sys.argv, 'router_weight_error': {}, 'runs': []}
    for f in a.formats:
        err = [((FORMATS[f](w) - w).norm() / w.norm()).item() for w in orig]
        res['router_weight_error'][f] = {'mean_rel_l2': sum(err) / len(err), 'max_rel_l2': max(err)}
    t0 = time.time()
    for pack in a.packs:
        for wi, ids in enumerate(windows(tok, a.texts / f'{pack}.txt', a.windows, a.tokens)):
            for (_, m), w0 in zip(rs, orig): m.w32.copy_(w0)
            base_lp, base_sel = run(ids)
            for f in a.formats:
                for (_, m), w0 in zip(rs, orig): m.w32.copy_(FORMATS[f](w0))
                lp, sel = run(ids)
                res['runs'].append({'pack': pack, 'window': wi, 'format': f, **compare(base_lp, base_sel, lp, sel, ids, k)})
                r = res['runs'][-1]
                print(f"{pack:15s} w{wi} {f}: same top-{k} set {r['same_topk_set']:.4f} (layer 0 {r['same_topk_set_layer0']:.4f}), "
                      f"KL {r['kl']:.5f}, top-1 {r['same_top1']:.4f}, dNLL {r['dnll']:+.5f}", flush=True)
            a.out.write_text(json.dumps(res, indent=1) + '\n')
    for (_, m), w0 in zip(rs, orig): m.w32.copy_(w0)
    for h in hooks: h.remove()
    summ = {}
    for f in a.formats:
        rr = [r for r in res['runs'] if r['format'] == f]
        n = len(rr)
        mean = lambda key: sum(r[key] for r in rr) / n
        se = lambda key: math.sqrt(sum((r[key] - mean(key)) ** 2 for r in rr) / (n - 1)) / math.sqrt(n) if n > 1 else float('nan')
        keys = ('same_topk_set', 'same_topk_set_layer0', 'same_topk_set_later', 'experts_changed', 'kl', 'same_top1', 'dnll')
        summ[f] = {key: mean(key) for key in keys}
        summ[f].update({'kl_se_over_windows': se('kl'), 'dnll_se_over_windows': se('dnll'), 'windows': n})
        ch = [1 - r['same_topk_set'] for r in rr]
        summ[f]['experts_changed_per_changed_set'] = mean('experts_changed') / (sum(ch) / n) if sum(ch) else 0.0
    res['summary'] = summ; res['seconds'] = time.time() - t0
    a.out.write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
