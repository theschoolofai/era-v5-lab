"""The Kronecker forward codec: upstream float32 wrapper and a float64 reference.

For a token with bytes b_0 .. b_{L-1} (L <= P) the code is the z-normalised vector

    x = (1 / sqrt(L)) * sum_p onehot(b_p * P + p)      in R^D, D = char_dim * P

(upstream ``kronecker_embeddings.codec.kronecker_codec``: unbiased std, ``std + eps`` in the
denominator). After z-normalisation every coordinate takes one of two values that depend only on L
(Lemma 1): ``high`` on the L support cells and ``low`` everywhere else. :func:`code_values` gives
both in closed form, so the float64 reference codes are exact per length and identical for every
string of that length.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .config import CHAR_DIM
from .tables import ByteTable


def output_dim(pos_dim: int, char_dim: int = CHAR_DIM) -> int:
    """D = char_dim * pos_dim."""
    return char_dim * pos_dim


def encode_ids(input_ids: Any, table: ByteTable, *, char_dim: int = CHAR_DIM, **codec_kwargs: Any):
    """Embed ``input_ids`` (any shape) with the upstream float32 ``kronecker_codec`` on CPU.

    Returns a tensor of shape ``input_ids.shape + (char_dim * table.pos_dim,)``.
    """
    import torch
    from kronecker_embeddings.codec import kronecker_codec

    ids = torch.as_tensor(input_ids, dtype=torch.long).cpu()
    flat = ids.reshape(-1)
    byte_buf = torch.from_numpy(table.bytes)[flat]
    len_buf = torch.from_numpy(table.lengths.astype(np.int64))[flat]
    out = kronecker_codec(byte_buf, len_buf, char_dim=char_dim, pos_dim=table.pos_dim, **codec_kwargs)
    return out.reshape(*ids.shape, char_dim * table.pos_dim)


def code_values(
    lengths: np.ndarray | int,
    pos_dim: int,
    *,
    char_dim: int = CHAR_DIM,
    length_normalize: bool = True,
    z_normalize: bool = True,
    eps: float = 1e-6,
) -> tuple[np.ndarray, np.ndarray]:
    """``(high, low)`` code values in float64 for strings of the given lengths (0 <= L <= P).

    The empty string (L = 0) has the all-zero code: ``high == low == 0``.
    """
    L = np.asarray(lengths, dtype=np.float64)
    if np.any(L < 0) or np.any(pos_dim < L):
        raise ValueError(f"lengths must lie in [0, {pos_dim}]")
    D = float(char_dim * pos_dim)
    nonempty = L > 0
    v = np.where(nonempty, 1.0 / np.sqrt(np.maximum(L, 1.0)), 0.0) if length_normalize else nonempty * 1.0
    if not z_normalize:
        return v, np.zeros_like(v)
    mean = L * v / D
    var = (L * (v - mean) ** 2 + (D - L) * mean**2) / (D - 1.0)
    std = np.sqrt(var) + eps
    return (v - mean) / std, -mean / std


def encode_f64(
    byte_rows: np.ndarray,
    lengths: np.ndarray,
    pos_dim: int,
    *,
    char_dim: int = CHAR_DIM,
    length_normalize: bool = True,
    z_normalize: bool = True,
    eps: float = 1e-6,
) -> np.ndarray:
    """Dense float64 reference codes, shape ``(N, char_dim * pos_dim)``.

    Same math as upstream ``kronecker_codec``, computed exactly per length (see module docstring).
    Memory is ``N * D * 8`` bytes: encode in chunks for large N.
    """
    byte_rows = np.asarray(byte_rows)
    lengths = np.asarray(lengths, dtype=np.int64)
    if byte_rows.ndim != 2 or byte_rows.shape[1] != pos_dim or lengths.shape != (byte_rows.shape[0],):
        raise ValueError(f"expected byte_rows (N, {pos_dim}) and lengths (N,); got {byte_rows.shape}, {lengths.shape}")
    high, low = code_values(
        lengths, pos_dim, char_dim=char_dim, length_normalize=length_normalize, z_normalize=z_normalize, eps=eps
    )
    out = np.repeat(low[:, None], char_dim * pos_dim, axis=1)
    pos = np.arange(pos_dim)
    rows, cols = np.nonzero(pos[None, :] < lengths[:, None])
    out[rows, byte_rows[rows, cols].astype(np.int64) * pos_dim + cols] = high[rows]
    return out


def read_support(code: Any, pos_dim: int) -> bytes:
    """Read the byte string back from one code (the argument of Lemma 1).

    The high cells are the support; cell ``i`` of the flattened ``(char_dim, P)`` grid is byte
    ``i // P`` at position ``i % P``. Works for float32, bfloat16 and float64 codes. Raises
    ``ValueError`` unless the support has exactly one cell per position ``0 .. L-1``.
    """
    if hasattr(code, "detach"):  # torch tensor (bf16 has no numpy dtype)
        code = code.detach().float().cpu().numpy()
    z = np.asarray(code, dtype=np.float64).reshape(-1)
    hi, lo = z.max(), z.min()
    if hi == lo:  # the all-zero code of the empty string
        return b""
    by_pos: dict[int, int] = {}
    for i in np.flatnonzero(z > (hi + lo) / 2).tolist():
        p = i % pos_dim
        if p in by_pos:
            raise ValueError(f"two lit cells at position {p}")
        by_pos[p] = i // pos_dim
    if sorted(by_pos) != list(range(len(by_pos))):
        raise ValueError("lit positions are not 0..L-1")
    return bytes(by_pos[p] for p in range(len(by_pos)))
