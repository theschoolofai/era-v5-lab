"""Node health check: one JSON report and one verdict (ADR 0003).

In simple words: before a job starts on a node, and every 30 s while nodes run, we check the GPUs
(errors, temperature, memory faults), the kernel log, the disk, the memory and the clock. A broken
node is taken out of service before it can waste paid GPU hours by crashing or slowing the main run.
A tool that is missing gives "skipped" with the reason: it is never counted as a pass.

Modes:
  --mode prolog    quick checks + DCGM diag level 1, for the Slurm prolog (budget 30 s; GPUs are idle here)
  --mode periodic  quick checks + DCGM health watches, for Slurm's HealthCheckProgram (GPUs may be busy)
  --mode full      adds DCGM diag level 2 and the all-reduce sweep (before dry runs, after a repair)

Why periodic mode never runs `dcgmi diag`: diag puts its own load on the GPUs, and NVIDIA advises not to run
it while a job uses them. On a busy GPU it can report a false "fail", which would drain the node and requeue
the main run, again and again. `dcgmi health -c` only reads the counters DCGM already watches: cheap and safe.
  --report-only    print the report, take no action

Exit codes (never 1 or 75, which belong to training jobs):
  0 pass   3 warn   4 fail
  In prolog mode a warn exits 0, because Slurm drains a node whose prolog exits non-zero.
"""
import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from common.events import emit, utc_now  # noqa: E402
from health import xid_scan  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "queue"))
import job_queue  # noqa: E402  (drain the node, ask its jobs to save)

STATE_DIR = os.environ.get("V5_HEALTH_STATE", "/var/lib/v5-health")
EXIT = {"pass": 0, "warn": 3, "fail": 4}


def check(name, status, detail="", required=False, metrics=None, gpu=None, seconds=0.0):
    return {"name": name, "status": status, "required": required, "detail": detail,
            "metrics": metrics or {}, "gpu": gpu, "seconds": round(seconds, 3)}


def timed(fn, *a):
    t0 = time.monotonic()
    out = fn(*a)
    for c in out:
        c["seconds"] = round(time.monotonic() - t0, 3)
    return out


def run(cmd, timeout=60):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return subprocess.CompletedProcess(cmd, 124, "", str(e))


GPU_FIELDS = ["index", "temperature.gpu", "power.draw", "ecc.errors.uncorrected.volatile.total",
              "ecc.errors.uncorrected.aggregate.total", "ecc.errors.corrected.volatile.total",
              "clocks_throttle_reasons.hw_slowdown", "pcie.link.width.current", "pcie.link.width.max"]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def gpu_checks(th, expect, fixture=None) -> list:
    req = expect > 0
    if fixture is None and not shutil.which("nvidia-smi"):
        return [check("gpu_inventory", "skipped", "nvidia-smi not found", required=req)]
    if fixture:
        out = open(fixture).read()
    else:
        p = run(["nvidia-smi", f"--query-gpu={','.join(GPU_FIELDS)}", "--format=csv,noheader,nounits"])
        if p.returncode != 0:
            # Drivers >= 535 renamed clocks_throttle_reasons.* to clocks_event_reasons.*
            alt = [f.replace("clocks_throttle_reasons", "clocks_event_reasons") for f in GPU_FIELDS]
            p = run(["nvidia-smi", f"--query-gpu={','.join(alt)}", "--format=csv,noheader,nounits"])
            if p.returncode != 0:
                return [check("gpu_inventory", "fail" if req else "skipped",
                              f"nvidia-smi failed: {p.stderr[:200]}", required=req)]
        out = p.stdout
    lines = out.strip().splitlines()
    rows = [dict(zip(GPU_FIELDS, [x.strip() for x in line.split(",")])) for line in lines]
    g = th["gpu"]
    # Names and metrics follow Team 08's v5-health/1 contract (gpu_inventory: count + one line per GPU)
    res = [check("gpu_inventory", "pass" if len(rows) == expect or not req else "fail",
                 f"{len(rows)} GPUs, expected {expect}", required=req,
                 metrics={"count": len(rows), "gpus": [l.strip() for l in lines]})]
    unc_all, cor_all = [], []
    for r in rows:
        i = int(r["index"])
        t = num(r["temperature.gpu"])
        if t is not None:
            st = "fail" if t >= g["temp_fail_c"] else "warn" if t >= g["temp_warn_c"] else "pass"
            res.append(check("gpu_temperature", st, f"{t} C", required=req, gpu=i, metrics={"temp_c": t}))
        unc = max(num(r["ecc.errors.uncorrected.volatile.total"]) or 0,
                  num(r["ecc.errors.uncorrected.aggregate.total"]) or 0)
        unc_all.append(int(unc))
        cor_all.append(num(r["ecc.errors.corrected.volatile.total"]))
        if r.get("clocks_throttle_reasons.hw_slowdown", "").lower() == "active":
            res.append(check("gpu_throttle", "warn", "hardware slowdown active", gpu=i))
        cur, mx = num(r["pcie.link.width.current"]), num(r["pcie.link.width.max"])
        if cur and mx:
            res.append(check("pcie_link", "warn" if cur / mx < g["pcie_width_min_ratio"] else "pass",
                             f"x{int(cur)} of x{int(mx)}", gpu=i))
    if rows:
        # one check for the node, one value per GPU (Team 08's contract); the detail names the bad GPUs
        bad = [i for i, u in enumerate(unc_all) if u >= g["ecc_uncorrectable_fail"]]
        res.append(check("ecc_uncorrectable", "fail" if bad else "pass",
                         f"uncorrectable on GPU {', '.join(f'{i} ({unc_all[i]})' for i in bad)}" if bad
                         else "0 uncorrectable", required=req, gpu=bad[0] if len(bad) == 1 else None,
                         metrics={"values": unc_all, "correctable": cor_all}))
    return res


def remap_checks(th, expect) -> list:
    if not shutil.which("nvidia-smi") or expect == 0:
        return []
    p = run(["nvidia-smi", "--query-remapped-rows=gpu_bus_id,remapped_rows.pending,remapped_rows.failure",
             "--format=csv,noheader"])
    if p.returncode != 0:
        return [check("remapped_rows", "skipped", "query not supported on this GPU")]
    res = []
    for i, line in enumerate(p.stdout.strip().splitlines()):
        parts = [x.strip().lower() for x in line.split(",")]
        if len(parts) < 3 or "n/a" in parts[1] or "not supported" in line.lower():
            res.append(check("remapped_rows", "skipped", "row remapping not supported on this GPU", gpu=i))
            continue
        pending, failure = parts[1] in ("yes", "1"), parts[2] in ("yes", "1")
        st = "fail" if failure else "warn" if pending else "pass"
        res.append(check("remapped_rows", st, f"pending={pending} failure={failure}", gpu=i, required=True))
    return res


def nvlink_checks(th, expect, fixture=None) -> list:
    """Inactive NVLink links (millermuttu's check, team 07). A down link does not raise an error: all-reduce just
    runs at half speed for the whole run. Without DCGM nothing else would see it."""
    if expect == 0 and fixture is None:
        return []
    if fixture:
        out = open(fixture).read()
    else:
        if not shutil.which("nvidia-smi"):
            return [check("nvlink", "skipped", "nvidia-smi not found")]
        p = run(["nvidia-smi", "nvlink", "-s"])
        if p.returncode != 0:
            return [check("nvlink", "skipped", f"nvidia-smi nvlink failed: {p.stderr[:120]}")]
        out = p.stdout
    links = [l for l in out.splitlines() if re.search(r"\bLink \d+:", l)]
    if not links:
        return [check("nvlink", "skipped", "no NVLink on this GPU (e.g. PCIe cards)")]
    down = [l.strip() for l in links if "inactive" in l.lower()]
    st = "fail" if len(down) >= th["nccl"].get("nvlink_inactive_fail", 1) else "pass"
    return [check("nvlink", st, f"{len(down)} of {len(links)} links inactive", required=True,
                  metrics={"links": len(links), "inactive": len(down), "down": down[:8]})]


def dcgm_check(level) -> list:
    if not shutil.which("dcgmi"):
        return [check("dcgm_diag", "skipped", "dcgmi not found")]
    p = run(["dcgmi", "diag", "-r", str(level), "-j"], timeout=1800)
    if p.returncode != 0:
        return [check("dcgm_diag", "fail", f"dcgmi diag -r {level} exit {p.returncode}", required=True)]
    return [check("dcgm_diag", "fail" if '"Fail"' in p.stdout else "pass", f"level {level}", required=True)]


def dcgm_health_check() -> list:
    """Read DCGM's background health watches (PCIe, memory, NVLink, thermal, power). No load on the GPUs."""
    if not shutil.which("dcgmi"):
        return [check("dcgm_health", "skipped", "dcgmi not found")]
    run(["dcgmi", "health", "-s", "a"], timeout=30)  # turn the watches on (no-op if they already are)
    p = run(["dcgmi", "health", "-c", "-j"], timeout=30)
    if p.returncode != 0:
        return [check("dcgm_health", "warn", f"dcgmi health -c exit {p.returncode}")]  # tool trouble: never drain
    if '"Failure"' in p.stdout:
        return [check("dcgm_health", "fail", "DCGM health watch reports Failure", required=True)]
    return [check("dcgm_health", "warn" if '"Warning"' in p.stdout else "pass", "health watches", required=True)]


def xid_check(th, log=None) -> list:
    lines, source = xid_scan.read_kernel_log(log)
    if not source:
        return [check("xid", "skipped", "no kernel log readable (needs root, or no dmesg)")]
    r = xid_scan.scan(lines, th["xid"], os.path.join(STATE_DIR, "xid_seen.json"))
    codes = sorted({x["xid"] for x in r["new"]})
    return [check("xid", r["status"], f"new Xid codes {codes}" if codes else "no new Xid",
                  metrics={"counts": r["counts"], "events": r["events"], "new": r["new"],
                           "already_seen": r["already_seen"]})]


def clock_check(th) -> list:
    if not shutil.which("chronyc"):
        return [check("clock_offset", "skipped", "chronyc not found")]
    p = run(["chronyc", "tracking"])
    m = re.search(r"System time\s*:\s*([\d.]+) seconds", p.stdout)
    if not m:
        return [check("clock_offset", "skipped", "chrony not synchronised or not running")]
    ms = float(m.group(1)) * 1000
    h = th["host"]
    st = "fail" if ms > h["clock_offset_fail_ms"] else "warn" if ms > h["clock_offset_warn_ms"] else "pass"
    return [check("clock_offset", st, f"{ms:.1f} ms", metrics={"offset_ms": ms})]


def disk_mem_checks(th) -> list:
    h = th["host"]
    res = []
    path = os.environ.get("V5_NVME", "/nvme")
    if os.path.isdir(path):
        free = shutil.disk_usage(path).free / 2 ** 30
        need = float(os.environ.get("V5_NVME_MIN_FREE_GB", h["nvme_min_free_gb"]))
        res.append(check("nvme_free", "fail" if free < need else "pass", f"{free:.1f} GiB free, need {need}",
                         metrics={"free_gb": round(free, 2), "need_gb": need}))
    else:
        res.append(check("nvme_free", "skipped", f"{path} not present"))
    try:
        mem = {k: int(v.split()[0]) for k, v in (l.split(":", 1) for l in open("/proc/meminfo"))}
        avail = mem["MemAvailable"] / 2 ** 20
        need = float(os.environ.get("V5_MEM_MIN_GB", h["mem_min_available_gb"]))
        res.append(check("host_mem", "warn" if avail < need else "pass", f"{avail:.1f} GiB available",
                         metrics={"available_gb": round(avail, 2)}))
    except OSError:
        res.append(check("host_mem", "skipped", "/proc/meminfo not readable (not Linux)"))
    return res


def drill_check() -> list:
    """Test only: a file that forces a fail, to rehearse drain-and-replace (ADR 0002 §10)."""
    p = os.path.join(STATE_DIR, "force_fail")
    if os.path.exists(p):
        why = open(p).read().strip() or "forced fail (drill)"
        return [check("drill_force_fail", "fail", why, required=True)]
    return []


def allreduce_check(th, expect) -> list:
    nproc = max(expect, 2) if expect else 2
    out = os.path.join(STATE_DIR, "allreduce.json")
    max_mb = os.environ.get("V5_COLL_MAX_MB", "1024" if expect else "16")   # Docker test: 16 MB on CPU
    ops = ",".join(th["nccl"].get("ops", ["all_reduce", "reduce_scatter", "all_gather", "all_to_all"]))
    if os.path.exists(out):
        os.remove(out)
    p = run([sys.executable, "-m", "torch.distributed.run", "--standalone", f"--nproc_per_node={nproc}",
             os.path.join(HERE, "allreduce_test.py"), "--max-mb", max_mb, "--ops", ops, "--out", out],
            timeout=th["nccl"]["timeout_s"])
    # torchrun exits 1 whenever a worker exits non-zero, so the exit code cannot tell a wrong value (the test
    # wrote its JSON) from a hang or crash (no JSON). The JSON decides; the old one is removed first.
    if not os.path.exists(out):
        return [check("nccl_collectives", "fail", f"test did not finish (exit {p.returncode})", required=True)]
    return collective_checks(json.load(open(out)))


def collective_checks(r) -> list:
    """One check per collective: all-reduce (DDP), reduce-scatter / all-gather (ZeRO, FSDP), all-to-all (MoE)."""
    return [check(o["name"], o["status"], f"{r['backend']} x{r['ranks']}: {o['detail']}", required=True,
                  metrics=dict(o["metrics"], backend=r["backend"], world_size=r["ranks"], status=o["status"]))
            for o in r["ops"]]


def verdict(checks) -> str:
    if any(c["status"] == "fail" for c in checks):
        return "fail"
    if any(c["status"] == "warn" or (c["status"] == "skipped" and c["required"]) for c in checks):
        return "warn"
    return "pass"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["prolog", "periodic", "full"], default="periodic")
    ap.add_argument("--report-only", action="store_true", help="never drain or signal")
    ap.add_argument("--thresholds", default=os.path.join(HERE, "thresholds.yaml"))
    ap.add_argument("--kernel-log", help="read this file instead of dmesg (tests)")
    ap.add_argument("--nvidia-smi-fixture", help="read nvidia-smi CSV from this file (tests)")
    ap.add_argument("--nvlink-fixture", help="read `nvidia-smi nvlink -s` output from this file (tests)")
    ap.add_argument("--out", help="also write the JSON report here")
    a = ap.parse_args(argv)
    os.makedirs(STATE_DIR, exist_ok=True)

    th = yaml.safe_load(open(a.thresholds))
    expect = int(os.environ.get("V5_EXPECT_GPUS", th["expect_gpus"]))
    t0 = time.monotonic()
    checks = []
    checks += timed(gpu_checks, th, expect, a.nvidia_smi_fixture)
    checks += timed(remap_checks, th, expect)
    checks += timed(nvlink_checks, th, expect, a.nvlink_fixture)
    checks += timed(xid_check, th, a.kernel_log)
    checks += timed(clock_check, th)
    checks += timed(disk_mem_checks, th)
    checks += drill_check()
    if a.mode == "full":
        checks += timed(dcgm_check, 2)
        checks += timed(allreduce_check, th, expect)
    elif a.mode == "prolog" and expect:
        checks += timed(dcgm_check, 1)      # GPUs are idle before the job starts
    elif expect:
        checks += timed(dcgm_health_check)  # periodic: the GPUs may be training

    v = verdict(checks)
    failed = [c for c in checks if c["status"] == "fail"]
    reason = ",".join(sorted({c["name"] for c in failed})) or None
    inv = next((c for c in checks if c["name"] == "gpu_inventory"), None)
    # admit_training says what the prolog does: a job starts unless the verdict is fail (a warn is visible, not a
    # stop), and on a GPU node only when the GPUs were counted
    admit = v != "fail" and (expect == 0 or (inv is not None and inv["status"] == "pass"))
    now = utc_now()
    report = {"schema": "v5-health/1", "timestamp_utc": now, "time": now, "host": socket.gethostname(),
              "mode": a.mode, "expected_gpus": expect, "checks": checks, "verdict": v,
              "admit_training": admit, "drain_reason": reason,
              "runtime_seconds": round(time.monotonic() - t0, 3)}
    emit("health.report", mode=a.mode, verdict=v, drain_reason=reason, runtime_seconds=report["runtime_seconds"],
         failed=[c["name"] for c in failed], warned=[c["name"] for c in checks if c["status"] == "warn"],
         skipped_required=[c["name"] for c in checks if c["status"] == "skipped" and c["required"]])
    text = json.dumps(report, indent=1)
    print(text)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text)

    if v == "fail" and not a.report_only and a.mode == "periodic":
        # Prolog failures are drained by Slurm itself; the periodic check drains and moves jobs off.
        job_queue.drain(reason)
        job_queue.ask_jobs_to_save_and_stop(why=f"health:{reason}")
    if a.mode == "prolog":
        return 4 if v == "fail" else 0
    return EXIT[v]


if __name__ == "__main__":
    sys.exit(main())
