"""CPU float64 reference: KE code vectors -> token IDs, original bytes and margins.

Matching contract (proposed for G6): minimize squared Euclidean distance.
Margin = second-best squared distance - best squared distance. Exact ties use
the smallest token ID. This decodes forward-codec vectors, not tokenizer text
or projected model hidden states. NumPy is the only runtime dependency.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass

import numpy as np


def _cpu_float64(value):
    """Validate and copy a real CPU matrix into contiguous float64 storage.

    Parameters
    ----------
    value : array-like, shape (N, D)
        Real, finite vectors convertible to a NumPy array. CPU tensor inputs
        must support NumPy conversion; accelerator tensors are rejected.

    Returns
    -------
    numpy.ndarray, shape (N, D), dtype float64
        A C-contiguous copy owned by the caller. An empty batch is permitted.

    Raises
    ------
    ValueError
        If the input is on an accelerator, complex, nonfinite or not 2D.
    TypeError
        If its values cannot be converted to float64.
    """
    if getattr(getattr(value, "device", None), "type", "cpu") != "cpu":
        raise ValueError("Reference inputs must be on CPU")
    if np.iscomplexobj(value):
        raise ValueError("Reference inputs must be real-valued")
    array = np.array(value, dtype=np.float64, order="C", copy=True)
    if array.ndim != 2 or not np.isfinite(array).all():
        raise ValueError("Expected a finite 2D batch of vectors")
    return array


class CodeTable:
    """One forward-codec vector, unique token ID and raw bytes per candidate.

    Raw bytes are supplied explicitly and may contain incomplete UTF-8. They
    are returned unchanged, never reconstructed through text decoding.
    Duplicate code vectors are permitted and produce zero-margin ties.
    """

    def __init__(self, codes, raw_bytes, token_ids=None):
        """Copy and validate a candidate vocabulary code table.

        Parameters
        ----------
        codes : array-like, shape (V, D)
            Real, finite CPU code vectors, with V >= 2 and D >= 1. These are
            copied to float64 and must share the query vectors' representation.
        raw_bytes : iterable of bytes, length V
            Original byte payload for each row, preserved without text decoding.
            Empty byte strings, NULs and incomplete UTF-8 fragments are allowed.
        token_ids : array-like of integers, shape (V,), optional
            Unique nonnegative IDs representable as int64. Omit to use row
            indices 0 through V-1. Use explicit IDs for reordered vocabularies.

        Returns
        -------
        None
            Initializes read-only code/ID arrays and an immutable byte tuple.

        Raises
        ------
        ValueError
            If matrix, ID or byte-payload validation fails.
        TypeError
            If codes cannot be converted to float64 or raw_bytes is not iterable.
        """
        self.codes = _cpu_float64(codes)
        n, width = self.codes.shape
        if n < 2 or width == 0:
            raise ValueError("At least two candidate codes of positive width are required")
        supplied = np.arange(n, dtype=np.int64) if token_ids is None else np.asarray(token_ids)
        if supplied.shape != (n,) or supplied.dtype.kind not in "iu":
            raise ValueError("token_ids must contain one integer per code")
        if (supplied < 0).any() or (supplied > np.iinfo(np.int64).max).any():
            raise ValueError("Token IDs must fit nonnegative int64")
        self.token_ids = supplied.astype(np.int64, copy=True)
        if len(np.unique(self.token_ids)) != n:
            raise ValueError("Token IDs must be unique")
        self.raw_bytes = tuple(raw_bytes)
        if len(self.raw_bytes) != n or any(not isinstance(b, bytes) for b in self.raw_bytes):
            raise ValueError("raw_bytes must contain one bytes object per code")
        self.codes.setflags(write=False)
        self.token_ids.setflags(write=False)

    @classmethod
    def from_codec(cls, codec, raw_bytes, token_ids=None):
        """Build candidates with the same forward codec used for query vectors.

        For KE2 this calls codec.encode(), not a model-head table helper.
        The supplied codec is external; this module contains no KE2 source.

        Parameters
        ----------
        codec : object with encode(sequences)
            External encoder returning a CPU matrix of shape (V, D). Use this
            same configuration and representation to produce the query vectors.
        raw_bytes : iterable of bytes, length V
            Candidate token bytes, materialized once and passed to the encoder.
        token_ids : array-like of integers, shape (V,), optional
            Original token IDs; omitted IDs default to row indices.

        Returns
        -------
        CodeTable
            Validated table containing the generated vectors and byte payloads.

        Raises
        ------
        ValueError
            If the resulting table fails CodeTable validation. Exceptions from
            the external encoder propagate without being suppressed.
        """
        raw_bytes = tuple(raw_bytes)
        return cls(codec.encode(raw_bytes), raw_bytes, token_ids)


@dataclass(frozen=True)
class DecodeResult:
    """One decoded query and its confidence information.

    Attributes
    ----------
    token_id : int
        Winning candidate ID; the smallest ID wins an exact distance tie.
    raw_bytes : bytes
        Original payload stored for the winning candidate, returned unchanged.
    best_distance : float
        Squared Euclidean distance to the winning candidate, computed in float64.
    second_distance : float
        Squared distance to the runner-up, which may equal the best distance.
    margin : float
        second_distance - best_distance. A zero gap exposes an ambiguous match;
        it is not a calibrated probability or an out-of-vocabulary threshold.
    """
    token_id: int
    raw_bytes: bytes
    best_distance: float
    second_distance: float
    margin: float


def decode_ref(vectors, code_table: CodeTable, *, chunk_size=256):
    """Exhaustive nearest-code search, preserving input batch order.

    Distances are summed directly from squared float64 differences. No BLAS,
    approximate search, GPU operation, text decoding or random choice is used.
    Candidate chunks bound temporary memory; they do not change score arithmetic.

    Parameters
    ----------
    vectors : array-like, shape (B, D)
        Real, finite CPU query code vectors. Converted to float64 before scoring;
        conversion cannot recover precision previously lost in lower precision.
    code_table : CodeTable
        At least two candidate rows in the same code representation as vectors.
        Distances and margins are relative to this supplied candidate set only.
    chunk_size : int, optional
        Positive number of candidate rows processed at once, default 256. Bounds
        temporary difference arrays, not the size of the stored dense code table.

    Returns
    -------
    list of DecodeResult, length B
        Best ID, original bytes, both squared distances and their gap for each
        query in input order. An empty query batch returns an empty list.

    Raises
    ------
    ValueError
        If query validation fails, widths differ or chunk_size is invalid.
    FloatingPointError
        If float64 distance arithmetic overflows or becomes invalid.
    """
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    queries = _cpu_float64(vectors)
    if queries.shape[1] != code_table.codes.shape[1]:
        raise ValueError("Query width does not match the code table")
    results = []
    for query in queries:
        distances = np.empty(len(code_table.codes), dtype=np.float64)
        with np.errstate(over="raise", invalid="raise"):
            for start in range(0, len(distances), chunk_size):
                stop = min(start + chunk_size, len(distances))
                delta = code_table.codes[start:stop] - query
                distances[start:stop] = np.einsum("ij,ij->i", delta, delta, optimize=False)
                # einsum reductions can overflow without honoring np.errstate.
                if not np.isfinite(distances[start:stop]).all():
                    raise FloatingPointError("Squared distances exceed finite float64 range")
        # lexsort's last key is primary: distance, then ascending token ID.
        first, second = np.lexsort((code_table.token_ids, distances))[:2]
        best, runner_up = float(distances[first]), float(distances[second])
        results.append(DecodeResult(int(code_table.token_ids[first]), code_table.raw_bytes[first],
                                    best, runner_up, runner_up - best))
    return results


def results_sha256(results):
    """Hash ordered IDs, raw bytes, both distances and margins without ambiguity.

    Parameters
    ----------
    results : iterable of DecodeResult
        Records in query order, usually returned by decode_ref. IDs, byte lengths
        and float values must fit the documented binary serialization format.

    Returns
    -------
    str
        A 64-character lowercase SHA-256 hex digest. A versioned header and
        explicit byte lengths distinguish record boundaries and empty payloads.

    Raises
    ------
    struct.error
        If a supplied record contains values outside the serialization ranges.
    """
    digest = hashlib.sha256(b"ke2-reference-decode-v1\n")
    for result in results:
        digest.update(struct.pack(">qdddQ", result.token_id, result.best_distance,
                                  result.second_distance, result.margin, len(result.raw_bytes)))
        digest.update(result.raw_bytes)
    return digest.hexdigest()
