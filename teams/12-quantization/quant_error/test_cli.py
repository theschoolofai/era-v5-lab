#!/usr/bin/env python3
"""Tests for the one-command run:  python test_cli.py

The end-to-end test runs quant_error.py on the tiny ERNIE model (a converter-made bf16 GGUF and a llama-quantize Q8_0)
and the real held-out file; it needs LLAMA_CPP_DIR (a llama.cpp b12359 checkout, built) and is skipped without it.
The pure parts (CSV writing, the size limit, the batches) always run.
"""
import csv, json, math, os, re, subprocess, sys, tempfile, unittest
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixtures  # noqa: E402
import quant_error as qe  # noqa: E402

LLAMA = os.environ.get('LLAMA_CPP_DIR')
HELDOUT = HERE.parents[2] / 'teams/05-architecture/heldout_v1/data/heldout_v1.jsonl'
BUILT = None   # fixtures.Built, for this module's tests
FILES = ('summary.json', 'tensors.csv', 'layers.csv', 'linears.csv', 'tokens.csv', 'kl.csv')
SUMMARY_KEYS = ('python', 'torch', 'transformers', 'gguf', 'llama_cpp', 'sha256', 'settings', 'wall_time_s', 'export_gap')


def setUpModule():
    global BUILT
    BUILT = fixtures.Built()


def tearDownModule():
    BUILT.close()


def read_csv(path: Path) -> list[dict]:
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


class PureTests(unittest.TestCase):
    def test_write_csv_none_inf_and_missing_keys(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'x.csv'
            qe.write_csv(p, ['a', 'b', 'c'], [{'a': None, 'b': math.inf, 'c': 1.5}, {'a': 2}])
            self.assertEqual(p.read_text(encoding='utf-8').splitlines(), ['a,b,c', ',inf,1.5', '2,,'])

    def test_write_csv_rejects_an_unknown_key(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                qe.write_csv(Path(t) / 'x.csv', ['a'], [{'a': 1, 'text': 'hello'}])

    def test_batches_cut_the_first_tokens_into_whole_sequences(self):
        ids = list(range(1000))
        got = qe.cut_batches(ids, tokens_per_slice=700, seq_len=512)
        self.assertEqual([b.tolist() for b in got], [ids[:512]])     # the 188-token remainder is dropped
        got = qe.cut_batches(ids, tokens_per_slice=64, seq_len=512)  # seq_len is capped at tokens_per_slice
        self.assertEqual([b.tolist() for b in got], [ids[:64]])
        got = qe.cut_batches(ids, tokens_per_slice=1000, seq_len=256)
        self.assertEqual([len(b) for b in got], [256, 256, 256])     # the 232-token remainder is dropped
        self.assertTrue(all(b.dtype == torch.long for b in got))
        with self.assertRaises(ValueError):                          # fewer tokens than one sequence
            qe.cut_batches(ids[:10], tokens_per_slice=64, seq_len=512)

    def test_size_limit(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'a').write_bytes(b'x' * 100)
            self.assertEqual(qe.folder_bytes(Path(t)), 100)
            self.assertTrue(qe.within_limit(Path(t), limit=100))
            self.assertFalse(qe.within_limit(Path(t), limit=99))

    def test_parse_quant(self):
        self.assertEqual(qe.parse_quant('Q8_0=/a/b=c.gguf'), ('Q8_0', Path('/a/b=c.gguf')))
        for bad in ('Q8_0', '=x.gguf', 'Q8_0='):
            with self.assertRaises(Exception):
                qe.parse_quant(bad)


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        if not LLAMA:
            self.skipTest('set LLAMA_CPP_DIR to a built llama.cpp b12359 checkout')

    def test_cli_tiny_ernie(self):
        hf = BUILT('ernie', fixtures.tiny_ernie)
        bf16 = BUILT('ernie-bf16.gguf', lambda out: fixtures.to_gguf(hf, out, 'bf16'))
        q8 = BUILT('ernie-q8_0.gguf', lambda out: self.quantize(bf16, out, 'Q8_0'))
        t = Path(BUILT._tmp.name)
        report = t / 'export_report.json'
        report.write_text(json.dumps({'verify': {'head_bias_effect': {'max_abs_logit_diff': 0.25}}}), encoding='utf-8')
        out = t / 'out'
        r = subprocess.run([sys.executable, str(HERE / 'quant_error.py'), 'all', '--hf-config', str(hf),
                            '--tokenizer', str(fixtures.P1536), '--ref', str(bf16), '--quant', f'Q8_0={q8}',
                            '--heldout', str(HELDOUT), '--llama-bin', str(Path(LLAMA) / 'build/bin'), '--out', str(out),
                            '--tokens-per-slice', '64', '--kl-chunks', '1', '--export-report', str(report)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-3000:])
        for name in FILES:
            self.assertTrue((out / name).is_file(), name)
        summary = json.loads((out / 'summary.json').read_text(encoding='utf-8'))
        for key in SUMMARY_KEYS:
            self.assertIn(key, summary)
        self.assertEqual(summary['export_gap'], {'max_abs_logit_diff': 0.25})
        self.assertRegex(summary['llama_cpp'], r'^b\d+ \([0-9a-f]{7,}\)$')
        self.assertEqual(set(summary['sha256']), {'ref', 'quants', 'heldout'})
        self.assertEqual(set(summary['sha256']['quants']), {'Q8_0'})
        self.assertLess(sum(p.stat().st_size for p in out.rglob('*') if p.is_file()), 5 * 1024 * 1024)
        self.assertEqual(sorted(p.name for p in out.iterdir()), sorted(FILES))   # no work files left in --out
        for name in FILES[1:]:
            rows = read_csv(out / name)
            self.assertTrue(rows, name)
            self.assertFalse({'text', 'ids', 'tokens_list'} & set(rows[0]), name)
            self.assertIn('format', rows[0], name)
        n_slices = len(qe.SLICES)
        self.assertEqual({r['slice'] for r in read_csv(out / 'tokens.csv')}, set(qe.SLICES))
        self.assertEqual(len(read_csv(out / 'tokens.csv')), n_slices)
        self.assertEqual(len(read_csv(out / 'layers.csv')), n_slices * 2)    # 2 layers
        kl = read_csv(out / 'kl.csv')
        self.assertEqual(len(kl), n_slices)
        self.assertTrue(all(row['chunks'] == '1' and row['kld_mean'] for row in kl), kl[:2])
        linears = read_csv(out / 'linears.csv')
        self.assertIn('rows', linears[0])
        self.assertTrue(any(row['tensor'] == 'lm_head.weight' and row['layer'] == '' for row in linears))
        # BF16 reference: a Q8_0 file of a bf16 reference has a small but non-zero error on its quantized matrices
        tensors = read_csv(out / 'tensors.csv')
        attn = [float(row['rel_err']) for row in tensors if row['kind'] == 'attn_q']
        self.assertTrue(attn and all(0 < e < 0.05 for e in attn), attn)

    @staticmethod
    def quantize(src: Path, out: Path, kind: str) -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([str(Path(LLAMA) / 'build/bin/llama-quantize'), '--output-tensor-type', 'q8_0',
                            str(src), str(out), kind], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f'llama-quantize failed:\n{r.stderr[-2000:]}')
        return out


if __name__ == '__main__':
    unittest.main()
