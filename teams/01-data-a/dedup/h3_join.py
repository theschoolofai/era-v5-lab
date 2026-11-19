"""H3 (translations across languages) in dedup.py: join h3.py's matches to the H1/H2 groups, after their survivors are
chosen. Used by dedup.py when its config has an "h3" section; without it, dedup.py's outputs are unchanged.

THE RULES (dedup v2 proposal, H3-a to H3-d; h3_design_v1.md)
=============================================================
- H3 never chooses a survivor. The H1/H2 groups and their survivors are decided first (source_priority_v1.md, rules 0-4).
  An H3 match is then an edge between two "sides": the H1/H2 group of each document, or the document alone if it is in
  no group. Rules 1-4 never see H3 edges (rule 3, "the longer copy", does not compare across scripts).
- Rule 0 only. When one side holds a held-out document and the other side holds none, the other side is a train
  translation of a held-out document. With "remove": true its surviving train copies are removed (rule H3,
  stage cross_language, priority_rule 0); with "remove": false (the default, until TSAI rules on H3) they are only
  reported as "would_remove". A held-out document is never removed.
- Every other H3 edge is reported, never removed: train <-> train (a translation pair inside the training data) and
  held-out <-> held-out.
- Parallel packs: an edge between two documents of the same pack listed in "parallel_packs" (for example Pralekha,
  BPCC: translations on purpose) is skipped and counted.
- Edges whose two documents are already in one H1/H2 group are counted as "same_group" and change nothing.

INPUT: h3_matches.csv (from h3.py)
==================================
Keyed by document, not by a row of h3.py's own tables (H3-c), so dedup.py needs no join on h3.py's internals:
  pack_id_a, split_a, part_a, row_in_part_a, doc_id_a, pack_id_b, split_b, part_b, row_in_part_b, doc_id_b,
  lang_a, lang_b, coverage
Each document is looked up in overlap_docs.parquet by (pack_id, split, part, row_in_part), and its doc_id must match:
an H3 run on other cleaned parts than the overlap run stops dedup.py.

OUTPUT: h3_pairs.csv
====================
One row per H3 edge: both documents (pack_id, split, part, row_in_part, doc_id), lang_a, lang_b, coverage, the H1/H2
group_id of each side ("" for a document in no group), and the outcome: removed, would_remove, reported_train_train,
reported_heldout_heldout, same_group or parallel_pack. dedup_groups.csv keeps the H1/H2 groups only: a train survivor
removed by H3 is written there as "removed", so the group ends with no survivor, as a rule-1 group can.
"""
import csv
from pathlib import Path

H3_HEADER = ["pack_id_a", "split_a", "part_a", "row_in_part_a", "doc_id_a",
             "pack_id_b", "split_b", "part_b", "row_in_part_b", "doc_id_b", "lang_a", "lang_b", "coverage"]
H3_DEFAULTS = {"matches": None, "remove": False, "parallel_packs": []}
OUTCOMES = ("removed", "would_remove", "reported_train_train", "reported_heldout_heldout", "same_group", "parallel_pack")


def check_config(h3, fatal):
    """The "h3" section of dedup.json, with defaults; raises fatal(message) on a bad value."""
    if not isinstance(h3, dict):
        raise fatal('h3 must be an object: {"matches": ..., "remove": false, "parallel_packs": []}')
    unknown = sorted(k for k in h3 if not k.startswith("_") and k not in H3_DEFAULTS)
    if unknown:
        raise fatal(f"unknown keys in h3: {unknown}")
    h3 = {**H3_DEFAULTS, **{k: v for k, v in h3.items() if not k.startswith("_")}}
    if not h3["matches"] or Path(h3["matches"]).is_absolute():
        raise fatal("h3.matches is required, relative to the repository root: the h3_matches.csv from h3.py")
    if not isinstance(h3["remove"], bool):
        raise fatal("h3.remove must be true or false")
    if not isinstance(h3["parallel_packs"], list) or not all(isinstance(p, str) for p in h3["parallel_packs"]):
        raise fatal("h3.parallel_packs must be a list of pack IDs")
    return h3


def read_matches(path, fatal):
    """[(key_a, doc_id_a, key_b, doc_id_b, lang_a, lang_b, coverage)], key = (pack_id, split, part, row_in_part)."""
    if not path.is_file():
        raise fatal(f"missing {path} (h3.matches)")
    out = []
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if r.fieldnames != H3_HEADER:
            raise fatal(f"{path}: header must be {','.join(H3_HEADER)}")
        for n, row in enumerate(r, 2):
            try:
                ka = (row["pack_id_a"], row["split_a"], row["part_a"].replace("\\", "/"), int(row["row_in_part_a"]))
                kb = (row["pack_id_b"], row["split_b"], row["part_b"].replace("\\", "/"), int(row["row_in_part_b"]))
                cov = float(row["coverage"])
            except ValueError:
                raise fatal(f"{path} line {n}: row_in_part and coverage must be numbers")
            if ka == kb:
                raise fatal(f"{path} line {n}: a document matched with itself")
            out.append((ka, row["doc_id_a"], kb, row["doc_id_b"], row["lang_a"], row["lang_b"], cov))
    return out


def lookup(results, matches, fatal):
    """{key: overlap_docs row dict} for every document in the H3 matches; the doc_id must match the overlap run."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    want = {}
    for ka, da, kb, db, *_ in matches:
        for k, d in ((ka, da), (kb, db)):
            if want.setdefault(k, d) != d:
                raise fatal(f"h3 matches give two doc_ids for {k}")
    cols = ["row", "doc_id", "pack", "split", "part", "row_in_part", "words", "shingles"]
    t = pq.read_table(results / "overlap_docs.parquet", columns=cols)
    ids = sorted(set(want.values()))
    hits = t.filter(pc.is_in(t["doc_id"], value_set=pa.array(ids, type=t.schema.field("doc_id").type))) if ids else t.slice(0, 0)
    found = {}
    for d in hits.to_pylist():
        k = (d["pack"], d["split"], d["part"].replace("\\", "/"), d["row_in_part"])
        if k in want and want[k] == d["doc_id"]:
            found[k] = d
    missing = sorted(set(want) - set(found))
    if missing:
        raise fatal(f"{len(missing)} H3 documents are not in overlap_docs.parquet with the same doc_id, e.g. {missing[0]}: "
                    "the H3 run and the overlap run read different cleaned parts")
    return found


def join(matches, by_key, groups, parallel_packs, remove):
    """Apply the rules above. groups: {row: (group_id, train_survivors, heldout_survivors)} for every row of an H1/H2
    group. Returns (pairs, removals): pairs for h3_pairs.csv; removals [(row, ref_row, coverage)], a train row to remove
    and the held-out row it translates, each row at most once."""
    parallel = set(parallel_packs)
    pairs, removals, removed = [], [], set()
    for ka, _, kb, _, la, lb, cov in matches:
        da, db = by_key[ka], by_key[kb]
        (gid_a, train_a, held_a), (gid_b, train_b, held_b) = _side(da, groups), _side(db, groups)
        rec = {"a": da, "b": db, "lang_a": la, "lang_b": lb, "coverage": cov, "group_a": gid_a, "group_b": gid_b}
        if da["pack"] == db["pack"] and da["pack"] in parallel:
            rec["outcome"] = "parallel_pack"
        elif gid_a and gid_a == gid_b:
            rec["outcome"] = "same_group"
        elif held_a and held_b:
            rec["outcome"] = "reported_heldout_heldout"
        elif not held_a and not held_b:
            rec["outcome"] = "reported_train_train"
        else:
            (train, end, held) = (train_b, da, held_a) if held_a else (train_a, db, held_b)
            ref_row = end["row"] if end["split"] == "heldout" else held[0]
            rec["outcome"] = "removed" if remove else "would_remove"
            if remove:
                for r in train:
                    if r not in removed:
                        removed.add(r)
                        removals.append((r, ref_row, cov))
        pairs.append(rec)
    return pairs, removals


def _side(d, groups):
    """(group_id, train survivors, held-out survivors) of a document's side: its H1/H2 group, or the document alone."""
    g = groups.get(d["row"])
    if g:
        return g
    held = d["split"] == "heldout"
    return "", ([] if held else [d["row"]]), ([d["row"]] if held else [])


def write_pairs(path, pairs):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pack_id_a", "split_a", "part_a", "row_in_part_a", "doc_id_a", "group_a",
                    "pack_id_b", "split_b", "part_b", "row_in_part_b", "doc_id_b", "group_b",
                    "lang_a", "lang_b", "coverage", "outcome"])
        for p in sorted(pairs, key=lambda p: (p["a"]["pack"], p["a"]["split"], p["a"]["part"], p["a"]["row_in_part"],
                                              p["b"]["pack"], p["b"]["split"], p["b"]["part"], p["b"]["row_in_part"])):
            a, b = p["a"], p["b"]
            w.writerow([a["pack"], a["split"], a["part"], a["row_in_part"], a["doc_id"], p["group_a"],
                        b["pack"], b["split"], b["part"], b["row_in_part"], b["doc_id"], p["group_b"],
                        p["lang_a"], p["lang_b"], round(p["coverage"], 6), p["outcome"]])
