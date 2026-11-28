#!/usr/bin/env python3
"""G5 reference log-probabilities for the SGLang and vLLM check.

    python make_ref.py --checkpoint <random checkpoint dir> --out <ref dir>

Builds G5's LanguageModel from the checkpoint exactly as export_hf.py's A1 test does, runs 12 random prompts
(16 to 512 tokens, seed 0) and saves, per prompt and position, the log-probability of the next real token, the
top-5 next tokens and the top-1 logit margin. Writes <ref dir>/prompts.json and ref.json.

The export is written with --drop-head-bias, so the reference an engine should match is G5 *minus* head.unigram
(fp32_nobias). Two more variants are saved: bf16 autocast on CPU (bf16_nobias) and the full model with its KAS
output bias (fp32_full), to show what dropping that bias changes on a random model. variants.py adds the rest.
Needs torch and this repo (export_hf.py and G5's harness); CPU only, about a minute at the dry-run-2 shape.
"""
import argparse, json, sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))   # teams/12-quantization/scripts
import export_hf as ex  # noqa: E402


def summarize(logits: torch.Tensor, ids: torch.Tensor, k: int = 5) -> dict:
    """logits [T, V] -> next-token log-probs of the real tokens, top-k, and the top-1 margin (logit gap)."""
    lp = logits.float().log_softmax(-1)
    T = ids.shape[0]
    target = lp[torch.arange(T - 1), ids[1:]]                       # position i predicts token i+1
    top = lp.topk(k, dim=-1)
    gap = logits.float().topk(2, dim=-1).values
    return dict(target_lp=target.tolist(), top_ids=top.indices.tolist(), top_lp=top.values.tolist(),
                margin=(gap[:, 0] - gap[:, 1]).tolist())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--checkpoint', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--lengths', default='16,32,64,128,256,512,16,32,64,128,256,512')
    a = ap.parse_args()
    weights, manifest = ex.find_checkpoint(a.checkpoint)
    state = ex.load_state(weights)
    spec = ex.resolve_spec(state, ex.load_spec(manifest))
    sys.path.insert(0, str(ex.HARNESS))
    from week2.model import LanguageModel
    ref = LanguageModel(dict(spec, mtp='mtp_head.weight' in state), state['embedding.rows'].numpy(),
                        state['embedding.lengths'].numpy()).eval()
    ex.load_reference(ref, state)
    unigram = state['head.unigram'].float()
    gen = torch.Generator().manual_seed(a.seed)
    prompts, out = [], dict(fp32_nobias=[], bf16_nobias=[], fp32_full=[])
    with torch.no_grad():
        for T in (int(x) for x in a.lengths.split(',')):
            ids = torch.randint(0, spec['vocab_size'], (1, T), generator=gen)
            mask = torch.ones_like(ids, dtype=torch.bool)
            full = ref(ids, mask)[0].float()
            with torch.autocast('cpu', dtype=torch.bfloat16):
                full_bf16 = ref(ids, mask)[0].float()
            prompts.append(ids[0].tolist())
            out['fp32_full'].append(summarize(full, ids[0]))
            out['fp32_nobias'].append(summarize(full - unigram, ids[0]))
            out['bf16_nobias'].append(summarize(full_bf16 - unigram, ids[0]))
            print(f'T={T} done', flush=True)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'prompts.json').write_text(json.dumps(prompts))
    (a.out / 'ref.json').write_text(json.dumps(dict(spec=spec, seed=a.seed, **out)))
    print(f'wrote {a.out}/prompts.json and ref.json ({len(prompts)} prompts)')


if __name__ == '__main__':
    main()
