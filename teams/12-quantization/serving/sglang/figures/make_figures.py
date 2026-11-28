#!/usr/bin/env python3
"""The README's figures, drawn from ../results/*.json (a light and a dark SVG of each):  python figures/make_figures.py

Every plotted number comes from results/spike_summary.json or results/sglang_pr_ernie21b.json, never typed in, and
is also written to values.json. Text is set in Inter and JetBrains Mono (SIL Open Font License 1.1, see OFL.txt):
each SVG embeds a subset of fonts/*.woff2 holding only the glyphs it uses, because GitHub shows an SVG as an image,
which loads no outside font. Motion is CSS inside each SVG: one soft fade or draw-in that plays once, only under
prefers-reduced-motion: no-preference; a renderer without CSS animation shows the finished figure. Nothing loops.
--static writes the finished state only (for previews).

Needs fonttools and brotli (pip install fonttools==4.68.0 brotli==1.2.1); with these versions a rerun reproduces the
SVGs byte for byte. --build-fonts DIR remakes fonts/*.woff2 from the google/fonts files named in FONT_SOURCES.
The colours passed palette checks (lightness band, chroma floor, CVD and normal-vision separation of the
pairs that share a chart, contrast) on both surfaces.
"""
from __future__ import annotations

import argparse, base64, hashlib, html, io, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent / 'results'
FONTS = HERE / 'fonts'
W = 880

PAL = {   # surfaces and ink from ../../kv_cache/figures; the three series steps were re-stepped to pass the checks
    'light': dict(bg='#FBFAF7', card='#FFFFFF', line='#E6E1D6', ink='#1C1B19', muted='#6F695F', grid='#EEEAE1',
                  accent='#A08B63', clay='#CA7A64', navy='#2E558F', brass='#B8892D'),
    'dark': dict(bg='#0F1115', card='#15181D', line='#272B33', ink='#ECE8E0', muted='#9A958A', grid='#21252C',
                 accent='#B9A27A', clay='#AF5840', navy='#6090D8', brass='#B58629'),
}
SANS_STACK = "'G12 Inter', Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO_STACK = "'G12 Mono', 'JetBrains Mono', 'SF Mono', ui-monospace, Menlo, Consolas, monospace"
MONO_CLASSES = {'n', 'big', 'ax', 'nb'}

GF_COMMIT = '5026800714d07231937d92eb4cceabf06e05d74e'   # github.com/google/fonts
FONT_SOURCES = {   # embedded family: (google/fonts path, sha256, axis limits, base subset file, weights)
    'G12 Inter': ('ofl/inter/Inter[opsz,wght].ttf', '29160a80ff49ddcab2c97711247e08b1fab27a484a329ce8b813d820dc559031',
                  dict(opsz=14, wght=(400, 600)), 'Inter-subset.woff2', '400 600'),
    'G12 Mono': ('ofl/jetbrainsmono/JetBrainsMono[wght].ttf',
                 '48715a42ec242c21e9f02692891e147d022299a52e48d5e413e1a942193ffeda',
                 dict(wght=(400, 500)), 'JetBrainsMono-subset.woff2', '400 500'),
}
CHARSET = (''.join(map(chr, range(0x20, 0x7F))) + ' ±µ·×Δ –—‖‘'
           '’“”•… ←↑→↓−≈≤≥')


# ----------------------------------------------------------------------------------------------------------- fonts
def _subset(font, chars: str):
    from fontTools import subset
    o = subset.Options()
    o.name_IDs, o.name_languages, o.notdef_outline = ['*'], ['*'], True      # keep the copyright and licence names
    o.layout_features = ['kern', 'liga', 'calt', 'tnum', 'case']
    s = subset.Subsetter(o)
    s.populate(text=chars)
    s.subset(font)


def _woff2(font) -> bytes:
    b = io.BytesIO()
    font.flavor = 'woff2'
    font.save(b)
    return b.getvalue()


def build_fonts(src: Path) -> None:
    """fonts/*.woff2 from the google/fonts files (same basenames in src): CHARSET only, axes limited."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    FONTS.mkdir(exist_ok=True)
    for path, sha, limits, out, _ in FONT_SOURCES.values():
        f = src / Path(path).name
        if hashlib.sha256(f.read_bytes()).hexdigest() != sha:
            raise SystemExit(f'{f}: not the file at google/fonts {GF_COMMIT[:12]} ({path})')
        font = TTFont(f, recalcTimestamp=False)
        _subset(font, CHARSET)
        font = instancer.instantiateVariableFont(font, limits)
        (FONTS / out).write_bytes(_woff2(font))
        print(f'wrote {FONTS / out}')


_cache: dict = {}


def font_face(family: str, chars: str) -> str:
    """@font-face with a data URI of the base subset cut down to `chars`."""
    from fontTools.ttLib import TTFont
    chars = ''.join(sorted(set(chars) | {' '}))
    if (family, chars) not in _cache:
        _, _, _, base, weights = FONT_SOURCES[family]
        font = TTFont(FONTS / base, recalcTimestamp=False)
        missing = set(chars) - {chr(c) for c in font.getBestCmap()}
        if missing:
            raise SystemExit(f'{family}: no glyph for {sorted(missing)}; add them to CHARSET and run --build-fonts')
        _subset(font, chars)
        data = base64.b64encode(_woff2(font)).decode()
        _cache[family, chars] = (f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weights};"
                                 f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return _cache[family, chars]


# ------------------------------------------------------------------------------------------------------------- svg
class Svg:
    def __init__(self, theme: str, h: int, static: bool):
        self.p, self.h, self.static, self.parts = PAL[theme], h, static, []
        self.chars = {'G12 Inter': '', 'G12 Mono': ''}

    def add(self, s: str):
        self.parts.append(s)

    def anim(self, cls: str, delay: float) -> str:
        return '' if self.static else f' class="{cls}" style="animation-delay:{delay:.2f}s"'

    def text(self, x, y, s, cls='lab', anchor='start', fill=None, wrap: str = ''):
        """One line of text; `cls` may hold several classes; `wrap` is an animation class and delay, e.g. 'f@0.4'."""
        self.chars['G12 Mono' if MONO_CLASSES & set(cls.split()) else 'G12 Inter'] += s
        f = f' fill="{fill}"' if fill else ''
        if wrap and not self.static:
            c, d = wrap.split('@')
            a = f' class="{cls} {c}" style="animation-delay:{float(d):.2f}s"'
        else:
            a = f' class="{cls}"'
        self.add(f'<text x="{x:.1f}" y="{y:.1f}"{a} text-anchor="{anchor}"{f}>{html.escape(s, quote=False)}</text>')

    def render(self, title: str, desc: str) -> str:
        p = self.p
        faces = ''.join(font_face(fam, ch) for fam, ch in self.chars.items() if ch)
        motion = '' if self.static else (
            '@media (prefers-reduced-motion:no-preference){'
            '@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}'
            '@keyframes show{from{opacity:0}to{opacity:1}}'
            '@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}'
            '@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}'
            '.f{animation:fade .9s cubic-bezier(.2,.7,.2,1) both}'
            '.s{animation:show .8s ease-out both}'
            '.g{transform-box:fill-box;transform-origin:left center;animation:grow 1s cubic-bezier(.22,.8,.24,1) both}'
            '.d{animation:draw 1.1s cubic-bezier(.45,.05,.25,1) both}}')
        css = (faces + f'text{{font-family:{SANS_STACK};fill:{p["ink"]};font-kerning:normal}}'
               f'.t{{font-size:21px;font-weight:600;letter-spacing:-.012em}}'
               f'.st{{font-size:12.5px;fill:{p["muted"]}}}'
               f'.cap{{font-size:10px;font-weight:600;letter-spacing:.14em;fill:{p["muted"]}}}'
               f'.lab{{font-size:12px;fill:{p["muted"]}}}'
               f'.lab2{{font-size:12.5px;font-weight:500}}'
               f'.n{{font-family:{MONO_STACK};font-size:11.5px;font-variant-numeric:tabular-nums}}'
               f'.nb{{font-family:{MONO_STACK};font-size:12px;font-weight:500;font-variant-numeric:tabular-nums}}'
               f'.big{{font-family:{MONO_STACK};font-size:32px;font-weight:500;letter-spacing:-.02em}}'
               f'.big.sm{{font-size:28px}}.t.lg{{font-size:24px}}'
               f'.ax{{font-family:{MONO_STACK};font-size:10.5px;fill:{p["muted"]};font-variant-numeric:tabular-nums}}'
               + motion)
        t = html.escape(title)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" viewBox="0 0 {W} {self.h}" '
                f'role="img" aria-labelledby="t d"><title id="t">{t}</title><desc id="d">{html.escape(desc)}</desc>'
                f'<style>{css}</style>'
                f'<rect x=".5" y=".5" width="{W - 1}" height="{self.h - 1}" rx="16" fill="{p["bg"]}" stroke="{p["line"]}"/>'
                + ''.join(self.parts) + '</svg>\n')


def header(s: Svg, kicker: str, title: str, sub: str):
    s.text(36, 44, kicker, 'cap')
    s.text(36, 72, title, 't')
    s.text(36, 94, sub, 'st')


def pc(x: float, d: int = 1) -> str:
    return f'{100 * x:.{d}f}%'


def dot(s: Svg, x, y, col, r=5.0, extra=''):
    s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}" stroke="{s.p["bg"]}" stroke-width="2"{extra}/>')


def legend(s: Svg, x, y, items):
    for col, lab in items:
        dot(s, x + 5, y - 4, col, r=4.5)
        s.text(x + 16, y, lab, 'lab')
        x += 16 + 6.4 * len(lab) + 26


# ------------------------------------------------------------------------------------------------------------ data
def load() -> tuple[dict, dict]:
    spike = json.loads((RES / 'spike_summary.json').read_text())
    up = json.loads((RES / 'sglang_pr_ernie21b.json').read_text())
    return spike, up


def share(m: dict) -> float:
    return m['same_top1'] / m['positions']


ENGINE_ROWS = [   # (group label, run or G5 variant, dtype label)
    ('SGLang 0.5.23, stock', 'c2_s002_bf16', 'bf16'), ('SGLang 0.5.23, stock', 'c3_s002_fp16', 'fp16'),
    ('vLLM 0.33.0', 'v2_s002_bf16', 'bf16'), ('vLLM 0.33.0', 'v3_s002_fp16', 'fp16'),
    ('SGLang + diagnostic patch', 'c2_s002_bf16_patched', 'bf16'), ('SGLang + diagnostic patch', 'c3_s002_fp16_patched', 'fp16'),
    ('G5 itself, rounded', 'g5_bf16', 'bf16'), ('G5 itself, rounded', 'g5_fp16', 'fp16'),
]


def engine_values(spike: dict) -> list[dict]:
    rows = []
    for group, key, dt in ENGINE_ROWS:
        if key in spike['runs']:
            m = spike['runs'][key]['single']
            on, off = m['g5'], m['g5_router_bias_off']
        else:
            on, off = spike['g5'][key]['g5'], spike['g5'][key]['g5_router_bias_off']
        rows.append(dict(group=group, key=key, dtype=dt, vs_g5=share(on), vs_g5_router_bias_off=share(off),
                         positions=on['positions']))
    return rows


# ------------------------------------------------------------------------------------------------------------ hero
def hero(theme, static, spike, up, values):
    s = Svg(theme, 300, static); p = s.p
    s.text(36, 46, 'TEAM 12 · SERVING · SGLANG AND VLLM', 'cap')
    s.text(36, 78, 'SGLang drops our router’s selection bias. vLLM keeps it.', 't lg')
    sgl, vl = spike['runs']['c2_s002_bf16'], spike['runs']['v2_s002_bf16']
    m = spike['model']
    s.text(36, 102, f"Our ERNIE export at the dry-run-2 shape ({m['n_layer']} layers, {m['moe']['num_experts']} experts, "
                    f"top-{m['moe']['top_k']}), random weights · SGLang {sgl['version']} and vLLM {vl['version']} · "
                    f"one {sgl['gpu'].removeprefix('NVIDIA ')} · bf16", 'st')
    s.add(f'<rect x="36" y="116" width="56" height="2" rx="1" fill="{p["accent"]}"{s.anim("g", 0)}/>')
    g5b = spike['g5']['g5_bf16']['g5']
    ra, rb = up['routed_experts']['main'], up['routed_experts']['fix']
    sv = up['serving']
    tiles = [
        ('STOCK SGLANG · BF16', pc(share(sgl['single']['g5'])), 'same top-1 as our model (G5 fp32)',
         f"{pc(share(sgl['single']['g5_router_bias_off']))} as G5 without the bias", p['clay']),
        ('VLLM · BF16', pc(share(vl['single']['g5'])), 'same top-1 as our model (G5 fp32)',
         f"G5’s own bf16 run: {pc(share(g5b))}", p['navy']),
        ('THE FIX, OPEN UPSTREAM', f"{pc(ra['prompt_all_layers'])[:-1]} → {pc(rb['prompt_all_layers'])}",
         'ERNIE-4.5-21B routing agreement',
         f"bs=1 TPOT {sv['main']['bs1_median_tpot_ms']:.2f} → {sv['fix']['bs1_median_tpot_ms']:.2f} ms", p['navy']),
    ]
    values['hero'] = [dict(caption=c, value=b, line1=l1, line2=l2) for c, b, l1, l2, _ in tiles]
    tw, gap, x0, y0, th = 260, 14, 36, 140, 124
    for i, (cap, big, l1, l2, col) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        s.add(f'<g{s.anim("f", .2 + .15 * i)}><rect x="{x}" y="{y0}" width="{tw}" height="{th}" rx="12" '
              f'fill="{p["card"]}" stroke="{p["line"]}"/>'
              f'<rect x="{x}" y="{y0 + 20}" width="3" height="{th - 40}" rx="1.5" fill="{col}"/></g>')
        d = f'f@{.3 + .15 * i:.2f}'
        s.text(x + 22, y0 + 32, cap, 'cap', wrap=d)
        s.text(x + 22, y0 + 74, big, 'big sm' if '→' in big else 'big', wrap=d)
        s.text(x + 22, y0 + 95, l1, 'lab', wrap=d)
        s.text(x + 22, y0 + 111, l2, 'n', fill=p['muted'], wrap=d)
    return s.render('SGLang and vLLM serving our model',
                    'Stock SGLang 0.5.23 agrees with our model on '
                    f"{values['hero'][0]['value']} of top-1 tokens and with the model without its router bias on "
                    f"{pc(share(sgl['single']['g5_router_bias_off']))}; vLLM 0.33.0 agrees on "
                    f"{values['hero'][1]['value']}. The upstream fix raises routing agreement on ERNIE-4.5-21B from "
                    f"{pc(ra['prompt_all_layers'])} to {pc(rb['prompt_all_layers'])}.")


# --------------------------------------------------------------------------------------------------------- engines
def engines(theme, static, spike, up, values):
    s = Svg(theme, 486, static); p = s.p
    n = spike['prompts']['top1_positions']
    header(s, f"OUR MODEL’S EXPORT · RANDOM WEIGHTS · {spike['prompts']['count']} PROMPTS · {n:,} POSITIONS",
           'Stock SGLang matches our model with the router bias removed',
           'Same top-1 next token as G5 in fp32, one request at a time. Rounding moves both dots; dropping the bias '
           'swaps them.')
    legend(s, 36, 128, [(p['navy'], 'vs our model (G5 fp32, as exported)'),
                        (p['brass'], 'vs G5 with its router bias set to zero')])
    rows = engine_values(spike)
    values['engines'] = rows
    X0, X1, lo, hi, C1, C2 = 300, 726, 0.6, 1.0, 776, 846
    xs = lambda v: X0 + (v - lo) / (hi - lo) * (X1 - X0)
    y, pitch, ggap, ys, prev = 166, 27, 14, [], None
    for r in rows:
        if prev is not None and r['group'] != prev:
            y += ggap
        ys.append(y); prev = r['group']; y += pitch
    top, bot = ys[0] - 16, ys[-1] + 14
    for gx in (0.6, 0.7, 0.8, 0.9, 1.0):
        s.add(f'<line x1="{xs(gx):.1f}" y1="{top}" x2="{xs(gx):.1f}" y2="{bot}" stroke="{p["grid"]}"/>')
        s.text(xs(gx), bot + 17, f'{100 * gx:.0f}%', 'ax', 'middle')
    s.text(X1, bot + 36, 'same top-1, share of positions →', 'ax', 'end')
    s.text(C1, top - 4, 'vs G5', 'ax', 'end')
    s.text(C2, top - 4, 'bias off', 'ax', 'end')
    prev = None
    for i, (r, yy) in enumerate(zip(rows, ys)):
        d = .2 + .06 * i
        if r['group'] != prev:
            s.text(36, yy + 4, r['group'], 'lab2', wrap=f'f@{d:.2f}')
        prev = r['group']
        s.text(X0 - 16, yy + 4, r['dtype'], 'n', 'end', fill=p['muted'], wrap=f'f@{d:.2f}')
        a, b = xs(r['vs_g5']), xs(r['vs_g5_router_bias_off'])
        s.add(f'<g{s.anim("f", d + .1)}><line x1="{min(a, b):.1f}" y1="{yy}" x2="{max(a, b):.1f}" y2="{yy}" '
              f'stroke="{p["line"]}" stroke-width="2" stroke-linecap="round"/></g>')
        s.add(f'<g{s.anim("f", d + .2)}>')
        dot(s, b, yy, p['brass'])
        dot(s, a, yy, p['navy'])
        s.add('</g>')
        s.text(C1, yy + 4, pc(r['vs_g5']), 'n', 'end', wrap=f'f@{d + .2:.2f}')
        s.text(C2, yy + 4, pc(r['vs_g5_router_bias_off']), 'n', 'end', fill=p['muted'], wrap=f'f@{d + .2:.2f}')
    s.text(36, 470, 'fp16 shrinks the rounding noise, not the gap: stock SGLang’s distance from our model is a routing '
                    'difference.', 'lab', wrap='s@1.0')
    return s.render('Engines against our model, with and without its router bias',
                    '; '.join(f"{r['group']} {r['dtype']}: {pc(r['vs_g5'])} same top-1 as G5, "
                              f"{pc(r['vs_g5_router_bias_off'])} as G5 without its router bias" for r in rows))


# --------------------------------------------------------------------------------------------------------- routing
def routing(theme, static, spike, up, values):
    s = Svg(theme, 452, static); p = s.p
    re_ = up['routed_experts']; a, b = re_['main'], re_['fix']
    layers = up['moe_layers']
    pr = up['prompts']
    header(s, f"THE FIX, OPEN UPSTREAM · {up['model'].split(' @')[0].upper()} · ONE {up['serving']['gpu'].removeprefix('NVIDIA ').split(' ')[0]}",
           'Routing agreement with transformers, per MoE layer',
           f"Share of prompt tokens whose routed experts equal transformers’ ({pr['prompt_tokens']} tokens × "
           f"{len(layers)} MoE layers; bf16 checkpoint, fp32 router)")
    legend(s, 36, 128, [(p['clay'], 'SGLang main (the bias is dropped)'), (p['navy'], 'with the fix')])
    X0, X1, Y0, Y1, lo, hi = 84, 720, 372, 156, 0.5, 1.0
    pitch = (X1 - X0) / len(layers)
    xs = lambda i: X0 + (i + .5) * pitch
    ys = lambda v: Y0 - (v - lo) / (hi - lo) * (Y0 - Y1)
    for gy in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        s.add(f'<line x1="{X0}" y1="{ys(gy):.1f}" x2="{X1}" y2="{ys(gy):.1f}" stroke="{p["grid"]}"/>')
        s.text(X0 - 10, ys(gy) + 3.5, f'{100 * gy:.0f}%', 'ax', 'end')
    for i, L in enumerate(layers):
        if L in (1, 5, 10, 15, 20, 25, layers[-1]):
            s.text(xs(i), Y0 + 18, str(L), 'ax', 'middle')
    s.text(X1, Y0 + 36, 'MoE layer →', 'ax', 'end')
    pa, pb = a['prompt_per_layer'], b['prompt_per_layer']
    for i in range(len(layers)):
        x, ya, yb = xs(i), ys(pa[i]), ys(pb[i])
        cls = '' if static else f' class="d" style="animation-delay:{.2 + .02 * i:.3f}s"'
        s.add(f'<path d="M{x:.1f},{ya:.1f} L{x:.1f},{yb:.1f}" stroke="{p["line"]}" stroke-width="2" '
              f'stroke-linecap="round" fill="none" pathLength="1" stroke-dasharray="1"{cls}/>')
    for i in range(len(layers)):
        s.add(f'<g{s.anim("f", .15 + .02 * i)}>'); dot(s, xs(i), ys(pa[i]), p['clay'], r=4.5); s.add('</g>')
        s.add(f'<g{s.anim("f", .4 + .02 * i)}>'); dot(s, xs(i), ys(pb[i]), p['navy'], r=4.5); s.add('</g>')
    for v, col, lab, dl in ((b['prompt_all_layers'], p['navy'], 'all layers', 1.1),
                            (a['prompt_all_layers'], p['clay'], 'all layers', 1.0)):
        y = ys(v)
        s.add(f'<g{s.anim("f", dl)}><line x1="{X1 + 8}" y1="{y:.1f}" x2="{X1 + 22}" y2="{y:.1f}" stroke="{col}" '
              f'stroke-width="2" stroke-linecap="round"/></g>')
        s.text(X1 + 30, y - 2, pc(v), 'nb', wrap=f'f@{dl:.2f}')
        s.text(X1 + 30, y + 13, lab, 'lab', wrap=f'f@{dl:.2f}')
    s.text(36, 436, f"Decode tokens: {pc(a['decode_all_layers'])} → {pc(b['decode_all_layers'])}. Six short prompts "
                    f"plus {pr['new_tokens_each']} greedy tokens each; one run per build. Measured for the SGLang PR.",
           'lab', wrap='s@1.0')
    values['routing'] = dict(layers=layers, main_prompt=pa, fix_prompt=pb, main_all=a['prompt_all_layers'],
                             fix_all=b['prompt_all_layers'], main_decode=a['decode_all_layers'],
                             fix_decode=b['decode_all_layers'])
    return s.render('Routing agreement on ERNIE-4.5-21B before and after the fix',
                    f"Across {len(layers)} MoE layers, SGLang main agrees with transformers on "
                    f"{pc(min(pa))} to {pc(max(pa))} of prompt tokens per layer ({pc(a['prompt_all_layers'])} overall); "
                    f"with the fix, {pc(min(pb))} to {pc(max(pb))} ({pc(b['prompt_all_layers'])} overall).")


FIGS = dict(hero=hero, engines=engines, routing=routing)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--static', action='store_true', help='no animation (for previews)')
    ap.add_argument('--out', type=Path, default=HERE)
    ap.add_argument('--build-fonts', type=Path, metavar='DIR', help='remake fonts/*.woff2 from the google/fonts files')
    a = ap.parse_args()
    if a.build_fonts:
        build_fonts(a.build_fonts)
    spike, up = load()
    a.out.mkdir(parents=True, exist_ok=True)
    values: dict = {}
    for name, fn in FIGS.items():
        for theme in PAL:
            (a.out / f'{name}-{theme}.svg').write_text(fn(theme, a.static, spike, up, values), encoding='utf-8')
    (a.out / 'values.json').write_text(json.dumps(values, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'wrote {2 * len(FIGS)} SVGs and values.json to {a.out}')


if __name__ == '__main__':
    main()
