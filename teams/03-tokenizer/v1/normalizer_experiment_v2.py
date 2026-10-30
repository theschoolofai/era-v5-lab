"""
G3 Tokenizer, v1 idea 2 (round 2): NFC + old-chillu -> atomic chillu, without the nukta penalty.

Round 1 showed plain NFC makes clean Bengali/Assamese/Punjabi WORSE, because NFC
splits "nukta" letters (ড় য় ਸ਼ ...) into letter + dot, and the tokenizer learned
the one-character forms. Fix tested here: after NFC, join those letters back
("keep-nukta"). NFC still fixes everything else (NFD input, split vowel signs).

Variants
  baseline              no normalizer (today)
  chillu                old-style Malayalam chillu -> atomic chillu
  nfc+chillu            the spec as written
  nfc+chillu+nukta      spec + re-join nukta letters in all 4 affected scripts
  nfc+chillu+nukta-BnPa spec + re-join only for Bengali and Gurmukhi

Inputs (FLORES-200 dev+devtest)
  clean      the text as published
  NFD        the same text in decomposed Unicode (how some keyboards/sites store it)
  old-chillu Malayalam only, rewritten with old-style chillus (consonant+virama+ZWJ)

Fertility = tokens / whitespace words of the ORIGINAL clean text, so all inputs
are compared on the same word count. Round trip: decode(encode(x)) == normalize(x).

Run from the BrahmicTokenizer-131K repo root:
    python normalizer_experiment_v2.py --out C:/tmp/v1_norm2 --save nfc+chillu+nukta
"""
import argparse
import hashlib
import os
import statistics
import unicodedata as ud

from tokenizers import Tokenizer, normalizers

LANGS = [
    ("En", "eng_Latn"), ("Hi", "hin_Deva"), ("Bn", "ben_Beng"), ("Ta", "tam_Taml"),
    ("Te", "tel_Telu"), ("Kn", "kan_Knda"), ("Ml", "mal_Mlym"), ("Mr", "mar_Deva"),
    ("Gu", "guj_Gujr"), ("Pa", "pan_Guru"), ("Or", "ory_Orya"), ("As", "asm_Beng"),
]
INDIC = [s for s, _ in LANGS if s != "En"]

VIRAMA, ZWJ = "\u0D4D", "\u200D"
CHILLU = {"\u0D23": "\u0D7A", "\u0D28": "\u0D7B", "\u0D30": "\u0D7C",
          "\u0D32": "\u0D7D", "\u0D33": "\u0D7E", "\u0D15": "\u0D7F"}

SCRIPT_RANGES = {"Deva": (0x0900, 0x097F), "Beng": (0x0980, 0x09FF),
                 "Guru": (0x0A00, 0x0A7F), "Orya": (0x0B00, 0x0B7F)}


def nukta_letters(scripts):
    """One-character letters that NFC splits apart (Unicode composition exclusions)."""
    out = []
    for sc in scripts:
        lo, hi = SCRIPT_RANGES[sc]
        for cp in range(lo, hi + 1):
            c = chr(cp)
            if ud.normalize("NFC", c) != c:
                out.append(c)
    return out


def chillu_rules():
    return [normalizers.Replace(c + VIRAMA + ZWJ, a) for c, a in CHILLU.items()]


def rejoin_rules(scripts):
    return [normalizers.Replace(ud.normalize("NFD", c), c) for c in nukta_letters(scripts)]


VARIANTS = {
    "baseline": None,
    "chillu": normalizers.Sequence(chillu_rules()),
    "nfc+chillu": normalizers.Sequence([normalizers.NFC()] + chillu_rules()),
    "nfc+chillu+nukta": normalizers.Sequence(
        [normalizers.NFC()] + chillu_rules() + rejoin_rules(["Deva", "Beng", "Guru", "Orya"])),
    "nfc+chillu+nukta-BnPa": normalizers.Sequence(
        [normalizers.NFC()] + chillu_rules() + rejoin_rules(["Beng", "Guru"])),
}


def to_old_chillu(s):
    for c, a in CHILLU.items():
        s = s.replace(a, c + VIRAMA + ZWJ)
    return s


def load_flores(root):
    data = {}
    for short, code in LANGS:
        lines = []
        for split in ("dev", "devtest"):
            with open(os.path.join(root, split, f"{code}.{split}"), encoding="utf-8") as f:
                lines += [l.rstrip("\n") for l in f]
        data[short] = lines
    return data


def fertility(tok, lines, words):
    return sum(len(tok.encode(l, add_special_tokens=False).ids) for l in lines) / words


def rt_fail(tok, norm, lines):
    bad = 0
    for l in lines:
        target = norm.normalize_str(l) if norm else l
        bad += tok.decode(tok.encode(l, add_special_tokens=False).ids, skip_special_tokens=False) != target
    return bad


def pct(new, old):
    return f"{new:.4f} ({100 * (new / old - 1):+.2f}%)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", default="tokenizer.json")
    ap.add_argument("--flores", default="/tmp/flores200_dataset")
    ap.add_argument("--out", required=True)
    ap.add_argument("--save", default="nfc+chillu+nukta", choices=[k for k in VARIANTS if k != "baseline"])
    a = ap.parse_args()

    clean = load_flores(a.flores)
    words = {s: sum(len(l.split()) for l in lines) for s, lines in clean.items()}
    nfd = {s: [ud.normalize("NFD", l) for l in lines] for s, lines in clean.items()}
    old_ml = [to_old_chillu(l) for l in clean["Ml"]]

    tok = Tokenizer.from_file(a.tokenizer)
    R = {}
    for name, norm in VARIANTS.items():
        tok.normalizer = norm
        R[name] = {
            "clean": {s: fertility(tok, clean[s], words[s]) for s in clean},
            "nfd": {s: fertility(tok, nfd[s], words[s]) for s in clean},
            "old_ml": fertility(tok, old_ml, words["Ml"]),
            "rt": {s: rt_fail(tok, norm, clean[s]) for s in clean},
        }
        print(f"done: {name}")

    names = list(VARIANTS)
    for key, title in (("clean", "A. Clean FLORES (as published)"),
                       ("nfd", "B. Same text in NFD (decomposed) Unicode")):
        base = R["baseline"][key]
        print(f"\n## {title}: fertility, % vs baseline on clean text\n")
        print("| Lang | " + " | ".join(names) + " |")
        print("|---|" + "---|" * len(names))
        ref = R["baseline"]["clean"]
        for s, _ in LANGS:
            print(f"| {s} | " + " | ".join(pct(R[n][key][s], ref[s]) for n in names) + " |")
        mref = statistics.mean(ref[s] for s in INDIC)
        print("| **Mean Brahmic** | " + " | ".join(
            "**" + pct(statistics.mean(R[n][key][s] for s in INDIC), mref) + "**" for n in names) + " |")

    ref = R["baseline"]["clean"]["Ml"]
    print("\n## C. Malayalam written with old-style chillus: fertility, % vs baseline on clean text\n")
    print("| | " + " | ".join(names) + " |")
    print("|---|" + "---|" * len(names))
    print("| Ml (old chillu) | " + " | ".join(pct(R[n]["old_ml"], ref) for n in names) + " |")

    print("\n## D. Round-trip failures on clean text (of 2,009 lines per language)\n")
    print("| Lang | " + " | ".join(names[1:]) + " |")
    print("|---|" + "---|" * (len(names) - 1))
    for s, _ in LANGS:
        print(f"| {s} | " + " | ".join(str(R[n]["rt"][s]) for n in names[1:]) + " |")

    os.makedirs(a.out, exist_ok=True)
    tok.normalizer = VARIANTS[a.save]
    path = os.path.join(a.out, "tokenizer.json")
    tok.save(path)
    print(f"\nSaved '{a.save}' to {path}")
    print("sha256 ", hashlib.sha256(open(path, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
