#!/usr/bin/env python3
"""Run the G9 ``eval_mini`` task set on one Hugging Face model with lm-evaluation-harness.

Examples (run from the repository root, inside the harness virtualenv):

    python teams/09-evaluation/harness/run_eval_mini.py --model Qwen/Qwen2.5-0.5B --profile mini
    python teams/09-evaluation/harness/run_eval_mini.py --model Qwen/Qwen2.5-0.5B --profile check
    python teams/09-evaluation/harness/run_eval_mini.py --model Qwen/Qwen2.5-0.5B --tasks arc_challenge --limit 5

Outputs, under ``runs/<model_slug>/<profile>/`` (gitignored, never commit):
  <task>_<k>shot.json  raw lm_eval result for that task at k shots (no per-sample logs)
  summary.json         run metadata plus one record per (task, shots, metric, filter), schema eval_mini_v0

``build_results.py`` merges the summaries into ``../results/eval_mini_v0.json`` and ``compare_v0.md``.
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "eval_mini_v0"
DEFAULT_SEED = 42
DEFAULT_BATCH_SIZE = 8
DEFAULT_DTYPE = "bfloat16"
HARNESS_DIR = Path(__file__).resolve().parent
DEFAULT_RUNS_DIR = HARNESS_DIR / "runs"

log = logging.getLogger("eval_mini")


@dataclass(frozen=True)
class TaskSpec:
    """One task of the eval_mini set: the lm_eval task name and the headline metric compare_v0.md uses."""

    name: str
    primary_metric: str
    primary_filter: str = "none"


TASKS: dict[str, TaskSpec] = {
    "arc_challenge": TaskSpec("arc_challenge", "acc_norm"),
    "arc_easy": TaskSpec("arc_easy", "acc_norm"),
    "hellaswag": TaskSpec("hellaswag", "acc_norm"),
    "mmlu": TaskSpec("mmlu", "acc"),
    "gsm8k": TaskSpec("gsm8k", "exact_match", "flexible-extract"),
    "truthfulqa_mc2": TaskSpec("truthfulqa_mc2", "acc"),
}


@dataclass(frozen=True)
class TaskRun:
    """How a profile runs one task: shots in the prompt and items scored (None = the full split)."""

    num_fewshot: int
    limit: int | None


# A profile fixes, per task, the shot count and the number of items. lm_eval takes the FIRST n items, so a
# limited run is reproducible. For ``mmlu`` the limit applies to each of the 57 subjects (10 -> 570 items).
#
# ``mini``  is the cheap, uniform set that other teams rerun on their models and diff against the baseline.
#           Multiple-choice tasks run 0-shot (the lm_eval default and the SmolLM2 setting), because on a laptop
#           GPU a 25-shot ARC prompt costs as much as ~20 zero-shot items and the goal here is a tight relative
#           comparison, not a published-table match. GSM8K keeps 5 shots: base models need the format examples.
# ``check`` runs the full evaluation split in the setting the publishers report, for the within-2-points check:
#           TruthfulQA 0-shot (Qwen2.5 report), GSM8K 5-shot (SmolLM2 card; lm_eval default) and 0-shot ARC
#           Easy + Challenge (SmolLM2 card's "ARC (Average)"). Use ``--num-fewshot`` for one-off variants such as
#           GSM8K 4-shot (Qwen2.5 report); the shot count is part of every record and of the output file name.
PROFILES: dict[str, dict[str, TaskRun]] = {
    "mini": {
        "arc_challenge": TaskRun(num_fewshot=0, limit=500),
        "hellaswag": TaskRun(num_fewshot=0, limit=400),
        "mmlu": TaskRun(num_fewshot=0, limit=10),
        "gsm8k": TaskRun(num_fewshot=5, limit=200),
        "truthfulqa_mc2": TaskRun(num_fewshot=0, limit=200),
    },
    "check": {
        "truthfulqa_mc2": TaskRun(num_fewshot=0, limit=None),
        "gsm8k": TaskRun(num_fewshot=5, limit=None),
        "arc_easy": TaskRun(num_fewshot=0, limit=None),
        "arc_challenge": TaskRun(num_fewshot=0, limit=None),
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="Hugging Face model id, e.g. Qwen/Qwen2.5-0.5B")
    parser.add_argument("--revision", default="main", help="branch, tag or commit; resolved to a commit sha")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="mini")
    parser.add_argument("--tasks", nargs="+", choices=sorted(TASKS), help="subset of the profile's tasks")
    parser.add_argument("--limit", type=int, help="override the profile limit for every task (smoke tests)")
    parser.add_argument("--num-fewshot", type=int, help="override the profile shot count for every task")
    parser.add_argument("--dtype", default=DEFAULT_DTYPE)
    parser.add_argument("--device", default="auto", help="auto | cuda | mps | cpu")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="random, numpy, torch and few-shot seed")
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--max-length", type=int, help="override the model's max context length")
    return parser.parse_args(argv)


def pick_device(requested: str) -> str:
    import torch

    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def describe_hardware(device: str) -> str:
    """Human-readable chip or GPU name for the run metadata."""
    import torch

    if device.startswith("cuda") and torch.cuda.is_available():
        return torch.cuda.get_device_name(0)
    if platform.system() == "Darwin":
        try:
            chip = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, check=True).stdout.strip()
            mem_bytes = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=True).stdout)
            return f"{chip}, {mem_bytes // (1024**3)} GB unified memory ({device})"
        except (subprocess.CalledProcessError, ValueError, OSError):
            pass
    return f"{platform.processor() or platform.machine()} ({device})"


def resolve_revision(model: str, revision: str) -> str:
    """Pin the run to a commit sha so the JSON names exactly which weights were evaluated."""
    try:
        from huggingface_hub import HfApi

        sha = HfApi().model_info(model, revision=revision).sha
        if sha:
            return sha
    except Exception as exc:  # network down, private repo, ...: keep the requested ref and say so
        log.warning("could not resolve %s@%s to a commit sha (%s); recording %r", model, revision, exc, revision)
    return revision


def library_versions() -> dict[str, str]:
    import lm_eval
    import torch
    import transformers

    return {
        "lm_eval": lm_eval.__version__,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "python": platform.python_version(),
    }


def model_slug(model: str) -> str:
    return model.replace("/", "__")


def count_items(results: dict, task: str) -> tuple[int, int]:
    """(effective, original) item counts for a task, summing the leaves of a group task."""
    samples = results.get("n-samples", {})
    if task in samples:
        return int(samples[task]["effective"]), int(samples[task]["original"])
    effective = original = 0
    for child in results.get("group_subtasks", {}).get(task, []):
        eff, orig = count_items(results, child)
        effective += eff
        original += orig
    return effective, original


def extract_records(results: dict, spec: TaskSpec, num_fewshot: int, context: dict) -> list[dict]:
    """One record per (metric, filter) of the task, in the eval_mini_v0 schema."""
    metrics = results["results"].get(spec.name) or results.get("groups", {}).get(spec.name) or {}
    effective, original = count_items(results, spec.name)
    shots = results.get("n-shot", {}).get(spec.name, num_fewshot)
    records = []
    for key, value in metrics.items():
        if key == "alias" or "," not in key or key.split(",")[0].endswith("_stderr"):
            continue
        metric, filt = key.split(",", 1)
        stderr = metrics.get(f"{metric}_stderr,{filt}")
        records.append(
            {
                **context,
                "task": spec.name,
                "metric": metric,
                "filter": filt,
                "value": value,
                "stderr": None if stderr in (None, "N/A") else stderr,
                "n_items": effective,
                "n_items_total": original,
                "num_fewshot": int(shots),
                "primary": metric == spec.primary_metric and filt == spec.primary_filter,
                "task_version": results.get("versions", {}).get(spec.name),
            }
        )
    return records


def strip_for_disk(results: dict) -> dict:
    """Raw harness output without the per-sample logs (we run with log_samples=False anyway)."""
    return {key: value for key, value in results.items() if key != "samples"}


def run_task(lm, spec: TaskSpec, num_fewshot: int, limit: int | None, seed: int) -> tuple[dict, float]:
    from lm_eval import simple_evaluate

    started = time.perf_counter()
    results = simple_evaluate(
        model=lm,
        tasks=[spec.name],
        num_fewshot=num_fewshot or None,  # None keeps a task's own 0-shot config (TruthfulQA)
        limit=limit,
        log_samples=False,
        random_seed=seed,
        numpy_random_seed=seed,
        torch_random_seed=seed,
        fewshot_random_seed=seed,
    )
    return results, time.perf_counter() - started


def apply_generation_cap(lm) -> None:
    """Make lm_eval's 256-token generation cap stick.

    lm_eval passes ``max_length = prompt + max_gen_toks`` to ``generate()``. If the model's generation_config.json
    sets ``max_new_tokens`` (Qwen2.5 ships 2048), transformers lets that win, so every GSM8K batch runs until all
    sequences hit a stop string or 2048 tokens: ~8x slower, and the answer filter then sees a longer generation
    than a standard harness run would. Clearing it restores the documented lm_eval behaviour.
    """
    generation_config = getattr(getattr(lm, "model", None), "generation_config", None)
    if generation_config is None:
        return
    if generation_config.max_new_tokens is not None:
        log.info("clearing generation_config.max_new_tokens=%s so lm_eval's max_gen_toks cap applies", generation_config.max_new_tokens)
        generation_config.max_new_tokens = None
    if generation_config.max_length not in (None, 20):
        log.info("clearing generation_config.max_length=%s so lm_eval's max_gen_toks cap applies", generation_config.max_length)
        generation_config.max_length = 20  # transformers' own default; lm_eval overrides it per call


def load_summary(path: Path) -> dict:
    if path.exists():
        with path.open() as fh:
            return json.load(fh)
    return {"schema_version": SCHEMA_VERSION, "run_meta": {}, "records": []}


def merge_records(existing: list[dict], fresh: list[dict]) -> list[dict]:
    """Replace records for the tasks just run; keep the others so a task can be re-run alone."""
    rerun = {(record["task"], record["num_fewshot"]) for record in fresh}
    kept = [record for record in existing if (record["task"], record["num_fewshot"]) not in rerun]
    return sorted(kept + fresh, key=lambda r: (r["task"], r["num_fewshot"], r["metric"], r["filter"]))


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpx2", "urllib3", "filelock", "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    args = parse_args(argv)

    task_names = args.tasks or list(PROFILES[args.profile])
    unknown = [name for name in task_names if name not in PROFILES[args.profile]]
    if unknown and (args.limit is None or args.num_fewshot is None):
        raise SystemExit(f"{unknown} are not in profile {args.profile!r}; pass both --limit and --num-fewshot")

    def task_run(name: str) -> TaskRun:
        base = PROFILES[args.profile].get(name, TaskRun(num_fewshot=0, limit=None))
        return TaskRun(
            num_fewshot=base.num_fewshot if args.num_fewshot is None else args.num_fewshot,
            limit=base.limit if args.limit is None else args.limit,
        )

    device = pick_device(args.device)
    hardware = describe_hardware(device)
    revision = resolve_revision(args.model, args.revision)
    versions = library_versions()
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log.info("model=%s revision=%s dtype=%s device=%s (%s)", args.model, revision, args.dtype, device, hardware)

    from lm_eval.models.huggingface import HFLM

    lm_kwargs = dict(pretrained=args.model, revision=revision, dtype=args.dtype, device=device, batch_size=args.batch_size)
    if args.max_length:
        lm_kwargs["max_length"] = args.max_length
    lm = HFLM(**lm_kwargs)
    apply_generation_cap(lm)

    out_dir = args.runs_dir / model_slug(args.model) / args.profile
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "summary.json"
    summary = load_summary(summary_path)
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for name in task_names:
        spec, run = TASKS[name], task_run(name)
        log.info("task=%s num_fewshot=%d limit=%s", name, run.num_fewshot, run.limit)
        results, seconds = run_task(lm, spec, run.num_fewshot, run.limit, args.seed)
        with (out_dir / f"{name}_{run.num_fewshot}shot.json").open("w") as fh:
            json.dump(strip_for_disk(results), fh, indent=1, default=str)
        context = {
            "model": args.model,
            "model_revision": revision,
            "dtype": args.dtype,
            "profile": args.profile,
            "limit": run.limit,
            "seed": args.seed,
            "harness_version": versions["lm_eval"],
            "run_date": run_date,
            "device": device,
            "hardware": hardware,
            "batch_size": args.batch_size,
            "wall_clock_s": round(seconds, 1),
        }
        records = extract_records(results, spec, run.num_fewshot, context)
        for record in records:
            if record["primary"]:
                log.info("RESULT %s %d-shot %s/%s = %.4f ± %s (n=%d, %.0fs)", name, record["num_fewshot"], record["metric"],
                         record["filter"], record["value"], record["stderr"], record["n_items"], seconds)
        # persist after every task so a stopped run keeps what it finished
        summary = {
            "schema_version": SCHEMA_VERSION,
            "run_meta": {
                **summary.get("run_meta", {}),
                "model": args.model,
                "model_revision": revision,
                "dtype": args.dtype,
                "profile": args.profile,
                "device": device,
                "hardware": hardware,
                "batch_size": args.batch_size,
                "seed": args.seed,
                "versions": versions,
                "last_started_at": started_at,
                "last_finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "task_runs": {**summary.get("run_meta", {}).get("task_runs", {}), f"{name}_{run.num_fewshot}shot": asdict(run)},
            },
            "records": merge_records(summary.get("records", []), records),
        }
        with summary_path.open("w") as fh:
            json.dump(summary, fh, indent=1)
        log.info("wrote %s (%d records)", summary_path, len(summary["records"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
