# Lab 5 D1 + B1: dataset list and unique-token supply (Team 1, draft)

No dataset is downloaded. The numbers come from Hub metadata, dataset cards and Parquet footers only.

| File | What |
|---|---|
| `dataset_list.csv` | B1 list: the 16 non-Indic packs of the 38, at full Hub size, each with a fallback |
| `unique_tokens.md` | D1 write-up: supply per part, findings, method, limits, what is left |
| `supply_by_part.md` | table made by `supply.py` |
| `hub_meta.py` | revision and stored_bytes from Hub metadata |
| `text_bytes.py` | text bytes from Parquet footers, then p1536 tokens |
| `supply.py` | overlap choices (`COUNT`), then totals per part: raw and cleaned, 4 and 3 passes |

## Commands (run 28 Nov 2026, huggingface_hub 0.36.2, pyarrow 21.0.0)

From this folder:

```
python hub_meta.py dataset_list.csv
python text_bytes.py dataset_list.csv ../../03-tokenizer/results/fertility_domains.json
python supply.py dataset_list.csv supply_by_part.md
```

Each script skips rows it already filled, so it can be rerun after rows are added. Gated repos need a Hub token that has accepted their terms.

## Sources for the in-38 rows

- Hub IDs and licences: `teams/10-post-training/licences/licence_table.md` (Stage 0) and `teams/01-data-a/jobs/2026-11-19-first-training/approved_inputs.json`.
- Subsets:
  - MegaMath `megamath-web`, starcoder2data-extras `stackoverflow` and issues-kaggle-notebooks `kaggle` come from `teams/01-data-a/dedup/licence_status_before_scale_v1.md`.
  - finemath `finemath-4plus` comes from the week-1 diagnosis `medicine.md`.
- Blocked for corpus-v1 staging (TSAI, 24 Nov): en-dclm, en-nemotroncc, en-nemotroncc-synth, math-finemath.
- p1536 bytes per token: `teams/03-tokenizer/results/fertility_domains.json`.
