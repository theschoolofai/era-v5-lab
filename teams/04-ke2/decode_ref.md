# KE1 cosine reference decoder: contract and CPU comparison

`src/decode_ref.py` is G6's CPU/float64 correctness reference for unprojected
forward-codec vectors from the public KE1 `kronecker-embeddings` package. This
documents the existing structured cosine implementation; its scoring, API and
result-hash format are unchanged.

## Inputs and outputs

Queries have shape `(N, 256 * P)`, or `(256 * P,)` for one query. Supply a
`CodeTable` built from the same byte table and normalization settings as the
forward encoder. NumPy and torch inputs are copied/promoted to CPU float64;
accelerator inputs are transferred to CPU, not decoded on the accelerator.
Promotion does not restore precision lost during float32 forward encoding.
Wrong widths, nonfinite values and zero query vectors are rejected.

```python
from decode_ref import CodeTable, decode
from ke2.config import TOKENIZER_SHA256
from ke2.tables import ByteTable

raw = ByteTable.load(
    "teams/04-ke2/results/tables/raw_table_P32.npz",
    tokenizer_sha256=TOKENIZER_SHA256,
)
result = decode(vectors, CodeTable.from_byte_table(raw))
result.token_ids, result.token_bytes, result.scores, result.margins, result.sha256()
```

For each query, every supplied candidate is scored using cosine similarity.
The largest score wins and the margin is **best cosine minus second-best
cosine**. Exact ties choose the lowest token ID and have margin zero. The
margin is neither a squared-distance gap nor a calibrated probability.

Raw tables return original token byte payloads. Decode-text tables return their
stored UTF-8 text bytes, potentially including U+FFFD substitutions introduced
before encoding. Matching those stored bytes does not recover original raw
bytes lost by text decoding. The current raw tables are untruncated; a truncated
table could return only its retained byte prefix. A collision cannot uniquely
identify its source ID.

The result hash includes table identity, IDs, stored bytes, scores and margins.
Repeatability was checked in the tested environment, across query chunk sizes
and a fresh process. Cross-platform bitwise equality is not asserted.

## Correctness results and reproduction

`results/decode_ref/summary.json` records **4,096 query IDs against all 131,072
candidates**, for raw and decode-text tables at P=32 and P=64. These are
full-vocabulary cosine margins. Raw tables recover all 4,096 tested IDs and
original payloads at both capacities. Decode-text tables recover 4,057 IDs;
their 40 tied queries reflect known lossy-table collisions, not 40 distinct
failed IDs. The separate collision audit covers all vocabulary rows.

The summary records exact sampled IDs, tokenizer/table identities, source
fingerprints, software environment, candidate counts and timing scope. The
historical `bytes_recovered` JSON field counts **stored table-row byte matches**;
`byte_comparison` now makes that interpretation explicit. Reported seconds
include code-table construction and decoding, excluding forward encoding and
the fresh-process verification. They are not the microbenchmark timings below.

From the repository root, with the pinned tokenizer available locally:

```sh
KRONECKER_SRC=/path/to/kronecker-embeddings/src \
KE2_TOKENIZER=/path/to/tokenizer.json \
python3 teams/04-ke2/src/run_experiment.py --skip tables proofs cpu_determinism mps

KRONECKER_SRC=/path/to/kronecker-embeddings/src \
KE2_TOKENIZER=/path/to/tokenizer.json \
python3 -m pytest teams/04-ke2/tests -q
```

## Why retain structured cosine scoring

The KE1 codes have only two coordinate values: one on the byte-position support
and another elsewhere. The decoder uses that structure to compute dot products
and norms without storing a dense `V * D` float64 code matrix. Dense storage
alone would require about 8.6 GB at P=32 or 17.2 GB at P=64 for 131,072 tokens,
before copies and temporary arrays.

This is an implementation advantage, not evidence that cosine as a metric is
inherently faster than squared Euclidean distance. A structured squared-distance
scorer could reuse dot products and norms. That would change the metric/margin
contract and require separate validation; the present requirements do not
justify replacing the existing reference.

`chunk_rows` limits how many queries are scored together. Its default estimates
a 256 MiB budget for scoring temporaries, not total process memory. Input copies,
byte/support arrays, outputs and other temporaries also occupy memory. Calling
`CodeTable.codes` on every token explicitly materializes the dense matrix;
reserve that helper for small checks.

## Separate CPU performance experiment

`src/benchmark_ke1_decode_ref.py` compares the current structured cosine decoder
with a dense direct squared-distance baseline matching the earlier approach.
The baseline is a benchmark kernel, not a second supported decoder API.

```sh
python3 teams/04-ke2/src/benchmark_ke1_decode_ref.py \
  --tables teams/04-ke2/results/tables \
  --out teams/04-ke2/results/decode_ref/ke1_cosine_vs_dense_euclidean_cpu.json \
  --full-cosine
```

The paired experiment uses the same 2,048 raw-byte candidates, 16 mathematical
float64 exact-code queries, seeds and ID mapping. Input checksums verify that
the candidates/queries match across methods. Every case runs in a separate
fresh process with three timed decode repetitions; table construction is timed
separately. Thread environment variables are fixed to one. Allocation tracing
is enabled, so these are instrumented local timings. Process peak RSS includes
imports/setup; traced Python/NumPy allocations are a different measure. Both
cases retain a structured table used to generate common queries.

Measured on Darwin arm64, Python 3.14.9, NumPy 2.4.4. MB below is decimal (1,000,000 bytes).

| P | Implementation | Candidates | Queries | Median decode (ms) | Peak process RSS (MB) |
|---|---|---:|---:|---:|---:|
| 32 | Structured cosine | 2,048 | 16 | 1.06 | 55.2 |
| 32 | Dense squared distance | 2,048 | 16 | 233.41 | 353.9 |
| 32 | Structured cosine | 131,072 | 16 | 105.05 | 278.3 |
| 64 | Structured cosine | 2,048 | 16 | 1.22 | 67.5 |
| 64 | Dense squared distance | 2,048 | 16 | 459.65 | 667.2 |
| 64 | Structured cosine | 131,072 | 16 | 106.91 | 293.6 |

The measured structured implementation was faster and used less peak process
memory than this dense baseline in the paired cases. This supports retaining
the existing reference, within the experiment scope above.

Both methods must recover every tested ID and stored payload with positive
margins and repeatable score fingerprints. This experiment uses exact-code
queries; cosine and squared distance can rank noisy/scaled inputs differently,
and their margin values are not compared for equality. The optional full-cosine
case checks all vocabulary candidates; a full-vocabulary dense case is not
implicitly attempted. The JSON records every timing, memory observation,
environment, source fingerprint and input identity.

These measurements are CPU-only microbenchmarks. They do not measure GPU
performance, model inference/training throughput or model accuracy. G6 should
compare fast implementations using the same representation, candidate set,
metric and tie rule, with an agreed tolerance for different precision/backends.
