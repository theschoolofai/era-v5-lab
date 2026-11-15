"""Tests for forgetting.py: the before/after comparison of two evaluate.py reports."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import forgetting as fg  # noqa: E402

SHA = "21c6e4b2" + "0" * 48 + "12bb"


def rec(task, value, stderr=0.01, n=500):
    return {"task": task, "metric": "acc_norm", "filter": "none", "value": value, "stderr": stderr, "n_items": n,
            "num_fewshot": 0}


def report(bpb=1.00, arc=0.40, hella=0.50, **over):
    r = {
        "schema": fg.SCHEMA, "device": "cuda", "compute_dtype": "float32 (TF32 off)", "tokenizer_sha256": "t" * 64,
        "forgetting": {"heldout_sha256": SHA, "window": 2048, "bpb_all": bpb, "groups": {"web": bpb, "code": bpb + 0.1}},
        "eval_mini": {"returncode": 0, "records": [rec("arc_challenge", arc), rec("hellaswag", hella)]},
    }
    r.update(over)
    return r


def test_no_change_is_not_forgetting():
    res = fg.compare(report(), report())
    assert res["forgetting"] is False and res["reasons"] == []
    assert res["bpb"]["delta"] == 0 and res["benchmarks"]["arc_challenge"]["delta"] == 0


def test_bpb_rise_over_limit_is_forgetting_and_at_limit_is_not():
    assert fg.compare(report(), report(bpb=1.0501))["forgetting"] is True
    assert fg.compare(report(), report(bpb=1.0499))["forgetting"] is False
    assert fg.compare(report(), report(bpb=0.90))["forgetting"] is False  # lower is better
    res = fg.compare(report(), report(bpb=1.2), max_bpb_rise=0.5)
    assert res["forgetting"] is False


def test_benchmark_drop_needs_both_sigmas_and_min_drop():
    # drop 0.05 against combined stderr ~0.0141 -> 3.5 sigma -> forgetting
    res = fg.compare(report(), report(arc=0.35))
    assert res["forgetting"] and res["benchmarks"]["arc_challenge"]["significant_drop"]
    assert "arc_challenge" in res["reasons"][0]
    # drop 0.02 is 1.4 sigma -> noise
    assert not fg.compare(report(), report(arc=0.38))["forgetting"]
    # tiny stderr: 5 sigma but under the absolute floor 0.01 -> not flagged
    tiny_b, tiny_a = report(), report(arc=0.395)
    for r in (tiny_b, tiny_a):
        r["eval_mini"]["records"][0]["stderr"] = 0.0005
    assert not fg.compare(tiny_b, tiny_a)["forgetting"]
    # a gain is never forgetting
    assert not fg.compare(report(), report(arc=0.60, hella=0.70))["forgetting"]


def test_missing_stderr_is_never_a_significant_drop_and_is_flagged():
    b, a = report(), report(arc=0.10)
    for r in (b, a):
        del r["eval_mini"]["records"][0]["stderr"]
    res = fg.compare(b, a)
    row = res["benchmarks"]["arc_challenge"]
    assert row["no_stderr"] and not row["significant_drop"] and not res["forgetting"]
    assert "no stderr" in fg.render_markdown(res)


@pytest.mark.parametrize("mutate,needle", [
    (lambda r: r["forgetting"].update(heldout_sha256="f" * 64), "held-out"),
    (lambda r: r["forgetting"].update(window=1024), "window"),
    (lambda r: r.update(tokenizer_sha256="x" * 64), "tokenizer"),
    (lambda r: r.update(device="cpu"), "device"),
    (lambda r: r.update(compute_dtype="bf16"), "compute_dtype"),
    (lambda r: r["eval_mini"]["records"][0].update(n_items=100), "n_items"),
    (lambda r: r["eval_mini"]["records"][1].update(num_fewshot=5), "num_fewshot"),
    (lambda r: r["eval_mini"]["records"][1].update(metric="acc"), "metric"),
])
def test_reports_that_measured_different_things_are_refused(mutate, needle):
    after = report()
    mutate(after)
    with pytest.raises(fg.ReportError, match=needle):
        fg.compare(report(), after)


@pytest.mark.parametrize("which", ["before", "after"])
@pytest.mark.parametrize("mutate,needle", [
    (lambda r: r.pop("forgetting"), "forgetting"),
    (lambda r: r.pop("eval_mini"), "eval_mini"),
    (lambda r: r["forgetting"].update(bpb_all=float("nan")), "bpb_all"),
    (lambda r: r["forgetting"].update(bpb_all="1.0"), "bpb_all"),
    (lambda r: r["forgetting"].pop("heldout_sha256"), "heldout_sha256"),
    (lambda r: r["eval_mini"].update(returncode=1), "failed"),
    (lambda r: r["eval_mini"].update(error_tail=["Error"]), "failed"),
    (lambda r: r["eval_mini"].update(records=[]), "failed"),
    (lambda r: r["eval_mini"]["records"].pop(), "missing hellaswag"),
    (lambda r: r["eval_mini"]["records"].append(rec("arc_challenge", 0.4)), "twice"),
    (lambda r: r["eval_mini"]["records"][0].update(value=None), "numeric"),
])
def test_unusable_reports_are_refused_with_the_side_named(which, mutate, needle):
    b, a = report(), report()
    mutate(b if which == "before" else a)
    with pytest.raises(fg.ReportError, match=f"{which}.*{needle}|{needle}"):
        fg.compare(b, a)


def test_groups_accept_numbers_or_dicts_and_skip_unshared_or_bad_ones():
    b, a = report(), report(bpb=1.01)
    b["forgetting"]["groups"] = {"web": {"bpb": 1.0}, "code": 1.1, "only_before": 2.0, "bad": "x"}
    a["forgetting"]["groups"] = {"web": {"bpb": 1.02}, "code": 1.3, "bad": 1.0}
    g = fg.compare(b, a)["bpb"]["groups"]
    assert set(g) == {"web", "code"}
    assert g["web"]["delta"] == pytest.approx(0.02) and g["code"]["delta"] == pytest.approx(0.2)


def test_comparison_does_not_change_its_inputs():
    b, a = report(), report(bpb=1.2, arc=0.3)
    b0, a0 = copy.deepcopy(b), copy.deepcopy(a)
    fg.compare(b, a)
    assert b == b0 and a == a0


def test_merge_reports_joins_separate_files_and_refuses_conflicts():
    full = report()
    bpb_only = {k: v for k, v in full.items() if k != "eval_mini"}
    mini_only = {"eval_mini": full["eval_mini"], "schema": fg.SCHEMA}
    assert fg.merge_reports(bpb_only, mini_only)["eval_mini"] == full["eval_mini"]
    other = {"eval_mini": {"returncode": 0, "records": []}}
    with pytest.raises(fg.ReportError, match="eval_mini"):
        fg.merge_reports(mini_only, other)
    # the same content twice is fine
    assert fg.merge_reports(mini_only, copy.deepcopy(mini_only))


def test_markdown_holds_every_number_and_the_verdict():
    res = fg.compare(report(), report(bpb=1.20, arc=0.30))
    md = fg.render_markdown(res)
    for s in ("1.0000", "1.2000", "+0.2000", "arc_challenge", "hellaswag", "FORGETTING", SHA, "group code"):
        assert s in md
    assert "No forgetting" in fg.render_markdown(fg.compare(report(), report()))


def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_cli_exit_codes_and_outputs(tmp_path, capsys):
    b, ok, bad = (write(tmp_path / n, d) for n, d in
                  [("b.json", report()), ("ok.json", report(bpb=1.01)), ("bad.json", report(bpb=1.5))])
    out = tmp_path / "sub" / "f.md"
    js = tmp_path / "f.json"
    assert fg.main(["--before", b, "--after", ok, "--out", str(out), "--out-json", str(js)]) == 0
    assert "No forgetting" in out.read_text(encoding="utf-8") and json.loads(js.read_text())["forgetting"] is False
    assert fg.main(["--before", b, "--after", bad, "--out", str(out)]) == 1
    assert "FORGETTING" in out.read_text(encoding="utf-8")
    capsys.readouterr()


def test_cli_bad_input_is_exit_2_with_a_message_and_writes_nothing(tmp_path, capsys):
    b = write(tmp_path / "b.json", report())
    other = report()
    other["forgetting"]["heldout_sha256"] = "e" * 64
    o = write(tmp_path / "o.json", other)
    notjson = tmp_path / "x.json"
    notjson.write_text("{nope", encoding="utf-8")
    lst = write(tmp_path / "l.json", [1, 2])
    out = tmp_path / "f.md"
    for after in (o, str(notjson), lst, str(tmp_path / "missing.json")):
        assert fg.main(["--before", b, "--after", after, "--out", str(out)]) == 2
        assert "error:" in capsys.readouterr().err
    assert not out.exists()


def test_cli_merges_separate_forgetting_and_eval_mini_files(tmp_path):
    full = report()
    parts = {}
    for side, r in (("b", full), ("a", report(bpb=1.01))):
        parts[side] = (write(tmp_path / f"{side}1.json", {k: v for k, v in r.items() if k != "eval_mini"}),
                       write(tmp_path / f"{side}2.json", {"eval_mini": r["eval_mini"]}))
    assert fg.main(["--before", *parts["b"], "--after", *parts["a"], "--out", str(tmp_path / "f.md")]) == 0


def test_a_rise_exactly_at_the_limit_is_not_forgetting():
    # 1.25 - 1.0 is exactly 0.25 in binary floating point, so this tests the boundary itself
    assert not fg.compare(report(bpb=1.0), report(bpb=1.25), max_bpb_rise=0.25)["forgetting"]
    assert fg.compare(report(bpb=1.0), report(bpb=1.5), max_bpb_rise=0.25)["forgetting"]
