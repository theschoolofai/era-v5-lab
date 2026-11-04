"""Cost model for checkpoint interval, spot vs on-demand, and the hot spare (ADR 0004).

In simple words: a failure costs us the work since the last checkpoint plus the time to restart.
Saving more often loses less work per failure, but every save pauses all GPUs a little. This script
finds the interval with the lowest total waste, and counts waste in node-hours (time on the GPU nodes; the
price is an input with no value in the repo, so cost = node-hours x your price). It also answers:
- Below which spot/on-demand price ratio is spot cheaper per USEFUL node-hour?
- Does a hot spare node pay for itself (does it save more node-hours than it uses)?

Model sizes are still open in config_v0.yaml (TSAI fills them on 31 Oct), so the model takes a range.

    python support/cost/cost_model.py [--measured support/simulation/results/metrics.json] [--out support/cost/cost_report.md]
"""
import argparse
import json
import math
import os
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))

# Published interruption rates, as GPU-hours per interruption (ADR 0001 §10).
MTBF_PRIORS = {"S15 reference run": 9_921, "Llama 3 (unexpected)": 50_677}


def young(stall_s: float, mtbf_s: float) -> float:
    """Young's interval: the save interval with the least waste, if stall and MTBF were all that mattered."""
    return math.sqrt(2 * stall_s * mtbf_s)


def waste_share(interval_s, stall_s, mttr_s, mtbf_s) -> float:
    """Share of wall-clock time lost: stall on every save + (half an interval + restart) on every failure."""
    return stall_s / interval_s + (interval_s / 2 + mttr_s) / mtbf_s


def choose_interval(stall_s, mttr_s, mtbf_s, rpo_cap_s=1800, eval_cadence_s=None) -> dict:
    y = young(stall_s, mtbf_s)
    caps = {"young": y, "rpo_cap": rpo_cap_s}
    if eval_cadence_s:
        caps["eval_cadence"] = eval_cadence_s
    binding = min(caps, key=caps.get)
    return {"interval_s": caps[binding], "binding": binding, "young_s": y}


def ckpt_bytes(params: float, bpp: float) -> float:
    return params * bpp


def scenario(p, params, nodes, mtbf_gph, mttr_s, interval_s=None):
    inst = p["instances"][p["main_instance"]]
    hw = p["hardware"]
    gpus = nodes * inst["gpus"]
    size = ckpt_bytes(params, p["checkpoint"]["bytes_per_param"])
    share = size / nodes
    stall = share / (hw["gpu_to_host_gbytes_s"] * 1e9)
    upload = share / (hw["upload_gbytes_s"] * 1e9)
    restore = share / (hw["download_gbytes_s"] * 1e9)
    mtbf_s = mtbf_gph / gpus * 3600
    mttr = mttr_s + restore
    pick = choose_interval(stall, mttr, mtbf_s)
    T = interval_s or pick["interval_s"]
    T = max(T, upload * 1.2)                       # an interval shorter than the upload queues saves
    w = waste_share(T, stall, mttr, mtbf_s)
    good = max(0.0, 1 - w)
    return {"params_b": params / 1e9, "nodes": nodes, "gpus": gpus,
            "ckpt_gb": round(size / 1e9, 1), "stall_s": round(stall, 2), "upload_s": round(upload, 1),
            "mtbf_h": round(mtbf_s / 3600, 1), "mttr_s": round(mttr, 1), "interval_min": round(T / 60, 1),
            "binding": pick["binding"], "young_min": round(pick["young_s"] / 60, 1),
            "goodput": round(good, 4), "node_h_per_productive_h": round(nodes / max(good, 1e-9), 3),
            "waste_node_h_per_day": round(nodes * 24 * w, 2),
            "lost_node_h_per_failure": round(nodes * (T / 2 + mttr) / 3600, 2),
            "stored_gb": round(size / 1e9 * p["checkpoint"]["keep_remote"], 1),
            "protected_gb_per_month": round(size / 1e9 * p["checkpoint"]["protected_per_month"], 1)}


def spot_vs_on_demand(p, params, nodes, mttr_s, od_mtbf_gph, spot_node_mtbf_h):
    """Spot: any node's reclaim stops the whole gang job, so job MTBF = node MTBF / nodes,
    on top of the hardware failure rate."""
    od = scenario(p, params, nodes, od_mtbf_gph, mttr_s)
    gpus = nodes * p["instances"][p["main_instance"]]["gpus"]
    hw_rate = gpus / od_mtbf_gph                    # failures per hour from hardware
    spot_rate = nodes / spot_node_mtbf_h            # reclaims per hour
    spot_mtbf_gph = gpus / (hw_rate + spot_rate)
    # A reclaim also needs new spot capacity: add the instance launch time to MTTR.
    sp = scenario(p, params, nodes, spot_mtbf_gph, mttr_s + p["hardware"]["instance_launch_s"])
    return od, sp


def spot_break_even(od, sp) -> float:
    """Spot price / on-demand price at which one useful node-hour costs the same on both.
    Cost per useful hour = price / goodput, so equal when ratio = spot goodput / on-demand goodput."""
    return round(sp["goodput"] / max(od["goodput"], 1e-9), 3)


def spare_value(p, nodes, mtbf_gph, mttr_with_spare_s):
    inst = p["instances"][p["main_instance"]]
    gpus = nodes * inst["gpus"]
    fails_per_h = gpus / mtbf_gph
    saved_s_per_h = fails_per_h * p["hardware"]["instance_launch_s"]
    saved_node_h = saved_s_per_h / 3600 * nodes     # cluster node-hours saved per hour by the spare
    return {"nodes": nodes, "spare_node_h_per_h": 1, "saved_node_h_per_h": round(saved_node_h, 3),
            "pays_for_itself": saved_node_h >= 1,
            "break_even_fails_per_day": round(24 * 3600 / p["hardware"]["instance_launch_s"] / nodes, 2)}


def table(rows, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", default=os.path.join(HERE, "..", "..", "metrics", "prices.yaml"))
    ap.add_argument("--measured", help="metrics.json from the simulation: uses its measured MTTR")
    ap.add_argument("--out", default=os.path.join(HERE, "cost_report.md"))
    a = ap.parse_args()
    p = yaml.safe_load(open(a.prices))
    mttr_s = 300.0
    src = "assumed 300 s (detect + reschedule + load), before the restore download"
    if a.measured and os.path.exists(a.measured):
        m = json.load(open(a.measured))
        v = (m.get("Q-20") or {}).get("value")
        if v:
            mttr_s, src = float(v), f"measured in the Docker simulation ({v:.0f} s; tiny model, so no download time)"

    lines = ["# Cost model report", "",
             f"Generated by `support/cost/cost_model.py` from `{os.path.basename(a.prices)}`. Results are in "
             f"**node-hours** (time on the GPU nodes). Cost = node-hours × the price of one node-hour, an input with "
             f"no value in the repo. Node: {p['main_instance']}. MTTR before download: {src}.", "",
             "Model sizes are open in config_v0.yaml, so each table runs over 1B, 7B and 30B parameters.", ""]
    cols = ["params_b", "nodes", "gpus", "ckpt_gb", "stall_s", "mtbf_h", "interval_min", "binding",
            "young_min", "goodput", "node_h_per_productive_h", "lost_node_h_per_failure", "waste_node_h_per_day",
            "stored_gb", "protected_gb_per_month"]
    for name, gph in MTBF_PRIORS.items():
        rows = [scenario(p, params, n, gph, mttr_s) for params in (1e9, 7e9, 30e9) for n in (2, 4, 8)]
        lines += [f"## On-demand, failure rate from {name} ({gph:,} GPU-h per interruption)", "",
                  table(rows, cols), ""]

    lines += ["## Spot vs on-demand (7B params, S15 failure rate)", "",
              "In simple words: spot is cheaper per hour, but each reclaim of ANY node stops the whole job, "
              "and new spot capacity takes time to get. We compare the cost of one useful (productive) hour: spot is "
              "cheaper only when its price is below `break_even_spot_ratio` × the on-demand price.", ""]
    rows = []
    for spot_h in (24, 72, 168):
        for n in (2, 8):
            od, sp = spot_vs_on_demand(p, 7e9, n, mttr_s, MTBF_PRIORS["S15 reference run"], spot_h)
            row = {"nodes": n, "spot_node_mtbf_h": spot_h, "od_goodput": od["goodput"], "spot_goodput": sp["goodput"],
                   "break_even_spot_ratio": spot_break_even(od, sp)}
            if p.get("spot_price_ratio"):
                row["cheaper"] = "spot" if p["spot_price_ratio"] < row["break_even_spot_ratio"] else "on-demand"
            rows.append(row)
    lines += [table(rows, list(rows[0])), "",
              "Spot prices are usually far below these break-even ratios, so spot looks cheaper per useful hour, "
              "but only if spot capacity for whole "
              "gpu-node-8 nodes can actually be obtained, and every reclaim adds a restart that a person may have to "
              "watch. Decision (ADR 0004): **main run on on-demand or a reserved capacity booking**; spot only for "
              "preemptible team jobs (ladder, evals), which already save on SIGTERM.", ""]

    lines += ["## Hot spare node", "",
              "In simple words: a spare uses one node-hour every hour. It pays for itself only if it saves more "
              "cluster node-hours than that, by cutting each failure's restart from 'launch a new node' to 'use the "
              "spare now'. No price is needed: both sides are node-hours.", ""]
    rows = [spare_value(p, n, MTBF_PRIORS["S15 reference run"], mttr_s) for n in (2, 4, 8, 16)]
    lines += [table(rows, list(rows[0])), "",
              "At this failure rate the spare's 15 minutes saved per failure is fewer node-hours than it uses, at "
              "every size here. Its other value is that the main run never waits for capacity that may not "
              "exist. Decision (ADR 0004): keep one hot spare, but let it run preemptible team jobs, so it is "
              "not idle money.", ""]
    with open(a.out, "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
