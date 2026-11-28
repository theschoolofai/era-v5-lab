"""G12 task 1, second question: which parts stay at higher precision (router, output layer, embeddings, attention) and why.

One bf16 GGUF is quantized into variants that change the precision of one part (or, for a few, of several; see the
list below), then each variant is scored with
llama-perplexity --kl-divergence against the bf16 GGUF on the same text (llama.cpp b11669, Metal). llama-quantize never
quantizes the router (`ffn_gate_inp`; src/llama-quant.cpp, tensor_allows_quantization) and convert_hf_to_gguf.py writes
it as F32, so the `router` step makes the router variants another way: it clones a GGUF and overwrites each F32 `ffn_gate_inp` tensor in place with its values rounded to Q8_0 or Q4_0
blocks (router_emul.py's rounding, bit-exact against gguf-py) and still stored as F32, so llama.cpp computes exactly the
router a quantized one would give, and `kl` scores it like every other variant. router_emul.py adds the expert-choice
counts in PyTorch.

    python parts_llamacpp.py quantize --bin <llama.cpp/bin> --bf16 M-bf16.gguf --work <dir> [--variants ...]
    python parts_llamacpp.py router   --work <dir> --from bf16=M-bf16.gguf g12=<dir>/M-g12.gguf
    python parts_llamacpp.py kl       --bin <bin> --bf16 M-bf16.gguf --work <dir> --texts <texts> --out kl.json
    python parts_llamacpp.py table    kl.json

Variants (base mix Q4_K_M unless the name says otherwise; `g12` = Team 12's rule, output Q8_0, router F32):
  llama-default   llama.cpp's own Q4_K_M mix (output Q6_K)
  g12             --output-tensor-type q8_0                       (what quantize_eval.py ships)
  out-q4_K        output at Q4_K
  out-bf16        output left at bf16
  embd-q8_0       g12 + token embedding at Q8_0
  attn-q8_0       g12 + every attention matrix at Q8_0
  experts-q4      Q8_0 everywhere except the routed experts (ffn_*_exps) at Q4_K
  pure-q4_K       --pure: every quantizable matrix at Q4_K, output and embedding included
  q8_0            Q8_0 with output Q8_0 (reference for the 8-bit end)

Text: the train split of the cleaned tokenizer sample v0 (never benchmark items), from kv_llamacpp.py's `text` step.
"""
import argparse, hashlib, json, re, subprocess, sys, time
from collections import defaultdict
from pathlib import Path

VARIANTS = {
    'llama-default': ('Q4_K_M', []),
    'g12': ('Q4_K_M', ['--output-tensor-type', 'q8_0']),
    'out-q4_K': ('Q4_K_M', ['--output-tensor-type', 'q4_K']),
    'out-bf16': ('Q4_K_M', ['--output-tensor-type', 'bf16']),
    'embd-q8_0': ('Q4_K_M', ['--output-tensor-type', 'q8_0', '--token-embedding-type', 'q8_0']),
    'attn-q8_0': ('Q4_K_M', ['--output-tensor-type', 'q8_0', '--tensor-type', r'attn_(q|k|v|output)\.weight=q8_0']),
    'experts-q4': ('Q8_0', ['--output-tensor-type', 'q8_0', '--tensor-type', r'ffn_(gate|up|down)_exps\.weight=q4_K']),
    'pure-q4_K': ('Q4_K', ['--pure']),
    'q8_0': ('Q8_0', ['--output-tensor-type', 'q8_0']),
}
DEFAULT_PACKS = ['en-fineweb-edu', 'code-python', 'ind-hi-fw2', 'ind-bn-fw2', 'ind-ta-fw2', 'ind-kn-fw2']


def part_of(name):
    """Which model part a GGUF tensor belongs to."""
    if name.startswith('token_embd'): return 'embedding'
    if name.startswith('output.'): return 'output'
    if 'ffn_gate_inp' in name: return 'router'
    if '_exps' in name: return 'experts'
    if '_shexp' in name: return 'shared expert'
    if re.search(r'attn_(q|k|v|output|qkv)\.', name): return 'attention'
    if 'ffn_' in name and 'norm' not in name: return 'dense ffn'
    return 'norms and other'


def gguf_parts(path):
    """Bytes and tensor types per part, read from the GGUF header with gguf-py."""
    import gguf
    r = gguf.GGUFReader(str(path))
    by, ty = defaultdict(int), defaultdict(set)
    for t in r.tensors:
        p = part_of(t.name); by[p] += int(t.n_bytes); ty[p].add(t.tensor_type.name)
    return {p: {'bytes': by[p], 'types': sorted(ty[p])} for p in by}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()


KLD_RE = {
    'kld': re.compile(r'Mean +KLD: +([-\d.]+) ± +([-\d.]+)'),
    'kld_p99': re.compile(r'99\.0% +KLD: +([-\d.]+)'),
    'kld_max': re.compile(r'Maximum KLD: +([-\d.]+)'),
    'ln_ratio': re.compile(r'Mean ln\(PPL\(Q\)/PPL\(base\)\) +: +([-\d.]+) ± +([-\d.]+)'),
    'same_top': re.compile(r'Same top p: +([-\d.]+) ± +([-\d.]+) %'),
    'ppl_q': re.compile(r'Mean PPL\(Q\) +: +([-\d.]+) ± +([-\d.]+)'),
    'ppl_base': re.compile(r'Mean PPL\(base\) +: +([-\d.]+) ± +([-\d.]+)'),
}


def parse_kld_log(text):
    out = {}
    for k, r in KLD_RE.items():
        m = r.search(text)
        if m:
            out[k] = float(m[1])
            if m.lastindex == 2: out[k + '_se'] = float(m[2])
    return out


def run_quantize(a):
    a.work.mkdir(parents=True, exist_ok=True)
    stem = a.bf16.name.removesuffix('-bf16.gguf').removesuffix('.gguf')
    rows = []
    for v in a.variants:
        ftype, extra = VARIANTS[v]
        out = a.work / f'{stem}-{v}.gguf'
        if not out.exists():
            cmd = [str(Path(a.bin) / 'llama-quantize'), *extra, str(a.bf16), str(out), ftype]
            t = time.time()
            r = subprocess.run(cmd, capture_output=True, text=True)
            (a.work / f'quantize-{v}.log').write_text(' '.join(cmd) + '\n' + r.stdout + r.stderr)
            if r.returncode: sys.exit(f'{v}: llama-quantize exit {r.returncode}\n{r.stderr[-2000:]}')
            print(f'{v}: {out.stat().st_size / 2**20:.1f} MiB in {time.time() - t:.0f} s', flush=True)
        rows.append({'variant': v, 'ftype': ftype, 'args': extra, 'file': out.name, 'bytes': out.stat().st_size,
                     'sha256': sha256(out), 'parts': gguf_parts(out)})
    (a.work / 'variants.json').write_text(json.dumps({'bf16': a.bf16.name, 'bf16_sha256': sha256(a.bf16),
                                                      'bf16_parts': gguf_parts(a.bf16), 'variants': rows}, indent=1))


def run_router(a):
    """Clone each --from GGUF and write its routers rounded to Q8_0 / Q4_0 (values kept as F32), as new variants."""
    import gguf, numpy as np, shutil, torch
    sys.path.insert(0, str(Path(__file__).resolve().parent))      # router_emul.py sits next to this file
    from router_emul import FORMATS
    meta_path = a.work / 'variants.json'
    meta = json.loads(meta_path.read_text())
    have = {v['variant'] for v in meta['variants']}
    for item in a.from_:
        tag, _, src = item.partition('=')
        src = Path(src)
        for fmt in a.formats:
            name = f'{tag}+router-{fmt}' if tag != 'bf16' else f'router-{fmt}'
            out = a.work / f'{src.stem.removesuffix("-bf16")}-{name}.gguf'
            if name in have: continue
            subprocess.run(['cp', '-c', str(src), str(out)], check=True)          # APFS clone, then edit in place
            r = gguf.GGUFReader(str(out), 'r+')
            n = 0
            for t in r.tensors:
                if not t.name.endswith('.ffn_gate_inp.weight'): continue
                if t.tensor_type != gguf.GGMLQuantizationType.F32: sys.exit(f'{t.name}: {t.tensor_type.name}, expected F32')
                w = torch.from_numpy(np.array(t.data, dtype=np.float32))
                t.data[...] = FORMATS[fmt](w).numpy().reshape(t.data.shape)
                n += 1
            r.data.flush(); del r
            print(f'{name}: {n} routers rounded to {fmt} in {out.name}', flush=True)
            meta['variants'].append({'variant': name, 'ftype': f'{tag} with router values rounded to {fmt} (stored F32)',
                                     'args': [], 'file': out.name, 'bytes': out.stat().st_size, 'sha256': sha256(out),
                                     'parts': gguf_parts(out), 'routers_rounded': n, 'router_format': fmt, 'from': tag})
            meta_path.write_text(json.dumps(meta, indent=1))


def run_kl(a):
    b = Path(a.bin)
    meta = json.loads((a.work / 'variants.json').read_text())
    res = {'machine': subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True).stdout.strip(),
           'llama_cpp': subprocess.run([str(b / 'llama-perplexity'), '--version'], capture_output=True, text=True).stderr.strip().splitlines()[0],
           'n_ctx': a.ctx, 'chunks_per_pack': a.chunks, 'argv': sys.argv, **meta, 'runs': []}
    if a.out.exists() and a.resume: res['runs'] = json.loads(a.out.read_text())['runs']
    done = {(r['variant'], r['pack']) for r in res['runs']}
    kdir = a.work / 'kld'; kdir.mkdir(exist_ok=True)
    for pack in a.packs:
        text = a.texts / f'{pack}.txt'
        common = ['-f', str(text), '-c', str(a.ctx), '--chunks', str(a.chunks), '-ngl', '99', '-fa', 'on', '-b', str(a.ctx)]
        base = kdir / f'{pack}-ctx{a.ctx}.kld'
        if not base.exists():
            r = subprocess.run([str(b / 'llama-perplexity'), '-m', str(a.bf16), *common, '--kl-divergence-base', str(base)],
                               capture_output=True, text=True)
            if r.returncode: sys.exit(f'base {pack}: exit {r.returncode}\n{r.stderr[-2000:]}')
        for row in meta['variants']:
            if (row['variant'], pack) in done: continue
            r = subprocess.run([str(b / 'llama-perplexity'), '-m', str(a.work / row['file']), *common,
                                '--kl-divergence-base', str(base), '--kl-divergence'], capture_output=True, text=True)
            log = r.stdout + r.stderr
            (kdir / f'{row["variant"]}-{pack}.log').write_text(log)
            p = parse_kld_log(log)
            print(f"{row['variant']:14s} {pack:15s} KLD {p.get('kld')} top {p.get('same_top')}", flush=True)
            res['runs'].append({'variant': row['variant'], 'pack': pack, 'exit': r.returncode, **p})
            a.out.write_text(json.dumps(res, indent=1) + '\n')


def run_table(a):
    d = json.loads(Path(a.file).read_text())
    sizes = {v['variant']: v for v in d['variants']}
    print(f"<!-- {d['llama_cpp']}; n_ctx {d['n_ctx']}; {d['chunks_per_pack']} chunks per pack -->")
    print('| variant | size MiB | output | embedding | attention | experts | mean KLD (s.e.) | same top-1 | worst pack |')
    print('|:--|--:|:--|:--|:--|:--|--:|--:|:--|')
    for v, meta in sizes.items():
        rs = [r for r in d['runs'] if r['variant'] == v and 'kld' in r]
        if not rs: continue
        n = len(rs); kld = sum(r['kld'] for r in rs) / n; se = sum(r['kld_se'] ** 2 for r in rs) ** 0.5 / n
        top = sum(r['same_top'] for r in rs) / n
        worst = max(rs, key=lambda r: r['kld'])['pack']
        t = lambda p: '/'.join(meta['parts'].get(p, {}).get('types', ['-']))
        print(f"| {v} | {meta['bytes'] / 2**20:.1f} | {t('output')} | {t('embedding')} | {t('attention')} | "
              f"{t('experts')} | {kld:.5f} ({se:.5f}) | {top:.2f}% | {worst} |")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('quantize')
    p.add_argument('--bin', required=True); p.add_argument('--bf16', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--variants', nargs='+', default=list(VARIANTS), choices=list(VARIANTS))
    p = sub.add_parser('kl')
    p.add_argument('--bin', required=True); p.add_argument('--bf16', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True); p.add_argument('--texts', type=Path, required=True)
    p.add_argument('--packs', nargs='+', default=DEFAULT_PACKS)
    p.add_argument('--ctx', type=int, default=4096); p.add_argument('--chunks', type=int, default=4)
    p.add_argument('--out', type=Path, required=True); p.add_argument('--resume', action='store_true')
    p = sub.add_parser('router')
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--from', dest='from_', nargs='+', required=True, metavar='TAG=FILE.gguf')
    p.add_argument('--formats', nargs='+', default=['q8_0', 'q4_0'])
    p = sub.add_parser('table'); p.add_argument('file')
    a = ap.parse_args()
    {'quantize': run_quantize, 'router': run_router, 'kl': run_kl, 'table': run_table}[a.cmd](a)


if __name__ == '__main__':
    main()
