#!/usr/bin/env python3
"""This folder's README figures (light and dark SVG of each), drawn from ../results/*.json, never typed in:
    python figures/make_figures.py [--static]
Style, palette and motion come from ../../figures/make_figures.py (#848), so both READMEs read as one study.
"""
from __future__ import annotations

import argparse, importlib.util, json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent / 'results'
_spec = importlib.util.spec_from_file_location('kvfig848', HERE.parent.parent / 'figures' / 'make_figures.py')
base = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(base)
Svg, header, W = base.Svg, base.header, base.W

BITS = {'f16': 16, 'bf16': 16, 'q8_0': 8.5, 'q5_1': 6, 'q5_0': 5.5, 'q4_1': 5, 'q4_0': 4.5, 'iq4_nl': 4.5}


def load(name):
    return json.loads((RES / name).read_text())


def pooled(runs, choice):
    rs = [r for r in runs if r['choice'] == choice and 'kld' in r]
    if not rs: return None
    return {'kld': sum(r['kld'] for r in rs) / len(rs), 'top': sum(r['same_top'] for r in rs) / len(rs),
            'ln': sum(r['ln_ratio'] for r in rs) / len(rs), 'packs': len(rs)}


def fmt_mib(x):
    return f'{x / 1024:.2f} GiB' if x >= 1024 else f'{x:.0f} MiB' if x >= 10 else f'{x:.2f} MiB'


# ------------------------------------------------------------------------------------------------------------- hero
def hero(theme, static, mem_t2, q):
    s = Svg(theme, 286, static); p = s.p
    s.text(36, 46, 'TEAM 12 · SERVING · KV CACHE ON A LAPTOP', 'cap', fill=p['brass'])
    s.text(36, 78, 'What each cache choice costs at 8k context', 't', extra=' style="font-size:25px"')
    s.text(36, 102, 'llama.cpp b11669 · Metal · Apple M6 32 GB · dry run 2 shape for memory, Llama-3.2-1B for quality', 'st')
    cls = '' if static else ' class="g"'
    s.add(f'<rect x="36" y="116" width="64" height="2" rx="1" fill="{p["brass"]}"{cls}/>')
    m = {r['choice']: r for r in mem_t2['runs'] if r['ctx'] == 8192}
    q8, q4, q4n = pooled(q['runs'], 'q8_0'), pooled(q['runs'], 'q4_0'), pooled(q['runs'], 'q4_0+norot')
    tiles = [
        ('Q8_0 · HALF THE CACHE', f"{m['q8_0']['kv_mib_per_1k']:g} MiB", 'per 1k tokens on dry run 2 (f16: '
         f"{m['f16']['kv_mib_per_1k']:g})", f"KL {q8['kld']:.5f} · same top-1 {q8['top']:.1f}%", p['sage']),
        ('Q4_0 · A QUARTER, NOT FREE', f"{m['q4_0']['kv_mib_per_1k']:g} MiB", 'per 1k tokens on dry run 2',
         f"KL {q4['kld']:.3f} · PPL +{100 * (math.exp(q4['ln']) - 1):.1f}%", p['navy']),
        ('ROTATION · ON BY DEFAULT', f"{q4n['kld'] / q4['kld']:.1f}×", 'less KL for q4_0 with it on',
         f"off: KL {q4n['kld']:.3f} · same top-1 {q4n['top']:.1f}%", p['clay']),
    ]
    tw, gap, x0, y0 = 258, 15, 36, 140
    for i, (cap, big, l1, l2, col) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        a = '' if static else f' class="f" style="animation-delay:{.25 + .18 * i:.2f}s"'
        s.add(f'<g{a}><rect x="{x}" y="{y0}" width="{tw}" height="118" rx="12" fill="{p["card"]}" stroke="{p["line"]}"/>'
              f'<rect x="{x}" y="{y0 + 18}" width="3" height="82" rx="1.5" fill="{col}"/>'
              f'<text x="{x + 20}" y="{y0 + 30}" class="cap">{cap}</text>'
              f'<text x="{x + 20}" y="{y0 + 72}" class="big" fill="{col}">{big}</text>'
              f'<text x="{x + 20}" y="{y0 + 92}" class="lab">{l1}</text>'
              f'<text x="{x + 20}" y="{y0 + 108}" class="n" fill="{p["muted"]}">{l2}</text></g>')
    return s.render('KV cache on a laptop at a glance')


# ------------------------------------------------------------------------------------------------ bits vs quality
def tradeoff(theme, static, q):
    s = Svg(theme, 440, static); p = s.p
    header(s, 'QUALITY AT 8K CONTEXT · LLAMA-3.2-1B · SIX PACKS', 'Eight bits are nearly free; each step below costs more',
           'Mean KL(f16 cache ‖ choice) per scored token, log scale, against bits per cached element; rotation lowers it at every width')
    x0, x1, y0, y1 = 96, 840, 150, 370
    lo, hi = 1e-5, 0.5
    cats = [16, 8.5, 6, 5.5, 5, 4.5]
    xs = lambda b: x0 + 40 + cats.index(b) * (x1 - x0 - 80) / (len(cats) - 1)
    ys = lambda k: y1 - (math.log10(max(k, lo)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (y1 - y0)
    for e in range(-5, 0):
        y = ys(10 ** e)
        s.add(f'<line x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{p["grid"]}"/>')
        s.text(x0 - 10, y + 4, f'1e{e}'.replace('-', '−'), 'ax', anchor='end')
    for b in (16, 8.5, 6, 5.5, 5, 4.5):
        s.text(xs(b), y1 + 22, f'{b:g}', 'ax', anchor='middle')
    s.text((x0 + x1) / 2, y1 + 42, 'bits per element (evenly spaced)', 'lab', anchor='middle')
    series = [('rotated (b11669 default)', p['navy'], ['q8_0', 'q5_1', 'q5_0', 'q4_1', 'q4_0']),
              ('rotation off', p['clay'], ['q8_0+norot', 'q5_0+norot', 'q4_0+norot'])]
    ref = pooled(q['runs'], 'bf16')
    if ref:
        x, y = xs(16), ys(ref['kld'])
        s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="none" stroke="{p["muted"]}" stroke-width="1.6"/>')
        s.text(x, y + 20, f'bf16 {ref["kld"]:.5f}', 'n', anchor='middle', fill=p['muted'])
        s.text(x, y + 35, 'the 16-bit floor', 'lab', anchor='middle')
    for si, (name, col, cs) in enumerate(series):
        pts = [(c, pooled(q['runs'], c)) for c in cs]
        pts = [(c, v) for c, v in pts if v]
        path = ' '.join(f'{"M" if i == 0 else "L"}{xs(BITS[c.split("+")[0]]):.1f},{ys(v["kld"]):.1f}' for i, (c, v) in enumerate(pts))
        d = '' if static else ' class="d" pathLength="1"'
        s.add(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="1.6" stroke-opacity=".55"{d}/>')
        for i, (c, v) in enumerate(pts):
            x, y = xs(BITS[c.split('+')[0]]), ys(v['kld'])
            a = '' if static else f' class="f" style="animation-delay:{.5 + .1 * i + .4 * si:.2f}s"'
            lab = c.split('+')[0]
            dy = 20 if si == 0 else -12
            s.add(f'<g{a}><circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{col}"/>'
                  f'<text x="{x:.1f}" y="{y + dy:.1f}" text-anchor="middle" class="n" fill="{col}">{lab} {f'{v["kld"]:.5f}' if v["kld"] < 0.001 else f'{v["kld"]:.4f}'}</text></g>')
        s.add(f'<circle cx="{x0 + 10}" cy="{y0 - 6 + 18 * si}" r="4.5" fill="{col}"/>')
        s.text(x0 + 20, y0 - 2 + 18 * si, name, 'lab')
    return s.render('KV-cache quality against bits per element at 8k context')


# --------------------------------------------------------------------------------------------- long-context memory
def longctx(theme, static, mem_t2, mem_l1):
    s = Svg(theme, 420, static); p = s.p
    header(s, 'LEAD ITEM 8 · MEMORY AGAINST CONTEXT', 'The cache grows by the same amount per 1k tokens at every length',
           'KV cache that llama.cpp allocates, MiB, at 8k, 32k and 128k context; f16, q8_0 and q4_0, both caches the same type')
    rows = [('dry run 2 shape', mem_t2), ('Llama-3.2-1B', mem_l1)]
    choices = [('f16', p['navy3']), ('q8_0', p['navy']), ('q4_0', p['sage'])]
    ctxs = [8192, 32768, 131072]
    top = max(r['kv_mib'] for _, m in rows for r in m['runs'] if r['choice'] in ('f16',))
    gx, gw, y = 196, 430, 130
    for ri, (name, m) in enumerate(rows):
        by = {(r['ctx'], r['choice']): r for r in m['runs']}
        s.text(36, y + 10, name, 'lab2')
        for ci, ctx in enumerate(ctxs):
            yy = y + 26 + ci * 28
            s.text(gx - 12, yy + 12, f'{ctx // 1024}k', 'ax', anchor='end')
            for k, (c, col) in enumerate(choices):
                r = by.get((ctx, c))
                if not r: continue
                w = max(1.5, r['kv_mib'] / top * gw)
                a = '' if static else f' class="g" style="animation-delay:{.2 + .12 * ci + .05 * k + .5 * ri:.2f}s"'
                s.add(f'<rect x="{gx}" y="{yy + k * 7}" width="{w:.1f}" height="6" rx="2" fill="{col}"{a}/>')
            r16, r8 = by[(ctx, 'f16')], by[(ctx, 'q8_0')]
            s.text(gx + r16['kv_mib'] / top * gw + 8, yy + 13, f"{fmt_mib(r16['kv_mib'])} · {fmt_mib(r8['kv_mib'])} q8_0", 'n',
                   fill=p['muted'])
        y += 26 + 3 * 28 + 12
    for k, (c, col) in enumerate(choices):
        s.add(f'<rect x="{36 + k * 70}" y="{392}" width="10" height="6" rx="2" fill="{col}"/>')
        s.text(50 + k * 70, 398, c, 'lab')
    return s.render('KV-cache memory against context length')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--static', action='store_true'); a = ap.parse_args()
    mem_t2, mem_l1 = load('memory_t2.json'), load('memory_llama1b.json')
    q = load('quality_llama1b_ctx8192.json')
    figs = {'hero': lambda t: hero(t, a.static, mem_t2, q), 'tradeoff': lambda t: tradeoff(t, a.static, q),
            'longctx': lambda t: longctx(t, a.static, mem_t2, mem_l1)}
    for name, f in figs.items():
        for theme in ('light', 'dark'):
            (HERE / f'{name}-{theme}{"-static" if a.static else ""}.svg').write_text(f(theme))
    print('wrote', ', '.join(figs))


if __name__ == '__main__':
    main()
