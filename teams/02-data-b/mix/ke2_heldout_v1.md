# KE2 data request (R2): held-out Indic text from Data B

Held-out text for KE2's R2, 5 to 20 MB per lane, one `docs.parquet` per language with a language label.

## Source

- FineWeb-2 **test** split (`HuggingFaceFW/fineweb-2`, `data/<config>/test/`). FineWeb-2 keeps test and train apart, so none of these documents were counted in `word_cost_v1.md` or `ke2_words_v1.csv` (both counted the train split only).
- Label: FineWeb-2's own language label (GlotLID) plus `language_score`. It is not checked by readers, so it is not a "verified" label in the task-0 sense. Lane: `fw2-public`.
- Licence: ODC-By 1.0 (FineWeb-2). Not the Data B shards. Not yet run through the F2 benchmark-overlap check.

## Files

The parquet files are not in the repo (3.5 MB each, binary). One command rebuilds them (Colab CPU, about 30 seconds):

```
pip install -q pyarrow huggingface_hub
python ke2_heldout.py --mb 10 --out ke2_heldout
```

Output `ke2_heldout/<lang>/docs.parquet`, columns `id, text, lang, fw2_config, language_score`. Our run (28 Nov 2026):

| lang | docs | text MB | file MB | min language_score | sha256 (pyarrow default writer) |
|---|---|---|---|---|---|
| hi | 1,511 | 10.03 | 3.85 | 0.694 | `7fd3e7cb9f4282511a6f30d3f8dc0aaff5eeecf6f56fa5383b4fab77877126eb` |
| mr | 1,390 | 10.00 | 3.82 | 0.917 | `397bdd98116179fda6746ecb9244830debc6e9afecf428e10ac5c065dff153d8` |
| bn | 1,593 | 10.02 | 3.82 | 0.896 | `f655835867ef96db9d29b4f4af1715db987d98d5f44580ba0334f78d4ad04e19` |
| ta | 1,095 | 10.02 | 3.55 | 1.000 | `4e052fe77c83d1679c17974525624f3a4c0a35adf0a0f2f00d67966ed16ed8f3` |
| sa | 233 | 6.66 | 2.42 | 0.808 | `07286a92ff577a569f2b7dff0bf3e9aec27d55bc69581eebd5cf3c36f14ea2ce` |

Sanskrit's whole FineWeb-2 test split is 6.66 MB, so `sa` is under 10 MB. The document list is fixed (files in name order, first documents up to 10 MB); the sha256 can differ with another pyarrow version even when the documents are the same.

## Not covered

R4 (names) and R6 (misspellings) need readers per language; asked in G2.
