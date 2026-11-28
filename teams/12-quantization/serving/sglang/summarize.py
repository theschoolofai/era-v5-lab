#!/usr/bin/env python3
"""Engines against G5: the README tables and results/spike_summary.json, from the probe outputs and the references.

    python summarize.py --ref <ref dir> --runs <out dir> --out results/spike_summary.json \
        [--std-ref 0.1=<ref dir, std 0.1 model> --std-ref 0.05=<ref dir, std 0.05 model>]

<ref dir> holds prompts.json and ref.json (make_ref.py) and variants.json (variants.py); <out dir> holds the probe
outputs and logs (modal_sgl.py, modal_vllm.py). Standard library only.

Alignment (SGLang 0.5.23, logprob_result_processor.py; vllm_probe.py writes the same layout). G5 position i predicts
token i+1. An engine's input_top_logprobs[i] (i >= 1) is the distribution for token i given the tokens before it, so
it matches G5 position i-1, and output_top_logprobs[0] (the one generated token) matches position T-1.
input_token_logprobs[i] is the log-probability of real token i, so it matches G5's target_lp[i-1]. Same top-1 is
counted over all T positions of a prompt (2,016 here), the log-probability differences over T-1 (2,004).
"""
from __future__ import annotations

import argparse, json, re
from pathlib import Path

RUNS = {   # probe output name: (engine, dtype, build)
    'c2_s002_bf16': ('sglang', 'bf16', 'stock'),
    'c3_s002_fp16': ('sglang', 'fp16', 'stock'),
    'c2_s002_bf16_patched': ('sglang', 'bf16', 'patched'),
    'c3_s002_fp16_patched': ('sglang', 'fp16', 'patched'),
    'v2_s002_bf16': ('vllm', 'bf16', 'stock'),
    'v3_s002_fp16': ('vllm', 'fp16', 'stock'),
}
FP32 = {'c1_s002_fp32': ('sglang', 'fp32', 'stock'), 'v1_s002_fp32': ('vllm', 'fp32', 'stock')}
REFS = {   # name: (file, key); every one is G5 without head.unigram except g5_with_head_bias
    'g5': ('ref', 'fp32_nobias'),                       # what the --drop-head-bias export should give
    'g5_router_bias_off': ('variants', 'fp32_no_router_bias'),
    'g5_bf16': ('variants', 'bf16_pure'),
    'g5_fp16': ('variants', 'fp16_pure'),
    'g5_bf16_autocast': ('ref', 'bf16_nobias'),
    'g5_fp16_autocast': ('variants', 'fp16_autocast'),
    'g5_with_head_bias': ('ref', 'fp32_full'),
}
ENGINE_REFS = ('g5', 'g5_router_bias_off', 'g5_bf16', 'g5_fp16')
TAIL = 0.1   # count of positions with |delta log-prob| above this


def sig(x: float, n: int = 6) -> float:
    return float(f'{x:.{n}g}')


def from_engine(r: dict, prompt: list[int]) -> tuple[list[float], list[int]]:
    """One probe result -> (target log-probs for G5 positions 0..T-2, top-1 ids for G5 positions 0..T-1)."""
    T = len(prompt)
    itl, itop, otop = r['input_token_logprobs'], r['input_top_logprobs'], r['output_top_logprobs']
    first = itl[0] if itl else None   # SGLang: [None, id, None]; vllm_probe.py: None
    if len(itl) != T or len(itop) != T or itop[0] is not None or (first is not None and first[0] is not None):
        raise ValueError(f'unexpected layout: {len(itl)} / {len(itop)} entries for a {T}-token prompt')
    if [x[1] for x in itl[1:]] != prompt[1:] or (first is not None and first[1] != prompt[0]):
        raise ValueError('input_token_logprobs ids differ from the prompt')
    return [itl[i][0] for i in range(1, T)], [itop[i][0][1] for i in range(1, T)] + [otop[0][0][1]]


def from_g5(rp: dict) -> tuple[list[float], list[int]]:
    return rp['target_lp'], [t[0] for t in rp['top_ids']]


def compare(a: list, b: list) -> dict:
    """a, b: per prompt (target log-probs, top-1 ids). Same top-1, mean and max |delta log-prob|, tail count."""
    n = same = m = tail = 0
    dsum = dmax = 0.0
    for (ta, ia), (tb, ib) in zip(a, b, strict=True):
        for x, y in zip(ta, tb, strict=True):
            d = abs(x - y)
            dsum, dmax, m, tail = dsum + d, max(dmax, d), m + 1, tail + (d > TAIL)
        for x, y in zip(ia, ib, strict=True):
            n, same = n + 1, same + (x == y)
    return dict(same_top1=same, positions=n, mean_abs_dlp=sig(dsum / m), max_abs_dlp=sig(dmax), over_0p1=tail)


def fp32_error(log: Path) -> str | None:
    """The last 'SomethingError: message' (or Triton's OutOfResources) line of a failed run, without the wrapper."""
    hits = [ln.strip() for ln in log.read_text(errors='replace').splitlines()
            if re.match(r'^\s*(?:[\w.]+\.)?(?:\w+Error|OutOfResources): ', ln) and 'Engine core initialization' not in ln]
    return re.sub(r'^(?:[\w]+\.)+(?=\w+: )', '', hits[-1]) if hits else None


def build(ref_dir: Path, runs_dir: Path, std_refs: dict[str, Path]) -> dict:
    prompts = json.loads((ref_dir / 'prompts.json').read_text())
    files = {'ref': json.loads((ref_dir / 'ref.json').read_text()),
             'variants': json.loads((ref_dir / 'variants.json').read_text())}
    refs = {k: [from_g5(rp) for rp in files[f][key]] for k, (f, key) in REFS.items()}
    out = dict(
        about='Same top-1 and |delta log-prob of the real next token| against G5, from summarize.py. Random weights at '
              'the dry-run-2 shape (std 0.02); 12 random prompts of 16-512 tokens.',
        prompts=dict(count=len(prompts), lengths=[len(p) for p in prompts], top1_positions=sum(map(len, prompts)),
                     logprob_positions=sum(len(p) - 1 for p in prompts)),
        model=files['ref']['spec'],
        g5={k: {r: compare(refs[k], refs[r]) for r in ('g5', 'g5_router_bias_off')}
            for k in REFS if k not in ('g5', 'g5_router_bias_off')},
        runs={}, fp32={}, std_check={})
    out['g5']['g5_router_bias_off'] = {'g5': compare(refs['g5_router_bias_off'], refs['g5'])}
    for name, (engine, dtype, build_) in RUNS.items():
        o = json.loads((runs_dir / f'{name}.json').read_text())
        modes = {m: [from_engine(r, p) for r, p in zip(o[m], prompts, strict=True)] for m in ('single', 'batched')}
        out['runs'][name] = dict(
            engine=engine, dtype=dtype, build=build_, version=o['sglang'].removeprefix('vllm '), torch=o['torch'],
            gpu=o['gpu'], **{m: {r: compare(modes[m], refs[r]) for r in ENGINE_REFS} for m in modes},
            single_vs_batched=compare(modes['single'], modes['batched']))
    for name, (engine, dtype, _) in FP32.items():
        ok = (runs_dir / f'{name}.json').exists()
        out['fp32'][name] = dict(engine=engine, dtype=dtype, ran=ok,
                                 error=None if ok else fp32_error(runs_dir / f'{name}.log'))
    for std, d in sorted(std_refs.items(), key=lambda kv: -float(kv[0])):
        r = json.loads((d / 'ref.json').read_text())
        s = compare([from_g5(x) for x in r['bf16_nobias']], [from_g5(x) for x in r['fp32_nobias']])
        out['std_check'][std] = dict(same_top1=s['same_top1'], positions=s['positions'])
    s = out['g5']['g5_bf16_autocast']['g5']   # the main model's own row (std 0.02)
    out['std_check']['0.02'] = dict(same_top1=s['same_top1'], positions=s['positions'])
    return out


def pct(s: dict) -> str:
    return f"{s['same_top1']}/{s['positions']} ({100 * s['same_top1'] / s['positions']:.2f}%)"


def report(v: dict) -> None:
    print('reference: G5 fp32 without head.unigram (what the --drop-head-bias export carries)\n')
    print(f"{'':34s} {'same top-1 vs G5':>22s} {'mean|dlp|':>10s} {'max|dlp|':>9s}   {'vs G5, router bias off':>22s}")
    for k in ('g5_bf16', 'g5_fp16', 'g5_bf16_autocast', 'g5_fp16_autocast', 'g5_router_bias_off', 'g5_with_head_bias'):
        a, b = v['g5'][k]['g5'], v['g5'][k].get('g5_router_bias_off')
        print(f"{'G5 ' + k[3:]:34s} {pct(a):>22s} {a['mean_abs_dlp']:10.3e} {a['max_abs_dlp']:9.3f}   "
              f"{pct(b) if b else '':>22s}")
    for name, r in v['runs'].items():
        a, b = r['single']['g5'], r['single']['g5_router_bias_off']
        label = f"{r['engine']} {r['version']} {r['dtype']} {r['build']}"
        print(f"{label:34s} {pct(a):>22s} {a['mean_abs_dlp']:10.3e} {a['max_abs_dlp']:9.3f}   {pct(b):>22s}"
              f"   batched vs single max {r['single_vs_batched']['max_abs_dlp']:.3f}")
    for name, f in v['fp32'].items():
        print(f"{f['engine']} fp32: {'ran' if f['ran'] else 'did not run: ' + str(f['error'])}")
    print('bf16 autocast vs fp32 same top-1 by weight std:',
          ', '.join(f"{k}: {pct(s)}" for k, s in v['std_check'].items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--ref', type=Path, required=True)
    ap.add_argument('--runs', type=Path, required=True)
    ap.add_argument('--out', type=Path, default=Path(__file__).resolve().parent / 'results/spike_summary.json')
    ap.add_argument('--std-ref', action='append', default=[], metavar='STD=DIR',
                    help='a reference folder of a model drawn with another --std (bf16 noise check)')
    a = ap.parse_args()
    v = build(a.ref, a.runs, {s.split('=', 1)[0]: Path(s.split('=', 1)[1]) for s in a.std_ref})
    report(v)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(v, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'\nwrote {a.out}')


if __name__ == '__main__':
    main()
