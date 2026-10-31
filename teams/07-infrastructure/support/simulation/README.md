# Simulation kit (optional): how we proved the design without paying for GPUs

**You do not need this folder to use or review the design.** The submission is the ADRs, the READMEs and the
production code in the team folder (`ckpt/`, `queue/`, `slurm/`, `health/`, `metrics/`, `common/`). This folder holds what we
used to **prove** it: a Docker copy of the Slurm cluster, a tiny test trainer, the drill script with its
results. The Kaggle GPU checks are next door in `../kaggle/`. Use it to re-run the evidence, or leave it alone.

> **In simple words.** We built a small copy of the cluster on a laptop and broke it on purpose, many times
> (killed processes, unplugged nodes, stopped the controller, injected NaN and loss spikes), and measured
> what happened each time. The production code runs unchanged inside it.

| Folder / file | What it is | Needs |
|---|---|---|
| `slurm-docker/` | the test cluster: MariaDB, `slurmdbd`, two controllers, an S3 emulator (moto), nodes `c1–c3` ("GPU", 2 placeholder GPUs each) and `c4` (eval/CPU) | Docker |
| `run_sim.py` | starts the cluster, runs every drill, checks the result, writes `results/` and `../docs/sim_results.md` | Docker, ~25 min |
| `results/` | the latest run: `drills.json`, `metrics.json`, `alerts.json`, `report.md` | — |
| `trainer/` | a tiny model (`tiny.py`) and trainer (`train.py`) that follow every checkpoint, signal, watchdog and loss-spike rule. **Stand-in for Team 05's real trainer** | CPU or GPU |
| `config_v0.yaml` | the architecture team's config, read by the test trainer (seed, grad clip, optimizer) | — |

## How the production code uses this folder

Only in two places, both replaceable:

- `queue/job_queue.py` starts `V5_TRAIN_SCRIPT`; the default is `support/simulation/trainer/train.py`. On EC2, set it to
  the real trainer.
- `support/tests/test_ckpt.py` trains the tiny model from `support/simulation/trainer/` to prove bit-equal restores.

## Run it

From `teams/07-infrastructure`, with Docker Desktop running:

```bash
docker compose -f support/simulation/slurm-docker/docker-compose.yml build slurmdbd   # once, ~5 min (again after
                                                                              # changing the Dockerfile)
python3 support/simulation/run_sim.py              # every drill; ends with "N/N drills passed"
python3 support/simulation/run_sim.py --keep-up    # leave the cluster up afterwards to explore it
docker compose -f support/simulation/slurm-docker/docker-compose.yml down -v          # remove it
```

The whole team folder is mounted read-only at `/opt/v5` in every container, so the containers run exactly
the files in git. The trainer runs on CPU (gloo); GPUs exist only as counted placeholders (`/dev/v5gpu0-1`),
enough to test allocation and GPU-hour accounting, not computation.

## The drills

| Drill | What we break | What must happen |
|---|---|---|
| preemption | team jobs fill the GPU nodes, then the main run is submitted | team jobs save and requeue; the main run starts |
| kill (×3) | `kill -9` a training process | requeued; restored from the last commit |
| SIGUSR1 (×3) | the stop signal a spot notice or health drain sends | emergency save; 0 steps lost |
| spot notice | the AWS 2-minute warning, on one node | node drained; save; job moves to the spare |
| health fail | force one node's health check to fail | drained; save; job moves |
| two nodes down | both main-run nodes fail, one spare | main run waits (no crash loop); recovers on repair |
| hang | `SIGSTOP` one rank | watchdog exits 75; restart |
| node loss | stop a node's container | marked DOWN after ~30 s; requeued |
| kill during save / restore | slow the upload / restore, then kill | the half-written checkpoint is never used / the next attempt restores cleanly |
| controller failover | stop the primary `slurmctld` | the backup takes over; training never stops |
| NaN, loss spike | inject them | nothing bad saved; job held **and its Slurm comment says why and what to do**; rollback on a new branch and on half the GPUs |
| crash loop | a job that crashes at step 3 | requeued twice, then held |
| accounts, budget, fair share, GPU allocation | no account; budget used up; heavy vs light account; over-asking GPUs | rejected; pending with the budget reason; lower priority; refused |
| DB backup, retention, export | dump + test-restore the accounting DB; delete old checkpoints; safetensors export | same tables; no protected checkpoint deleted; probe bit-equal |
| live alerts | `metrics/watch.py` runs all the time | the HIGH alerts the drills cause fire live |

Results of the latest run: [../docs/sim_results.md](../docs/sim_results.md); what they mean:
[../docs/review_week1.md](../docs/review_week1.md).

## Docker vs EC2

Same `slurm.conf`. Different, by design: CPU instead of GPU (gloo instead of NCCL); placeholder GPUs; no cgroup
enforcement (`site.conf`, `cgroup.conf`); no Pyxis containers; no power saving; no EFA; an S3 emulator instead
of S3. Time is compressed: save every 8 s instead of 30 min, watchdog 20 s, crash-loop window 10 s.

## Kaggle (real GPUs)

See [../kaggle/README.md](../kaggle/README.md). Results go in `support/kaggle/results/`.
