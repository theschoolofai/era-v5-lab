"""Tests of guard_status.py.

    python -m pytest test_guard_status.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard_status as g  # noqa: E402

LINE = "model-Q5_K_M.gguf: log p(' Paris') = -0.5, generation -0.5, off-by-one value -7.0; cache max diff 0.0498"
DEFAULT_LOG = LINE + "\nPASS\n"
WARN_LOG = (LINE + "; check 4 warn only (EVAL_GUARD_CHECK4)\nWARN 4. easy item answered wrong: [-1.84, -1.84, -3.0, -4.0]\nPASS\n")
FAIL_LOG = LINE + "\nFAIL 3. prefix cache changes a score by 0.0784\n1 check(s) failed\n"
WARN = {"EVAL_GUARD_CHECK4": "warn"}


def test_parse_default_pass():
    r = g.parse_guard_log(DEFAULT_LOG, {})
    assert (r["result"], r["cache_diff"], r["warnings"], r["overrides"]) == ("PASS", 0.0498, [], {})


def test_parse_warning_run():
    r = g.parse_guard_log(WARN_LOG, WARN)
    assert r["result"] == "PASS" and len(r["warnings"]) == 1 and r["warnings"][0].startswith("4. easy item answered wrong")


def test_parse_fail_and_missing_result_line():
    assert g.parse_guard_log(FAIL_LOG, {})["result"] == "FAIL"
    assert g.parse_guard_log("model does not rank ' Paris' in its top-5\n", {})["result"] == "FAIL"


def test_parse_uses_the_last_run_of_an_appended_log():
    r = g.parse_guard_log(FAIL_LOG + WARN_LOG, WARN)
    assert r["result"] == "PASS" and len(r["warnings"]) == 1


def test_default_run_is_labelled_default_and_ships():
    guard = g.add_run(None, g.parse_guard_log(DEFAULT_LOG, {}), ["mmlu"], "t1")
    assert g.task_label(guard, "mmlu") == ("default", True)


def test_warn_mode_is_labelled_and_kept_out_of_the_ship_table():
    guard = g.add_run(None, g.parse_guard_log(WARN_LOG, WARN), ["mmlu"], "t1")
    label, ship = g.task_label(guard, "mmlu")
    assert ship is False and "check 4 warn mode" in label and "WARNING RAISED" in label


def test_warn_setting_without_a_warning_is_still_labelled():
    guard = g.add_run(None, g.parse_guard_log(DEFAULT_LOG, WARN), ["mmlu"], "t1")
    label, ship = g.task_label(guard, "mmlu")
    assert ship is False and label == "check 4 warn mode"


def test_cache_limit_label_and_the_default_limit_is_not_relaxed():
    ten = g.add_run(None, g.parse_guard_log(DEFAULT_LOG, {"EVAL_GUARD_CACHE_TOL": "0.10"}), ["mmlu"], "t1")
    assert g.task_label(ten, "mmlu") == ("check 3 limit 0.10", False)
    same = g.add_run(None, g.parse_guard_log(DEFAULT_LOG, {"EVAL_GUARD_CACHE_TOL": "0.05"}), ["mmlu"], "t1")
    assert g.task_label(same, "mmlu") == ("default", True)


def test_guard_prompt_override_is_labelled_but_does_not_exclude():
    guard = g.add_run(None, g.parse_guard_log(DEFAULT_LOG, {"EVAL_GUARD_CONTEXT": "The capital of France is the city of"}),
                      ["mmlu"], "t1")
    assert g.task_label(guard, "mmlu") == ("guard prompt override", True)


def test_a_later_guard_relog_does_not_relabel_tasks_scored_earlier():
    # scored under the defaults, then the format is re-logged under warn mode without scoring anything
    guard = g.add_run(None, g.parse_guard_log(DEFAULT_LOG, {}), ["mmlu", "arc_challenge"], "t1")
    guard = g.add_run(guard, g.parse_guard_log(WARN_LOG, WARN), [], "t2")
    assert g.task_label(guard, "mmlu") == ("default", True)
    # ... and a task scored in the later run carries the later label
    guard = g.add_run(guard, g.parse_guard_log(WARN_LOG, WARN), ["belebele_kan_Knda"], "t3")
    assert g.task_label(guard, "belebele_kan_Knda")[1] is False and g.task_label(guard, "mmlu")[1] is True


def test_task_without_a_record():
    assert g.task_label({"runs": []}, "mmlu") == ("no guard record", False)
