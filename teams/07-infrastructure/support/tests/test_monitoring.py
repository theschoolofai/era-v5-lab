"""Monitoring must be able to explain everything the system reports (metrics/README.md).

In simple words: if the code can emit a cause, drain a node for a reason or fire an alert, a person must be able
to look it up and get "what happened, what was done, what you do". These tests fail when someone adds a new
cause without adding its explanation.
"""
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")                    # the team folder
SUB = ROOT
sys.path[:0] = [SUB, os.path.join(SUB, "queue")]
import ckpt.ckpt as ck  # noqa: E402
import job_queue  # noqa: E402
from common import reasons  # noqa: E402
from metrics.explain import all_md, explain  # noqa: E402

CAT = yaml.safe_load(open(os.path.join(SUB, "metrics", "catalog.yaml")))
IDS = {m["id"] for m in CAT["metrics"]}


def src(*parts):
    return open(os.path.join(ROOT, *parts)).read()


def test_every_checkpoint_error_is_explained():
    errors = {n for n, v in vars(ck).items() if isinstance(v, type) and issubclass(v, ck.CheckpointError)}
    errors -= {"NonFiniteError"}          # reported as cause "nonfinite"
    missing = errors - set(reasons.CAUSES)
    assert not missing, f"add these to common/reasons.py CAUSES: {missing}"


def test_every_emitted_cause_is_explained():
    found = set(re.findall(r'cause="([a-z_]+)"', src("ckpt", "ckpt.py")))
    found |= set(re.findall(r'"(loss_spike|nonfinite|hang_watchdog|saved_and_stopped|done|crash)"',
                            src("support", "simulation", "trainer", "train.py")))
    found |= {"crash", "crash_loop", "unknown_fatal"}            # queue/job_queue.py
    assert found - set(reasons.CAUSES) == set()


def test_every_drain_reason_is_explained():
    hc = src("health", "health_check.py")
    can_fail = {n for n in re.findall(r'check\("([a-z_]+)", "fail"', hc)}
    can_fail |= {"gpu_inventory", "ecc_uncorrectable", "remapped_rows", "xid", "dcgm_diag", "gpu_temperature",
                 "nvme_free", "clock_offset", "nccl_collectives", "drill_force_fail", "spot_notice",
                 "nccl_all_reduce", "nccl_reduce_scatter", "nccl_all_gather", "nccl_all_to_all", "nvlink"}
    assert can_fail - set(reasons.DRAIN) == set()


def test_alert_ids_exist_in_catalog():
    used = {c["alert"] for c in reasons.CAUSES.values() if c.get("alert")}
    used |= {e["alert"] for e in reasons.EXIT_CODES.values() if e.get("alert")}
    assert used - IDS == set()


def test_explain_answers_what_people_see():
    for word in ["78", "75", "137", "4", "loss_spike", "crash_loop(3 in 1800s)", "CK-05", "q-02",
                 "v5:xid,ecc_uncorrectable", "JobHeldUser", "UploadTimeout"]:
        out = explain(word, CAT)
        assert "not listed" not in out, word
    assert "What you do" in explain("nonfinite", CAT)
    assert "not listed" in explain("no-such-thing", CAT)
    assert "| `loss_spike` |" in all_md(CAT)


def test_wrapper_message_says_what_to_do():
    x = job_queue.explain(78, "loss_spike", 78, {"step": 5880, "detail": "loss 9.1 > 1.5 x median"}, 0)
    assert x["title"].startswith("V5 HELD (78): loss spike") and "at step 5880" in x["title"]
    assert "roll back" in x["you_do"] and x["severity"] == "high"
    x = job_queue.explain(75, "crash", 137, {}, 2)
    assert "trainer exit 137" in x["title"] and "out of memory" in x["title"] and x["you_do"] == "nothing"


def test_exit_note_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("V5_RUNS_DIR", str(tmp_path))
    monkeypatch.setenv("RUN_ID", "r")
    monkeypatch.setenv("SLURM_JOB_ID", "7")
    reasons.write_exit_note(75, "hang_watchdog", 10, rank=1)
    reasons.write_exit_note(78, "nonfinite", 12)
    notes = reasons.read_exit_notes()
    assert [n["cause"] for n in notes] == ["nonfinite", "hang_watchdog"]   # the fatal one wins
    monkeypatch.setenv("SLURM_RESTART_COUNT", "1")
    assert reasons.read_exit_notes() == []                                 # a new start ignores old notes


def test_catalog_entries_parse_cleanly():
    """A comma inside an unquoted name splits a YAML flow mapping (CK-05 and Q-06 had this)."""
    allowed = {"id", "area", "name", "unit", "direction", "low", "medium", "high", "sim", "owner", "why", "action",
               "scale"}
    bad = {m["id"]: sorted(set(m) - allowed) for m in CAT["metrics"] if set(m) - allowed}
    assert not bad, f"quote these names in catalog.yaml: {bad}"
