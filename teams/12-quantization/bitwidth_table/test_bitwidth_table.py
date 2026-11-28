#!/usr/bin/env python3
"""Tests for measure_mac.py and build_table.py, with a fake llama-bench (no llama.cpp needed):  python test_bitwidth_table.py"""
import argparse, csv, json, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_table, measure_mac  # noqa: E402

LOG = """ggml_metal_device_init: recommendedMaxWorkingSetSize  = 10922.67 MB
print_info: file size   = 343.32 MiB (8.00 BPW)
load_tensors:  MTL0_Mapped model buffer size =   343.32 MiB
llama_context:        CPU  output buffer size =     0.50 MiB
llama_kv_cache:       MTL0 KV buffer size =   185.62 MiB
llama_kv_cache: size =  185.62 MiB (  8448 cells,  30 layers,  1/1 seqs), K (f16):   92.81 MiB, V (f16):   92.81 MiB
sched_reserve:       MTL0 compute buffer size =   108.77 MiB
sched_reserve:        CPU compute buffer size =    12.77 MiB
~llama_context:       MTL0 compute buffer size is 108.7656 MiB, matches expectation of 108.7656 MiB
"""


def bench_json(cmd):
    depth = int(cmd[cmd.index('-d') + 1]) if '-d' in cmd else 0
    base = dict(model_size=360_000_000, model_n_params=360_000_000, build_commit='620d222', n_depth=depth)
    if depth:
        return [dict(base, n_prompt=0, n_gen=16, avg_ts=90.04)]
    return [dict(base, n_prompt=512, n_gen=0, avg_ts=2000.0), dict(base, n_prompt=0, n_gen=128, avg_ts=150.26)]


class MeasureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)
        self.keep = subprocess.run
        self.calls = []

        def fake(cmd, **kw):
            self.calls.append(cmd)
            if cmd[0].endswith('llama-bench'):
                err = LOG if '-v' in cmd else 'ggml_metal_device_init: recommendedMaxWorkingSetSize  = 10922.67 MB\n'
                return subprocess.CompletedProcess(cmd, 0, json.dumps(bench_json(cmd)), err)
            return subprocess.CompletedProcess(cmd, 0, '17179869184' if 'hw.memsize' in cmd else 'Mac16,12', '')
        subprocess.run = fake

    def tearDown(self):
        subprocess.run = self.keep; self.tmp.cleanup()

    def args(self, **kw):
        a = dict(bench=Path('/x/llama-bench'), build='b11669', contributor='me', model='', format='', depth=8192,
                 reps=5, ngl=99, notes='')
        return argparse.Namespace(**(a | kw))

    def test_names(self):
        self.assertEqual(measure_mac.fmt_from_name('dryrun2-1234-8d1600b2-Q5_K_M.gguf'), 'Q5_K_M')
        self.assertEqual(measure_mac.fmt_from_name('dryrun2-1234-8d1600b2-bf16.gguf'), 'bf16')
        self.assertEqual(measure_mac.fmt_from_name('model.gguf'), '')
        self.assertEqual(measure_mac.model_from_name('dryrun2-1234-8d1600b2-Q8_0.gguf', 'Q8_0'), 'dryrun2-1234-8d1600b2')

    def test_measure_row(self):
        g = self.d / 'm-Q8_0.gguf'; g.write_bytes(b'gguf')
        row = measure_mac.measure(g, self.args(), dict(machine='Mac16,12', chip='Apple M5', ram_gb=16, os='macOS 26'))
        self.assertEqual(set(row), set(measure_mac.FIELDS))
        self.assertEqual((row['model'], row['format'], row['bpw']), ('m', 'Q8_0', 8.0))
        self.assertEqual((row['pp512_tok_s'], row['tg128_tok_s'], row['tg16_at_depth_tok_s']), (2000.0, 150.3, 90.0))
        self.assertEqual((row['weights_mb'], row['kv_mb'], row['kv_cells']), (360.0, 194.6, 8448))
        self.assertEqual((row['compute_mb'], row['total_mb'], row['kv_mb_per_1k']), (128.0, 682.6, 23.59))
        self.assertEqual((row['gpu_working_set_mb'], row['fits_gpu']), (10922.7, 'yes'))
        self.assertEqual(len(self.calls), 2)  # speed and long run, each its own process
        self.assertIn('-d 8192', row['command'])
        self.assertNotIn('/x/', row['command'])

    def test_no_buffer_log_stops(self):
        keep = subprocess.run
        subprocess.run = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, json.dumps(bench_json(cmd)), '')
        g = self.d / 'm-Q8_0.gguf'; g.write_bytes(b'gguf')
        try:
            with self.assertRaises(SystemExit):
                measure_mac.measure(g, self.args(), {})
        finally:
            subprocess.run = keep

    def test_failed_bench_stops(self):
        subprocess.run = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, '', 'error: failed to load model')
        g = self.d / 'm-Q8_0.gguf'; g.write_bytes(b'gguf')
        with self.assertRaises(SystemExit):
            measure_mac.measure(g, self.args(), {})


def row(**kw):
    base = dict(date='2026-11-28', contributor='me', machine='Mac16,12', chip='Apple M5', ram_gb='16', os='macOS 26',
                runtime='llama.cpp b11669 (620d222), Metal, ngl 99', model='dr2', format='Q8_0', gguf_sha256='a' * 64,
                size_bytes='200000000', n_params='176000000', bpw='8.5', pp512_tok_s='2000', tg128_tok_s='150',
                depth='8192', tg16_at_depth_tok_s='90', weights_mb='360.0', kv_mb='194.6', kv_cells='8448',
                kv_mb_per_1k='23.59', compute_mb='128.0', total_mb='682.6', gpu_working_set_mb='10922.7', fits_gpu='yes',
                command='c', notes='')
    return base | kw


class TableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, rows, fields=measure_mac.FIELDS):
        p = self.d / name
        with open(p, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
        return p

    def scores(self):
        f = lambda fmt, s, sha: dict(model='dr2', format=fmt, bpw=8.5 if fmt == 'Q8_0' else 16.0, size_bytes=200_000_000,
                                     score=s, sha256=sha, n_items=20, eval_set='eval_own_20')
        return {'formats': [f('bf16', 0.40, 'b' * 64), f('Q8_0', 0.35, 'a' * 64)]}

    def prompts(self):
        ag = {'g10_55': dict(identical_outputs=50, of=55, mean_shared_prefix_fraction=0.95),
              'g12_fill_45': dict(identical_outputs=40, of=45, mean_shared_prefix_fraction=0.9)}
        return {'formats': {'bf16': {}, 'Q8_0': {'agreement_with_bf16': ag}}}

    def test_full_table(self):
        rows = build_table.read_rows([self.write('a.csv', [row(), row(format='bf16', gguf_sha256='b' * 64)]),
                                      self.write('b.csv', [row(ram_gb='32', chip='Apple M6', contributor='you')])])
        text = build_table.build(rows, self.scores(), self.prompts())
        self.assertIn('| 8 | Q8_0 | 8.5 | 200.0 | 0.3500 | -0.0500 | 50/55 / 40/45 (g10_55 / g12_fill_45) | 0.950 / 0.900 |', text)
        self.assertIn('| 16 | bf16 |', text)
        self.assertIn('Apple M6 32 GB', text)
        self.assertLess(text.index('| dr2 | 16 | bf16'), text.index('| dr2 | 8 | Q8_0'))
        self.assertIn('one sha256 across all rows and the job', text)

    def test_sha_mismatch_listed(self):
        rows = build_table.read_rows([self.write('a.csv', [row(), row(contributor='you', ram_gb='32', gguf_sha256='c' * 64)])])
        bad = build_table.sha_mismatches(rows, self.scores())
        self.assertEqual(len(bad), 1)
        self.assertIn('dr2 Q8_0', bad[0])
        self.assertIn('dry run 2 job', bad[0])

    def test_rerun_keeps_last_row(self):
        rows = build_table.read_rows([self.write('a.csv', [row(tg128_tok_s='100'), row(tg128_tok_s='150')])])
        self.assertEqual([x['tg128_tok_s'] for x in rows], ['150'])

    def test_missing_columns_refused(self):
        p = self.write('bad.csv', [{'model': 'x'}], fields=['model'])
        with self.assertRaises(SystemExit):
            build_table.read_rows([p])

    def test_no_job_yet(self):
        text = build_table.build(build_table.read_rows([self.write('a.csv', [row()])]), None, None)
        self.assertIn('the dry run 2 job has not run', text)


if __name__ == '__main__':
    unittest.main()
