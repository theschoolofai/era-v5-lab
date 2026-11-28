r"""The H3 harm check with planted cases (task 3.5). It reads run_h3_harm.sh's outputs and h3_harm_plant.py's plants.csv,
and passes only if, in every layout (one language held out at a time, h3.py at E5c's thresholds):

  - h3.py verified every candidate (not_verified_over_max_verify is 0), so no planted pair went unchecked;
  - with h3.remove true, dedup.py's harm check passes (no gold document removed) and no held-out document is removed;
  - with h3.remove false nothing changes: its remove_list.csv is byte-identical to the run without H3;
  - p1 and p2 (held-out <-> train): the train document is removed, by rule H3, exactly when h3.py qualifies it against
    a held-out document (h3_matches.csv; for p2 that can be the original page as well as its planted half), and the
    held-out document is kept; whether the planted pair itself qualifies is recorded;
  - every language pair with p1 plants has at least one pair removed, so removal itself is tested;
  - p3 (train <-> train): neither document is removed.

It also lists every H3 removal of a document that is not planted (real data), and the margin: per language pair, the
highest coverage of a verified pair of real documents, overall and with a gold document on either side.

HOW TO RUN IT
=============
From the repository root, after run_h3_harm.sh's dedup.py runs:

    python3 -I teams/01-data-a/dedup/h3_harm_check.py --out out/h3harm --gold teams/01-data-a/gold teams/02-data-b/gold

Writes <out>/harm_cases.json (IDs, scores and counts only) and prints a table per layout; exits 1 if a check fails.
numpy and pyarrow only. No Python loop runs over rows, documents or pairs: loops remain over the layouts, the three
dedup.py modes, the cases and the language pairs.
"""
import sys
sys.dont_write_bytecode = True

import argparse, json  # noqa: E401,E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.compute as pc  # noqa: E402
import pyarrow.csv as pacsv  # noqa: E402
import pyarrow.json as pajson  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

REPO = Path(__file__).resolve().parents[3]   # teams/01-data-a/dedup/h3_harm_check.py -> the repository root
MODES = ("noh3", "report", "remove")
PAIRS = ("sa-en", "sa-hi", "hi-en")
HELD_SIDE = ("p1_heldout_train", "p2_real_web")
PLANT = "plant-"
STRINGS = ("pack_id_a", "doc_id_a", "split_a", "pack_id_b", "doc_id_b", "split_b", "outcome", "lang_a", "lang_b",
           "layout", "case", "language_pair", "a_pack", "a_split", "a_doc_id", "b_pack", "b_split", "b_doc_id",
           "expected", "source_doc_id", "id_a", "id_b", "pack_a", "pack_b", "removed_pack_id", "removed_id",
           "removed_split", "rule", "doc_id", "a_lang", "b_lang")


def flags(x):
    return np.asarray(pc.fill_null(x, False).to_numpy(zero_copy_only=False), bool)


def col(table, name):
    return table.column(name).combine_chunks()


def read_csv(path):
    if not path.is_file():
        sys.exit(f"ERROR: {path} is missing")
    return pacsv.read_csv(path, convert_options=pacsv.ConvertOptions(
        column_types={c: pa.string() for c in STRINGS}, strings_can_be_null=False))


def doc_key(pack, doc_id):
    return pc.binary_join_element_wise(pack, doc_id, "\t")


def pair_key(a, b):
    """The same key for (a, b) and (b, a)."""
    first = pc.less_equal(a, b)
    return pc.binary_join_element_wise(pc.if_else(first, a, b), pc.if_else(first, b, a), "|")


def removals(path):
    """(the keys of every document dedup.py removed, the keys it removed by rule H3, H3's held-out removals)."""
    if not path.is_file():
        sys.exit(f"ERROR: {path} is missing")
    if path.stat().st_size == 0:
        empty = pa.array([], pa.string())
        return empty, empty, 0
    log = pajson.read_json(str(path), parse_options=pajson.ParseOptions(explicit_schema=pa.schema(
        [(c, pa.string()) for c in ("removed_pack_id", "removed_id", "removed_split", "rule")]),
        unexpected_field_behavior="ignore"))
    keys = doc_key(col(log, "removed_pack_id"), col(log, "removed_id"))
    h3 = pc.equal(col(log, "rule"), "H3")
    heldout = int(flags(pc.and_(h3, pc.equal(col(log, "removed_split"), "heldout"))).sum())
    return keys, keys.filter(h3), heldout


def gold_keys(gold_dirs):
    """pack \t doc_id of every gold document in <pack>_gold.csv under the gold folders."""
    keys = []
    for d in gold_dirs:                                           # the gold folders
        for f in sorted(d.glob("*_gold.csv")):                    # one file per pack
            t = read_csv(f)
            keys.append(doc_key(pa.repeat(pa.scalar(f.name[:-len("_gold.csv")]), t.num_rows), col(t, "doc_id")))
    return pc.unique(pa.concat_arrays(keys)) if keys else pa.array([], pa.string())


def margin(run, gold):
    """Per language pair, over verified pairs of real (not planted) documents: count, highest coverage, highest with a
    gold document on either side."""
    cand = read_csv(run / "h3" / "h3_candidates.csv")
    docs = pq.read_table(run / "h3" / "h3_docs.parquet", columns=["row", "doc_id", "pack"])
    key = doc_key(col(docs, "pack"), col(docs, "doc_id"))
    a = key.take(pc.cast(col(cand, "row_a"), pa.int64()))
    b = key.take(pc.cast(col(cand, "row_b"), pa.int64()))
    real = pc.invert(pc.or_(pc.match_substring(a, "\t" + PLANT), pc.match_substring(b, "\t" + PLANT)))
    with_gold = pc.or_(pc.is_in(a, value_set=gold), pc.is_in(b, value_set=gold))
    cov = np.asarray(pc.fill_null(pc.cast(col(cand, "coverage"), pa.float64()), 0.0).to_numpy(), np.float64)
    la, lb = col(cand, "lang_a"), col(cand, "lang_b")
    out = {}
    for name in PAIRS:                                            # the language pairs
        x, y = name.split("-")
        m = flags(pc.or_(pc.and_(pc.equal(la, x), pc.equal(lb, y)), pc.and_(pc.equal(la, y), pc.equal(lb, x))))
        m &= flags(real)
        g = m & flags(with_gold)
        out[name] = {"verified": int(m.sum()), "qualifying": int((m & flags(col(cand, "qualifies"))).sum()),
                     "highest_coverage": round(float(cov[m].max()), 3) if m.any() else None,
                     "highest_with_gold": round(float(cov[g].max()), 3) if g.any() else None}
    return out


def check_layout(out, held, plants, gold):
    run, failures = out / f"{held}-held", []
    h3s = json.loads((run / "h3" / "h3_summary.json").read_text(encoding="utf-8"))
    if h3s.get("status") != "complete":
        failures.append(f"h3.py status {h3s.get('status')!r}")
    if h3s.get("not_verified_over_max_verify", 0):
        failures.append(f"h3.py left {h3s['not_verified_over_max_verify']} candidates unverified (max_verify)")
    summ = {m: json.loads((run / f"dedup_{m}" / "dedup_summary.json").read_text(encoding="utf-8")) for m in MODES}
    harm = summ["remove"]["harm_check"]
    if harm.get("status") != "pass":
        failures.append(f"harm check {harm.get('status')!r}: {harm.get('gold_removed')} gold documents removed")
    same = (run / "dedup_noh3" / "remove_list.csv").read_bytes() == (run / "dedup_report" / "remove_list.csv").read_bytes()
    if not same:
        failures.append("h3.remove false changed remove_list.csv")
    removed, h3_removed, h3_heldout = removals(run / "dedup_remove" / "dedup_log.jsonl")
    if h3_heldout:
        failures.append(f"H3 removed {h3_heldout} held-out documents")

    matches = read_csv(run / "h3" / "h3_matches.csv")
    ka = doc_key(col(matches, "pack_id_a"), col(matches, "doc_id_a"))
    kb = doc_key(col(matches, "pack_id_b"), col(matches, "doc_id_b"))
    qual = pair_key(ka, kb)
    cross = pc.not_equal(col(matches, "split_a"), col(matches, "split_b"))   # held-out <-> train
    targeted = pc.if_else(pc.equal(col(matches, "split_a"), "train"), ka, kb).filter(cross)
    pairs = read_csv(run / "dedup_remove" / "h3_pairs.csv")
    pkey = pair_key(doc_key(col(pairs, "pack_id_a"), col(pairs, "doc_id_a")),
                    doc_key(col(pairs, "pack_id_b"), col(pairs, "doc_id_b")))
    docs = pq.read_table(run / "h3" / "h3_docs.parquet", columns=["doc_id", "pack"])
    read_by_h3 = doc_key(col(docs, "pack"), col(docs, "doc_id"))
    cand = read_csv(run / "h3" / "h3_candidates.csv")             # every verified pair, at report_floor 0
    verified = pair_key(read_by_h3.take(pc.cast(col(cand, "row_a"), pa.int64())),
                        read_by_h3.take(pc.cast(col(cand, "row_b"), pa.int64())))
    cov_v = pc.cast(col(cand, "coverage"), pa.float64())

    p = plants.filter(pc.equal(plants["layout"], held))
    a, b = doc_key(col(p, "a_pack"), col(p, "a_doc_id")), doc_key(col(p, "b_pack"), col(p, "b_doc_id"))
    key = pair_key(a, b)
    q = flags(pc.is_in(key, value_set=qual))
    gone_a, gone_b = flags(pc.is_in(a, value_set=removed)), flags(pc.is_in(b, value_set=removed))
    h3_a, h3_b = flags(pc.is_in(a, value_set=h3_removed)), flags(pc.is_in(b, value_set=h3_removed))
    held_side = flags(pc.is_in(col(p, "case"), value_set=pa.array(HELD_SIDE)))
    target = flags(pc.is_in(b, value_set=targeted))                # b qualifies against some held-out document
    ok = np.where(held_side, (target == h3_b) & ~gone_a, ~(h3_a | h3_b))
    outcome = col(pairs, "outcome").take(pc.index_in(key, value_set=pkey))
    coverage = cov_v.take(pc.index_in(key, value_set=verified))   # empty when h3.py did not verify the pair
    rows = pa.table({"case": col(p, "case"), "language_pair": col(p, "language_pair"), "block": col(p, "block"),
                     "source_doc_id": col(p, "source_doc_id"), "a": pc.binary_join_element_wise(
                         col(p, "a_pack"), col(p, "a_doc_id"), ":"), "b": pc.binary_join_element_wise(
                         col(p, "b_pack"), col(p, "b_doc_id"), ":"),
                     "read_by_h3": pa.array(flags(pc.is_in(a, value_set=read_by_h3))
                                            & flags(pc.is_in(b, value_set=read_by_h3))),
                     "qualifies": pa.array(q), "train_side_targeted": pa.array(target & held_side),
                     "coverage": coverage, "outcome": outcome,
                     "removed_by_h3": pa.array(np.where(held_side, h3_b, h3_a | h3_b)), "ok": pa.array(ok)})
    if not ok.all():
        failures.append(f"{int((~ok).sum())} planted pairs not as expected")
    tested = {}
    p1 = flags(pc.equal(col(p, "case"), "p1_heldout_train"))
    lp = col(p, "language_pair")
    for name in PAIRS:                                            # the language pairs
        m = p1 & flags(pc.equal(lp, name))
        if m.any():
            tested[name] = {"planted": int(m.sum()), "removed": int((m & h3_b).sum())}
            if not (m & h3_b).any():
                failures.append(f"{name}: no p1 pair removed, so removal is not tested")
    real = h3_removed.filter(pc.invert(pc.match_substring(h3_removed, "\t" + PLANT)))
    by_case = {c: {"planted": int(m.sum()), "qualifying": int((m & q).sum()),
                   "removed_by_h3": int((m & (h3_b if c in HELD_SIDE else (h3_a | h3_b))).sum()),
                   "ok": int((m & ok).sum())}
               for c in ("p1_heldout_train", "p2_real_web", "p3_train_train")
               for m in [flags(pc.equal(col(p, "case"), c))]}
    return {"status": "fail" if failures else "pass", "failures": failures,
            "harm_check": {k: harm.get(k) for k in ("status", "gold_ids_in_input", "gold_removed", "gold_removed_ids")},
            "report_only_remove_list_unchanged": same, "h3_verified": h3s.get("verified"),
            "h3_not_verified_over_max_verify": h3s.get("not_verified_over_max_verify"),
            "h3_qualifying": h3s.get("qualifying"), "h3_removed": int(len(h3_removed)),
            "h3_removed_real_documents": pc.replace_substring(real, "\t", ":").to_pylist(),
            "removal_tested": tested, "cases": by_case, "planted_pairs": rows.to_pylist(),
            "margin": margin(run, gold)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="run_h3_harm.sh's output folder, inside out/")
    ap.add_argument("--gold", nargs="+", default=[], help="gold folders, relative to the repository root")
    args = ap.parse_args(argv)
    out = REPO / args.out
    if Path(args.out).is_absolute() or not out.resolve().is_relative_to((REPO / "out").resolve()):
        sys.exit(f"ERROR: --out must be inside out/ in the repository root, not {args.out!r}")
    plants = read_csv(out / "plants.csv")
    gold = gold_keys([REPO / g for g in args.gold])
    layouts = pc.unique(col(plants, "layout")).to_pylist()
    result = {"layouts": {f"{h}-held": check_layout(out, h, plants, gold) for h in layouts}}
    result["status"] = "pass" if all(r["status"] == "pass" for r in result["layouts"].values()) else "fail"
    (out / "harm_cases.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("| Layout | Harm check | Gold in input | Gold removed | remove false = no H3 | H3 removed (real) "
          "| p1 removed / qualifying / planted | p2 | p3 removed / planted | Status |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for name, r in result["layouts"].items():
        c, hc = r["cases"], r["harm_check"]
        p2 = c["p2_real_web"]
        print(f"| {name} | {hc['status']} | {hc['gold_ids_in_input']} | {hc['gold_removed']} "
              f"| {'yes' if r['report_only_remove_list_unchanged'] else 'NO'} "
              f"| {r['h3_removed']} ({len(r['h3_removed_real_documents'])}) "
              f"| {c['p1_heldout_train']['removed_by_h3']} / {c['p1_heldout_train']['qualifying']} / "
              f"{c['p1_heldout_train']['planted']} "
              f"| {p2['removed_by_h3']} / {p2['qualifying']} / {p2['planted']} "
              f"| {c['p3_train_train']['removed_by_h3']} / {c['p3_train_train']['planted']} | {r['status']} |")
        for f in r["failures"]:
            print(f"  FAIL {name}: {f}")
    print(f"harm cases: {result['status']}", flush=True)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
