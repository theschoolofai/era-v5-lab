"""Health check tests (ADR 0003 §Validation). Run: python -m pytest -q health/test_health.py"""
import json
import os
import subprocess
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.join(HERE, "..", "..")
sys.path.insert(0, SUB)
from health import health_check, xid_scan  # noqa: E402

TH = yaml.safe_load(open(os.path.join(SUB, "health", "thresholds.yaml")))
FIX = os.path.join(HERE, "fixtures", "health")


def test_xid_classes_and_no_second_drain(tmp_path):
    lines = open(os.path.join(FIX, "kernel_xid.log")).read().splitlines()
    state = str(tmp_path / "seen.json")
    first = xid_scan.scan(lines, TH["xid"], state)
    assert first["status"] == "fail"
    assert {(x["xid"], x["class"]) for x in first["new"]} == {(13, "warn"), (79, "fatal"), (94, "restart"),
                                                              (157, "unknown")}
    again = xid_scan.scan(lines, TH["xid"], state)   # same log after a repair/reboot: no new drain
    assert again["status"] == "pass" and again["already_seen"] == 4


def test_gpu_fixture_findings():
    res = health_check.gpu_checks(TH, 8, os.path.join(FIX, "nvidia_smi_bad.csv"))
    by = {(c["name"], c["gpu"]): c["status"] for c in res}
    assert by[("ecc_uncorrectable", 3)] == "fail"
    assert by[("gpu_temperature", 2)] == "warn" and by[("gpu_throttle", 2)] == "warn"
    assert by[("pcie_link", 4)] == "warn"
    assert health_check.verdict(res) == "fail"


def test_missing_tools_are_skipped_never_pass(tmp_path, monkeypatch):
    monkeypatch.setenv("V5_HEALTH_STATE", str(tmp_path))
    monkeypatch.setattr(health_check, "STATE_DIR", str(tmp_path))
    monkeypatch.setenv("PATH", "/nonexistent")
    res = health_check.gpu_checks(TH, 8)
    assert res[0]["status"] == "skipped" and res[0]["required"]
    assert health_check.verdict(res) == "warn"          # a required check we could not run is not a pass
    assert health_check.verdict(health_check.gpu_checks(TH, 0)) == "pass"  # CPU node: not required


def test_prolog_warn_exits_zero(tmp_path, monkeypatch):
    monkeypatch.setenv("V5_EXPECT_GPUS", "8")      # GPU node with no nvidia-smi -> warn
    monkeypatch.setattr(health_check, "STATE_DIR", str(tmp_path))
    assert health_check.main(["--mode", "prolog", "--report-only", "--kernel-log", os.devnull]) == 0
    assert health_check.main(["--mode", "periodic", "--report-only", "--kernel-log", os.devnull]) == 3


def test_forced_fail_and_schema(tmp_path, monkeypatch):
    monkeypatch.setenv("V5_EXPECT_GPUS", "0")
    monkeypatch.setattr(health_check, "STATE_DIR", str(tmp_path))
    (tmp_path / "force_fail").write_text("drill: GPU 3 Xid 79")
    out = tmp_path / "r.json"
    code = health_check.main(["--mode", "prolog", "--report-only", "--kernel-log", os.devnull, "--out", str(out)])
    r = json.load(open(out))
    assert code == 4 and r["verdict"] == "fail" and r["drain_reason"] == "drill_force_fail"
    assert set(r) == {"schema", "timestamp_utc", "time", "host", "mode", "expected_gpus", "checks", "verdict",
                      "admit_training", "drain_reason", "runtime_seconds"}
    assert r["admit_training"] is False
    assert all(c["status"] in ("pass", "warn", "fail", "skipped") for c in r["checks"])


def collectives(tmp_path, ranks, env=None):
    out = tmp_path / f"coll{ranks}.json"
    import socket
    with socket.socket() as so:         # 127.0.0.1, not --standalone: a .local host name may not resolve
        so.bind(("127.0.0.1", 0))
        port = str(so.getsockname()[1])
    p = subprocess.run([sys.executable, "-m", "torch.distributed.run", "--master-addr", "127.0.0.1",
                        "--master-port", port, f"--nproc_per_node={ranks}",
                        os.path.join(SUB, "health", "allreduce_test.py"), "--max-mb", "2", "--iters", "3",
                        "--out", str(out)],
                       capture_output=True, text=True, timeout=180, env=dict(os.environ, **(env or {})))
    return p.returncode, json.load(open(out))


def test_four_collectives_exact_on_gloo(tmp_path):
    """All-reduce, reduce-scatter, all-gather and all-to-all (millermuttu's set): exact values on 2 and 3 ranks."""
    for ranks in (2, 3):
        rc, r = collectives(tmp_path, ranks)
        assert rc == 0 and r["status"] == "pass" and r["backend"] == "gloo" and r["ranks"] == ranks
        assert [o["op"] for o in r["ops"]] == ["all_reduce", "reduce_scatter", "all_gather", "all_to_all"]
        assert all(o["status"] == "pass" and all(s["busbw_gbps"] > 0 for s in o["metrics"]["sizes"]) for o in r["ops"])


def test_a_wrong_collective_value_fails(tmp_path):
    rc, r = collectives(tmp_path, 2, {"V5_COLL_CORRUPT": "all_to_all"})
    st = {o["op"]: o["status"] for o in r["ops"]}
    # torchrun reports a failed worker as exit 1; the JSON names the collective
    assert rc != 0 and r["status"] == "fail" and st["all_to_all"] == "fail" and st["all_reduce"] == "pass"


def test_xid94_restart_once_drain_on_repeat(tmp_path):
    """Contained ECC (94): the job restarts and the GPU stays; a second 94 on that GPU within 24 h drains."""
    state = str(tmp_path / "seen.json")
    line = "kernel: NVRM: Xid (PCI:0000:5c:00): 94, pid={}, Contained ECC error."
    assert xid_scan.scan([line.format(1)], TH["xid"], state, now=1000)["status"] == "warn"
    assert xid_scan.scan([line.format(2)], TH["xid"], state, now=2000)["status"] == "fail"
    assert xid_scan.scan([line.format(3)], TH["xid"], str(tmp_path / "s2.json"), now=0)["status"] == "warn"
    later = 2000 + 25 * 3600                       # outside the window: one 94 again is only a warning
    assert xid_scan.scan([line.format(4)], TH["xid"], state, now=later)["status"] == "warn"
    assert xid_scan.scan(["NVRM: Xid (PCI:0000:5c:00): 61, pid=1, breakpoint"], TH["xid"])["status"] == "fail"


def test_nvlink_inactive_link_fails(tmp_path):
    up, down, none = tmp_path / "up", tmp_path / "down", tmp_path / "none"
    up.write_text("GPU 0: NVIDIA GPU\n\t Link 0: 26.562 GB/s\n\t Link 1: 26.562 GB/s\n")
    down.write_text("GPU 0: NVIDIA GPU\n\t Link 0: 26.562 GB/s\n\t Link 1: <inactive>\n")
    none.write_text("GPU 0: GPU\n")
    assert health_check.nvlink_checks(TH, 8, str(up))[0]["status"] == "pass"
    bad = health_check.nvlink_checks(TH, 8, str(down))[0]
    assert bad["status"] == "fail" and bad["metrics"]["inactive"] == 1
    assert health_check.nvlink_checks(TH, 8, str(none))[0]["status"] == "skipped"


def test_periodic_mode_never_runs_dcgm_diag(tmp_path, monkeypatch):
    """diag loads the GPUs; on a training node a false fail would drain it and requeue the main run."""
    bin_dir, log = tmp_path / "bin", tmp_path / "dcgmi.log"
    bin_dir.mkdir()
    (bin_dir / "dcgmi").write_text(f'#!/bin/sh\necho "$@" >> {log}\necho \'{{"Overall Health": "Healthy"}}\'\n')
    (bin_dir / "dcgmi").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    monkeypatch.setenv("V5_EXPECT_GPUS", "8")
    monkeypatch.setattr(health_check, "STATE_DIR", str(tmp_path))
    fx = os.path.join(FIX, "nvidia_smi_bad.csv")
    for mode in ("periodic", "prolog"):
        health_check.main(["--mode", mode, "--report-only", "--nvidia-smi-fixture", fx, "--out", str(tmp_path / mode)])
    calls = log.read_text().splitlines()
    assert calls[:2] == ["health -s a", "health -c -j"]           # periodic: watches only
    assert calls[2:] == ["diag -r 1 -j"]                          # prolog: the GPUs are idle
    rep = json.load(open(tmp_path / "periodic"))
    assert [c["status"] for c in rep["checks"] if c["name"] == "dcgm_health"] == ["pass"]


def test_renamed_throttle_field_is_not_a_failure(monkeypatch):
    """Newer drivers reject clocks_throttle_reasons.*; the retry with clocks_event_reasons.* must be used, not
    reported as a broken GPU (that would drain healthy nodes)."""
    good = "".join(f"{i}, 40, 300.0, 0, 0, 0, Not Active, 16, 16\n" for i in range(8))

    def fake_run(cmd, timeout=60):
        old = any("clocks_throttle_reasons" in c for c in cmd)
        return subprocess.CompletedProcess(cmd, 2 if old else 0, "" if old else good, "unknown field" if old else "")

    monkeypatch.setattr(health_check.shutil, "which", lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(health_check, "run", fake_run)
    res = health_check.gpu_checks(TH, 8)
    assert health_check.verdict(res) == "pass", res


# ---------------------------------------------------------------- Team 08's v5-health/1 contract (lab PR #125)
# Our own copy of the rules in teams/08-monitoring/health-check/health_check.py, so this test does not depend on
# their PR being merged. Two rules are relaxed and marked OPEN: they are under discussion with Team 08.
T8_FATAL = {48, 64, 74, 79, 95, 119, 120}
T8_CONTAINED = {63, 94}


def team08_problems(r):
    p = []
    for k, t in (("schema", str), ("host", str), ("timestamp_utc", str), ("mode", str), ("expected_gpus", int),
                 ("verdict", str), ("admit_training", bool), ("checks", list)):
        if not isinstance(r.get(k), t):
            p.append(f"{k} missing or not {t.__name__}")
    if r.get("schema") != "v5-health/1" or r.get("mode") not in ("prolog", "periodic", "full"):
        p.append("schema or mode")
    checks = r.get("checks") or []
    by = {}
    for c in checks:
        by.setdefault(c["name"], []).append(c)
        if c["status"] not in ("pass", "warn", "fail", "skipped") or not isinstance(c["required"], bool) \
                or not isinstance(c["metrics"], dict):
            p.append(f"{c['name']}: status/required/metrics")
        if c["status"] == "skipped" and not c["detail"].strip():
            p.append(f"{c['name']}: skipped without a reason")
    want = "fail" if any(c["status"] == "fail" for c in checks) else "warn" if any(
        c["status"] == "warn" or (c["status"] == "skipped" and c["required"]) for c in checks) else "pass"
    if r["verdict"] != want:
        p.append(f"verdict {r['verdict']} != {want}")
    inv = by.get("gpu_inventory", [])
    if r["expected_gpus"] > 0:
        if len(inv) != 1:
            p.append("one gpu_inventory check needed when expected_gpus > 0")
        elif inv[0]["status"] == "pass" and inv[0]["metrics"].get("count") != r["expected_gpus"]:
            p.append("gpu_inventory passed with the wrong count")
    if r["admit_training"]:
        if want == "fail":                      # OPEN: their draft also refuses admission on warn
            p.append("admit_training true on fail")
        if r["expected_gpus"] > 0 and (not inv or inv[0]["status"] != "pass"):
            p.append("admit_training true without a passing gpu_inventory")
    if want == "fail" and not (r.get("drain_reason") or "").strip():
        p.append("drain_reason empty on fail")
    for c in by.get("xid", []):
        if c["status"] == "skipped":
            continue
        m = c["metrics"]
        tally = {}
        for e in m["events"]:
            tally[str(e["code"])] = tally.get(str(e["code"]), 0) + 1
            if e["severity"] not in ("warn", "fail") or not e["pci_bdf"].strip():
                p.append(f"xid event {e}")
            if e["code"] in T8_FATAL and e["severity"] != "fail":
                p.append(f"fatal Xid {e['code']} not fail")
        if m["counts"] != tally:
            p.append("xid counts do not match events")
        sev = "fail" if any(e["severity"] == "fail" for e in m["events"]) else "warn" if m["events"] else "pass"
        if c["status"] != sev:
            p.append(f"xid status {c['status']} != {sev}")
    for c in by.get("ecc_uncorrectable", []):
        vals = c["metrics"].get("values")
        if not isinstance(vals, list) or (c["status"] == "pass" and any(v > 0 for v in vals)):
            p.append("ecc_uncorrectable values")
    for c in by.get("nccl_all_reduce", []):
        m = c["metrics"]
        if c["status"] != "pass":
            continue
        if not (m.get("backend") in ("nccl", "gloo") and isinstance(m.get("world_size"), int)
                and m["world_size"] >= 2 and m.get("status") == "pass" and m.get("sizes")):
            p.append("nccl_all_reduce metrics")
        if m.get("backend") != "nccl" and r["expected_gpus"] > 0:   # OPEN: their draft never lets gloo pass
            p.append("gloo collective passed on a GPU node")
        for s in m.get("sizes", []):
            if not all(k in s for k in ("bytes", "seconds", "max_error", "all_ranks_correct")) \
                    or s["all_ranks_correct"] is not True or s["max_error"] != 0:
                p.append(f"nccl_all_reduce size {s}")
    return p


def report(tmp_path, monkeypatch, gpus, *args):
    monkeypatch.setenv("V5_EXPECT_GPUS", str(gpus))
    monkeypatch.setattr(health_check, "STATE_DIR", str(tmp_path))
    out = tmp_path / "r.json"
    health_check.main(["--report-only", "--out", str(out), *args])
    return json.load(open(out))


def test_team08_contract_bad_gpu_node(tmp_path, monkeypatch):
    """GPU node with planted faults (ECC on GPU 3, Xid 79/94/13): valid v5-health/1, fail, not admitted."""
    r = report(tmp_path, monkeypatch, 8, "--mode", "prolog", "--kernel-log", os.path.join(FIX, "kernel_xid.log"),
               "--nvidia-smi-fixture", os.path.join(FIX, "nvidia_smi_bad.csv"))
    assert team08_problems(r) == [], team08_problems(r)
    by = {c["name"]: c for c in r["checks"]}
    assert r["verdict"] == "fail" and r["admit_training"] is False
    assert by["gpu_inventory"]["metrics"]["count"] == len(by["gpu_inventory"]["metrics"]["gpus"])
    assert by["ecc_uncorrectable"]["status"] == "fail" and by["ecc_uncorrectable"]["metrics"]["values"][3] > 0
    ev = {e["code"]: e["severity"] for e in by["xid"]["metrics"]["events"]}
    assert ev[79] == "fail" and ev[94] == "warn" and ev[13] == "warn"


def test_team08_contract_gpu_node_without_tools(tmp_path, monkeypatch):
    """GPU node where nvidia-smi is missing: gpu_inventory skipped (never pass), warn, not admitted."""
    monkeypatch.setenv("PATH", "/nonexistent")
    r = report(tmp_path, monkeypatch, 8, "--mode", "prolog", "--kernel-log", os.devnull)
    assert team08_problems(r) == [], team08_problems(r)
    assert r["verdict"] == "warn" and r["admit_training"] is False


def test_team08_contract_cpu_full_with_collectives(tmp_path, monkeypatch):
    """CPU host, full mode: the four collectives on gloo carry backend, world_size, max_error per size."""
    rc, coll = collectives(tmp_path, 2)     # started like the tests above (no --standalone on a laptop)
    monkeypatch.setattr(health_check, "allreduce_check", lambda th, expect: health_check.collective_checks(coll))
    r = report(tmp_path, monkeypatch, 0, "--mode", "full", "--kernel-log", os.devnull)
    assert team08_problems(r) == [], team08_problems(r)
    ar = next(c for c in r["checks"] if c["name"] == "nccl_all_reduce")
    assert ar["metrics"]["backend"] == "gloo" and ar["metrics"]["world_size"] == 2
    assert all(s["max_error"] == 0 and s["all_ranks_correct"] for s in ar["metrics"]["sizes"])


def test_team08_wrong_collective_has_max_error(tmp_path):
    rc, r = collectives(tmp_path, 2, {"V5_COLL_CORRUPT": "all_reduce"})
    sizes = next(o for o in r["ops"] if o["op"] == "all_reduce")["metrics"]["sizes"]
    assert all(s["max_error"] > 0 and s["all_ranks_correct"] is False for s in sizes)
