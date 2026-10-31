"""Every code and cause our system can report, in plain words, with what to do next (monitoring guide).

In simple words: a number like 78 or a word like "IntegrityError" means nothing at 4 a.m. This table is the
one place that says, for each of them: what happened, what the system already did by itself, and what a person
does now. The job wrapper copies the answer into the Slurm job comment and the job log, the alert watcher puts
it in every page, and `python metrics/explain.py <code>` prints it.

Each entry:
    title    short label, shown in `squeue` / `scontrol show job` comments
    severity high (act now) | medium (today) | low (weekly) | none (nothing to do)
    meaning  what happened
    auto     what the system already did, without anyone
    you_do   what a person does now ("nothing" is a valid answer)
    alert    the metric in metrics/catalog.yaml that fires for it, if any
"""
import glob
import json
import os
import time

EXIT_DONE, EXIT_RETRY, EXIT_FATAL = 0, 75, 78

ROLLBACK = ("roll back: sbatch --export=ALL,TRAIN_EXTRA=\"--from-step <last good step> --skip <N> "
            "--branch <new name>\" slurm/mainrun.sbatch (last good step: python ckpt/ckpt.py list --run <run>)")

# ------------------------------------------------------------------ exit codes of a training job (ADR 0001 §6)
EXIT_CODES = {
    0: dict(title="DONE", severity="none", meaning="Training finished and the final checkpoint is committed.",
            auto="Slurm marks the job COMPLETED.", you_do="nothing"),
    75: dict(title="RETRY", severity="none",
             meaning="The job stopped in a safe state (it just saved, or there was nothing to save) and asks to run "
                     "again. Also used for one-off crashes.",
             auto="Slurm requeues the job (RequeueExit=75); it restarts from latest.json, on another node if needed.",
             you_do="nothing, unless it repeats: then see Q-05 (interruptions) and the cause in the job comment"),
    78: dict(title="HELD", severity="high",
             meaning="The job stopped and must NOT be retried: retrying would burn GPU hours for nothing (NaN, loss "
                     "spike, failed restore checks, changed environment, or a crash loop).",
             auto="Slurm holds the job (RequeueExitHold=78; squeue shows SPECIAL_EXIT / JobHeldUser). Nothing bad "
                  "was saved.",
             you_do="read the cause in the job comment (scontrol show job <id> | grep Comment) and follow its "
                    "entry here; then `scontrol release <id>` or submit the fix", alert="Q-02"),
}

# What a raw exit code from the trainer usually means before the wrapper maps it to 75 (or 78 after a loop).
RAW_EXIT = {
    1: "Python error (an uncaught exception, often a NCCL error raised by TORCH_NCCL_ASYNC_ERROR_HANDLING)",
    124: "a command timed out",
    134: "abort (SIGABRT), often NCCL or CUDA aborting the process",
    137: "killed with SIGKILL: out of memory (kernel OOM killer), kill -9, or Slurm after KillWait",
    139: "segmentation fault (SIGSEGV): a crash in native code (CUDA, NCCL, a custom kernel)",
    143: "SIGTERM not handled by the trainer",
}

# ------------------------------------------------------------------ causes (the `cause` field of events)
CAUSES = {
    # job ends (job.ended / job.requeued / job.held, from queue/job_queue.py)
    "done": dict(title="finished", severity="none", meaning="Training reached its last step.",
                 auto="final checkpoint committed", you_do="nothing"),
    "saved_and_stopped": dict(
        title="saved and stopped", severity="none",
        meaning="A stop signal arrived (preemption, spot notice, health drain or an operator), the job saved, "
                "and stopped.",
        auto="emergency checkpoint committed; Slurm requeues the job, it restarts from that checkpoint (≈0 work lost)",
        you_do="nothing"),
    "hang_watchdog": dict(
        title="hang: watchdog restart", severity="medium",
        meaning="No training step finished within WATCHDOG_S: a frozen rank, a deadlock or a data wait.",
        auto="all Python stacks dumped to the job log; exit 75; Slurm restarts from the last checkpoint",
        you_do="read the stack dump in the job log (which rank, which call). Two in an hour pages (H-14)",
        alert="H-14"),
    "crash": dict(
        title="crash: automatic retry", severity="low",
        meaning="The trainer died without saying why (see trainer_exit: 1 Python error, 137 killed/OOM, "
                "139 segfault).",
        auto="the wrapper turned it into 75: Slurm restarts from the last checkpoint; work since that commit is lost",
        you_do="nothing for one crash; look at the job log if it repeats (3 in 30 min holds the job)"),
    "crash_loop": dict(
        title="crash loop: held", severity="high",
        meaning="The job crashed 3 times within 30 minutes. It is not a one-off fault.",
        auto="job held so it stops burning GPU hours",
        you_do="read the last job log for the real error, fix it, then `scontrol release <id>`", alert="Q-04"),
    "unknown_fatal": dict(
        title="stopped as fatal, no reason given", severity="high",
        meaning="The trainer exited 78 but left no exit note (a trainer that does not call write_exit_note).",
        auto="job held", you_do="read the end of the job log for the FATAL line; then follow that cause here",
        alert="Q-02"),
    # trainer, fatal (exit 78)
    "nonfinite": dict(
        title="NaN: held", severity="high",
        meaning="The loss (or the state) became NaN/Inf. Nothing was saved after it.",
        auto="no checkpoint written; job held", you_do=ROLLBACK + ", skipping the batches around the bad step",
        alert="CK-07"),
    "loss_spike": dict(
        title="loss spike: held", severity="high",
        meaning="The loss stayed above 1.5 × its recent median for 3 steps: the model is diverging, even without NaN.",
        auto="no checkpoint written during the spike; job held", you_do=ROLLBACK + "; tell Team 05", alert="H-24"),
    "StrictLoadError": dict(
        title="model keys differ: held", severity="high",
        meaning="The model code has different tensor names, shapes or dtypes than the checkpoint (the V4 misload).",
        auto="restore refused; every key that differs is listed in the job log",
        you_do="fix the model code or the checkpoint mapping; never resume by ignoring keys", alert="CK-06"),
    "FrozenChangedError": dict(
        title="frozen tensor changed: held", severity="high",
        meaning="A tensor that must never train (e.g. the KE2 Kronecker tables) changed since the last checkpoint. "
                "Training touched it: a missing requires_grad=False, or an optimizer that includes it.",
        auto="nothing saved (the previous checkpoint is still good); job held",
        you_do="find which code trains the named tensor (the job log lists it), fix it, then roll back to the last "
               "checkpoint: " + ROLLBACK, alert="CK-06"),
    "DataManifestError": dict(
        title="other data: held", severity="high",
        meaning="The data loader's shard list differs from the one this checkpoint was trained on. Resuming "
                "would continue on other data without anyone noticing.",
        auto="restore refused before any step; nothing was lost",
        you_do="point the loader back at the run's shard list, or, if new data is intended, start a new branch "
               "and tell Teams 01/02", alert="CK-06"),
    "EnvMismatchError": dict(
        title="environment changed: held", severity="high",
        meaning="The software or config differs from the checkpoint (image digest, torch/CUDA/NCCL, config sha, "
                "OMP_NUM_THREADS).",
        auto="restore refused; the differences are listed in the job log",
        you_do="if the change is intended and approved, resubmit with TRAIN_EXTRA=--allow-env-change (it is "
               "logged); otherwise go back to the old image", alert="CK-06"),
    "CheckpointError": dict(
        title="no usable checkpoint: held", severity="high",
        meaning="Every committed checkpoint failed its checks, or the requested step does not exist.",
        auto="restore refused", you_do="python ckpt/ckpt.py list/verify --run <run>; check S3 and CK-04/CK-05",
        alert="CK-06"),
    # checkpoint and restore events
    "nvme_full": dict(
        title="save skipped: disk full", severity="high",
        meaning="The node's NVMe has less free space than 1.2 × this node's checkpoint share.",
        auto="save skipped (training continues, but nothing new is protected)",
        you_do="free NVMe space (old restore folders, data cache) or drain the node", alert="CK-03"),
    "IntegrityError": dict(
        title="checksum mismatch", severity="high",
        meaning="A checkpoint file does not match its sha256: damaged on disk, network or S3.",
        auto="the damaged checkpoint is never used; a restore falls back to the previous commit",
        you_do="pin the last good checkpoint (ckpt.py pin); find the hop that corrupts data", alert="CK-04"),
    "RestoreCheckError": dict(
        title="restore check failed", severity="high",
        meaning="The restored state is not the saved state (digest, probe loss, next batch or frozen hashes differ).",
        auto="the job fell back to the previous commit",
        you_do="compare the two printed values in the job log; do not continue on that checkpoint", alert="CK-05"),
    "UploadTimeout": dict(
        title="upload timeout", severity="medium",
        meaning="A rank did not finish its S3 upload in time.", auto="save not committed; training continues",
        you_do="check S3 errors and upload throughput (CK-11)", alert="CK-03"),
    "FencedError": dict(
        title="another attempt owns the run: stopped", severity="medium",
        meaning="A newer attempt of this run claimed latest.json (a higher epoch), so this attempt may not commit. "
                "Two attempts were alive at once: usually a node that lost its network, so Slurm started a new "
                "job while the old one kept running.",
        auto="this attempt's commit was refused and it stopped; the pointer and the newer attempt are untouched",
        you_do="nothing for the run; find out why the old attempt was still alive (node network, slurmd) and "
               "drain that node if it repeats", alert=None),
    "ReshardError": dict(
        title="cannot resume at this size: held", severity="high",
        meaning="The checkpoint was saved by a data loader that keeps a separate position per rank. At another "
                "world size those positions do not map to the new ranks, so data would repeat or be skipped.",
        auto="restore refused before any step; nothing was lost",
        you_do="resubmit at the saved world size (the job log names it), or fix the loader to keep one global "
               "ledger offset (ckpt/loader_contract.py)", alert="CK-06"),
    "crash_ledger_unavailable": dict(
        title="crash count not stored", severity="medium",
        meaning="The crash was retried, but the crash count could not be written to the run's S3 folder, so "
                "the 3-in-30-min crash-loop cap is not counting.",
        auto="job requeued as a normal crash",
        you_do="check S3 access from the batch node (the same fault usually also fails checkpoint uploads)",
        alert="CK-03"),
}

# ------------------------------------------------------------------ node drain reasons (sinfo -R shows "v5:<names>")
DRAIN = {
    "spot_notice": ("AWS will reclaim this spot instance in 2 minutes.",
                    "node drained, jobs saved and moved to the spare", "nothing; the instance goes away by itself"),
    "gpu": ("nvidia-smi could not run on a GPU node (driver broken or GPU hung).", "node drained, jobs saved and moved",
            "reboot the instance; if nvidia-smi still fails, replace it"),
    "gpu_count": ("Fewer GPUs visible than expected.", "node drained, jobs saved and moved",
                  "reboot the instance; if still missing, replace it"),
    "ecc_uncorrectable": ("A GPU memory error lost data.", "node drained, jobs saved and moved",
                          "replace the instance (stop/start moves it to new hardware)"),
    "remapped_rows": ("GPU memory row remap failed (or is pending a reset).", "node drained on failure",
                      "failure: replace; pending: reset the GPU / reboot"),
    "xid": ("The GPU driver logged a fatal Xid error (79 off the bus, 95 uncontained memory error, …), "
            "or Xid 94 (contained ECC) twice on one GPU within 24 h.",
            "node drained, jobs saved and moved", "replace the instance; the Xid code is in the health report"),
    "dcgm_diag": ("NVIDIA's diagnostic failed.", "node drained", "replace the instance"),
    "dcgm_health": ("DCGM's background health watch reports a GPU failure (PCIe, memory, NVLink, thermal or power).",
                    "node drained; its jobs saved and moved", "run `health_check.py --mode full`; replace if it fails again"),
    "gpu_temperature": ("A GPU is at its slowdown temperature.", "node drained", "check cooling; replace if repeated"),
    "nvme_free": ("Local disk too full for the next checkpoint.", "node drained",
                  "clean /nvme, then `scontrol update nodename=<n> state=resume`"),
    "clock_offset": ("The node clock is off by more than 100 ms.", "node drained",
                     "fix chrony (Amazon Time Sync), then resume the node"),
    "nccl_collectives": ("The collective test did not finish (hang, crash or timeout).", "node drained",
                         "run health_check.py --mode full on it; read the NCCL flight-recorder dump; replace if it fails again"),
    "nccl_all_reduce": ("All-reduce (data-parallel gradients) gave a wrong value or was too slow.", "node drained",
                        "run health_check.py --mode full on it; replace if it fails again"),
    "nccl_reduce_scatter": ("Reduce-scatter (ZeRO/FSDP gradients) gave a wrong value or was too slow.",
                            "node drained", "run health_check.py --mode full on it; replace if it fails again"),
    "nccl_all_gather": ("All-gather (ZeRO-3/FSDP weights) gave a wrong value or was too slow.", "node drained",
                        "run health_check.py --mode full on it; replace if it fails again"),
    "nccl_all_to_all": ("All-to-all (MoE expert exchange) gave a wrong value or was too slow.", "node drained",
                        "run health_check.py --mode full on it; replace if it fails again"),
    "nvlink": ("An NVLink link between GPUs is inactive: no error, but all-reduce runs at about half speed.",
               "node drained", "reset the GPUs or reboot; replace the instance if the link stays down"),
    "drill_force_fail": ("A drill forced this node to fail (test only).", "node drained",
                         "remove /var/lib/v5-health/force_fail and resume the node"),
}

# ------------------------------------------------------------------ Slurm states and pending reasons you will see
SLURM = {
    "SPECIAL_EXIT": "held after exit 78 (RequeueExitHold). Read the job Comment for the cause.",
    "JobHeldUser": "held after exit 78, or by `scontrol hold`. Read the job Comment for the cause.",
    "BeginTime": "requeued; Slurm waits for the old launch credential to expire (≈ 50 s). Normal after a restart.",
    "Resources": "waiting for free nodes. For the main run: Q-01 pages after 10 min (not enough healthy nodes).",
    "Priority": "higher-priority jobs are ahead. Normal for team jobs.",
    "AssocGrpCPUMinutesLimit": "the account's budget (GrpTRESMins) is used up. Talk to the lead (Q-15).",
    "AssocGrpGRESMinutes": "the account's GPU-minute budget is used up. Talk to the lead (Q-15).",
    "AssocGrpGRES": "the team already uses its GPU share (GrpTRES=gres/gpu). It starts when its own jobs free GPUs.",
    "QOSMaxGRESPerJob": "the job asks for more GPUs than its QOS allows per job. Ask for fewer, or use another QOS.",
    "QOSMaxWallDurationPerJobLimit": "--time is above the QOS MaxWall. Ask for less; long runs requeue themselves.",
    "QOSMaxSubmitJobPerUserLimit": "the user has the most jobs this QOS lets one user queue. Wait or cancel some.",
    "QOSMaxJobsPerUserLimit": "the user already runs the most jobs this QOS allows at once. It starts when one ends.",
    "AssocGrpNodeLimit": "the team already holds its 2 nodes (GrpTRES=node=2). It starts when one frees up.",
    "ReqNodeNotAvail": "the nodes asked for are drained or down. Check `sinfo -R`.",
    "PREEMPTED": "a team job gave its node to the main run; it saved and is back in the queue.",
    "NODE_FAIL": "the node stopped answering (SlurmdTimeout 30 s); the job is requeued by Slurm.",
    "REQUEUED": "the job is back in the queue and restarts from its last checkpoint.",
}


def lookup(cause: str) -> dict:
    """The entry for a cause, with a safe default so the wrapper never fails on an unknown word."""
    if cause in CAUSES:
        return CAUSES[cause]
    return dict(title=cause, severity="medium", meaning=f"unlisted cause '{cause}'", auto="see the job log",
                you_do="read the job log; add this cause to common/reasons.py")


# ------------------------------------------------------------------ the trainer tells the wrapper why it stopped
# Any trainer (ours, or Team 05's real one) calls write_exit_note() just before it exits. The job wrapper reads
# the notes after srun returns. Without a note the wrapper still works, but can only report the bare exit code.

def _runs_dir(run_id: str = None) -> str:
    return os.path.join(os.environ.get("V5_RUNS_DIR", "/var/log/v5/runs"), run_id or os.environ.get("RUN_ID", "run"))


def write_exit_note(code: int, cause: str, step: int = None, detail: str = "", rank: int = 0) -> None:
    try:
        d = _runs_dir()
        os.makedirs(d, exist_ok=True)
        name = f"exit-{os.environ.get('SLURM_JOB_ID', 'local')}-{os.environ.get('SLURM_RESTART_COUNT', '0')}-r{rank}.json"
        with open(os.path.join(d, name), "w") as f:
            json.dump({"time": time.time(), "code": code, "cause": cause, "step": step, "detail": detail[:500]}, f)
    except OSError:
        pass  # a note is a courtesy; it must never change how the trainer exits


def read_exit_notes(run_id: str = None) -> list:
    pat = os.path.join(_runs_dir(run_id), f"exit-{os.environ.get('SLURM_JOB_ID', 'local')}-"
                                          f"{os.environ.get('SLURM_RESTART_COUNT', '0')}-r*.json")
    out = []
    for p in glob.glob(pat):
        try:
            out.append(json.load(open(p)))
        except (OSError, ValueError):
            pass
    # the most serious note wins: a fatal cause, then a hang, then anything else
    out.sort(key=lambda n: (n.get("code") != EXIT_FATAL, n.get("cause") != "hang_watchdog", n.get("time", 0)))
    return out
