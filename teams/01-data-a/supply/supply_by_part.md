Cleaned = raw x 0.9794 (sample-v0: cleaning dropped 1.97% of docs, dedup 1,345 of 1,414,996).

| Part | Measured p1536 (B) | Card-only, other tokenizer (B) | Counted rows | Rows with no number | Raw max share of 20T, 4 passes | 3 passes | Cleaned, 4 passes | 3 passes |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| code | 265.5 | 0.0 | 10 | opc-annealing-corpus algorithmic | 5.31% | 3.98% | 5.20% | 3.90% |
| synthetic code | 0.0 | 0.0 | 2 | opc-annealing-corpus synthetic; Nemotron-Pretraining-Code-v1 synthetic | 0.00% | 0.00% | 0.00% | 0.00% |
| code-adjacent | 45.8 | 0.0 | 7 | commitpackft | 0.92% | 0.69% | 0.90% | 0.67% |
| math | 262.2 | 11.0 | 5 | Nemotron-CC-Math-v1 | 5.46% | 4.10% | 5.35% | 4.01% |
| English real | 17,365.8 | 0.0 | 2 | - | 347.32% | 260.49% | 340.15% | 255.11% |
| English synthetic | 54.8 | 1,900.0 | 4 | Nemotron-CC-v2 synthetic | 39.10% | 29.32% | 38.29% | 28.72% |
| science | 1,227.9 | 42.0 | 4 | common-pile pubmed | 25.40% | 19.05% | 24.87% | 18.66% |
