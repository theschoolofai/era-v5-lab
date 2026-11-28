#!/usr/bin/env python3
"""PILOT.md's figures, drawn from the committed CSVs (light and dark SVG of each):  python figures/make_figures.py

kld-slices     llama.cpp mean KLD per held-out slice (../kl.csv, kld_mean): experts-only Q4_K against Q4_K_M, with
               Q8_0 and MXFP4_MOE for context.
router-layers  router top-8 agreement by layer (../layers.csv, router_agree, mean over the 20 slices), four formats.

Every plotted number is read from those files (the llama.cpp version from ../summary.json), never typed in, and is
written to values.json beside the figures so it can be checked. The colours are the hues of Team 12's kv_cache figures
(navy, brass, sage, clay), stepped until every pair passes the dataviz palette checks in both themes: lightness band,
chroma floor, colour-blind separation (all pairs), normal-vision separation and contrast. Motion is CSS inside each
SVG: it plays once on load, stops for prefers-reduced-motion, and a renderer without CSS animation shows the finished
figure. --static writes the finished state only (for previews). Standard library only.
"""
from __future__ import annotations

import argparse, csv, json
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
FORMATS = ['Q8_0', 'Q4_K_M', 'experts-Q4_K', 'MXFP4_MOE']
GROUPS = [('ENGLISH', 'c4-'), ('INDIC', 'fw2-'), ('MATH', 'owm-'), ('SCIENCE', 'pes2o-'), ('CODE', 'vault-')]

PAL = {
    'light': dict(bg='#FBFAF7', line='#E6E1D6', ink='#1C1B19', muted='#7A746A', grid='#EEEAE1', link='#D8D2C6',
                  series={'Q8_0': '#556BAD', 'Q4_K_M': '#BB8422', 'experts-Q4_K': '#279376', 'MXFP4_MOE': '#A8423A'}),
    'dark': dict(bg='#0F1115', line='#272B33', ink='#ECE8E0', muted='#9A958A', grid='#21252C', link='#3A3F48',
                 series={'Q8_0': '#698CC9', 'Q4_K_M': '#BC881D', 'experts-Q4_K': '#3FA787', 'MXFP4_MOE': '#AF585F'}),
}
SANS = "Inter, 'SF Pro Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'SF Mono', ui-monospace, Menlo, Consolas, monospace"
W = 880


def mean(xs):
    return sum(xs) / len(xs)


def load() -> dict:
    """The numbers both figures plot, from the CSVs (and the llama.cpp version from summary.json)."""
    kl = list(csv.DictReader((RES / 'kl.csv').open(encoding='utf-8')))
    slices = list(dict.fromkeys(r['slice'] for r in kl))
    kld = {f: [next(float(r['kld_mean']) for r in kl if r['slice'] == s and r['format'] == f) for s in slices]
           for f in FORMATS}
    chunks, scored = {r['chunks'] for r in kl}, {r['tokens_scored'] for r in kl}
    assert len(chunks) == len(scored) == 1, 'kl.csv: not one chunk count and one scored-token count for every row'
    layers = list(csv.DictReader((RES / 'layers.csv').open(encoding='utf-8')))
    n_layers = 1 + max(int(r['layer']) for r in layers)
    agree = {f: [mean([float(r['router_agree']) for r in layers if r['format'] == f and int(r['layer']) == l])
                 for l in range(n_layers)] for f in FORMATS}
    per_layer = {len([r for r in layers if r['format'] == f and int(r['layer']) == l])
                 for f in FORMATS for l in range(n_layers)}
    assert per_layer == {len(slices)}, f'layers.csv: {per_layer} rows per format and layer, not {len(slices)}'
    groups = []
    for s in slices:
        g = next(name for name, prefix in GROUPS if s.startswith(prefix))
        if not groups or groups[-1][0] != g:
            assert g not in [x[0] for x in groups], f'kl.csv: slice group {g} is not contiguous'
            groups.append((g, []))
        groups[-1][1].append(s)
    llama = json.loads((RES / 'summary.json').read_text(encoding='utf-8'))['llama_cpp']
    return dict(slices=slices, groups=groups, kld=kld, kld_mean={f: mean(kld[f]) for f in FORMATS},
                chunks=int(chunks.pop()), scored=int(scored.pop()), agree=agree, n_layers=n_layers,
                llama=llama.split()[0])


class Svg:
    def __init__(self, theme: str, h: int, static: bool):
        self.p, self.h, self.static, self.parts = PAL[theme], h, static, []

    def add(self, s: str):
        self.parts.append(s)

    def anim(self, cls: str, delay: float) -> str:
        return '' if self.static else f' class="{cls}" style="animation-delay:{delay:.2f}s"'

    def text(self, x, y, s, cls='', anchor='start', fill=None):
        f = f' fill="{fill}"' if fill else ''
        c = f' class="{cls}"' if cls else ''
        self.add(f'<text x="{x:.1f}" y="{y:.1f}"{c} text-anchor="{anchor}"{f}>{escape(s)}</text>')

    def render(self, title: str, desc: str) -> str:
        p = self.p
        anim = '' if self.static else (
            '@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}'
            '@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}'
            '.f{animation:fade .8s cubic-bezier(.2,.7,.2,1) both}'
            '.d{stroke-dasharray:1;animation:draw 1.6s cubic-bezier(.45,.05,.25,1) both}'
            '@media (prefers-reduced-motion:reduce){*{animation:none!important}}')
        css = (f'text{{font-family:{SANS};fill:{p["ink"]}}}'
               f'.t{{font-size:21px;font-weight:600;letter-spacing:-.012em}}'
               f'.st{{font-size:12.5px;fill:{p["muted"]}}}'
               f'.cap{{font-size:10px;font-weight:600;letter-spacing:.14em;fill:{p["muted"]}}}'
               f'.lab{{font-size:12px;fill:{p["muted"]}}}'
               f'.lab2{{font-size:12.5px;font-weight:500}}'
               f'.n{{font-family:{MONO};font-variant-numeric:tabular-nums;font-size:11.5px}}'
               f'.sl{{font-family:{MONO};font-size:11px;fill:{p["muted"]}}}'
               f'.ax{{font-family:{MONO};font-variant-numeric:tabular-nums;font-size:10.5px;fill:{p["muted"]}}}' + anim)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" viewBox="0 0 {W} {self.h}" '
                f'role="img" aria-label="{escape(title)}"><title>{escape(title)}</title><desc>{escape(desc)}</desc>'
                f'<style>{css}</style>'
                f'<rect x=".5" y=".5" width="{W - 1}" height="{self.h - 1}" rx="16" fill="{p["bg"]}" stroke="{p["line"]}"/>'
                + ''.join(self.parts) + '</svg>\n')


def header(s: Svg, kicker: str, title: str, sub: str):
    s.text(36, 44, kicker, 'cap')
    s.text(36, 72, title, 't')
    s.text(36, 94, sub, 'st')


def marker(s: Svg, fmt: str, x: float, y: float) -> str:
    """Q8_0 and MXFP4_MOE are context (hollow circle, hollow diamond); Q4_K_M and experts-Q4_K are the comparison
    (filled, with a 2px ring in the surface colour)."""
    p, col = s.p, s.p['series'][fmt]
    if fmt == 'Q8_0':
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{p["bg"]}" stroke="{col}" stroke-width="1.6"/>'
    if fmt == 'MXFP4_MOE':
        r = 4.4
        return (f'<path d="M{x:.1f},{y - r:.1f} L{x + r:.1f},{y:.1f} L{x:.1f},{y + r:.1f} L{x - r:.1f},{y:.1f} Z" '
                f'fill="{p["bg"]}" stroke="{col}" stroke-width="1.6" stroke-linejoin="round"/>')
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{col}" stroke="{p["bg"]}" stroke-width="2"/>'


def legend(s: Svg, y: float, items: list[tuple[str, float]], line: bool):
    """A key per format, mirroring the mark (a marker for the dot plot, a line with its end dot for the line chart)."""
    p = s.p
    for fmt, x in items:
        if line:
            col = p['series'][fmt]
            s.add(f'<line x1="{x:.1f}" y1="{y - 4:.1f}" x2="{x + 18:.1f}" y2="{y - 4:.1f}" stroke="{col}" '
                  f'stroke-width="2" stroke-linecap="round"/>')
            s.text(x + 26, y, fmt, 'lab2')
        else:
            s.add(marker(s, fmt, x + 5, y - 4))
            s.text(x + 16, y, fmt, 'lab2')


# --------------------------------------------------------------------------------------------- (a) KLD per slice
def kld_slices(theme: str, static: bool, d: dict):
    X0, X1, XMAX, RH, GAP, TOP = 236, 828, 0.05, 18, 10, 166
    xs = lambda v: X0 + v / XMAX * (X1 - X0)
    assert max(max(v) for v in d['kld'].values()) <= XMAX, 'kl.csv: a kld_mean beyond the x axis'
    ys, y = {}, TOP
    for gi, (g, members) in enumerate(d['groups']):
        y += GAP if gi else 0
        for sl in members:
            ys[sl] = y
            y += RH
    mean_y = y + 26
    axis_y = mean_y + 34
    s = Svg(theme, axis_y + 38, static); p = s.p
    n = len(d['slices'])
    below = sum(e < q for e, q in zip(d['kld']['experts-Q4_K'], d['kld']['Q4_K_M']))
    header(s, f'QUANT_ERROR · OLMOE PILOT · LLAMA.CPP {d["llama"].upper()} · KL.CSV',
           f'Experts-only Q4_K is below Q4_K_M on {below} of {n} held-out slices',
           f'Mean KL(bf16 ‖ quant) in nats from llama-perplexity, per slice: {d["chunks"]} chunks of 512 tokens, '
           f'{d["scored"]:,} tokens scored per slice and format')
    legend(s, 126, [('Q8_0', 36), ('Q4_K_M', 104), ('experts-Q4_K', 190), ('MXFP4_MOE', 312)], line=False)
    s.text(420, 126, 'experts-Q4_K: routed experts at Q4_K, everything else Q8_0', 'lab')

    for t in (0, 0.01, 0.02, 0.03, 0.04, 0.05):
        s.add(f'<line x1="{xs(t):.1f}" y1="{TOP - 12}" x2="{xs(t):.1f}" y2="{mean_y + 12}" stroke="{p["grid"]}"/>')
        s.text(xs(t), axis_y, '0' if t == 0 else f'{t:.2f}', 'ax', 'middle')
    s.text(X1, axis_y + 18, 'mean KLD, nats →', 'ax', 'end')

    def row(y, vals, title, delay):
        e, q = xs(vals['experts-Q4_K']), xs(vals['Q4_K_M'])
        hit = f'<rect x="36" y="{y - RH / 2:.1f}" width="{X1 - 36}" height="{RH}" fill="{p["bg"]}" fill-opacity="0"/>'
        marks = (marker(s, 'Q8_0', xs(vals['Q8_0']), y) + marker(s, 'MXFP4_MOE', xs(vals['MXFP4_MOE']), y)
                 + f'<line x1="{e:.1f}" y1="{y:.1f}" x2="{q:.1f}" y2="{y:.1f}" stroke="{p["link"]}" stroke-width="2" '
                   f'stroke-linecap="round"/>'
                 + marker(s, 'Q4_K_M', q, y) + marker(s, 'experts-Q4_K', e, y))
        s.add(f'<g{s.anim("f", delay)}><title>{escape(title)}</title>{hit}{marks}</g>')

    for gi, (g, members) in enumerate(d['groups']):
        s.text(36, ys[members[0]] + 4, g, 'cap')
        for sl in members:
            i = d['slices'].index(sl)
            vals = {f: d['kld'][f][i] for f in FORMATS}
            s.text(110, ys[sl] + 4, sl, 'sl')
            row(ys[sl], vals, f'{sl}: ' + ' · '.join(f'{f} {vals[f]:.4g}' for f in FORMATS), .15 + .03 * i)

    m = d['kld_mean']
    s.add(f'<line x1="36" y1="{mean_y - 17:.1f}" x2="{X1}" y2="{mean_y - 17:.1f}" stroke="{p["line"]}"/>')
    s.text(36, mean_y + 4, f'MEAN OF {n}', 'cap')
    row(mean_y, m, f'mean of {n} slices: ' + ' · '.join(f'{f} {m[f]:.4g}' for f in FORMATS), .15 + .03 * n)
    a = s.anim('f', .3 + .03 * n)
    lab = lambda f: f'{m[f]:.4g}'
    s.add(f'<g{a}>'
          f'<text x="{xs(m["Q8_0"]) + 10:.1f}" y="{mean_y + 4:.1f}" class="n" fill="{p["muted"]}">{lab("Q8_0")}</text>'
          f'<text x="{xs(m["experts-Q4_K"]) - 11:.1f}" y="{mean_y + 4:.1f}" class="n" text-anchor="end">'
          f'{lab("experts-Q4_K")}</text>'
          f'<text x="{xs(m["Q4_K_M"]) + 11:.1f}" y="{mean_y + 4:.1f}" class="n">{lab("Q4_K_M")}</text>'
          f'<text x="{xs(m["MXFP4_MOE"]) + 10:.1f}" y="{mean_y + 4:.1f}" class="n" fill="{p["muted"]}">'
          f'{lab("MXFP4_MOE")}</text></g>')
    shown = dict(source='kl.csv', column='kld_mean', unit='nats', llama_cpp=d['llama'], x_axis=[0, XMAX],
                 chunks=d['chunks'],
                 tokens_scored=d['scored'], slices=d['slices'], groups={g: mem for g, mem in d['groups']},
                 kld_mean={f: d['kld'][f] for f in FORMATS}, mean_of_slices=m,
                 mean_labels={f: lab(f) for f in FORMATS}, experts_q4k_below_q4_k_m=f'{below} of {n}')
    title = f'llama.cpp mean KLD per held-out slice: experts-only Q4_K below Q4_K_M on {below} of {n}'
    desc = (f'Dot plot of kl.csv kld_mean for {n} slices and 4 formats. Means of the slices: '
            + ', '.join(f'{f} {lab(f)}' for f in FORMATS) + '.')
    return s.render(title, desc), shown


# --------------------------------------------------------------------------------------- (b) router agreement
def router_layers(theme: str, static: bool, d: dict):
    X0, X1, Y1, Y0, LO, HI = 84, 684, 166, 426, 0.5, 1.0
    L = d['n_layers']
    xs = lambda l: X0 + l / (L - 1) * (X1 - X0)
    ys = lambda v: Y0 - (v - LO) / (HI - LO) * (Y0 - Y1)
    ag = d['agree']
    assert LO <= min(min(v) for v in ag.values()) and max(max(v) for v in ag.values()) <= HI, 'layers.csv: off axis'
    s = Svg(theme, Y0 + 64, static); p = s.p
    header(s, f'QUANT_ERROR · OLMOE PILOT · TWIN FORWARD · LAYERS.CSV',
           'Under Q4_K_M the expert choice already changes at layer 0',
           f'Share of tokens whose top-8 expert set is exactly the bf16 one, per layer; mean over the '
           f'{len(d["slices"])} held-out slices')
    legend(s, 126, [('Q8_0', 36), ('Q4_K_M', 112), ('experts-Q4_K', 212), ('MXFP4_MOE', 348)], line=True)

    for t in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        s.add(f'<line x1="{X0}" y1="{ys(t):.1f}" x2="{X1}" y2="{ys(t):.1f}" stroke="{p["grid"]}"/>')
        s.text(X0 - 12, ys(t) + 3.5, f'{t:.1f}', 'ax', 'end')
    for l in range(L):
        s.text(xs(l), Y0 + 20, str(l), 'ax', 'middle')
    s.text(X1, Y0 + 40, 'layer →', 'ax', 'end')

    order = ['MXFP4_MOE', 'Q4_K_M', 'experts-Q4_K', 'Q8_0']          # Q8_0 last: on top where the lines meet
    for i, f in enumerate(order):
        col = p['series'][f]
        path = 'M' + ' L'.join(f'{xs(l):.1f},{ys(v):.1f}' for l, v in enumerate(ag[f]))
        dcls = '' if s.static else f' class="d" pathLength="1" style="animation-delay:{.2 + .18 * i:.2f}s"'
        s.add(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round" '
              f'stroke-linecap="round"{dcls}><title>{escape(f)}: ' + ' · '.join(f'layer {l} {v:.3f}' for l, v in
                                                                              enumerate(ag[f])) + '</title></path>')
    for i, f in enumerate(order):
        col = p['series'][f]
        a = s.anim('f', 1.2 + .1 * i)
        dots = ''.join(f'<circle cx="{xs(l):.1f}" cy="{ys(ag[f][l]):.1f}" r="5" fill="{col}" stroke="{p["bg"]}" '
                       f'stroke-width="2"><title>{escape(f)}, layer {l}: {ag[f][l]:.3f}</title></circle>'
                       for l in (0, L - 1))
        s.add(f'<g{a}>{dots}</g>')

    end = {f: f'{ag[f][-1]:.3f}' for f in FORMATS}
    a = s.anim('f', 1.7)
    labels = ''.join(f'<text x="{X1 + 16}" y="{ys(ag[f][-1]) + 4:.1f}" class="lab2">{escape(f)}</text>'
                     f'<text x="{W - 36}" y="{ys(ag[f][-1]) + 4:.1f}" class="n" text-anchor="end" '
                     f'fill="{p["muted"]}">{end[f]}</text>' for f in FORMATS)
    s.add(f'<g{a}>{labels}</g>')

    first = {f: f'{ag[f][0]:.3f}' for f in FORMATS}
    same = [f for f in FORMATS if f != 'Q4_K_M' and first[f] == first['Q8_0']]
    a = s.anim('f', 1.9)
    s.add(f'<g{a}><text x="{X0 + 12}" y="{ys(ag["Q8_0"][0]) - 14:.1f}" class="lab">'
          f'{first["Q8_0"]} · {escape(", ".join(same))}</text>'
          f'<text x="{X0 + 12}" y="{ys(ag["Q4_K_M"][0]) + 22:.1f}" class="lab">'
          f'{first["Q4_K_M"]} · Q4_K_M</text></g>')
    shown = dict(source='layers.csv', column='router_agree', aggregate=f'mean over the {len(d["slices"])} slices of '
                 'each format and layer', y_axis=[LO, HI], layers=list(range(L)), router_agree=ag,
                 layer0_labels=first, layer15_labels=end, layer0_same_as_q8_0=same)
    title = 'Router top-8 agreement with bf16 by layer, four formats'
    desc = ('Line chart of layers.csv router_agree, mean over the slices, layers 0 to 15. Layer 0: '
            + ', '.join(f'{f} {first[f]}' for f in FORMATS) + f'. Layer {L - 1}: '
            + ', '.join(f'{f} {end[f]}' for f in FORMATS) + '.')
    return s.render(title, desc), shown


FIGS = {'kld-slices': kld_slices, 'router-layers': router_layers}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--static', action='store_true', help='no animation (for previews)')
    ap.add_argument('--out', type=Path, default=HERE)
    a = ap.parse_args()
    d = load()
    a.out.mkdir(parents=True, exist_ok=True)
    values = {'note': 'Every number the figures plot or print, as make_figures.py reads or computes it from the CSVs '
                      'beside PILOT.md (means are plain means over the rows named).'}
    for name, fn in FIGS.items():
        for theme in PAL:
            svg, shown = fn(theme, a.static, d)
            (a.out / f'{name}-{theme}.svg').write_text(svg, encoding='utf-8')
        values[name] = shown
    (a.out / 'values.json').write_text(json.dumps(values, indent=1) + '\n', encoding='utf-8')
    print(f'wrote {2 * len(FIGS)} SVGs and values.json to {a.out}')


if __name__ == '__main__':
    main()
