Cleaned = raw x 0.9794 (sample-v0: cleaning dropped 1.97% of docs, dedup 1,345 of 1,414,996).

| Part | Measured p1536 (B) | Card-only, other tokenizer (B) | Counted rows | Rows with no number | Raw max share of 20T, 4 passes | 3 passes | Cleaned, 4 passes | 3 passes |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| code | 84.3 | 0.0 | 6 | - | 1.69% | 1.26% | 1.65% | 1.24% |
| synthetic code | 0.0 | 0.0 | 0 | - | 0.00% | 0.00% | 0.00% | 0.00% |
| code-adjacent | 10.6 | 0.0 | 3 | commitpackft | 0.21% | 0.16% | 0.21% | 0.16% |
| math | 219.4 | 0.0 | 2 | - | 4.39% | 3.29% | 4.30% | 3.22% |
| English real | 3,664.0 | 0.0 | 1 | - | 73.28% | 54.96% | 71.77% | 53.83% |
| English synthetic | 0.0 | 1,900.0 | 1 | - | 38.00% | 28.50% | 37.22% | 27.91% |
| science | 1,206.9 | 0.0 | 1 | - | 24.14% | 18.10% | 23.64% | 17.73% |
