# G6 W5 evidence list

Named owner: **Raj H**. Index keeper: **Tharun**.

Team members: add a row when you have a command, output hash, and git SHA.  
Result write-ups stay under `teams/06-performance/results/` (or a linked gist).  
Bring-up rows must say GPU, seeds, and “not official 2×” until the baseline run.

| Task | Command | Output file / hash | Git SHA | Diff vs reference | Status | Filled by |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Metrics three fields (PR-C) | `pytest correctness/test_throughput_rates.py` (+ mfu guards) | class [#888](https://github.com/theschoolofai/era-v5-lab/pull/888) | `63b2d314` (merge) | old `tokens_per_s` kept; added `positions_per_s`, `scored_tokens_per_s`, `bytes_per_s`. Headline for 2× = scored tokens/s | **MERGED** | Raj |
| #805 SDPA vs eager | TSAI job comment on [#805](https://github.com/theschoolofai/era-v5-lab/pull/805) | job folder `summary.json` / `metrics.jsonl` | (job) | 1.33× wall, 1.48× median tok/s; quality **no claim** (eval ranges after step 600) | Result in | Raj / Varshith tip fill |
| Loader contract 1/2/4 | `loader_contract.py --factory dataio.mixloader:make_loader` | | | | | Tharun / Vaibhav |
| Resume proof | `python correctness/prove_resume.py` | | | | | Tharun / Vaibhav |
| Composition log sample | | | | | | Vaibhav |
| KAS loss-goes-down (PR-B) | | | | | | Sunil |
| Baseline 1(b) | | | | scored / positions / bytes per s, peak mem, bpb, ≥2 seeds | | Sunil |
| Design 3 packing (bring-up) | | class [#940](https://github.com/theschoolofai/era-v5-lab/pull/940) | | Colab T4 / small model — not official 2×; official V4 arms = window + packed-no-mask until mask patch | Bring-up | Shashank |
| Design 6 waste (bring-up) | | class [#920](https://github.com/theschoolofai/era-v5-lab/pull/920) | | Within-run stalls + #869 outside-step ~24%; between-job idle needs TSAI timestamps | Bring-up | Shashank |
| Design 5 NS share | | tip [#108](https://github.com/vaibh27/era-v5-lab/pull/108) | | Full + zero-grad + bpb after P0 / TSAI optim note | Prep | Adinath |
