# Diagnosis pack viewer

A local viewer for the week 1 data diagnosis (`diagnosis/DISEASES.md`). It shows each document of your pack with
hidden characters made visible, lets you label it, and exports `labels.csv` in the template format.

```bash
pip install pyarrow
python teams/08-monitoring/diagnosis-viewer/review_server.py --pack <pack_id>.parquet
# open http://127.0.0.1:8765/
```

Options:

| Option | Meaning |
|---|---|
| `--labels labels.csv` | start from an existing label sheet; each row shows as the "starting label", which you confirm or change |
| `--reviews file.json` | where your labels are saved (default: `<pack_id>.reviews.json` next to the pack) |
| `--port N` | default 8765 |

## What it shows

- Each line starts with `@offset`, the character offset of the line start. Use it for the `evidence` column.
- Invisible and control characters show as tags: `ZWSP`, `BOM`, `SHY`, `LRM`, `NBSP`, `U+0000`, …
  ZWJ and ZWNJ show too; they are **not** a disease in Indic text (A1 note).
- A vowel sign or other combining mark with no letter before it shows as `◌ి` (possible G1).
- `h` lists every invisible character, control, `U+FFFD` and letter of another Indic script, with its offset, for the
  `hex` column.
- Text quoted in the evidence of the starting label is highlighted, and each `offset N` it cites is marked `▸`.
- The disease checkboxes come from `diagnosis/DISEASES.md`; hover a code for its name.

## Keys

`j` / `k` next and previous · `c` confirm the starting label · `s` save your label · `h` code-point list.
Filters: not reviewed, changed against the starting label, starting verdict, a disease code, or a text search.

## Saving and export

Every save writes the reviews file at once, so you can stop at any time. **Export labels.csv** gives one row per
document: your saved label, or else the starting label. Copy it to
`diagnosis/submissions/<pack_id>/<your-github-handle>/labels.csv`.

## Rules it does not enforce for you

- The server binds to `127.0.0.1` only. Do not change that, and do not commit the pack or the reviews file.
- For F1 and E3, write only the type and the offset (`phone number at offset 2432`). Never the value.
- `clean` means you read the whole document and found no disease. The form refuses `clean` with a disease
  (except D3 alone, which DISEASES.md says to label, not judge) and `fix` or `drop` without one.
