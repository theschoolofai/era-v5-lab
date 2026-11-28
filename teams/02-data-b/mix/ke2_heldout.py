"""KE2 R2: held-out Indic text for hi, mr, bn, ta, sa.

Source: FineWeb-2 *test* split (HuggingFaceFW/fineweb-2, data/<config>/test/*.parquet).
The test split is disjoint from the train split that word_cost.py counted, so no
document here was counted in ke2_words_v1.csv or word_cost_v1.md.
Takes documents in file order until --mb MB of UTF-8 text per language.
Label: FineWeb-2's language label (GlotLID) and language_score; not read by people.

Run:  pip install -q pyarrow huggingface_hub
      python ke2_heldout.py --mb 10 --out ke2_heldout
Writes ke2_heldout/<lang>/docs.parquet (id, text, lang, fw2_config, language_score)
and prints docs, MB and sha256 of each file.
"""
import argparse, hashlib, os
import pyarrow as pa, pyarrow.parquet as pq
from huggingface_hub import HfFileSystem

LANGS = {"hi": "hin_Deva", "mr": "mar_Deva", "bn": "ben_Beng", "ta": "tam_Taml", "sa": "san_Deva"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mb", type=float, default=10)
    ap.add_argument("--out", default="ke2_heldout")
    a = ap.parse_args()
    fs = HfFileSystem()
    for lang, cfg in LANGS.items():
        files = sorted(fs.ls(f"datasets/HuggingFaceFW/fineweb-2/data/{cfg}/test", detail=False))
        ids, texts, scores, nbytes = [], [], [], 0
        for f in files:
            with fs.open(f, "rb") as fh:
                pf = pq.ParquetFile(fh)
                for rg in range(pf.num_row_groups):
                    t = pf.read_row_group(rg, columns=["id", "text", "language_score"]).to_pydict()
                    for i, x, s in zip(t["id"], t["text"], t["language_score"]):
                        ids.append(i); texts.append(x); scores.append(s)
                        nbytes += len(x.encode("utf-8"))
                        if nbytes >= a.mb * 1e6:
                            break
                    if nbytes >= a.mb * 1e6:
                        break
            if nbytes >= a.mb * 1e6:
                break
        os.makedirs(os.path.join(a.out, lang), exist_ok=True)
        p = os.path.join(a.out, lang, "docs.parquet")
        pq.write_table(pa.table({"id": ids, "text": texts, "lang": [lang] * len(ids),
                                 "fw2_config": [cfg] * len(ids), "language_score": scores}), p)
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        print(f"{lang} docs={len(ids)} text_MB={nbytes/1e6:.2f} file_MB={os.path.getsize(p)/1e6:.2f} "
              f"min_score={min(scores):.3f} sha256={sha}", flush=True)

if __name__ == "__main__":
    main()
