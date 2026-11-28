"""G12 task 4 (and lead item 8's memory part) on a laptop: KV-cache memory, quality and speed per cache choice in
llama.cpp, the runtime under the GGUF / Ollama release.

A cache choice is `K[/V][+norot]`: the K and V cache types (`-ctk` / `-ctv`; one type means both), and `+norot` for
llama.cpp's Hadamard rotation of quantized K/V switched off (`LLAMA_ATTN_ROT_DISABLE=1`). From b11669 the rotation is on
by default whenever a cache type is quantized and the head dim is a multiple of 64 (src/llama-kv-cache.cpp).

    python kv_llamacpp.py memory  --bin <llama.cpp/bin> --model NAME=FILE.gguf ... --ctx 8192 32768 131072 --out mem.json
    python kv_llamacpp.py text    --data <tokenizer_sample_v0_clean> --out-dir <texts> [--packs ...]
    python kv_llamacpp.py quality --bin <bin> --model NAME=FILE.gguf --texts <texts> --kld-dir <scratch> --out q.json
    python kv_llamacpp.py speed   --bin <bin> --model NAME=FILE.gguf --depth 0 8192 --out speed.json
    python kv_llamacpp.py table   mem.json q.json speed.json           # quick tables of any results file
    python kv_llamacpp.py report                                         # the README's tables, from results/

memory: loads each model once per (choice, context) with llama-completion (prompt "Hello", 1 token) and records what
llama.cpp reports (KV buffer, K and V sizes, compute buffers, model buffers, flash attention, rotation) and macOS's peak
memory footprint (`/usr/bin/time -l`). The KV bytes are checked against n_layer * n_kv_head * head_dim * bytes/element.
quality: llama-perplexity --kl-divergence at n_ctx (default 8192) against the f16 cache of the same weights; llama.cpp
scores the second half of each chunk, so every scored token attends to n_ctx/2 or more cached tokens.
speed: llama-bench, prompt (pp) and generation (tg) tokens per second at each depth (tokens already in the cache).

Text: the train split of the cleaned tokenizer sample v0 (never benchmark items). It, the KL base files and the logs stay
on the machine; results/ holds numbers only.
"""
import argparse, hashlib, json, math, os, platform, re, subprocess, sys, time
from pathlib import Path

# bytes per element of each llama.cpp cache type: (block size, bytes per block), from ggml's type traits
TYPE_BYTES = {'f32': (1, 4), 'f16': (1, 2), 'bf16': (1, 2), 'q8_0': (32, 34), 'q5_1': (32, 24), 'q5_0': (32, 22),
              'q4_1': (32, 20), 'q4_0': (32, 18), 'iq4_nl': (32, 18)}
DEFAULT_CHOICES = ['f16', 'bf16', 'q8_0', 'q5_1', 'q5_0', 'q4_1', 'q4_0', 'iq4_nl', 'q8_0/q4_0', 'q8_0/q5_0',
                   'q8_0+norot', 'q4_0+norot', 'q8_0/q4_0+norot']
DEFAULT_PACKS = ['en-fineweb-edu', 'code-python', 'ind-hi-fw2', 'ind-bn-fw2', 'ind-ta-fw2', 'ind-kn-fw2']
MIB = 1024 * 1024


def parse_choice(c):
    """'q8_0/q4_0+norot' -> ('q8_0', 'q4_0', False); 'f16' -> ('f16', 'f16', True)."""
    rot = not c.endswith('+norot')
    kv = c.removesuffix('+norot')
    k, v = kv.split('/') if '/' in kv else (kv, kv)
    for t in (k, v):
        if t not in TYPE_BYTES: raise ValueError(f'unknown cache type {t!r} in {c!r}')
    return k, v, rot


def bits(t):
    blk, nb = TYPE_BYTES[t]
    return 8 * nb / blk


def kv_bytes_per_token(n_layer, n_kv_head, head_k, head_v, k, v):
    """Bytes the K and V caches take per token (all layers), as llama.cpp lays them out (one row per head per token)."""
    bk, nbk = TYPE_BYTES[k]; bv, nbv = TYPE_BYTES[v]
    if head_k % bk or head_v % bv: raise ValueError(f'head dim {head_k}/{head_v} is not a multiple of the block')
    return n_layer * n_kv_head * (head_k // bk * nbk + head_v // bv * nbv)


def env_for(rot):
    env = dict(os.environ)
    env.pop('LLAMA_ATTN_ROT_DISABLE', None)
    if not rot: env['LLAMA_ATTN_ROT_DISABLE'] = '1'
    return env


def cache_args(k, v, fa='on'):
    return ['-ctk', k, '-ctv', v, '-fa', fa]


# ---------------------------------------------------------------- log parsing
RE = {
    'kv': re.compile(r'llama_kv_cache: size = +([\d.]+) MiB \( *(\d+) cells, +(\d+) layers, +(\d+)/(\d+) seqs\), '
                     r'K \((\w+)\): +([\d.]+) MiB, V \((\w+)\): +([\d.]+) MiB'),
    'kv_buf': re.compile(r'llama_kv_cache: +(\S+) KV buffer size = +([\d.]+) MiB'),
    'compute': re.compile(r'sched_reserve: +(\S+) compute buffer size = +([\d.]+) MiB'),
    'model_buf': re.compile(r'load_tensors: +(\S+) model buffer size = +([\d.]+) MiB'),
    'fa': re.compile(r'llama_context: flash_attn += (\w+)'),
    'rot_k': re.compile(r'llama_kv_cache: n_rot_k = (\d+)'),
    'rot_v': re.compile(r'llama_kv_cache: n_rot_v = (\d+)'),
    'rot_off': re.compile(r'attention rotation force disabled'),
    'splits': re.compile(r'sched_reserve: graph: nodes = (\d+), splits = (\d+)'),
    'offload': re.compile(r'offloaded (\d+)/(\d+) layers to GPU'),
    'footprint': re.compile(r'^\s*(\d+)\s+peak memory footprint', re.M),
    'rss': re.compile(r'^\s*(\d+)\s+maximum resident set size', re.M),
    'hp': re.compile(r'print_info: (n_layer|n_head_kv|n_embd_head_k|n_embd_head_v|n_ctx_train|n_vocab|n_embd)\s+= (\d+)'),
}


def parse_memory_log(text):
    """Pull llama.cpp's own memory report and /usr/bin/time -l's peak footprint out of one run's stderr."""
    out = {}
    m = RE['kv'].search(text)
    if m:
        out.update(kv_mib=float(m[1]), cells=int(m[2]), layers=int(m[3]), k_type=m[6], k_mib=float(m[7]),
                   v_type=m[8], v_mib=float(m[9]))
    out['kv_buffers'] = {d: float(s) for d, s in RE['kv_buf'].findall(text)}
    comp = {}
    for d, s in RE['compute'].findall(text): comp[d] = float(s)     # the last reserve wins (it is the one kept)
    out['compute_buffers'] = comp
    mb = {}
    for d, s in RE['model_buf'].findall(text): mb[d] = mb.get(d, 0.0) + float(s)
    out['model_buffers'] = mb
    for key, conv in (('fa', str), ('rot_k', int), ('rot_v', int)):
        m = RE[key].search(text)
        out[key] = conv(m[1]) if m else None
    out['rot_disabled_logged'] = bool(RE['rot_off'].search(text))
    s = RE['splits'].findall(text)                   # the last reserve is the graph that runs
    out['graph_nodes'], out['graph_splits'] = (int(s[-1][0]), int(s[-1][1])) if s else (None, None)
    m = RE['offload'].search(text); out['offloaded'] = f'{m[1]}/{m[2]}' if m else None
    m = RE['footprint'].search(text); out['peak_footprint_bytes'] = int(m[1]) if m else None
    m = RE['rss'].search(text); out['max_rss_bytes'] = int(m[1]) if m else None
    out['hparams'] = {k: int(v) for k, v in RE['hp'].findall(text)}
    return out


KLD_RE = {
    'kld': re.compile(r'Mean +KLD: +([-\d.]+) ± +([-\d.]+)'),
    'kld_max': re.compile(r'Maximum KLD: +([-\d.]+)'),
    'kld_p99': re.compile(r'99\.0% +KLD: +([-\d.]+)'),
    'kld_median': re.compile(r'Median +KLD: +([-\d.]+)'),
    'ln_ratio': re.compile(r'Mean ln\(PPL\(Q\)/PPL\(base\)\) +: +([-\d.]+) ± +([-\d.]+)'),
    'ppl_q': re.compile(r'Mean PPL\(Q\) +: +([-\d.]+) ± +([-\d.]+)'),
    'ppl_base': re.compile(r'Mean PPL\(base\) +: +([-\d.]+) ± +([-\d.]+)'),
    'same_top': re.compile(r'Same top p: +([-\d.]+) ± +([-\d.]+) %'),
    'rms_dp': re.compile(r'RMS Δp +: +([-\d.]+) ± +([-\d.]+) %'),
    'chunks': re.compile(r'computing over (\d+) chunks, n_ctx=(\d+)'),
}


def parse_kld_log(text):
    out = {}
    for k, r in KLD_RE.items():
        m = r.search(text)
        if not m: continue
        if k == 'chunks': out['chunks'], out['n_ctx'] = int(m[1]), int(m[2])
        elif m.lastindex == 2: out[k], out[k + '_se'] = float(m[1]), float(m[2])
        else: out[k] = float(m[1])
    return out


# ---------------------------------------------------------------- helpers
def sha256(path, cache={}):
    path = Path(path)
    key = (str(path), path.stat().st_size, path.stat().st_mtime)
    if key not in cache:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
        cache[key] = h.hexdigest()
    return cache[key]


def machine():
    if platform.system() == 'Darwin':
        sc = lambda k: subprocess.run(['sysctl', '-n', k], capture_output=True, text=True).stdout.strip()
        return f'{sc("machdep.cpu.brand_string")} {int(sc("hw.memsize")) // 2**30} GB, macOS {platform.mac_ver()[0]}'
    return platform.platform()


def llama_version(bin_dir):
    r = subprocess.run([str(Path(bin_dir) / 'llama-completion'), '--version'], capture_output=True, text=True)
    return (r.stdout + r.stderr).strip().splitlines()[0] if (r.stdout + r.stderr).strip() else 'unknown'


def models_arg(items):
    out = []
    for it in items:
        name, _, path = it.partition('=')
        if not path: sys.exit(f'--model wants NAME=FILE.gguf, got {it!r}')
        p = Path(path).expanduser()
        if not p.exists(): sys.exit(f'{p}: not found')
        out.append((name, p))
    return out


def save(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + '\n')


def header(a):
    return {'machine': machine(), 'llama_cpp': llama_version(a.bin), 'date': time.strftime('%Y-%m-%d %H:%M %z'),
            'argv': [Path(sys.argv[0]).name] + sys.argv[1:]}


# ---------------------------------------------------------------- memory
def run_memory(a):
    b = Path(a.bin); res = {**header(a), 'runs': []}
    for name, path in models_arg(a.model):
        for ctx in a.ctx:
            for c in a.choices:
                k, v, rot = parse_choice(c)
                cmd = ['/usr/bin/time', '-l', str(b / 'llama-completion'), '-m', str(path), '-c', str(ctx),
                       *cache_args(k, v, a.fa), '-ngl', str(a.ngl), '-ub', str(a.ubatch), '-n', '1', '-p', 'Hello',
                       '-no-cnv', '--no-warmup', '--temp', '0', '-lv', '4']
                r = subprocess.run(cmd, capture_output=True, text=True, env=env_for(rot))
                if a.logs:
                    Path(a.logs).mkdir(parents=True, exist_ok=True)
                    (Path(a.logs) / f'mem-{name}-{ctx}-{c.replace("/", "_")}.log').write_text(r.stderr)
                p = parse_memory_log(r.stderr)
                row = {'model': name, 'gguf': path.name, 'gguf_sha256': sha256(path), 'ctx': ctx, 'choice': c,
                       'k': k, 'v': v, 'rotation_requested': rot, 'ubatch': a.ubatch, 'exit': r.returncode, **p}
                hp = p['hparams']
                if 'kv_mib' in p and {'n_layer', 'n_head_kv', 'n_embd_head_k', 'n_embd_head_v'} <= hp.keys():
                    bpt = kv_bytes_per_token(hp['n_layer'], hp['n_head_kv'], hp['n_embd_head_k'], hp['n_embd_head_v'], k, v)
                    row['formula_kv_mib'] = bpt * p['cells'] / MIB
                    row['kv_mib_per_1k'] = p['kv_mib'] / p['cells'] * 1024
                    row['kv_bytes_per_token'] = bpt
                print(f"{name} ctx {ctx} {c:16s} exit {r.returncode} KV {p.get('kv_mib')} MiB"
                      f" compute {sum(p['compute_buffers'].values()):.1f} MiB footprint "
                      f"{(p['peak_footprint_bytes'] or 0) / MIB:.1f} MiB rot {p['rot_k']}/{p['rot_v']} fa {p['fa']}",
                      flush=True)
                res['runs'].append(row)
                save(a.out, res)
    return res


# ---------------------------------------------------------------- text
def run_text(a):
    import pyarrow.parquet as pq
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for pack in a.packs:
        files = sorted((a.data / 'train' / pack).glob('*.parquet'))     # the train split only, never held-out text
        if not files: sys.exit(f'{a.data / "train" / pack}: no parquet files')
        parts, n = [], 0
        for f in files:
            for t in pq.read_table(f, columns=['text']).column('text').to_pylist():
                parts.append(t); n += len(t.encode())
                if n >= a.bytes: break
            if n >= a.bytes: break
        (a.out_dir / f'{pack}.txt').write_text('\n\n'.join(parts))
        print(f'{pack}: {len(parts)} documents, {n:,} bytes', flush=True)


# ---------------------------------------------------------------- quality
def run_quality(a):
    b = Path(a.bin); res = {**header(a), 'n_ctx': a.ctx, 'chunks_per_pack': a.chunks, 'runs': []}
    if Path(a.out).exists() and a.resume:                      # keep earlier rows; record every invocation
        old = json.loads(Path(a.out).read_text())
        res['invocations'] = old.get('invocations', [old['argv']]) + [res['argv']]
        res['runs'] = old['runs']
    done = {(r['model'], r['pack'], r['choice']) for r in res['runs']}
    a.kld_dir.mkdir(parents=True, exist_ok=True)
    for name, path in models_arg(a.model):
        for pack in a.packs:
            text = a.texts / f'{pack}.txt'
            if not text.exists(): sys.exit(f'{text}: run `text` first')
            base = a.kld_dir / f'{name}-{pack}-ctx{a.ctx}-f16.kld'
            common = ['-m', str(path), '-f', str(text), '-c', str(a.ctx), '--chunks', str(a.chunks), '-ngl', str(a.ngl),
                      '-b', str(a.ctx), '-ub', str(a.ubatch), '-lv', '4'] + (['-t', str(a.threads)] if a.threads else [])
            if not base.exists():
                r = subprocess.run([str(b / 'llama-perplexity'), *common, *cache_args('f16', 'f16', a.fa),
                                    '--kl-divergence-base', str(base)], capture_output=True, text=True, env=env_for(True))
                if r.returncode: sys.exit(f'base run failed for {name} {pack}:\n{r.stderr[-3000:]}')
            for c in a.choices:
                if (name, pack, c) in done: continue
                k, v, rot = parse_choice(c)
                r = subprocess.run([str(b / 'llama-perplexity'), *common, *cache_args(k, v, a.fa),
                                    '--kl-divergence-base', str(base), '--kl-divergence'],
                                   capture_output=True, text=True, env=env_for(rot))
                log = r.stdout + r.stderr
                if a.logs:
                    Path(a.logs).mkdir(parents=True, exist_ok=True)
                    (Path(a.logs) / f'kld-{name}-{pack}-{c.replace("/", "_")}.log').write_text(log)
                p = parse_kld_log(log); m = parse_memory_log(log)
                row = {'model': name, 'gguf': path.name, 'gguf_sha256': sha256(path), 'pack': pack, 'choice': c,
                       'k': k, 'v': v, 'rotation_requested': rot, 'rot_k': m['rot_k'], 'rot_v': m['rot_v'],
                       'fa': m['fa'], 'exit': r.returncode, **p}
                print(f"{name} {pack:15s} {c:16s} exit {r.returncode} KLD {p.get('kld')} ± {p.get('kld_se')}"
                      f" top {p.get('same_top')} rot {m['rot_k']}/{m['rot_v']}", flush=True)
                res['runs'].append(row); save(a.out, res)
    return res


def pooled(runs, model, choice):
    """Mean KLD and same-top over packs, weighting each pack by its scored tokens (equal here: same chunks)."""
    rs = [r for r in runs if r['model'] == model and r['choice'] == choice and 'kld' in r]
    if not rs: return None
    n = len(rs)
    kld = sum(r['kld'] for r in rs) / n
    se = (sum(r['kld_se'] ** 2 for r in rs)) ** 0.5 / n
    top = sum(r['same_top'] for r in rs) / n if all('same_top' in r for r in rs) else None
    ln = sum(r['ln_ratio'] for r in rs) / n if all('ln_ratio' in r for r in rs) else None
    return {'packs': n, 'kld': kld, 'kld_se': se, 'same_top': top, 'ln_ratio': ln,
            'worst_pack': max(rs, key=lambda r: r['kld'])['pack']}


# ---------------------------------------------------------------- speed
def run_speed(a):
    b = Path(a.bin); res = {**header(a), 'runs': []}
    for name, path in models_arg(a.model):
        for c in a.choices:
            k, v, rot = parse_choice(c)
            cmd = [str(b / 'llama-bench'), '-m', str(path), *cache_args(k, v, '1' if a.fa == 'on' else '0'),
                   '-ngl', str(a.ngl), '-p', str(a.prompt), '-n', str(a.gen), '-d', ','.join(map(str, a.depth)),
                   '-r', str(a.reps), '-o', 'json']
            r = subprocess.run(cmd, capture_output=True, text=True, env=env_for(rot))
            if r.returncode:
                print(f'{name} {c}: llama-bench exit {r.returncode}\n{r.stderr[-1500:]}', flush=True)
                res['runs'].append({'model': name, 'choice': c, 'exit': r.returncode}); save(a.out, res); continue
            for t in json.loads(r.stdout):
                row = {'model': name, 'gguf': path.name, 'gguf_sha256': sha256(path), 'choice': c, 'k': k, 'v': v,
                       'rotation_requested': rot, 'n_prompt': t['n_prompt'], 'n_gen': t['n_gen'],
                       'n_depth': t.get('n_depth', 0), 'avg_ts': t['avg_ts'], 'stdev_ts': t['stddev_ts'], 'samples_ts': t.get('samples_ts'),
                       'type_k': t.get('type_k'), 'type_v': t.get('type_v'), 'flash_attn': t.get('flash_attn'),
                       'build': t.get('build_commit'), 'gpu': t.get('gpu_info'), 'n_threads': t.get('n_threads')}
                print(f"{name} {c:16s} pp{t['n_prompt']} tg{t['n_gen']} d{row['n_depth']}: "
                      f"{t['avg_ts']:.1f} ± {t['stddev_ts']:.1f} tok/s", flush=True)
                res['runs'].append(row)
            save(a.out, res)
    return res


# ---------------------------------------------------------------- tables
def run_table(a):
    for f in a.files:
        d = json.loads(Path(f).read_text()); runs = d['runs']
        print(f'\n<!-- {Path(f).name}: {d["machine"]}; {d["llama_cpp"]} -->')
        if runs and 'kv_mib' in runs[0] or any('kv_mib' in r for r in runs):
            print('| model | ctx | choice | bits/elem K/V | KV MiB | MiB per 1k | formula MiB | compute MiB | rot K/V |')
            print('|:--|--:|:--|--:|--:|--:|--:|--:|:--|')
            for r in runs:
                if 'kv_mib' not in r: continue
                print(f"| {r['model']} | {r['ctx']:,} | {r['choice']} | {bits(r['k']):g}/{bits(r['v']):g} | "
                      f"{r['kv_mib']:.2f} | {r['kv_mib_per_1k']:.3f} | {r.get('formula_kv_mib', float('nan')):.2f} | "
                      f"{sum(r['compute_buffers'].values()):.1f} | {r['rot_k']}/{r['rot_v']} |")
        elif any('kld' in r for r in runs):
            models = sorted({r['model'] for r in runs}); choices = list(dict.fromkeys(r['choice'] for r in runs))
            print('| model | choice | mean KLD (s.e.) | same top-1 | ln PPL ratio | worst pack |')
            print('|:--|:--|--:|--:|--:|:--|')
            for m in models:
                for c in choices:
                    p = pooled(runs, m, c)
                    if p: print(f"| {m} | {c} | {p['kld']:.5f} ({p['kld_se']:.5f}) | {p['same_top']:.2f}% | "
                                f"{p['ln_ratio']:+.5f} | {p['worst_pack']} |")
        else:
            print('| model | choice | test | depth | tok/s |')
            print('|:--|:--|:--|--:|--:|')
            for r in runs:
                if 'avg_ts' not in r: continue
                test = f"pp{r['n_prompt']}" if r['n_prompt'] else f"tg{r['n_gen']}"
                print(f"| {r['model']} | {r['choice']} | {test} | {r['n_depth']:,} | {r['avg_ts']:.1f} ± {r['stdev_ts']:.1f} |")


def vllm_bits(key_bits, value_bits, head_dim):
    """vLLM 0.33.0 TurboQuant slot size in bits per element (../figures/make_figures.py, #848): keys ceil(d*b/8) bytes
    plus an fp16 norm, values the same plus an fp16 scale and zero point."""
    return (math.ceil(head_dim * key_bits / 8) + 2 + math.ceil(head_dim * value_bits / 8) + 4) * 8 / (2 * head_dim)


def vllm_mib_per_1k(n_layer, n_kv_head, head_dim, bits_compressed):
    """MiB per 1k tokens in vLLM 0.33.0: min(2, L // 2) layers at each end stay bf16 for every TurboQuant preset."""
    skip = 2 * min(2, n_layer // 2) if bits_compressed < 8 else 0
    per_tok_bits = 2 * n_kv_head * head_dim * (16 * skip + bits_compressed * (n_layer - skip))
    return per_tok_bits / 8 * 1024 / MIB


def run_report(a):
    """The README's tables, from the committed results (every number below comes from these files)."""
    R = Path(a.results)
    get = lambda n: json.loads((R / n).read_text()) if (R / n).exists() else None
    m2, m1 = get('memory_t2.json'), get('memory_llama1b.json')
    q, qc = get('quality_llama1b_ctx8192.json'), get('quality_llama1b_ctx8192_cpu_fa.json')
    sp = get('speed_kv.json')
    idx = lambda m: {(r['ctx'], r['choice']): r for r in m['runs']}
    i2, i1 = idx(m2), idx(m1)
    order = ['f16', 'bf16', 'q8_0', 'q5_1', 'q5_0', 'q4_1', 'q4_0', 'iq4_nl', 'q8_0/q4_0', 'q8_0/q5_0']
    ollama = {'f16': 'yes', 'q8_0': 'yes', 'q4_0': 'yes', 'q5_0': 'Llama-1B', 'iq4_nl': 'Llama-1B'}   # run in Ollama 0.40.18
    print('### Memory per 1k tokens at 8k context (measured)\n')
    print('| cache K/V | bits per element K/V | dry run 2 shape | Llama-3.2-1B | vs f16 | = formula | attention on Metal | tested in Ollama |')
    print('|:--|--:|--:|--:|--:|:--:|:--|:--:|')
    for c in order:
        r2, r1 = i2[(8192, c)], i1[(8192, c)]
        same = all(abs(r['kv_mib'] - r['formula_kv_mib']) < 1e-9 for r in (r2, r1))
        metal = ('GPU' if r2['graph_splits'] == 2 and r1['graph_splits'] == 2 else
                 f"CPU ({r2['graph_splits']} / {r1['graph_splits']} graph splits, not 2)")
        print(f"| {c} | {bits(r2['k']):g} / {bits(r2['v']):g} | {r2['kv_mib_per_1k']:.3f} MiB | {r1['kv_mib_per_1k']:.3f} MiB | "
              f"{r2['kv_mib_per_1k'] / i2[(8192, 'f16')]['kv_mib_per_1k']:.3f}× | {'yes' if same else 'NO'} | {metal} | "
              f"{ollama.get(c, '')} |")
    hp = m2['runs'][0]['hparams']
    L, H, D = hp['n_layer'], hp['n_head_kv'], hp['n_embd_head_k']
    print(f'\nvLLM 0.33.0 on the dry run 2 shape ({L} layers, {H} KV heads, head dim {D}), computed from its slot sizes as in '
          '#848, not run:\n')
    print('| `--kv-cache-dtype` | MiB per 1k tokens | vs bf16 |')
    print('|:--|--:|--:|')
    rows = [('auto (bf16)', 16), ('fp8', 8), ('turboquant_4bit_nc', vllm_bits(4, 4, D)),
            ('turboquant_k3v4_nc', vllm_bits(3, 4, D)), ('turboquant_3bit_nc', vllm_bits(3, 3, D))]
    b16 = vllm_mib_per_1k(L, H, D, 16)
    for name, b in rows:
        v = vllm_mib_per_1k(L, H, D, b)
        print(f'| {name} | {v:.3f} | {v / b16:.3f}× |')
    print('\n### Long context: what llama.cpp allocates (measured)\n')
    print('| model | context | KV f16 | KV q8_0 | KV q4_0 | compute buffers (f16 run) | peak footprint f16 / q8_0 / q4_0 |')
    print('|:--|--:|--:|--:|--:|--:|--:|')
    for name, ix in (('dry run 2 shape', i2), ('Llama-3.2-1B', i1)):
        for ctx in (8192, 32768, 131072):
            f, e, h = ix[(ctx, 'f16')], ix[(ctx, 'q8_0')], ix[(ctx, 'q4_0')]
            fp = ' / '.join(f"{r['peak_footprint_bytes'] / MIB:,.0f}" for r in (f, e, h))
            print(f"| {name} | {ctx // 1024}k | {f['kv_mib']:,.0f} MiB | {e['kv_mib']:,.0f} MiB | {h['kv_mib']:,.0f} MiB | "
                  f"{sum(f['compute_buffers'].values()):,.0f} MiB | {fp} MiB |")
    if q:
        print('\n### Quality at 8k context, Llama-3.2-1B (measured)\n')
        print('| cache K/V | rotation | packs | mean KL (s.e.) | KL range over packs | same top-1 | perplexity change |')
        print('|:--|:--|--:|--:|--:|--:|--:|')
        allruns = q['runs'] + (qc['runs'] if qc else [])
        for c in list(dict.fromkeys(r['choice'] for r in allruns)):
            rs = [r for r in allruns if r['choice'] == c and 'kld' in r]
            p = pooled(rs, rs[0]['model'], c)
            lo, hi = min(r['kld'] for r in rs), max(r['kld'] for r in rs)
            k, v, rot = parse_choice(c)
            rotation = 'off' if not rot else ('n/a' if k in ('f16', 'bf16') and v in ('f16', 'bf16') else 'on')
            print(f"| {c.removesuffix('+norot')} | {rotation} | {p['packs']} | {p['kld']:.5f} ({p['kld_se']:.5f}) | "
                  f"{lo:.5f} to {hi:.5f} | {p['same_top']:.2f}% | {100 * (math.exp(p['ln_ratio']) - 1):+.2f}% |")
        if qc:
            few = sorted({r['pack'] for r in qc['runs']})
            refs = []
            for ref in ('q8_0', 'q4_0'):
                rr = [r for r in q['runs'] if r['choice'] == ref and r['pack'] in few and 'kld' in r]
                if rr: refs.append(f"{ref} {sum(r['kld'] for r in rr) / len(rr):.5f}")
            print(f"\nThe rows with 2 packs ({', '.join(few)}) are the cache types whose attention runs on the CPU; on the same "
                  f"two packs the 6-pack rows give: {', '.join(refs)}.")
    bw = get('bandwidth_mps.json')
    if sp:
        print('\n### Speed (measured; mean ± s.d. of 5 runs)\n')
        models = list(dict.fromkeys(r['model'] for r in sp['runs']))
        for m in models:
            rs = {(r['choice'], 'pp' if r['n_prompt'] else 'tg', r['n_depth']): r for r in sp['runs'] if r['model'] == m and 'avg_ts' in r}
            # a dense model reads every weight on the GPU once per generated token, plus the cache up to that token
            dense = m.startswith('llama')
            print(f'\n{m}, tokens per second:\n')
            print('| cache K/V | prompt, empty cache | prompt at 8k | generation, empty cache | generation at 8k | generation at 8k vs f16 |'
                  + (' bytes read per token at 8k | effective read rate at 8k |' if dense else ''))
            print('|:--|--:|--:|--:|--:|--:|' + ('--:|--:|' if dense else ''))
            g16 = rs[('f16', 'tg', 8192)]['avg_ts']
            for c in list(dict.fromkeys(r['choice'] for r in sp['runs'])):
                if (c, 'tg', 8192) not in rs: continue
                f = lambda t, d: f"{rs[(c, t, d)]['avg_ts']:,.0f} ± {rs[(c, t, d)]['stdev_ts']:,.0f}"
                extra = ''
                if dense and (8192, c) in i1:
                    r, t = i1[(8192, c)], rs[(c, 'tg', 8192)]
                    per_tok = r['model_buffers'].get('MTL0_Mapped', 0) * MIB + r['kv_bytes_per_token'] * (t['n_depth'] + t['n_gen'] / 2)
                    extra = f' {per_tok / 1e9:.3f} GB | {t["avg_ts"] * per_tok / 1e9:.1f} GB/s |'
                print(f"| {c} | {f('pp', 0)} | {f('pp', 8192)} | {f('tg', 0)} | {f('tg', 8192)} | "
                      f"{rs[(c, 'tg', 8192)]['avg_ts'] / g16:.2f}× |" + extra)
            if dense:
                print('\nBytes read per token = weights on the GPU (`MTL0_Mapped`) + cache bytes per token × (8,192 + 64), the '
                      'mean cache length over the 128 generated tokens; effective read rate = generated tokens per second × '
                      'that.' + (f" For scale, `bw_mps.py` measured {min(bw['read_GBps']):.0f} to {max(bw['read_GBps']):.0f} GB/s "
                                 'of read bandwidth in its last run.' if bw else ''))
    ub = sorted(R.glob('memory_t2_ub*.json'), key=lambda p: int(p.stem.split('ub')[1]))
    if ub:
        print('\n### Compute buffer against micro-batch size, dry run 2 shape at 8k (measured)\n')
        print('| `-ub` | compute buffers | KV f16 | peak footprint |')
        print('|--:|--:|--:|--:|')
        for p in ub:
            r = next(r for r in json.loads(p.read_text())['runs'] if r['choice'] == 'f16')
            print(f"| {r['ubatch']} | {sum(r['compute_buffers'].values()):.1f} MiB | {r['kv_mib']:.0f} MiB | "
                  f"{r['peak_footprint_bytes'] / MIB:.0f} MiB |")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    def common(p):
        p.add_argument('--bin', required=True, help='llama.cpp bin folder (b11669)')
        p.add_argument('--model', nargs='+', required=True, metavar='NAME=FILE.gguf')
        p.add_argument('--choices', nargs='+', default=DEFAULT_CHOICES)
        p.add_argument('--ngl', type=int, default=99)
        p.add_argument('--fa', default='on', choices=['on', 'off'])
        p.add_argument('--out', required=True)
    p = sub.add_parser('memory'); common(p)
    p.add_argument('--ctx', type=int, nargs='+', default=[8192])
    p.add_argument('--ubatch', type=int, default=512)
    p.add_argument('--logs')
    p = sub.add_parser('text')
    p.add_argument('--data', type=Path, required=True, help='tokenizer_sample_v0_clean folder (parquet packs)')
    p.add_argument('--packs', nargs='+', default=DEFAULT_PACKS)
    p.add_argument('--bytes', type=int, default=600_000, help='bytes of text per pack')
    p.add_argument('--out-dir', type=Path, required=True)
    p = sub.add_parser('quality'); common(p)
    p.add_argument('--texts', type=Path, required=True)
    p.add_argument('--packs', nargs='+', default=DEFAULT_PACKS)
    p.add_argument('--ctx', type=int, default=8192)
    p.add_argument('--chunks', type=int, default=2)
    p.add_argument('--ubatch', type=int, default=512)
    p.add_argument('--kld-dir', type=Path, required=True)
    p.add_argument('--logs')
    p.add_argument('--resume', action='store_true')
    p.add_argument('--threads', type=int, help='CPU threads (only matters for cache types whose attention runs on the CPU)')
    p = sub.add_parser('speed'); common(p)
    p.add_argument('--depth', type=int, nargs='+', default=[0, 8192])
    p.add_argument('--prompt', type=int, default=512)
    p.add_argument('--gen', type=int, default=128)
    p.add_argument('--reps', type=int, default=3)
    p = sub.add_parser('table'); p.add_argument('files', nargs='+')
    p = sub.add_parser('report'); p.add_argument('--results', default=str(Path(__file__).resolve().parent / 'results'))
    a = ap.parse_args()
    {'memory': run_memory, 'text': run_text, 'quality': run_quality, 'speed': run_speed, 'table': run_table,
     'report': run_report}[a.cmd](a)


if __name__ == '__main__':
    main()
