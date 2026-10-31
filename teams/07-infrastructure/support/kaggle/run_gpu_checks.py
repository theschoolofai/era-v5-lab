"""GPU validation on Kaggle 2 x T4 (ADR 0001 §Validation, ADR 0003 §Validation).

In simple words: the Docker Slurm test proved the logic on CPU. This script runs the parts that need a real
NVIDIA GPU, on Kaggle's free 2-GPU machine, and writes one results file to bring back:
  1. environment   : driver, CUDA, NCCL, GPU model
  2. health check  : real nvidia-smi values (prolog mode), and full mode with the all-reduce test
  3. all-reduce    : NCCL across both GPUs, exact sums, measured bus bandwidth
  4. NCCL timeout  : a stuck GPU becomes a fast, clean failure with a flight-recorder trace
  5. checkpoint    : tests T1-T23 with the trainer on GPU (bit-equal resume on CUDA), DeepSpeed ZeRO-1/2/3 and
                     fp16 included (T18-T23) when DeepSpeed installs (needs Internet on; skipped otherwise)
  6. save speed    : GPU -> host copy and DCP save time, to replace the cost model's assumptions

Run in a Kaggle notebook (Accelerator: GPU T4 x2, Internet: on), from the repo root:
    !python teams/07-infrastructure/support/kaggle/run_gpu_checks.py
Results: /kaggle/working/gpu_results/summary.md (+ summary.json and raw files). Download summary.md.
"""
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.environ.get("V5_GPU_RESULTS", "/kaggle/working/gpu_results" if os.path.isdir("/kaggle") else
                     os.path.join(HERE, "results"))
PY = sys.executable
DS_VERSION = "0.18.0"          # same as support/simulation/slurm-docker/Dockerfile
steps = []


def run(name, cmd, timeout, env=None, cwd=ROOT):
    t0 = time.time()
    e = dict(os.environ, **(env or {}))
    try:
        p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True, timeout=timeout)
        code, out = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired as x:
        code, out = "timeout", (x.stdout or b"").decode(errors="replace") if isinstance(x.stdout, bytes) else str(x.stdout or "")
    except OSError as x:
        code, out = "not_found", str(x)
    with open(os.path.join(OUT, f"{name}.log"), "w") as f:
        f.write(" ".join(cmd) + "\n\n" + out)
    r = {"step": name, "exit": code, "seconds": round(time.time() - t0, 1)}
    print(f"[{time.strftime('%H:%M:%S')}] {name}: exit {code} in {r['seconds']} s", flush=True)
    return r, out


def load(path):
    try:
        return json.load(open(path))
    except (OSError, json.JSONDecodeError):
        return None


def main():
    os.makedirs(OUT, exist_ok=True)
    for mod, pkg in (("yaml", "pyyaml"), ("safetensors", "safetensors"), ("pytest", "pytest")):
        try:
            __import__(mod)
        except ImportError:
            subprocess.run([PY, "-m", "pip", "install", "-q", pkg], check=False)
    import torch  # noqa: E402

    # DeepSpeed, pinned like the cluster image (DS-7). Built without ops (they would compile for minutes);
    # the trainer uses torch's AdamW. No Internet: the DeepSpeed tests skip themselves.
    try:
        import deepspeed  # noqa: F401
    except ImportError:
        subprocess.run([PY, "-m", "pip", "install", "-q", "setuptools", "wheel", "ninja"], check=False)
        subprocess.run([PY, "-m", "pip", "install", "-q", "--no-build-isolation", f"deepspeed=={DS_VERSION}"],
                       env=dict(os.environ, DS_BUILD_OPS="0"), check=False)
    ds = subprocess.run([PY, "-c", "import deepspeed; print(deepspeed.__version__)"], capture_output=True, text=True)
    ds_version = ds.stdout.strip() if ds.returncode == 0 else "not installed (Internet off?)"

    ngpu = torch.cuda.device_count()
    work = os.path.join(OUT, "work")
    os.makedirs(work, exist_ok=True)
    base = {"V5_EVENTS_DIR": os.path.join(work, "events"), "V5_HEALTH_STATE": os.path.join(work, "health"),
            "V5_NVME": work, "V5_NVME_MIN_FREE_GB": "5", "V5_EXPECT_GPUS": str(ngpu), "PYTHONWARNINGS": "ignore"}

    # 1. environment
    r, smi = run("env_nvidia_smi", ["nvidia-smi"], 60)
    env = {"gpus": ngpu, "gpu_name": torch.cuda.get_device_name(0) if ngpu else None, "torch": torch.__version__,
           "cuda": torch.version.cuda, "nccl": ".".join(map(str, torch.cuda.nccl.version())) if ngpu else None,
           "deepspeed": ds_version,
           "driver": next((l.split("Driver Version:")[1].split()[0] for l in smi.splitlines() if "Driver Version" in l), None)}
    r["result"] = env
    steps.append(r)
    if ngpu < 1:
        print("No GPU found. In Kaggle: Settings -> Accelerator -> GPU T4 x2.")

    # 2. health check: prolog (quick) and full (adds DCGM if present and the all-reduce sweep)
    for mode in ("prolog", "full"):
        out = os.path.join(OUT, f"health_{mode}.json")
        r, _ = run(f"health_{mode}", [PY, "health/health_check.py", "--mode", mode, "--report-only", "--out", out],
                   900, base)
        rep = load(out) or {}
        r["result"] = {"verdict": rep.get("verdict"), "runtime_s": rep.get("runtime_seconds"),
                       "checks": {c["name"] + ("" if c["gpu"] is None else f"[{c['gpu']}]"): c["status"]
                                  for c in rep.get("checks", [])}}
        steps.append(r)

    # 3. the four collectives across all GPUs; if NCCL peer-to-peer hangs on this host, retry without it
    out = os.path.join(OUT, "allreduce.json")
    cmd = [PY, "-m", "torch.distributed.run", "--standalone", f"--nproc_per_node={max(ngpu, 1)}",
           "health/allreduce_test.py", "--max-mb", "1024", "--out", out]
    r, _ = run("allreduce", cmd, 300, base)
    if r["exit"] != 0:
        r2, _ = run("allreduce_p2p_off", cmd, 300, dict(base, NCCL_P2P_DISABLE="1"))
        r2["note"] = "retried with NCCL_P2P_DISABLE=1"
        r = r2
    ar = load(out) or {}
    # one entry per collective (all_reduce, reduce_scatter, all_gather, all_to_all): status and busbw by size
    r["result"] = {"status": ar.get("status"), "backend": ar.get("backend"), "ranks": ar.get("ranks"),
                   "ops": {o["op"]: {"status": o["status"], "detail": o["detail"],
                                     "busbw_gbps_by_mb": {x["bytes"] // 2 ** 20: x["busbw_gbps"] for x in o["metrics"]["sizes"]}}
                           for o in ar.get("ops", [])}}
    steps.append(r)

    # 4. NCCL timeout: a stuck rank must turn into a clean failure (needs 2 GPUs)
    if ngpu >= 2:
        out = os.path.join(OUT, "nccl_timeout.json")
        r, _ = run("nccl_timeout", [PY, "-m", "torch.distributed.run", "--standalone", "--nproc_per_node=2",
                                    "support/kaggle/nccl_timeout_test.py", "--timeout-s", "20", "--out", out], 300, base)
        r["result"] = load(out)
        steps.append(r)

    # 5. checkpoint tests with the trainer on GPU
    junit = os.path.join(OUT, "ckpt_tests.xml")
    r, _ = run("ckpt_tests_cuda", [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-W", "ignore", "-rA",
                                   f"--junitxml={junit}", "support/tests/test_ckpt.py"], 1800, dict(base, V5_DEVICE="cuda"))
    r["result"] = junit_summary(junit)
    steps.append(r)

    # 6. save speed on this GPU and disk
    out = os.path.join(OUT, "bench_save.json")
    r, _ = run("bench_save", [PY, "support/tools/bench_save.py", "--sizes-gb", "0.5", "1", "2", "--dir", work, "--out", out],
               900, base)
    r["result"] = load(out)
    steps.append(r)

    shutil.rmtree(work, ignore_errors=True)
    json.dump({"env": env, "steps": steps}, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    write_md(env)
    print(f"\nDone. Download {os.path.join(OUT, 'summary.md')} (and summary.json).")
    return 0


def junit_summary(path):
    import xml.etree.ElementTree as ET
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return None
    cases = {}
    for tc in root.iter("testcase"):
        st = "pass"
        for tag in ("failure", "error", "skipped"):
            el = tc.find(tag)
            if el is not None:
                st = {"failure": "FAIL", "error": "ERROR", "skipped": "skip"}[tag] + \
                     (f": {(el.get('message') or '')[:200]}" if tag != "skipped" else "")
        cases[tc.get("name")] = st
    return cases


def write_md(env):
    L = ["# GPU validation results (Kaggle)", "",
         f"Generated by `support/kaggle/run_gpu_checks.py` on {time.strftime('%Y-%m-%d %H:%M %Z')}.", "",
         f"- GPUs: {env['gpus']} × {env['gpu_name']}; driver {env['driver']}; CUDA {env['cuda']}; "
         f"NCCL {env['nccl']}; torch {env['torch']}; DeepSpeed {env['deepspeed']}", "", "| Step | Exit | Seconds | Result |", "|---|---|---|---|"]
    for s in steps:
        res = json.dumps(s.get("result"))[:1500].replace("|", "\\|")
        L.append(f"| {s['step']} | {s['exit']} | {s['seconds']} | `{res}` |")
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
