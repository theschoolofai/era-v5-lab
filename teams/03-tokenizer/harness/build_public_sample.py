"""A stand-in for sample v0 from public data, in the same folder layout, so `design_units.py prep` and its held-out
eval text work unchanged (G3 week 5; used when sample v0 itself is not at hand).

    python teams/03-tokenizer/harness/build_public_sample.py --out <dir> [--total-mb 1100]

Sources (Hugging Face, public, read with HfFileSystem one row group at a time, so only what is needed is downloaded):
  HuggingFaceFW/fineweb-2   data/<lang>/train/*.parquet  -> packs ind-<xx>-fw2 (11 Indic languages and Sanskrit)
  HuggingFaceFW/fineweb-edu sample/10BT/*.parquet        -> pack en-fineweb-edu
Shares of the training text: English 30%, Hindi 15%, each of the other 11 languages 5% (less if the source has less).
No code, math or science packs: this stand-in covers English and the Indic languages only.
Per pack: train/ gets docs up to its share; heldout/ gets the next HELDOUT_BYTES of docs (never in train/; exact
duplicates of train docs are dropped). doc_id = sha256 of the text, as in sample v0. Writes SHA256SUMS (sha256 of each
part) and SOURCE.json (sources, files read, bytes per pack).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

LANGS = {"hi": "hin_Deva", "mr": "mar_Deva", "bn": "ben_Beng", "as": "asm_Beng", "ta": "tam_Taml", "te": "tel_Telu",
         "kn": "kan_Knda", "ml": "mal_Mlym", "gu": "guj_Gujr", "pa": "pan_Guru", "or": "ory_Orya", "sa": "san_Deva"}
SHARE = {"en": 0.30, "hi": 0.15}
HELDOUT_BYTES = 1_200_000


def packs():
    out = {"en-fineweb-edu": ("HuggingFaceFW/fineweb-edu", "sample/10BT/*.parquet", SHARE["en"])}
    for k, code in LANGS.items():
        out[f"ind-{k}-fw2"] = ("HuggingFaceFW/fineweb-2", f"data/{code}/train/*.parquet", SHARE.get(k, 0.05))
    return out


def take(fs, repo, pattern, want_train):
    files = sorted(fs.glob(f"datasets/{repo}/{pattern}"))
    if not files:
        sys.exit(f"no files for {repo}/{pattern}")
    train, held, seen, nt, nh, used = [], [], set(), 0, 0, []
    for f in files:
        used.append(f)
        with fs.open(f, "rb", block_size=8 << 20) as fh:
            pf = pq.ParquetFile(fh)
            for rg in range(pf.num_row_groups):
                for x in pf.read_row_group(rg, columns=["text"])["text"].to_pylist():
                    if not x or not x.strip():
                        continue
                    h = hashlib.sha256(x.encode()).hexdigest()
                    n = len(x.encode())
                    if nt < want_train:
                        if h not in seen:
                            seen.add(h)
                            train.append((h, x))
                            nt += n
                    elif nh < HELDOUT_BYTES:
                        if h not in seen:
                            seen.add(h)
                            held.append((h, x))
                            nh += n
                    else:
                        return train, held, nt, nh, used
    return train, held, nt, nh, used


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"doc_id": [h for h, _ in rows], "text": [x for _, x in rows]}), path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--total-mb", type=int, default=1100)
    a = ap.parse_args()
    from huggingface_hub import HfFileSystem
    fs = HfFileSystem()
    src, sums = {}, []
    for pack, (repo, pattern, share) in packs().items():
        out_t, out_h = a.out / "train" / pack / "part-00000.parquet", a.out / "heldout" / pack / "part-00000.parquet"
        if out_t.exists() and out_h.exists():
            print(pack, "already there", flush=True)
            prev = json.loads((a.out / "SOURCE.json").read_text())["packs"].get(pack) if (a.out / "SOURCE.json").exists() else None
            if prev:
                src[pack] = prev
                continue
        want = int(share * a.total_mb * 10**6)
        print(f"{pack}: reading {want / 1e6:.0f} MB from {repo}/{pattern}", flush=True)
        train, held, nt, nh, used = take(fs, repo, pattern, want)
        write(out_t, train)
        write(out_h, held)
        src[pack] = {"repo": repo, "files_read": [u.split(repo + "/", 1)[-1] for u in used], "train_docs": len(train),
                     "train_bytes": nt, "heldout_docs": len(held), "heldout_bytes": nh, "wanted_train_bytes": want}
        print(f"{pack}: train {nt / 1e6:.1f} MB ({len(train):,} docs), heldout {nh / 1e6:.2f} MB", flush=True)
        (a.out / "SOURCE.json").write_text(json.dumps({"kind": "public stand-in for sample v0", "packs": src}, indent=1))
    for p in sorted(a.out.glob("*/*/*.parquet")):
        sums.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(a.out)}")
    (a.out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    (a.out / "SOURCE.json").write_text(json.dumps({"kind": "public stand-in for sample v0", "packs": src}, indent=1))
    print("total train MB", round(sum(v["train_bytes"] for v in src.values()) / 1e6, 1))


if __name__ == "__main__":
    sys.exit(main())
