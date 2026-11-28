"""Tests of dt_on_quantized.py: block quantizers against gguf-py, the packed masked layer, memory accounting, and every
arm end to end on a toy Qwen3 (CPU, no download).

    python -m pytest test_dt_on_quantized.py -q
"""
import argparse, sys
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dt_on_quantized as dq  # noqa: E402


@pytest.mark.parametrize("fmt,qtype", [("q8_0", "Q8_0"), ("q4_0", "Q4_0")])
def test_block_quantizers_match_gguf_py(fmt, qtype):
    gguf = pytest.importorskip("gguf")
    x = np.random.default_rng(0).standard_normal((6, 128)).astype(np.float32) * 0.07
    t = getattr(gguf.GGMLQuantizationType, qtype)
    ref = gguf.quants.dequantize(gguf.quants.quantize(x, t), t)
    codes, scales = dq.quantize(torch.from_numpy(x), fmt)
    mine = dq.dequantize(codes, scales, fmt, x.shape, torch.float32).numpy()
    assert np.array_equal(mine, ref), np.abs(mine - ref).max()


def test_quantization_error_is_ordered_and_zero_blocks_survive():
    w = torch.randn(8, 64)
    w[0, :32] = 0.0
    errs = {}
    for fmt in ("q8_0", "q4_0"):
        c, s = dq.quantize(w, fmt)
        d = dq.dequantize(c, s, fmt, w.shape, torch.float32)
        assert torch.equal(d[0, :32], torch.zeros(32))
        errs[fmt] = float((d - w).abs().max())
    assert errs["q8_0"] < errs["q4_0"]


def test_input_dimension_must_be_a_multiple_of_the_block():
    with pytest.raises(ValueError):
        dq.quantize(torch.randn(2, 40), "q8_0")


def _masked(fmt, seed=0):
    torch.manual_seed(seed)
    lin = nn.Linear(64, 16, bias=False)
    gen = torch.Generator().manual_seed(1)
    m = dq.dtmask.MaskedLinear(lin, 100.0, 1000.0, 10, gen)
    return lin.weight.detach().clone(), dq.to_packed(m, fmt)


@pytest.mark.parametrize("fmt", ["q8_0", "q4_0"])
def test_packed_layer_applies_the_quantized_weight_and_the_hard_mask(fmt):
    w, m = _masked(fmt)
    c, s = dq.quantize(w, fmt)
    deq = dq.dequantize(c, s, fmt, w.shape, torch.float32)
    assert torch.equal(m.base_weight, deq)
    m.gate.data = torch.randn_like(m.gate) * 0.01              # about half the weights deleted
    m.eval()
    x = torch.randn(3, 64)
    assert torch.allclose(m(x), x @ (deq * (m.gate > 0).float()).T, atol=1e-6)
    assert "weight" not in m._parameters and m.packed_bytes() < w.numel() * 2


def test_packed_storage_matches_the_llama_cpp_block_sizes():
    w, q8 = _masked("q8_0"); _, q4 = _masked("q4_0")
    blocks = w.numel() // 32
    assert q8.packed_bytes() == blocks * 34 and q4.packed_bytes() == blocks * 18


def test_bake_and_regulariser_work_on_packed_layers():
    _, m = _masked("q4_0")
    net = nn.Sequential(m)
    assert float(dq.dtmask.regulariser(net)) > 0
    keep = (m.gate > 0)
    masks = dq.dtmask.bake(net)
    assert isinstance(net[0], nn.Linear) and torch.equal(masks["0.weight"], keep.cpu())


def test_memory_accounting_on_a_toy_model():
    tr = pytest.importorskip("transformers")
    cfg = tr.Qwen3Config(vocab_size=100, hidden_size=64, intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                         num_key_value_heads=2, head_dim=16)
    model = tr.Qwen3ForCausalLM(cfg)
    r = dq.memory_accounting(model, ("gate_proj",), "q4_0")
    assert r["masked_weights"] == 2 * 64 * 128
    assert r["dt_state_bytes"] == r["masked_weights"] * 16
    assert r["saved_by_format_bytes"] == round(r["decoder_linear_weights"] * (2 - 18 / 32))


def test_paired_bootstrap():
    a = [1.0, 2.0, 3.0, 4.0]
    same = dq.paired_bootstrap(a, a)
    assert same["mean_diff"] == 0 and same["ci95"] == [0.0, 0.0]
    assert dq.paired_bootstrap([x + 0.5 for x in a], a)["ci95"] == [0.5, 0.5]


@pytest.fixture()
def toy(tmp_path):
    tr = pytest.importorskip("transformers")
    torch.manual_seed(0)
    cfg = tr.Qwen3Config(vocab_size=64, hidden_size=64, intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                         num_key_value_heads=2, head_dim=16, tie_word_embeddings=True)
    tr.Qwen3ForCausalLM(cfg).save_pretrained(tmp_path / "toy")
    rng = np.random.default_rng(0)
    win = lambda n: [rng.integers(0, 64, 16).tolist() for _ in range(n)]
    args = argparse.Namespace(model=str(tmp_path / "toy"), revision=None, dtype="float32", targets="gate", seed=1, steps=4,
                              batch=2, micro=1, lr=2e-3, eta=1 / 64, prior_strength=3.0, lam=1e-5, alpha_start=100.0,
                              alpha_end=1000.0, then=["q8_0", "q4_0"])
    return args, {"train": win(8), "calib": win(2), "test": win(6)}


def test_every_arm_runs_end_to_end(toy):
    args, windows = toy
    dev = torch.device("cpu")
    out = {a: dq.run_arm(a, args, windows, dev) for a in ("base", "base_q8_0", "base_q4_0", "dt", "dt_q8_0", "dt_q4_0")}
    for r in out.values():
        assert np.isfinite(r["test_nll_mean"]) and r["test_windows"] == 6 and len(r["per_window_nll"]) == 6
    assert set(out["dt"]["then"]) == {"q8_0", "q4_0"} and "then" not in out["dt_q8_0"]
    assert all(v["memory"]["dt_state_bytes"] == 0 for v in out["dt"]["then"].values())   # baked and quantized: nothing to train
    for q in ("dt_q8_0", "dt_q4_0"):
        assert out[q]["packed_bytes_targeted"] < out[q]["bf16_bytes_targeted"] and out[q]["masked_layers"] == 2
        assert 0.0 <= out[q]["deletion_final"] <= 1.0
    assert out["dt_q4_0"]["packed_bytes_targeted"] < out["dt_q8_0"]["packed_bytes_targeted"]
    assert out["dt"]["memory"]["format"] == "float32" and out["dt_q4_0"]["memory"]["format"] == "q4_0"


def test_dt_arm_is_deterministic(toy):
    args, windows = toy
    a = dq.run_arm("dt_q8_0", args, windows, torch.device("cpu"))
    b = dq.run_arm("dt_q8_0", args, windows, torch.device("cpu"))
    assert a["per_window_nll"] == b["per_window_nll"] and a["deleted"] == b["deleted"]


def test_dt_then_arm_names_are_rejected_by_run_arm(toy):
    args, windows = toy
    with pytest.raises(AssertionError):
        dq.run_arm("dt_then_q8_0", args, windows, torch.device("cpu"))


def test_the_prior_marks_weights_on_quantized_arms_at_the_real_eta(toy):
    args, windows = toy
    args.eta = 1 / 2048                                          # k = 4 of 8192 per layer; Q8_0 and Q4_0 zero far more than that
    dev = torch.device("cpu")
    res = {a: dq.run_arm(a, args, windows, dev) for a in ("dt", "dt_q8_0", "dt_q4_0")}
    for a, r in res.items():
        assert r["wanda_prior"]["prior_deleted"] > 0, (a, r["wanda_prior"])
    assert res["dt_q4_0"]["weights_zero_before_prior"] > res["dt_q8_0"]["weights_zero_before_prior"] > 0


def test_zeroed_weights_do_not_set_the_threshold():
    w = torch.randn(4, 64)
    w[0, :32] = 0.0                                              # a whole block already zero
    lin = nn.Linear(64, 4, bias=False); lin.weight.data.copy_(w)
    layer = dq.dtmask.MaskedLinear(lin, 100.0, 1000.0, 10, torch.Generator().manual_seed(0))
    scores = {"x": layer.base_weight.detach().abs() * torch.ones(64)}
    z = layer.base_weight == 0
    scores["x"] = torch.where(z, torch.full_like(scores["x"], float("inf")), scores["x"])
    net = nn.Sequential(); net.add_module("x", layer)
    info = dq.dtmask.apply_wanda_prior(net, scores, eta=8 / 256)       # k = 8; the official rule marks scores strictly below the 8th: 7
    assert info["prior_deleted"] == 7
    assert int((layer.gate.detach()[0, :32] > 0).sum()) == 32          # the zeroed block was never marked for deletion


def test_quantized_arms_refuse_a_half_precision_dtype(toy):
    args, windows = toy
    args.dtype = "bfloat16"
    with pytest.raises(ValueError):
        dq.run_arm("dt_q8_0", args, windows, torch.device("cpu"))
    with pytest.raises(ValueError):
        dq.run_arm("base_q4_0", args, windows, torch.device("cpu"))


def test_memory_accounting_counts_dt_state_only_for_dt_arms(toy):
    args, windows = toy
    base = dq.run_arm("base", args, windows, torch.device("cpu"))["memory"]
    dt = dq.run_arm("dt", args, windows, torch.device("cpu"))["memory"]
    assert base["dt_state_bytes"] == 0 and dt["dt_state_bytes"] == dt["masked_weights"] * 16
    assert dt["weights_bytes"] == dt["decoder_linear_weights"] * 4           # float32 arm: 4 bytes, not bf16's 2
