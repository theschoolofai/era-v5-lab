# Team 08's health-check contract (`v5-health/1`): what we changed, and what we suggest

Team 08 (monitoring) wrote the JSON format our node health reports must follow, with a validator and a
ClickHouse row mapper: `teams/08-monitoring/health-check/` in lab PR #125 (author: sandeepkunkunuru). It was
written against another Team 07 draft (`gpu_health.sh`, `nccl_probe.py`). This note says how our
`health/health_check.py` now meets it, and what we suggest adding to the contract from what we built and tested.

> **In simple words.** Team 08 reads our health reports to draw dashboards and raise alerts. If the two teams
> spell the fields differently, their dashboard shows zeros for our nodes. So we now write the fields their way,
> keep our extra fields next to them, and a test checks every report shape against their rules. We also found
> things their format misses, which we offer back to them below.

## 1. What we changed (31 Oct)

| Contract rule | Before | Now |
|---|---|---|
| `timestamp_utc`, `expected_gpus`, `admit_training` on every report | `time` only; no GPU count; no admit flag | all three added (`time` kept) |
| GPU count check `gpu_inventory` with `count` and one line per GPU | `gpu_count` (and `gpu` when nvidia-smi failed) | one `gpu_inventory` check |
| `ecc_uncorrectable` with `values`, one per GPU | one check per GPU | one check for the node, `values` per GPU; the detail names the bad GPUs |
| `xid` metrics `counts` + `events` (`pci_bdf`, `code`, `severity` warn/fail, `reason`) | `new` + `already_seen` | both (ours kept) |
| collective metrics `backend`, `world_size`, `status`; per size `bytes`, `seconds`, `max_error`, `all_ranks_correct` | `bytes`, `time_s`, busbw | all added; `max_error` is the largest error on any rank |
| standalone `xid_scan.py` output has `name: "xid"`, `source` | no name | added |

Test: `support/tests/test_health.py` (`test_team08_*`) checks real reports against our own copy of their rules: a
GPU node with planted faults, a GPU node with no tools, a CPU host with the four collectives, a wrong collective.

## 2. Two points to agree with Team 08

| Point | Their draft | What we do | Why |
|---|---|---|---|
| **A `warn` report and admission** | `admit_training` is false unless the verdict is `pass` | true on `warn` (our prolog starts the job); false on `fail`, or when the GPUs were not counted | A warn is shown, not a stop. A missing optional tool or a slightly warm GPU on every node would otherwise block the whole main run. Hard faults are `fail` and do block. |
| **CPU `gloo` collectives** | gloo can never pass `nccl_all_reduce` | gloo may pass only when `expected_gpus == 0` (Docker cluster, CPU test hosts); on a GPU node it must be NCCL | Our Docker cluster and CI have no GPUs; refusing gloo there makes every test node fail. On a GPU node we agree: gloo proves nothing about NVLink. |

## 3. Suggestions for the contract, from what we built and tested

| # | Suggestion | Why | Where we do it |
|---|---|---|---|
| 1 | **Add Xid 61, 62, 92, 140 to the fatal list** | NVIDIA's catalog: internal micro-controller breakpoint and halt (61, 62), high single-bit ECC rate (92), unrecovered ECC (140) | `health/thresholds.yaml` `xid.fatal` |
| 2 | **Write the Xid 94 repeat rule into the contract**: one 94 → `warn` (job restarts, GPU stays); the same GPU again within 24 h → `fail` | NVIDIA says a contained error needs only an application restart; a second one means the GPU is failing | `xid_scan.py`, `restart_window_h` |
| 3 | **`events` are new events only**, not every Xid line in the log window | a periodic report every 30 s over the last 30 min would count one Xid up to 60 times in ClickHouse, and an old error would drain a repaired node again | `xid_scan.py` remembers lines already seen (`already_seen`) |
| 4 | **Four collectives, not only all-reduce**: `nccl_all_reduce`, `nccl_reduce_scatter`, `nccl_all_gather`, `nccl_all_to_all` | reduce-scatter and all-gather carry FSDP / ZeRO traffic, all-to-all carries MoE expert traffic; a link can fail one pattern and pass another | `health/allreduce_test.py` |
| 5 | **Bus bandwidth per size** (`busbw_gbps`, nccl-tests convention) | a slow node slows the whole run; `seconds` alone cannot be compared across sizes and GPU counts | `allreduce_test.py`; floor in `thresholds.yaml` |
| 6 | **`remapped_rows` as a standard check** (`pending` → warn, `failure` → fail) | a row-remap failure is a GPU that cannot repair its memory; it shows in no Xid until it is too late | `remap_checks` |
| 7 | **`nvlink` metrics fixed**: `links`, `inactive`, `down` | a down link raises no error; all-reduce just runs at half speed for the whole run | `nvlink_checks` (millermuttu's check) |
| 8 | **Use the aggregate ECC count too**, not only volatile | the volatile counter resets on reboot, so a GPU that lost data before a reboot looks clean | `gpu_checks`: max of volatile and aggregate |
| 9 | **`dcgm_health` for periodic mode**; DCGM diag only in prolog and full | `dcgmi diag` loads the GPUs and would slow training every 30 s; health watches cost nothing | `dcgm_health_check` |
| 10 | **Time per check and per report** (`seconds`, `runtime_seconds`) | the prolog has a time budget (30 s); a slow check delays every job start, and Team 08 can alert on it | `check()`, report |
| 11 | **`drain_reason` as the failed check names** (`ecc_uncorrectable,xid`) | Slurm shows it as `v5:<names>` in `sinfo -R`; each name maps to plain words and an action (`metrics/explain.py`), which their dashboard could show next to the node | `common/reasons.py` |
| 12 | **A skipped standalone Xid scan has no `source`** | the validator requires `source`; when no kernel log is readable there is none | allow `source: null` when `status == "skipped"` |
| 13 | **Host checks as standard optional checks**: `clock_offset`, `nvme_free`, `host_mem`, `gpu_temperature`, `pcie_link`, `gpu_throttle` | each has drained or slowed a node in our drills or in the course's failure tables | `health_check.py` |
| 14 | **No GPU model names in the README example** | the instructor asked Team 07 to keep GPU and instance types out of the repo; the same likely applies to every team | — |
