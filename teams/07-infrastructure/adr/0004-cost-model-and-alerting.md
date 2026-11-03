# ADR 0004: Cost model, purchase options and severity-tiered alerting

- Status: Proposed
- Date: 2026-10-27 (revised after the week-1 review, see [review_week1.md](../support/docs/review_week1.md))
- Area: Cost (`support/cost/cost_model.py`, `metrics/prices.yaml`), metrics and alerts (`metrics/catalog.yaml`,
  `metrics/evaluate.py`, `support/docs/metrics_catalog.md`)
- Related: ADR 0001 (checkpoint), ADR 0002 (queue, goodput), ADR 0003 (health)

> **In simple words.** GPU time is the biggest cost of the lab. A node-hour is wasted when GPUs wait (a save
> pause, a restart, a hang, an idle node) or when work has to be redone (training since the last checkpoint).
> This ADR decides how we buy GPU time, how we count waste in node-hours, and which numbers wake
> somebody up at night (HIGH), which wait until the morning (MEDIUM), and which wait for the weekly review (LOW).

## Context

- We will run on cloud GPU nodes (proposed `gpu-node-8`, 8 GPUs) through Slurm (ADR 0002).
- **Costs are counted in node-hours** (one GPU node for one hour). Waste and risk in node-hours do not depend on a
  price; cost = node-hours × the price of one node-hour. The price is an **input with no value in the repo**
  (`price_per_node_h` in `metrics/prices.yaml`, or `--price-per-node-h` / `V5_PRICE_PER_NODE_H` at run time).
  A 2-node run uses 48 node-hours per day, an 8-node run 192.
- V4 lost GPU time in ways nobody measured: a cluster idle for 3 days, hand-typed restarts, a run continued on a
  silently misloaded checkpoint.
- Model sizes are still open (`config_v0.yaml`, 31 Oct), so the checkpoint size is a range: 12 bytes per
  parameter (fp32 master + AdamW m and v) gives 12 GB at 1B, 84 GB at 7B and 360 GB at 30B.

## Decision drivers

1. Every node-hour of waste has a name (bucket) and an owner.
2. GPU time already spent (in checkpoints) is never lost by our own mistake.
3. A person is paged only when acting now saves GPU time or protects a checkpoint; everything else waits.
4. Decisions use measured numbers where we have them (simulation, dry runs) and labelled assumptions otherwise.

## Decision

### 1. Where the GPU time goes: the cost model

> **In simple words.** Waste per hour ≈ (save pause ÷ interval) + (half an interval + restart time) ÷ time
> between failures. Multiply by the number of nodes and you get node-hours; multiply by a price and you get cost.

```text
waste share  = stall/interval + (interval/2 + MTTR) / MTBF_job
MTBF_job     = (GPU-hours per interruption) / GPUs          # more GPUs, more failures
node-hours per useful hour  = nodes / (1 − waste share)
node-hours lost per failure = nodes × (interval/2 + MTTR)
cost = node-hours × price per node-hour                     # price: an input, no value in the repo
```

`support/cost/cost_model.py` evaluates this for 1B / 7B / 30B parameters on 2 / 4 / 8 nodes with the S15 and Llama 3
failure rates, and writes `support/cost/cost_report.md`. Main results (S15 failure rate):

| Size, nodes | Checkpoint | Best interval | Lost per failure | Waste per day | Waste share |
|---|---|---|---|---|---|
| 7B, 2 nodes | 84 GB | 30 min (RPO cap) | ≈ 0.55 node-h | ≈ 0.04 node-h | 0.09% |
| 7B, 8 nodes | 84 GB | 8 min (Young) | ≈ 0.72 node-h | ≈ 0.2 node-h | 0.10% |
| 30B, 8 nodes | 360 GB | 17 min (Young) | ≈ 1.3 node-h | ≈ 0.37 node-h | 0.20% |

The checkpoint itself is cheap: the stall is under 4 s at these sizes (assumed 50 GB/s GPU-to-host per node),
and the store holds 3 recent checkpoints (36–1,080 GB) plus the protected ones. **Restarts and idle GPUs waste far
more node-hours than saves**, so the design spends effort on fast, automatic restarts and on never letting paid GPUs idle.

### 2. Checkpoint decisions driven by cost

| Decision | Why, in GPU time |
|---|---|
| Interval = `min(Young, eval cadence, 30-min RPO cap)`, start 30 min | a failure costs ≈ half an interval of the whole cluster; the cap bounds that at ≈ 15 min of cluster time |
| Emergency save on every warning (preemption, spot, health drain) | a warned interruption then loses seconds, not ≈ 15 min (measured in the simulation) |
| Commit only after every file is re-checked; manifest last; `latest.json` moved last | a damaged checkpoint can never waste a restart or, worse, a whole run on a misload |
| Automatic fallback to the previous commit | no person needed at 4 a.m. to pick a checkpoint |
| Protected checkpoints, S3 versioning, delete only by the retention role | the GPU time in a checkpoint cannot be deleted by a training bug |
| Keep 3 recent in S3 Standard, protected ones to the archive tier after X days; abort incomplete uploads after 1 day | storage is billed monthly; old and orphan objects are the only storage waste |
| Same region and zone for nodes, bucket and eval, a private storage endpoint | no data-transfer charges on checkpoint traffic |

### 3. Purchase options

> **In simple words.** Spot instances are much cheaper per hour, but the cloud can take them back with 2 minutes
> notice, and the whole multi-node job stops when any one node goes. On-demand costs more but stays.

| Use | Purchase | Why |
|---|---|---|
| Main run | **on-demand, or a reserved capacity booking** booked for the run | the model says spot is cheaper per useful hour *if* capacity exists, but whole 8-GPU nodes are rarely available as spot, and a reclaim can leave the run waiting for capacity that never comes. A reserved capacity booking gives a fixed price and guaranteed nodes for the booked window |
| Hot spare | on-demand, **running preemptible team jobs** | the model shows the spare's saved restart time (≈ 15 min per failure) saves fewer node-hours than the spare uses at S15 failure rates; its value is that the run never waits for capacity. Letting it run team work recovers most of its cost |
| Team ladder runs, benchmarks | spot where available, else on-demand in `teams` | they save on SIGTERM (ADR 0002) and lose only seconds when reclaimed |
| Eval, quantization | smaller, cheaper GPU nodes (`eval` partition) | never the training node; a smaller node |
| CPU jobs (data, retention, export) | small on-demand or spot CPU instances | no GPU needed |
| Idle nodes | stopped by Slurm power saving after 10 min (`SuspendTime=600`), one spare kept up | an idle GPU node is billed every hour for nothing |

### 4. Severity tiers

> **In simple words.** HIGH means GPU time is burning right now or a checkpoint is in danger: wake someone.
> MEDIUM means it gets more expensive the longer we wait: fix it today. LOW means it is a trend: look at it
> in the weekly review.

| Severity | Meaning | Response | Who |
|---|---|---|---|
| **HIGH** | paid GPU time is being wasted now, or a checkpoint (GPU time already spent) is at risk | page now, 24×7, acknowledge ≤ 15 min | Team 07 on-call; Team 08 delivers the page |
| **MEDIUM** | degraded; cost grows if nobody acts | fix the same working day (≤ 4 h) | Team 07 |
| **LOW** | a trend or a small inefficiency | weekly ops review | Team 07 + lead |

Each metric has up to three thresholds, and the highest one crossed sets the severity. For example, time since
the last commit is LOW at 1.2 × interval, MEDIUM at 1.5 × and HIGH at 2 ×.

### 5. The catalog

`metrics/catalog.yaml` is the single source: **74 metrics** in four areas (checkpoint 20, queue 21, health 24,
cost 9), each with its unit, direction, LOW / MEDIUM / HIGH thresholds, a plain-words "why it matters", the
action, and the owner. [metrics_catalog.md](../support/docs/metrics_catalog.md) is generated from it
(`python metrics/evaluate.py --render-md support/docs/metrics_catalog.md`), so the two never disagree.
`metrics/evaluate.py` computes every metric it can from the events and checks the thresholds; 41 metrics are
computable from the Docker simulation, and the rest need real GPUs or the cloud account (marked `sim: false`).

HIGH alerts, all areas:

| Area | HIGH alerts |
|---|---|
| Checkpoint | CK-01/02 time or node-hours at risk ≥ 2 intervals · CK-03 2 failed saves in a row · CK-04 checksum mismatch · CK-05 restore check failure · CK-06 strict-load / environment refusal · CK-07 NaN guard · CK-08 stall ≥ 5% · CK-09 commit latency ≥ 20 min · CK-12 NVMe headroom ≤ 1.2 · CK-13 restore ≥ 30 min · CK-14 lost work ≥ 2 intervals · CK-15 protected checkpoint missing |
| Queue | Q-01 main run pending ≥ 10 min · Q-02 main run held · Q-03 reschedule ≥ 10 min · Q-05 ≥ 10 interruptions/day · Q-06 idle GPU ≥ 4 node-h/day · Q-07 allocated but not stepping ≥ 15 min · Q-09 drained ≥ 3 · Q-10 node replacement ≥ 15 min · Q-11 slurmctld down · Q-15 budget ≥ 90% · Q-17 clock offset ≥ 500 ms · Q-19 goodput ≤ 80% · Q-20 MTTR ≥ 60 min |
| Health | H-01 fatal Xid · H-03 ECC uncorrectable · H-06 row remap failure · H-07 GPU missing · H-08 at slowdown temperature · H-11 NVLink / fast network down · H-12 busbw ≤ 0.7× · H-13 wrong all-reduce · H-14 watchdog ≥ 2/h · H-15 straggler ≥ 1.25 · H-16 NCCL timeouts ≥ 2/h · H-21 spot notice · H-22 DCGM fail · H-23 host memory ≤ need · H-24 loss-spike guard |
| Cost | C-01 burn ≥ 1.25 × plan · C-02 node-hours per useful node-hour ≥ 1.25 · C-03 waste ≥ 20% · C-04 one incident ≥ 3 intervals of node-hours · C-05 instance running outside Slurm · C-06 budget days ≤ 0.8 × training days left |

### 6. Live alerting and cost tracking (added after the week-1 review)

- **Live alerts:** `metrics/watch.py` recomputes the catalog every 30 s from the events and, when a metric reaches
  a new severity, writes `alert.fired` and posts to `V5_ALERT_WEBHOOK`. HIGH sets `page: true`. In the simulation
  it runs during all drills, and the drill-caused HIGH alerts must fire (drill `live_alerts`).
- **Every alert says what to do:** the payload carries `why`, `action`, `respond` (how fast), `who`, and
  `explain` (`python metrics/explain.py <id>`). `metrics/explain.py` explains any exit code, cause, alert id,
  drain reason or Slurm reason; `support/tests/test_monitoring.py` fails if the code can report something without an
  explanation. Guide for Team 08 and on-call: [metrics/README.md](../metrics/README.md).
- **Rates are scaled:** per-day and per-hour metrics divide by the observed window (the first report printed raw
  counts as "per day"). In the simulation report, alerts caused by the injected fault rate are marked
  "fault rate", and alerts a drill causes on purpose are marked "yes".
- **Cost tags** on every instance: `v5:cluster`, `v5:role` (gpu / eval / cpu / head), `v5:team` (Slurm account or
  `shared`), `v5:run`. They are activated as **cost allocation tags**, so the cloud bill and **the cloud's budget alerts** split by
  team, with alerts at 50 / 75 / 90% (same as the Slurm `GrpTRESMins` budgets, which now count GPU-minutes via
  `AccountingStorageTRES=gres/gpu`).
- **Instances outside Slurm** (C-05): `support/cost/find_unmanaged.py` compares running cloud instances with Slurm's node
  list. A running instance Slurm does not know, or one Slurm thinks is powered down, is HIGH, with the node-hours it
  burns per day; an instance missing a cost tag is reported. Tested on fixtures (`support/tests/test_cost.py`); runs against the
  cloud's instance list once we have the account.

### 7. Simulation findings that changed the design

| Finding | Cost effect | Change |
|---|---|---|
| Slurm delays every requeued job by ≈ 121 s (`PENDING (BeginTime)`) | ≈ 2 min of the whole cluster idle per restart (≈ 0.07 node-h on 2 nodes; ≈ 0.27 on 8) | `AuthInfo=cred_expire=60`: ≈ 90 s, safe, and it covers a 30 s prolog twice over (`cred_expire=30` gave ≈ 50 s but no prolog margin, week-1 review). A faster hack (force start, ≈ 4 s) lost the main run in run 7 ("credential revoked" → FAILED) and was removed: a cheaper restart is not worth a lost run (ADR 0002 §5) |
| `OMP_NUM_THREADS` changes the loss bits on CPU | a "bit-equal" resume check would fail for the wrong reason and block a restart | job scripts set it; the manifest records it (ADR 0001 §1) |
| A drill's `pkill -f 'train.py …'` matched its own shell and froze the test | none in production, but the same trap applies to any ops script | ops scripts use the `[t]rain.py` pattern |
| torchrun turns SIGTERM into exit 1 for the workers' parent | a preempted job would be counted as a crash | trainers run under `srun`, which forwards signals; the wrapper maps exits (ADR 0002 §5) |

## Consequences

Good:

- Every node-hour of the main run is in a named bucket in `support/simulation/results/report.md` today and in
  the dry-run reports later.
- Paging is limited to events where acting now saves GPU time or protects a checkpoint.
- Purchase decisions are written down with their reason, and can be revisited by re-running the model with a real
  price as input.

Bad and accepted:

- **No price is in the repo.** Results are in node-hours; a money figure needs the price given at run time. The
  decisions depend on ratios (waste share, the spot break-even ratio), not on the price.
- The failure rate (MTBF) is a prior from published runs until our own incident records replace it after the dry runs.
- 33 of the 74 metrics cannot be tested until we have GPUs and the cloud account.
- A reserved capacity booking must be booked ahead and is paid whether or not we use it, so the run plan must be ready in time.

## Validation

- `support/cost/cost_model.py` runs and writes `support/cost/cost_report.md`; with `--measured support/simulation/results/metrics.json` it uses
  the MTTR measured in the simulation.
- `support/simulation/run_sim.py` runs every drill and `metrics/evaluate.py`; each injected fault must raise its expected alert
  (column "Caused by the test?" in `support/simulation/results/report.md`), and `metrics/watch.py` must fire them live.
  See [sim_results.md](../support/docs/sim_results.md).
- `python -m pytest support/tests/test_cost.py`: the unmanaged-instance check and the cost-model formulas.

## Open points

- The price of a node-hour (an input, kept out of the repo); reserved capacity booking availability for the GPU node.
- The lab's total GPU budget and the capacity calendar (needed for C-01 and C-06).
- Who receives HIGH pages (on-call rota) and through which channel (Team 08).
