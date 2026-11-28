#!/usr/bin/env python3
"""Tests for run_loop.py with a fake quantize_eval.py (no llama.cpp, no torch):  python test_run_loop.py"""
import contextlib, io, json, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_loop  # noqa: E402

SCORES = {'bf16': 0.80, 'Q8_0': 0.80, 'Q4_K_M': 0.65}


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); d = Path(self.tmp.name); self.d = d
        for n in ('model.safetensors', 'manifest.json', 'tok.json', 'eval.json'): (d / n).write_text(n)
        self.calls = []
        self.keep = run_loop.sh
        run_loop.sh = self.fake_sh

    def tearDown(self):
        run_loop.sh = self.keep; self.tmp.cleanup()

    def fake_sh(self, cmd, **kw):
        cmd = [str(c) for c in cmd]
        fmt = cmd[cmd.index('--formats') + 1]; self.calls.append(fmt)
        row = dict(score=SCORES[fmt], score_by_kind=dict(mcq=SCORES[fmt]), size_gb=1.0, bpw=8.0, gen_tok_s=5.0, n_items=20, sha256='ab', format=fmt)
        Path(cmd[cmd.index('--scores-out') + 1]).write_text(json.dumps(dict(formats=[row], export_a1=dict(passed=True), gguf_a3=dict(passed=True))))
        return ' '.join(cmd)

    def loop(self, *extra):
        d = self.d
        argv = ['--weights', str(d / 'model.safetensors'), '--manifest', str(d / 'manifest.json'), '--tokenizer', str(d / 'tok.json'),
                '--eval', str(d / 'eval.json'), '--out', str(d / 'out'), '--formats', 'bf16,Q8_0,Q4_K_M', '--drop-head-bias', *extra]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run_loop.main(argv), 0)

    def test_rerun_skips_and_a_changed_stage_reruns_only_what_it_must(self):
        self.loop(); self.assertEqual(self.calls, ['bf16', 'Q8_0', 'Q4_K_M'])
        self.loop(); self.assertEqual(len(self.calls), 3, 'a finished loop reruns nothing')
        run_loop.STAGES['quantize'] += 1
        try:
            self.loop(); self.assertEqual(len(self.calls), 6, 'a new quantize version reruns the format stages')
        finally:
            run_loop.STAGES['quantize'] -= 1
        log = [json.loads(x) for x in (self.d / 'out/loop_log.jsonl').read_text().splitlines()]
        self.assertEqual([x['event'] for x in log if x.get('stage') == 'strip'], ['start', 'done', 'skip', 'skip'])   # strip never reran

    def test_killed_stage_leaves_no_marker_and_the_rerun_resumes_there(self):
        real = self.fake_sh
        def die(cmd, **kw):
            if 'Q8_0' in [str(c) for c in cmd]: raise KeyboardInterrupt
            return real(cmd, **kw)
        run_loop.sh = die
        with self.assertRaises(KeyboardInterrupt): self.loop()
        self.assertTrue((self.d / 'out/stages/q_bf16.json').exists()); self.assertFalse((self.d / 'out/stages/q_Q8_0.json').exists())
        run_loop.sh = real; self.calls.clear(); self.loop()
        self.assertEqual(self.calls, ['Q8_0', 'Q4_K_M'])

    def test_gap_and_label(self):
        self.loop()
        g = json.loads((self.d / 'out/gap.json').read_text())
        self.assertEqual([r['gap'] for r in g['formats']], [0.0, 0.0, -0.15])
        self.assertIn('RELAXED: --drop-head-bias', g['guards']); self.assertIn('no watcher score given', g['watcher']['status'])

    def test_changed_checkpoint_reruns_everything(self):
        self.loop(); (self.d / 'model.safetensors').write_text('new weights'); self.loop()
        self.assertEqual(len(self.calls), 6)


if __name__ == '__main__':
    unittest.main(verbosity=1)
