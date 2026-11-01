"""Run the G9 GPU jobs one at a time, in priority order. Safe to stop and restart.

A job is skipped when its output already exists (results.json for lm-eval, codegen_meta.json for code generation).
lm-eval's request cache (--use_cache) lets an interrupted job resume where it stopped. Each job waits until its model's
verified weights are on disk (fetch_weights.py writes SOURCE.json last).

Usage (from this folder):  python -u run_queue.py [--only eval_mini|gate|all] [--with-bbh]
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from fetch_weights import local_dir
from run_lm_eval import HERE, RUNS

PY = sys.executable
SPEC = HERE / "eval_mini_v0_spec.json"
MODELS = ["qwen2.5-1.5b", "gemma-2-2b", "llama-3.2-3b"]
# Deferred on 25 Oct (lead's decision): week-1 focus is code; MMLU-Pro already covers the gate. Run with --include-deferred.
DEFERRED = {("gemma-2-2b", "gate_milu_Hindi"), ("gemma-2-2b", "gate_milu_Telugu"),
            ("llama-3.2-3b", "gate_milu_English"), ("llama-3.2-3b", "gate_milu_Hindi"), ("llama-3.2-3b", "gate_milu_Telugu")}


def jobs(only, with_bbh):
    q = []
    if only in ("eval_mini", "all"):  # Team 12 needs eval_mini_v0.json on 28 Oct, so these come first
        for m in MODELS:
            q.append((m, "codegen", RUNS / m / "evalplus" / "codegen_meta.json", [PY, "-u", str(HERE / "run_codegen.py"), "--model", m]))
            q.append((m, "eval_mini_v0", RUNS / m / "eval_mini_v0" / "results.json",
                      [PY, "-u", str(HERE / "run_lm_eval.py"), "--model", m, "--samples-file", str(SPEC), "--tag", "eval_mini_v0"]))
    if only in ("gate", "all"):  # full test sets, cheapest-first within each benchmark
        for m in MODELS:
            q.append((m, "gate_leaderboard_mmlu_pro", RUNS / m / "gate_leaderboard_mmlu_pro" / "results.json",
                      [PY, "-u", str(HERE / "run_lm_eval.py"), "--model", m, "--tasks", "leaderboard_mmlu_pro", "--tag", "gate_leaderboard_mmlu_pro"]))
        for m in ("gemma-2-2b", "llama-3.2-3b"):
            for lang in ("English", "Hindi", "Telugu"):
                t = f"milu_{lang}"
                q.append((m, f"gate_{t}", RUNS / m / f"gate_{t}" / "results.json",
                          [PY, "-u", str(HERE / "run_lm_eval.py"), "--model", m, "--tasks", t, "--num-fewshot", "5", "--tag", f"gate_{t}"]))
        if with_bbh:
            for m in MODELS:
                q.append((m, "gate_leaderboard_bbh", RUNS / m / "gate_leaderboard_bbh" / "results.json",
                          [PY, "-u", str(HERE / "run_lm_eval.py"), "--model", m, "--tasks", "leaderboard_bbh", "--tag", "gate_leaderboard_bbh"]))
    return q


def weights_ready(model):
    m = json.loads((HERE / "published_scores.json").read_text(encoding="utf-8"))["models"][model]
    return (local_dir(m["hf_id"], m["revision"]) / "SOURCE.json").exists()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="all", choices=["eval_mini", "gate", "all"])
    ap.add_argument("--with-bbh", action="store_true")
    ap.add_argument("--include-deferred", action="store_true")
    a = ap.parse_args()
    for model, name, done, cmd in jobs(a.only, a.with_bbh):
        if (model, name) in DEFERRED and not a.include_deferred:
            print(f"[{datetime.now():%m-%d %H:%M}] deferred {model}/{name}", flush=True)
            continue
        if done.exists():
            print(f"[{datetime.now():%m-%d %H:%M}] skip {model}/{name} (done)", flush=True)
            continue
        while not weights_ready(model):
            print(f"[{datetime.now():%m-%d %H:%M}] waiting for {model} weights", flush=True)
            time.sleep(300)
        log = RUNS / model / f"{name}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        print(f"[{datetime.now():%m-%d %H:%M}] start {model}/{name} -> {log}", flush=True)
        t0 = time.time()
        with open(log, "a", encoding="utf-8") as f:
            rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"}).returncode
        print(f"[{datetime.now():%m-%d %H:%M}] {'ok' if rc == 0 else f'FAILED rc={rc}'} {model}/{name} in {(time.time() - t0) / 60:.0f} min", flush=True)
    print(f"[{datetime.now():%m-%d %H:%M}] queue finished", flush=True)


if __name__ == "__main__":
    main()
