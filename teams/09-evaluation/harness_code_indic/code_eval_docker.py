"""Execute evalplus samples (HumanEval+ / MBPP+) in a local Linux container. Same step as code_eval_colab.ipynb, without the upload.

The sandbox that runs model-written code needs Unix signals, so it cannot run on Windows, and running it straight on a
laptop executes model-written code with your own user account. This script runs it in a throwaway container instead:
only the model's evalplus folder is mounted, and the container is removed afterwards. It needs network access once per
run, to install evalplus and download the benchmark tests.

Usage (from this folder, with Docker running), after run_codegen.py:
    python code_eval_docker.py --model qwen2.5-1.5b
    python code_eval_docker.py --model qwen2.5-1.5b --datasets humaneval
    python code_eval_docker.py --model qwen2.5-1.5b --replace     (results from an earlier run are moved to .bak)

Reads   runs/<model>/evalplus/<model>__<dataset>.jsonl
Writes  runs/<model>/evalplus/<model>__<dataset>_eval_results.json   (what compare.py reads)
        runs/<model>/evalplus/code_eval_docker.json                  (image digest, platform, dataset hash, pass counts, timeouts)
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"
IMAGE = "python:3.12-slim"
EVALPLUS = "evalplus==0.3.1"  # the version run_codegen.py and code_eval_colab.ipynb use


def summarise(results_path):
    """Pass counts and timeouts from an evalplus results file. A plus pass needs the base tests to pass too."""
    data = json.loads(results_path.read_text(encoding="utf-8"))
    rows = [v[0] for v in data["eval"].values()]
    base = sum(r["base_status"] == "pass" for r in rows)
    plus = sum(r["base_status"] == "pass" and r["plus_status"] == "pass" for r in rows)
    timeouts = sum("timeout" in (r["base_status"], r["plus_status"]) for r in rows)
    n = len(rows)
    return {"dataset_hash": data.get("hash"), "n": n, "base_pass": base, "plus_pass": plus, "base": round(100 * base / n, 2), "plus": round(100 * plus / n, 2),
            "timeouts": timeouts}


def clear_old_results(folder, model, datasets, replace):
    """evalplus.evaluate loads <model>__<dataset>_eval_results.json when it exists and does not execute the samples again
    ('Load from previous results'), so results from Colab or an earlier run would be reported as this container's. Stop
    when such a file exists; with --replace, move it to .bak first."""
    old = [p for p in (folder / f"{model}__{d}_eval_results.json" for d in datasets) if p.exists()]
    if old and not replace:
        names = ", ".join(p.name for p in old)
        sys.exit(f"results already exist in {folder}: {names}\nevalplus would load them instead of executing the samples. "
                 "Run again with --replace to move them to .bak, or move them yourself.")
    for p in old:
        backup = p.with_name(p.name + ".bak")
        p.replace(backup)
        print(f"moved {p.name} -> {backup.name}", flush=True)


def image_digest():
    """The digest of the image that ran, e.g. python@sha256:...; the tag alone moves over time."""
    out = subprocess.run(["docker", "image", "inspect", "--format", "{{join .RepoDigests \",\"}}", IMAGE],
                         capture_output=True, text=True, timeout=60)
    return out.stdout.strip() or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="key in published_scores.json 'models'")
    ap.add_argument("--datasets", default="humaneval,mbpp")
    ap.add_argument("--memory", default="6g", help="container memory limit")
    ap.add_argument("--replace", action="store_true", help="move existing *_eval_results.json to .bak and execute again")
    a = ap.parse_args()

    folder = RUNS / a.model / "evalplus"
    datasets = [d.strip() for d in a.datasets.split(",") if d.strip()]
    missing = [d for d in datasets if not (folder / f"{a.model}__{d}.jsonl").exists()]
    if missing:
        sys.exit(f"no samples for {', '.join(missing)} in {folder}: run run_codegen.py --model {a.model} first")
    if shutil.which("docker") is None:
        sys.exit("docker not found on PATH: install Docker, or use code_eval_colab.ipynb")
    if subprocess.run(["docker", "info"], capture_output=True, timeout=60).returncode != 0:
        sys.exit("the Docker daemon is not answering: start Docker and try again")
    clear_old_results(folder, a.model, datasets, a.replace)

    steps = [f"pip install -q --root-user-action=ignore {EVALPLUS}",
             "python -c \"import platform; print('platform:', platform.platform())\""]
    steps += [f"evalplus.evaluate --dataset {d} --samples {a.model}__{d}.jsonl" for d in datasets]
    cmd = ["docker", "run", "--rm", "--memory", a.memory, "-v", f"{folder}:/work", "-w", "/work", IMAGE,
           "bash", "-c", " && ".join(steps)]
    print(" ".join(cmd), flush=True)
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(out.stdout[-3000:], out.stderr[-1500:], sep="\n", flush=True)
    if out.returncode != 0:
        sys.exit(f"container exited with code {out.returncode}")

    platform_line = next((line for line in out.stdout.splitlines() if line.startswith("platform:")), "platform: unknown")
    record = {"image": IMAGE, "image_digest": image_digest(), "evalplus": EVALPLUS, "platform": platform_line.split(":", 1)[1].strip(), "results": {}}
    for d in datasets:
        record["results"][d] = summarise(folder / f"{a.model}__{d}_eval_results.json")
        print(d, record["results"][d], flush=True)
    (folder / "code_eval_docker.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
