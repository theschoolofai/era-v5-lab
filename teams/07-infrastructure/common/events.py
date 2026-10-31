"""One JSON line per event, shared by checkpoint, queue and health code (ADR 0002 §8).

In simple words: every part of the system writes what happened, and when, in the same format.
Monitoring (Team 08) and our metrics script read these lines; nobody has to parse free-text logs.

Each process appends to its own file, so two processes never write into the same file at once.
"""
import json
import os
import socket
import time
from datetime import datetime, timezone

SCHEMA = "v5-event/1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_time(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def emit(event: str, **fields) -> dict:
    rec = {
        "schema": SCHEMA,
        "time": utc_now(),
        "host": socket.gethostname(),
        "run_id": os.environ.get("RUN_ID", ""),
        "job_id": os.environ.get("SLURM_JOB_ID", ""),
        "event": event,
        **fields,
    }
    out_dir = os.environ.get("V5_EVENTS_DIR")
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{rec['host']}-{os.getpid()}.jsonl")
        with open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")
    return rec


def read_all(events_dir: str) -> list:
    out = []
    if not os.path.isdir(events_dir):
        return out
    for name in sorted(os.listdir(events_dir)):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(events_dir, name)) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass  # a torn last line from a killed process
    out.sort(key=lambda r: r["time"])
    return out


class Timer:
    def __init__(self):
        self.t0 = time.monotonic()

    def s(self) -> float:
        return round(time.monotonic() - self.t0, 4)
