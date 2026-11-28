"""G12 lead item 8 (with Team 6): speculative decoding on a laptop, llama.cpp b11669 llama-server, Metal.

For each target model and each mode, one llama-server serves the same prompts greedily (temperature 0, fixed n_predict)
and the script records, per prompt, the server's own timings: generated tokens per second (`predicted_per_second`),
tokens generated, draft tokens proposed and accepted. Greedy speculative decoding must give the target's own output,
so every mode's text is compared with the baseline's text for the same prompt.

Modes:
  base                     the target alone
  draft:<gguf>[:N]         a small draft model (-md, --spec-type draft-simple), N tokens per draft (default 8)
  ngram:<type>[:N]         a draft-free n-gram mode (ngram-simple, ngram-mod, ngram-map-k, ngram-cache), N max draft

    python spec_bench.py --bin <llama.cpp/bin> --target 3b=Llama-3.2-3B-Instruct-Q8_0.gguf \
        --modes base draft:Llama-3.2-1B-Instruct-Q8_0.gguf:8 ngram:ngram-mod --prompts prompts.jsonl --out spec.json

Prompts: a JSONL file of {"id", "messages"} rows (the chat template comes from the GGUF, --jinja). `make-prompts` builds
the set used here: Team 12's prompts_v1.jsonl chat and reason rows, plus code-edit rows whose code is from the train split
of the cleaned tokenizer sample v0 (never benchmark items; the code text stays on the machine, results hold numbers only).
"""
import argparse, hashlib, json, os, re, signal, socket, subprocess, sys, time, urllib.request
from pathlib import Path


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


def post(port, path, body, timeout=600):
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.loads(r.read())


def wait_ready(port, proc, timeout=300):
    t = time.time()
    while time.time() - t < timeout:
        if proc.poll() is not None: return False
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2) as r:
                if r.status == 200: return True
        except Exception: time.sleep(0.5)
    return False


def mode_args(mode, ngl_draft):
    """Server arguments for one mode string."""
    if mode == 'base': return []
    kind, _, rest = mode.partition(':')
    if kind == 'draft':
        path, _, n = rest.partition(':')
        # b11669 loads a -md model but drafts only when a draft type is requested (the default type is none)
        return ['-md', path, '-ngld', str(ngl_draft), '--spec-type', 'draft-simple', '--spec-draft-n-max', n or '8']
    if kind == 'ngram':
        typ, _, n = rest.partition(':')
        if n and typ != 'ngram-mod': raise ValueError(f'{mode!r}: a draft length is only wired for ngram-mod here')
        return ['--spec-type', typ] + (['--spec-ngram-mod-n-max', n] if n else [])
    raise ValueError(f'unknown mode {mode!r}')


def mode_label(mode):
    if mode.startswith('draft:'):
        _, path, *n = mode.split(':')
        return f'draft {Path(path).name.removesuffix(".gguf")} n{n[0] if n else 8}'
    return mode


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()


def run(a):
    prompts = [json.loads(l) for l in Path(a.prompts).read_text().splitlines() if l.strip()]
    if a.limit: prompts = prompts[:a.limit]
    res = {'machine': subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True).stdout.strip(),
           'llama_cpp': subprocess.run([str(Path(a.bin) / 'llama-server'), '--version'], capture_output=True, text=True).stderr.strip(),
           'n_predict': a.n_predict, 'prompts': a.prompts, 'n_prompts': len(prompts), 'argv': sys.argv, 'files': {}, 'runs': []}
    if a.out.exists() and a.resume: res['runs'] = json.loads(a.out.read_text())['runs']
    done = {(r['target'], r['mode'], r['id']) for r in res['runs']}
    for t in a.target:
        tname, _, tpath = t.partition('=')
        res['files'][tname] = {'gguf': Path(tpath).name, 'sha256': sha256(tpath)}
        for mode in a.modes:
            if mode.startswith('draft:'):
                dp = mode.split(':')[1]; res['files'][Path(dp).name] = {'gguf': Path(dp).name, 'sha256': sha256(dp)}
            todo = [p for p in prompts if (tname, mode_label(mode), p['id']) not in done]
            if not todo: continue
            port = free_port()
            cmd = [str(Path(a.bin) / 'llama-server'), '-m', tpath, '--port', str(port), '-ngl', '99', '-c', str(a.ctx),
                   '-np', '1', '--jinja', '--no-webui', '--temp', '0', '--seed', '0', '-fa', 'on', *mode_args(mode, 99)]
            log = open(a.logs / f'server-{tname}-{mode_label(mode).replace(" ", "_")}.log', 'w') if a.logs else subprocess.DEVNULL
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            try:
                if not wait_ready(port, proc): sys.exit(f'{tname} {mode}: server did not start (see log)')
                post(port, '/v1/chat/completions', {'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 8,
                                                    'temperature': 0})                                    # warm-up
                for p in todo:
                    body = {'messages': p['messages'], 'max_tokens': a.n_predict, 'temperature': 0, 'seed': 0,
                            'cache_prompt': False}
                    if a.ignore_eos: body['ignore_eos'] = True
                    t0 = time.time(); r = post(port, '/v1/chat/completions', body); wall = time.time() - t0
                    tm = r.get('timings', {})
                    text = r['choices'][0]['message'].get('content') or ''
                    row = {'target': tname, 'mode': mode_label(mode), 'id': p['id'], 'category': p.get('category'),
                           'predicted_n': tm.get('predicted_n'), 'predicted_per_second': tm.get('predicted_per_second'),
                           'predicted_ms': tm.get('predicted_ms'),
                           'prompt_n': tm.get('prompt_n'), 'prompt_per_second': tm.get('prompt_per_second'),
                           'draft_n': tm.get('draft_n'), 'draft_n_accepted': tm.get('draft_n_accepted'),
                           'wall_s': wall, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                           'finish': r['choices'][0].get('finish_reason')}
                    res['runs'].append(row)
                    acc = (row['draft_n_accepted'] / row['draft_n']) if row.get('draft_n') else None
                    print(f"{tname} {row['mode']:34s} {p['id']:12s} {row['predicted_n']} tok "
                          f"{row['predicted_per_second']:.1f} tok/s" + (f" accept {acc:.2f}" if acc is not None else ''), flush=True)
                    a.out.write_text(json.dumps(res, indent=1) + '\n')
            finally:
                proc.send_signal(signal.SIGINT)
                try: proc.wait(timeout=30)
                except subprocess.TimeoutExpired: proc.kill()
    summarize(res); a.out.write_text(json.dumps(res, indent=1) + '\n')


def summarize(res):
    """Per (target, mode): total generated tokens / total generation time, acceptance, and output agreement with base."""
    out = {}
    base_text = {(r['target'], r['id']): r['text_sha256'] for r in res['runs'] if r['mode'] == 'base'}
    for key in sorted({(r['target'], r['mode']) for r in res['runs']}):
        rs = [r for r in res['runs'] if (r['target'], r['mode']) == key and r.get('predicted_per_second')]
        if not rs: continue
        # generation time per prompt = tokens / the server's predicted_per_second (one definition for every row; the server
        # times the tokens after the first, so this is within a few per mille of predicted_ms)
        secs = lambda r: r['predicted_n'] / r['predicted_per_second']
        n = sum(r['predicted_n'] for r in rs); t = sum(secs(r) for r in rs)
        dn = sum(r['draft_n'] or 0 for r in rs); da = sum(r['draft_n_accepted'] or 0 for r in rs)
        same = [r['text_sha256'] == base_text.get((r['target'], r['id'])) for r in rs if (r['target'], r['id']) in base_text]
        cats = {}
        for c in sorted({r['category'] for r in rs}):
            cr = [r for r in rs if r['category'] == c]
            cats[c] = sum(r['predicted_n'] for r in cr) / sum(secs(r) for r in cr)
        out[f'{key[0]} | {key[1]}'] = {'prompts': len(rs), 'tokens': n, 'tok_per_s': n / t, 'tok_per_s_by_category': cats,
                                       'draft_n': dn, 'draft_accepted': da, 'acceptance': da / dn if dn else None,
                                       'same_text_as_base': f'{sum(same)}/{len(same)}' if same else None}
    for k, v in out.items():
        b = out.get(k.split(' | ')[0] + ' | base')
        v['speedup_vs_base'] = v['tok_per_s'] / b['tok_per_s'] if b else None
    res['summary'] = out
    for k, v in out.items():
        print(f"{k:50s} {v['tok_per_s']:7.1f} tok/s x{(v['speedup_vs_base'] or 0):.2f} accept {v['acceptance']} same {v['same_text_as_base']}")


MIB = 2 ** 20
BUF_RE = re.compile(r'(load_tensors|llama_kv_cache|sched_reserve): +(\S+) (model|KV|compute) buffer size = +([\d.]+) MiB')


def parse_buffers(text):
    """llama.cpp's own buffer report, in load order: the target's lines come first, then the draft's (if any)."""
    out = []
    for stage, dev, kind, mib in BUF_RE.findall(text):
        out.append({'kind': kind, 'device': dev, 'mib': float(mib)})
    return out


def run_memory(a):
    """Start one llama-server per target and mode (as `run` does, with -lv 4), read its buffer report, stop it."""
    res = {'llama_cpp': subprocess.run([str(Path(a.bin) / 'llama-server'), '--version'], capture_output=True, text=True).stderr.strip(),
           'ctx': a.ctx, 'argv': sys.argv, 'runs': []}
    for t in a.target:
        tname, _, tpath = t.partition('=')
        for mode in a.modes:
            port = free_port()
            cmd = [str(Path(a.bin) / 'llama-server'), '-m', tpath, '--port', str(port), '-ngl', '99', '-c', str(a.ctx),
                   '-np', '1', '--jinja', '--no-webui', '-fa', 'on', '-lv', '4', *mode_args(mode, 99)]
            logf = Path(a.out).with_suffix(f'.{tname}.{mode_label(mode).replace(" ", "_")}.log')
            with open(logf, 'w') as log:
                proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                try: ok = wait_ready(port, proc)
                finally:
                    proc.send_signal(signal.SIGINT)
                    try: proc.wait(timeout=30)
                    except subprocess.TimeoutExpired: proc.kill()
            bufs = parse_buffers(logf.read_text())
            total = sum(b['mib'] for b in bufs)
            files = [tpath] + ([mode.split(':')[1]] if mode.startswith('draft:') else [])
            res['runs'].append({'target': tname, 'mode': mode_label(mode), 'ready': ok, 'buffers': bufs, 'total_mib': total,
                                'gguf_bytes': {Path(f).name: Path(f).stat().st_size for f in files}})
            print(f"{tname} {mode_label(mode):34s} ready {ok} buffers {total:,.0f} MiB", flush=True)
            Path(a.out).write_text(json.dumps(res, indent=1) + '\n')


def report(a):
    """The README's tables: per target, generated tokens per second by mode and prompt category, speed-up over the
    target alone, draft acceptance and how many outputs match the target's own greedy text."""
    for f in a.files:
        res = json.loads(Path(f).read_text())
        if res['runs'] and 'buffers' in res['runs'][0]:          # a `memory` file
            print(f"\nllama.cpp's buffers at {res['ctx']:,}-token context, MiB (weights are memory-mapped from the GGUF; KV and "
                  'compute are allocated):\n')
            # weights: each GGUF once (its file size). llama.cpp maps a tied embedding twice (CPU_Mapped for the lookup and
            # inside the Metal range for the output), so summing its model buffers would count it twice.
            print('| target | mode | weights (GGUF sizes) | KV cache | compute | total | added by the draft |')
            print('|:--|:--|--:|--:|--:|--:|--:|')
            tot = lambda r: sum(r['gguf_bytes'].values()) / MIB + sum(b['mib'] for b in r['buffers'] if b['kind'] != 'model')
            base = {r['target']: tot(r) for r in res['runs'] if r['mode'] == 'base'}
            for r in res['runs']:
                kind = lambda k: sum(b['mib'] for b in r['buffers'] if b['kind'] == k)
                add = '' if r['mode'] == 'base' else f"{tot(r) - base[r['target']]:,.0f}"
                print(f"| {r['target']} | {r['mode']} | {sum(r['gguf_bytes'].values()) / MIB:,.0f} | {kind('KV'):,.0f} | "
                      f"{kind('compute'):,.0f} | {tot(r):,.0f} | {add} |")
            continue
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()): summarize(res)
        s = res['summary']
        cats = sorted({c for v in s.values() for c in v['tok_per_s_by_category']})
        for target in dict.fromkeys(k.split(' | ')[0] for k in s):
            base = s.get(f'{target} | base')
            print(f"\n{target} ({res['files'][target]['gguf']}), {res['n_prompts']} prompts, up to {res['n_predict']} tokens each:\n")
            print('| mode | all prompts | ' + ' | '.join(cats) + ' | acceptance | same text as alone |')
            print('|:--|--:|' + '--:|' * len(cats) + '--:|--:|')
            for k, v in s.items():
                if not k.startswith(target + ' | '): continue
                mode = k.split(' | ', 1)[1]
                cell = lambda x, b: f'{x:.1f}' + (f' ({x / b:.2f}×)' if b and mode != 'base' else '')
                acc = '' if v['acceptance'] is None else f"{v['acceptance']:.0%}"
                by_cat = ' | '.join(cell(v['tok_per_s_by_category'].get(c, float('nan')),
                                         base and base['tok_per_s_by_category'].get(c)) for c in cats)
                same = '' if mode == 'base' else (v['same_text_as_base'] or '')
                print(f"| {mode} | {cell(v['tok_per_s'], base and base['tok_per_s'])} | {by_cat} | {acc} | {same} |")


def make_prompts(a):
    import pyarrow.parquet as pq
    rows = [json.loads(l) for l in Path(a.base).read_text().splitlines() if l.strip()]
    out = [{'id': r['id'], 'category': r['category'], 'messages': r['messages']} for r in rows if r['category'] in ('chat', 'reason')]
    files = sorted((Path(a.data) / 'train' / 'code-python').glob('*.parquet'))
    n = 0
    for f in files:
        for t in pq.read_table(f, columns=['text']).column('text').to_pylist():
            if not (600 <= len(t) <= 2500) or 'def ' not in t: continue
            out.append({'id': f'code-edit-{n:02d}', 'category': 'code_edit', 'messages': [{'role': 'user', 'content':
                        'Add a short docstring to every function in this Python code. Return the whole code and '
                        'nothing else.\n\n```python\n' + t + '\n```'}]})
            n += 1
            if n == a.code: break
        if n == a.code: break
    if a.per_category:                                # the first N of each category, in file order
        out = [r for c in dict.fromkeys(r['category'] for r in out) for r in [x for x in out if x['category'] == c][:a.per_category]]
    Path(a.out).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in out))
    print(f'{len(out)} prompts -> {a.out}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('run')
    p.add_argument('--bin', required=True); p.add_argument('--target', nargs='+', required=True, metavar='NAME=FILE.gguf')
    p.add_argument('--modes', nargs='+', default=['base'])
    p.add_argument('--prompts', required=True); p.add_argument('--limit', type=int)
    p.add_argument('--n-predict', type=int, default=256); p.add_argument('--ctx', type=int, default=8192)
    p.add_argument('--ignore-eos', action='store_true')
    p.add_argument('--out', type=Path, required=True); p.add_argument('--logs', type=Path)
    p.add_argument('--resume', action='store_true')
    p = sub.add_parser('memory')
    p.add_argument('--bin', required=True); p.add_argument('--target', nargs='+', required=True, metavar='NAME=FILE.gguf')
    p.add_argument('--modes', nargs='+', default=['base']); p.add_argument('--ctx', type=int, default=8192)
    p.add_argument('--out', required=True)
    p = sub.add_parser('report'); p.add_argument('files', nargs='+')
    p = sub.add_parser('make-prompts')
    p.add_argument('--base', required=True, help="Team 12's serving/prompts_v1.jsonl")
    p.add_argument('--data', required=True, help='tokenizer_sample_v0_clean folder')
    p.add_argument('--code', type=int, default=20); p.add_argument('--out', required=True)
    p.add_argument('--per-category', type=int, help='keep the first N prompts of each category')
    a = ap.parse_args()
    if a.cmd == 'run':
        if a.logs: a.logs.mkdir(parents=True, exist_ok=True)
        run(a)
    elif a.cmd == 'report': report(a)
    elif a.cmd == 'memory': run_memory(a)
    else: make_prompts(a)


if __name__ == '__main__':
    main()
