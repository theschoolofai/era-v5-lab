# D1: unique tokens needed, and do they exist (draft, 28 Nov)

Team 1, Lab 5 design task 1 + B1. Stage 1 budget 20T tokens. All token counts are p1536 (sha `e6b93a93...`) unless marked.

**Status (draft):**
- Supply side: done for every dataset that has numbers on the Hub. Raw and cleaned, 4 and 3 passes.
- Shares per part: on hold, so there is no need number per part yet. The table gives the largest share each part can carry instead.
- Indic: not in D1's parts list. Data B lists it; our own Indic rows are still to do, and we compare with Data B's total when it comes.

Team choices so far:
- Licences: everything is counted as listed, and the licence column is kept, so a licence filter can be applied later.
- Passes: both 4 (1 read + 3 repeats) and 3 are reported.
- Code-adjacent: listed here too. Data B's total is a cross-check.
- Raw and cleaned: both are reported.

## Supply per part

From `supply_by_part.md` (`python supply.py dataset_list.csv supply_by_part.md`). Overlapping rows are counted once; see the `counted` / `count_reason` columns in `dataset_list.csv`.

| Part | Measured p1536 (B) | Card-only, other tokenizer (B) | Rows with no number yet | Raw max share, 4 passes | 3 passes | Cleaned, 4 passes | 3 passes |
|---|---:|---:|---|---:|---:|---:|---:|
| code | 265.5 | 0 | opc-annealing algorithmic (jsonl) | 5.3% | 4.0% | 5.2% | 3.9% |
| synthetic code | 0 | 0 | opc-annealing synthetic (jsonl); Nemotron-Pretraining-Code-v1 (gated) | 0% | 0% | 0% | 0% |
| code-adjacent | 45.8 | 0 | commitpackft (jsonl) | 0.9% | 0.7% | 0.9% | 0.7% |
| math | 262.2 | 11.0 | Nemotron-CC-Math-v1 (gated) | 5.5% | 4.1% | 5.4% | 4.0% |
| English real | 17,365.8 | 0 | - | 347% | 260% | 340% | 255% |
| English synthetic | 54.8 | 1,900.0 | Nemotron-CC-v2 synthetic (gated) | 39% | 29% | 38% | 29% |
| science | 1,227.9 | 42.0 | common-pile pubmed (jsonl) | 25% | 19% | 25% | 19% |

"Max share" = supply × passes ÷ 20T: the largest share of Stage 1 the part can fill without breaking the repeat rule. "Cleaned" = raw × 0.9794, the sample-v0 drop rates (cleaning 1.97% of documents, #244; dedup 1,345 of 1,414,996). These are document rates applied to tokens.

## What it already says

1. **Code is the tight part.**
   - Counted code supply is about 266B tokens. At 4 passes it fills at most 5.3% of 20T.
   - That is 116 GB of starcoderdata in our 6 languages, plus the other starcoderdata languages, compiler IR, and code web pages.
   - The Stack v2 is not counted: it is a superset of starcoderdata, and its content sits on Software Heritage, not the Hub. It is the obvious fix for a code gap, but its size has to come from its paper or card.
2. **Synthetic code has no number yet.** Both candidates are either jsonl (no footer to read) or gated with manual approval.
3. **Code-adjacent is small**: about 46B, at most 0.9% of 20T. Data B lists it too (their task 1); their total will be a cross-check.
4. **Math fills at most about 5.5%.**
5. **English web and science are not short.**
   - English real: fineweb alone is 17.4T.
   - English synthetic: Nemotron-CC synthetic is 1.9T, a paper count to verify.
   - Science: finepdfs English is 1.2T.

## How the numbers are made (no data downloaded)

1. `hub_meta.py`: revision and `stored_bytes` = sum of file sizes from Hub metadata.
2. `text_bytes.py`: `text_bytes` = stored_bytes × (uncompressed size of the text column ÷ file size).
   - The ratio comes from the Parquet footers of 3 files per row (footer bytes only).
   - `tokens_p1536` = text_bytes ÷ p1536 bytes per token, from G3's measurement on the held-out part of each pack (`teams/03-tokenizer/results/fertility_domains.json`). New rows use the mean of their part's packs.
3. `supply.py`: marks overlaps, totals per part.

**Check against the cards:**

| Dataset | Ours, p1536 | Card |
|---|---:|---:|
| finemath-4plus | 10.0B | 9.6B |
| finemath-3plus | 32.4B | 34B |
| infiwebmath-3plus | 20.4B | 20.5B |
| cosmopedia | 25.4B | 25B |
| open-web-math | 13.1B | 14.7B |
| fineweb | 17.4T | 18.5T (GPT-2) |
| dclm | 3.66T | 4T |
| fineweb-edu | 1.54T | 1.3T (GPT-2) |

## Known limits

- Footer sampling uses 3 files per row; datasets with uneven files can be off by a few %.
- The cleaned figures use sample-v0 document drop rates, not per-part token rates.
- Overlap between Common Crawl sets (fineweb, dclm, Nemotron-CC, dolma) is handled by counting only fineweb, which is conservative.
- Nemotron-CC v1 counts come from its paper, not the Hub (it is served from data.commoncrawl.org).
- peS2o's 42B is whitespace words, not tokens.
- Gated-manual repos (NVIDIA) need someone with Hub access who accepted their terms.

## Still to do

- Need per part, once shares are set.
- Gaps, a fix inside the repeat rule for each, and its cost.
- Our own Indic rows; compare with Data B's Indic and code-adjacent totals.
- Rows with no number: jsonl sets (card counts where given) and gated NVIDIA sets (need Hub access).
- Compare with TSAI's list, after ours is finished.
