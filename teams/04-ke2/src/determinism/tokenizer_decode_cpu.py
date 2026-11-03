#!/usr/bin/env python3
"""Check tokenizer decoding repeatability in three fresh CPU processes.

Input: a tokenizer.json artifact. Output: hashes of every token ID's decoded
UTF-8 text. Calls the tokenizer's decode([id]) API independently of embedding
implementations. Reuse this check for the same artifact; rerun against its new
expected SHA-256 whenever the tokenizer changes.

A pass establishes tokenizer repeatability, not vector encoding, raw-byte
preservation or vector-to-token-ID recovery. Results are written to
tokenizer_decode_cpu_metadata.json and tokenizer_decode_cpu_sha256.txt.
The v1 suffix in HASH_FORMAT identifies the hash serialization version.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import struct
import subprocess
import sys
from pathlib import Path

HASH_FORMAT = "ke2-decode-cpu-v1"
TEAM_DIR = Path(__file__).resolve().parents[2]


def hash_rows(rows):
    """Hash ordered (token ID, decoded UTF-8 bytes), with explicit framing."""
    digest = hashlib.sha256((HASH_FORMAT + "\n").encode("ascii"))
    for token_id, payload in rows:
        digest.update(struct.pack(">II", token_id, len(payload)))
        digest.update(payload)
    return digest.hexdigest()


def check_ids(vocab):
    ids = sorted(vocab.values())
    if not ids or ids != list(range(len(ids))):
        raise ValueError("Vocabulary IDs must be unique and contiguous from zero")
    return ids


def decoded_rows(tokenizer, ids, special_literals):
    """Exercise the real decoder for every ID, including special tokens."""
    for token_id in ids:
        text = tokenizer.decode([token_id], skip_special_tokens=False)
        payload = text.encode("utf-8")
        # Swati's decode table uses literal UTF-8 for special tokens. Require
        # the actual decoder to agree, rather than silently bypassing decoding.
        if token_id in special_literals and payload != special_literals[token_id]:
            raise ValueError(f"Decoder disagrees with literal special token {token_id}")
        yield token_id, payload


def decode_once(path, expected_sha256=None):
    import tokenizers

    original = path.read_bytes()
    tokenizer_sha256 = hashlib.sha256(original).hexdigest()
    if expected_sha256 and tokenizer_sha256 != expected_sha256:
        raise ValueError("Tokenizer SHA-256 differs from the expected artifact")
    config = json.loads(original)
    tokenizer = tokenizers.Tokenizer.from_str(original.decode("utf-8"))
    ids = check_ids(tokenizer.get_vocab(with_added_tokens=True))
    specials = {
        entry["id"]: entry["content"].encode("utf-8")
        for entry in config.get("added_tokens", [])
        if entry.get("special", False)
    }
    digest = hash_rows(decoded_rows(tokenizer, ids, specials))
    return {
        "sha256": digest,
        "tokenizer_sha256": tokenizer_sha256,
        "token_count": len(ids),
        "first_id": ids[0],
        "last_id": ids[-1],
        "special_token_count": len(specials),
        "tokenizers_version": tokenizers.__version__,
        "python_version": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        "device": "cpu",
    }


def verify_runs(runs):
    if len(runs) != 3:
        raise ValueError("Exactly three decoding runs are required")
    if any(run != runs[0] for run in runs[1:]):
        raise ValueError("The three decoding runs disagree; determinism check failed")


def run_three(path, expected_sha256=None):
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--tokenizer", str(path)]
    if expected_sha256:
        command += ["--expected-sha256", expected_sha256]
    environment = dict(os.environ, TOKENIZERS_PARALLELISM="false")
    runs = []
    for index in range(3):
        result = subprocess.run(command, capture_output=True, text=True, env=environment)
        if result.returncode:
            raise RuntimeError(f"CPU run {index + 1} failed: {result.stderr.strip()}")
        runs.append(json.loads(result.stdout))
    verify_runs(runs)
    return runs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tokenizer", required=True, type=Path, help="local tokenizer.json; never downloaded implicitly"
    )
    parser.add_argument("--expected-sha256", help="require this exact tokenizer artifact")
    parser.add_argument("--out", type=Path, default=TEAM_DIR / "results")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    path = args.tokenizer.resolve()
    if args.worker:
        print(json.dumps(decode_once(path, args.expected_sha256), sort_keys=True))
        return 0
    runs = run_three(path, args.expected_sha256)
    report = {
        "hash_format": HASH_FORMAT,
        "serialization": "ASCII format name plus LF; then ascending IDs as uint32 big-endian, UTF-8 byte lengths as uint32 big-endian, then bytes",
        "decoder": "tokenizers.Tokenizer.decode([id], skip_special_tokens=False)",
        "special_token_policy": "decode every ID; require specials to equal literal content, matching the reviewed table builder",
        "process_policy": "three fresh sequential CPU processes; TOKENIZERS_PARALLELISM=false",
        "all_match": True,
        "runs": runs,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "tokenizer_decode_cpu_sha256.txt").write_text("".join(run["sha256"] + "\n" for run in runs), encoding="ascii")
    (args.out / "tokenizer_decode_cpu_metadata.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {runs[0]['token_count']} token IDs decoded in each of three fresh CPU processes")
    print(runs[0]["sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
