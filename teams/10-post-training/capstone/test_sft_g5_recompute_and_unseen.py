"""Activation recompute on Team 5's blocks and the calibrated / uncalibrated expert report (Lab 5, design task 2).

Tiny CPU model of Team 5's real classes (t2 arm shrunk, router bias on). Mechanics only.

    python -m pytest capstone/test_sft_g5_recompute_and_unseen.py -q
"""
from __future__ import annotations

import copy
import re
import shlex
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("safetensors")
HERE = Path(__file__).resolve().parent
TEAMS = HERE.parents[1]
H5 = TEAMS / "05-architecture" / "harness"
sys.path[:0] = [str(HERE), str(TEAMS / "10-post-training" / "rl-loop"), str(H5)]
import dryrun2_dt_compare as job  # noqa: E402
import sft_g5  # noqa: E402
from sft_g5 import dtmask  # noqa: E402
from week2 import config as C  # noqa: E402
from week2.model import LanguageModel  # noqa: E402

parametrize = pytest.mark.parametrize
IDS = torch.randint(0, 256, (2, 16), generator=torch.Generator().manual_seed(5))
VALID = torch.ones_like(IDS, dtype=torch.bool)


def _make():
    m = copy.deepcopy(C.load_runtime(str(TEAMS / "05-architecture" / "configs" / "arms" / "t2.yaml"))["model"])
    m.update(vocab_size=256, block_size=32, n_layer=2, n_head=2, n_kv_head=1, n_embd=64)
    m["moe"] = dict(m["moe"], num_experts=4, top_k=2, num_shared=1, ffn_hidden=32, bias_gamma=0.001)
    rows = torch.randint(0, 255, (256, 32), generator=torch.Generator().manual_seed(1)).to(torch.uint8)
    lengths = torch.randint(1, 5, (256,), generator=torch.Generator().manual_seed(2))
    torch.manual_seed(0)
    return LanguageModel(m, rows, lengths)


def _grads(model, recompute: bool):
    model.train()
    model.zero_grad(set_to_none=True)
    with sft_g5.block_recompute(model, recompute) as wrapped:
        logits = model(IDS, VALID)
        loss = torch.nn.functional.cross_entropy(logits[:, :-1].reshape(-1, 256), IDS[:, 1:].reshape(-1))
        loss.backward()
    return wrapped, loss.detach(), {n: p.grad.clone() for n, p in model.named_parameters() if p.grad is not None}


@parametrize("method", ["full", "dt"])
def test_recompute_gives_the_same_loss_and_gradients_on_the_same_parameters(method):
    base = _make()
    if method == "dt":
        dtmask.convert(base, dtmask.TARGET_SETS["g5_gate"], 100, 1000, 10, seed=0)
    other = copy.deepcopy(base)
    n0, loss0, g0 = _grads(base, False)
    n1, loss1, g1 = _grads(other, True)
    assert (n0, n1) == (0, 2)
    assert torch.equal(loss0, loss1)
    assert g0.keys() == g1.keys() and g0
    for n in g0:
        torch.testing.assert_close(g1[n], g0[n], rtol=1e-5, atol=1e-7, msg=n)
    for (n, a), (_, b) in zip(base.named_buffers(), other.named_buffers()):
        assert torch.equal(a, b), n  # router_bias included


def test_recompute_really_reruns_the_block_and_restores_forward():
    model = _make().train()
    calls = []
    hook = model.blocks[0].attn.register_forward_hook(lambda *_: calls.append(1))
    _grads(model, True)
    assert len(calls) == 2  # forward, then again inside backward
    assert all("forward" not in b.__dict__ for b in model.blocks)
    calls.clear()
    _grads(model, False)
    assert len(calls) == 1
    calls.clear()
    with sft_g5.block_recompute(model, True), torch.no_grad():
        model(IDS, VALID)
    assert len(calls) == 1  # no gradients: nothing to recompute
    hook.remove()


def test_forward_is_restored_when_the_step_raises():
    model = _make().train()
    with pytest.raises(RuntimeError, match="boom"):
        with sft_g5.block_recompute(model, True):
            raise RuntimeError("boom")
    assert all("forward" not in b.__dict__ for b in model.blocks)


@parametrize("policy", ["official", "keep"])
def test_unseen_report_splits_the_experts_calibration_missed(policy):
    model = _make()
    dtmask.convert(model, dtmask.TARGET_SETS["g5_gate"], 100, 1000, 10, seed=0)
    layers = dict(dtmask.masked_layers(model))
    idle = [n for n in layers if n.startswith("blocks.0.moe.experts.")][:2]
    scores = {n: m.base_weight.abs().float() for n, m in layers.items() if n not in idle}
    prior = dtmask.apply_wanda_prior(torch.nn.ModuleDict({"lm": model}), {f"lm.{n}": v for n, v in scores.items()},
                                     1 / 2048, unseen=policy)
    assert prior["unseen_layer_names"] == [f"lm.{n}" for n in idle] and prior["layers_without_scores"] == 2
    rep = dtmask.unseen_report(model, prior["unseen_layer_names"])  # names carry the wrapper's "lm." prefix
    whole = dtmask.deletion_stats(model)
    assert rep["unseen"]["layers"] == 2 and rep["seen"]["layers"] == len(layers) - 2
    assert rep["unseen"]["deleted"] + rep["seen"]["deleted"] == whole["deleted"]
    assert rep["unseen"]["targeted"] + rep["seen"]["targeted"] == whole["targeted"]
    if policy == "official":
        assert 0.35 < rep["unseen"]["deleted_frac"] < 0.65 and rep["seen"]["deleted_frac"] < 0.02
    else:
        assert rep["unseen"]["deleted_frac"] < 0.02


def test_keep_changes_nothing_when_every_layer_has_a_score():
    masks = []
    for policy in ("official", "keep"):
        model = _make()
        dtmask.convert(model, dtmask.TARGET_SETS["g5_gate"], 100, 1000, 10, seed=0)
        scores = {n: m.base_weight.abs().float() for n, m in dtmask.masked_layers(model)}
        prior = dtmask.apply_wanda_prior(model, scores, 1 / 2048, unseen=policy)
        assert prior["unseen_layer_names"] == []
        masks.append([m.gate.clone() for _, m in dtmask.masked_layers(model)])
    assert all(torch.equal(a, b) for a, b in zip(*masks))


def test_the_comparison_job_command_asks_for_keep_and_the_wrapper_passes_it_to_the_dt_arm():
    text = (HERE.parent / "jobs" / "2026-11-26-g10-dryrun2-dt-vs-fft.md").read_text(encoding="utf-8")
    line = next(x for x in text.splitlines() if x.startswith("Command:"))
    words = shlex.split(re.sub(r"<([A-Z0-9_]+)>", r"/staged/\1", line.split(" -- ", 1)[1]))
    a = job.parse_args(["--g5-root", "g", "--run-folder", "r", "--tokenizer", "t", "--byte-table", "b", *words])
    cmd = job.build_arm_cmd(a, "dt", Path("c"), Path("t"), Path("d"), Path("o"), 3, False)
    assert cmd[cmd.index("--dt-unseen") + 1] == "keep" and cmd[cmd.index("--dt-calib-rows") + 1] == "64"
    assert "--dt-unseen" not in job.build_arm_cmd(a, "full", Path("c"), Path("t"), Path("d"), Path("o"), 3, False)


def test_unseen_report_with_nothing_unseen_and_with_an_unknown_name():
    model = _make()
    dtmask.convert(model, dtmask.TARGET_SETS["g5_gate"], 100, 1000, 10, seed=0)
    rep = dtmask.unseen_report(model, [])
    assert rep["unseen"] == {"layers": 0, "deleted": 0, "targeted": 0, "deleted_frac": None}
    with pytest.raises(ValueError, match="not in the model"):
        dtmask.unseen_report(model, ["blocks.9.moe.experts.0.gate"])


def test_comparison_table_prints_both_groups():
    rep = {"unseen": {"layers": 2, "deleted": 5, "targeted": 10, "deleted_frac": 0.5},
           "seen": {"layers": 6, "deleted": 1, "targeted": 1000, "deleted_frac": 0.001}}
    dt = {"log": [{}], "optimizer": {"kind": "adamw", "optim_step_share": 0.1}, "train_peak_memory_bytes": 123,
          "method": {"wanda_prior": {"unseen_policy": "keep", "layers_without_scores": 2},
                     "unseen_at_init": rep, "unseen_final": rep}}
    comp, md = job.summarise_comparison({"dt": dt}, None)
    assert comp["arms"]["dt"]["dt_unseen_final"] == rep and comp["arms"]["dt"]["train_peak_memory_bytes"] == 123
    assert "at init: uncalibrated layers 0.50000 (2 layers), calibrated layers 0.00100 (6 layers)" in md
    assert "Deleted fraction final:" in md
