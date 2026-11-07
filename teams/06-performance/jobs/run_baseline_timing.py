#!/usr/bin/env python3
"""TSAI job wrapper: time G6 baseline (or a short CPU smoke) and write only under --out.

Usage (repo root):
  python teams/06-performance/jobs/run_baseline_timing.py --out out
  python teams/06-performance/jobs/run_baseline_timing.py --out out --synthetic
  python teams/06-performance/jobs/run_baseline_timing.py --out out --smoke-cpu

No network. Reads configs under teams/06-performance. Writes only under --out.

GPU path (non-smoke): two --repeat 1 clean,layer runs with layer_warmup=20 and a
120s cool-down between them; the second run uses --against the first JSON so the
compare gate still applies without tip-side sleep.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

JOB_DIR = Path(__file__).resolve().parent
PERF_ROOT = JOB_DIR.parent
REPO_ROOT = PERF_ROOT.parents[1]

# Cool-down between the two layer processes to cut thermal hysteresis on
# fwd:block* / opt.muon when the node is warm from a prior long job.
LAYER_COOLDOWN_S = 120
LAYER_WARMUP = 20


def _newest_json(out: Path, tag: str) -> Path | None:
    """Resolve the JSON stem free_path wrote for ``tag`` (tag.json or tag-N.json)."""
    matches = sorted(out.glob(f"{tag}.json")) + sorted(out.glob(f"{tag}-*.json"))
    # Exclude second-run tags that start with ``{tag}-run``.
    matches = [p for p in matches if not p.name.startswith(f"{tag}-run")]
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


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

    config = PERF_ROOT / "configs" / "base.yaml"
    tag = "baseline_v1_job"
    tag2 = f"{tag}-run2"
    base_args = [
        sys.executable, "-m", "perfkit.bench",
        "--config", str(config),
        "--modes", "clean,layer",
        "--level", "3",
        "--repeat", "1",
        f"bench.layer_warmup={LAYER_WARMUP}",
        f"bench.out_dir={out.as_posix()}",
    ]
    if synthetic:
        base_args.append("data.source=synthetic")

    args1 = [*base_args, "--tag", tag]
    print("cwd:", PERF_ROOT)
    print("cmd:", " ".join(args1))
    proc1 = subprocess.run(args1, cwd=str(PERF_ROOT), env=env)
    if proc1.returncode != 0:
        summary = {
            "pass": False,
            "exit_code": proc1.returncode,
            "tag": tag,
            "config": str(config.relative_to(REPO_ROOT)),
            "smoke_cpu": smoke_cpu,
            "synthetic": synthetic,
            "layer_warmup": LAYER_WARMUP,
            "cooldown_s": LAYER_COOLDOWN_S,
            "phase": "run1",
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "out_dir": str(out),
        }
        (out / "result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary))
        return proc1.returncode

    first_json = _newest_json(out, tag)
    if first_json is None or not first_json.is_file():
        print("ERROR: first-run JSON not found under", out, file=sys.stderr)
        return 2

    print(f"cool-down {LAYER_COOLDOWN_S}s between layer processes (thermal hysteresis)…")
    time.sleep(LAYER_COOLDOWN_S)

    args2 = [*base_args, "--tag", tag2, "--against", str(first_json)]
    print("cmd:", " ".join(args2))
    proc2 = subprocess.run(args2, cwd=str(PERF_ROOT), env=env)
    summary = {
        "pass": proc2.returncode == 0,
        "exit_code": proc2.returncode,
        "tag": tag2,
        "against": str(first_json),
        "config": str(config.relative_to(REPO_ROOT)),
        "smoke_cpu": smoke_cpu,
        "synthetic": synthetic,
        "layer_warmup": LAYER_WARMUP,
        "cooldown_s": LAYER_COOLDOWN_S,
        "phase": "run2",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "out_dir": str(out),
    }
    (out / "result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return proc2.returncode


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
