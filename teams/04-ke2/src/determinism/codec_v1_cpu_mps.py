#!/usr/bin/env python3
"""Check the original week-1 codec on CPU and MPS, with numerical comparisons.

Imports the public kronecker-embeddings package. Three fresh processes hash CPU
and MPS forward outputs at P=32/64 and compare their values. Requires MPS; CPU
is the comparison baseline, so this is not a standalone CPU-only command.
Uses float32 and excludes learned projection and backward computation.

Results: codec_v1_cpu_mps_results.json and codec_v1_cpu_mps_sha256.txt. Historical
results retained under these names were renamed without changing their contents.
Tokenizer decoding is checked independently by tokenizer_decode_cpu.py.
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

if __package__ in (None, ""):  # run as a script: make the ke2 package importable
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ke2.config import TEAM_DIR
from ke2.config import TOKENIZER_SHA256 as TOKENIZER_SHA
from ke2.tables import TABLE_FORMAT_VERSION, table_content_sha256

HASH_FORMAT = "ke2-codec-float32-v1"


def read_table(path, P, tokenizer_sha):
    import numpy as np

    with np.load(path, allow_pickle=False) as z:
        if int(z["format_version"]) != TABLE_FORMAT_VERSION or str(z["kind"]) != "raw" or int(z["pos_dim"]) != P:
            raise ValueError(f"Expected a v{TABLE_FORMAT_VERSION} raw byte table with matching P")
        if str(z["tokenizer_sha256"]) != tokenizer_sha:
            raise ValueError("Table belongs to a different tokenizer")
        buf, lengths = z["bytes"], z["lengths"]
        if buf.dtype != np.uint8 or lengths.dtype != np.int16:
            raise ValueError("Unexpected table dtypes")
        if buf.ndim != 2 or buf.shape[1] != P or lengths.shape != (buf.shape[0],):
            raise ValueError("Invalid byte/length shapes")
        if not len(lengths) or (lengths < 0).any() or (lengths > P).any():
            raise ValueError("Invalid table lengths")
        digest = table_content_sha256("raw", P, buf, lengths)
        if digest != str(z["table_sha256"]):
            raise ValueError("Table content hash mismatch")
        return buf, lengths, digest


def output_digest(P, count):
    # Identical headers on CPU and MPS permit a direct bitwise comparison.
    header = {
        "format": HASH_FORMAT,
        "P": P,
        "rows": count,
        "columns": 256 * P,
        "dtype": "little-endian float32",
        "order": "ascending token ID, row-major",
    }
    return hashlib.sha256((json.dumps(header, sort_keys=True) + "\n").encode())


def summarize(runs):
    if len(runs) != 3:
        raise ValueError("Exactly three fresh processes are required")
    if any(r["environment"] != runs[0]["environment"] for r in runs[1:]):
        raise ValueError("Environment or codec source changed between processes")
    summary = {}
    for P in (32, 64):
        entries = [r["tables"][str(P)] for r in runs]
        identity = ("table_sha256", "rows", "vocabulary_size", "first_id", "last_id", "batch_size")
        if any(any(e[k] != entries[0][k] for k in identity) for e in entries[1:]):
            raise ValueError("Input table or coverage changed between processes")
        summary[str(P)] = {
            "rows_per_run": entries[0]["rows"],
            "full_vocabulary": entries[0]["rows"] == entries[0]["vocabulary_size"],
            "mps_three_hashes_match": len({e["mps_sha256"] for e in entries}) == 1,
            "cpu_three_hashes_match": len({e["cpu_sha256"] for e in entries}) == 1,
            "cpu_mps_bitwise_equal": all(e["mps_sha256"] == e["cpu_sha256"] for e in entries),
            "cpu_mps_all_close": all(e["values_outside_tolerance"] == 0 for e in entries),
            "max_absolute_difference": max(e["max_absolute_difference"] for e in entries),
            "strict_probe_statuses": [e["strict_probe"]["status"] for e in entries],
        }
    return summary


def measure(args):
    import numpy as np
    import torch

    if os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") != "0":
        raise RuntimeError("Run through the parent with CPU fallback disabled")
    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS is unavailable; this experiment cannot run on CPU")
    source = args.codec_src.resolve()
    sys.path.insert(0, str(source))
    import kronecker_embeddings.codec as codec

    codec_file = Path(codec.__file__).resolve()
    if codec_file.parent != source / "kronecker_embeddings":
        raise RuntimeError("Imported codec does not match --codec-src")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(False)
    result = {
        "environment": {
            "torch_version": torch.__version__,
            "numpy_version": np.__version__,
            "python_version": platform.python_version(),
            "macos_version": platform.mac_ver()[0],
            "machine": platform.machine(),
            "device": "mps",
            "dtype": "float32",
            "cpu_threads": 1,
            "cpu_fallback": False,
            "mps_fast_math": False,
            "tokenizer_sha256": args.expected_tokenizer_sha256,
            "codec_source_sha256": hashlib.sha256(codec_file.read_bytes()).hexdigest(),
        },
        "tables": {},
    }
    with torch.inference_mode():
        for P in (32, 64):
            buf, lengths, table_sha = read_table(args.tables / f"raw_table_P{P}.npz", P, args.expected_tokenizer_sha256)
            count = min(args.limit, len(lengths)) if args.limit is not None else len(lengths)
            cpu_hash, mps_hash = output_digest(P, count), output_digest(P, count)
            max_error = 0.0
            differing_values = outside_tolerance = differing_rows = 0
            for start in range(0, count, args.batch_size):
                end = min(start + args.batch_size, count)
                b = torch.from_numpy(buf[start:end])
                n = torch.from_numpy(lengths[start:end].astype(np.int64))
                reference = codec.kronecker_codec(b, n, pos_dim=P)
                output = codec.kronecker_codec(b.to("mps"), n.to("mps"), pos_dim=P)
                if output.device.type != "mps":
                    raise RuntimeError("Codec output is not on MPS")
                torch.mps.synchronize()
                observed = output.cpu().contiguous()
                if not torch.isfinite(observed).all() or not torch.isfinite(reference).all():
                    raise RuntimeError("Nonfinite codec output")
                cpu_array = reference.numpy().astype("<f4", copy=False)
                mps_array = observed.numpy().astype("<f4", copy=False)
                cpu_hash.update(cpu_array.tobytes())
                mps_hash.update(mps_array.tobytes())
                unequal = cpu_array.view("<u4") != mps_array.view("<u4")
                differing_values += int(unequal.sum())
                differing_rows += int(unequal.any(axis=1).sum())
                outside_tolerance += int((~torch.isclose(observed, reference, rtol=args.rtol, atol=args.atol)).sum())
                max_error = max(max_error, float((observed - reference).abs().max()))
                del output, observed, reference
            # This probes strict mode, separately from the ordinary-mode full run.
            torch.use_deterministic_algorithms(True)
            try:
                probe_n = min(8, count)
                probe = codec.kronecker_codec(
                    torch.from_numpy(buf[:probe_n]).to("mps"),
                    torch.from_numpy(lengths[:probe_n].astype(np.int64)).to("mps"),
                    pos_dim=P,
                )
                torch.mps.synchronize()
                strict = {"status": "accepted_for_probe", "rows": probe_n}
                del probe
            except RuntimeError as error:
                message = str(error)
                if "deterministic implementation" not in message:
                    raise
                strict = {"status": "rejected_no_deterministic_implementation", "rows": probe_n, "error": message}
            finally:
                torch.use_deterministic_algorithms(False)
            result["tables"][str(P)] = {
                "table_sha256": table_sha,
                "vocabulary_size": len(lengths),
                "rows": count,
                "first_id": 0,
                "last_id": count - 1,
                "batch_size": args.batch_size,
                "cpu_sha256": cpu_hash.hexdigest(),
                "mps_sha256": mps_hash.hexdigest(),
                "bitwise_different_values": differing_values,
                "bitwise_different_rows": differing_rows,
                "max_absolute_difference": max_error,
                "values_outside_tolerance": outside_tolerance,
                "strict_probe": strict,
            }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", required=True, type=Path, help="directory containing Swati's v2 raw .npz tables")
    parser.add_argument("--codec-src", required=True, type=Path, help="kronecker-embeddings/src directory")
    parser.add_argument("--expected-tokenizer-sha256", default=TOKENIZER_SHA)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--rtol", type=float, default=1e-5)
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--limit", type=int, help="optional smoke-test row limit; omit for full coverage")
    parser.add_argument("--out", type=Path, default=TEAM_DIR / "results")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.batch_size <= 0 or (args.limit is not None and args.limit <= 0) or args.rtol < 0 or args.atol < 0:
        parser.error("batch size and limit must be positive; tolerances must be nonnegative")
    if args.worker:
        print(json.dumps(measure(args), sort_keys=True))
        return 0
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--tables",
        str(args.tables.resolve()),
        "--codec-src",
        str(args.codec_src.resolve()),
        "--expected-tokenizer-sha256",
        args.expected_tokenizer_sha256,
        "--batch-size",
        str(args.batch_size),
        "--rtol",
        str(args.rtol),
        "--atol",
        str(args.atol),
    ]
    if args.limit is not None:
        command += ["--limit", str(args.limit)]
    env = dict(os.environ, PYTORCH_ENABLE_MPS_FALLBACK="0", PYTORCH_MPS_FAST_MATH="0", PYTHONDONTWRITEBYTECODE="1")
    runs = []
    for index in range(3):
        process = subprocess.run(command, env=env, capture_output=True, text=True)
        if process.returncode:
            raise RuntimeError(f"MPS process {index + 1} failed: {process.stderr.strip()}")
        runs.append(json.loads(process.stdout))
        print(f"Completed fresh MPS process {index + 1}/3", flush=True)
    summary = summarize(runs)
    report = {
        "hash_format": HASH_FORMAT,
        "hash_serialization": "sorted JSON header plus LF; then all output values as row-major little-endian float32",
        "scope": "raw-table forward codec, three fresh processes, fixed ascending order and batch size; no learned projection",
        "measurement_mode": "strict deterministic algorithms disabled; CPU fallback and MPS fast math disabled",
        "comparison": {"rtol": args.rtol, "atol": args.atol},
        "summary": summary,
        "runs": runs,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "codec_v1_cpu_mps_results.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# P run MPS_SHA256 CPU_SHA256\n"]
    for P in (32, 64):
        for index, run in enumerate(runs, 1):
            entry = run["tables"][str(P)]
            lines.append(f"{P} {index} {entry['mps_sha256']} {entry['cpu_sha256']}\n")
    (args.out / "codec_v1_cpu_mps_sha256.txt").write_text("".join(lines))
    print(json.dumps(summary, indent=2))
    return (
        0
        if all(
            s["mps_three_hashes_match"] and s["cpu_three_hashes_match"] and s["cpu_mps_all_close"]
            for s in summary.values()
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
