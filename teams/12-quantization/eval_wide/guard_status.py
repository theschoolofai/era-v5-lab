"""Which guard-test settings each task of a format was scored under (G12 wide pass; used by eval_wide.ipynb).

The guard test (../eval_mini/test_llamacpp_lm.py) can run with relaxed settings (EVAL_GUARD_CHECK4=warn,
EVAL_GUARD_CACHE_TOL). A number scored under a relaxed setting must be labelled as such in the results, and kept out of
the ship table. The notebook calls parse_guard_log() on each format's guard log and appends the run to
<runs>/<format>/guard.json together with the tasks that run scored; the results cell then labels every row of
scores_long.csv with task_label(). A format re-logged later under other settings (a guard check only, no scoring) keeps
the label of the run that scored each task, because tasks_scored lists them.
"""
from __future__ import annotations

DEFAULT_CACHE_TOL = 0.05


def parse_guard_log(text: str, overrides: dict) -> dict:
    """The last guard run in a log (the log is appended to): its result, cache diff and any WARN lines."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if "cache max diff" in line]
    if not starts:
        return {"result": "FAIL", "cache_diff": None, "warnings": [], "line": "", "overrides": dict(overrides)}
    head, tail = lines[starts[-1]], lines[starts[-1] + 1:]
    diff = head.split("cache max diff", 1)[1].split()[0].rstrip(";,")
    stripped = [line.strip() for line in tail]
    result = "FAIL" if any(line.startswith("FAIL") or "check(s) failed" in line for line in stripped) else (
        "PASS" if "PASS" in stripped else "FAIL")
    return {"result": result, "cache_diff": float(diff), "line": head[:400], "overrides": dict(overrides),
            "warnings": [line[5:] for line in tail if line.startswith("WARN ")]}


def relaxed(overrides: dict) -> bool:
    """True if the settings loosen a check: check 4 as a warning, or a check 3 limit above the default."""
    cache = overrides.get("EVAL_GUARD_CACHE_TOL")
    return overrides.get("EVAL_GUARD_CHECK4") == "warn" or (cache not in (None, "") and float(cache) != DEFAULT_CACHE_TOL)


def task_label(guard: dict, task: str) -> tuple[str, bool]:
    """(label, in the ship table) for one task, from the guard run that scored it."""
    run = next((r for r in reversed(guard.get("runs", [])) if task in r.get("tasks_scored", [])), None)
    if run is None:
        return "no guard record", False
    ov, parts = run["overrides"], []
    if ov.get("EVAL_GUARD_CHECK4") == "warn":
        parts.append("check 4 warn mode")
    if ov.get("EVAL_GUARD_CACHE_TOL") not in (None, "") and float(ov["EVAL_GUARD_CACHE_TOL"]) != DEFAULT_CACHE_TOL:
        parts.append(f"check 3 limit {ov['EVAL_GUARD_CACHE_TOL']}")
    if ov.get("EVAL_GUARD_CONTEXT"):
        parts.append("guard prompt override")
    if run["warnings"]:
        parts.append("WARNING RAISED: " + "; ".join(w[:60] for w in run["warnings"]))
    return (", ".join(parts) or "default"), not relaxed(ov)


def add_run(guard: dict | None, record: dict, tasks_scored: list[str], logged: str) -> dict:
    guard = guard or {"runs": []}
    guard["runs"].append({**record, "tasks_scored": sorted(tasks_scored), "logged": logged})
    return guard
