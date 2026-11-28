"""What every quant_error figure shares: surfaces, palette, fonts, motion and the SVG writer.

Used by figures/make_figures.py (the README's figures) and by results/*/figures/make_figures.py. The look follows
Team 12's serving notes (serving/kv_cache/, serving/sglang/): soft surfaces, Inter for text and JetBrains Mono for
numbers (SIL Open Font License 1.1, see OFL.txt), one quiet fade or draw-in that plays once and only under
prefers-reduced-motion: no-preference. GitHub shows an SVG as an image, which loads no outside font, so each SVG
embeds a subset of fonts/*.woff2 holding only the glyphs it uses.

The four series colours (navy, brass, green, red; navy and brass as in serving/sglang/) passed palette checks on both
surfaces of each theme, for all pairs, since the pilot's four formats share one plot: lightness band, chroma floor,
colour-blind (protan, deutan) and normal-vision separation, and contrast.

Needs fonttools and brotli (pip install fonttools==4.68.0 brotli==1.2.1); with these versions a rerun reproduces
the SVGs byte for byte. build_fonts() remakes fonts/*.woff2 from the google/fonts files named in FONT_SOURCES.
"""
from __future__ import annotations

import base64, hashlib, html, io
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / 'fonts'
W = 880

PAL = {
    'light': dict(bg='#FBFAF7', card='#FFFFFF', line='#E6E1D6', ink='#1C1B19', muted='#6F695F', grid='#EEEAE1',
                  accent='#A08B63', link='#D8D2C6', soft='#F3F0E9',
                  navy='#2E558F', brass='#B8892D', green='#1C9273', red='#A3423E'),
    'dark': dict(bg='#0F1115', card='#15181D', line='#272B33', ink='#ECE8E0', muted='#9A958A', grid='#21252C',
                 accent='#B9A27A', link='#3A3F48', soft='#1B1F25',
                 navy='#6090D8', brass='#B58629', green='#009775', red='#A74541'),
}
SANS_STACK = "'G12 Inter', Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO_STACK = "'G12 Mono', 'JetBrains Mono', 'SF Mono', ui-monospace, Menlo, Consolas, monospace"
MONO_CLASSES = {'n', 'nb', 'big', 'ax', 'sl', 'file'}

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
            raise SystemExit(f'{family}: no glyph for {sorted(missing)}; add them to CHARSET and run build_fonts')
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
        """class and delay of a fade ('f'), show ('s'), grow ('g') or draw ('d'); nothing in --static."""
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
               f'.t{{font-size:21px;font-weight:600;letter-spacing:-.012em}}.t.lg{{font-size:24px}}'
               f'.st{{font-size:12.5px;fill:{p["muted"]}}}'
               f'.cap{{font-size:10px;font-weight:600;letter-spacing:.14em;fill:{p["muted"]}}}'
               f'.lab{{font-size:12px;fill:{p["muted"]}}}'
               f'.lab2{{font-size:12.5px;font-weight:500}}'
               f'.n{{font-family:{MONO_STACK};font-size:11.5px;font-variant-numeric:tabular-nums}}'
               f'.nb{{font-family:{MONO_STACK};font-size:12px;font-weight:500;font-variant-numeric:tabular-nums}}'
               f'.file{{font-family:{MONO_STACK};font-size:14px;font-weight:500}}'
               f'.sl{{font-family:{MONO_STACK};font-size:11px;fill:{p["muted"]}}}'
               f'.big{{font-family:{MONO_STACK};font-size:32px;font-weight:500;letter-spacing:-.02em}}'
               f'.ax{{font-family:{MONO_STACK};font-size:10.5px;fill:{p["muted"]};font-variant-numeric:tabular-nums}}'
               + motion)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" viewBox="0 0 {W} {self.h}" '
                f'role="img" aria-labelledby="t d"><title id="t">{html.escape(title)}</title>'
                f'<desc id="d">{html.escape(desc)}</desc><style>{css}</style>'
                f'<rect x=".5" y=".5" width="{W - 1}" height="{self.h - 1}" rx="16" fill="{p["bg"]}" stroke="{p["line"]}"/>'
                + ''.join(self.parts) + '</svg>\n')


def header(s: Svg, kicker: str, title: str, sub: str):
    s.text(36, 44, kicker, 'cap')
    s.text(36, 72, title, 't')
    s.text(36, 94, sub, 'st')


def dot(s: Svg, x, y, col, r=5.0, extra=''):
    """A filled marker with a 2px ring in the surface colour."""
    s.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}" stroke="{s.p["bg"]}" stroke-width="2"{extra}/>')


def tile(s: Svg, x, y, w, h, col, cap, big, l1, l2, delay, big_cls='big'):
    """A stat tile: caption, one figure, two lines; a thin accent strip on the left carries the colour."""
    p = s.p
    s.add(f'<g{s.anim("f", delay)}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{p["card"]}" '
          f'stroke="{p["line"]}"/><rect x="{x}" y="{y + 20}" width="3" height="{h - 40}" rx="1.5" fill="{col}"/></g>')
    d = f'f@{delay + .1:.2f}'
    s.text(x + 22, y + 32, cap, 'cap', wrap=d)
    s.text(x + 22, y + 74, big, big_cls, wrap=d)
    s.text(x + 22, y + 95, l1, 'lab', wrap=d)
    s.text(x + 22, y + 111, l2, 'n', fill=p['muted'], wrap=d)
