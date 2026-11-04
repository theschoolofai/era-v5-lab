#!/usr/bin/env python3
"""KE1 CPU float64 reference decoder: code vectors -> token ID, raw bytes and decode margin.

G6 uses this to check fast decoders against unprojected KE1 forward-codec vectors.
Queries and table rows must use the same codec settings. This is exhaustive cosine matching:

* Runs on CPU in float64. Results are deterministic: the same input always gives the same output
  and the same :meth:`DecodeResult.sha256` in the tested environment, including across query
  chunk sizes and a fresh process. Cross-platform bitwise equality is not asserted.
* Exhaustive: every vector is scored against the code of **every** token in the code table by
  cosine similarity. The best match gives the token ID and its raw bytes. The margin is the gap
  between the best and the second-best cosine. A margin of 0 means a tie (two tokens share a code,
  for example the U+FFFD rows of the decode table); ties go to the lowest token ID.

How a score is computed
-----------------------
Every code is two-valued (Lemma 1): ``z_t = low(L_t) + (high(L_t) - low(L_t)) * 1[support of t]``,
where the support is the L_t cells ``b_p * P + p``. So for a query q

    q . z_t = low(L_t) * sum(q) + (high(L_t) - low(L_t)) * sum_{p < L_t} q[b_p * P + p]

which needs one gather of L_t values per token instead of a dense V x D product (8.6 GB at P=32 in
float64). Sums run in a fixed order with numpy reductions, never BLAS, so results are bitwise
stable within the tested environment. ``CodeTable.codes`` materializes dense codes only for
checks on small subsets. Raw tables return original byte payloads; decode-text tables return
their stored, possibly lossy UTF-8 text bytes. See ``../decode_ref.md`` for scope and measurements.

Usage
-----
    python src/decode_ref.py --table results/tables/raw_table_P32.npz --vectors codes.npy [--out decoded.jsonl]

``codes.npy`` holds an ``(N, 256 * P)`` float array. The command prints the result hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # run as a script: make the ke2 package importable
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from ke2.codec import code_values, encode_f64
from ke2.config import CHAR_DIM, TOKENIZER_SHA256
from ke2.tables import ByteTable

log = logging.getLogger("decode_ref")

HASH_FORMAT = "ke2-decode-ref-v1"
DEFAULT_BUDGET_BYTES = 256 * 1024**2
"""Approximate scoring-temporary budget; not a cap on total process or input memory."""


class DecodeInputError(ValueError):
    """The vectors cannot be decoded against this code table."""


@dataclass(frozen=True)
class CodeTable:
    """The KE code of every token, defined by a byte table and the codec settings.

    Codes are not stored densely; each token is its support cells plus per-length code values.
    """

    kind: str
    pos_dim: int
    char_dim: int
    byte_rows: np.ndarray  # uint8 (V, P)
    lengths: np.ndarray  # int64 (V,)
    high: np.ndarray  # float64 (V,): code value on the support
    low: np.ndarray  # float64 (V,): code value elsewhere
    norms: np.ndarray  # float64 (V,): Euclidean norm of each code
    support: np.ndarray  # int64 (sum L,): support cells, token by token, position order
    offsets: np.ndarray  # int64 (V,): start of each token's cells in ``support``
    table_sha256: str
    length_normalize: bool = True
    z_normalize: bool = True
    eps: float = 1e-6

    @classmethod
    def from_byte_table(
        cls,
        table: ByteTable,
        *,
        char_dim: int = CHAR_DIM,
        length_normalize: bool = True,
        z_normalize: bool = True,
        eps: float = 1e-6,
    ) -> CodeTable:
        """Build structured candidates with the public KE1 codec's defaults.

        Parameters
        ----------
        table : ByteTable
            Verified byte rows, lengths and capacity P. Row indices are token IDs.
            The table's arrays must remain unchanged while decoding.
        char_dim : int
            Byte alphabet size, normally 256; must match the forward encoder.
        length_normalize, z_normalize : bool
            Forward-codec normalization settings; must match the query encoder.
        eps : float
            KE1 standard-deviation stabilizer; must match the query encoder.

        Returns
        -------
        CodeTable
            Sparse support cells, per-length values and float64 code norms.
        """
        P = table.pos_dim
        if table.vocab_size < 2:
            raise ValueError("a code table needs at least two tokens to define a margin")
        lengths = table.lengths.astype(np.int64)
        high, low = code_values(
            lengths, P, char_dim=char_dim, length_normalize=length_normalize, z_normalize=z_normalize, eps=eps
        )
        D = char_dim * P
        norms = np.sqrt(lengths * high**2 + (D - lengths) * low**2)
        rows, cols = np.nonzero(np.arange(P)[None, :] < lengths[:, None])  # row-major: token, then position
        support = table.bytes[rows, cols].astype(np.int64) * P + cols
        offsets = np.concatenate(([0], np.cumsum(lengths)[:-1])).astype(np.int64)
        return cls(
            kind=table.kind,
            pos_dim=P,
            char_dim=char_dim,
            byte_rows=table.bytes,
            lengths=lengths,
            high=high,
            low=low,
            norms=norms,
            support=support,
            offsets=offsets,
            table_sha256=table.sha256(),
            length_normalize=length_normalize,
            z_normalize=z_normalize,
            eps=eps,
        )

    @property
    def vocab_size(self) -> int:
        """Number of candidates V; IDs are row indices 0 through V-1."""
        return int(self.lengths.shape[0])

    @property
    def dim(self) -> int:
        """Required query width D = char_dim * pos_dim."""
        return self.char_dim * self.pos_dim

    def token_bytes(self, tid: int) -> bytes:
        """Return the stored unpadded payload for token-row index tid (int)."""
        return self.byte_rows[tid, : int(self.lengths[tid])].tobytes()

    def codes(self, ids: Any) -> np.ndarray:
        """Materialize float64 codes for ids (1D integer array), returning (len(ids), D).

        For small checks only: requesting all IDs allocates a dense V-by-D matrix.
        """
        ids = np.asarray(ids, dtype=np.int64)
        return encode_f64(
            self.byte_rows[ids],
            self.lengths[ids],
            self.pos_dim,
            char_dim=self.char_dim,
            length_normalize=self.length_normalize,
            z_normalize=self.z_normalize,
            eps=self.eps,
        )

    def dot_scores(self, queries: np.ndarray) -> np.ndarray:
        """``queries @ codes.T`` for float64 queries ``(n, D)``, shape ``(n, V)``."""
        totals = queries.sum(axis=1, keepdims=True)  # (n, 1)
        gathered = queries[:, self.support]  # (n, sum L)
        on_support = np.zeros((queries.shape[0], self.vocab_size), dtype=np.float64)
        nonempty = self.lengths > 0
        # reduceat sums each token's cells in order; empty tokens keep 0 (reduceat would not).
        on_support[:, nonempty] = np.add.reduceat(gathered, self.offsets[nonempty], axis=1)
        return self.low * totals + (self.high - self.low) * on_support

    def cosine_scores(self, queries: np.ndarray) -> np.ndarray:
        """Cosine similarity of float64 queries ``(n, D)`` to every code, shape ``(n, V)``.

        The empty token's zero code has no direction and scores 0.
        """
        qnorm = np.sqrt((queries * queries).sum(axis=1, keepdims=True))
        denom = qnorm * self.norms
        dots = self.dot_scores(queries)
        out = np.zeros_like(dots)
        np.divide(dots, denom, out=out, where=denom > 0)
        return out


@dataclass(frozen=True)
class DecodeResult:
    """Decoder output, one entry per input vector."""

    token_ids: np.ndarray  # int64 (N,)
    token_bytes: list[bytes]
    scores: np.ndarray  # float64 (N,): best cosine similarity
    margins: np.ndarray  # float64 (N,): best minus second-best cosine (>= 0)
    pos_dim: int
    table_sha256: str

    def __len__(self) -> int:
        """Return the number of decoded query vectors."""
        return int(self.token_ids.shape[0])

    def sha256(self) -> str:
        """Framed hash: header line, then per row id (u32 BE), length (u16 BE), bytes, score and margin (f64 BE)."""
        h = hashlib.sha256(f"{HASH_FORMAT}|P={self.pos_dim}|table={self.table_sha256}|n={len(self)}\n".encode())
        for tid, raw, score, margin in zip(
            self.token_ids.tolist(), self.token_bytes, self.scores, self.margins, strict=True
        ):
            h.update(struct.pack(">IH", tid, len(raw)))
            h.update(raw)
            h.update(struct.pack(">dd", float(score), float(margin)))
        return h.hexdigest()

    def records(self) -> list[dict]:
        """JSON-ready rows: ``id``, ``bytes_hex``, ``score``, ``margin``."""
        return [
            {"id": int(t), "bytes_hex": b.hex(), "score": float(s), "margin": float(m)}
            for t, b, s, m in zip(self.token_ids, self.token_bytes, self.scores, self.margins, strict=True)
        ]


def sample_token_ids(vocab_size: int, special_ids: Any = (), *, n: int = 4096, seed: int = 0) -> np.ndarray:
    """Return n distinct IDs from vocab_size candidates, with edge cases and seeded sampling.

    Parameters: vocab_size (int) is the candidate count; special_ids is an iterable
    of special-token IDs; n (int) is the requested count; seed (int) controls the
    NumPy permutation. Returns an int64 array of shape (n,).

    Edges: the first and last ID, IDs 77 and 173 (partial-UTF-8 tokens of BrahmicTokenizer-131K that
    share a decode-table row) and up to eight special tokens.
    """
    edges = list(dict.fromkeys(i for i in (0, 77, 173, vocab_size - 1, *sorted(special_ids)[:8]) if i < vocab_size))
    if n > vocab_size:
        raise ValueError(f"cannot draw {n} distinct IDs from a vocabulary of {vocab_size}")
    taken = set(edges)
    rest = [i for i in np.random.default_rng(seed).permutation(vocab_size).tolist() if i not in taken]
    return np.array((edges + rest)[:n], dtype=np.int64)


def _as_float64_cpu(vectors: Any, dim: int) -> np.ndarray:
    """Copy vectors to a CPU float64 matrix with required width dim (int).

    vectors may be a NumPy array or torch tensor, shape (N, dim) or (dim,).
    Accelerator tensors are copied to CPU. Returns shape (N, dim). Raises
    DecodeInputError for bad shape, nonfinite values or any zero query vector.
    Promotion cannot restore precision already lost during forward encoding.
    """
    if hasattr(vectors, "detach"):  # torch tensor on any device, any float dtype
        import torch

        vectors = vectors.detach().to(device="cpu", dtype=torch.float64).numpy()
    q = np.array(vectors, dtype=np.float64, copy=True)
    if q.ndim == 1:
        q = q[None, :]
    if q.ndim != 2 or q.shape[1] != dim:
        raise DecodeInputError(f"expected vectors of shape (N, {dim}); got {q.shape}")
    if not np.isfinite(q).all():
        raise DecodeInputError("vectors contain NaN or infinity")
    zero = ~q.any(axis=1)
    if zero.any():
        raise DecodeInputError(f"zero vector at rows {np.flatnonzero(zero)[:5].tolist()}: no direction to match")
    return q


def decode(vectors: Any, code_table: CodeTable, *, chunk_rows: int | None = None) -> DecodeResult:
    """Match KE1 code vectors exhaustively using float64 cosine similarity on CPU.

    Parameters
    ----------
    vectors : numpy.ndarray or torch.Tensor, shape (N, D) or (D,)
        Finite, nonzero unprojected forward-codec vectors. Copied/promoted to CPU
        float64; an accelerator input is transferred rather than scored there.
    code_table : CodeTable
        Candidates in the same representation/settings as the queries. Margins
        are relative to every candidate in this supplied table.
    chunk_rows : int or None
        Positive number of query rows scored at once. None estimates a chunk
        from a 256 MiB scoring-temporary budget. This is not a total-memory cap:
        input copies, code-table arrays and output records also consume memory.

    Returns
    -------
    DecodeResult
        Token IDs, stored bytes, best cosine scores and best-minus-second-best
        cosine margins in query order. Exact ties select the lowest token ID
        with margin zero. A margin is not a calibrated probability. Results and
        hashes agree across tested chunk sizes in a fixed environment.

    Raises
    ------
    DecodeInputError
        For invalid shape, nonfinite values or zero query vectors.
    ValueError
        If chunk_rows is not positive.
    """
    q = _as_float64_cpu(vectors, code_table.dim)
    n = q.shape[0]
    if chunk_rows is None:
        per_row = 8 * (code_table.support.shape[0] + 3 * code_table.vocab_size)
        chunk_rows = max(1, DEFAULT_BUDGET_BYTES // per_row)
    if chunk_rows < 1:
        raise ValueError("chunk_rows must be positive")

    ids = np.empty(n, dtype=np.int64)
    best = np.empty(n, dtype=np.float64)
    second = np.empty(n, dtype=np.float64)
    for start in range(0, n, chunk_rows):
        scores = code_table.cosine_scores(q[start : start + chunk_rows])
        top = np.argmax(scores, axis=1)  # first maximum: ties go to the lowest token ID
        rows = np.arange(scores.shape[0])
        end = start + scores.shape[0]
        ids[start:end] = top
        best[start:end] = scores[rows, top]
        scores[rows, top] = -np.inf
        second[start:end] = scores.max(axis=1)
    return DecodeResult(
        token_ids=ids,
        token_bytes=[code_table.token_bytes(int(t)) for t in ids],
        scores=best,
        margins=best - second,
        pos_dim=code_table.pos_dim,
        table_sha256=code_table.table_sha256,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the decoder CLI; argv is an optional argument list without program name.

    Loads --table and --vectors, optionally writes --out JSONL, prints the result
    SHA-256 and returns zero. None reads arguments from sys.argv[1:].
    """
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True, type=Path, help="byte table .npz written by build_tables.py")
    ap.add_argument("--vectors", required=True, type=Path, help=".npy array of shape (N, 256 * P)")
    ap.add_argument("--tokenizer-sha256", default=TOKENIZER_SHA256, help="tokenizer the table must belong to")
    ap.add_argument("--chunk-rows", type=int, default=None)
    ap.add_argument("--out", type=Path, help="write one JSON record per vector to this .jsonl file")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    table = ByteTable.load(a.table, tokenizer_sha256=a.tokenizer_sha256)
    result = decode(np.load(a.vectors, allow_pickle=False), CodeTable.from_byte_table(table), chunk_rows=a.chunk_rows)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            for rec in result.records():
                f.write(json.dumps(rec) + "\n")
    log.info("decoded %d vectors, P=%d, %s table; min margin %.6g", len(result), table.pos_dim, table.kind,
             float(result.margins.min()))  # fmt: skip
    print(result.sha256())
    return 0


if __name__ == "__main__":
    sys.exit(main())
