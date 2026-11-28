#!/usr/bin/env python3
"""More G5 reference variants on the same prompts, to read the distance between an engine and G5.

    python variants.py --checkpoint <random checkpoint dir> --prompts <ref dir>/prompts.json --out <ref dir>/variants.json

Every variant is G5 minus head.unigram (what the export carries):
  fp16_autocast        CPU autocast fp16 (fp32 weights and residual stream)
  bf16_pure            the whole model cast to bf16 (weights, activations, residual stream), as an all-bf16 engine
                       runs; G5's router still computes in fp32 from the bf16-rounded weights (model.py casts it)
  fp16_pure            the same in fp16
  fp32_no_router_bias  router_bias zeroed: what an engine that ignored the selection bias would give
"""
import argparse, copy, json, sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_ref import ex, summarize  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--checkpoint', type=Path, required=True)
    ap.add_argument('--prompts', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    weights, manifest = ex.find_checkpoint(a.checkpoint)
    state = ex.load_state(weights)
    spec = ex.resolve_spec(state, ex.load_spec(manifest))
    sys.path.insert(0, str(ex.HARNESS))
    from week2.model import LanguageModel

    def build(st):
        m = LanguageModel(dict(spec, mtp='mtp_head.weight' in st), st['embedding.rows'].numpy(),
                          st['embedding.lengths'].numpy()).eval()
        ex.load_reference(m, st)
        return m

    ref = build(state)
    nob = copy.deepcopy(state)
    for k in nob:
        if k.endswith('.router_bias'):
            nob[k] = torch.zeros_like(nob[k])
    ref_nob = build(nob)
    pure = {dt: copy.deepcopy(ref).to(dt) for dt in (torch.bfloat16, torch.float16)}
    unigram = state['head.unigram'].float()
    prompts = json.loads(a.prompts.read_text())
    out = {k: [] for k in ('fp16_autocast', 'bf16_pure', 'fp16_pure', 'fp32_no_router_bias')}
    with torch.no_grad():
        for p in prompts:
            ids = torch.tensor([p])
            mask = torch.ones_like(ids, dtype=torch.bool)
            with torch.autocast('cpu', dtype=torch.float16):
                out['fp16_autocast'].append(summarize(ref(ids, mask)[0].float() - unigram, ids[0]))
            out['bf16_pure'].append(summarize(pure[torch.bfloat16](ids, mask)[0].float() - unigram, ids[0]))
            out['fp16_pure'].append(summarize(pure[torch.float16](ids, mask)[0].float() - unigram, ids[0]))
            out['fp32_no_router_bias'].append(summarize(ref_nob(ids, mask)[0].float() - unigram, ids[0]))
            print(f'T={len(p)} done', flush=True)
    a.out.write_text(json.dumps(out))
    print(f'wrote {a.out}')


if __name__ == '__main__':
    main()
