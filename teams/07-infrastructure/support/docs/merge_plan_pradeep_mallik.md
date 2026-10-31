# Team 07: Pradeep's and Mallik's work compared, and one merged submission

> **Superseded for decisions by [team07_merge_plan.md](team07_merge_plan.md)** (Pradeep + Mallik + Max in one
> page). This file stays as the detailed review behind it.

Compared: this repo (`pradeep-kumar-gs/era-v5-lab`, branch `infrastructure`, commit `fd0f59b`) and Mallik's
(`millermuttu/era-v5-lab`, branch `07-infrastructure`, commit `c6e38a3`, 28 Oct 2026). Written 30 Oct 2026.

**Target agreed for this plan: the TSAI shared GPU node(s)**, from 1 Nov: one (or a few) GPU nodes, with
every Slurm daemon on the node, and S3 keys held by TSAI. Not a self-managed EC2 fleet. That choice decides most
of the queue recommendation below.

> **In simple words.** Mallik's repo is small, clear and built for the node we will actually get. Ours is
> large and goes much further, mostly on the checkpoint, on what happens after a failure, and on monitoring, but
> parts of it assume an AWS fleet we will not have. The best submission keeps **our checkpoint, job contract,
> monitoring and launch script**, takes **Mallik's single-node Slurm setup, GPU-share accounts, four-collective
> network test, NVLink check and fast smoke test**, and parks our EC2-only parts in `support/` for later.

## How this was checked

- Every file of both repos was read. Ours was also run: 56 unit tests pass (2 GPU-only skipped), and the Docker
  drills passed 32 of 33 in run 13 (the one failure found a real bug, since fixed; run 14 is in progress).
- **Mallik's tests were not run here.** Running code downloaded from another repo was blocked by this
  machine's safety settings, so everything said about Mallik's code comes from reading it. His README says
  `test.sh` passes in about 90 s and `ckpt.py` self-test passes; that is his claim, not checked here.

## Size

| | Code (py, sh, conf) | Docs (md) | Tests |
|---|---|---|---|
| Pradeep | 7,317 lines (4,327 in `submission/`) | 4,501 lines | 30 unit tests (T1–T27 + store/health/cost/queue suites), 33 Docker drills, Kaggle GPU script |
| Mallik | 847 lines | 338 lines | `ckpt.py` self-test, `xid_scan.py` self-test, `test.sh`: 13 Slurm checks in ~90 s |

A reviewer can read all of Mallik's work in an hour. Ours needs a day. That matters for a course submission,
so the merged `submission/` should be leaner than ours is today (see "Merged layout").

## Area by area

Legend: **P** = Pradeep, **M** = Mallik. "Keep" is the recommendation for the merged submission.

### 1. Checkpoint

| Aspect | P | M | Keep |
|---|---|---|---|
| Format | PyTorch DCP shards + per-rank JSON (RNG, loader) + MANIFEST; DeepSpeed backend too | PyTorch DCP shards + `rank<N>.pt` + `meta.json` | **P** (both DCP; P also has DeepSpeed ZeRO 1/2/3) |
| Commit rule | all ranks upload → sums per rank → re-check every object → MANIFEST last → conditional `latest.json` | write `step_N.tmp/`, barrier, `COMPLETE` last, rename | **P**. M's rename works on one disk but not on S3 (M's own doc says so) |
| Finding the newest | `latest.json` pointer + `commits.jsonl` history | list folders, pick newest with `COMPLETE` | **P**: no listing, and history gives a fallback order |
| Damaged newest checkpoint | sha256 per file; falls back to the previous commit by itself | no checksums; a damaged newest checkpoint fails to load and the job stops | **P** |
| Proof the restore is right | state digest (reshard-safe), probe-loss bits, next-batch hash, frozen fingerprints | strict keys (missing keys raise), `meta` equality, frozen hash | **P**, plus one idea from M (below) |
| Frozen parameters | fingerprint saved, checked at restore | **refuses to save** if a frozen part changed since the previous checkpoint | **Add M's rule to P**: check at save against the previous commit, so the error shows up the moment training touches a frozen part, not at the next restore |
| What `meta` covers | git sha, image digest, torch/CUDA/NCCL, config sha, tokenizer sha, `OMP_NUM_THREADS`, DeepSpeed config | config sha, tokenizer sha, **embedding policy id** | **P + add `embedding_policy_id`** from M (Team 04's KE2 policy) |
| RNG | Python, NumPy, torch CPU, CUDA of every local GPU, per rank | Python, torch CPU, current CUDA device | **P** (M misses NumPy and other local GPUs) |
| Different number of GPUs | reshards; RNG reseeded per rank; refuses if the loader keeps per-rank positions (`ReshardError`) | reshards; ranks without a file read `rank0.pt`, so **every new rank gets rank 0's RNG** (identical dropout streams) | **P** |
| Data position | contract in `loader_contract.py`: one global ledger offset + skip list, checked at every save | proposal in DESIGN.md: global sample count, ledger offset, **shard manifest sha** checked at restore | **P's contract + M's `manifest` field**: a different shard list must stop the run |
| Async save | `dcp.async_save`, own copy of CPU tensors (bug found and fixed, T27) | not built (listed as "not built yet") | **P** |
| Remote storage | S3 through `store.py`, tested on an S3 emulator, conditional writes | local/shared disk only; S3 "week 2" | **P** |
| Two copies of a run alive | epoch fencing: the old one cannot commit (T24–T26, drill `split_brain`) | not handled | **P** |
| Retention | own job/role, never deletes protected or pinned, orphans after 1 h | inside `save()`: the training job deletes old folders | **P** (on S3 the training role should not be allowed to delete) |
| Export for Teams 09/12 | `export_safetensors` with strict keys + probe check; DeepSpeed via `zero_to_fp32` | `dcp_to_torch_save` one-liner | **P** |
| Unpickling | JSON for per-rank state | `torch.load(..., weights_only=True)` | both safe |
| Docs worth keeping | ADR 0001 | DESIGN.md: **"when is the loss bit-equal" list** (same layout, GPU type, versions, kernel set, data order, `attention.impl: eager`), Young/Daly with **our own lab's 12.9 h MTBF**, 30B sizing (360 GB) | **add M's three sections to ADR 0001** (sizing marked provisional until config v1) |

Verdict: **P's checkpoint**, with three additions from M (frozen check at save, `embedding_policy_id`, shard
`manifest` in the data position) and his bit-equal conditions and interval numbers in the ADR.

### 2. Job queue and Slurm

> **Updated:** the queue now has a third source, Max's `uz9ai/queue`. Its deep review and the three-way
> verdict are in [queue_review_max.md](queue_review_max.md), which **replaces this section's "Keep" column**:
> Max's `cluster.toml` installer, QOS limits, configless Slurm and evidence folders join the merged queue.

| Aspect | P | M | Keep (shared node) |
|---|---|---|---|
| Slurm version / OS | Ubuntu 24.04, Slurm 23.11 (Docker lab works: we create the cgroup slice by hand) | Ubuntu 26.04, Slurm 25.11 (says 23.11 cannot launch steps in Docker) | **Match the real node's OS** once known (1 Nov). Both configs are plain `slurm.conf`; keep P's 23.11 workaround documented in case the node is 24.04 |
| One config for test and production | `slurm.conf` + EC2 files (`site.ec2.conf`, `nodes.ec2.conf`, `gres.ec2.conf`) | `slurm.conf` + `docker/` vs `node/` site files; `node/` = **one host runs every daemon** | **M's `docker/` vs `node/` split**, with P's `slurm.conf` settings merged in (below). EC2 files move to `support/ec2/` |
| Accounts | `setup_accounts.sh`: 11 team accounts, `GrpTRES=node=2`, mainrun QoS | `accounts.cfg` loaded with `sacctmgr load`: team01–team12, **GPU shares `GrpTRES=gres/gpu=N`** | **M's `accounts.cfg` with GPU shares** (on one 8-GPU node a 2-node cap means nothing) + P's `mainrun` QoS, GPU-hour budgets (`GrpTRESMins`) and fair share |
| Main run protection | QoS `mainrun` preempts team jobs (requeue, 60 s grace, teams save on SIGUSR1) | none | **P's QoS**, if the main run shares the node with team jobs (team decision, below) |
| Exit-code contract | 0 done, 75 requeue (`RequeueExit`), 78 hold (`RequeueExitHold`), crash loop (3 in 30 min) → hold, job comment says what to do | `--requeue` on node failure only | **P**. Without it a NaN or a bad restore would be retried forever |
| Launcher | `srun` one task per GPU, `job_queue.py run` wraps it (signals, exit codes) | `srun` one task per node + `torchrun` with c10d rendezvous, **new rendezvous id per restart** | **P's wrapper**; take M's rendezvous id idea (`$SLURM_JOB_ID-$SLURM_RESTART_COUNT`) for the moment Team 05's trainer needs torchrun |
| Prolog / epilog / periodic health | `prolog.sh`, `epilog.sh`, `HealthCheckProgram` every 30 s, auto-drain | none (health is a separate job; drain by hand) | **P** |
| Hot spare, spot watcher, power saving | built (`keep-spare`, `spot-watch`) | none | **Park in `support/ec2/`**: no spot and no spare on one shared node |
| Controller failover, DB backup | backup `slurmctld2` (82 s takeover), daily dump + test restore | none | **Keep DB backup** (cheap, works on one host). **Park failover**: there is no second host |
| Test users | service user `svc` + per-team accounts | real users alice/bob/carol with fixed UIDs | **M's**: closer to how students will submit; carol proves "no account → refused" |
| Production start | `launch.sh` (12 checked steps, tested on Docker) | README steps 1–5 by hand | **P's `launch.sh`** set for one host (`V5_CTLD_HOSTS=<node>`, no backup controller; steps already skip what is running) |

### 3. Node health and network

| Aspect | P | M | Keep |
|---|---|---|---|
| Shape | `health_check.py`: modes prolog / periodic / full, JSON out, thresholds in `thresholds.yaml`, drains and asks jobs to save | `gpu_health.sh`: one shell script, prints `BAD` lines, exit 1 | **P's engine** (JSON is what Team 08 and the alerts consume), with M's checks added |
| GPU checks | count, temperature, power, ECC (volatile + aggregate + corrected), HW slowdown, PCIe width, row remap, clock offset | count, temperature, ECC, row remap pending/failed, **NVLink inactive links** | **add M's NVLink check** to P (a down link halves all-reduce speed with no error; P only sees it if DCGM is installed) |
| DCGM | `dcgmi health -c` in periodic (no load), `diag` only in full mode | `dcgmi diag -r 1` (or 3) every pre-flight | **P's rule** (diag loads the GPUs; NVIDIA advises not to run it next to a job), M's `DCGM_LEVEL` knob for the long check before the run |
| Xid table | fatal 48, 63, 64, 74, 79, 94, 95, 119, 120; warn 13, 31, 43 | hardware 48, 61, 62, 64, 74, 79, 92, 94, 95, 119, 120, 140 | **merge: P's table + 61, 62, 92, 140 from M.** Both treat **94 (contained ECC)** as fatal; NVIDIA says the app can restart on the same GPU. Move 94 to "restart the job, drain if it repeats" (the G7 review points at this too) |
| Collective test | `allreduce_test.py`: all-reduce only, exact-sum check, busbw floor | `allreduce.py`: **all-reduce, reduce-scatter, all-gather, all-to-all**, result check, busbw floor | **M's four collectives** (reduce-scatter/all-gather = ZeRO/FSDP, all-to-all = MoE experts), inside P's JSON/threshold frame |
| Hang diagnosis | flight recorder env in `mainrun.sbatch` | same, plus `TORCH_NCCL_DEBUG_INFO_TEMP_FILE` path per job and a "how to read it" guide | **add M's trace-file path and guide** |
| Faking faults without GPUs | fixtures (`nvidia_smi_bad.csv`, `kernel_xid.log`), `force_fail` file | **fake `nvidia-smi` and `dmesg` installed in the image**, faults planted in `/run/fake/*` | **M's fakes**: the real scripts run unchanged in Docker, which tests more of the code |
| Operator guide | `health/README.md` | `TESTING.md`: level 1 (one GPU), 2 (faked faults), 3 (shared node), with exact commands and expected output | **M's TESTING.md**, it is the clearest week-2 checklist we have |

### 4. Monitoring and cost

P only: ADR 0004, 74-metric catalogue, live alert watcher, `explain.py`, cost model, GPU-hour accounting.
M: none. **Keep P**, trimmed for one node: drop the EC2 price and unmanaged-instance parts from `submission/`
(they move to `support/ec2/`), keep the alerts, `explain.py` and GPU-hour accounting per team.

### 5. Tests and evidence

| | P | M | Keep |
|---|---|---|---|
| Fast check (< 2 min) | none; unit suite 17 min, drills 30 min | `test.sh`: 13 checks in ~90 s (accounts, refusals, 2-node job, GPU-share wait `AssocGrpGRES`, requeue on node down, health pass/fail, 4 collectives, hot GPU stops launch, **chained 2-node FSDP2 restart, bit-equal losses and weights**) | **M's `test.sh` as the smoke test** run on every change; P's drills as the full gate |
| FSDP2 without GPUs | not possible on torch 2.5.1 (CUDA only); T16 waits for Kaggle | **torch 2.9.1: FSDP2 on CPU over gloo works** in Docker | **move our Docker image to torch 2.9.1** (check DeepSpeed 0.18 with it), so FSDP2 save/reshard/restore runs in every drill, not only on Kaggle |
| Depth | 30 unit tests, 33 drills (kills, signals, kill during save/restore, split brain, NaN, spike, rollback, reshard, failover, DB restore, budget, fair share, retention, export, live alerts) | the 13 checks above | **P** for depth |
| GPU evidence | Kaggle 2×T4 package ready, not yet run | GPU-on-CPU restore checked by hand once (27 Oct) | neither has GPU numbers yet: the Kaggle run is the next step |

## Merged layout (proposal)

```text
teams/07-infrastructure/
├── README.md                  one page: what is here, who wrote what (provenance)
├── submission/                what the instructor reviews: lean, all of it runs on the shared node
│   ├── adr/                   P's 4 ADRs + M's bit-equal conditions, interval numbers, sizing in 0001
│   ├── launch.sh              P, set for one host
│   ├── ckpt/                  P's ckpt.py, ds_ckpt.py, store.py, loader_contract.py (+ M's 3 additions)
│   ├── queue/                 P's job_queue.py (exit contract, crash loop, drain, status)
│   ├── slurm/                 slurm.conf (P's settings) + node/ (M) + accounts.cfg (M, GPU shares + P's QoS/budgets)
│   │                          + mainrun.sbatch, team_job.sbatch, prolog/epilog/healthcheck, backup_db.sh (P)
│   ├── health/                P's health_check.py + M's 4-collective test and NVLink check, merged Xid table,
│   │                          TESTING.md (M)
│   └── metrics/               P's catalogue, watch.py, explain.py (EC2 cost parts moved out)
└── support/
    ├── slurm-docker/          one Docker cluster: P's drills + M's test.sh smoke test and fake nvidia-smi/dmesg
    ├── tests/                 P's unit tests
    ├── kaggle/                GPU checks
    ├── ec2/                   parked for later: site/nodes/gres.ec2.conf, keep-spare, spot-watch, failover, EC2 cost
    └── docs/                  reviews, sim results, this plan
```

## Work list, in order

| # | Task | From | Size |
|---|---|---|---|
| 1 | Add `node/` site files and `accounts.cfg` (GPU shares); load accounts with `sacctmgr load`, keep `mainrun` QoS and budgets | M → P | S |
| 2 | Health: four collectives in `allreduce_test.py`, NVLink check, merged Xid table (94 → restart), trace-file path | M → P | M |
| 3 | Fake `nvidia-smi` / `dmesg` in the Docker image; port M's `test.sh` as the 90-second smoke test | M → P | M |
| 4 | Checkpoint: frozen check at save, `embedding_policy_id` in env, shard `manifest` in the loader contract; M's bit-equal conditions and interval numbers into ADR 0001 | M → P | S |
| 5 | Docker image to torch 2.9.1; run T16 (FSDP2) on CPU in the drills; re-check DeepSpeed 0.18 | M's finding | M |
| 6 | Move EC2-only parts to `support/ec2/`; `launch.sh` defaults for one host | P | S |
| 7 | One README with provenance (who wrote which file), one PR | both | S |
| 8 | On the node (1 Nov): M's TESTING.md level 3, then `launch.sh`; Kaggle run for GPU numbers | both | — |

Queue tasks Q1–Q8 from [queue_review_max.md](queue_review_max.md) slot in after task 1.

## Questions for the team

1. **OS on the shared node** (Ubuntu 24.04 → Slurm 23.11, or 26.04 → 25.11)? Decides the Docker base image.
2. **Does the main run share the node with team jobs?** If yes, keep P's preemption QoS; if the node is
   reserved for the main run in its window, preemption can be parked too.
3. **GPU share per team** (`GrpTRES=gres/gpu=N`): TSAI sets it; until then M's 4 per team in Docker.
4. **Who owns each merged area** for the PR: suggestion, Pradeep for checkpoint and monitoring, Mallik for
   Slurm node config and health/network tests, both review each other.
