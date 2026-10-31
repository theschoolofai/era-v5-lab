"""Scan the kernel log for NVIDIA Xid errors and classify them (ADR 0003 §1).

In simple words: when a GPU breaks, the driver writes an "Xid" line with a number into the kernel log.
Some numbers mean "this GPU is broken, take the node out" (fatal), some mean "watch it" (warn), and some
mean "the job died but the GPU recovered" (restart): Xid 94, a contained ECC error. NVIDIA says the application
should restart and the GPU can stay in service, so one 94 is a warning; the same GPU logging it again within
`restart_window_h` hours is a failing GPU and drains the node.
We remember which lines we already saw, so an old error does not take a repaired node out again.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

XID_RE = re.compile(r"NVRM: Xid \(PCI:([0-9A-Fa-f:.]+)\): (\d+)(?:, (.*))?")


def read_kernel_log(path: str = None) -> tuple:
    """Returns (lines, source). source is None when no log can be read (laptop, Colab, no root)."""
    if path:
        with open(path) as f:
            return f.read().splitlines(), path
    for cmd in (["journalctl", "-k", "-o", "short-iso", "--no-pager", "-q"], ["dmesg", "-T"]):
        if shutil.which(cmd[0]):
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                if p.returncode == 0 and p.stdout:
                    return p.stdout.splitlines(), " ".join(cmd[:2])
            except (OSError, subprocess.TimeoutExpired):
                pass
    return [], None


def classify(code: int, table: dict) -> str:
    if code in table.get("fatal", []):
        return "fatal"
    if code in table.get("restart", []):
        return "restart"
    if code in table.get("warn", []):
        return "warn"
    return "unknown"


def scan(lines, table: dict, state_path: str = None, now: float = None) -> dict:
    now = time.time() if now is None else now
    seen, history = set(), {}
    if state_path and os.path.exists(state_path):
        with open(state_path) as f:
            st = json.load(f)
        if isinstance(st, list):          # state written before the "restart" class existed
            st = {"seen": st}
        seen, history = set(st.get("seen", [])), st.get("restart", {})
    window = float(table.get("restart_window_h", 24)) * 3600
    history = {k: [t for t in v if now - t < window] for k, v in history.items()}
    new, old = [], []
    for line in lines:
        m = XID_RE.search(line)
        if not m:
            continue
        h = hashlib.sha256(line.encode()).hexdigest()[:16]
        code = int(m.group(2))
        rec = {"pci": m.group(1), "xid": code, "class": classify(code, table), "text": (m.group(3) or "")[:120]}
        if h not in seen and rec["class"] == "restart":
            k = f"{rec['pci']}:{code}"
            history.setdefault(k, []).append(now)
            rec["repeats_in_window"] = len(history[k])
        (old if h in seen else new).append(rec)
        seen.add(h)
    if state_path:
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w") as f:
            json.dump({"seen": sorted(seen)[-5000:], "restart": {k: v for k, v in history.items() if v}}, f)
    worst = "pass"
    if any(r["class"] in ("warn", "unknown", "restart") for r in new):
        worst = "warn"     # an unknown code is reported as warn, never ignored
    if any(r["class"] == "fatal" or r.get("repeats_in_window", 0) >= 2 for r in new):
        worst = "fail"
    return {"status": worst, "new": new, "already_seen": len(old)}


def main():
    import yaml
    ap = argparse.ArgumentParser()
    ap.add_argument("log", nargs="?", help="a saved kernel log; default: journalctl -k or dmesg")
    ap.add_argument("--state", help="file that remembers lines already seen")
    ap.add_argument("--thresholds", default=os.path.join(os.path.dirname(__file__), "thresholds.yaml"))
    a = ap.parse_args()
    table = yaml.safe_load(open(a.thresholds))["xid"]
    lines, source = read_kernel_log(a.log)
    out = scan(lines, table, a.state) if source else {"status": "skipped", "reason": "no kernel log readable"}
    print(json.dumps(out, indent=1))
    return {"pass": 0, "warn": 3, "fail": 4, "skipped": 0}[out["status"]]


if __name__ == "__main__":
    sys.exit(main())
