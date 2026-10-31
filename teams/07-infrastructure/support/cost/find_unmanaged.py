"""Find EC2 instances that cost money but are not Slurm nodes, and instances missing cost tags (ADR 0004).

In simple words: V4 lost money on a cluster that sat idle for 3 days. Here we list every running instance in
the account and compare it with the nodes Slurm knows. Anything running that Slurm does not know (a forgotten
test box, a node Slurm thinks is powered off) is metric C-05, HIGH. Anything without the cost tags cannot be
charged to a team in the AWS bill.

Cost tags every instance must carry (set by ec2_resume.sh and the launch template):
    v5:cluster=v5   v5:role=gpu|eval|cpu|head   v5:team=<account>|shared   v5:run=<run id>|none
AWS Budgets and Cost Explorer then split the bill by v5:team (cost allocation tags must be activated once).

    python support/cost/find_unmanaged.py                          # live: boto3 + sinfo
    python support/cost/find_unmanaged.py --instances support/tests/fixtures/cost/ec2.json --slurm-nodes support/tests/fixtures/cost/sinfo.txt   # test
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from common.events import emit  # noqa: E402

REQUIRED_TAGS = ("v5:cluster", "v5:role", "v5:team", "v5:run")


def live_instances(region):
    import boto3
    ec2 = boto3.client("ec2", region_name=region)
    out = []
    for page in ec2.get_paginator("describe_instances").paginate(
            Filters=[{"Name": "instance-state-name", "Values": ["pending", "running"]}]):
        for r in page["Reservations"]:
            for i in r["Instances"]:
                out.append({"id": i["InstanceId"], "type": i["InstanceType"],
                            "tags": {t["Key"]: t["Value"] for t in i.get("Tags", [])}})
    return out


def slurm_nodes(path=None):
    """Node name -> state. Nodes Slurm considers powered down (~, CLOUD, POWERED_DOWN) should have no instance."""
    text = open(path).read() if path else subprocess.run(["sinfo", "-h", "-N", "-o", "%N %T"],
                                                         capture_output=True, text=True).stdout
    return dict(line.split()[:2] for line in text.splitlines() if line.strip())


def check(instances, nodes, prices):
    unmanaged, untagged, idle_powered = [], [], []
    for i in instances:
        name = i["tags"].get("Name", "")
        missing = [t for t in REQUIRED_TAGS if t not in i["tags"]]
        if missing:
            untagged.append({"id": i["id"], "name": name, "missing": missing})
        st = nodes.get(name)
        cost = prices.get(i["type"], 0.0)
        if i["tags"].get("v5:role") == "head":
            continue
        if st is None:
            unmanaged.append({"id": i["id"], "name": name, "type": i["type"], "usd_h": cost,
                              "why": "running, but not a Slurm node"})
        elif any(s in st for s in ("~", "powered_down", "power_down", "cloud")):
            idle_powered.append({"id": i["id"], "name": name, "type": i["type"], "usd_h": cost,
                                 "why": f"Slurm thinks it is powered down ({st})"})
    bad = unmanaged + idle_powered
    return {"unmanaged": bad, "untagged": untagged, "c05_count": len(bad),
            "usd_per_day_at_risk": round(24 * sum(x["usd_h"] for x in bad), 2)}


def main():
    import yaml
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", help="JSON list (test fixture) instead of the AWS API")
    ap.add_argument("--slurm-nodes", help="sinfo -N -o '%%N %%T' output (test fixture)")
    ap.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    ap.add_argument("--prices", default=os.path.join(os.path.dirname(__file__), "..", "..", "metrics", "prices.yaml"))
    a = ap.parse_args()
    p = yaml.safe_load(open(a.prices))
    prices = {k: v["on_demand_usd_h"] for k, v in p["instances"].items()}
    inst = json.load(open(a.instances)) if a.instances else live_instances(a.region)
    res = check(inst, slurm_nodes(a.slurm_nodes), prices)
    emit("cost.unmanaged_check", **res)
    print(json.dumps(res, indent=1))
    return 4 if res["c05_count"] else (3 if res["untagged"] else 0)


if __name__ == "__main__":
    sys.exit(main())
