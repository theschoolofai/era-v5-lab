# D4 draft: G5 rollback integration

Status: local proposal, based on main 821c82ad89602433527846e45dbb518f3f9aa522.
This does not approve production, change DR2, or remove G7's rollback procedure.
D3 (#826), D4, #819 and #820 remain separate drafts pending agreement.

## Proposed behavior

Use --resume-committed with --from-step N, --skip BATCHES, --branch NAME,
and/or --allow-env-change. Every intervention requires a new --branch.
Branch names contain 1-64 ASCII letters, digits, dashes or underscores and
start with a letter or digit. Names already present in the commit journal
are refused. The checkpoint run ID stays unchanged; branch is a G7 checkpoint
namespace within that run, not a Git branch or a second independent run.
Normal committed resume without these options keeps its existing defaults.
Native --resume does not accept these rollback options.

--from-step selects exactly N through Checkpointer.restore. In G7's current
API it selects the most recent journal entry matching that step across all
branches; it does not select a source branch. No matching checkpoint, a
corrupt selected checkpoint, or incompatible state stops the attempt; explicit
selection never falls back to another step. Review the recorded from_path.
Without --from-step, G7's ordinary latest-good fallback policy still applies.
The --branch argument names the destination, never the source.

--skip counts whole G5 training batches, not optimizer updates, tokens,
documents, bytes, or G7's other loaders' units. It advances the same shuffled
window order, offset and private sampler RNG as discarding that many next()
calls, including epoch reshuffles and batches crossing epoch boundaries.
It does not materialize data, advance model RNG or optimizer state, increment
the restored training step, or add discarded tokens to trained-token counts.
G7 checks the saved model, optimizer, RNG/probe and next-batch fingerprint
before applying the skip. The next training update uses the advanced sampler.
No bit-equal replay promise applies to skipping or environment interventions.

--allow-env-change overrides G7's environment-manifest gate only. The exact
G5 identity hash remains mandatory, binding resolved config, artifacts, data,
source files, device and PyTorch version. This flag therefore does NOT permit
changing a recipe, model, tokenizer, data, device or PyTorch version. G7
records its actual environment differences; integrity, strict tensor loading
and restore probes still run. A new branch is required even if no actual
G7 environment difference is found. Broader override policy needs lead review.
Existing checkpoints from an older trainer source identity remain incompatible;
this proposal does not silently migrate their identity or relax that guard.

## History, provenance and durability

Loss traces, metrics rows, cumulative scored tokens and elapsed training time
come from the selected checkpoint, not from a newer output directory. Restored
trace lengths and row steps must agree with its committed step. The output
directory must be fresh. Historical metrics through the selected step are
replayed into that attempt's local metrics file; later rows from abandoned
attempts are not copied or deleted. Token counts exclude skipped data.

The manifest records G7 restore details and the resulting branch. Each
intervention appends a rollback_events record containing the source checkpoint
path, step, trained tokens, destination branch, skipped batches, requested
environment override and actual environment differences. These records persist
in committed checkpoint history, native exports and summaries, including later
ordinary resumes. Intervened lineage is marked as draft rollback and excluded
from quality-comparison eligibility; this is a conservative draft policy.

Before the next optimizer update, publish and wait for a checkpoint on the new
branch containing the restored/skipped state and provenance. This also covers
zero-update attempts. Step-zero forks retain the original lazy optimizer state
using the existing start-checkpoint protocol. G7 keeps ownership claims,
fencing, integrity checks, async upload and checkpoint path generation.

No checkpoint, pin, retention policy, prior attempt output or operation document
is deleted or modified. Pin a rollback source with the existing G7 operations
procedure before retention can remove it. Branching does not automatically pin
its source; retention and pins currently operate across the shared run. A
missing retained source fails restore. A new branch commit moves latest.json
for the SAME run; it is not an independent parallel trainer.

## Explicit integration holds

- G8's current adapter keys metrics by run ID, without checkpoint branch.
  New rollback options with --logger-factory fail before loading inputs.
  Resuming an existing rollback lineage with that logger also stops before
  opening its writer. Local metrics remain available. Agree branch/attempt
  identity, historical-row ingestion and decreasing-step watcher behavior with
  G8/G9 before enabling monitored operational rollback. This is an intentional
  draft limitation, not a claim of watcher continuity.
- #820 currently rejects these flags. G5-only support does not make its launcher
  rollback-capable. Agree reviewed argument-file flags and operator procedure
  with Max; preserve fail-closed launcher validation.
- D4 remains main-based and does not include D3's proposed implementation.
  Revised #826 at 84e6ed7 removes the lifetime OS lock and proposes G7's public
  claim_initial(identity_sha256, allow_takeover=False) API for fresh filesystem
  initialization and explicit precommit recovery. Committed resume/rollback
  continues through restore(); it must not call claim_initial(). G5 does not
  write G7 private ownership fields or add another ownership protocol.
  The operator or launcher must confirm the prior trainer stopped before
  authorizing recovery or rollback. Neither flag proves process death.
  When both drafts land, preserve D3's initial-claim route, mutually exclusive
  recovery mode and watchdog-protected recovery checkpoint barrier alongside
  D4's rollback options and barrier. Rollback options require committed resume,
  so they must be rejected with --recover-precommit. D3's API still needs G7 review.
- Both barriers require a completed wait and confirmation of the exact committed
  step before an optimizer update. Ownership loss takes priority and exits 78;
  skipped, failed or unconfirmed saves exit 75. A boolean wait result alone does
  not establish which step committed. The existing step watchdog stays armed.
- Combining the trainer sources changes G5's strict source identity. Checkpoints
  from a standalone D3 or D4 trainer are not silently migrated to the combined
  trainer; preserve the identity hold even with --allow-env-change.
- Source-branch selection, same-step entries on multiple branches, automatic pin
  policy, and broader environment overrides need agreement. This draft retains
  and documents G7's current step-selection semantics rather than inventing a
  competing checkpoint selector.

## Validation

The focused tests use real G7 filesystem save/restore with small fixture models.
They cover AdamW and Muon, an explicit older step after newer commits, exact
unskipped replay, skip continuation against an independently advanced native
restore, step-zero rollback, no-update branch publication, trained-token counts,
provenance persistence, missing/corrupt selection, reused branch rejection,
unsafe CLI combinations, G7 environment override and strict G5 identity holds.
A CUDA variant runs when CUDA is available. These fixtures are not full T2,
production, object-store, multi-node locking or SLURM qualification.

### Local results, 26 November 2026

- CPU G5 regression directory: 284 passed, 13 skipped, 89 subtests passed
  (145.39 s). This run was collected before the additional KAS-only CUDA
  rollback test was added; the final focused run below covers that addition.
- Final rollback file on the CUDA-capable Python: 6 passed, no skips,
  10 subtests passed (77.52 s). Includes actual KAS bf16 rollback with both
  AdamW and Muon, plus the ordinary CUDA fixture rollback.
- Earlier rollback plus existing KAS CUDA checks: 9 passed, no skips,
  8 subtests passed (44.93 s).
- git diff --check passed. No commit, push, PR or comment was created.

CPU Python: C:/Users/udisi/anaconda3/envs/islp/python.exe.
CUDA Python: C:/Users/udisi/miniforge3/python.exe (RTX 3070 Laptop GPU).
Both used PYTHONDONTWRITEBYTECODE=1, pytest -p no:cacheprovider, and the
existing d3-test-deps directory on PYTHONPATH; global environments were not
changed. PYTHONPATH also included the G5 harness/tests and G7 infrastructure.
OMP_NUM_THREADS=1 and MKL_NUM_THREADS=1 bounded the regression test processes.

Reproduce from the repo with those environment settings:

    <cpu-python> -m pytest -p no:cacheprovider teams/05-architecture/tests -q
    <cuda-python> -m pytest -p no:cacheprovider teams/05-architecture/tests/test_week2_rollback.py -q

These results demonstrate fixture behavior, not approval of a production
rollback, monitoring integration, an old-checkpoint migration, or DR2 changes.

### Alignment with revised #826, 26 November 2026

D4 base: 194850b4426d19096af35281b395be1c2f754c18 plus this alignment change.
D3 reviewed/tested head: 84e6ed7ddfb780238edcab871204eedf76e63d2e (still draft).
No D3 commits or implementation files were added to the D4 branch.

The rollback barrier now checks ownership loss before interpreting the wait
result, then requires last_commit_step to equal the restored step. Ten failure
cases exercise steps 0 and 2 with skipped saves, actual upload errors, actual
conditional-write conflicts, failed waits, and a successful wait without a
confirmed commit. They verify exit 78 for fencing, exit 75 otherwise, no call
to the optimizer-update path, and no final checkpoint export or summary.

- Standalone D4 focused CPU: **5 passed, 2 skipped, 18 subtests passed** (27.50 s).
- Standalone D4 focused CUDA: **7 passed, no skips, 20 subtests passed** (53.25 s),
  including KAS bf16 AdamW/Muon rollback.
- Isolated combined D3+D4 CPU, full G5 directory plus G8 adapter and G7 initial
  claim tests: **317 passed, 15 skipped, 114 subtests passed** (124.28 s).
- Isolated combined D3+D4 CUDA, rollback/KAS/initial-claim tests:
  **31 passed, no skips, 29 subtests passed** (68.82 s).
- git diff --check passed.

The combined copy resolves the two trainer overlaps by preserving both the
recovery parser option and rollback options, and both pre-update checkpoint
barriers. Additional isolated checks reject recovery with active rollback
options before input loading and exercise recovery followed by rollback under
the same run ID with AdamW and Muon. The combined KAS bf16 CUDA rollback test
also starts through D3 recovery. These combined checks used a temporary source
snapshot; they do not make D4 depend on the unmerged D3 draft or install that
snapshot into DR2. A future actual merge still needs conflict resolution and
validation against the heads that are agreed at that time.

The launcher, monitoring and target-filesystem acceptance items above remain
pending. This alignment creates no PR or deployment and does not relax training
identity, the prior-process-stopped precondition, or the draft status.
