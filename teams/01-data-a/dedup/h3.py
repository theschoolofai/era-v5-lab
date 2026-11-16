r"""H3, the same content in another language: candidate document pairs from a multilingual sentence encoder, confirmed
by sentence alignment. A measurement job (E5): it lists and counts pairs and removes nothing.

dedup_design_v1.md, "H3": H1 and H2 find same-language copies within and across packs; translations need another
method, since they share no hash and few word shingles. Two documents in different languages are an H3 pair when most
sentences of the shorter one have a mutual best match in the other:

    coverage = aligned sentence pairs / sentences of the shorter document >= coverage_threshold

as H2's Jaccard counts shared shingles. The thresholds here are provisional; E5's sweep and hand review set them. Rule 0
applies to any later removal: a held-out copy always survives (source_priority_v1.md).

HOW TO RUN IT
=============
Python 3.9+ with numpy, pyarrow, torch and sentence-transformers (requirements_h3.txt), and the encoder in a local folder
(model_path: LaBSE in sentence-transformers format). The model is never downloaded: the script sets the Hugging Face
libraries offline, so it needs no network and no keys. It reads only its inputs and writes only to out/ in the
repository root; paths in the config are relative to the repository root.

    python teams/01-data-a/dedup/h3.py --config teams/01-data-a/dedup/h3_local.json

STAGES (cheapest first, so the encoder sees as little text as possible; each stage is timed)
==========================================================================================
  read      only the parts whose pack_id matches a configured pack (the pack_id column is read first); sentences are
            split and short documents skipped without the model; with max_docs_per_pack a part is left as soon as its
            packs have enough documents
  encode    one vector per document from its first head_sentences sentences, in batches; cached per part under cache,
            so a rerun with other thresholds encodes nothing again
  url       pages whose URLs differ only in a language marker (hi.example.org, /hi/, ?lang=hi): an exact key join
  retrieve  for each configured language pair, each document's top_k nearest documents in the other language by exact
            cosine, in blocks of rows (no index to build, no estimate); with mutual, a pair must be in both lists
  verify    URL pairs first, then the others by cosine, at most max_verify: the length ratio is checked, then each
            document's sentences are encoded (once per document) and the mutual best sentence matches are counted

TIME
====
max_minutes stops the run at the next check (between batches, blocks and chunks). The summary then has status
"stopped_time_limit" and no other output is written: an incomplete run must not be used. Each stage's seconds and rate
are in the summary. A test run limited by max_docs_per_pack also gets an estimate for all documents of the selected
packs, and a suggested Max time for the job request (1.5 x the estimate).

CONFIG (JSON; keys starting with "_" are comments)
==================================================
  inputs              TSAI's cleaned output, train/ and heldout/: only the parts under those two folders are read, as by
                      overlap.py. Or the raw <pack>/Part_N/ and <pack>/Heldout/: every part is read, a folder named
                      heldout, in any case, is held-out and everything else is train
  out, cache          the output folder and the embedding cache, both inside out/; cache "" turns the cache off
  packs               {pack_id pattern: language}, e.g. {"ind-hi-*": "hi", "en-*": "en"}; other packs are not read
  pairs               the language pairs to compare, e.g. [["sa", "en"], ["hi", "en"]]
  model_path, device  the local encoder folder; auto, cpu, mps or cuda
  batch_size, max_seq_length                         encoder batch and token limit
  min_chars, min_sentences                           shorter documents are skipped (counted, never encoded)
  sentence_min_chars, head_sentences, max_sentences  sentence length; sentences in the document vector; sentences kept
  top_k, doc_floor, mutual                           neighbours per document, lowest cosine kept, both lists required
  max_length_ratio                                   longer/shorter characters allowed (URL pairs are kept regardless)
  sentence_threshold, coverage_threshold, report_floor   aligned sentence cosine, H3 coverage, lowest coverage listed
  max_verify, url_group_max, block, max_docs_per_pack (0: all), max_minutes, max_output_mb

WHAT IT WRITES (in out; IDs, scores and counts only, never text)
================================================================
  h3_docs.parquet     row -> document: row, id, doc_id, pack, lang, split, part, row_in_part, chars, sentences
  h3_candidates.csv   every verified pair at or above report_floor, and every URL pair, highest coverage first
  h3_matches.csv      pairs at or above coverage_threshold, keyed by document for dedup.py (h3_join.py): pack_id, split,
                      part, row_in_part and doc_id of each document, then lang_a, lang_b, coverage
  h3_by_pack.csv     pack x pack: retrieved, URL, verified, listed and qualifying pairs
  h3_histogram.csv    bins of 0.01: the cosine of every retrieved pair, the coverage of every verified pair
  h3_summary.json     counts, stage times and rates, the estimate, the model and package versions, each output's sha256

In TSAI's cleaned output, part is the path under the split folder, as in overlap_docs.parquet, and row_in_part counts
every row of the part from 0, as overlap.py does. dedup.py finds each document of h3_matches.csv in overlap_docs.parquet
by (pack_id, split, part, row_in_part) and checks its doc_id, so H3 and overlap must read the same cleaned parts.
"""
import sys
sys.dont_write_bytecode = True   # write only to ./out/: no __pycache__ beside the scripts

import argparse, csv, fnmatch, hashlib, json, math, os, platform, resource, time  # noqa: E402,E401
from collections import Counter, defaultdict  # noqa: E402
from contextlib import contextmanager  # noqa: E402
from itertools import combinations  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h3_signals import (latin_share, latin_tokens, length_ratio, multiset_jaccard, numbers,  # noqa: E402
                        split_sentences, url_key)

try:
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq
    from h3_align import align, cross_topk, unit
except ImportError:   # main() says what to install
    np = None

REPO = Path(__file__).resolve().parents[3]   # teams/01-data-a/dedup/h3.py -> the repository root
DEFAULTS = {"inputs": "out/tokenizer_sample_v0_clean", "out": "out/h3", "cache": "out/h3_cache",
            "packs": {}, "pairs": [], "model_path": "", "device": "auto", "batch_size": 64, "max_seq_length": 128,
            "min_chars": 200, "min_sentences": 3, "sentence_min_chars": 20, "head_sentences": 4, "max_sentences": 16,
            "top_k": 3, "doc_floor": 0.5, "mutual": True, "max_length_ratio": 4.0,
            "sentence_threshold": 0.7, "coverage_threshold": 0.6, "report_floor": 0.3,
            "max_verify": 10000, "url_group_max": 20, "block": 128, "max_docs_per_pack": 0,
            "max_minutes": 60, "max_output_mb": 50}
POSITIVE = ("batch_size", "max_seq_length", "head_sentences", "max_sentences", "top_k", "max_verify", "url_group_max",
            "block")
NONNEGATIVE = ("min_chars", "min_sentences", "sentence_min_chars", "max_docs_per_pack")
OUTPUTS = ("h3_docs.parquet", "h3_candidates.csv", "h3_matches.csv", "h3_by_pack.csv", "h3_histogram.csv")
MATCHES_HEADER = ["pack_id_a", "split_a", "part_a", "row_in_part_a", "doc_id_a",      # H3_HEADER of h3_join.py
                  "pack_id_b", "split_b", "part_b", "row_in_part_b", "doc_id_b", "lang_a", "lang_b", "coverage"]
SPLITS = ("train", "heldout")   # the split folders of TSAI's cleaned output, as overlap.py reads them
CHUNK = 2048            # texts per encoder call; the time limit is checked between calls
PAIR_CHUNK = 512        # candidate pairs per verify step
SENTENCE_CACHE = 20000  # documents whose sentence vectors are held at once


class TimeLimit(Exception):
    pass


class Clock:
    """Seconds per stage, and the time limit of the whole run."""

    def __init__(self, max_minutes):
        self.t0 = time.time()
        self.deadline = self.t0 + max_minutes * 60
        self.stages = {}

    @contextmanager
    def stage(self, name):
        start = time.time()
        try:
            yield
        finally:
            self.stages[name] = round(self.stages.get(name, 0.0) + time.time() - start, 3)

    def check(self):
        if time.time() > self.deadline:
            raise TimeLimit

    def elapsed(self):
        return time.time() - self.t0


def load_config(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    unknown = sorted(k for k in raw if not k.startswith("_") and k not in DEFAULTS)
    if unknown:
        sys.exit(f"ERROR: unknown keys in {path}: {unknown}")
    cfg = {**DEFAULTS, **{k: v for k, v in raw.items() if not k.startswith("_")}}
    for name in ("inputs", "out", "cache", "model_path"):
        if not isinstance(cfg[name], str) or Path(cfg[name]).is_absolute():
            sys.exit(f"ERROR: {name} must be a path relative to the repository root")
    for name in ("out", "cache"):
        if (name == "out" or cfg[name]) and not (REPO / cfg[name]).resolve().is_relative_to((REPO / "out").resolve()):
            sys.exit(f"ERROR: {name} must be inside out/ in the repository root, not {cfg[name]!r}")
    packs = cfg["packs"]
    if (not isinstance(packs, dict) or not packs
            or any(not isinstance(v, str) or not k.strip() or not v.strip() for k, v in packs.items())):
        sys.exit("ERROR: packs must be a nonempty {pack_id pattern: language} map")
    langs, pairs = set(packs.values()), cfg["pairs"]
    if (not isinstance(pairs, list) or not pairs
            or any(not isinstance(p, list) or len(p) != 2 or not all(isinstance(x, str) for x in p)
                   or p[0] == p[1] or not set(p) <= langs for p in pairs)
            or len({frozenset(p) for p in pairs}) != len(pairs)):
        sys.exit(f"ERROR: pairs must be distinct [language, language] pairs of two languages in packs {sorted(langs)}")
    for name in POSITIVE:
        if type(cfg[name]) is not int or cfg[name] <= 0:
            sys.exit(f"ERROR: {name} must be a positive integer")
    for name in NONNEGATIVE:
        if type(cfg[name]) is not int or cfg[name] < 0:
            sys.exit(f"ERROR: {name} must be a nonnegative integer")
    if cfg["head_sentences"] > cfg["max_sentences"]:
        sys.exit("ERROR: head_sentences must be at most max_sentences")
    number = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)
    if not number(cfg["doc_floor"]) or not -1 <= cfg["doc_floor"] <= 1:
        sys.exit("ERROR: doc_floor must be a cosine between -1 and 1")
    for name in ("sentence_threshold", "coverage_threshold", "report_floor"):
        if not number(cfg[name]) or not 0 <= cfg[name] <= 1:
            sys.exit(f"ERROR: {name} must be between 0 and 1")
    if not number(cfg["max_length_ratio"]) or cfg["max_length_ratio"] < 1:
        sys.exit("ERROR: max_length_ratio must be at least 1")
    if not number(cfg["max_minutes"]) or cfg["max_minutes"] <= 0:
        sys.exit("ERROR: max_minutes must be above 0")
    if not number(cfg["max_output_mb"]) or not 0 < cfg["max_output_mb"] <= 50:
        sys.exit("ERROR: max_output_mb must be above 0 and at most 50 (JOB_REQUEST.md)")
    if type(cfg["mutual"]) is not bool:
        sys.exit("ERROR: mutual must be true or false")
    if cfg["device"] not in ("auto", "cpu", "mps", "cuda"):
        sys.exit("ERROR: device must be auto, cpu, mps or cuda")
    return cfg


def lang_of(pack, packs):
    """The language of the first pattern in packs that matches pack_id, or None (the pack is not read)."""
    for pattern, lang in packs.items():
        if fnmatch.fnmatchcase(pack, pattern):
            return lang
    return None


def find_parts(inputs):
    """The Parquet parts to read, as (split, part, path). With a train/ or heldout/ folder under inputs (TSAI's cleaned
    output), only the parts under those folders, and part is the path under the split folder, as overlap.py names it.
    Otherwise (the raw <pack>/Part_N/ layout) every part, part is the path under inputs, and a folder named heldout, in
    any case, makes a part held-out. Pack identity comes only from each row's pack_id."""
    if not inputs.is_dir():
        sys.exit(f"ERROR: no input folder {inputs}")
    roots = [(s, inputs / s) for s in SPLITS if (inputs / s).is_dir()] or [(None, inputs)]
    parts = []
    for split, root in roots:
        for path in sorted(root.rglob("*.parquet")):
            rel = path.relative_to(root)
            if path.is_file() and not any(c.startswith(".") for c in rel.parts):
                s = split or ("heldout" if any(c.lower() == "heldout" for c in rel.parts[:-1]) else "train")
                parts.append((s, rel.as_posix(), path))
    if not parts:
        sys.exit(f"ERROR: no Parquet parts under {inputs}")
    return parts


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def peak_rss_mb():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss   # bytes on macOS, KiB on Linux
    return round(r / (1 << 20) if sys.platform == "darwin" else r / 1024, 1)


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def histogram(values):
    """Counts in 100 bins of 0.01 over [0, 1]; values below 0 go to the first bin."""
    v = np.clip(np.asarray(values, dtype=np.float64), 0.0, 1.0)
    return np.bincount(np.minimum((v * 100 + 1e-9).astype(np.int64), 99), minlength=100)


class Encoder:
    """The sentence-transformers model in model_path, loaded offline. encode() returns unit float32 rows."""

    def __init__(self, cfg):
        os.environ["HF_HUB_OFFLINE"] = "1"         # never download: the model must already be in model_path
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        path = REPO / cfg["model_path"]
        if not cfg["model_path"] or not path.is_dir():
            sys.exit(f"ERROR: model_path {cfg['model_path']!r} is not a local folder; the model is never downloaded")
        try:
            import torch
            import sentence_transformers
            from sentence_transformers import SentenceTransformer
        except ImportError:
            sys.exit("ERROR: needs torch and sentence-transformers: "
                     "python3 -m pip install -r teams/01-data-a/dedup/requirements_h3.txt")
        device = cfg["device"]
        if device == "auto":
            device = ("cuda" if torch.cuda.is_available()
                      else "mps" if torch.backends.mps.is_available() else "cpu")
        self.model = SentenceTransformer(str(path), device=device)
        self.model.max_seq_length = cfg["max_seq_length"]
        self.batch_size = cfg["batch_size"]
        weights = {p.relative_to(path).as_posix(): {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
                   for p in sorted(path.rglob("*")) if p.is_file() and p.suffix in (".safetensors", ".bin")
                   and ".cache" not in p.relative_to(path).parts}
        config_sha = sha256_file(path / "config.json") if (path / "config.json").is_file() else ""
        self.info = {"path": cfg["model_path"], "name": path.name, "device": device,
                     "max_seq_length": cfg["max_seq_length"], "dim": self.model.get_sentence_embedding_dimension(),
                     "config_sha256": config_sha, "weights": weights,
                     "torch": torch.__version__, "sentence_transformers": sentence_transformers.__version__}
        self.id = hashlib.sha256(json.dumps([config_sha, weights, cfg["max_seq_length"]],
                                            sort_keys=True).encode()).hexdigest()

    def encode(self, texts):
        v = self.model.encode(list(texts), batch_size=self.batch_size, convert_to_numpy=True,
                              normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(v, dtype=np.float32)


def encode(encoder, texts, clock, stats, counter):
    """Encode in chunks of CHUNK texts, checking the time limit before each."""
    out = []
    for lo in range(0, len(texts), CHUNK):
        clock.check()
        out.append(unit(encoder.encode(texts[lo:lo + CHUNK])))
        stats[counter] += len(texts[lo:lo + CHUNK])
    return np.concatenate(out)


def encode_heads(encoder, heads, rows, path, cfg, cache, clock, stats):
    """One vector per document of a part; from the cache when the same encoder, part bytes, settings and rows were
    encoded before."""
    file = None
    if cache:
        with clock.stage("cache"):
            settings = {k: cfg[k] for k in ("min_chars", "min_sentences", "sentence_min_chars", "head_sentences",
                                            "max_sentences")}
            h = hashlib.sha256()
            for piece in (encoder.id, sha256_file(path), json.dumps(settings, sort_keys=True)):
                h.update(piece.encode())
            h.update(np.asarray(rows, dtype=np.int64).tobytes())
            file = cache / f"{h.hexdigest()}.npy"
            if file.is_file():
                v = np.load(file)
                if len(v) == len(heads):
                    stats["cached_parts"] += 1
                    return unit(v)
    with clock.stage("encode"):
        v = encode(encoder, heads, clock, stats, "encoded_heads")
    if file is not None:
        cache.mkdir(parents=True, exist_ok=True)
        np.save(file, v.astype(np.float16))
    return v


def read_texts(todo, D, part_paths, cfg, clock):
    """For the documents of the pairs to verify: (sentences, numbers, Latin tokens), from one more pass over their
    parts. Text is held only for these documents, and never written."""
    need = defaultdict(dict)   # (split, part) -> {row_in_part: document row}; a part name can be in both splits
    for a, b, *_ in todo:
        for d in (a, b):
            need[(D["split"][d], D["part"][d])][D["row_in_part"][d]] = d
    info = {}
    for key, rows in need.items():
        last, row = max(rows), 0
        for batch in pq.ParquetFile(part_paths[key]).iter_batches(batch_size=1000, columns=["text"]):
            clock.check()
            for text in batch.column(0).to_pylist():
                if row in rows:
                    text = text if isinstance(text, str) else ""
                    info[rows[row]] = (split_sentences(text, cfg["sentence_min_chars"], cfg["max_sentences"]),
                                       numbers(text), latin_tokens(text))
                row += 1
            if row > last:
                break
    return info


def estimate(cfg, clock, stats, D, rows_total, seen, taken, verified):
    """The time for every document of the selected packs, from this run's rates: read scales with rows, encode with
    documents, retrieve with the product of the two languages' documents, verify with the smaller language's documents
    (at most max_verify pairs)."""
    st = clock.stages
    now, full = Counter(D["lang"]), Counter()
    for pack, rows in rows_total.items():
        if seen[pack]:
            full[lang_of(pack, cfg["packs"])] += rows * taken[pack] / seen[pack]
    product = lambda c: sum(c[a] * c[b] for a, b in cfg["pairs"])
    smaller = lambda c: sum(min(c[a], c[b]) for a, b in cfg["pairs"])
    scanned, total_rows = stats["rows_scanned"], sum(rows_total.values())
    sec = {"load_model": st.get("load_model", 0.0),
           "read": st.get("read", 0.0) * total_rows / scanned if scanned else None,
           "encode": (st["encode"] / stats["encoded_heads"] * sum(full.values())
                      if stats["encoded_heads"] and st.get("encode") else None),
           "retrieve": st.get("retrieve", 0.0) * product(full) / product(now) if product(now) else None}
    pairs_full = min(cfg["max_verify"], verified * smaller(full) / smaller(now)) if smaller(now) else 0
    verify_time = st.get("verify_read", 0.0) + st.get("verify", 0.0)
    sec["verify"] = verify_time / verified * pairs_full if verified else None
    known = [v for v in sec.values() if v is not None]
    total = sum(known)
    return {"documents_encoded": dict(now), "documents_full": {k: round(v) for k, v in full.items()},
            "seconds": {k: (round(v, 1) if v is not None else None) for k, v in sec.items()},
            "minutes_total": round(total / 60, 1), "every_stage_measured": len(known) == len(sec),
            "suggested_max_time_minutes": math.ceil(1.5 * total / 60) if known else None,
            "basis": "this run's rates; read scales with rows, encode with documents, retrieve with the product of the "
                     "two languages' documents, verify with the smaller language's documents (at most max_verify)"}


def run(cfg, encoder, clock, stats, summary):
    inputs, out = REPO / cfg["inputs"], REPO / cfg["out"]
    cache = REPO / cfg["cache"] if cfg["cache"] else None
    parts = find_parts(inputs)

    # 1. Select the parts by their pack_id column, then read them: sentences, length, URL key, and the head to encode.
    selected, rows_total = [], Counter()
    with clock.stage("read"):
        for split, name, path in parts:
            pf = pq.ParquetFile(path)
            missing = {"pack_id", "doc_id", "text"} - set(pf.schema_arrow.names)
            if missing:
                sys.exit(f"ERROR: {path} has no {sorted(missing)} column (it has {pf.schema_arrow.names})")
            counts = Counter(pf.read(columns=["pack_id"]).column(0).to_pylist())
            keep = {p for p in counts if isinstance(p, str) and lang_of(p, cfg["packs"])}
            if keep:
                selected.append((split, name, path, keep, "url" in pf.schema_arrow.names))
                for p in keep:
                    rows_total[p] += counts[p]
    if not selected:
        sys.exit(f"ERROR: no part under {inputs} holds a pack matching {sorted(cfg['packs'])}")
    print(f"{len(selected)} of {len(parts)} parts hold a configured pack: {', '.join(sorted(rows_total))}", flush=True)

    D = {k: [] for k in ("pack", "lang", "split", "part", "row_in_part", "doc_id", "chars", "sentences", "url")}
    vectors, seen, short, taken, limit = [], Counter(), Counter(), Counter(), cfg["max_docs_per_pack"]
    for split, name, path, keep, has_url in selected:
        heads, rows = [], []
        with clock.stage("read"):
            columns = ["pack_id", "doc_id", "text"] + (["url"] if has_url else [])
            row = 0
            for batch in pq.ParquetFile(path).iter_batches(batch_size=1000, columns=columns):
                clock.check()
                values = [batch.column(c).to_pylist() for c in columns]
                for k in range(batch.num_rows):
                    r, row, pack = row, row + 1, values[0][k]
                    if pack not in keep or (limit and taken[pack] >= limit):
                        continue
                    doc_id = values[1][k]
                    if not isinstance(doc_id, str) or not doc_id.strip():
                        sys.exit(f"ERROR: {path} row {r} has invalid doc_id {doc_id!r}")
                    text = values[2][k] if isinstance(values[2][k], str) else ""
                    seen[pack] += 1
                    sentences = split_sentences(text, cfg["sentence_min_chars"], cfg["max_sentences"])
                    if len(text) < cfg["min_chars"] or len(sentences) < cfg["min_sentences"]:
                        short[pack] += 1
                        continue
                    taken[pack] += 1
                    for column, value in (("pack", pack), ("lang", lang_of(pack, cfg["packs"])), ("split", split),
                                          ("part", name), ("row_in_part", r), ("doc_id", doc_id),
                                          ("chars", len(text)), ("sentences", len(sentences)),
                                          ("url", url_key(values[3][k])[0] if has_url else None)):
                        D[column].append(value)
                    heads.append(" ".join(sentences[:cfg["head_sentences"]]))
                    rows.append(r)
                stats["rows_scanned"] += batch.num_rows
                if limit and all(taken[p] >= limit for p in keep):
                    break
        if heads:
            vectors.append(encode_heads(encoder, heads, rows, path, cfg, cache, clock, stats))
        print(f"{split}/{name}: {len(heads)} documents encoded or cached ({clock.elapsed():.0f}s)", flush=True)
    N = len(D["pack"])
    if N < 2:
        sys.exit(f"ERROR: {N} document(s) long enough to compare")
    V = np.concatenate(vectors)
    lang = np.array(D["lang"])
    pairset = {frozenset(p) for p in cfg["pairs"]}
    cands = {}   # (row_a, row_b) with row_a < row_b -> [document cosine, how it was found]

    # 2. URL: the same page in two languages, by an exact join on the language-neutral URL key.
    url_stats = Counter()
    with clock.stage("url"):
        groups = defaultdict(list)
        for i, key in enumerate(D["url"]):
            if key:
                groups[key].append(i)
        for group in groups.values():
            if len(group) < 2:
                continue
            url_stats["groups_with_2_or_more"] += 1
            if len(group) > cfg["url_group_max"]:
                url_stats["groups_over_url_group_max"] += 1
                continue
            for a, b in combinations(group, 2):
                if frozenset((D["lang"][a], D["lang"][b])) in pairset:
                    cands.setdefault((a, b), [float(V[a] @ V[b]), set()])[1].add("url")
                    url_stats["pairs"] += 1

    # 3. Retrieve: each document's top_k nearest documents in the other language.
    hist_cos, retrieved = np.zeros(100, np.int64), {}
    with clock.stage("retrieve"):
        for la, lb in cfg["pairs"]:
            ia, ib = np.flatnonzero(lang == la), np.flatnonzero(lang == lb)
            name = f"{la}-{lb}"
            retrieved[name] = {"documents_a": int(len(ia)), "documents_b": int(len(ib)), "pairs_in_top_k": 0, "kept": 0}
            if not len(ia) or not len(ib):
                continue
            i, j, cos, side = cross_topk(V[ia], V[ib], cfg["top_k"], cfg["block"], clock.check)
            hist_cos += histogram(cos)
            keep = cos >= cfg["doc_floor"]
            if cfg["mutual"]:
                keep &= side == 3
            for x, y, c in zip(ia[i[keep]].tolist(), ib[j[keep]].tolist(), cos[keep].tolist()):
                cands.setdefault((min(x, y), max(x, y)), [c, set()])[1].add("embedding")
            retrieved[name].update(pairs_in_top_k=int(len(cos)), kept=int(keep.sum()))
            print(f"retrieve {name}: {len(ia)} x {len(ib)} documents, {int(keep.sum())} candidates "
                  f"({clock.elapsed():.0f}s)", flush=True)

    # 4. Verify: URL pairs first, then by cosine; sentence alignment of each pair.
    todo, too_long = [], 0
    for (a, b), (cos, found) in sorted(cands.items(), key=lambda kv: ("url" not in kv[1][1], -kv[1][0], kv[0])):
        ratio = length_ratio(D["chars"][a], D["chars"][b])
        if ratio > cfg["max_length_ratio"] and "url" not in found:
            too_long += 1
            continue
        todo.append((a, b, cos, "+".join(sorted(found)), ratio))
    not_verified = max(0, len(todo) - cfg["max_verify"])
    todo = todo[:cfg["max_verify"]]
    part_paths = {(split, name): path for split, name, path, _, _ in selected}
    with clock.stage("verify_read"):
        info = read_texts(todo, D, part_paths, cfg, clock)
    results, hist_cov, vecs = [], np.zeros(100, np.int64), {}
    with clock.stage("verify"):
        for lo in range(0, len(todo), PAIR_CHUNK):
            chunk = todo[lo:lo + PAIR_CHUNK]
            missing = sorted({d for a, b, *_ in chunk for d in (a, b) if d not in vecs})
            texts = [s for d in missing for s in info[d][0]]
            if texts:
                V2, offset = encode(encoder, texts, clock, stats, "encoded_sentences"), 0
                for d in missing:
                    vecs[d] = V2[offset:offset + len(info[d][0])]
                    offset += len(info[d][0])
            for a, b, cos, found, ratio in chunk:
                (sa, na_, la_), (sb, nb_, lb_) = info[a], info[b]
                aligned, mean = align(vecs[a], vecs[b], cfg["sentence_threshold"])
                coverage = aligned / min(len(sa), len(sb)) if min(len(sa), len(sb)) else 0.0
                results.append((a, b, cos, found, ratio, multiset_jaccard(na_, nb_), latin_share(la_, lb_),
                                len(sa), len(sb), aligned, coverage, mean, coverage >= cfg["coverage_threshold"]))
            if len(vecs) > SENTENCE_CACHE:
                vecs.clear()
            print(f"verify: {min(lo + PAIR_CHUNK, len(todo))}/{len(todo)} pairs ({clock.elapsed():.0f}s)", flush=True)
        hist_cov += histogram([r[10] for r in results]) if results else 0

    # 5. Outputs, all inside ./out/: IDs, scores and counts only.
    out.mkdir(parents=True, exist_ok=True)
    ids = [f"{p}-{d}" for p, d in zip(D["pack"], D["doc_id"])]
    pq.write_table(pa.table({"row": np.arange(N), "id": ids, "doc_id": D["doc_id"], "pack": D["pack"],
                             "lang": D["lang"], "split": D["split"], "part": D["part"],
                             "row_in_part": D["row_in_part"], "chars": D["chars"], "sentences": D["sentences"]}),
                   out / "h3_docs.parquet", compression="zstd")
    fmt = lambda x: "" if x is None else f"{x:.6f}"
    listed = sorted((r for r in results if r[10] >= cfg["report_floor"] or "url" in r[3]),
                    key=lambda r: (-r[10], -r[2], r[0], r[1]))
    write_csv(out / "h3_candidates.csv",
              ["row_a", "row_b", "id_a", "id_b", "pack_a", "pack_b", "lang_a", "lang_b", "split_a", "split_b",
               "found_by", "doc_cosine", "length_ratio", "numbers_jaccard", "latin_share", "sentences_a",
               "sentences_b", "aligned", "coverage", "mean_sentence_cosine", "qualifies"],
              ([a, b, ids[a], ids[b], D["pack"][a], D["pack"][b], D["lang"][a], D["lang"][b], D["split"][a],
                D["split"][b], found, fmt(cos), f"{ratio:.3f}", fmt(nj), fmt(ls), n_a, n_b, n, f"{cov:.6f}",
                fmt(mean), q] for a, b, cos, found, ratio, nj, ls, n_a, n_b, n, cov, mean, q in listed))
    matches = [r for r in listed if r[12]]
    key = lambda d: [D["pack"][d], D["split"][d], D["part"][d], D["row_in_part"][d], D["doc_id"][d]]
    write_csv(out / "h3_matches.csv", MATCHES_HEADER,
              ([*key(r[0]), *key(r[1]), D["lang"][r[0]], D["lang"][r[1]], f"{r[10]:.6f}"] for r in matches))
    grid = defaultdict(Counter)
    pack_pair = lambda a, b: tuple(sorted((D["pack"][a], D["pack"][b])))
    for (a, b), (_, found) in cands.items():
        for how in found:
            grid[pack_pair(a, b)][how] += 1
    for r in results:
        grid[pack_pair(r[0], r[1])]["verified"] += 1
        grid[pack_pair(r[0], r[1])]["listed"] += r[10] >= cfg["report_floor"] or "url" in r[3]
        grid[pack_pair(r[0], r[1])]["qualifying"] += r[12]
    write_csv(out / "h3_by_pack.csv", ["pack_a", "pack_b", "retrieved", "url", "verified", "listed", "qualifying"],
              ([pa_, pb_, c["embedding"], c["url"], c["verified"], c["listed"], c["qualifying"]]
               for (pa_, pb_), c in sorted(grid.items())))
    write_csv(out / "h3_histogram.csv", ["from", "to", "retrieved_pairs_doc_cosine", "verified_pairs_coverage"],
              ([f"{b / 100:.2f}", f"{(b + 1) / 100:.2f}", int(hist_cos[b]), int(hist_cov[b])] for b in range(100)))

    files = {f: {"bytes": (out / f).stat().st_size, "sha256": sha256_file(out / f)} for f in OUTPUTS}
    output_bytes = sum(v["bytes"] for v in files.values())
    by_lang = Counter(f"{D['lang'][r[0]]}-{D['lang'][r[1]]}" for r in matches)
    summary.update({
        "status": "complete",
        "inputs": {"root": cfg["inputs"], "parts_found": len(parts), "parts_selected": len(selected),
                   "parts": [f"{s}/{n}" for s, n, *_ in selected]},
        "documents": {p: {"lang": lang_of(p, cfg["packs"]), "rows_in_parts": rows_total[p], "read": seen[p],
                          "too_short": short[p], "encoded": taken[p]} for p in sorted(rows_total)},
        "documents_compared": N,
        "url": dict(url_stats),
        "retrieved": retrieved,
        "candidates": len(cands),
        "rejected_length_ratio": too_long,
        "not_verified_over_max_verify": not_verified,
        "verified": len(results),
        "listed": len(listed),
        "qualifying": len(matches),
        "qualifying_heldout_train": sum(1 for r in matches if {D["split"][r[0]], D["split"][r[1]]} == {"train", "heldout"}),
        "qualifying_by_language_pair": dict(by_lang),
        "rule": {"h3": f"aligned sentences / sentences of the shorter document >= {cfg['coverage_threshold']}; "
                       f"a sentence pair aligns when each is the other's best match with cosine >= "
                       f"{cfg['sentence_threshold']}",
                 "thresholds": "provisional: set by E5's sweep and hand review"},
        "counts": dict(stats),
        "stages_seconds": dict(clock.stages),
        "rates": {"heads_per_second": (round(stats["encoded_heads"] / clock.stages["encode"], 1)
                                       if clock.stages.get("encode") else None),
                  "sentences_per_second": (round(stats["encoded_sentences"] / clock.stages["verify"], 1)
                                           if clock.stages.get("verify") else None)},
        "estimate_all_documents": estimate(cfg, clock, stats, D, rows_total, seen, taken, len(results)),
        "wall_seconds": round(clock.elapsed(), 1),
        "peak_rss_mb": peak_rss_mb(),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pyarrow": pa.__version__,
                     "platform": platform.platform()},
        "outputs": files,
        "output_mb": round(output_bytes / (1 << 20), 2),
    })
    (out / "h3_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    shown = ("documents_compared", "url", "retrieved", "candidates", "verified", "qualifying",
             "qualifying_heldout_train", "qualifying_by_language_pair", "stages_seconds", "rates",
             "estimate_all_documents", "wall_seconds", "peak_rss_mb")
    print(json.dumps({k: summary[k] for k in shown}, indent=2))
    print(f"\nWrote {', '.join(OUTPUTS)} and h3_summary.json to {out.relative_to(REPO)}")
    if output_bytes + (out / "h3_summary.json").stat().st_size > cfg["max_output_mb"] * (1 << 20):
        summary["status"] = "failed_output_limit"
        (out / "h3_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        sys.exit(f"ERROR: the outputs are over max_output_mb {cfg['max_output_mb']}; job failed")


def main(encoder=None):
    """encoder: for the tests, an object with .id, .info and .encode(texts); by default the model in model_path."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="JSON config; see CONFIG above")
    cfg = load_config(ap.parse_args().config)
    if np is None:
        sys.exit("ERROR: needs numpy and pyarrow: python3 -m pip install -r teams/01-data-a/dedup/requirements_h3.txt")
    clock, stats, out = Clock(cfg["max_minutes"]), Counter(), REPO / cfg["out"]
    summary = {"status": "running", "config": cfg}
    try:
        if encoder is None:
            with clock.stage("load_model"):
                encoder = Encoder(cfg)
        summary["model"] = encoder.info
        run(cfg, encoder, clock, stats, summary)
    except TimeLimit:
        out.mkdir(parents=True, exist_ok=True)
        for f in OUTPUTS:                     # no output of an earlier run may sit beside this summary
            (out / f).unlink(missing_ok=True)
        summary.update(status="stopped_time_limit", counts=dict(stats), stages_seconds=dict(clock.stages),
                       wall_seconds=round(clock.elapsed(), 1), peak_rss_mb=peak_rss_mb())
        (out / "h3_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        sys.exit(f"ERROR: stopped at max_minutes {cfg['max_minutes']}; the run is incomplete and must not be used")


if __name__ == "__main__":
    sys.exit(main())
