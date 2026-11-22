"""Tests of the Qwen3 surrogate profile (sft/bench/retok.py) and the ladder runner config (dt/run_ladder.py)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


retok = _load("g10_bench_retok_ladder_test", PKG / "sft/bench/retok.py")
ladder = _load("g10_dt_run_ladder_test", PKG / "dt/run_ladder.py")


def _qwen3_profile():
    retok.set_profile("qwen3")
    try:
        yield retok
    finally:
        retok.set_profile("smollm2")


qwen3 = pytest.fixture(_qwen3_profile, name="qwen3")


def test_default_profile_is_the_smollm2_bench():
    assert retok.PROFILE == "smollm2"
    assert retok.SPECIAL_IDS == frozenset(range(17))
    assert (retok.IM_END_ID, retok.EOS_ID) == (2, 0)
    assert retok.MARKER_MAP["think"] == ("<jupyter_script>", 15)


def test_qwen3_profile_maps_markers_to_existing_specials(qwen3):
    T = qwen3.T
    assert qwen3.SPECIAL_IDS == frozenset(range(151643, 151665))  # the 22 added tokens of the Base tokenizer.json
    assert (qwen3.IM_END_ID, qwen3.EOS_ID) == (151645, 151643)
    assert {sid for _, sid in qwen3.MARKER_MAP.values()} <= qwen3.SPECIAL_IDS
    text = f"{T['im_start']}assistant\n{T['think']}plan{T['think_end']}code{T['im_end']}"
    surr, moves = qwen3.to_surrogate(text)
    assert surr == "<|im_start|>assistant\n<|object_ref_start|>plan<|object_ref_end|>code<|im_end|>"
    assert len(moves) == 4
    assert qwen3.from_surrogate(surr) == text


def test_qwen3_profile_rejects_foreign_special_surfaces_in_content(qwen3):
    with pytest.raises(qwen3.RetokReject, match="surrogate_special_in_content"):
        qwen3.to_surrogate(f"{qwen3.T['im_start']}user\nuse <|fim_prefix|> here{qwen3.T['im_end']}")
    # <think> is not an added token of the Base tokenizer.json, so it stays plain text
    surr, _ = qwen3.to_surrogate(f"{qwen3.T['im_start']}user\n<think> as text{qwen3.T['im_end']}")
    assert "<think> as text" in surr


def test_unknown_profile_is_refused():
    with pytest.raises(SystemExit):
        retok.set_profile("llama")
    assert retok.PROFILE == "smollm2"


def test_flags_turns_config_into_cli():
    assert ladder.flags({"lr": 2e-3, "grad_checkpointing": True, "train_marker_rows": False, "micro_tokens": 4096}) == [
        "--lr", "0.002", "--grad-checkpointing", "--micro-tokens", "4096"]


def test_job_config_matches_the_preregistered_arms():
    cfg = ladder.load_config(str(PKG / "dt/ladder_qwen3.yaml"))
    assert cfg["profile"] == "qwen3" and cfg["keep_models"] is False
    tc = cfg["train_common"]
    assert (tc["steps"], tc["batch"], tc["seed"], tc["autocast"]) == (400, 8, 1, "bf16")
    arms = {f"{s['name']}/{a['name']}": a for s in cfg["sizes"] for a in s["arms"]}
    assert list(arms) == ["8b/base", "8b/dt", "8b/dtm", "8b/full", "8b/lora", "8b/full_lo", "4b/base", "4b/dt", "4b/dtm",
                          "4b/full", "4b/lora", "4b-steps/dtm_800"]
    lrs = {k: a.get("train", {}).get("lr") for k, a in arms.items()}
    assert lrs["4b/full"] == lrs["8b/full"] == 1e-4 and lrs["8b/full_lo"] == 1e-5
    assert lrs["4b/lora"] == lrs["8b/lora"] == 1e-3
    assert lrs["4b/dt"] == lrs["8b/dt"] == lrs["4b/dtm"] == 2e-3
    for k in ("4b/dtm", "8b/dtm", "4b-steps/dtm_800"):
        assert arms[k]["method"] == "dt" and arms[k]["train"]["train_marker_rows"] is True
    for k in ("4b/dt", "8b/dt"):
        assert "train_marker_rows" not in arms[k]["train"]
    assert arms["4b-steps/dtm_800"]["train"]["steps"] == 800
    methods = {a["method"] for a in arms.values()}
    assert methods <= {"base", "full", "lora", "dt"}
