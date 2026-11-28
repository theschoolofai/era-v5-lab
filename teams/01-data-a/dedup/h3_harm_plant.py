r"""Planted cases for H3's harm check (task 3.5): pairs whose answer is known, added to the diagnosis-pack layouts of
run_h3_harm.sh, so that the harm check at E5c's thresholds tests removal, not only that nothing was removed.

The diagnosis packs have no held-out split, so run_h3_harm.sh holds out one language at a time (sa, hi, en). In each
layout <out>/<held>-held/inputs/{train,heldout}/<pack>/, this adds one part, part-plant.parquet, to each pack that takes
a planted document, and it writes every case to <out>/plants.csv:

  p1_heldout_train  FLORES+ devtest blocks of 8 sentences: block i in the held-out language and block i in another
                    language, in train. The train document translates held-out content: with h3.remove true it must be
                    removed (rule H3) exactly when h3.py qualifies the pair, and the held-out document kept. 3 blocks
                    for each language pair with the held-out language.
  p2_real_web       the ind-sa-fw2 same-page pairs read by hand as real translations (real_translations.csv; their two
                    halves from known_pairs.parquet): the Sanskrit half held out, the translation half in train. The
                    same rule applies; whether they qualify is recorded. sa-held layout only.
  p3_train_train    one FLORES+ block in each of the two other languages, both in train: a translation pair inside the
                    training data, reported and never removed. 2 blocks.

Blocks are distinct within a layout, so each planted document has one counterpart. Planted doc_ids start with
"plant-", which no gold set uses. Language pairs are the ruled scope (sa-en, sa-hi, hi-en; theschoolofai/era-v5-lab#625);
Odia has no gold set, so it stays report-only (theschoolofai/era-v5-lab#626) and is not planted.

FLORES+ is an evaluation benchmark and the web pairs hold page text: the parts stay in out/, and plants.csv and
plants.json hold IDs, hashes and counts only.

HOW TO RUN IT
=============
After run_h3_harm.sh's layout step, from the repository root (paths other than --out are relative to the current folder):

    python3 -I teams/01-data-a/dedup/h3_harm_plant.py --out out/h3harm --flores-dir ../flores_plus \
        --known-pairs ../known_pairs.parquet --real ../real_translations.csv

--flores-dir is read as h3_e5d_flores.py reads it (eng_Latn, hin_Deva, san_Deva: <code>.txt or devtest/<code>.jsonl, with
the same sentence ids in every language). numpy and pyarrow only. No Python loop runs over rows or documents: loops
remain over the layouts, the cases and the packs written.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h3_e5d_flores as flores  # noqa: E402  FLORES+ reading, id check and 8-sentence blocks

REPO = Path(__file__).resolve().parents[3]   # teams/01-data-a/dedup/h3_harm_plant.py -> the repository root
HELD = ("sa", "hi", "en")
PACK = {"sa": "ind-sa-fw2", "hi": "ind-hi-fw2", "en": "en-fineweb-edu"}   # the pack that takes a language's plants
PAIRS = (("sa", "en"), ("sa", "hi"), ("hi", "en"))
P1_BLOCKS, P3_BLOCKS, BLOCK = 3, 2, 8
PLANT_PART = "part-plant.parquet"
SHORT = {"p1_heldout_train": "p1", "p2_real_web": "p2", "p3_train_train": "p3"}
EXPECTED = {"p1_heldout_train": "removed_if_qualifying", "p2_real_web": "removed_if_qualifying",
            "p3_train_train": "never_removed"}
PLANT_COLUMNS = ["layout", "case", "language_pair", "block", "source_doc_id", "a_pack", "a_split", "a_doc_id", "a_lang",
                 "b_pack", "b_split", "b_doc_id", "b_lang", "expected"]


def pair_name(x, y):
    """The ruled language pair of two languages, in its usual order (sa-en, sa-hi, hi-en)."""
    return next(f"{a}-{b}" for a, b in PAIRS if {a, b} == {x, y})


def const(value, n, typ=pa.string()):
    return pa.repeat(pa.scalar(value, typ), n)


def flores_blocks(flores_dir):
    """{lang: block texts} for en, hi and sa, and {file: sha256}; every language must hold the same sentence ids."""
    blocks, ids, digests = {}, {}, {}
    for lang in ("en", "hi", "sa"):                               # the three languages
        text, sid, path, data = flores.sentences(flores_dir, flores.LANGS[lang])
        digests[path.name] = flores.sha256(data)
        ids[lang], blocks[lang] = sid, pc.utf8_trim_whitespace(pc.fill_null(text, ""))
    for lang in ("hi", "sa"):
        if len(ids[lang]) != len(ids["en"]) or not pc.all(pc.equal(ids[lang], ids["en"])).as_py():
            sys.exit(f"ERROR: {flores.LANGS[lang]} and {flores.LANGS['en']} hold different sentence ids")
    n = len(ids["en"]) // BLOCK
    need = 2 * P1_BLOCKS + P3_BLOCKS
    if n < need:
        sys.exit(f"ERROR: FLORES+ gives {n} blocks of {BLOCK} sentences; the plants need {need}")
    return {lang: flores.blocks(v, BLOCK, n) for lang, v in blocks.items()}, digests


def flores_cases(held):
    """[(case, side a language, side b language, split a, split b, block numbers)] for one layout."""
    others = [t for p in PAIRS if held in p for t in p if t != held]
    out, b = [], 0
    for t in others:                                              # p1: held-out language against each other one
        out.append(("p1_heldout_train", held, t, "heldout", "train", np.arange(b, b + P1_BLOCKS)))
        b += P1_BLOCKS
    x, y = next(p for p in PAIRS if held not in p)
    out.append(("p3_train_train", x, y, "train", "train", np.arange(b, b + P3_BLOCKS)))
    return out


def doc_ids(prefix, keys, lang):
    """prefix-<key>-<lang> for every key (a string array)."""
    return pc.binary_join_element_wise(prefix, keys, lang, "-")


def real_pairs(known_path, real_path):
    """The known pairs read as real translations: (doc_id, sa_text, tr_text, tr_lang), and {file: sha256}."""
    known = pq.read_table(known_path, columns=["doc_id", "sa_text", "tr_text", "tr_lang"])
    known = pa.table({c: pc.cast(known.column(c).combine_chunks(), pa.string()) for c in known.column_names})
    real = pacsv.read_csv(real_path, convert_options=pacsv.ConvertOptions(column_types={"doc_id": pa.string()}))
    want = real.column("doc_id").combine_chunks()
    found = pc.is_in(want, value_set=known.column("doc_id").combine_chunks())
    if not pc.all(found).as_py():
        missing = want.filter(pc.invert(found))
        sys.exit(f"ERROR: {real_path} names {len(missing)} doc_ids that {known_path} lacks, e.g. {missing[0].as_py()}")
    rows = known.filter(pc.is_in(known.column("doc_id"), value_set=want))
    lang = rows.column("tr_lang").combine_chunks()
    if not pc.all(pc.is_in(lang, value_set=pa.array(["en", "hi"]))).as_py():
        sys.exit(f"ERROR: {known_path}: tr_lang must be en or hi")
    digests = {Path(p).name: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (known_path, real_path)}
    return rows, digests


def plant(out, flores_dir, known_path, real_path):
    blocks, digests = flores_blocks(flores_dir)
    real, real_digests = real_pairs(known_path, real_path)
    tables, written = [], {}
    for held in HELD:                                             # the layouts
        layout = out / f"{held}-held" / "inputs"
        if not layout.is_dir():
            sys.exit(f"ERROR: no layout {layout}: run run_h3_harm.sh's layout step first")
        parts = {}                                                # (split, pack) -> [(doc_id, text, lang)]
        rows = []
        for case, x, y, sx, sy, idx in flores_cases(held):        # the FLORES+ cases
            n, take = len(idx), pa.array(idx)
            keys = pc.binary_join_element_wise(const(f"{held}-b", n), pc.utf8_lpad(pc.cast(pa.array(idx + 1),
                                                                                         pa.string()), 3, "0"), "")
            a_id, b_id = doc_ids(f"plant-{SHORT[case]}", keys, x), doc_ids(f"plant-{SHORT[case]}", keys, y)
            parts.setdefault((sx, PACK[x]), []).append((a_id, blocks[x].take(take), x))
            parts.setdefault((sy, PACK[y]), []).append((b_id, blocks[y].take(take), y))
            rows.append({"layout": const(held, n), "case": const(case, n), "language_pair": const(pair_name(x, y), n),
                         "block": pa.array(idx + 1, pa.int64()), "source_doc_id": pa.nulls(n, pa.string()),
                         "a_pack": const(PACK[x], n), "a_split": const(sx, n), "a_doc_id": a_id, "a_lang": const(x, n),
                         "b_pack": const(PACK[y], n), "b_split": const(sy, n), "b_doc_id": b_id, "b_lang": const(y, n),
                         "expected": const(EXPECTED[case], n)})
        if held == "sa" and real.num_rows:                        # the real web pairs, Sanskrit half held out
            n, src = real.num_rows, real.column("doc_id").combine_chunks()
            tr_lang = real.column("tr_lang").combine_chunks()
            a_id = doc_ids("plant-p2", pc.binary_join_element_wise("sa", src, "-"), "sa")
            b_id = pc.binary_join_element_wise(const("plant-p2-sa", n), src, tr_lang, "-")
            parts.setdefault(("heldout", PACK["sa"]), []).append((a_id, real.column("sa_text").combine_chunks(), "sa"))
            for lang in ("en", "hi"):                             # the translation half's language
                m = pc.equal(tr_lang, lang)
                if pc.any(m).as_py():
                    parts.setdefault(("train", PACK[lang]), []).append(
                        (b_id.filter(m), real.column("tr_text").combine_chunks().filter(m), lang))
            rows.append({"layout": const("sa", n), "case": const("p2_real_web", n),
                         "language_pair": pc.if_else(pc.equal(tr_lang, "en"), pa.scalar("sa-en"), pa.scalar("sa-hi")),
                         "block": pa.nulls(n, pa.int64()), "source_doc_id": src,
                         "a_pack": const(PACK["sa"], n), "a_split": const("heldout", n), "a_doc_id": a_id,
                         "a_lang": const("sa", n),
                         "b_pack": pc.if_else(pc.equal(tr_lang, "en"), pa.scalar(PACK["en"]), pa.scalar(PACK["hi"])),
                         "b_split": const("train", n), "b_doc_id": b_id, "b_lang": tr_lang,
                         "expected": const(EXPECTED["p2_real_web"], n)})
        for (split, pack), pieces in parts.items():               # one plant part per pack that takes plants
            folder = layout / split / pack
            if not folder.is_dir():
                sys.exit(f"ERROR: {folder} is missing: the layout puts {pack} in the other split")
            ids = pa.concat_arrays([p[0] for p in pieces])
            text = pa.concat_arrays([p[1] for p in pieces])
            lang = pa.concat_arrays([const(p[2], len(p[0])) for p in pieces])
            pq.write_table(pa.table({"pack_id": const(pack, len(ids)), "doc_id": ids, "text": text,
                                     "lang_label": lang}), folder / PLANT_PART)
            written[f"{held}-held/{split}/{pack}"] = len(ids)
        tables.extend(pa.table(r).select(PLANT_COLUMNS) for r in rows)
    plants = pa.concat_tables(tables)
    pacsv.write_csv(plants, out / "plants.csv")
    counts = {f"{held}-held": {case: int(pc.sum(pc.and_(pc.equal(plants["layout"], held),
                                                         pc.equal(plants["case"], case))).as_py() or 0)
                               for case in SHORT} for held in HELD}
    summary = {"inputs_sha256": {**digests, **real_digests}, "block_sentences": BLOCK, "pairs": counts,
               "documents_written": written}
    (out / "plants.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for held in HELD:
        c = counts[f"{held}-held"]
        print(f"{held}-held: {c['p1_heldout_train']} held-out <-> train, {c['p2_real_web']} real web, "
              f"{c['p3_train_train']} train <-> train pairs planted", flush=True)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="run_h3_harm.sh's output folder, inside out/")
    ap.add_argument("--flores-dir", required=True, type=Path)
    ap.add_argument("--known-pairs", required=True, type=Path)
    ap.add_argument("--real", required=True, type=Path)
    args = ap.parse_args(argv)
    out = REPO / args.out
    if Path(args.out).is_absolute() or not out.resolve().is_relative_to((REPO / "out").resolve()):
        sys.exit(f"ERROR: --out must be inside out/ in the repository root, not {args.out!r}")
    here = lambda p: p if p.is_absolute() else Path.cwd() / p
    for p in (args.known_pairs, args.real):
        if not here(p).is_file():
            sys.exit(f"ERROR: no file {p}")
    plant(out, here(args.flores_dir), here(args.known_pairs), here(args.real))
    return 0


if __name__ == "__main__":
    sys.exit(main())
