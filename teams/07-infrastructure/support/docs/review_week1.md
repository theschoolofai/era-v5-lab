# Week-1 review: what the simulation showed, and what the instructor may ask

Team 07, 27 Oct 2026. Companion to ADR 0001–0004. Every item below is marked:

- **FIXED + TESTED**: changed, and a test or drill proves it;
- **DECIDED**: a written decision in an ADR, nothing to run yet;
- **OPEN**: needs something we do not have yet (GPUs, the cloud account, another team), with the reason.

> **In simple words.** We broke a small copy of the cluster on purpose, many times, and wrote down what
> happened. Then we listed the basic questions an instructor would ask about running a paid GPU training job,
> checked each against our design, and fixed what we could test on a laptop.

## 1. What the simulation shows

Setup: a Docker Slurm cluster with two controllers, the accounting database, an **S3 emulator** (the real S3
code runs against it), three "GPU" nodes with two placeholder GPUs each (allocation and accounting only; no
computation) and one eval/CPU node. The main run uses 2 nodes × 2 ranks; the third node is the hot spare. The
tiny model trains at about 50 ms per step and saves every 8 s. Latest results: [sim_results.md](sim_results.md).
The kit lives in `support/simulation/` (optional; see [support/simulation/README.md](../simulation/README.md)).

**Latest full run (run 11, 29 Oct 2026): 31 of 31 drills pass in 30 minutes**, with every fix from the
week-1 check-in review (§2b): async save, logical fingerprints, crash count in S3, node-local logs,
`cred_expire=60` (run 10: 31 of 31 on the new layout; run 9 adds `held_job_explains_itself`; run 8: 30 of 30).

| Fault injected | What happened | MTTR p50 (n) | Work lost |
|---|---|---|---|
| kill a training process | wrapper turns the crash into "retry"; requeued; restored from the last commit | 50 s (3) | 24–45 steps (since last save) |
| preemption signal (SIGUSR1) | emergency save, exit 75, requeued | 58 s (3) | 0 |
| kill **during** a save | the half-uploaded checkpoint is never used; previous commit restored | 50 s | since previous commit |
| kill **during** a restore | next attempt restores the same checkpoint, no failure | 112 s | 0 extra |
| spot notice | node drained, emergency save, job moves to the spare | 57 s | 0 |
| fake GPU failure | health check drains within one interval; save; job moves | 60–88 s | 0 |
| two nodes down, one spare | main run waits (no crash loop); recovers when nodes return | 58 s after repair | — |
| frozen process (hang) | watchdog fires at 20 s; restart | 56 s | 44 steps |
| node unplugged | Slurm marks it down after ~30 s; requeued on remaining nodes | 88 s | 24 steps |
| controller stopped | backup takes over in 82 s; training never stops; new jobs accepted | — | 0 |
| NaN, loss spike | nothing bad saved; job held; rollback on a new branch, on half the GPUs | rollback 3 s | — |

Also passing: accounts (no account → rejected), preemption of team jobs (they save first), GPU allocation
(`gres/gpu=4`, over-ask refused), crash-loop hold, DB backup + test restore (31 of 31 tables), budget limit,
fair share, GPU-minutes per account (main run 32.4 GPU-min in run 9), retention on S3 (no protected checkpoint deleted), safetensors export
(bit-equal probe), live alerts (23 fired, including every drill-caused HIGH).

**Why MTTR is ≈ 85 s now (it was 3–57 s in run 3):** most of it is Slurm's requeue wait. Our earlier
"restart immediately" fix lost the main run in run 7 (see §2), so we use Slurm's supported setting
`cred_expire`. Run 10 used 30 s (MTTR ≈ 55 s); the review showed that leaves no margin for a 30 s prolog, so
run 11 uses 60 s (reschedule 90 s, MTTR 85 s). About 90 s per restart is the price of never losing the run; at
8 nodes that is ≈ $23 per restart (assumed prices), small next to the work lost per failure.

Reporting gap found in run 8 and closed in run 9: GPU-minutes counted only the last segment of each requeued job
(`sacct` without `-D`), so `mainrun` showed 0.2 GPU-minutes. With `-D`, run 9 shows 32.4.

How to read the goodput number in the report: the simulation injects a fault about every half minute, while a
real run sees one every few hours to days. So "useful share of time" is low **by design of the test**. What
matters is each step's duration (detection, reschedule, restore), which `support/cost/cost_model.py --measured`
projects onto real failure rates.

## 2. Bugs we found and fixed during the simulation

| Found | Effect | Fix | Status |
|---|---|---|---|
| Slurm holds every requeued job ≈ 121 s (`BeginTime`) | ≈ 2 min of the whole cluster idle on every restart | `AuthInfo=cred_expire=60` (≈ 90 s, safe, prolog margin; was 30 s ≈ 50 s) | FIXED + TESTED |
| our first fix for that (force an immediate start) | run 7: the job started while the old credential was valid, Slurm killed it ("credential revoked") and marked it FAILED: **main run lost** | hack removed; replaced by the row above | FIXED + TESTED |
| `OMP_NUM_THREADS` changes the loss bits on CPU | a bit-equal restore check fails for the wrong reason | set in job scripts; recorded in the manifest | FIXED + TESTED |
| torchrun turns a stop signal into exit 1 | preemption counted as a crash | trainers run under `srun` | FIXED + TESTED |
| a drill's `pkill` matched its own shell | the test froze | `[t]rain.py` pattern | FIXED |
| the rollback argument was not shell-quoted | rollback drill could not submit | quoted | FIXED + TESTED |
| a 3rd kill within 30 min held the main run | the crash-loop cap **works**; the drills were too close in compressed time | crash-loop window scaled to the simulation's timescale (10 s) | FIXED + TESTED |
| report: "8 interruptions per day" was 8 in 10 min | wrong alert level | rates divide by the observed window | FIXED + TESTED |
| report: one hang counted once per rank | watchdog rate tripled | one count per hang | FIXED + TESTED |
| report: the drill switch counted as a real Xid | H-01 false positive | H-01 counts only real Xid lines | FIXED + TESTED |
| catalog: an unquoted comma in two metric names (CK-05, Q-06) broke their YAML entry | names cut short in pages | quoted; test added | FIXED + TESTED |
| health: on new drivers the renamed-field retry was ignored | a healthy GPU node reported "nvidia-smi failed" and drained | retry result used; test added | FIXED + TESTED |
| report: test-caused alerts not marked | readers think production is broken | column "Caused by the test?" (yes / fault rate / no) | FIXED + TESTED |

## 2b. Findings from the week-1 check-in review, and what changed

The review read the code against the ADRs. Each finding was right; none showed up in the simulation, because the
test trainer uses DDP (every rank holds a full copy) and the Docker cluster shares one `/s3` volume.

| # | Finding | Fix | Proof | Status |
|---|---|---|---|---|
| R1 | Save deadlocks under FSDP: the probe forward and the digest ran on rank 0 only | every rank runs the probe, the fingerprint and the loader check together, before the async copy (`ckpt.py` `save`) | T16: FSDP2 save + restore on 2 GPUs (Kaggle); T17: sharded digest on gloo | **FIXED**; T17 tested, T16 runs on Kaggle |
| R2 | Digest covered only rank 0's shard, so it would fail after any reshard | logical fingerprint: each rank adds its shard weighted by position in the full tensor, one all-reduce; the same at any world size (ADR 0001 §8) | T14 (uneven rows, columns, 5 dtypes, swapped row, one bit), T17 (real DTensors, 2 and 3 ranks) | **FIXED + TESTED** |
| R3 | Async save claimed, blocking `dcp.save` used; sha256 of the whole state on the stall path | `dcp.async_save` on its own gloo group; the stall ends at the host copy; integer fingerprint on the GPU replaces sha256 (`V5_ASYNC_SAVE=0` for the old path) | all checkpoint tests and every drill run with it; stall on Kaggle's GPUs from `bench_save.py` | **FIXED + TESTED** (GPU stall number: Kaggle) |
| R4 | "No shared FS" but logs, events and the crash counter needed `/s3` | crash count → `crashes.json` in the run's S3 folder, rewritten whole (no append); logs/events/exit notes → node-local `/var/log/v5`, shipped by the log agent | `test_queue.py` (count survives 3 different nodes, no append, S3 down → retry + event); crash-loop drill in run 11 against the S3 emulator | **FIXED + TESTED** |
| R5 | `dcgmi diag -r 1` ran every 30 s on busy GPUs: a false fail requeues the main run in a loop | periodic mode reads `dcgmi health -c` (DCGM's watches, no load); diag only in prolog (idle GPUs) and full mode | `test_health.py`: periodic calls only `health -s a` / `health -c -j`, prolog calls `diag -r 1` | **FIXED + TESTED** (real DCGM: week-2 node) |
| R6 | A resharded restore gives every rank rank 0's loader state: wrong for per-rank loaders | contract now requires one global ledger offset, identical on every rank, and tests a resume at another world size; every save records `loader_global`; a resharded restore without it stops with `ReshardError` (78) and says what to do | T13 (our loader passes, also resharded), T15 (a per-rank loader fails) | **FIXED + TESTED** |
| C1 | `SuspendExcNodes=gpu-[1-9]:1` may count busy nodes, so no spare is kept | not depending on it: `job_queue.py keep-spare` every minute names the spare node (`SuspendExcNodes=<node>`) and boots one if none is free; `ReconfigFlags=KeepPowerSaveSettings` | `test_queue.py` (busy main-run nodes are never the spare; nothing free → power up); man page checked: says "powered up", silent on busy | **FIXED**; unit-tested, real power saving needs the cloud |
| C2 | `cred_expire=30` with a 30 s prolog budget leaves no margin | `cred_expire=60` (2 × prolog budget); man page: the lifetime must cover "run prolog" | run 11: 31 of 31, every requeue succeeds; reschedule 57 → 90 s, MTTR 55 → 85 s; Q-03 LOW raised 60 → 120 s so a normal restart does not alert | **FIXED + TESTED** |

## 3. Questions the instructor may ask, and our answer

### A. Would it work on day 1 on cloud nodes?

| # | Question | Answer | Status |
|---|---|---|---|
| A1 | How does a job get its GPUs, and only its GPUs? | `GresTypes=gpu`; the cloud `gres.conf` `AutoDetect=nvml`; `cgroup.conf` `ConstrainDevices=yes`; job scripts ask `--gpus-per-node=8`; GPU-hours recorded per account (`AccountingStorageTRES=gres/gpu`). Drill: main run allocated `gres/gpu=4`; over-asking refused | FIXED + TESTED (Docker placeholders) |
| A2 | Where is the S3 code? | `ckpt/store.py` `S3Store` (boto3, multipart, retries, SHA256 checksums). All checkpoint tests also pass against the S3 emulator, and every drill saves to it | FIXED + TESTED (emulator) |
| A3 | Is the node's disk persistent? | Not always: a node's local NVMe can be wiped when it stops or is replaced. It is a cache only; restores always work from the shared store | DECIDED (ADR 0001 §2) |
| A4 | Does the same config run in Docker and on cloud nodes? | yes: one `slurm.conf`; four small files differ (`site`, `nodes`, `gres`, `cgroup`) | FIXED |
| A5 | What runs on cloud nodes that the Docker test cannot show? | real GPUs and NCCL, the fast network, Pyxis/Enroot, power saving, cloud identity | OPEN: Kaggle kit for GPUs; cloud account for the rest |

### B. What happens when things fail?

| # | Question | Answer | Status |
|---|---|---|---|
| B1 | A process, a node, a GPU fails | drills: kill, node loss, health fail, spot notice, hang; each restarts by itself from the last commit | TESTED |
| B2 | Two nodes fail and there is one spare | main run waits (no crash loop), Q-01 pages at 10 min; recovers when nodes return; no automatic shrink (decided: a smaller world is not bit-equal and needs a person to agree) | TESTED + DECIDED |
| B3 | The process dies **during** a save | the half-uploaded checkpoint is never used; restore uses the previous commit | TESTED |
| B4 | The process dies **during** a restore | next attempt restores the same checkpoint cleanly | TESTED |
| B5 | The Slurm controller dies | backup controller takes over; training continues; new jobs accepted; primary returns | TESTED |
| B6 | The accounting database is lost | daily dump; a backup counts only after a test restore with the same tables | TESTED |
| B7 | The loss spikes without a NaN | spike guard: > 1.5 × median for 3 steps → no save, hold (78), rollback | TESTED |
| B8 | NaN | no save, hold (78), rollback with skip and new branch | TESTED |
| B9 | A job crashes again and again | 3 crashes in 30 min → hold; also caught the main run in run 4 | TESTED |
| B10 | S3 is slow or down | uploads retry (boto3 standard mode); a save that cannot commit is `checkpoint.failed`, CK-03 pages after 2 in a row; training continues meanwhile | DECIDED; slow-S3 drill OPEN |
| B11 | Silent data corruption | not covered in the first main run; step replay considered after dry run 2 | OPEN (known gap, ADR 0003 §2) |

### C. Operations

| # | Question | Answer | Status |
|---|---|---|---|
| C1 | How does a person get woken up? | `metrics/watch.py` raises `alert.fired` live and posts to a webhook (Team 08's pager). HIGH pages | FIXED + TESTED (fired live in the simulation) |
| C2 | How is cost tracked per team? | Slurm GPU-minute budgets per account; cloud cost tags `v5:team/role/run/cluster` + the cloud's budget alerts at 50/75/90% | DECIDED; Budgets need the account |
| C3 | What if an instance runs outside Slurm? | `support/cost/find_unmanaged.py`: C-05 HIGH with dollars per day; untagged instances listed | FIXED + TESTED (fixtures) |
| C4 | What if someone deletes the bucket? | versioning; only the retention role may delete; protected checkpoints replicated to a second region (deletes not replicated) | DECIDED (ADR 0001 §5) |
| C5 | How do you upgrade image / driver / Slurm mid-run? | at a checkpoint: emergency save → roll nodes → requeue with `--allow-env-change` (logged); Slurm dbd → ctld → slurmd | DECIDED (ADR 0002 §11) |
| C6 | Where are the logs? | node-local, shipped to S3 by Team 08's agent; 90 days, then the archive tier | DECIDED |
| C7 | Security | cloud role per job type, no keys, session manager only, munge key from the cloud secrets store, pr-guard + gitleaks | DECIDED; needs the cloud account |

### E. Monitoring: can people act on what they see?

| # | Question | Answer | Status |
|---|---|---|---|
| E1 | A held job shows `SPECIAL_EXIT / JobHeldUser`. How does anyone know why? | the wrapper writes the cause and next step into the Slurm job comment, the job log and the events (`V5 HELD (78): NaN at step 5595 … Do: roll back …`) | FIXED + TESTED (drill `held_job_explains_itself`) |
| E2 | What does exit 137, `IntegrityError` or `v5:xid` mean? | `python metrics/explain.py <anything>`; all on one page in [codes_and_actions.md](codes_and_actions.md) | FIXED + TESTED |
| E3 | Does a page say what to do? | every alert carries why, action, response time, owner, and the explain command | FIXED + TESTED (live alerts) |
| E4 | Can a new cause be added without an explanation? | no: `support/tests/test_monitoring.py` fails | FIXED + TESTED |
| E5 | How does Team 08 consume it? | events (JSON lines), the webhook, `metrics.json`; guide and dashboard panels in [metrics/README.md](../../metrics/README.md) | DECIDED; their store and pager are Team 08's |

### D. Evidence quality

| # | Question | Answer | Status |
|---|---|---|---|
| D1 | Each drill ran once? | kill and SIGUSR1 run 3 times each; the report gives MTTR p50 / p95 / max per fault type | FIXED + TESTED |
| D2 | A 1 MB checkpoint proves nothing about speed | `support/tools/bench_save.py` measures GPU-to-host and save speed; on Kaggle's GPUs now, on the GPU node in week 2 | OPEN (Kaggle run pending) |
| D3 | Resharding is the easy DDP case | yes; FSDP/ZeRO-3 and expert-parallel resharding need Team 05's model | OPEN (week 2, ADR 0001 open points) |
| D4 | The data loader is synthetic | `ckpt/loader_contract.py`: the test Teams 01/02's real loader must pass (save, resume, peek, skip); ours passes | FIXED; real loader OPEN (Teams 01/02) |
| D5 | Prices are guesses | `metrics/prices.yaml` says so (`checked: null`); decisions rest on ratios | OPEN: check on the provider's price list |

## 4. Still open, with owner

| Item | Needs | Owner |
|---|---|---|
| GPU behaviour (NCCL, nvidia-smi, CUDA bit-equal, save speed) | Kaggle run (`support/kaggle/run_gpu_checks.py`) | Team 07 |
| the fast network, Pyxis/Enroot, power saving, cloud identity, the cloud's budget alerts, real S3 throughput | the cloud account and the week-2 node | Team 07 + instructor |
| Sharded-state resharding (FSDP/EP) | Team 05's model and parallel layout | Team 05 + 07 |
| Real data-loader state | the loader passing `ckpt/loader_contract.py` | Teams 01/02 |
| Slow-S3 drill, silent data corruption | after dry run 1 | Team 07 |
| Real prices, reserved capacity booking | the provider's price list, booking | Team 07 + lead |
| On-call rota and alert channel | people | lead + Team 08 |
