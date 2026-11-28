#!/usr/bin/env python3
"""Kill the eval watcher again and again during a replayed run and show that it survives (Team 9 task 3).

In simple words: this test replays a real commits.jsonl (dry run 2: 9 commits, step 0 to the final step 1,221) into
a store folder, faster than real time. Two real eval_watcher.py processes follow it, Tier A on every commit and
Tier B on every Nth, sharing one GPU slot lock, as on the eval slot. A fake scorer stands in for run_lab_ckpt.py
(no GPU, no model) and takes --score-s seconds per checkpoint. While the run goes on, the test kills the watchers
and restarts each one as a supervisor does: after exit 75 or a death by signal, never after 0, 1 or 78 (the exit
codes of eval_watcher.py).

    python teams/09-evaluation/harness_lab/watcher_restart_test.py --random-kills 0     # planned kills only
    python teams/09-evaluation/harness_lab/watcher_restart_test.py --random-kills 10    # plus seeded random kills

The planned kills (each fires once, at an exact moment):

- mid-score: SIGKILL to the watcher while its scorer runs (the scorer sends it to its own watcher).
- after-write: SIGKILL to the watcher after its scorer wrote the result and before the state says so.
- sigterm: SIGTERM to the watcher while its scorer runs: the watcher must exit 75 and finish on the next start.
- load-after-delete, load-after-insert (with --clickhouse-url): a proxy in front of ClickHouse sends SIGKILL to the
  watcher right after the server ran load_jsonl.py's DELETE of the run_id (its rows are gone, none inserted yet), or
  right after the INSERT into eval_mini (before the state says loaded).

Random kills: --random-kills SIGKILLs at seeded random times over the run, to either tier (a poll, a state save, the
slot wait, a load). A random kill can cut off a scorer before its planned kill fires, so the check that every
planned kill fired is strict only with --random-kills 0.

--restore-after K adds a trainer restore to the replay: after commit K the trainer resumes from that commit and
commits its step again (epoch 2, as Team 7's restore does), so the older commit of that step is superseded.

What must hold at the end (exit 0 only if all do):

1. Each watcher ends by itself with exit 0 after the final commit (--until-final), after all its restarts.
2. Every commit a watcher owns is done once in its state: scored and loaded (parsed with --no-load) with a result
   file that names that commit, or superseded by a later commit of the same step.
3. No owned commit is left out, and none outside its tier is in its state.
4. Two scorers never ran at the same time on the slot: each scorer checks, when it starts, that no earlier scorer is
   still alive (also the ones a kill cut off), across both tiers and all restarts.
5. No scorer is still running when the test ends.
6. With --clickhouse-url: each run_id holds the rows of exactly one result in eval_mini, and one ingest_manifest row.
7. With --random-kills 0: every planned kill fired and hit a live watcher.

It reports the scorer runs the kills cost beyond one per commit, the results a restarted watcher kept, and the
largest lag from commit to score in run time (the replay is scaled back by --speed), against the 30-minute Tier A
rule. Exit codes: 0 all checks pass, 1 a check failed, 2 bad input.
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
WATCHER = HERE / "eval_watcher.py"
POSIX = os.name != "nt"
EXIT_OK, EXIT_RETRY = 0, 75


def alive(pid: int) -> bool:
    """True while the process exists and is not a zombie (a zombie holds no lock and no memory)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        try:
            return stat.read_text().rsplit(")", 1)[-1].split()[0] != "Z"
        except OSError:
            return False
    try:
        out = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    except OSError:
        return True
    return bool(out) and not out.startswith("Z")


# The fake scorer: called as <fake> <run_lab_ckpt.py> --run-dir R --step N --out O --scorer S ... (the argv the
# watcher builds). It writes the same kind of eval-mini v1 file run_lab_ckpt.py writes, last, as run_lab_ckpt.py does.
FAKE_SCORER = r'''
import hashlib, json, os, signal, sys, time
from pathlib import Path
sys.path.insert(0, os.environ["FAKE_HELPERS"])
from watcher_restart_test import alive
argv = sys.argv[2:]
a = dict(zip(argv[0::2], argv[1::2]))
run_dir, step, out = Path(a["--run-dir"]), int(a["--step"]), Path(a["--out"])
label, events = os.environ["FAKE_LABEL"], Path(os.environ["FAKE_EVENTS"])
watcher = os.getppid()  # the watcher that started this scorer

def event(kind, **kw):
    with open(events, "a") as f:
        f.write(json.dumps({"t": time.time(), "kind": kind, "label": label, "step": step, "pid": os.getpid(),
                            **kw}) + "\n")

def fire(moment, sig):
    """Send a planned signal once, and only to the watcher that started this scorer: a scorer whose watcher is
    already dead has another parent now (init, or a subreaper), and that one must never get it."""
    key = f"{label}:{step}:{moment}"
    if key not in os.environ.get("FAKE_KILLS", "").split(",") or os.getppid() != watcher:
        return
    marker = Path(os.environ["FAKE_MARKS"]) / key.replace(":", "_")
    try:
        marker.touch(exist_ok=False)
    except FileExistsError:
        return
    event("kill", moment=moment, target=watcher)
    os.kill(watcher, sig)

# As run_lab_ckpt.py: the pointer (the last commits.jsonl line of the step) and MANIFEST.json are read first.
lines = [json.loads(x) for x in (run_dir / "commits.jsonl").read_text().splitlines() if x.strip()]
path = [c for c in lines if c["step"] == step][-1]["path"]
revision = hashlib.sha256((run_dir / path / "MANIFEST.json").read_bytes()).hexdigest()
others = []
for line in events.read_text().splitlines() if events.exists() else []:
    e = json.loads(line)
    if e["kind"] == "start":
        others.append(e["pid"])
    elif e["kind"] == "end" and e["pid"] in others:
        others.remove(e["pid"])
event("start", watcher=watcher)
live = [p for p in others if p != os.getpid() and alive(p)]
if live:
    event("overlap", with_pids=live)
half = float(os.environ["FAKE_SCORE_S"]) / 2
time.sleep(half)
fire("mid", signal.SIGKILL)
fire("sigterm", signal.SIGTERM)
time.sleep(half)
record = {
    "model": "lab:" + run_dir.name, "model_revision": revision,
    "checkpoint": {"run": run_dir.name, "branch": "main", "step": step, "epoch": 1, "tokens_seen": None,
                   "path": a["--run-dir"].rstrip("/") + "/" + path},
    "format": "fp32", "backend": "lab", "dtype": "float32", "task": "lab_smoke_next_token", "metric": "acc",
    "filter": "none", "primary": True, "value": 25.0, "stderr": None, "n_items": 960, "item_set": "limit:64",
    "num_fewshot": 0, "decoding": "loglikelihood", "notes": ["watcher_restart_test fake scorer"],
    "seed": {"random": 1234, "numpy": 1234, "torch": 1234, "fewshot": 1234},
    "harness": {"name": "run_lab_ckpt", "version": "0.1"}, "hardware": "test (cpu)", "run_date": "replay",
}
doc = {"schema_version": "eval_mini_v1", "generated": "replay", "sources": [], "notes": [], "records": [record]}
out.write_text(json.dumps(doc))
event("end")
fire("after-write", signal.SIGKILL)
'''


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def read_commits(path: Path) -> list[dict]:
    commits = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if not commits or not all(isinstance(c.get("step"), int) and isinstance(c.get("path"), str) for c in commits):
        raise SystemExit(f"{path}: not a Team 7 commits.jsonl")
    if commits[-1].get("reason") != "final":
        raise SystemExit(f"{path}: the last commit is not the final one; --until-final would never end")
    return commits


def with_restore(commits: list[dict], after: int) -> list[dict]:
    """The trainer resumes from commit `after` (1-based) and commits that step again, then goes on in epoch 2."""
    if not 1 <= after < len(commits):
        raise SystemExit(f"--restore-after must be 1 to {len(commits) - 1}")
    r = commits[after - 1]
    again = dict(r, path=re.sub(r"-e\d+$", "-e2", r["path"]), epoch=2, reason="start", time=r["time"] + 60)
    later = [dict(c, path=re.sub(r"-e\d+$", "-e2", c["path"]), epoch=2) for c in commits[after:]]
    return commits[:after] + [again] + later


class Trainer(threading.Thread):
    """Appends the commits to the store at their recorded gaps divided by --speed, as Team 7's Checkpointer does:
    the step folder and MANIFEST.json first, then one write of line + newline to commits.jsonl."""

    def __init__(self, run_dir: Path, commits: list[dict], speed: float):
        super().__init__(daemon=True)
        self.run_dir, self.commits, self.speed = run_dir, commits, speed
        self.started = threading.Event()
        self.wall0 = 0.0
        # A new model_revision per test run, so its run_ids never meet the rows of an older test in ClickHouse.
        self.nonce = os.urandom(8).hex()

    def run(self) -> None:
        self.wall0 = time.time()
        self.started.set()
        t0 = self.commits[0]["time"]
        for c in self.commits:
            time.sleep(max(0.0, self.wall0 + (c["time"] - t0) / self.speed - time.time()))
            folder = self.run_dir / c["path"]
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "MANIFEST.json").write_text(json.dumps({"run_id": self.run_dir.name, "step": c["step"],
                                                              "branch": c["branch"], "epoch": c.get("epoch"),
                                                              "test_run": self.nonce}))
            line = dict(c, time=time.time())  # the commit time the watcher sees, for its lag
            with open(self.run_dir / "commits.jsonl", "ab") as f:
                f.write((json.dumps(line) + "\n").encode("utf-8"))
            log(f"trainer: committed step {c['step']} ({c['reason']}, {c['path']})")


class Supervised:
    """One watcher process, restarted as a supervisor does it: after exit 75 or a death by signal."""

    def __init__(self, name: str, cmd: list[str], env: dict, logfile: Path, restart_delay: float):
        self.name, self.cmd, self.env, self.logfile, self.delay = name, cmd, env, logfile, restart_delay
        self.proc: subprocess.Popen | None = None
        self.exits: list[int] = []
        self.pids: list[int] = []
        self.done = threading.Event()
        self.lock = threading.Lock()

    def start(self) -> None:
        with self.lock, open(self.logfile, "ab") as out:
            out.write(f"=== start {len(self.exits) + 1}\n".encode())
            out.flush()
            self.proc = subprocess.Popen(self.cmd, env=self.env, stdout=out, stderr=subprocess.STDOUT)
            self.pids.append(self.proc.pid)

    def kill(self, sig=signal.SIGKILL) -> int | None:
        with self.lock:
            if self.proc is None or self.proc.poll() is not None:
                return None
            self.proc.send_signal(sig)
            return self.proc.pid

    def loop(self, deadline: float) -> None:
        self.start()
        while True:
            try:
                code = self.proc.wait(max(0.1, deadline - time.time()))
            except subprocess.TimeoutExpired:
                log(f"{self.name}: still running at --timeout, killed")
                self.kill()
                self.proc.wait()
                return
            self.exits.append(code)
            if code == EXIT_OK:
                log(f"{self.name}: watcher exited 0")
                self.done.set()
                return
            if code != EXIT_RETRY and code >= 0:
                log(f"{self.name}: watcher exited {code}: not restarted (0 done, 1 failed, 78 fatal)")
                return
            log(f"{self.name}: watcher exited {code}, restart in {self.delay:g} s")
            time.sleep(self.delay)
            self.start()


class ProcMonitor(threading.Thread):
    """--real (Linux): finds the real run_lab_ckpt.py processes in /proc every --monitor-s seconds, writes the same
    events as the fake scorer (start, end, overlap, kill) and sends the planned kills to their watchers.

    A scorer has ended ("end") when it is gone and its --out file was written while it lived; a scorer gone without
    that was cut off. Two live scorers in one scan is an overlap. Planned kills: mid and sigterm once the scorer has
    run --kill-after-s seconds, after-write as soon as its --out file is written; each only to the watcher that
    started that scorer (its parent)."""

    def __init__(self, outs: dict, sups: dict, plan: set, period: float, kill_after: float):
        super().__init__(daemon=True)
        self.outs, self.sups, self.plan, self.period, self.kill_after = outs, sups, plan, period, kill_after
        self.events: list[dict] = []
        self.live: dict[int, dict] = {}
        self.fired: set[str] = set()
        self.halt = threading.Event()

    def event(self, kind: str, p: dict, **kw) -> None:
        self.events.append({"t": time.time(), "kind": kind, "label": p["label"], "step": p["step"], "pid": p["pid"],
                            **kw})

    @staticmethod
    def scorers() -> dict[int, dict]:
        found = {}
        for d in os.listdir("/proc"):
            if not d.isdigit():
                continue
            try:
                argv = Path(f"/proc/{d}/cmdline").read_bytes().split(b"\0")
                if not any(x.endswith(b"run_lab_ckpt.py") for x in argv):
                    continue
                state, ppid = Path(f"/proc/{d}/stat").read_text().rsplit(")", 1)[-1].split()[:2]
            except OSError:
                continue
            if state == "Z":
                continue
            args = [x.decode() for x in argv]
            kv = dict(zip(args, args[1:]))
            found[int(d)] = {"pid": int(d), "ppid": int(ppid), "step": int(kv["--step"]), "out": Path(kv["--out"])}
        return found

    def written(self, p: dict) -> bool:
        try:
            return p["out"].stat().st_mtime >= p["t0"] - 0.05
        except OSError:
            return False

    def run(self) -> None:
        while not self.halt.is_set():
            now = self.scorers()
            for pid, p in now.items():
                if pid not in self.live:
                    p["t0"] = time.time()
                    p["label"] = next((lab for lab, o in self.outs.items() if p["out"].parent == o), "?")
                    self.live[pid] = p
                    self.event("start", p, watcher=p["ppid"])
            for pid in [x for x in self.live if x not in now]:
                p = self.live.pop(pid)
                if self.written(p):
                    self.event("end", p)
            if len(self.live) > 1:
                for p in self.live.values():
                    others = [x for x in self.live if x != p["pid"]]
                    if not p.get("overlap"):
                        p["overlap"] = True
                        self.event("overlap", p, with_pids=others)
            for p in list(self.live.values()):
                sup = self.sups[p["label"]]
                for moment, sig in (("mid", signal.SIGKILL), ("sigterm", signal.SIGTERM),
                                    ("after-write", signal.SIGKILL)):
                    key = f"{p['label']}:{p['step']}:{moment}"
                    if key not in self.plan or key in self.fired:
                        continue
                    due = self.written(p) if moment == "after-write" else time.time() - p["t0"] >= self.kill_after
                    if due and sup.proc is not None and sup.proc.pid == p["ppid"] and sup.kill(sig):
                        self.fired.add(key)
                        self.event("kill", p, moment=moment, target=p["ppid"])
            time.sleep(self.period)


class ClickHouseProxy(http.server.ThreadingHTTPServer):
    """Forwards each request to ClickHouse. After a planned DELETE or INSERT of a run_id has run on the server, it
    sends SIGKILL to the watcher that sent it, before the answer reaches that watcher."""

    daemon_threads = True

    def __init__(self, upstream: str, plan: set[str], tiers: dict, events: list):
        super().__init__(("127.0.0.1", 0), ProxyHandler)
        self.upstream, self.plan, self.tiers, self.events = upstream.rstrip("/"), plan, tiers, events
        self.fired: set[str] = set()
        self.lock = threading.Lock()


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    RUN_ID = re.compile(rb"main/step_(\d+)-e\d+:([A-Za-z0-9_.-]+):")

    def log_message(self, *args):
        pass

    def _forward(self, method: str) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0)) if method == "POST" else None
        req = urllib.request.Request(self.server.upstream + self.path, data=body, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                status, data = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, data = e.code, e.read()
        head = (body or b"")[:64]
        kind = ("load-after-delete" if head.startswith(b"ALTER TABLE eval_mini DELETE") else
                "load-after-insert" if head.startswith(b"INSERT INTO eval_mini ") else None)
        m = self.RUN_ID.search(body or b"") if kind else None
        if m and status == 200:
            key = f"{m.group(2).decode()}:{int(m.group(1))}:{kind}"
            with self.server.lock:
                fire = key in self.server.plan and key not in self.server.fired
                if fire:
                    self.server.fired.add(key)
            if fire:
                pid = self.server.tiers[m.group(2).decode()].kill()
                self.server.events.append({"kind": "kill", "moment": kind, "label": m.group(2).decode(),
                                           "step": int(m.group(1)), "target": pid})
                what = "DELETE of its rows" if kind == "load-after-delete" else "INSERT into eval_mini"
                log(f"proxy: SIGKILL {m.group(2).decode()} (pid {pid}) right after the {what}, step {int(m.group(1))}")
        try:
            self.send_response(status)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except OSError:
            pass  # the watcher is dead

    def do_POST(self):
        self._forward("POST")

    def do_GET(self):
        self._forward("GET")


def ch_count(url: str, table: str, run_id: str) -> int:
    q = f"SELECT count() FROM {table} WHERE run_id = '{run_id}' FORMAT TabSeparated"
    with urllib.request.urlopen(url.rstrip("/") + "/?query=" + urllib.parse.quote(q), timeout=30) as r:
        return int(r.read().decode().strip())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commits", type=Path, default=HERE.parents[1] / "05-architecture" / "results" / "dryrun2-1234"
                    / "commits.jsonl", help="the commits.jsonl to replay (default: the dry run 2 record)")
    ap.add_argument("--speed", type=float, default=200.0, help="replay speed: run seconds per wall second")
    ap.add_argument("--score-s", type=float, default=1.0, help="seconds the fake scorer takes per checkpoint")
    ap.add_argument("--every-b", type=int, default=3,
                    help="Tier B scores every Nth commit (10 on the eval slot; 3 so that it owns some of 9 commits)")
    ap.add_argument("--random-kills", type=int, default=6, help="SIGKILLs at seeded random times, over both tiers")
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--restore-after", type=int, help="add a trainer restore after this commit (1-based)")
    ap.add_argument("--interval", type=float, default=0.2, help="watcher poll interval in seconds")
    ap.add_argument("--restart-delay", type=float, default=0.3, help="seconds before the supervisor restarts it")
    ap.add_argument("--timeout", type=float, default=300.0, help="seconds before the test gives up")
    ap.add_argument("--clickhouse-url", help="load into this ClickHouse (through a killing proxy) and count the rows; "
                                             "default --no-load")
    ap.add_argument("--real", action="store_true",
                    help="Linux, torch: a real Team 7 store written by tests/replay_trainer.py while the watchers run, "
                         "scored by the real run_lab_ckpt.py --scorer smoke (no fake scorer)")
    ap.add_argument("--monitor-s", type=float, default=0.01, help="--real: seconds between /proc scans")
    ap.add_argument("--kill-after-s", type=float, default=0.3, help="--real: a mid-score kill this long after start")
    ap.add_argument("--watcher", type=Path, default=WATCHER, help="the eval_watcher.py under test")
    ap.add_argument("--work", type=Path, help="work folder, kept (default: a temporary folder, deleted after)")
    a = ap.parse_args(argv)
    if not POSIX:
        print("watcher_restart_test: needs POSIX signals (Linux or macOS)", file=sys.stderr)
        return 2
    if not a.commits.is_file():
        print(f"watcher_restart_test: {a.commits} not found (it comes with the dry run 2 record)", file=sys.stderr)
        return 2
    if a.real and not sys.platform.startswith("linux"):
        print("watcher_restart_test: --real reads /proc (Linux)", file=sys.stderr)
        return 2
    if a.real and a.restore_after:
        print("watcher_restart_test: --restore-after is for the fake store only", file=sys.stderr)
        return 2
    commits = read_commits(a.commits)
    if a.restore_after:
        commits = with_restore(commits, a.restore_after)
    work = a.work or Path(tempfile.mkdtemp(prefix="watcher-restart-"))
    if a.work and work.exists():
        shutil.rmtree(work)
    run_dir = work / "store" / "dryrun2-1234"
    run_dir.mkdir(parents=True)  # the real trainer's Checkpointer makes the same folder (remote root / run id)
    marks = work / "marks"
    marks.mkdir()
    events_path = work / "scorer_events.jsonl"
    fake = work / "fake_python"
    fake.write_text(f"#!{sys.executable}\n{FAKE_SCORER}")
    fake.chmod(0o755)

    # The planned kills. Tier A owns every commit: the scorer kills on step 0, the middle commit and the final
    # commit, the SIGTERM on the third, the load kills on the second and fourth. Tier B gets one, on its first commit.
    steps = [c["step"] for c in commits]
    b_steps = [c["step"] for i, c in enumerate(commits, 1) if i % a.every_b == 0]
    plan = {f"tier-a:{steps[0]}:mid", f"tier-a:{steps[len(steps) // 2]}:after-write", f"tier-a:{steps[-1]}:mid",
            f"tier-a:{steps[2]}:sigterm"} | ({f"tier-b:{b_steps[0]}:after-write"} if b_steps else set())
    load_plan = ({f"tier-a:{steps[1]}:load-after-delete", f"tier-a:{steps[3]}:load-after-insert"}
                 | ({f"tier-b:{b_steps[-1]}:load-after-insert"} if b_steps else set())) if a.clickhouse_url else set()

    span = (commits[-1]["time"] - commits[0]["time"]) / a.speed
    rng = random.Random(a.seed)
    random_kills = sorted((rng.uniform(0.0, span), rng.choice(["tier-a", "tier-b"])) for _ in range(a.random_kills))

    tiers, sups = {}, {}
    proxy_events: list[dict] = []
    proxy = None
    if a.clickhouse_url:
        proxy = ClickHouseProxy(a.clickhouse_url, load_plan, sups, proxy_events)
        threading.Thread(target=proxy.serve_forever, daemon=True).start()
        load = ["--clickhouse-url", f"http://127.0.0.1:{proxy.server_address[1]}"]
    else:
        load = ["--no-load"]
    slot = work / "out" / "gpu_slot.lock"
    (work / "logs").mkdir()
    for label, every in (("tier-a", 1), ("tier-b", a.every_b)):
        out = work / "out" / f"dryrun2-1234.{label}.every{every}"
        cmd = [sys.executable, str(a.watcher), "--run-dir", str(run_dir), "--label", label, "--every", str(every),
               "--out-dir", str(out), "--slot-lock", str(slot), "--until-final", "--interval", str(a.interval),
               *load, *(["--scorer", "smoke", "--", "--steps", str(steps[-1])] if a.real else ["--python", str(fake)])]
        env = dict(os.environ, FAKE_LABEL=label, FAKE_EVENTS=str(events_path), FAKE_MARKS=str(marks),
                   FAKE_SCORE_S=str(a.score_s), FAKE_KILLS=",".join(sorted(plan)), FAKE_HELPERS=str(HERE))
        sups[label] = Supervised(label, cmd, env, work / "logs" / f"{label}.log", a.restart_delay)
        tiers[label] = (out, every)

    restore = f", restore after commit {a.restore_after}" if a.restore_after else ""
    scorer = ("real Team 7 store and run_lab_ckpt.py --scorer smoke" if a.real
              else f"fake scorer {a.score_s:g} s per checkpoint")
    log(f"replay {a.commits.name} ({len(commits)} commits{restore}, "
        f"run span {span * a.speed:.0f} s) at {a.speed:g}x = {span:.1f} s wall; "
        f"{scorer}; "
        f"Tier B every {a.every_b}; {'ClickHouse through the proxy' if proxy else '--no-load'}")
    log(f"planned kills: {', '.join(sorted(plan | load_plan))}")
    log(f"random SIGKILLs at wall s: {', '.join(f'{t:.2f} {lab}' for t, lab in random_kills) or 'none'}")

    deadline = time.time() + a.timeout
    threads = [threading.Thread(target=s.loop, args=(deadline,), daemon=True) for s in sups.values()]
    monitor = None
    if a.real:
        monitor = ProcMonitor({lab: o for lab, (o, _) in tiers.items()}, sups, plan, a.monitor_s, a.kill_after_s)
        monitor.start()
        with open(work / "logs" / "trainer.log", "wb") as tlog:
            trainer_proc = subprocess.Popen([sys.executable, str(HERE / "tests" / "replay_trainer.py"), "--commits",
                                             str(a.commits), "--store", str(run_dir.parent), "--run-id", run_dir.name,
                                             "--speed", str(a.speed)], stdout=tlog, stderr=subprocess.STDOUT)
        wall0 = time.time()
    else:
        trainer = Trainer(run_dir, commits, a.speed)
        trainer.start()
        trainer.started.wait()
        wall0 = trainer.wall0
    for t in threads:
        t.start()
    random_hits = 0
    for at, label in random_kills:
        time.sleep(max(0.0, wall0 + at - time.time()))
        pid = sups[label].kill()
        if pid:
            random_hits += 1
            log(f"{label}: random SIGKILL (pid {pid}) at wall {at:.2f} s")
    if a.real:
        trainer_code = trainer_proc.wait(max(1.0, deadline - time.time()))
        log(f"trainer: exit {trainer_code}; {(work / 'logs' / 'trainer.log').read_text().strip().splitlines()[-1:]}")
    else:
        trainer.join()
    for t in threads:
        t.join(max(0.0, deadline - time.time()))
    if monitor:
        time.sleep(0.5)
        monitor.halt.set()
        monitor.join()

    # ---- checks -------------------------------------------------------------------------------------------------
    ok = True

    def check(cond: bool, text: str) -> None:
        nonlocal ok
        ok &= bool(cond)
        log(f"{'PASS' if cond else 'FAIL'} {text}")

    if a.real:
        events = list(monitor.events)
        check(trainer_code == 0, "the real trainer committed every step")
    else:
        events = [json.loads(x) for x in events_path.read_text().splitlines()] if events_path.exists() else []
    starts = {e["pid"]: e for e in events if e["kind"] == "start"}
    ends = {e["pid"] for e in events if e["kind"] == "end"}
    kills = [e for e in events if e["kind"] == "kill"] + proxy_events
    fired = sorted(f"{e['label']}:{e['step']}:{e['moment']}" for e in kills)
    log(f"planned kills fired: {', '.join(fired) or 'none'}; "
        f"random kills that hit a live watcher: {random_hits}")
    for label, (out, every) in tiers.items():
        sup = sups[label]
        check(sup.done.is_set(),
              f"{label}: ended by itself with exit 0 after {len(sup.exits)} start(s); exits {sup.exits}")
        state_path = out / "state.json"
        state = json.loads(state_path.read_text())["checkpoints"] if state_path.exists() else {}
        owned = [c for i, c in enumerate(commits, 1) if i % every == 0]
        last_path = {c["step"]: c["path"] for c in commits}
        check(set(state) == {c["path"] for c in owned},
              f"{label}: state holds exactly the {len(owned)} owned commit(s)")
        bad, n_superseded = [], 0
        for c in owned:
            r = state.get(c["path"], {})
            if r.get("status") == "superseded" and last_path[c["step"]] != c["path"]:
                n_superseded += 1
                continue
            done = r.get("status") == "scored" and (r.get("loaded") if a.clickhouse_url else True)
            try:
                named = json.loads(Path(r["out"]).read_text())["records"][0]["checkpoint"]["path"].endswith(
                    "/" + c["path"])
            except (KeyError, OSError, ValueError, IndexError):
                named = False
            if not (done and named):
                bad.append(c["path"])
        check(not bad, f"{label}: {len(owned) - len(bad) - n_superseded} scored and "
                       f"{'loaded' if a.clickhouse_url else 'parsed'} with a file that names the commit, "
                       f"{n_superseded} superseded{'; not done: ' + ', '.join(bad) if bad else ''}")
        runs = sum(1 for p, e in starts.items() if e["label"] == label and p in ends)
        cut = sum(1 for p, e in starts.items() if e["label"] == label and p not in ends)
        scored = sum(1 for r in state.values() if r.get("status") == "scored")
        kept = sum(1 for r in state.values() if r.get("reused"))
        log(f"{label}: {runs} scorer run(s) finished for {scored} scored commit(s), {kept} of them kept from a "
            f"killed watcher; {runs - scored} extra finished run(s) from kills; {cut} scorer(s) cut off by a kill")
        lags = [r["lag_s"] for r in state.values() if isinstance(r.get("lag_s"), (int, float))]
        if lags:
            log(f"{label}: largest lag from commit to score {max(lags):.2f} s wall = {max(lags) * a.speed:.0f} s of "
                f"run time{' (Tier A rule: 1,800 s)' if every == 1 else ' (Tier B waits for Tier A on the slot)'}")
        if a.clickhouse_url:
            secs = [r["load_seconds"] for r in state.values() if isinstance(r.get("load_seconds"), (int, float))]
            rows = {r["run_id"]: (ch_count(a.clickhouse_url, "eval_mini", r["run_id"]),
                                  ch_count(a.clickhouse_url, "ingest_manifest", r["run_id"]), r["records"])
                    for r in state.values() if r.get("status") == "scored"}
            wrong = {k: v for k, v in rows.items() if v[0] != v[2] or v[1] != 1}
            check(not wrong, f"{label}: each of {len(rows)} run_id(s) holds exactly one result in eval_mini and one "
                             f"ingest_manifest row{' ' + str(wrong) if wrong else ''}")
            if secs:
                log(f"{label}: load_jsonl.py time per checkpoint {sum(secs) / len(secs):.2f} s mean, "
                    f"{max(secs):.2f} s max")
    overlaps = [e for e in events if e["kind"] == "overlap"]
    for e in overlaps:
        log(f"  overlap: {e['label']} step {e['step']} (pid {e['pid']}) started while pid(s) {e['with_pids']} ran")
    check(not overlaps, f"no two scorers ran at the same time on the slot ({len(starts)} scorer start(s))")
    time.sleep(a.score_s + 0.5)
    left = [p for p in starts if p not in ends and alive(p)]
    check(not left, f"no scorer left running{' ' + str(left) if left else ''}")
    watcher_pids = {p for s in sups.values() for p in s.pids}
    hit = {f"{e['label']}:{e['step']}:{e['moment']}" for e in kills if e.get("target") in watcher_pids}
    missed = sorted((plan | load_plan) - hit)
    if a.random_kills == 0:
        check(not missed, f"every planned kill fired at a live watcher ({len(hit)} of {len(plan | load_plan)})"
                          f"{'; missed ' + ', '.join(missed) if missed else ''}")
        check(EXIT_RETRY in sups["tier-a"].exits, "the SIGTERM ended a watcher with exit 75")
    else:
        log(f"planned kills that fired: {len(hit)} of {len(plan | load_plan)}"
            f"{' (cut off by random kills: ' + ', '.join(missed) + ')' if missed else ''}")
    if proxy:
        proxy.shutdown()
    log(f"RESULT {'PASS' if ok else 'FAIL'}")
    if a.work is None:
        shutil.rmtree(work, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
