"""The job queue, from the training job's side (ADR 0002). Slurm schedules; this file decides what each outcome
means and what happens next.

In simple words: Slurm only understands "run again" (requeue) or "wait for a person" (hold). This file turns
everything that can happen to a training job into one of three answers, says why in plain words, and takes a
sick or disappearing node out of the queue so its job moves to a healthy one:

    0  finished
    75 run me again          Slurm requeues (RequeueExit=75); the job restarts from its last checkpoint
    78 stop and call a person Slurm holds (RequeueExitHold=78); retrying would only burn GPU hours

A crash we do not understand (exit 1, killed, segfault) is retried, because most crashes at scale are one-off
hardware or network faults. If it crashes 3 times in 30 minutes, it is not one-off: we hold the job.

Commands:
    job_queue.py run -- <srun args> -- <trainer args>   the job wrapper; every sbatch script calls it
    job_queue.py spot-watch                             per node: cloud's 2-minute spot warning -> drain + save
    job_queue.py drain <reason> [--node N]              take a node out; its jobs save and move
    job_queue.py status                                 jobs and drained nodes, explained in plain words
    job_queue.py keep-spare                             controller, every minute: name the hot spare, boot one if none

Where it reports: the Slurm job comment (`squeue -o "%.10i %.12T %.20r %k"`), a banner at the end of the job log,
and the job.* / node.* events. The words come from common/reasons.py.

Not called `queue.py` on purpose: that name would hide Python's own `queue` module, which boto3 and threads use.
"""
import argparse
import json
import os
import signal
import socket
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from ckpt.store import open_store  # noqa: E402  (no torch: the wrapper stays light)
from common.events import emit  # noqa: E402
from common.reasons import (DRAIN, EXIT_CODES, EXIT_DONE, EXIT_FATAL, EXIT_RETRY, RAW_EXIT, SLURM,  # noqa: E402
                            lookup, read_exit_notes)

# The trainer the wrapper starts. On Cloud nodes: Team 05's real trainer. Default: the test trainer in the support kit.
TRAIN_SCRIPT = os.environ.get("V5_TRAIN_SCRIPT",
                              os.path.join(HERE, "..", "support", "simulation", "trainer", "train.py"))
CRASHLOOP_N = int(os.environ.get("CRASHLOOP_N", "3"))
CRASHLOOP_WINDOW_S = float(os.environ.get("CRASHLOOP_WINDOW_S", "1800"))


# ============================================================================ Slurm actions on a node
def _slurm(cmd, timeout=30):
    if not shutil.which(cmd[0]):
        return None
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None


def node_name() -> str:
    return os.environ.get("SLURMD_NODENAME") or socket.gethostname()


def drain(reason: str, node: str = None) -> bool:
    """"Drain" = no new jobs on this node. `sinfo -R` then shows v5:<reason>."""
    node = node or node_name()
    p = _slurm(["scontrol", "update", f"nodename={node}", "state=drain", f"reason=v5:{reason}"[:250]])
    ok = p is not None and p.returncode == 0
    emit("node.drained", node=node, reason=reason, ok=ok)
    return ok


def jobs_on(node: str = None) -> list:
    p = _slurm(["squeue", "-h", "-w", node or node_name(), "-t", "RUNNING", "-o", "%A"])
    if p is None or p.returncode != 0:
        return []
    return [j for j in p.stdout.split() if j.strip()]


def ask_jobs_to_save_and_stop(node: str = None, why: str = "") -> list:
    """SIGUSR1 to every job on the node: they save, exit 75, and Slurm restarts them on a healthy node."""
    jobs = jobs_on(node)
    for j in jobs:
        _slurm(["scancel", "--signal=USR1", j])
        emit("job.signalled", node=node or node_name(), signalled_job=j, signal="USR1", why=why)
    return jobs


# ============================================================================ the hot spare
# In simple words: one GPU node must always be up and free for the main run, so a failure moves the run in
# seconds, not after a new instance boots (up to 15 min). Slurm's `SuspendExcNodes=gpu-[1-9]:1` count form is
# not clear on whether busy nodes count toward the 1, so we do not depend on it. Every minute, on the
# controller, this names the spare node explicitly (`SuspendExcNodes=<that node>`), and powers one up if no
# node is free. A spare may run preemptible team jobs (ADR 0002 §1): the main run preempts them.
OK_STATES = {"idle", "mix", "alloc", "comp"}       # powered up and usable; "~" off, "#" powering up, drain/down out


def keep_spare(partition: str = "gpu", want: int = 1) -> dict:
    p = _slurm(["sinfo", "-h", "-N", "-p", partition, "-o", "%N|%t"])
    if p is None or p.returncode != 0:
        return {"ok": False, "detail": "sinfo not available"}
    state = dict(line.split("|", 1) for line in p.stdout.split() if "|" in line)
    q = _slurm(["squeue", "-h", "-q", "mainrun", "-t", "RUNNING,COMPLETING", "-o", "%N"])
    main = set()
    for nl in (q.stdout.split() if q is not None and q.returncode == 0 else []):
        h = _slurm(["scontrol", "show", "hostnames", nl])
        main |= set(h.stdout.split()) if h is not None and h.returncode == 0 else {nl}
    free = sorted(n for n, s in state.items() if s in OK_STATES and n not in main)
    free.sort(key=lambda n: state[n] != "idle")            # prefer an idle node over one running team jobs
    booting = sorted(n for n, s in state.items() if s.endswith("#") and n not in main)
    spares = (free + booting)[:want]
    powered = []
    for n in sorted(n for n, s in state.items() if s == "idle~"):
        if len(spares) >= want:
            break
        _slurm(["scontrol", "update", f"nodename={n}", "state=power_up"])
        spares.append(n)
        powered.append(n)
    if spares:
        _slurm(["scontrol", "update", f"SuspendExcNodes={','.join(spares)}"])
    out = {"ok": len(spares) >= want, "spares": spares, "powered_up": powered, "main_run_nodes": sorted(main)}
    emit("node.spare", **out)
    return out


# ============================================================================ the job wrapper
def crash_loop(run_url: str) -> tuple:
    """Record this crash in the run's folder of the shared store; return (is_loop, crashes_in_window).

    In simple words: a requeued job can start on any node, so the count cannot live on a node's disk (it
    would start from zero each time) or in an appended file (an object store cannot append). It is one small
    file, `crashes.json`, read and rewritten whole. Only one wrapper of a job runs at a time, so there is no race.
    If the store cannot be reached, the crash is retried as usual and an event says the cap is not counting."""
    now = time.time()
    try:
        st = open_store(run_url)
        log = st.get_json("crashes.json") if st.exists("crashes.json") else []
        log = [r for r in log if now - r["time"] <= CRASHLOOP_WINDOW_S]
        log.append({"time": now, "job_id": os.environ.get("SLURM_JOB_ID"),
                    "restart": int(os.environ.get("SLURM_RESTART_COUNT", "0")), "node": node_name()})
        st.put_json("crashes.json", log)
    except Exception as e:  # noqa: BLE001 - a broken ledger must never turn a retry into a lost job
        emit("job.crash_ledger_unavailable", cause="crash_ledger_unavailable", detail=str(e)[:300],
             **{k: v for k, v in lookup("crash_ledger_unavailable").items() if k in ("title", "you_do", "severity")})
        return False, 0
    return len(log) >= CRASHLOOP_N, len(log)


def set_comment(text: str) -> None:
    """Put the plain-words status on the Slurm job, so `squeue` and `scontrol show job` show it."""
    jid = os.environ.get("SLURM_JOB_ID")
    if jid:
        _slurm(["scontrol", "update", f"JobId={jid}", f"Comment={text.replace(chr(34), chr(39))[:250]}"], 15)
        # the comment helps people; a failure here must never change the exit code


def explain(out: int, cause: str, rc: int, note: dict, restart: int) -> dict:
    r = lookup(cause)
    step = note.get("step")
    where = f" at step {step}" if step is not None else ""
    raw = f" (trainer exit {rc}: {RAW_EXIT[rc]})" if rc in RAW_EXIT and cause in ("crash", "crash_loop") else ""
    head = f"V5 {EXIT_CODES[out]['title']} ({out}): {r['title']}{where}{raw}"
    todo = "nothing" if out == EXIT_RETRY and r["severity"] in ("none", "low") else r["you_do"]
    return {"title": head, "meaning": r["meaning"], "auto": r["auto"], "you_do": todo,
            "severity": r["severity"], "alert": r.get("alert"), "detail": note.get("detail", "")}


def banner(x: dict) -> None:
    lines = ["", "=" * 100, x["title"], f"What happened : {x['meaning']}",
             f"Already done  : {x['auto']}", f"What you do   : {x['you_do']}"]
    if x["detail"]:
        lines.append(f"Detail        : {x['detail']}")
    lines += ["More          : python metrics/explain.py <cause or code>  (metrics/README.md)", "=" * 100, ""]
    print("\n".join(lines), file=sys.stderr, flush=True)


def run(srun_args: list, train_args: list) -> int:
    run_id = os.environ.get("RUN_ID", "run")
    run_url = os.environ.get("V5_REMOTE_ROOT", "/shared/ckpt").rstrip("/") + "/" + run_id   # same folder as the checkpoints
    restart = int(os.environ.get("SLURM_RESTART_COUNT", "0"))
    emit("job.started", restart_count=restart, nodes=os.environ.get("SLURM_JOB_NODELIST", ""),
         account=os.environ.get("SLURM_JOB_ACCOUNT", ""), qos=os.environ.get("SLURM_JOB_QOS", ""))
    set_comment(f"V5 RUNNING (start #{restart + 1}): restoring from latest.json")

    cmd = ["srun", "--kill-on-bad-exit=1", *srun_args, sys.executable, TRAIN_SCRIPT, *train_args]
    child = subprocess.Popen(cmd)

    # Preemption sends SIGTERM to the batch shell too. Keep waiting: the trainers got the same signal,
    # they are saving, and we must report their exit code, not ours.
    # The time-limit warning (--signal=B:USR1@<lead>) reaches only this batch shell, so pass SIGUSR1 on to the
    # trainers through srun, which forwards it to every task. A trainer that already got it (scancel
    # --signal=USR1 signals the steps) only sets its stop flag again.
    def forward(signum, _frame):
        emit("job.signal", signal=signal.Signals(signum).name)
        if signum == signal.SIGUSR1 and child.poll() is None:
            child.send_signal(signal.SIGUSR1)

    signal.signal(signal.SIGTERM, forward)
    signal.signal(signal.SIGUSR1, forward)
    rc = child.wait()

    notes = read_exit_notes(run_id)
    note = notes[0] if notes and notes[0].get("code") == rc else {}
    if rc in (EXIT_DONE, EXIT_RETRY, EXIT_FATAL):
        out = rc
        cause = note.get("cause") or {0: "done", 75: "saved_and_stopped", 78: "unknown_fatal"}[rc]
    else:
        loop, n = crash_loop(run_url)
        out = EXIT_FATAL if loop else EXIT_RETRY
        cause = "crash_loop" if loop else "crash"
        if loop:
            note = dict(note, detail=f"{n} crashes in {int(CRASHLOOP_WINDOW_S)} s; last trainer exit {rc}")
    x = explain(out, cause, rc, note, restart)
    banner(x)
    set_comment(f"{x['title']}. Explain: python metrics/explain.py {cause}. Do: {x['you_do']}")
    plain = {k: x[k] for k in ("title", "you_do", "severity")}
    emit("job.ended", trainer_exit=rc, exit=out, cause=cause, restart_count=restart, step=note.get("step"), **plain)
    if out == EXIT_RETRY:
        emit("job.requeued", cause=cause, restart_count=restart, **plain)
    elif out == EXIT_FATAL:
        emit("job.held", cause=cause, restart_count=restart, step=note.get("step"), **plain)
    return out


# ============================================================================ spot watcher
# The cloud gives a spot (preemptible) node a short warning, about 2 minutes, before taking it back. We poll it
# every 5 s. When it comes, we drain the node and ask its jobs to save now: we lose seconds of work, not the whole
# interval since the last checkpoint. How to ask differs per cloud, so it is a setting: V5_SPOT_NOTICE_CMD is a
# command (set in /etc/v5/node.env by the node image) that prints the notice, or nothing when there is none, e.g.
# a query of the node's metadata service. Without it (Docker test) the watcher reads a file.
NOTICE_CMD = os.environ.get("V5_SPOT_NOTICE_CMD")
NOTICE_FILE = os.environ.get("V5_SPOT_NOTICE_FILE", "/var/lib/v5-health/spot_notice")
POLL_S = float(os.environ.get("V5_SPOT_POLL_S", "5"))


def spot_notice() -> str:
    if NOTICE_CMD:
        try:
            p = subprocess.run(NOTICE_CMD, shell=True, capture_output=True, text=True, timeout=5)
            return p.stdout.strip() if p.returncode == 0 else ""   # an error or a timeout means "no notice yet"
        except (OSError, subprocess.TimeoutExpired):
            return ""
    if os.path.exists(NOTICE_FILE):
        return open(NOTICE_FILE).read().strip() or "spot notice (drill)"
    return ""


def spot_watch() -> int:
    os.environ.setdefault("V5_EVENTS_DIR", "/var/log/v5/events")
    handled = False
    while True:
        n = spot_notice()
        if n and not handled:
            emit("node.spot_notice", node=node_name(), detail=n[:200])
            drain("spot_notice")
            ask_jobs_to_save_and_stop(why="spot_notice")
            handled = True
        elif not n:
            handled = False
        time.sleep(POLL_S)


# ============================================================================ status, for people
def status() -> int:
    """Every job and every drained node, each with what it means and what to do."""
    q = _slurm(["squeue", "-h", "-o", "%i|%j|%u|%a|%T|%r|%k"])
    if q is None or q.returncode != 0:
        print("squeue is not available here (run this on a Slurm node or the controller)")
        return 1
    print("JOBS")
    for line in filter(None, q.stdout.splitlines()):
        jid, name, _user, acct, state, reason, comment = (line.split("|", 6) + [""] * 7)[:7]
        why = SLURM.get(reason) or SLURM.get(state) or ""
        print(f"  {jid:>8} {name:<14} {acct:<9} {state:<12} {reason}")
        if comment and comment != "(null)":
            print(f"           {comment}")
        elif why:
            print(f"           {why}")
    r = _slurm(["sinfo", "-R", "-h", "-o", "%N|%E"])
    rows = [line.split("|", 1) for line in (r.stdout.splitlines() if r and r.returncode == 0 else []) if line]
    print("\nNODES OUT OF SERVICE" if rows else "\nNODES: none drained or down")
    for node, why in rows:
        print(f"  {node}: {why}")
        for part in why[3:].split(",") if why.startswith("v5:") else []:
            if part in DRAIN:
                meaning, done, todo = DRAIN[part]
                print(f"      {part}: {meaning} Done: {done}. You do: {todo}")
    print("\nExplain anything: python metrics/explain.py <exit code | cause | alert id | reason>")
    return 0


# ============================================================================ command line
def main(argv) -> int:
    if argv and argv[0] == "run":
        sep = [i for i, a in enumerate(argv) if a == "--"]
        if len(sep) < 2:
            sys.exit("usage: job_queue.py run -- <srun args> -- <trainer args>")
        return run(argv[sep[0] + 1:sep[1]], argv[sep[1] + 1:])
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="the job wrapper: run -- <srun args> -- <trainer args>")
    sub.add_parser("spot-watch", help="watch for the spot warning on this node")
    d = sub.add_parser("drain", help="take a node out of service; its jobs save and move")
    d.add_argument("reason")
    d.add_argument("--node")
    sub.add_parser("status", help="jobs and drained nodes, in plain words")
    k = sub.add_parser("keep-spare", help="controller, every minute: keep one free GPU node up (the hot spare)")
    k.add_argument("--partition", default="gpu")
    k.add_argument("--spares", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "keep-spare":
        return 0 if keep_spare(a.partition, a.spares)["ok"] else 3
    if a.cmd == "spot-watch":
        return spot_watch()
    if a.cmd == "drain":
        drain(a.reason, a.node)
        ask_jobs_to_save_and_stop(a.node, why=a.reason)
        return 0
    return status()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
