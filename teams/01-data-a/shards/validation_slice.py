"""The validation slice (B4: a fixed-seed slice per pack), shared by shard_writer.py, which applies it, and
pipeline/reconcile_shards.py, which recomputes it: the docs outside it are counted, never listed, so the two must agree.

A held-out doc is in the slice of fraction F with seed N when the first 8 bytes of sha256("<N>:<pack_id>:<doc_id>"),
read big-endian as a fraction of 2^64, are below F. Each doc is decided alone, so the slice does not depend on row
order, parts or workers, and a larger F keeps every doc of a smaller one. Standard library only.
"""
import hashlib

VALIDATION_SEED = 20261101  # the default seed: the seed of the week-2 sample's 1% held-out split
SLICE_RULE = "first 8 bytes of sha256('<seed>:<pack_id>:<doc_id>'), big-endian, / 2^64 < fraction"


def in_slice(seed, pack_id, doc_id, fraction):
    """True when the doc is in the validation slice. Every doc is in a slice of fraction 1."""
    if fraction >= 1:
        return True
    digest = hashlib.sha256(f"{seed}:{pack_id}:{doc_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") < fraction * 2 ** 64


def slice_problem(fraction):
    """Why this fraction cannot be used, or None."""
    return None if 0 < fraction <= 1 else f"--validation-fraction is {fraction}, expected a number above 0 and at most 1"
