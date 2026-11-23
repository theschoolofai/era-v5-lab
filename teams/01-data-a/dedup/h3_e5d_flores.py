r"""FLORES-200 test data for E5d's reader sheets (h3_e5d_sheets.py): pairs whose answer is known, so the sheets can be
checked before E5c (theschoolofai/era-v5-lab#625) and theschoolofai/era-v5-lab#666 return.

FLORES-200 is an evaluation benchmark (openlanguagedata/flores_plus on Hugging Face, gated): it is read here to test the
tools and is never training data. Its text stays in out/; only the counts in flores_build.json and flores_check.json
are kept.

HOW TO RUN IT
=============
numpy and pyarrow; no model and no network. Paths are relative to the repository root, and it writes only to out/.

    python teams/01-data-a/dedup/h3_e5d_flores.py build --flores-dir ../flores_plus --out out/e5d_flores
    python teams/01-data-a/dedup/h3.py --config teams/01-data-a/dedup/h3_e5d_flores.json
    python teams/01-data-a/dedup/h3.py --config teams/01-data-a/dedup/h3_e5d_flores_t07.json
    python teams/01-data-a/dedup/h3_e5d_sheets.py --config teams/01-data-a/dedup/h3_e5d_flores_sheets.json
    python teams/01-data-a/dedup/h3_e5d_flores.py check --sheets out/e5d_flores/sheets --out out/e5d_flores

build   --flores-dir holds, for eng_Latn, hin_Deva, san_Deva and ory_Orya, either <code>.txt (one sentence per line in
        devtest order, as labse_check.py reads it) or FLORES+'s devtest/<code>.jsonl (as `hf download` saves
        openlanguagedata/flores_plus; sentences put in the order of their id). Their sha256 go in flores_build.json:
        G9 pins revision e707e62e of FLORES+ with each file's sha256 (teams/09-evaluation/fingerprints/v1/flores200/
        MANIFEST.json). Every block of --block consecutive sentences becomes
        one document, one pack per language (flores-en, flores-hi, flores-sa, flores-or), in h3.py's raw layout
        (<pack>/Part_1/, <pack>/Heldout/; every fourth English block is held out). Block i is the same text in every
        language, so (block i, block i) of two languages is a translation and (block i, block j) a same-domain
        non-translation. controls.parquet: for each language pair, block i against block i + n/2 of the other
        language, expected "no", for h3_e5d_sheets.py's controls.
check   reads the sheets and the key that h3_e5d_sheets.py wrote. A candidate is a translation exactly when its two
        documents are the same block. It counts, per language pair and band, the translations and non-translations
        drawn, and on each side of --threshold the translations the threshold misses and the non-translations it
        lets through. It also checks that the sheets are blind (only item, text_1, text_2, translation, note; no doc_id
        in a text) and match the key item for item, and that every control is a non-translation. Writes
        flores_check.json and flores_truth.csv (item and answer, no text); exits 1 if a check fails.
"""
import sys
sys.dont_write_bytecode = True

import argparse, hashlib, json  # noqa: E401,E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pyarrow as pa  # noqa: E402
import pyarrow.compute as pc  # noqa: E402
import pyarrow.csv as pacsv  # noqa: E402
import pyarrow.json as pajson  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

REPO = Path(__file__).resolve().parents[3]   # teams/01-data-a/dedup/h3_e5d_flores.py -> the repository root
LANGS = {"en": "eng_Latn", "hi": "hin_Deva", "sa": "san_Deva", "or": "ory_Orya"}
PAIRS = (("sa", "en"), ("sa", "hi"), ("hi", "en"), ("or", "en"))   # E5c's language pairs (#625)
SHEET_COLUMNS = ["item", "text_1", "text_2", "translation", "note"]
DOC_ID = r"block-\d{3}"   # the doc_id of every FLORES document built here


def out_dir(path):
    out = REPO / path
    if Path(path).is_absolute() or not out.resolve().is_relative_to((REPO / "out").resolve()):
        sys.exit(f"ERROR: --out must be inside out/ in the repository root, not {path!r}")
    return out


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def blocks(lines, block, n):
    """The first n blocks of block lines each, every block one text with a sentence per line."""
    offsets = pa.array(np.arange(0, n * block + 1, block, dtype=np.int32))
    return pc.binary_join(pa.ListArray.from_arrays(offsets, lines.slice(0, n * block)), "\n")


def sentences(flores_dir, code):
    """(the language's devtest sentences in devtest order, the file read, its bytes): <code>.txt, one sentence per
    line, or FLORES+'s devtest/<code>.jsonl, one record per sentence, put in the order of its id."""
    txt, jsonl = flores_dir / f"{code}.txt", flores_dir / "devtest" / f"{code}.jsonl"
    if txt.is_file():
        data = txt.read_bytes()
        return pa.array(data.decode("utf-8").splitlines(), pa.string()), txt, data
    if jsonl.is_file():
        data = jsonl.read_bytes()
        t = pajson.read_json(pa.BufferReader(data), parse_options=pajson.ParseOptions(
            explicit_schema=pa.schema([("id", pa.int64()), ("text", pa.string())]),
            unexpected_field_behavior="ignore"))
        ids = t.column("id").combine_chunks()
        if pc.count_distinct(ids).as_py() != t.num_rows or ids.null_count:
            sys.exit(f"ERROR: {jsonl}: every record needs a distinct id")
        return t.column("text").combine_chunks().take(pc.sort_indices(ids)), jsonl, data
    sys.exit(f"ERROR: --flores-dir {flores_dir} has neither {code}.txt nor devtest/{code}.jsonl")


def build(flores_dir, out, block):
    lines, digests = {}, {}
    for lang, code in LANGS.items():                              # the four languages
        text, path, data = sentences(flores_dir, code)
        digests[path.name] = sha256(data)
        lines[lang] = pc.utf8_trim_whitespace(pc.fill_null(text, ""))
    sizes = {lang: len(v) for lang, v in lines.items()}
    if len(set(sizes.values())) != 1:
        sys.exit(f"ERROR: the FLORES files must have the same number of lines (one sentence each), not {sizes}")
    n = next(iter(sizes.values())) // block
    if n < 2:
        sys.exit(f"ERROR: at least two blocks of {block} sentences are needed")
    i = np.arange(n)
    doc_id = pc.binary_join_element_wise("block", pc.utf8_lpad(pc.cast(pa.array(i + 1), pa.string()), 3, "0"), "-")
    texts = {lang: blocks(v, block, n) for lang, v in lines.items()}
    inputs = out / "inputs"
    written = {}
    for lang, text in texts.items():                              # one pack per language
        pack = f"flores-{lang}"
        heldout = (i % 4 == 0) if lang == "en" else np.zeros(n, bool)
        table = pa.table({"pack_id": pa.repeat(pa.scalar(pack), n), "doc_id": doc_id, "text": text,
                          "lang_label": pa.repeat(pa.scalar(lang), n)})
        for folder, rows in (("Part_1", ~heldout), ("Heldout", heldout)):
            if rows.any():
                (inputs / pack / folder).mkdir(parents=True, exist_ok=True)
                pq.write_table(table.filter(pa.array(rows)), inputs / pack / folder / "part-00000.parquet")
        written[pack] = {"train": int((~heldout).sum()), "heldout": int(heldout.sum())}
    j = pa.array((i + n // 2) % n)
    controls = pa.concat_tables([pa.table({
        "pair": pa.repeat(pa.scalar(f"{x}-{y}"), n), "text_a": texts[x], "text_b": texts[y].take(j),
        "expected": pa.repeat(pa.scalar("no"), n), "source": pa.repeat(pa.scalar("flores-other-block"), n)})
        for x, y in PAIRS])                                       # the language pairs
    pq.write_table(controls, out / "controls.parquet")
    summary = {"flores_sha256": digests, "sentences_per_language": sizes, "block": block, "blocks": n,
               "packs": written, "controls_per_pair": n}
    (out / "flores_build.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"flores build: {n} blocks of {block} sentences in {len(LANGS)} languages, {n} controls per pair; "
          f"{out.relative_to(REPO)}", flush=True)
    return summary


def read_csv(path):
    data = path.read_bytes()
    data = data[3:] if data.startswith(b"\xef\xbb\xbf") else data
    return pacsv.read_csv(pa.BufferReader(data), parse_options=pacsv.ParseOptions(newlines_in_values=True),
                          convert_options=pacsv.ConvertOptions(strings_can_be_null=True, column_types={
                              "item": pa.string(), "doc_id_a": pa.string(), "doc_id_b": pa.string(),
                              "text_1": pa.string(), "text_2": pa.string(), "translation": pa.string(),
                              "note": pa.string()}))


def strings(table, name):
    return table.column(name).combine_chunks()


def sorted_items(table):
    items = strings(table, "item")
    return items.take(pc.sort_indices(items))


def check(sheets, out, threshold):
    keys = sorted((sheets / "key").glob("*_key.csv"))
    if not keys:
        sys.exit(f"ERROR: no key files in {sheets / 'key'}")
    failures, pairs, truth_items, truth_values = [], {}, [], []
    for path in keys:                                             # the language pairs
        name = path.name[:-len("_key.csv")]
        key = read_csv(path)
        item, source = strings(key, "item"), strings(key, "source")
        cand = np.asarray(pc.equal(source, "candidate").to_numpy(zero_copy_only=False), bool)
        same = np.asarray(pc.fill_null(pc.equal(strings(key, "doc_id_a"), strings(key, "doc_id_b")), False)
                          .to_numpy(zero_copy_only=False), bool)
        drawn = strings(key, "drawn_for")
        cov = np.full(key.num_rows, np.nan)
        for enc in pc.unique(drawn.filter(pa.array(cand))).to_pylist():   # the encoders drawn for
            mine = np.asarray(pc.fill_null(pc.equal(drawn, enc), False).to_numpy(zero_copy_only=False), bool)
            c = np.asarray(pc.fill_null(pc.cast(strings(key, f"coverage_{enc}"), pa.float64()), np.nan).to_numpy())
            cov[mine] = c[mine]
        above = cand & (cov >= threshold)
        below = cand & (cov < threshold)
        band = strings(key, "band")
        bands = {}
        for b in pc.unique(band.filter(pa.array(cand))).to_pylist():      # the bands
            inb = cand & np.asarray(pc.equal(band, b).to_numpy(zero_copy_only=False), bool)
            bands[b] = {"items": int(inb.sum()), "translations": int((inb & same).sum())}
        ctl = ~cand
        expected_no = np.asarray(pc.fill_null(pc.equal(strings(key, "expected"), "no"), False)
                                 .to_numpy(zero_copy_only=False), bool)
        wrong = ctl & ~expected_no
        if wrong.any():
            failures.append(f"{name}: {int(wrong.sum())} controls not expected 'no'")
        pairs[name] = {"candidates": int(cand.sum()), "translations": int((cand & same).sum()), "controls":
                       int(ctl.sum()), "bands": bands, "both_sides_of_threshold": bool(above.any() and below.any()),
                       "translations_below_threshold": int((below & same).sum()),
                       "non_translations_at_or_above_threshold": int((above & ~same).sum())}
        sheet_files = sorted(sheets.glob(f"sheets/{name}_reader*.csv"))
        if not sheet_files:
            failures.append(f"{name}: no sheets")
        for sp in sheet_files:                                    # the readers' sheets
            sheet = read_csv(sp)
            if sheet.column_names != SHEET_COLUMNS:
                failures.append(f"{sp.name}: columns {sheet.column_names}, not {SHEET_COLUMNS}")
                continue
            mine, theirs = sorted_items(sheet), sorted_items(key)
            if len(mine) != len(theirs) or not pc.all(pc.equal(mine, theirs)).as_py():
                failures.append(f"{sp.name}: its items differ from the key's")
            text = pc.binary_join_element_wise(strings(sheet, "text_1"), strings(sheet, "text_2"), "\n")
            if pc.any(pc.match_substring_regex(text, DOC_ID)).as_py():          # FLORES doc_ids are block-NNN
                failures.append(f"{sp.name}: a text holds a doc_id")
        truth_items.append(item)
        truth_values.append(pa.array(np.where(cand, np.where(same, "yes", "no"), "no")))
    pacsv.write_csv(pa.table({"item": pa.concat_arrays(truth_items),
                              "translation": pa.concat_arrays(truth_values)}), out / "flores_truth.csv")
    result = {"status": "fail" if failures else "ok", "threshold": threshold, "failures": failures, "pairs": pairs}
    (out / "flores_check.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name, p in pairs.items():
        print(f"{name}: {p['candidates']} candidates ({p['translations']} translations), {p['controls']} controls; "
              f"below {threshold}: {p['translations_below_threshold']} translations; at or above: "
              f"{p['non_translations_at_or_above_threshold']} non-translations", flush=True)
    print(f"flores check: {result['status']}" + (f" ({'; '.join(failures)})" if failures else ""), flush=True)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="step", required=True)
    b = sub.add_parser("build")
    b.add_argument("--flores-dir", required=True, type=Path)
    b.add_argument("--out", required=True)
    b.add_argument("--block", type=int, default=8)
    c = sub.add_parser("check")
    c.add_argument("--sheets", required=True, help="h3_e5d_sheets.py's out folder")
    c.add_argument("--out", required=True)
    c.add_argument("--threshold", type=float, default=0.6)
    args = ap.parse_args(argv)
    out = out_dir(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.step == "build":
        if args.block < 1:
            sys.exit("ERROR: --block must be at least 1")
        build(args.flores_dir if args.flores_dir.is_absolute() else Path.cwd() / args.flores_dir, out, args.block)
        return 0
    return 1 if check(REPO / args.sheets, out, args.threshold)["status"] != "ok" else 0


if __name__ == "__main__":
    sys.exit(main())
