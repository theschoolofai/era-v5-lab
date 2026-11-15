"""Deletion Tuning as the RL method (train.dt): only mask logits train, base weights never change, state resumes.

Toy task, tiny random OLMoE, CPU. Fixtures, not training data.
"""
import copy
import json
import sys
from pathlib import Path

import pytest
import torch
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import train  # noqa: E402

TIMING = {"times_s", "step_s", "seconds", "rollout_tokens_per_s", "peak_torch_gb", "gpu_used_gb", "gpu_total_gb"}


def cfg_dt(out: Path, steps: int) -> dict:
    cfg = yaml.safe_load((HERE / "config" / "smoke_objective_v1.yaml").read_text())
    cfg["out_dir"] = str(out)
    cfg["verbose"] = False
    cfg["train"].update(steps=steps, eval_every=4, state_every=2, state_dir=str(out / "state"), ppo_epochs=1, lr=0.01,
                        dt={"targets": "attn", "alpha_start": 5.0, "alpha_end": 50.0, "eta": 0.05, "calib_prompts": 8,
                            "alpha_steps": 8})
    return cfg


def rows(out: Path, name: str) -> list[dict]:
    return [{k: v for k, v in json.loads(line).items() if k not in TIMING}
            for line in (out / name).read_text().splitlines()]


def final_state(out: Path) -> dict:
    latest = json.loads((out / "state" / "LATEST.json").read_text())
    return torch.load(out / "state" / latest["file"], map_location="cpu", weights_only=False)


def test_dt_trains_only_mask_logits_and_reports_deletions(tmp_path):
    s = train.train(cfg_dt(tmp_path / "run", 8))
    d = s["deletion_tuning"]
    assert d["masked_layers"] > 0 and d["optimizer_steps"] == s["objective"]["steps_with_optimizer_update"]
    assert d["wanda_prior"]["prior_deleted"] > 0
    assert 0 < d["deletion_final"]["deleted_frac_of_targeted"] < 1
    st = final_state(tmp_path / "run")
    assert st["trainable"] and all(n.endswith(".gate") for n in st["trainable"])  # nothing but logits is trainable
    assert st["dt_steps"] == d["optimizer_steps"]
    assert s["router_unchanged"]
    recs = rows(tmp_path / "run", "metrics.jsonl")
    stepped = [r for r in recs if r.get("optimizer_stepped")]
    assert stepped and all("dt_deleted" in r and r["dt_alpha"] >= 5.0 for r in stepped)
    assert stepped[-1]["dt_alpha"] > stepped[0]["dt_alpha"]  # the sharpness schedule advances with optimizer steps
    assert s["trainable_weight_change"]["share_changed"] > 0


def test_dt_base_weights_are_bitwise_unchanged(tmp_path, monkeypatch):
    seen = {}
    real_convert = None

    def spy(model, *a, **kw):
        seen["before"] = {n: p.detach().clone() for n, p in model.named_parameters()}
        seen["model"] = model
        return real_convert(model, *a, **kw)

    dt = train.load_dt()
    real_convert = dt.convert
    monkeypatch.setattr(dt, "convert", spy)
    monkeypatch.setattr(train, "load_dt", lambda: dt)
    train.train(cfg_dt(tmp_path / "run", 6))
    after = dict(seen["model"].named_parameters())
    assert any(n.endswith(".gate") for n in after)
    for n, p in seen["before"].items():
        assert torch.equal(p, after[n].detach()), n  # every pretrained tensor, routers included


def test_dt_stop_and_continue_equals_uninterrupted(tmp_path):
    whole = train.train(cfg_dt(tmp_path / "whole", 8))
    cfg = cfg_dt(tmp_path / "split", 8)
    cfg["train"]["max_steps_this_call"] = 3
    assert train.train(copy.deepcopy(cfg))["status"] == "PAUSED_AT_DEADLINE"
    del cfg["train"]["max_steps_this_call"]
    done = train.train(copy.deepcopy(cfg))
    assert done["status"] == "COMPLETE" and done["resumed_from_step"] == 3
    assert rows(tmp_path / "whole", "metrics.jsonl") == rows(tmp_path / "split", "metrics.jsonl")
    assert rows(tmp_path / "whole", "evals.jsonl") == rows(tmp_path / "split", "evals.jsonl")
    a, b = final_state(tmp_path / "whole"), final_state(tmp_path / "split")
    assert a["dt_steps"] == b["dt_steps"] > 0
    for n in a["trainable"]:
        assert torch.equal(a["trainable"][n], b["trainable"][n]), n
    assert whole["deletion_tuning"]["deletion_final"] == done["deletion_tuning"]["deletion_final"]


def test_dt_refuses_other_algorithms_and_trainable_patterns(tmp_path):
    cfg = cfg_dt(tmp_path / "a", 2)
    cfg["train"]["algo"] = "dr_grpo"
    with pytest.raises(ValueError, match="train.dt"):
        train.train(cfg)
    cfg = cfg_dt(tmp_path / "b", 2)
    cfg["train"]["trainable"] = ["attn"]
    with pytest.raises(ValueError, match="train.dt"):
        train.train(cfg)
