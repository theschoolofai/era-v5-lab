"""Lab 5 cross-contract tests:
1. rl-loop/metrics_feed.py output parses cleanly in Team 8's ClickHouse loader (teams/08-monitoring)
   and aligns with metric_list_v1.yaml.
2. rl-loop/train.py with optimizer=hybrid_muon saves and restores Muon momentum buffers (`buf`)
   across a state_dir stop-and-continue restart (TSAI 28 Nov Hybrid Muon requirement (b)).
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest
import torch
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
TEAM8_CATALOG = REPO_ROOT / "teams" / "08-monitoring" / "metrics" / "metric_list_v1.yaml"
TEAM8_LOADER = REPO_ROOT / "teams" / "08-monitoring" / "clickhouse" / "load_jsonl.py"

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import metrics_feed  # noqa: E402
import train  # noqa: E402


def _load_team8_loader():
    spec = importlib.util.spec_from_file_location("team8_load_jsonl", TEAM8_LOADER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.skipif(
    not (TEAM8_CATALOG.is_file() and TEAM8_LOADER.is_file()),
    reason="teams/08-monitoring files not present",
)
def test_metrics_feed_parses_in_team8_clickhouse_loader_and_matches_catalog(tmp_path):
    metrics = tmp_path / "metrics.jsonl"
    evals = tmp_path / "evals.jsonl"
    summary = tmp_path / "summary.json"
    feed = tmp_path / "rl_feed.jsonl"

    metrics.write_text(
        json.dumps({
            "step": 4,
            "train_reward": 0.625,
            "entropy": 0.41,
            "mismatch_k3": 0.0079,
            "mismatch_abs_logratio": 0.019,
            "grad_norm": 1.23,
            "group_kinds": {"mixed": 6, "all_pass": 1, "all_fail": 1},
            "rollout_tokens_per_s": 77.4,
            "times_s": {"reward": 0.42},
            "optim_step_s": 0.15,
            "step_s": 1.5,
            "kl_to_start": 0.03,
            "subgroups": {"code": {"passes": 4, "rollouts": 8}, "indic": {"passes": 6, "rollouts": 8}},
            "quant_scheme": "bf16",
            "quant_refresh_s": 0.12,
        }) + "\n",
        encoding="utf-8",
    )
    evals.write_text(
        json.dumps({"step": 4, "name": "heldout", "pass": 0.75}) + "\n"
        + json.dumps({"step": 4, "name": "heldout_quant", "pass": 0.74}) + "\n",
        encoding="utf-8",
    )
    summary.write_text(json.dumps({"router_unchanged": True}), encoding="utf-8")

    rows = metrics_feed.convert(metrics, feed, summary=summary, evals=evals)
    assert len(rows) == 1
    assert rows[0]["router_checksum_ok"] is True
    assert math.isclose(rows[0]["optim_step_share"], 0.1)

    catalog = yaml.safe_load(TEAM8_CATALOG.read_text(encoding="utf-8"))
    catalog_names = {entry["name"] for entry in catalog["metrics"]}
    for core in ("train_reward", "reward_per_env", "entropy", "mismatch_k3", "mismatch_abs_logratio", "gradient_norm"):
        assert core in catalog_names, f"{core} missing from Team 8 catalog"
        assert core in rows[0], f"{core} missing from metrics_feed output"

    loader = _load_team8_loader()
    parsed = loader.parse_source(str(feed), run_id_override="g10_lab5_rl_smoke")
    by_name = {item["name"]: item["value"] for item in parsed["rows"]}
    assert math.isclose(by_name["train_reward"], 0.625)
    assert math.isclose(by_name["reward_per_env.code"], 0.5)
    assert math.isclose(by_name["reward_per_env.indic"], 0.75)
    assert math.isclose(by_name["entropy"], 0.41)
    assert math.isclose(by_name["mismatch_k3"], 0.0079)
    assert math.isclose(by_name["mismatch_abs_logratio"], 0.019)
    assert math.isclose(by_name["gradient_norm"], 1.23)
    assert math.isclose(by_name["heldout_reward"], 0.75)
    assert math.isclose(by_name["optim_step_share"], 0.1)


def test_rl_train_hybrid_muon_stop_and_continue_restores_muon_buf(tmp_path):
    base = yaml.safe_load((HERE / "config" / "smoke_tiny_olmoe.yaml").read_text(encoding="utf-8"))

    def make_cfg(out_dir: Path, steps: int, state_dir: Path | None = None) -> dict:
        cfg = json.loads(json.dumps(base))
        cfg.update(seed=11, verbose=False, out_dir=str(out_dir))
        cfg["train"].update(
            algo="objective_v1",
            optimizer="hybrid_muon",
            lr=1e-3,
            muon_lr=5e-3,
            steps=steps,
            eval_every=4,
            prompts_per_step=4,
            k=4,
            max_new=8,
            fail_on_lost_update=False,
        )
        if state_dir is not None:
            cfg["train"]["state_dir"] = str(state_dir)
        return cfg

    # Uninterrupted 4-step Hybrid Muon run
    full_dir = tmp_path / "full"
    full_state = tmp_path / "full_state"
    s_full = train.train(make_cfg(full_dir, steps=4, state_dir=full_state))
    assert s_full["steps"] == 4
    assert "optimizer" in s_full and s_full["optimizer"]["kind"] == "hybrid_muon"

    # Interrupted at step 2, verify Muon momentum buffers are saved, then resume to step 4
    res_dir = tmp_path / "resumed"
    res_state = tmp_path / "resumed_state"
    s_part = train.train(make_cfg(res_dir, steps=2, state_dir=res_state))
    assert s_part["steps"] == 2
    saved_pt = res_state / "state.step000002.pt"
    assert saved_pt.is_file()
    payload = torch.load(saved_pt, map_location="cpu", weights_only=False)
    opt_state = payload["opt"]
    # HybridOptimizer state_dict nests one state dict per sub-optimizer under "optimizers"
    assert "muon" in opt_state["optimizers"], f"Expected muon sub-optimizer state, got {opt_state.keys()}"
    muon_states = opt_state["optimizers"]["muon"]["state"]
    assert any("buf" in st and isinstance(st["buf"], torch.Tensor) for st in muon_states.values()), (
        "Muon momentum buffer `buf` must be persisted in rl_state checkpoint"
    )

    s_res = train.train(make_cfg(res_dir, steps=4, state_dir=res_state))
    assert s_res["steps"] == 4
    assert s_res["heldout_reward_end"] == s_full["heldout_reward_end"]

    # Final saved trainable weights after resume must match uninterrupted run bit-for-bit
    st_full = torch.load(full_state / "state.step000004.pt", map_location="cpu", weights_only=False)["trainable"]
    st_res = torch.load(res_state / "state.step000004.pt", map_location="cpu", weights_only=False)["trainable"]
    assert set(st_full) == set(st_res)
    for k in st_full:
        assert torch.equal(st_full[k], st_res[k]), f"Weight mismatch after Hybrid Muon resume on {k}"
