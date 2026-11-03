"""The rules that cut a token's bytes to at most P bytes (proof.md, Lemma 2).

Three rules are in use. They agree on valid UTF-8, and no BrahmicTokenizer-131K token is longer
than 32 bytes, so on that tokenizer none of them ever cuts anything at P = 32 or P = 64.

``repo_truncate``           upstream ``utf8_safe_truncate``: the first of the prefixes of length
                            P, P-1, P-2, P-3 that is valid UTF-8, else ``b""``. Used by the proofs.
``proposed_truncate``       proof.md's proposed fix: never splits a character, never empties a
                            non-empty token.
``continuation_truncate``   the decode table's rule (from build_tables.py): step back over
                            continuation bytes. The decode table only holds valid UTF-8.
``byte_truncate``           the raw table's rule: a plain byte cut.
"""

from __future__ import annotations

from collections.abc import Callable

TruncateRule = Callable[[bytes, int], bytes]


def _is_continuation(byte: int) -> bool:
    return (byte & 0xC0) == 0x80


def repo_truncate(raw: bytes, P: int) -> bytes:
    """Upstream rule (``kronecker_embeddings.tokenizer_utils.utf8_safe_truncate``).

    A token longer than P with no valid prefix among the four (for example one starting with a
    stray continuation byte) becomes ``b""`` and gets the all-zero code.
    """
    from kronecker_embeddings.tokenizer_utils import utf8_safe_truncate

    return utf8_safe_truncate(raw, P)


def proposed_truncate(raw: bytes, P: int) -> bytes:
    """Cut to at most P bytes without splitting a UTF-8 character, but keep the bytes.

    Try the cut positions P, P-1, P-2, P-3 in order and take the first whose byte is not a
    continuation byte. If none works (a run of stray continuation bytes), cut at exactly P.
    Equal to the repository rule on valid UTF-8.
    """
    if len(raw) <= P:
        return raw
    for c in range(P, max(P - 4, 0), -1):
        if not _is_continuation(raw[c]):
            return raw[:c]
    return raw[:P]


def continuation_truncate(raw: bytes, P: int) -> bytes:
    """Decode-table rule: walk back from P over continuation bytes, then cut."""
    if len(raw) <= P:
        return raw
    cut = P
    while cut > 0 and _is_continuation(raw[cut]):
        cut -= 1
    return raw[:cut]


def byte_truncate(raw: bytes, P: int) -> bytes:
    """Raw-table rule: keep the first P bytes."""
    return raw[:P]


RULES: dict[str, TruncateRule] = {
    "repo": repo_truncate,
    "proposed": proposed_truncate,
    "continuation": continuation_truncate,
    "bytes": byte_truncate,
}
