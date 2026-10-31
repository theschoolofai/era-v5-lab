# Tokenizer decoding determinism and optional MPS codec checks

`src/determinism/tokenizer_decode_cpu.py` tests token IDs -> decoded text on CPU.
`src/determinism/codec_v1_cpu_mps.py` tests raw byte tables -> forward KE vectors on MPS,
with CPU codec comparisons. Neither is the KE-vector-to-ID reference decoder.
The tokenizer outputs use the explicit tokenizer_decode_cpu prefix.
The original week-plan filename was decode_cpu_sha256.txt; its historical
contents and hashes are preserved under the clearer name.

This checks that decoding every token ID gives identical results in three fresh
CPU processes. It uses the Rust `tokenizers` engine through its Python API; no
model, PyTorch, GPU, or random seed is needed.

Run from the lab repository root with a local tokenizer artifact:

```sh
python3 -m pip install tokenizers==0.22.2 pytest
python3 teams/04-ke2/src/determinism/tokenizer_decode_cpu.py \
  --tokenizer /path/to/tokenizer.json \
  --expected-sha256 01d968a7970b029c071b29f060abf6104b66168dedf2ff3b1a0290a545739fff
python3 -m pytest teams/04-ke2/tests/test_tokenizer_decode_cpu.py -q
```

Keep the tokenizer outside this repository. The script never downloads artifacts.
Obtain `tokenizer.json` from https://huggingface.co/theschoolofai/BrahmicTokenizer-131K/tree/main
and verify its hash with the command above.
The SHA above identifies the BrahmicTokenizer-131K artifact reviewed for week 1.
When G3 supplies a new tokenizer, verify its identity and rerun with its SHA.
The metadata records the exact Python and tokenizers versions used.

## What each pass does

1. Read the tokenizer file, compute its SHA-256 and load that same file content.
2. Require a contiguous vocabulary and visit every ID in ascending order.
3. Call `decode([id], skip_special_tokens=False)` for every ID, including specials.
   Require each special to decode to its literal content, matching Swati's decode
   table policy. Revisit this policy with G10's final special-token list.
4. Encode each decoded string as UTF-8. Preserve U+FFFD, whitespace and all other
   returned characters; apply no extra normalization or cleanup.
5. Hash the framed records using SHA-256, then report the hash and environment.

The parent starts three separate Python processes and requires their hashes,
tokenizer identities, coverage and environment records to agree. A failed child
or disagreement produces a nonzero exit status without writing passing results.

## Hash format and outputs

The hash begins with ASCII `ke2-decode-cpu-v1` followed by LF. Each record is the
token ID as four big-endian bytes, the UTF-8 byte length as four big-endian bytes,
then the UTF-8 bytes. Explicit lengths distinguish different record boundaries.

- `teams/04-ke2/results/tokenizer_decode_cpu_sha256.txt`: three hashes, one per pass.
- `teams/04-ke2/results/tokenizer_decode_cpu_metadata.json`: artifact identity, versions,
  coverage, settings and matching hashes. No local file paths are recorded.

This hashes decoded token records, rather than `.npz` files, padded table arrays,
or Kronecker vectors. Its hashes need only match each other; other serialization
formats have different hashes. P=32 and P=64 are downstream table capacities and
do not enter single-token decoding, so decoding determinism is checked once.

The test covers repeatability, including repeatability of replacement characters.
It does not prove raw-byte preservation, collision freedom, codec determinism,
or determinism across library versions and different machines. Those are separate
checks. The raw-byte table fixes information loss that this decode baseline retains.

## References

- Table PR: https://github.com/theschoolofai/era-v5-lab/pull/7
- Reviewed builder commit: `aac72afd5806b289c515486034abcc0445fe3a43`.
- Proof: https://github.com/subramanyanaik/era-v5-lab/blob/ke2-forward-proof/teams/04-ke2/theorem/theorem1/proof.md

The decoder output was compared against the reviewed table builder for every
token ID of the pinned tokenizer. All 131,072 inputs matched. All three CPU runs
produced `3bbeb19318f233b76c3a5d725a7034327681837ef60d9aa2367518db1ef08e57`.
The generated metadata is the record of these runs; rerun after changing the
tokenizer, decoder or token policy.

## Optional MPS codec experiment

The CPU tokenizer-decoding result above stands separately. `codec_v1_cpu_mps.py` adds an
optional Apple GPU experiment on the forward codec, after table construction.
It excludes the learned projection and backward pass.

Use the v2-format raw tables from the reviewed tables PR and a local checkout of
the v1 codec (reviewed upstream commit
`d07cb543f03d7a72a7c35bc68cfb795bcb02e1ec`). Keep those inputs outside this PR;
the results record both table content hashes and the exact codec file SHA-256.
Install PyTorch and NumPy in addition to the CPU-check requirements. The measured
versions are recorded in `codec_v1_cpu_mps_results.json`.

```sh
python3 teams/04-ke2/src/determinism/codec_v1_cpu_mps.py \
  --tables /path/to/tables \
  --codec-src /path/to/kronecker-embeddings/src
```

This starts three fresh processes. Each processes all raw token IDs in ascending
order at P=32 and P=64 using float32 and batches of 512. Smaller batches can be
selected with `--batch-size`; `--limit` is for smoke tests and is explicitly
reported as partial coverage. The default tokenizer hash is the pinned Brahmic
artifact; use `--expected-tokenizer-sha256` for a different agreed artifact.

CPU fallback and MPS fast math are disabled. Every output must be on MPS and
finite. Each batch is synchronized and copied back for hashing. The hash covers
a sorted JSON header describing the shape and dtype, followed by output values
as little-endian float32 in token-ID order. It is independent of batch boundaries
as a serialization format; computation may still depend on batch size, so the
measurement records and fixes it across runs.

The JSON and text outputs under `teams/04-ke2/results/codec_v1_cpu_mps_*` distinguish:

- Three matching MPS hashes: observed repeatability for this fixed environment.
- CPU/MPS bitwise equality and maximum absolute difference.
- CPU/MPS numerical agreement using `rtol=1e-5`, `atol=1e-6`, with counts outside
  tolerance and counts of bitwise-different values and rows.
- A separate strict-determinism probe on the first eight rows at each P.

The full measurement uses ordinary mode (`use_deterministic_algorithms(False)`).
PyTorch may reject the strict probe because its MPS scatter implementation lacks
deterministic support. That rejection is recorded; it is not counted as a strict
mode pass. Matching ordinary-mode hashes cannot establish a general guarantee.
CPU and MPS hashes need not match each other because floating-point kernels may
produce small numerical differences.

The script saves results even when repeated hashes or numerical agreement fail,
and exits nonzero for either failure. Unavailable MPS, corrupt/mismatched tables,
nonfinite output, or an unexpected kernel error aborts the run. Strict-mode
rejection alone does not fail the ordinary-mode experiment.

Portable tests run with the normal suite; the MPS integration test is opt-in and
uses only 16 rows to verify the runner without repeating the full study:

```sh
KE2_RUN_V1_MPS_TESTS=1 \
KE2_V1_MPS_TABLES=/path/to/tables \
KE2_V1_CODEC_SRC=/path/to/kronecker-embeddings/src \
python3 -m pytest teams/04-ke2/tests/test_codec_v1_cpu_mps.py -q
```

PyTorch references:
[MPS backend](https://docs.pytorch.org/docs/2.14/notes/mps.html),
[deterministic algorithms](https://docs.pytorch.org/docs/2.14/generated/torch.use_deterministic_algorithms.html).

### Measured MPS results, 26 October 2026

Three fresh processes each covered IDs 0 through 131071 at both P values.
The measured environment was macOS 26.7.1 arm64, PyTorch 2.14.0, NumPy 2.4.4,
Python 3.14.9; batch size 512 and float32. Input and output hashes are in
`results/codec_v1_cpu_mps_results.json` and `results/codec_v1_cpu_mps_sha256.txt`.

| P | Matching MPS hashes | Matching CPU hashes | CPU/MPS maximum absolute difference | Values outside tolerance |
|---|---|---|---|---|
| 32 | 3 of 3 | 3 of 3 | 7.62939453125e-6 | 0 |
| 64 | 3 of 3 | 3 of 3 | 1.52587890625e-5 | 0 |

CPU/MPS hashes differ: bitwise differences affect 62,623 rows at P=32 and 83,216
rows at P=64, consistently across the three processes. All values satisfy
`abs(MPS - CPU) <= 1e-6 + 1e-5 * abs(CPU)`.

All six strict-mode probes were rejected with
`scatter_reduce_mps does not have a deterministic implementation`.
The outcome is observed ordinary-mode repeatability for this environment and
batch configuration, with numerical CPU agreement. Strict MPS determinism is
not established.
