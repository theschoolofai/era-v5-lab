#!/usr/bin/env python3
"""Build the KE2 decode and raw byte tables for BrahmicTokenizer-131K.

* **decode** table: upstream behaviour (``decode([id])`` then UTF-8). Tokens holding part of a
  character become U+FFFD and share one code. Kept as the baseline.
* **raw** table: the fix. Exact token bytes from the inverted GPT-2 ByteLevel alphabet.

Both are built for every P (default 32 and 64) and saved as compressed ``.npz`` (``bytes`` uint8
``(V, P)``, ``lengths`` int16 ``(V,)``) with a ``manifest.json`` of SHA-256 fingerprints.
The logic lives in the ``ke2`` package; this file is the command line and keeps the names other
code imports from it.

Usage
-----
    python build_tables.py [--tokenizer PATH_OR_HF_ID] [--out DIR] [--pos-dims 32 64] [--allow-download]

Without ``--tokenizer`` the tokenizer is found via ``$KE2_TOKENIZER``, ``$BRAHMIC_TOKENIZER_DIR``,
then the Hugging Face cache at the pinned revision.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

if __package__ in (None, ""):  # run as a script: make the ke2 package importable
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from ke2.codec import encode_ids as ke2_encode
from ke2.codec import output_dim as ke2_output_dim
from ke2.codec import read_support
from ke2.config import CHAR_DIM, HF_ID, POS_DIMS, TABLES_DIR
from ke2.hashing import sha256_file
from ke2.script_class import classify_vocab, script_class
from ke2.tables import (
    TABLE_FORMAT_VERSION,
    ByteTable,
    TableContractError,
    build_all,
    build_decode_table,
    build_raw_table,
    load_table,
    table_path,
)
from ke2.tokenizer import (
    BYTE_TO_UNI,
    U_FFFD,
    UNI_TO_BYTE,
    TokenizerBundle,
    VocabHoleError,
    decode_bytes_for_id,
    gpt2_bytes_to_unicode,
    load_tokenizer,
    piece_to_raw_bytes,
    raw_bytes_for_id,
    resolve_tokenizer_path,
)
from ke2.truncation import continuation_truncate as utf8_safe_truncate

__all__ = [
    "BYTE_TO_UNI",
    "CHAR_DIM",
    "HF_ID",
    "POS_DIMS",
    "TABLE_FORMAT_VERSION",
    "UNI_TO_BYTE",
    "U_FFFD",
    "ByteTable",
    "TableContractError",
    "TokenizerBundle",
    "VocabHoleError",
    "build_all",
    "build_decode_table",
    "build_raw_table",
    "classify_vocab",
    "decode_bytes_for_id",
    "gpt2_bytes_to_unicode",
    "ke2_decode_vector",
    "ke2_encode",
    "ke2_output_dim",
    "load_table",
    "load_tokenizer",
    "main",
    "piece_to_raw_bytes",
    "raw_bytes_for_id",
    "resolve_tokenizer_path",
    "script_class",
    "sha256_file",
    "table_path",
    "utf8_safe_truncate",
]  # fmt: skip


def ke2_decode_vector(vec, pos_dim: int, char_dim: int = CHAR_DIM) -> bytes:
    """Recover the bytes from one KE2 vector (Lemma 1). Kept for callers of the original script."""
    if len(vec) != char_dim * pos_dim:
        raise ValueError(f"expected D={char_dim * pos_dim}, got {len(vec)}")
    return read_support(vec, pos_dim)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer", default=None, help="path to tokenizer.json or its folder, or an HF id")
    ap.add_argument("--out", type=Path, default=TABLES_DIR, help="output directory for the .npz tables")
    ap.add_argument("--pos-dims", type=int, nargs="+", default=list(POS_DIMS))
    ap.add_argument("--allow-download", action="store_true", help="fetch the tokenizer from the HF Hub if needed")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    tb = load_tokenizer(a.tokenizer, allow_download=a.allow_download)
    logging.info("tokenizer: %s (V=%d, sha256=%s…)", tb.path.name, tb.vocab_size, tb.sha256[:12])
    build_all(tb, a.out, a.pos_dims)
    return 0


if __name__ == "__main__":
    sys.exit(main())
