#!/usr/bin/env python3
"""The README's figures, light and dark:  python figures/make_figures.py  (from teams/12-quantization/quant_error)

hero       what the tool gives, its tests, and the rehearsal's cost
outputs    the six output files: what each answers, its rows, its measure columns, its size in the rehearsal
positions  which positions the twin forward and llama.cpp score in one slice, at the default settings

Every number is read from this folder, never typed in: quant_error.py (output files, column lists, constants and the
command's defaults, parsed with ast), weights.py (the supported architectures), the test_*.py files (test counts)
and REHEARSAL.md (the rehearsal's time, memory and sizes). All of them go to values.json. The look, fonts and motion
come from svgkit.py. --static writes the finished state only (for previews).
"""
from __future__ import annotations

import argparse, ast, json, re
from pathlib import Path

import svgkit as kit
from svgkit import Svg, header, tile

HERE = Path(__file__).resolve().parent
QE = HERE.parent
CONSTANTS = ('OUTPUT_FILES', 'KL_CTX', 'X_ROWS', 'MAX_OUT_BYTES', 'TENSOR_FIELDS', 'LAYER_FIELDS', 'LINEAR_FIELDS',
             'TOKEN_FIELDS', 'KL_FIELDS')
KEYS = {'format', 'slice', 'layer', 'tensor', 'kind', 'expert', 'ggml_type', 'bits_per_weight', 'numel', 'n_tokens',
        'chunks', 'tokens_scored', 'time_s'}   # columns that say which row it is, not what was measured


def _eval(node: ast.AST, where: str):
    """A module-level constant: a literal, or arithmetic on literals (5 * 1024 * 1024)."""
    return eval(compile(ast.Expression(node), where, 'eval'), {'__builtins__': {}})


def from_code() -> dict:
    tree = ast.parse((QE / 'quant_error.py').read_text(encoding='utf-8'))
    c = {n.targets[0].id: _eval(n.value, 'quant_error.py') for n in tree.body
         if isinstance(n, ast.Assign) and len(n.targets) == 1 and getattr(n.targets[0], 'id', None) in CONSTANTS}
    missing = set(CONSTANTS) - set(c)
    assert not missing, f'quant_error.py: no {sorted(missing)}'
    defaults, choices = {}, {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, 'attr', '') == 'add_argument' and n.args \
                and isinstance(n.args[0], ast.Constant):
            for kw in n.keywords:
                if kw.arg == 'default':
                    defaults[n.args[0].value] = ast.literal_eval(kw.value)
                if kw.arg == 'choices':
                    choices[n.args[0].value] = list(ast.literal_eval(kw.value))
    w = ast.parse((QE / 'weights.py').read_text(encoding='utf-8'))
    archs = next(_eval(n.value, 'weights.py') for n in w.body
                 if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', None) == 'ARCHS')
    tests = {}
    for f in sorted(QE.glob('test_*.py')):
        t = ast.parse(f.read_text(encoding='utf-8'))
        tests[f.name] = sum(isinstance(n, ast.FunctionDef) and n.name.startswith('test') for n in ast.walk(t))
    return dict(constants=c, defaults=defaults, choices=choices, archs=sorted(archs.values()), tests=tests)


def from_rehearsal() -> dict:
    text = (QE / 'REHEARSAL.md').read_text(encoding='utf-8')

    def grab(pattern: str):
        m = re.search(pattern, text)
        assert m, f'REHEARSAL.md: no match for {pattern!r}'
        return m.groups()

    params, n_layers, formats, slices = grab(r'\| Model \| ([0-9]+) M parameters \(([0-9]+) layers.*?\), ([0-9]+) formats, '
                                             r'([0-9]+) slices')
    wall, t_tensors, t_twin, t_kl = grab(r'\| Wall time \| ([0-9.]+) s .*?tensors ([0-9.]+) s, twin forward ([0-9.]+) s'
                                         r'.*?llama\.cpp KL ([0-9.]+) s')
    rss, footprint = grab(r'\| Peak memory \| ([0-9.]+) GB maximum resident set size; ([0-9.]+) GB peak memory footprint')
    total_kb, parts = grab(r'\| Output size \| ([0-9]+) KB \(`out/`: ([^)]*)\)')
    sizes = {name: int(kb) for name, kb in re.findall(r'([a-z]+\.(?:csv|json)) ([0-9]+) KB', parts)}
    chunks, scored = grab(r'every one with ([0-9]+) chunks and ([0-9]+) scored tokens')
    return dict(params_m=int(params), layers=int(n_layers), formats=int(formats), slices=int(slices),
                wall_s=float(wall), tensors_s=float(t_tensors), twin_s=float(t_twin), kl_s=float(t_kl),
                max_rss_gb=float(rss), footprint_gb=float(footprint), out_kb=int(total_kb), sizes_kb=sizes,
                kl_chunks=int(chunks), kl_scored=int(scored))


def load() -> dict:
    code, reh = from_code(), from_rehearsal()
    c, d = code['constants'], code['defaults']
    scored_per_chunk = c['KL_CTX'] // 2 - 1          # llama-perplexity scores positions ctx/2 .. ctx-2 of each chunk
    assert reh['kl_chunks'] == d['--kl-chunks'] and reh['kl_scored'] == d['--kl-chunks'] * scored_per_chunk, \
        'REHEARSAL.md: chunk counts do not match the defaults of quant_error.py'
    assert set(reh['sizes_kb']) == set(c['OUTPUT_FILES']), 'REHEARSAL.md: sizes do not name the six output files'
    return dict(code=code, rehearsal=reh, scored_per_chunk=scored_per_chunk)


# ------------------------------------------------------------------------------------------------------------ hero
def hero(theme, static, d, values):
    s = Svg(theme, 300, static); p = s.p
    c, r, tests = d['code']['constants'], d['rehearsal'], d['code']['tests']
    s.text(36, 46, 'TEAM 12 · QUANTIZATION · QUANT_ERROR', 'cap')
    s.text(36, 78, 'Where does quantization error come from?', 't lg')
    s.text(36, 102, 'One offline command: quantized GGUFs against their bf16 reference on G5’s held-out text, per '
                    'tensor, layer, router and slice', 'st')
    s.add(f'<rect x="36" y="116" width="56" height="2" rx="1" fill="{p["accent"]}"{s.anim("g", 0)}/>')
    n_files, total = len(c['OUTPUT_FILES']), sum(tests.values())
    tiles = [
        ('OUTPUT', f'{n_files} files', 'numbers only: no text, no token ids',
         f'exit 1 above {c["MAX_OUT_BYTES"] / 2 ** 20:g} MB', p['navy']),
        ('TESTS', f'{total}', f'in {len(tests)} test files, one end to end',
         f'test_cli.py: {tests["test_cli.py"]} on llama.cpp', p['green']),
        ('REHEARSAL · DRY-RUN-2 SHAPE', f'{r["wall_s"]:g} s',
         f'random {r["params_m"]} M, {r["formats"]} formats, {r["slices"]} slices',
         f'{r["out_kb"]} KB out · {r["max_rss_gb"]:g} GB max RSS', p['brass']),
    ]
    values['hero'] = [dict(caption=t[0], value=t[1], line1=t[2], line2=t[3]) for t in tiles]
    for i, (cap, big, l1, l2, col) in enumerate(tiles):
        tile(s, 36 + i * 274, 140, 260, 124, col, cap, big, l1, l2, .2 + .15 * i)
    return s.render('quant_error at a glance',
                    f'{n_files} output files with numbers only; {total} tests in {len(tests)} files; the rehearsal at '
                    f'the dry-run-2 shape ran in {r["wall_s"]:g} s and wrote {r["out_kb"]} KB.')


# --------------------------------------------------------------------------------------------------------- outputs
CARDS = [   # file, the step that writes it, the question it answers, one row per
    ('tensors.csv', 'tensors', 'Which tensors lose the most?', 'tensor and format'),
    ('layers.csv', 'twin forward', 'Where does the error build up?', 'format, slice, layer'),
    ('linears.csv', 'twin forward', 'Which modules, on real inputs?', 'format and nn.Linear'),
    ('tokens.csv', 'twin forward', 'How far does the output drift?', 'format, slice'),
    ('kl.csv', 'llama.cpp KL', 'What do llama.cpp users get?', 'slice, format'),
    ('summary.json', 'last', 'Can the run be reproduced?', 'run'),
]
FIELDS = {'tensors.csv': 'TENSOR_FIELDS', 'layers.csv': 'LAYER_FIELDS', 'linears.csv': 'LINEAR_FIELDS',
          'tokens.csv': 'TOKEN_FIELDS', 'kl.csv': 'KL_FIELDS'}
SUMMARY = ['versions', 'sha256', 'settings', 'step times']


def _wrap(words: list[str], width: int) -> list[str]:
    lines, cur = [], ''
    for w in words:
        nxt = f'{cur}, {w}' if cur else w
        if len(nxt) > width and cur:
            lines.append(cur + ',')
            cur = w
        else:
            cur = nxt
    return lines + [cur] if cur else lines


def outputs(theme, static, d, values):
    s = Svg(theme, 494, static); p = s.p
    c, r = d['code']['constants'], d['rehearsal']
    assert [f for f, *_ in CARDS] == list(c['OUTPUT_FILES']), 'CARDS must follow quant_error.OUTPUT_FILES'
    step_col = {'tensors': p['green'], 'twin forward': p['navy'], 'llama.cpp KL': p['brass'], 'last': p['muted']}
    header(s, 'QUANT_ERROR · THE SIX OUTPUT FILES · ALL IN --out',
           'Six files, one question each',
           f'The step that writes each file, its rows, the columns that hold the measure, and its size in the '
           f'rehearsal ({r["out_kb"]} KB in all)')
    cw, ch, gx, gy, x0, y0 = 258, 156, 17, 16, 36, 122
    top = max(r['sizes_kb'].values())
    shown = []
    for i, (name, step, question, rows) in enumerate(CARDS):
        x, y = x0 + (i % 3) * (cw + gx), y0 + (i // 3) * (ch + gy)
        col, delay = step_col[step], .2 + .1 * i
        measures = [f for f in c[FIELDS[name]] if f not in KEYS] if name in FIELDS else SUMMARY
        s.add(f'<g{s.anim("f", delay)}><rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="12" fill="{p["card"]}" '
              f'stroke="{p["line"]}"/><circle cx="{x + 22}" cy="{y + 24}" r="4" fill="{col}"/></g>')
        w = f'f@{delay + .1:.2f}'
        s.text(x + 32, y + 28, step.upper(), 'cap', wrap=w)
        s.text(x + 18, y + 54, name, 'file', wrap=w)
        s.text(x + 18, y + 74, question, 'lab2', wrap=w)
        s.text(x + 18, y + 91, f'one row per {rows}', 'lab', wrap=w)
        lines = _wrap(measures, 30)
        if len(lines) > 2:   # two lines at most: the second ends with "+N more" and stays within 30 characters
            first = lines[0].rstrip(',').split(', ')
            second = lines[1].rstrip(',').split(', ')
            while second and len(', '.join(second)) + len(f' +{len(measures) - len(first) - len(second)} more') > 30:
                second.pop()
            lines = [lines[0], ', '.join(second) + f' +{len(measures) - len(first) - len(second)} more']
        for j, line in enumerate(lines):
            s.text(x + 18, y + 110 + 15 * j, line, 'sl', wrap=w)
        kb = r['sizes_kb'][name]
        bw = (cw - 36 - 54) * kb / top
        s.add(f'<rect x="{x + 18}" y="{y + ch - 19}" width="{cw - 36 - 54}" height="6" rx="3" fill="{p["soft"]}"/>')
        s.add(f'<rect x="{x + 18}" y="{y + ch - 19}" width="{max(bw, 3):.1f}" height="6" rx="3" fill="{col}"'
              f'{s.anim("g", delay + .3)}/>')
        s.text(x + cw - 18, y + ch - 13, f'{kb} KB', 'n', 'end', fill=p['muted'], wrap=w)
        shown.append(dict(file=name, step=step, question=question, rows=rows, measures=measures, rehearsal_kb=kb))
    s.text(36, 474, f'Together they stay under {c["MAX_OUT_BYTES"] / 2 ** 20:g} MB, or the command exits 1. An '
                    'empty field means “not applicable”; inf means an exact match.', 'lab', wrap='s@.9')
    values['outputs'] = shown
    return s.render('The six output files of quant_error.py all',
                    '; '.join(f'{x["file"]} ({x["step"]}): {x["question"]} One row per {x["rows"]}; '
                              f'{x["rehearsal_kb"]} KB in the rehearsal' for x in shown))


# ------------------------------------------------------------------------------------------------------- positions
def positions(theme, static, d, values):
    s = Svg(theme, 360, static); p = s.p
    c, df = d['code']['constants'], d['code']['defaults']
    per_slice, seq, chunks, ctx = df['--tokens-per-slice'], df['--seq-len'], df['--kl-chunks'], c['KL_CTX']
    n_seq, span, scored = per_slice // min(seq, per_slice), chunks * ctx, chunks * d['scored_per_chunk']
    header(s, 'HOW TO READ THE NUMBERS · ONE SLICE AT THE DEFAULT SETTINGS',
           'The twin forward and llama.cpp score different positions',
           f'Drawn to scale in tokens: the twin forward reads the first {per_slice:,}, llama.cpp the first {chunks} '
           f'chunks of {ctx}')
    X0, X1 = 36, 844
    xs = lambda t: X0 + t / span * (X1 - X0)
    rows = [(160, 'Twin forward', 'tokens.csv, layers.csv, linears.csv',
             f'{n_seq} sequences of {seq}; every position scored', p['navy']),
            (250, 'llama.cpp', 'kl.csv',
             f'{chunks} chunks of {ctx}; positions {ctx // 2} to {ctx - 2} scored: {scored:,} tokens', p['brass'])]
    for y, name, files, note, col in rows:
        s.text(X0, y - 14, name, 'lab2', wrap='f@.15')
        s.text(X0 + 7.2 * len(name) + 16, y - 14, files, 'sl', wrap='f@.15')
        s.text(X1, y - 14, note, 'lab', 'end', wrap='f@.15')
    y = rows[0][0]
    for k in range(n_seq):
        a, b = xs(k * seq) + (1 if k else 0), xs((k + 1) * seq) - 1
        s.add(f'<rect x="{a:.1f}" y="{y}" width="{b - a:.1f}" height="26" rx="4" fill="{p["navy"]}"'
              f'{s.anim("s", .3 + .08 * k)}/>')
    y = rows[1][0]
    for k in range(chunks):
        a, m, b = xs(k * ctx) + (1 if k else 0), xs(k * ctx + ctx // 2), xs((k + 1) * ctx) - 1
        dl = .5 + .06 * k
        s.add(f'<rect x="{a:.1f}" y="{y}" width="{m - a:.1f}" height="26" rx="4" fill="{p["soft"]}" '
              f'stroke="{p["line"]}"{s.anim("s", dl)}/>'
              f'<rect x="{m:.1f}" y="{y}" width="{b - m:.1f}" height="26" rx="4" fill="{p["brass"]}"{s.anim("s", dl)}/>')
    for t in range(0, span + 1, per_slice):
        s.add(f'<line x1="{xs(t):.1f}" y1="{y + 36}" x2="{xs(t):.1f}" y2="{y + 41}" stroke="{p["muted"]}"/>')
        s.text(xs(t), y + 55, f'{t:,}', 'ax', 'middle' if 0 < t < span else ('start' if t == 0 else 'end'))
    s.text(X1, y + 72, 'tokens of the slice →', 'ax', 'end')
    ly = 340
    for x, col, lab, stroke in ((X0, p['navy'], 'scored by the twin forward', ''),
                                (X0 + 200, p['brass'], 'scored by llama.cpp', ''),
                                (X0 + 360, p['soft'], 'read as context, not scored', f' stroke="{p["line"]}"')):
        s.add(f'<rect x="{x}" y="{ly - 9}" width="12" height="10" rx="2" fill="{col}"{stroke}/>')
        s.text(x + 18, ly, lab, 'lab')
    s.text(X1, ly, 'so read tokens.csv and kl.csv each on its own', 'lab', 'end')
    values['positions'] = dict(tokens_per_slice=per_slice, seq_len=seq, sequences=n_seq, kl_chunks=chunks, kl_ctx=ctx,
                               kl_span_tokens=span, kl_scored_per_chunk=d['scored_per_chunk'], kl_scored=scored,
                               scored_from=ctx // 2, scored_to=ctx - 2)
    return s.render('Which positions the twin forward and llama.cpp score',
                    f'The twin forward scores every position of {n_seq} sequences of {seq} tokens from the first '
                    f'{per_slice}; llama.cpp scores positions {ctx // 2} to {ctx - 2} of each of {chunks} chunks of '
                    f'{ctx}, {scored} tokens.')


FIGS = dict(hero=hero, outputs=outputs, positions=positions)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--static', action='store_true', help='no animation (for previews)')
    ap.add_argument('--out', type=Path, default=HERE)
    ap.add_argument('--build-fonts', type=Path, metavar='DIR', help='remake fonts/*.woff2 from the google/fonts files')
    a = ap.parse_args()
    if a.build_fonts:
        kit.build_fonts(a.build_fonts)
    d = load()
    a.out.mkdir(parents=True, exist_ok=True)
    values = dict(code=d['code'], rehearsal=d['rehearsal'])
    for name, fn in FIGS.items():
        for theme in kit.PAL:
            (a.out / f'{name}-{theme}.svg').write_text(fn(theme, a.static, d, values), encoding='utf-8')
    (a.out / 'values.json').write_text(json.dumps(values, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'wrote {2 * len(FIGS)} SVGs and values.json to {a.out}')


if __name__ == '__main__':
    main()
