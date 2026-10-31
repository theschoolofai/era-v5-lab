"""Live alerting: check the metrics every N seconds and raise new alerts (ADR 0004 §4).

In simple words: evaluate.py writes a report after the fact. This script runs all the time next to the
cluster. Every N seconds it recomputes the metrics from the events; when a metric reaches a new severity it
writes an `alert.fired` event, and, if V5_ALERT_WEBHOOK is set (Team 08's pager or a Slack/Discord webhook),
posts the alert there. HIGH alerts page someone; MEDIUM and LOW only go to the channel.

    python metrics/watch.py --events /s3/events --run v5main --nodes 2 --interval-s 1800 --every 30
"""
import argparse
import json
import os
import sys
import time
import urllib.request

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from common.events import emit, read_all  # noqa: E402
from metrics.evaluate import CATALOG, ORDER, Run, compute, severity  # noqa: E402


def message(alert) -> str:
    """The page a person reads: what, why it matters, what to do, how fast, and where to read more."""
    return (f"[{alert['severity'].upper()}] {alert['id']} {alert['name']}: {alert['value']} {alert['unit']}\n"
            f"Why it matters: {alert['why']}\n"
            f"What to do: {alert['action']}\n"
            f"Respond: {alert['respond']} ({alert['who']}). More: {alert['explain']}")


def post(url, alert):
    """Generic JSON webhook; Slack and Discord accept {"text"/"content": ...}."""
    text = message(alert)
    body = json.dumps({"text": text, "content": text, "alert": alert}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:  # noqa: BLE001 - a failed page must not stop the watcher; it is retried next round
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--run", default="v5main")
    ap.add_argument("--nodes", type=int, default=2)
    ap.add_argument("--interval-s", type=float, default=1800)
    ap.add_argument("--every", type=float, default=30)
    ap.add_argument("--prices", default=os.path.join(HERE, "prices.yaml"))
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    cat = yaml.safe_load(open(CATALOG))
    p = yaml.safe_load(open(a.prices))
    price = p["instances"][p["main_instance"]]["on_demand_usd_h"] * a.nodes
    interval_cost = price * a.interval_s / 3600
    hook = os.environ.get("V5_ALERT_WEBHOOK")
    state = {}          # metric id -> highest severity already raised
    while True:
        ev = read_all(a.events)
        if ev:
            m, _ = compute(Run(ev, a.run, a.interval_s), price, a.sim)
            for x in cat["metrics"]:
                v = m.get(x["id"])
                scale = interval_cost if x.get("scale") == "interval_cost" else 1.0
                sev = severity(x, v, scale)
                if sev and ORDER[sev] > ORDER[state.get(x["id"])]:
                    state[x["id"]] = sev
                    alert = {"id": x["id"], "severity": sev, "name": x["name"], "value": round(v, 4),
                             "unit": x["unit"], "area": x["area"], "why": x["why"], "action": x["action"],
                             "respond": cat["severity"][sev]["response"], "who": cat["severity"][sev]["who"],
                             "explain": f"python metrics/explain.py {x['id']}"}
                    delivered = post(hook, alert) if hook else None
                    emit("alert.fired", **alert, page=sev == "high", delivered=delivered)
                    print(json.dumps(alert), flush=True)
        if a.once:
            return 0
        time.sleep(a.every)


if __name__ == "__main__":
    sys.exit(main())
