# D3: interrupted initialization recovery (draft)

This revises #826 for the simpler direction discussed with Shivanshu and Max.
It remains a draft, not approval to deploy. D4 rollback is separate. Do not
change the running Dry Run 2 trainer, inputs or launch policy for this proposal.

## Problem and resulting behavior

A trainer can claim a run ID and then stop before its first checkpoint commits.
Normal fresh mode correctly refuses the existing claim, while committed resume
has nothing to restore. D3 adds an explicit way to initialize that same logical
run again, after the operator or launcher has confirmed the old attempt stopped.
It does not recover work that was never committed or diagnose why training failed.

`--recover-precommit` is mutually exclusive with native and committed resume.
It requires the checkpoint store, same run ID and same resolved training identity.
Use a fresh output directory. The flag authorizes takeover; it does not prove the
previous process is dead. Claim age and an empty history are not evidence of death.
If the previous attempt cannot be confirmed stopped, retain the exit-78 hold.

## Proposed public G7 interface

This draft proposes `Checkpointer.claim_initial(identity_sha256,
allow_takeover=False)` in G7. Max/G7 still needs to review and agree that API.
G5 calls it through a small adapter; G5 no longer writes G7's private `epoch`
or `_ptr_ver` fields, creates lock protocol markers, or holds a lifetime OS lock.
G7's existing short-lived storage CAS lock and checkpoint fencing are unchanged.

The method supports a single-process trainer using a filesystem checkpoint store:

1. Read the exact pointer bytes/version and commit history. Read failures,
   malformed pointers and any nonempty history hold without changing ownership.
2. Fresh mode requires no pointer or history. Explicit recovery instead requires
   a valid claim with no checkpoint reference and a matching training identity.
   Missing identities hold; the earlier D3 draft's identity field is accepted.
3. Advance ownership once, conditional on the exact inspected pointer version.
   A competing claim or checkpoint publication produces `FencedError`; there is
   no takeover retry against the winner. Existing writers retain normal fencing.
4. Record the new epoch and emit G7's existing `checkpoint.claimed` event.

Checking for a committed pointer before takeover matters even when history has
not yet been appended. Calling unrestricted `claim()` first and rejecting a
checkpoint afterwards could fence its healthy owner. This narrower method avoids
that change of ownership. Unreferenced uploads, including sealed manifests, are
not treated as committed progress and are not restored.

Object-store recovery and distributed trainer initialization remain unsupported
by this proposal. Normal object-store fresh/committed-resume behavior is retained.
No metadata or leftover lock files are deleted. In particular, a lock file from
the previous D3 revision is not proof of a stopped process and is not used here.

## Trainer initialization and checkpoint barrier

After successful explicit recovery, the trainer initializes model, optimizer,
RNG and data stream from the reviewed inputs at step zero. It records old/new
claim epochs in `manifest.json` under `precommit_recovery`, separately from the
training identity. It requests a G7 step-zero checkpoint and waits for its commit
before the first training update. A skipped or failed/unconfirmed save exits 75;
ownership loss exits 78. The step watchdog remains active during that wait.

Normal `--checkpoint-at-start` behavior remains asynchronous. Existing committed
resume keeps its restore, identity and checksum checks. The step-zero snapshot
preserves lazy optimizer initialization so restoring it reproduces uninterrupted
AdamW/Muon training. No checkpoint cadence or production topology changes here.

## What is still pending

- **G7/Max:** agree and review the proposed public API, ownership precondition and
  filesystem semantics. This PR includes the proposed implementation so the
  interface can be reviewed concretely; it is not already supplied by #820.
- **G7 launcher:** #820 still holds `claimed_only`. Keep that hold until agreement.
  Any later opt-in recovery route must be launcher-owned, require confirmation
  that the old attempt stopped, and exercise the real trainer. Do not silently
  enable recovery through arbitrary input-file arguments.
- **G7/G8:** review `checkpoint.claimed` with `recovered_precommit`, the existing
  `CheckpointError`/`FencedError` exit-note causes, and held-job guidance together.
  This revision no longer emits the old `PrecommitRecoveryError` cause; any
  catalog entry added for that earlier draft may need corresponding adjustment.
- **TSAI/G7/G5:** validate the agreed launcher/trainer flow and fencing on the
  target shared filesystem before adoption. Local regression tests do not prove
  cross-node behavior or production readiness. DR2 gains no recovery option.
- **Shivanshu:** review the revised draft. Accepting the simpler direction was
  not approval of this code or of a production run.

## Validation

Tests cover actual filesystem conditional writes; refusal of committed pointers
before history publication; malformed, missing and mismatched claim metadata;
competing claim/commit races without retry; and stale-writer fencing. G5 tests
cover public-API delegation, recovery failure before any optimizer update, and
a watchdog timeout while waiting for the recovered step-zero checkpoint.

End-to-end small-fixture tests recover interrupted initialization with AdamW and
Muon, compare loss traces, then restore the recovered step-zero checkpoint and
compare the final model hash. CUDA tests also exercise the actual KAS V2 head
with bf16 and the watchdog. These are regression checks, not a DR2 or production
acceptance run.

Local validation on 26 Nov 2026:

- Full G5 CPU suite, G8 adapter and proposed G7 initial-claim tests:
  **308 passed, 13 skipped, 89 subtests passed** (PyTorch 2.5.1 CPU).
  After adding two metadata read/write failure cases, the complete G7
  initial-claim test file also passed independently: **17 passed**.
- Targeted CUDA/checkpoint/adapter/watchdog/initial-claim run:
  **36 passed, 22 subtests passed, no skips** (PyTorch 2.5.1, CUDA 12.1,
  RTX 3070 Laptop GPU). The real KAS V2 recovery case uses bf16 with AdamW
  and Muon. This run preceded the two additional metadata failure cases above.
- Existing G7 stale-owner checkpoint and asynchronous snapshot regressions:
  **2 passed**. The existing local-store concurrency test initially encountered
  a Windows temporary-directory permission error opening `log.jsonl.lock`;
  rerunning it with a workspace temporary directory passed (**1 passed**).

Counts from the earlier lifetime-lock revision do not validate this revision.
