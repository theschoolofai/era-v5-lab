"""rollout_check.py: the weights export, the verdict, and its place in the trainer. A tiny Team 5 model on CPU, made-up
scores, no benchmark data: mechanics only.

    python -m pytest rl-loop/test_rollout_check.py -q
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("safetensors")
import yaml  # noqa: E402
from safetensors.torch import load_file  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import quant_rollout as qr  # noqa: E402
import rollout_check as rc  # noqa: E402
import train  # noqa: E402

parametrize = pytest.mark.parametrize

# Stands in for Team 9's script in these tests: each made-up score file carries one number, "bpb".
STAND_IN = """
def compare(baseline, candidate):
    d = candidate["bpb"] - baseline["bpb"]
    return {"tasks": {"mmlu_x": {"gold_bpb_delta": d, "gold_bpb_ci95": [d - 0.01, d + 0.01]}},
            "heldout_bpb_delta": {"val/bpb": d}, "profile": "quick"}
"""


@pytest.fixture
def script(tmp_path):
    path = tmp_path / "stand_in_compare.py"
    path.write_text(STAND_IN)
    return path


def _config(tmp_path, steps=4, check=None, **overrides):
    cfg = yaml.safe_load((HERE / "config" / "smoke_team5_tiny.yaml").read_text())
    cfg["out_dir"] = str(tmp_path / "out")
    cfg["task"].update(n_train=32, n_heldout=8)
    cfg["train"].update(steps=steps, eval_every=steps, eval_k=2, prompts_per_step=4, k=4, ppo_epochs=1, sampler="quant",
                        quant={"scheme": "w4a16_sim", "guard": False}, **overrides)
    if check is not None:
        cfg["train"]["rollout_check"] = check
    cfg["verbose"] = False
    return cfg


def _rows(tmp_path):
    return [json.loads(x) for x in (tmp_path / "out" / "metrics.jsonl").read_text().splitlines()]


def _score(step_dir: Path, role: str, bpb: float, **changes):
    request = json.loads((step_dir / "request.json").read_text())
    doc = {"model_revision": request["weights"][role]["sha256"], "step": request["step"], "bpb": bpb, **changes}
    (step_dir / request["scores"][role]).write_text(json.dumps(doc))


HASHES = {k: f"made-up {k}" for k in rc.SUITE_HASHES}


def _fast_scorer(monkeypatch, rollout_bpb: float):
    """Score files appear as soon as the trainer has exported, as from a scorer faster than one step."""
    real = rc.export

    def export(*args, **kwargs):
        step_dir = real(*args, **kwargs)
        _score(step_dir, "learner", 2.0, **HASHES)
        _score(step_dir, "rollout", rollout_bpb, **HASHES)
        return step_dir

    monkeypatch.setattr(rc, "export", export)


def _export_tiny(tmp_path, step=5, scheme="w4a16_sim"):
    cfg = _config(tmp_path)
    policy, _ = train.build_model(copy.deepcopy(cfg["model"]), "cpu")
    rollout, _info = qr.quantized_copy(policy.model, scheme)
    d = rc.export(tmp_path / "check", step, policy.model, rollout, scheme, policy.model_spec, "ab" * 32)
    return policy, rollout, d


def test_the_exported_files_load_strictly_into_team5s_model_and_match(tmp_path):
    policy, rollout, d = _export_tiny(tmp_path)
    from week2.model import LanguageModel  # noqa: PLC0415  (on sys.path once build_model has run)
    request = json.loads((d / "request.json").read_text())
    config = json.loads((d / request["model_config"]).read_text())
    assert config["artifacts"]["tokenizer_sha256"] == "ab" * 32 and request["scores_cover_the_whole_scheme"]
    ids = torch.randint(0, 16, (2, 8), generator=torch.Generator().manual_seed(0))
    valid = torch.ones_like(ids, dtype=torch.bool)
    for role, source in (("learner", policy.model), ("rollout", rollout)):
        path = d / request["weights"][role]["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == request["weights"][role]["sha256"]
        spec = config["config"]["model"]
        torch.manual_seed(123)  # other initial weights: only the file may make them equal
        table = policy.model.state_dict()["embedding.rows"]
        fresh = LanguageModel(spec, torch.zeros_like(table), torch.ones(spec["vocab_size"], dtype=torch.int16)).eval()
        fresh.load_state_dict(load_file(str(path)), strict=True)
        with torch.no_grad():
            torch.testing.assert_close(fresh(ids, valid), source.eval()(ids, valid), rtol=0, atol=0)
    assert any(not torch.equal(a, b) for a, b in zip(policy.model.state_dict().values(), rollout.state_dict().values()))


def test_the_verdict_uses_only_the_deciding_tasks_and_both_measures():
    def compare(_b, _c):
        good = {"gold_bpb_delta": 0.0, "gold_bpb_ci95": [-0.1, 0.1], "accuracy_delta_points": -5.0,
                "accuracy_ci95_points": [-10.0, 0.0]}
        return {"tasks": {"mmlu_a": good,
                          "milu_b": {**good, "gold_bpb_delta": 0.2, "gold_bpb_ci95": [0.1, 0.3]},
                          "arith_c": {**good, "accuracy_ci95_points": [-20.0, -1.0], "accuracy_delta_points": -9.0},
                          "hellaswag_d": {**good, "gold_bpb_ci95": [5.0, 6.0]}},
                "heldout_bpb_delta": {"val/bpb": 0.4}, "profile": "quick"}

    v = rc.judge({}, {}, compare)
    assert v["verdict"] == "worse" and set(v["tasks"]) == {"mmlu_a", "milu_b", "arith_c"}
    assert [w.split(":")[0] for w in v["worse"]] == ["arith_c", "milu_b"] and v["heldout_bpb_delta"] == {"val/bpb": 0.4}
    assert [w.split(":")[0] for w in rc.judge({}, {}, compare, min_bpb=0.25)["worse"]] == ["arith_c"]  # 0.2 is below it
    with pytest.raises(ValueError, match="deciding"):
        rc.judge({}, {}, lambda *_: {"tasks": {"hellaswag_d": {}}})


def test_a_step_waits_for_its_scores_refuses_other_weights_and_then_drops_the_weights(tmp_path, script):
    compare = rc.load_compare(script)
    _, _, d = _export_tiny(tmp_path)
    root = d.parent
    assert rc.poll(root, compare) == {"new": [], "pending": [5], "errors": []}
    _score(d, "learner", 2.0)
    _score(d, "rollout", 2.5, model_revision="0" * 64)
    got = rc.poll(root, compare)
    assert not got["new"] and "does not score the rollout weights of step 5" in got["errors"][0]
    for broken in ("{", "[1, 2]", "null"):  # whatever the file holds, it is reported, not raised
        (d / "rollout.score.json").write_text(broken)
        assert rc.poll(root, compare)["errors"] and len(list(d.glob("*.safetensors"))) == 2
    (root / "step_notes").mkdir()  # a folder that is not a step is ignored
    _score(d, "rollout", 2.5)
    assert rc.poll(root, compare, up_to=4) == {"new": [], "pending": [], "errors": []}
    verdict, = rc.poll(root, compare)["new"]
    assert verdict["verdict"] == "worse" and verdict["baseline"] == "learner at the same step"
    assert not list(d.glob("*.safetensors")) and rc.verdicts(root) == [verdict]
    assert rc.poll(root, compare) == {"new": [], "pending": [], "errors": []}
    assert rc.main(["judge", "--check-dir", str(root), "--compare-script", str(script)]) == 4
    _export_tiny(tmp_path)  # the step is redone: the old scores and verdict are gone
    assert not (d / "verdict.json").exists() and rc.poll(root, compare)["pending"] == [5]
    assert rc.main(["judge", "--check-dir", str(root), "--compare-script", str(script)]) == 3


def test_scores_from_different_devices_are_not_compared(tmp_path, script):
    _, _, d = _export_tiny(tmp_path)
    _score(d, "learner", 2.0, device="cpu")
    _score(d, "rollout", 2.5, device="cuda")
    got = rc.poll(d.parent, rc.load_compare(script))
    assert not got["new"] and "differ in device (cpu / cuda)" in got["errors"][0]
    assert len(list(d.glob("*.safetensors"))) == 2  # kept, so either side can be scored again
    _score(d, "rollout", 2.0, device="cpu", profile="smoke")
    _score(d, "learner", 2.0, device="cpu", profile="smoke")
    assert "execution evidence only" in rc.poll(d.parent, rc.load_compare(script))["errors"][0]
    _export_tiny(tmp_path)
    _score(d, "learner", 2.0, device="cpu")
    _score(d, "rollout", 2.0, device="cpu")
    assert rc.poll(d.parent, rc.load_compare(script))["new"] and not list(d.glob("*.safetensors"))


def test_the_control_runs_rollout_copy_is_the_baseline_when_given(tmp_path, script):
    compare = rc.load_compare(script)
    _, _, quant = _export_tiny(tmp_path / "quant")
    _, _, control = _export_tiny(tmp_path / "control", scheme="bf16")
    _score(quant, "rollout", 2.0)
    assert rc.poll(quant.parent, compare, control.parent)["pending"] == [5]
    _score(control, "rollout", 2.3)
    verdict, = rc.poll(quant.parent, compare, control.parent)["new"]
    assert verdict["verdict"] == "ok" and verdict["baseline"] == "control run's rollout copy (bf16)"
    sha = {d: json.loads((d / "request.json").read_text())["weights"]["rollout"]["sha256"] for d in (control, quant)}
    assert verdict["revision"] == {"baseline": sha[control], "candidate": sha[quant]}
    assert (control / "rollout.safetensors").exists()  # the control run's files are never touched
    assert (quant / "learner.safetensors").exists()  # not scored yet, so kept
    assert not (quant / "rollout.safetensors").exists()  # scored, so gone even before the control's score arrived


def test_a_report_run_records_verdicts_and_trains_exactly_as_without_the_check(tmp_path, script, monkeypatch):
    plain = train.train(_config(tmp_path / "plain"))
    _fast_scorer(monkeypatch, rollout_bpb=2.5)
    check = {"dir": str(tmp_path / "check"), "every": 2, "compare_script": str(script)}
    s = train.train(_config(tmp_path / "checked", check=check))
    assert not s.get("failures") and s["steps"] == 4
    assert [v["step"] for v in s["rollout_check"]["verdicts"]] == [2, 4] and not s["rollout_check"]["pending_steps"]
    rows = _rows(tmp_path / "checked")
    assert [r["step"] for r in rows if "rollout_check" in r] == [2, 4]
    logged, = rows[1]["rollout_check"]  # what Team 9 asks to be logged: revision, step, format and the suite hashes
    assert logged["step"] == 2 and logged["scheme"] == "w4a16_sim" and logged["suite_hashes"] == HASHES
    assert all(len(v) == 64 for v in logged["revision"].values()) and len(set(logged["revision"].values())) == 2
    assert s["rollout_check"]["verdicts"][0] == logged
    assert [r["step"] for r in rows if "rollout_check_export_s" in r] == [2, 4]
    keep = ("train_reward", "loss", "mismatch_k3")
    assert [[r.get(k) for k in keep] for r in rows] == [[r.get(k) for k in keep] for r in _rows(tmp_path / "plain")]
    assert plain["heldout_reward_end"] == s["heldout_reward_end"]


def test_a_control_run_setup_writes_only_the_rollout_copy_and_late_judging_uses_the_same_baseline(tmp_path, script):
    control = tmp_path / "control"
    check = {"dir": str(tmp_path / "check"), "every": 4, "control": str(control), "min_bpb": 0.5,
             "compare_script": str(script)}
    train.train(_config(tmp_path, check=check))
    step_dir = tmp_path / "check" / "step_000004"
    assert sorted(p.name for p in step_dir.glob("*.safetensors")) == ["rollout.safetensors"]
    _, _, control_step = _export_tiny(tmp_path / "other", step=4, scheme="bf16")
    control_step.parent.rename(control)
    _score(control / "step_000004", "rollout", 2.0)
    _score(step_dir, "rollout", 2.3)  # worse by 0.3: below this run's floor of 0.5
    assert rc.main(["judge", "--check-dir", str(step_dir.parent), "--compare-script", str(script)]) == 0
    verdict, = rc.verdicts(step_dir.parent)
    assert verdict["baseline"] == "control run's rollout copy (bf16)" and verdict["min_bpb"] == 0.5


def test_unscored_exports_are_capped_but_the_last_step_is_always_written(tmp_path, script):
    check = {"dir": str(tmp_path / "check"), "every": 1, "max_pending": 2, "compare_script": str(script)}
    s = train.train(_config(tmp_path, steps=5, check=check))
    assert s["rollout_check"]["pending_steps"] == [1, 2, 5]
    assert [r["step"] for r in _rows(tmp_path) if r.get("rollout_check_skipped")] == [3, 4]


def test_a_run_that_died_before_its_first_saved_state_can_start_again(tmp_path, script):
    check = {"dir": str(tmp_path / "check"), "every": 2, "compare_script": str(script)}
    cfg = _config(tmp_path, check=check, state_dir=str(tmp_path / "state"), state_every=1, max_steps_this_call=2)
    train.train(copy.deepcopy(cfg))
    for f in (tmp_path / "state").iterdir():
        f.unlink()  # as if it had died before any state reached disk
    step_dir = tmp_path / "check" / "step_000002"
    _score(step_dir, "learner", 2.0)
    _score(step_dir, "rollout", 2.5)
    rc.poll(step_dir.parent, rc.load_compare(script))
    assert (step_dir / "verdict.json").exists()
    del cfg["train"]["max_steps_this_call"]
    s = train.train(cfg)
    assert s["steps"] == 4 and not s["rollout_check"]["verdicts"]  # the dead attempt's verdict was discarded
    assert s["rollout_check"]["pending_steps"] == [2, 4]
    other = _config(tmp_path, check=check, state_dir=str(tmp_path / "other_state"))
    with pytest.raises(ValueError, match="another run"):
        train.train(other)


def test_without_a_scorer_the_run_finishes_and_lists_the_pending_steps(tmp_path, script):
    check = {"dir": str(tmp_path / "check"), "every": 3, "action": "stop", "compare_script": str(script)}
    s = train.train(_config(tmp_path, check=check))
    assert not s.get("failures") and s["rollout_check"]["pending_steps"] == [3, 4]  # the last step is always checked
    assert _rows(tmp_path)[-1]["rollout_check_pending"] == 2
    with pytest.raises(ValueError, match="another run"):
        train.train(_config(tmp_path, check=check))


def test_action_stop_ends_the_run_and_it_stays_stopped(tmp_path, script, monkeypatch):
    _fast_scorer(monkeypatch, rollout_bpb=2.5)
    check = {"dir": str(tmp_path / "check"), "every": 2, "action": "stop", "compare_script": str(script)}
    cfg = _config(tmp_path, steps=6, check=check, state_dir=str(tmp_path / "state"), state_every=5)
    first = train.train(copy.deepcopy(cfg))
    again = train.train(copy.deepcopy(cfg))
    assert first["steps"] == again["steps"] == 2 and [r["step"] for r in _rows(tmp_path)] == [1, 2]
    assert first["quant"]["stopped"] == again["quant"]["stopped"]
    assert first["quant"]["stopped"]["check_step"] == 2 and "rollout check of step 2" in again["failures"][0]


def test_a_worse_verdict_already_on_disk_stops_a_resumed_run(tmp_path, script):
    check = {"dir": str(tmp_path / "check"), "every": 2, "action": "stop", "compare_script": str(script)}
    cfg = _config(tmp_path, steps=6, check=check, state_dir=str(tmp_path / "state"), state_every=1,
                  max_steps_this_call=3)
    assert train.train(copy.deepcopy(cfg))["status"] == "PAUSED_AT_DEADLINE"
    step_dir = tmp_path / "check" / "step_000002"
    _score(step_dir, "learner", 2.0)
    _score(step_dir, "rollout", 2.5)
    assert rc.main(["judge", "--check-dir", str(step_dir.parent), "--compare-script", str(script)]) == 4  # from outside
    del cfg["train"]["max_steps_this_call"]
    s = train.train(cfg)
    assert s["steps"] == 4 and s["quant"]["stopped"]["check_step"] == 2


@parametrize("change, match", [
    ({"check": {"every": 2}}, "rollout_check is"),
    ({"check": {"dir": "x", "action": "halt"}}, "rollout_check is"),
    ({"check": {"dir": "x", "every": 0}}, "rollout_check is"),
    ({"check": {"dir": "x", "max_pending": 0}}, "rollout_check is"),
    ({"check": {"dir": "x", "min_bpb": -0.1}}, "rollout_check is"),
    ({"check": {"dir": "x", "min_bpb": float("nan")}}, "rollout_check is"),
    ({"check": {"dir": "x", "control": "x"}}, "own folder"),
    ({"check": {"dir": "x", "compare_script": "no/such/file.py"}}, "lab PR 929"),
    ({"check": {"dir": "x"}, "model": "tiny_olmoe"}, "Team 5 model"),
    ({"check": {"dir": "x"}, "sampler": "policy"}, "sampler quant"),
])
def test_bad_check_configs_are_refused(tmp_path, change, match):
    cfg = _config(tmp_path, check=change["check"])
    if change.get("model"):
        cfg["model"] = yaml.safe_load((HERE / "config" / "smoke_tiny_olmoe.yaml").read_text())["model"]
    if change.get("sampler"):
        cfg["train"].update(sampler=change["sampler"])
        del cfg["train"]["quant"]
    with pytest.raises((ValueError, FileNotFoundError), match=match):
        train.train(cfg)


@pytest.mark.skipif(not rc.COMPARE_SCRIPT.is_file(), reason="Team 9's minibench_compare.py (lab PR 929) is not here")
def test_with_team9s_comparison_equal_scores_pass_and_a_uniform_loss_increase_fails():
    def doc(extra_nats):
        shared = {k: "x" for k in ("suite", "suite_sha256", "profile", "items_sha256", "heldout_sha256",
                                   "heldout_sources_sha256", "tokenizer_sha256")}
        items = [{"id": str(i), "gold_nll_nats": 3.0 + i / 10 + extra_nats, "utf8_bytes": 4, "correct": i % 2 == 0}
                 for i in range(20)]
        return {**shared, "schema_version": "minibench_cont_v1", "items": {"mmlu_cloze": items},
                "heldout": {"val/bpb": 2.0 + extra_nats}}

    compare = rc.load_compare()
    assert rc.judge(doc(0.0), doc(0.0), compare)["verdict"] == "ok"
    verdict = rc.judge(doc(0.0), doc(0.05), compare)
    assert verdict["verdict"] == "worse" and verdict["worse"][0].startswith("mmlu_cloze: gold bpb +")
