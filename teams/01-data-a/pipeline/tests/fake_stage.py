"""Stand-in for clean_job.py, overlap.py and dedup.py in the runner's tests.

It takes the command line the runner gives them (--config, and for clean one --only per part), copies the folder named by
"fixture" in the config to the output folder, and prints what it was given (the runner's log keeps it). The output folder is
the config's "out" (overlap, dedup) or "output_root" (clean), relative to the working directory, the repository root, as the
real scripts read it. Like the real clean job it refuses an output folder that already exists.
"""
import argparse, json, shutil
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--config", type=Path, required=True)
ap.add_argument("--only", action="append", default=[])
a = ap.parse_args()
cfg = json.loads(a.config.read_text(encoding="utf-8"))
out = Path(cfg.get("out") or cfg["output_root"])
shutil.copytree(cfg["fixture"], out)
print(json.dumps({"config": a.config.as_posix(), "out": out.as_posix(), "input_root": cfg.get("input_root"), "only": a.only,
                  "keys": {k: cfg.get(k) for k in ("inputs", "out", "results")}}))
