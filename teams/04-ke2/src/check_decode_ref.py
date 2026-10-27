#!/usr/bin/env python3
"""Validate the reference against a locally authorized KE2 codec; no downloads.

The candidate codebook and queries both use a declared sample of real token IDs.
This is not an exhaustive full-vocabulary nearest-neighbour search.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

TOKENIZER_SHA = "01d968a7970b029c071b29f060abf6104b66168dedf2ff3b1a0290a545739fff"


def load_raw_bytes(path, expected_tokenizer_sha):
    """Validate a raw-byte table artifact and recover complete token payloads.

    Parameters
    ----------
    path : str or pathlib.Path
        Local .npz file in the reviewed v2 raw-table format. Rows must retain
        complete bytes: n_truncated must be zero.
    expected_tokenizer_sha : str
        SHA-256 identity that must match the table's tokenizer metadata.

    Returns
    -------
    tuple of (list of bytes, str)
        Unpadded payloads in token-ID/row order and the verified table-content
        SHA-256. This byte table is not itself the encoded KE candidate matrix.

    Raises
    ------
    ValueError
        If format, identity, truncation, dtype, shape, length or hash checks fail.
    KeyError
        If a required artifact field is absent.
    OSError
        If the file cannot be opened or read.
    """
    import numpy as np

    with np.load(path, allow_pickle=False) as z:
        if int(z["format_version"]) != 2 or str(z["kind"]) != "raw":
            raise ValueError("Expected a v2-format raw table")
        if str(z["tokenizer_sha256"]) != expected_tokenizer_sha:
            raise ValueError("Tokenizer identity mismatch")
        if int(z["n_truncated"]) != 0:
            raise ValueError("Source raw table must preserve complete token bytes")
        P, buf, lengths = int(z["pos_dim"]), z["bytes"], z["lengths"]
        if buf.dtype != np.uint8 or lengths.dtype != np.int16:
            raise ValueError("Unexpected source table dtype")
        if buf.ndim != 2 or buf.shape[1] != P or lengths.shape != (len(buf),):
            raise ValueError("Invalid source table shape")
        if (lengths < 0).any() or (lengths > P).any():
            raise ValueError("Invalid source byte lengths")
        digest = hashlib.sha256(f"ke2-table-v2|raw|{P}|".encode())
        digest.update(np.ascontiguousarray(buf).tobytes())
        digest.update(np.ascontiguousarray(lengths).tobytes())
        if digest.hexdigest() != str(z["table_sha256"]):
            raise ValueError("Source table content hash mismatch")
        return [buf[i, :int(n)].tobytes() for i, n in enumerate(lengths)], digest.hexdigest()


def worker(args):
    """Measure sampled KE2 encode/decode round trips in one CPU process.

    Parameters
    ----------
    args : argparse.Namespace
        Worker options: ke2_src (Path to the external src directory), raw_table
        (Path to the raw .npz), expected_tokenizer_sha256 (str), sample_size
        (int, at least two) and seed (int for reproducible candidate selection).

    Returns
    -------
    dict
        JSON-compatible environment/source identities, selected candidate IDs
        and per-capacity coverage, distance/margin statistics and output hashes.
        Both queries and candidate tables use the same declared sample.

    Raises
    ------
    ValueError
        If the source or raw table is wrong, sample size is invalid, or a sampled
        token exceeds the smallest tested position capacity (32 bytes).
    AssertionError
        If float64 construction, IDs, bytes, margins or native inverse checks fail.
    ImportError
        If the authorized external codec dependency is unavailable.
    """
    import numpy as np
    from decode_ref import CodeTable, decode_ref, results_sha256

    source = args.ke2_src.resolve()
    sys.path.insert(0, str(source))
    import kronecker_v2.codec as ke2

    if Path(ke2.__file__).resolve().parent != source / "kronecker_v2":
        raise ValueError("Imported codec does not match --ke2-src")
    raw, source_sha = load_raw_bytes(args.raw_table, args.expected_tokenizer_sha256)
    if not 2 <= args.sample_size <= len(raw):
        raise ValueError("sample-size must be between two and source vocabulary size")
    ids = np.sort(np.random.default_rng(args.seed).choice(len(raw), args.sample_size, replace=False))
    sampled = [raw[i] for i in ids]
    if max(map(len, sampled)) > 32:
        raise ValueError("Sample contains tokens exceeding the smallest tested position capacity")
    result = {"environment": {"numpy": np.__version__, "python": platform.python_version(),
              "system": platform.system(), "machine": platform.machine(), "device": "cpu", "dtype": "float64",
              "decoder_sha256": hashlib.sha256((Path(__file__).parent / "decode_ref.py").read_bytes()).hexdigest(),
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "external_source_sha256": {name: hashlib.sha256((source / "kronecker_v2" / name).read_bytes()).hexdigest()
                                          for name in ("codec.py", "codebooks.py")}},
              "source_table_sha256": source_sha, "source_vocabulary_size": len(raw),
              "candidate_ids": ids.tolist(), "tables": {}}
    for P in (32, 64):
        config = {"d_c": 64, "L_max": P, "seed": 0, "variant": "v2",
                  "byte_method": "hadamard_bits", "pos_kind": "dft", "overflow": "truncate"}
        codec = ke2.KroneckerCodec(**config)
        table = CodeTable.from_codec(codec, sampled, ids)
        queries = codec.encode(sampled[::-1])
        if queries.dtype != np.float64:
            raise AssertionError("Forward codes must be constructed in float64")
        outputs = decode_ref(queries, table)
        if [r.token_id for r in outputs] != ids[::-1].tolist():
            raise AssertionError("Reference returned incorrect token IDs")
        if [r.raw_bytes for r in outputs] != sampled[::-1]:
            raise AssertionError("Reference returned incorrect raw bytes")
        if not all(r.margin > 0 for r in outputs):
            raise AssertionError("Expected unambiguous code matches")
        if codec.decode(queries) != sampled[::-1]:
            raise AssertionError("Independent table reference disagrees with native byte inverse")
        result["tables"][str(P)] = {"encoder_config": config, "query_count": len(outputs), "candidate_count": len(ids),
            "code_width": table.codes.shape[1], "ids_and_raw_bytes_match": True,
            "native_inverse_agrees": True, "minimum_margin": min(r.margin for r in outputs),
            "max_best_squared_distance": max(r.best_distance for r in outputs), "sha256": results_sha256(outputs)}
        del table, queries, outputs
    return result


def verify_runs(runs):
    """Require complete agreement across exactly three process reports.

    Parameters
    ----------
    runs : list of dict
        JSON-compatible reports from worker. Equality includes environment,
        source identities, candidate selection, statistics and output hashes.

    Returns
    -------
    None
        Successful return means all three reports compare equal.

    Raises
    ------
    ValueError
        If there are not exactly three reports or any report differs.
    """
    if len(runs) != 3 or any(run != runs[0] for run in runs[1:]):
        raise ValueError("Expected three identical CPU reference-decoding results")


def main(argv=None):
    """Run the CLI worker or coordinate three processes and save local results.

    Parameters
    ----------
    argv : sequence of str, optional
        CLI arguments without the program name; None reads sys.argv[1:].
        Required flags are --raw-table, --ke2-src and --out. Optional flags set
        sample size (3072), seed (20261027), expected tokenizer SHA, or worker mode.

    Returns
    -------
    int
        Zero on success. Worker mode prints one JSON report. Coordinator mode
        verifies three reports and writes decode_ref_results.json and
        decode_ref_cpu_sha256.txt to the explicitly selected local output folder.

    Raises
    ------
    RuntimeError
        If a worker subprocess fails.
    ValueError
        If three completed process reports disagree.
    SystemExit
        For argparse help or invalid command-line arguments.
    OSError
        If a subprocess cannot start or output files cannot be written.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-table", required=True, type=Path)
    parser.add_argument("--ke2-src", required=True, type=Path)
    parser.add_argument("--sample-size", type=int, default=3072)
    parser.add_argument("--seed", type=int, default=20261027)
    parser.add_argument("--expected-tokenizer-sha256", default=TOKENIZER_SHA)
    parser.add_argument("--out", required=True, type=Path, help="local results directory; review sharing permissions separately")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        print(json.dumps(worker(args), sort_keys=True))
        return 0
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--raw-table", str(args.raw_table.resolve()),
               "--ke2-src", str(args.ke2_src.resolve()), "--sample-size", str(args.sample_size), "--seed", str(args.seed),
               "--expected-tokenizer-sha256", args.expected_tokenizer_sha256, "--out", str(args.out.resolve())]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MKL_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1")
    runs = []
    for index in range(3):
        process = subprocess.run(command, env=env, capture_output=True, text=True)
        if process.returncode:
            raise RuntimeError(f"Reference CPU process {index + 1} failed: {process.stderr}")
        runs.append(json.loads(process.stdout))
        print(f"Completed KE2 encode->reference decode process {index + 1}/3", flush=True)
    verify_runs(runs)
    report = {"scope": "sampled queries and sampled candidate table; not full-vocabulary nearest-neighbour search",
              "metric": "squared Euclidean distance", "margin": "second-best distance minus best distance",
              "ties": "smallest token ID", "seed": args.seed,
              "tokenizer_sha256": args.expected_tokenizer_sha256, "all_three_runs_identical": True, "runs": runs}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "decode_ref_results.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# P run SHA256 (token IDs, raw bytes, distances, margins)\n"]
    for P in (32, 64):
        for index, run in enumerate(runs, 1):
            lines.append(f"{P} {index} {run['tables'][str(P)]['sha256']}\n")
    (args.out / "decode_ref_cpu_sha256.txt").write_text("".join(lines))
    print("PASS: exact token-ID/raw-byte round trips and identical output/margin hashes in three CPU processes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
