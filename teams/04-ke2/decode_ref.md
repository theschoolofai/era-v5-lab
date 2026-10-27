# CPU float64 reference decoder for G6

`src/decode_ref.py` implements the inverse interface: a batch of forward KE code
vectors plus a candidate code table produces token IDs, raw bytes and margins.
It is independent of tokenizer text decoding, model logits, a learned projection,
and the encoder's native byte decoder. NumPy is its only runtime dependency.

## Runnable API example

Use a Python environment with NumPy installed (`python3 -m pip install numpy`).
From the lab repository root, start Python with
`PYTHONPATH=teams/04-ke2/src python3`. This complete example uses an invented
two-dimensional table to demonstrate the API, not actual KE2 vectors:

```python
from decode_ref import CodeTable, decode_ref, results_sha256

table = CodeTable(
    codes=[[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]],
    raw_bytes=[b"cat", b"dog", b"bat"],
    token_ids=[10, 20, 30],
)
results = decode_ref([[0.9, 0.1]], table)
for result in results:
    print(result.token_id, result.raw_bytes, f"{result.margin:.2f}")
print(results_sha256(results))
```

The first printed line is `10 b'cat' 1.60`: squared distances are 0.02 for the
winner and 1.62 for the runner-up, giving margin 1.60. The second line is the
result fingerprint. `results[0]` also exposes `best_distance` and `second_distance`.

To build real candidates, use the externally supplied forward codec and original
token bytes. The codec object and vocabulary come from the caller:

```python
table = CodeTable.from_codec(codec, token_bytes, token_ids)
queries = codec.encode([token_bytes[7], token_bytes[2]])
results = decode_ref(queries, table)
```

The decoder does not need text or `tokenizer.json` when the vectors, IDs and raw
bytes are already supplied. The validation runner below uses an existing raw-byte
artifact to obtain a reproducible sample; it constructs a new encoded code table.

## Input and output

Candidate codes have shape `(V, D)` and queries have shape `(B, D)`, where `V`
is candidate count, `B` is query count, and `D` is code-vector width.
Supply at least two candidates, one bytes object and a unique nonnegative ID per
row. Token IDs default to row indices when omitted; if another adapter sorts
the vocabulary, pass the original IDs explicitly. Outputs preserve query order.

Each `DecodeResult` contains `token_id`, `raw_bytes`, `best_distance`,
`second_distance` and `margin`. CodeTable constructor parameters and every
function's inputs, returns and errors are documented in their docstrings.

## Matching contract

The explicit score contract proposed for G4/G6 is **squared Euclidean distance**:

```
distance(query, candidate) = sum((query - candidate) ** 2)
margin = second_best_distance - best_distance
```

The smallest distance wins. Exact distance ties choose the smallest token ID,
regardless of row order, and produce zero margin. Every input returns one nearest
candidate; no confidence threshold or out-of-vocabulary rejection is imposed.
For unit-norm candidate codes the winner also maximizes the dot product, but a
squared-distance margin uses different units from a dot-product gap. Agree on
this metric before comparing G6's fast implementation.

Raw bytes are copied from the winning candidate unchanged, including NULs and
incomplete UTF-8 fragments. No `decode([id])`, normalization, trimming or lossy
text conversion is involved. A zero-margin collision cannot identify which of
several original tokens was intended. The returned bytes belong to the chosen
token; they are not proof that bytes discarded by an overflowing encoder were
recovered. Collisions remain visible rather than being treated as unique matches.

## Representation and numerical rules

Queries and table rows must use the **same forward-codec representation and
configuration**. For the locally supplied KE2 codec, `CodeTable.from_codec` uses
`codec.encode(...)` for table rows. Do not mix those queries with a differently
transformed model-head table merely because the vector widths match. Hidden
states and vocabulary logits are not valid substitutes for code vectors.

Inputs must be on CPU. Scores, best/second-best distances and margins are computed
in float64. The table owns its arrays and leaves caller inputs unchanged. Lower
precision arrays can be promoted for scoring; promotion does not recover lost
precision. KE2 validation constructs forward codes in float64 from the outset.

The implementation deliberately scans every supplied candidate using direct
squared differences and a fixed reduction without BLAS or approximate search.
`chunk_size` bounds temporary candidate memory without changing score arithmetic.
The full dense code table still consumes `V * D * 8` bytes, plus copies; this
reference prioritizes correctness over throughput and full-vocabulary feasibility.
Nonfinite inputs and overflowing distance arithmetic fail rather than yielding
an arbitrary token.

`results_sha256` hashes outputs in query order. Each record contains a big-endian
int64 token ID, three float64 values (best distance, second distance, margin), a
uint64 byte length and the raw bytes, following a versioned header. Repeatability
is checked in a fixed software/hardware environment; cross-platform bitwise
identity is not asserted.

## Validation

Portable tests cover manual and independent-oracle distances, noisy queries,
byte fragments, duplicate codes and ties, copied inputs, invalid input, candidate
chunking, reduction overflow, hash repeatability and a 3,000-code structured round
trip. Install pytest to run them (`python3 -m pip install pytest`).

Optional integration tests use an authorized local KE2 checkout without copying
its implementation. They cover 3,000 native float64 codes, the production code
widths for capacities 32 and 64, byte fragments, empty/NUL bytes and an explicit
truncation collision. Without `KE2_SRC`, these tests skip with a reason.

```sh
python3 -m pytest teams/04-ke2/tests -q
KE2_SRC=/path/to/authorized/ke2/src \
  python3 -m pytest teams/04-ke2/tests -q
```

The measured round-trip runner samples 3,072 actual tokenizer IDs, builds table
rows with the external float64 KE2 encoder and separately encodes queries in
reverse order. It checks every returned ID and raw byte string, positive margins,
and agreement with the native byte inverse. Three fresh CPU processes must
produce identical result and margin hashes. It tests both position capacities.

```sh
python3 teams/04-ke2/src/check_decode_ref.py \
  --raw-table /path/to/raw_table_P64.npz \
  --ke2-src /path/to/authorized/ke2/src \
  --out /path/to/local/results
```

The source raw table must have the verified v2 format, match the expected tokenizer
hash, and contain untruncated bytes. `--expected-tokenizer-sha256` selects another
agreed artifact. The runner records sampled IDs, coverage, score definitions,
source identities, software versions and hashes. `--sample-size` and `--seed`
make the choice explicit and reproducible. The source table does not serve as
the KE2 code table: it supplies bytes to the new forward encoder.

**Coverage limit:** queries and candidate tables both use the declared sample.
This validates a few-thousand-token round trip, not a search against all 131,072
candidates. A sampled candidate table gives sampled-table margins, not full-vocab
margins. Results are written only to the explicitly selected `--out` directory;
local KE2 validation artifacts are kept outside the public lab checkout.

## Using the reference to check G6's fast decoder

Give both implementations identical query vectors, candidate vectors, IDs and
raw bytes. Match token IDs and raw bytes exactly, use the same smallest-ID tie
rule, and compare squared distances/margins with an explicitly agreed tolerance
if the fast implementation uses a different numerical precision or backend.
The reference's CPU repeatability hashes need not equal a GPU implementation's
hashes. A valid comparison must use the same complete candidate set: matching a
sample-only margin against a full-vocabulary margin would be misleading.
