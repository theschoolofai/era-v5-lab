r"""Controls for E5d's reader sheets (h3_e5d_sheets.py, "controls"): ind-sa-fw2 same-page pairs whose answer is known,
mixed into the Sanskrit sheets blind, so that each reader's labels can be checked.

The pairs are build_known_pairs.py's 433 same-page pairs: a Sanskrit half and an English or Hindi half of one raw
ind-sa-fw2 page (known_pairs.parquet; h3_checks/). Most are the same topic but not translations, which is what a
reader must tell apart; a few are translations. The encoder checks of 15 and 16 Nov (labse_check.py, LaBSE and BGE-M3;
h3_labse_check_results_v1.md, h3_bge_m3_check_results_v1.md) scored every pair (pair_scores.csv), and pairs were read
by hand: 6 real translations, 3 not translations. So a control is one of:

  read_not_translation   a pair read by hand as not a translation (expected "no"); both encoders score these at the cut
  low_both_encoders      an unread pair far below every real translation on both encoders (expected "no"): BGE-M3
                         coverage at sentence threshold 0.5 at most --max-bge (the 6 real translations: 0.857 and up)
                         and LaBSE's below --max-labse (theirs: 0.3 and up)
  read_translation       with --positives: a pair read by hand as a real translation (expected "yes")

Left out: the real translations (unless --positives), and pairs of kind not_sanskrit (the "Sanskrit" half is Hindi).
Per language pair (sa-en, sa-hi: the translation half's language), the controls are the read non-translations, then
unread low pairs drawn at random (seeded) up to --per-pair, then, with --positives, the read translations. The unread
ones have not been read: they are listed in controls.json for a person to check before the sheets go out.

HOW TO RUN IT
=============
From the repository root (paths other than --out are relative to the current folder):

    python3 -I teams/01-data-a/dedup/h3_e5d_controls.py --out out/e5d_controls --known-pairs ../known_pairs.parquet \
        --real ../real_translations.csv --labse ../pair_scores_labse_bge_m3/labse_15nov/pair_scores.csv \
        --bge ../pair_scores_labse_bge_m3/bge_m3_16nov/pair_scores.csv \
        --not-translations fea1f4f3908e44b3 d0479a80829a2dc1 f4dd16e97e012036

WHAT IT WRITES (in --out, inside out/)
======================================
  controls.parquet   pair, text_a (the Sanskrit half), text_b, expected, source (kind of control, then the doc_id),
                     doc_id: h3_e5d_sheets.py's "controls" file. It holds page text and is never committed
  controls.json      the rule, the inputs' sha256, counts per language pair (pool, drawn, shortfall) and the doc_ids of
                     every control, the unread ones listed apart for the hand check: IDs and counts only

numpy and pyarrow only. No Python loop runs over rows or pairs: loops remain over the language pairs.
"""
import sys
sys.dont_write_bytecode = True

import argparse, hashlib, json  # noqa: E401,E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.compute as pc  # noqa: E402
import pyarrow.csv as pacsv  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

REPO = Path(__file__).resolve().parents[3]   # teams/01-data-a/dedup/h3_e5d_controls.py -> the repository root
PAIRS = {"en": "sa-en", "hi": "sa-hi"}        # the translation half's language -> E5d's language pair
SCORE = "coverage_0.5"                        # coverage at sentence threshold 0.5, in both pair_scores.csv
COLUMNS = ["pair", "text_a", "text_b", "expected", "source", "doc_id"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def col(table, name):
    return table.column(name).combine_chunks()


def flags(x):
    return np.asarray(pc.fill_null(x, False).to_numpy(zero_copy_only=False), bool)


def read_scores(path, name):
    t = pacsv.read_csv(path, convert_options=pacsv.ConvertOptions(column_types={
        "doc_id": pa.string(), "kind": pa.string(), "tr_lang": pa.string(), SCORE: pa.float64()}))
    missing = sorted({"doc_id", "kind", "tr_lang", SCORE} - set(t.column_names))
    if missing:
        sys.exit(f"ERROR: {name} {path} lacks {missing}")
    if pc.count_distinct(t.column("doc_id")).as_py() != t.num_rows:
        sys.exit(f"ERROR: {name} {path} lists a pair twice")
    return t


def build(out, known_path, real_path, labse_path, bge_path, read_no, per_pair, max_bge, max_labse, seed, positives):
    known = pq.read_table(known_path, columns=["doc_id", "sa_text", "tr_text", "tr_lang"])
    known = pa.table({c: pc.cast(col(known, c), pa.string()) for c in known.column_names})
    labse, bge = read_scores(labse_path, "LaBSE"), read_scores(bge_path, "BGE-M3")
    ids = col(labse, "doc_id")
    pos = pc.index_in(ids, value_set=col(bge, "doc_id"))
    if labse.num_rows != bge.num_rows or not pc.all(pc.is_valid(pos)).as_py():
        sys.exit("ERROR: the LaBSE and BGE-M3 pair_scores.csv must score the same pairs")
    if not pc.all(pc.is_in(ids, value_set=col(known, "doc_id"))).as_py():
        sys.exit(f"ERROR: the scores name pairs that {known_path} lacks")
    real = col(pacsv.read_csv(real_path, convert_options=pacsv.ConvertOptions(
        column_types={"doc_id": pa.string()})), "doc_id")
    read_no = pa.array(read_no, pa.string())
    for name, given in (("real translation", real), ("read non-translation", read_no)):
        if not pc.all(pc.is_in(given, value_set=ids)).as_py():
            sys.exit(f"ERROR: a {name} is not among the scored pairs")
    if pc.any(pc.is_in(read_no, value_set=real)).as_py():
        sys.exit("ERROR: a pair is listed both as a real translation and as read not a translation")

    kind, lang = col(labse, "kind"), col(labse, "tr_lang")
    s_labse = np.asarray(pc.fill_null(col(labse, SCORE), np.inf).to_numpy(), np.float64)
    s_bge = np.asarray(pc.fill_null(col(bge, SCORE).take(pos), np.inf).to_numpy(), np.float64)
    is_real, is_no = flags(pc.is_in(ids, value_set=real)), flags(pc.is_in(ids, value_set=read_no))
    sanskrit = ~flags(pc.equal(kind, "not_sanskrit"))
    low = sanskrit & ~is_real & ~is_no & (s_bge <= max_bge) & (s_labse < max_labse)
    rng = np.random.default_rng(seed)
    picks, counts = [], {}
    for tr, name in PAIRS.items():                                # the language pairs
        here = flags(pc.equal(lang, tr))
        read_ix = np.flatnonzero(here & is_no & sanskrit)
        pool = np.flatnonzero(here & low)
        want = max(per_pair - len(read_ix), 0)
        drawn = np.sort(rng.choice(pool, size=min(want, len(pool)), replace=False)) if len(pool) else pool
        pos_ix = np.flatnonzero(here & is_real & sanskrit) if positives else np.zeros(0, np.int64)
        for ix, source, expected in ((read_ix, "read_not_translation", "no"), (drawn, "low_both_encoders", "no"),
                                     (pos_ix, "read_translation", "yes")):
            picks.append((ix, source, expected, name))
        counts[name] = {"read_not_translation": len(read_ix), "low_both_encoders_pool": len(pool),
                        "low_both_encoders_drawn": len(drawn), "read_translation": len(pos_ix),
                        "shortfall": max(want - len(drawn), 0),
                        "unread_doc_ids_to_check": ids.take(pa.array(drawn, pa.int64())).to_pylist()}
    ix = np.concatenate([p[0] for p in picks]).astype(np.int64)
    n = np.array([len(p[0]) for p in picks])
    doc = ids.take(pa.array(ix))
    at = pc.index_in(doc, value_set=col(known, "doc_id"))
    source = pa.array(np.repeat([p[1] for p in picks], n), pa.string())
    table = pa.table({"pair": pa.array(np.repeat([p[3] for p in picks], n), pa.string()),
                      "text_a": col(known, "sa_text").take(at), "text_b": col(known, "tr_text").take(at),
                      "expected": pa.array(np.repeat([p[2] for p in picks], n), pa.string()),
                      "source": pc.binary_join_element_wise(source, doc, ":"), "doc_id": doc}).select(COLUMNS)
    out.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out / "controls.parquet")
    summary = {"rule": {"score": SCORE, "max_bge": max_bge, "max_labse_below": max_labse, "per_pair": per_pair,
                        "seed": seed, "positives": positives, "excluded_kinds": ["not_sanskrit"]},
               "inputs_sha256": {Path(known_path).name: sha256(known_path), Path(real_path).name: sha256(real_path),
                                 "labse/pair_scores.csv": sha256(labse_path), "bge_m3/pair_scores.csv": sha256(bge_path)},
               "pairs": counts,
               "controls": {name: col(table, "source").filter(pc.equal(col(table, "pair"), name)).to_pylist()
                            for name in PAIRS.values()}}
    (out / "controls.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for name, c in counts.items():
        print(f"{name}: {c['read_not_translation']} read non-translations + {c['low_both_encoders_drawn']} of "
              f"{c['low_both_encoders_pool']} unread pairs low on both encoders + {c['read_translation']} read "
              f"translations; shortfall {c['shortfall']}", flush=True)
        print(f"  to check by hand: {' '.join(c['unread_doc_ids_to_check']) or 'none'}", flush=True)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="the output folder, inside out/")
    ap.add_argument("--known-pairs", required=True, type=Path)
    ap.add_argument("--real", required=True, type=Path, help="real_translations.csv: the pairs read as translations")
    ap.add_argument("--labse", required=True, type=Path, help="LaBSE's pair_scores.csv")
    ap.add_argument("--bge", required=True, type=Path, help="BGE-M3's pair_scores.csv")
    ap.add_argument("--not-translations", nargs="+", default=[], help="doc_ids read by hand as not translations")
    ap.add_argument("--per-pair", type=int, default=10)
    ap.add_argument("--max-bge", type=float, default=0.5)
    ap.add_argument("--max-labse", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=20261123)
    ap.add_argument("--positives", action="store_true", help="add the read translations as expected-yes controls")
    args = ap.parse_args(argv)
    out = REPO / args.out
    if Path(args.out).is_absolute() or not out.resolve().is_relative_to((REPO / "out").resolve()):
        sys.exit(f"ERROR: --out must be inside out/ in the repository root, not {args.out!r}")
    if args.per_pair < 1:
        sys.exit("ERROR: --per-pair must be at least 1")
    here = lambda p: p if p.is_absolute() else Path.cwd() / p
    paths = [here(p) for p in (args.known_pairs, args.real, args.labse, args.bge)]
    for p in paths:
        if not p.is_file():
            sys.exit(f"ERROR: no file {p}")
    build(out, *paths, args.not_translations, args.per_pair, args.max_bge, args.max_labse, args.seed, args.positives)
    return 0


if __name__ == "__main__":
    sys.exit(main())
