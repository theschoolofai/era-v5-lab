"""G5 initialization through G7's existing public checkpoint interfaces."""


def claim_for_start(checkpointer):
    """Refuse committed runs before claiming; recheck after claiming for races.

    The launcher/caller must first establish that the previous attempt stopped.
    Existing candidates are refused without changing ownership. A checkpoint
    racing with the claim is detected by the second check after ownership changes.
    Committed restore and ordinary startup without --checkpoint-at-start do not
    use this path. No private fields or pointer schema extensions are needed.
    """
    from ckpt.ckpt import CheckpointError

    refuse = "Committed checkpoints exist; use --resume-committed"
    try:
        if checkpointer.candidates():
            raise CheckpointError(refuse)
        epoch = checkpointer.claim()
        if checkpointer.candidates():
            raise CheckpointError(refuse)
    except CheckpointError:
        raise
    except Exception as error:
        raise CheckpointError(f"Cannot claim or classify initialization state: {error}") from error
    return epoch
