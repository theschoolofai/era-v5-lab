# D1: unique tokens needed, and do they exist (draft, 28 Nov)

Team 1, Lab 5 design task 1 + B1. Stage 1 budget 20T tokens. All token counts are p1536 (sha `e6b93a93...`) unless marked.

**Scope.** The list holds the datasets behind the 16 non-Indic packs of the 38, each measured at its full Hub size, not the sample slice. Indic is not in D1's parts list. Each row names a fallback, as B1 asks. No new source is added or processed; the fallback named in the list is the "another source" fix for a gap.

**Status (draft):**
- Supply side: done. Raw and cleaned, 4 and 3 passes.
- Shares per part: on hold, so there is no need number per part yet. The table gives the largest share each part can carry instead.
- Licences: everything is counted as listed; the licence column is kept.

## Supply per part

From `supply_by_part.md` (`python supply.py dataset_list.csv supply_by_part.md`). Overlapping rows are counted once; see the `counted` / `count_reason` columns in `dataset_list.csv`.

| Part | Supply p1536 (B) | Raw max share, 4 passes | 3 passes | Cleaned, 4 passes | 3 passes |
|---|---:|---:|---:|---:|---:|
| code | 84.3 | 1.7% | 1.3% | 1.7% | 1.2% |
| synthetic code | 0 (no pack in the 38) | 0% | 0% | 0% | 0% |
| code-adjacent | 10.6 (commitpackft not measured, jsonl) | 0.2% | 0.2% | 0.2% | 0.2% |
| math | 219.4 | 4.4% | 3.3% | 4.3% | 3.2% |
| English real | 3,664.0 (dclm) | 73% | 55% | 72% | 54% |
| English synthetic | 1,900 (Nemotron-CC paper count) | 38% | 29% | 37% | 28% |
| science | 1,206.9 | 24% | 18% | 24% | 18% |

"Max share" = supply × passes ÷ 20T: the largest share of Stage 1 the part can fill without breaking the repeat rule. "Cleaned" = raw × 0.9794, the sample-v0 drop rates (cleaning 1.97% of documents, #244; dedup 1,345 of 1,414,996). These are document rates applied to tokens.

## What it says

1. **Code is the tightest part**: 84B tokens in the 6 starcoderdata languages, at most 1.7% of 20T.
2. **Synthetic code has no source in the 38**, so its supply is 0.
3. **Code-adjacent is small**: about 11B measured, at most 0.2%.
4. **Math fills at most about 4.4%.**
5. **English web and science are not short**: dclm alone is 3.66T, Nemotron-CC synthetic 1.9T (paper), finepdfs English 1.2T.

## How the numbers are made (no data downloaded)

1. `hub_meta.py`: revision and `stored_bytes` = sum of file sizes from Hub metadata.
2. `text_bytes.py`: `text_bytes` = stored_bytes × (uncompressed size of the text column ÷ file size).
   - The ratio comes from the Parquet footers of 3 files per row (footer bytes only).
   - `tokens_p1536` = text_bytes ÷ p1536 bytes per token for that pack, from G3's measurement on the held-out part of each pack (`teams/03-tokenizer/results/fertility_domains.json`).
3. `supply.py`: marks overlaps, totals per part.

**Check against the cards:**

| Dataset | Ours, p1536 | Card |
|---|---:|---:|
| finemath-4plus | 10.0B | 9.6B |
| dclm | 3.66T | 4T |
| fineweb-edu | 1.54T | 1.3T (GPT-2) |

## Known limits

- Footer sampling uses 3 files per row; datasets with uneven files can be off by a few %.
- The cleaned figures use sample-v0 document drop rates, not per-part token rates.
- dclm, fineweb-edu and Nemotron-CC real are all Common Crawl, so only dclm is counted. This is conservative.
- Nemotron-CC v1 counts come from its paper, not the Hub (it is served from data.commoncrawl.org).
- commitpackft is jsonl, so it has no footer to read.

## Still to do

- Need per part, once shares are set.
- Gaps, a fix inside the repeat rule for each (more repeats, the fallback source, a smaller share), and its cost.
- Compare with TSAI's list, after ours is finished.
