r"""E5d, the blind reader sheets for H3's threshold sweep (h3_design_v1.md, "Validation").

Bilingual readers label candidate pairs of finished h3.py runs as translations or not, blind, on both sides of the
coverage threshold; their labels set the thresholds per language pair. For the Sanskrit pairs the candidates of two
encoders are pooled (LaBSE in E5c, theschoolofai/era-v5-lab#625; BGE-M3 in theschoolofai/era-v5-lab#666; TSAI on
theschoolofai/era-v5-lab#626: E5d labels both encoders' candidates). A pair that either encoder listed is read once,
and the key holds each encoder's scores, so one label scores both encoders.

HOW TO RUN IT
=============
numpy and pyarrow, and h3.py's own reader (requirements_h3.txt); no model and no network. Paths in the config are
relative to the repository root, and it writes only to out/ in the repository root.

    python teams/01-data-a/dedup/h3_e5d_sheets.py --config teams/01-data-a/dedup/h3_e5d_flores_sheets.json

STAGES
======
  load      each run's h3_candidates.csv and h3_docs.parquet (the run must be complete). Each pair is named by its
            configured language pair and put in that pair's order: side a is in the pair's first language
  sample    per language pair, coverage band and encoder: pairs at random (seeded), per_band per band split evenly
            between the encoders that listed the pair's language pair; a pair already drawn is not drawn again.
            With "buckets" instead: per language pair and bucket, n pairs from the bucket's bands in order: a band
            whose pairs all fit is taken whole (every encoder's, each pair once, e.g. every qualifying pair), else the
            rest is drawn at random, split evenly between the encoders and topped up from any of them
  controls  per language pair, n_controls pairs of known answer from the controls file (for example same-topic pages
            that are not translations), mixed in blind
  texts     each document's text from inputs, read as h3.py read it and checked against the run's character counts;
            each side is shown as the sentences h3.py scored, one per line: sentence_min_chars and max_sentences come
            from the runs' h3_summary.json, and runs that split sentences differently are refused
  blind     items get IDs in a random order, the two sides of each item are swapped at random, and every reader gets
            the items in their own order

CONFIG (JSON; keys starting with "_" are comments)
==================================================
  runs        {encoder: h3.py output folder}, e.g. {"labse": "...", "bge-m3": "..."}; every run read the same inputs
  inputs      the inputs those runs read (h3.py's "inputs")
  controls    "" (none), or a Parquet file with pair ("sa-en"), text_a (in the pair's first language), text_b, expected
              ("yes" or "no") and source
  out         the output folder, inside out/
  pairs       the language pairs, e.g. [["sa", "en"], ["sa", "hi"], ["hi", "en"], ["or", "en"]]
  bands       coverage band edges, e.g. [0.3, 0.45, 0.6, 0.75, 1.0]: the bands either side of the 0.6 threshold
  per_band    pairs drawn per band; one count for every language pair, or a {language pair: count} map that names
              each pair (either order), e.g. {"sa-en": 20, "sa-hi": 20, "hi-en": 10, "or-en": 10}
  buckets     instead of bands and per_band: {bucket: {"bands": [[low, high], ...], "n": count or per-pair map}}, e.g.
              {"above": {"bands": [[0.6, 1.0], [0.45, 0.6]], "n": {"sa-en": 18, "sa-hi": 20, "hi-en": 25}},
               "below": {"bands": [[0.3, 0.45]], "n": {"sa-en": 17, "sa-hi": 19, "hi-en": 25}}}
              (a band holds coverage low <= c < high, and c = 1.0 when high is 1.0); the key then has a bucket column
  n_controls  controls per language pair; one count, or a map as for per_band
  readers, seed

WHAT IT WRITES (in out)
=======================
  sheets/<pair>_reader<k>.csv  what reader k gets: item, text_1, text_2, translation, note (translation and note empty;
                               UTF-8 with a byte-order mark, so spreadsheets show the scripts)
  readers_guide.md             what to answer for each item; it goes to the readers with the sheets
  key/<pair>_key.csv           for each item: source (candidate or control), band (and bucket, with "buckets"), the
                               encoder it was drawn for, which side is text_1, both documents (pack, split, doc_id,
                               lang), the control's expected label, and each encoder's coverage, cosines, signals and
                               found_by (empty where it did not list the pair). Never shown to readers
  key/sentences.parquet        the sentences shown, per item and side, for the sentence-threshold sweep
  e5d_summary.json             counts per language pair, band and encoder (in the band, drawn, wanted; with "buckets",
                               per language pair, bucket and band: available, drawn per encoder), shortfalls,
                               the runs' sentence settings, the seed, the inputs' and outputs' sha256 and the stage
                               times: IDs and counts only

The sheets and sentences.parquet hold document text: they stay in out/ and are never committed.

SPEED (TSAI rule, 14 Nov)
=========================
pyarrow compute and numpy over whole columns: no Python loop over rows, documents, sentences or pairs. Python loops
remain over the runs, the language pairs, bands and encoders (the strata), the readers and the parts read.
"""
import sys
sys.dont_write_bytecode = True   # write only to ./out/: no __pycache__ beside the scripts

import argparse, json, platform, re, time  # noqa: E401,E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.compute as pc  # noqa: E402
import pyarrow.csv as pacsv  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

import h3  # noqa: E402  find_parts and read_texts: the documents exactly as h3.py read them
from h3_signals import sentences_batch  # noqa: E402

REPO = Path(__file__).resolve().parents[3]   # teams/01-data-a/dedup/h3_e5d_sheets.py -> the repository root
DEFAULTS = {"runs": {}, "inputs": "", "controls": "", "out": "out/e5d", "pairs": [],
            "bands": [0.3, 0.45, 0.6, 0.75, 1.0], "per_band": 20, "n_controls": 10, "readers": 2, "seed": 20261122,
            "buckets": None}
SENTENCE_SETTINGS = ("sentence_min_chars", "max_sentences")   # how h3.py split the sentences it scored
SHEET_COLUMNS = ["item", "text_1", "text_2", "translation", "note"]
SIDE = ("row", "id", "pack", "lang", "split", "sentences")          # h3_candidates.csv columns with _a and _b
SCORES = ("coverage", "doc_cosine", "mean_sentence_cosine", "length_ratio", "numbers_jaccard", "latin_share",
          "aligned", "qualifies", "found_by")
STRINGS = ("id_a", "id_b", "pack_a", "pack_b", "lang_a", "lang_b", "split_a", "split_b", "found_by")
DOC_COLUMNS = ("row", "doc_id", "pack", "lang", "split", "part", "row_in_part", "chars")
CONTROL_COLUMNS = ("pair", "text_a", "text_b", "expected", "source")
ITEM_COLUMNS = ["pair", "source", "band", "bucket", "drawn_for", "pair_id", "expected", "control_source",
                "pack_a", "split_a", "doc_id_a", "lang_a", "sentences_a", "text_a",
                "pack_b", "split_b", "doc_id_b", "lang_b", "sentences_b", "text_b"]
BOM = b"\xef\xbb\xbf"
GUIDE = """# E5d: what to answer for each item

Each item shows two texts in two panels, `text_1` and `text_2`, in two languages. Each text is the start of a web
page: its sentences, one per line, with very short lines (menus, headings) left out.

For each item, answer one of these (in the viewer: the buttons, or the keys y, n and u; in a spreadsheet: the
`translation` column):

- `yes`: one text is a translation of the other. Most sentences of the shorter text have a sentence with the same
  meaning in the other one. A loose translation, or one text being longer, is still `yes`.
- `no`: not a translation, even if both are about the same topic, event or person, or share names and numbers.
- `unsure`: you cannot tell.

Use the note for anything else, for example "only the first half is translated".

Read on your own. Do not compare with another reader, and do not look the texts up.
"""


class _Clock:
    """h3.read_texts checks a time limit between parts; the sheets have none."""

    def check(self):
        pass


def bools(x):
    return np.asarray(pc.fill_null(x, False).to_numpy(zero_copy_only=False), dtype=bool)


def column(table, name):
    return table.column(name).combine_chunks()


def const(value, n):
    """A string array of n copies of value."""
    return pa.repeat(pa.scalar(value, pa.string()), n)


def ints(table, name):
    return np.asarray(column(table, name).to_numpy(zero_copy_only=False), dtype=np.int64)


def floats(table, name):
    return np.asarray(pc.fill_null(pc.cast(column(table, name), pa.float64()), np.nan).to_numpy(), dtype=np.float64)


def repo_path(cfg, name):
    if not isinstance(cfg[name], str) or not cfg[name] or Path(cfg[name]).is_absolute():
        sys.exit(f"ERROR: {name} must be a path relative to the repository root")
    return REPO / cfg[name]


def load_config(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    unknown = sorted(k for k in raw if not k.startswith("_") and k not in DEFAULTS)
    if unknown:
        sys.exit(f"ERROR: unknown keys in {path}: {unknown}")
    cfg = {**DEFAULTS, **{k: v for k, v in raw.items() if not k.startswith("_")}}
    runs = cfg["runs"]
    if not isinstance(runs, dict) or not runs or any(not isinstance(k, str) or not k.strip() for k in runs):
        sys.exit("ERROR: runs must be a nonempty {encoder: h3.py output folder} map")
    for name in runs.values():
        if not isinstance(name, str) or not name or Path(name).is_absolute():
            sys.exit("ERROR: each run must be an h3.py output folder relative to the repository root")
    repo_path(cfg, "inputs")
    if cfg["controls"]:
        repo_path(cfg, "controls")
    if not repo_path(cfg, "out").resolve().is_relative_to((REPO / "out").resolve()):
        sys.exit(f"ERROR: out must be inside out/ in the repository root, not {cfg['out']!r}")
    pairs = cfg["pairs"]
    if (not isinstance(pairs, list) or not pairs
            or any(not isinstance(p, list) or len(p) != 2 or not all(isinstance(x, str) and x for x in p)
                   or p[0] == p[1] for p in pairs)
            or len({frozenset(p) for p in pairs}) != len(pairs)):
        sys.exit("ERROR: pairs must be distinct [language, language] pairs, e.g. [[\"sa\", \"en\"]]")
    b = cfg["bands"]
    if (not isinstance(b, list) or len(b) < 2 or not all(is_number(x) and 0 <= x <= 1 for x in b)
            or not all(np.diff(np.asarray(b, dtype=np.float64)) > 0)):
        sys.exit("ERROR: bands must be at least two increasing coverage values between 0 and 1")
    if type(cfg["readers"]) is not int or cfg["readers"] <= 0:
        sys.exit("ERROR: readers must be a positive integer")
    if type(cfg["seed"]) is not int or cfg["seed"] < 0:
        sys.exit("ERROR: seed must be a nonnegative integer")
    names = {**{f"{b}-{a}": f"{a}-{b}" for a, b in pairs}, **{f"{a}-{b}": f"{a}-{b}" for a, b in pairs}}
    cfg["per_band"] = per_pair(cfg["per_band"], names, 1, "per_band")
    cfg["n_controls"] = per_pair(cfg["n_controls"], names, 0, "n_controls")
    if cfg["buckets"] is not None:
        if {"bands", "per_band"} & set(raw):
            sys.exit("ERROR: buckets replace bands and per_band: give one or the other")
        cfg["buckets"] = check_buckets(cfg["buckets"], names)
    return cfg


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def per_pair(value, names, low, label):
    """One count for every language pair, or a {language pair: count} map naming each pair once (either order)."""
    if isinstance(value, dict):
        named = [names.get(k) for k in value]
        if None in named or len(set(named)) != len(named) or set(named) != set(names.values()):
            sys.exit(f"ERROR: a {label} map must name each language pair of pairs once (either order): "
                     f"{sorted(set(names.values()))}")
        value = {names[k]: v for k, v in value.items()}
    if not all(type(v) is int and v >= low for v in (value.values() if isinstance(value, dict) else [value])):
        sys.exit(f"ERROR: {label} must be {'a positive' if low else 'a nonnegative'} integer, or a map of them")
    return value


def check_buckets(value, names):
    """{bucket: {"bands": [[low, high], ...], "n": count or per-pair map}}, checked; bands as floats."""
    if not isinstance(value, dict) or not value:
        sys.exit('ERROR: buckets must be a nonempty {bucket: {"bands": [[low, high], ...], "n": count}} map')
    out = {}
    for bucket, spec in value.items():                            # the buckets
        if not isinstance(bucket, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", bucket):
            sys.exit(f"ERROR: bucket names must be lowercase words, not {bucket!r}")
        if not isinstance(spec, dict) or set(spec) != {"bands", "n"}:
            sys.exit(f'ERROR: bucket {bucket} needs exactly "bands" and "n"')
        bands = spec["bands"]
        if (not isinstance(bands, list) or not bands
                or not all(isinstance(r, list) and len(r) == 2 and all(is_number(x) for x in r)
                           and 0 <= r[0] < r[1] <= 1 for r in bands)):
            sys.exit(f"ERROR: bucket {bucket}: bands must be [low, high] coverage ranges, 0 <= low < high <= 1")
        out[bucket] = {"bands": [[float(lo), float(hi)] for lo, hi in bands],
                       "n": per_pair(spec["n"], names, 0, f"bucket {bucket} n")}
    return out


def count(cfg, name, pair):
    """per_band or n_controls for one language pair."""
    return for_pair(cfg[name], pair)


def for_pair(value, pair):
    return value[pair] if isinstance(value, dict) else value


def load_run(encoder, folder, pairs):
    """One finished h3.py run: its candidate pairs, named by language pair and put in the pair's order, and its
    documents. Pairs of languages not in pairs are dropped (and counted)."""
    folder = REPO / folder
    cand_path, docs_path, summary_path = (folder / f for f in ("h3_candidates.csv", "h3_docs.parquet",
                                                               "h3_summary.json"))
    for path in (cand_path, docs_path, summary_path):
        if not path.is_file():
            sys.exit(f"ERROR: run {encoder}: {path} is missing; runs must be h3.py output folders")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("status") != "complete":
        sys.exit(f"ERROR: run {encoder} has status {summary.get('status')!r}; only a complete h3.py run may be used")
    run_cfg = summary.get("config") or {}
    settings = {k: run_cfg.get(k) for k in SENTENCE_SETTINGS}
    if (type(settings["sentence_min_chars"]) is not int or settings["sentence_min_chars"] < 0
            or type(settings["max_sentences"]) is not int or settings["max_sentences"] <= 0):
        sys.exit(f"ERROR: run {encoder}: {summary_path} does not record h3.py's {' and '.join(SENTENCE_SETTINGS)}")
    types = {c: pa.string() for c in STRINGS} | {"row_a": pa.int64(), "row_b": pa.int64()}
    cand = pacsv.read_csv(cand_path, convert_options=pacsv.ConvertOptions(column_types=types))
    docs = pq.read_table(docs_path)
    missing = sorted(set(DOC_COLUMNS) - set(docs.column_names))
    if missing:
        sys.exit(f"ERROR: run {encoder}: {docs_path} lacks {missing}")
    if not np.array_equal(ints(docs, "row"), np.arange(docs.num_rows)):
        sys.exit(f"ERROR: run {encoder}: {docs_path} rows are not 0, 1, 2, ...")
    la, lb = column(cand, "lang_a"), column(cand, "lang_b")
    pair = np.full(cand.num_rows, -1, np.int64)
    swap = np.zeros(cand.num_rows, bool)
    for k, (x, y) in enumerate(pairs):                            # the configured language pairs
        rev = bools(pc.and_(pc.equal(la, y), pc.equal(lb, x)))
        pair[bools(pc.and_(pc.equal(la, x), pc.equal(lb, y))) | rev] = k
        swap |= rev
    keep = pair >= 0
    cand, pair, sw = cand.filter(pa.array(keep)), pair[keep], pa.array(swap[keep])
    cols = {"pair": pa.array(pair)}
    for s in SIDE:
        a, b = column(cand, f"{s}_a"), column(cand, f"{s}_b")
        cols[f"{s}_a"], cols[f"{s}_b"] = pc.if_else(sw, b, a), pc.if_else(sw, a, b)
    for s in SCORES:
        cols[s] = column(cand, s)
    key = {s: pc.binary_join_element_wise(cols[f"split_{s}"], cols[f"id_{s}"], "/") for s in "ab"}
    cols["pair_id"] = pc.binary_join_element_wise(key["a"], key["b"], "|")
    table = pa.table(cols)
    if pc.count_distinct(table["pair_id"]).as_py() != table.num_rows:
        sys.exit(f"ERROR: run {encoder}: {cand_path} lists a pair twice")
    return {"name": encoder, "folder": folder, "table": table, "docs": docs, "pair": pair, "settings": settings,
            "coverage": floats(table, "coverage"), "pair_id": column(table, "pair_id"),
            "dropped": int((~keep).sum()), "sha256": {p.name: h3.sha256_file(p) for p in (cand_path, docs_path)}}


def sample(runs, cfg, names, rng):
    """The drawn pairs: (run, row of its table, band label, bucket label or None) per pair, one count record per
    stratum, and the shortfalls."""
    if cfg["buckets"] is not None:
        return sample_buckets(runs, cfg, names, rng)
    edges, last = cfg["bands"], len(cfg["bands"]) - 2
    labels = np.array([f"{a:.2f}-{b:.2f}" for a, b in zip(edges, edges[1:])], dtype=object)
    run_ix, row_ix, band_ix, strata = [], [], [], []
    taken = pa.array([], pa.string())
    for k, name in enumerate(names):                              # strata: language pair, band, encoder
        encs = [e for e, r in enumerate(runs) if (r["pair"] == k).any()]
        if not encs:
            continue
        per = -(-count(cfg, "per_band", name) // len(encs))
        for b in range(last + 1):
            lo, hi = edges[b], edges[b + 1]
            for e in encs:
                r = runs[e]
                cov = r["coverage"]
                inband = (r["pair"] == k) & (cov >= lo) & ((cov < hi) | ((b == last) & (cov <= hi)))
                free = np.flatnonzero(inband & ~bools(pc.is_in(r["pair_id"], value_set=taken)))
                pick = np.sort(rng.choice(free, size=min(per, len(free)), replace=False)) if len(free) else free
                taken = pa.concat_arrays([taken, r["pair_id"].take(pa.array(pick, pa.int64()))])
                run_ix.append(np.full(len(pick), e))
                row_ix.append(pick)
                band_ix.append(np.full(len(pick), b))
                strata.append({"pair": name, "band": f"{lo:.2f}-{hi:.2f}", "encoder": r["name"],
                               "in_band": int(inband.sum()), "drawn": len(pick), "wanted": per})
    cat = lambda xs: np.concatenate(xs).astype(np.int64) if xs else np.zeros(0, np.int64)
    band_ix = cat(band_ix)
    return (cat(run_ix), cat(row_ix), labels[band_ix], np.full(len(band_ix), None, dtype=object), strata,
            [s for s in strata if s["drawn"] < s["wanted"]])


def sample_buckets(runs, cfg, names, rng):
    """sample() with "buckets": per language pair and bucket, n pairs from the bucket's bands, in order. A band whose
    free pairs all fit is taken whole, every encoder's, each pair once; otherwise the rest is drawn at random, split
    evenly between the encoders that listed the language pair, then topped up from any of them."""
    picks, strata, shortfalls = [], [], []
    state = {"taken": pa.array([], pa.string())}

    def free_rows(r, k, lo, hi):
        cov = r["coverage"]
        inband = (r["pair"] == k) & (cov >= lo) & ((cov < hi) | ((hi >= 1.0) & (cov <= hi)))
        return np.flatnonzero(inband & ~bools(pc.is_in(r["pair_id"], value_set=state["taken"])))

    def take(e, rows, label, bucket):
        state["taken"] = pa.concat_arrays([state["taken"], runs[e]["pair_id"].take(pa.array(rows, pa.int64()))])
        picks.append((e, rows, label, bucket))
        return len(rows)

    for k, name in enumerate(names):                              # the language pairs
        encs = [e for e, r in enumerate(runs) if (r["pair"] == k).any()]
        if not encs:
            continue
        for bucket, spec in cfg["buckets"].items():               # the buckets, in config order
            want = left = for_pair(spec["n"], name)
            for lo, hi in spec["bands"]:                          # the bucket's bands, in order
                label = f"{lo:.2f}-{hi:.2f}"
                free = {e: free_rows(runs[e], k, lo, hi) for e in encs}
                ids = pa.concat_arrays([runs[e]["pair_id"].take(pa.array(free[e], pa.int64())) for e in encs])
                available = pc.count_distinct(ids).as_py() if len(ids) else 0
                got = {runs[e]["name"]: 0 for e in encs}
                wanted = left
                if left and available <= left:                    # the whole band, each pair once
                    for e in encs:
                        got[runs[e]["name"]] += take(e, free_rows(runs[e], k, lo, hi), label, bucket)
                elif left:                                        # a random draw, split between the encoders
                    per = -(-left // len(encs))
                    for e in encs:
                        rows = free_rows(runs[e], k, lo, hi)
                        n = min(per, len(rows), left - sum(got.values()))
                        pick = np.sort(rng.choice(rows, size=n, replace=False)) if n else rows[:0]
                        got[runs[e]["name"]] += take(e, pick, label, bucket)
                    rest = left - sum(got.values())
                    if rest:                                      # top up from any encoder's free pairs
                        rows = [free_rows(runs[e], k, lo, hi) for e in encs]
                        enc = np.concatenate([np.full(len(r), e) for r, e in zip(rows, encs)]).astype(np.int64)
                        row = np.concatenate(rows).astype(np.int64)
                        pid = pa.concat_arrays([runs[e]["pair_id"].take(pa.array(r, pa.int64()))
                                                for r, e in zip(rows, encs)])
                        code = np.asarray(pc.index_in(pid, value_set=pc.unique(pid)), dtype=np.int64)
                        first = np.sort(np.unique(code, return_index=True)[1])   # each pair's first listing
                        pick = np.sort(rng.choice(first, size=min(rest, len(first)), replace=False))
                        for e in encs:                            # the encoders the top-up came from
                            mine = row[pick[enc[pick] == e]]
                            if len(mine):
                                got[runs[e]["name"]] += take(e, mine, label, bucket)
                n_drawn = sum(got.values())
                strata.append({"pair": name, "bucket": bucket, "band": label, "available": available,
                               "wanted": wanted, "drawn": n_drawn, "drawn_by_encoder": got})
                left -= n_drawn
            if left:
                shortfalls.append({"pair": name, "bucket": bucket, "wanted": want, "drawn": want - left})
    n = [len(p[1]) for p in picks]
    run_ix = np.repeat([p[0] for p in picks], n).astype(np.int64) if picks else np.zeros(0, np.int64)
    row_ix = np.concatenate([p[1] for p in picks]).astype(np.int64) if picks else np.zeros(0, np.int64)
    band = np.repeat(np.array([p[2] for p in picks], dtype=object), n) if picks else np.zeros(0, dtype=object)
    bucket = np.repeat(np.array([p[3] for p in picks], dtype=object), n) if picks else np.zeros(0, dtype=object)
    return run_ix, row_ix, band, bucket, strata, shortfalls


def read_documents(run, rows, parts):
    """The text of documents rows of run (rows of its h3_docs.parquet), read from inputs as h3.py read them, and
    checked against the character counts the run recorded."""
    docs = run["docs"]
    where = pc.binary_join_element_wise(column(docs, "split"), column(docs, "part"), "\t")
    pix = pc.index_in(where, value_set=parts["keys"]).take(pa.array(rows, pa.int64()))
    if not bools(pc.is_valid(pix)).all():
        k = int(rows[int(np.flatnonzero(~bools(pc.is_valid(pix)))[0])])
        sys.exit(f"ERROR: run {run['name']}: the part of document {column(docs, 'doc_id')[k].as_py()} is not under "
                 f"inputs")
    part_ix = np.zeros(docs.num_rows, np.int64)
    part_ix[rows] = np.asarray(pix.to_numpy(zero_copy_only=False), dtype=np.int64)
    texts = h3.read_texts(rows, part_ix, ints(docs, "row_in_part"), parts["paths"], _Clock())
    bad = np.flatnonzero(np.asarray(pc.utf8_length(texts), np.int64) != ints(docs, "chars")[rows])
    if len(bad):
        sys.exit(f"ERROR: run {run['name']}: {len(bad)} documents differ from what h3.py read (first: doc_id "
                 f"{column(docs, 'doc_id')[int(rows[bad[0]])].as_py()}); inputs must be the inputs of the runs")
    return texts


def scored_settings(runs):
    """The sentence settings every run used; runs that split sentences differently are refused, since one sheet
    shows each pair once."""
    first = runs[0]["settings"]
    for run in runs[1:]:                                          # the runs
        if run["settings"] != first:
            sys.exit(f"ERROR: runs {runs[0]['name']} and {run['name']} split sentences differently ({first} and "
                     f"{run['settings']}); the sheets need one setting")
    return first


def shown(texts, settings):
    """Each text as h3.py scored it, with the runs' settings: its sentences, as a list and as lines."""
    s, parent = sentences_batch(texts, settings["sentence_min_chars"], settings["max_sentences"])
    counts = np.bincount(parent, minlength=len(texts))
    offsets = pa.array(np.concatenate(([0], np.cumsum(counts))).astype(np.int32))
    lists = pa.ListArray.from_arrays(offsets, s.combine_chunks() if isinstance(s, pa.ChunkedArray) else s)
    return lists, pc.binary_join(lists, "\n")


def candidate_items(runs, run_ix, row_ix, band, bucket, names, parts, settings):
    """One row per drawn pair: its documents, the sentences shown, its band and bucket labels; in run order."""
    pieces = []
    for e, run in enumerate(runs):                                # the runs
        at = np.flatnonzero(run_ix == e)
        if not len(at):
            continue
        t = run["table"].take(pa.array(row_ix[at], pa.int64()))
        ra, rb = ints(t, "row_a"), ints(t, "row_b")
        rows = np.unique(np.concatenate([ra, rb]))
        lists, lines = shown(read_documents(run, rows, parts), settings)
        docs, n = run["docs"], len(at)
        piece = {"pair": pa.array(names, pa.string()).take(pa.array(ints(t, "pair"))),
                 "source": const("candidate", n),
                 "band": pa.array(band[at], pa.string()), "bucket": pa.array(bucket[at], pa.string()),
                 "drawn_for": const(run["name"], n), "pair_id": column(t, "pair_id"),
                 "expected": pa.nulls(n, pa.string()), "control_source": pa.nulls(n, pa.string())}
        for s, r in (("a", ra), ("b", rb)):
            ix = pa.array(np.searchsorted(rows, r), pa.int64())
            for c in ("pack", "split", "doc_id", "lang"):
                piece[f"{c}_{s}"] = column(docs, c).take(pa.array(r, pa.int64()))
            piece[f"sentences_{s}"], piece[f"text_{s}"] = lists.take(ix), lines.take(ix)
        pieces.append(pa.table(piece).select(ITEM_COLUMNS))
    return pieces


def control_items(cfg, names, rng, settings):
    """n_controls pairs of known answer per language pair, from the controls file, and the counts."""
    if not cfg["controls"] or not any(count(cfg, "n_controls", name) for name in names):
        return [], {}
    path = REPO / cfg["controls"]
    if not path.is_file():
        sys.exit(f"ERROR: no controls file {path}")
    t = pq.read_table(path)
    missing = sorted(set(CONTROL_COLUMNS) - set(t.column_names))
    if missing:
        sys.exit(f"ERROR: {path} lacks {missing}")
    expected = column(t, "expected")
    if not bools(pc.is_in(expected, value_set=pa.array(["yes", "no"]))).all():
        sys.exit(f"ERROR: {path}: expected must be yes or no")
    pair = column(t, "pair")
    if not bools(pc.is_in(pair, value_set=pa.array(names))).all():
        sys.exit(f"ERROR: {path}: pair must be one of {names}")
    pieces, counts = [], {}
    for k, name in enumerate(names):                              # the language pairs
        idx = np.flatnonzero(bools(pc.equal(pair, name)))
        want = count(cfg, "n_controls", name)
        pick = np.sort(rng.choice(idx, size=min(want, len(idx)), replace=False)) if len(idx) else idx
        counts[name] = {"available": len(idx), "drawn": len(pick), "wanted": want}
        if not len(pick):
            continue
        c = t.take(pa.array(pick, pa.int64()))
        n, (x, y) = len(pick), cfg["pairs"][k]
        none = pa.nulls(n, pa.string())
        piece = {"pair": const(name, n), "source": const("control", n), "band": const("control", n),
                 "bucket": const("control", n) if cfg["buckets"] is not None else none, "drawn_for": none, "pair_id": none, "expected": pc.cast(column(c, "expected"), pa.string()),
                 "control_source": pc.cast(column(c, "source"), pa.string())}
        for s, lang in (("a", x), ("b", y)):
            piece[f"pack_{s}"], piece[f"split_{s}"], piece[f"doc_id_{s}"] = none, none, none
            piece[f"lang_{s}"] = const(lang, n)
            piece[f"sentences_{s}"], piece[f"text_{s}"] = shown(column(c, f"text_{s}"), settings)
        pieces.append(pa.table(piece).select(ITEM_COLUMNS))
    return pieces, counts


def scores_by_encoder(items, runs):
    """Each encoder's scores for each item's pair: empty where that encoder did not list it (or for a control)."""
    out = {}
    for run in runs:                                              # the runs
        pos = pc.index_in(items["pair_id"], value_set=run["pair_id"])
        t = run["table"]
        for s in SCORES:
            out[f"{s}_{run['name']}"] = column(t, s).take(pos)
    return out


def write_csv(path, table, bom=False):
    buf = pa.BufferOutputStream()
    pacsv.write_csv(table, buf, write_options=pacsv.WriteOptions(quoting_style="needed"))
    path.write_bytes((BOM if bom else b"") + buf.getvalue().to_pybytes())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="JSON config; see CONFIG above")
    cfg = load_config(ap.parse_args(argv).config)
    if h3.np is None:
        sys.exit("ERROR: needs numpy, pyarrow and h3.py's packages: "
                 "python3 -m pip install -r teams/01-data-a/dedup/requirements_h3.txt")
    t0, seconds = time.perf_counter(), {}
    tick = lambda name: seconds.__setitem__(name, round(time.perf_counter() - t0 - sum(seconds.values()), 2))
    names = [f"{x}-{y}" for x, y in cfg["pairs"]]
    rng = np.random.default_rng(cfg["seed"])
    runs = [load_run(enc, folder, cfg["pairs"]) for enc, folder in cfg["runs"].items()]
    settings = scored_settings(runs)
    found = h3.find_parts(REPO / cfg["inputs"])
    parts = {"keys": pa.array([f"{s}\t{p}" for s, p, _ in found]), "paths": [path for _, _, path in found]}
    tick("load")
    run_ix, row_ix, band, bucket, strata, shortfalls = sample(runs, cfg, names, rng)
    tick("sample")
    pieces = candidate_items(runs, run_ix, row_ix, band, bucket, names, parts, settings)
    controls, control_counts = control_items(cfg, names, rng, settings)
    tick("texts")
    rows = pieces + controls
    out = REPO / cfg["out"]
    (out / "sheets").mkdir(parents=True, exist_ok=True)
    (out / "key").mkdir(parents=True, exist_ok=True)
    for old in list((out / "sheets").glob("*.csv")) + list((out / "key").glob("*")):   # no sheet of an earlier run
        old.unlink()
    items_total, sentence_tables = {}, []
    if rows:
        items = pa.concat_tables(rows, promote_options="default")
        for k, name in enumerate(names):                          # the language pairs
            sub = items.filter(pc.equal(items["pair"], name))
            n = sub.num_rows
            items_total[name] = n
            if not n:
                continue
            sub = sub.take(pa.array(rng.permutation(n)))
            item = pc.binary_join_element_wise(name, pc.utf8_lpad(pc.cast(pa.array(np.arange(1, n + 1)),
                                                                          pa.string()), 3, "0"), "-")
            flip = pa.array(rng.random(n) < 0.5)
            text_1 = pc.if_else(flip, column(sub, "text_b"), column(sub, "text_a"))
            text_2 = pc.if_else(flip, column(sub, "text_a"), column(sub, "text_b"))
            empty = const("", n)
            sheet = pa.table([item, text_1, text_2, empty, empty], names=SHEET_COLUMNS)
            assert sheet.column_names == SHEET_COLUMNS            # blind: text only, no score, ID or pack
            for r in range(1, cfg["readers"] + 1):                # the readers
                write_csv(out / "sheets" / f"{name}_reader{r}.csv", sheet.take(pa.array(rng.permutation(n))),
                          bom=True)
            key = {"item": item, "source": column(sub, "source"), "band": column(sub, "band")}
            if cfg["buckets"] is not None:                       # the per-band mode's key stays as it was
                key["bucket"] = column(sub, "bucket")
            key |= {"drawn_for": column(sub, "drawn_for"), "expected": column(sub, "expected"),
                   "control_source": column(sub, "control_source"),
                   "text_1_side": pc.if_else(flip, pa.scalar("b"), pa.scalar("a"))}
            for s in "ab":
                for c in ("pack", "split", "doc_id", "lang"):
                    key[f"{c}_{s}"] = column(sub, f"{c}_{s}")
            key |= scores_by_encoder({"pair_id": column(sub, "pair_id")}, runs)
            write_csv(out / "key" / f"{name}_key.csv", pa.table(key))
            sentence_tables.append(pa.table({"item": pa.concat_arrays([item, item]),
                                             "side": pa.concat_arrays([const("a", n), const("b", n)]),
                                             "sentences": pa.concat_arrays([column(sub, "sentences_a"),
                                                                            column(sub, "sentences_b")])}))
    if sentence_tables:
        pq.write_table(pa.concat_tables(sentence_tables), out / "key" / "sentences.parquet", compression="zstd")
    (out / "readers_guide.md").write_text(GUIDE, encoding="utf-8")
    tick("write")
    outputs = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "e5d_summary.json")
    summary = {
        "status": "complete", "config": cfg,
        "runs": {r["name"]: {"folder": r["folder"].relative_to(REPO).as_posix(), "sha256": r["sha256"],
                             "pairs_listed": {n: int((r["pair"] == k).sum()) for k, n in enumerate(names)},
                             "other_language_pairs_dropped": r["dropped"]} for r in runs},
        "strata": strata, "shortfalls": shortfalls,
        "controls": control_counts,
        "controls_sha256": h3.sha256_file(REPO / cfg["controls"]) if control_counts else None,
        "items": items_total, "readers": cfg["readers"], "sentence_settings": settings,
        "outputs": {p.relative_to(out).as_posix(): h3.sha256_file(p) for p in outputs},   # "/" on every OS
        "stages_seconds": seconds, "wall_seconds": round(time.perf_counter() - t0, 2),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pyarrow": pa.__version__}}
    (out / "e5d_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for name in names:
        drawn = sum(s["drawn"] for s in strata if s["pair"] == name)
        ctl = control_counts.get(name, {}).get("drawn", 0)
        print(f"{name}: {drawn} candidates and {ctl} controls -> {items_total.get(name, 0)} items, "
              f"{cfg['readers']} sheets", flush=True)
    print(f"e5d sheets: {sum(items_total.values())} items, {len(summary['shortfalls'])} "
          f"{'buckets' if cfg['buckets'] is not None else 'strata'} short "
          f"({summary['wall_seconds']} s); {out.relative_to(REPO)}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
