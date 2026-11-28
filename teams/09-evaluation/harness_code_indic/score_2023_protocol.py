"""Score samples from codegen_2023_protocol.py the way the EvalPlus leaderboard did (issues #334 and #335).

Steps:
  1. keep only the tasks that exist in the current dataset (MBPP+ v0.1.0 had 399 tasks, v0.2.0 has 378)
  2. clean the samples with evalplus's sanitizer of 30 Dec 2023 (tools/sanitize.py at commit d48a1e4)
  3. execute them with evalplus.evaluate 0.3.1 in a Linux container
  4. print the counts and write <name>_summary.json next to the samples

The old sanitizer is not kept in this repo. It is downloaded once from github.com/evalplus/evalplus at the pinned
commit into runs/evalplus_2023_tools/ and checked against a sha256.

Usage:
  python score_2023_protocol.py --samples runs/protocol_2023/phi-2__mbpp.jsonl --dataset mbpp
  python score_2023_protocol.py --samples runs/protocol_2023/qwen__humaneval.jsonl --dataset humaneval \
      --humaneval-file runs/protocol_2023/HumanEvalPlus-v0.1.9.jsonl

--humaneval-file scores against another HumanEval+ release. evalplus 0.3.1 ignores --version for HumanEval+, so
the file is passed through HUMANEVAL_OVERRIDE_PATH. Releases: github.com/evalplus/humanevalplus_release.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS_DIR = HERE / "runs" / "evalplus_2023_tools"
SANITIZER_COMMIT = "d48a1e41fdd416cda9a0549db4d6c41a51f674c6"
RAW_URL = f"https://raw.githubusercontent.com/evalplus/evalplus/{SANITIZER_COMMIT}/tools/"
TOOL_SHA256 = {
    "sanitize.py": "54c0ef2b02af5492fa33700cf57b3182a2cb183513b95b389ee54455520db23f",
    "checker.py": "03748c735742eb82071a3d2c712812a9a856634a1281de36daee4030aaee5575",
}
IMAGE = "python:3.12-slim"
EVALPLUS = "evalplus==0.3.1"
CONTAINER_MEMORY = "6g"
DOWNLOAD_TIMEOUT_S = 60
DOCKER_CHECK_TIMEOUT_S = 30
EVALUATE_TIMEOUT_S = 3600


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch_sanitizer():
    """Download the Dec 2023 sanitizer once, and refuse any file that does not match its pinned hash."""
    package = TOOLS_DIR / "tools"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").touch()
    for name, expected in TOOL_SHA256.items():
        path = package / name
        if not path.exists():
            with urllib.request.urlopen(RAW_URL + name, timeout=DOWNLOAD_TIMEOUT_S) as response:
                path.write_bytes(response.read())
        if sha256(path.read_bytes()) != expected:
            sys.exit(f"{path} does not match the pinned sha256. Delete it and run again.")
    return TOOLS_DIR


def current_task_ids(dataset):
    if dataset == "humaneval":
        from evalplus.data import get_human_eval_plus
        return set(get_human_eval_plus())
    from evalplus.data import get_mbpp_plus
    return set(get_mbpp_plus())


def keep_current_tasks(samples, dataset):
    """Write <name>_current.jsonl with the tasks of the current dataset; stop if any current task has no sample."""
    wanted = current_task_ids(dataset)
    rows = [json.loads(line) for line in samples.read_text(encoding="utf-8").splitlines() if line.strip()]
    kept = [row for row in rows if row["task_id"] in wanted]
    missing = wanted - {row["task_id"] for row in kept}
    if missing:
        sys.exit(f"{len(missing)} tasks have no sample, for example {sorted(missing)[:3]}. Finish the generation first.")
    out = samples.with_name(samples.stem + "_current.jsonl")
    out.write_text("".join(json.dumps(row) + "\n" for row in kept), encoding="utf-8")
    print(f"kept {len(kept)} of {len(rows)} samples", flush=True)
    return out


def sanitize(samples, dataset, tools_dir):
    done = subprocess.run([sys.executable, "-m", "tools.sanitize", "--samples", str(samples), "--dataset", dataset],
                          cwd=tools_dir, capture_output=True, text=True)
    if done.returncode != 0:
        sys.exit(f"the sanitizer failed:\n{done.stderr[-2000:]}")
    print(done.stdout.strip().splitlines()[-1], flush=True)
    return samples.with_name(samples.stem + "-sanitized.jsonl")


def check_docker():
    try:
        done = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"], capture_output=True, text=True,
                              timeout=DOCKER_CHECK_TIMEOUT_S)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        sys.exit("Docker did not answer. Start Docker Desktop (or the Docker service) and run again.")
    if done.returncode != 0:
        sys.exit(f"Docker is not running: {done.stderr.strip()[:300]}")


def evaluate(sanitized, dataset, humaneval_file):
    """Run evalplus.evaluate in a container. Any earlier results file is removed, so evalplus cannot load it."""
    results = sanitized.with_name(sanitized.stem + "_eval_results.json")
    results.unlink(missing_ok=True)
    cmd = ["docker", "run", "--rm", "--memory", CONTAINER_MEMORY, "-v", f"{sanitized.parent}:/work", "-w", "/work"]
    if humaneval_file:
        cmd += ["-v", f"{humaneval_file.parent}:/data:ro", "-e", f"HUMANEVAL_OVERRIDE_PATH=/data/{humaneval_file.name}"]
    cmd += [IMAGE, "bash", "-c", f"pip install -q --root-user-action=ignore {EVALPLUS} && "
            f"evalplus.evaluate --dataset {dataset} --samples {sanitized.name}"]
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=EVALUATE_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        sys.exit(f"the container did not finish in {EVALUATE_TIMEOUT_S} s")
    if done.returncode != 0 or not results.exists():
        sys.exit(f"evalplus.evaluate failed:\n{(done.stdout + done.stderr)[-2000:]}")
    return results


def summarise(results, dataset, humaneval_file):
    data = json.loads(results.read_text(encoding="utf-8"))
    rows = {task_id: runs[0] for task_id, runs in data["eval"].items()}
    base = sorted(t for t, r in rows.items() if r["base_status"] == "pass")
    plus = sorted(t for t in base if rows[t]["plus_status"] == "pass")
    n = len(rows)
    return {
        "dataset": dataset,
        "dataset_hash": data.get("hash"),
        "humaneval_file": humaneval_file.name if humaneval_file else None,
        "n": n,
        "base_pass": len(base),
        "base_pct": round(100 * len(base) / n, 2),
        "plus_pass": len(plus),
        "plus_pct": round(100 * len(plus) / n, 2),
        "timeouts": sum("timeout" in (r["base_status"], r["plus_status"]) for r in rows.values()),
        "base_pass_plus_fail": sorted(set(base) - set(plus)),
        "sanitizer_commit": SANITIZER_COMMIT,
        "evaluator": f"{EVALPLUS} in {IMAGE}",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--samples", required=True, type=Path, help="jsonl from codegen_2023_protocol.py")
    ap.add_argument("--dataset", required=True, choices=["humaneval", "mbpp"])
    ap.add_argument("--humaneval-file", type=Path, help="unzipped HumanEvalPlus.jsonl of another release")
    args = ap.parse_args()

    samples = args.samples.resolve()
    if not samples.is_file():
        sys.exit(f"no such file: {samples}")
    humaneval_file = args.humaneval_file.resolve() if args.humaneval_file else None
    if humaneval_file and (args.dataset != "humaneval" or not humaneval_file.is_file()):
        sys.exit("--humaneval-file needs --dataset humaneval and an existing file")

    check_docker()
    tools_dir = fetch_sanitizer()
    current = keep_current_tasks(samples, args.dataset)
    sanitized = sanitize(current, args.dataset, tools_dir)
    results = evaluate(sanitized, args.dataset, humaneval_file)
    summary = summarise(results, args.dataset, humaneval_file)
    out = samples.with_name(samples.stem + "_summary.json")
    out.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "base_pass_plus_fail"}, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
