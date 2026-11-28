"""Tests for parts_llamacpp.py and router_emul.py. CPU, seconds.

    python -m pytest test_parts.py -q          # needs torch; the gguf-py comparison needs the gguf package
"""
import numpy as np
import pytest
import torch

from parts_llamacpp import VARIANTS, parse_kld_log, part_of
from router_emul import q4_0, q8_0


def test_part_of_names_every_llama_cpp_tensor_kind():
    assert part_of('token_embd.weight') == 'embedding'
    assert part_of('output.weight') == 'output'
    assert part_of('output_norm.weight') == 'norms and other'
    assert part_of('blk.3.ffn_gate_inp.weight') == 'router'
    assert part_of('blk.3.ffn_up_exps.weight') == 'experts'
    assert part_of('blk.3.ffn_down_shexp.weight') == 'shared expert'
    assert part_of('blk.0.attn_q.weight') == 'attention'
    assert part_of('blk.0.attn_output.weight') == 'attention'
    assert part_of('blk.0.attn_norm.weight') == 'norms and other'
    assert part_of('blk.0.ffn_up.weight') == 'dense ffn'


def test_variants_change_one_thing_each():
    assert VARIANTS['g12'] == ('Q4_K_M', ['--output-tensor-type', 'q8_0'])
    for name in ('embd-q8_0', 'attn-q8_0'):
        ftype, args = VARIANTS[name]
        assert ftype == 'Q4_K_M' and args[:2] == ['--output-tensor-type', 'q8_0'] and len(args) == 4


def test_parse_kld_log():
    log = ('Mean ln(PPL(Q)/PPL(base))     :   0.056935 ±   0.004330\nMean    KLD:   0.060502 ±   0.001529\n'
           '99.0%   KLD:   0.512000\nMaximum KLD:   3.250000\nSame top p: 86.789 ± 0.374 %\n')
    p = parse_kld_log(log)
    assert (p['kld'], p['kld_se'], p['same_top'], p['ln_ratio'], p['kld_p99'], p['kld_max']) == \
        (0.060502, 0.001529, 86.789, 0.056935, 0.512, 3.25)


def test_quantizers_keep_shape_and_zero_blocks():
    w = torch.zeros(4, 64)
    assert torch.equal(q8_0(w), w) and torch.equal(q4_0(w), w)
    w = torch.randn(8, 128)
    assert q8_0(w).shape == w.shape and q4_0(w).shape == w.shape


def test_q8_0_error_is_small_and_q4_0_larger():
    torch.manual_seed(0)
    w = torch.randn(64, 2048)
    e8 = ((q8_0(w) - w).norm() / w.norm()).item()
    e4 = ((q4_0(w) - w).norm() / w.norm()).item()
    assert e8 < 0.01 < e4 < 0.15


def test_q4_0_uses_sixteen_levels_per_block():
    torch.manual_seed(1)
    w = torch.randn(1, 32)
    levels = torch.unique(torch.round(q4_0(w) / (q4_0(w).abs().max() / 8), decimals=3))
    assert len(levels) <= 16


@pytest.mark.parametrize('name,fn', [('Q8_0', q8_0), ('Q4_0', q4_0)])
def test_matches_gguf_py_reference(name, fn):
    gguf = pytest.importorskip('gguf')
    from gguf import quants
    rng = np.random.default_rng(0)
    x = (rng.standard_normal((16, 256)) * 0.05).astype(np.float32)
    qt = getattr(gguf.GGMLQuantizationType, name)
    ref = quants.dequantize(quants.quantize(x, qt), qt)
    ours = fn(torch.from_numpy(x)).numpy()
    np.testing.assert_allclose(ours, ref, rtol=0, atol=1e-7)


@pytest.mark.parametrize('name,fn', [('Q8_0', q8_0), ('Q4_0', q4_0)])
def test_matches_gguf_py_on_ties_and_bf16_values(name, fn):
    # real router weights are bf16 values, so exact halves and equal-magnitude extremes occur; build both on purpose
    gguf = pytest.importorskip('gguf')
    from gguf import quants
    qt = getattr(gguf.GGMLQuantizationType, name)
    rng = np.random.default_rng(1)
    x = torch.from_numpy(rng.standard_normal((64, 256)).astype(np.float32) * 0.02).to(torch.bfloat16).float().numpy()
    x[0, :32] = np.linspace(-1, 1, 32, dtype=np.float32); x[0, 5] = -1.0          # opposite-sign tie for the largest |x|
    x[1, :32] = 0.0; x[1, 0] = 127.0; x[1, 1] = 0.5; x[1, 2] = -1.5; x[1, 3] = 2.5  # halves of the Q8_0 step d = 1
    ref = quants.dequantize(quants.quantize(x, qt), qt)
    np.testing.assert_allclose(fn(torch.from_numpy(x)).numpy(), ref, rtol=0, atol=0)


GGUF_NAMES = ['token_embd.weight', 'output.weight', 'output_norm.weight', 'blk.0.attn_q.weight', 'blk.0.attn_k.weight',
              'blk.0.attn_v.weight', 'blk.0.attn_output.weight', 'blk.0.attn_norm.weight', 'blk.0.attn_q_norm.weight',
              'blk.0.ffn_gate_inp.weight', 'blk.0.ffn_gate_exps.weight', 'blk.0.ffn_up_exps.weight',
              'blk.0.ffn_down_exps.weight', 'blk.0.ffn_down_shexp.weight', 'blk.0.ffn_norm.weight']


def _regex(variant):
    import re
    args = VARIANTS[variant][1]
    pat = args[args.index('--tensor-type') + 1].split('=')[0]
    return {n for n in GGUF_NAMES if re.search(pat, n)}


def test_variant_regexes_hit_only_their_part():
    assert _regex('attn-q8_0') == {'blk.0.attn_q.weight', 'blk.0.attn_k.weight', 'blk.0.attn_v.weight',
                                   'blk.0.attn_output.weight'}
    assert _regex('experts-q4') == {'blk.0.ffn_gate_exps.weight', 'blk.0.ffn_up_exps.weight', 'blk.0.ffn_down_exps.weight'}
    assert VARIANTS['experts-q4'][0] == 'Q8_0' and VARIANTS['q8_0'][0] == 'Q8_0' and VARIANTS['llama-default'] == ('Q4_K_M', [])
    assert VARIANTS['pure-q4_K'] == ('Q4_K', ['--pure'])
    assert VARIANTS['out-q4_K'][1] == ['--output-tensor-type', 'q4_K'] and VARIANTS['out-bf16'][1] == ['--output-tensor-type', 'bf16']
    assert VARIANTS['embd-q8_0'][1][2:] == ['--token-embedding-type', 'q8_0']


def test_part_of_more_names():
    assert part_of('blk.0.attn_qkv.weight') == 'attention'
    assert part_of('blk.0.ffn_norm.weight') == 'norms and other'
    assert part_of('blk.0.attn_q_norm.weight') == 'norms and other'


def test_router_metrics():
    from router_emul import compare
    base_lp = torch.log_softmax(torch.tensor([[2.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 1.0, 3.0]]), -1)
    lp = torch.log_softmax(torch.tensor([[2.0, 0.0, -1.0], [1.0, 0.0, 0.0], [1.0, 1.0, 3.0]]), -1)
    sel_b = [torch.tensor([[0, 1], [0, 2], [1, 3]]), torch.tensor([[0, 1], [0, 1], [0, 1]])]
    sel_q = [torch.tensor([[0, 1], [0, 3], [1, 3]]), torch.tensor([[2, 3], [0, 1], [0, 1]])]
    r = compare(base_lp, sel_b, lp, sel_q, [5, 0, 1], k=2)
    assert r['same_topk_set_by_layer'] == pytest.approx([2 / 3, 2 / 3])
    assert r['same_topk_set_layer0'] == pytest.approx(2 / 3) and r['same_topk_set_later'] == pytest.approx(2 / 3)
    assert r['experts_changed'] == pytest.approx((1 / 3 + 2 / 3) / 2)        # layer 0: one expert in one row; layer 1: two
    kl_row = (base_lp[1].exp() * (base_lp[1] - lp[1])).sum().item()        # KL(original || quantized), row 1 only differs
    assert r['kl'] == pytest.approx(kl_row / 3) and r['same_top1'] == pytest.approx(2 / 3)
    # targets ids[1:] = 0, 1 are scored at rows 0 and 1; only row 1 changed, by log-prob 1 -> 0 of the target
    assert r['dnll'] == pytest.approx(((-lp[1, 1]) - (-base_lp[1, 1])).item() / 2)
    assert r['dnll'] == pytest.approx(0.5)


def test_fp32_router_matches_the_module_and_uses_fp32():
    from router_emul import fp32_router
    torch.manual_seed(0)

    class TopKRouter(torch.nn.Module):            # the transformers 5.x OlmoeTopKRouter, in bf16
        def __init__(self):
            super().__init__(); self.top_k, self.num_experts, self.norm_topk_prob, self.hidden_dim = 2, 8, False, 64
            self.weight = torch.nn.Parameter(torch.randn(8, 64).to(torch.bfloat16))

        def forward(self, h):
            h = h.reshape(-1, self.hidden_dim); logits = torch.nn.functional.linear(h, self.weight)
            probs = torch.softmax(logits, dtype=torch.float, dim=-1); v, i = torch.topk(probs, self.top_k, dim=-1)
            return logits, v.to(logits.dtype), i

    m = TopKRouter(); h = torch.randn(16, 64).to(torch.bfloat16)
    w = fp32_router(m)
    assert w.dtype == torch.float32 and torch.equal(w, m.weight.float())
    logits, v, i = m(h)
    assert logits.dtype == torch.float32 and v.dtype == torch.bfloat16
    assert torch.equal(logits, torch.nn.functional.linear(h.float(), w))      # computed in fp32, not bf16 then cast
    m.norm_topk_prob = True
    _, v2, _ = m(h)
    assert torch.allclose(v2.float().sum(-1), torch.ones(16), atol=1e-2)     # renormalised over the chosen experts
    exp = torch.topk(torch.softmax(h.float() @ w.T, -1), 2, dim=-1).indices
    assert torch.equal(i, exp)
    m.w32.copy_(q8_0(w)); _, _, i2 = m(h)             # the rounded weights reach the forward, in fp32
    assert torch.equal(i2, torch.topk(torch.softmax(h.float() @ q8_0(w).T, -1), 2, dim=-1).indices)


def test_router_rewrite_in_place(tmp_path):
    gguf = pytest.importorskip('gguf')
    import json, types
    from parts_llamacpp import run_router
    src = tmp_path / 'm-bf16.gguf'
    wr = gguf.GGUFWriter(str(src), 'llama')
    rng = np.random.default_rng(2)
    gate = (rng.standard_normal((4, 64)) * 0.1).astype(np.float32); other = rng.standard_normal((8, 64)).astype(np.float32)
    exps = rng.standard_normal((2, 4, 64)).astype(np.float32)
    wr.add_tensor('blk.0.ffn_gate_inp.weight', gate); wr.add_tensor('blk.0.attn_q.weight', other)
    wr.add_tensor('blk.0.ffn_gate_exps.weight', exps)
    wr.write_header_to_file(); wr.write_kv_data_to_file(); wr.write_tensors_to_file(); wr.close()
    (tmp_path / 'variants.json').write_text(json.dumps({'variants': []}))
    run_router(types.SimpleNamespace(work=tmp_path, from_=[f'bf16={src}'], formats=['q4_0']))
    out = gguf.GGUFReader(str(tmp_path / 'm-router-q4_0.gguf'))
    t = {x.name: np.array(x.data) for x in out.tensors}
    np.testing.assert_array_equal(t['blk.0.ffn_gate_inp.weight'], q4_0(torch.from_numpy(gate)).numpy())
    np.testing.assert_array_equal(t['blk.0.attn_q.weight'], other)
    np.testing.assert_array_equal(t['blk.0.ffn_gate_exps.weight'], exps)               # not a router: untouched
    np.testing.assert_array_equal(np.array(gguf.GGUFReader(str(src)).tensors[0].data), gate)   # the source is untouched
    v = json.loads((tmp_path / 'variants.json').read_text())['variants'][0]
    assert v['variant'] == 'router-q4_0' and v['routers_rounded'] == 1


def test_router_rewrite_refuses_a_router_not_stored_as_f32(tmp_path):
    gguf = pytest.importorskip('gguf')
    import json, types
    from parts_llamacpp import run_router
    src = tmp_path / 'm-bf16.gguf'
    wr = gguf.GGUFWriter(str(src), 'llama')
    wr.add_tensor('blk.0.ffn_gate_inp.weight', np.zeros((4, 64), dtype=np.float16))
    wr.write_header_to_file(); wr.write_kv_data_to_file(); wr.write_tensors_to_file(); wr.close()
    (tmp_path / 'variants.json').write_text(json.dumps({'variants': []}))
    with pytest.raises(SystemExit):
        run_router(types.SimpleNamespace(work=tmp_path, from_=[f'bf16={src}'], formats=['q8_0']))
