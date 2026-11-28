"""Tests for kv_llamacpp.py: cache-choice parsing, the bytes-per-token formula, and the log parsers on lines copied from
llama.cpp b11669 (620d222) runs on the dry run 2 stand-in. CPU only, no llama.cpp needed.

    python -m pytest test_kv_llamacpp.py -q
"""
import pytest

from kv_llamacpp import (TYPE_BYTES, bits, env_for, kv_bytes_per_token, parse_choice, parse_kld_log,
                         parse_memory_log, pooled)

# stderr of `llama-completion -c 8192 -ctk q8_0 -ctv q8_0 -fa on -lv 4` + `/usr/bin/time -l`, trimmed
MEM_LOG = """\
0.00.071.225 I print_info: n_ctx_train           = 2048
0.00.071.226 I print_info: n_embd                = 512
0.00.071.226 I print_info: n_layer               = 8
0.00.071.226 I print_info: n_head_kv             = 2
0.00.071.227 I print_info: n_embd_head_k         = 64
0.00.071.227 I print_info: n_embd_head_v         = 64
0.00.071.240 I print_info: n_vocab               = 131072
0.00.180.104 I load_tensors: offloaded 9/9 layers to GPU
0.00.180.105 I load_tensors:   CPU_Mapped model buffer size =    68.00 MiB
0.00.180.105 I load_tensors:  MTL0_Mapped model buffer size =    68.00 MiB
0.00.180.106 I load_tensors:  MTL0_Mapped model buffer size =   168.16 MiB
0.00.199.871 I llama_context: flash_attn            = enabled
0.00.201.322 I llama_kv_cache:       MTL0 KV buffer size =    17.00 MiB
0.00.201.330 I llama_kv_cache: size =   17.00 MiB (  8192 cells,   8 layers,  1/1 seqs), K (q8_0):    8.50 MiB, V (q8_0):    8.50 MiB
0.00.201.331 I llama_kv_cache: n_rot_k = 64, n_embd_head_k_all = 64
0.00.201.331 I llama_kv_cache: n_rot_v = 64, n_embd_head_k_all = 64
0.00.204.002 I sched_reserve:       MTL0 compute buffer size =   268.05 MiB
0.00.204.003 I sched_reserve:        CPU compute buffer size =    12.05 MiB
0.00.204.004 I sched_reserve: graph: nodes = 539, splits = 2, input objects = 4, input tensors = 11
            481787904  maximum resident set size
            103941344  peak memory footprint
"""

KLD_LOG = """\
perplexity: computing over 2 chunks, n_ctx=8192, batch_size=8192, n_seq=1
Mean PPL(Q)                   :  10.123456 ±   0.123456
Mean PPL(base)                :  10.100000 ±   0.120000
Mean ln(PPL(Q)/PPL(base))     :   0.002320 ±   0.000400
====== KL divergence statistics ======
Mean    KLD:   0.004321 ±   0.000123
Maximum KLD:   1.234567
99.0%   KLD:   0.045678
Median  KLD:   0.001234
====== Token probability statistics ======
RMS Δp    :  1.234 ± 0.045 %
Same top p: 97.123 ± 0.210 %
"""


def test_parse_choice():
    assert parse_choice('f16') == ('f16', 'f16', True)
    assert parse_choice('q8_0/q4_0') == ('q8_0', 'q4_0', True)
    assert parse_choice('q4_0+norot') == ('q4_0', 'q4_0', False)
    assert parse_choice('q8_0/q4_0+norot') == ('q8_0', 'q4_0', False)
    with pytest.raises(ValueError):
        parse_choice('q3_k')


def test_bits_per_element():
    assert [bits(t) for t in ('f16', 'bf16', 'q8_0', 'q5_1', 'q5_0', 'q4_1', 'q4_0', 'iq4_nl')] == \
        [16, 16, 8.5, 6, 5.5, 5, 4.5, 4.5]


def test_formula_matches_llama_cpp_on_the_standin():
    # dry run 2 shape: 8 layers, 2 KV heads, head dim 64; llama.cpp reported these MiB at 8,192 cells
    measured = {'f16': 32.0, 'q8_0': 17.0, 'q4_0': 9.0, 'iq4_nl': 9.0, ('q8_0', 'q4_0'): 13.0}
    for key, mib in measured.items():
        k, v = key if isinstance(key, tuple) else (key, key)
        assert kv_bytes_per_token(8, 2, 64, 64, k, v) * 8192 / 2**20 == mib


def test_formula_rejects_a_head_dim_off_the_block():
    with pytest.raises(ValueError):
        kv_bytes_per_token(8, 2, 48, 48, 'q8_0', 'q8_0')
    assert kv_bytes_per_token(1, 1, 48, 48, 'f16', 'f16') == 192


def test_parse_memory_log():
    p = parse_memory_log(MEM_LOG)
    assert (p['kv_mib'], p['cells'], p['layers'], p['k_type'], p['k_mib'], p['v_type'], p['v_mib']) == \
        (17.0, 8192, 8, 'q8_0', 8.5, 'q8_0', 8.5)
    assert p['kv_buffers'] == {'MTL0': 17.0}
    assert p['compute_buffers'] == {'MTL0': 268.05, 'CPU': 12.05}
    assert p['model_buffers'] == {'CPU_Mapped': 68.0, 'MTL0_Mapped': 236.16}
    assert (p['fa'], p['rot_k'], p['rot_v'], p['rot_disabled_logged']) == ('enabled', 64, 64, False)
    assert p['offloaded'] == '9/9'
    assert (p['graph_nodes'], p['graph_splits']) == (539, 2)
    assert (p['peak_footprint_bytes'], p['max_rss_bytes']) == (103941344, 481787904)
    assert p['hparams'] == {'n_ctx_train': 2048, 'n_embd': 512, 'n_layer': 8, 'n_head_kv': 2,
                            'n_embd_head_k': 64, 'n_embd_head_v': 64, 'n_vocab': 131072}


def test_parse_memory_log_sees_the_rotation_switch():
    log = MEM_LOG.replace('n_rot_k = 64', 'n_rot_k = 0').replace('n_rot_v = 64', 'n_rot_v = 0') + \
        '0.00.2 W llama_kv_cache: attention rotation force disabled (LLAMA_ATTN_ROT_DISABLE)\n'
    p = parse_memory_log(log)
    assert (p['rot_k'], p['rot_v'], p['rot_disabled_logged']) == (0, 0, True)


def test_parse_memory_log_on_a_failed_run():
    p = parse_memory_log('error: failed to load model\n')
    assert 'kv_mib' not in p and p['compute_buffers'] == {} and p['peak_footprint_bytes'] is None


def test_parse_kld_log():
    p = parse_kld_log(KLD_LOG)
    assert (p['chunks'], p['n_ctx']) == (2, 8192)
    assert (p['kld'], p['kld_se']) == (0.004321, 0.000123)
    assert (p['same_top'], p['same_top_se']) == (97.123, 0.21)
    assert (p['ln_ratio'], p['ln_ratio_se']) == (0.00232, 0.0004)
    assert (p['ppl_q'], p['ppl_base']) == (10.123456, 10.1)
    assert (p['kld_max'], p['kld_p99'], p['kld_median']) == (1.234567, 0.045678, 0.001234)
    assert (p['rms_dp'], p['rms_dp_se']) == (1.234, 0.045)


def test_env_for_sets_and_clears_the_rotation_switch(monkeypatch):
    monkeypatch.setenv('LLAMA_ATTN_ROT_DISABLE', '1')
    assert 'LLAMA_ATTN_ROT_DISABLE' not in env_for(True)
    assert env_for(False)['LLAMA_ATTN_ROT_DISABLE'] == '1'


def test_pooled_means_over_packs():
    runs = [{'model': 'm', 'choice': 'q4_0', 'pack': p, 'kld': k, 'kld_se': 0.003, 'same_top': t, 'ln_ratio': 0.01}
            for p, k, t in (('a', 0.01, 98.0), ('b', 0.03, 96.0))]
    p = pooled(runs, 'm', 'q4_0')
    assert p['packs'] == 2 and p['kld'] == pytest.approx(0.02) and p['same_top'] == pytest.approx(97.0)
    assert p['kld_se'] == pytest.approx((2 * 0.003 ** 2) ** 0.5 / 2)
    assert p['worst_pack'] == 'b'
    assert pooled(runs, 'm', 'f16') is None


def test_every_type_has_whole_bytes_per_block():
    for t, (blk, nb) in TYPE_BYTES.items():
        assert blk in (1, 32) and nb > 0


def test_vllm_slot_sizes_match_848():
    from kv_llamacpp import vllm_bits, vllm_mib_per_1k
    # #848: 4.375 bits on the compressed layers for 4bit_nc at head dim 64; 4.1875 at head dim 128, which is where
    # TurboQuantConfig's docstring gets its 3.8x (16 / 4.1875)
    assert vllm_bits(4, 4, 64) == 4.375 and vllm_bits(4, 4, 128) == 4.1875
    # dry run 2 shape: bf16 4 MiB per 1k tokens, fp8 2, and 4bit_nc keeps 4 of 8 layers bf16 -> 1.57x bf16's tokens
    assert vllm_mib_per_1k(8, 2, 64, 16) == 4.0 and vllm_mib_per_1k(8, 2, 64, 8) == 2.0
    assert round(4.0 / vllm_mib_per_1k(8, 2, 64, vllm_bits(4, 4, 64)), 2) == 1.57


def test_formula_with_different_k_and_v_head_dims():
    # MLA-style caches can have head_k != head_v; each side uses its own dim
    assert kv_bytes_per_token(2, 1, 192, 128, 'f16', 'f16') == 2 * (192 * 2 + 128 * 2)
    assert kv_bytes_per_token(1, 1, 64, 128, 'q8_0', 'q4_0') == 64 // 32 * 34 + 128 // 32 * 18


# ------------------------------------------------------------------ report (every README table comes from it)
def _mem_rows(n_layer, n_kv, hd, splits_cpu, kv_off=None):
    from kv_llamacpp import parse_choice
    rows = []
    for ctx in (8192, 32768, 131072):
        for c in ('f16', 'bf16', 'q8_0', 'q5_1', 'q5_0', 'q4_1', 'q4_0', 'iq4_nl', 'q8_0/q4_0', 'q8_0/q5_0'):
            k, v, _ = parse_choice(c)
            bpt = kv_bytes_per_token(n_layer, n_kv, hd, hd, k, v)
            kv = bpt * ctx / 2**20 + (kv_off if (kv_off and c == 'q5_0') else 0)
            rows.append({'ctx': ctx, 'choice': c, 'k': k, 'v': v, 'kv_mib': kv, 'formula_kv_mib': bpt * ctx / 2**20,
                         'kv_mib_per_1k': kv / ctx * 1024, 'kv_bytes_per_token': bpt,
                         'graph_splits': splits_cpu if c in ('iq4_nl', 'q8_0/q4_0', 'q8_0/q5_0') else 2,
                         'compute_buffers': {'MTL0': 268.0, 'CPU': 12.0}, 'model_buffers': {'MTL0_Mapped': 1000.0},
                         'peak_footprint_bytes': 100 * 2**20,
                         'hparams': {'n_layer': n_layer, 'n_head_kv': n_kv, 'n_embd_head_k': hd, 'n_embd_head_v': hd}})
    return {'runs': rows}


def _report(tmp_path, mem2, mem1, quality=None, speed=None, bw=None):
    import json, io, contextlib, types
    from kv_llamacpp import run_report
    for name, d in (('memory_t2.json', mem2), ('memory_llama1b.json', mem1), ('quality_llama1b_ctx8192.json', quality),
                    ('speed_kv.json', speed), ('bandwidth_mps.json', bw)):
        if d is not None: (tmp_path / name).write_text(json.dumps(d))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): run_report(types.SimpleNamespace(results=str(tmp_path)))
    return buf.getvalue()


def test_report_memory_table(tmp_path):
    # a CPU fallback on only one of the two models must still say CPU; a KV size off the formula must say NO
    out = _report(tmp_path, _mem_rows(8, 2, 64, 2), _mem_rows(16, 8, 64, 34, kv_off=0.5))
    rows = {l.split(' | ')[0].strip('| '): l for l in out.splitlines() if l.startswith('| ')}
    assert '| GPU |' in rows['q8_0'] and 'CPU (2 / 34 graph splits, not 2)' in rows['iq4_nl']
    assert '| NO |' in rows['q5_0'] and '| yes |' in rows['q4_0']
    assert '4.000 MiB | 32.000 MiB' in rows['f16'] and '2.125 MiB | 17.000 MiB' in rows['q8_0']
    assert rows['q5_0'].endswith('| Llama-1B |') and rows['q4_0'].endswith('| yes |') and rows['bf16'].endswith('|  |')


def test_report_quality_and_speed(tmp_path):
    import math
    mem2, mem1 = _mem_rows(8, 2, 64, 18), _mem_rows(16, 8, 64, 34)
    q = {'runs': [{'model': 'm', 'choice': c, 'pack': 'a', 'kld': 0.07, 'kld_se': 0.001, 'same_top': 88.0, 'ln_ratio': 0.0693}
                  for c in ('bf16', 'q8_0', 'q4_0+norot')]}
    sp = {'runs': [{'model': 'llama-x', 'choice': c, 'n_prompt': npr, 'n_gen': ng, 'n_depth': d, 'avg_ts': 50.0, 'stdev_ts': 1.0}
                   for c in ('f16', 'q8_0') for npr, ng in ((512, 0), (0, 8192)) for d in (0, 8192)]}
    out = _report(tmp_path, mem2, mem1, q, sp, {'read_GBps_median': 100.0, 'read_GBps': [90.0, 100.0, 110.0]})
    assert any(l.startswith('| bf16 | n/a |') for l in out.splitlines())
    assert any(l.startswith('| q8_0 | on |') for l in out.splitlines())
    assert any(l.startswith('| q4_0 | off |') for l in out.splitlines())
    assert f'{100 * (math.exp(0.0693) - 1):+.2f}%' in out          # perplexity change is exp(ln ratio) - 1
    # bytes per token: weights + cache bytes per token x (depth + n_gen / 2); effective rate = tok/s x that
    per_tok = 1000 * 2**20 + kv_bytes_per_token(16, 8, 64, 64, 'f16', 'f16') * (8192 + 8192 / 2)
    assert f' {per_tok / 1e9:.3f} GB | {50.0 * per_tok / 1e9:.1f} GB/s |' in out
