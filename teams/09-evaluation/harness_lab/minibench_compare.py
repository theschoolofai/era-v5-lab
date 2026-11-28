"""Compare two minibench_v1 sidecars with paired resampling on fixed items."""

import argparse
import json
import math
from pathlib import Path

import numpy as np


def run_setting(doc):
    """Device class and hardware of one sidecar. GGUF sidecars record n_gpu_layers instead of device."""
    if "device" in doc:
        device = "gpu" if doc["device"] == "cuda" else doc["device"]
        hardware = doc.get("hardware")
    else:
        device = "gpu" if doc.get("n_gpu_layers") else "cpu"
        hardware = None if doc.get("n_gpu_layers") else doc.get("hardware")  # GGUF records the CPU name
    return {"device": device, "hardware": hardware, "format": doc.get("format"), "dtype": doc.get("dtype")}


def compare(baseline, candidate, allow_device_change=False):
    for field in ("schema_version", "suite_sha256", "profile", "items_sha256", "heldout_sha256",
                  "heldout_sources_sha256", "tokenizer_sha256"):
        if baseline.get(field) is None or baseline[field] != candidate.get(field):
            raise ValueError(f"Comparison requires the same {field}")
    if baseline["schema_version"] != "minibench_cont_v1":
        raise ValueError("Expected minibench_cont_v1 evidence")
    if set(baseline["items"]) != set(candidate["items"]):
        raise ValueError("Task sets differ")
    settings = {"baseline": run_setting(baseline), "candidate": run_setting(candidate)}
    left_set, right_set = settings["baseline"], settings["candidate"]
    device_change = left_set["device"] != right_set["device"] or (
        None not in (left_set["hardware"], right_set["hardware"]) and left_set["hardware"] != right_set["hardware"])
    if device_change and not allow_device_change:
        raise ValueError(f"Comparison requires the same device: baseline {left_set['device']} ({left_set['hardware']}), "
                         f"candidate {right_set['device']} ({right_set['hardware']}). On the same weights, CPU against "
                         "GPU moved quick task bpb by up to 0.009 (minibench_v1 card, design check 6)")
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
            "settings": settings, "device_change": device_change, "tasks": out, "heldout_bpb_delta": heldout}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--allow-device-change", action="store_true",
                        help="compare runs from different devices; the deltas then include the device gap")
    args = parser.parse_args()
    left, right = (json.loads(path.read_text(encoding="utf-8")) for path in (args.baseline, args.candidate))
    print(json.dumps(compare(left, right, args.allow_device_change), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
