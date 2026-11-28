# D4 draft: explicit committed-step restore

Status: narrowed local revision of #847 following Suresh's G7 guidance on
#826/#820 and Shivanshu's review on #847. Keep the PR draft. This is not
approval to deploy, start the main run, or change DR2.

## Why this revision

Suresh identified the smallest D4 trainer fix as --from-step only, using the
existing Checkpointer.restore(from_step=...) interface. Shivanshu described
the broader implementation but explicitly did not approve it; launcher,
source-branch selection and the monitoring hold remain open.

The earlier four-flag proposal is superseded by this revision. --skip,
--branch and --allow-env-change are no longer exposed by G5. BatchStream and
CheckpointProgress return to their main-based implementations; G5 adds no
skip adapter, branch creation or environment override. No G7 code is changed.

Review evidence, read in full on 27 November 2026:

- Suresh, #826: https://github.com/theschoolofai/era-v5-lab/pull/826#issuecomment-7198102329
- Suresh, #820: https://github.com/theschoolofai/era-v5-lab/pull/820#issuecomment-7208915972
- Shivanshu, #847: https://github.com/theschoolofai/era-v5-lab/pull/847#issuecomment-7200086602

## Proposed trainer behavior

Use --resume-committed --from-step N with the existing --checkpoint-store,
--run-id and a fresh --out directory. N must be nonnegative, including zero.
Native --resume and fresh startup cannot use --from-step. Do not combine it
with the initialization flag --checkpoint-at-start.

G5 passes from_step=N to G7's existing public restore(). G7 claims the run,
selects the newest journal entry at exactly N, and validates the checkpoint.
A missing, corrupt or incompatible explicit selection stops the attempt;
it never falls back to another step. Without --from-step, ordinary committed
resume retains G7's normal latest-good/fallback behavior.

Selection is across the run's journal, not a separately selected source branch.
When multiple entries share N, G7 selects the newest matching entry. The actual
source path and branch are recorded for review. No destination branch is
created: subsequent saves continue on G7's restored branch under a new epoch,
within the same run ID. Source selection still needs G7/lead agreement.

G7's integrity, tensor/optimizer, RNG, probe and next-batch checks remain active.
G5's exact training-identity check remains active. There is no environment or
source-identity bypass, and no automatic migration of older checkpoints.

## Training history and evidence

Loss traces, metrics rows, elapsed training time and trained-token counts come
from the selected committed checkpoint. Trace lengths and row steps must agree
with its step. No newer attempt's history is copied into the restored prefix.
Old attempt outputs are not deleted or rewritten.

The attempt manifest records G7's restore details. An explicit selection adds
a rollback_events record with source path, step, trained tokens and restored
branch. replay_guaranteed remains false as a conservative draft policy.
Records persist through subsequent committed resumes and native exports/resumes.
Rollback lineage remains excluded from quality-comparison eligibility, and the
manifest marks it as DRAFT_ROLLBACK_NOT_A_QUALITY_RESULT, pending lead agreement.

The selected state is already committed. With no skip or new destination
branch, D4 does not publish a duplicate checkpoint before another update.
An attempt with no further updates reports the restored checkpoint path.
Subsequent updates use the existing save cadence, fencing and final-save checks.
A restore/fencing/identity failure exits 78 before training updates. The step
watchdog and normal checkpoint failure handling remain unchanged.

Checkpoint pins and retention are unchanged. Pin the desired source through
G7's existing procedure before retention can delete it. A missing source is a
restore failure. This draft does not remove G7's operations procedures.

## Monitoring remains an explicit hold

Suresh clarified that launcher attempts each write their own
<run>/<job>.<restart>/train/metrics.jsonl. G8 ingestion must read all attempts;
G9's ordinary watcher reads committed checkpoints. That does not by itself
settle historical-row duplication, rollback to repeated/lower steps, or
selection among same-step commits for this new D4 path.

Following Shivanshu's review, explicit rollback with --logger-factory remains
held before input loading. Later resumes of rollback lineage also stop before
opening that external writer. Local metrics remain available. G8/G9 must agree
attempt-history and watcher behavior before enabling operational monitoring.
This is a remaining deployment limitation, not evidence that the existing G9
watcher is broken or permission to redesign its identity here.

## D3 and launcher boundary

D4 remains main-based and separate from #826. Revised D3 head 83632902 uses
G7's existing public claim() then candidates() for --checkpoint-at-start.
There is no claim_initial API, recovery flag, pointer identity extension,
lifetime lock or private-field assignment to adopt into D4. Committed restore
still uses restore(); it must not call D3's initialization adapter.

D3's step-zero save/wait barrier belongs to its proposed initialization path.
It is different from restoring an already committed step in D4. Ordinary
startup and initialization options are not changed by this D4 revision.
Combining trainer source changes still changes G5 identity; preserve that hold.

At the latest review, #820 head 96fdcf49 still rejected --from-step in G5
arguments. Trainer support alone does not enable launcher rollback. G7 must
agree argument validation, stop/hold conditions, explicit authorization and
selected checkpoint routing before main-run use. Do not add TRAIN_EXTRA,
automatic rollback or a recovery flag as a workaround.

Suresh's interim D3 procedure is to confirm in sacct that the earlier job ended
and resubmit under a NEW RUN_ID when nothing committed. Automated sacct checks
and claim()/candidates() initialization are week-5 work after the 28 November
go/no-go and store confirmation. That uncommitted-start workaround is NOT a
rollback procedure for committed progress. The trainer does not prove job
liveness. A rollback caller/launcher must establish the old attempt stopped.
No DR2, production recipe, interval/watchdog pin, or launcher code changes here.

## Pending agreements

| Pending item | Proposed resolution |
| --- | --- |
| Previous attempt stopped | G7 owns launcher job/attempt identification and confirmation. Retain a hold when status is uncertain; age or empty history is not proof. |
| Launcher route | Max/G7 must explicitly validate and route --from-step with committed resume. Current #820 still rejects it. No automatic rollback is introduced. |
| Source checkpoint | Agree newest matching step across branches and behavior with repeated step numbers; record the exact selected path. |
| Monitoring | G8/G9 must validate all-attempt ingestion, historical rows, repeated/lower steps and committed-checkpoint watcher behavior before removing the logger hold. |
| Lead behavior | Shivanshu reviews the narrowed scope, same-branch continuation, provenance and quality-comparison policy. His earlier review was not approval. |
| Joint/target validation | Test against current D3/G7 heads locally, then agree a dedicated target-filesystem/launcher test separate from DR2. Local fixtures do not establish SLURM, object-store or production acceptance. |

## Validation for this revision

Local validation on 27 November 2026:

| Source/test set | Result |
| --- | --- |
| Standalone D4 focused CPU | 2 passed, 3 skipped, 11 subtests passed (24.17 s) |
| Standalone D4 focused CUDA | 4 passed, 1 skipped, 13 subtests passed (76.22 s) |
| Combined D3+D4+#820: full G5 CPU suite, G8 adapter and G7 shared-candidate test | 303 passed, 15 skipped, 104 subtests passed (366.32 s) |
| Combined D3+D4+#820: targeted CUDA/KAS, checkpoint and initialization tests | 26 passed, no skips, 37 subtests passed (366.19 s) |
| #820 start-mode/shared-candidate/hold-event Python tests | 8 passed (1.04 s) |

Standalone tests skip the conditional joint-initialization case because D3 is
not included in this branch; CPU also skips the two CUDA cases. The same joint
case runs in the combined copy. Its KAS bf16 CUDA test initializes a claim-only
run using D3's --checkpoint-at-start, trains, and then restores an explicit
older step, with AdamW and Muon. D3's actual two-process gloo checkpoint test
also passed in the combined suites; this is not distributed G5 training support.

Other checks cover replay losses and final model hashes, step-zero restore,
restored token/history counts, source manifest preservation, no duplicate save
for a zero-update restore, persisted lineage in later/native resumes, the
monitoring hold, and failure before optimizer updates for missing/corrupt
selection, changed identity/environment and ownership loss.

The combined source copy used D3 at
83632902c333d3a3190f848f76a2da13ef1c03ce and all 11 changed #820 files at
8077cc82e7784691285c0dc66d83b8f0030689ed; downloaded G7 file blob hashes were
verified. D3's trainer initialization changes were composed with the narrowed
D4 working tree in a temporary snapshot. No D3/G7 changes were merged into D4.
Current main at 36e582ae had no overlapping trainer/adapter/checkpoint changes,
and the original D4 base was retained. No other open PR besides #826/#847
changed these D4 paths at review.

Tests used the existing CPU Python and CUDA-capable Python, the existing
borrowed test dependencies, PYTHONDONTWRITEBYTECODE=1, pytest
-p no:cacheprovider, and OMP_NUM_THREADS=1/MKL_NUM_THREADS=1. No global Python
environment was changed. git diff --check passed. The loader and adapter have
zero diff against the original base; the proposed PR now has three files.

Earlier four-flag and claim_initial-based counts do not validate this revision.
These results do not enable the still-rejecting launcher, settle monitoring,
prove real shared-filesystem/object-store/SLURM behavior, or approve deployment.
The remote PR description must be revised to match this narrowed scope when
the user publishes the revision.


### Latest #820 recheck

Remote heads were rechecked directly: #820 is now
96fdcf4976ea0c1ee476a1ccdea9eafaf241a34d; #826 remains
83632902c333d3a3190f848f76a2da13ef1c03ce. #847 still points to the earlier
published four-flag revision at 5e0d0084; this narrowed local work is not yet
published there. The latest discussions were reread from the PR pages after
the unauthenticated API rate limit was reached; a failed API call was not used
as evidence that discussion or approval was absent.

The complete #820 delta from 8077cc82 to 96fdcf49 changes four files:
runbook guidance, the start_mode docstring, launcher hold wording/comments,
and launcher-test assertions. It implements Suresh's three requested changes:

- Claim-only hold/runbook guidance says confirm the earlier job ended in sacct
  and resubmit with a new RUN_ID; the runbook also says cancel the held job
  rather than release it into the same hold again.
- The pinned 600-second interval/watchdog now references the provisional
  interval document and related retention sizing.
- The runbook identifies metrics.jsonl per attempt and G8 all-attempt ingestion;
  G9's ordinary watcher still reads committed checkpoints.

No restore/candidate API, G5 flag allowlist or rollback route changed in this
delta. Automated previous-job checks and the D3 initialization route remain
future work. The G5 unsupported list still includes --from-step, --skip,
--branch and --allow-env-change. These new G7 changes therefore require no
additional D4 trainer code and do not authorize removing the monitoring hold.

The isolated combined copy was updated with all four changed #820 files.
Targeted validation against D3 83632902 plus G7 96fdcf49 passed:

- D4 rollback file plus G7 shared restore-candidate test: **4 passed,
  2 skipped, 13 subtests passed** (39.39 s). Only CUDA cases skipped on CPU;
  initialization followed by explicit-step restore ran with AdamW and Muon.
- Updated G7 start-mode/candidate/hold-event Python tests: **8 passed** (0.48 s).

The prior full CPU/CUDA evidence remains labeled with its actual 8077cc82 G7
head above; it is not relabeled as a fresh full run against 96fdcf49. No full
POSIX launcher/SLURM test or target-storage validation is claimed here.

Trainer-side D4 is ready for review of this narrowed proposal. Operational D4
remains open until G7 agrees and tests a launcher rollback route, G8/G9 agree
attempt-history handling, and the lead accepts the behavior. Do not treat the
new #820 wording as approval of #847, automated rollback, or the main run.
