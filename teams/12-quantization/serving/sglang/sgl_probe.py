#!/usr/bin/env python3
"""Load our ERNIE-layout export in SGLang and dump prompt log-probabilities (runs on a CUDA GPU; see modal_sgl.py).

    python sgl_probe.py --model <export dir> --prompts <ref dir>/prompts.json --out <out>.json --dtype bfloat16

Runs every prompt twice: one request at a time, then all prompts in one batched call (a first look at whether the
numbers depend on the batch). Token ids go in directly (skip_tokenizer_init), so the tokenizer is not involved.
One new token per prompt (max_new_tokens=1), so only prefill is exercised; the radix cache is off.
"""
import argparse, json, time


def run(engine, prompts, batched: bool, k: int):
    sp = dict(max_new_tokens=1, temperature=0.0)
    kw = dict(return_logprob=True, logprob_start_len=0, top_logprobs_num=k)
    if batched:
        rs = engine.generate(input_ids=prompts, sampling_params=[sp] * len(prompts), **kw)
    else:
        rs = [engine.generate(input_ids=p, sampling_params=sp, **kw) for p in prompts]
    keep = ('input_token_logprobs', 'input_top_logprobs', 'output_token_logprobs', 'output_top_logprobs')
    return [{key: r['meta_info'].get(key) for key in keep} for r in rs]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', required=True)
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--dtype', default='bfloat16')
    ap.add_argument('--attention-backend', default=None)
    ap.add_argument('--disable-cuda-graph', action='store_true')
    ap.add_argument('--top-k', type=int, default=5)
    a = ap.parse_args()
    import sglang as sgl
    import torch
    kwargs = dict(model_path=a.model, dtype=a.dtype, skip_tokenizer_init=True, disable_radix_cache=True,
                  mem_fraction_static=0.5, random_seed=0, log_level='info')
    if a.attention_backend:
        kwargs['attention_backend'] = a.attention_backend
    if a.disable_cuda_graph:
        kwargs['disable_cuda_graph'] = True
    t0 = time.time()
    engine = sgl.Engine(**kwargs)
    load_s = time.time() - t0
    prompts = json.load(open(a.prompts))
    single = run(engine, prompts, batched=False, k=a.top_k)
    batched = run(engine, prompts, batched=True, k=a.top_k)
    engine.shutdown()
    json.dump(dict(config=vars(a), sglang=sgl.__version__, torch=torch.__version__,
                   gpu=torch.cuda.get_device_name(0), load_seconds=load_s, single=single, batched=batched),
              open(a.out, 'w'))
    print(f'PROBE_OK {a.out}', flush=True)


if __name__ == '__main__':
    main()
