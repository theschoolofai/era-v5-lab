"""Task 5 (G3, 28 Nov brief), the part on our own unit lists: FLORES-200 devtest for the unit lists that
`design_units_unseen.py train` writes, next to the frozen p1536. Same languages, word rule, encoding and lossless check
as `flores_task5.py` (its loader and language lists are reused), and the same FLORES files (sha256 checked against
`results/flores_task5.json`).

    python teams/03-tokenizer/harness/flores_ours.py --flores <flores200_dataset> --p1536 <p1536 tokenizer.json> \
        --ours <work>/ours --out teams/03-tokenizer/results/flores_task5_ours

FLORES reports on unit lists; it is not used to choose one. Our lists were trained on sample v0 (100 MB or 1 GB),
p1536 on corpus60 (#414).
"""
import argparse
import json
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flores_task5 as ft  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"
ORDER = ["plain 100MB 100k", "plain 1GB 100k", "SuperBPE 100MB t80k→100k", "SuperBPE 1GB t80k→100k",
         "SuperBPE 100MB t180k→200k"]


def name_of(f):
    return f.name[:-len(".tokenizer.json")].replace("-", "→").replace("_", " ")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--flores", type=Path, required=True)
    ap.add_argument("--p1536", type=Path, required=True)
    ap.add_argument("--ours", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--train-note", default="sample v0",
                    help="what the lists were trained on, for the caveat line")
    a = ap.parse_args()
    from tokenizers import Tokenizer
    if ft.sha(a.p1536) != ft.P1536:
        sys.exit("--p1536 is not the frozen p1536")
    toks = {"p1536 (frozen)": (ft.HF(Tokenizer.from_file(str(a.p1536))), {"sha256": ft.P1536})}
    found = {name_of(f): f for f in sorted(a.ours.glob("*.tokenizer.json"))}
    for n in sorted(found, key=lambda n: ORDER.index(n) if n in ORDER else 99):
        toks[n] = (ft.HF(Tokenizer.from_file(str(found[n]))), {"sha256": ft.sha(found[n]), "file": found[n].name})
    want = json.loads((RESULTS / "flores_task5.json").read_text(encoding="utf-8"))["flores"]
    langs = ft.INDIC + ft.OTHER
    texts = {}
    for code, fl in langs:
        f = a.flores / "devtest" / f"{fl}.devtest"
        h = ft.sha(f)
        if h != want[code]["sha256"]:
            sys.exit(f"{f}: sha256 {h} is not the file flores_task5.json used ({want[code]['sha256']})")
        texts[code] = f.read_text(encoding="utf-8").splitlines()
    res = {}
    for name, (t, meta) in toks.items():
        res[name] = {"meta": {**meta, "vocab": t.vocab}, "langs": {}}
        for code, _ in langs:
            ntok = nw = nb = ok = 0
            for s in texts[code]:
                ids = t.ids(s)
                ntok += len(ids)
                nw += len(s.split())
                nb += len(s.encode("utf-8"))
                ok += t.lossless(s, ids)
            res[name]["langs"][code] = {"tokens": ntok, "words": nw, "bytes": nb,
                                        "tokens_per_word": round(ntok / nw, 4), "bytes_per_token": round(nb / ntok, 3),
                                        "lossless": round(ok / len(texts[code]), 4)}
        ind = [res[name]["langs"][c]["tokens_per_word"] for c, _ in ft.INDIC]
        res[name]["indic_mean_tokens_per_word"] = round(sum(ind) / len(ind), 4)
        print(f"{name}: Indic mean tokens/word {res[name]['indic_mean_tokens_per_word']}", flush=True)
    out = {"train_note": a.train_note, "word_rule": "maximal runs of non-whitespace (str.split()); no word segmentation for Zh, Ja",
           "flores": {c: want[c] for c, _ in langs}, "tokenizers": res,
           "environment": {"python": platform.python_version(), "script_sha256": ft.sha(__file__),
                           "tokenizers": __import__("tokenizers").__version__}}
    a.out.with_suffix(".json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    write_md(out, langs, a.out.with_suffix(".md"))


def write_md(o, langs, path):
    R = o["tokenizers"]
    codes = [c for c, _ in langs]
    p = R["p1536 (frozen)"]["langs"]
    md = ["# FLORES-200 devtest: our own unit lists vs the frozen p1536 (Task 5)", "",
          "Made by `harness/flores_ours.py`, with the method of `flores_task5.py` (same FLORES files, sha256 checked). "
          "The unit lists are the ones in `design_units.md`, rebuilt by `design_units_unseen.py train` and written as "
          "standard `tokenizer.json` files (SuperBPE: the one-file form). FLORES reports on them; it does not choose one.",
          "", "- **Word rule (all languages):** " + o["word_rule"] + ".",
          "- **Encoding:** each of the 1,012 devtest sentences per language alone, `add_special_tokens=False`.",
          "- **Mean:** the 11 Indic languages (Hi … Or).",
          "- **Caveat:** our lists were trained on " + o["train_note"] + " (100 MB or 1 GB), p1536 on corpus60 (#414), "
          "with 131,072 ids against our 100k or 200k.", "",
          "## Tokens per word (lower is better)", "",
          "| Tokenizer | Ids | " + " | ".join(codes) + " | **Indic mean** |", "|---|---:|" + "---:|" * len(codes) + "---:|"]
    for n in R:
        md.append(f"| {n} | {R[n]['meta']['vocab']:,} | " +
                  " | ".join(f"{R[n]['langs'][c]['tokens_per_word']:.3f}" + ("*" if c in ft.NO_SPACES else "")
                             for c in codes) + f" | **{R[n]['indic_mean_tokens_per_word']:.3f}** |")
    md += ["", "\\* Chinese and Japanese have no spaces between words: read bytes per token there.", "",
           "## Tokens against p1536 (negative = fewer tokens than p1536)", "",
           "| Tokenizer | " + " | ".join(codes) + " | **Indic total** |", "|---|" + "---:|" * len(codes) + "---:|"]
    pin = sum(p[c]["tokens"] for c, _ in ft.INDIC)
    for n in R:
        if n == "p1536 (frozen)":
            continue
        L = R[n]["langs"]
        tin = sum(L[c]["tokens"] for c, _ in ft.INDIC)
        md.append(f"| {n} | " + " | ".join(f"{(L[c]['tokens'] / p[c]['tokens'] - 1) * 100:+.1f}%" for c in codes) +
                  f" | **{(tin / pin - 1) * 100:+.1f}%** |")
    md += ["", "## Bytes per token (higher is better)", "",
           "| Tokenizer | " + " | ".join(codes) + " |", "|---|" + "---:|" * len(codes)]
    for n in R:
        md.append(f"| {n} | " + " | ".join(f"{R[n]['langs'][c]['bytes_per_token']:.2f}" for c in codes) + " |")
    md += ["", "## Lossless (share of sentences where decode(encode(x)) equals x after the normalizer)", "",
           "| Tokenizer | " + " | ".join(codes) + " |", "|---|" + "---:|" * len(codes)]
    for n in R:
        md.append(f"| {n} | " + " | ".join(f"{R[n]['langs'][c]['lossless']:.3f}" for c in codes) + " |")
    md += ["", "## Files", "", "| Tokenizer | sha256 of the tokenizer.json |", "|---|---|"]
    md += [f"| {n} | `{R[n]['meta']['sha256'][:16]}…` |" for n in R]
    md += ["", "FLORES files: `flores200_dataset/devtest/<lang>.devtest`; sha256 values in the JSON."]
    path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[10:10 + len(R) + 2]))


if __name__ == "__main__":
    sys.exit(main())
