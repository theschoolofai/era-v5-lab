"""Compare two minibench_v1 sidecars with paired resampling on fixed items."""

import argparse
import json
import math
from pathlib import Path

import numpy as np


def compare(baseline, candidate):
    for field in ("schema_version", "suite_sha256", "profile", "items_sha256", "heldout_sha256",
                  "heldout_sources_sha256", "tokenizer_sha256"):
        if baseline.get(field) is None or baseline[field] != candidate.get(field):
            raise ValueError(f"Comparison requires the same {field}")
    if baseline["schema_version"] != "minibench_cont_v1":
        raise ValueError("Expected minibench_cont_v1 evidence")
    if set(baseline["items"]) != set(candidate["items"]):
        raise ValueError("Task sets differ")
    rng = np.random.default_rng(20261128)
    out = {}
    for task, left in sorted(baseline["items"].items()):
        right = candidate["items"][task]
        left_ids, right_ids = [r["id"] for r in left], [r["id"] for r in right]
        size = np.array([r["utf8_bytes"] for r in left])
        if (not left or len(set(left_ids)) != len(left) or left_ids != right_ids
                or size.tolist() != [r["utf8_bytes"] for r in right] or np.any(size <= 0)):
            raise ValueError(f"Item order, identities or gold byte counts differ for {task}")
        nats = np.array([b["gold_nll_nats"] - a["gold_nll_nats"] for a, b in zip(left, right)])
        sample = rng.integers(len(left), size=(2000, len(left)))
        bpb = nats.sum() / size.sum() / math.log(2)
        bpb_sample = nats[sample].sum(axis=1) / size[sample].sum(axis=1) / math.log(2)
        out[task] = {"items": len(left), "gold_bpb_delta": float(bpb),
                     "gold_bpb_ci95": np.quantile(bpb_sample, [0.025, 0.975]).tolist()}
        if "correct" in left[0]:
            scores = np.array([int(b["correct"]) - int(a["correct"]) for a, b in zip(left, right)])
            score_sample = 100 * scores[sample].mean(axis=1)
            out[task].update(accuracy_delta_points=float(100 * scores.mean()),
                             accuracy_ci95_points=np.quantile(score_sample, [0.025, 0.975]).tolist())
    heldout = {key: candidate["heldout"][key] - val for key, val in baseline["heldout"].items()
               if key == "val/bpb" or key.endswith("/bpb") or key.endswith("_bpb")}
    return {"suite": baseline["suite"], "profile": baseline["profile"], "direction": "candidate_minus_baseline",
            "tasks": out, "heldout_bpb_delta": heldout}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    left, right = (json.loads(path.read_text(encoding="utf-8")) for path in (args.baseline, args.candidate))
    print(json.dumps(compare(left, right), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
