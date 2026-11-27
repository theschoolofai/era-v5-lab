#!/usr/bin/env python3
"""Tests for the llama.cpp KL-per-slice runner (fake llama-perplexity, no llama.cpp needed):  python test_kl_slices.py"""
import importlib.util, re, sys, tempfile, unittest
from pathlib import Path

from tokenizers import Tokenizer, models, pre_tokenizers

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kl_slices as k  # noqa: E402

_spec = importlib.util.spec_from_file_location('kl_eval', HERE.parent / 'quality' / 'kl_eval.py')
kl_eval = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(kl_eval)

# one line per key of kl_eval.PATTERNS, copied from llama-perplexity's format (tools/perplexity/perplexity.cpp)
FIXTURE_LOG = '''====== Perplexity statistics ======
Mean PPL(Q)                   :   8.969900 ±   0.174300
Mean PPL(Q)/PPL(base)         :   1.012345 ±   0.002345
====== KL divergence statistics ======
Mean    KLD:   0.023286 ±   0.000319
Maximum KLD:   9.812345
99.0%   KLD:   0.182544
Median  KLD:   0.004321
====== Token probability statistics ======
RMS Δp    :  4.123 ± 0.044 %
Same top p: 92.083 ± 0.211 %
'''
EXPECTED = dict(ppl_ratio=1.012345, ppl_ratio_unc=0.002345, kld_mean=0.023286, kld_mean_unc=0.000319,
                kld_99=0.182544, same_top_p=92.083)


def make_tokenizer(path: Path) -> Path:
    """A word-level tokenizer: one token per whitespace-separated word."""
    vocab = {'[UNK]': 0, 'w': 1}
    tok = Tokenizer(models.WordLevel(vocab, unk_token='[UNK]'))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    tok.save(str(path))
    return path


class FakeRunner:
    """Stands in for kl_eval.perplexity: records each call, writes the fixture log, and the base file on a base pass."""

    def __init__(self):
        self.calls = []

    def __call__(self, args, gguf, ngl, extra, log):
        self.calls.append(dict(gguf=Path(gguf), ngl=ngl, extra=list(extra), chunks=args.chunks, ctx=args.ctx,
                               llama_bin=args.llama_bin))
        if '--kl-divergence' not in extra:  # base pass: llama-perplexity saves the base log-probabilities
            Path(extra[extra.index('--kl-divergence-base') + 1]).write_bytes(b'base')
        log.write_text(FIXTURE_LOG, encoding='utf-8')
        return log.read_text(encoding='utf-8'), 1.5


class KlSlicesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.tok = make_tokenizer(self.dir / 'tokenizer.json')

    def tearDown(self):
        self.tmp.cleanup()

    def test_fixture_covers_every_pattern(self):
        for key, pat in kl_eval.PATTERNS.items():
            self.assertTrue(re.search(pat, FIXTURE_LOG), key)

    def test_plan_chunks(self):
        self.assertEqual(k.plan_chunks(600, 512, 8), 1)
        self.assertEqual(k.plan_chunks(100, 512, 8), 0)
        self.assertEqual(k.plan_chunks(10_000, 512, 8), 8)

    def test_rows_and_base_cleanup(self):
        text = self.dir / 'c4-val.txt'
        text.write_text(' '.join(['w'] * 600), encoding='utf-8')  # 600 tokens: one chunk of 512
        short = self.dir / 'owm-test.txt'
        short.write_text(' '.join(['w'] * 100), encoding='utf-8')  # too short for one chunk
        work = self.dir / 'work'
        work.mkdir()
        runner = FakeRunner()
        rows = k.run_kl_slices(self.dir / 'ref.gguf', {'Q8_0': self.dir / 'q8.gguf', 'Q4_K_M': self.dir / 'q4.gguf'},
                               {'c4-val': text, 'owm-test': short}, self.tok, Path('/llama/bin'), work, runner=runner)
        self.assertEqual([(r['slice'], r['format']) for r in rows],
                         [('c4-val', 'Q8_0'), ('c4-val', 'Q4_K_M'), ('owm-test', None)])
        for row in rows[:2]:
            self.assertEqual(row['chunks'], 1)
            self.assertEqual(row['tokens_scored'], 255)  # llama.cpp scores ctx - 1 - ctx//2 tokens per chunk
            self.assertEqual(row['time_s'], 1.5)
            for key, value in EXPECTED.items():
                self.assertAlmostEqual(row[key], value)
        self.assertEqual(rows[2], {'slice': 'owm-test', 'format': None, 'chunks': 0})
        # one base pass on the reference, then one KL pass per format, all on the GPU, none for the short slice
        self.assertEqual([c['gguf'].name for c in runner.calls], ['ref.gguf', 'q8.gguf', 'q4.gguf'])
        self.assertEqual({c['ngl'] for c in runner.calls}, {99})
        self.assertEqual({(c['chunks'], c['ctx'], c['llama_bin']) for c in runner.calls}, {(1, 512, '/llama/bin')})
        self.assertIn('--kl-divergence-base', runner.calls[0]['extra'])
        self.assertNotIn('--kl-divergence', runner.calls[0]['extra'])
        self.assertIn('--kl-divergence', runner.calls[1]['extra'])
        self.assertEqual(list(work.glob('*.kld')), [])  # the ~260 KB-per-token base file is deleted

    def test_failed_pass_still_deletes_base_file(self):
        text = self.dir / 'c4-val.txt'
        text.write_text(' '.join(['w'] * 600), encoding='utf-8')
        work = self.dir / 'work'
        work.mkdir()

        def broken(args, gguf, ngl, extra, log):
            if '--kl-divergence' in extra:
                return 'no statistics here', 0.1
            return FakeRunner()(args, gguf, ngl, extra, log)

        with self.assertRaisesRegex(RuntimeError, 'no "ppl"'):
            k.run_kl_slices(self.dir / 'ref.gguf', {'Q8_0': self.dir / 'q8.gguf'}, {'c4-val': text}, self.tok,
                            Path('/llama/bin'), work, runner=broken)
        self.assertEqual(list(work.glob('*.kld')), [])


if __name__ == '__main__':
    unittest.main()
