#!/usr/bin/env python3
"""TSAI job wrapper: time G6 baseline (or a short CPU smoke) and write only under --out.

Usage (repo root):
  python teams/06-performance/jobs/run_baseline_timing.py --out out
  python teams/06-performance/jobs/run_baseline_timing.py --out out --synthetic
  python teams/06-performance/jobs/run_baseline_timing.py --out out --smoke-cpu

No network. Reads configs under teams/06-performance. Writes only under --out.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

JOB_DIR = Path(__file__).resolve().parent
PERF_ROOT = JOB_DIR.parent
REPO_ROOT = PERF_ROOT.parents[1]


def _run_bench(out: Path, *, smoke_cpu: bool, synthetic: bool) -> int:
    out.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PERF_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    if smoke_cpu:
        config = PERF_ROOT / "configs" / "tiny_cpu.yaml"
        tag = "baseline_smoke_cpu"
        args = [
            sys.executable, "-m", "perfkit.bench",
            "--config", str(config),
            "--tag", tag,
            "--modes", "clean",
            "--level", "1",
            "--warmup", "2",
            "--steps", "10",
            "--repeat", "1",
            f"bench.out_dir={out.as_posix()}",
            "data.source=synthetic",
            "run.device=cpu",
            "run.dtype=fp32",
        ]
    else:
        config = PERF_ROOT / "configs" / "base.yaml"
        tag = "baseline_v1_job"
        args = [
            sys.executable, "-m", "perfkit.bench",
            "--config", str(config),
            "--tag", tag,
            "--modes", "clean,layer",
            "--level", "3",
            "--repeat", "2",
            "bench.layer_warmup=10",
            f"bench.out_dir={out.as_posix()}",
        ]
        if synthetic:
            args.append("data.source=synthetic")

    print("cwd:", PERF_ROOT)
    print("cmd:", " ".join(args))
    proc = subprocess.run(args, cwd=str(PERF_ROOT), env=env)
    summary = {
        "pass": proc.returncode == 0,
        "exit_code": proc.returncode,
        "tag": tag,
        "config": str(config.relative_to(REPO_ROOT)),
        "smoke_cpu": smoke_cpu,
        "synthetic": synthetic,
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "out_dir": str(out),
    }
    (out / "result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="out", help="output folder (only write target)")
    ap.add_argument(
        "--smoke-cpu",
        action="store_true",
        help="short synthetic CPU run for the attached test log",
    )
    ap.add_argument(
        "--synthetic",
        action="store_true",
        help="force data.source=synthetic (lab nodes without FineWeb shards)",
    )
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    # JOB_REQUEST rule: write only under ./out when run from the job cwd.
    if out.name != "out" and "out" not in out.parts:
        print("refusing out path that is not under an 'out' folder:", out, file=sys.stderr)
        return 2
    return _run_bench(out, smoke_cpu=a.smoke_cpu, synthetic=a.synthetic)


if __name__ == "__main__":
    raise SystemExit(main())
