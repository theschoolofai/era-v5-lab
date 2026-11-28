"""Design tasks 1-4 of the G3 28 Nov brief: our own unit lists (plain BPE and SuperBPE-style), against the frozen p1536,
o200k_base (also cut to the same sizes) and the released SuperBPE tokenizers, on 12 domains.

    python teams/03-tokenizer/harness/design_units.py prep  --sample <sample v0> --work <dir>
    python teams/03-tokenizer/harness/design_units.py train --work <dir> --p1536 release/tokenizer.json
    python teams/03-tokenizer/harness/design_units.py eval  --work <dir> --sample <sample v0> --p1536 release/tokenizer.json \
        --superbpe <dir with UW tokenizer.json files> --out teams/03-tokenizer/results/design_units

prep   Training text: every train/ doc of sample v0 (6.0 GB of text, 38 packs, already at the Stage 1 group shares),
       exact duplicates removed (doc_id is sha256 of the text), put in a fixed random order (sha256 of SEED:doc_id), and
       cut into nested sets of 10 MB, 100 MB and 1 GB of UTF-8 text (the 10 MB set is the start of the 100 MB set).
train  plain BPE    the p1536 normalizer and pre-tokenizer (o200k regex, byte level) with a BPE learned from scratch on
                    each set, up to MAX_MERGES[set] merges (training stops early when no pair is seen twice).
       SuperBPE     two stages, as in Liu et al. 2025 (github.com/PythonNut/superbpe): stage 1 is the plain BPE above, cut
                    at T merges; stage 2 learns more merges over stage-1 tokens with the stage-2 split rule STAGE2 of
                    superbpe/scripts/extend_tokenizer.sh, so a unit may cross spaces. Stock `tokenizers` cannot resume
                    training, so stage 2 writes each stage-1 token as one character (U+10000 + id) and learns a plain
                    character BPE on those strings; encoding is stage 1, then stage 2. The merges are the same as a
                    resumed run would learn; only the stage-1 split inside a stage-2 chunk can differ at chunk edges.
eval   12 domains (DOMAINS), the heldout/ parts of sample v0 (never in training), at most EVAL_BYTES per domain.
       Unit caps 32 and 64 bytes: merges whose unit is longer are removed (every later merge built on one is longer too,
       so the list stays a valid BPE). Merge curves: the first 1k / 10k / 100k / 1M merges (a prefix of a BPE is a BPE).
       o200k_base cut to the same sizes: its first 256 + k ranks.
       Per tokenizer and domain: tokens per word (word = maximal non-whitespace run, str.split()), bytes per token,
       lossless share (decode(encode(x)) == normalizer(x)), unused units (ids never produced on all eval text), and the
       encoder rate in tokens/s on one core (RAYON_NUM_THREADS=1). Numbers: how fixed number strings split.
"""
import os
import sys

if "eval" in sys.argv[1:2]:
    os.environ.setdefault("RAYON_NUM_THREADS", "1")       # encoder rate on one core; training uses every core
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import argparse  # noqa: E402
import glob  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import pyarrow as pa  # noqa: E402
import pyarrow.compute as pc  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

P1536 = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"
SEED = 20261128
SETS = {"10MB": 10 * 10**6, "100MB": 100 * 10**6, "1GB": 10**9}
MAX_MERGES = {"10MB": 1_000_000, "100MB": 1_000_000, "1GB": 1_000_000}
CURVE = (1_000, 10_000, 100_000, 1_000_000)
CAPS = (32, 64)
# (set, T stage-1 merges, total merges, stage-2 split rule)
SUPER = [("100MB", 80_000, 100_000, "marks"), ("100MB", 80_000, 100_000, "upstream"), ("100MB", 180_000, 200_000, "marks"),
         ("1GB", 80_000, 100_000, "marks")]     # 1 GB t180k left out: stage 2 on 1 GB took 46 min in 16 GB of RAM
# upstream: superbpe/scripts/extend_tokenizer.sh. It counts combining marks (\p{M}: Indic vowel signs, virama) as
# punctuation, so "है।" splits as "ह" + "ै।" and stage 2 can make an Indic word worse than stage 1.
# marks: the same rule with \p{M} kept with letters.
STAGE2 = {"upstream": r"\p{N}{1,3}| ?[^\s\p{L}\p{N}]{2,}[\r\n/]*| +(?!\S)",
          "marks": r"\p{N}{1,3}| ?[^\s\p{L}\p{M}\p{N}]{2,}[\r\n/]*| +(?!\S)"}
BASE_CP = 0x10000
EVAL_BYTES = 1_000_000
DOMAINS = {
    "en-web": ["en-dclm", "en-fineweb-edu", "en-nemotroncc"],
    "en-synthetic": ["en-nemotroncc-synth"],
    "code-python": ["code-python"],
    "code-other": ["code-cpp", "code-go", "code-java", "code-js-ts", "code-rust"],
    "code-adjacent": ["cadj-commits", "cadj-notebooks", "cadj-stackexchange"],
    "math": ["math-finemath", "math-megamath"],
    "science-pdf": ["sci-finepdfs"],
    "hi-mr (Devanagari)": ["ind-hi-fw2", "ind-hi-hplt", "ind-hi-indiccorp", "ind-hi-sangraha-s", "ind-hi-sangraha-v",
                           "ind-mr-fw2", "ind-mr-sangraha-v"],
    "bn-or-gu": ["ind-bn-fw2", "ind-bn-sangraha-v", "ind-or-fw2", "ind-gu-fw2"],
    "ta-ml": ["ind-ta-fw2", "ind-ta-sangraha-s", "ind-ta-sangraha-v", "ind-ml-fw2"],
    "te-kn": ["ind-te-fw2", "ind-te-sangraha-s", "ind-te-sangraha-v", "ind-kn-fw2", "ind-kn-sangraha-s",
              "ind-kn-sangraha-v"],
    "sanskrit": ["ind-sa-fw2"],
}
NUMBERS = ["7", "42", "1999", "2026", "12345", "1234567", "3.14159", "-0.0001", "1,50,000", "1,000,000", "1e-9",
           "0x7fff", "2026-11-28", "10:45", "₹2,499", "99.9%", "१२३४५", "৩৬৫", "௨௦௨௬"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- prep
def prep(a):
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(Path(a.sample) / "train" / "*" / "*.parquet")))
    keys = {}
    for f in files:
        t = pq.read_table(f, columns=["doc_id", "text"])
        nb = pc.binary_length(pc.cast(t["text"], pa.binary())).to_pylist()
        for d, n in zip(t["doc_id"].to_pylist(), nb):
            if d not in keys:
                keys[d] = (hashlib.sha256(f"{SEED}:{d}".encode()).digest(), n)
    order = sorted(keys, key=lambda d: keys[d][0])
    tier, total, cut = {}, 0, list(SETS.items())
    for d in order:
        total += keys[d][1]
        i = next((i for i, (_, lim) in enumerate(cut) if total <= lim), None)
        if i is None:
            break
        tier[d] = i
    log(f"{len(keys):,} unique docs, {len(tier):,} kept for {cut[-1][0]}")
    w = pq.ParquetWriter(work / "train_text.parquet", pa.schema([("tier", pa.int8()), ("pack", pa.string()),
                                                                  ("text", pa.string())]))
    for f in files:
        t = pq.read_table(f, columns=["doc_id", "text"])
        ids = t["doc_id"].to_pylist()
        rows = [(tier.pop(d), Path(f).parent.name, x) for d, x in zip(ids, t["text"].to_pylist()) if d in tier]
        if rows:
            w.write_table(pa.table({"tier": [r[0] for r in rows], "pack": [r[1] for r in rows],
                                    "text": [r[2] for r in rows]}, schema=w.schema))
    w.close()
    t = pq.read_table(work / "train_text.parquet", columns=["tier", "text"])
    nb = pc.binary_length(pc.cast(t["text"], pa.binary())).to_numpy()
    tiers = t["tier"].to_numpy()
    meta = {"seed": SEED, "sample_sha256sums": sha(Path(a.sample) / "SHA256SUMS"), "unique_docs": len(keys),
            "sets": {n: {"docs": int((tiers <= i).sum()), "bytes": int(nb[tiers <= i].sum())}
                     for i, n in enumerate(SETS)}}
    (work / "train_text.json").write_text(json.dumps(meta, indent=1))
    log(meta["sets"])


def texts(work, name):
    i = list(SETS).index(name)
    t = pq.read_table(Path(work) / "train_text.parquet", columns=["tier", "text"], filters=[("tier", "<=", i)])
    return t["text"].to_pylist()


# ---------------------------------------------------------------- tokenizers
def from_p1536(p1536):
    from tokenizers import Tokenizer
    if sha(p1536) != P1536:
        sys.exit("--p1536 is not the frozen p1536")
    return Tokenizer.from_file(str(p1536))


def train_plain(work, name, p1536):
    from tokenizers import Tokenizer, models, pre_tokenizers, trainers
    out = Path(work) / f"plain_{name}.json"
    if out.exists():
        return
    p = from_p1536(p1536)
    tok = Tokenizer(models.BPE())
    tok.normalizer, tok.pre_tokenizer, tok.decoder = p.normalizer, p.pre_tokenizer, p.decoder
    tr = trainers.BpeTrainer(vocab_size=256 + MAX_MERGES[name], min_frequency=2, show_progress=False,
                             initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    docs = texts(work, name)
    log(f"plain {name}: {len(docs):,} docs")
    t0 = time.time()
    tok.train_from_iterator(docs, trainer=tr, length=len(docs))
    secs = time.time() - t0
    tok.save(str(out))
    m = json.loads(out.read_text())["model"]
    meta = {"merges": len(m["merges"]), "train_seconds": round(secs, 1), "threads": os.cpu_count()}
    out.with_suffix(".meta.json").write_text(json.dumps(meta))
    log(f"plain {name}: {meta}")


def bpe_json(base, merges, alphabet):
    """A tokenizer.json dict with the given byte-level merges (pairs of strings) on base's normalizer/pre-tokenizer."""
    vocab = {c: i for i, c in enumerate(alphabet)}
    for l, r in merges:
        vocab.setdefault(l + r, len(vocab))
    d = json.loads(json.dumps(base))
    d["model"]["vocab"], d["model"]["merges"] = vocab, [list(m) for m in merges]
    d["added_tokens"] = []
    return d


def cut(merges, k, cap=None, nbytes=len):
    """First k merges whose unit is at most cap bytes."""
    out = []
    for l, r in merges:
        if cap is None or nbytes(l) + nbytes(r) <= cap:
            out.append((l, r))
            if len(out) == k:
                break
    return out


def stage2_split(rule):
    from tokenizers import Regex, pre_tokenizers
    return pre_tokenizers.Split(Regex(STAGE2[rule]), behavior="isolated")


class Plain:
    def __init__(self, d, name):
        from tokenizers import Tokenizer
        self.tok = Tokenizer.from_str(json.dumps(d))
        self.name, self.vocab = name, self.tok.get_vocab_size()

    def encode(self, docs):
        return [e.ids for e in self.tok.encode_batch(docs, add_special_tokens=False)]

    def decode(self, ids):
        return self.tok.decode(ids)

    def norm(self, x):
        return self.tok.normalizer.normalize_str(x) if self.tok.normalizer else x


class Super:
    """Stage 1 (a Plain), then stage 2: a character BPE over stage-1 ids written as chr(BASE_CP + id)."""

    def __init__(self, s1, s2d, name, rule):
        from tokenizers import Tokenizer
        self.s1, self.s2 = s1, Tokenizer.from_str(json.dumps(s2d))
        self.split = stage2_split(rule)
        self.name, self.vocab = name, self.s2.get_vocab_size()
        inv = {i: t for t, i in self.s2.get_vocab().items()}
        self.units = [[ord(c) - BASE_CP for c in inv[i]] for i in range(len(inv))]

    def chunks(self, docs):
        out, owner = [], []
        for j, x in enumerate(docs):
            x = self.s1.norm(x)
            for piece, _ in self.split.pre_tokenize_str(x):
                out.append(piece)
                owner.append(j)
        return out, owner

    def encode(self, docs):
        ch, owner = self.chunks(docs)
        mapped = ["".join(chr(BASE_CP + i) for i in ids) for ids in self.s1.encode(ch)]
        res = [[] for _ in docs]
        for j, e in zip(owner, self.s2.encode_batch(mapped, add_special_tokens=False)):
            res[j].extend(e.ids)
        return res

    def decode(self, ids):
        return self.s1.decode([i for u in ids for i in self.units[u]])

    def norm(self, x):
        return self.s1.norm(x)


def train_super(work, name, T, total, rule):
    from tokenizers import Tokenizer, models, trainers
    out = Path(work) / f"super_{name}_t{T // 1000}k_{total // 1000}k_{rule}.json"
    if out.exists():
        return
    base = json.loads((Path(work) / f"plain_{name}.json").read_text())
    alphabet = [t for t, i in sorted(base["model"]["vocab"].items(), key=lambda x: x[1])][:256]
    merges = [tuple(m) for m in base["model"]["merges"]]
    if len(merges) < T:
        log(f"super {name} t{T}: stage 1 has only {len(merges)} merges, skipped")
        return
    s1d = bpe_json(base, merges[:T], alphabet)
    s1 = Plain(s1d, "stage1")
    splitter = Super.__new__(Super)
    splitter.s1, splitter.split = s1, stage2_split(rule)
    docs = texts(work, name)
    log(f"super {name} t{T} {rule}: stage-1 encoding {len(docs):,} docs")
    t0 = time.time()

    def mapped():
        for k in range(0, len(docs), 2000):
            ch, _ = splitter.chunks(docs[k:k + 2000])
            for ids in s1.encode(ch):
                if len(ids) > 1:
                    yield "".join(chr(BASE_CP + i) for i in ids)

    s2 = Tokenizer(models.BPE())
    v1 = s1.vocab
    tr = trainers.BpeTrainer(vocab_size=v1 + (total - T), min_frequency=2, show_progress=False,
                             initial_alphabet=[chr(BASE_CP + i) for i in range(v1)])
    s2.train_from_iterator(mapped(), trainer=tr)
    secs = time.time() - t0
    d = json.loads(s2.to_str())
    # stage-2 vocab must give every stage-1 id the same character id order: rebuild it as alphabet then merges
    m2 = [tuple(m) for m in d["model"]["merges"]]
    d["model"]["vocab"] = {chr(BASE_CP + i): i for i in range(v1)}
    for l, r in m2:
        d["model"]["vocab"].setdefault(l + r, len(d["model"]["vocab"]))
    d["model"]["merges"] = [list(m) for m in m2]
    out.write_text(json.dumps({"stage1": s1d, "stage2": d, "T": T, "total": total, "rule": rule,
                               "stage2_merges": len(m2), "train_seconds": round(secs, 1)}))
    log(f"super {name} t{T}: {len(m2)} stage-2 merges in {secs:.0f}s")


def one_file(d, rule):
    """The two stages as one standard tokenizer.json, packaged like the released SuperBPE: stage-2 split rule, byte
    level, then the stage-1 merges followed by the stage-2 merges written as bytes. Inside a chunk the stage-1 merges
    then also apply across the stage-1 word split, so counts can differ slightly from the two-stage encoder."""
    s1 = d["stage1"]
    s1inv = {i: t for t, i in s1["model"]["vocab"].items()}

    def text(u):
        return "".join(s1inv[ord(c) - BASE_CP] for c in u)

    out = json.loads(json.dumps(s1))
    vocab = out["model"]["vocab"]
    merges = [tuple(m) for m in s1["model"]["merges"]]
    for l, r in d["stage2"]["model"]["merges"]:
        a, b = text(l), text(r)
        vocab.setdefault(a + b, len(vocab))
        merges.append((a, b))
    out["model"]["merges"] = [list(m) for m in merges]
    out["model"]["ignore_merges"] = False
    out["pre_tokenizer"] = {"type": "Sequence", "pretokenizers": [
        {"type": "Split", "pattern": {"Regex": STAGE2[rule]}, "behavior": "Isolated", "invert": False},
        {"type": "ByteLevel", "add_prefix_space": False, "trim_offsets": True, "use_regex": False}]}
    return out


def train(a):
    for name in SETS:
        if name in (a.sets or SETS):
            train_plain(a.work, name, a.p1536)
    for name, T, total, rule in SUPER:
        if name in (a.sets or SETS):
            train_super(a.work, name, T, total, rule)


# ---------------------------------------------------------------- eval
def eval_text(sample):
    out = {}
    for dom, packs in DOMAINS.items():
        docs, n = [], 0
        for p in packs:
            for f in sorted(glob.glob(str(Path(sample) / "heldout" / p / "*.parquet"))):
                docs += [(p, x) for x in pq.read_table(f, columns=["text"])["text"].to_pylist()]
        # round robin over packs so a domain's cap takes from each of its packs
        by = {p: [x for q, x in docs if q == p] for p in packs}
        picked, i = [], 0
        while n < EVAL_BYTES and any(i < len(v) for v in by.values()):
            for p in packs:
                if i < len(by[p]) and n < EVAL_BYTES:
                    picked.append(by[p][i])
                    n += len(by[p][i].encode())
            i += 1
        out[dom] = picked
    return out


class Tik:
    def __init__(self, k=None):
        import tiktoken
        base = tiktoken.get_encoding("o200k_base")
        if k is None:
            self.enc, self.name = base, "o200k_base"
        else:
            ranks = {b: r for b, r in base._mergeable_ranks.items() if r < 256 + k}
            self.enc = tiktoken.Encoding(f"o200k_{k}", pat_str=base._pat_str, mergeable_ranks=ranks, special_tokens={})
            self.name = f"o200k first {k // 1000}k"
        self.vocab = self.enc.n_vocab

    def encode(self, docs):
        return self.enc.encode_ordinary_batch(docs, num_threads=1)

    def decode(self, ids):
        return self.enc.decode(ids)

    def norm(self, x):
        return x


class HFFile(Plain):
    def __init__(self, path, name):
        from tokenizers import Tokenizer
        self.tok = Tokenizer.from_file(str(path))
        self.name, self.vocab = name, self.tok.get_vocab_size()


def measure(t, ev):
    used = set()
    row, all_tok, all_secs = {}, 0, 0.0
    for dom, docs in ev.items():
        t0 = time.perf_counter()
        ids = t.encode(docs)
        secs = time.perf_counter() - t0
        ntok = sum(map(len, ids))
        nw = sum(len(x.split()) for x in docs)
        nb = sum(len(x.encode()) for x in docs)
        ok = sum(t.decode(i) == t.norm(x) for i, x in zip(ids, docs))
        for i in ids:
            used.update(i)
        row[dom] = {"tokens": ntok, "tokens_per_word": round(ntok / nw, 4), "bytes_per_token": round(nb / ntok, 3),
                    "lossless": round(ok / len(docs), 4)}
        all_tok += ntok
        all_secs += secs
    return {"vocab": t.vocab, "domains": row, "total_tokens": all_tok,
            "unused_units": t.vocab - len(used), "unused_share": round(1 - len(used) / t.vocab, 4),
            "tokens_per_s_core": round(all_tok / all_secs)}


def numbers(t):
    out = {}
    for s in NUMBERS:
        ids = t.encode([s])[0]
        out[s] = [t.decode([i]) for i in ids]
    return out


def evaluate(a):
    work = Path(a.work)
    ev = eval_text(a.sample)
    p = from_p1536(a.p1536)
    base = json.loads(p.to_str())
    res, nums = {}, {}

    def run(t, group, **meta):
        log("eval", t.name)
        r = measure(t, ev)
        r.update(group=group, **meta)
        res[t.name] = r
        nums[t.name] = numbers(t)

    run(HFFile(a.p1536, "p1536 (frozen)"), "reference", sha256=P1536)
    run(Tik(), "reference")
    for k in CURVE[:-1]:
        run(Tik(k), "o200k cut", merges=k)
    for name in SETS:
        f = work / f"plain_{name}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        meta = json.loads(f.with_suffix(".meta.json").read_text())
        alphabet = [t for t, i in sorted(d["model"]["vocab"].items(), key=lambda x: x[1])][:256]
        merges = [tuple(m) for m in d["model"]["merges"]]
        for k in CURVE:
            if k > len(merges):
                continue
            for cap in (None,) + CAPS:
                mk = cut(merges, k, cap)
                if cap and len(mk) < k:
                    continue
                if cap and name != "100MB" and k != 100_000:
                    continue      # caps on the 100 MB set at every size, and at 100k for the other sets
                nm = f"plain {name} {k // 1000}k" + (f" ≤{cap}B" if cap else "")
                run(Plain(bpe_json(base, mk, alphabet), nm), "plain BPE", train_set=name, merges=k, cap=cap,
                    train_seconds=meta["train_seconds"] if k == len(merges) or k == CURVE[-1] else None,
                    max_unit_bytes=max(len(l) + len(r) for l, r in mk))
    for f in sorted(x for x in work.glob("super_*.json") if not x.name.endswith(".tokenizer.json")):
        d = json.loads(f.read_text())
        s1 = Plain(d["stage1"], "stage1")
        s2 = d["stage2"]
        inv = {i: t for t, i in s2["model"]["vocab"].items()}
        s1inv = {i: t for t, i in d["stage1"]["model"]["vocab"].items()}

        def nbytes(u):
            return sum(len(s1inv[ord(c) - BASE_CP]) for c in u)

        m2 = [tuple(m) for m in s2["model"]["merges"]]
        train_set = f.stem.split("_")[1]
        for cap in (None,) + CAPS:
            mk = cut(m2, len(m2), cap, nbytes)
            dd = json.loads(json.dumps(s2))
            v1 = s1.vocab
            dd["model"]["vocab"] = {chr(BASE_CP + i): i for i in range(v1)}
            for l, r in mk:
                dd["model"]["vocab"].setdefault(l + r, len(dd["model"]["vocab"]))
            dd["model"]["merges"] = [list(m) for m in mk]
            nm = (f"SuperBPE {train_set} t{d['T'] // 1000}k→{d['total'] // 1000}k" + ("" if d["rule"] == "marks" else
                  " upstream rule") + (f" ≤{cap}B" if cap else ""))
            if cap and d["rule"] != "marks":
                continue
            run(Super(s1, dd, nm, d["rule"]), "SuperBPE (ours)", train_set=train_set, merges=d["T"] + len(mk),
                T=d["T"], cap=cap, rule=d["rule"],
                stage2_merges=len(mk), train_seconds=d["train_seconds"] if cap is None else None,
                max_unit_bytes=max([nbytes(l + r) for l, r in mk] or [0]))
        del inv
        one = one_file(d, d["rule"])
        (work / f"{f.stem}.tokenizer.json").write_text(json.dumps(one, ensure_ascii=False))
        run(Plain(one, f"SuperBPE {train_set} t{d['T'] // 1000}k→{d['total'] // 1000}k" +
                  ("" if d["rule"] == "marks" else " upstream rule") + " (one file)"), "SuperBPE (ours, one file)",
            train_set=train_set, merges=len(one["model"]["merges"]), T=d["T"], rule=d["rule"])
    if a.superbpe:
        for f in sorted(Path(a.superbpe).glob("*/tokenizer.json")):
            rev = f.parent / "REVISION"
            run(HFFile(f, f.parent.name.replace("__", "/")), "SuperBPE (released)", sha256=sha(f),
                revision=rev.read_text().strip() if rev.exists() else None)
    out = {"domains": {k: {"packs": v, "docs": len(ev[k]), "bytes": sum(len(x.encode()) for x in ev[k])}
                       for k, v in DOMAINS.items()},
           "train_text": json.loads((work / "train_text.json").read_text()),
           "train_meta": {f.stem: json.loads(f.read_text()) for f in work.glob("plain_*.meta.json")},
           "tokenizers": res, "numbers": nums,
           "environment": {"python": platform.python_version(), "machine": platform.machine(),
                           "cpus": os.cpu_count(), "script_sha256": sha(__file__)}}
    Path(a.out).with_suffix(".json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    log("wrote", Path(a.out).with_suffix(".json"))
    report(a)


def report(a):
    o = json.loads(Path(a.out).with_suffix(".json").read_text())
    R, doms = o["tokenizers"], list(o["domains"])
    short = {d: d.split(" ")[0] for d in doms}

    def mean(n, key):
        return sum(R[n]["domains"][d][key] for d in doms) / len(doms)

    def row(n, key, fmt):
        return f"| {n} | {R[n]['vocab']:,} | " + " | ".join(format(R[n]["domains"][d][key], fmt) for d in doms) + \
            f" | **{format(mean(n, key), fmt)}** |"

    head = "| Tokenizer | Ids | " + " | ".join(short.values()) + " | **Mean** |"
    rule = "|---|---:|" + "---:|" * len(doms) + "---:|"
    pick = [n for n in R if R[n]["group"] in ("reference", "SuperBPE (released)")
            or (R[n].get("merges") in (100_000, 200_000) and not R[n].get("cap")
                and R[n]["group"] in ("plain BPE", "SuperBPE (ours)", "o200k cut"))]
    pick += [n for n in R if R[n]["group"] in ("SuperBPE (ours)", "SuperBPE (ours, one file)") and not R[n].get("cap")
             and n not in pick]
    tt = o["train_text"]["sets"]
    md = ["# Design tasks 1-4: our own unit lists vs p1536, o200k and released SuperBPE", "",
          "Made by `harness/design_units.py` (`prep`, `train`, `eval`). Numbers in `design_units.json`.", "",
          "- **Training text:** sample v0 `train/` (6.0 GB, 38 packs at the Stage 1 group shares), exact duplicates "
          "removed, fixed random order (seed " + str(o["train_text"]["seed"]) + "), nested sets: " +
          ", ".join(f"{k} = {v['docs']:,} docs" for k, v in tt.items()) + ".",
          "- **Evaluation text:** the `heldout/` parts of the same packs (never trained on), up to 1 MB per domain:",
          "", "| Domain | Packs | Docs | Bytes |", "|---|---|---:|---:|"]
    md += [f"| {d} | {', '.join(v['packs'])} | {v['docs']:,} | {v['bytes']:,} |" for d, v in o["domains"].items()]
    md += ["", "- **Word rule:** maximal non-whitespace runs (`str.split()`), the same for every domain. For code, "
           "tokens per word is only a relative measure; bytes per token is the comparable one.",
           "- **Mean:** the plain average over the 12 domains, so each domain counts the same.", "",
           "## Task 1: tokens per word by domain (lower is better)", "", head, rule]
    md += [row(n, "tokens_per_word", ".3f") for n in pick]
    md += ["", "## Task 1: bytes per token by domain (higher is better)", "", head, rule]
    md += [row(n, "bytes_per_token", ".2f") for n in pick]

    md += ["", "## Task 1: merge curves (mean bytes per token over the 12 domains)", "",
           "Each column is one unit list cut to its first k merges. A dash: training stopped before k merges "
           "(no pair seen twice).", "", "| Merges | " + " | ".join(f"plain {k}" for k in SETS) + " | o200k cut |",
           "|---:|" + "---:|" * (len(SETS) + 1)]
    for k in CURVE:
        cells = []
        for name in list(SETS) + ["o200k"]:
            n = f"plain {name} {k // 1000}k" if name != "o200k" else (f"o200k first {k // 1000}k" if k < CURVE[-1]
                                                                      else None)
            cells.append(f"{mean(n, 'bytes_per_token'):.3f}" if n in R else "–")
        md.append(f"| {k:,} | " + " | ".join(cells) + " |")
    md += ["", "Mean bytes per token at each size, by domain, plain BPE on 1 GB:", "",
           "| Merges | " + " | ".join(short.values()) + " |", "|---:|" + "---:|" * len(doms)]
    for k in CURVE:
        n = f"plain 1GB {k // 1000}k"
        if n in R:
            md.append(f"| {k:,} | " + " | ".join(f"{R[n]['domains'][d]['bytes_per_token']:.2f}" for d in doms) + " |")

    md += ["", "## Task 1: unit caps of 32 and 64 bytes", "",
           "Merges whose unit is longer than the cap are removed. Plain BPE on 100 MB at every size, and the SuperBPE "
           "lists. `Longest` is the longest unit kept.", "",
           "| Unit list | Cap | Longest | Mean bytes/token | " + " | ".join(short[d] for d in doms) + " |",
           "|---|---:|---:|---:|" + "---:|" * len(doms)]
    for n, r in R.items():
        if r["group"] in ("plain BPE", "SuperBPE (ours)") and (r["group"] == "SuperBPE (ours)" or
                                                              r.get("train_set") == "100MB"):
            if r["group"] == "SuperBPE (ours)" and r.get("rule") != "marks":
                continue
            md.append(f"| {n.split(' ≤')[0]} | {r.get('cap') or 'none'} | {r.get('max_unit_bytes', '')} | "
                      f"{mean(n, 'bytes_per_token'):.3f} | " +
                      " | ".join(f"{r['domains'][d]['bytes_per_token']:.2f}" for d in doms) + " |")

    md += ["", "## Task 2: lossless, unused units, encoder rate", "",
           "Lossless: share of eval docs where decode(encode(x)) equals the normalizer's output. Unused units: ids never "
           "produced on all 12 MB of eval text. Rate: tokens per second on one core over all eval text (Apple " +
           o["environment"]["machine"] + ", RAYON_NUM_THREADS=1).", "",
           "| Tokenizer | Ids | Lossless (min over domains) | Unused units | Unused share | Tokens/s/core |",
           "|---|---:|---:|---:|---:|---:|"]
    for n, r in R.items():
        md.append(f"| {n} | {r['vocab']:,} | {min(v['lossless'] for v in r['domains'].values()):.4f} | "
                  f"{r['unused_units']:,} | {r['unused_share'] * 100:.1f}% | {r['tokens_per_s_core']:,} |")

    md += ["", "## Task 2: numbers", "", "Each string encoded alone; pieces joined with `·`; `�` is a piece that is "
           "part of one character's UTF-8 bytes.", "",
           "| Tokenizer | " + " | ".join(f"`{x}`" for x in NUMBERS[:10]) + " |", "|---|" + "---|" * 10]
    numpick = [n for n in pick if n in o["numbers"]]
    for n in numpick:
        md.append(f"| {n} | " + " | ".join("·".join(p.replace("|", "\\|") for p in o["numbers"][n][x]).strip()
                                          for x in NUMBERS[:10]) + " |")
    md += ["", "| Tokenizer | " + " | ".join(f"`{x}`" for x in NUMBERS[10:]) + " |", "|---|" + "---|" * len(NUMBERS[10:])]
    for n in numpick:
        md.append(f"| {n} | " + " | ".join("·".join(o["numbers"][n][x]).strip() for x in NUMBERS[10:]) + " |")

    md += ["", "## Task 3: training-text size (10 MB, 100 MB, 1 GB)", "",
           "| Set | Docs | Merges learned (stop: no pair seen twice) | Train seconds (10 threads) | "
           "Mean bytes/token at 100k merges | " + " | ".join(short[d] for d in doms) + " |",
           "|---|---:|---:|---:|---:|" + "---:|" * len(doms)]
    for name in SETS:
        m = o["train_meta"].get(f"plain_{name}.meta")
        n = f"plain {name} 100k"
        if m and n in R:
            md.append(f"| {name} | {tt[name]['docs']:,} | {m['merges']:,} | {m['train_seconds']} | "
                      f"{mean(n, 'bytes_per_token'):.3f} | " +
                      " | ".join(f"{R[n]['domains'][d]['bytes_per_token']:.2f}" for d in doms) + " |")
    md += ["", "## Tokenizers", "", "| Tokenizer | Group | Source |", "|---|---|---|"]
    for n, r in R.items():
        src = (f"`{r['sha256'][:16]}…`" if r.get("sha256") else "") + (f" @ `{r['revision'][:12]}`"
                                                                         if r.get("revision") else "")
        md.append(f"| {n} | {r['group']} | {src or 'this script'} |")
    Path(a.out).with_suffix(".md").write_text("\n".join(md) + "\n")
    log("wrote", Path(a.out).with_suffix(".md"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=["prep", "train", "eval", "report"])
    ap.add_argument("--sample")
    ap.add_argument("--work", required=True)
    ap.add_argument("--p1536")
    ap.add_argument("--superbpe")
    ap.add_argument("--sets", nargs="*")
    ap.add_argument("--out")
    a = ap.parse_args()
    {"prep": prep, "train": train, "eval": evaluate, "report": report}[a.step](a)


if __name__ == "__main__":
    sys.exit(main())
