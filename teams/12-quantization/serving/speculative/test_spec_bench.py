"""Tests for spec_bench.py: server arguments per mode, the summary arithmetic and the report table. CPU, no llama.cpp.

    python -m pytest test_spec_bench.py -q
"""
import contextlib, io, json

import pytest

from spec_bench import mode_args, mode_label, report, summarize


def test_mode_args():
    assert mode_args('base', 99) == []
    a = mode_args('draft:/m/d.gguf:4', 99)
    assert a[:4] == ['-md', '/m/d.gguf', '-ngld', '99']
    # b11669 only drafts when a draft type is requested; -md alone loads the model and never drafts
    assert a[a.index('--spec-type') + 1] == 'draft-simple' and a[a.index('--spec-draft-n-max') + 1] == '4'
    assert mode_args('draft:/m/d.gguf', 99)[-1] == '8'
    assert mode_args('ngram:ngram-mod', 99) == ['--spec-type', 'ngram-mod']
    assert mode_args('ngram:ngram-mod:32', 99) == ['--spec-type', 'ngram-mod', '--spec-ngram-mod-n-max', '32']
    with pytest.raises(ValueError):
        mode_args('eagle:x', 99)
    with pytest.raises(ValueError):                    # a draft length for another n-gram type would be ignored silently
        mode_args('ngram:ngram-simple:16', 99)


def test_mode_label():
    assert mode_label('draft:/a/b/llama-1b-Q8_0.gguf:4') == 'draft llama-1b-Q8_0 n4'
    assert mode_label('draft:/a/b/llama-1b-Q8_0.gguf') == 'draft llama-1b-Q8_0 n8'
    assert mode_label('ngram:ngram-mod') == 'ngram:ngram-mod'


def _res():
    run = lambda mode, pid, cat, n, tps, dn=None, da=None, txt='a': {
        'target': 't', 'mode': mode, 'id': pid, 'category': cat, 'predicted_n': n, 'predicted_per_second': tps,
        'draft_n': dn, 'draft_n_accepted': da, 'text_sha256': txt}
    runs = [run('base', 'p1', 'chat', 100, 50.0), run('base', 'p2', 'code', 100, 25.0, txt='b'),
            run('fast', 'p1', 'chat', 100, 100.0, 80, 60), run('fast', 'p2', 'code', 100, 50.0, 20, 10, txt='x')]
    return {'runs': runs, 'files': {'t': {'gguf': 't.gguf'}}, 'n_prompts': 2, 'n_predict': 100}


def test_summarize_weights_by_time_not_by_prompt():
    res = _res()
    with contextlib.redirect_stdout(io.StringIO()): summarize(res)
    b, f = res['summary']['t | base'], res['summary']['t | fast']
    # 200 tokens in 2 + 4 seconds = 33.3 tok/s, not the mean of 50 and 25
    assert b['tok_per_s'] == pytest.approx(200 / 6) and f['tok_per_s'] == pytest.approx(200 / 3)
    assert f['speedup_vs_base'] == pytest.approx(2.0)
    assert f['acceptance'] == pytest.approx(70 / 100) and b['acceptance'] is None
    assert f['same_text_as_base'] == '1/2' and b['same_text_as_base'] == '2/2'
    assert f['tok_per_s_by_category'] == {'chat': 100.0, 'code': 50.0}
    # a category's speed is its tokens over its time, not the mean of per-prompt speeds
    res['runs'].append({'target': 't', 'mode': 'fast', 'id': 'p3', 'category': 'chat', 'predicted_n': 300,
                        'predicted_per_second': 300.0, 'draft_n': 0, 'draft_n_accepted': 0, 'text_sha256': 'a'})
    with contextlib.redirect_stdout(io.StringIO()): summarize(res)
    assert res['summary']['t | fast']['tok_per_s_by_category']['chat'] == pytest.approx(400 / 2)


def test_report_table(tmp_path):
    p = tmp_path / 'r.json'; p.write_text(json.dumps(_res()))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): report(type('A', (), {'files': [str(p)]}))
    out = buf.getvalue()
    assert '| fast | 66.7 (2.00×) | 100.0 (2.00×) | 50.0 (2.00×) | 70% | 1/2 |' in out
    assert '| base | 33.3 | 50.0 | 25.0 |  |  |' in out          # base is not compared with itself


def test_parse_buffers_keeps_target_then_draft():
    from spec_bench import parse_buffers
    log = ('I load_tensors:   CPU_Mapped model buffer size =   399.23 MiB\n'
           'I load_tensors:  MTL0_Mapped model buffer size =  3264.94 MiB\n'
           'I llama_kv_cache:       MTL0 KV buffer size =   896.00 MiB\n'
           'I sched_reserve:       MTL0 compute buffer size =   256.50 MiB\n'
           'I common_speculative_init_result: loading draft model\n'
           'I load_tensors:  MTL0_Mapped model buffer size =  1252.41 MiB\n'
           'I llama_kv_cache:       MTL0 KV buffer size =   256.00 MiB\n')
    b = parse_buffers(log)
    assert [x['kind'] for x in b] == ['model', 'model', 'KV', 'compute', 'model', 'KV']
    assert sum(x['mib'] for x in b) == 399.23 + 3264.94 + 896 + 256.5 + 1252.41 + 256


def test_memory_report_counts_each_gguf_once(tmp_path):
    mem = {'ctx': 8192, 'runs': [
        {'target': 't', 'mode': 'base', 'gguf_bytes': {'t.gguf': 1000 * 2**20},
         'buffers': [{'kind': 'model', 'device': 'CPU_Mapped', 'mib': 200.0}, {'kind': 'model', 'device': 'MTL0_Mapped', 'mib': 1000.0},
                     {'kind': 'KV', 'device': 'MTL0', 'mib': 100.0}, {'kind': 'compute', 'device': 'MTL0', 'mib': 10.0}]},
        {'target': 't', 'mode': 'draft d n8', 'gguf_bytes': {'t.gguf': 1000 * 2**20, 'd.gguf': 300 * 2**20},
         'buffers': [{'kind': 'model', 'device': 'MTL0_Mapped', 'mib': 1300.0}, {'kind': 'KV', 'device': 'MTL0', 'mib': 130.0},
                     {'kind': 'compute', 'device': 'MTL0', 'mib': 20.0}]}]}
    p = tmp_path / 'm.json'; p.write_text(json.dumps(mem))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): report(type('A', (), {'files': [str(p)]}))
    out = buf.getvalue()
    assert '| t | base | 1,000 | 100 | 10 | 1,110 |  |' in out          # the CPU_Mapped copy of the embedding is not added
    assert '| t | draft d n8 | 1,300 | 130 | 20 | 1,450 | 340 |' in out
