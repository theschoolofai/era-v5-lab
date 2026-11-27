"""G5 initialization through G7's existing public checkpoint interfaces."""


def claim_for_start(checkpointer):
    """Claim before classifying, as agreed with G7 for the week-5 D3 draft.

    The launcher/caller must first establish that the previous attempt stopped.
    This changes ownership even if candidates are subsequently found and refused.
    Committed restore and ordinary startup without --checkpoint-at-start do not
    use this path. No private fields or pointer schema extensions are needed.
    """
    from ckpt.ckpt import CheckpointError

    try:
        epoch = checkpointer.claim()
        if checkpointer.candidates():
            raise CheckpointError("Committed checkpoints exist; use --resume-committed")
    except CheckpointError:
        raise
    except Exception as error:
        raise CheckpointError(f"Cannot claim or classify initialization state: {error}") from error
    return epoch
