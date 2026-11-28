"""Task 00 (extreme compression, joint with Team 4), G3 side: SuperBPE stage 2 on top of the frozen p1536.

Stage 1 is p1536 unchanged (ids 0..131071 keep their meaning). Stage 2 learns new units, each a sequence of p1536 ids, that
may cross spaces (SuperBPE, arXiv 2503.13423), with the "marks" split rule from #887 (Indic vowel signs and virama stay
with letters) and a unit cap of 32 bytes (64 for one comparison point). New units get ids from 131072 up.

Data: public text only (not sample v0). Per domain, consecutive documents after exact dedup:
  C  held-out  first EVAL_BYTES    (never used for anything but scoring)
  B  model     next  MODEL_BYTES   (stand-in for the model's training text: which units the model would see)
  A  dict      next  DICT_BYTES    (stage-2 merges are learned here only)

Per unit list and domain, on C: bytes per token, tokens per word, tokens vs p1536, lossless share.
Unseen units: share of C positions whose unit never occurs in B (B cut at 1/5 and all of it, to show the trend).
Backoff: the same C text when every new unit seen fewer than m times in B is written as its p1536 spelling (lossless).
Scoring cost: head size N, logits per byte relative to p1536 = (N / 131072) * (p1536 tokens / tokens), and the shortlist
size K (most frequent units in B first) that covers 99% / 99.9% of C positions.

Run (Colab, CPU is enough):
  pip install -q tokenizers==0.23.3 regex pyarrow huggingface_hub gdown
  python task00_units.py --p1536 tokenizer.json --out out/
"""
import argparse, collections, gzip, hashlib, io, json, os, sys, time
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "true")

P1536 = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"
BASE_CP = 0x10000
STAGE2 = r"\p{N}{1,3}| ?[^\s\p{L}\p{M}\p{N}]{2,}[\r\n/]*| +(?!\S)"   # "marks" rule from #887
EVAL_BYTES, MODEL_BYTES, DICT_BYTES = 1_000_000, 5_000_000, 8_000_000
EXTRA = 1_000_000                                   # stage-2 merges asked of the trainer (before the byte cap)
LISTS = [(262_144, 32), (524_288, 32), (1_048_576, 32), (1_048_576, 64)]   # (total ids, unit cap in bytes)
FW2 = "datasets/HuggingFaceFW/fineweb-2/data/{}/train"
DOMAINS = {   # name: (repo folder, text column candidates)
    "en-web": ("datasets/HuggingFaceFW/fineweb-edu/sample/10BT", ["text"]),
    "math": ("datasets/HuggingFaceTB/finemath/finemath-4plus", ["text"]),
    "code-python": ("datasets/codeparrot/codeparrot-clean-valid", ["content", "text", "code"]),
    "hi": (FW2.format("hin_Deva"), ["text"]),
    "mr": (FW2.format("mar_Deva"), ["text"]),
    "bn": (FW2.format("ben_Beng"), ["text"]),
    "ta": (FW2.format("tam_Taml"), ["text"]),
    "te": (FW2.format("tel_Telu"), ["text"]),
    "sa": (FW2.format("san_Deva"), ["text"]),
}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- data
def rows(folder, cols):
    from huggingface_hub import HfFileSystem
    import pyarrow.parquet as pq
    fs = HfFileSystem()
    files = sorted(f for f in fs.find(folder) if f.endswith((".parquet", ".json.gz", ".jsonl", ".jsonl.gz", ".json")))
    for f in files:
        if f.endswith(".parquet"):
            with fs.open(f, "rb") as fh:
                pf = pq.ParquetFile(fh)
                col = next(c for c in cols if c in pf.schema_arrow.names)
                for rg in range(pf.num_row_groups):
                    yield from pf.read_row_group(rg, columns=[col]).column(col).to_pylist()
        else:
            with fs.open(f, "rb") as fh:
                data = fh.read()
            if f.endswith(".gz"):
                data = gzip.decompress(data)
            txt = data.decode("utf-8")
            items = json.loads(txt) if txt.lstrip().startswith("[") else (json.loads(l) for l in txt.splitlines() if l.strip())
            for d in items:
                c = next((c for c in cols if c in d), None)
                if c:
                    yield d[c]


def load(folder, cols):
    seen, parts, sizes = set(), {"C": [], "B": [], "A": []}, {"C": 0, "B": 0, "A": 0}
    caps = {"C": EVAL_BYTES, "B": MODEL_BYTES, "A": DICT_BYTES}
    order = ["C", "B", "A"]
    k = 0
    for t in rows(folder, cols):
        if not t or not t.strip():
            continue
        h = hashlib.sha256(t.encode("utf-8", "surrogatepass")).digest()
        if h in seen:
            continue
        seen.add(h)
        n = len(t.encode("utf-8", "surrogatepass"))
        parts[order[k]].append(t)
        sizes[order[k]] += n
        if sizes[order[k]] >= caps[order[k]]:
            k += 1
            if k == 3:
                break
    return parts, sizes


# ---------------------------------------------------------------- tokenizers
class Two:
    """Stage 1 = p1536, stage 2 = character BPE over p1536 ids written as chr(BASE_CP + id)."""

    def __init__(self, p, s2=None):
        from tokenizers import Regex, pre_tokenizers
        self.p, self.s2 = p, s2
        self.split = pre_tokenizers.Split(Regex(STAGE2), behavior="isolated")
        self.v1 = p.get_vocab_size(with_added_tokens=True)
        if s2 is not None:
            inv = {i: t for t, i in s2.get_vocab().items()}
            self.units = [[ord(c) - BASE_CP for c in inv[i]] for i in range(len(inv))]

    def norm(self, x):
        return self.p.normalizer.normalize_str(x) if self.p.normalizer else x

    def chunks(self, docs):
        out, owner = [], []
        for j, x in enumerate(docs):
            for piece, _ in self.split.pre_tokenize_str(self.norm(x)):
                out.append(piece)
                owner.append(j)
        return out, owner

    def mapped(self, docs):
        ch, owner = self.chunks(docs)
        enc = self.p.encode_batch(ch, add_special_tokens=False)
        return ["".join(chr(BASE_CP + i) for i in e.ids) for e in enc], owner

    def encode(self, docs, step=2000):
        res = [[] for _ in docs]
        for k in range(0, len(docs), step):
            m, owner = self.mapped(docs[k:k + step])
            if self.s2 is None:
                for j, s in zip(owner, m):
                    res[k + j].extend(ord(c) - BASE_CP for c in s)
            else:
                for j, e in zip(owner, self.s2.encode_batch(m, add_special_tokens=False)):
                    res[k + j].extend(e.ids)
        return res

    def decode(self, ids):
        flat = ids if self.s2 is None else [i for u in ids for i in self.units[u]]
        return self.p.decode(flat, skip_special_tokens=False)


def train_stage2(two, docs):
    from tokenizers import Tokenizer, models, trainers

    def gen():
        for k in range(0, len(docs), 2000):
            m, _ = two.mapped(docs[k:k + 2000])
            for s in m:
                if len(s) > 1:
                    yield s

    s2 = Tokenizer(models.BPE())
    tr = trainers.BpeTrainer(vocab_size=two.v1 + EXTRA, min_frequency=2, show_progress=False, limit_alphabet=two.v1,
                             initial_alphabet=[chr(BASE_CP + i) for i in range(two.v1)])
    t0 = time.time()
    s2.train_from_iterator(gen(), trainer=tr)
    merges = [tuple(m) for m in json.loads(s2.to_str())["model"]["merges"]]
    return merges, time.time() - t0


def build(two, merges, total, cap, unit_bytes):
    """First (total - v1) stage-2 merges whose unit is at most cap bytes (later merges on a dropped unit are longer too)."""
    from tokenizers import Tokenizer
    vocab = {chr(BASE_CP + i): i for i in range(two.v1)}
    keep = []
    for l, r in merges:
        if unit_bytes(l) + unit_bytes(r) <= cap:
            vocab.setdefault(l + r, len(vocab))
            keep.append([l, r])
            if len(vocab) >= total:
                break
    d = {"version": "1.0", "truncation": None, "padding": None, "added_tokens": [], "normalizer": None,
         "pre_tokenizer": None, "post_processor": None, "decoder": None,
         "model": {"type": "BPE", "dropout": None, "unk_token": None, "continuing_subword_prefix": None,
                   "end_of_word_suffix": None, "fuse_unk": False, "byte_fallback": False, "ignore_merges": False,
                   "vocab": vocab, "merges": keep}}
    return Two(two.p, Tokenizer.from_str(json.dumps(d))), len(vocab)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p1536", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--domains", nargs="*", default=list(DOMAINS))
    ap.add_argument("--scale", type=float, default=1.0, help="multiply all text sizes (quick test: 0.05)")
    ap.add_argument("--no-sha", action="store_true", help="skip the p1536 sha check (local tests only)")
    a = ap.parse_args()
    global EVAL_BYTES, MODEL_BYTES, DICT_BYTES
    EVAL_BYTES, MODEL_BYTES, DICT_BYTES = (int(x * a.scale) for x in (EVAL_BYTES, MODEL_BYTES, DICT_BYTES))
    from tokenizers import Tokenizer
    if not a.no_sha and sha(a.p1536) != P1536:
        sys.exit("--p1536 is not the frozen p1536")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    p = Tokenizer.from_file(a.p1536)
    base = Two(p)
    log(f"p1536 ids: {base.v1:,}")

    data, sizes = {}, {}
    for name in a.domains:
        folder, cols = DOMAINS[name]
        try:
            data[name], sizes[name] = load(folder, cols)
            log(f"{name}: " + ", ".join(f"{k} {len(v):,} docs {sizes[name][k]/1e6:.2f} MB" for k, v in data[name].items()))
        except Exception as e:                       # a missing public source drops the domain, it does not stop the run
            log(f"{name}: SKIPPED ({type(e).__name__}: {e})")
    names = [n for n in a.domains if n in data and data[n]["C"] and data[n]["A"]]

    alldict = [t for n in names for t in data[n]["A"]]
    log(f"stage 2: training on {len(alldict):,} docs, {sum(sizes[n]['A'] for n in names)/1e6:.1f} MB")
    merges, secs = train_stage2(base, alldict)
    log(f"stage 2: {len(merges):,} merges in {secs:.0f}s")

    tok_bytes = {}
    for i in range(base.v1):
        tok_bytes[chr(BASE_CP + i)] = len(p.decode([i], skip_special_tokens=False).encode("utf-8"))

    def unit_bytes(s):
        return sum(tok_bytes[c] for c in s)

    lists = [("p1536", base, base.v1, None)]
    for total, cap in LISTS:
        t, n = build(base, merges, total, cap, unit_bytes)
        lists.append((f"p1536+SuperBPE {n // 1000}k cap{cap}", t, n, cap))
        log(f"built {lists[-1][0]}: {n:,} ids")

    res = {"data": {n: sizes[n] for n in names}, "stage2_merges_learned": len(merges), "stage2_train_seconds": round(secs),
           "p1536_sha": P1536, "lists": []}
    p_tokens = {}
    for label, t, N, cap in lists:
        log(f"eval {label}")
        row = {"label": label, "ids": N, "cap": cap, "domains": {}}
        allC, allB_counts_small, allB_counts = [], collections.Counter(), collections.Counter()
        for n in names:
            C = data[n]["C"]
            ec = t.encode(C)
            ok = sum(t.decode(e) == t.norm(x) for e, x in zip(ec, C))
            ntok = sum(map(len, ec))
            nbytes = sum(len(x.encode("utf-8", "surrogatepass")) for x in C)
            nwords = sum(len(x.split()) for x in C)
            B = data[n]["B"]
            eb = t.encode(B)
            cut_at, acc, small = sizes[n]["B"] / 5, 0, collections.Counter()
            full = collections.Counter()
            for x, e in zip(B, eb):
                full.update(e)
                if acc < cut_at:
                    small.update(e)
                acc += len(x.encode("utf-8", "surrogatepass"))
            allB_counts.update(full)
            allB_counts_small.update(small)
            pos = [u for e in ec for u in e]
            allC.extend(pos)
            d = {"docs": len(C), "bytes": nbytes, "tokens": ntok, "lossless": f"{ok}/{len(C)}",
                 "bytes_per_token": nbytes / ntok, "tokens_per_word": ntok / max(nwords, 1),
                 "unseen_small_B": sum(1 for u in pos if small[u] == 0) / ntok,
                 "unseen_B": sum(1 for u in pos if full[u] == 0) / ntok}
            if t.s2 is not None:
                for m in (1, 10):
                    d[f"backoff_m{m}_tokens"] = sum(len(t.units[u]) if (u >= base.v1 and full[u] < m) else 1 for u in pos)
            if label == "p1536":
                p_tokens[n] = ntok
            d["x_fewer_than_p1536"] = p_tokens[n] / ntok
            if t.s2 is not None:
                for m in (1, 10):
                    d[f"backoff_m{m}_x_fewer"] = p_tokens[n] / d[f"backoff_m{m}_tokens"]
            row["domains"][n] = d
        # pooled numbers
        T = len(allC)
        row["tokens"] = T
        row["mean_x_fewer"] = sum(row["domains"][n]["x_fewer_than_p1536"] for n in names) / len(names)
        row["mean_bytes_per_token"] = sum(row["domains"][n]["bytes_per_token"] for n in names) / len(names)
        row["unseen_B_pooled"] = sum(1 for u in allC if allB_counts[u] == 0) / T
        row["unseen_small_B_pooled"] = sum(1 for u in allC if allB_counts_small[u] == 0) / T
        row["ids_used_on_C"] = len(set(allC))
        row["ids_never_in_B"] = N - len(allB_counts)
        ptot = sum(p_tokens.values())
        row["head_logits_per_byte_vs_p1536"] = (N / base.v1) * (T / ptot)
        rank = {u: r for r, (u, _) in enumerate(allB_counts.most_common())}
        rs = sorted(rank.get(u, 10**12) for u in allC)
        for q in (0.99, 0.999):
            k = rs[int(q * T) - 1]
            row[f"shortlist_K_{q}"] = (k + 1) if k < 10**12 else None
        row["coverage_top131k"] = sum(1 for r in rs if r < 131_072) / T
        if t.s2 is not None:
            for m in (1, 10):
                bt = sum(row["domains"][n][f"backoff_m{m}_tokens"] for n in names)
                kept = sum(1 for u, c in allB_counts.items() if u < base.v1 or c >= m) if m > 1 else len(allB_counts)
                row[f"backoff_m{m}_mean_x_fewer"] = sum(row["domains"][n][f"backoff_m{m}_x_fewer"] for n in names) / len(names)
                row[f"backoff_m{m}_ids_needed"] = base.v1 + sum(1 for u, c in allB_counts.items() if u >= base.v1 and c >= m)
        res["lists"].append(row)
        log(f"  {label}: mean {row['mean_x_fewer']:.2f}x fewer, unseen {row['unseen_B_pooled']:.2%}, "
            f"head/byte {row['head_logits_per_byte_vs_p1536']:.2f}x")

    (out / "task00_units.json").write_text(json.dumps(res, indent=1))
    (out / "task00_units.md").write_text(report(res, names))
    print(report(res, names))


def report(res, names):
    L = res["lists"]
    o = ["# Task 00, G3 side: SuperBPE units on top of frozen p1536 (public text)", ""]
    o.append(f"Stage 2 learned {res['stage2_merges_learned']:,} merges in {res['stage2_train_seconds']} s. Data per domain "
             "(MB): " + "; ".join(f"{n} C {v['C']/1e6:.1f} / B {v['B']/1e6:.1f} / A {v['A']/1e6:.1f}" for n, v in res["data"].items()))
    o += ["", "## Tokens vs p1536 (times fewer tokens on held-out C; higher is better)", "",
          "| Unit list | Ids | " + " | ".join(names) + " | **Mean** |", "|---|---:|" + "---:|" * (len(names) + 1)]
    for r in L:
        o.append(f"| {r['label']} | {r['ids']:,} | " + " | ".join(f"{r['domains'][n]['x_fewer_than_p1536']:.2f}" for n in names)
                 + f" | **{r['mean_x_fewer']:.2f}** |")
    o += ["", "## Bytes per token", "", "| Unit list | " + " | ".join(names) + " | Mean |", "|---|" + "---:|" * (len(names) + 1)]
    for r in L:
        o.append(f"| {r['label']} | " + " | ".join(f"{r['domains'][n]['bytes_per_token']:.2f}" for n in names)
                 + f" | {r['mean_bytes_per_token']:.2f} |")
    o += ["", "## Unseen units: share of held-out positions whose unit never occurs in the model text B", "",
          "| Unit list | " + " | ".join(names) + " | Pooled (B/5) | Pooled (B) |", "|---|" + "---:|" * (len(names) + 2)]
    for r in L:
        o.append(f"| {r['label']} | " + " | ".join(f"{r['domains'][n]['unseen_B']:.1%}" for n in names)
                 + f" | {r['unseen_small_B_pooled']:.1%} | {r['unseen_B_pooled']:.1%} |")
    o += ["", "## Backoff: new units seen < m times in B written as their p1536 spelling (times fewer than p1536)", "",
          "| Unit list | m | " + " | ".join(names) + " | Mean | Ids still needed |", "|---|---:|" + "---:|" * (len(names) + 2)]
    for r in L[1:]:
        for m in (1, 10):
            o.append(f"| {r['label']} | {m} | " + " | ".join(f"{r['domains'][n][f'backoff_m{m}_x_fewer']:.2f}" for n in names)
                     + f" | {r[f'backoff_m{m}_mean_x_fewer']:.2f} | {r[f'backoff_m{m}_ids_needed']:,} |")
    o += ["", "## Output scoring cost", "",
          "| Unit list | Head size N | Lossless | Logits per byte vs p1536 | Ids used on C | Ids never in B | Shortlist K for 99% | for 99.9% | Top-131k coverage |",
          "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for r in L:
        ok = all(r["domains"][n]["lossless"].split("/")[0] == r["domains"][n]["lossless"].split("/")[1] for n in names)
        k1 = f"{r['shortlist_K_0.99']:,}" if r["shortlist_K_0.99"] else "not reachable"
        k2 = f"{r['shortlist_K_0.999']:,}" if r["shortlist_K_0.999"] else "not reachable"
        o.append(f"| {r['label']} | {r['ids']:,} | {'yes, every doc' if ok else 'NO'} | {r['head_logits_per_byte_vs_p1536']:.2f}x | "
                 f"{r['ids_used_on_C']:,} | {r['ids_never_in_B']:,} | {k1} | {k2} | {r['coverage_top131k']:.1%} |")
    o.append("")
    return "\n".join(o)


if __name__ == "__main__":
    main()
