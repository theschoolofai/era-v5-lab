# Combined spec v1.1: harm and speed results

These are the results for `../../sheets/specv1_1.md`, the combined spec (spec v1 + Spec v1.1, TSAI Gate 2 decision, 14 Nov 2026). Their summary, `validation.md`, is also the "Combined validation" section of that sheet. Everything here holds doc_ids, counts and digests only, never text.

| file | what it holds |
|---|---|
| `validation.md` | The summary: harm in order per pack and speed, spec v1 against combined. `scripts/combine_spec.py --validation` puts it into the sheet. |
| `harm_tests.md` | The full report of `spec_v1/validate/make_harm_tests.py`: `clean()` per pack, each rule alone on the gold of its packs, each disease-code function. Its title and its mentions of `specv1.md` and `spec_v1/tools` are the harness's own text; the `clean.py` it tested was built from the combined sheet. |
| `specv1_<pack>_harm.json` | That harness's report for each of the 13 Data A packs. |
| `combined_ind-te-sangraha-v_harm.json` | `harmtest/harm_test.py --rule all` on the combined sheet, with Data B's 80-doc gold. Each of the 246 rules alone, then all in sheet order. |
| `speed.md` | The `clean()` timing on 14 packs, spec v1 against combined. |

**About `clean.py`.** In these reports, `rules` reads `teams/01-data-a/spec_v1/clean.py`. That was a copy of the branch whose `clean.py` had been rebuilt from the combined sheet (sha256 `2034fe8f84b3…`), not the committed `clean.py`, which is spec v1's as on TSAI main (`22d818c72c9f…`). Rebuilding the committed one is task 2 (due 17 Nov).

## Reproduce

From `teams/01-data-a`, in a copy of the branch, so the committed `clean.py` is left alone. `<W1>` is the folder of the Week 1 packs:

```bash
python3 -I spec_v1_1/scripts/combine_spec.py --v1 spec_v1/sheets/specv1.md --additions spec_v1_1/sheets/specv1_1_additions.md \
  --validation spec_v1_1/results/combined/validation.md --out spec_v1_1/sheets/specv1_1.md
python3 -I spec_v1/build/build_clean.py --sheet spec_v1_1/sheets/specv1_1.md --out spec_v1/clean.py
python3 -I spec_v1/validate/make_harm_tests.py <copy root> <W1>/code <W1>/math <W1>/sci <W1>/english \
  --out <out>/harm_tests.md --results <out>
python3 -I harmtest/harm_test.py --pack <ind-te-sangraha-v.parquet> --gold ../02-data-b/gold/ind-te-sangraha-v_gold.csv \
  --rules spec_v1_1/sheets/specv1_1.md --rule all --report <out>/combined_ind-te-sangraha-v_harm.json
```

The run of 14 Nov:
- `make_harm_tests.py`: 51 s for the 13 packs. It exits 1, because finemath and sci-finepdfs fail on their gold contradictions.
- `harm_test.py` on ind-te-sangraha-v: `result: FAIL` (2/80), again only its 2 gold contradictions.
