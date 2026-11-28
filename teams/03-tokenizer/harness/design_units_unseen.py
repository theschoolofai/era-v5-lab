"""Design task 2 (G3, 28 Nov brief): held-out units never seen in training, and what happens to them. Also writes the
standard tokenizer.json files of our unit lists, for Task 5 FLORES (`flores_ours.py`).

    python teams/03-tokenizer/harness/design_units.py prep --sample <sample v0> --work <dir>
    python teams/03-tokenizer/harness/design_units_unseen.py train  --work <dir> --p1536 <p1536 tokenizer.json> [--super-1gb]
    python teams/03-tokenizer/harness/design_units_unseen.py unseen --work <dir> --sample <sample v0> --p1536 <...> \
        --out teams/03-tokenizer/results/design_units_unseen

Same training text, same unit lists and the same held-out text as `design_units.py` (its prep, train_plain, train_super,
one_file and eval_text are reused unchanged). `train` builds only the lists this needs: plain BPE on 100 MB and 1 GB
(cut to 100k merges), SuperBPE (marks rule) on 100 MB at t80k→100k and t180k→200k, and with --super-1gb also on 1 GB at
t80k→100k (stage 2 on 1 GB took 46 min in 16 GB of RAM). Each list is written as one standard tokenizer.json:
`<work>/ours/<name>.tokenizer.json`. SuperBPE lists use the one-file form (`design_units.one_file`).

Two measures, per list, against the text that list was trained on (100 MB or 1 GB):
  units   every training doc is encoded with the list; a unit is "seen" if training text produces it at least once.
          On the held-out text: share of tokens that are unseen units, how many distinct ids, and which. Also the share
          of the vocabulary that training text never produces (a unit can be learned and still never be produced: it
          is always merged further).
  words   a held-out word (maximal non-whitespace run, str.split()) is "seen" if it occurs in the training text. Share
          of held-out word occurrences that are unseen, and what happens to them: tokens per word, and share of their
          tokens that are byte pieces (part of one character's UTF-8 bytes), seen vs unseen. Each distinct word is
          encoded alone with a leading space, as it is mid-sentence.
p1536 is shown for reference against the 1 GB set, but it was trained on corpus60 (#414), not on sample v0, so for p1536
"seen" means "seen in our 1 GB set", not in its own training text.
"""
import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "true")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_units as du  # noqa: E402

PLAIN = [("100MB", 100_000), ("1GB", 100_000)]
SUPER = [("100MB", 80_000, 100_000, "marks"), ("100MB", 180_000, 200_000, "marks")]
SUPER_1GB = ("1GB", 80_000, 100_000, "marks")
BATCH = 2000
SAMPLE_V0 = "0b7da76396a7078b07a5e5f96a4ced88279e77205c164a35f284f387b0546faa"   # sha256 of sample v0 SHA256SUMS
# design_units.json mean bytes/token over 12 domains (Soham's run), to check we rebuilt the same lists
EXPECT = {"plain 100MB 100k": 6.008, "plain 1GB 100k": 6.117, "SuperBPE 100MB t80k→100k": 6.458,
          "SuperBPE 100MB t180k→200k": 7.184, "SuperBPE 1GB t80k→100k": 6.596, "p1536 (frozen)": 5.952}


class Stream:
    """The docs of one training set, read from train_text.parquet in batches instead of held as one list (1 GB of
    text as Python strings plus the BPE trainer did not fit in 12 GB of RAM)."""

    def __init__(self, work, name):
        self.path, self.tier = Path(work) / "train_text.parquet", list(du.SETS).index(name)
        self.n = json.loads((Path(work) / "train_text.json").read_text())["sets"][name]["docs"]

    def __len__(self):
        return self.n

    def batches(self, size=BATCH):
        import pyarrow.parquet as pq
        f = pq.ParquetFile(self.path)
        for b in f.iter_batches(batch_size=size, columns=["tier", "text"]):
            t, x = b.column(0).to_pylist(), b.column(1).to_pylist()
            yield [d for i, d in zip(t, x) if i <= self.tier]

    def __iter__(self):
        for b in self.batches():
            yield from b


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def plain_name(s, k):
    return f"plain {s} {k // 1000}k"


def super_name(s, T, total):
    return f"SuperBPE {s} t{T // 1000}k→{total // 1000}k"


def file_name(n):
    return n.replace(" ", "_").replace("→", "-") + ".tokenizer.json"


def train(a):
    work = Path(a.work)
    ours = work / "ours"
    ours.mkdir(exist_ok=True)
    base = json.loads(du.from_p1536(a.p1536).to_str())
    if a.max_merges:      # only the first 100k (plain) or 180k (SuperBPE stage 1) merges are used; a BPE prefix is a BPE
        du.MAX_MERGES = {k: a.max_merges for k in du.MAX_MERGES}
    texts = du.texts
    for s, k in PLAIN:
        if a.only_100mb and s != "100MB":
            continue
        du.texts = Stream             # train_plain reads the training docs as a stream (train_super slices a list)
        du.train_plain(a.work, s, a.p1536)
        du.texts = texts
        d = json.loads((work / f"plain_{s}.json").read_text())
        alphabet = [t for t, i in sorted(d["model"]["vocab"].items(), key=lambda x: x[1])][:256]
        merges = [tuple(m) for m in d["model"]["merges"]][:k]
        (ours / file_name(plain_name(s, k))).write_text(json.dumps(du.bpe_json(base, merges, alphabet),
                                                                   ensure_ascii=False))
    for s, T, total, rule in SUPER + ([SUPER_1GB] if a.super_1gb else []):
        du.train_super(a.work, s, T, total, rule)
        f = work / f"super_{s}_t{T // 1000}k_{total // 1000}k_{rule}.json"
        if f.exists():
            (ours / file_name(super_name(s, T, total))).write_text(
                json.dumps(du.one_file(json.loads(f.read_text()), rule), ensure_ascii=False))
    for f in sorted(ours.glob("*.tokenizer.json")):
        log("wrote", f, du.sha(f)[:16])


def lists(a):
    work = Path(a.work) / "ours"
    out = [("p1536 (frozen)", Path(a.p1536), "1GB")]
    for s, k in PLAIN:
        out.append((plain_name(s, k), work / file_name(plain_name(s, k)), s))
    for s, T, total, _ in SUPER + [SUPER_1GB]:
        n = super_name(s, T, total)
        out.append((n, work / file_name(n), s))
    return [x for x in out if x[1].exists()]


def unseen(a):
    import numpy as np
    from tokenizers import Tokenizer
    if du.sha(a.p1536) != du.P1536:
        sys.exit("--p1536 is not the frozen p1536")
    ev = {k: v for k, v in du.eval_text(a.sample).items() if v}       # a stand-in sample may lack some domains
    soham = du.sha(Path(a.sample) / "SHA256SUMS") == SAMPLE_V0
    src = Path(a.sample) / "SOURCE.json"
    source = json.loads(src.read_text()) if src.exists() else {"kind": "sample v0"}
    words = {}                                    # held-out word -> occurrences, over all domains
    for docs in ev.values():
        for x in docs:
            for w in x.split():
                words[w] = words.get(w, 0) + 1
    seen_words = {}                               # train set -> set of held-out words seen in it
    for s in sorted({s for _, _, s in lists(a)}):
        log(f"scanning {s} training text for held-out words")
        seen, n = set(), 0
        for x in Stream(a.work, s):
            for w in x.split():
                if w in words:
                    seen.add(w)
            n += 1
        seen_words[s] = seen
        log(f"{s}: {n:,} docs, {len(seen):,} of {len(words):,} distinct held-out words seen")
    res = {}
    for name, path, s in lists(a):
        tok = Tokenizer.from_file(str(path))
        V = tok.get_vocab_size()
        log(f"{name}: encoding the {s} training text")
        count = np.zeros(V, dtype=np.int64)
        t0 = time.time()
        for b in Stream(a.work, s).batches():
            enc = tok.encode_batch(b, add_special_tokens=False)
            count += np.bincount(np.fromiter((i for e in enc for i in e.ids), dtype=np.int64), minlength=V)
        train_secs = time.time() - t0
        partial = np.array(["�" in t for t in tok.decode_batch([[i] for i in range(V)])])
        units = {}
        tot = {"tokens": 0, "unseen_tokens": 0, "bytes": 0}
        held = np.zeros(V, dtype=np.int64)
        for dom, dd in ev.items():
            enc = tok.encode_batch(dd, add_special_tokens=False)
            c = np.bincount(np.fromiter((i for e in enc for i in e.ids), dtype=np.int64), minlength=V)
            held += c
            ntok, un = int(c.sum()), int(c[count == 0].sum())
            nb = sum(len(x.encode()) for x in dd)
            units[dom] = {"tokens": ntok, "unseen_unit_tokens": un, "unseen_share": round(un / ntok, 6),
                          "distinct_unseen_ids": int(((c > 0) & (count == 0)).sum()),
                          "bytes_per_token": round(nb / ntok, 3)}
            tot["tokens"] += ntok
            tot["unseen_tokens"] += un
        un_held = held * (count == 0)
        top = np.argsort(-un_held)[:15]
        top = [{"unit": tok.decode([int(i)]), "id": int(i), "held_out": int(held[i])} for i in top if un_held[i] > 0]
        # words: encode each distinct held-out word alone, with a leading space
        wl = list(words)
        wtok, wpart = {}, {}
        for k in range(0, len(wl), 20000):
            for w, e in zip(wl[k:k + 20000], tok.encode_batch([" " + w for w in wl[k:k + 20000]],
                                                              add_special_tokens=False)):
                wtok[w] = len(e.ids)
                wpart[w] = int(partial[e.ids].sum()) if e.ids else 0
        sw = seen_words[s]
        wr = {}
        for dom, dd in ev.items():
            acc = {True: [0, 0, 0], False: [0, 0, 0]}        # occurrences, tokens, byte-piece tokens
            for x in dd:
                for w in x.split():
                    r = acc[w in sw]
                    r[0] += 1
                    r[1] += wtok[w]
                    r[2] += wpart[w]
            occ = acc[True][0] + acc[False][0]
            wr[dom] = {"words": occ, "unseen_words": acc[False][0], "unseen_share": round(acc[False][0] / occ, 6),
                       "tokens_per_word_seen": round(acc[True][1] / max(acc[True][0], 1), 4),
                       "tokens_per_word_unseen": round(acc[False][1] / max(acc[False][0], 1), 4),
                       "byte_piece_share_seen": round(acc[True][2] / max(acc[True][1], 1), 4),
                       "byte_piece_share_unseen": round(acc[False][2] / max(acc[False][1], 1), 4)}
        mean_bpt = sum(u["bytes_per_token"] for u in units.values()) / len(units)
        res[name] = {"file_sha256": du.sha(path), "vocab": V, "train_set": s,
                     "vocab_never_produced_on_train": int((count == 0).sum()),
                     "vocab_never_produced_share": round(float((count == 0).mean()), 4),
                     "heldout_unseen_unit_share": round(tot["unseen_tokens"] / tot["tokens"], 6),
                     "mean_bytes_per_token": round(mean_bpt, 3), "expected_mean_bytes_per_token": EXPECT.get(name) if soham else None,
                     "units": units, "words": wr, "top_unseen_units": top,
                     "train_encode_seconds": round(train_secs, 1)}
        log(f"{name}: held-out unseen-unit share {res[name]['heldout_unseen_unit_share']:.4%}, mean bytes/token "
            f"{mean_bpt:.3f} (design_units.json: {EXPECT.get(name)})")
    out = {"train_text": json.loads((Path(a.work) / "train_text.json").read_text()), "sample_is_v0": soham,
           "source": source,
           "domains": {k: {"docs": len(v), "bytes": sum(len(x.encode()) for x in v)} for k, v in ev.items()},
           "distinct_heldout_words": len(words), "lists": res,
           "environment": {"python": platform.python_version(), "machine": platform.machine(), "cpus": os.cpu_count(),
                           "tokenizers": __import__("tokenizers").__version__, "script_sha256": du.sha(__file__),
                           "design_units_sha256": du.sha(du.__file__)}}
    Path(a.out).with_suffix(".json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    report(out, Path(a.out).with_suffix(".md"))


def report(o, path):
    R = o["lists"]
    doms = list(o["domains"])   # only domains with held-out text
    short = [d.split(" ")[0] for d in doms]
    tt = o["train_text"]

    def mean(n, part, key):
        return sum(R[n][part][d][key] for d in doms) / len(doms)

    if o["sample_is_v0"]:
        data = ("Same training sets, unit lists and held-out text as `design_units.md` (sample v0 `SHA256SUMS` sha256 `" +
                tt["sample_sha256sums"][:16] + "…`).")
    else:
        P = o["source"].get("packs", {})
        data = ("**Not sample v0.** Training and held-out text are a public stand-in built by `build_public_sample.py`: "
                "FineWeb-2 (11 Indic languages and Sanskrit) and FineWeb-Edu (English), " +
                ", ".join(f"{k} {v['train_bytes'] / 1e6:.0f} MB" for k, v in P.items()) +
                ". No code, math or science text, so only the domains below are measured. The method and training "
                "settings are those of `design_units.py` (its prep, train_plain, train_super and one_file, unchanged), "
                "but the lists differ from the ones in `design_units.md`, and these numbers are not comparable with "
                "it one to one.")
    md = ["# Design task 2: held-out units and words never seen in training", "",
          "Made by `harness/design_units_unseen.py`; numbers in `" + path.with_suffix(".json").name + "`. " + data, "",
          "- **Unseen unit:** a unit that the list's own training text (100 MB or 1 GB) never produces when encoded with "
          "that list.",
          "- **Unseen word:** a held-out word (maximal non-whitespace run) that never occurs in the training text.",
          "- **Byte piece:** a token that is only part of one character's UTF-8 bytes.",
          "- **p1536** is measured against our 1 GB set for reference only: it was trained on corpus60 (#414), not on "
          "this text.", f"- **Mean:** plain average over the {len(doms)} domains measured.", "",
          "## Headline", "",
          "| Unit list | Ids | Trained on | Ids never produced on training text | Held-out tokens that are unseen units | "
          "Held-out words unseen | Tokens/word seen → unseen | Byte pieces seen → unseen | Mean bytes/token (check) |",
          "|---|---:|---|---:|---:|---:|---|---|---:|"]
    for n, r in R.items():
        md.append(f"| {n} | {r['vocab']:,} | {r['train_set']} | {r['vocab_never_produced_share'] * 100:.1f}% | "
                  f"{r['heldout_unseen_unit_share'] * 100:.3f}% | {mean(n, 'words', 'unseen_share') * 100:.1f}% | "
                  f"{mean(n, 'words', 'tokens_per_word_seen'):.2f} → {mean(n, 'words', 'tokens_per_word_unseen'):.2f} | "
                  f"{mean(n, 'words', 'byte_piece_share_seen') * 100:.1f}% → "
                  f"{mean(n, 'words', 'byte_piece_share_unseen') * 100:.1f}% | {r['mean_bytes_per_token']:.3f}"
                  + (f" ({r['expected_mean_bytes_per_token']:.3f})" if r["expected_mean_bytes_per_token"] else "") + " |")
    md += ["", "Check column: mean bytes/token on the held-out text" + (", and in brackets the same list in "
           "`design_units.json`. Equal values mean the lists were rebuilt exactly." if o["sample_is_v0"] else "."), "",
           "## Held-out tokens that are unseen units, by domain", "",
           "| Unit list | " + " | ".join(short) + " |", "|---|" + "---:|" * len(doms)]
    for n in R:
        md.append(f"| {n} | " + " | ".join(f"{R[n]['units'][d]['unseen_share'] * 100:.3f}%" for d in doms) + " |")
    md += ["", "## Held-out words never seen in training, by domain (share of word occurrences)", "",
           "| Unit list | " + " | ".join(short) + " |", "|---|" + "---:|" * len(doms)]
    for n in R:
        md.append(f"| {n} | " + " | ".join(f"{R[n]['words'][d]['unseen_share'] * 100:.1f}%" for d in doms) + " |")
    md += ["", "## What happens to unseen words: tokens per word, seen / unseen", "",
           "| Unit list | " + " | ".join(short) + " |", "|---|" + "---:|" * len(doms)]
    for n in R:
        md.append(f"| {n} | " + " | ".join(f"{R[n]['words'][d]['tokens_per_word_seen']:.2f} / "
                                          f"{R[n]['words'][d]['tokens_per_word_unseen']:.2f}" for d in doms) + " |")
    md += ["", "## What happens to unseen words: byte-piece share of their tokens, seen / unseen", "",
           "| Unit list | " + " | ".join(short) + " |", "|---|" + "---:|" * len(doms)]
    for n in R:
        md.append(f"| {n} | " + " | ".join(f"{R[n]['words'][d]['byte_piece_share_seen'] * 100:.1f}% / "
                                          f"{R[n]['words'][d]['byte_piece_share_unseen'] * 100:.1f}%" for d in doms) + " |")
    md += ["", "## Most frequent unseen units on held-out text", ""]
    for n, r in R.items():
        md.append(f"- **{n}:** " + (", ".join(f"`{json.dumps(u['unit'], ensure_ascii=False)[1:-1].replace('`', 'ˋ')}` "
                                              f"({u['held_out']})" for u in r["top_unseen_units"][:10]) or "none"))
    md += ["", "## Files", "", "| Unit list | tokenizer.json sha256 |", "|---|---|"]
    md += [f"| {n} | `{r['file_sha256'][:16]}…` |" for n, r in R.items()]
    md += ["", f"Environment: Python {o['environment']['python']}, tokenizers {o['environment']['tokenizers']}, "
           f"{o['environment']['machine']}, {o['environment']['cpus']} CPUs."]
    path.write_text("\n".join(md) + "\n", encoding="utf-8")
    log("wrote", path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=["train", "unseen"])
    ap.add_argument("--work", required=True)
    ap.add_argument("--sample")
    ap.add_argument("--p1536", required=True)
    ap.add_argument("--super-1gb", action="store_true")
    ap.add_argument("--only-100mb", action="store_true", help="train only the 100 MB lists")
    ap.add_argument("--max-merges", type=int, help="learn at most this many merges per plain list (default: design_units)")
    ap.add_argument("--out")
    a = ap.parse_args()
    {"train": train, "unseen": unseen}[a.step](a)


if __name__ == "__main__":
    sys.exit(main())
