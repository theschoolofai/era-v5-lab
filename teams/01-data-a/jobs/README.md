# Data A jobs

| Job | Request / configuration | Execution evidence |
|---|---|---|
| Tokenizer sample v0 cleaning | [Request](2026-11-02-tokenizer-sample-v0-clean.md), [run instructions and pinned inputs](../spec_v1/jobs/README.md) | [Local log](logs/2026-11-02-tokenizer-sample-v0-local.txt), [summary](logs/2026-11-02-tokenizer-sample-v0-summary.json), [rule counts](logs/2026-11-02-tokenizer-sample-v0-rule-counts.csv), [validation log](logs/2026-11-02-tokenizer-sample-v0-validation.txt) |
| Cleaned-sample overlap measurement | Original request/implementation absent from this checkout; provenance is recorded in the result README | [2026-11-04 overlap bundle](results/2026-11-04-overlap/README.md) |

Requests, logs, and result bundles live here. The sample config and checksum-pinned manifest retain their existing paths in `spec_v1/jobs/`; this index connects the two locations. Cleaned document text and Parquet outputs are kept outside the committed job evidence.

For sample commands and the train/heldout output layout, use the [sample guide](../spec_v1/jobs/README.md). The existing local log is a selected-part test; completeness must be read from the run's manifest/summary rather than inferred from its filename.
