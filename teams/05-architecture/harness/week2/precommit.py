"""G5 adapter to G7's proposed public initial-claim interface (D3 draft)."""


def claim_initial_state(checkpointer, *, identity_sha256, recovering=False):
    """The caller must stop the prior attempt before authorizing takeover.

    G7 validates metadata, enforces the exact conditional transition and owns
    its epoch/pointer state. G5 only records the returned transition for evidence.
    """
    from ckpt.ckpt import CheckpointError

    method = getattr(checkpointer, "claim_initial", None)
    if method is None:
        raise CheckpointError("G7's public claim_initial interface is required for this D3 draft")
    epoch = method(identity_sha256, allow_takeover=recovering)
    return {"previous_epoch": epoch - 1, "epoch": epoch}
