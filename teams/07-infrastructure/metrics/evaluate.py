"""Turn events into metrics, goodput, dollars and alerts (ADR 0004).

In simple words: every component writes events. This script reads them, rebuilds each incident
(fault -> job ends -> job restarts -> restore -> first useful step), splits the main run's wall-clock
time into "useful training" and each kind of waste, prices the waste, and checks every metric in
metrics/catalog.yaml against its LOW / MEDIUM / HIGH thresholds.

    python metrics/evaluate.py --events /s3/events --out /s3/report --run v5main --nodes 2 --interval-s 1800
    python metrics/evaluate.py --render-md ../support/docs/metrics_catalog.md      (catalog table for the docs)
"""
import argparse
import json
import os
import statistics
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from common.events import parse_time, read_all  # noqa: E402

CATALOG = os.path.join(HERE, "catalog.yaml")
ORDER = {"high": 3, "medium": 2, "low": 1, None: 0}
# Metrics a drill triggers on purpose: in --sim mode their alerts are expected, and prove the alert works.
# Metrics that are high in the simulation only because a fault is injected about every minute.
FAULT_RATE_DRIVEN = {"Q-19", "C-02", "C-03", "Q-05", "H-14"}
DRILL_TRIGGERED = {"CK-07", "Q-02", "Q-04", "H-14", "H-21", "H-24", "Q-05", "Q-21", "CK-19", "Q-09", "Q-16",
                   "Q-01", "Q-03", "Q-10", "C-04",
                   "CK-04", "CK-06"}


def severity(m, value, scale=1.0):
    if value is None:
        return None
    best = None
    for lvl in ("low", "medium", "high"):
        th = m.get(lvl)
        if th is None:
            continue
        th = th * scale
        hit = value >= th if m["direction"] == "above" else value <= th
        if hit:
            best = lvl
    return best


class Run:
    def __init__(self, ev, run, interval_s):
        self.all = ev
        self.ev = [e for e in ev if e.get("run_id") == run]
        self.run, self.interval_s = run, interval_s
        for e in ev:
            e["t"] = parse_time(e["time"])

    def of(self, name, ev=None):
        return [e for e in (ev if ev is not None else self.ev) if e["event"] == name]

    def first_after(self, t, name, until=None, **match):
        for e in self.ev:
            if e["t"] > t and e["event"] == name and (until is None or e["t"] <= until) and \
                    all(e.get(k) == v for k, v in match.items()):
                return e
        return None

    def last_before(self, t, name, **match):
        out = None
        for e in self.ev:
            if e["t"] <= t and e["event"] == name and all(e.get(k) == v for k, v in match.items()):
                out = e
        return out

    def step_time(self):
        st = [e["step_s"] for e in self.of("train.step") if e.get("step_s")]
        return statistics.median(st) if st else 0.0

    def incidents(self):
        """One record per fault: drill.injected (simulation) or an unplanned job end (production)."""
        faults = [(e["t"], e.get("drill", "unplanned"), e.get("cause_class", "unknown"), e)
                  for e in self.of("drill.injected")
                  if e.get("drill") not in ("preemption", "crash_loop", "ctld_failover")]   # no main-run outage
        drill_times = [f[0] for f in faults]
        for e in self.of("job.ended"):
            if e["exit"] != 0 and not any(0 <= e["t"] - t < 300 for t in drill_times):
                faults.append((e["t"] - 0.001, "unplanned", "unknown", e))
        faults.sort(key=lambda f: f[0])
        out = []
        st = self.step_time()
        for i, (tf, kind, cause, e) in enumerate(faults):
            nxt = faults[i + 1][0] if i + 1 < len(faults) else None
            end = self.first_after(tf, "job.ended", until=nxt)
            started = self.first_after(tf, "job.started", until=nxt)
            rd = self.first_after(tf, "restore.done", until=nxt)
            fs = self.first_after(rd["t"], "train.step", until=nxt, first_after_start=True) if rd else None
            # Only this incarnation: steps redone after an earlier restore have lower numbers.
            since = max([r["t"] for r in self.of("restore.done") + self.of("train.started") if r["t"] <= tf],
                        default=0)
            before = [s["step"] for s in self.of("train.step") if since <= s["t"] <= tf]
            at_fault = max(before) if before else 0
            t_end = end["t"] if end else (started["t"] if started else None)
            rec = {"kind": kind, "cause_class": cause, "t_fault": e["time"],
                   "detect_s": round(t_end - tf, 2) if t_end else None,
                   "reschedule_s": round(max(0.0, started["t"] - t_end), 2) if (started and t_end) else None,
                   "restore_s": round(fs["t"] - started["t"], 2) if (fs and started) else None,
                   "mttr_s": round(fs["t"] - tf, 2) if fs else None,
                   "restored_step": rd["step"] if rd else None, "step_at_fault": at_fault,
                   "lost_steps": max(0, at_fault - rd["step"]) if rd else None,
                   "human_action": kind in ("nan", "loss_spike", "rollback") or kind.startswith("operator"),
                   "exit": end["exit"] if end else None}
            rec["lost_s"] = round(rec["lost_steps"] * st, 2) if rec["lost_steps"] is not None else None
            out.append(rec)
        return out


def compute(run: Run, price_usd_h: float, sim: bool):
    m, detail = {}, {}
    I = run.interval_s
    commits = run.of("checkpoint.committed")
    failed = run.of("checkpoint.failed")
    restores = run.of("restore.done")
    incs = run.incidents()
    stall = [c["stall_s"] + c.get("backpressure_s", 0) for c in commits]

    # --- checkpoint
    at_risk = 0.0
    for s in run.of("train.step"):
        if s.get("rank", 0) != 0:
            continue
        base = [c["t"] for c in commits if c["t"] <= s["t"]] + [r["t"] for r in restores if r["t"] <= s["t"]]
        start = run.last_before(s["t"], "train.started")
        if start:
            base.append(start["t"])
        if base:
            at_risk = max(at_risk, s["t"] - max(base))
    m["CK-01"] = at_risk / I
    m["CK-02"] = at_risk / 3600 * price_usd_h
    seq, worst = 0, 0
    for e in sorted(commits + failed, key=lambda e: e["t"]):
        seq = seq + 1 if e["event"] == "checkpoint.failed" else 0
        worst = max(worst, seq)
    m["CK-03"] = worst
    m["CK-04"] = sum(1 for e in failed if e.get("cause") == "IntegrityError") + \
        sum(1 for e in run.of("restore.failed") if e.get("cause") == "IntegrityError")
    m["CK-05"] = sum(1 for e in run.of("restore.failed") if e.get("cause") == "RestoreCheckError")
    m["CK-06"] = len(run.of("restore.fatal"))
    m["CK-07"] = len({e["step"] for e in run.of("train.nonfinite")})
    m["CK-08"] = (statistics.mean(stall) / I * 100) if stall else None
    m["CK-09"] = max((c["commit_latency_s"] for c in commits), default=None)
    m["CK-10"] = len(run.of("checkpoint.backpressure"))
    m["CK-13"] = max((i["restore_s"] for i in incs if i["restore_s"] is not None), default=None)
    lost = [i["lost_s"] / I for i in incs if i["lost_s"] is not None]
    m["CK-14"] = max(lost) if lost else None
    ret = [e for e in run.all if e["event"] == "checkpoint.retention"]
    m["CK-15"] = sum(len(set(e["deleted"]) & set(e["protected"])) for e in ret) if ret else None
    m["CK-16"] = (sum(e["freed_bytes"] for e in ret if e["orphans"]) / 1e9) if ret else None
    m["CK-18"] = len([e for e in run.all if e["event"] == "export.failed"])
    m["CK-19"] = sum(1 for r in restores if r.get("resharded"))
    m["CK-20"] = sum(1 for r in restores if not r.get("probe_recorded", True))
    detail["checkpoint"] = {"commits": len(commits), "failed": len(failed), "restores": len(restores),
                            "stall_s_mean": round(statistics.mean(stall), 4) if stall else None,
                            "stall_s_p95": round(sorted(stall)[int(0.95 * (len(stall) - 1))], 4) if stall else None,
                            "commit_latency_s_mean": round(statistics.mean(c["commit_latency_s"] for c in commits), 4)
                            if commits else None,
                            "bytes_per_commit": commits[-1]["bytes"] if commits else None}

    # --- queue
    res = [i["reschedule_s"] for i in incs if i["reschedule_s"] is not None]
    m["Q-01"] = max(res) if res else None
    m["Q-02"] = len(run.of("job.held"))
    m["Q-03"] = max(res) if res else None
    m["Q-04"] = sum(1 for e in run.all if e["event"] == "job.held" and "crash_loop" in e.get("cause", ""))
    # Per-day and per-hour rates are scaled by the observed window, not reported as raw counts.
    window_s = (run.ev[-1]["t"] - run.ev[0]["t"]) if run.ev else 0
    m["Q-05"] = len(incs) / (window_s / 86400) if window_s else None
    gaps = []
    for js in run.of("job.started"):
        fs = run.first_after(js["t"], "train.step")
        if fs:
            gaps.append(fs["t"] - js["t"])
    gaps += [w["idle_s"] for w in run.of("train.watchdog")]
    m["Q-07"] = max(gaps) if gaps else None
    drained, cur = 0, set()
    for e in run.all:
        if e["event"] == "node.drained":
            cur.add(e["node"])
        elif e["event"] == "node.resumed":
            cur.discard(e["node"])
        drained = max(drained, len(cur))
    m["Q-09"] = drained
    repl = []
    for d in [e for e in run.all if e["event"] == "node.drained"]:
        rd = run.first_after(d["t"], "restore.done")
        fs = run.first_after(rd["t"], "train.step", first_after_start=True) if rd else None
        if fs:
            repl.append(fs["t"] - d["t"])
    m["Q-10"] = max(repl) if repl else None
    team_lost = 0.0
    for stop in [e for e in run.all if e["event"] == "train.stop_requested" and e["run_id"] != run.run]:
        nxt = [r for r in run.all if r["event"] == "restore.done" and r["run_id"] == stop["run_id"] and r["t"] > stop["t"]]
        if nxt:
            team_lost += max(0, stop["step"] - nxt[0]["step"]) * run.step_time() / 3600
    m["Q-14"] = team_lost
    m["Q-16"] = len([e for e in run.all if e["event"] == "job.rejected"])
    mttr = [i["mttr_s"] for i in incs if i["mttr_s"] is not None]
    m["Q-20"] = statistics.mean(mttr) if mttr else None
    # A node put back into service by a person counts; the simulation's own resumes (by=drill) would be
    # done by a person in production too, so they are reported separately, not hidden.
    m["Q-21"] = sum(1 for i in incs if i["human_action"])
    detail["node_resumes_by_drill"] = len([e for e in run.all if e["event"] == "node.resumed" and e.get("by") == "drill"])

    # --- goodput buckets over the main run window
    starts = run.of("job.started") or run.of("train.started")
    ends = run.of("train.exit")
    buckets = {}
    if starts and ends:
        t0, t1 = starts[0]["t"], ends[-1]["t"]
        wall = t1 - t0
        b = {"checkpoint_stall": sum(stall),
             "lost_work": sum(i["lost_s"] or 0 for i in incs),
             "detection": sum(i["detect_s"] or 0 for i in incs),
             "reschedule": sum(i["reschedule_s"] or 0 for i in incs),
             "restore": sum(i["restore_s"] or 0 for i in incs)}
        b["productive"] = max(0.0, wall - sum(b.values()))
        buckets = {k: {"seconds": round(v, 2), "share": round(v / wall, 4),
                       "usd": round(v / 3600 * price_usd_h, 2)} for k, v in b.items()}
        buckets["wall_clock"] = {"seconds": round(wall, 2), "share": 1.0, "usd": round(wall / 3600 * price_usd_h, 2)}
        good = b["productive"] / wall
        m["Q-19"] = good * 100
        m["C-02"] = 1 / good if good else None
        m["C-03"] = (1 - good) * 100
    inc_cost = [((i["lost_s"] or 0) + (i["detect_s"] or 0) + (i["reschedule_s"] or 0) + (i["restore_s"] or 0)) / I
                for i in incs]
    m["C-04"] = max(inc_cost) if inc_cost else None

    # --- health
    hr = [e for e in run.all if e["event"] == "health.report"]
    m["H-01"] = sum(1 for e in hr if "xid" in e.get("failed", []))          # real Xid only, not the drill switch
    hangs = {(e["job_id"], e["step"] // 50) for e in run.of("train.watchdog")}  # one hang fires on every rank
    m["H-14"] = len(hangs) / (window_s / 3600) if window_s else None
    m["H-24"] = len({e["job_id"] + str(e["t"] // 60) for e in run.of("train.exit") if e.get("cause") == "loss_spike"})
    ratios = []
    by_step = {}
    for s in run.of("train.step"):
        if s.get("first_after_start"):
            continue  # the first step after a start includes warm-up; not a straggler signal
        by_step.setdefault((s["job_id"], s["step"], round(s["t"] / 60)), []).append(s["step_s"])
    for v in by_step.values():
        if len(v) > 1 and statistics.median(v) > 0:
            ratios.append(max(v) / statistics.median(v))
    m["H-15"] = max(ratios) if ratios else None
    pro = [e["runtime_seconds"] for e in hr if e.get("mode") == "prolog"]
    m["H-17"] = max(pro) if pro else None
    m["H-18"] = sum(1 for e in hr if e.get("skipped_required"))
    m["H-21"] = len([e for e in run.all if e["event"] == "node.spot_notice"])
    detail["incidents"] = incs
    by_kind = {}
    for i in incs:
        if i["mttr_s"] is not None:
            by_kind.setdefault(i["kind"], []).append(i["mttr_s"])
    detail["mttr_by_kind"] = {k: {"n": len(v), "p50": round(statistics.median(v), 2),
                                  "p95": round(sorted(v)[min(len(v) - 1, int(round(0.95 * (len(v) - 1))))], 2),
                                  "max": round(max(v), 2)} for k, v in by_kind.items()}
    detail["goodput_buckets"] = buckets
    return m, detail


def render_md(cat, path):
    lines = ["# Metrics catalog", "",
             "Generated from `metrics/catalog.yaml` by `python metrics/evaluate.py --render-md`. Do not edit by hand.",
             "", "| Severity | Response | Who |", "|---|---|---|"]
    for k, v in cat["severity"].items():
        lines.append(f"| **{k.upper()}** | {v['response']} | {v['who']} |")
    for area in ("checkpoint", "queue", "health", "cost"):
        rows = [x for x in cat["metrics"] if x["area"] == area]
        lines += ["", f"## {area.capitalize()} ({len(rows)} metrics)", "",
                  "| ID | Metric | Unit | Alert when | LOW | MEDIUM | HIGH | Why it matters (simple words) | Action | Sim |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for x in rows:
            f = lambda v: "—" if v is None else (f"{v} × interval cost" if x.get("scale") else str(v))  # noqa: E731
            lines.append(f"| {x['id']} | {x['name']} | {x['unit']} | {x['direction']} | {f(x.get('low'))} | "
                         f"{f(x.get('medium'))} | {f(x.get('high'))} | {x['why']} | {x['action']} | "
                         f"{'yes' if x['sim'] else 'no'} |")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events")
    ap.add_argument("--out")
    ap.add_argument("--run", default="v5main")
    ap.add_argument("--nodes", type=int, default=2)
    ap.add_argument("--interval-s", type=float, default=1800)
    ap.add_argument("--prices", default=os.path.join(HERE, "prices.yaml"))
    ap.add_argument("--sim", action="store_true", help="mark alerts caused by injected drills as expected")
    ap.add_argument("--render-md", help="write the catalog as a Markdown table and exit")
    a = ap.parse_args()
    cat = yaml.safe_load(open(CATALOG))
    if a.render_md:
        render_md(cat, a.render_md)
        return 0

    p = yaml.safe_load(open(a.prices))
    price = p["instances"][p["main_instance"]]["on_demand_usd_h"] * a.nodes
    run = Run(read_all(a.events), a.run, a.interval_s)
    m, detail = compute(run, price, a.sim)
    interval_cost = price * a.interval_s / 3600

    alerts, metrics_out = [], {}
    for x in cat["metrics"]:
        v = m.get(x["id"])
        scale = interval_cost if x.get("scale") == "interval_cost" else 1.0
        sev = severity(x, v, scale)
        metrics_out[x["id"]] = {"name": x["name"], "value": None if v is None else round(v, 4), "unit": x["unit"],
                                "severity": sev, "computed": v is not None}
        if sev:
            alerts.append({"id": x["id"], "severity": sev, "name": x["name"], "value": round(v, 4), "unit": x["unit"],
                           "action": x["action"], "expected_in_sim": a.sim and x["id"] in DRILL_TRIGGERED,
                           "fault_rate_driven": a.sim and x["id"] in FAULT_RATE_DRIVEN})
    alerts.sort(key=lambda r: -ORDER[r["severity"]])
    os.makedirs(a.out, exist_ok=True)
    json.dump(metrics_out, open(os.path.join(a.out, "metrics.json"), "w"), indent=1)
    json.dump(alerts, open(os.path.join(a.out, "alerts.json"), "w"), indent=1)

    L = [f"# Simulation metrics report: run `{a.run}`", "",
         f"Cluster price used: {a.nodes} × {p['main_instance']} = **${price:,.2f}/h** (assumed price, see "
         f"metrics/prices.yaml). Interval: {a.interval_s:.0f} s (one interval = ${interval_cost:,.2f}).", ""]
    if a.sim:
        L += ["> In the simulation a fault is injected about once a minute, while a real run sees one every "
              "few hours or days. So goodput and cost-waste numbers here are far worse than production will be. "
              "The simulation proves the *mechanism* and measures each step's *duration*; "
              "`support/cost/cost_model.py --measured` projects those durations onto real failure rates.", ""]
    computed = sum(1 for v in metrics_out.values() if v["computed"])
    L += [f"Metrics in catalog: {len(cat['metrics'])}; computed from simulation events: {computed}.", "",
          "## Alerts", "", "| Severity | ID | Metric | Value | Caused by the test? | Action |", "|---|---|---|---|---|---|"]
    for r in alerts:
        L.append(f"| {r['severity'].upper()} | {r['id']} | {r['name']} | {r['value']} {r['unit']} | "
                 f"{'fault rate' if r['fault_rate_driven'] else 'yes' if r['expected_in_sim'] else 'no'} | "
                 f"{r['action']} |")
    b = detail["goodput_buckets"]
    if b:
        L += ["", "## Where the main run's wall-clock time (and money) went", "",
              "| Bucket | Seconds | Share | USD |", "|---|---|---|---|"]
        for k, v in b.items():
            L.append(f"| {k} | {v['seconds']} | {v['share'] * 100:.1f}% | ${v['usd']:,.2f} |")
    if detail.get("mttr_by_kind"):
        L += ["", "## Recovery time by fault type (MTTR, seconds)", "", "| Fault | n | p50 | p95 | max |",
              "|---|---|---|---|---|"]
        for k, v in sorted(detail["mttr_by_kind"].items()):
            L.append(f"| {k} | {v['n']} | {v['p50']} | {v['p95']} | {v['max']} |")
    L += ["", "## Incidents", "",
          "| Fault | Cause class | Detect s | Reschedule s | Restore s | MTTR s | Lost steps | Restored step | Human |",
          "|---|---|---|---|---|---|---|---|---|"]
    for i in detail["incidents"]:
        L.append(f"| {i['kind']} | {i['cause_class']} | {i['detect_s']} | {i['reschedule_s']} | {i['restore_s']} | "
                 f"{i['mttr_s']} | {i['lost_steps']} | {i['restored_step']} | {'yes' if i['human_action'] else 'no'} |")
    c = detail["checkpoint"]
    L += ["", "## Checkpoint", "", f"- committed: {c['commits']}, failed: {c['failed']}, restores: {c['restores']}",
          f"- stall per save: mean {c['stall_s_mean']} s, p95 {c['stall_s_p95']} s; "
          f"commit latency mean {c['commit_latency_s_mean']} s; size {c['bytes_per_commit']} bytes (tiny model)", "",
          "## All computed metrics", "", "| ID | Metric | Value | Unit | Severity |", "|---|---|---|---|---|"]
    for k, v in metrics_out.items():
        if v["computed"]:
            L.append(f"| {k} | {v['name']} | {v['value']} | {v['unit']} | {(v['severity'] or 'ok').upper()} |")
    open(os.path.join(a.out, "report.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
