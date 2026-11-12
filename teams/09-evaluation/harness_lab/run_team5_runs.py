"""Score Team 5 lab checkpoints with eval-mini and write eval-mini v1 records.

Reads run folders written by teams/05-architecture/harness/train_week2.py (each holds manifest.json, checkpoint.pt and,
for finished runs, summary.json), loads the model with Team 5's own code (week2/model.py, week2/artifacts.py), and scores
it with lm-evaluation-harness through a small lm_eval LM class. The task list, item sets and seeds are in
eval_lab_v1.yaml: the freeze set (the guard of results/config_freeze_proposal.md) and the diagnostics TSAI allowed on
#357, each diagnostic number labelled "diagnostic, not cleared for contamination".

Usage (from the repo root):
    python teams/09-evaluation/harness_lab/run_team5_runs.py --runs ./inputs/runs --tokenizer ./inputs/tokenizer_v0.json --byte-table ./inputs/raw_table_P32.npz --hf-home ./inputs/hf --offline --device cuda --out ./out

--runs is one run folder or a folder of run folders. --limit N is for tests only: the first N items of each task
(N per subject for MMLU); every record then says it is a test.

Firewall (teams/09-evaluation/firewall/eval_firewall.md, section 3): the script reads only its inputs, needs no network
with --offline, writes only to --out, never logs samples or prompts, and writes no item text. Outputs:
    out/eval_mini_lab.json   eval-mini v1 records (results/eval_mini_v1_schema.md; section 6 for lab checkpoints)
    out/guard.json           pooled freeze-set accuracy per run, for decision 3 of the proposal
    out/run.json             versions, input hashes, timings
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import platform
import sys
import time
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEAM = HERE.parent                                   # teams/09-evaluation
REPO = TEAM.parent.parent
WEEK2 = REPO / "teams" / "05-architecture" / "harness"
TASKS_DIR = TEAM / "harness_code_indic" / "tasks"     # MILU task configs


def say(msg: str) -> None:
    """Progress line with a UTC time. Phase and task names only, never item text."""
    print(f"[{datetime.now(timezone.utc):%H:%M:%S}Z] {msg}", flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=Path, required=True, help="a run folder, or a folder of run folders")
    ap.add_argument("--tokenizer", type=Path, required=True, help="tokenizer v0 tokenizer.json (sha256 2de039f2...)")
    ap.add_argument("--byte-table", type=Path, required=True, help="the raw P32 table the runs were trained with")
    ap.add_argument("--config", type=Path, default=HERE / "eval_lab_v1.yaml")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    ap.add_argument("--hf-home", type=Path, help="Hugging Face cache with the datasets (HF_HOME)")
    ap.add_argument("--offline", action="store_true", help="no network: HF_DATASETS_OFFLINE=1 and HF_HUB_OFFLINE=1")
    ap.add_argument("--limit", type=int, help="TEST ONLY: first N items per task (N per subject for MMLU)")
    ap.add_argument("--max-batch-tokens", type=int, default=16384, help="padded tokens per forward pass")
    ap.add_argument("--groups", help="comma-separated group names from the config (default: all)")
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    # Environment first: datasets and huggingface_hub read these at import time.
    if a.hf_home:
        os.environ["HF_HOME"] = str(a.hf_home.resolve())
    if a.offline:
        os.environ["HF_DATASETS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    for name in ("lm-eval", "lm_eval", "datasets", "transformers", "huggingface_hub", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)

    if a.out.exists() and any(a.out.iterdir()):
        sys.exit(f"{a.out} is not empty: use a fresh output folder")
    a.out.mkdir(parents=True, exist_ok=True)

    import torch
    import yaml

    sys.path.append(str(WEEK2))                       # Team 5's week2 package, used as is
    sys.path.append(str(TEAM / "results"))           # convert_v0_to_v1.check, the v1 validator
    from week2.artifacts import Artifacts
    from week2.model import LanguageModel
    from convert_v0_to_v1 import KEY, check
    from lm_eval_lab import LabLM, evaluate_group

    cfg = yaml.safe_load(a.config.read_text(encoding="utf-8"))
    label = cfg["labels"]
    spec_path = TEAM / cfg["spec"]["path"]
    spec_sha = sha256_file(spec_path)
    if spec_sha != cfg["spec"]["sha256"]:
        sys.exit(f"{spec_path}: sha256 {spec_sha} differs from the config ({cfg['spec']['sha256']})")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    groups = cfg["groups"]
    if a.groups:
        want = {g.strip() for g in a.groups.split(",")}
        groups = [g for g in groups if g["name"] in want]

    say("checking tokenizer and byte table")
    art = Artifacts(a.tokenizer, a.byte_table)       # checks tokenizer v0 and the table against it
    runs = [a.runs] if (a.runs / "manifest.json").exists() else sorted(
        d for d in a.runs.iterdir() if (d / "manifest.json").exists())
    if not runs:
        sys.exit(f"no run folder with manifest.json under {a.runs}")

    device = torch.device(a.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        sys.exit("CUDA unavailable")
    hardware = torch.cuda.get_device_name() if device.type == "cuda" else (platform.processor() or "cpu")
    script_sha = sha256_file(Path(__file__))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    test_note = [f"TEST RUN (--limit {a.limit}): not a result"] if a.limit else []

    records, guard, run_meta = [], [], []
    for run_dir in runs:
        t0 = time.time()
        man = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        ident = man["artifacts"]
        if ident["tokenizer_sha256"] != art.tokenizer_sha:
            sys.exit(f"{run_dir.name}: trained with tokenizer {ident['tokenizer_sha256'][:12]}, not {art.tokenizer_sha[:12]}")
        if ident["table_content_sha256"] != art.table_content_sha:
            sys.exit(f"{run_dir.name}: trained with table content {ident['table_content_sha256'][:12]}, "
                     f"not {art.table_content_sha[:12]}: pass the table this run used")
        say(f"{run_dir.name}: loading checkpoint")
        ckpt_path = run_dir / "checkpoint.pt"
        revision = sha256_file(ckpt_path)
        # A Team 5 harness checkpoint, written by train_week2.py; it also holds optimizer and RNG state.
        state = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        model = LanguageModel(man["config"]["model"], art.bytes, art.lengths)
        model.load_state_dict(state["model"])
        model.to(device).eval()
        bf16 = device.type == "cuda" and man["config"]["run"]["dtype"] == "bf16"
        summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8")) if (run_dir / "summary.json").exists() else {}
        lm = LabLM(model, art, block_size=man["config"]["model"]["block_size"], device=device, bf16=bf16,
                   max_batch_tokens=a.max_batch_tokens)
        common = {
            "model": f"lab:{run_dir.name}", "model_revision": revision,
            # eval_mini_v1_schema.md section 6, rule for a Team 5 checkpoint.pt: run = folder name, step = the file's step.
            "checkpoint": {"run": run_dir.name, "branch": None, "step": int(state["step"]), "epoch": None,
                           "tokens_seen": None, "path": run_dir.as_posix()},
            "format": "bf16" if bf16 else "fp32", "backend": "lab", "dtype": "bfloat16" if bf16 else "float32",
            "decoding": "loglikelihood", "hardware": hardware, "run_date": today, "derived_from": None,
            "harness": {"name": "lm_eval", "version": metadata.version("lm_eval"), "script_sha256": script_sha},
        }
        del state
        run_records = []
        for g in groups:
            say(f"{run_dir.name}: group {g['name']}")
            for entry, res in evaluate_group(lm, g, spec, TASKS_DIR, a.limit):
                task, metric = entry["task"], entry["primary"]
                say(f"{run_dir.name}: {task} done ({res['n'][task]['effective']} items)")
                r = res["results"][task]
                n = res["n"][task]
                if a.limit:
                    item_set = f"limit:{a.limit}"
                elif g["items"] == "spec":
                    item_set = f"spec:{spec_sha}"
                else:
                    item_set = f"limit:{entry['limit']}"
                notes = [label["diagnostic"] if entry["role"] == "diagnostic" else label["freeze"]] + test_note
                for m in ("acc", "acc_norm"):
                    if f"{m},none" not in r:
                        continue
                    se = points_or_none(r.get(f"{m}_stderr,none"))
                    run_records.append({
                        **common, "task": task, "metric": m, "filter": "none", "primary": m == metric,
                        "value": round(100 * r[f"{m},none"], 2),
                        "stderr": se,
                        "n_items": n["effective"], "n_items_total": n["original"], "item_set": item_set,
                        "profile": g["profile"], "num_fewshot": entry["num_fewshot"], "seed": dict(g["seed"]),
                        "notes": notes,
                    })
        records += run_records
        guard.append(guard_row(run_dir.name, run_records, cfg["guard"], bool(a.limit)))
        run_meta.append({"run": run_dir.name, "checkpoint_sha256": revision, "step": common["checkpoint"]["step"],
                         "summary_status": summary.get("status"), "eligible_for_quality_comparison":
                         summary.get("eligible_for_quality_comparison"), "final_model_sha256": summary.get("final_model_sha256"),
                         "parameters": man.get("parameters"), "block_size": man["config"]["model"]["block_size"],
                         "encode_fallbacks": lm.encode_fallbacks, "requests": lm.requests_scored,
                         "wall_seconds": round(time.time() - t0, 1)})
        del model, lm
        if device.type == "cuda":
            torch.cuda.empty_cache()

    records.sort(key=lambda r: tuple(str(r[k]) for k in KEY))
    doc = {"schema_version": "eval_mini_v1", "generated": today,
           "sources": [{"path": "teams/09-evaluation/harness_lab/run_team5_runs.py", "sha256": script_sha,
                        "schema_version": "eval_mini_v1"}],
           "notes": [f"Diagnostic tasks: {label['diagnostic']}. They never pick or block a candidate (TSAI, #357).",
                     "Lab checkpoints: model is lab:<run folder>, model_revision is the sha256 of checkpoint.pt "
                     "(eval_mini_v1_schema.md section 6)."] + test_note,
           "records": records}
    print("v1 checks:")
    if not check(doc, 0):
        sys.exit("v1 checks failed")
    (a.out / "eval_mini_lab.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False, allow_nan=False) + "\n",
                                              encoding="utf-8", newline="\n")
    (a.out / "guard.json").write_text(json.dumps({"guard": cfg["guard"], "runs": guard}, indent=1) + "\n",
                                      encoding="utf-8", newline="\n")
    (a.out / "run.json").write_text(json.dumps({
        "script_sha256": script_sha, "config": a.config.name, "config_sha256": sha256_file(a.config),
        "spec_sha256": spec_sha, "tokenizer_sha256": art.tokenizer_sha, "table_file_sha256": art.table_file_sha,
        "table_content_sha256": art.table_content_sha, "device": a.device, "hardware": hardware,
        "offline": a.offline, "limit": a.limit, "groups": [g["name"] for g in groups],
        "env": {"python": sys.version.split()[0], "platform": platform.platform(),
                **{p: metadata.version(p) for p in ("lm_eval", "torch", "datasets", "tokenizers", "numpy")}},
        "runs": run_meta}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(records)} records for {len(runs)} run(s) to {a.out}")
    for row in guard:
        print("  guard", json.dumps(row))


def points_or_none(x):
    """lm-eval gives a stderr as a fraction, "N/A", or NaN when it cannot compute one (for example 2 items in a test);
    the v1 schema wants points or null."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return round(100 * v, 2) if math.isfinite(v) else None


def guard_row(run, recs, g, test):
    """Pooled freeze-set accuracy over the items actually scored (decision 3 needs it; the verdict is in the results doc)."""
    freeze = {r["task"]: r for r in recs if r["primary"] and r["task"] in g["expected_items"]}
    n = sum(r["n_items"] for r in freeze.values())
    pooled = round(sum(r["value"] * r["n_items"] for r in freeze.values()) / n, 2) if n else None
    complete = not test and all(t in freeze and freeze[t]["n_items"] == k for t, k in g["expected_items"].items())
    return {"run": run, "freeze_tasks": {t: [r["value"], r["n_items"]] for t, r in sorted(freeze.items())},
            "pooled_items": n, "pooled_accuracy": pooled, "complete": complete,
            "below_pooled_floor": None if pooled is None else pooled < g["pooled_floor"]}


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main()
