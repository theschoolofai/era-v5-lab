#!/usr/bin/env python3
"""The same check on vLLM (runs on a CUDA GPU; see modal_vllm.py). Writes the layout of sgl_probe.py
(input_token_logprobs / input_top_logprobs / output_top_logprobs as [logprob, token_id, None]), so summarize.py reads
both engines the same way.

    python vllm_probe.py --model <export dir> --prompts <ref dir>/prompts.json --out <out>.json --dtype bfloat16
"""
import argparse, json, time


def top(d: dict, k: int):
    """vLLM {token_id: Logprob} -> top-k [[lp, id, None]] by rank (the dict also holds the real token)."""
    items = sorted(d.items(), key=lambda kv: kv[1].rank)[:k]
    return [[v.logprob, tid, None] for tid, v in items]


def convert(res, prompt, k):
    pl = res.prompt_logprobs                     # len T; [0] is None; [i] is the distribution for token i
    itl = [None] + [[pl[i][prompt[i]].logprob, prompt[i], None] for i in range(1, len(prompt))]
    itop = [None] + [top(pl[i], k) for i in range(1, len(prompt))]
    otop = [top(res.outputs[0].logprobs[0], k)]
    return dict(input_token_logprobs=itl, input_top_logprobs=itop, output_top_logprobs=otop)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', required=True)
    ap.add_argument('--prompts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--dtype', default='bfloat16')
    ap.add_argument('--eager', action='store_true')
    ap.add_argument('--top-k', type=int, default=5)
    a = ap.parse_args()
    import torch, vllm
    from vllm import LLM, SamplingParams
    from vllm.inputs import TokensPrompt
    t0 = time.time()
    llm = LLM(model=a.model, dtype=a.dtype, skip_tokenizer_init=True, enforce_eager=a.eager, seed=0,
              gpu_memory_utilization=0.5, max_model_len=2048, enable_prefix_caching=False)
    load_s = time.time() - t0
    prompts = json.load(open(a.prompts))
    sp = SamplingParams(max_tokens=1, temperature=0.0, prompt_logprobs=a.top_k, logprobs=a.top_k, detokenize=False)
    single = [convert(llm.generate([TokensPrompt(prompt_token_ids=p)], sp, use_tqdm=False)[0], p, a.top_k)
              for p in prompts]
    outs = llm.generate([TokensPrompt(prompt_token_ids=p) for p in prompts], sp, use_tqdm=False)
    batched = [convert(r, p, a.top_k) for r, p in zip(outs, prompts)]
    json.dump(dict(config=vars(a), sglang=f'vllm {vllm.__version__}', torch=torch.__version__,
                   gpu=torch.cuda.get_device_name(0), load_seconds=load_s, single=single, batched=batched),
              open(a.out, 'w'))
    print(f'PROBE_OK {a.out}', flush=True)


if __name__ == '__main__':
    main()
