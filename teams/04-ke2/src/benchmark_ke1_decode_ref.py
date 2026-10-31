#!/usr/bin/env python3
"""Compare structured KE1 cosine decoding with a dense squared-distance baseline.

CPU/float64 exact-code microbenchmark, not GPU or model throughput. Each case
runs in a fresh process. The dense kernel below is only a benchmark baseline;
src/decode_ref.py remains the reference API. Margins use different units.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

import decode_ref
from ke2.config import TOKENIZER_SHA256
from ke2.tables import ByteTable


def dense_distance_baseline(queries, codes, chunk_size=256):
    """Score a dense candidate matrix using the earlier direct-distance approach.

    Parameters
    ----------
    queries : ndarray, shape (N, D), float64
        Finite CPU exact-code queries.
    codes : ndarray, shape (V, D), float64
        Candidate vectors, in ascending original-token-ID order.
    chunk_size : int
        Positive candidate chunk size; bounds subtraction temporaries only.

    Returns
    -------
    tuple[ndarray, ndarray, ndarray]
        Winning row indices, best squared distances and second-minus-best gaps.
        Exact ties choose the lowest row, equivalent here to the lowest ID.
    """
    rows, best, margins = [], [], []
    for query in queries:
        distances = np.empty(len(codes), dtype=np.float64)
        for start in range(0, len(codes), chunk_size):
            delta = codes[start : start + chunk_size] - query
            distances[start : start + chunk_size] = np.einsum("ij,ij->i", delta, delta, optimize=False)
        first, second = np.lexsort((np.arange(len(codes)), distances))[:2]
        rows.append(first)
        best.append(distances[first])
        margins.append(distances[second] - distances[first])
    return np.array(rows), np.array(best), np.array(margins)


def worker(args):
    """Measure one method/capacity/candidate count in an isolated CPU process.

    Parameters
    ----------
    args : argparse.Namespace
        tables (Path), capacity (int), candidates/queries/repeats (positive ints),
        method ('cosine' or 'dense_euclidean'), seed/query_seed (ints), and
        expected_tokenizer_sha256 (str).

    Returns
    -------
    dict
        Timings, memory observations, input/source identities and correctness
        checks. RSS includes imports and setup; traced memory is a different
        allocation measure. Neither is an estimate of GPU memory.
    """
    tracemalloc.start()
    raw = ByteTable.load(
        args.tables / f"raw_table_P{args.capacity}.npz", tokenizer_sha256=args.expected_tokenizer_sha256
    )
    if not 2 <= args.candidates <= raw.vocab_size or not 1 <= args.queries <= args.candidates or args.repeats < 1:
        raise ValueError("Require 2 <= candidates <= vocabulary, 1 <= queries <= candidates, repeats >= 1")
    ids = np.sort(np.random.default_rng(args.seed).choice(raw.vocab_size, args.candidates, replace=False))
    sub = ByteTable(
        "raw", args.capacity, raw.bytes[ids].copy(), raw.lengths[ids].copy(), 0, 0, 0, args.expected_tokenizer_sha256
    )
    query_rows = np.random.default_rng(args.query_seed).choice(len(ids), args.queries, replace=False)
    # Retained in both methods to generate identical mathematical float64 queries.
    shared = decode_ref.CodeTable.from_byte_table(sub)
    queries = shared.codes(query_rows)
    start = time.perf_counter()
    if args.method == "cosine":
        candidates = decode_ref.CodeTable.from_byte_table(sub)
    else:
        candidates = np.array(shared.codes(np.arange(len(ids))), dtype=np.float64, order="C", copy=True)
    build_seconds = time.perf_counter() - start
    times, fingerprints = [], []
    for _ in range(args.repeats):
        start = time.perf_counter()
        if args.method == "cosine":
            result = decode_ref.decode(queries, candidates)
            seconds = time.perf_counter() - start
            rows, best, margins = result.token_ids, result.scores, result.margins
            assert result.token_bytes == [sub.row(int(i)) for i in query_rows]
        else:
            rows, best, margins = dense_distance_baseline(queries, candidates)
            seconds = time.perf_counter() - start
        assert np.array_equal(rows, query_rows)
        assert np.array_equal(ids[rows], ids[query_rows])
        assert [sub.row(int(i)) for i in rows] == [sub.row(int(i)) for i in query_rows]
        assert (margins > 0).all()
        fingerprint = hashlib.sha256()
        for value in (ids[rows].astype("<i8"), best.astype("<f8"), margins.astype("<f8")):
            fingerprint.update(value.tobytes())
        fingerprints.append(fingerprint.hexdigest())
        times.append(seconds)
    assert len(set(fingerprints)) == 1
    _, traced_peak = tracemalloc.get_traced_memory()
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "method": args.method,
        "P": args.capacity,
        "candidates": len(ids),
        "queries": len(queries),
        "source_table_sha256": raw.sha256(),
        "query_token_ids": ids[query_rows].tolist(),
        "query_vectors_sha256": hashlib.sha256(queries.astype("<f8").tobytes()).hexdigest(),
        "candidate_ids_sha256": hashlib.sha256(ids.astype("<i8").tobytes()).hexdigest(),
        "build_seconds": build_seconds,
        "decode_seconds": times,
        "median_decode_seconds": float(np.median(times)),
        "peak_process_rss_bytes": rss if platform.system() == "Darwin" else rss * 1024,
        "python_numpy_traced_peak_bytes": traced_peak,
        "ids_and_stored_bytes_match": True,
        "repeat_fingerprints_match": True,
        "score_fingerprint": fingerprints[0],
        "metric": "cosine similarity" if args.method == "cosine" else "squared Euclidean distance",
    }


def main(argv=None):
    """Run fresh-process cases and write the KE1 CPU comparison JSON.

    Parameters
    ----------
    argv : sequence[str] or None
        CLI arguments without program name; None reads sys.argv. Required:
        --tables and --out. Defaults: 2,048 candidates, 16 queries, 3 repeats,
        P=32/64, seed=20261027, query-seed=10. --full-cosine adds full-vocabulary
        cosine cases; no full-vocabulary dense case is implicitly attempted.

    Returns
    -------
    int
        Zero on success. Invalid inputs and failed worker checks raise errors.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--candidates", type=int, default=2048)
    parser.add_argument("--queries", type=int, default=16)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--pos-dims", type=int, nargs="+", default=[32, 64])
    parser.add_argument("--seed", type=int, default=20261027)
    parser.add_argument("--query-seed", type=int, default=10)
    parser.add_argument("--full-cosine", action="store_true")
    parser.add_argument("--expected-tokenizer-sha256", default=TOKENIZER_SHA256)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--method", choices=["cosine", "dense_euclidean"], help=argparse.SUPPRESS)
    parser.add_argument("--capacity", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        print(json.dumps(worker(args)))
        return 0
    threads = dict.fromkeys(
        ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"), "1"
    )
    env = dict(os.environ, **threads, PYTHONDONTWRITEBYTECODE="1")
    report = {
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "device": "cpu",
            "dtype": "float64",
            "thread_environment": threads,
        },
        "source_sha256": {
            "benchmark_ke1_decode_ref.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "decode_ref.py": hashlib.sha256(Path(decode_ref.__file__).read_bytes()).hexdigest(),
            "ke2/codec.py": hashlib.sha256((Path(__file__).parent / "ke2/codec.py").read_bytes()).hexdigest(),
        },
        "tokenizer_sha256": args.expected_tokenizer_sha256,
        "seed": args.seed,
        "query_seed": args.query_seed,
        "scope": "CPU exact-code microbenchmark; metrics/margin units differ; no GPU or model-throughput claim",
        "timing_scope": "decode only, with allocation tracing; build timed separately; imports/encoding excluded",
        "memory_scope": "RSS includes imports/setup; traced allocations differ; shared query-generation table retained in both cases",
        "measurements": [],
    }
    for capacity in args.pos_dims:
        cases = [("cosine", args.candidates), ("dense_euclidean", args.candidates)]
        if args.full_cosine:
            table = ByteTable.load(
                args.tables / f"raw_table_P{capacity}.npz", tokenizer_sha256=args.expected_tokenizer_sha256
            )
            cases.append(("cosine", table.vocab_size))
        for method, count in cases:
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                "--tables",
                str(args.tables.resolve()),
                "--out",
                str(args.out.resolve()),
                "--method",
                method,
                "--capacity",
                str(capacity),
                "--candidates",
                str(count),
                "--queries",
                str(args.queries),
                "--repeats",
                str(args.repeats),
                "--seed",
                str(args.seed),
                "--query-seed",
                str(args.query_seed),
                "--expected-tokenizer-sha256",
                args.expected_tokenizer_sha256,
            ]
            result = subprocess.run(command, env=env, capture_output=True, text=True, check=True)
            measurement = json.loads(result.stdout)
            report["measurements"].append(measurement)
            print(f"Measured {method}, P={capacity}, candidates={count}", flush=True)
        a, b = report["measurements"][-len(cases) :][:2]
        assert a["candidate_ids_sha256"] == b["candidate_ids_sha256"]
        assert a["query_vectors_sha256"] == b["query_vectors_sha256"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
