# #666 on a Colab T4, 25 Nov 2026

The job of `jobs/2026-11-19-h3-e5c-bge-m3.md` (theschoolofai/era-v5-lab#666): BGE-M3 on E5c's Sanskrit pairs,
report-only. Run outside TSAI's machines, on a Colab GPU; whether it stands as #666's result is asked on #666.

| | This run | The request |
|---|---|---|
| Code | `h3.py`, `h3_align.py`, `h3_signals.py` byte-identical to `85fa92e` (sha256 `c9c04172…`, `02fe6548…`, `a635379d…`), checked before the run | `85fa92e` |
| Config | `h3_666_colab.json`: #666's `h3.json` (sha256 `6348c585…`) with `max_verify` 60,000, as in E5c's full rerun | `max_verify` 10,000 (the default) |
| Model | `BAAI/bge-m3` at revision `5617a9f61b028005a4858fdac845db406aefb181`; `h3_summary.json` records `pytorch_model.bin` (2,271,145,830 bytes, sha256 `b5e0ce34…`) and `config.json` (sha256 `26159e7a…`), the request's hashes for that revision | revision `5617a9f` |
| Inputs | The #244 cleaning of sample v0 (`spec_v1/clean.py` `22d818c7`, the config of `jobs/2026-11-12-pr244-rerun/`), rebuilt from the raw sample parts, whose sha256 match the sample's manifest. Every part's row count equals TSAI's #244 output (`jobs/results/2026-11-12-overlap-rerun/overlap_summary.json`) | The #244 cleaned sample v0 |
| Hardware | Tesla T4 (16 GB), CUDA 13.0, fp16 | 1 CUDA GPU, 16 GB or more |
| Software | Python 3.13.16 and torch 2.14.1+cu130 (Colab's own); numpy 2.4.3, pyarrow 23.0.1, sentence-transformers 6.3.0 and transformers 5.23.0 installed at `requirements_h3.txt`'s pins | Python 3.12, torch 2.13.0 |

The model was downloaded with:

```sh
hf download BAAI/bge-m3 config.json modules.json sentence_bert_config.json config_sentence_transformers.json \
    1_Pooling/config.json pytorch_model.bin sentencepiece.bpe.model tokenizer.json tokenizer_config.json \
    special_tokens_map.json --revision 5617a9f61b028005a4858fdac845db406aefb181 --local-dir ../models/bge-m3
```

The run, from the repository root, with no embedding cache (cold start):

```sh
python -I teams/01-data-a/dedup/h3.py --config out/h3_666_colab.json
```

Wall time 1,605.7 s (26 min 51 s); peak memory 3.6 GB. The console log is `../2026-11-25-h3-e5c-bge-m3-colab.txt`.

Files here: `h3_summary.json`, `h3_candidates.csv`, `h3_matches.csv`, `h3_by_pack.csv`, `h3_histogram.csv` and the
config used. `h3_docs.parquet` (7.7 MB, IDs and counts only) is not committed: the repository takes no data files and no
file over 5 MB. Its sha256 is in `h3_summary.json`'s `outputs`.
