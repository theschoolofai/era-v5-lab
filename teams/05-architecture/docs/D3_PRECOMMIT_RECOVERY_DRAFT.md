# D3: interrupted initialization recovery (week-5 draft)

This revision follows Suresh's Team 7 direction, Shivanshu's review and Pradeep's
read-only candidate-precheck request on #826.
It remains a draft. Do not deploy it into Dry Run 2 or change this week's fresh
start or launcher behavior. Target week 5, after the main-run go/no-go on
28 Nov and confirmation of the main-run checkpoint store. D4 rollback is separate.

## Problem

A trainer can claim a run ID and stop before its first checkpoint commits.
Ordinary fresh mode refuses that run ID, while committed resume has nothing to
restore. D3 lets an authorized replacement attempt initialize the logical run
again when no committed checkpoints exist. Uncommitted training work is not
restored. This is initialization recovery, not failure diagnosis or rollback.

## Entry condition and ownership

There is no new recovery flag or G7 API. For the proposed week-5 flow, the
launcher passes the existing `--checkpoint-at-start` for fresh and claim-only
initialization. Before resubmitting a claim-only run, G7 requires the launcher
to check the previous job with `sacct` and establish it is no longer RUNNING or
PENDING. That check belongs in Max's #820; this trainer does not perform it.
Direct callers likewise must establish the previous attempt stopped before
using this initialization path. An empty checkpoint history is not that proof.

With a checkpoint store and `--checkpoint-at-start`, and without native or
committed resume, the trainer calls G7's existing public methods:

1. Read `candidates()` without claiming. If committed candidates already exist,
   exit 78 with `use --resume-committed`, preserving the pointer and live owner.
2. `claim()` advances the ownership epoch using G7's conditional writes and
   existing retry/fencing rules.
3. `candidates()` rechecks committed state after the claim. If candidates
   exist, exit 78 with `use --resume-committed`; do not initialize over them.
4. Without candidates, initialize step zero and request a checkpoint. Wait for
   its commit before the first training update, with the step watchdog active.

Pradeep's review adds the read-only precheck: an accidental start against an
already-committed run must not fence its live owner. The second check remains
necessary. If an old attempt commits after the precheck but before/during claim,
the claim can advance ownership, then the new candidate is refused. Existing
checkpoint references/history are preserved. An old attempt publishing after
takeover is fenced. A competing claim causes `FencedError` rather than a G5
takeover retry.

Without `--checkpoint-at-start`, ordinary fresh startup retains the existing
run-ID check and lazy claim at save time. Committed resume retains its existing
restore path. The initialization flag now waits for step-zero commit on fresh
starts as well as on claim-only restarts; that is a proposed future behavior,
not a change to an active launch. Native resume is not an initialization restart.

## Data, metadata and failures

- G7 checkpoint source and pointer schema are unchanged from the pre-D3 base.
  No identity fields or ownership protocol markers are added to `latest.json`.
- G5 records the initialization epoch in its output `manifest.json` under
  `team7_initialization`. Existing training identity and checkpoint manifest
  config/code/data checks remain in their normal locations.
- No previous identity is inferred from an uncommitted claim. The launcher must
  supply reviewed inputs for reinitialization; no checkpoint exists to compare
  or restore. Normal committed restore keeps its identity/checksum checks.
- Unreferenced uploads, including sealed manifests, are not restored. Nothing
  deletes claim metadata, old upload directories or leftover lock files.
- Claim/candidate errors hold with exit 78. Candidates require committed resume.
  A lost claim exits 78. A skipped, failed or unconfirmed step-zero checkpoint
  exits 75 before training updates. Existing CheckpointError/FencedError causes
  are used; no PrecommitRecoveryError reason-catalog entry is needed.
- The watchdog covers initial evaluation, the step-zero save and its wait.
  A stall exits through the existing watchdog event/note and stack dump.

## Scope and pending work

- **G5:** this draft implements the trainer entry path and regressions. It does
  not enable a launcher route or modify the current DR2 job/run inputs.
- **G7/Max (#820):** implement and validate the prior-job check, owned arguments
  and fresh/claim-only routing. Until agreement and adoption, keep claim-only
  as exit 78. The interim runbook workaround is to confirm the old job ended
  and resubmit under a new run ID. G7 owns that runbook update.
- **G7/Pradeep:** review this revision against the existing checkpoint contract,
  including read-only candidate rejection, postclaim race detection, and
  the two-process test.
- **G7/G8:** review existing event and exit-note handling with the actual launcher.
  G7 emits its normal checkpoint.claimed event; G5 does not duplicate it.
- **TSAI/G7/G5:** confirm the main-run store and validate the agreed integrated
  flow on the target environment before adoption. Shivanshu's draft review and
  deployment/run approval remain pending.

The adapter uses G7's existing interfaces without a new store-type gate. This
does not establish that G5 training supports distributed main-run topologies:
the two-rank test validates the initialization/checkpoint boundary
using G7's tiny model/loader, not a multi-rank G5 training run. Object-store and
live SLURM integration remain validation work; no such acceptance is claimed.

**Future multi-rank D2 prerequisite (week 5 or later).** Each rank currently reads
`candidates()` independently. Ranks could observe different state or read errors:
one could exit while another enters collective `claim()` and waits for it. Before
enabling distributed G5 training, have rank 0 classify candidates and broadcast
the decision or error for both the preclaim and postclaim checks, so all ranks
take the same path. Add tests for divergent reads/errors and coordinated exits
without hangs. The current two-process success test does not cover disagreement.
This coordination is not implemented here and is not required for the current
single-process, one-GPU scope.

## Regression coverage

- Public candidates/claim/candidates order with no private state assignments.
- Fresh and claim-only initialization with the standard G7 pointer schema.
- An actual stale-writer checkpoint upload rejected after takeover.
- Existing committed candidates rejected without changing the pointer/history;
  the live owner can still commit afterwards.
- A checkpoint committed between the precheck and claim is caught by the second
  candidate check, without initializing over it.
- An actual commit racing with claim: G7 retries, then G5 rejects the candidate.
- A competing claim fences the losing initialization attempt.
- Metadata exceptions hold rather than triggering an initialization fallback.
- Actual trainer exits 78 for candidates/competing claims and 75 for skipped,
  failed or unconfirmed step-zero saves, with no optimizer update.
- Actual two-process gloo ranks acquire one shared epoch and commit step zero.
- Ordinary fresh/committed-resume paths bypass the initialization adapter.
- CPU fp32 and CUDA bf16 AdamW/Muon loss-trace and recovered-step-zero restore parity,
  including the real KAS V2 head; watchdog protection of the initialization wait.

Validation of Pradeep's precheck revision on 27 Nov 2026:

- Initialization contract, real trainer checkpoint/restore, watchdog and CUDA
  regressions: **28 passed, 24 subtests passed, no skips**. Includes read-only
  rejection with the live owner's next commit succeeding, both commit-race
  windows, competing claims, actual two-process gloo commit, and real KAS V2
  CUDA bf16 recovery/restore with AdamW and Muon.
- `git diff --check` passed. No trainer flags, G7 files or launch scripts changed.

Previous revision's validation on 26 Nov 2026 (before Pradeep's precheck fix):

- Full G5 CPU suite and G8 adapter: **299 passed, 13 skipped, 91 subtests passed**
  with PyTorch 2.5.1 CPU. Includes the initialization-wait watchdog test and the
  actual two-process gloo checkpoint test.
- Targeted CUDA/KAS, checkpoint and public-interface regressions:
  **21 passed, 22 subtests passed, no skips**, with PyTorch 2.5.1, CUDA 12.1
  and RTX 3070 Laptop GPU. Includes real KAS V2 bf16 AdamW/Muon recovery and
  step-zero restore parity. The two-process case uses CPU gloo in this run.
- `git diff --check` passed. G7 checkpoint source matches the pre-D3 base;
  the proposed G7 API and its dedicated tests were removed.
- Inspected #820 at `8077cc82`: the public claim/candidates/wait interfaces
  remain compatible with these calls. This is a source-interface check, not
  a live launcher or combined-branch acceptance test.

Earlier API/lock-based test counts do not validate this implementation. These
local checks do not establish S3, SLURM, target-filesystem or production acceptance.
