# D3: interrupted initialization recovery (draft)

Proposal for #819 D3, coordinated with the launcher in #820. This is not
production approval. D4 rollback is outside this change. Do not deploy this
trainer into the running Dry Run 2: its source identity differs from that run.

## Safety rule

An empty commit history does not mean a claim is abandoned. Neither claim age
nor SLURM status proves that its process has stopped. The existing exit-78 hold
remains the fallback whenever exclusive ownership cannot be established.

This draft implements recovery only for a shared filesystem whose OS file locks
work across all participating nodes. Normal local-store trainer invocations hold
an exclusive `.g5-owner.lock` in the run's shared checkpoint directory from
checkpoint initialization through trainer cleanup. Competing invocations fail
with exit 78. The OS releases the lock when the process exits or is killed;
there is no age threshold and the lock file must never be deleted or replaced.
The lock does not cover a different run ID.

Fresh initialization atomically writes a claim with protocol
`g5-local-owner-lock/1` and the exact epoch that the guard protects. This epoch
binding makes a claim advanced by an older, unguarded G7 caller ineligible for
recovery. Existing conditional checkpoint commits still fence old writers.

## Proposed trainer interface

`--recover-precommit` is mutually exclusive with `--resume` and
`--resume-committed`, and requires the usual checkpoint store and run ID.
It must be an explicit launcher decision, not an implicit consequence of an
empty store. With the same reviewed inputs and a fresh output directory, it:

1. Acquires the run's OS owner lock without waiting or breaking a live lock.
2. Requires the supported protocol/epoch, the same G5 training identity, no referenced checkpoint, and no
   nonempty commit history. Legacy claims and malformed history are held.
3. Advances the exact inspected claim with one conditional write. A competing
   change holds; recovery does not retry takeover against a newer owner.
4. Starts a newly initialized model/data stream at step zero and requests a
   step-zero commit before the first optimizer update. Unreferenced uploads,
   including sealed ones, are not restored.

This is reinitialization before any committed progress, not a checkpoint restore
or a rollback. Its manifest records the old/new claim epochs separately from
the training identity. An existing committed run must use normal committed
resume and retains all its normal identity, checksum and replay checks.

S3/object-store recovery remains exit 78: it has no shared OS lock. Claims from
before this protocol also remain exit 78 because an old live writer never took
the lock. Network/filesystem errors and unavailable locking must not authorize
fresh recovery. Actual cross-node lock behavior, including filesystem failure
modes, requires TSAI/G7 target-environment validation before deployment.

## Coordination required with Max

#820 currently holds `claimed_only`, so it will not activate this feature merely
because the trainer has it. Keep that behavior until Shivanshu and Max agree on
the protocol. A coordinated launcher change would own `--recover-precommit`,
pass it only through the agreed recovery path, and still let the trainer hold
unknown/live/object-store claims. Do not add it as an unrestricted input-file
option. Exercise the real trainer as well as mocked command construction.

The adapter seeds G7's `epoch` and `_ptr_ver` after the conditional claim so its
existing `claim()` is a no-op for this attempt. This private-field seam needs
G7 review; a public conditional initial-claim API would be preferable before
production adoption. This branch does not modify G7's checkpoint or launcher
files.

The new exit-note cause is `PrecommitRecoveryError`. The current G7 wrapper
preserves exit 78 and emits its usual held-job event, but its reason catalog
uses generic guidance for that name. Agree a dedicated catalog entry with
Max/G7 and G8 before deployment; it must tell operators not to remove the owner
lock or bypass an unknown/live claim.

## Watchdog and cleanup integration

The lifetime lock remains held until outstanding checkpoint uploads finish.
On a training failure, that cleanup wait runs before the step watchdog closes;
the watchdog is rearmed at the last completed step, so a stuck cleanup wait
still exits 75 with the usual `hang_watchdog` note and stack dump. A test forces
an evaluation failure followed by a stalled cleanup wait. A separate child
process test checks that watchdog `os._exit(75)` releases the OS lock and leaves
a precommit claim eligible for explicit recovery. Watchdog event tests read
JSONL records by event name because the earlier claim event shares the file.

## Acceptance evidence

- A live process blocks recovery without moving the pointer.
- Killing that owner releases its OS lock and permits explicit recovery.
- A stale owner cannot commit using its previous pointer version.
- A concurrent pointer change is refused without a takeover retry.
- Legacy/unknown claims, commit history, read/write failures and unsupported
  stores hold without starting training.
- Interrupted initialization recovers with the same loss trace and step-zero
  resume result as uninterrupted initialization for AdamW and Muon.

The CPU checks below do not establish CUDA parity or the target filesystem's
cross-node locking semantics. Local CUDA results are recorded separately below;
cross-node locking remains separate validation before deployment.

Local validation on 26 Nov 2026 (Windows, PyTorch 2.5.1 CPU): the complete G5
suite passed with 289 tests passed, 12 skipped and 95 subtests passed. The
ownership checks include a real child process holding the lock, forced process
termination, stale-version fencing and claim races. A separate compatibility
check against #820 at `10b7333c` confirmed that its start-mode helper accepts
this metadata and continues to return `claimed_only`; no launcher policy was
changed by this draft.

After protecting the failure-cleanup wait with the watchdog, the full G5 suite
plus G8's adapter tests passed: 297 passed, 12 skipped, 95 subtests passed.
An additional audit inspected actual recovered AdamW and Muon outputs before
fixture cleanup: run-evidence identity/checkpoint validation passed, G8 rows
had the expected run ID and contiguous steps, and smoke runs remained
ineligible for quality acceptance. The #820 start-mode compatibility check
also passed again. These checks used CPU/local Windows locking, not a live
SLURM cluster, CUDA, or a cross-node shared filesystem.

### Local CUDA validation

On 26 Nov 2026, local GPU validation used an NVIDIA GeForce RTX 3070 Laptop
GPU (8 GiB, compute capability 8.6), native bf16, and CUDA-enabled PyTorch
2.5.1 with CUDA runtime 12.1 in the existing Miniforge environment.

The CUDA suite now includes interrupted-start recovery through the actual G5
trainer with the real KAS V2 head, bf16 autocast and the watchdog enabled at
60 seconds. AdamW and Muon both reproduce the uninterrupted loss trace and
the final model hash after restoring the recovered step-zero checkpoint.
Existing GPU fixture parity, bf16 precision and optimizer/RNG resume checks
also pass.

Combined CUDA, checkpoint and ownership regression run: **19 passed, 26
subtests passed, no skips**. This includes all five tests in
`test_week2_kas_cuda.py`. These are small-fixture GPU regression tests, not
a full T2 Dry Run 2, multi-node or production acceptance run.
