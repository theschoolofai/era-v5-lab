# ADR 0003: Node health checks and hang policy

- Status: Proposed
- Date: 2026-10-27 (revised from 2026-10-25; second revision after the week-1 review, see [review_week1.md](../support/docs/review_week1.md))
- Area: Health (`health/health_check.py`, `health/xid_scan.py`, `health/allreduce_test.py`,
  `queue/job_queue.py`, `health/thresholds.yaml`, `slurm/healthcheck.sh`, `slurm/prolog.sh`), hang and
  straggler policy (`support/simulation/trainer/train.py`)
- Related: ADR 0001 (exit codes), ADR 0002 (drain, events, incident records), ADR 0004 (cost, metrics)

> **In simple words.** Most interruptions in big training runs come from broken hardware. A broken GPU
> either crashes the job (we pay for the restart and the lost work) or quietly slows everyone down (we pay
> for every slow hour). So we check every node before it gets a job and every 30 seconds after. A bad node
> is taken out, its job saves and moves to a healthy node, and a frozen job is restarted instead of
> sitting there burning money.

## Context

Llama 3's 419 unexpected interruptions were:

| Cause | Share |
|---|---|
| Faulty GPU | 30.1% |
| GPU memory (HBM) | 17.2% |
| Software | 12.9% |
| Network | 8.4% |
| Host maintenance | 7.6% |
| Other (NIC, SRAM, NCCL timeouts, power) | 22.4% |
| Silent data corruption | 1.4% |

The S15 reference run had 10 of 38 interruptions from GPU or node hardware, 9 from slow storage and 2 from the network.

Session 15 names four tools: DCGM health and Xid alerts; `dcgmi diag` before the run; the PyTorch **NCCL flight
recorder** for hangs; **per-GPU step timing** for stragglers. Its alert table: Xid 79, 94 or 95, or an ECC error
→ page, remove the node. PyTorch aborts a collective after 10 min with no progress.

V4's repository has **no GPU health check at all**. The scripts must run on a laptop (no GPU), on Colab or Kaggle
(no DCGM, no `dmesg`), in the Docker Slurm test, and on the real node.

## Decision drivers

1. Catch a bad node **before** it joins a job, and while a job runs.
2. Turn a hang into a fast restart instead of a 10-minute (or endless) wait.
3. Machine-readable output for the queue (ADR 0002) and Monitoring (Team 08).
4. Never crash, and never claim "pass", because a tool is absent.
5. Prolog-fast: seconds, not minutes.
6. Measured: detection time, false drains and misses are numbers.

## Options considered

| Option | For | Against |
|---|---|---|
| A. DCGM only (`dcgmi health`, `dcgmi diag`) | NVIDIA's own; deep | absent on laptop, Colab, Kaggle and Docker; `diag -r 3` takes minutes; no NCCL test |
| B. A ready-made Kubernetes health agent | less code | we are not on Kubernetes (ADR 0002); hides what is checked |
| C. **Our own small Python checks wrapping nvidia-smi, DCGM if present, a kernel-log Xid scan and an all-reduce test, with one JSON schema, plus runtime rules for hangs and stragglers** | runs everywhere; each check visible and testable | we maintain the Xid table and thresholds |

> **In simple words.** We write small checks ourselves (C), so the same code runs on a laptop and on the
> real cluster, and everyone can see exactly what is checked.

## Decision

**C.**

### 1. Pre-job and periodic checks (`health/health_check.py`)

- Driver and CUDA versions; GPU count against the expected count (`thresholds.yaml: expect_gpus`).
- Per GPU, from `nvidia-smi`: temperature; **ECC uncorrectable** (volatile and aggregate) and the correctable
  count (kept for a trend); hardware-slowdown throttle; PCIe link width against max.
- Row remapping: pending (warn: reset needed) and failure (fail: replace the GPU).
- **NVLink:** any link `<inactive>` in `nvidia-smi nvlink -s` fails the node. A down link raises no error; it only
  halves all-reduce speed for the whole run, and without DCGM nothing else would see it (millermuttu's check, team 07).
- `dcgmi diag -r 1` in prolog mode only (the GPUs are idle before a job) and level 2 in `--mode full`. Periodic
  mode, which runs while training uses the GPUs, reads `dcgmi health -c` instead: DCGM's background watches,
  no extra load. NVIDIA advises against `diag` on busy GPUs, and a false diag "fail" would drain the node and
  requeue the main run over and over (review finding, week 1).
- **Xid scan** (`health/xid_scan.py`): reads `journalctl -k` or `dmesg`, parses `NVRM: Xid (PCI:…): <code>`:

| Class | Codes |
|---|---|
| **fatal → drain** | 48, 61/62, 63/64, 74, **79**, 92, **95**, 119/120, 140 |
| **restart** | **94** (contained ECC): NVIDIA says the application restarts and the GPU stays in service, so one 94 is a warning; a second 94 on the same GPU within 24 h drains the node |
| **warn** | 13, 31, 43 (usually the application, not the GPU) |
| unknown | reported as warn, never ignored |

- **De-duplication:** a hash of every Xid line already seen is stored per node, so an old Xid does not drain a
  repaired node again.
- Clock offset (chrony), free NVMe (ADR 0001 §2), available host memory.
- **Collective test** (`health/allreduce_test.py`, `--mode full`): the four collectives training uses
  (millermuttu's set, team 07): **all-reduce** (data-parallel gradients), **reduce-scatter** (ZeRO-2/3, FSDP gradients),
  **all-gather** (ZeRO-3, FSDP weights) and **all-to-all** (MoE experts). Every value is a small whole number in
  fp32 (all-reduce: `rank + 1`, sum `n(n+1)/2`; all-to-all: chunk `j` of rank `r` holds `r·n + j`), so the result
  is exact in any reduction order; a wrong value means a fault, not rounding. 5 warm-up and 20 timed iterations,
  1 MB to 1 GB. Reports algbw and busbw (nccl-tests convention: ×2(n−1)/n for all-reduce, ×(n−1)/n for the
  others), one check per collective (`nccl_all_reduce`, …). Fails on a wrong value, a timeout, or busbw below the
  floor. Without GPUs it uses gloo and says `backend: gloo`. torchrun reports any failed worker as exit 1, so
  the JSON result, not the exit code, decides.

| Mode | Use | Budget |
|---|---|---|
| `--mode prolog` | quick checks + `dcgmi diag -r 1` before every job | ≤ 30 s |
| `--mode periodic` | Slurm `HealthCheckProgram`: quick checks + `dcgmi health -c` (never `diag`); drains and moves jobs on `fail` | ≤ 30 s |
| `--mode full` | adds DCGM diag 2 and the all-reduce sweep, before dry runs and after a repair | ≤ 15 min |
| `--report-only` | report, take no action | — |

**JSON contract** (also emitted as the `health.report` event, ADR 0002 §8):

```json
{
  "schema": "v5-health/1", "timestamp_utc": "UTC ISO-8601", "time": "(same)", "host": "...",
  "mode": "prolog|periodic|full", "expected_gpus": 8,
  "checks": [{"name": "ecc_uncorrectable", "status": "pass|warn|fail|skipped",
              "required": true, "detail": "...", "metrics": {"values": [0, 0, 0, 0, 0, 0, 0, 0]},
              "gpu": null, "seconds": 0.0}],
  "verdict": "pass|warn|fail", "admit_training": true, "drain_reason": null, "runtime_seconds": 0.0
}
```

- **Team 08's contract (31 Oct).** `v5-health/1` is the format Team 08 validates and loads into ClickHouse
  (lab PR #125). We follow it: check names `gpu_inventory`, `ecc_uncorrectable` (one value per GPU), `xid`
  (`counts` + `events`), collective metrics (`backend`, `world_size`, `status`, `max_error`,
  `all_ranks_correct` per size), and the report fields `timestamp_utc`, `expected_gpus`, `admit_training`.
  *Why:* one format means their dashboards need no Team 07 special case. Two points are open with them:
  `admit_training` stays true on `warn` (a warn is shown, not a stop: a missing optional tool on every node
  would otherwise block the whole run), and a CPU `gloo` collective may pass when the node has no real GPU
  (Docker and CPU test hosts), never on a GPU node.

- A missing tool gives `skipped` with the reason. `skipped` never turns into `pass` or `fail`.
- **Verdict:** any `fail` → `fail`. Otherwise any `warn`, or any `skipped` check marked `required` (GPU checks
  on a GPU node), → `warn`. Otherwise `pass`.

**Exit codes**, aligned with ADR 0001:

- The health CLI uses `0` pass, `3` warn, `4` fail. Codes `1`, `75` and `78` are left to training jobs.
- **In prolog mode a `warn` exits 0**, because Slurm drains any node whose prolog exits non-zero. Only `fail`
  exits non-zero there. (The first draft returned 3 for warn, which would have drained healthy nodes.)
- **Periodic mode drains by itself**: Slurm ignores `HealthCheckProgram`'s exit code, so on `fail` the check
  runs `scontrol update state=drain reason=v5:<checks>` and sends SIGUSR1 to the jobs on the node. They save and
  exit 75, and Slurm restarts them on a healthy node (`queue/job_queue.py`).
- **Full mode reports, the caller drains:** `launch.sh` drains a node whose `--mode full` fails, with reason
  `health: <checks>` (found while planning the merge: it used to report the node as drained without draining it).
- **Slurm starts the prolog and health program with a bare environment.** Both scripts set a full `PATH` first;
  without it, a tool in `/usr/local/bin` is "not found" and its checks report `skipped` instead of failing
  (found by the Docker drill `health_fakes`).

> **In simple words.** "Drain" means "no new work for this node". The job already there is asked to save
> first, so moving it costs seconds, not the work since the last checkpoint.

### 2. Hang and failure policy (runtime)

| Setting | Value | Why |
|---|---|---|
| `TORCH_NCCL_ASYNC_ERROR_HANDLING` | `1` (abort the communicator, raise) | a NCCL error stops the process instead of hanging; the wrapper retries it (ADR 0001 §6) |
| NCCL collective timeout | **10 min** for dry run 1; then **3 × the longest collective measured** in the dry runs, but no lower than the checkpoint and restore collectives need | the PyTorch default, tightened from data |
| `TORCH_NCCL_TRACE_BUFFER_SIZE` | `2000` | NCCL **flight recorder**: the last collectives per rank |
| `TORCH_NCCL_DUMP_ON_TIMEOUT` | `1` | on a timeout, dump the trace that shows which rank stopped (S15) |
| **Step watchdog** | no step completes in `WATCHDOG_S` (production: `max(5 × p99 step time, 10 min)`) → dump all Python stacks → exit **75** | a hang without a NCCL error (data wait, deadlock, a frozen rank) becomes a restart |
| **Straggler rule** | per-rank compute time ÷ median over the last 100 steps > **1.1** → warn; in 3 windows → drain at the next checkpoint, then exit 75 | S15: one slow GPU slows all GPUs. Needs per-rank compute time from the training loop (Team 05/06) |
| **Loss-spike guard** | loss > 1.5 × median of the last 100 steps for 3 steps → no save, exit **78** (ADR 0001 §6) | divergence without NaN is invisible to the NaN check |
| **Alert delivery** | `metrics/watch.py` raises alerts live; Team 08's pager delivers them; Team 07 owns the node action (drain, swap) | one owner per action |

**Silent data corruption:** not covered in V5's first main run. It needs step replay on a second GPU (S15;
Gemini replayed about 0.25% of steps). Recorded as a known gap and revisited after dry run 2.

### 3. Coverage map

| Failure class (Llama 3 share) | Caught by |
|---|---|
| Faulty GPU (30.1%) | Xid scan, DCGM diag, ECC, GPU count, step watchdog |
| HBM (17.2%) | ECC uncorrectable and correctable trend, row remap, Xid 48/63/64/94/95 |
| Network (8.4%) | all-reduce test (busbw floor), flight recorder, NCCL async error handling |
| Software (12.9%) | step watchdog, exit codes, crash-loop cap, loss-spike guard; not prevented |
| Host maintenance (7.6%) | spot / scheduled-event watcher → drain + emergency save (ADR 0002 §5) |
| Storage (S15: 9 of 38) | **not by health checks**: data-wait metric (Q-M9) and checkpoint throughput (CK-11) |
| Silent data corruption (1.4%) | **not covered** (above) |

### 4. Thresholds (`health/thresholds.yaml`)

- Every threshold lives in one file, with its source.
- Until the week-2 baseline exists, thresholds are vendor limits (temperature, power) or `warn` only.
- **Baseline method:** at least 5 `--mode full` runs on known-good nodes.
  - busbw floor = **0.9 × the median** per message size;
  - temperature warn = the vendor slowdown temperature − 5 °C;
  - correctable ECC: warn when the 24 h count exceeds 3 × the fleet median.

## Metrics

All health metrics with LOW / MEDIUM / HIGH thresholds are H-01 … H-24 in `metrics/catalog.yaml`
([metrics_catalog.md](../support/docs/metrics_catalog.md)). The ones that page immediately (HIGH):

| ID | Metric | HIGH when |
|---|---|---|
| H-01 | Fatal Xid | any |
| H-03 | ECC uncorrectable | any |
| H-06 | Row remap failure | any |
| H-07 | GPU missing | any |
| H-08 | GPU at its slowdown temperature | 0 °C margin |
| H-11 | NVLink / fast network link down | any |
| H-12 | All-reduce busbw | ≤ 0.7 × baseline |
| H-13 | Collective wrong value (any of the four) | any |
| H-14 | Step watchdog | ≥ 2 per hour |
| H-15 | Straggler ratio | ≥ 1.25 |
| H-16 | NCCL timeouts | ≥ 2 per hour |
| H-21 | Spot interruption notice | any (automatic save; page if no commit in 90 s) |
| H-22 | DCGM diag failure | any |
| H-23 | Host memory for staging | ≤ 1.0 × need |
| H-24 | Loss-spike guard trip | any |

Targets: detection ≤ 1 health interval for Xid/ECC, ≤ the watchdog limit for hangs; false drains ≤ 1 per week;
prolog ≤ 30 s; full ≤ 15 min.

## Consequences

Good:

- Bad GPUs are removed before they cost a restart, and their jobs move after saving.
- Hangs become restarts in minutes.
- Every node reports the same JSON; detection and miss rates are measured.
- The scripts run on a laptop, Kaggle, Docker Slurm and the cluster.

Bad and accepted:

- Silent data corruption and storage slowness are not caught here (§3).
- The Xid table and thresholds need upkeep.
- `dmesg` may need root, so on the cluster the scan runs in the root prolog and health check.
- The straggler rule and the step watchdog need per-rank timing from the training loop (Teams 05/06).
- A tight NCCL timeout risks killing a slow but healthy save or restore; hence the measured floor in §2.

## Validation

| Where | Test | Result |
|---|---|---|
| `support/tests/test_health.py` (Docker image) | Xid fixture (13, 79, 94, unknown 157): expected classes; the same log again gives no second drain | pass |
| same | nvidia-smi fixture: ECC uncorrectable → fail, hot + throttled → warn, x8 of x16 → warn | pass |
| same | no nvidia-smi on a GPU node → `skipped`, required → verdict `warn` (never pass); on a CPU node → pass | pass |
| same | prolog warn exits 0; periodic warn exits 3; forced fail exits 4 with drain reason; JSON keys match the schema | pass |
| same | four collectives on gloo with 2 and 3 ranks: exact values, busbw > 0; a corrupted all-to-all fails only `nccl_all_to_all` | pass |
| same | Xid 94 once → warn; again on the same GPU within 24 h → fail; after 25 h → warn; Xid 61 → fail | pass |
| same | NVLink: one `<inactive>` link → fail; all up → pass; no NVLink (PCIe card) → skipped | pass |
| Docker Slurm, fake `nvidia-smi`/`dmesg` (millermuttu's fakes) | GPU checks run on every GPU node and pass; planted hot GPU, ECC, row-remap failure, NVLink down, Xid 79 → fail on the right check; Xid 94 → warn; NVLink down is drained by the periodic check (`v5:nvlink`) | pass (drills `health_gpu_checks_run`, `health_planted_faults`, `health_nvlink_drains_node`) |
| `launch.sh` against Docker | NVLink down on one node: full check fails, node drained `health: nvlink`, launch goes on with 2 of 3 | pass |
| Docker Slurm (`support/simulation/run_sim.py`) | forced `fail` on a main-run node: periodic check drains it, job saves, exits 75 and moves to the spare | pass: detect 26 s, 0 steps lost, MTTR 31 s ([sim_results.md](../support/docs/sim_results.md)) |
| Docker Slurm | forced `fail` on **both** main-run nodes with one spare: both drained, main run waits (no crash loop), recovers when they return | see [sim_results.md](../support/docs/sim_results.md) |
| Docker Slurm | `SIGSTOP` on one rank: the watchdog on the other ranks exits 75 with a stack dump; job restarts | pass: watchdog at 20 s, MTTR 24 s ([sim_results.md](../support/docs/sim_results.md)) |
| Kaggle (2 GPUs) (`support/kaggle/run_gpu_checks.py`) | real nvidia-smi values; 2-rank NCCL all-reduce with exact sums and measured busbw; a stuck rank fails cleanly after the NCCL timeout with a flight-recorder trace (`support/kaggle/nccl_timeout_test.py`) | ready, to run (results go in `support/kaggle/results/`) |
| Week-2 node | `--mode full` five times gives the baseline thresholds | week 2 |

## Open points

- The on-call rota: who acts at 4 a.m.?
- Should a `warn` node stay in the main-run pool?
- `HealthCheckInterval` during the main run, and its measured cost in step time.
- Whether V5 adds step replay for silent data corruption after dry run 2.
- Kaggle results (`support/kaggle/run_gpu_checks.py`): real nvidia-smi parsing on Kaggle's GPUs and the NCCL timeout test.
