#!/usr/bin/env python3
"""Tests for the llama.cpp KL-per-slice runner (fake llama-perplexity, no llama.cpp needed):  python test_kl_slices.py"""
import importlib.util, re, subprocess, sys, tempfile, unittest
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
BASE_LOG = 'perplexity: calculating perplexity over {n} chunks, n_ctx=512, batch_size=2048, n_seq=4\n'
EXPECTED = dict(ppl=8.9699, ppl_unc=0.1743, ppl_ratio=1.012345, ppl_ratio_unc=0.002345, kld_mean=0.023286,
                kld_mean_unc=0.000319, kld_median=0.004321, kld_99=0.182544, kld_max=9.812345, same_top_p=92.083,
                same_top_p_unc=0.211, rms_dp=4.123)


def make_tokenizer(path: Path) -> Path:
    """A word-level tokenizer: one token per whitespace-separated word."""
    vocab = {'[UNK]': 0, 'w': 1}
    tok = Tokenizer(models.WordLevel(vocab, unk_token='[UNK]'))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    tok.save(str(path))
    return path


class FakeRunner:
    """Stands in for kl_eval.perplexity: records each call, writes the fixture log, and the base file on a base pass."""

    def __init__(self, actual_chunks=None):
        self.calls = []
        self.actual_chunks = actual_chunks  # what the base log claims llama.cpp ran; default: as asked

    def __call__(self, args, gguf, ngl, extra, log):
        self.calls.append(dict(gguf=Path(gguf), ngl=ngl, extra=list(extra), chunks=args.chunks, ctx=args.ctx,
                               llama_bin=args.llama_bin))
        if '--kl-divergence' not in extra:  # base pass: llama-perplexity saves the base log-probabilities
            Path(extra[extra.index('--kl-divergence-base') + 1]).write_bytes(b'base')
        if '--kl-divergence' in extra:
            log.write_text(FIXTURE_LOG, encoding='utf-8')
        else:
            log.write_text(BASE_LOG.format(n=self.actual_chunks or args.chunks), encoding='utf-8')
        return log.read_text(encoding='utf-8'), 1.5


class LlamaLikeRunner(FakeRunner):
    """As FakeRunner, but the base pass reports the chunk count llama-perplexity would run on the text file: its words,
    plus one BOS if the GGUF adds one (`gguf_adds_bos`), divided by ctx, at most --chunks; under 2 * ctx tokens it
    refuses the text, as llama-perplexity does."""

    def __init__(self, gguf_adds_bos: bool):
        super().__init__()
        self.gguf_adds_bos = gguf_adds_bos

    def __call__(self, args, gguf, ngl, extra, log):
        if '-f' in extra:
            n = len(Path(extra[extra.index('-f') + 1]).read_text(encoding='utf-8').split()) + self.gguf_adds_bos
            if n < 2 * args.ctx:
                raise subprocess.CalledProcessError(1, 'llama-perplexity')
            self.actual_chunks = min(args.chunks, n // args.ctx)
        return super().__call__(args, gguf, ngl, extra, log)


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
        self.assertEqual(k.plan_chunks(600, 512, 8), 0)  # llama-perplexity needs 2 * ctx tokens
        self.assertEqual(k.plan_chunks(1023, 512, 8), 0)
        self.assertEqual(k.plan_chunks(1024, 512, 8), 2)
        self.assertEqual(k.plan_chunks(100, 512, 8), 0)
        self.assertEqual(k.plan_chunks(10_000, 512, 8), 8)

    def test_rows_and_base_cleanup(self):
        text = self.dir / 'c4-val.txt'
        text.write_text(' '.join(['w'] * 1100), encoding='utf-8')  # 1100 words + BOS: 2 chunks of 512
        short = self.dir / 'owm-test.txt'
        short.write_text(' '.join(['w'] * 600), encoding='utf-8')  # 601 tokens: under 2 * 512, llama.cpp refuses
        work = self.dir / 'work'
        work.mkdir()
        runner = FakeRunner()
        rows = k.run_kl_slices(self.dir / 'ref.gguf', {'Q8_0': self.dir / 'q8.gguf', 'Q4_K_M': self.dir / 'q4.gguf'},
                               {'c4-val': text, 'owm-test': short}, self.tok, Path('/llama/bin'), work, runner=runner,
                               add_bos=True)
        self.assertEqual([(r['slice'], r['format']) for r in rows],
                         [('c4-val', 'Q8_0'), ('c4-val', 'Q4_K_M'), ('owm-test', None)])
        for row in rows[:2]:
            self.assertEqual(row['chunks'], 2)
            self.assertEqual(row['tokens_scored'], 510)  # llama.cpp scores ctx - 1 - ctx//2 tokens per chunk
            self.assertEqual(row['time_s'], 1.5)
            for key, value in EXPECTED.items():
                self.assertAlmostEqual(row[key], value)
        self.assertEqual(rows[2], {'slice': 'owm-test', 'format': None, 'chunks': 0})
        # one base pass on the reference, then one KL pass per format, all on the GPU, none for the short slice
        self.assertEqual([c['gguf'].name for c in runner.calls], ['ref.gguf', 'q8.gguf', 'q4.gguf'])
        self.assertEqual({c['ngl'] for c in runner.calls}, {99})
        self.assertEqual({(c['chunks'], c['ctx'], c['llama_bin']) for c in runner.calls}, {(2, 512, '/llama/bin')})
        self.assertIn('--kl-divergence-base', runner.calls[0]['extra'])
        self.assertNotIn('--kl-divergence', runner.calls[0]['extra'])
        self.assertIn('--kl-divergence', runner.calls[1]['extra'])
        self.assertEqual(list(work.glob('*.kld')), [])  # the ~260 KB-per-token base file is deleted

    def test_bos_is_counted_only_when_the_gguf_adds_one(self):
        """1535 words: 1536 tokens and 3 chunks with a BOS, 1535 tokens and 2 chunks without. 1023 words: 1024 tokens
        and 2 chunks with a BOS; without one, under 2 * 512, so no llama.cpp call. A plan that always counted a BOS
        would ask for 3 chunks (and raise) or call llama.cpp on a text it refuses."""
        for words, add_bos, chunks in ((1535, True, 3), (1535, False, 2), (1023, True, 2), (1023, False, 0)):
            with self.subTest(words=words, add_bos=add_bos):
                text = self.dir / 'c4-val.txt'
                text.write_text(' '.join(['w'] * words), encoding='utf-8')
                work = self.dir / f'work-{words}-{add_bos}'
                work.mkdir()
                runner = LlamaLikeRunner(add_bos)
                rows = k.run_kl_slices(self.dir / 'ref.gguf', {'Q8_0': self.dir / 'q8.gguf'}, {'c4-val': text},
                                       self.tok, Path('/llama/bin'), work, runner=runner, add_bos=add_bos)
                self.assertEqual([r['chunks'] for r in rows], [chunks])
                self.assertEqual(len(runner.calls), 2 if chunks else 0)

    def test_failed_pass_still_deletes_base_file(self):
        text = self.dir / 'c4-val.txt'
        text.write_text(' '.join(['w'] * 1100), encoding='utf-8')
        work = self.dir / 'work'
        work.mkdir()

        def broken(args, gguf, ngl, extra, log):
            if '--kl-divergence' in extra:
                return 'no statistics here', 0.1
            return FakeRunner()(args, gguf, ngl, extra, log)

        with self.assertRaisesRegex(RuntimeError, 'no "ppl"'):
            k.run_kl_slices(self.dir / 'ref.gguf', {'Q8_0': self.dir / 'q8.gguf'}, {'c4-val': text}, self.tok,
                            Path('/llama/bin'), work, runner=broken, add_bos=True)
        self.assertEqual(list(work.glob('*.kld')), [])

    def test_chunk_count_mismatch_is_an_error(self):
        text = self.dir / 'c4-val.txt'
        text.write_text(' '.join(['w'] * 1100), encoding='utf-8')  # planned: 2 chunks
        work = self.dir / 'work'
        work.mkdir()
        with self.assertRaisesRegex(RuntimeError, r'c4-val.*planned 2 chunks.*ran 1'):
            k.run_kl_slices(self.dir / 'ref.gguf', {'Q8_0': self.dir / 'q8.gguf'}, {'c4-val': text}, self.tok,
                            Path('/llama/bin'), work, runner=FakeRunner(actual_chunks=1), add_bos=True)
        self.assertEqual(list(work.glob('*.kld')), [])

    def test_missing_chunk_line_is_an_error(self):
        text = self.dir / 'c4-val.txt'
        text.write_text(' '.join(['w'] * 1100), encoding='utf-8')
        work = self.dir / 'work'
        work.mkdir()

        def silent(args, gguf, ngl, extra, log):
            Path(extra[extra.index('--kl-divergence-base') + 1]).write_bytes(b'base')
            return 'nothing useful', 0.1

        with self.assertRaisesRegex(RuntimeError, 'no "calculating perplexity over N chunks"'):
            k.run_kl_slices(self.dir / 'ref.gguf', {'Q8_0': self.dir / 'q8.gguf'}, {'c4-val': text}, self.tok,
                            Path('/llama/bin'), work, runner=silent, add_bos=True)


if __name__ == '__main__':
    unittest.main()
